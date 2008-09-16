from fontTools.pens.basePen import BasePen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.cocoaPen import CocoaPen
from robofab.pens.pointPen import AbstractPointPen


# -------------
# no components
# -------------

def NoComponentsNSBezierPathFactory(glyph, font):
    pen = NoComponentsCocoaPen(font)
    glyph.draw(pen)
    return pen.path

class NoComponentsCocoaPen(CocoaPen):

    def addComponent(self, glyphName, transformation):
        pass


# ---------------
# only components
# ---------------

def OnlyComponentsNSBezierPathFactory(glyph, font):
    pen = OnlyComponentsCocoaPen(font)
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
            pass
        else:
            tPen = TransformPen(self.pen, transformation)
            glyph.draw(self.pen)


# ----------
# point data
# ----------

class OutlineInformationPen(AbstractPointPen):

    def __init__(self):
        self._rawPointData = []
        self._rawComponentData = []

    def getData(self):
        data = dict(onCurvePoints=[], offCurvePoints=[], anchors=[], components=self._rawComponentData)
        for contour in self._rawPointData:
            # anchor
            if len(contour) == 1:
                anchor = contour[0]
                data["anchors"].append(anchor)
            # points
            else:
                for point in contour:
                    if point["segmentType"] is None:
                        data["offCurvePoints"].append(point)
                    else:
                        data["onCurvePoints"].append(point)
        return data

    def beginPath(self):
        self._rawPointData.append([])

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        d = dict(point=pt, segmentType=segmentType, smooth=smooth, name=name)
        self._rawPointData[-1].append(d)

    def addComponent(self, baseGlyphName, transformation):
        d = dict(baseGlyphName=baseGlyphName, transformation=transformation)
        self._rawComponentData.append((baseGlyphName, transformation))


def OutlineInformationFactory(glyph, font):
    pen = OutlineInformationPen()
    glyph.drawPoints(pen)
    return pen.getData()

