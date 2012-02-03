from AppKit import *

MenuImageBackgroundColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.35, 0.35, 0.37, 1.0)
MenuImageGlyphColor = NSColor.whiteColor()

def MenuImageRepresentationFactory(glyph):
    font = glyph.font
    cellHeight = 60.0
    cellWidth = 60.0
    imageSize = (cellWidth, cellHeight)
    availableHeight = cellHeight * .6
    yBuffer = int((cellHeight - availableHeight) / 2)
    upm = font.info.unitsPerEm
    descender = font.info.descender
    scale = availableHeight / upm
    glyphWidth = glyph.width * scale
    centerOffset = (cellWidth - glyphWidth) * 0.5
    path = glyph.getRepresentation("defconAppKit.NSBezierPath")
    image = NSImage.alloc().initWithSize_(imageSize)
    image.lockFocus()
    bounds = ((0, 0), imageSize)
    MenuImageBackgroundColor.set()
    NSRectFillUsingOperation(bounds, NSCompositeSourceOver)
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(centerOffset, yBuffer)
    transform.scaleXBy_yBy_(scale, scale)
    transform.translateXBy_yBy_(0, abs(descender))
    transform.concat()
    MenuImageGlyphColor.set()
    path.fill()
    image.unlockFocus()
    return image