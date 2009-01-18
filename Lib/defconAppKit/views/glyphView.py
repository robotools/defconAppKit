from Foundation import *
from AppKit import *
from robofab.pens.pointPen import AbstractPointPen
import vanilla
from defconAppKit.views.placardScrollView import PlacardScrollView, PlacardPopUpButton

backgroundColor = NSColor.whiteColor()
metricsColor = NSColor.colorWithCalibratedWhite_alpha_(.4, .5)
metricsTitlesColor = NSColor.colorWithCalibratedWhite_alpha_(.1, .5)
marginColor = NSColor.colorWithCalibratedWhite_alpha_(.5, .11)
fillColor = NSColor.colorWithCalibratedWhite_alpha_(0, .4)
strokeColor = NSColor.colorWithCalibratedWhite_alpha_(0, 1)
fillAndStrokFillColor = NSColor.blackColor()
componentFillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .2, .1, .4)
componentStrokeColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0, .2, .1, .7)
pointColor = NSColor.colorWithCalibratedWhite_alpha_(.6, 1)
pointStrokeColor = NSColor.colorWithCalibratedWhite_alpha_(1, 1)
startPointColor = NSColor.colorWithCalibratedWhite_alpha_(0, .2)
bezierHandleColor = NSColor.colorWithCalibratedWhite_alpha_(0, .2)
pointCoordinateColor = NSColor.colorWithCalibratedWhite_alpha_(.5, .75)
anchorColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .2, 0, 1)
bluesColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, .7, 1, .3)
familyBluesColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, .5, .3)


class DefconAppKitGlyphNSView(NSView):

    def init(self):
        self = super(DefconAppKitGlyphNSView, self).init()
        self._glyph = None

        self._unitsPerEm = 1000
        self._descender = -250
        self._xHeight = 500
        self._capHeight = 750
        self._ascender = 750

        self._showFill = True
        self._showStroke = True
        self._showMetrics = True
        self._showMetricsTitles = True
        self._showOnCurvePoints = True
        self._showOffCurvePoints = False
        self._showPointCoordinates = False
        self._showAnchors = True
        self._showBlues = False
        self._showFamilyBlues = False

        self._pointSize = None
        self._centerVertically = True
        self._centerHorizontally = True

        self._noPointSizePadding = 200
        self._xCanvasAddition = 250
        self._yCanvasAddition = 250
        self._verticalCenterYBuffer = 0
        self._scale = 1.0
        self._inverseScale = 0.1
        self._impliedPointSize = 1000

        self._backgroundColor = backgroundColor
        self._metricsColor = metricsColor
        self._metricsTitlesColor = metricsTitlesColor
        self._marginColor = marginColor
        self._fillColor = fillColor
        self._strokeColor = strokeColor
        self._fillAndStrokFillColor = fillAndStrokFillColor
        self._componentFillColor = componentFillColor
        self._componentStrokeColor = componentStrokeColor
        self._pointColor = pointColor
        self._pointStrokeColor = pointStrokeColor
        self._startPointColor = startPointColor
        self._bezierHandleColor = bezierHandleColor
        self._pointCoordinateColor = pointCoordinateColor
        self._anchorColor = anchorColor
        self._bluesColor = bluesColor
        self._familyBluesColor = familyBluesColor

        self._fitToFrame = None

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
        if self._pointSize is None:
            visibleHeight = self.superview().visibleRect().size[1]
            fitHeight = visibleHeight
            glyphWidth, glyphHeight = self._getGlyphWidthHeight()
            glyphHeight += self._noPointSizePadding * 2
            self._scale = fitHeight / glyphHeight
        else:
            self._scale = self._pointSize / float(self._unitsPerEm)
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
        if self._pointSize is not None:
            glyphWidth += self._xCanvasAddition * 2
            glyphHeight += self._yCanvasAddition * 2
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

    # ---------------
    # Display Control
    # ---------------

