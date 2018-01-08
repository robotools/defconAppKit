from AppKit import NSFontAttributeName, NSFont, NSForegroundColorAttributeName, NSColor, NSActionCell, \
    NSBezierPath, NSAttributedString


pillTextAttributes = {
    NSFontAttributeName: NSFont.fontWithName_size_("Helvetica Bold", 12.0),
    NSForegroundColorAttributeName: NSColor.whiteColor()
}

pillColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.75, .75, .8, 1.0)


class DefconAppKitPillCell(NSActionCell):

    def setColor_(self, color):
        self._color = color

    def drawWithFrame_inView_(self, frame, view):
        row = view.selectedRow()
        columnCount = len(view.tableColumns())
        frames = [view.frameOfCellAtColumn_row_(i, row) for i in range(columnCount)]
        selected = frame in frames

        (x, y), (w, h) = frame
        y += 1
        h -= 2

        if selected:
            pillTextAttributes[NSForegroundColorAttributeName] = self._color
            foregroundColor = NSColor.whiteColor()
        else:
            pillTextAttributes[NSForegroundColorAttributeName] = NSColor.whiteColor()
            foregroundColor = self._color

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


def PillListCell(color=None):
    cell = DefconAppKitPillCell.alloc().init()
    if color is None:
        color = pillColor
    cell.setColor_(color)
    return cell
