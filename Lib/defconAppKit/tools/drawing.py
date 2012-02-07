from Foundation import *
from AppKit import *

"""
Common glyph drawing functions for all views. Notes:
- all drawing is done in font units
- the scale argument is the factor to scale a glyph unit to a view unit
- the rect argument is the rect that the glyph is being drawn in
"""

"""
setLayer_drawingAttributes_(layerName, attributes)

showGlyphFill
showGlyphStroke
showGlyphOnCurvePoints
showGlyphStartPoints
showGlyphOffCurvePoints
showGlyphPointCoordinates
showGlyphAnchors
showGlyphImage
showGlyphMargins
showFontVerticalMetrics
showFontVerticalMetricsTitles
showFontPostscriptBlues
showFontPostscriptFamilyBlues
"""

# ------
# Colors
# ------

defaultColors = dict(

    # General
    # -------

    background=NSColor.whiteColor(),

    # Font
    # ----

    # vertical metrics
    fontVerticalMetrics=NSColor.colorWithCalibratedWhite_alpha_(.4, .5),

    fontPostscriptBlues=NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, .7, 1, .3),
    fontPostscriptFamilyBlues=NSColor.colorWithCalibratedRed_green_blue_alpha_(1, 1, .5, .3),

    # Glyph
    # -----

    # margins
    glyphMarginsFill=NSColor.colorWithCalibratedWhite_alpha_(.5, .11),
    glyphMarginsStroke=NSColor.colorWithCalibratedWhite_alpha_(.7, .5),

    # contour fill
    glyphContourFill=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1),

    # contour stroke
    glyphContourStroke=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1),

    # component fill
    glyphComponentFill=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1),

    # component stroke
    glyphComponentStroke=NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 0, 1),

    # points
    glyphPoints=NSColor.colorWithCalibratedRed_green_blue_alpha_(.6, .6, .6, 1),

    # anchors
    glyphAnchor=NSColor.colorWithCalibratedRed_green_blue_alpha_(1, .2, 0, 1),

)

def colorToNSColor(color):
    r, g, b, a = color
    return NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)

def getDefaultColor(name):
    return defaultColors[name]

# ----------
# Primitives
# ----------

def drawFilledRect(rect):
    context = NSGraphicsContext.currentContext()
    context.setShouldAntialias_(False)
    NSRectFillUsingOperation(rect, NSCompositeSourceOver)
    context.setShouldAntialias_(True)

def drawFilledOval(rect):
    path = NSBezierPath.bezierPath()
    path.appendBezierPathWithOvalInRect_(rect)
    path.fill()

def drawLine((x1, y1), (x2, y2), lineWidth=1.0):
    turnOffAntiAliasing = False
    if x1 == x2 or y1 == y2:
        turnOffAntiAliasing = True
    if turnOffAntiAliasing:
        context = NSGraphicsContext.currentContext()
        context.setShouldAntialias_(False)
    path = NSBezierPath.bezierPath()
    path.moveToPoint_((x1, y1))
    path.lineToPoint_((x2, y2))
    if turnOffAntiAliasing and lineWidth == 1.0:
        lineWidth = 0.001
    path.setLineWidth_(lineWidth)
    path.stroke()
    if turnOffAntiAliasing:
        context.setShouldAntialias_(True)

def drawTextAtPoint(text, pt, scale, attributes={}, xAlign="left", yAlign="bottom"):
    text = NSAttributedString.alloc().initWithString_attributes_(text, attributes)
    if xAlign != "left" or yAlign != "bottom":
        width, height = text.size()
        width *= scale
        height *= scale
        x, y = pt
        if xAlign == "center":
            x -= width / 2
        elif xAlign == "right":
            x -= width
        if yAlign == "center":
            y -= height / 2
        elif yAlign == "top":
            y -= height
        pt = (x, y)
    context = NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(pt[0], pt[1])
    transform.scaleXBy_yBy_(scale, scale)
    transform.concat()
    text.drawAtPoint_((0, 0))
    context.restoreGraphicsState()

