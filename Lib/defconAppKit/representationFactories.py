from __future__ import division
from AppKit import *


def registerAllFactories():
    from defcon.objects.glyph import addRepresentationFactory
    addRepresentationFactory("NSBezierPath", NSBezierPathFactory)
    addRepresentationFactory("defconAppKitGlyphCell", GlyphCellFactory)
    addRepresentationFactory("defconAppKitGlyphCellDetail", GlyphCellDetailFactory)


def NSBezierPathFactory(glyph, font):
    from fontTools.pens.cocoaPen import CocoaPen
    pen = CocoaPen(font)
    glyph.draw(pen)
    return pen.path


GlyphCellHeaderHeight = 14
GlyphCellMinHeightForHeader = 40

def GlyphCellFactory(glyph, font, width, height, bufferPercent=.2, color=(0, 0, 0, 1), drawHeader=False, drawMetrics=False):
    if drawHeader:
        headerHeight = GlyphCellHeaderHeight
    else:
        headerHeight = 0
    availableHeight = (height - headerHeight) * (1.0 - (bufferPercent * 2))
    buffer = height * bufferPercent
    scale = availableHeight / font.info.unitsPerEm
    xOffset = (width - (glyph.width * scale)) / 2
    yOffset = abs(font.info.descender * scale) + buffer

    image = NSImage.alloc().initWithSize_((width, height))
    image.setFlipped_(True)
    image.lockFocus()

    # metrics

    if drawMetrics:
        NSColor.colorWithCalibratedWhite_alpha_(0, .08).set()
        path = NSBezierPath.bezierPath()
        path.moveToPoint_((0, int(yOffset) - .5))
        path.lineToPoint_((width, int(yOffset) - .5))
        path.setLineWidth_(1.0)
        path.stroke()
        path = NSBezierPath.bezierPath()
        path.appendBezierPathWithRect_(((0, 0), (int(xOffset) - .5, height - headerHeight)))
        w = glyph.width * scale
        path.appendBezierPathWithRect_(((int(xOffset + w) - .5, 0), (int(xOffset + w) - .5, height - headerHeight)))
        path.fill()

    # glyph

    context = NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(xOffset, yOffset)
    transform.scaleBy_(scale)
    transform.concat()

    r, g, b, a = color
    NSColor.colorWithCalibratedRed_green_blue_alpha_(r, g, b, a).set()

    path = glyph.getRepresentation("NSBezierPath")
    path.fill()
    context.restoreGraphicsState()

    # header

    if drawHeader:
        headerRect = ((0, -height+headerHeight), (width, headerHeight))
        headerColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.5, .5, .55, .4)
        headerShadowColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.25, .25, .3, .5)

        paragraph = NSMutableParagraphStyle.alloc().init()
        paragraph.setAlignment_(NSCenterTextAlignment)
        paragraph.setLineBreakMode_(NSLineBreakByTruncatingMiddle)
        shadow = NSShadow.alloc().init()
        shadow.setShadowOffset_((1, 1))
        shadow.setShadowColor_(NSColor.whiteColor())
        shadow.setShadowBlurRadius_(1.0)
        attributes = {
            NSFontAttributeName : NSFont.systemFontOfSize_(10.0),
            NSForegroundColorAttributeName : NSColor.colorWithCalibratedRed_green_blue_alpha_(.12, .12, .17, 1.0),
            NSParagraphStyleAttributeName : paragraph,
            NSShadowAttributeName : shadow
        }
        text = NSAttributedString.alloc().initWithString_attributes_(glyph.name, attributes)

        context.saveGraphicsState()
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(0, headerHeight)
        transform.scaleXBy_yBy_(1.0, -1.0)
        transform.concat()
        headerColor.set()
        NSRectFill(headerRect)
        context.restoreGraphicsState()

        context.saveGraphicsState()
        shadow = NSShadow.alloc().init()
        shadow.setShadowOffset_((0, -5))
        shadow.setShadowColor_(headerShadowColor)
        shadow.setShadowBlurRadius_(10.0)
        shadow.set()
        NSBezierPath.clipRect_(((0, height - headerHeight), (width, headerHeight)))
        NSColor.whiteColor().set()
        NSRectFill(((-10, 0), (width + 20, height - headerHeight)))
        context.restoreGraphicsState()

        context.saveGraphicsState()
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(0, headerHeight)
        transform.scaleXBy_yBy_(1.0, -1.0)
        transform.concat()
        text.drawInRect_(headerRect)
        context.restoreGraphicsState()

    image.unlockFocus()

    return image


