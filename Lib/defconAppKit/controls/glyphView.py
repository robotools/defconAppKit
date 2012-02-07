from Foundation import *
from AppKit import *
from ufoLib.pointPen import AbstractPointPen
import vanilla
from defconAppKit.controls.placardScrollView import PlacardScrollView, PlacardPopUpButton
from defconAppKit.tools import drawing


class DefconAppKitGlyphNSView(NSView):

    def init(self):
        self = super(DefconAppKitGlyphNSView, self).init()
        self._glyph = None

        # drawing attributes
        self._layerDrawingAttributes = {}
        self._fallbackDrawingAttributes = dict(
            showGlyphFill=True,
            showGlyphStroke=True,
            showGlyphOnCurvePoints=True,
            showGlyphStartPoints=True,
            showGlyphOffCurvePoints=False,
            showGlyphPointCoordinates=False,
            showGlyphAnchors=True,
            showGlyphImage=False,
            showGlyphMargins=True,
            showFontVerticalMetrics=True,
            showFontVerticalMetricsTitles=True,
            showFontPostscriptBlues=False,
            showFontPostscriptFamilyBlues=False
        )

        # cached vertical metrics
        self._unitsPerEm = 1000
        self._descender = -250
        self._capHeight = 750
        self._ascender = 750

        # drawing data cache
        self._drawingRect = None
        self._fitToFrame = None
        self._scale = 1.0
        self._inverseScale = 0.1
        self._impliedPointSize = 1000

        # drawing calculation
        self._centerVertically = True
        self._centerHorizontally = True
        self._noPointSizePadding = 200
        self._verticalCenterYBuffer = 0

        self._backgroundColor = NSColor.whiteColor()

        return self

    # --------------
    # Custom Methods
    # --------------

    def recalculateFrame(self):
        self._calcScale()
        self._setFrame()
        self.setNeedsDisplay_(True)

    def _getGlyphWidthHeight(self):
        if self._glyph.bounds:
            left, bottom, right, top = self._glyph.bounds
        else:
            left = right = bottom = top = 0
        left = min((0, left))
        right = max((right, self._glyph.width))
        bottom = self._descender
        top = max((self._capHeight, self._ascender, self._unitsPerEm + self._descender))
        width = abs(left) + right
        height = -bottom + top
        return width, height

    def _calcScale(self):
        if self.superview() is None:
            return
        visibleHeight = self.superview().visibleRect().size[1]
        fitHeight = visibleHeight
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphHeight += self._noPointSizePadding * 2
        self._scale = fitHeight / glyphHeight
        if self._scale <= 0:
            self._scale = .01
        self._inverseScale = 1.0 / self._scale
        self._impliedPointSize = self._unitsPerEm * self._scale

    def _setFrame(self):
        if not self.superview():
            return
        scrollWidth, scrollHeight = self.superview().visibleRect().size
        # pick the width and height
        glyphWidth, glyphHeight = self._getGlyphWidthHeight()
        glyphWidth = glyphWidth * self._scale
        glyphHeight = glyphHeight * self._scale
        width = glyphWidth
        height = glyphHeight
        if scrollWidth > width:
            width = scrollWidth
        if scrollHeight > height:
            height = scrollHeight
        # set the frame
        self.setFrame_(((0, 0), (width, height)))
        self._fitToFrame = self.superview().visibleRect().size
        # calculate and store the vetical centering offset
        self._verticalCenterYBuffer = (height - glyphHeight) / 2.0

    def setGlyph_(self, glyph):
        self._glyph = glyph
        self._font = None
        if glyph is not None:
            font = self._font = glyph.getParent()
            if font is not None:
                self._unitsPerEm = font.info.unitsPerEm
                self._descender = font.info.descender
                self._xHeight = font.info.xHeight
                self._ascender = font.info.ascender
                self._capHeight = font.info.capHeight
            self.recalculateFrame()
        self.setNeedsDisplay_(True)

    def getGlyph(self):
        return self._glyph

    # --------------------
    # Notification Support
    # --------------------

    def glyphChanged(self):
        self.setNeedsDisplay_(True)

    def fontChanged(self):
        self.setGlyph_(self._glyph)

    # ---------------
    # Display Control
    # ---------------

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

    def setShowFill_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphFill", value, None)

    def getShowFill(self):
        return self.getDrawingAttribute_layerName_("showGlyphFill", None)

    def setShowStroke_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphStroke", value, None)

    def getShowStroke(self):
        return self.getDrawingAttribute_layerName_("showGlyphStroke", None)

    def setShowMetrics_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphMargins", value, None)
        self.setDrawingAttribute_value_layerName_("showFontVerticalMetrics", value, None)

    def getShowMetrics(self):
        return self.getDrawingAttribute_layerName_("showGlyphMargins", None)

    def setShowImage_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphImage", value, None)

    def getShowImage(self):
        return self.getDrawingAttribute_layerName_("showGlyphImage", None)

    def setShowMetricsTitles_(self, value):
        self.setDrawingAttribute_value_layerName_("showFontVerticalMetricsTitles", value, None)

    def getShowMetricsTitles(self):
        return self.getDrawingAttribute_layerName_("showFontVerticalMetricsTitles", None)

    def setShowOnCurvePoints_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphStartPoints", value, None)
        self.setDrawingAttribute_value_layerName_("showGlyphOnCurvePoints", value, None)

    def getShowOnCurvePoints(self):
        return self.getDrawingAttribute_layerName_("showGlyphOnCurvePoints", None)

    def setShowOffCurvePoints_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphOffCurvePoints", value, None)

    def getShowOffCurvePoints(self):
        return self.getDrawingAttribute_layerName_("showGlyphOffCurvePoints", None)

    def setShowPointCoordinates_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphPointCoordinates", value, None)

    def getShowPointCoordinates(self):
        return self.getDrawingAttribute_layerName_("showGlyphPointCoordinates", None)

    def setShowAnchors_(self, value):
        self.setDrawingAttribute_value_layerName_("showGlyphAnchors", value, None)

    def getShowAnchors(self):
        return self.getDrawingAttribute_layerName_("showGlyphAnchors", None)

    def setShowBlues_(self, value):
        self.setDrawingAttribute_value_layerName_("showFontPostscriptBlues", value, None)

    def getShowBlues(self):
        return self.getDrawingAttribute_layerName_("showFontPostscriptBlues", None)

    def setShowFamilyBlues_(self, value):
        self.setDrawingAttribute_value_layerName_("showFontPostscriptFamilyBlues", value, None)

    def getShowFamilyBlues(self):
        return self.getDrawingAttribute_layerName_("showFontPostscriptFamilyBlues", None)

    # --------------
    # NSView Methods
    # --------------

    def isOpaque(self):
        return True

    def drawRect_(self, rect):
        needCalc = False
        if self.superview() and self._fitToFrame != self.superview().visibleRect().size:
            needCalc = True
        if self.inLiveResize():
            needCalc = True
        if needCalc:
            self.recalculateFrame()

        self.drawBackground()
        if self._glyph is None:
            return

        # apply the overall scale
        transform = NSAffineTransform.transform()
        transform.scaleBy_(self._scale)
        transform.concat()

        # move into position
        visibleWidth = self.bounds().size[0]
        width = self._glyph.width * self._scale
        diff = visibleWidth - width
        xOffset = round((diff / 2) * self._inverseScale)

        yOffset = self._verticalCenterYBuffer * self._inverseScale
        yOffset -= self._descender

        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(xOffset, yOffset)
        transform.concat()

        # store the current drawing rect
        w, h = self.bounds().size
        w *= self._inverseScale
        h *= self._inverseScale
        justInCaseBuffer = 1 * self._inverseScale
        xOffset += justInCaseBuffer
        yOffset += justInCaseBuffer
        w += justInCaseBuffer * 2
        h += justInCaseBuffer * 2
        self._drawingRect = ((-xOffset, -yOffset), (w, h))

        # draw the image
        if self.getDrawingAttribute_layerName_("showGlyphImage", None):
            self.drawImage()
        # draw the blues
        if self.getDrawingAttribute_layerName_("showFontPostscriptBlues", None):
            self.drawBlues()
        if self.getDrawingAttribute_layerName_("showFontPostscriptFamilyBlues", None):
            self.drawFamilyBlues()
        # draw the margins
        if self.getDrawingAttribute_layerName_("showFontPostscriptBlues", None):
            self.drawMargins()
        # draw the vertical metrics
        if self.getDrawingAttribute_layerName_("showFontVerticalMetrics", None) or self.getDrawingAttribute_layerName_("showGlyphMargins", None):
            self.drawVerticalMetrics()
        # draw the glyph
        if self.getDrawingAttribute_layerName_("showGlyphFill", None) or self.getDrawingAttribute_layerName_("showGlyphStroke", None):
            self.drawFillAndStroke()
        if self.getDrawingAttribute_layerName_("showGlyphOnCurvePoints", None) or self.getDrawingAttribute_layerName_("showGlyphOffCurvePoints", None):
            self.drawPoints()
        if self.getDrawingAttribute_layerName_("showGlyphAnchors", None):
            self.drawAnchors()

    def drawBackground(self):
        self._backgroundColor.set()
        NSRectFill(self.bounds())

    def drawImage(self):
        drawing.drawGlyphImage(self._glyph, self._inverseScale, self._drawingRect, backgroundColor=self._backgroundColor)

    def drawBlues(self):
        drawing.drawFontPostscriptBlues(self._glyph, self._inverseScale, self._drawingRect, backgroundColor=self._backgroundColor)

    def drawFamilyBlues(self):
        drawing.drawFontPostscriptFamilyBlues(self._glyph, self._inverseScale, self._drawingRect, backgroundColor=self._backgroundColor)

    def drawVerticalMetrics(self):
        drawText = self.getDrawingAttribute_layerName_("showFontVerticalMetricsTitles", None) and self._impliedPointSize > 150
        drawing.drawFontVerticalMetrics(self._glyph, self._inverseScale, self._drawingRect, drawText=drawText, backgroundColor=self._backgroundColor)

    def drawMargins(self):
        drawing.drawGlyphMargins(self._glyph, self._inverseScale, self._drawingRect, backgroundColor=self._backgroundColor)

    def drawFillAndStroke(self):
        showFill = self.getDrawingAttribute_layerName_("showGlyphFill", None)
        showStroke = self.getDrawingAttribute_layerName_("showGlyphFill", None)
        drawing.drawGlyphFillAndStroke(self._glyph, self._inverseScale, self._drawingRect, drawFill=showFill, drawStroke=showStroke, backgroundColor=self._backgroundColor)

    def drawPoints(self):
        drawStartPoint = self.getDrawingAttribute_layerName_("showGlyphStartPoints", None) and self._impliedPointSize > 175
        drawOnCurves = self.getDrawingAttribute_layerName_("showGlyphOnCurvePoints", None) and self._impliedPointSize > 175
        drawOffCurves = self.getDrawingAttribute_layerName_("showGlyphStartPoints", None) and self._impliedPointSize > 175
        drawCoordinates = self.getDrawingAttribute_layerName_("showGlyphPointCoordinates", None) and self._impliedPointSize > 250
        drawing.drawGlyphPoints(self._glyph, self._inverseScale, self._drawingRect,
            drawStartPoint=drawStartPoint, drawOnCurves=drawOnCurves, drawOffCurves=drawOffCurves, drawCoordinates=drawCoordinates,
            backgroundColor=self._backgroundColor)

    def drawAnchors(self):
        drawText = self._impliedPointSize > 50
        drawing.drawGlyphAnchors(self._glyph, self._inverseScale, self._drawingRect, drawText=drawText, backgroundColor=self._backgroundColor)

