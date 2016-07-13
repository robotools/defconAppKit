import weakref
import time
from Foundation import *
from AppKit import *
import vanilla
from defconAppKit.controls.placardScrollView import PlacardScrollView, PlacardPopUpButton, DefconAppKitPlacardNSScrollView
from defconAppKit.tools import drawing


defaultAlternateHighlightColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.45, 0.50, 0.55, 1.0)


class DefconAppKitGlyphLineNSView(NSView):

    def init(self):
        self = super(DefconAppKitGlyphLineNSView, self).init()

        self._showLayers = False
        self._layerDrawingAttributes = {}
        self._fallbackDrawingAttributes = dict(
            showGlyphFill=True,
            showGlyphStroke=False,
            showGlyphOnCurvePoints=False,
            showGlyphStartPoints=False,
            showGlyphOffCurvePoints=False,
            showGlyphPointCoordinates=False,
            showGlyphAnchors=False,
            showGlyphImage=False,
            showGlyphMargins=False,
            showFontVerticalMetrics=False,
            showFontPostscriptBlues=False,
            showFontPostscriptFamilyBlues=False
        )

        self._glyphRecords = []
        self._alternateRects = {}
        self._currentZeroZeroPoint = NSPoint(0, 0)

        self._rightToLeft = False
        self._pointSize = 150
        self._impliedPointSize = 150
        self._scale = 1.0
        self._inverseScale = 0.1
        self._upm = 1000
        self._descender = -250
        self._bufferLeft = self._bufferRight = self._bufferBottom = self._bufferTop = 15

        self._fitToFrame = None

        self._backgroundColor = NSColor.whiteColor()
        self._glyphColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1)
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
        self.setShowLayers_(self._showLayers)

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

    def setShowLayers_(self, value):
        self._layerDrawingAttributes = {}
        self._showLayers = value
        if value:
            for record in self._glyphRecords:
                glyph = record.glyph
                layerSet = glyph.layerSet
                if layerSet is not None:
                    for layerName in layerSet.layerOrder:
                        self._layerDrawingAttributes[layerName] = dict(showGlyphFill=True)
        self.setNeedsDisplay_(True)

    def setDrawingAttribute_value_layerName_(self, attr, value, layerName):
        if layerName is None:
            self._fallbackDrawingAttributes[attr] = value
        else:
            if layerName not in self._layerDrawingAttributes:
                self._layerDrawingAttributes[layerName] = {}
            self._layerDrawingAttributes[layerName][attr] = value
        self.setNeedsDisplay_(True)

    def getDrawingAttribute_layerName_(self, attr, layerName):
        if layerName is None:
            return self._fallbackDrawingAttributes.get(attr)
        d = self._layerDrawingAttributes.get(layerName, {})
        return d.get(attr)

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
            fitH = h - self._bufferBottom - self._bufferTop
            self._scale = fitH / self._upm
        else:
            self._scale = self._pointSize / float(self._upm)
        if self._scale < .01:
            self._scale = 0.01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._upm * self._scale

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
        width += self._bufferLeft + self._bufferRight

        if scrollHeight is None:
            height = (self._unitsPerEm - self._descender) * scale
        else:
            height = scrollHeight
        if scrollWidth > width:
            width = scrollWidth

        self.setFrame_(((0, 0), (width, height)))
        self.setNeedsDisplay_(True)
        self._fitToFrame = self.superview().bounds()

    def needsToDrawRectInGlyphSpace_scale_(self, rect, scale=None):
        if scale is None:
            scale = self._scale
        (x, y), (w, h) = rect
        x *= scale
        y *= -scale
        x += self._currentZeroZeroPoint.x
        y += self._currentZeroZeroPoint.y
        w *= scale
        h *= scale
        y -= h
        return self.needsToDrawRect_(((x, y), (w, h)))

    def needsToDrawPointInGlyphSpace_scale_(self, (x, y), scale=None):
        if scale is None:
            scale = self._scale
        b = 20
        x *= scale
        y *= -scale
        x += self._currentZeroZeroPoint.x - b
        y += self._currentZeroZeroPoint.y - b
        w = b * 2
        h = b * 2
        return self.needsToDrawRect_(((x, y), (w, h)))

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

    # -------------
    # glyph drawing
    # -------------

    def drawGlyph(self, glyph, rect, alternate=False):
        # gather the layers
        layerSet = glyph.layerSet
        if layerSet is None or not self._showLayers:
            layers = [(glyph, None)]
        else:
            glyphName = glyph.name
            layers = []
            for layerName in reversed(layerSet.layerOrder):
                layer = layerSet[layerName]
                if glyphName not in layer:
                    continue
                g = layer[glyphName]
                if g == glyph:
                    layerName = None
                layers.append((g, layerName))

        self.drawGlyphBackground(glyph, rect, alternate=alternate)
        if self.needsToDrawRectInGlyphSpace_scale_(rect):
            for g, layerName in layers:
                # draw the image
                if self.getDrawingAttribute_layerName_("showGlyphImage", layerName):
                    self.drawImage(g, layerName, rect)
                # draw the blues
                if layerName is None and self.getDrawingAttribute_layerName_("showFontPostscriptBlues", None):
                    self.drawBlues(g, layerName, rect)
                if layerName is None and self.getDrawingAttribute_layerName_("showFontPostscriptFamilyBlues", None):
                    self.drawFamilyBlues(g, layerName, rect)
                # draw the margins
                if self.getDrawingAttribute_layerName_("showGlyphMargins", layerName):
                    self.drawMargins(g, layerName, rect)
                # draw the vertical metrics
                if layerName is None and self.getDrawingAttribute_layerName_("showFontVerticalMetrics", None):
                    self.drawVerticalMetrics(g, layerName, rect)
                # draw the glyph
                if self.getDrawingAttribute_layerName_("showGlyphFill", layerName) or self.getDrawingAttribute_layerName_("showGlyphStroke", layerName):
                    self.drawFillAndStroke(g, layerName, rect)
                if self.getDrawingAttribute_layerName_("showGlyphOnCurvePoints", layerName) or self.getDrawingAttribute_layerName_("showGlyphOffCurvePoints", layerName):
                    self.drawPoints(g, layerName, rect)
                if self.getDrawingAttribute_layerName_("showGlyphAnchors", layerName):
                    self.drawAnchors(g, layerName, rect)

        self.drawGlyphForeground(glyph, rect, alternate=alternate)

    def drawGlyphBackground(self, glyph, rect, alternate=False):
        if self.needsToDrawRectInGlyphSpace_scale_(rect):
            if glyph.name == ".notdef":
                self._notdefBackgroundColor.set()
                NSRectFillUsingOperation(rect, NSCompositeSourceOver)
            if alternate:
                self._alternateHighlightColor.set()
                NSRectFillUsingOperation(rect, NSCompositeSourceOver)

    def drawImage(self, glyph, layerName, rect):
        drawing.drawGlyphImage(glyph, self._inverseScale, rect, backgroundColor=self._backgroundColor)

    def drawBlues(self, glyph, layerName, rect):
        drawing.drawFontPostscriptBlues(glyph, self._inverseScale, rect, backgroundColor=self._backgroundColor)

    def drawFamilyBlues(self, glyph, layerName, rect):
        drawing.drawFontPostscriptFamilyBlues(glyph, self._inverseScale, rect, backgroundColor=self._backgroundColor)

    def drawVerticalMetrics(self, glyph, layerName, rect):
        drawText = self.getDrawingAttribute_layerName_("showFontVerticalMetricsTitles", layerName) and self._impliedPointSize > 150
        drawing.drawFontVerticalMetrics(glyph, self._inverseScale, rect, drawText=drawText, backgroundColor=self._backgroundColor, flipped=True)

    def drawMargins(self, glyph, layerName, rect):
        drawing.drawGlyphMargins(glyph, self._inverseScale, rect, backgroundColor=self._backgroundColor)

    def drawFillAndStroke(self, glyph, layerName, rect):
        showFill = self.getDrawingAttribute_layerName_("showGlyphFill", layerName)
        showStroke = self.getDrawingAttribute_layerName_("showGlyphStroke", layerName)
        fillColor = None
        if not self._showLayers:
            fillColor = self._glyphColor
        drawing.drawGlyphFillAndStroke(glyph, self._inverseScale, rect, drawFill=showFill, drawStroke=showStroke, contourFillColor=fillColor, componentFillColor=fillColor, backgroundColor=self._backgroundColor)

    def drawPoints(self, glyph, layerName, rect):
        drawStartPoint = self.getDrawingAttribute_layerName_("showGlyphStartPoints", layerName) and self._impliedPointSize > 175
        drawOnCurves = self.getDrawingAttribute_layerName_("showGlyphOnCurvePoints", layerName) and self._impliedPointSize > 175
        drawOffCurves = self.getDrawingAttribute_layerName_("showGlyphOffCurvePoints", layerName) and self._impliedPointSize > 175
        drawCoordinates = self.getDrawingAttribute_layerName_("showGlyphPointCoordinates", layerName) and self._impliedPointSize > 250
        drawing.drawGlyphPoints(glyph, self._inverseScale, rect,
            drawStartPoint=drawStartPoint, drawOnCurves=drawOnCurves, drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=self._backgroundColor, flipped=True)

    def drawAnchors(self, glyph, layerName, rect):
        drawText = self._impliedPointSize > 50
        drawing.drawGlyphAnchors(glyph, self._inverseScale, rect, drawText=drawText, backgroundColor=self._backgroundColor, flipped=True)

    def drawGlyphForeground(self, glyph, rect, alternate=False):
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
        return super(DefconAppKitGlyphLineNSView, self).menuForEvent_(event)

    def drawRect_(self, rect):
        w, h = self.frame().size
        if w == 0 or h == 0:
            return
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
        # offset for the buffer
        ctx = NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()
        aT = NSAffineTransform.transform()
        aT.translateXBy_yBy_(self._bufferLeft, self._bufferTop)
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
        height = upm * scale
        left = self._bufferLeft
        bottom = self._bufferTop

        for recordIndex, glyphRecord in enumerate(self._glyphRecords):
            glyph = glyphRecord.glyph
            w = glyphRecord.advanceWidth
            h = glyphRecord.advanceHeight
            xP = glyphRecord.xPlacement
            yP = glyphRecord.yPlacement
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            # handle offsets from the record
            bottom += yP * scale
            glyphHeight = height + ((h + yA) * scale)
            glyphLeft = left + (xP * scale)
            glyphWidth = (w + xA) * scale
            # store the glyph rect for the alternate menu
            rect = ((glyphLeft, bottom), (glyphWidth, glyphHeight))
            self._alternateRects[rect] = recordIndex
            self._currentZeroZeroPoint = NSPoint(glyphLeft, bottom + height + (descender * scale))
            # handle placement
            if xP or yP:
                aT = NSAffineTransform.transform()
                aT.translateXBy_yBy_(xP, yP)
                aT.concat()
            # draw the glyph
            rect = ((-xP, descender - yP), (w, upm))
            self.drawGlyph(glyph, rect, alternate=bool(glyphRecord.alternates))
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
        scrollWidth = bounds.size[0]
        # offset for the buffer
        ctx = NSGraphicsContext.currentContext()
        ctx.saveGraphicsState()
        aT = NSAffineTransform.transform()
        aT.translateXBy_yBy_(scrollWidth - self._bufferLeft, self._bufferTop)
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
        left = scrollWidth - self._bufferLeft
        bottom = self._bufferTop
        height = upm * scale
        previousXA = 0
        for recordIndex, glyphRecord in enumerate(reversed(self._glyphRecords)):
            glyph = glyphRecord.glyph
            w = glyphRecord.advanceWidth
            h = glyphRecord.advanceHeight
            xP = glyphRecord.xPlacement
            yP = glyphRecord.yPlacement
            xA = glyphRecord.xAdvance
            yA = glyphRecord.yAdvance
            # handle offsets from the record
            bottom += yP * scale
            glyphHeight = height + ((h + yA) * scale)
            glyphLeft = left + ((-w + xP - xA) * scale)
            glyphWidth = (-w - xA) * scale
            # store the glyph rect for the alternate menu
            rect = ((glyphLeft, bottom), (glyphWidth, glyphHeight))
            self._alternateRects[rect] = recordIndex
            self._currentZeroZeroPoint = NSPoint(glyphLeft, bottom + height + (descender * scale))
            # handle the placement
            aT = NSAffineTransform.transform()
            if xP:
                xP += previousXA
            aT.translateXBy_yBy_(-w - xA + xP, yP)
            aT.concat()
            # draw the glyph
            rect = ((-w + xA - xP, descender - yP), (w, upm))
            self.drawGlyph(glyph, rect, alternate=bool(glyphRecord.alternates))
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


