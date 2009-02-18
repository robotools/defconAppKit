import re

# -------------------
# Syntax Highlighting
# -------------------

_keywords = """Ascender
Attach
CapHeight
CaretOffset
CodePageRange
Descender
FontRevision
GlyphClassDef
HorizAxis.BaseScriptList
HorizAxis.BaseTagList
HorizAxis.MinMax
IgnoreBaseGlyphs
IgnoreLigatures
IgnoreMarks
LigatureCaretByDev
LigatureCaretByIndex
LigatureCaretByPos
LineGap
MarkAttachClass
MarkAttachmentType
NULL
Panose
RightToLeft
TypoAscender
TypoDescender
TypoLineGap
UnicodeRange
UseMarkFilteringSet
Vendor
VertAdvanceY
VertAxis.BaseScriptList
VertAxis.BaseTagList
VertAxis.MinMax
VertOriginY
VertTypoAscender
VertTypoDescender
VertTypoLineGap
XHeight
anchorDef
anchor
anonymous
anon
by
contour
cursive
device
enumerate
enum
exclude_dflt
featureNames
feature
from
ignore
include_dflt
include
languagesystem
language
lookupflag
lookup
markClass
mark
nameid
name
parameters
position
pos
required
reversesub
rsub
script
sizemenuname
substitute
subtable
sub
table
useExtension
valueRecordDef
winAscent
winDescent"""

_keywordRE = re.compile(
    "[<\s;]+"
    "(" + "|".join(_keywords.splitlines()) + ")"
    "[>\s;(]+"
)


_tokens = """;
,
\
-
=
'
{
}
[
]
<
>
(
)"""

_tokenRE = re.compile(
    "(" + "|".join([re.escape(token) for token in _tokens.splitlines()]) + ")"
)

_commentRE = re.compile(
    "(#.*$)",
    re.MULTILINE
    )

_classNameRE = re.compile(
    "(@[a-zA-Z0-9_.]*)"
    )

_includeRE = re.compile(
    "include\s*\("
    "([^)]+)"
    "\)\s*;"
)

_stringRE = re.compile(
    "(\".*\")"
)

def _findKnownPatterns(text):
    knownPatterns = []
    # comments
    commentCount = len(_commentRE.findall(text))
    if commentCount:
        text = _commentRE.sub("", text)
        knownPatterns.append(dict(pattern=_commentRE, count=commentCount, type="comment"))
    # strings
    stringCount = len(_stringRE.findall(text))
    if stringCount:
        text = _stringRE.sub("", text)
        knownPatterns.append(dict(pattern=_stringRE, count=stringCount, type="string"))
    # includes
    includeCount = len(_includeRE.findall(text))
    if includeCount:
        text = _includeRE.sub("", text)
        knownPatterns.append(dict(pattern=_includeRE, count=includeCount, type="include"))
    # class names
    classNameCount = len(_classNameRE.findall(text))
    if classNameCount:
        text = _classNameRE.sub("", text)
        knownPatterns.append(dict(pattern=_classNameRE, count=classNameCount, type="className"))
    # tokens
    tokenCount = len(_tokenRE.findall(text))
    if tokenCount:
        knownPatterns.append(dict(pattern=_tokenRE, count=tokenCount, type="token"))
    # keywords
    keywordCount = len(_keywordRE.findall(text))
    if keywordCount:
        knownPatterns.append(dict(pattern=_keywordRE, count=keywordCount, type="keyword"))
    return knownPatterns

def breakFeatureTextIntoRuns(text):
    patterns = _findKnownPatterns(text)
    return _breakFeatureTextIntoRuns(text, patterns)

def _breakFeatureTextIntoRuns(text, patterns, offset=0):
    if not text:
        return []
    result = []
    for patternDict in patterns:
        if patternDict["count"] == 0:
            continue
        pattern = patternDict["pattern"]
        m = pattern.search(text)
        if m is not None:
            patternDict["count"] -= 1
            start, end = m.span()
            result.append((offset + start, offset + end, patternDict["type"]))
            # go back
            result = _breakFeatureTextIntoRuns(text[:start], patterns, offset=offset) + result
            # go forward
            result = result + _breakFeatureTextIntoRuns(text[end:], patterns, offset=offset+end)
            break
    return result

# ---------------
# Block Searching
# ---------------

_commentSubRE = re.compile(
    "(#.*)$",
    re.MULTILINE
    )

_blockOpenScanRE = re.compile(
    "([\s;]+)"
    "(feature|table)"
    "\s+"
    "([A-Za-z0-9]+)"
    "\s*"
    "(\{)"
)

_lineEndRE = re.compile("([\r\n]+)", re.MULTILINE)
_notLineEndRE = re.compile("(.*$)")

def findBlockOpenLineStarts(text):
    # remove all comments
    strippedText = _commentSubRE.sub("", text)
    # remove all strings
    strippedText = _stringRE.sub("", strippedText)
    # work through the text
    found = []
    truncatedText = strippedText
    offset = 0
    while True:
        m = _blockOpenScanRE.search(truncatedText)
        if m is None:
            break
        else:
            start, end = m.span()
            start += len(m.group(1))
            truncatedText = truncatedText[end:]
            start += offset
            end += offset
            offset = end
            # get the line number=
            lineBreaks = _lineEndRE.findall(strippedText[:start])
            lineNumber = len("".join(lineBreaks))
            # work out the character position
            lines = text.splitlines()[:lineNumber]
            characters = sum([len(line) for line in lines])
            characterIndex = characters + len("".join(lineBreaks[:len(lines)]))
            # store
            found.append((m.group(3), characterIndex))
    return found

