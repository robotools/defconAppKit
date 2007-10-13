from AppKit import NSColor
import vanilla
import vanilla.dialogs
from defconAppKit.windows.progressWindow import ProgressWindow

class BaseWindowController(object):

    def setUpBaseWindowBehavior(self):
        self.w.bind("close", self.windowCloseCallback)
        if isinstance(self.w, vanilla.Sheet):
            self.w.bind("became key", self.windowSelectCallback)
            self.w.bind("resigned key", self.windowDeselectCallback)
        else:
            self.w.bind("became main", self.windowSelectCallback)
            self.w.bind("resigned main", self.windowDeselectCallback)

    def windowCloseCallback(self, sender):
        self.w.unbind("close", self.windowCloseCallback)
        if isinstance(self.w, vanilla.Sheet):
            self.w.unbind("became key", self.windowSelectCallback)
            self.w.unbind("resigned key", self.windowDeselectCallback)
        else:
            self.w.unbind("became main", self.windowSelectCallback)
            self.w.unbind("resigned main", self.windowDeselectCallback)

    def windowSelectCallback(self, sender):
        nsWindow = self.w.getNSWindow()
        color = NSColor.colorWithCalibratedRed_green_blue_alpha_(.84, .84, .84, 1.0)
        nsWindow.setBackgroundColor_(color)
        nsWindow.contentView().setNeedsDisplay_(True)

    def windowDeselectCallback(self, sender):
        nsWindow = self.w.getNSWindow()
        if nsWindow is not None:
            nsWindow.setBackgroundColor_(None)
            nsWindow.contentView().setNeedsDisplay_(True)

    def startProgress(self, text="", tickCount=None):
        return ProgressWindow(text, tickCount, self.w)

    def showMessage(self, messageText, informativeText):
        vanilla.dialogs.message(parentWindow=self.w.getNSWindow(), messageText=messageText, informativeText=informativeText)

    def showAskYesNo(self, messageText, informativeText, callback):
        vanilla.dialogs.askYesNo(parentWindow=self.w.getNSWindow(), messageText=messageText, informativeText=informativeText, resultCallback=callback)

    def showGetFile(self, fileTypes, callback, allowsMultipleSelection=False):
        vanilla.dialogs.getFile(fileTypes=fileTypes, allowsMultipleSelection=allowsMultipleSelection,
            parentWindow=self.w.getNSWindow(), resultCallback=callback)

    def showPutFile(self, fileTypes, callback, accessoryView=None):
        if accessoryView is not None:
            w, h = accessoryView._posSize[2:]
            accessoryView._nsObject.setFrame_(((0, 0), (w, h)))
            accessoryView = accessoryView._nsObject
        vanilla.dialogs.putFile(fileTypes=fileTypes,
            parentWindow=self.w.getNSWindow(), resultCallback=callback, accessoryView=accessoryView)

