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
from defconAppKit.views.glyphMultilineView import GlyphMultilineView
from defconAppKit.views.glyphNameComboBox import GlyphNameComboBox
from defconAppKit.tools.osFontBridgeManager import OSFontBridgeManager
from fontAppTools import splitText

registerAllFactories()


import objc
objc.setVerbose(True)

NibClassBuilder.extractClasses("MainMenu")


class DefconAppKitTestAppDelegate(NSObject):

    def init(self):
        self = super(DefconAppKitTestAppDelegate, self).init()
        self._osFontBridgeManager = OSFontBridgeManager()
        return self

    def OSFontBridgeManager(self):
        return self._osFontBridgeManager


class DefconAppKitTestDocument(NSDocument):

    def readFromFile_ofType_(self, path, tp):
        progress = ProgressWindow("Opening...")
        try:
            font = self.font = Font(path)
            NSApp().delegate().OSFontBridgeManager().addFont(font)
            window = self.vanillaWindowController = DefconAppKitTestDocumentWindow(font)
            self.addWindowController_(window.w.getNSWindowController())
        finally:
            progress.close()
        return True

    def dealloc(self):
        NSApp().delegate().OSFontBridgeManager().removeFont(self.font)
        super(DefconAppKitTestDocument, self).dealloc()


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

        self.w.tabs = vanilla.Tabs((10, 10, -10, -10), ["Window", "GlyphCollectionView", "GlyphLineView", "GlyphMultilineView", "Misc. Controls"])
        self.windowTab = self.w.tabs[0]
        self.collectionViewTab = self.w.tabs[1]
        self.lineViewTab = self.w.tabs[2]
        self.multilineViewTab = self.w.tabs[3]
        self.controlsTab = self.w.tabs[4]

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
        self.lineViewTab.lineViewSizeSlider = vanilla.Slider((-160, 11, 150, 20), minValue=10, maxValue=500, value=100,
            continuous=True, callback=self.lineViewResize)
        self.lineViewTab.textInput = vanilla.EditText((10, 10, -170, 22), callback=self.lineViewTextInput)
        self.lineViewTab.lineView = GlyphLineView((10, 40, -10, -10), dropCallback=self.lineViewDropCallback)

        # test multiline view
        self.multilineViewTab.multilineViewSizeSlider = vanilla.Slider((10, 10, 150, 20), minValue=10, maxValue=500, value=100,
            continuous=True, callback=self.multilineViewResize)
        self.multilineViewTab.multilineView = GlyphMultilineView((10, 40, -10, -10), callback=self.multilineViewTextInput)
        self.multilineViewTab.multilineView.setFont(font)
        lines = [[]]
        for glyph in self.glyphs:
            lines[-1].append(glyph.name)
            if len(lines[-1]) == 10:
                lines.append([])
        self.multilineViewTab.multilineView.set(lines)

        # test controls

        self.controlsTab.glyphNameComboBox = GlyphNameComboBox((10, 10, -10, 22), self.font)

        self.setUpBaseWindowBehavior()

        self.w.tabs.set(3)

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

    def lineViewResize(self, sender):
        self.lineViewTab.lineView.setPointSize(sender.get())

    # multiline view

    def multilineViewTextInput(self, sender):
        lines = sender.get()
        print "multiline input:", lines

    def multilineViewResize(self, sender):
        self.multilineViewTab.multilineView.setPointSize(sender.get())



if __name__ == "__main__":
    AppHelper.runEventLoop()
