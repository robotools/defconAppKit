import vanilla
import vanilla.dialogs
from defconAppKit.windows.progressWindow import ProgressWindow

class BaseWindowController(object):

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