# ----
# Font
# ----

# Vertical Metrics

def drawFontVerticalMetrics(glyph, scale, rect, drawLines=True, drawText=True, color=None, backgroundColor=None):
    font = glyph.font
    if font is None:
        return
    if color is None:
        color = getDefaultColor("fontVerticalMetrics")
    if backgroundColor is None:
        backgroundColor = getDefaultColor("background")
    color.set()
    # gather y positions
    toDraw = (
        ("Descender", "descender"),
        ("X Height", "xHeight"),
        ("Cap Height", "capHeight"),
        ("Ascender", "ascender")
    )
    toDraw = [(name, getattr(font.info, attr)) for name, attr in toDraw if getattr(font.info, attr) is not None]    
    toDraw.append(("Baseline", 0))
    positions = {}
    for name, position in toDraw:
        if position not in positions:
            positions[position] = []
        positions[position].append(name)
    # create lines
    xMin = rect[0][0]
    xMax = xMin + rect[1][0]
    lines = []
    for y, names in sorted(positions.items()):
        names = ", ".join(names)
        lines.append(((xMin, y), (xMax, y), names))
    # draw lines
    if drawLines:
        lineWidth = 1.0 * scale
        for pt1, pt2, names in lines:
            drawLine(pt1, pt2, lineWidth=lineWidth)
    # draw text
    if drawText:
        fontSize = 9
        shadow = NSShadow.shadow()
        shadow.setShadowColor_(backgroundColor)
        shadow.setShadowBlurRadius_(5)
        shadow.setShadowOffset_((0, 0))
        attributes = {
            NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
            NSForegroundColorAttributeName : color
        }
        glowAttributes = {
            NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
            NSForegroundColorAttributeName : color,
            NSStrokeColorAttributeName : backgroundColor,
            NSStrokeWidthAttributeName : 25,
            NSShadowAttributeName : shadow
        }
        for pt1, pt2, names in lines:
            x, y = pt1
            x += 5 * scale
            y -= (fontSize / 2.0) * scale
            drawTextAtPoint(names, (x, y), scale, glowAttributes)
            drawTextAtPoint(names, (x, y), scale, attributes)

# Blues

def drawFontPostscriptBlues(glyph, scale, rect, color=None, backgroundColor=None):
    font = glyph.font
    if font is None:
        return
    blues = []
    if font.info.postscriptBlueValues:
        blues += font.info.postscriptBlueValues
    if font.info.postscriptOtherBlues:
        blues += font.info.postscriptOtherBlues
    if not blues:
        return
    if color is None:
        color = getDefaultColor("fontPostscriptBlues")
    color.set()
    _drawBlues(blues, rect)

def drawFontPostscriptFamilyBlues(glyph, scale, rect, color=None, backgroundColor=None):
    font = glyph.font
    if font is None:
        return
    blues = []
    if font.info.postscriptFamilyBlues:
        blues += font.info.postscriptFamilyBlues
    if font.info.postscriptFamilyOtherBlues:
        blues += font.info.postscriptFamilyOtherBlues
    if not blues:
        return
    if color is None:
        color = getDefaultColor("fontPostscriptFamilyBlues")
    color.set()
    _drawBlues(blues, rect)

def _drawBlues(blues, rect):
    yMins = [i for index, i in enumerate(blues) if not index % 2]
    yMaxs = [i for index, i in enumerate(blues) if index % 2]
    blues = zip(yMins, yMaxs)
    x = rect[0][0]
    w = rect[1][0]
    for yMin, yMax in blues:
        drawFilledRect(((x, yMin), (w, yMax - yMin)))

# Image

def drawGlyphImage(glyph, scale, rect, backgroundColor=None):
    if glyph.image.fileName is None:
        return
    context = NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    aT = NSAffineTransform.transform()
    aT.setTransformStruct_(glyph.image.transformation)
    aT.concat()
    image = glyph.image.getRepresentation("defconAppKit.NSImage")
    image.drawAtPoint_fromRect_operation_fraction_(
        (0, 0), ((0, 0), image.size()), NSCompositeSourceOver, 1.0
    )
    context.restoreGraphicsState()

