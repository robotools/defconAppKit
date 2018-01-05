import vanilla
from defconAppKit.tools.textSplitter import splitText


class GlyphSequenceEditText(vanilla.EditText):

    def __init__(self, posSize, font, callback=None, sizeStyle="regular"):
        self._font = font
        self._finalCallback = callback
        super(GlyphSequenceEditText, self).__init__(posSize, callback=self._inputCallback, sizeStyle=sizeStyle)

    def _breakCycles(self):
        self._font = None
        self._finalCallback = None
        super(GlyphSequenceEditText, self)._breakCycles()

    def _inputCallback(self, sender):
        if self._finalCallback is None:
            return
        self._finalCallback(self)

    def get(self):
        text = super(GlyphSequenceEditText, self).get()
        glyphNames = splitText(text, self._font.unicodeData)
        glyphs = [self._font[glyphName] for glyphName in glyphNames if glyphName in self._font]
        return glyphs
