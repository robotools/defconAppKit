import os
from tempfile import mkstemp
import time
import weakref
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._n_a_m_e import NameRecord
from fontTools.encodings.MacRoman import MacRoman
from ufo2fdk.outlineOTF import OutlineOTFCompiler
from dynamicFontManager import dynamicFontManager as OSFontBridge
from AppKit import NSObject, NSData, NSTimer
from defcon.tools.notifications import NotificationCenter


class OSFontBridgeManager(object):

    def __init__(self, globalActivation=False, reloadDelay=.5):
        self._globalActivation = globalActivation
        self._reloadDelay = reloadDelay
        self._fontToIDNumber = {}
        self._idToTempPath = {}
        self._reloadTimers = {}
        self._bridge = OSFontBridge.alloc().init()
        self._timerTarget = OSFontBridgeManagerTarget.alloc().init()
        self._timerTarget.pythonObject = weakref.ref(self)
        self._notificationCenter = NotificationCenter()
        self._compilingFont = None

    def __del__(self):
        for font in self._fontToIDNumber.keys():
            self._deactivateFont(font)

    # ------------
    # External API
    # ------------

    def addFont(self, font):
        font.addObserver(observer=self, methodName="_fontChanged", notification="Font.Changed")
        self._activateFont(font)

    def removeFont(self, font):
        font.removeObserver(observer=self, notification="Font.Changed")
        self._deactivateFont(font)

    def __contains__(self, font):
        return font in self._fontToIDNumber

    def getNameForFont(self, font):
        id = self._fontToIDNumber[font]
        return self._bridge.getFontNameFromContainer_(id)

    def addObserver(self, observer, callbackString, font):
        self._notificationCenter.addObserver(observer=observer, callbackString=callbackString,
                notification="OSFontBridgeManager.Reload", observable=font)

    def removeObserver(self, observer, font):
        self._notificationCenter.removeObserver(observer=observer, notification="OSFontBridgeManager.Reload",
            observable=font)

    # -------------------
    # Activate/Deactivate
    # -------------------

    def _activateFont(self, font):
        # compile OTF
        fileHandle, tempPath = mkstemp()
        os.close(fileHandle)
        tempPath += ".otf"
        self._compileFont(font, tempPath)
        # deactivate previous version
        if font in self._fontToIDNumber:
            self._deactivateFont(font)
        # load font
        id = self._bridge.activateFontFromPath_isLocal_(tempPath, not self._globalActivation)
        self._fontToIDNumber[font] = id
        self._idToTempPath[id] = tempPath

    def _deactivateFont(self, font):
        id = self._fontToIDNumber[font]
        tempPath = self._idToTempPath[id]
        self._bridge.deactivateFont_(id)
        os.remove(tempPath)
        del self._fontToIDNumber[font]
        del self._idToTempPath[id]

    # -------
    # Compile
    # -------

    def _compileFont(self, font, path):
        # make glyph order
        order = [i for i in MacRoman if i in font]
        order += [i for i in sorted(font.keys()) if i not in order]
        # compile
        c = OSFontBridgeOTFCompiler(font, path, glyphOrder=order)
        c.compile()

    # -------
    # Changes
    # -------

    def _fontChanged(self, notification):
        font = notification.object
        if font in self._reloadTimers:
            t = self._reloadTimers[font]
            t.invalidate()
            del self._reloadTimers[font]
        id = self._fontToIDNumber[font]
        timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            self._reloadDelay, self._timerTarget, "fire:", dict(id=id), False
        )
        self._reloadTimers[font] = timer

    def _reloadFont(self, id):
        for font, otherID in self._fontToIDNumber.items():
            if otherID == id:
                break
        self._activateFont(font)
        self._notificationCenter.postNotification(notification="OSFontBridgeManager.Reload", observable=font)


class OSFontBridgeManagerTarget(NSObject):

    def fire_(self, sender):
        userInfo = sender.userInfo()
        self.pythonObject()._reloadFont(userInfo["id"])



class OSFontBridgeOTFCompiler(OutlineOTFCompiler):

    def makeUnicodeToGlyphNameMapping(self):
        # XXX what should this do about .notdef and space if they are missing?
        unicodeData = self.ufo.unicodeData
        mapping = {}
        for glyphName in self.allGlyphs.keys():
            uni = unicodeData.forcedUnicodeForGlyphName(glyphName)
            mapping[uni] = glyphName
        return mapping

    def setupTable_name(self):
        super(OSFontBridgeOTFCompiler, self).setupTable_name()
        name = self.otf["name"]
        name.names = []
        familyName = self.ufo.info.familyName
        styleName = self.ufo.info.styleName
        t = time.asctime(time.gmtime())
        data = {
            1 : familyName,
            2 : styleName,
            3 : "%s %s:%s" % (familyName, styleName, t),
            4 : "%s %s" % (familyName, styleName),
            6 : ("%s-%s" % (familyName, styleName)).replace(" ", ""),
            5 : "Version 0.0, %s %s Proof Font Time: %s" % (familyName, styleName, t),
        }
        groups = [
            (1, 0, 0),
        ]
        for (pID, eID, lID) in groups:
            for nID, s in sorted(data.items()):
                r = NameRecord()
                r.nameID = nID
                r.platformID = pID
                r.platEncID = eID
                r.langID = lID
                r.string = s
                name.names.append(r)

    def setupTable_OS2(self):
        super(OSFontBridgeOTFCompiler, self).setupTable_OS2()
        # XXX fix the unicode and code page ranges
        os2 = self.otf["OS/2"]
        os2.ulUnicodeRange1 = 0
        os2.ulUnicodeRange2 = 0
        os2.ulUnicodeRange3 = 0
        os2.ulUnicodeRange4 = 0
        os2.ulCodePageRange1 = 0
        os2.ulCodePageRange2 = 0

