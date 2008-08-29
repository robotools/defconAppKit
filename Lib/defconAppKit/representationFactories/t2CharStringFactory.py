from ufo2fdk.charstringPen import T2CharStringPen


def T2CharStringRepresentationFactory(glyph, font):
    pen = T2CharStringPen(glyph.width, font)
    glyph.draw(pen)
    return pen.getCharString()
