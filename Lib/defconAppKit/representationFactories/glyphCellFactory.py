from AppKit import *

GlyphCellHeaderHeight = 14
GlyphCellMinHeightForHeader = 40

cellHeaderBaseColor = NSColor.colorWithCalibratedWhite_alpha_(.6, .4)
cellHeaderHighlightColor = NSColor.colorWithCalibratedWhite_alpha_(.7, .4)
cellHeaderSelectionColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .3, .7, .15)
cellHeaderLineColor = NSColor.colorWithCalibratedWhite_alpha_(0, .2)
cellHeaderHighlightLineColor = NSColor.colorWithCalibratedWhite_alpha_(1, .5)
cellMetricsLineColor = NSColor.colorWithCalibratedWhite_alpha_(0, .08)
cellMetricsFillColor = NSColor.colorWithCalibratedWhite_alpha_(0, .08)



def GlyphCellFactory(glyph, font, width, height, drawHeader=False, drawMetrics=False):
    obj = GlyphCellFactoryDrawingController(glyph=glyph, font=font, width=width, height=height, drawHeader=drawHeader, drawMetrics=drawMetrics)
    return obj.getImage()


class GlyphCellFactoryDrawingController(object):

    def __init__(self, glyph, font, width, height, drawHeader=False, drawMetrics=False):
        self.glyph = glyph
        self.font = font
        self.width = width
        self.height = height
        self.bufferPercent = .2
        self.shouldDrawHeader = drawHeader
        self.shouldDrawMetrics = drawMetrics

        self.headerHeight = 0
        if drawHeader:
            self.headerHeight = GlyphCellHeaderHeight
        availableHeight = (height - self.headerHeight) * (1.0 - (self.bufferPercent * 2))
        self.buffer = height * self.bufferPercent
        self.scale = availableHeight / font.info.unitsPerEm
        self.xOffset = (width - (glyph.width * self.scale)) / 2
        self.yOffset = abs(font.info.descender * self.scale) + self.buffer

    def getImage(self):
        image = NSImage.alloc().initWithSize_((self.width, self.height))
        image.setFlipped_(True)
        image.lockFocus()
        context = NSGraphicsContext.currentContext()
        bodyRect = ((0, 0), (self.width, self.height-self.headerHeight))
        headerRect = ((0, -self.height+self.headerHeight), (self.width, self.headerHeight))
        # background
        context.saveGraphicsState()
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(0, self.height-self.headerHeight)
        transform.scaleXBy_yBy_(1.0, -1.0)
        transform.concat()
        self.drawCellBackground(bodyRect)
        context.restoreGraphicsState()
        # glyph
        if self.shouldDrawMetrics:
            self.drawCellHorizontalMetrics(bodyRect)
            self.drawCellVerticalMetrics(bodyRect)
        context.saveGraphicsState()
        NSBezierPath.clipRect_(((0, 0), (self.width, self.height-self.headerHeight)))
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(self.xOffset, self.yOffset)
        transform.scaleBy_(self.scale)
        transform.concat()
        self.drawCellGlyph()
        context.restoreGraphicsState()
        # header
        if self.shouldDrawHeader:
            context.saveGraphicsState()
            transform = NSAffineTransform.transform()
            transform.translateXBy_yBy_(0, self.headerHeight)
            transform.scaleXBy_yBy_(1.0, -1.0)
            transform.concat()
            self.drawCellHeaderBackground(headerRect)
            self.drawCellHeaderText(headerRect)
            context.restoreGraphicsState()
        # done
        image.unlockFocus()
        return image

    def drawCellBackground(self, rect):
        pass

    def drawCellHorizontalMetrics(self, rect):
        (xMin, yMin), (width, height) = rect
        glyph = self.glyph
        font = self.font
        scale = self.scale
        yOffset = self.yOffset
        path = NSBezierPath.bezierPath()
        lines = set((0, font.info.descender, font.info.xHeight, font.info.capHeight, font.info.ascender))
        for y in lines:
            y = round((y * scale) + yMin + yOffset) - .5
            path.moveToPoint_((xMin, y))
            path.lineToPoint_((xMin + width, y))
        cellMetricsLineColor.set()
        path.setLineWidth_(1.0)
        path.stroke()

    def drawCellVerticalMetrics(self, rect):
        (xMin, yMin), (width, height) = rect
        glyph = self.glyph
        scale = self.scale
        xOffset = self.xOffset
        left = round((0 * scale) + xMin + xOffset) - .5
        right = round((glyph.width * scale) + xMin + xOffset) - .5
        rects = [
            ((xMin, yMin), (left - xMin, height)),
            ((xMin + right, yMin), (width - xMin + right, height))
        ]
        cellMetricsFillColor.set()
        NSRectFillListUsingOperation(rects, len(rects), NSCompositeSourceOver)

    def drawCellGlyph(self):
        NSColor.blackColor().set()
        path = self.glyph.getRepresentation("NSBezierPath")
        path.fill()

    def drawCellHeaderBackground(self, rect):
        (xMin, yMin), (width, height) = rect
        # background
        try:
            gradient = NSGradient.alloc().initWithColors_([cellHeaderHighlightColor, cellHeaderBaseColor])
            gradient.drawInRect_angle_(rect, 90)
        except NameError:
            cellHeaderBaseColor.set()
            NSRectFill(rect)
        # left and right line
        cellHeaderHighlightLineColor.set()
        sizePath = NSBezierPath.bezierPath()
        sizePath.moveToPoint_((xMin + .5, yMin))
        sizePath.lineToPoint_((xMin + .5, yMin + height))
        sizePath.moveToPoint_((xMin + width - 1.5, yMin))
        sizePath.lineToPoint_((xMin + width - 1.5, yMin + height))
        sizePath.setLineWidth_(1.0)
        sizePath.stroke()
        # bottom line
        cellHeaderLineColor.set()
        bottomPath = NSBezierPath.bezierPath()
        bottomPath.moveToPoint_((xMin, yMin + height - .5))
        bottomPath.lineToPoint_((xMin + width, yMin + height - .5))
        bottomPath.setLineWidth_(1.0)
        bottomPath.stroke()

    def drawCellHeaderText(self, rect):
        paragraph = NSMutableParagraphStyle.alloc().init()
        paragraph.setAlignment_(NSCenterTextAlignment)
        paragraph.setLineBreakMode_(NSLineBreakByTruncatingMiddle)
        shadow = NSShadow.alloc().init()
        shadow.setShadowColor_(NSColor.whiteColor())
        shadow.setShadowOffset_((0, 1))
        shadow.setShadowBlurRadius_(1)
        attributes = {
            NSFontAttributeName : NSFont.systemFontOfSize_(10.0),
            NSForegroundColorAttributeName : NSColor.colorWithCalibratedRed_green_blue_alpha_(.22, .22, .27, 1.0),
            NSParagraphStyleAttributeName : paragraph,
            NSShadowAttributeName : shadow
        }
        text = NSAttributedString.alloc().initWithString_attributes_(self.glyph.name, attributes)
        text.drawInRect_(rect)

