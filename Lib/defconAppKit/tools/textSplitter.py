def characterToGlyphName(c, cmap):
    try:
        c = unicode(c)
        v = ord(c)
        v = cmap.get(v)
        if isinstance(v, list):
            v = v[0]
        return v
    except UnicodeDecodeError:
        return None

def splitText(text, cmap, fallback=".notdef"):
    """
    Break a string of characters or / delimited glyph names
    into a list.

    - Test name compiling
    >>> splitText("/a", {})
    ['a']
    >>> splitText("/aacute/bbreve", {})
    ['aacute', 'bbreve']
    >>> splitText("/aacute /bbreve", {})
    ['aacute', 'bbreve']

    - Test character input
    >>> splitText("*.", {})
    ['.notdef', '.notdef']
    >>> splitText("*.", {42:"asterisk", 46:"period"})
    ['asterisk', 'period']

    - Test slash escaping
    >>> splitText("//", {})
    ['slash']
    >>> splitText("///", {})
    ['slash']
    >>> splitText("////", {})
    ['slash', 'slash']
    >>> splitText("/ /", {})
    []
    >>> splitText("/ /", {})
    []
    >>> splitText("1//2", {49:"one", 50:"two"})
    ['one', 'slash', 'two']

    - Test mixture
    >>> splitText("*/aacute .%//", {42:"asterisk", 46:"period"})
    ['asterisk', 'aacute', 'period', '.notdef', 'slash']
    """
    # escape //
    text = text.replace("//", "/slash ")
    #
    glyphNames = []
    compileStack = None
    for c in text:
        # start a glyph name compile.
        if c == "/":
            # finishing a previous compile.
            if compileStack is not None:
                # only add the compile if something has been added to the stack.
                if compileStack:
                    glyphNames.append("".join(compileStack))
            # reset the stack.
            compileStack = []
        # adding to or ending a glyph name compile.
        elif compileStack is not None:
            # space. conclude the glyph name compile.
            if c == " ":
                # only add the compile if something has been added to the stack.
                if compileStack:
                    glyphNames.append("".join(compileStack))
                compileStack = None
            # add the character to the stack.
            else:
                compileStack.append(c)
        # adding a character that needs to be converted to a glyph name.
        else:
            glyphName = characterToGlyphName(c, cmap)
            if glyphName is None:
                glyphName = fallback
            glyphNames.append(glyphName)
    # catch remaining compile.
    if compileStack is not None and compileStack:
        glyphNames.append("".join(compileStack))
    return glyphNames

if __name__ =="__main__":
    import doctest
    doctest.testmod()
