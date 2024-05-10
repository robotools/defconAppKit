from AppKit import NSColor, NSScrollView, NSRectFill, NSRectFillUsingOperation, NSBezierPath, \
    NSCompositeSourceOver, NSPopUpButtonCell, NSSegmentedCell, NSGradientConvexStrong
from objc import super
import vanilla
import platform

inOS104 = platform.mac_ver()[0].startswith("10.4.")

placardBorderColor = NSColor.colorWithCalibratedWhite_alpha_(.5, .7)


class DefconAppKitPlacardNSScrollView(NSScrollView):

    def dealloc(self):
        if hasattr(self, "placard"):
            del self.placard
        super(DefconAppKitPlacardNSScrollView, self).dealloc()

    def tile(self):
        super(DefconAppKitPlacardNSScrollView, self).tile()
        if self.window() is None:
            return
        if hasattr(self, "placard"):
            placardWidth = self.placard.frame().size[0]
            scroller = self.horizontalScroller()
            (x, y), (w, h) = scroller.frame()
            if w > 0 and h > 0:
                scroller.setFrame_(((x + placardWidth, y), (w - placardWidth, h)))
            self.placard.setFrame_(((x, y), (placardWidth, h)))

    def setPlacard_(self, view):
        if hasattr(self, "placard") and self.placard is not None:
            self.placard.removeFromSuperview()
            self.placard = None
        self.placard = view
        self.addSubview_(view)
        self.setNeedsDisplay_(True)


class PlacardScrollView(vanilla.ScrollView):

    nsScrollViewClass = DefconAppKitPlacardNSScrollView

    def setPlacard(self, placard):
        if isinstance(placard, vanilla.VanillaBaseObject):
            placard = placard.getNSView()
        self._nsObject.setPlacard_(placard)


# -------------
# Button Colors
# -------------

placardGradientColor1 = NSColor.whiteColor()
placardGradientColor2 = NSColor.colorWithCalibratedWhite_alpha_(.9, 1)
placardGradientColorFallback = NSColor.colorWithCalibratedWhite_alpha_(.95, 1)

# ----------------
# Segmented Button
# ----------------


class DefconAppKitPlacardNSSegmentedCell(NSSegmentedCell):

    def drawingRectForBounds_(self, rect):
        return rect

    def cellSizeForBounds_(self, rect):
        return rect.size

    def drawWithFrame_inView_(self, frame, view):
        # draw background
        try:
            gradient = NSGradient.alloc().initWithColors_([placardGradientColor1, placardGradientColor2])
            gradient.drawInRect_angle_(frame, 90)
        except NameError:
            placardGradientColorFallback.set()
            NSRectFill(frame)
        # draw border
        (x, y), (w, h) = frame
        path = NSBezierPath.bezierPath()
        path.moveToPoint_((x + w - .5, h))
        path.lineToPoint_((x + w - .5, .5))
        path.lineToPoint_((x, .5))
        path.setLineWidth_(1.0)
        placardBorderColor.set()
        path.stroke()
        # draw segments
        x, y = frame.origin
        h = frame.size[1]
        for index in range(self.segmentCount()):
            w = self.widthForSegment_(index)
            self.drawSegment_inFrame_withView_(index, ((x, y), (w, h)), view)
            x += w

    def drawSegment_inFrame_withView_(self, segment, frame, view):
        (x, y), (w, h) = frame
        # draw highlight
        if self.isSelectedForSegment_(segment):
            NSColor.colorWithCalibratedWhite_alpha_(0, .2).set()
            NSRectFillUsingOperation(frame, NSCompositeSourceOver)
        # draw border
        if segment != 0:
            path = NSBezierPath.bezierPath()
            path.moveToPoint_((x + .5, y + h))
            path.lineToPoint_((x + .5, y))
            path.setLineWidth_(1.0)
            placardBorderColor.set()
            path.stroke()
            x += 1
        # draw image
        image = self.imageForSegment_(segment)
        if image is not None:
            image.drawAtPoint_fromRect_operation_fraction_((x, y), ((0, 0), image.size()), NSCompositeSourceOver, 1.0)


class PlacardSegmentedButton(vanilla.SegmentedButton):

    nsSegmentedCellClass = DefconAppKitPlacardNSSegmentedCell


# ------------
# PopUp Button
# ------------

class DefconAppKitPlacardNSPopUpButtonCell(NSPopUpButtonCell):

    def init(self):
        self = super(DefconAppKitPlacardNSPopUpButtonCell, self).init()
        self._backgroundColor = None
        return self

    def setBackgroundColor_(self, color):
        self._backgroundColor = color

    def drawBorderAndBackgroundWithFrame_inView_(self, frame, view):
        # draw background
        if self._backgroundColor is not None:
            self._backgroundColor.set()
            NSRectFill(frame)
        else:
            try:
                gradient = NSGradient.alloc().initWithColors_([placardGradientColor1, placardGradientColor2])
                gradient.drawInRect_angle_(frame, 90)
            except NameError:
                placardGradientColorFallback.set()
                NSRectFill(frame)
        # draw border
        (x, y), (w, h) = frame
        path = NSBezierPath.bezierPath()
        path.moveToPoint_((x + w - .5, h))
        path.lineToPoint_((x + w - .5, .5))
        path.lineToPoint_((x, .5))
        path.setLineWidth_(1.0)
        NSColor.colorWithCalibratedWhite_alpha_(.5, .7).set()
        path.stroke()
        # let the super do the rest
        w -= 1
        if inOS104:
            w -= 4
        frame = ((x, y), (w, h))
        super(DefconAppKitPlacardNSPopUpButtonCell, self).drawBorderAndBackgroundWithFrame_inView_(frame, view)


class PlacardPopUpButton(vanilla.PopUpButton):

    nsPopUpButtonCellClass = DefconAppKitPlacardNSPopUpButtonCell

    def __init__(self, posSize, items, **kwargs):
        super(PlacardPopUpButton, self).__init__(posSize, items, **kwargs)
        self._nsObject.setBordered_(False)
        self._nsObject.cell().setGradientType_(NSGradientConvexStrong)

    def setBackgroundColor(self, color):
        self._nsObject.cell().setBackgroundColor_(color)