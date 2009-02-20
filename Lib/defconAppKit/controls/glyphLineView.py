import weakref
import time
from Foundation import *
from AppKit import *
import vanilla
from defconAppKit.controls.placardScrollView import PlacardScrollView, PlacardPopUpButton


defaultAlternateHighlightColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.45, 0.50, 0.55, 1.0)


class DefconAppKitGlyphLineNSView(NSView):

    def init(self):
        self = super(DefconAppKitGlyphLineNSView, self).init()
        self._glyphRecords = []
        self._alternateRects = {}

        self._rightToLeft = False
        self._pointSize = 150
        self._scale = 1.0
        self._upm = 1000
        self._descender = -250
        self._buffer = 15

        self._fitToFrame = None

        self._backgroundColor = NSColor.whiteColor()
        self._glyphColor = NSColor.blackColor()
        self._alternateHighlightColor = defaultAlternateHighlightColor
        self._notdefBackgroundColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 0, 0, .25)
        return self

    # --------------
    # Custom Methods
    # --------------

    def setGlyphRecords_(self, glyphRecords):
        self._glyphRecords = glyphRecords
        upms = []
        descenders = []
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            font = glyph.getParent()
            if font is not None:
                upm = font.info.unitsPerEm
                if upm is not None:
                    upms.append(upm)
                descender = font.info.descender
                if descender is not None:
                    descenders.append(descender)
        if upms:
            self._upm = max(upms)
        if descenders:
            self._descender = min(descenders)
        self.recalculateFrame()

    def getGlyphRecords(self):
        return list(self._glyphRecords)

    def setPointSize_(self, pointSize):
        self._pointSize = pointSize
        self.recalculateFrame()

    def setRightToLeft_(self, value):
        self._rightToLeft = value
        self.recalculateFrame()

    def setGlyphColor_(self, color):
        self._glyphColor = color
        self.setNeedsDisplay_(True)

    def setBackgroundColor_(self, color):
        self._backgroundColor = color
        self.setNeedsDisplay_(True)

    def setAlternateHighlightColor_(self, color):
        self._alternateHighlightColor = color
        self.setNeedsDisplay_(True)

    def setAllowsDrop_(self, value):
        if value:
            self.registerForDraggedTypes_(["DefconAppKitGlyphPboardType"])
        else:
            self.unregisterDraggedTypes()

    # ----------------
    # Frame Management
    # ----------------

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
        if not self._glyphRecords:
            width = 0
        else:
            width = 0
            for glyphRecord in self._glyphRecords:
                width += (glyphRecord.glyph.width + glyphRecord.xPlacement + glyphRecord.xAdvance) * self._scale
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

    # window resize notification support

    def viewDidEndLiveResize(self):
        self.recalculateFrame()

    def viewDidMoveToWindow(self):
        self.recalculateFrame()

    # -----------------------------
    # NSMenu creation and retrieval
    # -----------------------------

    def _makeMenuForGlyphRecord(self, index):
        glyphRecord = self._glyphRecords[index]
        glyph = glyphRecord.glyph
        font = glyph.getParent()
        if font is None:
            return None
        menu = NSMenu.alloc().init()
        for alternateName in glyphRecord.alternates:
            alternate = font[alternateName]
            item = self._getGlyphMenuItem(alternate)
            menu.addItem_(item)
        return menu

    def _getGlyphMenuItem(self, glyph):
        name = glyph.name
        menuItem = NSMenuItem.alloc().init()
        image = glyph.getRepresentation("defconAppKit.MenuImage")
        menuItem.setImage_(image)
        menuItem.setTitle_(name)
        menuItem.setTarget_(self)
        menuItem.setAction_("_dummyAction:")
        return menuItem

    def _dummyAction_(self, sender):
        pass

    # --------------
    # NSView Methods
    # --------------

    def isFlipped(self):
        return True

    def isOpaque(self):
        return True

    def menuForEvent_(self, event):
        eventLocation = event.locationInWindow()
        eventLocation = self.convertPoint_fromView_(eventLocation, None)
        for rect, recordIndex in self._alternateRects.items():
            if NSPointInRect(eventLocation, rect):
                menu = self._makeMenuForGlyphRecord(recordIndex)
                if menu is not None:
                    return menu
        return super(GlyphLineView, self).menuForEvent_(event)

    def drawRect_(self, rect):
        needCalc = False
        if self.superview() and self._fitToFrame != self.superview().bounds():
            needCalc = True
        if self.inLiveResize() and self._pointSize is None:
            needCalc = True
        if needCalc:
            self._calcScale()
        if self._rightToLeft:
            self.drawRectRightToLeft_(rect)
        else:
            self.drawRectLeftToRight_(rect)

    def drawRectLeftToRight_(self, rect):
        self._alternateRects = {}
        # draw the background
        bounds = self.bounds()
        self._backgroundColor.set()
        NSRectFill(bounds)
        # create some reusable values
        scale = self._scale
        descender = self._descender
        upm = self._upm
        scaledBuffer = self._buffer * (1.0 / scale)
        # offset for the buffer
        ctx = NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()
        aT = NSAffineTransform.transform()
        aT.translateXBy_yBy_(self._buffer, self._buffer)
        aT.concat()
        # offset for the descender
        aT = NSAffineTransform.transform()
        aT.scaleBy_(scale)
        aT.translateXBy_yBy_(0, descender)
        aT.concat()
        # flip
        flipTransform = NSAffineTransform.transform()
        flipTransform.translateXBy_yBy_(0, upm)
        flipTransform.scaleXBy_yBy_(1.0, -1.0)
        flipTransform.concat()
        # set the glyph color
        self._glyphColor.set()
        # draw the records
        left = self._buffer
        bottom = self._buffer
        height = upm * scale
        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            glyph = glyphRecord.glyph
            w = glyphRecord.advanceWidth
            h = glyphRecord.advanceHeight
            xP = glyphRecord.xPlacement
            yP = glyphRecord.yPlacement
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            path = glyph.getRepresentation("defconAppKit.NSBezierPath")
            # handle offsets from the record
            bottom += yP * scale
            glyphHeight = height + ((h + yA) * scale)
            glyphLeft = left + (xP * scale)
            glyphWidth = (w + xA) * scale
            # store the glyph rect for the alternate menu
            rect = ((glyphLeft, bottom), (glyphWidth, glyphHeight))
            self._alternateRects[rect] = recordIndex
            # fill the glyph rect if glyph glyph is .notdef
            if glyph.name == ".notdef":
                self._notdefBackgroundColor.set()
                rect = ((0, descender), (w, upm))
                NSRectFillUsingOperation(rect, NSCompositeSourceOver)
                self._glyphColor.set()
            # handle the placement offset
            if xP or yP:
                aT = NSAffineTransform.transform()
                aT.translateXBy_yBy_(xP, yP)
                aT.concat()
            # fill the path, highlighting alternates
            # if necessary
            if glyphRecord.alternates:
                self._alternateHighlightColor.set()
                path.fill()
                self._glyphColor.set()
            else:
                path.fill()
            # shift for the next glyph
            aT = NSAffineTransform.transform()
            aT.translateXBy_yBy_(w + xA - xP, h + yA - yP)
            aT.concat()
            left += glyphWidth
        ctx.restoreGraphicsState()

    def drawRectRightToLeft_(self, rect):
        self._alternateRects = {}
        # draw the background
        bounds = self.bounds()
        self._backgroundColor.set()
        NSRectFill(bounds)
        # create some reusable values
        scale = self._scale
        descender = self._descender
        upm = self._upm
        scaledBuffer = self._buffer * (1.0 / scale)
        scrollWidth = bounds.size[0]
        # offset for the buffer
        ctx = NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()
        aT = NSAffineTransform.transform()
        aT.translateXBy_yBy_(scrollWidth - self._buffer, self._buffer)
        aT.concat()
        # offset for the descender
        aT = NSAffineTransform.transform()
        aT.scaleBy_(scale)
        aT.translateXBy_yBy_(0, descender)
        aT.concat()
        # flip
        flipTransform = NSAffineTransform.transform()
        flipTransform.translateXBy_yBy_(0, upm)
        flipTransform.scaleXBy_yBy_(1.0, -1.0)
        flipTransform.concat()
        # set the glyph color
        self._glyphColor.set()
        # draw the records
        left = scrollWidth - self._buffer
        bottom = self._buffer
        height = upm * scale
        previousXA = 0
        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            glyph = glyphRecord.glyph
            w = glyphRecord.advanceWidth
            h = glyphRecord.advanceHeight
            xP = glyphRecord.xPlacement
            yP = glyphRecord.yPlacement
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            path = glyph.getRepresentation("defconAppKit.NSBezierPath")
            # handle offsets from the record
            bottom += yP * scale
            glyphHeight = height + ((h + yA) * scale)
            glyphLeft = left + ((-w + xP - xA) * scale)
            glyphWidth = (-w - xA) * scale
            # store the glyph rect for the alternate menu
            rect = ((glyphLeft, bottom), (glyphWidth, glyphHeight))
            self._alternateRects[rect] = recordIndex
            # fill the glyph rect if glyph glyph is .notdef
            if glyph.name == ".notdef":
                self._notdefBackgroundColor.set()
                rect = ((-w, descender), (w, upm))
                NSRectFillUsingOperation(rect, NSCompositeSourceOver)
                self._glyphColor.set()
            # shift into place and draw the glyph
            aT = NSAffineTransform.transform()
            if xP:
                xP += previousXA
            aT.translateXBy_yBy_(-w - xA + xP, yP)
            aT.concat()
            # fill the path, highlighting alternates
            # if necessary
            if glyphRecord.alternates:
                self._alternateHighlightColor.set()
                path.fill()
                self._glyphColor.set()
            else:
                path.fill()
            # shift for the next glyph
            aT = NSAffineTransform.transform()
            aT.translateXBy_yBy_(-xP, h + yA - yP)
            aT.concat()
            left += (-w - xP - xA) * scale
            previousXA = xA
        ctx.restoreGraphicsState()

