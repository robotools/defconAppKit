import os
from AppKit import *
import vanilla
from defconAppKit.controls.placardScrollView import DefconAppKitPlacardNSScrollView, PlacardPopUpButton


# -------
# Sorting
# -------

def fontFileNameSort(fonts):
    sortable = []
    noPathCounter = 0
    for font in fonts:
        if font.path is not None:
            s = os.path.basename(font.path)
        else:
            noPathCounter += 1
            s = []
            if font.info.familyName is not None:
                s = font.info.familyName
            else:
                s = "Untitled Family"
            if font.info.styleName is not None:
                s += "-" + font.info.styleName
            else:
                s += "-Untitled Style"
        sortable.append((s, font))
    fonts = [item[-1] for item in sorted(sortable)]
    return fonts

def _isItalic(font):
    isItalic = False
    if font.info.styleMapStyleName is not None and "italic" in font.info.styleMapStyleName:
        isItalic = True
    elif font.info.italicAngle != 0:
        isItalic = True
    return isItalic

def fontWidthWeightSort(fonts):
    sortable = []
    for font in fonts:
        isItalic = _isItalic(font)
        fileName = None
        if font.path is not None:
            fileName = os.path.basename(font.path)
        s = (
            font.info.familyName,
            font.info.openTypeOS2WidthClass,
            font.info.openTypeOS2WeightClass,
            isItalic,
            font.info.styleName,
            fileName,
            font
        )
        sortable.append(s)
    fonts = [item[-1] for item in sorted(sortable)]
    return fonts


# -----------
# Main Object
# -----------

