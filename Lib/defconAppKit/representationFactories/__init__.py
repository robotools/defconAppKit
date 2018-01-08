from defcon import Glyph, Image, registerRepresentationFactory
from defconAppKit.representationFactories.nsBezierPathFactory import NSBezierPathFactory
from defconAppKit.representationFactories.glyphCellFactory import GlyphCellFactory
from defconAppKit.representationFactories.glyphCellDetailFactory import GlyphCellDetailFactory
from defconAppKit.representationFactories.glyphViewFactories import NoComponentsNSBezierPathFactory,\
    OnlyComponentsNSBezierPathFactory, OutlineInformationFactory, NSImageFactory
from defconAppKit.representationFactories.menuImageFactory import MenuImageRepresentationFactory

_glyphFactories = {
    "defconAppKit.NSBezierPath": (NSBezierPathFactory, None),
    "defconAppKit.NoComponentsNSBezierPath": (NoComponentsNSBezierPathFactory, None),
    "defconAppKit.OnlyComponentsNSBezierPath": (OnlyComponentsNSBezierPathFactory, None),
    "defconAppKit.GlyphCell": (GlyphCellFactory, None),
    "defconAppKit.GlyphCellDetail": (GlyphCellDetailFactory, None),
    "defconAppKit.OutlineInformation": (OutlineInformationFactory, None),
    "defconAppKit.MenuImage": (MenuImageRepresentationFactory, None),
}
_imageFactories = {
    "defconAppKit.NSImage": (NSImageFactory, ["Image.FileNameChanged", "Image.ColorChanged", "Image.ImageDataChanged"])
}

def registerAllFactories():
    for name, (factory, destructiveNotifications) in _glyphFactories.items():
        registerRepresentationFactory(Glyph, name, factory, destructiveNotifications=destructiveNotifications)
    for name, (factory, destructiveNotifications) in _imageFactories.items():
        registerRepresentationFactory(Image, name, factory, destructiveNotifications=destructiveNotifications)
