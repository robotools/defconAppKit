from AppKit import *

pillTextAttributes = {
        NSFontAttributeName : NSFont.fontWithName_size_("Helvetica Bold", 12.0),
        NSForegroundColorAttributeName : NSColor.whiteColor()
}

pillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.75, .75, .8, 1.0)


class DefconAppKitPillCell(NSActionCell):

    def drawWithFrame_inView_(self, frame, view):
        row = view.selectedRow()
        columnCount = len(view.tableColumns())
        frames = [view.frameOfCellAtColumn_row_(i, row) for i in xrange(columnCount)]
        selected = frame in frames

        (x, y), (w, h) = frame
        y += 1
        h -= 2

        if selected:
            pillTextAttributes[NSForegroundColorAttributeName] = pillColor
            foregroundColor = NSColor.whiteColor()
        else:
            pillTextAttributes[NSForegroundColorAttributeName] = NSColor.whiteColor()
            foregroundColor = pillColor

        text = self.title()
        text = NSAttributedString.alloc().initWithString_attributes_(text, pillTextAttributes)
        textRect = text.boundingRectWithSize_options_((w, h), 0)
        (textX, textY), (textW, textH) = textRect

        foregroundColor.set()
        path = NSBezierPath.bezierPath()
        radius = h / 2.0
        path.appendBezierPathWithOvalInRect_(((x, y), (h, h)))
        path.appendBezierPathWithOvalInRect_(((x + textW - 1, y), (h, h)))
        path.appendBezierPathWithRect_(((x + radius, y), (textW - 1, h)))
        path.fill()
        text.drawInRect_(((x + radius, y), (textW, textH)))


def PillListCell():
    return DefconAppKitPillCell.alloc().init()

