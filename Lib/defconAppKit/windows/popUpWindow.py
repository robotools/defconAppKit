import time
from AppKit import *
from Foundation import *
import vanilla
from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath


# ----------
# Basic View
# ----------


HUDWindowLineColor = NSColor.colorWithCalibratedWhite_alpha_(.5, 1.0)
HUDWindowColor = NSColor.colorWithCalibratedWhite_alpha_(0, .65)


class DefconAppKitInformationPopUpWindowContentView(NSView):

    def drawRect_(self, rect):
        rect = self.bounds()
        rect = NSInsetRect(rect, .5, .5)
        path = roundedRectBezierPath(rect, 7)
        HUDWindowColor.set()
        path.fill()
        HUDWindowLineColor.set()
        path.stroke()


class InformationPopUpWindow(vanilla.FloatingWindow):

    nsWindowStyleMask = NSBorderlessWindowMask
    nsWindowLevel = NSTornOffMenuWindowLevel

    def __init__(self, posSize):
        super(InformationPopUpWindow, self).__init__(posSize, "", minSize=None,
                maxSize=None, textured=False, autosaveName=None,
                closable=False, initiallyVisible=False)
        contentView = DefconAppKitInformationPopUpWindowContentView.alloc().init()
        self._window.setContentView_(contentView)
        self._window.setBackgroundColor_(NSColor.clearColor())
        self._window.setAlphaValue_(0.0)
        self._window.setOpaque_(False)
        self._window.setHasShadow_(True)
        self._window.setMovableByWindowBackground_(False)

    # -----------------------------
    # methods requiring fade in/out
    # -----------------------------

    def _fadeIn(self):
        stepValue = .2
        current = self._window.alphaValue()
        steps = int((1.0 - current) / stepValue)
        for i in xrange(steps):
            a = self._window.alphaValue() + stepValue
            if a > 1.0:
                a = 1.0
            self._window.setAlphaValue_(a)
            if i != steps - 1:
                time.sleep(.02)
        self._window.setAlphaValue_(1.0)

    def _fadeOut(self):
        stepValue = .2
        current = self._window.alphaValue()
        steps = int(current / stepValue)
        for i in xrange(steps):
            a = self._window.alphaValue() - stepValue
            if a < 0:
                a = 0
            self._window.setAlphaValue_(a)
            if i != steps - 1:
                time.sleep(.02)
        self._window.setAlphaValue_(0.0)

    def open(self):
        super(InformationPopUpWindow, self).open()
        self._fadeIn()

    def close(self):
        self._fadeOut()
        super(InformationPopUpWindow, self).close()

    def show(self):
        super(InformationPopUpWindow, self).show()
        self._fadeIn()

    def hide(self):
        self._fadeOut()
        super(InformationPopUpWindow, self).hide()

    # --------------------------
    # special positioning method
    # --------------------------

    def setPositionNearCursor(self, (x, y)):
        screen = self._window.screen()
        if screen is None:
            return
        screenFrame = screen.visibleFrame()
        (screenMinX, screenMinY), (screenW, screenH) = screenFrame
        screenMaxX = screenMinX + screenW
        screenMaxY = screenMinY + screenH

        cursorOffset = 16

        x += cursorOffset
        y -= cursorOffset

        windowW, windowH = self._window.frame().size
        if x + windowW > screenMaxX:
            x = x - windowW - (cursorOffset * 2)
        elif x < screenMinX:
            x = screenMinX + cursorOffset
        if y > screenMaxY:
            y = screenMaxY
        elif y - windowH < screenMinY:
            y = screenMinY + windowH

        self._window.setFrameTopLeftPoint_((x, y))


class HUDTextBox(vanilla.TextBox):

    def __init__(self, *args, **kwargs):
        super(HUDTextBox, self).__init__(*args, **kwargs)
        self._nsObject.setTextColor_(NSColor.whiteColor())


class HUDNSLineView(NSView):

    def drawRect_(self, rect):
        HUDWindowLineColor.set()
        NSRectFill(rect)


class HUDHorizontalLine(vanilla.VanillaBaseObject):

    def __init__(self, posSize):
        self._setupView(HUDNSLineView, posSize)


class HUDVerticalLine(HUDHorizontalLine):

    def __init__(self, posSize):
        self._setupView(HUDNSLineView, posSize)


# ----------------
# Interactive View
# ----------------

interactiveWindowColor = NSColor.colorWithCalibratedWhite_alpha_(.9, .9)


class DefconAppKitInteractivePopUpNSWindow(NSPanel):

    def canBecomeKeyWindow(self):
        return True


class DefconAppKitInteractivePopUpWindowContentView(NSView):

    def drawRect_(self, rect):
        rect = self.bounds()
        path = roundedRectBezierPath(rect, 5)
        interactiveWindowColor.set()
        path.fill()


class InteractivePopUpWindow(vanilla.Window):

    nsWindowClass = DefconAppKitInteractivePopUpNSWindow
    nsWindowStyleMask = NSBorderlessWindowMask
    contentViewClass = DefconAppKitInteractivePopUpWindowContentView

    def __init__(self, posSize):
        super(InteractivePopUpWindow, self).__init__(posSize)
        self._window.setMovableByWindowBackground_(True)

        # set the background
        contentView = self.contentViewClass.alloc().init()
        self._window.setContentView_(contentView)
        self._window.setOpaque_(False)
        self._window.setBackgroundColor_(NSColor.clearColor())

        # set up the window to close when it loses focus
        self.bind("resigned key", self.windowDeselectCallback)
        self._closing = False

        # open and fade in
        self.open()
        self._window.setAlphaValue_(0.0)
        for i in xrange(5):
            a = i * .2
            self._window.setAlphaValue_(a)
            time.sleep(.02)
        self._window.setAlphaValue_(1.0)

    def windowDeselectCallback(self, sender):
        if self._closing:
            return
        self.close()

    def close(self):
        self._closing = True
        for i in xrange(5):
            a = 1.0 - (i * .2)
            self._window.setAlphaValue_(a)
            time.sleep(.02)
        super(InteractivePopUpWindow, self).close()