#    # -------------
#    # Drag and Drop
#    # -------------
#
#    # this all needs to be rebuilt
#
#    def draggingEntered_(self, sender):
#        source = sender.draggingSource()
#        if source == self:
#            return NSDragOperationNone
#        return NSDragOperationCopy
#
#    def draggingUpdated_(self, sender):
#        source = sender.draggingSource()
#        if source == self:
#            return NSDragOperationNone
#        return NSDragOperationCopy
#
#    def draggingExited_(self, sender):
#        return None
#
#    def prepareForDragOperation_(self, sender):
#        source = sender.draggingSource()
#        if source == self:
#            return NSDragOperationNone
#        glyphs = source.getGlyphsFromDraggingInfo_(sender)
#        return self.vanillaWrapper()._proposeDrop(glyphs, testing=True)
#
#    def performDragOperation_(self, sender):
#        source = sender.draggingSource()
#        if source == self:
#            return NSDragOperationNone
#        glyphs = source.getGlyphsFromDraggingInfo_(sender)
#        return self.vanillaWrapper()._proposeDrop(glyphs, testing=False)


pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]


class GlyphLineView(PlacardScrollView):

    def __init__(self, posSize, pointSize=100, rightToLeft=False, applyKerning=False,
        glyphColor=None, backgroundColor=None, alternateHighlightColor=None,
        autohideScrollers=True, showPointSizePlacard=False):
        if glyphColor is None:
            glyphColor = NSColor.blackColor()
        if backgroundColor is None:
            backgroundColor = NSColor.whiteColor()
        if alternateHighlightColor is None:
            alternateHighlightColor = defaultAlternateHighlightColor
        self._applyKerning = applyKerning
        self._glyphLineView = DefconAppKitGlyphLineNSView.alloc().init()
        self._glyphLineView.setPointSize_(pointSize)
        self._glyphLineView.setRightToLeft_(rightToLeft)
        self._glyphLineView.setGlyphColor_(glyphColor)
        self._glyphLineView.setBackgroundColor_(backgroundColor)
        self._glyphLineView.setAlternateHighlightColor_(alternateHighlightColor)
        self._glyphLineView.vanillaWrapper = weakref.ref(self)
        # don't autohide if the placard is to be visible.
        # bad things will happen if this is not the case.
        if showPointSizePlacard:
            autohideScrollers = False
        # setup the scroll view
        super(GlyphLineView, self).__init__(posSize, self._glyphLineView, autohidesScrollers=autohideScrollers, backgroundColor=backgroundColor)
        # placard
        if showPointSizePlacard:
            self._pointSizes = ["Auto"] + [str(i) for i in pointSizes]
            placardW = 55
            placardH = 16
            self._placard = vanilla.Group((0, 0, placardW, placardH))
            self._placard.button = PlacardPopUpButton((0, 0, placardW, placardH),
                self._pointSizes, callback=self._placardSelection, sizeStyle="mini")
            self.setPlacard(self._placard)
            pointSize = str(pointSize)
            if pointSize in self._pointSizes:
                index = self._pointSizes.index(pointSize)
                self._placard.button.set(index)

    def _breakCycles(self):
        if hasattr(self, "_glyphLineView"):
            self._unsubscribeFromGlyphs()
            del self._glyphLineView.vanillaWrapper
            del self._glyphLineView
        super(GlyphLineView, self)._breakCycles()

    # -------
    # Placard
    # -------

    def _placardSelection(self, sender):
        value = self._pointSizes[sender.get()]
        if value == "Auto":
            value = None
        else:
            value = int(value)
        print value, sender.get()
        self.setPointSize(value)

