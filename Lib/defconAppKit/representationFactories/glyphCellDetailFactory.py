from AppKit import *
from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath

def GlyphCellDetailFactory(glyph, font):
    imageWidth = 200
    imageHeight = 280

    scale = 120 / font.info.unitsPerEm
    glyphLeftOffset = (imageWidth - (glyph.width * scale)) / 2

    basePath = roundedRectBezierPath(((.5, .5), (imageWidth - 1, imageHeight - 1)), 7)
    basePath.setLineWidth_(1.0)

    glyphPath = glyph.getRepresentation("NSBezierPath")

    line1Path = NSBezierPath.bezierPath()
    line1Path.moveToPoint_((1, 120.5))
    line1Path.lineToPoint_((imageWidth-1, 120.5))
    line1Path.setLineWidth_(1.0)

    line2Path = NSBezierPath.bezierPath()
    line2Path.moveToPoint_((1, 121.5))
    line2Path.lineToPoint_((imageWidth-1, 121.5))
    line2Path.setLineWidth_(1.0)

    lineColor = NSColor.colorWithCalibratedWhite_alpha_(.5, 1.0)

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
    width = round(width, 3)
    if width == int(width):
        width = int(width)
    widthText = NSAttributedString.alloc().initWithString_attributes_(str(width), rightAttributes)

    leftTitle = NSAttributedString.alloc().initWithString_attributes_("Left Margin", leftAttributes)
    leftMargin = glyph.leftMargin
    if leftMargin is None:
        leftMargin = 0
    leftMargin = round(leftMargin, 3)
    if leftMargin == int(leftMargin):
        leftMargin = int(leftMargin)
    leftText = NSAttributedString.alloc().initWithString_attributes_(str(leftMargin), rightAttributes)

    rightTitle = NSAttributedString.alloc().initWithString_attributes_("Right Margin", leftAttributes)
    rightMargin = glyph.rightMargin
    if rightMargin is None:
        rightMargin = 0
    rightMargin = round(rightMargin, 3)
    if rightMargin == int(rightMargin):
        rightMargin = int(rightMargin)
    rightText = NSAttributedString.alloc().initWithString_attributes_(str(rightMargin), rightAttributes)

    image = NSImage.alloc().initWithSize_((imageWidth, imageHeight))
    image.setFlipped_(True)
    image.lockFocus()

    NSColor.colorWithCalibratedWhite_alpha_(0, .65).set()
    basePath.fill()
    lineColor.set()
    basePath.stroke()

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

    lineColor.set()
    line1Path.stroke()
    NSColor.colorWithCalibratedWhite_alpha_(0, .5).set()
    line2Path.stroke()

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

