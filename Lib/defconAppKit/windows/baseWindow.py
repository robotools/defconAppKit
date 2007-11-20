from AppKit import NSColor
import vanilla
import vanilla.dialogs

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
        pass

    def windowDeselectCallback(self, sender):
        pass

    def startProgress(self, text="", tickCount=None):
        from defconAppKit.windows.progressWindow import ProgressWindow
        return ProgressWindow(text, tickCount, self.w)

    def showMessage(self, messageText, informativeText):
        vanilla.dialogs.message(parentWindow=self.w.getNSWindow(), messageText=messageText, informativeText=informativeText)

    def showAskYesNo(self, messageText, informativeText, callback):
        vanilla.dialogs.askYesNo(parentWindow=self.w.getNSWindow(), messageText=messageText, informativeText=informativeText, resultCallback=callback)

    def showGetFile(self, fileTypes, callback, allowsMultipleSelection=False):
        vanilla.dialogs.getFile(fileTypes=fileTypes, allowsMultipleSelection=allowsMultipleSelection,
            parentWindow=self.w.getNSWindow(), resultCallback=callback)

    def showPutFile(self, fileTypes, callback, fileName=None, directory=None, accessoryView=None):
        if accessoryView is not None:
            w, h = accessoryView._posSize[2:]
            accessoryView._nsObject.setFrame_(((0, 0), (w, h)))
            accessoryView = accessoryView._nsObject
        vanilla.dialogs.putFile(fileTypes=fileTypes,
            parentWindow=self.w.getNSWindow(), resultCallback=callback, fileName=fileName, directory=directory, accessoryView=accessoryView)

