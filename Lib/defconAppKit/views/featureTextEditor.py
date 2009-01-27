import re
import weakref
from AppKit import *
import vanilla
from vanilla.vanillaTextEditor import VanillaTextEditorDelegate
from defconAppKit.views.placardScrollView import DefconAppKitPlacardNSScrollView, PlacardPopUpButton


# ---------------------------------------
# Syntax Highlighting Regular Expressions
# ---------------------------------------

_keywords = """anchor
anonymous
anon
by
caret
cursive
device
enumerate
enum
exclude_dflt
feature
from
ignore
IgnoreBaseGlyphs
IgnoreLigatures
IgnoreMarks
include
include_dflt
language
languagesystem
lookup
lookupflag
mark
nameid
parameters
position
pos
required
RightToLeft
script
substitute
sub
subtable
table
useExtension"""

_keywordREs = []
for keyword in _keywords.splitlines():
    pattern = re.compile("(^|[\s;]+)(" + keyword +")($|[\s;(]+)")
    _keywordREs.append(pattern)

_tokens = """;
,
\
-
=
'
"
{
}
[
]
<
>
(
)"""

_tokenREs = []
for token in _tokens.splitlines():
    pattern = re.compile("()(" + re.escape(token) +")()")
    _tokenREs.append(pattern)

_commentSubRE = re.compile("#.*$", re.MULTILINE)

_classNameRE = re.compile(
    "()"
    "(@[a-zA-Z0-9_.]*)"
    "()"
    )

_includeRE = re.compile(
    "(include\s*\()"
    "([^)]+)"
    "(\)\s*;)"
)

# ------------------------------------------
# Line Number Extraction Regular Expressions
# ------------------------------------------

_lineNumberScanOpen = re.compile(
    "(^|[\s;]+)"
    "feature"
    "\s+"
    "([A-Za-z0-9]+)"
    "\s*"
    "\{"
)

_lineNumberScanClose = re.compile(
    "}"
    "\s*"
    "([A-Za-z0-9]+)"
)

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
        vanillaWrapper = self.vanillaWrapper()
        if vanillaWrapper._wrapLines is None:
            vanillaWrapper.setWrapLines(False)


class DefconAppKitFeatureTextEditorDelegate(VanillaTextEditorDelegate):

    def textStorageDidProcessEditing(self, notification):
        self.vanillaWrapper()._highlightSyntaxAsAResultOfEditing()

    def textViewDidChangeSelection_(self, notification):
        self.vanillaWrapper()._selectionChangedCallback()


# -------------
# Public Object
# -------------

class FeatureTextEditor(vanilla.TextEditor):

    nsTextViewClass = DefconAppKitFeatureTextView
    nsScrollViewClass = DefconAppKitPlacardNSScrollView
    delegateClass = DefconAppKitFeatureTextEditorDelegate

    def __init__(self, posSize, text, callback=None):
        # don't wrap lines
        self._wrapLines = None
        # there must be a callback as it triggers the creation of the delegate
        if callback is None:
            callback = self._fallbackCallback
        super(FeatureTextEditor, self).__init__(posSize, "", callback=callback)
        font = NSFont.fontWithName_size_("Monaco", 10)
        self._textView.setFont_(font)
        # colors
        self._mainColor = NSColor.blackColor()
        self._commentColor = NSColor.colorWithCalibratedWhite_alpha_(.6, 1)
        self._keywordColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, 0, 0, 1)
        self._tokenColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, .4, 0, 1)
        self._classColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, .8, 1)
        self._includeColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, 0, .8, 1)
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
            self._textViewDelegate, "textStorageDidProcessEditing", NSTextStorageDidProcessEditingNotification, self._textView.textStorage())
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
        # find all patterns that appaear in the text
        textWithoutComments = re.sub(_commentSubRE, "", text)
        knownKeywords = self._findMatchingPatterns(textWithoutComments, _keywordREs)
        knownTokens = self._findMatchingPatterns(textWithoutComments, _tokenREs)
        # run through all lines
        characterCounter = location
        for line in text.splitlines():
            lineLength = len(line)
            # comments
            if "#" in line:
                before, after = line.split("#", 1)
                after = "#" + after
                location = characterCounter + len(before)
                length = len(after)
                self._textView.setTextColor_range_(self._commentColor, (location, length))
            # keywords
            strippedLine = line.split("#", 1)[0].rstrip()
            for keyword in knownKeywords:
                self._patternRecurse(strippedLine, keyword, characterCounter, self._keywordColor)
            # tokens
            for token in knownTokens:
                self._patternRecurse(strippedLine, token, characterCounter, self._tokenColor)
            # classes
            self._patternRecurse(strippedLine, _classNameRE, characterCounter, self._classColor)
            # include
            self._patternRecurse(strippedLine, _includeRE, characterCounter, self._includeColor)
            characterCounter += lineLength + 1
        # update the pop up
        self._updatePopUp()

    def _findMatchingPatterns(self, text, patterns):
        found = []
        for pattern in patterns:
            if pattern.findall(text):
                found.append(pattern)
        return found

    def _patternRecurse(self, line, pattern, lineStart, color):
        m = pattern.search(line)
        if m is None:
            return
        # get the span
        matchStart, matchEnd = m.span()
        # strip the match from the line
        leftOverLine = line[matchEnd:]
        # work out the relevant match location
        junk1, matchedText, junk2 = m.groups()
        location = lineStart + len(junk1) + matchStart
        length = len(matchedText)
        # colorize
        self._textView.setTextColor_range_(color, (location, length))
        # if there is any text left, go again
        if leftOverLine.strip():
            self._patternRecurse(leftOverLine, pattern, lineStart+matchEnd, color)

    # placard support

    def _updatePopUp(self):
        ranges = []
        openFeature = None
        openFeatureStart = 0
        characterCounter = 0
        for lineIndex, line in enumerate(self.get().splitlines()):
            lineLength = len(line)
            line = line.split("#", 1)[0]
            if openFeature:
                closures = _lineNumberScanClose.findall(line)
                if openFeature in closures:
                    ranges.append((openFeature, openFeatureStart))
                    openFeature = None
                    # this could inadvertantly skip a feature that is defined
                    # on the same line as another feature is being closed.
                    # this probably isn't that big of a deal as long as
                    # the failure will be handled gracefully.
            else:
                m = _lineNumberScanOpen.search(line)
                if m is not None:
                    openFeature = m.group(2)
                    openFeatureStart = characterCounter
            characterCounter += lineLength + 1
        # if a feature is left open, politely close it
        if openFeature:
            ranges.append((openFeature, openFeatureStart))
        # set the pop up
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
        if self._wrapLines == value:
            return
        self._wrapLines = value
        self._nsObject.setHasHorizontalScroller_(True)
        self._textView.setHorizontallyResizable_(not value)
        height = height = self._textView.maxSize()[1]
        if value:
            width = self._nsObject.contentView().bounds().size[0]
        else:
            width = height
        self._textView.setMaxSize_((width, height))
        self._textView.textContainer().setWidthTracksTextView_(value)
        self._textView.textContainer().setContainerSize_((width, height))

    def getWrapLines(self):
        """
        Boolean representing if the lines are soft wrapped or not.
        """
        return self._wrapLines

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
        self._classColor = value
        self._highlightSyntax(0, self.get())

    def getClassColor(self):
        return self._classColor

    def setIncludeColor(self, value):
        self._includeColor = value
        self._highlightSyntax(0, self.get())

    def getIncludeColor(self):
        return self._includeColor