class FontList(vanilla.List):

    """
    This object presents the user with a standard list showing fonts.
    It follows the same API as vanilla.List. When you set objects into
    the view, you always pass font objects. The object will then extract
    the relevant data to display.

    Constructor Arguments:

    All of the vanilla.List contstructor arguments apply, with the
    following modifications.

    columnDescriptions
    This sets up the columns in the list. These follow the same format
    of the column descriptions in vanilla.List. The only exception is that
    you need to provide an "attribute" key/value pair. This is the font
    attribute that the list will extract display values from. For example:

        dict(title="Font Path", key="fontPath", attribute="path")

    If no columnDescriptions is provided, the font will be shown in a single
    single column represented with its file name or a combination of its
    family and style names.

    The list may show an "Options..." placard if either of the following is given:

    placardSortItems
    A list of dictionaries describing font sorting options. The dictionaries
    must follow this form:

        dict(title=string, callback=callback)

    The title must begin with "Sort by" for this to work properly. The callback
    must accept one argument: fonts. This will be a list of all fonts in the list.
    The callback should return a list of sorted fonts.

    placardItems
    A list of dictionaries describing arbitrary items to show in the placard.
    The dictionaries must follow this form:

        dict(title=string, callback=callback)

    The callback must accept one argument, sender, which will be the font list.
    """

    nsScrollViewClass = DefconAppKitPlacardNSScrollView

    def __init__(self, posSize, items,
        placardSortItems=[
            dict(title="Sort by File Name", callback=fontFileNameSort),
            dict(title="Sort by Weight and Width", callback=fontWidthWeightSort),
        ],
        placardItems=[],
        **kwargs):
        # make default column descriptions if needed
        if not kwargs.get("columnDescriptions"):
            kwargs["columnDescriptions"] = [fontListFontNameColumnDescription]
            kwargs["showColumnTitles"] = False
        # set some defaults
        kwargs["autohidesScrollers"] = False
        # build the internal column reference
        self._keyToAttribute = {}
        self._orderedListKeys = []
        self._wrappedListItems = {}
        for columnDescription in kwargs["columnDescriptions"]:
            title = columnDescription["title"]
            key = columnDescription.get("key", title)
            attribute = columnDescription["attribute"]
            self._keyToAttribute[key] = attribute
            self._orderedListKeys.append(key)
        # wrap the items
        items = [self._wrapFontForList(font) for font in items]
        # start the list
        super(FontList, self).__init__(posSize, items, **kwargs)
        # set the initial sort mode
        self._sortMode = None
        self._placardSortOptions = {}
        self._placardOptions = {}
        # placard
        if len(placardSortItems) + len(placardItems):
            # build the sort options
            if placardSortItems:
                self._sortMode = placardSortItems[0]["title"]
                for d in placardSortItems:
                    title = d["title"]
                    assert title.startswith("Sort by")
                    self._placardSortOptions[title] = d["callback"]
            # build the other options
            if placardItems:
                for d in placardItems:
                    self._placardOptions[d["title"]] = d["callback"]
            # build
            placardW = 65
            placardH = 16
            self._placard = vanilla.Group((0, 0, placardW, placardH))
            # make a default item
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Options...", None, "")
            item.setHidden_(True)
            items = [item]
            # add the items
            items += [d["title"] for d in placardSortItems]
            items += [d["title"] for d in placardItems]
            self._placard.optionsButton = PlacardPopUpButton((0, 0, placardW, placardH), items,
                callback=self._placardCallback, sizeStyle="mini")
            button = self._placard.optionsButton.getNSPopUpButton()
            button.setTitle_("Options...")
            self._nsObject.setPlacard_(self._placard.getNSView())
        # update the sort
        self._updateSort()

    def _breakCycles(self):
        for font in self._wrappedListItems.keys():
            del self._wrappedListItems[font]
            self._unsubscribeFromFont(font)
        self._placard = None
        self._placardSortOptions = {}
        super(FontList, self)._breakCycles()

    def setSortMode(self, mode):
        """
        Set the sort mode in the popup. 
        """
        self._sortMode = mode
        self._updateSort()

    # -------------------
    # Placard and Sorting
    # -------------------

    def _placardCallback(self, sender):
        index = sender.get()
        title = sender.getItems()[index]
        # title item
        if title == "Options...":
            return
        # sorting
        elif title.startswith("Sort by"):
            self._sortMode = title
            self._updateSort()
        # other
        else:
            self._placardOptions[title](self)
        sender.set(0)

    def _updateSort(self):
        if self._sortMode is None:
            return
        # gather the wrappers and the selection states
        oldSelection = self.getSelection()
        fontToWrapper = {}
        for index, wrapper in enumerate(self._arrayController.content()):
            fontToWrapper[wrapper["_font"]] = (wrapper, index in oldSelection)
        # sort the fonts
        fonts = fontToWrapper.keys()
        sortFunction = self._placardSortOptions[self._sortMode]
        fonts = sortFunction(fonts)
        # clear the list
        count = len(self)
        for index in range(count):
            count -= 1
            super(FontList, self).__delitem__(count)
        # reset the items
        sortedWrappers = []
        newSelection = []
        for index, font in enumerate(fonts):
            wrapper, selected = fontToWrapper[font]
            sortedWrappers.append(wrapper)
            if selected:
                newSelection.append(index)
        super(FontList, self).set(sortedWrappers)
        # reset the selection
        self.setSelection(newSelection)

    # -------------
    # list behavior
    # -------------

    def _subscribeToFont(self, font):
        font.addObserver(self, "_fontChanged", "Font.Changed")

    def _unsubscribeFromFont(self, font):
        font.removeObserver(self, "Font.Changed")

    def _fontChanged(self, notification):
        font = notification.object
        if font not in self._wrappedListItems:
            return
        d = self._wrappedListItems[font]
        for key, attr in self._keyToAttribute.items():
            d[key] = getattr(font, attr)

    # editing

    def _listEditCallback(self, sender):
        # skip if in an edit loop
        if self._listEditChangingFont is not None:
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
        item = super(FontList, self).__getitem__(rowIndex)
        font = item["_font"]()
        self._listEditChangingAttribute = editedAttribute
        self._listEditChangingFont = font
        # known attribute. procees it individually.
        if editedAttribute is not None:
            # set the attribute
            value = item[editedKey]
            fontValue = getattr(font, editedAttribute)
            if value != fontValue:
                setattr(font, editedAttribute, value)
        # unknown attribute. process all.
        else:
            for key, attribute in self._keyToAttribute.items():
                value = getattr(font, attribute)
                if value != item[key]:
                    setattr(font, attribute, item[key])
        # update the dict contents
        for key, attribute in self._keyToAttribute.items():
            if key == editedKey and attribute == editedAttribute:
                continue
            value = getattr(font, attribute)
            if value != item[key]:
                item[key] = value
        self._listEditChangingAttribute = None
        self._listEditChangingFont = None

    # wrapping

    def _wrapFontForList(self, font):
        changed = False
        if font in self._wrappedListItems:
            d = self._wrappedListItems[font]
        else:
            d = NSMutableDictionary.dictionary()
            self._subscribeToFont(font)
        for key, attribute in self._keyToAttribute.items():
            if attribute == defaultFontIDAttribute:
                value = makeDefaultIDString(font)
            else:
                value = getattr(font, attribute)
            if not key in d or d.get(key) != value:
                d[key] = value
                changed = True
        d["_font"] = font
        if changed:
            self._wrappedListItems[font] = d
        return d

    def _unwrapListItems(self, items=None):
        if items is None:
            items = super(FontList, self).get()
        fonts = [d["_font"] for d in items]
        return fonts

    # standard API

    def __contains__(self, font):
        return font in self._wrappedListItems

    def __getitem__(self, index):
        item = super(FontList, self).__getitem__(index)
        font = self._unwrapListItems([item])[0]
        return font

    def __setitem__(self, index, font):
        existing = self[index]
        item = self._wrapFontForList(font)
        super(FontList, self).__setitem__(index, font)
        if not super(FontList, self).__contains__(existing):
            otherFont = existing["_font"]
            del self._wrappedListItems[otherFont]
            self._unsubscribeFromFont(otherFont)

    def __delitem__(self, index):
        item = super(FontList, self).__getitem__(index)
        super(FontList, self).__delitem__(index)
        if not super(FontList, self).__contains__(item):
            font = item["_font"]
            del self._wrappedListItems[font]
            self._unsubscribeFromFont(font)

    def append(self, font):
        item = self._wrapFontForList(font)
        super(FontList, self).append(item)

    def remove(self, font):
        item = self._wrappedListItems[font]
        super(FontList, self).remove(item)
        if not super(FontList, self).__contains__(item):
            font = item["_font"]
            del self._wrappedListItems[font]
            self._unsubscribeFromFont(font)

    def index(self, font):
        item = self._wrappedListItems[font]
        return super(FontList, self).index(item)

    def insert(self, index, font):
        item = self._wrapFontForList(font)
        super(FontList, self).insert(index, item)

    def extend(self, fonts):
        items = [self._wrapFontForList(font) for font in fonts]
        super(FontList, self).extend(items)

    def set(self, fonts):
        """
        Set the fonts in the list.
        """
        # remove removed wrapped items
        removedFonts = set(self._wrappedListItems) - set(fonts)
        for font in removedFonts:
            del self._wrappedListItems[font]
            self._unsubscribeFromFont(font)
        # wrap the fonts for the list
        wrappedFonts = [self._wrapFontForList(font) for font in fonts]
        # set the list
        super(FontList, self).set(wrappedFonts)

    def get(self):
        """
        Get the fonts in the list.
        """
        return self._unwrapListItems()

