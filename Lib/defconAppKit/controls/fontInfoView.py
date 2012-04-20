import time
from Foundation import *
from AppKit import *
import vanilla
from ufo2fdk.fontInfoData import getAttrWithFallback, dateStringToTimeValue
from defconAppKit.tools.roundedRectBezierPath import roundedRectBezierPath

import objc
objc.setVerbose(True)


# -----------------------------------
# Formatters
# These will be used in the controls.
# -----------------------------------

integerFormatter = NSNumberFormatter.alloc().init()
integerFormatter.setFormat_("#;0;-#")
integerFormatter.setAllowsFloats_(False)
integerFormatter.setGeneratesDecimalNumbers_(False)

integerPositiveFormatter = NSNumberFormatter.alloc().init()
integerPositiveFormatter.setFormat_("#;0;-#")
integerPositiveFormatter.setAllowsFloats_(False)
integerPositiveFormatter.setGeneratesDecimalNumbers_(False)
integerPositiveFormatter.setMinimum_(NSNumber.numberWithInt_(0))

floatFormatter = NSNumberFormatter.alloc().init()
floatFormatter.setNumberStyle_(NSNumberFormatterDecimalStyle)
floatFormatter.setFormat_("#.00;0.00;-#.00")
floatFormatter.setAllowsFloats_(True)
floatFormatter.setGeneratesDecimalNumbers_(False)

positiveFloatFormatter = NSNumberFormatter.alloc().init()
positiveFloatFormatter.setAllowsFloats_(True)
positiveFloatFormatter.setGeneratesDecimalNumbers_(False)
positiveFloatFormatter.setMinimum_(NSNumber.numberWithInt_(0))

class NegativeIntegerEditText(vanilla.EditText):

    def __init__(self, *args, **kwargs):
        self._finalCallback = kwargs.get("callback")
        kwargs["callback"] = self._textEditCallback
        super(NegativeIntegerEditText, self).__init__(*args, **kwargs)

    def _breakCycles(self):
        self._finalCallback = None
        super(NegativeIntegerEditText, self)._breakCycles()

    def _get(self):
        return self._nsObject.stringValue()

    def get(self):
        v = self._get()
        if not v:
            return None
        v = int(v)
        return v

    def _textEditCallback(self, sender):
        value = sender._get()
        if value != "-":
            try:
                v = int(value)
                if v > 0:
                    sender.set("")
                    return
            except ValueError:
                if value.startswith("-"):
                    value = value = "-"
                else:
                    value = ""
                sender.set(value)
                return
            if self._finalCallback is not None:
                self._finalCallback(sender)


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

    #def attributedStringForObjectValue_withDefaultAttributes_(self, value, attrs):
    #    value = self.stringForObjectValue_(value)
    #    valid, partiallyValid, value, error = self._parseString(value)
    #    if not valid:
    #        attrs[NSForegroundColorAttributeName] = NSColor.redColor()
    #    else:
    #        attrs[NSForegroundColorAttributeName] = NSColor.blackColor()
    #    string = NSAttributedString.alloc().initWithString_attributes_(value, attrs)
    #    return string

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
                    tempValues.append(int(i))
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
            control = vanilla.TextBox((titlePosition, currentTop+2, titleWidth, 17), "", alignment="right")
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
            control.set(value[index+1])

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
        self.subsettingCheckBox = vanilla.CheckBox((0, 30, -0, 20), "Allow Subsetting", callback=self._controlCallback)
        self.bitmapCheckBox = vanilla.CheckBox((0, 55, -10, 20), "Allow Only Bitmap Embedding", callback=self._controlCallback)
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
        self.subsettingCheckBox.set(not 8 in values)
        self.bitmapCheckBox.set(9 in values)
        self._handleEnable()

    def get(self):
        values = []
        basicValue = self.basicsPopUp.get()
        if basicValue != 0:
            return values
        if not self.subsettingCheckBox.get():
            values.append(8)
        if self.bitmapCheckBox.get():
            values.append(9)
        return values


class CheckList(vanilla.List):

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
            dict(title="title"),
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


# -------------------------------------------------------
# Input control definitions.
# These describe the controls and how they should behave.
# -------------------------------------------------------

