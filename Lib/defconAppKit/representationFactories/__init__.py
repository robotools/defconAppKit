from defcon.objects.glyph import addRepresentationFactory
from defconAppKit.representationFactories.nsBezierPathFactory import NSBezierPathFactory
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactory
from defconAppKit.representationFactories.glyphCellDetailFactory import GlyphCellDetailFactory


def registerAllFactories():
    addRepresentationFactory("NSBezierPath", NSBezierPathFactory)
    addRepresentationFactory("defconAppKitGlyphCell", GlyphCellFactory)
    addRepresentationFactory("defconAppKitGlyphCellDetail", GlyphCellDetailFactory)