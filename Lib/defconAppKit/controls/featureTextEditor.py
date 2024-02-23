import re
import weakref
from AppKit import NSTextView, NSColor, NSFont, NSMiniControlSize, NSOnState, NSOffState, NSFontAttributeName, \
    NSIntersectsRect, NSRulerView, NSNotificationCenter, NSNotFound, NSFontNameAttribute, NSString, NSTextStorageDidProcessEditingNotification, \
    NSNumberFormatter, NSNumber, NSFocusRingTypeNone, NSUnionRect
from objc import super
import vanilla
from vanilla.vanillaTextEditor import VanillaTextEditorDelegate
from objc import python_method
from defconAppKit.controls.placardScrollView import DefconAppKitPlacardNSScrollView, PlacardPopUpButton
from defconAppKit.windows.popUpWindow import InteractivePopUpWindow
from defconAppKit.tools.featureTextTools import breakFeatureTextIntoRuns, findBlockOpenLineStarts


# -------------------
# Whitespace Guessing
# -------------------

_whitespaceRE = re.compile("([ \t]+)")


def _guessMinWhitespace(text):
    # gather all whitespace at the beginning of a line
    whitespace = set()
    for line in text.splitlines():
        # skip completely blank lines
        if not line.strip():
            continue
        # store the found whitespace
        m = _whitespaceRE.match(line)
        if m is not None:
            whitespace.add(m.group(1))
    # if nothing was found, fallback to a single tab
    if not whitespace:
        return "\t"
    # get the smallest whitespace increment
    whitespace = min(whitespace)
    # if the whitespace starts with a tab, use a single tab
    if whitespace.startswith("\t"):
        return "\t"
    # use what was found
    return whitespace


# -------------------
# NSObject Subclasses
# -------------------

class DefconAppKitFeatureTextView(NSTextView):

    def insertTab_(self, sender):
        # this is very basic and could be improved
        # see PyDETextView for a better implementation
        vanillaWrapper = self.vanillaWrapper()
        if vanillaWrapper._usesTabs:
            super(DefconAppKitFeatureTextView, self).insertTab_(sender)
        else:
            self.insertText_(vanillaWrapper._whitespace)

    def viewDidMoveToWindow(self):
        self._setWrapLines_(False)
        ruler = self.enclosingScrollView().verticalRulerView()
        if ruler is not None:
            ruler.clientViewSelectionChanged_(None)

    # -------------------
    # menu item callbacks
    # -------------------

    def validateMenuItem_(self, item):
        if item.action() in "toggleWrapLines:":
            if self.getWrapLines():
                state = NSOnState
            else:
                state = NSOffState
            item.setState_(state)
        return super(DefconAppKitFeatureTextView, self).validateMenuItem_(item)

    def showJumpToLineInterface_(self, sender):
        frame = self.enclosingScrollView().frame()
        superview = self.enclosingScrollView()
        while True:
            s = superview.superview()
            if s is None:
                break
            else:
                frame = s.convertRect_fromView_(frame, superview)
                superview = s
        (x, y), (w, h) = frame
        (x, y) = self.window().convertBaseToScreen_((x, y))
        JumpToLinePopUpWindow(((x, y), (w, h)), self.window().screen(), self._jumpToLineInterfaceCallback_)

    @python_method
    def _jumpToLineInterfaceCallback_(self, lineNumber):
        self.jumpToLine_(lineNumber)

    def jumpToLine_(self, lineNumber):
        lineNumber -= 1
        text = self.string()
        lines = text.splitlines()
        if lineNumber > len(lines):
            lineStart = len(text)
        else:
            precedingLines = lines[:lineNumber]
            lineStart = len(u"\n".join(precedingLines)) + 1
        self.setSelectedRange_((lineStart, 0))
        self.scrollRangeToVisible_((lineStart, 0))

    # -------------
    # line wrapping
    # -------------

    def toggleWrapLines_(self, sender):
        self.setWrapLines_(not self.getWrapLines())

    def getWrapLines(self):
        return not self.isHorizontallyResizable()

    def setWrapLines_(self, value):
        if value == self.getWrapLines():
            return
        self._setWrapLines_(value)

    @python_method
    def _setWrapLines_(self, value):
        scrollView = self.enclosingScrollView()
        height = height = self.maxSize()[1]
        if value:
            width = scrollView.contentView().bounds().size[0]
        else:
            width = height
        self.setMaxSize_((width, height))
        self.setHorizontallyResizable_(not value)
        self.textContainer().setWidthTracksTextView_(value)
        self.textContainer().setContainerSize_((width, height))


