from AppKit import *
import vanilla


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
        self._nsObject.setPlacard_(placard)


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
            gray = NSColor.colorWithCalibratedWhite_alpha_(.9, 1)
            white = NSColor.whiteColor()
            gradient = NSGradient.alloc().initWithColors_([white, gray])
            gradient.drawInRect_angle_(frame, 90)
        except NameError:
            NSColor.colorWithCalibratedWhite_alpha_(.95, 1).set()
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
        for index in xrange(self.segmentCount()):
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

