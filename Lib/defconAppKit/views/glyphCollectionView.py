import weakref
from AppKit import *
import vanilla
from defconAppKit.views.placardScrollView import DefconAppKitPlacardNSScrollView, PlacardSegmentedButton
from defconAppKit.views.glyphCellView import DefconAppKitGlyphCellNSView, gridColor, GlyphInformationPopUpWindow


class GlyphCollectionView(vanilla.List):

    """
    This object presents the user with a view showing a collection of glyphs.
    The object contains a small control that allows the user to toggle between
    two different viewing modes: the default is to show a collection of cells
    and the other is to show a standard list view.

    The object follows the API of vanilla.List with some special contructor
    arguments and some special methods. When you set objects into the view,
    you always pass glyph objects. The object will then extract the relevant
    data to display. SImilarly, when you recieve drop callbacks as a result
    of a drag and dro operation, the "data" in the drop info will be a
    list of glyphs.

    Contructor Arguments:

    initialMode
    The initial mode for the view. Either "cell" or "list".

    listColumnDescriptions
    This sets up the columns in the list mode. These follow the same format
    of the column descriptions in vanilla.List. The only exception is that
    you need to provide an "attribute" key/value pair. This is the glyph
    attribute that the list will extract display values from. For example:

        dict(title="Glyph Width", key="glyphWidth", attribute="width")

    If no listColumnDescriptions is provided, the glyph name will be
    shown in a single column.

    listShowColumnTitles
    Same as showColumnTitles in vanilla.List

    showModePlacard
    Flag to indicate if the mode switch placard should be shown. This can be
    useful if you only want to show the list or the cell view.

    cellRepresentationName
    The representation name used to fetch the cell representations.

    glyphDetailWindowClass
    A window class to use when the user control-clicks a cell. This must be a
    subclass of vanilla.Window and it must have the following methods:
        window.set(glyph)
        window.setPosition((x, y))

    selectionCallback, doubleClickCallback, deleteCallback, editCallback
    Sames as the arguments in vanilla.List

    enableDelete
    Flag to indicate if the delete key has any effect on the contents of the view.

    various drop settings:
    These follow the same format as vanilla.List. The biggest exception is that
    you do not provide a "type" key/value pair. That will be set by the
    dragAndDropType argument. You can provide allowsDropOnRow settings, but dropping
    on a row is not yet supported. There is currently no support for reordering
    with the selfDropSettings as there is in vanilla.List. That will be supported
    at some point in the future.

    allowDrag:
    Unlike vanilla.List, you don't povide any data about dragging. All you do
    is tell the view if you want dragging allowed or not.

    dragAndDropType
    The drag and drop type for the view. Only change this if you know what you are doing.
    """

    nsScrollViewClass = DefconAppKitPlacardNSScrollView
    glyphCellViewClass = DefconAppKitGlyphCellNSView

    def __init__(self, posSize, initialMode="cell", listColumnDescriptions=None, listShowColumnTitles=False,
        showModePlacard=True,
        cellRepresentationName="defconAppKitGlyphCell", glyphDetailWindowClass=GlyphInformationPopUpWindow,
        selectionCallback=None, doubleClickCallback=None, deleteCallback=None, editCallback=None,
        enableDelete=False,
        selfWindowDropSettings=None, selfDocumentDropSettings=None, selfApplicationDropSettings=None,
        otherApplicationDropSettings=None, allowDrag=False, dragAndDropType="DefconAppKitSelectedGlyphIndexesPboardType"):
        # placeholder attributes
        self._selectionCallback = None
        self._doubleClickCallback = None
        self._deleteCallback = deleteCallback
        self._dragAndDropType = dragAndDropType
        ## set up the list
        self._listEditChangingAttribute = None
        self._listEditChangingGlyph = None
        enableDelete = deleteCallback is not None
        if editCallback is not None:
            self._finalEditCallback = editCallback
            editCallback = self._listEditCallback
        # prep for drag and drop
        if selfWindowDropSettings is not None:
            selfWindowDropSettings = dict(selfWindowDropSettings)
        if selfDocumentDropSettings is not None:
            selfDocumentDropSettings = dict(selfDocumentDropSettings)
        if selfApplicationDropSettings is not None:
            selfApplicationDropSettings = dict(selfApplicationDropSettings)
        if otherApplicationDropSettings is not None:
            otherApplicationDropSettings = dict(otherApplicationDropSettings)
        dropSettings = [
            (selfWindowDropSettings, self._selfWindowDropCallback),
            (selfDocumentDropSettings, self._selfDocumentDropCallback),
            (selfApplicationDropSettings, self._selfApplicationDropCallback),
            (otherApplicationDropSettings, self._otherApplicationDropCallback)
        ]
        for d, internalCallback in dropSettings:
            if d is None:
                continue
            d["type"] = dragAndDropType
            d["finalCallback"] = d["callback"]
            d["callback"] = internalCallback
        dragSettings = None
        if allowDrag:
            dragSettings = dict(type=dragAndDropType, callback=self._packListRowsForDrag)
        if listColumnDescriptions is None:
            listColumnDescriptions = [dict(title="Name", attribute="name")]
        super(GlyphCollectionView, self).__init__(posSize, [], columnDescriptions=listColumnDescriptions,
            editCallback=editCallback, selectionCallback=selectionCallback,
            showColumnTitles=listShowColumnTitles, enableTypingSensitivity=True, enableDelete=enableDelete,
            autohidesScrollers=False,
            selfWindowDropSettings=selfWindowDropSettings, selfDocumentDropSettings=selfDocumentDropSettings,
            selfApplicationDropSettings=selfApplicationDropSettings, otherApplicationDropSettings=otherApplicationDropSettings,
            dragSettings=dragSettings)
        self._keyToAttribute = {}
        self._orderedListKeys = []
        self._wrappedListItems = {}
        for columnDescription in listColumnDescriptions:
            title = columnDescription["title"]
            key = columnDescription.get("key", title)
            attribute = columnDescription["attribute"]
            self._keyToAttribute[key] = attribute
            self._orderedListKeys.append(key)
        ## set up the cell view
        self._glyphCellView = self.glyphCellViewClass.alloc().initWithFrame_cellRepresentationName_detailWindowClass_(
            ((0, 0), (400, 400)), cellRepresentationName, glyphDetailWindowClass)
        self._glyphCellView.vanillaWrapper = weakref.ref(self)
        self._glyphCellView.setAllowsDrag_(allowDrag)
        dropTypes = []
        for d in (selfWindowDropSettings, selfDocumentDropSettings, selfApplicationDropSettings, otherApplicationDropSettings):
            if d is not None:
                dropTypes.append(d["type"])
        self._glyphCellView.registerForDraggedTypes_(dropTypes)
        ## set up the placard
        if showModePlacard:
            placardW = 34
            placardH = 16
            self._placard = vanilla.Group((0, 0, placardW, placardH))
            self._placard.button = PlacardSegmentedButton((0, 0, placardW, placardH),
                [dict(imageObject=placardCellImage, width=16), dict(imageObject=placardListImage, width=18)],
                callback=self._placardSelection, sizeStyle="mini")
            self._nsObject.setPlacard_(self._placard.getNSView())
        else:
            self._placard = None
        ## tweak the scroll view
        self._nsObject.setBackgroundColor_(gridColor)
        ## table view tweak
        self._haveTweakedColumnWidths = initialMode == "list"
        ## set the mode
        self._mode = None
        self.setMode(initialMode)

    def _breakCycles(self):
        for glyph in self._wrappedListItems.keys():
            del self._wrappedListItems[glyph]
            self._unsubscribeFromGlyph(glyph)
        self._placard = None
        self._glyphCellView = None
        super(GlyphCollectionView, self)._breakCycles()

    def _placardSelection(self, sender):
        mode = ["cell", "list"][sender.get()]
        self.setMode(mode)

    # ---------------
    # mode management
    # ---------------

    def setMode(self, mode):
        """
        Set the view mode. The options are "cell" and "list".
        """
        if mode == self._mode:
            return
        selection = self.getSelection()
        placard = self._placard
        if mode == "list":
            documentView = self._tableView
            if placard is not None:
                placard.button.set(1)
        elif mode == "cell":
            documentView = self._glyphCellView
            if placard is not None:
                placard.button.set(0)
        self._nsObject.setDocumentView_(documentView)
        self._mode = mode
        self.setSelection(selection)
        if mode == "cell":
            self._glyphCellView.recalculateFrame()
        elif not self._haveTweakedColumnWidths:
            tableView = self.getNSTableView()
            tableView.sizeToFit()
            self._haveTweakedColumnWidths = True

    def getMode(self):
        """
        Get the current mode.
        """
        return self._mode

    # --------------------
    # selection management
    # --------------------

    def getSelection(self):
        """
        Get the selection in the view as a list of indexes.
        """
        if self._mode == "list":
            return super(GlyphCollectionView, self).getSelection()
        return self._glyphCellView.getSelection()

    def setSelection(self, selection):
        """
        Sets the selection in the view. The passed value
        should be a list of indexes.
        """
        if self._mode == "list":
            super(GlyphCollectionView, self).setSelection(selection)
        else:
            self._glyphCellView.setSelection_(selection)

    def scrollToSelection(self):
        """
        Scroll the view so that the current selection is visible.
        """
        super(GlyphCollectionView, self).scrollToSelection()
        selection = self.getSelection()
        if selection:
            self._glyphCellView.scrollToCell_(selection[0])

    # -------------
    # drag and drop
    # -------------

    def _packListRowsForDrag(self, sender, indexes):
        return indexes

    def _convertDropInfo(self, dropInfo):
        source = dropInfo["source"]
        indexes = [int(i) for i in dropInfo["data"]]
        if isinstance(source, vanilla.VanillaBaseObject):
            glyphs = [source[i] for i in indexes]
        else:
            glyphs = source.getGlyphsAtIndexes_(indexes)
        dropInfo["data"] = glyphs
        return dropInfo

    def _selfWindowDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._selfWindowDropSettings["finalCallback"](self, dropInfo)

    def _selfDocumentDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._selfDocumentDropSettings["finalCallback"](self, dropInfo)

    def _selfApplicationDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._selfApplicationDropSettings["finalCallback"](self, dropInfo)

    def _otherApplicationDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._otherApplicationDropSettings["finalCallback"](self, dropInfo)

    # -------------
    # list behavior
    # -------------

    # notifications

    def _subscribeToGlyph(self, glyph):
        glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")

    def _unsubscribeFromGlyph(self, glyph):
        glyph.removeObserver(self, "Glyph.Changed")

    def _glyphChanged(self, notification):
        glyph = notification.object
        if glyph not in self._wrappedListItems:
            return
        d = self._wrappedListItems[glyph]
        for key, attr in self._keyToAttribute.items():
            d[key] = getattr(glyph, attr)
        self._glyphCellView.setNeedsDisplay_(True)

    # editing

    def _listEditCallback(self, sender):
        # only listen to this if the list is the first responder
        window = self._tableView.window()
        if window is None:
            return
        app = NSApp()
        windows = [app.keyWindow(), app.mainWindow()]
        if window not in windows:
            return
        if window.firstResponder() != self._tableView:
            responder = window.firstResponder()
            foundSelf = False
            if hasattr(responder, "superview"):
                superview = responder.superview()
                while superview is not None:
                    if superview == self._tableView:
                        foundSelf = True
                        break
                    else:
                        superview = superview.superview()
            if not foundSelf:
                return
        # skip if in an edit loop
        if self._listEditChangingGlyph is not None:
            return
        if not self.getSelection():
            return
        columnIndex, rowIndex = sender.getEditedColumnAndRow()
        if columnIndex == -1 or rowIndex == -1:
            rowIndex = self.getSelection()[0]
            editedKey = None
            editedAttribute = None
        else:
            editedKey = self._orderedListKeys[columnIndex]
            editedAttribute = self._keyToAttribute[editedKey]
        item = super(GlyphCollectionView, self).__getitem__(rowIndex)
        glyph = item["_glyph"]()
        self._listEditChangingAttribute = editedAttribute
        self._listEditChangingGlyph = glyph
        # known attribute. procees it individually.
        if editedAttribute is not None:
            # set the attribute
            value = item[editedKey]
            glyphValue = getattr(glyph, editedAttribute)
            if value != glyphValue:
                setattr(glyph, editedAttribute, value)
        # unknown attribute. process all.
        else:
            for key, attribute in self._keyToAttribute.items():
                value = getattr(glyph, attribute)
                if value != item[key]:
                    setattr(glyph, attribute, item[key])
        # update the dict contents
        for key, attribute in self._keyToAttribute.items():
            if key == editedKey and attribute == editedAttribute:
                continue
            value = getattr(glyph, attribute)
            if value != item[key]:
                item[key] = value
        self._listEditChangingAttribute = None
        self._listEditChangingGlyph = None

    # wrapping

    def _wrapGlyphForList(self, glyph):
        changed = False
        if glyph in self._wrappedListItems:
            d = self._wrappedListItems[glyph]
        else:
            d = NSMutableDictionary.dictionary()
            self._subscribeToGlyph(glyph)
        for key, attribute in self._keyToAttribute.items():
            value = getattr(glyph, attribute)
            if d.get(key) != value:
                d[key] = value
                changed = True
        d["_glyph"] = weakref.ref(glyph)
        if changed:
            self._wrappedListItems[glyph] = d
        return d

    def _unwrapListItems(self, items=None):
        if items is None:
            items = super(GlyphCollectionView, self).get()
        glyphs = [d["_glyph"]() for d in items]
        return glyphs

    # standard API

    def _removeSelection(self):
        if not self._enableDelete:
            return
        selection = self.getSelection()
        # list
        super(GlyphCollectionView, self)._removeSelection()
        # cell
        self._glyphCellView.setGlyphs_(self._unwrapListItems())
        # call the callback
        if self._deleteCallback is not None:
            self._deleteCallback(self)

    def __contains__(self, glyph):
        return glyph in self._wrappedListItems

    def __getitem__(self, index):
        item = super(GlyphCollectionView, self).__getitem__(index)
        glyph = self._unwrapListItems([item])[0]
        return glyph

    def __setitem__(self, index, glyph):
        # list
        existing = self[index]
        item = self._wrapGlyphForList(glyph)
        super(GlyphCollectionView, self).__setitem__(index, glyph)
        if not super(GlyphCollectionView, self).__contains__(existing):
            otherGlyph = existing["_glyph"]
            del self._wrappedListItems[otherGlyph]
            self._unsubscribeFromGlyph(otherGlyph)
        # cell view
        self._glyphCellView.setGlyphs_(self._unwrapListItems())

    def __delitem__(self, index):
        # list
        item = self[index]
        super(GlyphCollectionView, self).__delitem__(index)
        if not super(GlyphCollectionView, self).__contains__(item):
            glyph = item["_glyph"]
            del self._wrappedListItems[glyph]
            self._unsubscribeFromGlyph(glyph)
        # cell view
        self._glyphCellView.setGlyphs_(self._unwrapListItems())

    def append(self, glyph):
        # list
        item = self._wrapGlyphForList(glyph)
        super(GlyphCollectionView, self).append(item)
        # cell view
        self._glyphCellView.setGlyphs_(self._unwrapListItems())

    def remove(self, glyph):
        # list
        item = self._wrappedListItems[glyph]
        super(GlyphCollectionView, self).remove(item)
        if not super(GlyphCollectionView, self).__contains__(item):
            glyph = item["_glyph"]
            del self._wrappedListItems[glyph]
            self._unsubscribeFromGlyph(glyph)
        # cell view
        self._glyphCellView.setGlyphs_(self._unwrapListItems())

    def index(self, glyph):
        item = self._wrappedListItems[glyph]
        return super(GlyphCollectionView, self).index(item)

    def insert(self, index, glyph):
        # list
        item = self._wrapGlyphForList(glyph)
        super(GlyphCollectionView, self).insert(index, item)
        # cell view
        self._glyphCellView.setGlyphs_(self._unwrapListItems())

    def extend(self, glyphs):
        # list
        items = [self._wrapGlyphForList(glyph) for glyph in glyphs]
        super(GlyphCollectionView, self).extend(items)
        # cell view
        self._glyphCellView.setGlyphs_(self._unwrapListItems())

    def set(self, glyphs):
        """
        Set the glyphs in the view.
        """
        # remove removed wrapped items
        removedGlyphs = set(self._wrappedListItems) - set(glyphs)
        for glyph in removedGlyphs:
            del self._wrappedListItems[glyph]
            self._unsubscribeFromGlyph(glyph)
        # wrap the glyphs for the list
        wrappedGlyphs = [self._wrapGlyphForList(glyph) for glyph in glyphs]
        # set the cell view
        self._glyphCellView.setGlyphs_(glyphs)
        # set the list
        super(GlyphCollectionView, self).set(wrappedGlyphs)

    def get(self):
        """
        Get the glyphs in the view.
        """
        return self._unwrapListItems()

    # ------------------
    # cell view behavior
    # ------------------

    def getGlyphCellView(self):
        """
        Get the cell NSView.
        """
        return self._glyphCellView

    def setCellSize(self, (width, height)):
        """
        Set the size of the cells.
        """
        self._glyphCellView.setCellSize_((width, height))

    def getCellSize(self):
        """
        Get the size of the cells.
        """
        return self._glyphCellView.getCellSize()

    def setCellRepresentationArguments(self, **kwargs):
        """
        Set the arguments that should be passed to the cell representation factory.
        """
        self._glyphCellView.setCellRepresentationArguments_(**kwargs)

    def getCellRepresentationArguments(self):
        """
        Get the arguments passed to the cell representation factory.
        """
        return self._glyphCellView.getCellRepresentationArguments()

    def preloadGlyphCellImages(self):
        """
        Preload the images to be used in the cells. This is useful
        when lots of cellsneed to be displayed.
        """
        self._glyphCellView.preloadGlyphCellImages()

# -------------
# placard icons
# -------------

placardIconColor = NSColor.colorWithCalibratedWhite_alpha_(0, .5)

placardListImage = NSImage.alloc().initWithSize_((16, 16))
placardListImage.lockFocus()
placardIconColor.set()
path = NSBezierPath.bezierPath()
for i in xrange(3):
    y = 5.5 + (i * 3)
    path.moveToPoint_((3, y))
    path.lineToPoint_((13, y))
path.setLineWidth_(1)
path.stroke()
placardListImage.unlockFocus()

placardCellImage = NSImage.alloc().initWithSize_((16, 16))
placardCellImage.lockFocus()
placardIconColor.set()
rects = [
    ((4, 4), (3, 3)),
    ((4, 9), (3, 3)),
    ((9, 4), (3, 3)),
    ((9, 9), (3, 3)),
]
NSRectFillListUsingOperation(rects, len(rects), NSCompositeSourceOver)
placardCellImage.unlockFocus()
