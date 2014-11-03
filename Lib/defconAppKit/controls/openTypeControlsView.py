from AppKit import *
import vanilla


class OpenTypeControlsView(vanilla.ScrollView):

    def __init__(self, posSize, callback):
        self._callback = callback
        # put the controls group into a flipped group.
        # this will give better scroll behavior.
        width = posSize[2] - NSScroller.scrollerWidth() - 2
        view = DefconAppKitTopAnchoredNSView.alloc().init()
        view.setFrame_(((0, 0), (width, 0)))
        # call the super
        super(OpenTypeControlsView, self).__init__(posSize, view, hasHorizontalScroller=False, drawsBackground=False)
        # build the view for the controls
        self._controlGroup = vanilla.Group((0, 0, width, 0))
        view.addSubview_(self._controlGroup.getNSView())
        # build the static controls
        top = 10
        # mode
        self._controlGroup.modeTitle = vanilla.TextBox((10, top, -10, 14),
            NSAttributedString.alloc().initWithString_attributes_("DISPLAY MODE", titleControlAttributes), sizeStyle="small")
        top += 20
        self._controlGroup.modeRadioGroup = vanilla.RadioGroup((10, top, -10, 38),
            ["Glyph Preview", "Glyph Records"], callback=self._controlEditCallback)
        self._controlGroup.modeRadioGroup.set(0)
        top += 48
        self._controlGroup.line1 = vanilla.HorizontalLine((10, top, -10, 1))
        top += 11
        # case
        self._controlGroup.caseTitle = vanilla.TextBox((10, top, -10, 14),
            NSAttributedString.alloc().initWithString_attributes_("CASE CONVERSION", titleControlAttributes), sizeStyle="small")
        top += 20
        self._controlGroup.caseRadioGroup = vanilla.RadioGroup((10, top, -10, 58),
            ["Unchanged", "Uppercase", "Lowercase"], callback=self._controlEditCallback)
        self._controlGroup.caseRadioGroup.set(0)
        top += 68
        # language, script and direction
        self._controlGroup.scriptTitle = vanilla.TextBox((10, top, -10, 14),
            NSAttributedString.alloc().initWithString_attributes_("SCRIPT & LANGUAGE", titleControlAttributes), sizeStyle="small")
        top += 20
        self._controlGroup.scriptPopUpButton = vanilla.PopUpButton((10, top, -10, 20), [], callback=self._controlEditCallback)
        top += 25
        self._controlGroup.languagePopUpButton = vanilla.PopUpButton((10, top, -10, 20), [], callback=self._controlEditCallback)
        top += 35
        self._controlGroup.directionTitle = vanilla.TextBox((10, top, -10, 14),
            NSAttributedString.alloc().initWithString_attributes_("WRITING DIRECTION", titleControlAttributes), sizeStyle="small")
        top += 20
        self._controlGroup.directionRadioGroup = vanilla.RadioGroup((10, top, -10, 38),
            ["Left to Right", "Right to Left"], callback=self._controlEditCallback)
        self._controlGroup.directionRadioGroup.set(0)
        top += 48
        # GSUB and GPOS
        self._controlGroup.line2 = vanilla.HorizontalLine((10, top, -10, 1))
        top += 11
        # set document view height
        (x, y), (w, h) = self._nsObject.documentView().frame()
        self._nsObject.documentView().setFrame_(((x, y), (w, top)))
        x, y, w, h = self._controlGroup.getPosSize()
        self._controlGroup.setPosSize((x, y, w, top))
        # storage
        self._dynamicTop = top
        self._gsubAttributes = {}
        self._gposAttributes = {}

    def _breakCycles(self):
        self._callback = None
        super(OpenTypeControlsView, self)._breakCycles()

    def _controlEditCallback(self, sender):
        self._callback(self)

    def setFont(self, font):
        # script list
        if font is None:
            scriptList = []
        else:
            scriptList = ["DFLT"] + font.getScriptList()
        unsupportedScripts = [i for i in scriptTags if i not in scriptList]
        if unsupportedScripts:
            scriptList.append(NSMenuItem.separatorItem())
            scriptList += unsupportedScripts
        self._controlGroup.scriptPopUpButton.setItems(scriptList)
        # language list
        if font is None:
            languageList = []
        else:
            languageList = ["Default"] + font.getLanguageList()
        unsupportedLanguages = [i for i in languageTags if i not in languageList]
        if unsupportedLanguages:
            languageList.append(NSMenuItem.separatorItem())
            languageList += unsupportedLanguages
        self._controlGroup.languagePopUpButton.setItems(languageList)
        # teardown existing controls
        for attr in self._gsubAttributes.keys() + self._gposAttributes.keys():
            delattr(self._controlGroup, attr)
        if hasattr(self._controlGroup, "gposTitle"):
            del self._controlGroup.gposTitle
        if hasattr(self._controlGroup, "gsubTitle"):
            del self._controlGroup.gsubTitle
        # stylistic set names
        if hasattr(font, "stylisticSetNames"):
            stylisticSetNames = font.stylisticSetNames
        else: stylisticSetNames = {}
        # GSUB
        top = self._dynamicTop
        if font is None:
            gsub = None
        else:
            gsub = font.gsub
        if gsub is None:
            gsubFeatureList = []
        else:
            gsubFeatureList = gsub.getFeatureList()
        self._gsubAttributes = {}
        if gsubFeatureList:
            self._controlGroup.gsubTitle = vanilla.TextBox((10, top, -10, 14),
                NSAttributedString.alloc().initWithString_attributes_("GSUB", titleControlAttributes), sizeStyle="small")
            top += 20
            for tag in gsubFeatureList:
                state = font.gsub.getFeatureState(tag)
                attr = "gsubCheckBox_%s" % tag
                obj = vanilla.CheckBox((10, top, -10, 22), tag, value=state, callback=self._controlEditCallback)
                setattr(self._controlGroup, attr, obj)
                self._gsubAttributes[attr] = tag
                top += 20
                # stylistic set name
                if tag in stylisticSetNames:
                    attr = "ssName_%s" % tag
                    setName = stylisticSetNames[tag]
                    obj = vanilla.TextBox((26, top, -10, 13), setName, sizeStyle="mini")
                    setattr(self._controlGroup, attr, obj)
                    top += 13
            top += 10
        # GPOS
        if font is None:
            gpos = None
        else:
            gpos = font.gpos
        if gpos is None:
            gposFeatureList = []
        else:
            gposFeatureList = gpos.getFeatureList()
        self._gposAttributes = {}
        if gposFeatureList:
            self._controlGroup.gposTitle = vanilla.TextBox((10, top, -10, 14),
                NSAttributedString.alloc().initWithString_attributes_("GPOS", titleControlAttributes), sizeStyle="small")
            top += 20
            for tag in gposFeatureList:
                state = font.gpos.getFeatureState(tag)
                attr = "gposCheckBox_%s" % tag
                obj = vanilla.CheckBox((10, top, -10, 22), tag, value=state, callback=self._controlEditCallback)
                setattr(self._controlGroup, attr, obj)
                self._gposAttributes[attr] = tag
                top += 20
            top += 10
        # set the view size
        (x, y), (w, h) = self._nsObject.documentView().frame()
        self._nsObject.documentView().setFrame_(((x, y), (w, top)))
        x, y, w, h = self._controlGroup.getPosSize()
        self._controlGroup.setPosSize((x, y, w, top))

    def get(self):
        mode = ["preview", "records"][self._controlGroup.modeRadioGroup.get()]
        caseConversion = ["unchanged", "upper", "lower"][self._controlGroup.caseRadioGroup.get()]
        script = self._controlGroup.scriptPopUpButton.getItems()
        if script:
            script = script[self._controlGroup.scriptPopUpButton.get()]
        else:
            script = None
        language = self._controlGroup.languagePopUpButton.getItems()
        if language:
            language = language[self._controlGroup.languagePopUpButton.get()]
        else:
            language = None
        if language == "Default":
            language = None
        gsubStates = {}
        for attr, tag in self._gsubAttributes.items():
            gsubStates[tag] = getattr(self._controlGroup, attr).get()
        gposStates = {}
        for attr, tag in self._gposAttributes.items():
            gposStates[tag] = getattr(self._controlGroup, attr).get()
        rightToLeft = self._controlGroup.directionRadioGroup.get()
        status = dict(
            mode=mode,
            case=caseConversion,
            script=script,
            language=language,
            gsub=gsubStates,
            gpos=gposStates,
            rightToLeft=rightToLeft
        )
        return status


