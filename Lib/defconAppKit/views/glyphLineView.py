import weakref
import time
from Foundation import *
from AppKit import *
import vanilla
from defconAppKit.notificationObserver import NSObjectNotificationObserver


class DefconAppKitGlyphLineNSView(NSView):

    def init(self):
        self = super(DefconAppKitGlyphLineNSView, self).init()
        self._glyphs = []
        self._notificationObserver = NSObjectNotificationObserver()

        self._pointSize = 150
        self._scale = 1.0
        self._upm = 1000
        self._descender = -250
        self._buffer = 15
        self._applyKerning = True

        self._fitToFrame = None

        self._backgroundColor = NSColor.whiteColor()
        self._glyphColor = NSColor.blackColor()
        return self

    # --------------
    # custom methods
    # --------------

    def setGlyphs_(self, glyphs):
        self._unsubscribeFromGlyphsAndKerning()
        self._glyphs = glyphs
        self._subscribeToGlyphsAndKerning()
        self.recalculateFrame()

    def setPointSize_(self, pointSize):
        self._pointSize = pointSize
        self.recalculateFrame()

    def setGlyphColor_(self, color):
        self._glyphColor = color
        self.setNeedsDisplay_(True)

    def setBackgroundColor_(self, color):
        self._backgroundColor = color
        self.setNeedsDisplay_(True)

    def setApplyKerning_(self, value):
        self._applyKerning = value
        self.recalculateFrame()

    def setAllowsDrop_(self, value):
        if value:
            self.registerForDraggedTypes_(["DefconAppKitGlyphPboardType"])
        else:
            self.unregisterDraggedTypes()

    def recalculateFrame(self):
        if self.superview() is None:
            return
        self._calcScale()
        self._setFrame()

    def _calcScale(self):
        if self._pointSize is None:
            w, h = self.superview().visibleRect()[1]
            fitH = h - (self._buffer * 2)
            self._scale = fitH / self._upm
        else:
            self._scale = self._pointSize / float(self._upm)
        if self._scale < 0:
            self._scale = 0

    def _setFrame(self):
        scrollHeight = None
        scrollWidth = None
        if self.superview():
            scrollWidth, scrollHeight = self.superview().bounds()[1]
        if not self._glyphs:
            width = 0
        else:
            width = 0
            previousGlyph = None
            previousFont = None
            for glyph in self._glyphs:
                kerning = 0
                if self._applyKerning:
                    font = glyph.getParent()
                    if previousGlyph is not None and font is not None and (previousFont == font):
                        kerning = font.kerning.get((previousGlyph.name, glyph.name))
                    previousGlyph = glyph
                    previousFont = font
                width += glyph.width + kerning
            width = width * self._scale
        width += self._buffer * 2

        if scrollHeight is None:
            height = (self._unitsPerEm - self._descender) * scale
        else:
            height = scrollHeight
        if scrollWidth > width:
            width = scrollWidth

        self.setFrame_(((0, 0), (width, height)))
        self.setNeedsDisplay_(True)
        self._fitToFrame = self.superview().bounds()

    # glyph change notification support

    def _subscribeToGlyphsAndKerning(self):
        fonts = set()
        for glyph in self._glyphs:
            self._notificationObserver.add(self, "_glyphChanged", glyph, "Glyph.Changed")
            font = glyph.getParent()
            fonts.add(font)
        for font in fonts:
            kerning = font.kerning
            if kerning is not None:
                self._notificationObserver.add(self, "_kerningChanged", kerning, "Kerning.Changed")

    def _unsubscribeFromGlyphsAndKerning(self):
        fonts = set()
        glyphs = set()
        for glyph in self._glyphs:
            if glyph in glyphs:
                continue
            self._notificationObserver.remove(self, glyph, "Glyph.Changed")
            glyphs.add(glyph)
            font = glyph.getParent()
            fonts.add(font)
        for font in fonts:
            kerning = font.kerning
            if kerning is not None:
                self._notificationObserver.remove(self, kerning, "Kerning.Changed")

    def _glyphChanged(self, notification):
        self.recalculateFrame()

    def _kerningChanged(self, notification):
        self.recalculateFrame()

    # window resize notification support

    def viewDidEndLiveResize(self):
        self.recalculateFrame()

    def viewDidMoveToWindow(self):
        self.recalculateFrame()

    # --------------
    # NSView methods
    # --------------

    def dealloc(self):
        self._unsubscribeFromGlyphsAndKerning()
        super(DefconAppKitGlyphLineNSView, self).dealloc()

    def isFlipped(self):
        return True

    def isOpaque(self):
        return True

    def drawRect_(self, rect):
        needCalc = False
        if self.superview() and self._fitToFrame != self.superview().bounds():
            needCalc = True
        if self.inLiveResize() and self._pointSize is None:
            needCalc = True
        if needCalc:
            self.recalculateFrame()

        bounds = self.bounds()
        self._backgroundColor.set()
        NSRectFill(bounds)

        scale = self._scale
        descender = self._descender
        upm = self._upm
        buffer = self._buffer

        transform = NSAffineTransform.transform()

        transform.translateXBy_yBy_(buffer, buffer)
        transform.concat()

        transform = NSAffineTransform.transform()
        transform.scaleBy_(scale)
        transform.translateXBy_yBy_(0, descender)
        transform.concat()

        flipTransform = NSAffineTransform.transform()
        flipTransform.translateXBy_yBy_(0, upm)
        flipTransform.scaleXBy_yBy_(1.0, -1.0)
        flipTransform.concat()

        left = buffer
        bottom = buffer
        height = upm * scale

        self._glyphColor.set()

        previousGlyph = None
        previousFont = None
        for glyph in self._glyphs:
            kerning = 0
            if self._applyKerning:
                font = glyph.getParent()
                if previousGlyph is not None and font is not None and (previousFont == font):
                    kerning = font.kerning.get((previousGlyph.name, glyph.name))
                previousGlyph = glyph
                previousFont = font
            if kerning:
                transform = NSAffineTransform.transform()
                transform.translateXBy_yBy_(kerning, 0)
                transform.concat()

            path = glyph.getRepresentation("NSBezierPath")
            path.fill()

            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(glyph.width, 0)
            transform.concat()

    # -------------
    # Drag and Drop
    # -------------

    # drop

    def draggingEntered_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        return NSDragOperationCopy

    def draggingUpdated_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        return NSDragOperationCopy

    def draggingExited_(self, sender):
        return None

    def prepareForDragOperation_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        glyphs = source.getGlyphsFromDraggingInfo_(sender)
        return self.vanillaWrapper()._proposeDrop(glyphs, testing=True)

    def performDragOperation_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        glyphs = source.getGlyphsFromDraggingInfo_(sender)
        return self.vanillaWrapper()._proposeDrop(glyphs, testing=False)