#    # ----
#    # Drop
#    # ----
#
#    def _proposeDrop(self, glyphs, testing):
#        if self._dropCallback is not None:
#            return self._dropCallback(self, glyphs, testing)
#        return False

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyphs(self, glyphRecords):
        handledGlyphs = set()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            if self._applyKerning:
                font = glyph.getParent()
                if font is not None and not font.kerning.hasObserver(self, "Kerning.Changed"):
                    font.kerning.addObserver(self, "_kerningChanged", "Kerning.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        glyphRecords = self._glyphLineView.getGlyphRecords()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")
            if self._applyKerning:
                font = glyph.getParent()
                if font is not None and font.kerning.hasObserver(self, "Kerning.Changed"):
                    font.kerning.removeObserver(self, "Kerning.Changed")

    def _glyphChanged(self, notification):
        self._glyphLineView.setNeedsDisplay_(True)

    def _kerningChanged(self, notification):
        glyphRecords = self._glyphLineView.getGlyphRecords()
        self._setKerningInGlyphRecords(glyphRecords)
        self._glyphLineView.setNeedsDisplay_(True)

    # ---------------
    # Kerning Support
    # ---------------

    def _setKerningInGlyphRecords(self, glyphRecords):
        previousGlyph = None
        previousFont = None
        for index, glyphRecord in enumerate(glyphRecords):
            glyph = glyphRecord.glyph
            font = glyph.getParent()
            if previousGlyph is not None and font is not None and (previousFont == font):
                kern = font.kerning.get((previousGlyph.name, glyph.name))
                if kern is None:
                    kern = 0
                glyphRecords[index - 1].xAdvance = kern
            previousGlyph = glyph
            previousFont = font

    # ------------
    # External API
    # ------------

    def set(self, glyphs):
        # unsubscribe from the old glyphs
        self._unsubscribeFromGlyphs()
        # test to see if glyph records are present
        needToWrap = False
        if glyphs:
            for attr in ("glyph", "xPlacement", "yPlacement", "xAdvance", "yAdvance", "alternates"):
                if not hasattr(glyphs[0], attr):
                    needToWrap = True
                    break
        # wrap into glyph records if necessary
        if needToWrap:
            glyphRecords = []
            for glyph in glyphs:
                glyphRecord = GlyphRecord()
                glyphRecord.glyph = glyph
                glyphRecord.advanceWidth = glyph.width
                glyphRecords.append(glyphRecord)
            # apply kerning as needed
            if self._applyKerning:
                self._setKerningInGlyphRecords(glyphRecords)
        else:
            glyphRecords = glyphs
        # set the records into the view
        self._glyphLineView.setGlyphRecords_(glyphRecords)
        # subscribe to the new glyphs
        self._subscribeToGlyphs(glyphRecords)

    def setPointSize(self, pointSize):
        self._glyphLineView.setPointSize_(pointSize)

    def setRightToLeft(self, value):
        self._glyphLineView.setRightToLeft_(value)

    def setGlyphColor(self, color):
        self._glyphLineView.setGlyphColor_(color)

    def setBackgroundColor(self, color):
        self.setBackgroundColor(color)
        self._glyphLineView.setBackgroundColor_(color)


# ------------------
# Basic Glyph Record
# ------------------

class GlyphRecord(object):

    __slots__ = ["glyph", "xPlacement", "yPlacement", "xAdvance", "yAdvance", "advanceWidth", "advanceHeight", "alternates"]

    def __init__(self):
        self.glyph = None
        self.xPlacement = 0
        self.yPlacement = 0
        self.xAdvance = 0
        self.yAdvance = 0
        self.advanceWidth = 0
        self.advanceHeight = 0
        self.alternates = []

