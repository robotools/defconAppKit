import weakref
import threading
from Foundation import *
from AppKit import *
import vanilla


class DefconAppKitNSTextView(NSTextView):

    def keyDown_(self, event):
        characters = event.charactersIgnoringModifiers()
        modifiers = event.modifierFlags()
        if characters == "/" and modifiers & NSAlternateKeyMask:
            self.vanillaWrapper().showInsertGlyphView()
        else:
            super(DefconAppKitNSTextView, self).keyDown_(event)


class GlyphMultilineView(vanilla.TextEditor):

    nsTextViewClass = DefconAppKitNSTextView

    def __init__(self, posSize, callback=None, applyKerning=True, glyphColor=None, backgroundColor=None):
        super(GlyphMultilineView, self).__init__(posSize, callback=callback)
        self._textView.turnOffLigatures_(None)
        if applyKerning:
            self._textView.useStandardKerning_(None)
        else:
            self._textView.turnOffKerning_(None)
        if glyphColor is not None:
            self._textView.setTextColor_(glyphColor)
        if backgroundColor is not None:
            self._textView.setBackgroundColor_(backgroundColor)
            self._nsObject.setBackgroundColor_(backgroundColor)
        self._font = None
        self._pointSize = 100

    def _updateTextView(self):
        manager = NSApp().delegate().OSFontBridgeManager()
        font = self._font()
        name = manager.getNameForFont(font)
        font = NSFont.fontWithName_size_(name, self._pointSize)
        self._textView.setFont_(font)
        self._reloadTimer = None

    def _fontReloaded(self, notification):
        if self._reloadTimer is not None:
            self._reloadTimer.cancel()
            self._reloadTimer = None
        self._reloadTimer = threading.Timer(.5, self._updateTextView)
        self._reloadTimer.start()

    def setFont(self, font):
        manager = NSApp().delegate().OSFontBridgeManager()
        # remove observation of the old font
        if self._font is not None:
            oldFont = self._font()
            manager.removeObserver(observer=self, font=oldFont)
        # observe new font
        manager.addObserver(observer=self, callbackString="_fontReloaded", font=font)
        # make a weakref to the font
        self._font = weakref.ref(font)
        # update the view
        self._updateTextView()

    def setPointSize(self, value):
        self._pointSize = value
        self._updateTextView()

    def set(self, text):
        pass

    def get(self):
        pass

    def showInsertGlyphView(self):
        # work out the center of the view in screen coordinates
        viewFrame = self._nsObject.frame()
        previous = self._nsObject
        while 1:
            s = previous.superview()
            if s is None:
                break
            else:
                viewFrame = s.convertRect_fromView_(viewFrame, previous)
                previous = s
        viewFramePosition, viewFrameSize = viewFrame
        window = self._nsObject.window()
        viewFramePosition = window.convertBaseToScreen_(viewFramePosition)
        viewFrame = (viewFramePosition, viewFrameSize)
        (sL, sB), (sW, sH) = NSScreen.mainScreen().frame()
        (vL, vB), (vW, vH) =  viewFrame
        vT = sH - vB - vH - 40
        w, h = self._nsObject.frame().size
        x = vL + (w / 2)
        y = vT + (h / 2)
        # open the view
        font = self._font()
        InsertGlyphView((x, y), font, self._insertGlyphResultCallback)

    def _insertGlyphResultCallback(self, glyphName):
        if glyphName is None:
            return
        uni = self._font().unicodeData.forcedUnicodeForGlyphName(glyphName)
        c = unichr(uni)
        self._textView.insertText_(c)


# ---------------------
# Glyph Insertion Panel
# ---------------------


import time
from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath
from glyphNameComboBox import GlyphNameComboBox
from glyphCollectionView import GlyphCollectionView


viewColor = NSColor.colorWithCalibratedWhite_alpha_(.9, .9)


class DefconAppKitGlyphInsertionNSWindow(NSPanel):

    def canBecomeKeyWindow(self):
        return True


class DefconAppKitGlyphInsertionBackgroundView(NSView):

    def drawRect_(self, rect):
        rect = self.bounds()
        path = roundedRectBezierPath(rect, 5)
        viewColor.set()
        path.fill()


class InsertGlyphView(vanilla.Window):

    nsWindowClass = DefconAppKitGlyphInsertionNSWindow
    nsWindowStyleMask = NSBorderlessWindowMask

    def __init__(self, center, font, callback, glyphSortDescriptors=None):
        self._font = font
        self._callback = callback

        # setup the window
        width = 352
        height = 300
        x, y = center
        x -= (width / 2)
        y -= (height / 2)
        posSize = (x, y, width, height)
        super(InsertGlyphView, self).__init__(posSize)
        self._window.setMovableByWindowBackground_(True)

        # set the background
        contentView = DefconAppKitGlyphInsertionBackgroundView.alloc().init()
        self._window.setContentView_(contentView)
        self._window.setAlphaValue_(0.0)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())

        # name entry
        self.glyphNameComboBox = GlyphNameComboBox((20, 20, -20, 22), font, callback=self.glyphNameEntryCallback)

        # collection view
        if glyphSortDescriptors is None:
            glyphSortDescriptors = [
                dict(type="alphabetical", allowPseudoUnicode=True),
                dict(type="category", allowPseudoUnicode=True),
                dict(type="unicode", allowPseudoUnicode=True),
                dict(type="script", allowPseudoUnicode=True),
                dict(type="suffix", allowPseudoUnicode=True),
                dict(type="decompositionBase", allowPseudoUnicode=True)
            ]
        glyphs = [font[glyphName] for glyphName in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.orderedGlyphNames = [glyph.name for glyph in glyphs]

        self.glyphCollectionView = GlyphCollectionView((20, 52, -20, -65), selectionCallback=self.glyphCollectionCallback)
        self.glyphCollectionView.setCellSize((42, 56))
        self.glyphCollectionView.setCellRepresentationArguments(drawHeader=True)
        self.glyphCollectionView.set(glyphs)

        # bottom
        self.bottomLine = vanilla.HorizontalLine((20, -55, -20, 1))
        self.cancelButton = vanilla.Button((-180, -40, 70, 20), "Cancel", callback=self.cancelCallback)
        self.cancelButton.bind(".", ["command"])
        self.applyButton = vanilla.Button((-100, -40, 70, 20), "Apply", callback=self.applyCallback)
        self.setDefaultButton(self.applyButton)

        self.bind("resigned key", self.finish)
        self.open()

        for i in xrange(5):
            a = i * .2
            self._window.setAlphaValue_(a)
            time.sleep(.02)
        self._window.setAlphaValue_(1.0)

    def finish(self, sender=None):
        for i in xrange(5):
            a = 1.0 - (i * .2)
            self._window.setAlphaValue_(a)
            time.sleep(.02)
        self._font = None
        self._callback = None
        self.close()

    def glyphNameEntryCallback(self, sender):
        glyphName = sender.get()
        selection = []
        if glyphName in self._font:
            index = self.orderedGlyphNames.index(glyphName)
            selection.append(index)
        self.glyphCollectionView.setSelection(selection)
        self.glyphCollectionView.scrollToSelection()

    def glyphCollectionCallback(self, sender):
        selection = sender.getSelection()
        if selection:
            index = selection[0]
            glyphName = self.orderedGlyphNames[index]
            self.glyphNameComboBox.set(glyphName)

    def cancelCallback(self, sender):
        self.finish()

    def applyCallback(self, sender):
        glyphName = self.glyphNameComboBox.get()
        if glyphName not in self._font:
            glyphName = None
        self._callback(glyphName)
        self.finish()