# --------------------
# Misc. Internal Stuff
# --------------------

class DefconAppKitTopAnchoredNSView(NSView):

    def isFlipped(self):
        return True


# title attributes
shadow = NSShadow.alloc().init()
shadow.setShadowColor_(NSColor.colorWithCalibratedWhite_alpha_(1, 1))
shadow.setShadowBlurRadius_(1.0)
shadow.setShadowOffset_((1.0, -1.0))
titleControlAttributes = {
    NSForegroundColorAttributeName : NSColor.colorWithCalibratedWhite_alpha_(.4, 1),
    NSShadowAttributeName : shadow,
    NSFontAttributeName : NSFont.boldSystemFontOfSize_(NSFont.systemFontSizeForControlSize_(NSSmallControlSize))
}


# all script and language tags
_scriptTags = """arab
armn
beng
bopo
brai
byzm
cans
cher
hani
cyrl
DFLT
deva
ethi
geor
grek
gujr
guru
jamo
hang
hebr
kana
knda
khmr
lao
latn
mlym
mong
mymr
ogam
orya
runr
sinh
syrc
taml
telu
thaa
thai
tibt
yi""".splitlines()

scriptTags = []
for i in _scriptTags:
    if len(i) < 4:
        i += " " * (4 - len(i))
    scriptTags.append(i)