#    def drawBottomLayers(self):
#        layerSet = self._glyph.layerSet
#        if layerSet is None:
#            return
#        glyphLayer = self._glyph.layer
#        glyphName = self._glyph.name
#        for otherLayerName in reversed(layerSet.layerOrder):
#            otherLayer = layerSet[otherLayerName]
#            if otherLayer == layer:
#                break
#            if glyphName in otherLayer:
#                drawing.drawGlyphFillAndStroke(otherLayer[glyphName], self._inverseScale, self._drawingRect, drawFill=self._showFill, drawStroke=self._showStroke, backgroundColor=self._backgroundColor)
#
#    def drawTopLayers(self):
#        return
#        layer = self._glyph.layer
#        if layer is None:
#            return
#        glyphName = self._glyph.name
#        layerSet = layer.layerSet
#        seenMain = False
#        for otherLayerName in reversed(layerSet.layerOrder):
#            otherLayer = layerSet[otherLayerName]
#            if otherLayer == layer:
#                seenMain = True
#                continue
#            if not seenMain:
#                continue
#            if glyphName in otherLayer:
#                drawing.drawGlyphFillAndStroke(otherLayer[glyphName], self._inverseScale, self._drawingRect, drawFill=self._showFill, drawStroke=self._showStroke, backgroundColor=self._backgroundColor)