# Margins

def drawGlyphMargins(glyph, scale, rect, drawFill=True, drawStroke=True, fillColor=None, strokeColor=None, backgroundColor=None):
    if fillColor is None:
        fillColor = getDefaultColor("glyphMarginsFill")
    if strokeColor is None:
        strokeColor = getDefaultColor("glyphMarginsStroke")
    (x, y), (w, h) = rect
    if drawFill:
        left = ((x, y), (-x, h))
        right = ((glyph.width, y), (w - glyph.width, h))
        fillColor.set()
        for rect in (left, right):
            drawFilledRect(rect)
    if drawStroke:
        strokeColor.set()
        drawLine((0, y), (0, y + h))
        drawLine((glyph.width, y), (glyph.width, y + h))

# Fill and Stroke

def drawGlyphFillAndStroke(glyph, scale, rect,
    drawFill=True, drawStroke=True,
    contourFillColor=None, contourStrokeColor=None, componentFillColor=None, backgroundColor=None):
    # get the layer color
    layer = glyph.layer
    layerColor = None
    if layer is not None and layer.color is not None:
        layerColor = colorToNSColor(layer.color)
    # get the paths
    contourPath = glyph.getRepresentation("defconAppKit.NoComponentsNSBezierPath")
    componentPath = glyph.getRepresentation("defconAppKit.OnlyComponentsNSBezierPath")
    # fill
    if drawFill:
        # work out the colors
        if contourFillColor is None and layerColor is not None:
            contourFillColor = layerColor
        elif contourFillColor is None and layerColor is None:
            contourFillColor = getDefaultColor("glyphContourFill")
        if componentFillColor is None and layerColor is not None:
            componentFillColor = layerColor
        elif componentFillColor is None and layerColor is None:
            componentFillColor = getDefaultColor("glyphComponentFill")
        # make the fill less opaque if stroking
        if drawStroke:
            contourFillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                contourFillColor.redComponent(),
                contourFillColor.greenComponent(),
                contourFillColor.blueComponent(),
                contourFillColor.alphaComponent() * 0.6
            )
            componentFillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(
                componentFillColor.redComponent(),
                componentFillColor.greenComponent(),
                componentFillColor.blueComponent(),
                componentFillColor.alphaComponent() * 0.6
            )
        # components
        componentFillColor.set()
        componentPath.fill()
        # contours
        contourFillColor.set()
        contourPath.fill()
    # stroke
    if drawStroke:
        # work out the color
        if contourStrokeColor is None and layerColor is not None:
            contourStrokeColor = layerColor
        elif contourStrokeColor is None and layerColor is None:
            contourStrokeColor = getDefaultColor("glyphContourStroke")
        # contours
        contourPath.setLineWidth_(1.0 * scale)
        contourStrokeColor.set()
        contourPath.stroke()

# points