class DefconAppKitFeatureTextEditorDelegate(VanillaTextEditorDelegate):

    def textStorageDidProcessEditing_(self, notification):
        self.vanillaWrapper()._highlightSyntaxAsAResultOfEditing()

    def textViewDidChangeSelection_(self, notification):
        self.vanillaWrapper()._selectionChangedCallback()


# ----------------------
# Jump To Line Interface
# ----------------------


class JumpToLinePopUpWindow(object):

    def __init__(self, frameToCenterInside, screen, callback):
        self._callback = callback
        width = 180
        height = 97
        (frameXMin, frameYMin), (frameWidth, frameHeight) = frameToCenterInside
        screenTop = screen.frame()[0][1]
        frameTop = screenTop - (frameYMin + frameHeight)

        x = frameXMin + ((frameWidth - width) / 2)
        y = frameTop + ((frameHeight - height) / 2)

        formatter = NSNumberFormatter.alloc().init()
        formatter.setFormat_("#;0;-#")
        formatter.setAllowsFloats_(False)
        formatter.setGeneratesDecimalNumbers_(False)
        formatter.setMinimum_(NSNumber.numberWithInt_(1))

        self.w = InteractivePopUpWindow((x, y, width, height))
        self.w.title = vanilla.TextBox((15, 18, 88, 17), "Jump to line:")
        self.w.lineInput = vanilla.EditText((103, 15, -15, 22), formatter=formatter)
        self.w.lineInput.getNSTextField().setFocusRingType_(NSFocusRingTypeNone)
        self.w.line = vanilla.HorizontalLine((15, -50, -15, 1))
        self.w.cancelButton = vanilla.Button((15, -35, 70, 20), "Cancel", callback=self.cancelCallback)
        self.w.okButton = vanilla.Button((95, -35, 70, 20), "OK", callback=self.okCallback)

        self.w.setDefaultButton(self.w.okButton)
        self.w.cancelButton.bind(".", ["command"])
        self.w.getNSWindow().makeFirstResponder_(self.w.lineInput.getNSTextField())

        self.w.open()

    def cancelCallback(self, sender):
        self._callback = None
        self.w.close()

    def okCallback(self, sender):
        self.w.close()
        value = self.w.lineInput.get()
        if value is not None:
            self._callback(value)
        self._callback = None


# -----------------
# Line Number Ruler
# -----------------

rulerFont = NSFont.labelFontOfSize_(NSFont.systemFontSizeForControlSize_(NSMiniControlSize))


