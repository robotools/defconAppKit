import time
from PyObjCTools import NibClassBuilder, AppHelper
from AppKit import *
import vanilla
from defcon import Font
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.windows.progressWindow import ProgressWindow
from defconAppKit.representationFactories import registerAllFactories
from defconAppKit.representationFactories import GlyphCellHeaderHeight, GlyphCellMinHeightForHeader
from defconAppKit.views.glyphCellView import GlyphCellView

registerAllFactories()


import objc
objc.setVerbose(True)

NibClassBuilder.extractClasses("MainMenu")


class DefconAppKitTestDocument(NSDocument):

    def readFromFile_ofType_(self, path, tp):
        progress = ProgressWindow("Opening...")
        try:
            font = Font(path)
            window = self.vanillaWindowController = DefconAppKitTestDocumentWindow(font)
            self.addWindowController_(window.w.getNSWindowController())
        finally:
            progress.close()
        return True


class DefconAppKitTestDocumentWindow(BaseWindowController):

    def __init__(self, font):
        self.font = font
        self.glyphs = [font[k] for k in sorted(font.keys())]
        self.w = vanilla.Window((500, 500), minSize=(400, 400))

        self.w.tabs = vanilla.Tabs((10, 10, -10, -10), ["Window", "GlyphCellView"])
        self.windowTab = self.w.tabs[0]
        self.cellViewTab = self.w.tabs[1]

        self.windowTab.messageButton = vanilla.Button((10, 10, 200, 20), "Show Message", callback=self.windowMessage)
        self.windowTab.progress1Button = vanilla.Button((10, 40, 200, 20), "Show Progress 1", callback=self.windowProgress1)
        self.windowTab.progress2Button = vanilla.Button((10, 70, 200, 20), "Show Progress 2", callback=self.windowProgress2)
        self.windowTab.askYesNoButton = vanilla.Button((10, 100, 200, 20), "Show Ask Yes No", callback=self.windowAskYesNo)
        self.windowTab.putFileButton = vanilla.Button((10, 130, 200, 20), "Show Put File", callback=self.windowPutFile)
        self.windowTab.getFileButton = vanilla.Button((10, 160, 200, 20), "Show Get File", callback=self.windowGetFile)

        # test automatic updating
        self.cellViewTab.cellViewModifyButton = vanilla.Button((10, 10, 150, 20), "Modify Glyphs", callback=self.cellViewModify)
        # test cell sizes
        self.cellViewTab.cellViewSizeSlider = vanilla.Slider((170, 10, 150, 20), minValue=10, maxValue=100, value=50,
            continuous=False, callback=self.cellViewResize)
        # the cell view
        self.cellViewTab.cellView = GlyphCellView((10, 40, -10, -10),
            selectionCallback=self.cellViewSelectionCallback, doubleClickCallback=self.cellViewDoubleClickCallback,
            deleteCallback=self.cellViewDeleteCallback, dropCallback=self.cellViewDropCallback)
        self.cellViewTab.cellView.set(self.glyphs)
        self.cellViewResize(self.cellViewTab.cellViewSizeSlider)

        self.setUpBaseWindowBehavior()

        self.w.tabs.set(1)

        self.w.open()

    # window

    def windowMessage(self, sender):
        self.showMessage("Message text.", "Informative text.")

    def windowProgress1(self, sender):
        progress = self.startProgress("Progress", 30)
        for i in xrange(30):
            progress.update("Progress: %d" % (i + 1))
            time.sleep(.1)
        progress.close()

    def windowProgress2(self, sender):
        progress = self.startProgress("Progress")
        for i in xrange(30):
            time.sleep(.1)
        progress.close()

    def windowAskYesNo(self, sender):
        self.showAskYesNo("Message text.", "Informative text.", self._windowAskYesNoResult)

    def _windowAskYesNoResult(self, result):
        print "Ask Yes No:", result

    def windowPutFile(self, sender):
        self.showPutFile(["txt"], self._windowPutFileResult)

    def _windowPutFileResult(self, result):
        print "Put File:", result

    def windowGetFile(self, sender):
        self.showGetFile(["ufo"], self._windowGetFileResult)

    def _windowGetFileResult(self, result):
        print "Get File:", result

    # cell view

    def cellViewDoubleClickCallback(self, sender):
        print "double click"

    def cellViewDeleteCallback(self, sender):
        print "delete", sender.getSelection()

    def cellViewDropCallback(self, sender, glyphs, testing):
        if not testing:
            for glyph in glyphs:
                self.font.insertGlyph(glyph, name=".glyph%d" % len(self.font))
            self.glyphs = [self.font[k] for k in sorted(self.font.keys())]
            self.cellViewTab.cellView.set(self.glyphs)
        return True

    def cellViewSelectionCallback(self, sender):
        self.cellViewTab.cellView.setSelection(sender.getSelection())

    def cellViewModify(self, sender):
        selection = [self.glyphs[index] for index in self.cellViewTab.cellView.getSelection()]
        for glyph in selection:
            glyph.move((100, 100))

    def cellViewResize(self, sender):
        width = height = int(sender.get())
        drawHeader = height > GlyphCellMinHeightForHeader
        if drawHeader:
            height += GlyphCellHeaderHeight
        self.cellViewTab.cellView.setCellSize((width, height))
        self.cellViewTab.cellView.setCellRepresentationArguments(drawHeader=drawHeader, drawMetrics=drawHeader)


if __name__ == "__main__":
    AppHelper.runEventLoop()
