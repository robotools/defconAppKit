from fontTools.misc.py23 import *
try:
    long
except:
    # py3 has no long
    long = int
import time
from copy import deepcopy
from Foundation import NSArray
from AppKit import NSOnOffButton, NSRoundRectBezelStyle, NSDate, NSColor, NSFontNameAttribute, \
    NSFormatter, NSTextField, NSTextView, NSTextFieldCell, NSView, NSNoTabsNoBorder, NSButton, NSObject, \
    NSDecimalNumber, NSString, NSInsetRect, NSNumberFormatter, NSPointInRect, NSMaxY, NSNull, NSWarningAlertStyle, \
    NSMutableIndexSet, NSSegmentedCell, NSRectFill
import vanilla
from vanilla.py23 import python_method
from vanilla import dialogs
from vanilla.vanillaList import VanillaTableViewSubclass
from ufo2fdk.fontInfoData import getAttrWithFallback, dateStringToTimeValue
from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath


# --------------------------
# First Responder Subclasses
# --------------------------

# EditText

class DefconAppKitTextField(NSTextField):

    def becomeFirstResponder(self):
        result = super(DefconAppKitTextField, self).becomeFirstResponder()
        if result:
            view = self.superview()
            if hasattr(view, "scrollControlToVisible_"):
                view.scrollControlToVisible_(self)
        return result


class InfoEditText(vanilla.EditText):

    nsTextFieldClass = DefconAppKitTextField


# TextEditor

class DefconAppKitTextView(NSTextView):

    def becomeFirstResponder(self):
        result = super(DefconAppKitTextView, self).becomeFirstResponder()
        if result:
            scrollView = self.enclosingScrollView()
            view = scrollView.superview()
            if hasattr(view, "scrollControlToVisible_"):
                view.scrollControlToVisible_(scrollView)
        return result


class InfoTextEditor(vanilla.TextEditor):

    nsTextViewClass = DefconAppKitTextView


# List

class DefconAppKitTableView(VanillaTableViewSubclass):

    def setIsWrappedList_(self, value):
        self._isWrappedList = value

    def isWrappedList(self):
        return getattr(self, "_isWrappedList", False)

    def becomeFirstResponder(self):
        result = super(DefconAppKitTableView, self).becomeFirstResponder()
        if result:
            parentView = self.enclosingScrollView()
            if self.isWrappedList():
                parentView = parentView.superview()
            view = parentView
            while 1:
                view = view.superview()
                if view is None:
                    break
                if hasattr(view, "scrollControlToVisible_"):
                    break
            if view is not None:
                if hasattr(view, "scrollControlToVisible_"):
                    view.scrollControlToVisible_(parentView)
        return result


class InfoList(vanilla.List):

    nsTableViewClass = DefconAppKitTableView

    def setIsWrappedList(self, value):
        self.getNSTableView().setIsWrappedList_(value)


class InfoCheckbox(vanilla.CheckBox):

    def get(self):
        # be sure to return a bool
        value = super(InfoCheckbox, self).get()
        return bool(value)


# -----------------------------------
# Formatters
# These will be used in the controls.
# -----------------------------------

class NumberEditText(InfoEditText):

    def __init__(self, posSize, text="", sizeStyle="regular", callback=None, allowFloat=True, allowNegative=True, minimum=None, maximum=None, decimals=2):
        super(NumberEditText, self).__init__(posSize, text="", callback=self._entryCallback, sizeStyle=sizeStyle)
        self._finalCallback = callback
        self._allowFloat = allowFloat
        self._allowNegative = allowNegative
        self._minimum = minimum
        self._maximum = maximum
        if allowFloat:
            self._floatFormat = "%%.%df" % decimals
        if allowFloat:
            self._numberClass = float
        else:
            self._numberClass = int
        self._previousString = None
        self.set(text)

    def _numberToString(self, value):
        if self._allowFloat:
            if not float(value).is_integer():
                return self._floatFormat % value
        return str(value)

    def _stringToNumber(self, string):
        value = None
        newString = string
        try:
            value = self._numberClass(string)
            if value < 0 and not self._allowNegative:
                newString = self._previousString
                value, n = self._stringToNumber(newString)
            if self._minimum is not None and value < self._minimum:
                value = self._minimum
                newString = self._numberToString(value)
            if self._maximum is not None and value > self._maximum:
                value = self._maximum
                newString = self._numberToString(value)
        except ValueError:
            value = None
            if string == "":
                pass
            elif string == "-" and self._allowNegative:
                pass
            elif string == "." and self._allowFloat:
                pass
            elif string == "-." and self._allowFloat and self._allowNegative:
                pass
            else:
                newString = self._previousString
        # handle -0.0
        if value == 0:
            value = 0
        return value, newString

    def _entryCallback(self, sender):
        oldString = super(NumberEditText, self).get()
        value, newString = self._stringToNumber(oldString)
        self._previousString = newString
        if newString != oldString:
            super(NumberEditText, self).set(newString)
        self._finalCallback(sender)

    def get(self):
        string = super(NumberEditText, self).get()
        return self._stringToNumber(string)[0]

    def set(self, value):
        if value is None:
            self._previousString = ""
        else:
            self._previousString = value
        if value == "":
            value = None
        if isinstance(value, basestring):
            if self._allowFloat:
                value = float(value)
            else:
                value = int(value)
        if value is not None:
            value = self._numberToString(value)
        super(NumberEditText, self).set(value)


class NumberSequenceFormatter(NSFormatter):

    def initWithMaxValuesCount_requiresEvenCount_(self, maxValuesCount, requiresEvenCount):
        self = super(NumberSequenceFormatter, self).init()
        self.maxValuesCount = maxValuesCount
        self.requiresEvenCount = requiresEvenCount
        return self

    def stringForObjectValue_(self, obj):
        if obj is None or isinstance(obj, NSNull):
            return ""
        if isinstance(obj, basestring):
            return obj
        else:
            return " ".join([str(i) for i in obj])

    def isPartialStringValid_newEditingString_errorDescription_(self, oldString, newString, error):
        valid, partiallyValid, value, error = self._parseString(oldString)
        if partiallyValid:
            error = None
        return partiallyValid, oldString, error

    # def attributedStringForObjectValue_withDefaultAttributes_(self, value, attrs):
    #     value = self.stringForObjectValue_(value)
    #     valid, partiallyValid, value, error = self._parseString(value)
    #     if not valid:
    #         attrs[NSForegroundColorAttributeName] = NSColor.redColor()
    #     else:
    #         attrs[NSForegroundColorAttributeName] = NSColor.blackColor()
    #     string = NSAttributedString.alloc().initWithString_attributes_(value, attrs)
    #     return string

    @python_method
    def _parseString(self, string):
        isValid = True
        isPartiallyValid = True
        errorString = None
        if not string.strip():
            pass
        else:
            values = []
            try:
                tempValues = []
                for i in string.strip().split(" "):
                    if not i:
                        continue
                    if i == "-":
                        continue
                    i = float(i)
                    if i.is_integer():
                        i = int(i)
                    tempValues.append(i)
                values = tempValues
            except ValueError:
                isValid = False
                isPartiallyValid = False
                errorString = "Could not convert entries to integers."
            if isValid:
                if self.requiresEvenCount and len(values) % 2:
                    isValid = False
                    errorString = "An even number of values is required."
                if len(values) > self.maxValuesCount:
                    isValid = False
                    isPartiallyValid = False
                    errorString = "Too many values."
        return isValid, isPartiallyValid, string, errorString

    def getObjectValue_forString_errorDescription_(self, value, string, error):
        valid, partiallyValid, value, error = self._parseString(string)
        return valid, value, error


# --------------------------------------------------------
# Special Controls
# These are vanilla subclasses that have special behavior.
# --------------------------------------------------------

# openTypeOS2Panose Control

panoseFamilyKindOptions = """Any
No Fit
Latin Text
Latin Hand Written
Latin Decorative
Latin Symbol""".splitlines()

panoseLatinTextOptions = """
Serif Style
Weight
Proportion
Contrast
Stroke Variation
Arm Style
Letterform
Midline
X-height
---
Any
No Fit
Cove
Obtuse Cove
Square Cove
Obtuse Square Cove
Square
Thin
Oval
Exaggerated
Triangle
Normal Sans
Obtuse Sans
Perpendicular Sans
Flared
Rounded
---
Any
No Fit
Very Light
Light
Thin
Book
Medium
Demi
Bold
Heavy
Black
Extra Black
---
Any
No fit
Old Style
Modern
Even Width
Extended
Condensed
Very Extended
Very Condensed
Monospaced
---
Any
No Fit
None
Very Low
Low
Medium Low
Medium
Medium High
High
Very High
---
Any
No Fit
No Variation
Gradual/Diagonal
Gradual/Transitional
Gradual/Vertical
Gradual/Horizontal
Rapid/Vertical
Rapid/Horizontal
Instant/Vertical
Instant/Horizontal
---
Any
No Fit
Straight Arms/Horizontal
Straight Arms/Wedge
Straight Arms/Vertical
Straight Arms/Single Serif
Straight Arms/Double Serif
Non-Straight/Horizontal
Non-Straight/Wedge
Non-Straight/Vertical
Non-Straight/Single Serif
Non-Straight/Double Serif
---
Any
No Fit
Normal/Contact
Normal/Weighted
Normal/Boxed
Normal/Flattened
Normal/Rounded
Normal/Off Center
Normal/Square
Oblique/Contact
Oblique/Weighted
Oblique/Boxed
Oblique/Flattened
Oblique/Rounded
Oblique/Off Center
Oblique/Square
---
Any
No Fit
Standard/Trimmed
Standard/Pointed
Standard/Serifed
High/Trimmed
High/Pointed
High/Serifed
Constant/Trimmed
Constant/Pointed
Constant/Serifed
Low/Trimmed
Low/Pointed
Low/Serifed
---
Any
No Fit
Constant/Small
Constant/Standard
Constant/Large
Ducking/Small
Ducking/Standard
Ducking/Large
"""

panoseLatinHandWrittenOptions = """
Tool Kind
Weight
Spacing
Aspect Ratio
Contrast
Topology
Form
Finials
X-ascent
---
Any
No Fit
Flat Nib
Pressure Point
Engraved
Ball (Round Cap)
Brush
Rough
Felt Pen/Brush Tip
Wild Brush - Drips a lot
---
Any
No Fit
Very Light
Light
Thin
Book
Medium
Demi
Bold
Heavy
Black
Extra Black (Nord)
---
Any
No fit
Proportional Spaced
Monospaced
---
Any
No Fit
Very Condensed
Condensed
Normal
Expanded
Very Expanded
---
Any
No Fit
None
Very Low
Low
Medium Low
Medium
Medium High
High
Very High
---
Any
No Fit
Roman Disconnected
Roman Trailing
Roman Connected
Cursive Disconnected
Cursive Trailing
Cursive Connected
Blackletter Disconnected
Blackletter Trailing
Blackletter Connected
---
Any
No Fit
Upright / No Wrapping
Upright / Some Wrapping
Upright / More Wrapping
Upright / Extreme Wrapping
Oblique / No Wrapping
Oblique / Some Wrapping
Oblique / More Wrapping
Oblique / Extreme Wrapping
Exaggerated / No Wrapping
Exaggerated / Some Wrapping
Exaggerated / More Wrapping
Exaggerated / Extreme Wrapping
---
Any
No Fit
None / No loops
None / Closed loops
None / Open loops
Sharp / No loops
Sharp / Closed loops
Sharp / Open loops
Tapered / No loops
Tapered / Closed loops
Tapered / Open loops
Round / No loops
Round / Closed loops
Round / Open loops
---
Any
No Fit
Very Low
Low
Medium
High
Very High
"""

panoseLatinDecorativesOptions = """
Class
Weight
Aspect
Contrast
Serif Variant
Treatment
Lining
Topology
Range of Characters
---
Any
No Fit
Derivative
Non-standard Topology
Non-standard Elements
Non-standard Aspect
Initials
Cartoon
Picture Stems
Ornamented
Text and Background
Collage
Montage
---
Any
No Fit
Very Light
Light
Thin
Book
Medium
Demi
Bold
Heavy
Black
Extra Black
---
Any
No fit
Super Condensed
Very Condensed
Condensed
Normal
Extended
Very Extended
Super Extended
Monospaced
---
Any
No Fit
None
Very Low
Low
Medium Low
Medium
Medium High
High
Very High
Horizontal Low
Horizontal Medium
Horizontal High
Broken
---
Any
No Fit
Cove
Obtuse Cove
Square Cove
Obtuse Square Cove
Square
Thin
Oval
Exaggerated
Triangle
Normal Sans
Obtuse Sans
Perpendicular Sans
Flared
Rounded
Script
---
Any
No Fit
None - Standard Solid Fill
White / No Fill
Patterned Fill
Complex Fill
Shaped Fill
Drawn / Distressed
---
Any
No Fit
None
Inline
Outline
Engraved (Multiple Lines)
Shadow
Relief
Backdrop
---
Any
No Fit
Standard
Square
Multiple Segment
Deco (E,M,S) Waco midlines
Uneven Weighting
Diverse Arms
Diverse Forms
Lombardic Forms
Upper Case in Lower Case
Implied Topology
Horseshoe E and A
Cursive
Blackletter
Swash Variance
---
Any
No Fit
Extended Collection
Litterals
No Lower Case
Small Caps
"""

panoseLatinPictorialOptions = """
Kind
Weight
Spacing
Aspect Ratio & Contrast
Aspect Ratio of Char. 94
Aspect Ratio of Char. 119
Aspect Ratio of Char. 157
Aspect Ratio of Char. 163
Aspect Ratio of Char. 211
---
Any
No Fit
Montages
Pictures
Shapes
Scientific
Music
Expert
Patterns
Boarders
Icons
Logos
Industry specific
---
Any
No Fit
---
Any
No fit
Proportional Spaced
Monospaced
---
Any
No Fit
---
Any
No Fit
No Width
Exceptionally Wide
Super Wide
Very Wide
Wide
Normal
Narrow
Very Narrow
---
Any
No Fit
No Width
Exceptionally Wide
Super Wide
Very Wide
Wide
Normal
Narrow
Very Narrow
---
Any
No Fit
No Width
Exceptionally Wide
Super Wide
Very Wide
Wide
Normal
Narrow
Very Narrow
---
Any
No Fit
No Width
Exceptionally Wide
Super Wide
Very Wide
Wide
Normal
Narrow
Very Narrow
---
Any
No Fit
No Width
Exceptionally Wide
Super Wide
Very Wide
Wide
Normal
Narrow
Very Narrow
"""


