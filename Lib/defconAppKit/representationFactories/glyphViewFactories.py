import math
from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.cocoaPen import CocoaPen
from ufoLib.pointPen import AbstractPointPen
from AppKit import NSImage, NSGraphicsContext, NSData, NSCompositeSourceOver
from Quartz import CIColor, CIImage, CIFilter


# -------------
# no components
# -------------

def NoComponentsNSBezierPathFactory(glyph):
    pen = NoComponentsCocoaPen(glyph.layer)
    glyph.draw(pen)
    return pen.path


class NoComponentsCocoaPen(CocoaPen):

    def addComponent(self, glyphName, transformation):
        pass


# ---------------
# only components
# ---------------

def OnlyComponentsNSBezierPathFactory(glyph):
    pen = OnlyComponentsCocoaPen(glyph.layer)
    glyph.draw(pen)
    return pen.path


class OnlyComponentsCocoaPen(BasePen):

    def __init__(self, glyphSet):
        BasePen.__init__(self, glyphSet)
        self.pen = CocoaPen(glyphSet)
        self.path = self.pen.path

    def _moveTo(self, (x, y)):
        pass

    def _lineTo(self, (x, y)):
        pass

    def _curveToOne(self, (x1, y1), (x2, y2), (x3, y3)):
        pass

    def _closePath(self):
        pass

    def addComponent(self, glyphName, transformation):
        try:
            glyph = self.glyphSet[glyphName]
        except KeyError:
            return
        else:
            tPen = TransformPen(self.pen, transformation)
            glyph.draw(tPen)


# ----------
# point data
# ----------

class OutlineInformationPen(AbstractPointPen):

    def __init__(self):
        self._rawPointData = []
        self._rawComponentData = []
        self._bezierHandleData = []

    def getData(self):
        data = dict(startPoints=[], onCurvePoints=[], offCurvePoints=[], bezierHandles=[], anchors=[], components=self._rawComponentData)
        for contour in self._rawPointData:
            # anchor
            if len(contour) == 1 and contour[0]["name"] is not None:
                anchor = contour[0]
                data["anchors"].append(anchor)
            # points
            else:
                haveFirst = False
                for pointIndex, point in enumerate(contour):
                    if point["segmentType"] is None:
                        data["offCurvePoints"].append(point)
                        # look for handles
                        back = contour[pointIndex - 1]
                        forward = contour[(pointIndex + 1) % len(contour)]
                        if back["segmentType"] in ("curve", "line"):
                            p1 = back["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append((p1, p2))
                        elif forward["segmentType"] in ("curve", "line"):
                            p1 = forward["point"]
                            p2 = point["point"]
                            if p1 != p2:
                                data["bezierHandles"].append((p1, p2))
                    else:
                        data["onCurvePoints"].append(point)
                        # catch first point
                        if not haveFirst:
                            haveFirst = True
                            nextOn = None
                            for nextPoint in contour[pointIndex:] + contour[:pointIndex]:
                                # if nextPoint["segmentType"] is None:
                                #    continue
                                if nextPoint["point"] == point["point"]:
                                    continue
                                nextOn = nextPoint
                                break
                            angle = None
                            if nextOn:
                                x1, y1 = point["point"]
                                x2, y2 = nextOn["point"]
                                xDiff = x2 - x1
                                yDiff = y2 - y1
                                angle = round(math.atan2(yDiff, xDiff) * 180 / math.pi, 3)
                            data["startPoints"].append((point["point"], angle))
        return data

    def beginPath(self, identifier=None):
        self._rawPointData.append([])

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation, identifier=None):
        self._rawComponentData.append((baseGlyphName, transformation))


def OutlineInformationFactory(glyph):
    pen = OutlineInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()


# -----
# image
# -----

def NSImageFactory(image):
    font = image.font
    if font is None:
        return
    layer = image.layer
    images = font.images
    if image.fileName not in images:
        return None
    imageColor = image.color
    if imageColor is None:
        imageColor = layer.color
    data = images[image.fileName]
    data = NSData.dataWithBytes_length_(data, len(data))
    if imageColor is None:
        return NSImage.alloc().initWithData_(data)
    # make the input image
    inputImage = CIImage.imageWithData_(data)
    # make a color filter
    r, g, b, a = imageColor
    color0 = CIColor.colorWithRed_green_blue_(r, g, b)
    color1 = CIColor.colorWithRed_green_blue_(1, 1, 1)
    falseColorFilter = CIFilter.filterWithName_("CIFalseColor")
    falseColorFilter.setValue_forKey_(inputImage, "inputImage")
    falseColorFilter.setValue_forKey_(color0, "inputColor0")
    falseColorFilter.setValue_forKey_(color1, "inputColor1")
    # get the result
    ciImage = falseColorFilter.valueForKey_("outputImage")
    # make an NSImage
    nsImage = NSImage.alloc().initWithSize_(ciImage.extent().size)
    nsImage.lockFocus()
    context = NSGraphicsContext.currentContext().CIContext()
    context.drawImage_atPoint_fromRect_(ciImage, (0, 0), ciImage.extent())
    nsImage.unlockFocus()
    # apply the alpha
    finalImage = NSImage.alloc().initWithSize_(nsImage.size())
    finalImage.lockFocus()
    nsImage.drawAtPoint_fromRect_operation_fraction_(
        (0, 0), ((0, 0), nsImage.size()), NSCompositeSourceOver, a
    )
    finalImage.unlockFocus()
    return finalImage
