import weakref
from AppKit import *
import vanilla
from defconAppKit.controls.glyphCellView import DefconAppKitGlyphCellNSView, gridColor, GlyphInformationPopUpWindow
from defconAppKit.controls.fontInfoView import GradientButtonBar


class DefconAppKitGlyphCollectionView(NSView):

    def viewDidMoveToWindow(self):
        wrapper = self.vanillaWrapper()
        wrapper.setPosSize(wrapper.getPosSize())
        for subview in self.subviews():
            if hasattr(subview, "vanillaWrapper"):
                wrapper = subview.vanillaWrapper()
                if wrapper is not None:
                    wrapper.setPosSize(wrapper.getPosSize())


class GlyphCollectionView(vanilla.Group):

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

    placardActionItems
    An optional list of items (defined as defined in vanilla.ActionButton) that
    will be shown via a vanilla.ActionButton. The default is None.

    showPlacard
    Flag to indicate if the placard should be shown. If showModePlacard is True
    or placardActionItems is not None, showPlacard will automatically be True.

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
    dragAndDropType argument.

    allowDrag:
    Unlike vanilla.List, you don't povide any data about dragging. All you do
    is tell the view if you want dragging allowed or not.

    dragAndDropType
    The drag and drop type for the view. Only change this if you know what you are doing.
    """

    nsViewClass = DefconAppKitGlyphCollectionView
    glyphCellViewClass = DefconAppKitGlyphCellNSView

    glyphListViewVanillaClass = vanilla.List

    def __init__(self, posSize, initialMode="cell", listColumnDescriptions=None, listShowColumnTitles=False,
        showPlacard=True, showModePlacard=True, placardActionItems=None,
        cellRepresentationName="defconAppKit.GlyphCell", glyphDetailWindowClass=GlyphInformationPopUpWindow,
        selectionCallback=None, doubleClickCallback=None, deleteCallback=None, editCallback=None,
        enableDelete=False,
        selfDropSettings=None, selfWindowDropSettings=None, selfDocumentDropSettings=None, selfApplicationDropSettings=None,
        otherApplicationDropSettings=None, allowDrag=False, dragAndDropType="DefconAppKitSelectedGlyphIndexesPboardType"
    ):
        super(GlyphCollectionView, self).__init__(posSize)
        if showModePlacard or placardActionItems is not None:
            showPlacard = True
        bottom = 0
        if showPlacard:
            bottom = -19
        self._selectionCallback = selectionCallback
        self._doubleClickCallback = doubleClickCallback
        self._deleteCallback = deleteCallback
        self._dragAndDropType = dragAndDropType
        self._enableDelete = enableDelete
        ## set up the list
        self._listEditChangingAttribute = None
        self._listEditChangingGlyph = None
        enableDelete = deleteCallback is not None
        if editCallback is not None:
            self._finalEditCallback = editCallback
            editCallback = self._listEditCallback

        # prep for drag and drop
        if selfDropSettings is not None:
            selfDropSettings = dict(selfDropSettings)
        if selfWindowDropSettings is not None:
            selfWindowDropSettings = dict(selfWindowDropSettings)
        if selfDocumentDropSettings is not None:
            selfDocumentDropSettings = dict(selfDocumentDropSettings)
        if selfApplicationDropSettings is not None:
            selfApplicationDropSettings = dict(selfApplicationDropSettings)
        if otherApplicationDropSettings is not None:
            otherApplicationDropSettings = dict(otherApplicationDropSettings)
        dropSettings = [
            (selfDropSettings, self._selfDropCallback),
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
        self._list = self.glyphListViewVanillaClass((0, 0, 0, bottom), [],
            columnDescriptions=listColumnDescriptions,
            editCallback=editCallback, selectionCallback=self._listSelectionCallback, doubleClickCallback=doubleClickCallback,
            showColumnTitles=listShowColumnTitles, enableTypingSensitivity=True, enableDelete=enableDelete,
            autohidesScrollers=True,
            selfDropSettings=selfDropSettings, selfWindowDropSettings=selfWindowDropSettings, selfDocumentDropSettings=selfDocumentDropSettings,
            selfApplicationDropSettings=selfApplicationDropSettings, otherApplicationDropSettings=otherApplicationDropSettings,
            dragSettings=dragSettings
        )
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
        for d in (selfDropSettings, selfWindowDropSettings, selfDocumentDropSettings, selfApplicationDropSettings, otherApplicationDropSettings):
            if d is not None:
                dropTypes.append(d["type"])
        self._glyphCellView.registerForDraggedTypes_(dropTypes)
        ## set array contoller
        self._glyphCellView.setArrayController_(self._arrayController)
        ## set up the placard
        if showPlacard:
            self._placard = vanilla.Group((0, -21, 0, 21))
            self._placard.base = GradientButtonBar((0, 0, 0, 0))
            extensionLeft = 0
            extensionWidth = 0
            # mode
            if showModePlacard:
                extensionLeft += 42
                modeButton = vanilla.SegmentedButton(
                    (0, 0, 43, 0),
                    [
                        dict(imageNamed="defconAppKitPlacardCellImage", width=20),
                        dict(imageNamed="defconAppKitPlacardListImage", width=20)
                    ],
                    callback=self._placardSelection
                )
                modeButton.frameAdjustments = dict(regular=(0, 0, 0, 0))
                modeButton.getNSSegmentedButton().setSegmentStyle_(NSSegmentStyleSmallSquare)
                modeButton.set(0)
                self._placard.button = modeButton
            # action button
            if placardActionItems is not None:
                extensionWidth -= 35
                actionButton = vanilla.ActionButton(
                    (-35, 0, 45, 21),
                    placardActionItems,
                    sizeStyle="small",
                    bordered=False
                )
                actionButton.frameAdjustments = dict(regular=(0, 0, 0, 0))
                button = actionButton.getNSPopUpButton()
                button.setBordered_(False)
                button.setBezelStyle_(NSSmallSquareBezelStyle)
                self._placard.actionButton = actionButton
            # extension
            self._placard.extension = vanilla.Group((extensionLeft, 0, extensionWidth, 0))
        else:
            self._placard = None
        ## tweak the scroll view
        self._list.getNSScrollView().setBackgroundColor_(gridColor)
        ## set the mode
        self._mode = None
        self.setMode(initialMode)

    def _get_arrayController(self):
        return self._list._arrayController

    _arrayController = property(_get_arrayController)

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
        placard = self._placard
        if mode == "list":
            documentView = self._list.getNSTableView()
            if placard is not None:
                placard.button.set(1)
            # the cell view needs to be told to stop paying attention to the window
            self._glyphCellView.unsubscribeFromWindow()
        elif mode == "cell":
            documentView = self._glyphCellView
            if placard is not None:
                placard.button.set(0)
        self._list.getNSScrollView().setDocumentView_(documentView)
        self._mode = mode
        if mode == "cell":
            # cell view
            self._glyphCellView.recalculateFrame()

    def getMode(self):
        """
        Get the current mode.
        """
        return self._mode

    # -----------------
    # placard retrieval
    # -----------------

    def getPlacardGroup(self):
        """
        If a placard has been defined, this returns
        a vanilla.Group between the prebuilt controls.
        """
        if self._placard is None:
            return None
        return self._placard.extension

    # --------------------
    # selection management
    # --------------------

    def getSelection(self):
        """
        Get the selection in the view as a list of indexes.
        """
        return self._list.getSelection()

    def setSelection(self, selection):
        """
        Sets the selection in the view. The passed value
        should be a list of indexes.
        """
        self._list.setSelection(selection)

    def scrollToSelection(self):
        """
        Scroll the view so that the current selection is visible.
        """
        self._list.scrollToSelection()
        selection = self.getSelection()
        if selection:
            self._glyphCellView.scrollToCell_(selection[0])

    def _listSelectionCallback(self, sender):
        if self._selectionCallback is not None:
            self._selectionCallback(self)

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

    def _selfDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._list._selfDropSettings["finalCallback"](self, dropInfo)

    def _selfWindowDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._list._selfWindowDropSettings["finalCallback"](self, dropInfo)

    def _selfDocumentDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._list._selfDocumentDropSettings["finalCallback"](self, dropInfo)

    def _selfApplicationDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._list._selfApplicationDropSettings["finalCallback"](self, dropInfo)

    def _otherApplicationDropCallback(self, sender, dropInfo):
        dropInfo = self._convertDropInfo(dropInfo)
        return self._list._otherApplicationDropSettings["finalCallback"](self, dropInfo)

    # -------------
    # list behavior
    # -------------

    # notifications

    def _subscribeToGlyph(self, glyph):
        glyph.addObserver(self, "_glyphChanged", "Glyph.Changed")
        font = glyph.getParent()
        if font is not None and not font.info.hasObserver(self, "Info.Changed"):
            font.info.addObserver(self, "_fontChanged", "Info.Changed")

    def _unsubscribeFromGlyph(self, glyph):
        glyph.removeObserver(self, "Glyph.Changed")
        font = glyph.getParent()
        if font is not None and font.info.hasObserver(self, "Info.Changed"):
            font.info.removeObserver(self, "Info.Changed")

    def _fontChanged(self, notification):
        info = notification.object
        font = info.getParent()
        repWidth, repHeight = self.getCellSize()
        repArgs = self.getCellRepresentationArguments()
        repName = self._glyphCellView.getCellRepresentationName()
        for glyph in self:
            if glyph.getParent() == font:
                glyph.destroyRepresentation(repName, width=repWidth, height=repHeight, **repArgs)
        self._glyphCellView.setNeedsDisplay_(True)

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
        window = self.getNSView().window()
        tableView = self._list.getNSTableView()
        if window is None:
            return
        app = NSApp()
        windows = [app.keyWindow(), app.mainWindow()]
        if window not in windows:
            return
        if window.firstResponder() != tableView:
            responder = window.firstResponder()
            foundSelf = False
            if hasattr(responder, "superview"):
                superview = responder.superview()
                while superview is not None:
                    if superview == tableView:
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
        item = self._list[rowIndex]
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
            if not key in d or d.get(key) != value:
                d[key] = value
                changed = True
        d["_glyph"] = weakref.ref(glyph)
        if changed:
            self._wrappedListItems[glyph] = d
        return d

    def _unwrapListItems(self, items=None):
        if items is None:
            items = self._arrayController.arrangedObjects()
        glyphs = [d["_glyph"]() for d in items]
        return glyphs

    # standard API

    def _removeSelection(self):
        if not self._enableDelete:
            return
        selection = self.getSelection()
        # list
        for index in reversed(sorted(selection)):
            del self._list[index]
        # cell view
        self._glyphCellView.setGlyphsFromArrayController()
        # call the callback
        if self._deleteCallback is not None:
            self._deleteCallback(self)

    def __contains__(self, glyph):
        return glyph in self._wrappedListItems

    def __getitem__(self, index):
        item = self._list[index]
        glyph = self._unwrapListItems([item])[0]
        return glyph

    def __setitem__(self, index, glyph):
        # list
        existing = self[index]
        item = self._wrapGlyphForList(glyph)
        self._list[index] = item
        if existing not in self._list:
            otherGlyph = existing["_glyph"]
            del self._wrappedListItems[otherGlyph]
            self._unsubscribeFromGlyph(otherGlyph)

    def __delitem__(self, index):
        # list
        item = self[index]
        del self._list[index]
        if item not in self._list:
            glyph = item["_glyph"]
            del self._wrappedListItems[glyph]
            self._unsubscribeFromGlyph(glyph)

    def append(self, glyph):
        item = self._wrapGlyphForList(glyph)
        self.getArrayController().addObject_(item)
        self.getArrayController().rearrangeObjects()

    def remove(self, glyph):
        toRemove = self._wrappedListItems[glyph]
        self.getArrayController().removeObject_(toRemove)
        self.getArrayController().rearrangeObjects()
        self._unsubscribeFromGlyph(glyph)

    def index(self, glyph):
        item = self._wrappedListItems[glyph]
        return self._list.index(item)

    def insert(self, index, glyph):
        item = self._wrapGlyphForList(glyph)
        self.getArrayController().insertObject_atArrangedObjectIndex_(item, index)
        self.getArrayController().rearrangeObjects()

    def extend(self, glyphs):
        items = [self._wrapGlyphForList(glyph) for glyph in glyphs]
        self.getArrayController().addObjects_(items)
        self.getArrayController().rearrangeObjects()

    def set(self, glyphs):
        """
        Set the glyphs in the view.
        """
        self._list._selectionCallback = None
        # remove sort descriptors
        self._arrayController.setSortDescriptors_([])
        # remove removed wrapped items
        removedGlyphs = set(self._wrappedListItems) - set(glyphs)
        for glyph in removedGlyphs:
            del self._wrappedListItems[glyph]
            self._unsubscribeFromGlyph(glyph)
        # wrap the glyphs for the list
        wrappedGlyphs = [self._wrapGlyphForList(glyph) for glyph in glyphs]
        items = NSMutableArray.arrayWithArray_(wrappedGlyphs)
        self._arrayController.setContent_(items)
        self._list._selectionCallback = self._selectionCallback

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
        self._glyphCellView.setCellRepresentationArguments_(kwargs)

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

