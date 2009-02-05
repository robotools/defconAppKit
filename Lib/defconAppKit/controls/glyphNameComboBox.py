from AppKit import *
import vanilla


class GlyphNameComboBox(vanilla.EditText):

    def __init__(self, posSize, font, callback=None, sizeStyle="regular"):
        super(GlyphNameComboBox, self).__init__(posSize, callback=self._textInputCallback, sizeStyle=sizeStyle)
        self._font = font
        self._finalCallback = callback
        self._currentText = ""

    def _breakCycles(self):
        self._font = None
        self._finalCallback = None
        super(GlyphNameComboBox, self)._breakCycles()

    def _textInputCallback(self, sender):
        input = sender.get()
        deleting = False
        if len(input) <= len(self._currentText):
            if self._currentText.startswith(input):
                deleting = True
        self._currentText = input
        input, match = _search(input, self._font, deleting=deleting)
        if match is None:
            return
        if match != input:
            self.set(match)
            selectionStart = len(input)
            selectionLength = len(match) - selectionStart
            textField = self._nsObject
            window = textField.window()
            fieldEditor = window.fieldEditor_forObject_(True, textField)
            if not deleting:
                fieldEditor.setSelectedRange_((selectionStart, selectionLength))
        if self._finalCallback is not None:
            self._finalCallback(self)


def _search(text, font, deleting):
    """
    >>> from fontTools.agl import AGL2UV
    >>> from defcon import Font
    >>> font = Font()
    >>> for glyphName, value in AGL2UV.items():
    ...     font.newGlyph(glyphName)
    ...     font[glyphName].unicodes = [value]
    ...     font.newGlyph(glyphName + ".alt")
    ...     font.newGlyph(glyphName + ".xxx")

    >>> _search("e", font, False)
    ('e', 'e')
    >>> _search("eg", font, False)
    ('eg', 'egrave')
    >>> _search("e.", font, False)
    ('e.', 'e.alt')

    >>> _search("eight.al", font, True)
    ('eight.al', 'eight')
    """
    # no text
    if not text:
        return text, None
    glyphNames = font.keys()
    match = None
    # direct match
    if text in glyphNames:
        match = text
    # character entry
    elif len(text) == 1:
        uniValue = ord(text)
        match = font.unicodeData.glyphNameForUnicode(uniValue)
        if match is not None:
            text = ""
    # fallback. find closest match
    if match is None:
        glyphNames = list(sorted(glyphNames))
        if not deleting:
            for glyphName in glyphNames:
                if glyphName.startswith(text):
                    match = glyphName
                    break
        else:
            matches = []
            for glyphName in glyphNames:
                if text.startswith(glyphName):
                    matches.append(glyphName)
                elif match is not None:
                    break
            diff = None
            for m in matches:
                d = len(m) - len(text)
                if diff is None or d < diff:
                    match = m
    return text, match


if __name__ == "__main__":
    import doctest
    doctest.testmod()
