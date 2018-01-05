from fontTools.pens.cocoaPen import CocoaPen


def NSBezierPathFactory(glyph):
    pen = CocoaPen(glyph.font)
    glyph.draw(pen)
    return pen.path
