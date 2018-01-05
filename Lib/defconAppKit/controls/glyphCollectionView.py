import weakref
from AppKit import NSView, NSSegmentStyleSmallSquare, NSSmallSquareBezelStyle
import vanilla
from defconAppKit.controls.glyphCellView import DefconAppKitGlyphCellNSView, gridColor, GlyphInformationPopUpWindow, GlyphCellItem
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
    glyphCellItemClass = GlyphCellItem

    def __init__(self, posSize, font=None, initialMode="cell", listColumnDescriptions=None, listShowColumnTitles=False,
            showPlacard=True, showModePlacard=True, placardActionItems=None,
            cellRepresentationName="defconAppKit.GlyphCell", glyphDetailWindowClass=GlyphInformationPopUpWindow,
            selectionCallback=None, doubleClickCallback=None, deleteCallback=None, editCallback=None,
            enableDelete=False,
            selfDropSettings=None, selfWindowDropSettings=None, selfDocumentDropSettings=None, selfApplicationDropSettings=None,
            otherApplicationDropSettings=None, allowDrag=False, dragAndDropType="DefconAppKitSelectedGlyphIndexesPboardType"):

        self._holdCallbacks = True
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
        # set up the list
        self._listEditChangingAttribute = None
        self._listEditChangingGlyph = None
        enableDelete = deleteCallback is not None

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

        self._glyphCellView = self.glyphCellViewClass.alloc().initWithFont_cellRepresentationName_detailWindowClass_(
            font, cellRepresentationName, glyphDetailWindowClass)
        self._glyphCellView.vanillaWrapper = weakref.ref(self)
        self._glyphCellView.setAllowsDrag_(allowDrag)

        dropTypes = []
        for d in (selfDropSettings, selfWindowDropSettings, selfDocumentDropSettings, selfApplicationDropSettings, otherApplicationDropSettings):
            if d is not None:
                dropTypes.append(d["type"])
        self._glyphCellView.registerForDraggedTypes_(dropTypes)

        self._list = self.glyphListViewVanillaClass(
            (0, 0, 0, bottom), None,
            dataSource=self._arrayController,
            columnDescriptions=listColumnDescriptions,
            editCallback=editCallback,
            selectionCallback=self._listSelectionCallback,
            doubleClickCallback=doubleClickCallback,
            showColumnTitles=listShowColumnTitles,
            enableTypingSensitivity=True,
            enableDelete=enableDelete,
            autohidesScrollers=True,
            selfDropSettings=selfDropSettings,
            selfWindowDropSettings=selfWindowDropSettings,
            selfDocumentDropSettings=selfDocumentDropSettings,
            selfApplicationDropSettings=selfApplicationDropSettings,
            otherApplicationDropSettings=otherApplicationDropSettings,
            dragSettings=dragSettings
        )

        # set up the placard
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
                button.setBezelStyle_(NSSmallSquareBezelStyle)
                self._placard.actionButton = actionButton
            # extension
            self._placard.extension = vanilla.Group((extensionLeft, 0, extensionWidth, 0))
        else:
            self._placard = None
        # tweak the scroll view
        self._list.getNSScrollView().setBackgroundColor_(gridColor)
        # set the mode
        self._mode = None
        self.setMode(initialMode)
        self._holdCallbacks = False

    def getArrayController(self):
        return self._glyphCellView.arrayController

    _arrayController = property(getArrayController)

    def _breakCycles(self):
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
            if placard is not None and hasattr(placard, "button"):
                placard.button.set(0)
        self._list.getNSScrollView().setDocumentView_(documentView)
        self._mode = mode
        if mode == "cell":
            # cell view
            self._glyphCellView.recalculateFrame()
        elif mode == "list":
            self._list.getNSTableView().sizeToFit()

    def getMode(self):
        """
        Get the current mode.
        """
        return self._mode

    # standard API

    def set(self, glyphs):
        if not glyphs:
            self.setFont(None)
        else:
            self.setFont(glyphs[0].font)
        self.setGlyphNames([glyph.name for glyph in glyphs])

    def get(self):
        font = self._glyphCellView.getFont()
        return [font[glyphName] for glyphName in self._glyphCellView._glyphNames if glyphName in font]

    def setGlyphNames(self, glyphNames):
        self._holdCallbacks = True
        self._glyphCellView.unSubscribeGlyphs()
        items = [self._wrapItem(glyphName) for glyphName in glyphNames]
        self.getArrayController().setContent_(None)
        self.getArrayController().addObjects_(items)
        self._holdCallbacks = False
        self._glyphCellView.recalculateFrame()

    def getGlyphNames(self):
        return self._glyphCellView._glyphNames

    def setFont(self, font):
        self._glyphCellView.setFont_(font)

    def _wrapItem(self, glyphName, glyph=None):
        item = self.glyphCellItemClass(glyphName, self._glyphCellView.getFont())
        if glyph is not None:
            item.setGlyphExternally_(glyph)
        return item

    def _removeSelection(self):
        if not self._enableDelete:
            return
        selection = self.getSelection()
        # list
        for index in reversed(sorted(selection)):
            del self[index]
        # call the callback
        if self._deleteCallback is not None:
            self._deleteCallback(self)

    def __contains__(self, glyph):
        return glyph.name in self.getGlyphNames()

    def __getitem__(self, index):
        return self._arrayController.arrangedObjects()[index].glyph()

    def __setitem__(self, index, glyph):
        # list
        existing = self._arrayController.arrangedObjects()[index]
        self._glyphCellView.unSubscribeGlyph(existing.glyph())
        existing.setGlyphExternally_(glyph)

    def __delitem__(self, index):
        # list
        existing = self._arrayController.arrangedObjects()[index]
        self._glyphCellView.unSubscribeGlyph(existing.glyph())
        self._arrayController.removeObject_(existing)

    def __len__(self):
        return self.getArrayController().arrangedObjects().count()

    def append(self, glyph):
        item = self._wrapItem(glyph.name, glyph=glyph)
        self.getArrayController().addObject_(item)
        self.getArrayController().rearrangeObjects()

    def remove(self, glyph):
        index = self.index(glyph)
        del self[index]

    def index(self, glyph):
        return self.getGlyphNames().index(glyph.name)

    def insert(self, index, glyph):
        item = self._wrapItem(glyph.name, glyph=glyph)
        self.getArrayController().insertObject_atArrangedObjectIndex_(item, index)
        self.getArrayController().rearrangeObjects()

    def extend(self, glyphs):
        items = [self._wrapItem(glyph.name, glyph=glyph) for glyph in glyphs]
        self.getArrayController().addObjects_(items)
        self.getArrayController().rearrangeObjects()

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
        selection = self._arrayController.selectionIndexes()
        # if nothing is selected return an empty list
        if not selection:
            return []
        return list(self._list._iterIndexSet(selection))

    def setSelection(self, selection):
        """
        Sets the selection in the view. The passed value
        should be a list of indexes.
        """
        self._list.setSelection(selection)
        if self.getMode() == "cell":
            self._glyphCellView.setLastFoundSelection(selection)
            self._glyphCellView.setNeedsDisplay_(True)

    def scrollToSelection(self):
        """
        Scroll the view so that the current selection is visible.
        """
        self._list.scrollToSelection()
        selection = self.getSelection()
        if selection:
            self._glyphCellView.scrollToCell_(selection[0])

    def _listSelectionCallback(self, sender):
        if self._holdCallbacks:
            return
        self._glyphCellView.setLastFoundSelection(self.getSelection())
        if self._selectionCallback is not None:
            self._selectionCallback(self)

    # -------------
    # drag and drop
    # -------------

    def _get_selfDropSettings(self):
        return self._list._selfDropSettings

    _selfDropSettings = property(_get_selfDropSettings)

    def _get_selfWindowDropSettings(self):
        return self._list._selfWindowDropSettings

    _selfWindowDropSettings = property(_get_selfWindowDropSettings)

    def _get_selfDocumentDropSettings(self):
        return self._list._selfDocumentDropSettings

    _selfDocumentDropSettings = property(_get_selfDocumentDropSettings)

    def _get_selfApplicationDropSettings(self):
        return self._list._selfApplicationDropSettings

    _selfApplicationDropSettings = property(_get_selfApplicationDropSettings)

    def _get_otherApplicationDropSettings(self):
        return self._list._otherApplicationDropSettings

    _otherApplicationDropSettings = property(_get_otherApplicationDropSettings)

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

    # ------------------
    # cell view behavior
    # ------------------

    def getGlyphCellView(self):
        """
        Get the cell NSView.
        """
        return self._glyphCellView

    def setCellSize(self, wh):
        """
        Set the size of the cells.
        """
        self._glyphCellView.setCellSize_(wh)

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
