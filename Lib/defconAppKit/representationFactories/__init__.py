from defcon.objects.glyph import addRepresentationFactory
from defconAppKit.representationFactories.nsBezierPathFactory import NSBezierPathFactory
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactory
from defconAppKit.representationFactories.glyphCellDetailFactory import GlyphCellDetailFactory
from defconAppKit.representationFactories.glyphViewFactories import NoComponentsNSBezierPathFactory, OnlyComponentsNSBezierPathFactory, OutlineInformationFactory

_factories = {
    "NSBezierPath" : NSBezierPathFactory,
    "NoComponentsNSBezierPath" : NoComponentsNSBezierPathFactory,
    "OnlyComponentsNSBezierPath" : OnlyComponentsNSBezierPathFactory,
    "defconAppKitGlyphCell" : GlyphCellFactory,
    "defconAppKitGlyphCellDetail" : GlyphCellDetailFactory,
    "defconAppKitOutlineInformation" : OutlineInformationFactory
}

# used by the glyph multiline view
try:
    from defconAppKit.representationFactories.t2CharStringFactory import T2CharStringRepresentationFactory
    _factories["T2CharString"] = T2CharStringRepresentationFactory
except ImportError:
    pass


def registerAllFactories():
    for name, factory in _factories.items():
        addRepresentationFactory(name, factory)