def drawGlyphPoints(glyph, scale, rect, drawStartPoint=True, drawOnCurves=True, drawOffCurves=True, drawCoordinates=True, color=None, backgroundColor=None):
    layer = glyph.layer
    layerColor = None
    if layer is not None:
        color = colorToNSColor(layer.color)
    if color is None:
        color = getDefaultColor("glyphPoints")
    if backgroundColor is None:
        backgroundColor = getDefaultColor("background")
    # get the outline data
    outlineData = glyph.getRepresentation("defconAppKit.OutlineInformation")
    points = []
    # start point
    if drawStartPoint and outlineData["startPoints"]:
        startWidth = startHeight = 15 * scale
        startHalf = startWidth / 2.0
        path = NSBezierPath.bezierPath()
        for point, angle in outlineData["startPoints"]:
            x, y = point
            if angle is not None:
                path.moveToPoint_((x, y))
                path.appendBezierPathWithArcWithCenter_radius_startAngle_endAngle_clockwise_(
                    (x, y), startHalf, angle - 90, angle + 90, True)
                path.closePath()
            else:
                path.appendBezierPathWithOvalInRect_(((x - startHalf, y - startHalf), (startWidth, startHeight)))
        r = color.redComponent()
        g = color.greenComponent()
        b = color.blueComponent()
        a = color.alphaComponent()
        a *= 0.3
        startPointColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
        startPointColor.set()
        path.fill()
    # off curve
    if drawOffCurves and outlineData["offCurvePoints"]:
        # lines
        color.set()
        for point1, point2 in outlineData["bezierHandles"]:
            drawLine(point1, point2)
        # points
        offWidth = 3 * scale
        offHalf = offWidth / 2.0
        path = NSBezierPath.bezierPath()
        for point in outlineData["offCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            x -= offHalf
            y -= offHalf
            path.appendBezierPathWithOvalInRect_(((x, y), (offWidth, offWidth)))
        path.setLineWidth_(3.0 * scale)
        color.set()
        path.stroke()
        backgroundColor.set()
        path.fill()
        color.set()
        path.setLineWidth_(1.0 * scale)
    # on curve
    if drawOnCurves and outlineData["onCurvePoints"]:
        width = 4 * scale
        half = width / 2.0
        smoothWidth = 5 * scale
        smoothHalf = smoothWidth / 2.0
        path = NSBezierPath.bezierPath()
        for point in outlineData["onCurvePoints"]:
            x, y = point["point"]
            points.append((x, y))
            if point["smooth"]:
                x -= smoothHalf
                y -= smoothHalf
                path.appendBezierPathWithOvalInRect_(((x, y), (smoothWidth, smoothWidth)))
            else:
                x -= half
                y -= half
                path.appendBezierPathWithRect_(((x, y), (width, width)))
        backgroundColor.set()
        path.setLineWidth_(3.0 * scale)
        path.stroke()
        color.set()
        path.fill()
    # coordinates
    if drawCoordinates:
        r = color.redComponent()
        g = color.greenComponent()
        b = color.blueComponent()
        a = color.alphaComponent()
        a *= 0.6
        color = NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a)
        fontSize = 9
        attributes = {
            NSFontAttributeName : NSFont.systemFontOfSize_(fontSize),
            NSForegroundColorAttributeName : color
        }
        for x, y in points:
            posX = x
            posY = y - 3
            x = round(x, 1)
            if int(x) == x:
                x = int(x)
            y = round(y, 1)
            if int(y) == y:
                y = int(y)
            text = "%d  %d" % (x, y)
            drawTextAtPoint(text, (posX, posY), scale, attributes=attributes, xAlign="center", yAlign="top")

# Anchors

def drawGlyphAnchors(glyph, scale, rect, drawAnchor=True, drawText=True, color=None, backgroundColor=None):
    if not glyph.anchors:
        return
    if color is None:
        color = getDefaultColor("glyphAnchor")
    fallbackColor = color
    if backgroundColor is None:
        backgroundColor = getDefaultColor("background")
    anchorSize = 5 * scale
    anchorHalfSize = anchorSize / 2
    for anchor in glyph.anchors:
        if anchor.color is not None:
            color = colorToNSColor(anchor.color)
        else:
            color = fallbackColor
        x = anchor.x
        y = anchor.y
        name = anchor.name
        context = NSGraphicsContext.currentContext()
        context.saveGraphicsState()
        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(backgroundColor)
        shadow.setShadowOffset_((0, 0))
        shadow.setShadowBlurRadius_(3)
        shadow.set()
        if drawAnchor:
            r = ((x - anchorHalfSize, y - anchorHalfSize), (anchorSize, anchorSize))
            color.set()
            drawFilledOval(r)
        if drawText and name:
            attributes = {
                NSFontAttributeName : NSFont.systemFontOfSize_(9),
                NSForegroundColorAttributeName : color,
            }
            y -= 2 * scale
            drawTextAtPoint(name, (x, y), scale, attributes, xAlign="center", yAlign="top")
        context.restoreGraphicsState()
