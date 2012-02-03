from defcon import Glyph, Image, registerRepresentationFactory
from defconAppKit.representationFactories.nsBezierPathFactory import NSBezierPathFactory
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactory
from defconAppKit.representationFactories.glyphCellDetailFactory import GlyphCellDetailFactory
from defconAppKit.representationFactories.glyphViewFactories import NoComponentsNSBezierPathFactory,\
    OnlyComponentsNSBezierPathFactory, OutlineInformationFactory, NSImageFactory
from defconAppKit.representationFactories.menuImageFactory import MenuImageRepresentationFactory

_glyphFactories = {
    "defconAppKit.NSBezierPath" : NSBezierPathFactory,
    "defconAppKit.NoComponentsNSBezierPath" : NoComponentsNSBezierPathFactory,
    "defconAppKit.OnlyComponentsNSBezierPath" : OnlyComponentsNSBezierPathFactory,
    "defconAppKit.GlyphCell" : GlyphCellFactory,
    "defconAppKit.GlyphCellDetail" : GlyphCellDetailFactory,
    "defconAppKit.OutlineInformation" : OutlineInformationFactory,
    "defconAppKit.MenuImage" : MenuImageRepresentationFactory,
}
_imageFactories = {
    "defconAppKit.NSImage" : NSImageFactory
}

def registerAllFactories():
    for name, factory in _glyphFactories.items():
        registerRepresentationFactory(Glyph, name, factory, destructiveNotifications=None)
    for name, factory in _imageFactories.items():
        registerRepresentationFactory(Image, name, factory, destructiveNotifications=None)

