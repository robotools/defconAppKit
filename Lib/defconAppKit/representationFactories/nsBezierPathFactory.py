from AppKit import *
from fontTools.pens.cocoaPen import CocoaPen


def NSBezierPathFactory(glyph, font):
    pen = CocoaPen(font)
    glyph.draw(pen)
    return pen.path