from PyObjCTools import NibClassBuilder, AppHelper
from AppKit import *
import vanilla
from defcon import Font
from defconAppKit.representationFactories import registerAllFactories
from defconAppKit.representationFactories import GlyphCellHeaderHeight, GlyphCellMinHeightForHeader
from defconAppKit.views.cellView import GlyphCellView

registerAllFactories()


import objc
objc.setVerbose(True)

NibClassBuilder.extractClasses("MainMenu")


class DefconAppKitTestDocument(NSDocument):

    def readFromFile_ofType_(self, path, tp):
        font = Font(path)
        window = self.vanillaWindowController = DefconAppKitTestDocumentWindow(font)
        self.addWindowController_(window.w.getNSWindowController())
        return True


class DefconAppKitTestDocumentWindow(object):

    def __init__(self, font):
        self.font = font
        self.glyphs = [font[k] for k in sorted(font.keys())]
        self.w = vanilla.Window((500, 500), minSize=(300, 100))

        self.w.tabs = vanilla.Tabs((10, 10, -10, -10), ["Window", "GlyphCellView"])
        self.windowTab = self.w.tabs[0]
        self.cellViewTab = self.w.tabs[1]

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

        self.w.open()

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
        self.cellViewTab.cellView.setRepresentationArguments(drawHeader=drawHeader, drawMetrics=drawHeader)


if __name__ == "__main__":
    AppHelper.runEventLoop()