#    def setPointSize_(self, value):
#        self._pointSize = value
#        self.setNeedsDisplay_(True)
#
#    def getPointSize(self):
#        return self._pointSize

    def setShowFill_(self, value):
        self._showFill = value
        self.setNeedsDisplay_(True)

    def getShowFill(self):
        return self._showFill

    def setShowStroke_(self, value):
        self._showStroke = value
        self.setNeedsDisplay_(True)

    def getShowStroke(self):
        return self._showStroke

    def setShowMetrics_(self, value):
        self._showMetrics = value
        self.setNeedsDisplay_(True)

    def getShowMetrics(self):
        return self._showMetrics

    def setShowMetricsTitles_(self, value):
        self._showMetricsTitles = value
        self.setNeedsDisplay_(True)

    def getShowMetricsTitles(self):
        return self._showMetricsTitles

    def setShowOnCurvePoints_(self, value):
        self._showOnCurvePoints = value
        self.setNeedsDisplay_(True)

    def getShowOnCurvePoints(self):
        return self._showOnCurvePoints

    def setShowOffCurvePoints_(self, value):
        self._showOffCurvePoints = value
        self.setNeedsDisplay_(True)

    def getShowOffCurvePoints(self):
        return self._showOffCurvePoints

    def setShowPointCoordinates_(self, value):
        self._showPointCoordinates = value
        self.setNeedsDisplay_(True)

    def getShowPointCoordinates(self):
        return self._showPointCoordinates

    def setShowAnchors_(self, value):
        self._showAnchors = value
        self.setNeedsDisplay_(True)

    def getShowAnchors(self):
        return self._showAnchors

    def setShowBlues_(self, value):
        self._showBlues = value
        self.setNeedsDisplay_(True)

    def getShowBlues(self):
        return self._showBlues

    def setShowFamilyBlues_(self, value):
        self._showFamilyBlues = value
        self.setNeedsDisplay_(True)

    def getShowFamilyBlues(self):
        return self._showFamilyBlues

    # --------------
    # NSView Methods
    # --------------

    def isOpaque(self):
        return True

    def drawRect_(self, rect):
        needCalc = False
        if self.superview() and self._fitToFrame != self.superview().visibleRect().size:
            needCalc = True
        if self.inLiveResize() and self._pointSize is None:
            needCalc = True
        if needCalc:
            self.recalculateFrame()

        self.drawBackground()
        if self._glyph is None:
            return
        # apply vertical offset
        transform = NSAffineTransform.transform()
        if self._centerVertically:
            yOffset = self._verticalCenterYBuffer
        else:
            canvasHeight = self._getGlyphWidthHeight()[1] + (self._yCanvasAddition * 2)
            canvasHeight = canvasHeight * self._scale
            frameHeight = self.frame().size[1]
            yOffset = frameHeight - canvasHeight + (self._yCanvasAddition * self._scale)
        transform.translateXBy_yBy_(0, yOffset)
        transform.concat()
        # apply the overall scale
        transform = NSAffineTransform.transform()
        transform.scaleBy_(self._scale)
        transform.concat()
        yOffset = yOffset * self._inverseScale
        # shift to baseline
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(0, -self._descender)
        transform.concat()
        yOffset = yOffset - self._descender
        # draw the blues
        if self._showBlues:
            self.drawBlues()
        if self._showFamilyBlues:
            self.drawFamilyBlues()
        # draw the margins
        if self._centerHorizontally:
            visibleWidth = self.bounds().size[0]
            width = self._glyph.width * self._scale
            diff = visibleWidth - width
            xOffset = round((diff / 2) * self._inverseScale)
        else:
            xOffset = self._xCanvasAddition
        if self._showMetrics:
            self.drawMargins(xOffset, yOffset)
        # draw the horizontal metrics
        if self._showMetrics:
            self.drawHorizontalMetrics()
        # apply horizontal offset
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(xOffset, 0)
        transform.concat()
        # draw the glyph
        if self._showFill:
            self.drawFill()
        if self._showStroke:
            self.drawStroke()
        self.drawPoints()
        if self._showAnchors:
            self.drawAnchors()

    def roundPosition(self, value):
        value = value * self._scale
        value = round(value) - .5
        value = value * self._inverseScale
        return value

    def drawBackground(self):
        self._backgroundColor.set()
        NSRectFill(self.bounds())

    def drawBlues(self):
        width = self.bounds().size[0] * self._inverseScale
        self._bluesColor.set()
        font = self._glyph.getParent()
        if font is None:
            return
        attrs = ["postscriptBlueValues", "postscriptOtherBlues"]
        for attr in attrs:
            values = getattr(font.info, attr)
            if not values:
                continue
            yMins = [i for index, i in enumerate(values) if not index % 2]
            yMaxs = [i for index, i in enumerate(values) if index % 2]
            for yMin, yMax in zip(yMins, yMaxs):
                NSRectFillUsingOperation(((0, yMin), (width, yMax - yMin)), NSCompositeSourceOver)

    def drawFamilyBlues(self):
        width = self.bounds().size[0] * self._inverseScale
        self._familyBluesColor.set()
        font = self._glyph.getParent()
        if font is None:
            return
        attrs = ["postscriptFamilyBlues", "postscriptFamilyOtherBlues"]
        for attr in attrs:
            values = getattr(font.info, attr)
            if not values:
                continue
            yMins = [i for index, i in enumerate(values) if not index % 2]
            yMaxs = [i for index, i in enumerate(values) if index % 2]
            for yMin, yMax in zip(yMins, yMaxs):
                NSRectFillUsingOperation(((0, yMin), (width, yMax - yMin)), NSCompositeSourceOver)

    def drawHorizontalMetrics(self):
        toDraw = [
            ("Descender", self._descender),
            ("Baseline", 0),
            ("X Height", self._xHeight),
            ("Cap Height", self._capHeight),
            ("Ascender", self._ascender)
        ]
        positions = {}
        for name, position in toDraw:
            if position not in positions:
                positions[position] = []
            positions[position].append(name)
        # lines
        path = NSBezierPath.bezierPath()
        x1 = 0
        x2 = self.bounds().size[0] * self._inverseScale
        for position, names in sorted(positions.items()):
            y = self.roundPosition(position)
            path.moveToPoint_((x1, y))
            path.lineToPoint_((x2, y))
        path.setLineWidth_(1.0 * self._inverseScale)
        self._metricsColor.set()
        path.stroke()
        # text
        if self._showMetricsTitles and self._impliedPointSize > 150:
            fontSize = 9 * self._inverseScale
            shadow = NSShadow.shadow()
            shadow.setShadowColor_(self._backgroundColor)
            shadow.setShadowBlurRadius_(5)
            shadow.setShadowOffset_((0, 0))
            attributes = {
                NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                NSForegroundColorAttributeName : self._metricsTitlesColor
            }
            glowAttributes = {
                NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                NSForegroundColorAttributeName : self._metricsColor,
                NSStrokeColorAttributeName : self._backgroundColor,
                NSStrokeWidthAttributeName : 25,
                NSShadowAttributeName : shadow
            }
            for position, names in sorted(positions.items()):
                y = position - (fontSize / 2)
                text = ", ".join(names)
                text = " %s " % text
                t = NSAttributedString.alloc().initWithString_attributes_(text, glowAttributes)
                t.drawAtPoint_((0, y))
                t = NSAttributedString.alloc().initWithString_attributes_(text, attributes)
                t.drawAtPoint_((0, y))

    def drawMargins(self, xOffset, yOffset):
        x1 = 0
        w1 = xOffset
        x2 = self._glyph.width + xOffset
        w2 = (self.bounds().size[0] * self._inverseScale) - x2
        h = self.bounds().size[1] * self._inverseScale
        rects = [
            ((x1, -yOffset), (w1, h)),
            ((x2, -yOffset), (w2, h))
        ]
        self._marginColor.set()
        for rect in rects:
            NSRectFillUsingOperation(rect, NSCompositeSourceOver)

    def drawFill(self):
        # outlines
        path = self._glyph.getRepresentation("NoComponentsNSBezierPath")
        if self._showStroke:
            self._fillColor.set()
        else:
            self._fillAndStrokFillColor.set()
        path.fill()
        # components
        path = self._glyph.getRepresentation("OnlyComponentsNSBezierPath")
        self._componentFillColor.set()
        path.fill()

    def drawStroke(self):
        # outlines
        path = self._glyph.getRepresentation("NoComponentsNSBezierPath")
        self._strokeColor.set()
        path.setLineWidth_(1.0 * self._inverseScale)
        path.stroke()
        # components
        path = self._glyph.getRepresentation("OnlyComponentsNSBezierPath")
        self._componentStrokeColor.set()
        path.setLineWidth_(1.0 * self._inverseScale)
        path.stroke()

    def drawPoints(self):
        # work out appropriate sizes and
        # skip if the glyph is too small
        pointSize = self._impliedPointSize
        if pointSize > 550:
            startPointSize = 21
            offCurvePointSize = 5
            onCurvePointSize = 6
            onCurveSmoothPointSize = 7
        elif pointSize > 250:
            startPointSize = 15
            offCurvePointSize = 3
            onCurvePointSize = 4
            onCurveSmoothPointSize = 5
        elif pointSize > 175:
            startPointSize = 9
            offCurvePointSize = 1
            onCurvePointSize = 2
            onCurveSmoothPointSize = 3
        else:
            return
        if pointSize > 250:
            coordinateSize = 9
        else:
            coordinateSize = 0
        # use the data from the outline representation
        outlineData = self._glyph.getRepresentation("defconAppKitOutlineInformation")
        points = []
        # start point
        if self._showOnCurvePoints and outlineData["startPoints"]:
            startWidth = startHeight = self.roundPosition(startPointSize * self._inverseScale)
            startHalf = startWidth / 2.0
            path = NSBezierPath.bezierPath()
            for point, angle in outlineData["startPoints"]:
                x, y = point
                if angle is not None:
                    path.moveToPoint_((x, y))
                    path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
                        (x, y), startHalf, angle-90, angle+90, True)
                    path.closePath()
                else:
                    path.appendBezierPathWithOvalInRect_(((x-startHalf, y-startHalf), (startWidth, startHeight)))
            self._startPointColor.set()
            path.fill()
        # off curve
        if self._showOffCurvePoints and outlineData["offCurvePoints"]:
            # lines
            path = NSBezierPath.bezierPath()
            for point1, point2 in outlineData["bezierHandles"]:
                path.moveToPoint_(point1)
                path.lineToPoint_(point2)
            self._bezierHandleColor.set()
            path.setLineWidth_(1.0 * self._inverseScale)
            path.stroke()
            # points
            offWidth = offHeight = self.roundPosition(offCurvePointSize * self._inverseScale)
            offHalf = offWidth / 2.0
            path = NSBezierPath.bezierPath()
            for point in outlineData["offCurvePoints"]:
                x, y = point["point"]
                points.append((x, y))
                x = self.roundPosition(x - offHalf)
                y = self.roundPosition(y - offHalf)
                path.appendBezierPathWithOvalInRect_(((x, y), (offWidth, offHeight)))
            path.setLineWidth_(3.0 * self._inverseScale)
            self._pointStrokeColor.set()
            path.stroke()
            self._backgroundColor.set()
            path.fill()
            self._pointColor.set()
            path.setLineWidth_(1.0 * self._inverseScale)
            path.stroke()
        # on curve
        if self._showOnCurvePoints and outlineData["onCurvePoints"]:
            width = height = self.roundPosition(onCurvePointSize * self._inverseScale)
            half = width / 2.0
            smoothWidth = smoothHeight = self.roundPosition(onCurveSmoothPointSize * self._inverseScale)
            smoothHalf = smoothWidth / 2.0
            path = NSBezierPath.bezierPath()
            for point in outlineData["onCurvePoints"]:
                x, y = point["point"]
                points.append((x, y))
                if point["smooth"]:
                    x = self.roundPosition(x - smoothHalf)
                    y = self.roundPosition(y - smoothHalf)
                    path.appendBezierPathWithOvalInRect_(((x, y), (smoothWidth, smoothHeight)))
                else:
                    x = self.roundPosition(x - half)
                    y = self.roundPosition(y - half)
                    path.appendBezierPathWithRect_(((x, y), (width, height)))
            self._pointStrokeColor.set()
            path.setLineWidth_(3.0 * self._inverseScale)
            path.stroke()
            self._pointColor.set()
            path.fill()
        # text
        if self._showPointCoordinates and coordinateSize:
            fontSize = 9 * self._inverseScale
            attributes = {
                NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
                NSForegroundColorAttributeName : self._pointCoordinateColor
            }
            for x, y in points:
                posX = x
                posY = y
                x = round(x, 1)
                if int(x) == x:
                    x = int(x)
                y = round(y, 1)
                if int(y) == y:
                    y = int(y)
                text = "%d  %d" % (x, y)
                self._drawTextAtPoint(text, attributes, (posX, posY), 3)

    def drawAnchors(self):
        pointSize = self._impliedPointSize
        anchorSize = 5
        fontSize = 9
        if pointSize > 500:
            pass
        elif pointSize > 250:
            fontSize = 7
        elif pointSize > 50:
            anchorSize = 3
            fontSize = 7
        else:
            return
        anchorSize = self.roundPosition(anchorSize * self._inverseScale)
        anchorHalf = anchorSize * .5
        fontSize = fontSize * self._inverseScale
        font = NSFont.boldSystemFontOfSize_(fontSize)
        attributes = {
            NSFontAttributeName : font,
            NSForegroundColorAttributeName : self._anchorColor
        }
        shadow = NSShadow.shadow()
        shadow.setShadowColor_(self._pointStrokeColor)
        shadow.setShadowBlurRadius_(5)
        shadow.setShadowOffset_((0, 0))
        glowAttributes = {
            NSFontAttributeName : font,
            NSForegroundColorAttributeName : self._anchorColor,
            NSStrokeColorAttributeName : self._pointStrokeColor,
            NSStrokeWidthAttributeName : 10,
            NSShadowAttributeName : shadow
        }
        path = NSBezierPath.bezierPath()
        for anchor in self._glyph.anchors:
            x, y = anchor.x, anchor.y
            name = anchor.name
            path.appendBezierPathWithOvalInRect_(((x - anchorHalf, y - anchorHalf), (anchorSize, anchorSize)))
            if pointSize > 100:
                self._drawTextAtPoint(name, glowAttributes, (x, y), fontSize * self._scale * .75)
                self._drawTextAtPoint(name, attributes, (x, y), fontSize * self._scale * .75)
        self._pointStrokeColor.set()
        path.setLineWidth_(3.0 * self._inverseScale)
        path.stroke()
        self._anchorColor.set()
        path.fill()

    def _drawTextAtPoint(self, text, attributes, (posX, posY), yOffset):
        text = NSAttributedString.alloc().initWithString_attributes_(text, attributes)
        fontSize = attributes[NSFontAttributeName].pointSize()
        w = text.size()[0]
        posX -= w / 2
        posY -= fontSize + (yOffset * self._inverseScale)
        posX = self.roundPosition(posX)
        posY = self.roundPosition(posY)
        text.drawAtPoint_((posX, posY))


class GlyphView(PlacardScrollView):

    def __init__(self, posSize):
        self._glyphView = DefconAppKitGlyphNSView.alloc().init()
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

    # --------------
    # Public Methods
    # --------------

    def set(self, glyph):
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