class GlyphLineView(vanilla.ScrollView):

    def __init__(self, posSize, pointSize=100, applyKerning=True, glyphColor=None, backgroundColor=None, dropCallback=None, autohideScrollers=True):
        if glyphColor is None:
            glyphColor = NSColor.blackColor()
        if backgroundColor is None:
            backgroundColor = NSColor.whiteColor()
        self._glyphLineView = DefconAppKitGlyphLineNSView.alloc().init()
        self._glyphLineView.setPointSize_(pointSize)
        self._glyphLineView.setApplyKerning_(applyKerning)
        self._glyphLineView.setGlyphColor_(glyphColor)
        self._glyphLineView.setBackgroundColor_(backgroundColor)
        self._glyphLineView.setAllowsDrop_(dropCallback is not None)
        self._dropCallback = dropCallback
        self._glyphLineView.vanillaWrapper = weakref.ref(self)
        super(GlyphLineView, self).__init__(posSize, self._glyphLineView, autohidesScrollers=autohideScrollers, backgroundColor=backgroundColor)

    def _breakCycles(self):
        if hasattr(self, "_glyphLineView"):
            del self._glyphLineView.vanillaWrapper
            del self._glyphLineView
        super(GlyphLineView, self)._breakCycles()

    def _proposeDrop(self, glyphs, testing):
        if self._dropCallback is not None:
            return self._dropCallback(self, glyphs, testing)
        return False

    def set(self, glyphs):
        self._glyphLineView.setGlyphs_(glyphs)

    def setPointSize(self, pointSize):
        self._glyphLineView.setPointSize_(pointSize)

    def setGlyphColor(self, color):
        self._glyphLineView.setGlyphColor_(color)

    def setBackgroundColor(self, color):
        self.setBackgroundColor(color)
        self._glyphLineView.setBackgroundColor_(color)