class DefconAppKitGlyphLineViewNSScrollView(DefconAppKitPlacardNSScrollView):

    def setFrame_(self, frame):
        super(DefconAppKitGlyphLineViewNSScrollView, self).setFrame_(frame)
        documentView = self.documentView()
        if documentView is not None:
            documentView.recalculateFrame()


pointSizes = [50, 75, 100, 125, 150, 200, 250, 300, 350, 400, 450, 500]


class GlyphLineView(PlacardScrollView):

    nsScrollViewClass = DefconAppKitGlyphLineViewNSScrollView
    glyphLineViewClass = DefconAppKitGlyphLineNSView

    def __init__(self, posSize, pointSize=100, rightToLeft=False, applyKerning=False,
        glyphColor=None, backgroundColor=None, alternateHighlightColor=None,
        autohideScrollers=True, showPointSizePlacard=False):
        if glyphColor is None:
            glyphColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1)
        if backgroundColor is None:
            backgroundColor = NSColor.whiteColor()
        if alternateHighlightColor is None:
            alternateHighlightColor = defaultAlternateHighlightColor
        self._applyKerning = applyKerning
        self._glyphLineView = self.glyphLineViewClass.alloc().init()
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
        handledFonts = set()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.getParent()
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.addObserver(self, "_fontChanged", "Info.Changed")
            if self._applyKerning:
                font.kerning.addObserver(self, "_kerningChanged", "Kerning.Changed")

    def _unsubscribeFromGlyphs(self):
        handledGlyphs = set()
        handledFonts = set()
        glyphRecords = self._glyphLineView.getGlyphRecords()
        for glyphRecord in glyphRecords:
            glyph = glyphRecord.glyph
            if glyph in handledGlyphs:
                continue
            handledGlyphs.add(glyph)
            glyph.removeObserver(self, "Glyph.Changed")
            font = glyph.getParent()
            if font is None:
                continue
            if font in handledFonts:
                continue
            handledFonts.add(font)
            font.info.removeObserver(self, "Info.Changed")
            if self._applyKerning:
                font.kerning.removeObserver(self, "Kerning.Changed")

    def _glyphChanged(self, notification):
        self._glyphLineView.setNeedsDisplay_(True)

    def _kerningChanged(self, notification):
        glyphRecords = self._glyphLineView.getGlyphRecords()
        self._setKerningInGlyphRecords(glyphRecords)
        self._glyphLineView.setNeedsDisplay_(True)

    def _fontChanged(self, notification):
        glyphRecords = self._glyphLineView.getGlyphRecords()
        self._glyphLineView.setGlyphRecords_(glyphRecords)

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
        self._glyphLineView.setBackgroundColor_(color)

    def setShowLayers(self, value):
        self._glyphLineView.setShowLayers_(value)


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

