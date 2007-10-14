from AppKit import *
from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath

def addCountBadgeToIcon(count, iconImage=None):
    if iconImage is None:
        iconImage = NSImage.alloc().initWithSize_((40, 40))
        iconImage.lockFocus()
        NSColor.colorWithCalibratedRed_green_blue_alpha_(0, 0, 1, .5).set()
        path = NSBezierPath.bezierPath()
        path.appendBezierPathWithOvalInRect_(((0, 0), iconImage.size()))
        path.fill()
        iconImage.unlockFocus()

    # badge text
    textShadow = NSShadow.alloc().init()
    textShadow.setShadowOffset_((2, -2))
    textShadow.setShadowColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(.3, 0, 0, 1.0))
    textShadow.setShadowBlurRadius_(2.0)

    paragraph = NSMutableParagraphStyle.alloc().init()
    paragraph.setAlignment_(NSCenterTextAlignment)
    paragraph.setLineBreakMode_(NSLineBreakByCharWrapping)
    attributes = {
        NSFontAttributeName : NSFont.boldSystemFontOfSize_(12.0),
        NSForegroundColorAttributeName : NSColor.whiteColor(),
        NSParagraphStyleAttributeName : paragraph,
        NSShadowAttributeName : textShadow
    }
    text = NSAttributedString.alloc().initWithString_attributes_(str(count), attributes)
    rectWidth, rectHeight = NSString.stringWithString_(str(count)).sizeWithAttributes_(attributes)
    rectWidth = int(round(rectWidth + 8))
    rectHeight = int(round(rectHeight + 4))
    rectLeft = 0
    rectRight = rectWidth
    rectBottom = 0
    rectTop = int(rectBottom + rectHeight)

    # badge shadow
    badgeShadow = NSShadow.alloc().init()
    badgeShadow.setShadowOffset_((0, -2))
    badgeShadow.setShadowColor_(NSColor.blackColor())
    badgeShadow.setShadowBlurRadius_(4.0)

    # badge path
    badgePath = roundedRectBezierPath(((rectLeft, rectBottom), (rectWidth, rectHeight)), 3)

    # badge image
    badgeWidth = rectWidth + 3
    badgeHeight = rectHeight + 3
    badgeImage = NSImage.alloc().initWithSize_((badgeWidth, badgeHeight))
    badgeImage.lockFocus()
    transform = NSAffineTransform.transform()
    transform.translateXBy_yBy_(1.5, 1.5)
    transform.concat()
    NSColor.colorWithCalibratedRed_green_blue_alpha_(.2, .2, .25, 1.0).set()
    badgePath.fill()
    NSColor.colorWithCalibratedRed_green_blue_alpha_(.8, .8, .9, 1.0).set()
    badgePath.setLineWidth_(1.0)
    badgePath.stroke()
    text.drawInRect_(((0, -1), (rectWidth, rectHeight)))
    badgeImage.unlockFocus()

    # make the composite image
    imageWidth, imageHeight = iconImage.size()
    imageWidth += (badgeWidth - 15)
    imageHeight += 10

    badgeLeft = imageWidth - badgeWidth - 3
    badgeBottom = 3

    image = NSImage.alloc().initWithSize_((imageWidth, imageHeight))
    image.lockFocus()
    context = NSGraphicsContext.currentContext()

    # icon
    iconImage.drawAtPoint_fromRect_operation_fraction_(
        (0, 10), ((0, 0), iconImage.size()), NSCompositeSourceOver, 1.0)

    # badge
    context.saveGraphicsState()
    badgeShadow.set()
    badgeImage.drawAtPoint_fromRect_operation_fraction_(
        (badgeLeft, badgeBottom), ((0, 0), badgeImage.size()), NSCompositeSourceOver, 1.0)
    context.restoreGraphicsState()

    # done
    image.unlockFocus()
    return image