# --------------------------
# Formatters, Cells and Such
# --------------------------

class DirtyStatusIndicatorCell(NSActionCell):

    def drawWithFrame_inView_(self, frame, view):
        value = self.objectValue()
        if not value:
            image = _drawDirtyStateImage(value)
        image = _drawDirtyStateImage(value)
        image.drawAtPoint_fromRect_operation_fraction_(frame.origin, ((0, 0), (13, 17)), NSCompositeSourceOver, 1.0)


def _drawDirtyStateImage(value):
    if value:
        imageName = "defconAppKitFontListDirtyStateTrue"
    else:
        imageName = "defconAppKitFontListDirtyStateFalse"
    image = NSImage.imageNamed_(imageName)
    if image is None:
        # make the image
        width = 13
        height = 17
        image = NSImage.alloc().initWithSize_((width, height))
        image.lockFocus()
        # draw if dirty
        if value:
            rect = ((2, 4), (9, 9))
            path = NSBezierPath.bezierPathWithOvalInRect_(rect)
            path.addClip()
            # colors
            color1 = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.1, 0.1, 1)
            color2 = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.5, 0.0, 0.0, 1)
            # fill
            color1.set()
            path.fill()
            # shadow
            try:
                gradient = NSGradient.alloc().initWithColors_([color1, color2])
                gradient.drawInBezierPath_angle_(path, -90)
            except NameError:
                pass
            # stroke
            color2.set()
            path.setLineWidth_(2)
            path.stroke()
        image.unlockFocus()
        image.setName_(imageName)
        image = NSImage.imageNamed_(imageName)
    return image


class FilePathFormatter(NSFormatter):

    def stringForObjectValue_(self, obj):
        if obj is None or isinstance(obj, NSNull):
            return ""
        return obj

    def attributedStringForObjectValue_withDefaultAttributes_(self, obj, attrs):
        if obj is None or isinstance(obj, NSNull):
            obj = ""
        paragraph = NSMutableParagraphStyle.alloc().init()
        paragraph.setLineBreakMode_(NSLineBreakByTruncatingHead)
        attrs = dict(attrs)
        attrs[NSParagraphStyleAttributeName] = paragraph
        return NSAttributedString.alloc().initWithString_attributes_(obj, attrs)

    def objectValueForString_(self, string):
        return string


def makeDefaultIDString(font):
    if font.path is None:
        if font.info.familyName is not None:
            s = font.info.familyName
        else:
            s = "Untitled Family"
        if font.info.styleName is not None:
            s += "-" + font.info.styleName
        else:
            s += "-Untitled Style"
        return s
    else:
        return os.path.basename(font.path)


# --------------------------
# Common Column Descriptions
# --------------------------

defaultFontIDAttribute = "defconAppKitFontIDString"
fontListFontNameColumnDescription = dict(title="Font", attribute=defaultFontIDAttribute, editable=False)
fontListFontPathColumnDescription = dict(title="Path", attribute="path", editable=False, formatter=FilePathFormatter.alloc().init())
fontListDirtyStateColoumnDescription = dict(title="Dirty", attribute="dirty", cell=DirtyStatusIndicatorCell.alloc().init(), width=13, editable=False)