def inputItemDict(**kwargs):
    default = dict(
        title=None,
        hasDefault=True,
        controlClass=vanilla.EditText,
        #controlOptions=None,
        conversionFromUFO=None,
        conversionToUFO=None,
    )
    default.update(kwargs)
    return default

def noneToZero(value):
    if value is None:
        return 0
    return value

## Basic Naming

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
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
versionMinorItem = inputItemDict(
    title="Version Minor",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)

## Basic Dimensions

unitsPerEmItem = inputItemDict(
    title="Units Per Em",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
descenderItem = inputItemDict(
    title="Descender",
    hasDefault=False,
    controlClass=NegativeIntegerEditText,
    controlOptions=dict(style="number"),
    conversionToUFO=noneToZero
)
xHeightItem = inputItemDict(
    title="x-height",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
capHeightItem = inputItemDict(
    title="Cap-height",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
ascenderItem = inputItemDict(
    title="Ascender",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
italicAngleItem = inputItemDict(
    title="Italic Angle",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=floatFormatter)
)

## Basic Legal

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

## Basic Parties

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

## Basic Note

noteItem = inputItemDict(
    title="",
    hasDefault=False,
    controlOptions=dict(lineCount=20)
)


## OpenType head Table

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
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
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

## OpenType name Table

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

## OpenType hhea Table

openTypeHheaAscenderItem = inputItemDict(
    title="Ascender",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeHheaDescenderItem = inputItemDict(
    title="Descender",
    controlClass=NegativeIntegerEditText,
    controlOptions=dict(style="number"),
    conversionToUFO=noneToZero
)
openTypeHheaLineGapItem = inputItemDict(
    title="LineGap",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeHheaCaretSlopeRiseItem = inputItemDict(
    title="caretSlopeRise",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeHheaCaretSlopeRunItem = inputItemDict(
    title="caretSlopeRun",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeHheaCaretOffsetItem = inputItemDict(
    title="caretOffset",
    controlOptions=dict(style="number", formatter=integerFormatter)
)

## OpenType vhea Table

openTypeVheaVertTypoAscenderItem = inputItemDict(
    title="vertTypoAscender",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeVheaVertTypoDescenderItem = inputItemDict(
    title="vertTypoDescender",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeVheaVertTypoLineGapItem = inputItemDict(
    title="vertTypoLineGap",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeVheaCaretSlopeRiseItem = inputItemDict(
    title="caretSlopeRise",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeVheaCaretSlopeRunItem = inputItemDict(
    title="caretSlopeRun",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeVheaCaretOffsetItem = inputItemDict(
    title="caretOffset",
    controlOptions=dict(style="number", formatter=integerFormatter)
)

## OpenType OS/2 Table

openTypeOS2WeightClassItem = inputItemDict(
    title="usWeightClass",
    hasDefault=False,
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
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
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeOS2TypoDescenderItem = inputItemDict(
    title="sTypoDescender",
    controlClass=NegativeIntegerEditText,
    controlOptions=dict(style="number"),
    conversionToUFO=noneToZero
)
openTypeOS2TypoLineGapItem = inputItemDict(
    title="sTypoLineGap",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeOS2WinAscentItem = inputItemDict(
    title="usWinAscent",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeOS2WinDescentItem = inputItemDict(
    title="usWinDescent",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeOS2TypeItem = inputItemDict(
    title="fsType",
    controlClass=EmbeddingControl,
    hasDefault=False
)
openTypeOS2SubscriptXSizeItem = inputItemDict(
    title="ySubscriptXSize",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SubscriptYSizeItem = inputItemDict(
    title="ySubscriptYSize",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SubscriptXOffsetItem = inputItemDict(
    title="ySubscriptXOffset",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SubscriptYOffsetItem = inputItemDict(
    title="ySubscriptYOffset",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SuperscriptXSizeItem = inputItemDict(
    title="ySuperscriptXSize",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SuperscriptYSizeItem = inputItemDict(
    title="ySuperscriptYSize",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SuperscriptXOffsetItem = inputItemDict(
    title="ySuperscriptXOffset",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2SuperscriptYOffsetItem = inputItemDict(
    title="ySuperscriptYOffset",
    controlOptions=dict(style="number", formatter=integerFormatter)
)
openTypeOS2StrikeoutSizeItem = inputItemDict(
    title="yStrikeoutSize",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
openTypeOS2StrikeoutPositionItem = inputItemDict(
    title="yStrikeoutPosition",
    controlOptions=dict(style="number", formatter=integerFormatter)
)

## Postscript Identification

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
    controlOptions=dict(style="idNumber", formatter=integerPositiveFormatter)
)

## Postscript Hinting

def _postscriptBluesToUFO(string, maxCount):
    if not string:
        return []
    try:
        values = [int(i) for i in string.split(" ") if i]
    except ValueError:
        values = []
    values = sorted(values)
    if len(values) % 2:
        values.pop()
    if len(values) > maxCount:
        value = value[:maxCount]
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
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
postscriptBlueShiftItem = inputItemDict(
    title="BlueShift",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter)
)
postscriptBlueScaleItem = inputItemDict(
    title="BlueScale",
    controlOptions=dict(style="number", formatter=positiveFloatFormatter)
)
postscriptForceBoldItem = inputItemDict(
    title="ForceBold",
    controlClass=vanilla.CheckBox
)

## Postscript Dimensions

postscriptSlantAngleItem = inputItemDict(
    title="SlantAngle",
    controlOptions=dict(style="number", formatter=floatFormatter)
)
postscriptUnderlineThicknessItem = inputItemDict(
    title="UnderlineThickness",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter),
    hasDefault=True
)
postscriptUnderlinePositionItem = inputItemDict(
    title="UnderlinePosition",
    controlOptions=dict(style="number", formatter=integerFormatter),
    hasDefault=True
)
postscriptIsFixedPitchItem = inputItemDict(
    title="isFixedPitched",
    controlClass=vanilla.CheckBox
)
postscriptDefaultWidthXItem = inputItemDict(
    title="DefaultWidthX",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter),
    hasDefault=True
)
postscriptNominalWidthXItem = inputItemDict(
    title="NominalWidthX",
    controlOptions=dict(style="number", formatter=integerPositiveFormatter),
    hasDefault=True
)

## Postscript Characters

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

postscriptWindowsCharacterSetItem = inputItemDict(
    title="Microsoft Character Set",
    controlClass=vanilla.PopUpButton,
    controlOptions=dict(items=postscriptWindowsCharacterSetOptions)
)

## Miscellaneous

macintoshFONDNameItem = inputItemDict(
    title="Font Name"
)
macintoshFONDFamilyIDItem = inputItemDict(
    title="Family ID Number",
    controlOptions=dict(style="idNumber", formatter=integerPositiveFormatter)
)

# -----------------------------------------------------------------------
# Interface Groups
# These define the grouping and subgrouping of controls in the interface.
# -----------------------------------------------------------------------

allControlDescriptions = dict(
    familyName=familyNameItem,
    styleName=styleNameItem,
    styleMapFamilyName=styleMapFamilyNameItem,
    styleMapStyleName=styleMapStyleNameItem,
    versionMajor=versionMajorItem,
    versionMinor=versionMinorItem,

    unitsPerEm=unitsPerEmItem,
    descender=descenderItem,
    xHeight=xHeightItem,
    capHeight=capHeightItem,
    ascender=ascenderItem,
    italicAngle=italicAngleItem,

    copyright=copyrightItem,
    trademark=trademarkItem,
    openTypeNameLicense=openTypeNameLicenseItem,
    openTypeNameLicenseURL=openTypeNameLicenseURLItem,

    openTypeNameDesigner=openTypeNameDesignerItem,
    openTypeNameDesignerURL=openTypeNameDesignerURLItem,
    openTypeNameManufacturer=openTypeNameManufacturerItem,
    openTypeNameManufacturerURL=openTypeNameManufacturerURLItem,

    note=noteItem,

    openTypeHeadCreated=openTypeHeadCreatedItem,
    openTypeHeadLowestRecPPEM=openTypeHeadLowestRecPPEMItem,
    openTypeHeadFlags=openTypeHeadFlagsItem,

    openTypeNamePreferredFamilyName=openTypeNamePreferredFamilyNameItem,
    openTypeNamePreferredSubfamilyName=openTypeNamePreferredSubfamilyNameItem,
    openTypeNameCompatibleFullName=openTypeNameCompatibleFullNameItem,
    openTypeNameWWSFamilyName=openTypeNameWWSFamilyNameItem,
    openTypeNameWWSSubfamilyName=openTypeNameWWSSubfamilyNameItem,
    openTypeNameVersion=openTypeNameVersionItem,
    openTypeNameUniqueID=openTypeNameUniqueIDItem,
    openTypeNameDescription=openTypeNameDescriptionItem,
    openTypeNameSampleText=openTypeNameSampleTextItem,

    openTypeHheaAscender=openTypeHheaAscenderItem,
    openTypeHheaDescender=openTypeHheaDescenderItem,
    openTypeHheaLineGap=openTypeHheaLineGapItem,
    openTypeHheaCaretSlopeRise=openTypeHheaCaretSlopeRiseItem,
    openTypeHheaCaretSlopeRun=openTypeHheaCaretSlopeRunItem,
    openTypeHheaCaretOffset=openTypeHheaCaretOffsetItem,

    openTypeVheaVertTypoAscender=openTypeVheaVertTypoAscenderItem,
    openTypeVheaVertTypoDescender=openTypeVheaVertTypoDescenderItem,
    openTypeVheaVertTypoLineGap=openTypeVheaVertTypoLineGapItem,
    openTypeVheaCaretSlopeRise=openTypeVheaCaretSlopeRiseItem,
    openTypeVheaCaretSlopeRun=openTypeVheaCaretSlopeRunItem,
    openTypeVheaCaretOffset=openTypeVheaCaretOffsetItem,

    openTypeOS2WidthClass=openTypeOS2WidthClassItem,
    openTypeOS2WeightClass=openTypeOS2WeightClassItem,
    openTypeOS2Selection=openTypeOS2SelectionItem,
    openTypeOS2VendorID=openTypeOS2VendorIDItem,
    openTypeOS2Panose=openTypeOS2PanoseItem,
    openTypeOS2UnicodeRanges=openTypeOS2UnicodeRangesItem,
    openTypeOS2CodePageRanges=openTypeOS2CodePageRangesItem,
    openTypeOS2TypoAscender=openTypeOS2TypoAscenderItem,
    openTypeOS2TypoDescender=openTypeOS2TypoDescenderItem,
    openTypeOS2TypoLineGap=openTypeOS2TypoLineGapItem,
    openTypeOS2WinAscent=openTypeOS2WinAscentItem,
    openTypeOS2WinDescent=openTypeOS2WinDescentItem,
    openTypeOS2Type=openTypeOS2TypeItem,
    openTypeOS2SubscriptXSize=openTypeOS2SubscriptXSizeItem,
    openTypeOS2SubscriptYSize=openTypeOS2SubscriptYSizeItem,
    openTypeOS2SubscriptXOffset=openTypeOS2SubscriptXOffsetItem,
    openTypeOS2SubscriptYOffset=openTypeOS2SubscriptYOffsetItem,
    openTypeOS2SuperscriptXSize=openTypeOS2SuperscriptXSizeItem,
    openTypeOS2SuperscriptYSize=openTypeOS2SuperscriptYSizeItem,
    openTypeOS2SuperscriptXOffset=openTypeOS2SuperscriptXOffsetItem,
    openTypeOS2SuperscriptYOffset=openTypeOS2SuperscriptYOffsetItem,
    openTypeOS2StrikeoutSize=openTypeOS2StrikeoutSizeItem,
    openTypeOS2StrikeoutPosition=openTypeOS2StrikeoutPositionItem,

    postscriptFontName=postscriptFontNameItem,
    postscriptFullName=postscriptFullNameItem,
    postscriptWeightName=postscriptWeightNameItem,
    postscriptUniqueID=postscriptUniqueIDItem,

    postscriptBlueValues=postscriptBlueValuesItem,
    postscriptOtherBlues=postscriptOtherBluesItem,
    postscriptFamilyBlues=postscriptFamilyBluesItem,
    postscriptFamilyOtherBlues=postscriptFamilyOtherBluesItem,
    postscriptStemSnapH=postscriptStemSnapHItem,
    postscriptStemSnapV=postscriptStemSnapVItem,
    postscriptBlueFuzz=postscriptBlueFuzzItem,
    postscriptBlueShift=postscriptBlueShiftItem,
    postscriptBlueScale=postscriptBlueScaleItem,
    postscriptForceBold=postscriptForceBoldItem,

    postscriptSlantAngle=postscriptSlantAngleItem,
    postscriptUnderlineThickness=postscriptUnderlineThicknessItem,
    postscriptUnderlinePosition=postscriptUnderlinePositionItem,
    postscriptIsFixedPitch=postscriptIsFixedPitchItem,
    postscriptDefaultWidthX=postscriptDefaultWidthXItem,
    postscriptNominalWidthX=postscriptNominalWidthXItem,

    postscriptDefaultCharacter=postscriptDefaultCharacterItem,
    postscriptWindowsCharacterSet=postscriptWindowsCharacterSetItem,

    macintoshFONDName=macintoshFONDNameItem,
    macintoshFONDFamilyID=macintoshFONDFamilyIDItem,
)

controlOrganization = [
    dict(
        title="General",
        customView=None,
        groups = [
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
        groups = [
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
                "openTypeNameSampleText"
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
        groups = [
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
        title="Miscellaneous",
        customView=None,
        groups = [
            ("FOND Data",
                "macintoshFONDName",
                "macintoshFONDFamilyID"
            )
        ]
    ),
]


## Toolbar

toolbarColor1 = NSColor.colorWithCalibratedWhite_alpha_(.4, .6)
toolbarColor2 = NSColor.colorWithCalibratedWhite_alpha_(.4, .2)
toolbarColor3 = NSColor.colorWithCalibratedWhite_alpha_(.65, 1)
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

## Group View

class DefconAppKitFontInfoSectionView(NSView):

    def viewDidMoveToWindow(self):
        if hasattr(self, "vanillaWrapper") and self.vanillaWrapper() is not None:
            v = self.vanillaWrapper()
            v._scrollView.setPosSize(v._scrollView._posSize)


class DefconAppKitFontInfoCategoryControlsGroup(NSView):

    def isFlipped(self):
        return True

    def viewDidMoveToWindow(self):
        if hasattr(self, "_haveMovedToWindow"):
            return
        self._haveMovedToWindow = True
        scrollView = self.enclosingScrollView()
        clipView = scrollView.contentView()
        pt = (0, 0)
        clipView.scrollToPoint_(pt)
        scrollView.reflectScrolledClipView_(clipView)


class FontInfoCategoryControlsGroup(vanilla.Group):

    nsViewClass = DefconAppKitFontInfoCategoryControlsGroup


backgroundColor = NSColor.colorWithCalibratedWhite_alpha_(.93, 1)


class FontInfoSection(vanilla.Group):

    nsViewClass = DefconAppKitFontInfoSectionView

    def __init__(self, posSize, groupOrganization, controlDescriptions, font):
        super(FontInfoSection, self).__init__(posSize)
        self._finishedSetup = False
        self._font = font
        left, top, width, height = posSize
        ## reference storage
        self._jumpButtons = {}
        self._groupTitlePositions = {}
        self._controlToAttributeData = {}
        self._attributeToControl = {}
        self._defaultControlToAttribute = {}
        self._attributeToDefaultControl = {}
        ## top navigation
        self._buttonBar = FontInfoToolbar((0, 12, -0, 60))
        groupTitles = [group[0] for group in groupOrganization]
        if len(groupTitles) > 1:
            buttonFont = FontInfoToolbarButton((0, 0, 0, 0), "", sizeStyle="small").getNSButton().font()
            attributes = {NSFontNameAttribute : buttonFont}
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
        ## controls
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
            "idNumber" : 140,
            "number" : 70,
            vanilla.EditText : itemInputStringWidth,
            vanilla.RadioGroup : itemInputStringWidth,
            vanilla.PopUpButton : itemInputStringWidth,
            CheckList : itemInputStringWidth,
            vanilla.DatePicker : itemInputStringWidth,
            vanilla.CheckBox : 22,
            PanoseControl : controlViewWidth,
            EmbeddingControl : itemInputStringWidth,
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
                # title
                itemTitle = item["title"]
                if itemTitle:
                    itemTitle += ":"
                # item title
                if itemTitle is not None:
                    itemTitleAttribute = "itemTitle_%s" % fontAttribute
                    itemTitleControl = vanilla.TextBox((itemTitleLeft, currentTop-19, itemTitleWidth, 17), itemTitle, alignment="right")
                    setattr(controlView, itemTitleAttribute, itemTitleControl)
                # control
                itemClass = item["controlClass"]
                itemOptions = item.get("controlOptions", {})
                itemWidthKey = itemOptions.get("style", itemClass)
                itemWidth = itemWidths[itemWidthKey]
                if itemClass == vanilla.EditText:
                    if itemOptions.get("lineCount", 1) != 1:
                        itemClass = vanilla.TextEditor
                ## EditText
                if itemClass == vanilla.EditText or itemClass == NegativeIntegerEditText:
                    itemHeight = 22
                    currentTop -= itemHeight
                    itemAttribute = "inputEditText_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), callback=self._controlEditCallback, formatter=itemOptions.get("formatter"))
                    setattr(controlView, itemAttribute, itemControl)
                ## TextEditor
                elif itemClass == vanilla.TextEditor:
                    itemHeight = (itemOptions["lineCount"] * 14) + 8
                    currentTop -= itemHeight
                    itemAttribute = "inputTextEditor_%s" % fontAttribute
                    if not itemTitle:
                        l = groupTitleLeft
                        w = groupTitleWidth
                    else:
                        l = itemInputLeft
                        w = itemWidth
                    itemControl = itemClass((l, currentTop, w, itemHeight), callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## RadioGroup
                elif itemClass == vanilla.RadioGroup:
                    radioOptions = itemOptions["items"]
                    itemHeight = 20 * len(radioOptions)
                    currentTop -= itemHeight
                    itemAttribute = "inputRadioGroup_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop-2, itemWidth, itemHeight), radioOptions, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## CheckBox
                elif itemClass == vanilla.CheckBox:
                    itemHeight = 22
                    currentTop -= itemHeight
                    itemAttribute = "inputCheckBox_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop-1, itemWidth, itemHeight), "", callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## PopUpButton
                elif itemClass == vanilla.PopUpButton:
                    itemHeight = 20
                    currentTop -= itemHeight
                    popupOptions = itemOptions["items"]
                    itemAttribute = "inputPopUpButton_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop-2, itemWidth, itemHeight), popupOptions, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## CheckList
                elif itemClass == CheckList:
                    listOptions = itemOptions["items"]
                    itemHeight = 200
                    if len(listOptions) * 20 < itemHeight:
                        itemHeight = len(listOptions) * 20
                    currentTop -= itemHeight
                    itemAttribute = "inputCheckList_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), listOptions, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## DatePicker
                elif itemClass == vanilla.DatePicker:
                    now = NSDate.date()
                    minDate = NSDate.dateWithString_("1904-01-01 00:00:01 +0000")
                    minDate = None
                    itemHeight = 27
                    currentTop -= itemHeight
                    itemAttribute = "inputDatePicker_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop+5, itemWidth, itemHeight), date=now, minDate=minDate, callback=self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## Panose
                elif itemClass == PanoseControl:
                    itemHeight = 335
                    currentTop -= itemHeight
                    itemAttribute = "inputPanoseControl_%s" % fontAttribute
                    itemControl = itemClass((10, currentTop, itemWidth, itemHeight), 0, itemTitleWidth, itemInputLeft-10, itemInputStringWidth, self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                ## Embedding
                elif itemClass == EmbeddingControl:
                    itemHeight = 75
                    currentTop -= itemHeight
                    itemAttribute = "inputEmbeddingControl_%s" % fontAttribute
                    itemControl = itemClass((itemInputLeft, currentTop, itemWidth, itemHeight), self._controlEditCallback)
                    setattr(controlView, itemAttribute, itemControl)
                else:
                    print itemClass
                    continue
                ## default
                if item["hasDefault"]:
                    currentTop -= 17
                    defaultControl = vanilla.CheckBox((itemInputLeft, currentTop, 100, 10), "Use Default Value", sizeStyle="mini", callback=self._useDefaultCallback)
                    defaultAttribute = "inputDefaultCheckBox_%s" % fontAttribute
                    setattr(controlView, defaultAttribute, defaultControl)
                    self._defaultControlToAttribute[defaultControl] = fontAttribute
                    self._attributeToDefaultControl[fontAttribute] = defaultControl
                ## store
                item["fontAttribute"] = fontAttribute
                self._controlToAttributeData[itemControl] = item
                self._attributeToControl[fontAttribute] = itemControl
                ## final offset
                currentTop -= 15


        # scroll view
        height = abs(currentTop)
        self._scrollView = vanilla.ScrollView((0, 62, -0, -0), controlView.getNSView(), backgroundColor=backgroundColor, hasHorizontalScroller=False)
        controlView.setPosSize((0, 0, width, height))
        controlView._setFrame(((0, 0), (width, height)))
        size = controlView.getNSView().frame().size
        controlView.getNSView().setFrame_(((0, 0), size))

        ##load info
        self._loadInfo()
        self._finishedSetup = True

    def _breakCycles(self):
        self._jumpButtons = []
        super(FontInfoSection, self)._breakCycles()

    def _loadInfo(self):
        for attribute, control in self._attributeToControl.items():
            value = getattr(self._font.info, attribute)
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

    # control view shortcut

    def _get_controlView(self):
        scrollView = self._scrollView.getNSScrollView()
        return scrollView.documentView()

    _controlView = property(_get_controlView)

    # navigation

    def _jumpButtonCallback(self, sender):
        scrollView = self._scrollView.getNSScrollView()
        clipView = scrollView.contentView()
        documentView = scrollView.documentView()
        index = self._jumpButtons[sender]
        viewH = documentView.bounds().size[1]
        clipViewH = clipView.bounds().size[1]
        y = clipViewH - self._groupTitlePositions[index]
        y -= 10
        if y > viewH:
            y = NSMaxY(documentView.frame()) - clipViewH
        pt = (0, y)
        clipView.scrollToPoint_(pt)
        scrollView.reflectScrolledClipView_(clipView)

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
        if isinstance(value, NSArray):
            value = list(value)
        elif isinstance(value, long):
            value = int(value)
        if conversionFunction is not None:
            value = conversionFunction(value)
        # set
        setattr(self._font.info, attribute, value)

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
        setattr(self._font.info, fontAttribute, value)
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


# ---------
# main view
# ---------


class FontInfoView(vanilla.Tabs):

    def __init__(self, posSize, font, controlAdditions=None):
        allControlOrganization = controlOrganization + controlAdditions
        sectionNames = [section["title"] for section in allControlOrganization]
        super(FontInfoView, self).__init__(posSize, sectionNames)
        self._nsObject.setTabViewType_(NSNoTabsNoBorder)
        left, top, width, height = posSize
        assert width > 0
        # controls
        buttonWidth = 85 * len(allControlOrganization)
        buttonLeft = (posSize[2] - buttonWidth) / 2
        segments = [dict(title=sectionName) for sectionName in sectionNames]
        self._segmentedButton = vanilla.SegmentedButton((buttonLeft, -26, buttonWidth, 24), segments, callback=self._tabSelectionCallback, sizeStyle="regular")
        self._segmentedButton.set(0)
        # sections
        for index, sectionData in enumerate(allControlOrganization):
            viewClass = sectionData.get("customView")
            if viewClass is not None:
                self[index].section = viewClass((0, 0, width, 0), font)
            else:
                controlDescriptions = sectionData.get("controlDescriptions")
                if controlDescriptions is None:
                    controlDescriptions = allControlDescriptions
                self[index].section = FontInfoSection((0, 0, width, 0), sectionData["groups"], controlDescriptions, font)

    def _tabSelectionCallback(self, sender):
        self.set(sender.get())