def makePanoseOptions(text):
    text = text.strip()
    groups = text.split("---")
    groups = [i.strip() for i in groups]
    assert len(groups) == 10
    groups = [group.splitlines() for group in groups]
    titles = groups[0]
    options = groups[1:]
    return titles, options


panoseControlOptionTree = [
    ("Any", [[] for i in range(9)]),
    ("No Fit", [[] for i in range(9)]),
    makePanoseOptions(panoseLatinTextOptions),
    makePanoseOptions(panoseLatinHandWrittenOptions),
    makePanoseOptions(panoseLatinDecorativesOptions),
    makePanoseOptions(panoseLatinPictorialOptions)
]


class PanoseControl(vanilla.Group):

    def __init__(self, posSize, titlePosition, titleWidth, buttonPosition, buttonWidth, callback):
        super(PanoseControl, self).__init__(posSize)
        self._callback = callback
        self.title = vanilla.TextBox((titlePosition, 0, -0, 17), "Panose")
        self.titleLine = vanilla.HorizontalLine((titlePosition, 22, -titlePosition, 1))
        self.familyKindTitle = vanilla.TextBox((titlePosition, 42, titleWidth, 17), "Family Kind:", alignment="right")
        self.familyKindPopUp = vanilla.PopUpButton((buttonPosition, 40, buttonWidth, 20), panoseFamilyKindOptions, self._familyKindCallback)
        currentTop = 70
        for i in range(9):
            attribute = "title%d" % i
            control = vanilla.TextBox((titlePosition, currentTop + 2, titleWidth, 17), "", alignment="right")
            setattr(self, attribute, control)
            attribute = "popup%d" % i
            control = vanilla.PopUpButton((buttonPosition, currentTop, buttonWidth, 20), [], callback=self._subdigitCallback)
            setattr(self, attribute, control)
            currentTop += 30
        self._currentFamilyKind = 0

    def _breakCycles(self):
        self._callback = None
        super(PanoseControl, self)._breakCycles()

    def _familyKindCallback(self, sender):
        value = sender.get()
        if value == self._currentFamilyKind:
            return
        self.set([value, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        self._callback(self)

    def _subdigitCallback(self, sender):
        self._callback(self)

    def set(self, value):
        # get the family kind data
        familyKind = self._currentFamilyKind = value[0]
        familyTitles, familyOptions = panoseControlOptionTree[familyKind]
        if familyKind in (0, 1):
            familyTitles = "        ".split(" ")
        # set the family
        self.familyKindPopUp.set(familyKind)
        # update the titles
        for index, title in enumerate(familyTitles):
            if title:
                title += ":"
            attribute = "title%d" % index
            control = getattr(self, attribute)
            control.set(title)
        # update the buttons
        for index, options in enumerate(familyOptions):
            attribute = "popup%d" % index
            control = getattr(self, attribute)
            control.setItems(options)
            control.set(value[index + 1])

    def get(self):
        familyKind = self.familyKindPopUp.get()
        if familyKind in (0, 1):
            values = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        else:
            values = []
            for index in range(9):
                attribute = "popup%d" % index
                control = getattr(self, attribute)
                values.append(control.get())
        return [familyKind] + values


# openTypeOS2Type Control

embeddingPopUpOptions = """
No embedding restrictions.
No embedding allowed.
Only preview and print embedding allowed.
Editable embedding allowed.
""".strip().splitlines()


class EmbeddingControl(vanilla.Group):

    def __init__(self, posSize, callback):
        super(EmbeddingControl, self).__init__(posSize)
        self._callback = callback
        self.basicsPopUp = vanilla.PopUpButton((0, 0, -0, 20), embeddingPopUpOptions, callback=self._controlCallback)
        self.subsettingCheckBox = InfoCheckbox((0, 30, -0, 20), "Allow Subsetting", callback=self._controlCallback)
        self.bitmapCheckBox = InfoCheckbox((0, 55, -10, 20), "Allow Only Bitmap Embedding", callback=self._controlCallback)
        self.subsettingCheckBox.enable(False)
        self.bitmapCheckBox.enable(False)

    def _breakCycles(self):
        self._callback = None
        super(EmbeddingControl, self)._breakCycles()

    def _controlCallback(self, sender):
        self._handleEnable()
        self._callback(self)

    def _handleEnable(self):
        enable = self.basicsPopUp.get() != 0
        self.subsettingCheckBox.enable(enable)
        self.bitmapCheckBox.enable(enable)

    def set(self, values):
        if 1 in values:
            self.basicsPopUp.set(1)
        elif 2 in values:
            self.basicsPopUp.set(2)
        elif 3 in values:
            self.basicsPopUp.set(3)
        else:
            self.basicsPopUp.set(0)
        self.subsettingCheckBox.set(8 not in values)
        self.bitmapCheckBox.set(9 in values)
        self._handleEnable()

    def get(self):
        values = []
        basicValue = self.basicsPopUp.get()
        if basicValue == 0:
            return values
        values.append(basicValue)
        if not self.subsettingCheckBox.get():
            values.append(8)
        if self.bitmapCheckBox.get():
            values.append(9)
        return values


# List of check boxes

class CheckList(InfoList):

    def __init__(self, posSize, template, callback):
        # create the dict items
        self._bitToIndex = {}
        self._indexToBit = {}
        self._titles = list(template)
        for index, title in enumerate(template):
            bit = int(title.split(" ")[0])
            self._bitToIndex[bit] = index
            self._indexToBit[index] = bit
        items = self._wrapItems()
        # describe the columns
        columnDescriptions = [
            dict(title="value", cell=vanilla.CheckBoxListCell(), width=16),
            dict(title="title", editable=False),
        ]
        # let super do the rest
        super(CheckList, self).__init__(posSize, items, columnDescriptions=columnDescriptions,
            showColumnTitles=False, autohidesScrollers=False, editCallback=callback, drawFocusRing=False)
        self.getNSScrollView().setHasHorizontalScroller_(False)

    def _wrapItems(self, selectedBits=[]):
        items = []
        for index, title in enumerate(self._titles):
            bit = self._indexToBit[index]
            d = dict(value=bit in selectedBits, title=title)
            items.append(d)
        return items

    def set(self, items):
        items = self._wrapItems(items)
        super(CheckList, self).set(items)

    def get(self):
        items = super(CheckList, self).get()
        bits = []
        for index, item in enumerate(items):
            if not item["value"]:
                continue
            bit = self._indexToBit[index]
            bits.append(bit)
        return bits


# list of dictionaries

class DictList(vanilla.Group):

    def __init__(self, posSize, columnDescriptions, listClass=None, itemPrototype=None, callback=None, validator=None, variableRowHeights=False, showColumnTitles=True):
        self._prototype = itemPrototype
        self._callback = callback
        self._validator = validator
        super(DictList, self).__init__(posSize)
        if listClass is None:
            if variableRowHeights:
                listClass = VariableRowHeightList
            else:
                listClass = InfoList
        self._list = listClass((0, 0, -0, -20), [], columnDescriptions=columnDescriptions,
            editCallback=self._listEditCallback, drawFocusRing=False, showColumnTitles=showColumnTitles)
        self._list.setIsWrappedList(True)
        self._buttonBar = GradientButtonBar((0, -22, -0, 22))
        self._addButton = vanilla.GradientButton((0, -22, 22, 22), imageNamed="NSAddTemplate", callback=self._addButtonCallback)
        self._removeButton = vanilla.GradientButton((21, -22, 22, 22), imageNamed="NSRemoveTemplate", callback=self._removeButtonCallback)

    def _listEditCallback(self, sender):
        self._callback(self)
        self._validate()

    def _addButtonCallback(self, sender):
        item = deepcopy(self._prototype)
        self._list.append(item)

    def _removeButtonCallback(self, sender):
        selection = self._list.getSelection()
        for index in reversed(selection):
            del self._list[index]

    def _validate(self):
        if self._validator is not None:
            valid, message, information = self._validator(self.get())
            if not valid:
                view = self.getNSView()
                window = view.window()
                dialogs.message(messageText=message, informativeText=information, parentWindow=window, alertStyle=NSWarningAlertStyle)

    def get(self):
        return self._list.get()

    def set(self, items):
        hold = self._validator
        self._list.set(items)
        self._validator = hold


class DefconAppKitGradientButtonBar(NSButton):

    def acceptsFirstResponder(self):
        return False

    def mouseDown_(self, event):
        return

    def mouseUp_(self, event):
        return


class GradientButtonBar(vanilla.GradientButton):

        nsButtonClass = DefconAppKitGradientButtonBar


# variable row height list

class DefconAppKitVariableRowHeightTableView(DefconAppKitTableView):

    def frameOfCellAtColumn_row_(self, column, row):
        frame = super(DefconAppKitVariableRowHeightTableView, self).frameOfCellAtColumn_row_(column, row)
        if frame.size.height < 17:
            frame.size.height = 17.0
        return frame


class DefconAppKitVariableRowHeightTableViewDelegate(NSObject):

    def tableView_heightOfRow_(self, tableView, row):
        heights = []
        columns = tableView.tableColumns()
        for column in columns:
            column = columns[-1]
            cell = column.dataCell()
            hold = cell.stringValue()
            text = tableView.dataSource().content()[row][column.identifier()]
            cell.setStringValue_(text)
            width = column.width()
            rect = ((0, 0), (width, 10000))
            height = cell.cellSizeForBounds_(rect)[1]
            cell.setStringValue_(hold)
            heights.append(height)
        return max(heights)


class VariableRowHeightList(InfoList):

    nsTableViewClass = DefconAppKitVariableRowHeightTableView

    def __init__(self, *args, **kwargs):
        super(VariableRowHeightList, self).__init__(*args, **kwargs)
        tableView = self.getNSTableView()
        for column in tableView.tableColumns():
            cell = column.dataCell()
            if isinstance(cell, NSTextFieldCell):
                cell.setWraps_(True)
        assert tableView.delegate() is None
        self._delegate = DefconAppKitVariableRowHeightTableViewDelegate.alloc().init()
        tableView.setDelegate_(self._delegate)


# -------------------------------------------------------
# Input control definitions.
# These describe the controls and how they should behave.
# -------------------------------------------------------

def inputItemDict(**kwargs):
    default = dict(
        title=None,
        hasDefault=True,
        controlClass=InfoEditText,
        # controlOptions=None,
        conversionFromUFO=None,
        conversionToUFO=None
    )
    default.update(kwargs)
    return default


def noneToZero(value):
    if value is None:
        return 0
    return value


# Basic Naming

familyNameItem = inputItemDict(
    title="Family Name",
    hasDefault=False
)
styleNameItem = inputItemDict(
    title="Style Name",
    hasDefault=False
)
styleMapFamilyNameItem = inputItemDict(
    title="Style Map Family Name"
)

styleMapStyleOptions = ["regular", "italic", "bold", "bold italic"]


def styleMapStyleNameFromUFO(value):
    return styleMapStyleOptions.index(value)


def styleMapStyleNameToUFO(value):
    return styleMapStyleOptions[value]


styleMapStyleNameItem = inputItemDict(
    title="Style Map Style",
    controlClass=vanilla.RadioGroup,
    conversionFromUFO=styleMapStyleNameFromUFO,
    conversionToUFO=styleMapStyleNameToUFO,
    controlOptions=dict(items=["Regular", "Italic", "Bold", "Bold Italic"])
)
versionMajorItem = inputItemDict(
    title="Version Major",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
versionMinorItem = inputItemDict(
    title="Version Minor",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)

# Basic Dimensions

unitsPerEmItem = inputItemDict(
    title="Units Per Em",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowNegative=False)
)
descenderItem = inputItemDict(
    title="Descender",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number"),
    conversionToUFO=noneToZero
)
xHeightItem = inputItemDict(
    title="x-height",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number")
)
capHeightItem = inputItemDict(
    title="Cap-height",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number")
)
ascenderItem = inputItemDict(
    title="Ascender",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number")
)
italicAngleItem = inputItemDict(
    title="Italic Angle",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", decimals=10)
)

# Basic Legal

copyrightItem = inputItemDict(
    title="Copyright",
    hasDefault=False,
    controlOptions=dict(lineCount=5)
)
trademarkItem = inputItemDict(
    title="Trademark",
    hasDefault=False,
    controlOptions=dict(lineCount=5)
)
openTypeNameLicenseItem = inputItemDict(
    title="License",
    hasDefault=False,
    controlOptions=dict(lineCount=20)
)
openTypeNameLicenseURLItem = inputItemDict(
    title="License URL",
    hasDefault=False
)

# Basic Parties

openTypeNameDesignerItem = inputItemDict(
    title="Designer",
    hasDefault=False
)
openTypeNameDesignerURLItem = inputItemDict(
    title="Designer URL",
    hasDefault=False
)
openTypeNameManufacturerItem = inputItemDict(
    title="Manufacturer",
    hasDefault=False,
)
openTypeNameManufacturerURLItem = inputItemDict(
    title="Manufacturer URL",
    hasDefault=False,
)

# Basic Note

noteItem = inputItemDict(
    title="",
    hasDefault=False,
    controlOptions=dict(lineCount=20)
)


# OpenType gasp table

def openTypeGaspRangeRecordsFromUFO(value):
    if value is None:
        return []
    items = []
    for record in value:
        behavior = record.get("rangeGaspBehavior", [])
        if behavior is None:
            behavior = []
        item = dict(
            ppem=record["rangeMaxPPEM"],
            gridfit=0 in behavior,
            doGray=1 in behavior,
            symmSmoothing=2 in behavior,
            symmGridfit=3 in behavior
        )
        items.append(item)
    return items


def openTypeGaspRangeRecordsToUFO(value):
    sorter = {}
    for item in value:
        ppem = item["ppem"]
        sorter[ppem] = item
    records = []
    for ppem, item in sorted(sorter.items()):
        if isinstance(ppem, long):
            ppem = int(ppem)
        elif isinstance(ppem, NSDecimalNumber):
            ppem = int(ppem.intValue())
        behavior = []
        if item["gridfit"]:
            behavior.append(0)
        if item["doGray"]:
            behavior.append(1)
        if item["symmSmoothing"]:
            behavior.append(2)
        if item["symmGridfit"]:
            behavior.append(3)
        record = dict(rangeMaxPPEM=ppem, rangeGaspBehavior=behavior)
        records.append(record)
    return records


def openTypeGaspRangeRecordsInputValidator(records):
    # look for duplicate sizes
    ppems = []
    for record in records:
        ppem = record["ppem"]
        if isinstance(ppem, long):
            ppem = int(ppem)
        elif isinstance(ppem, NSDecimalNumber):
            ppem = int(ppem.intValue())
        if ppem in ppems:
            return False, "A duplicate PPEM %d record has been created." % ppem, "Duplicate PPEM records aren't allowed. Only the final PPEM %d record will be stored in the font." % ppem
        ppems.append(ppem)
    return True, None, None


openTypeGaspSizeFormatter = NSNumberFormatter.alloc().init()
openTypeGaspSizeFormatter.setPositiveFormat_("#")
openTypeGaspSizeFormatter.setAllowsFloats_(False)
openTypeGaspSizeFormatter.setGeneratesDecimalNumbers_(False)  # this seems to have no effect. NSNumberFormatter is awful.
openTypeGaspSizeFormatter.setMinimum_(0)
openTypeGaspSizeFormatter.setMaximum_(65535)

openTypeGaspRangeRecordsItem = inputItemDict(
    title="",
    hasDefault=False,
    controlClass=DictList,
    controlOptions=dict(
        showColumnTitles=False,
        columnDescriptions=[
            dict(key="ppem", title="Max PPEM", width=50, editable=True, formatter=openTypeGaspSizeFormatter),
            dict(key="gridfit", title="", width=60, editable=True, cell=vanilla.CheckBoxListCell(title="Gridfit")),
            dict(key="doGray", title="", width=77, editable=True, cell=vanilla.CheckBoxListCell(title="Grayscale")),
            dict(key="symmSmoothing", title="", width=143, editable=True, cell=vanilla.CheckBoxListCell(title="Symmetric Smoothing")),
            dict(key="symmGridfit", title="", editable=True, cell=vanilla.CheckBoxListCell(title="Symmetric Gridfit")),
        ],
        itemPrototype=dict(ppem=65535, gridfit=False, doGray=False, symmSmoothing=False, symmGridfit=False),
        validator=openTypeGaspRangeRecordsInputValidator
    ),
    conversionFromUFO=openTypeGaspRangeRecordsFromUFO,
    conversionToUFO=openTypeGaspRangeRecordsToUFO,
)


# OpenType head Table

def openTypeHeadCreatedFromUFO(value):
    t = dateStringToTimeValue(value)
    s = time.strftime("%Y/%m/%d %H:%M:%S +0000", time.gmtime(t))
    return NSDate.dateWithString_(s)


def openTypeHeadCreatedToUFO(value):
    value = value.descriptionWithCalendarFormat_timeZone_locale_("%Y/%m/%d %H:%M:%S", None, None)
    return value


openTypeHeadCreatedItem = inputItemDict(
    title="created",
    controlClass=vanilla.DatePicker,
    conversionFromUFO=openTypeHeadCreatedFromUFO,
    conversionToUFO=openTypeHeadCreatedToUFO,
)

openTypeHeadLowestRecPPEMItem = inputItemDict(
    title="lowestRecPPEM",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)

openTypeHeadFlagsOptions = [
    "0 Baseline for font at y=0",
    "1 Left sidebearing point at x=0",
    "2 Instructions may depend on point size",
    "3 Force ppem to integer values for all internal scaler math",
    "4 Instructions may alter advance width",
    "11 Font data is \"lossless\"",
    "12 Font converted (produce compatible metrics)",
    "13 Font optimized for ClearType",
]

openTypeHeadFlagsItem = inputItemDict(
    title="flags",
    controlClass=CheckList,
    controlOptions=dict(items=openTypeHeadFlagsOptions)
)

# OpenType name Table

openTypeNamePreferredFamilyNameItem = inputItemDict(
    title="Preferred Family Name"
)
openTypeNamePreferredSubfamilyNameItem = inputItemDict(
    title="Preferred Subfamily Name"
)
openTypeNameCompatibleFullNameItem = inputItemDict(
    title="Compatible Full Name"
)
openTypeNameWWSFamilyNameItem = inputItemDict(
    title="WWS Family Name"
)
openTypeNameWWSSubfamilyNameItem = inputItemDict(
    title="WWS Subfamily Name"
)
openTypeNameVersionItem = inputItemDict(
    title="Version"
)
openTypeNameUniqueIDItem = inputItemDict(
    title="Unique ID"
)
openTypeNameDescriptionItem = inputItemDict(
    title="Description",
    hasDefault=False,
    controlOptions=dict(lineCount=5)
)
openTypeNameSampleTextItem = inputItemDict(
    title="Sample Text",
    hasDefault=False,
    controlOptions=dict(lineCount=5)
)


class OpenTypeNameRecordDict(dict):

    def __init__(self, other=None):
        if other is None:
            other = dict()
        super(OpenTypeNameRecordDict, self).__init__(other)
        self._sortedKeys = None
        self._revesersedDict = None

    def __setitem__(self, key, value):
        # make immutable
        pass

    def update(self, other):
        # make immutable
        pass

    def sortedKeys(self):
        if self._sortedKeys is None:
            self._sortedKeys = [self[k] for k in sorted(self)]
        return self._sortedKeys

    def _get_reversed(self):
        if self._revesersedDict is None:
            self._revesersedDict = {v: k for k, v in self.items()}
        return self._revesersedDict

    reversed = property(_get_reversed)


class OpenTypeNameNameIDsRecordDict(OpenTypeNameRecordDict):

    def __getitem__(self, key):
        if key not in self:
            dict.__setitem__(self, key, "[%s]" % key)
        return dict.__getitem__(self, key)


# name recored data taken from https://www.microsoft.com/typography/otspec/name.htm

nameIDs = OpenTypeNameNameIDsRecordDict({
    0 : '[0] Copyright Notice',
    1 : '[1] Font Family Name',
    2 : '[2] Font Subfamily name',
    3 : '[3] Unique font identifier',
    4 : '[4] Full font name',
    5 : '[5] Version string',
    6 : '[6] PostScript name',
    7 : '[7] Trademark',
    8 : '[8] Manufacturer Name',
    9 : '[9] Designer',
    10 : '[10] Description',
    11 : '[11] URL Vendor',
    12 :  '[12] URL Designer',
    13 : '[13] License Description',
    14 : '[14] License Info URL',
    # 15 : '[15] Reserved',
    16 : '[16] Typographic Family name',
    17 : '[17] Typographic Subfamily name',
    18 : '[18] Compatible Full',
    19 : '[19] Sample text',
    20 : '[20] PostScript CID name',
    21 : '[21] WWS Family Name',
    22 : '[22] WWS Subfamily Name',
    # 23 : '[23] Light Background Palette',
    # 24 : '[24] Dark Background Palette',
    # 25 : '[25] Variations PostScript Name Prefix'
})


platformIDs = OpenTypeNameRecordDict({
    0 : "Unicode",
    1 : "Macintosh",
    2 : "ISO (deprecated)",
    3 : "Windows",
    # 4 : "Custom"
})


# platform unicode encoding
encodingIDsplatform0 = OpenTypeNameRecordDict({
    0 : "Unicode 1.0",
    1 : "Unicode 1.1",
    2 : "ISO/IEC 10646",
    3 : "BMP Unicode",
    4 : "Full Unicode",
    5 : "Unicode Variation Sequences",
    6 : "Unicode full",
})


# platform Macintosh encoding
encodingIDsplatform1 = OpenTypeNameRecordDict({
    0 : 'Roman',
    1 : 'Japanese',
    2 : 'Chinese',
    3 : 'Korean',
    4 : 'Arabic',
    5 : 'Hebrew',
    6 : 'Greek',
    7 : 'Russian',
    8 : 'RSymbol',
    9 : 'Devanagari',
    10 : 'Gurmukhi',
    11 : 'Gujarati',
    12 : 'Oriya',
    13 : 'Bengali',
    14 : 'Tamil',
    15 : 'Telugu',
    16 : 'Kannada',
    17 : 'Malayalam',
    18 : 'Sinhalese (Traditional)',
    19 : 'Burmese',
    20 : 'Khmer',
    21 : 'Thai',
    22 : 'Laotian',
    23 : 'Georgian',
    24 : 'Armenian',
    25 : 'Chinese (Simplified)',
    26 : 'Tibetan',
    27 : 'Mongolian',
    28 : 'Geez',
    29 : 'Slavic',
    30 : 'Vietnamese',
    31 : 'Sindhi',
    32 : 'Uninterpreted'
})


# platform iso encoding
encodingIDsplatform2 = OpenTypeNameRecordDict({
    0 : '7-bit ASCII  (deprecated)',
    1 : 'ISO 10646  (deprecated)',
    2 : 'ISO 8859-1  (deprecated)'
})


# platform windows encoding
encodingIDsplatform3 = OpenTypeNameRecordDict({
    0 : 'Symbol',
    1 : 'Unicode BMP (UCS-2)',
    2 : 'ShiftJIS',
    3 : 'PRC',
    4 : 'Big5',
    5 : 'Wansung',
    6 : 'Johab',
    # 7 : 'Reserved',
    # 8 : 'Reserved',
    # 9 : 'Reserved',
    10 : 'Unicode UCS-4',
})


# platform Macintosh language
languageIDsplatform1 = OpenTypeNameRecordDict({
   0: 'English',
   1: 'French',
   2: 'German',
   3: 'Italian',
   4: 'Dutch',
   5: 'Swedish',
   6: 'Spanish',
   7: 'Danish',
   8: 'Portuguese',
   9: 'Norwegian',
   10: 'Hebrew',
   11: 'Japanese',
   12: 'Arabic',
   13: 'Finnish',
   14: 'Armenian Inuktitut',
   15: 'Icelandic',
   16: 'Maltese',
   17: 'Turkish',
   18: 'Croatian',
   19: 'Chinese (Traditional)',
   20: 'Urdu',
   21: 'Hindi',
   22: 'Thai',
   23: 'Korean',
   24: 'Lithuanian',
   25: 'Polish',
   26: 'Hungarian',
   27: 'Estonian',
   28: 'Latvian',
   29: 'Sami',
   30: 'Faroese',
   31: 'Farsi/Persian',
   32: 'Russian',
   33: 'Chinese (Simplified)',
   34: 'Flemish',
   35: 'Irish Gaelic',
   36: 'Albanian',
   37: 'Romanian',
   38: 'Czech',
   39: 'Slovak',
   40: 'Slovenian',
   41: 'Yiddish',
   42: 'Serbian',
   43: 'Macedonian',
   44: 'Bulgarian',
   45: 'Ukrainian',
   46: 'Byelorussian',
   47: 'Uzbek',
   48: 'Kazakh',
   49: 'Azerbaijani (Cyrillic script)',
   50: 'Azerbaijani (Arabic script)',
   51: 'Armenian',
   52: 'Georgian',
   53: 'Moldavian',
   54: 'Kirghiz',
   55: 'Tajiki',
   56: 'Turkmen',
   57: 'Mongolian (Mongolian script)',
   58: 'Mongolian (Cyrillic script)',
   59: 'English Pashto',
   60: 'French Kurdish',
   61: 'German Kashmiri',
   62: 'Italian Sindhi',
   63: 'Dutch Tibetan',
   64: 'Swedish Nepali',
   65: 'Spanish Sanskrit',
   66: 'Danish Marathi',
   67: 'Portuguese Bengali',
   68: 'Norwegian Assamese',
   69: 'Hebrew Gujarati',
   70: 'Japanese Punjabi',
   71: 'Arabic Oriya',
   72: 'Finnish Malayalam',
   73: 'Greek Kannada',
   74: 'Icelandic Tamil',
   75: 'Maltese Telugu',
   76: 'Turkish Sinhalese',
   77: 'Croatian Burmese',
   78: 'Chinese (Traditional) Khmer',
   79: 'Urdu Lao',
   80: 'Hindi Vietnamese',
   81: 'Thai Indonesian',
   82: 'Korean Tagalong',
   83: 'Lithuanian Malay (Roman script)',
   84: 'Polish Malay (Arabic script)',
   85: 'Hungarian Amharic',
   86: 'Estonian Tigrinya',
   87: 'Latvian Galla',
   88: 'Sami Somali',
   89: 'Faroese Swahili',
   90: 'Farsi/Persian Kinyarwanda/Ruanda',
   91: 'Russian Rundi',
   92: 'Chinese (Simplified) Nyanja/Chewa',
   93: 'Flemish Malagasy',
   94: 'Irish Gaelic Esperanto',
   128: 'Albanian Welsh',
   129: 'Romanian Basque',
   130: 'Czech Catalan',
   131: 'Slovak Latin',
   132: 'Slovenian Quenchua',
   133: 'Yiddish Guarani',
   134: 'Serbian Aymara',
   135: 'Macedonian Tatar',
   136: 'Bulgarian Uighur',
   137: 'Ukrainian Dzongkha',
   138: 'Byelorussian Javanese (Roman script)',
   139: 'Uzbek Sundanese (Roman script)',
   140: 'Kazakh Galician',
   141: 'Azerbaijani (Cyrillic script) Afrikaans',
   142: 'Azerbaijani (Arabic script) Breton',
   144: 'Georgian Scottish Gaelic',
   145: 'Moldavian Manx Gaelic',
   146: 'Kirghiz Irish Gaelic (with dot above)',
   147: 'Tajiki Tongan',
   148: 'Turkmen Greek (polytonic)',
   149: 'Mongolian (Mongolian script) Greenlandic',
   150: 'Mongolian (Cyrillic script) Azerbaijani (Roman script)',
})


# platform Windows language
languageIDsplatform3 = OpenTypeNameRecordDict({
   1025: "Arabic (Saudi Arabia)",
   1026: "Bulgarian (Bulgaria)",
   1027: "Catalan (Catalan)",
   1028: "Chinese (Taiwan)",
   1029: "Czech (Czech Republic)",
   1030: "Danish (Denmark)",
   1031: "German (Germany)",
   1032: "Greek (Greece)",
   1033: "English (United States)",
   1034: "Spanish (Traditional Sort) (Spain)",
   1035: "Finnish (Finland)",
   1036: "French (France)",
   1037: "Hebrew (Israel)",
   1038: "Hungarian (Hungary)",
   1039: "Icelandic (Iceland)",
   1040: "Italian (Italy)",
   1041: "Japanese (Japan)",
   1042: "Korean (Korea)",
   1043: "Dutch (Netherlands)",
   1044: "Norwegian (Bokmal) (Norway)",
   1045: "Polish (Poland)",
   1046: "Portuguese (Brazil)",
   1047: "Romansh (Switzerland)",
   1048: "Romanian (Romania)",
   1049: "Russian (Russia)",
   1050: "Croatian (Croatia)",
   1051: "Slovak (Slovakia)",
   1052: "Albanian (Albania)",
   1053: "Swedish (Sweden)",
   1054: "Thai (Thailand)",
   1055: "Turkish (Turkey)",
   1056: "Urdu (Islamic Republic of Pakistan)",
   1057: "Indonesian (Indonesia)",
   1058: "Ukrainian (Ukraine)",
   1059: "Belarusian (Belarus)",
   1060: "Slovenian (Slovenia)",
   1061: "Estonian (Estonia)",
   1062: "Latvian (Latvia)",
   1063: "Lithuanian (Lithuania)",
   1064: "Tajik (Cyrillic) (Tajikistan)",
   1066: "Vietnamese (Vietnam)",
   1067: "Armenian (Armenia)",
   1068: "Azeri (Latin) (Azerbaijan)",
   1069: "Basque (Basque)",
   1070: "Upper Sorbian (Germany)",
   1071: "Macedonian (FYROM) (Former Yugoslav Republic of Macedonia)",
   1074: "Setswana (South Africa)",
   1076: "isiXhosa (South Africa)",
   1077: "isiZulu (South Africa)",
   1078: "Afrikaans (South Africa)",
   1079: "Georgian (Georgia)",
   1080: "Faroese (Faroe Islands)",
   1081: "Hindi (India)",
   1082: "Maltese (Malta)",
   1083: "Sami (Northern) (Norway)",
   1086: "Malay (Malaysia)",
   1087: "Kazakh (Kazakhstan)",
   1088: "Kyrgyz (Kyrgyzstan)",
   1089: "Kiswahili (Kenya)",
   1090: "Turkmen (Turkmenistan)",
   1091: "Uzbek (Latin) (Uzbekistan)",
   1092: "Tatar (Russia)",
   1093: "Bengali (India)",
   1094: "Punjabi (India)",
   1095: "Gujarati (India)",
   1096: "Odia (formerly Oriya) (India)",
   1097: "Tamil (India)",
   1098: "Telugu (India)",
   1099: "Kannada (India)",
   1100: "Malayalam (India)",
   1101: "Assamese (India)",
   1102: "Marathi (India)",
   1103: "Sanskrit (India)",
   1104: "Mongolian (Cyrillic) (Mongolia)",
   1105: "Tibetan (PRC)",
   1106: "Welsh (United Kingdom)",
   1107: "Khmer (Cambodia)",
   1108: "Lao (Lao P.D.R.)",
   1110: "Galician (Galician)",
   1111: "Konkani (India)",
   1114: "Syriac (Syria)",
   1115: "Sinhala (Sri Lanka)",
   1117: "Inuktitut (Canada)",
   1118: "Amharic (Ethiopia)",
   1121: "Nepali (Nepal)",
   1122: "Frisian (Netherlands)",
   1123: "Pashto (Afghanistan)",
   1124: "Filipino (Philippines)",
   1125: "Divehi (Maldives)",
   1128: "Hausa (Latin) (Nigeria)",
   1130: "Yoruba (Nigeria)",
   1131: "Quechua (Bolivia)",
   1132: "Sesotho sa Leboa (South Africa)",
   1133: "Bashkir (Russia)",
   1134: "Luxembourgish (Luxembourg)",
   1135: "Greenlandic (Greenland)",
   1136: "Igbo (Nigeria)",
   1144: "Yi (PRC)",
   1146: "Mapudungun (Chile)",
   1148: "Mohawk (Mohawk)",
   1150: "Breton (France)",
   1152: "Uighur (PRC)",
   1153: "Maori (New Zealand)",
   1154: "Occitan (France)",
   1155: "Corsican (France)",
   1156: "Alsatian (France)",
   1157: "Yakut (Russia)",
   1158: "K'iche (Guatemala)",
   1159: "Kinyarwanda (Rwanda)",
   1160: "Wolof (Senegal)",
   1164: "Dari (Afghanistan)",
   2049: "Arabic (Iraq)",
   2052: "Chinese (People's Republic of China)",
   2055: "German (Switzerland)",
   2057: "English (United Kingdom)",
   2058: "Spanish (Mexico)",
   2060: "French (Belgium)",
   2064: "Italian (Switzerland)",
   2067: "Dutch (Belgium)",
   2068: "Norwegian (Nynorsk) (Norway)",
   2070: "Portuguese (Portugal)",
   2074: "Serbian (Latin) (Serbia)",
   2077: "Sweden (Finland)",
   2092: "Azeri (Cyrillic) (Azerbaijan)",
   2094: "Lower Sorbian (Germany)",
   2107: "Sami (Northern) (Sweden)",
   2108: "Irish (Ireland)",
   2110: "Malay (Brunei Darussalam)",
   2115: "Uzbek (Cyrillic) (Uzbekistan)",
   2117: "Bengali (Bangladesh)",
   2128: "Mongolian (Traditional) (People's Republic of China)",
   2141: "Inuktitut (Latin) (Canada)",
   2143: "Tamazight (Latin) (Algeria)",
   2155: "Quechua (Ecuador)",
   3073: "Arabic (Egypt)",
   3076: "Chinese (Hong Kong S.A.R.)",
   3079: "German (Austria)",
   3081: "English (Australia)",
   3082: "Spanish (Modern Sort) (Spain)",
   3084: "French (Canada)",
   3098: "Serbian (Cyrillic) (Serbia)",
   3131: "Sami (Northern) (Finland)",
   3179: "Quechua (Peru)",
   4097: "Arabic (Libya)",
   4100: "Chinese (Singapore)",
   4103: "German (Luxembourg)",
   4105: "English (Canada)",
   4106: "Spanish (Guatemala)",
   4108: "French (Switzerland)",
   4122: "Croatian (Latin) (Bosnia and Herzegovina)",
   4155: "Sami (Lule) (Norway)",
   5121: "Arabic (Algeria)",
   5124: "Chinese (Macao S.A.R.)",
   5127: "German (Liechtenstein)",
   5129: "English (New Zealand)",
   5130: "Spanish (Costa Rica)",
   5132: "French (Luxembourg)",
   5146: "Bosnian (Latin) (Bosnia and Herzegovina)",
   5179: "Sami (Lule) (Sweden)",
   6145: "Arabic (Morocco)",
   6153: "English (Ireland)",
   6154: "Spanish (Panama)",
   6156: "French (Principality of Monaco)",
   6170: "Serbian (Latin) (Bosnia and Herzegovina)",
   6203: "Sami (Southern) (Norway)",
   7169: "Arabic (Tunisia)",
   7177: "English (South Africa)",
   7178: "Spanish (Dominican Republic)",
   7194: "Serbian (Cyrillic) (Bosnia and Herzegovina)",
   7227: "Sami (Southern) (Sweden)",
   8193: "Arabic (Oman)",
   8201: "English (Jamaica)",
   8202: "Spanish (Venezuela)",
   8218: "Bosnian (Cyrillic) (Bosnia and Herzegovina)",
   8251: "Sami (Skolt) (Finland)",
   9217: "Arabic (Yemen)",
   9225: "English (Caribbean)",
   9226: "Spanish (Colombia)",
   9275: "Sami (Inari) (Finland)",
   10241: "Arabic (Syria)",
   10249: "English (Belize)",
   10250: "Spanish (Peru)",
   11265: "Arabic (Jordan)",
   11273: "English (Trinidad and Tobago)",
   11274: "Spanish (Argentina)",
   12289: "Arabic (Lebanon)",
   12297: "English (Zimbabwe)",
   12298: "Spanish (Ecuador)",
   13313: "Arabic (Kuwait)",
   13321: "English (Republic of the Philippines)",
   13322: "Spanish (Chile)",
   14337: "Arabic (U.A.E.)",
   14346: "Spanish (Uruguay)",
   15361: "Arabic (Bahrain)",
   15370: "Spanish (Paraguay)",
   16385: "Arabic (Qatar)",
   16393: "English (India)",
   16394: "Spanish (Bolivia)",
   17417: "English (Malaysia)",
   17418: "Spanish (El Salvador)",
   18441: "English (Singapore)",
   18442: "Spanish (Honduras)",
   19466: "Spanish (Nicaragua)",
   20490: "Spanish (Puerto Rico)",
   21514: "Spanish (United States)"
})


platformEncodingIDsMap = {
    platformIDs[0]: encodingIDsplatform0,
    platformIDs[1]: encodingIDsplatform1,
    platformIDs[2]: encodingIDsplatform2,
    platformIDs[3]: encodingIDsplatform3,
}


platformLanguageIDsMap = {
    platformIDs[1]: languageIDsplatform1,
    platformIDs[3]: languageIDsplatform3,
}


identifierMap = {
    "encodingID": platformEncodingIDsMap,
    "languageID": platformLanguageIDsMap
}

openTypeNameRecordNotSetString = "-"

openTypeNameRecordtooltipTemplate = """name ID: %(nameID)s
platform ID: %(platformID)s
encoding ID: %(encodingID)s
language ID: %(languageID)s

%(string)s"""


class OpenTypeNameRecordTableView(DefconAppKitTableView):

    def tableView_toolTipForCell_rect_tableColumn_row_mouseLocation_(self, tableview, cell, rect, column, row, location):
        if row:
            item = tableview.dataSource().content()[row]
            if item["string"]:
                tooltip = openTypeNameRecordtooltipTemplate % item
                return tooltip, rect
        return None, rect

    def tableView_dataCellForTableColumn_row_(self, tableview, column, row):
        if column is None:
            return None
        cell = column.dataCell()
        if column.identifier() in identifierMap:
            item = tableview.dataSource().content()[row]
            data = identifierMap[column.identifier()]
            options = data.get(item["platformID"], OpenTypeNameRecordDict())
            options = options.sortedKeys()
            cell.removeAllItems()
            cell.addItemsWithTitles_(options)
            if item[column.identifier()] not in options:
                value = openTypeNameRecordNotSetString
                if options:
                    value = options[0]
                item[column.identifier()] = value
        return cell


class OpenTypeNameRecordList(InfoList):

    nsTableViewClass = OpenTypeNameRecordTableView

    def __init__(self, *args, **kwargs):
        self._superEditCallback = kwargs.get("editCallback")
        kwargs["editCallback"] = self.editCallback
        super(OpenTypeNameRecordList, self).__init__(*args, **kwargs)
        self._tableView.setDelegate_(self._tableView)

    def editCallback(self, sender):
        # reload specific cells on change...
        rowIndexes = self._tableView.selectedRowIndexes()
        columnIndexes = NSMutableIndexSet.alloc().init()
        for index, column in enumerate(self._tableView.tableColumns()):
            if column.identifier() in ("encodingID", "languageID"):
                columnIndexes.addIndex_(index)
        self._tableView.reloadDataForRowIndexes_columnIndexes_(rowIndexes, columnIndexes)
        if self._superEditCallback:
            self._superEditCallback(sender)


def openTypeNameRecordFromUFO(value):
    converted = dict(value)
    converted["nameID"] = nameIDs[value["nameID"]]
    converted["platformID"] = platformIDs[value["platformID"]]
    if converted["platformID"] in platformEncodingIDsMap:
        data = platformEncodingIDsMap[converted["platformID"]]
        converted["encodingID"] = data.get(value["encodingID"])
    else:
        converted["encodingID"] = ""
    if converted["platformID"] in platformLanguageIDsMap:
        data = platformLanguageIDsMap[converted["platformID"]]
        converted["languageID"] = data.get(value["languageID"])
    else:
        converted["languageID"] = ""
    return converted


def openTypeNameRecordsFromUFO(values):
    if values is None:
        return []
    items = []
    for value in values:
        item = openTypeNameRecordFromUFO(value)
        items.append(item)
    return items


def openTypeNameRecordsToUFO(value):
    records = {}
    sortKeys = ["nameID", "platformID", "encodingID", "languageID"]
    for item in value:
        record = dict(item)
        record["nameID"] = nameIDs.reversed[item["nameID"]]
        record["platformID"] = platformIDs.reversed[item["platformID"]]
        if record["encodingID"] == openTypeNameRecordNotSetString:
            record["encodingID"] = 0
        elif item["platformID"] in platformEncodingIDsMap:
            data = platformEncodingIDsMap[item["platformID"]]
            record["encodingID"] = data.reversed.get(item["encodingID"], 0)
        else:
            record["encodingID"] = 0

        if record["languageID"] == openTypeNameRecordNotSetString:
            record["languageID"] = 0
        elif item["platformID"] in platformLanguageIDsMap:
            data = platformLanguageIDsMap[item["platformID"]]
            record["languageID"] = data.reversed.get(item["languageID"], 0)
        else:
            record["languageID"] = 0

        key = tuple([record[k] for k in sortKeys])
        records[key] = record
    records = [value for key, value in sorted(records.items())]
    return records


openTypeNameRecordFormatter = NSNumberFormatter.alloc().init()
openTypeNameRecordFormatter.setPositiveFormat_("#")
openTypeNameRecordFormatter.setAllowsFloats_(False)
openTypeNameRecordFormatter.setGeneratesDecimalNumbers_(False)  # this seems to have no effect. NSNumberFormatter is awful.
openTypeNameRecordFormatter.setMinimum_(0)
openTypeNameRecordFormatter.setMaximum_(65535)

openTypeNameRecordsItem = inputItemDict(
    title="Name Records",
    hasDefault=False,
    controlClass=DictList,
    controlOptions=dict(
        listClass=OpenTypeNameRecordList,
        showColumnTitles=True,
        columnDescriptions=[
            dict(key="nameID", title="Name ID", width=130, editable=True, cell=vanilla.PopUpButtonListCell(nameIDs.sortedKeys()), binding="selectedValue"),
            dict(key="platformID", title="Platform ID", width=80, editable=True, cell=vanilla.PopUpButtonListCell(platformIDs.sortedKeys()), binding="selectedValue"),
            dict(key="encodingID", title="Encoding ID", width=60, editable=True, cell=vanilla.PopUpButtonListCell([]), binding="selectedValue"),
            dict(key="languageID", title="Language ID", width=60, editable=True, cell=vanilla.PopUpButtonListCell([]), binding="selectedValue"),
            dict(key="string", title="String", width=500, editable=True),
        ],
        itemPrototype=openTypeNameRecordFromUFO(dict(nameID=0, platformID=1, encodingID=0, languageID=0, string="")),
    ),
    conversionFromUFO=openTypeNameRecordsFromUFO,
    conversionToUFO=openTypeNameRecordsToUFO,
)


# OpenType hhea Table

openTypeHheaAscenderItem = inputItemDict(
    title="Ascender",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeHheaDescenderItem = inputItemDict(
    title="Descender",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False),
    conversionToUFO=noneToZero
)
openTypeHheaLineGapItem = inputItemDict(
    title="LineGap",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeHheaCaretSlopeRiseItem = inputItemDict(
    title="caretSlopeRise",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeHheaCaretSlopeRunItem = inputItemDict(
    title="caretSlopeRun",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeHheaCaretOffsetItem = inputItemDict(
    title="caretOffset",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)

# OpenType vhea Table

openTypeVheaVertTypoAscenderItem = inputItemDict(
    title="vertTypoAscender",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeVheaVertTypoDescenderItem = inputItemDict(
    title="vertTypoDescender",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeVheaVertTypoLineGapItem = inputItemDict(
    title="vertTypoLineGap",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeVheaCaretSlopeRiseItem = inputItemDict(
    title="caretSlopeRise",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeVheaCaretSlopeRunItem = inputItemDict(
    title="caretSlopeRun",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeVheaCaretOffsetItem = inputItemDict(
    title="caretOffset",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)

# OpenType OS/2 Table

openTypeOS2WeightClassItem = inputItemDict(
    title="usWeightClass",
    hasDefault=False,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)

openTypeOS2WidthClassOptions = [
    "None",
    "Ultra-condensed",
    "Extra-condensed",
    "Condensed",
    "Semi-condensed",
    "Medium (normal)",
    "Semi-expanded",
    "Expanded",
    "Extra-expanded",
    "Ultra-expanded"
]


def openTypeOS2WidthClassFromUFO(value):
    if value is None:
        return 0
    return value


def openTypeOS2WidthClassToUFO(value):
    if value == 0:
        return None
    return value


openTypeOS2WidthClassItem = inputItemDict(
    title="usWidthClass",
    hasDefault=False,
    controlClass=vanilla.PopUpButton,
    controlOptions=dict(items=openTypeOS2WidthClassOptions),
    conversionFromUFO=openTypeOS2WidthClassFromUFO,
    conversionToUFO=openTypeOS2WidthClassToUFO
)

openTypeOS2SelectionOptions = [
    "1 UNDERSCORE",
    "2 NEGATIVE",
    "3 OUTLINED",
    "4 STRIKEOUT",
    "7 USE_TYPO_METRICS",
    "8 WWS",
    "9 OBLIQUE",
]

openTypeOS2SelectionItem = inputItemDict(
    title="fsSelection",
    controlClass=CheckList,
    controlOptions=dict(items=openTypeOS2SelectionOptions)
)

openTypeOS2VendorIDItem = inputItemDict(
    title="achVendID",
    hasDefault=False,
)
openTypeOS2PanoseItem = inputItemDict(
    title="",
    hasDefault=False,
    controlClass=PanoseControl
)

openTypeOS2UnicodeRangesOptions = [
    "0 Basic Latin",
    "1 Latin-1 Supplement",
    "2 Latin Extended-A",
    "3 Latin Extended-B",
    "4 IPA Extensions",
    "5 Spacing Modifier Letters",
    "6 Combining Diacritical Marks",
    "7 Greek and Coptic",
    "8 Coptic",
    "9 Cyrillic",
    "10 Armenian",
    "11 Hebrew",
    "12 Vai",
    "13 Arabic",
    "14 ",
    "15 Devanagari",
    "16 Bengali",
    "17 Gurmukhi",
    "18 Gujarati",
    "19 Oriya",
    "20 Tamil",
    "21 Telugu",
    "22 Kannada",
    "23 Malayalam",
    "24 Thai",
    "25 Lao",
    "26 Georgian",
    "27 Balinese",
    "28 Hangul Jamo",
    "29 Latin Extended Additional",
    "30 Greek Extended",
    "31 General Punctuation",
    "32 Superscripts And Subscripts",
    "33 Currency Symbols",
    "34 Combining Diacritical Marks For Symbols",
    "35 Letterlike Symbols",
    "36 Number Forms",
    "37 Arrows",
    "38 Mathematical Operators",
    "39 Miscellaneous Technical",
    "40 Control Pictures",
    "41 Optical Character Recognition",
    "42 Enclosed Alphanumerics",
    "43 Box Drawing",
    "44 Block Elements",
    "45 Geometric Shapes",
    "46 Miscellaneous Symbols",
    "47 Dingbats",
    "48 CJK Symbols And Punctuation",
    "49 Hiragana",
    "50 Katakana",
    "51 Bopomofo",
    "52 Hangul Compatibility Jamo",
    "53 Phags-pa",
    "54 Enclosed CJK Letters And Months",
    "55 CJK Compatibility",
    "56 Hangul Syllables",
    "57 Non-Plane 0 *",
    "58 Phoenician",
    "59 CJK Unified Ideographs",
    "60 Private Use Area (plane 0)",
    "61 CJK Strokes",
    "62 Alphabetic Presentation Forms",
    "63 Arabic Presentation Forms-A",
    "64 Combining Half Marks",
    "65 Vertical Forms",
    "66 Small Form Variants",
    "67 Arabic Presentation Forms-B",
    "68 Halfwidth And Fullwidth Forms",
    "69 Specials",
    "70 Tibetan",
    "71 Syriac",
    "72 Thaana",
    "73 Sinhala",
    "74 Myanmar",
    "75 Ethiopic",
    "76 Cherokee",
    "77 Unified Canadian Aboriginal Syllabics",
    "78 Ogham",
    "79 Runic",
    "80 Khmer",
    "81 Mongolian",
    "82 Braille Patterns",
    "83 Yi Syllables",
    "84 Tagalog",
    "85 Old Italic",
    "86 Gothic",
    "87 Deseret",
    "88 Byzantine Musical Symbols",
    "89 Mathematical Alphanumeric Symbols",
    "90 Private Use (plane 15)",
    "91 Variation Selectors",
    "92 Tags",
    "93 Limbu",
    "94 Tai Le",
    "95 New Tai Lue",
    "96 Buginese",
    "97 Glagolitic",
    "98 Tifinagh",
    "99 Yijing Hexagram Symbols",
    "100 Syloti Nagri",
    "101 Linear B Syllabary",
    "102 Ancient Greek Numbers",
    "103 Ugaritic",
    "104 Old Persian",
    "105 Shavian",
    "106 Osmanya",
    "107 Cypriot Syllabary",
    "108 Kharoshthi",
    "109 Tai Xuan Jing Symbols",
    "110 Cuneiform",
    "111 Counting Rod Numerals",
    "112 Sundanese",
    "113 Lepcha",
    "114 Ol Chiki",
    "115 Saurashtra",
    "116 Kayah Li",
    "117 Rejang",
    "118 Cham",
    "119 Ancient Symbols",
    "120 Phaistos Disc",
    "121 Carian",
    "122 Domino Tiles",
]

openTypeOS2UnicodeRangesItem = inputItemDict(
    title="ulUnicodeRange",
    hasDefault=False,
    controlClass=CheckList,
    controlOptions=dict(items=openTypeOS2UnicodeRangesOptions),
)

openTypeOS2CodePageRangesOptions = [
    "0 1252 Latin 1",
    "1 1250 Latin 2: Eastern Europe",
    "2 1251 Cyrillic",
    "3 1253 Greek",
    "4 1254 Turkish",
    "5 1255 Hebrew",
    "6 1256 Arabic",
    "7 1257 Windows Baltic",
    "8 1258 Vietnamese",
    "16 874 Thai",
    "17 932 JIS/Japan",
    "18 936 Chinese: Simplified chars--PRC and Singapore",
    "19 949 Korean Wansung",
    "20 950 Chinese: Traditional chars--Taiwan and Hong Kong",
    "21 1361 Korean Johab",
    "29 Macintosh Character Set (US Roman)",
    "30 OEM Character Set",
    "31 Symbol Character Set",
    "48 869 IBM Greek",
    "49 866 MS-DOS Russian",
    "50 865 MS-DOS Nordic",
    "51 864 Arabic",
    "52 863 MS-DOS Canadian French",
    "53 862 Hebrew",
    "54 861 MS-DOS Icelandic",
    "55 860 MS-DOS Portuguese",
    "56 857 IBM Turkish",
    "57 855 IBM Cyrillic; primarily Russian",
    "58 852 Latin 2",
    "59 775 MS-DOS Baltic",
    "60 737 Greek; former 437 G",
    "61 708 Arabic; ASMO 708",
    "62 850 WE/Latin 1",
    "63 437 US",
]

openTypeOS2CodePageRangesItem = inputItemDict(
    title="ulCodePageRange",
    hasDefault=False,
    controlClass=CheckList,
    controlOptions=dict(items=openTypeOS2CodePageRangesOptions),
)

openTypeOS2TypoAscenderItem = inputItemDict(
    title="sTypoAscender",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2TypoDescenderItem = inputItemDict(
    title="sTypoDescender",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False),
    conversionToUFO=noneToZero
)
openTypeOS2TypoLineGapItem = inputItemDict(
    title="sTypoLineGap",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2WinAscentItem = inputItemDict(
    title="usWinAscent",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)
openTypeOS2WinDescentItem = inputItemDict(
    title="usWinDescent",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)
openTypeOS2TypeItem = inputItemDict(
    title="fsType",
    controlClass=EmbeddingControl,
    hasDefault=False
)
openTypeOS2SubscriptXSizeItem = inputItemDict(
    title="ySubscriptXSize",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SubscriptYSizeItem = inputItemDict(
    title="ySubscriptYSize",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SubscriptXOffsetItem = inputItemDict(
    title="ySubscriptXOffset",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SubscriptYOffsetItem = inputItemDict(
    title="ySubscriptYOffset",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SuperscriptXSizeItem = inputItemDict(
    title="ySuperscriptXSize",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SuperscriptYSizeItem = inputItemDict(
    title="ySuperscriptYSize",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SuperscriptXOffsetItem = inputItemDict(
    title="ySuperscriptXOffset",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2SuperscriptYOffsetItem = inputItemDict(
    title="ySuperscriptYOffset",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2StrikeoutSizeItem = inputItemDict(
    title="yStrikeoutSize",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)
openTypeOS2StrikeoutPositionItem = inputItemDict(
    title="yStrikeoutPosition",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False)
)

# Postscript Identification

postscriptFontNameItem = inputItemDict(
    title="FontName"
)
postscriptFullNameItem = inputItemDict(
    title="FullName"
)
postscriptWeightNameItem = inputItemDict(
    title="WeightName"
)
postscriptUniqueIDItem = inputItemDict(
    title="Unique ID Number",
    controlClass=NumberEditText,
    controlOptions=dict(style="idNumber", allowFloat=False, allowNegative=False)
)


# Postscript Hinting

def _postscriptBluesToUFO(string, maxCount):
    if not string:
        return []
    try:
        values = []
        for i in string.split(" "):
            if i:
                i = float(i)
                if i.is_integer():
                    i = int(i)
                values.append(i)
    except ValueError:
        values = []
    values = sorted(values)
    if len(values) % 2:
        values.pop()
    if len(values) > maxCount:
        values = values[:maxCount]
    return values


def postscriptBluesToUFO(string):
    return _postscriptBluesToUFO(string, 14)


def postscriptOtherBluesToUFO(string):
    return _postscriptBluesToUFO(string, 10)


def postscriptStemSnapToUFO(string):
    if not string:
        return []
    try:
        values = [int(i) for i in string.split(" ") if i]
    except ValueError:
        values = []
    if len(values) >= 12:
        values = values[:12]
    return values


def infoListFromUFO(value):
    if value is None:
        return ""
    value = [str(i) for i in value]
    return " ".join(value)


postscriptBlueValuesItem = inputItemDict(
    title="BlueValues",
    hasDefault=False,
    controlOptions=dict(formatter=NumberSequenceFormatter.alloc().initWithMaxValuesCount_requiresEvenCount_(14, True)),
    conversionFromUFO=infoListFromUFO,
    conversionToUFO=postscriptBluesToUFO,
)
postscriptOtherBluesItem = inputItemDict(
    title="OtherBlues",
    hasDefault=False,
    controlOptions=dict(formatter=NumberSequenceFormatter.alloc().initWithMaxValuesCount_requiresEvenCount_(10, True)),
    conversionFromUFO=infoListFromUFO,
    conversionToUFO=postscriptOtherBluesToUFO,
)
postscriptFamilyBluesItem = inputItemDict(
    title="FamilyBlues",
    hasDefault=False,
    controlOptions=dict(formatter=NumberSequenceFormatter.alloc().initWithMaxValuesCount_requiresEvenCount_(14, True)),
    conversionFromUFO=infoListFromUFO,
    conversionToUFO=postscriptBluesToUFO,
)
postscriptFamilyOtherBluesItem = inputItemDict(
    title="FamilyOtherBlues",
    hasDefault=False,
    controlOptions=dict(formatter=NumberSequenceFormatter.alloc().initWithMaxValuesCount_requiresEvenCount_(10, True)),
    conversionFromUFO=infoListFromUFO,
    conversionToUFO=postscriptOtherBluesToUFO,
)
postscriptStemSnapHItem = inputItemDict(
    title="StemSnapH",
    hasDefault=False,
    controlOptions=dict(formatter=NumberSequenceFormatter.alloc().initWithMaxValuesCount_requiresEvenCount_(12, False)),
    conversionFromUFO=infoListFromUFO,
    conversionToUFO=postscriptStemSnapToUFO,
)
postscriptStemSnapVItem = inputItemDict(
    title="StemSnapV",
    hasDefault=False,
    controlOptions=dict(formatter=NumberSequenceFormatter.alloc().initWithMaxValuesCount_requiresEvenCount_(12, False)),
    conversionFromUFO=infoListFromUFO,
    conversionToUFO=postscriptStemSnapToUFO,
)
postscriptBlueFuzzItem = inputItemDict(
    title="BlueFuzz",
    controlClass=NumberEditText,
    controlOptions=dict(style="number")
)
postscriptBlueShiftItem = inputItemDict(
    title="BlueShift",
    controlClass=NumberEditText,
    controlOptions=dict(style="number")
)
postscriptBlueScaleItem = inputItemDict(
    title="BlueScale",
    controlClass=NumberEditText,
    controlOptions=dict(style="number", decimals=10)
)
postscriptForceBoldItem = inputItemDict(
    title="ForceBold",
    controlClass=InfoCheckbox
)

# Postscript Dimensions

postscriptSlantAngleItem = inputItemDict(
    title="SlantAngle",
    controlClass=NumberEditText,
    controlOptions=dict(style="number")
)
postscriptUnderlineThicknessItem = inputItemDict(
    title="UnderlineThickness",
    controlClass=NumberEditText,
    controlOptions=dict(style="number"),
    hasDefault=True
)
postscriptUnderlinePositionItem = inputItemDict(
    title="UnderlinePosition",
    controlClass=NumberEditText,
    controlOptions=dict(style="number"),
    hasDefault=True
)
postscriptIsFixedPitchItem = inputItemDict(
    title="isFixedPitched",
    controlClass=InfoCheckbox
)
postscriptDefaultWidthXItem = inputItemDict(
    title="DefaultWidthX",
    controlClass=NumberEditText,
    controlOptions=dict(style="number"),
    hasDefault=True
)
postscriptNominalWidthXItem = inputItemDict(
    title="NominalWidthX",
    controlClass=NumberEditText,
    controlOptions=dict(style="number"),
    hasDefault=True
)

# Postscript Characters

postscriptDefaultCharacterItem = inputItemDict(
    title="Default Character"
)

postscriptWindowsCharacterSetOptions = [
    "Western CP 1252 /ANSI",
    "Unknown",
    "Symbol",
    "Macintosh Mac Roman",
    "Japanese Shift JIS",
    "Korean EUC-KR or Unified Hangul Code",
    "Korean Hangeul (Johab)",
    "Simplified Chinese GB2312 (EUC-CN / GBK)",
    "Chinese BIG5",
    "Greek CP 1253",
    "Turkish (Latin 5) CP 1254",
    "Vietnamese CP 1258",
    "Hebrew CP 1255",
    "Arabic CP 1256",
    "Baltic CP 1257",
    "Bitstream font Set",
    "Cyrillic CP 1251",
    "Thai",
    "Central European CP 1250",
    "OEM / DOS"
]


def postscriptWindowsCharacterSetFromUFO(value):
    return value - 1


def postscriptWindowsCharacterSetToUFO(value):
    return value + 1


postscriptWindowsCharacterSetItem = inputItemDict(
    title="Microsoft Character Set",
    controlClass=vanilla.PopUpButton,
    controlOptions=dict(items=postscriptWindowsCharacterSetOptions),
    conversionFromUFO=postscriptWindowsCharacterSetFromUFO,
    conversionToUFO=postscriptWindowsCharacterSetToUFO
)

# WOFF Identification

woffMajorVersionItem = inputItemDict(
    title="Major Version",
    hasDefault=True,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)
woffMinorVersionItem = inputItemDict(
    title="Minor Version",
    hasDefault=True,
    controlClass=NumberEditText,
    controlOptions=dict(style="number", allowFloat=False, allowNegative=False)
)


def woffMetadataUniqueIDFromUFO(value):
    if value is None:
        return None
    return value["id"]


def woffMetadataUniqueIDToUFO(value):
    if not value:
        return None
    return dict(id=value)


woffMetadataUniqueIDItem = inputItemDict(
    title="Unique ID",
    hasDefault=False,
    conversionFromUFO=woffMetadataUniqueIDFromUFO,
    conversionToUFO=woffMetadataUniqueIDToUFO,
)

# WOFF Vendor

woffMetadataVendorNameItem = inputItemDict(
    title="Name",
    hasDefault=False
)

woffMetadataVendorURLItem = inputItemDict(
    title="URL",
    hasDefault=False
)

woffWritingDirectionToIndex = {
    None: 0,
    "ltr": 1,
    "rtl": 2
}

indexToWoffWritingDirection = {
    0: None,
    1: "ltr",
    2: "rtl"
}


def woffMetadataDirectionFromUFO(value):
    return woffWritingDirectionToIndex[value]


def woffMetadataDirectionToUFO(value):
    return indexToWoffWritingDirection[value]


woffMetadataVendorDirectionItem = inputItemDict(
    title="Dir",
    hasDefault=False,
    controlClass=vanilla.PopUpButton,
    controlOptions=dict(items=["Default", "Left to Right", "Right to Left"]),
    conversionFromUFO=woffMetadataDirectionFromUFO,
    conversionToUFO=woffMetadataDirectionToUFO,
)

woffMetadataVendorClassItem = inputItemDict(
    title="Class",
    hasDefault=False
)

# WOFF Credits

def woffMetadataCreditsFromUFO(value):
    if value is None:
        return []
    items = []
    for item in value:
        item = dict(item)
        item["name"] = item.get("name", "")
        item["role"] = item.get("role", "")
        item["url"] = item.get("url", "")
        item["class"] = item.get("class", "")
        item["dir"] = item.get("dir", "Default")
        items.append(item)
    return items


def woffMetadataCreditsToUFO(value):
    items = []
    for item in value:
        item = dict(item)
        direction = item.get("dir")
        if direction == "Default":
            item["dir"] = None
        for key, value in list(item.items()):
            if value is None or value == "":
                del item[key]
        if item:
            items.append(item)
    if not items:
        return None
    return items


woffMetadataCreditsItem = inputItemDict(
    title="",
    hasDefault=False,
    controlClass=DictList,
    controlOptions=dict(
        columnDescriptions=[
            dict(title="Name", key="name", editable=True),
            dict(title="Role", key="role", editable=True),
            dict(title="URL", key="url", editable=True),
            dict(title="Dir", key="dir", editable=True, cell=vanilla.PopUpButtonListCell(["Default", "ltr", "rtl"]), binding="selectedValue"),
            dict(title="Class", key="class", editable=True),
        ],
        itemPrototype={"name": "Name", "role": "Role", "url": "http://url.com", "dir": "Default", "class": ""}
    ),
    conversionFromUFO=woffMetadataCreditsFromUFO,
    conversionToUFO=woffMetadataCreditsToUFO,
)


# WOFF Generic Text

def woffMetadataGenericTextFromUFO(value):
    if value is None:
        return []
    items = []
    for item in value:
        item = dict(item)
        item["text"] = item.get("text", "")
        item["language"] = item.get("language", "")
        item["class"] = item.get("class", "")
        item["dir"] = item.get("dir", "Default")
        items.append(item)
    return items


def woffMetadataGenericTextToUFO(value):
    items = []
    for item in value:
        item = dict(item)
        direction = item.get("dir")
        if direction == "Default":
            item["dir"] = None
        for key, value in list(item.items()):
            if value is None or value == "":
                del item[key]
        if item:
            items.append(item)
    if not items:
        return None
    return items


def woffMetadataGenericTextItemFactory(title=""):
    item = inputItemDict(
        title=title,
        hasDefault=False,
        controlClass=DictList,
        controlOptions=dict(
            columnDescriptions=[
                dict(title="Text", key="text", editable=True),
                dict(title="Language", key="language", editable=True),
                dict(title="Dir", key="dir", editable=True, cell=vanilla.PopUpButtonListCell(["Default", "ltr", "rtl"]), binding="selectedValue"),
                dict(title="Class", key="class", editable=True)
            ],
            itemPrototype={"text": "Text", "language": "", "dir": "Default", "class": ""},
            variableRowHeights=True
        ),
        conversionFromUFO=woffMetadataGenericTextFromUFO,
        conversionToUFO=woffMetadataGenericTextToUFO,
    )
    return item


# WOFF Description

woffMetadataDescriptionURLItem = inputItemDict(
    title="URL",
    hasDefault=False
)

woffMetadataDescriptionTextItem = woffMetadataGenericTextItemFactory("Text")

# WOFF Legal

woffMetadataCopyrightTextItem = woffMetadataGenericTextItemFactory("Copyright Text")

woffMetadataTrademarkTextItem = woffMetadataGenericTextItemFactory("Trademark Text")

woffMetadataLicenseURLItem = inputItemDict(
    title="License URL",
    hasDefault=False
)

woffMetadataLicenseIDItem = inputItemDict(
    title="License ID",
    hasDefault=False
)

woffMetadataLicenseTextItem = woffMetadataGenericTextItemFactory("License Text")

woffMetadataLicenseeNameItem = inputItemDict(
    title="Licensee Name",
    hasDefault=False
)

woffMetadataLicenseeDirectionItem = inputItemDict(
    title="Licensee Dir",
    hasDefault=False,
    controlClass=vanilla.PopUpButton,
    controlOptions=dict(items=["Default", "Left to Right", "Right to Left"]),
    conversionFromUFO=woffMetadataDirectionFromUFO,
    conversionToUFO=woffMetadataDirectionToUFO,
)

woffMetadataLicenseeClassItem = inputItemDict(
    title="Licensee Class",
    hasDefault=False
)


# Miscellaneous

macintoshFONDNameItem = inputItemDict(
    title="Font Name"
)
macintoshFONDFamilyIDItem = inputItemDict(
    title="Family ID Number",
    controlClass=NumberEditText,
    controlOptions=dict(style="idNumber", allowFloat=False, allowNegative=False)
)

# -----------------------------------------------------------------------
# Interface Groups
# These define the grouping and subgrouping of controls in the interface.
# -----------------------------------------------------------------------

allControlDescriptions = {
    "familyName": familyNameItem,
    "styleName": styleNameItem,
    "styleMapFamilyName": styleMapFamilyNameItem,
    "styleMapStyleName": styleMapStyleNameItem,
    "versionMajor": versionMajorItem,
    "versionMinor": versionMinorItem,

    "unitsPerEm": unitsPerEmItem,
    "descender": descenderItem,
    "xHeight": xHeightItem,
    "capHeight": capHeightItem,
    "ascender": ascenderItem,
    "italicAngle": italicAngleItem,

    "copyright": copyrightItem,
    "trademark": trademarkItem,
    "openTypeNameLicense": openTypeNameLicenseItem,
    "openTypeNameLicenseURL": openTypeNameLicenseURLItem,

    "openTypeNameDesigner": openTypeNameDesignerItem,
    "openTypeNameDesignerURL": openTypeNameDesignerURLItem,
    "openTypeNameManufacturer": openTypeNameManufacturerItem,
    "openTypeNameManufacturerURL": openTypeNameManufacturerURLItem,

    "note": noteItem,

    "openTypeGaspRangeRecords": openTypeGaspRangeRecordsItem,

    "openTypeHeadCreated": openTypeHeadCreatedItem,
    "openTypeHeadLowestRecPPEM": openTypeHeadLowestRecPPEMItem,
    "openTypeHeadFlags": openTypeHeadFlagsItem,

    "openTypeNamePreferredFamilyName": openTypeNamePreferredFamilyNameItem,
    "openTypeNamePreferredSubfamilyName": openTypeNamePreferredSubfamilyNameItem,
    "openTypeNameCompatibleFullName": openTypeNameCompatibleFullNameItem,
    "openTypeNameWWSFamilyName": openTypeNameWWSFamilyNameItem,
    "openTypeNameWWSSubfamilyName": openTypeNameWWSSubfamilyNameItem,
    "openTypeNameVersion": openTypeNameVersionItem,
    "openTypeNameUniqueID": openTypeNameUniqueIDItem,
    "openTypeNameDescription": openTypeNameDescriptionItem,
    "openTypeNameSampleText": openTypeNameSampleTextItem,
    "openTypeNameRecords": openTypeNameRecordsItem,

    "openTypeHheaAscender": openTypeHheaAscenderItem,
    "openTypeHheaDescender": openTypeHheaDescenderItem,
    "openTypeHheaLineGap": openTypeHheaLineGapItem,
    "openTypeHheaCaretSlopeRise": openTypeHheaCaretSlopeRiseItem,
    "openTypeHheaCaretSlopeRun": openTypeHheaCaretSlopeRunItem,
    "openTypeHheaCaretOffset": openTypeHheaCaretOffsetItem,

    "openTypeVheaVertTypoAscender": openTypeVheaVertTypoAscenderItem,
    "openTypeVheaVertTypoDescender": openTypeVheaVertTypoDescenderItem,
    "openTypeVheaVertTypoLineGap": openTypeVheaVertTypoLineGapItem,
    "openTypeVheaCaretSlopeRise": openTypeVheaCaretSlopeRiseItem,
    "openTypeVheaCaretSlopeRun": openTypeVheaCaretSlopeRunItem,
    "openTypeVheaCaretOffset": openTypeVheaCaretOffsetItem,

    "openTypeOS2WidthClass": openTypeOS2WidthClassItem,
    "openTypeOS2WeightClass": openTypeOS2WeightClassItem,
    "openTypeOS2Selection": openTypeOS2SelectionItem,
    "openTypeOS2VendorID": openTypeOS2VendorIDItem,
    "openTypeOS2Panose": openTypeOS2PanoseItem,
    "openTypeOS2UnicodeRanges": openTypeOS2UnicodeRangesItem,
    "openTypeOS2CodePageRanges": openTypeOS2CodePageRangesItem,
    "openTypeOS2TypoAscender": openTypeOS2TypoAscenderItem,
    "openTypeOS2TypoDescender": openTypeOS2TypoDescenderItem,
    "openTypeOS2TypoLineGap": openTypeOS2TypoLineGapItem,
    "openTypeOS2WinAscent": openTypeOS2WinAscentItem,
    "openTypeOS2WinDescent": openTypeOS2WinDescentItem,
    "openTypeOS2Type": openTypeOS2TypeItem,
    "openTypeOS2SubscriptXSize": openTypeOS2SubscriptXSizeItem,
    "openTypeOS2SubscriptYSize": openTypeOS2SubscriptYSizeItem,
    "openTypeOS2SubscriptXOffset": openTypeOS2SubscriptXOffsetItem,
    "openTypeOS2SubscriptYOffset": openTypeOS2SubscriptYOffsetItem,
    "openTypeOS2SuperscriptXSize": openTypeOS2SuperscriptXSizeItem,
    "openTypeOS2SuperscriptYSize": openTypeOS2SuperscriptYSizeItem,
    "openTypeOS2SuperscriptXOffset": openTypeOS2SuperscriptXOffsetItem,
    "openTypeOS2SuperscriptYOffset": openTypeOS2SuperscriptYOffsetItem,
    "openTypeOS2StrikeoutSize": openTypeOS2StrikeoutSizeItem,
    "openTypeOS2StrikeoutPosition": openTypeOS2StrikeoutPositionItem,

    "postscriptFontName": postscriptFontNameItem,
    "postscriptFullName": postscriptFullNameItem,
    "postscriptWeightName": postscriptWeightNameItem,
    "postscriptUniqueID": postscriptUniqueIDItem,

    "postscriptBlueValues": postscriptBlueValuesItem,
    "postscriptOtherBlues": postscriptOtherBluesItem,
    "postscriptFamilyBlues": postscriptFamilyBluesItem,
    "postscriptFamilyOtherBlues": postscriptFamilyOtherBluesItem,
    "postscriptStemSnapH": postscriptStemSnapHItem,
    "postscriptStemSnapV": postscriptStemSnapVItem,
    "postscriptBlueFuzz": postscriptBlueFuzzItem,
    "postscriptBlueShift": postscriptBlueShiftItem,
    "postscriptBlueScale": postscriptBlueScaleItem,
    "postscriptForceBold": postscriptForceBoldItem,

    "postscriptSlantAngle": postscriptSlantAngleItem,
    "postscriptUnderlineThickness": postscriptUnderlineThicknessItem,
    "postscriptUnderlinePosition": postscriptUnderlinePositionItem,
    "postscriptIsFixedPitch": postscriptIsFixedPitchItem,
    "postscriptDefaultWidthX": postscriptDefaultWidthXItem,
    "postscriptNominalWidthX": postscriptNominalWidthXItem,

    "postscriptDefaultCharacter": postscriptDefaultCharacterItem,
    "postscriptWindowsCharacterSet": postscriptWindowsCharacterSetItem,

    "woffMajorVersion": woffMajorVersionItem,
    "woffMinorVersion": woffMinorVersionItem,
    "woffMetadataUniqueID": woffMetadataUniqueIDItem,

    "woffMetadataVendor{name": woffMetadataVendorNameItem,
    "woffMetadataVendor{url": woffMetadataVendorURLItem,
    "woffMetadataVendor{dir": woffMetadataVendorDirectionItem,
    "woffMetadataVendor{class": woffMetadataVendorClassItem,

    "woffMetadataCredits{credits": woffMetadataCreditsItem,

    "woffMetadataDescription{url": woffMetadataDescriptionURLItem,
    "woffMetadataDescription{text": woffMetadataDescriptionTextItem,

    "woffMetadataCopyright{text": woffMetadataCopyrightTextItem,
    "woffMetadataTrademark{text": woffMetadataTrademarkTextItem,
    "woffMetadataLicense{url": woffMetadataLicenseURLItem,
    "woffMetadataLicense{id": woffMetadataLicenseIDItem,
    "woffMetadataLicense{text": woffMetadataLicenseTextItem,
    "woffMetadataLicensee{name": woffMetadataLicenseeNameItem,
    "woffMetadataLicensee{dir": woffMetadataLicenseeDirectionItem,
    "woffMetadataLicensee{class": woffMetadataLicenseeClassItem,

    "macintoshFONDName": macintoshFONDNameItem,
    "macintoshFONDFamilyID": macintoshFONDFamilyIDItem
}

controlOrganization = [
    dict(
        title="General",
        customView=None,
        groups=[
            ("Identification",
                "familyName",
                "styleName",
                "styleMapFamilyName",
                "styleMapStyleName",
                "versionMajor",
                "versionMinor"
            ),
            ("Dimensions",
                "unitsPerEm",
                "descender",
                "xHeight",
                "capHeight",
                "ascender",
                "italicAngle"
            ),
            ("Legal",
                "copyright",
                "trademark",
                "openTypeNameLicense",
                "openTypeNameLicenseURL"
            ),
            ("Parties",
                "openTypeNameDesigner",
                "openTypeNameDesignerURL",
                "openTypeNameManufacturer",
                "openTypeNameManufacturerURL"
            ),
            ("Note", "note")
        ]
    ),
    dict(
        title="OpenType",
        customView=None,
        groups=[
            ("gasp Table",
                "openTypeGaspRangeRecords"
            ),
            ("head Table",
                "openTypeHeadCreated",
                "openTypeHeadLowestRecPPEM",
                "openTypeHeadFlags"
            ),
            ("name Table",
                "openTypeNamePreferredFamilyName",
                "openTypeNamePreferredSubfamilyName",
                "openTypeNameCompatibleFullName",
                "openTypeNameWWSFamilyName",
                "openTypeNameWWSSubfamilyName",
                "openTypeNameVersion",
                "openTypeNameUniqueID",
                "openTypeNameDescription",
                "openTypeNameSampleText",
                "openTypeNameRecords"
            ),
            ("hhea Table",
                "openTypeHheaAscender",
                "openTypeHheaDescender",
                "openTypeHheaLineGap",
                "openTypeHheaCaretSlopeRise",
                "openTypeHheaCaretSlopeRun",
                "openTypeHheaCaretOffset"
            ),
            ("vhea Table",
                "openTypeVheaVertTypoAscender",
                "openTypeVheaVertTypoDescender",
                "openTypeVheaVertTypoLineGap",
                "openTypeVheaCaretSlopeRise",
                "openTypeVheaCaretSlopeRun",
                "openTypeVheaCaretOffset"
            ),
            ("OS/2 Table",
                "openTypeOS2WidthClass",
                "openTypeOS2WeightClass",
                "openTypeOS2Selection",
                "openTypeOS2VendorID",
                "openTypeOS2Type",
                "openTypeOS2UnicodeRanges",
                "openTypeOS2CodePageRanges",
                "openTypeOS2TypoAscender",
                "openTypeOS2TypoDescender",
                "openTypeOS2TypoLineGap",
                "openTypeOS2WinAscent",
                "openTypeOS2WinDescent",
                "openTypeOS2SubscriptXSize",
                "openTypeOS2SubscriptYSize",
                "openTypeOS2SubscriptXOffset",
                "openTypeOS2SubscriptYOffset",
                "openTypeOS2SuperscriptXSize",
                "openTypeOS2SuperscriptYSize",
                "openTypeOS2SuperscriptXOffset",
                "openTypeOS2SuperscriptYOffset",
                "openTypeOS2StrikeoutSize",
                "openTypeOS2StrikeoutPosition",
                "openTypeOS2Panose"
            )
        ]
    ),
    dict(
        title="Postscript",
        customView=None,
        groups=[
            ("Identification",
                "postscriptFontName",
                "postscriptFullName",
                "postscriptWeightName",
                "postscriptUniqueID"
            ),
            ("Hinting",
                "postscriptBlueValues",
                "postscriptOtherBlues",
                "postscriptFamilyBlues",
                "postscriptFamilyOtherBlues",
                "postscriptStemSnapH",
                "postscriptStemSnapV",
                "postscriptBlueFuzz",
                "postscriptBlueShift",
                "postscriptBlueScale",
                "postscriptForceBold"
            ),
            ("Dimensions",
                "postscriptSlantAngle",
                "postscriptUnderlineThickness",
                "postscriptUnderlinePosition",
                "postscriptIsFixedPitch",
                "postscriptDefaultWidthX",
                "postscriptNominalWidthX"
            ),
            ("Characters",
                "postscriptDefaultCharacter",
                "postscriptWindowsCharacterSet"
            )
        ]
    ),
    dict(
        title="WOFF",
        customView=None,
        groups=[
            ("Identification",
                "woffMajorVersion",
                "woffMinorVersion",
                "woffMetadataUniqueID"
            ),
            ("Vendor",
                "woffMetadataVendor{name",
                "woffMetadataVendor{url",
                "woffMetadataVendor{dir",
                "woffMetadataVendor{class"
            ),
            ("Credits",
                "woffMetadataCredits{credits"
            ),
            ("Description",
                "woffMetadataDescription{url",
                "woffMetadataDescription{text"
            ),
            ("Legal",
                "woffMetadataCopyright{text",
                "woffMetadataTrademark{text",
                "woffMetadataLicense{url",
                "woffMetadataLicense{id",
                "woffMetadataLicense{text",
                "woffMetadataLicensee{name",
                "woffMetadataLicensee{dir",
                "woffMetadataLicensee{class",
            )
        ]
    ),
    dict(
        title="Miscellaneous",
        customView=None,
        groups=[
            ("FOND Data",
                "macintoshFONDName",
                "macintoshFONDFamilyID"
            )
        ]
    ),
]


controlRequiredPrototypes = {
    "woffMetadataDescription": {"text": [{'text': 'Text'}]},
    "woffMetadataVendor": {"name": ""},
    "woffMetadataLicensee": {"name": ""},
}


# Attribute Getting and Setting

def getAttributeValue(info, attr):
    if "{" not in attr:
        return getattr(info, attr)
    keys = attr.split("{")
    attr = keys[0]
    keys = keys[1:]
    d = getattr(info, attr, {})
    if d is None:
        d = {}
    for key in keys[:-1]:
        if key not in d:
            return None
        d = d[key]
    return d.get(keys[-1])


def setAttributeValue(info, attr, value):
    if value == "":
        value = None
    if "{" not in attr:
        setattr(info, attr, value)
        return
    keys = attr.split("{")
    attr = keys[0]
    keys = keys[1:]
    d = getattr(info, attr)
    if d is None:
        d = deepcopy(controlRequiredPrototypes.get(attr, {}))
    for key in keys[:-1]:
        if key not in d:
            d[key] = {}
        d = d[key]
    key = keys[-1]
    if value is None:
        if key in d:
            del d[key]
    else:
        d[key] = value
    setattr(info, attr, d)


# Toolbar

toolbarColor1 = NSColor.underPageBackgroundColor()
toolbarColor2 = NSColor.windowBackgroundColor()
toolbarColor3 = NSColor.tertiaryLabelColor()
toolbarColorFallback = NSColor.colorWithCalibratedWhite_alpha_(0, .25)


class DefconAppKitFontInfoToolbarView(NSView):

    def drawRect_(self, rect):
        bounds = self.bounds()
        bounds = NSInsetRect(bounds, .5, .5)
        # fill
        fillPath = roundedRectBezierPath(bounds, 5, roundLowerLeft=False, roundLowerRight=False)
        # 10.5+
        try:
            gradient = NSGradient.alloc().initWithColors_([toolbarColor1, toolbarColor2])
            gradient.drawInBezierPath_angle_(fillPath, 90)
        except NameError:
            toolbarColorFallback.set()
            fillPath.fill()
        # stroke
        strokePath = roundedRectBezierPath(bounds, 5, roundLowerLeft=False, roundLowerRight=False, closeBottom=False)
        strokePath.setLineWidth_(1)
        toolbarColor3.set()
        strokePath.stroke()


class FontInfoToolbar(vanilla.Group):

    nsViewClass = DefconAppKitFontInfoToolbarView
    nsButtonType = NSOnOffButton


class FontInfoToolbarButton(vanilla.Button):

    nsBezelStyle = NSRoundRectBezelStyle
    frameAdjustments = {
        "mini": (0, 0, 0, 0),
        "small": (0, 0, 0, 0),
        "regular": (0, 0, 0, 0),
    }


class DefconAppKitFontInfoSegmentedCell(NSSegmentedCell):

    def drawWithFrame_inView_(self, frame, view):
        NSColor.windowBackgroundColor().set()
        backgroundRect = NSInsetRect(frame, 3, 5)
        backgroundRectFillPath = roundedRectBezierPath(backgroundRect, 5)
        backgroundRectFillPath.fill()
        super(DefconAppKitFontInfoSegmentedCell, self).drawWithFrame_inView_(frame, view)


class FontInfoSegmentedButton(vanilla.SegmentedButton):

    nsSegmentedCellClass = DefconAppKitFontInfoSegmentedCell


# Group View

class DefconAppKitFontInfoSectionView(NSView):

    def viewDidMoveToWindow(self):
        if self.window() is None:
            return
        if hasattr(self, "vanillaWrapper") and self.vanillaWrapper() is not None:
            v = self.vanillaWrapper()
            v.buildUI()
            v._scrollView.setPosSize(v._scrollView._posSize)
            v._adjustControlSizes()


class DefconAppKitFontInfoCategoryControlsGroup(NSView):

    def isFlipped(self):
        return True

    def viewDidMoveToWindow(self):
        if self.window() is None:
            return
        if hasattr(self, "_haveMovedToWindow"):
            return
        self._haveMovedToWindow = True
        scrollView = self.enclosingScrollView()
        clipView = scrollView.contentView()
        pt = (0, 0)
        clipView.scrollToPoint_(pt)
        scrollView.reflectScrolledClipView_(clipView)

    def scrollControlToVisible_(self, control):
        frame = control.frame()
        top = (0, frame.origin.y)
        bottom = (0, frame.origin.y + frame.size.height)
        visibleRect = self.visibleRect()
        if not NSPointInRect(top, visibleRect) or not NSPointInRect(bottom, visibleRect):
            scrollView = self.enclosingScrollView()
            clipView = scrollView.contentView()
            viewHeight = clipView.visibleRect().size.height
            x, y = bottom
            if y < viewHeight:
                y = viewHeight
            clipView.scrollToPoint_((x, y))
            scrollView.reflectScrolledClipView_(clipView)


class FontInfoCategoryControlsGroup(vanilla.Group):

    nsViewClass = DefconAppKitFontInfoCategoryControlsGroup


backgroundColor = NSColor.windowBackgroundColor()


class FontInfoSection(vanilla.Group):

    nsViewClass = DefconAppKitFontInfoSectionView

    def __init__(self, posSize, groupOrganization, controlDescriptions, font):
        super(FontInfoSection, self).__init__(posSize)
        self._finishedSetup = False
        self._groupOrganization = groupOrganization
        self._controlDescriptions = controlDescriptions
        self._font = font
        # reference storage
        self._jumpButtons = {}
        self._groupTitlePositions = {}
        self._controlToAttributeData = {}
        self._attributeToControl = {}
        self._defaultControlToAttribute = {}
        self._attributeToDefaultControl = {}

    def buildUI(self):
        if self._finishedSetup:
            return
        groupOrganization = self._groupOrganization
        controlDescriptions = self._controlDescriptions
        left, top, width, height = self._posSize
        # top navigation
        self._buttonBar = FontInfoToolbar((0, 12, -0, 60))
        groupTitles = [group[0] for group in groupOrganization]
        if len(groupTitles) > 1:
            buttonFont = FontInfoToolbarButton((0, 0, 0, 0), "", sizeStyle="small").getNSButton().font()
            attributes = {NSFontNameAttribute: buttonFont}
            buttonWidth = 18 + max([NSString.stringWithString_(title).sizeWithAttributes_(attributes)[0] for title in groupTitles])
            buttonBufferWidth = 5
            buttonGroupWidth = buttonWidth * len(groupTitles)
            buttonGroupWidth += buttonBufferWidth * (len(groupTitles) - 1)
            left = (width - buttonGroupWidth) / 2
            for index, groupTitle in enumerate(groupTitles):
                attribute = "jumpButton%d" % index
                jumpButton = FontInfoToolbarButton((left, 25, buttonWidth, 17), groupTitle, sizeStyle="small", callback=self._jumpButtonCallback)
                setattr(self._buttonBar, attribute, jumpButton)
                left += buttonWidth
                left += buttonBufferWidth
                self._jumpButtons[jumpButton] = index
        # controls
        controlView = FontInfoCategoryControlsGroup((0, 0, 10, 10))
        # positions and sizes
        controlViewHeight = 0
        controlViewWidth = width - 16
        groupTitleLeft = 10
        groupTitleWidth = controlViewWidth - 20
        itemTitleLeft = 10
        itemTitleWidth = 175
        itemInputLeft = itemTitleLeft + itemTitleWidth + 5
        itemInputStringWidth = controlViewWidth - 10 - itemInputLeft
        itemWidths = {
            "idNumber": 140,
            "number": 70,
            InfoEditText: itemInputStringWidth,
            vanilla.RadioGroup: itemInputStringWidth,
            vanilla.PopUpButton: itemInputStringWidth,
            CheckList: itemInputStringWidth,
            vanilla.DatePicker: itemInputStringWidth,
            vanilla.CheckBox: 22,
            InfoCheckbox: 22,
            PanoseControl: controlViewWidth,
            EmbeddingControl: itemInputStringWidth,
            DictList: controlViewWidth,
        }
        # run through the groups
        currentTop = -10
        for groupIndex, group in enumerate(groupOrganization):
            # group title
            self._groupTitlePositions[groupIndex] = currentTop
            currentTop -= 17
            groupTitleAttribute = "groupTitle%d" % groupIndex
            groupTitle = group[0]
            groupTitleControl = vanilla.TextBox((groupTitleLeft, currentTop, groupTitleWidth, 17), groupTitle)
            setattr(controlView, groupTitleAttribute, groupTitleControl)
            # group title line
            currentTop -= 5
            groupTitleLineAttribute = "groupTitleLine%d" % groupIndex
            groupTitleLineControl = vanilla.HorizontalLine((groupTitleLeft, currentTop, groupTitleWidth, 1))
            setattr(controlView, groupTitleLineAttribute, groupTitleLineControl)
            currentTop -= 15
            # run through the controls
            for fontAttribute in group[1:]:
                item = controlDescriptions[fontAttribute]
                itemClass = item["controlClass"]
                fontAttributeTag = fontAttribute.replace("{", "_").replace("}", "_")
                # title
                itemTitle = item["title"]
                if itemTitle:
                    itemTitle += ":"
                # item title
                if itemTitle:
                    itemTitleAttribute = "itemTitle_%s" % fontAttributeTag
                    alignment = "right"
                    if itemClass == DictList:
                        alignment = "left"
                    itemTitleControl = vanilla.TextBox((itemTitleLeft, currentTop - 19, itemTitleWidth, 17), itemTitle, alignment=alignment)
                    setattr(controlView, itemTitleAttribute, itemTitleControl)
                    if itemClass == DictList:
                        currentTop -= 25
                # control
                itemOptions = item.get("controlOptions", {})
                itemWidthKey = itemOptions.get("style", itemClass)
                itemWidth = itemWidths[itemWidthKey]
                if itemClass == InfoEditText:
                    if itemOptions.get("lineCount", 1) != 1:
                        itemClass = InfoTextEditor
                # EditText, NumberEditText
                if itemClass == InfoEditText or itemClass == NumberEditText:
                    itemHeight = 22
                    currentTop -= itemHeight
                    itemAttribute = "inputEditText_%s" % fontAttributeTag
                    if itemClass == NumberEditText:
                        allowFloat = itemOptions.get("allowFloat", True)
                        allowNegative = itemOptions.get("allowNegative", True)
                        minimum = itemOptions.get("minimum", None)
                        maximum = itemOptions.get("maximum", None)
                        decimals = itemOptions.get("decimals", 2)
                        itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), callback=self._controlEditCallback,
                            allowFloat=allowFloat, allowNegative=allowNegative, minimum=minimum, maximum=maximum, decimals=decimals)
                    else:
                        itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), callback=self._controlEditCallback, formatter=itemOptions.get("formatter"))
                    setattr(controlView, itemAttribute, itemControl)
                # TextEditor
                elif itemClass == InfoTextEditor:
                    itemHeight = (itemOptions["lineCount"] * 14) + 8
                    currentTop -= itemHeight
                    itemAttribute = "inputTextEditor_%s" % fontAttributeTag
                    if not itemTitle:
                        l = groupTitleLeft
                        w = groupTitleWidth
                    else:
                        l = itemInputLeft
                        w = itemWidth
                    itemControl = itemClass((l, currentTop, w, itemHeight), callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # RadioGroup
                elif itemClass == vanilla.RadioGroup:
                    radioOptions = itemOptions["items"]
                    itemHeight = 20 * len(radioOptions)
                    currentTop -= itemHeight
                    itemAttribute = "inputRadioGroup_%s" % fontAttributeTag
                    itemControl = itemClass((itemInputLeft, currentTop - 2, itemWidth, itemHeight), radioOptions, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # CheckBox
                elif itemClass in (vanilla.CheckBox, InfoCheckbox):
                    itemHeight = 22
                    currentTop -= itemHeight
                    itemAttribute = "inputCheckBox_%s" % fontAttributeTag
                    itemControl = itemClass((itemInputLeft, currentTop - 1, itemWidth, itemHeight), "", callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # PopUpButton
                elif itemClass == vanilla.PopUpButton:
                    itemHeight = 20
                    currentTop -= itemHeight
                    popupOptions = itemOptions["items"]
                    itemAttribute = "inputPopUpButton_%s" % fontAttributeTag
                    itemControl = itemClass((itemInputLeft, currentTop - 2, itemWidth, itemHeight), popupOptions, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # CheckList
                elif itemClass == CheckList:
                    listOptions = itemOptions["items"]
                    itemHeight = 200
                    if len(listOptions) * 20 < itemHeight:
                        itemHeight = len(listOptions) * 20
                    currentTop -= itemHeight
                    itemAttribute = "inputCheckList_%s" % fontAttributeTag
                    itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), listOptions, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # DatePicker
                elif itemClass == vanilla.DatePicker:
                    now = NSDate.date()
                    minDate = NSDate.dateWithString_("1904-01-01 00:00:01 +0000")
                    minDate = None
                    itemHeight = 27
                    currentTop -= itemHeight
                    itemAttribute = "inputDatePicker_%s" % fontAttributeTag
                    itemControl = itemClass((itemInputLeft, currentTop + 5, itemWidth, itemHeight), date=now, minDate=minDate, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # Panose
                elif itemClass == PanoseControl:
                    itemHeight = 335
                    currentTop -= itemHeight
                    itemAttribute = "inputPanoseControl_%s" % fontAttributeTag
                    itemControl = itemClass((10, currentTop, itemWidth, itemHeight), 0, itemTitleWidth, itemInputLeft - 10, itemInputStringWidth, self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # Embedding
                elif itemClass == EmbeddingControl:
                    itemHeight = 75
                    currentTop -= itemHeight
                    itemAttribute = "inputEmbeddingControl_%s" % fontAttributeTag
                    itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                # DictList
                elif itemClass == DictList:
                    itemHeight = 200
                    currentTop -= itemHeight
                    itemAttribute = "inputDictList_%s" % fontAttributeTag
                    columnDescriptions = itemOptions["columnDescriptions"]
                    itemPrototype = itemOptions["itemPrototype"]
                    listClass = itemOptions.get("listClass")
                    validator = itemOptions.get("validator")
                    variableRowHeights = itemOptions.get("variableRowHeights", False)
                    showColumnTitles = itemOptions.get("showColumnTitles", True)
                    itemControl = itemClass((groupTitleLeft, currentTop, groupTitleWidth, itemHeight), columnDescriptions=columnDescriptions, listClass=listClass, itemPrototype=itemPrototype, callback=self._controlEditCallback, validator=validator, variableRowHeights=variableRowHeights, showColumnTitles=showColumnTitles)
                    setattr(controlView, itemAttribute, itemControl)
                else:
                    print(itemClass)
                    continue
                # default
                if item["hasDefault"]:
                    currentTop -= 17
                    defaultControl = vanilla.CheckBox((itemInputLeft, currentTop, 100, 10), "Use Default Value", sizeStyle="mini", callback=self._useDefaultCallback)
                    defaultAttribute = "inputDefaultCheckBox_%s" % fontAttributeTag
                    setattr(controlView, defaultAttribute, defaultControl)
                    self._defaultControlToAttribute[defaultControl] = fontAttribute
                    self._attributeToDefaultControl[fontAttribute] = defaultControl
                # store
                item["fontAttribute"] = fontAttribute
                self._controlToAttributeData[itemControl] = item
                self._attributeToControl[fontAttribute] = itemControl
                # final offset
                currentTop -= 15

        # scroll view
        height = abs(currentTop)
        self._scrollView = vanilla.ScrollView((0, 62, -0, -0), controlView.getNSView(), backgroundColor=backgroundColor, hasHorizontalScroller=False)
        self._scrollView.getNSScrollView().setFrame_(((0, 0), (0, 0)))
        controlView.setPosSize((0, 0, width, height))
        controlView._setFrame(((0, 0), (width, height)))
        size = controlView.getNSView().frame().size
        controlView.getNSView().setFrame_(((0, 0), size))

        # load info
        self._loadInfo()
        self._updatePlaceholders()
        self._finishedSetup = True

        # observe
        self._font.info.addObserver(self, "_infoChanged", "Info.Changed")

    def _breakCycles(self):
        if self._font is not None and self._font.info.hasObserver(self, "Info.Changed"):
            self._font.info.removeObserver(self, "Info.Changed")
        self._font = None
        # reference storage
        self._jumpButtons = None
        self._groupTitlePositions = None
        self._controlToAttributeData = None
        self._attributeToControl = None
        self._defaultControlToAttribute = None
        self._attributeToDefaultControl = None
        super(FontInfoSection, self)._breakCycles()

    def _loadInfo(self):
        for attribute, control in self._attributeToControl.items():
            value = getAttributeValue(self._font.info, attribute)
            attributeData = self._controlToAttributeData[control]
            # handle the default control
            if attributeData["hasDefault"]:
                defaultControl = self._attributeToDefaultControl[attribute]
                defaultControl.set(value is None)
                control.enable(value is not None)
            # handle the main control
            if value is not None:
                # convert
                conversionFunction = attributeData["conversionFromUFO"]
                if conversionFunction:
                    value = conversionFunction(value)
                # set
                control.set(value)

    def _infoChanged(self, notification):
        self._updatePlaceholders()

    # control view shortcut

    def _get_controlView(self):
        scrollView = self._scrollView.getNSScrollView()
        return scrollView.documentView()

    _controlView = property(_get_controlView)

    # control adjustments

    def _adjustControlSizes(self):
        view = self._controlView
        for subview in view.subviews():
            if not hasattr(subview, "vanillaWrapper"):
                continue
            wrapper = subview.vanillaWrapper()
            if wrapper is None:
                continue
            if not isinstance(wrapper, vanilla.RadioGroup):
                continue
            matrix = wrapper.getNSMatrix()
            matrixWidth = 0
            for cell in matrix.cells():
                w = cell.cellSize().width
                if w > matrixWidth:
                    matrixWidth = w
            matrixHeight = matrix.frame().size.height
            matrix.setFrameSize_((matrixWidth, matrixHeight))

    # navigation

    def _jumpButtonCallback(self, sender):
        scrollView = self._scrollView.getNSScrollView()
        clipView = scrollView.contentView()
        documentView = scrollView.documentView()
        index = self._jumpButtons[sender]
        viewH = documentView.bounds().size[1]
        clipViewH = clipView.bounds().size[1]
        y = -self._groupTitlePositions[index] - 10
        if y > viewH:
            y = NSMaxY(documentView.frame()) - clipViewH
        pt = (0, y)
        documentView.scrollPoint_(pt)

    # callbacks

    def _controlEditCallback(self, sender):
        if not self._finishedSetup:
            return
        attributeData = self._controlToAttributeData[sender]
        attribute = attributeData["fontAttribute"]
        conversionFunction = attributeData["conversionToUFO"]
        # get the value
        value = sender.get()
        # convert
        if isinstance(value, bool):
            # pass a bool
            # seems like in py3 isinstance(True, int) is also True...
            pass
        elif isinstance(value, NSArray):
            value = list(value)
        elif isinstance(value, long):
            value = int(value)
        if conversionFunction is not None:
            value = conversionFunction(value)
        # set
        setAttributeValue(self._font.info, attribute, value)

    def _useDefaultCallback(self, sender):
        state = sender.get()
        fontAttribute = self._defaultControlToAttribute[sender]
        control = self._attributeToControl[fontAttribute]
        attributeData = self._controlToAttributeData[control]
        # get the value
        if state:
            value = None
        else:
            value = getAttrWithFallback(self._font.info, fontAttribute)
        # set in the font
        setAttributeValue(self._font.info, fontAttribute, value)
        # convert for the interface
        if value is not None:
            conversionFunction = attributeData["conversionFromUFO"]
            if conversionFunction is not None:
                value = conversionFunction(value)
        # update the control
        control.enable(not state)
        if value is None:
            if isinstance(control, vanilla.EditText):
                control.set("")
        else:
            control.set(value)

    def _updatePlaceholders(self):
        for control, attributeData in self._controlToAttributeData.items():
            if isinstance(control, vanilla.EditText):
                if not attributeData["hasDefault"]:
                    continue
                attribute = attributeData["fontAttribute"]
                value = getAttrWithFallback(self._font.info, attribute)
                if value is None:
                    value = ""
                if not isinstance(value, basestring):
                    value = str(value)
                control.setPlaceholder(value)


# ---------
# main view
# ---------

class FontInfoView(vanilla.Tabs):

    def __init__(self, posSize, font, controlAdditions=None):
        self._font = font
        if controlAdditions is None:
            controlAdditions = []
        self._allControlOrganization = controlOrganization + controlAdditions
        sectionNames = [section["title"] for section in self._allControlOrganization]
        super(FontInfoView, self).__init__(posSize, sectionNames)
        self._nsObject.setTabViewType_(NSNoTabsNoBorder)
        left, top, width, height = posSize
        assert width > 0
        # controls
        buttonWidth = 85 * len(self._allControlOrganization)
        buttonLeft = (width - buttonWidth) / 2
        segments = [dict(title=sectionName) for sectionName in sectionNames]
        self._segmentedButton = FontInfoSegmentedButton((buttonLeft, -26, buttonWidth, 24), segments, callback=self._tabSelectionCallback, sizeStyle="regular")
        self._segmentedButton.set(0)
        # sections
        for index, sectionData in enumerate(self._allControlOrganization):
            viewClass = sectionData.get("customView")
            if viewClass is not None:
                self[index].section = viewClass((0, 0, width, 0), self._font)
            else:
                controlDescriptions = sectionData.get("controlDescriptions")
                if controlDescriptions is None:
                    controlDescriptions = allControlDescriptions
                self[index].section = FontInfoSection((0, 0, width, 0), sectionData["groups"], controlDescriptions, self._font)

    def _tabSelectionCallback(self, sender):
        self.set(sender.get())

    def _breakCycles(self):
        self._font = None
        self._allControlOrganization = None
        super(FontInfoView, self)._breakCycles()
