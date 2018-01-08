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
    "^"                                           # start of string
    "(" + "|".join(_keywords.splitlines()) + ")"  # keywords
    "[>\s;(]+"                                    # space, >, ;, (
    "|"                                           # or...
    "[<\s;]+"                                     # space, <, ;
    "(" + "|".join(_keywords.splitlines()) + ")"  # keywords
    "[>\s;(]+"                                    # space, >, ;, (
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


def breakFeatureTextIntoRuns(text):
    runs = []
    # tokens
    runs.append(("tokens", _findRuns(text, _tokenRE)))
    # keywords
    runs.append(("keywords", _findRuns(text, _keywordRE)))
    # class names
    runs.append(("classNames", _findRuns(text, _classNameRE)))
    # includes
    runs.append(("includes", _findRuns(text, _includeRE)))
    # strings
    runs.append(("strings", _findRuns(text, _stringRE)))
    # comments
    runs.append(("comments", _findRuns(text, _commentRE)))
    return runs


def _findRuns(text, pattern):
    runs = []
    offset = 0
    while 1:
        m = pattern.search(text)
        if m is None:
            break
        else:
            start, end = m.span()
            runs.append((start + offset, end + offset))
            offset = offset + end
            text = text[end:]
            if not text:
                break
    return runs


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
