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
        self.w.glyphList = vanilla.List((0, 0, 200, -70), sorted(font.keys()), selectionCallback=self.selection)
        self.w.modifyButton = vanilla.Button((10, -60, 180, 20), "Modify Glyphs", callback=self.modify)
        self.w.sizeSlider = vanilla.Slider((10, -30, 180, 20), minValue=10, maxValue=100, value=50,
            continuous=False, callback=self.resize)
        self.w.cellView = GlyphCellView((200, 0, -0, -0),
            selectionCallback=self.selectionCallback, doubleClickCallback=self.doubleClickCallback,
            deleteCallback=self.deleteCallback, dropCallback=self.dropCallback)
        self.w.cellView.set(self.glyphs)
        self.resize(self.w.sizeSlider)
        self.w.open()

    def selectionCallback(self, sender):
        print "selection", sender.getSelection()

    def doubleClickCallback(self, sender):
        print "double click"

    def deleteCallback(self, sender):
        print "delete", sender.getSelection()

    def dropCallback(self, sender, glyphs, testing):
        if not testing:
            for glyph in glyphs:
                self.font.insertGlyph(glyph, name=".glyph%d" % len(self.font))
            self.glyphs = [self.font[k] for k in sorted(self.font.keys())]
            self.w.cellView.set(self.glyphs)
            self.w.glyphList.set(sorted(self.font.keys()))
        return True

    def selection(self, sender):
        self.w.cellView.setSelection(sender.getSelection())

    def modify(self, sender):
        selection = [self.glyphs[index] for index in self.w.cellView.getSelection()]
        for glyph in selection:
            glyph.move((50, 50))

    def resize(self, sender):
        width = height = int(sender.get())
        drawHeader = height > GlyphCellMinHeightForHeader
        if drawHeader:
            height += GlyphCellHeaderHeight
        self.w.cellView.setCellSize((width, height))
        self.w.cellView.setRepresentationArguments(drawHeader=drawHeader, drawMetrics=drawHeader)


if __name__ == "__main__":
    AppHelper.runEventLoop()