class GlyphView(PlacardScrollView):

    glyphViewClass = DefconAppKitGlyphNSView

    def __init__(self, posSize):
        self._glyphView = self.glyphViewClass.alloc().init()
        super(GlyphView, self).__init__(posSize, self._glyphView, autohidesScrollers=False)
        self.buildPlacard()
        self.setPlacard(self.placard)

    def buildPlacard(self):
        placardW = 65
        placardH = 16
        self.placard = vanilla.Group((0, 0, placardW, placardH))
        self.placard.optionsButton = PlacardPopUpButton((0, 0, placardW, placardH),
            [], callback=self._placardDisplayOptionsCallback, sizeStyle="mini")
        self._populatePlacard()
        #button.menu().setAutoenablesItems_(False)

    def _populatePlacard(self):
        options = [
            "Fill",
            "Stroke",
            "Image",
            "Metrics",
            "On Curve Points",
            "Off Curve Points",
            "Point Coordinates",
            "Anchors",
            "Blues",
            "Family Blues"
        ]
        # make a default item
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Display...", None, "")
        ## 10.5+
        try:
            item.setHidden_(True)
        ## ugh. in <= 10.4, make the item disabled
        except AttributeError:
            item.setEnabled_(False)
            item.setState_(False)
        items = [item]
        for attr in options:
            method = "getShow" + attr.replace(" ", "")
            state = getattr(self._glyphView, method)()
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(attr, None, "")
            item.setState_(state)
            items.append(item)
        ## set the items
        self.placard.optionsButton.setItems(items)
        button = self.placard.optionsButton.getNSPopUpButton()
        button.setTitle_("Display...")

    def _breakCycles(self):
        self._unsubscribeFromGlyph()
        self._glyphView = None
        super(GlyphView, self)._breakCycles()

    def _placardDisplayOptionsCallback(self, sender):
        index = sender.get()
        attr = sender.getItems()[index]
        method = "getShow" + attr.replace(" ", "")
        state = getattr(self._glyphView, method)()
        method = "setShow" + attr.replace(" ", "") + "_"
        getattr(self._glyphView, method)(not state)
        self._populatePlacard()

    # -------------
    # Notifications
    # -------------

    def _subscribeToGlyph(self, glyph):
        if glyph is not None:
            glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
            font = glyph.getParent()
            if font is not None:
                font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyph(self):
        if self._glyphView is not None:
            glyph = self._glyphView.getGlyph()
            if glyph is not None:
                glyph.removeObserver(self, "Glyph.Changed")
                font = glyph.getParent()
                if font is not None:
                    font.info.removeObserver(self, "Info.Changed")

    def _glyphChanged(self, notification):
        self._glyphView.glyphChanged()

    def _fontChanged(self, notification):
        self._glyphView.fontChanged()

    # --------------
    # Public Methods
    # --------------

    def set(self, glyph):
        self._unsubscribeFromGlyph()
        self._subscribeToGlyph(glyph)
        self._glyphView.setGlyph_(glyph)

    def setShowFill(self, value):
        self._populatePlacard()
        self._glyphView.setShowFill_(value)

    def getShowFill(self):
        return self._glyphView.getShowFill()

    def setShowStroke(self, value):
        self._populatePlacard()
        self._glyphView.setShowStroke_(value)

    def getShowStroke(self):
        return self._glyphView.getShowStroke()

    def setShowMetrics(self, value):
        self._populatePlacard()
        self._glyphView.setShowMetrics_(value)

    def getShowImage(self):
        return self._glyphView.getShowImage()

    def setShowImage(self, value):
        self._populatePlacard()
        self._glyphView.setShowImage_(value)

    def getShowMetrics(self):
        return self._glyphView.getShowMetrics()

    def setShowMetricsTitles(self, value):
        self._populatePlacard()
        self._glyphView.setShowMetricsTitles_(value)

    def getShowMetricsTitles(self):
        return self._glyphView.getShowMetricsTitles()

    def setShowOnCurvePoints(self, value):
        self._populatePlacard()
        self._glyphView.setShowOnCurvePoints_(value)

    def getShowOnCurvePoints(self):
        return self._glyphView.getShowOnCurvePoints()

    def setShowOffCurvePoints(self, value):
        self._populatePlacard()
        self._glyphView.setShowOffCurvePoints_(value)

    def getShowOffCurvePoints(self):
        return self._glyphView.getShowOffCurvePoints()

    def setShowPointCoordinates(self, value):
        self._populatePlacard()
        self._glyphView.setShowPointCoordinates_(value)

    def getShowPointCoordinates(self):
        return self._glyphView.getShowPointCoordinates()

    def setShowAnchors(self, value):
        self._populatePlacard()
        self._glyphView.setShowAnchors_(value)

    def getShowAnchors(self):
        return self._glyphView.getShowAnchors()

    def setShowBlues(self, value):
        self._populatePlacard()
        self._glyphView.setShowBlues_(value)

    def getShowBlues(self):
        return self._glyphView.getShowBlues()

    def setShowFamilyBlues(self, value):
        self._populatePlacard()
        self._glyphView.setShowFamilyBlues_(value)

    def getShowFamilyBlues(self):
        return self._glyphView.getShowFamilyBlues()