class DefconAppKitLineNumberView(NSRulerView):

    def init(self):
        self = super(DefconAppKitLineNumberView, self).init()
        self._existingText = None
        self._existingClientViewWidth = None
        self._lineRects = []
        return self

    def dealloc(self):
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)
        super(DefconAppKitLineNumberView, self).dealloc()

    def requiredThickness(self):
        count = len(self._lineRects)
        count = NSString.stringWithString_(str(count))
        width, height = count.sizeWithAttributes_({NSFontNameAttribute : rulerFont})
        return width + 10

    def _updateRects(self):
        clientView = self.clientView()
        clientFrame = clientView.frame()
        if clientFrame[1][0] == 0 or clientFrame[1][1] == 0:
            return
        text = clientView.string()
        attributedString = clientView.attributedString()
        font = clientView.font()
        pointSize = font.pointSize()
        layoutManager = clientView.layoutManager()
        textContainer = clientView.textContainer()
        previousLineBottom = 0
        lineStart = 0
        lineRects = []
        for index, line in enumerate(text.splitlines()):
            index += 1
            lineLength = len(line)
            rectArray, rectCount = layoutManager.rectArrayForCharacterRange_withinSelectedCharacterRange_inTextContainer_rectCount_(
                (lineStart, lineLength), (NSNotFound, 0), textContainer, None
            )
            # make sure that the first rect has a width
            if rectArray[0].size[0] == 0:
                (x, y), (w, h) = rectArray[0]
                w = 1
                rectArray = [((x, y), (w, h))] + list(rectArray[1:])
            # merge the rects
            rect = rectArray[0]
            for otherRect in rectArray[1:]:
                rect = NSUnionRect(rect, otherRect)
            # store
            lineRects.append((index, rect))
            # offset for next line
            lineStart += lineLength + 1
            previousLineBottom = rect[0][1] + rect[1][1]
        self._lineRects = lineRects
        self._existingText = text
        self._existingClientViewWidth = clientFrame.size[0]

    def drawHashMarksAndLabelsInRect_(self, rect):
        clientView = self.clientView()
        visibleRect = clientView.visibleRect()
        visibleYMin = visibleRect[0][1]
        rulerWidth = self.frame().size[0]
        attributes = {NSFontAttributeName : rulerFont}
        for index, lineRect in self._lineRects:
            if not NSIntersectsRect(visibleRect, lineRect):
                continue
            text = NSString.stringWithString_(str(index))
            textWidth, textHeight = text.sizeWithAttributes_(attributes)
            (xMin, yMin), (w, h) = lineRect
            y = yMin - visibleYMin
            x = rulerWidth - textWidth - 5
            text.drawAtPoint_withAttributes_((x, y), attributes)

    def clientViewSelectionChanged_(self, notification):
        clientView = self.clientView()
        # look to see if the rects need to be recalculated
        text = clientView.string()
        if text != self._existingText or clientView.frame().size[0] != self._existingClientViewWidth:
            self._updateRects()
            requiredThickness = self.requiredThickness()
            if requiredThickness != self.ruleThickness():
                self.setRuleThickness_(requiredThickness)
        self.setNeedsDisplay_(True)


# -------------
# Public Object
# -------------

