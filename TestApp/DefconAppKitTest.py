import time
from PyObjCTools import NibClassBuilder, AppHelper
from AppKit import *
import vanilla
from defcon import Font
from defconAppKit.windows.baseWindow import BaseWindowController
from defconAppKit.windows.progressWindow import ProgressWindow
from defconAppKit.representationFactories import registerAllFactories
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellHeaderHeight, GlyphCellMinHeightForHeader
from defconAppKit.views.glyphCollectionView import GlyphCollectionView
from defconAppKit.views.glyphLineView import GlyphLineView
from defconAppKit.views.glyphNameComboBox import GlyphNameComboBox
from fontAppTools import splitText

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


glyphSortDescriptors = [
    dict(type="alphabetical", allowPseudoUnicode=True),
    dict(type="category", allowPseudoUnicode=True),
    dict(type="unicode", allowPseudoUnicode=True),
    dict(type="script", allowPseudoUnicode=True),
    dict(type="suffix", allowPseudoUnicode=True),
    dict(type="decompositionBase", allowPseudoUnicode=True)
]


class DefconAppKitTestDocumentWindow(BaseWindowController):

    def __init__(self, font):
        self.font = font
        self.glyphs = [font[k] for k in font.unicodeData.sortGlyphNames(font.keys(), glyphSortDescriptors)]
        self.w = vanilla.Window((700, 500), minSize=(400, 400))

        self.w.tabs = vanilla.Tabs((10, 10, -10, -10), ["Window", "GlyphCollectionView", "GlyphLineView", "Misc. Controls"])
        self.windowTab = self.w.tabs[0]
        self.collectionViewTab = self.w.tabs[1]
        self.lineViewTab = self.w.tabs[2]
        self.controlsTab = self.w.tabs[3]

        # test various window methods
        self.windowTab.messageButton = vanilla.Button((10, 10, 200, 20), "Show Message", callback=self.windowMessage)
        self.windowTab.progress1Button = vanilla.Button((10, 40, 200, 20), "Show Progress 1", callback=self.windowProgress1)
        self.windowTab.progress2Button = vanilla.Button((10, 70, 200, 20), "Show Progress 2", callback=self.windowProgress2)
        self.windowTab.askYesNoButton = vanilla.Button((10, 100, 200, 20), "Show Ask Yes No", callback=self.windowAskYesNo)
        self.windowTab.putFileButton = vanilla.Button((10, 130, 200, 20), "Show Put File", callback=self.windowPutFile)
        self.windowTab.getFileButton = vanilla.Button((10, 160, 200, 20), "Show Get File", callback=self.windowGetFile)

        # test cell view
        dropSettings = dict(callback=self.collectionViewDropCallback)
        self.collectionViewTab.collectionViewModifyButton = vanilla.Button((10, 10, 150, 20), "Modify Glyphs", callback=self.collectionViewModify)
        self.collectionViewTab.collectionViewSizeSlider = vanilla.Slider((170, 10, 150, 20), minValue=10, maxValue=100, value=50,
            continuous=False, callback=self.collectionViewResize)
        self.collectionViewTab.collectionView = GlyphCollectionView((10, 40, -10, -10), allowDrag=True,
            selectionCallback=self.collectionViewSelectionCallback, doubleClickCallback=self.collectionViewDoubleClickCallback,
            deleteCallback=self.collectionViewDeleteCallback, selfApplicationDropSettings=dropSettings)
        self.collectionViewTab.collectionView.set(self.glyphs)
        self.collectionViewResize(self.collectionViewTab.collectionViewSizeSlider)

        # test line view
        self.lineViewTab.textInput = vanilla.EditText((10, 10, -10, 22), callback=self.lineViewTextInput)
        self.lineViewTab.lineView = GlyphLineView((10, 40, -10, -10), dropCallback=self.lineViewDropCallback)

        # test controls

        self.controlsTab.glyphNameComboBox = GlyphNameComboBox((10, 10, -10, 22), self.font)

        self.setUpBaseWindowBehavior()

        self.w.tabs.set(2)

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

    def collectionViewDoubleClickCallback(self, sender):
        print "double click"

    def collectionViewDeleteCallback(self, sender):
        print "delete", sender.getSelection()

    def collectionViewDropCallback(self, sender, dropInfo):
        glyphs = dropInfo["data"]
        isProposal = dropInfo["isProposal"]
        if not isProposal:
            for glyph in glyphs:
                self.font.insertGlyph(glyph, name=".glyph%d" % len(self.font))
            self.glyphs = [self.font[k] for k in sorted(self.font.keys())]
            self.collectionViewTab.collectionView.set(self.glyphs)
        return True

    def collectionViewSelectionCallback(self, sender):
        self.collectionViewTab.collectionView.setSelection(sender.getSelection())

    def collectionViewModify(self, sender):
        selection = [self.glyphs[index] for index in self.collectionViewTab.collectionView.getSelection()]
        for glyph in selection:
            glyph.move((100, 100))

    def collectionViewResize(self, sender):
        width = height = int(sender.get())
        drawHeader = height > GlyphCellMinHeightForHeader
        if drawHeader:
            height += GlyphCellHeaderHeight
        self.collectionViewTab.collectionView.setCellSize((width, height))
        self.collectionViewTab.collectionView.setCellRepresentationArguments(drawHeader=drawHeader, drawMetrics=drawHeader)

    # list view

    def listViewEdit(self, sender):
        pass

    # line view

    def lineViewTextInput(self, sender):
        glyphNames = splitText(sender.get(), self.font.cmap)
        glyphs = [self.font[glyphName] for glyphName in glyphNames if glyphName in self.font]
        self.lineViewTab.lineView.set(glyphs)

    def lineViewDropCallback(self, sender, glyphs, testing):
        if not testing:
            self.lineViewTab.lineView.set(glyphs)
        return True


if __name__ == "__main__":
    AppHelper.runEventLoop()