def GlyphCellDetailFactory(glyph, font):
    from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath

    imageWidth = 200
    imageHeight = 280

    scale = 120 / font.info.unitsPerEm
    glyphLeftOffset = (imageWidth - (glyph.width * scale)) / 2

    basePath = roundedRectBezierPath(((.5, .5), (imageWidth - 1, imageHeight - 1)), 7)

    glyphPath = glyph.getRepresentation("NSBezierPath")

    linePath = NSBezierPath.bezierPath()
    linePath.moveToPoint_((10, 120.5))
    linePath.lineToPoint_((imageWidth - 10, 120.5))
    linePath.setLineWidth_(1.0)

    paragraph = NSMutableParagraphStyle.alloc().init()
    paragraph.setAlignment_(NSRightTextAlignment)
    paragraph.setLineBreakMode_(NSLineBreakByCharWrapping)
    leftAttributes = {
        NSFontAttributeName : NSFont.systemFontOfSize_(12.0),
        NSForegroundColorAttributeName : NSColor.whiteColor(),
        NSParagraphStyleAttributeName : paragraph
    }

    paragraph = NSMutableParagraphStyle.alloc().init()
    paragraph.setAlignment_(NSLeftTextAlignment)
    paragraph.setLineBreakMode_(NSLineBreakByTruncatingMiddle)
    rightAttributes = {
        NSFontAttributeName : NSFont.systemFontOfSize_(12.0),
        NSForegroundColorAttributeName : NSColor.whiteColor(),
        NSParagraphStyleAttributeName : paragraph
    }

    nameTitle = NSAttributedString.alloc().initWithString_attributes_("Name", leftAttributes)
    nameText = NSAttributedString.alloc().initWithString_attributes_(glyph.name, rightAttributes)

    uniTitle = NSAttributedString.alloc().initWithString_attributes_("Unicode", leftAttributes)
    uni = glyph.unicode
    if uni is None:
        uni = ""
    else:
        uni = hex(uni)[2:].upper()
        if len(uni) < 4:
            uni = uni.zfill(4)
    uniText = NSAttributedString.alloc().initWithString_attributes_(str(uni), rightAttributes)

    widthTitle = NSAttributedString.alloc().initWithString_attributes_("Width", leftAttributes)
    width = glyph.width
    if width is None:
        width = 0
    width = round(width)
    if width == int(width):
        width = int(width)
    widthText = NSAttributedString.alloc().initWithString_attributes_(str(width), rightAttributes)

    leftTitle = NSAttributedString.alloc().initWithString_attributes_("Left Margin", leftAttributes)
    leftMargin = glyph.leftMargin
    if leftMargin is None:
        leftMargin = 0
    leftMargin = round(leftMargin)
    if leftMargin == int(leftMargin):
        leftMargin = int(leftMargin)
    leftText = NSAttributedString.alloc().initWithString_attributes_(str(leftMargin), rightAttributes)

    rightTitle = NSAttributedString.alloc().initWithString_attributes_("Right Margin", leftAttributes)
    rightMargin = glyph.rightMargin
    if rightMargin is None:
        rightMargin = 0
    rightMargin = round(rightMargin)
    if rightMargin == int(rightMargin):
        rightMargin = int(rightMargin)
    rightText = NSAttributedString.alloc().initWithString_attributes_(str(rightMargin), rightAttributes)

    image = NSImage.alloc().initWithSize_((imageWidth, imageHeight))
    image.setFlipped_(True)
    image.lockFocus()

    NSColor.colorWithCalibratedWhite_alpha_(0, .65).set()
    basePath.fill()

    context = NSGraphicsContext.currentContext()
    context.saveGraphicsState()
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(glyphLeftOffset, 145)
    transform.scaleBy_(scale)
    transform.translateXBy_yBy_(0, -font.info.descender)
    transform.concat()

    NSColor.whiteColor().set()
    glyphPath.fill()
    context.restoreGraphicsState()

    NSColor.whiteColor().set()
    linePath.stroke()

    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(0, 110)
    transform.scaleXBy_yBy_(1.0, -1.0)
    transform.concat()

    nameTitle.drawInRect_(((0, 0), (90, 17)))
    nameText.drawInRect_(((95, 0), (85, 17)))

    uniTitle.drawInRect_(((0, 20), (90, 17)))
    uniText.drawInRect_(((95, 20), (85, 17)))

    widthTitle.drawInRect_(((0, 40), (90, 17)))
    widthText.drawInRect_(((95, 40), (85, 17)))

    leftTitle.drawInRect_(((0, 60), (90, 17)))
    leftText.drawInRect_(((95, 60), (85, 17)))

    rightTitle.drawInRect_(((0, 80), (90, 17)))
    rightText.drawInRect_(((95, 80), (85, 17)))

    image.unlockFocus()
    return image