_languageTags = """Default
ABA
ABK
ADY
AFK
AFR
AGW
ALT
AMH
ARA
ARI
ARK
ASM
ATH
AVR
AWA
AYM
AZE
BAD
BAG
BAL
BAU
BBR
BCH
BCR
BEL
BEM
BEN
BGR
BHI
BHO
BIK
BIL
BKF
BLI
BLN
BLT
BMB
BML
BRE
BRH
BRI
BRM
BSH
BTI
CAT
CEB
CHE
CHG
CHH
CHI
CHK
CHP
CHR
CHU
CMR
COP
CRE
CRR
CRT
CSL
CSY
DAN
DAR
DCR
DEU
DGR
DHV
DJR
DNG
DNK
DUN
DZN
EBI
ECR
EDO
EFI
ELL
ENG
ERZ
ESP
ETI
EUQ
EVK
EVN
EWE
FAN
FAR
FIN
FJI
FLE
FNE
FON
FOS
FRA
FRI
FRL
FTA
FUL
GAD
GAE
GAG
GAL
GAR
GAW
GEZ
GIL
GMZ
GON
GRN
GRO
GUA
GUJ
HAI
HAL
HAR
HAU
HAW
HBN
HIL
HIN
HMA
HND
HO
HRI
HRV
HUN
HYE
IBO
IJO
ILO
IND
ING
INU
IRI
IRT
ISL
ISM
ITA
IWR
JAV
JII
JAN
JUD
JUL
KAB
KAC
KAL
KAN
KAR
KAT
KAZ
KEB
KGE
KHA
KHK
KHM
KHS
KHV
KHW
KIK
KIR
KIS
KKN
KLM
KMB
KMN
KMO
KMS
KNR
KOD
KOK
KON
KOP
KOR
KOZ
KPL
KRI
KRK
KRL
KRM
KRN
KRT
KSH
KSI
KSM
KUI
KUL
KUM
KUR
KUU
KUY
KYK
LAD
LAH
LAK
LAM
LAO
LAT
LAZ
LCR
LDK
LEZ
LIN
LMA
LMB
LMW
LSB
LSM
LTH
LUB
LUG
LUH
LUO
LVI
MAJ
MAK
MAL
MAN
MAR
MAW
MBN
MCH
MCR
MDE
MEN
MIZ
MKD
MLE
MLG
MLN
MLR
MLY
MND
MNG
MNI
MNK
MNX
MOK
MOL
MON
MOR
MRI
MTH
MTS
MUN
NAG
NAN
NAS
NCR
NDB
NDG
NEP
NEW
NHC
NIS
NIU
NKL
NLD
NOG
NOR
NSM
NTA
NTO
NYN
OCR
OJB
ORI
ORO
OSS
PAA
PAL
PAN
PAP
PAS
PGR
PIL
PLG
PLK
PRO
PTG
QIN
RAJ
RCR
RBU
RIA
RMS
ROM
ROY
RSY
RUA
RUS
SAD
SAN
SAT
SAY
SEK
SEL
SGO
SHN
SIB
SID
SIG
SKS
SKY
SLA
SLV
SML
SMO
SNA
SND
SNH
SNK
SOG
SOT
SQI
SRB
SRK
SRR
SSL
SSM
SUR
SVA
SVE
SWA
SWK
SWZ
SXT
SYR
TAB
TAJ
TAM
TAT
TCR
TEL
TGN
TGR
TGY
THA
THT
TIB
TKM
TMN
TNA
TNE
TNG
TOD
TRK
TSG
TUA
TUL
TUV
TWI
UDM
UKR
URD
USB
UYG
UZB
VEN
VIT
WA
WAG
WCR
WEL
WLF
XHS
YAK
YBA
YCR
YIC
YIM
ZHP
ZHS
ZHT
ZND
ZUL""".splitlines()

languageTags = []
for i in _languageTags:
    if len(i) < 4:
        i += " " * (4 - len(i))
    languageTags.append(i)

