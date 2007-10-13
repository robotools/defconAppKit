from __future__ import division
from AppKit import *


def registerAllFactories():
    from defcon.objects.glyph import addRepresentationFactory
    addRepresentationFactory("NSBezierPath", NSBezierPathFactory)
    addRepresentationFactory("defconAppKitGlyphCell", GlyphCellFactory)


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

        paragraph = NSMutableParagraphStyle.alloc().init()
        paragraph.setAlignment_(NSCenterTextAlignment)
        paragraph.setLineBreakMode_(NSLineBreakByCharWrapping)
        attributes = {
            NSFontAttributeName : NSFont.systemFontOfSize_(10.0),
            NSForegroundColorAttributeName : NSColor.colorWithCalibratedWhite_alpha_(0, .6),
            NSParagraphStyleAttributeName : paragraph
        }
        text = NSAttributedString.alloc().initWithString_attributes_(glyph.name, attributes)

        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(0, headerHeight)
        transform.scaleXBy_yBy_(1.0, -1.0)
        transform.concat()
        headerColor.set()
        NSRectFill(headerRect)
        text.drawInRect_(headerRect)

    image.unlockFocus()

    return image
    