class FeatureTextEditor(vanilla.TextEditor):

    nsTextViewClass = DefconAppKitFeatureTextView
    nsScrollViewClass = DefconAppKitPlacardNSScrollView
    delegateClass = DefconAppKitFeatureTextEditorDelegate

    def __init__(self, posSize, text, callback=None):
        # there must be a callback as it triggers the creation of the delegate
        if callback is None:
            callback = self._fallbackCallback
        super(FeatureTextEditor, self).__init__(posSize, "", callback=callback)
        self._nsObject.setHasHorizontalScroller_(True)
        font = NSFont.fontWithName_size_("Monaco", 10)
        self._textView.setFont_(font)
        self._textView.setUsesFindPanel_(True)
        ## line numbers
        #ruler = DefconAppKitLineNumberView.alloc().init()
        #ruler.setClientView_(self._textView)
        #self._nsObject.setVerticalRulerView_(ruler)
        #self._nsObject.setHasHorizontalRuler_(False)
        #self._nsObject.setHasVerticalRuler_(True)
        #self._nsObject.setRulersVisible_(True)
        #notificationCenter = NSNotificationCenter.defaultCenter()
        #notificationCenter.addObserver_selector_name_object_(
        #    ruler, "clientViewSelectionChanged:", NSTextViewDidChangeSelectionNotification, self._textView
        #)
        # colors
        self._mainColor = NSColor.blackColor()
        self._commentColor = NSColor.colorWithCalibratedWhite_alpha_(.6, 1)
        self._keywordColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, 0, 0, 1)
        self._tokenColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, .4, 0, 1)
        self._classNameColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, .8, 1)
        self._includeColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, 0, .8, 1)
        self._stringColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .6, 0, 1)
        # build the placard
        placardW = 65
        placardH = 16
        self._placardJumps = []
        self._placard = vanilla.Group((0, 0, placardW, placardH))
        self._placard.featureJumpButton = PlacardPopUpButton((0, 0, placardW, placardH),
            [], callback=self._placardFeatureSelectionCallback, sizeStyle="mini")
        self._nsObject.setPlacard_(self._placard.getNSView())
        # registed for syntax coloring notifications
        self._programmaticallySettingText = False
        delegate = self._textViewDelegate
        delegate.vanillaWrapper = weakref.ref(self)
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.addObserver_selector_name_object_(
            self._textViewDelegate, "textStorageDidProcessEditing:", NSTextStorageDidProcessEditingNotification, self._textView.textStorage())
        # set the text
        self.set(text)

    def _breakCycles(self):
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self._textViewDelegate)

    def _fallbackCallback(self, sender):
        pass

    # Code Editing Support

    def _highlightSyntaxAsAResultOfEditing(self):
        if self._programmaticallySettingText:
            return
        string = self._textView.string()
        editedRange = self._textView.textStorage().editedRange()
        lineStart, lineLength = string.lineRangeForRange_(editedRange)
        text = string.substringWithRange_((lineStart, lineLength))
        self._highlightSyntax(lineStart, text)

    def _highlightSyntax(self, location, text):
        # convert all text to black
        self._textView.setTextColor_range_(self._mainColor, (location, len(text)))
        colors = dict(
            comments=self._commentColor,
            strings=self._stringColor,
            tokens=self._tokenColor,
            keywords=self._keywordColor,
            includes=self._includeColor,
            classNames=self._classNameColor,
        )
        for typ, runs in breakFeatureTextIntoRuns(text):
            color = colors[typ]
            for start, end in runs:
                length = end - start
                start = location + start
                self._textView.setTextColor_range_(color, (start, length))
        # update the pop up
        self._updatePopUp()

    # placard support

    def _updatePopUp(self):
        text = self.get()
        ranges = findBlockOpenLineStarts(text)
        self._placardJumps = ranges
        titles = [i[0] for i in ranges]
        self._placard.featureJumpButton.setItems(titles)

    def _placardFeatureSelectionCallback(self, sender):
        index = sender.get()
        name, start = self._placardJumps[index]
        self._textView.setSelectedRange_((start, 0))
        self._textView.scrollRangeToVisible_((start, 0))
        self._textView.setNeedsDisplay_(True)

    def _selectionChangedCallback(self):
        selectionStart = self._textView.selectedRange()[0]
        newIndex = None
        for index, (name, start) in enumerate(self._placardJumps):
            if newIndex is None:
                newIndex = index
                continue
            if start > selectionStart:
                break
            else:
                newIndex = index
        if newIndex is not None:
            self._placard.featureJumpButton.set(newIndex)

    # Public Methods

    def set(self, text):
        """
        Set the text in the editor.
        """
        self._programmaticallySettingText = True
        super(FeatureTextEditor, self).set(text)
        self._whitespace = _guessMinWhitespace(text)
        self._usesTabs = self._whitespace == "\t"
        self._highlightSyntax(0, text)
        self._programmaticallySettingText = False

    def setWrapLines(self, value):
        """
        Boolean representing if lines should be soft wrapped or not.
        """
        self._textView.setWrapLines_(value)

    def getWrapLines(self):
        """
        Boolean representing if the lines are soft wrapped or not.
        """
        return self._textView.getWrapLines()

    def setMainColor(self, value):
        self._mainColor = value
        self._highlightSyntax(0, self.get())

    def getMainColor(self):
        return self._mainColor

    def setCommentColor(self, value):
        self._commentColor = value
        self._highlightSyntax(0, self.get())

    def getCommentColor(self):
        return self._commentColor

    def setKeywordColor(self, value):
        self._keywordColor = value
        self._highlightSyntax(0, self.get())

    def getKeywordColor(self):
        return self._keywordColor

    def setTokenColor(self, value):
        self._tokenColor = value
        self._highlightSyntax(0, self.get())

    def getTokenColor(self):
        return self._tokenColor

    def setClassColor(self, value):
        self._classNameColor = value
        self._highlightSyntax(0, self.get())

    def getClassColor(self):
        return self._classNameColor

    def setIncludeColor(self, value):
        self._includeColor = value
        self._highlightSyntax(0, self.get())

    def getIncludeColor(self):
        return self._includeColor
