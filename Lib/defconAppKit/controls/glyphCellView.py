import time
import objc
from objc import super
from AppKit import NSColor, NSShadow, NSImage, NSGraphicsContext, NSBezierPath, NSAffineTransform, \
    NSObject, NSInsetRect, NSView, NSNotificationCenter, NSViewFrameDidChangeNotification, NSIndexSet, \
    NSPasteboard, NSUpArrowFunctionKey, NSLeftArrowFunctionKey, NSDownArrowFunctionKey, NSShiftKeyMask, \
    NSDragOperationGeneric, NSCommandKeyMask, NSControlKeyMask, NSPointInRect, NSDragOperationCopy, NSWindowDidResignKeyNotification, \
    NSDragOperationNone, NSString, NSBackspaceCharacter, NSDeleteFunctionKey, NSDeleteCharacter, NSKeyValueObservingOptionNew, \
    NSMutableIndexSet, NSWindowWillCloseNotification, NSDragPboard, NSRectFill, NSEvent, NSApp, NSRightArrowFunctionKey, \
    NSHomeFunctionKey, NSBeginFunctionKey, NSPageUpFunctionKey, NSPageDownFunctionKey, NSIntersectsRect, \
    NSCompositeSourceOver, NSCompositeMultiply, NSRectFillUsingOperation, NSAlternateKeyMask, NSEndFunctionKey

from math import ceil, floor
import vanilla
from objc import python_method
from defconAppKit.tools.iconCountBadge import addCountBadgeToIcon
from defconAppKit.windows.popUpWindow import InformationPopUpWindow, HUDTextBox, HUDHorizontalLine


def _makeGlyphCellDragIcon(glyphs):
    font = None
    glyphRepresentation = None
    glyphWidth = None
    for glyph in glyphs:
        rep = glyph.getRepresentation("defconAppKit.NSBezierPath")
        if not rep.isEmpty():
            font = glyph.getParent()
            glyphRepresentation = rep
            glyphWidth = glyph.width
            break
    # set up the image
    iconImage = NSImage.alloc().initWithSize_((40, 40))
    iconImage.lockFocus()
    context = NSGraphicsContext.currentContext()
    # draw the page base
    pageSize = 35
    pagePath = NSBezierPath.bezierPath()
    pagePath.moveToPoint_((.5, 5.5))
    pagePath.lineToPoint_((.5, 39.5))
    pagePath.lineToPoint_((34.5, 39.5))
    pagePath.lineToPoint_((34.5, 5.5))
    pagePath.lineToPoint_((.5, 5.5))
    # set the shadow
    context.saveGraphicsState()
    shadow = NSShadow.alloc().init()
    shadow.setShadowOffset_((1, -1))
    shadow.setShadowColor_(NSColor.blackColor())
    shadow.setShadowBlurRadius_(2.0)
    shadow.set()
    # fill the page
    NSColor.whiteColor().set()
    pagePath.fill()
    try:
        color1 = NSColor.colorWithCalibratedWhite_alpha_(.95, 1)
        color2 = NSColor.colorWithCalibratedWhite_alpha_(.85, 1)
        gradient = NSGradient.alloc().initWithColors_([color1, color2])
        gradient.drawInBezierPath_angle_(pagePath, -90)
    except NameError:
        pass
    # remove the shadow
    context.restoreGraphicsState()
    # draw the glyph
    if glyphRepresentation is not None:
        context.saveGraphicsState()
        buffer = pageSize * .125
        upm = font.info.unitsPerEm
        scale = (pageSize - buffer - buffer) / float(upm)
        xOffset = ((pageSize * (1.0 / scale)) - glyphWidth) / 2
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(0, 5 + buffer)
        transform.scaleBy_(scale)
        transform.translateXBy_yBy_(xOffset, -font.info.descender)
        transform.concat()
        NSColor.colorWithCalibratedWhite_alpha_(0, .8).set()
        # XXX should clip the glyph path here to prevent overflow
        glyphRepresentation.fill()
        context.restoreGraphicsState()
    # draw the page border
    NSColor.grayColor().set()
    pagePath.stroke()
    # done
    iconImage.unlockFocus()
    # add the count badge
    return addCountBadgeToIcon(len(glyphs), iconImage)


class nsCallbackWrapper(object):
    """
    A wrapper for a ns object callback.
    """
    def __init__(self, ref):
        self._ref = ref

    def action(self, sender):
        return self._ref(sender)


class GlyphCellItem(NSObject):

    def __new__(cls, *args, **kwargs):
        return cls.alloc().init()

    def __init__(self, glyphName, font):
        self._glyphName = glyphName
        self._font = font
        self._glyph = None

    def dealloc(self):
        self._font = None
        self._glyph = None
        super(GlyphCellItem, self).dealloc()

    def glyph(self):
        if self._glyph is None:
            self._glyph = self._font[self._glyphName]
            self._font = None
        return self._glyph

    def setGlyphExternally_(self, glyph):
        self._glyphName = glyph.name
        self._glyph = glyph
        self._font = None

    # api

    def __getitem__(self, key):
        # fallback when the vanilla list is thinking this object is a dict
        if key == "_glyph":
            print("GlyphCollection item '_glyph' is deprecated use item.glyph()")
            return self.glyph()
        raise NotImplementedError

    def item(self):
        # fallback when no column descriptions are given
        return self.Name()

    def Name(self):
        return self._glyphName

    def setName_(self, value):
        self.glyph().name = self._glyphName = value

    def renameGlyphName_(self, glyphName):
        self._glyphName = glyphName


class DefconAppKitGlyphCellNSView(NSView):

    nsArrayControllerClass = vanilla.vanillaList.VanillaArrayController

    gridColor = backgroundColor = NSColor.colorWithCalibratedWhite_alpha_(.6, 1.0)
    selectionColor = NSColor.selectedControlColor()
    insertionLocationColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.16, .3, .85, 1)
    insertionLocationShadowColor = NSColor.whiteColor()

    def initWithFont_cellRepresentationName_detailWindowClass_(self, font, cellRepresentationName, detailWindowClass):
        self = super(DefconAppKitGlyphCellNSView, self).initWithFrame_(((0, 0), (400, 400)))
        self._cellRepresentationName = cellRepresentationName
        self._cellRepresentationArguments = {}

        self.arrayController = self.nsArrayControllerClass.alloc().init()
        self.arrayController.setSelectsInsertedObjects_(False)
        self.arrayController.setAvoidsEmptySelection_(False)

        self.arrayController.addObserver_forKeyPath_options_context_(self, "arrangedObjects", NSKeyValueObservingOptionNew, 0)

        self._glyphNames = []
        self._subscribedGlyphs = {}
        self._font = font
        self.subscribeFont()

        self._cellWidth = 60
        self._cellHeight = 60
        self._columnCount = 0
        self._rowCount = 0
        self._currentSelection = None

        self._clickRectsToIndex = {}
        self._indexToClickRects = {}

        self._lastSelectionFound = None
        self._lastKeyInputTime = None

        self._allowDrag = False
        self._dropTargetBetween = None
        self._dropTargetOn = None
        self._dropTargetSelf = False

        self._glyphDetailWindowClass = detailWindowClass
        self._glyphDetailWindow = None
        self._glyphDetailRequiredModifiers = [NSControlKeyMask]
        self._glyphDetailOnMouseDown = True
        self._glyphDetailOnMouseUp = False
        self._glyphDetailOnMouseDragged = True
        self._glyphDetailOnMouseMoved = False

        self._havePreviousMouseDown = False
        self._windowIsClosed = False

        self.insertionLocationShadow = NSShadow.shadow()
        self.insertionLocationShadow.setShadowColor_(self.insertionLocationShadowColor)
        self.insertionLocationShadow.setShadowBlurRadius_(10)
        self.insertionLocationShadow.setShadowOffset_((0, 0))

        return self

    # --------------
    # custom methods
    # --------------

    def setAllowsDrag_(self, value):
        self._allowDrag = value

    def getGlyphsAtIndexes_(self, indexes):
        return [self._font[glyphName] for glyphName in self.getGlyphNamesAtIndexes_(indexes)]

    def getGlyphNamesAtIndexes_(self, indexes):
        return [self._glyphNames[i] for i in indexes]

    def setFont_(self, font):
        self.unSubscribeFont()
        self._font = font
        self.subscribeFont()
        self.recalculateFrame()

    def getFont(self):
        return self._font

    def getGlyph_(self, glyphName):
        if glyphName in self._font:
            return self._font[glyphName]
        return None

    def setCellSize_(self, wh):
        w, h = wh
        self._cellWidth = w
        self._cellHeight = h
        self.recalculateFrame()

    def getCellSize(self):
        return self._cellWidth, self._cellHeight

    def getCellRepresentationName(self):
        return self._cellRepresentationName

    def setCellRepresentationArguments_(self, kwargs):
        self._cellRepresentationArguments = kwargs
        self.setNeedsDisplay_(True)

    def getCellRepresentationArguments(self):
        return dict(self._cellRepresentationArguments)

    def getRepresentationForGlyph_cellRepresentationName_cellRepresentationArguments_(self, glyph, representationName, representationArguments):
        return glyph.getRepresentation(representationName, **representationArguments)

    def preloadGlyphCellImages(self):
        representationName = self._cellRepresentationName
        representationArguments = self._cellRepresentationArguments
        representationArguments["width"] = self._cellWidth
        representationArguments["height"] = self._cellHeight
        for glyphName in self._glyphNames:
            glyph = self._font[glyphName]
            self.getRepresentationForGlyph_cellRepresentationName_cellRepresentationArguments_(glyph, representationName, representationArguments)

    def setGlyphDetailModifiers_mouseDown_mouseUp_mouseDragged_mouseMoved_(self,
            modifiers=[], mouseDown=False, mouseUp=False, mouseDragged=False, mouseMoved=False):
        """
        Set the conditions that will be used to determine the visibility of the detail window.
        This is subject to change, so use it at your own risk.
        """
        self._glyphDetailRequiredModifiers = modifiers
        self._glyphDetailOnMouseDown = mouseDown
        self._glyphDetailOnMouseUp = mouseUp
        self._glyphDetailOnMouseDragged = mouseDragged
        self._glyphDetailOnMouseMoved = mouseMoved

    def glyphDetailWindow(self):
        if self._glyphDetailWindow is None and self._glyphDetailWindowClass is not None:
            self._setupGlyphDetailWindow()
        return self._glyphDetailWindow

    def _setupGlyphDetailWindow(self):
        if self._glyphDetailWindow is None and self._glyphDetailWindowClass is not None and self.window() is not None:
            screen = self.window().screen()
            self._glyphDetailWindow = self._glyphDetailWindowClass(screen=screen)
            window = self.window()
            # try to add it to the document so that
            # it can be released when the document is closed.
            windowController = window.windowController()
            if windowController is not None:
                document = windowController.document()
                if document is not None:
                    document.addWindowController_(self._glyphDetailWindow.getNSWindowController())

    # ------------------
    # font nofitications
    # ------------------

    def subscribeFont(self):
        if self._font is not None:
            self.__fontInfoCallbackWrapper = nsCallbackWrapper(self._fontInfoChanged)
            self._font.info.addObserver(self.__fontInfoCallbackWrapper, "action", "Info.Changed")

    def unSubscribeFont(self):
        if self._font is not None:
            self._font.info.removeObserver(self.__fontInfoCallbackWrapper, "Info.Changed")
            del self.__fontInfoCallbackWrapper

    @python_method
    def subscribeGlyph(self, glyph):
        if glyph not in self._subscribedGlyphs:
            glyphNameChangedCallbackWrapper = nsCallbackWrapper(self._glyphNameChanged)
            glyphChangedCallbackWrapper = nsCallbackWrapper(self._glyphChanged)
            self._subscribedGlyphs[glyph] = (glyphNameChangedCallbackWrapper, glyphChangedCallbackWrapper)
            glyph.addObserver(glyphNameChangedCallbackWrapper, "action", "Glyph.NameChanged")
            glyph.addObserver(glyphChangedCallbackWrapper, "action", "Glyph.Changed")

    @python_method
    def unSubscribeGlyph(self, glyph):
        if glyph in self._subscribedGlyphs:
            glyphNameChangedCallbackWrapper, glyphChangedCallbackWrapper = self._subscribedGlyphs[glyph]
            glyph.removeObserver(glyphNameChangedCallbackWrapper, "Glyph.NameChanged")
            glyph.removeObserver(glyphChangedCallbackWrapper, "Glyph.Changed")
            del self._subscribedGlyphs[glyph]

    def unSubscribeGlyphs(self):
        glyphs = self._subscribedGlyphs.keys()
        for glyph in list(glyphs):
            self.unSubscribeGlyph(glyph)

    @python_method
    def _fontInfoChanged(self, notification):
        repWidth, repHeight = self.getCellSize()
        repArgs = self.getCellRepresentationArguments()
        repArgs["width"] = repWidth
        repArgs["height"] = repHeight
        repName = self.getCellRepresentationName()
        for glyph in self._subscribedGlyphs:
            glyph.destroyRepresentation(repName, **repArgs)
        self.setNeedsDisplay_(True)

    @python_method
    def _glyphNameChanged(self, notification):
        data = notification.data
        oldName = data["oldValue"]
        newName = data["newValue"]
        index = self._glyphNames.index(oldName)
        self._glyphNames[index] = newName
        items = self.arrayController.arrangedObjects()
        items[index].renameGlyphName_(newName)
        self.setNeedsDisplay_(True)

    @python_method
    def _glyphChanged(self, notification):
        glyph = notification.object
        if glyph.name not in self._glyphNames:
            return
        self.setNeedsDisplay_(True)
    # --------------
    # NSView methods
    # --------------

    def dealloc(self):
        self.unSubscribeFont()
        self.unSubscribeGlyphs()
        self.unsubscribeFromWindow()
        self._glyphNames = None
        self._subscribedGlyphs = None
        self._font = None
        super(DefconAppKitGlyphCellNSView, self).dealloc()

    def isFlipped(self):
        return True

    def acceptsFirstResponder(self):
        return True

    # def preservesContentDuringLiveResize(self):
    #     return False

    def allowsVibrancy(self):
        return False

    def viewDidMoveToWindow(self):
        if self.window() is not None:
            self.subscribeToWindow()
            self.subscribeToScrollViewFrameChange()
            self.recalculateFrame()

    # window resize notification support

    def clipViewFrameChangeNotification_(self, notification):
        self.recalculateFrame()

    def subscribeToScrollViewFrameChange(self):
        scrollView = self.enclosingScrollView()
        if scrollView is not None:
            notificationCenter = NSNotificationCenter.defaultCenter()
            notificationCenter.addObserver_selector_name_object_(
                self, "clipViewFrameChangeNotification:", NSViewFrameDidChangeNotification, scrollView
            )
            scrollView.setPostsFrameChangedNotifications_(True)

    def viewDidEndLiveResize(self):
        self.recalculateFrame()

    # close notification support

    def windowResignMainNotification_(self, notification):
        self._handleDetailWindow(None, None)

    def windowCloseNotification_(self, notification):
        self._windowIsClosed = True
        if self._glyphDetailWindow is not None:
            if self._glyphDetailWindow.getNSWindow() is not None:
                self._glyphDetailWindow.hide()
                self._glyphDetailWindow.getNSWindow().orderOut_(None)
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_(self)

    def subscribeToWindow(self):
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.addObserver_selector_name_object_(
            self, "windowResignMainNotification:", NSWindowDidResignKeyNotification, self.window()
        )
        notificationCenter.addObserver_selector_name_object_(
            self, "windowCloseNotification:", NSWindowWillCloseNotification, self.window()
        )

    def unsubscribeFromWindow(self):
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_name_object_(self, NSWindowDidResignKeyNotification, self.window())
        notificationCenter.removeObserver_name_object_(self, NSWindowWillCloseNotification, self.window())

    def scrollWheel_(self, event):
        super(DefconAppKitGlyphCellNSView, self).scrollWheel_(event)

    def observeValueForKeyPath_ofObject_change_context_(self, keyPath, obj, change, context):
        if keyPath == "arrangedObjects":
            self._glyphNames = [item.Name() for item in obj.arrangedObjects()]
            self.recalculateFrame()

    def recalculateFrame(self):
        superview = self.superview()
        if superview is None:
            return
        width, height = superview.frame().size
        if width == 0 or height == 0:
            return
        if self._glyphNames:
            columnCount = int(floor(width / self._cellWidth))
            if columnCount == 0:
                columnCount = 1
            rowCount = len(self._glyphNames) / float(columnCount)
            rowCount = int(ceil(rowCount))
            if columnCount * rowCount < len(self._glyphNames):
                rowCount += 1
            newWidth = self._cellWidth * columnCount
            newHeight = self._cellHeight * rowCount
        else:
            columnCount = 0
            rowCount = 0
            newWidth = newHeight = 0
        if width > newWidth:
            newWidth = width
        if height > newHeight:
            newHeight = height
        self._clickRectsToIndex = {}
        self._indexToClickRects = {}
        self.setFrame_(((0, 0), (newWidth, newHeight)))
        self._columnCount = columnCount
        self._rowCount = rowCount
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        if self._font is None:
            return
        self.backgroundColor.set()
        NSRectFill(rect)

        cellWidth = self._cellWidth
        cellHeight = self._cellHeight
        width, height = self.frame().size

        representationName = self._cellRepresentationName
        representationArguments = self._cellRepresentationArguments
        representationArguments["width"] = cellWidth
        representationArguments["height"] = cellHeight

        visibleStart = int(floor(rect.origin.y / cellHeight))
        visibleRows = int(ceil(rect.size.height / cellHeight)) + 1

        startIndex = visibleStart * self._columnCount
        endIndex = startIndex + visibleRows * self._columnCount

        selection = self.arrayController.selectionIndexes()

        left = 0
        top = cellHeight * visibleStart + cellHeight
        index = startIndex
        for glyphName in self._glyphNames[startIndex:endIndex]:
            t = top - cellHeight
            cellRect = ((left, t), (cellWidth, cellHeight))

            self._clickRectsToIndex[cellRect] = index
            self._indexToClickRects[index] = cellRect

            if NSIntersectsRect(rect, cellRect):
                glyph = self.getGlyph_(glyphName)
                if glyph is not None:
                    self.subscribeGlyph(glyph)
                    image = self.getRepresentationForGlyph_cellRepresentationName_cellRepresentationArguments_(glyph, representationName, representationArguments)
                    image.drawAtPoint_fromRect_operation_fraction_(
                        (left, t), ((0, 0), (cellWidth, cellHeight)), NSCompositeSourceOver, 1.0
                    )
                if selection.containsIndex_(index):
                    r = ((left, t), (cellWidth, cellHeight))
                    self.selectionColor.set()
                    NSRectFillUsingOperation(r, NSCompositeMultiply)

            index += 1
            left += cellWidth
            if left + cellWidth > width:
                left = 0
                top += cellHeight

        # lines
        path = NSBezierPath.bezierPath()

        startRow = floor(rect.origin.y / cellHeight)
        endRow = ceil((rect.origin.y + rect.size.height) / cellHeight)
        startColumn = floor(rect.origin.x / cellWidth)
        endColumn = ceil((rect.origin.x + rect.size.width) / cellWidth)

        for i in range(startRow, endRow + 1):
            top = (i * cellHeight) - .5
            path.moveToPoint_((startColumn * cellWidth, top))
            path.lineToPoint_((endColumn * cellWidth, top))

        for i in range(startColumn, endColumn + 1):
            left = (i * cellWidth) - .5
            path.moveToPoint_((left, startRow * cellHeight))
            path.lineToPoint_((left, endRow * cellHeight))



        # startRow = math.floor(r.origin.y / cellHeight)
        # endRow = math.ceil((r.origin.y + r.size.height) / cellHeight)
        # for i in range(startRow, endRow + 1):
        #     top = (i * cellHeight) - .5
        #     path.moveToPoint_((0, top))
        #     path.lineToPoint_((width, top))
        # for i in range(1, int(self._columnCount) + 1):
        #     left = (i * cellWidth) - .5
        #     path.moveToPoint_((left, 0))
        #     path.lineToPoint_((left, height))
        self.gridColor.set()
        path.setLineWidth_(1.0)
        path.stroke()

        # drop insertion position
        if self._dropTargetBetween is not None or self._dropTargetOn is not None or self._dropTargetSelf:
            # drop on a cell
            if self._dropTargetOn:
                cellRect = self._indexToClickRects[self._dropTargetOn]
                cellRect = NSInsetRect(cellRect, 1, 1)
                path = NSBezierPath.bezierPathWithRect_(cellRect)
                path.setLineWidth_(2)
                self.insertionLocationColor.set()
                path.stroke()
            # drop between cells
            elif self._dropTargetBetween:
                location1, location2 = self._dropTargetBetween
                location1 = self._indexToClickRects.get(location1)
                location2 = self._indexToClickRects.get(location2)
                if location1 is None:
                    (x, y), (w, h) = location2
                    barPositions = [(x, y, h)]
                elif location2 is None:
                    (x, y), (w, h) = location1
                    barPositions = [(x, y, h)]
                else:
                    (x1, y1), (w1, h1) = location1
                    (x2, y2), (w2, h2) = location2
                    if y1 == y2:
                        barPositions = [(x2, y2, h2)]
                    else:
                        barPositions = [(x1 + w1, y1, h1), (x2, y2, h2)]
                for (x, y, h) in barPositions:
                    path = NSBezierPath.bezierPath()
                    path.appendBezierPathWithRect_(((x - 2, y), (3, h)))
                    path.appendBezierPathWithOvalInRect_(((x - 5, y - 5), (9, 9)))
                    path.appendBezierPathWithOvalInRect_(((x - 5, y + h - 5), (9, 9)))
                    self.insertionLocationShadow.set()
                    path.setLineWidth_(2)
                    NSColor.whiteColor().set()
                    path.stroke()
                    self.insertionLocationColor.set()
                    path.fill()
            # drop on view
            else:
                visibleRect = self.visibleRect()
                path = NSBezierPath.bezierPathWithRect_(visibleRect)
                path.setLineWidth_(6)
                self.insertionLocationColor.set()
                self.insertionLocationShadow.set()
                path.stroke()

    # ---------
    # Selection
    # ---------

    @python_method
    def _linearSelection(self, index, selection=None):
        if selection is None:
            selection = NSMutableIndexSet.alloc().initWithIndexSet_(self.arrayController.selectionIndexes())
        contains = selection.containsIndex_(index)
        if contains:
            return
        elif selection.count() == 0:
            selection.addIndex_(index)
        else:
            if index < self._lastSelectionFound:
                s = index
                c = self._lastSelectionFound - index + 1
            else:
                s = self._lastSelectionFound
                c = index - self._lastSelectionFound + 1
            selection.addIndexesInRange_((s, c))

    def scrollToCell_(self, index):
        if index not in self._indexToClickRects:
            top = (index // self._columnCount) * self._cellHeight
            left = (index % self._columnCount) * self._cellWidth
            rect = ((left, top), (self._cellWidth, self._cellHeight))
            self._clickRectsToIndex[rect] = index
            self._indexToClickRects[index] = rect
        else:
            rect = self._indexToClickRects[index]
        self.scrollRectToVisible_(rect)

    @python_method
    def rectForIndex(self, index):
        top = (index // self._columnCount) * self._cellHeight
        left = (index % self._columnCount) * self._cellWidth
        rect = ((left, top), (self._cellWidth, self._cellHeight))
        self._clickRectsToIndex[rect] = index
        self._indexToClickRects[index] = rect
        return rect

    # mouse

    def mouseDown_(self, event):
        self._havePreviousMouseDown = True
        found = self._findGlyphForEvent(event)
        self._currentSelection = self.arrayController.selectionIndexes()
        self._mouseSelection(event, found, mouseDown=True)
        self._currentSelection = self.arrayController.selectionIndexes()
        self._lastSelectionFound = found
        self._handleDetailWindow(event, found, mouseDown=True)
        if event.clickCount() > 1:
            vanillaWrapper = self.vanillaWrapper()
            if vanillaWrapper._doubleClickCallback is not None:
                vanillaWrapper._doubleClickCallback(vanillaWrapper)
        self.autoscroll_(event)

    def mouseDragged_(self, event):
        found = self._findGlyphForEvent(event)
        self._mouseSelection(event, found, mouseDragged=True)
        self._currentSelection = self.arrayController.selectionIndexes()
        self._lastSelectionFound = found
        self._handleDetailWindow(event, found, mouseDragged=True)
        self.autoscroll_(event)
        # mouseUp is not called if a drag has begun.
        # so, kill the flag now if the conditions
        # for drag and drop are right
        if self._allowDrag:
            modifiers = event.modifierFlags()
            shiftDown = modifiers & NSShiftKeyMask
            commandDown = modifiers & NSCommandKeyMask
            controlDown = modifiers & NSControlKeyMask
            if not commandDown and not shiftDown and not controlDown:
                self._havePreviousMouseDown = False

    def mouseMoved_(self, event):
        found = self._findGlyphForEvent(event)
        self._handleDetailWindow(event, found, mouseMoved=True)

    def mouseUp_(self, event):
        if self._havePreviousMouseDown:
            found = self._findGlyphForEvent(event)
            self._mouseSelection(event, found, mouseUp=True)
            self._handleDetailWindow(event, found, mouseUp=True)
            self._currentSelection = None
            self._havePreviousMouseDown = False

    @python_method
    def _findGlyphForEvent(self, event):
        eventLocation = event.locationInWindow()
        mouseLocation = self.convertPoint_fromView_(eventLocation, None)
        return self._findGlyphForLocation(mouseLocation)

    @python_method
    def _findGlyphForLocation(self, location):
        found = None
        for rect, index in self._clickRectsToIndex.items():
            if NSPointInRect(location, rect):
                found = index
                break
        return found

    @python_method
    def _handleDetailWindow(self, event, found, mouseDown=False, mouseMoved=False, mouseDragged=False, mouseUp=False, inDragAndDrop=False):
        # no window
        if self._windowIsClosed:
            return
        glyphDetailWindow = self.glyphDetailWindow()
        if glyphDetailWindow is None:
            return
        # determine show/hide
        shouldBeVisible = True
        # event is None
        if event is None:
            shouldBeVisible = False
        # window is not key
        elif NSApp().keyWindow() != self.window():
            shouldBeVisible = False
        # XXX work around an issue that causes mouseDragged
        # to be called after a drop from the view has occurred
        # outside of the view.
        elif mouseDragged and not glyphDetailWindow.isVisible():
            shouldBeVisible = False
        # event requirements
        else:
            eventLocation = event.locationInWindow()
            mouseLocation = self.convertPoint_fromView_(eventLocation, None)
            # drag and drop
            if inDragAndDrop:
                shouldBeVisible = False
            # modifiers
            modifiers = event.modifierFlags()
            for modifier in self._glyphDetailRequiredModifiers:
                if not modifiers & modifier:
                    shouldBeVisible = False
                    break
            # mouse conditions
            haveMouseCondition = False
            requireMouseCondition = True in (self._glyphDetailOnMouseDown, self._glyphDetailOnMouseUp, self._glyphDetailOnMouseMoved, self._glyphDetailOnMouseDragged)
            if not requireMouseCondition:
                haveMouseCondition = True
            else:
                if self._glyphDetailOnMouseDown and mouseDown:
                    haveMouseCondition = True
                elif self._glyphDetailOnMouseUp and mouseUp:
                    haveMouseCondition = True
                elif self._glyphDetailOnMouseMoved and mouseMoved:
                    haveMouseCondition = True
                elif self._glyphDetailOnMouseDragged and mouseDragged:
                    haveMouseCondition = True
            if not haveMouseCondition:
                shouldBeVisible = False
            # glyph hit
            if found is None:
                shouldBeVisible = False
            # mouse position is visible
            if not NSPointInRect(mouseLocation, self.visibleRect()):
                shouldBeVisible = False
        # set the position
        if shouldBeVisible:
            detailX, detailY = self.window().convertBaseToScreen_(eventLocation)
            glyphName = self._glyphNames[found]
            glyphDetailWindow.setPositionNearCursor((detailX, detailY))
            glyphDetailWindow.set(self._font[glyphName])
            if not glyphDetailWindow.isVisible():
                glyphDetailWindow.show()
        else:
            glyphDetailWindow.hide()

    @python_method
    def _mouseSelection(self, event, found, mouseDown=False, mouseDragged=False, mouseUp=False, mouseMoved=False):
        selection = NSMutableIndexSet.alloc().initWithIndexSet_(self.arrayController.selectionIndexes())
        if found is None:
            selection.removeAllIndexes()
            if self._currentSelection is not None and not selection.isEqualToIndexSet_(self._currentSelection):
                self.arrayController.setSelectionIndexes_(selection)
                self.setNeedsDisplay_(True)
            return
        modifiers = event.modifierFlags()
        shiftDown = modifiers & NSShiftKeyMask
        commandDown = modifiers & NSCommandKeyMask
        optionDown = modifiers & NSAlternateKeyMask
        controlDown = modifiers & NSControlKeyMask

        containsFound = selection.containsIndex_(found)
        # dragging
        if self._havePreviousMouseDown and (mouseDragged and self._allowDrag) and containsFound and (not commandDown and not shiftDown and not controlDown):
            if found is None:
                return
            else:
                self._beginDrag(event)
                return
        if mouseDragged and not self._havePreviousMouseDown:
            return

        if commandDown:
            if found is None:
                return
            if mouseDown:
                if containsFound:
                    selection.removeIndex_(found)
                else:
                    selection.addIndex_(found)
            elif mouseUp:
                pass
            elif mouseDragged and found == self._lastSelectionFound:
                pass
            else:
                if containsFound and self._currentSelection is not None and self._currentSelection.containsIndex_(found):
                    selection.removeIndex_(found)
                elif not containsFound and self._currentSelection is not None and not self._currentSelection.containsIndex_(found):
                    selection.addIndex_(found)
        elif shiftDown:
            if found is None:
                return
            else:
                self._linearSelection(found, selection)
        else:
            if found is None:
                selection.removeAllIndexes()
            elif mouseDown or controlDown:
                if not containsFound:
                    selection.removeAllIndexes()
                selection.addIndex_(found)
            else:
                selection.removeAllIndexes()
                selection.addIndex_(found)

        if self._currentSelection is not None and not selection.isEqualToIndexSet_(self._currentSelection):
            self.arrayController.setSelectionIndexes_(selection)
            self.setNeedsDisplay_(True)

    # key
    @python_method
    def setLastFoundSelection(self, selection):
        if selection:
            self._lastSelectionFound = max(selection)
        else:
            self._lastSelectionFound = None

    def selectAll_(self, sender):
        selection = NSIndexSet.indexSetWithIndexesInRange_((0, len(self._glyphNames)))
        self.arrayController.setSelectionIndexes_(selection)
        self.setNeedsDisplay_(True)

    def keyDown_(self, event):
        # adapted from vanilla.vanillaList.List._keyDown

        # get the characters
        characters = event.characters()
        # get the field editor
        fieldEditor = self.window().fieldEditor_forObject_(True, self)

        deleteCharacters = [
            NSBackspaceCharacter,
            NSDeleteFunctionKey,
            NSDeleteCharacter,
            chr(0x007F),
        ]
        arrowCharacters = [
            NSUpArrowFunctionKey,
            NSDownArrowFunctionKey,
            NSLeftArrowFunctionKey,
            NSRightArrowFunctionKey,
            NSHomeFunctionKey,
            NSBeginFunctionKey
        ]
        nonCharacters = [
            NSPageUpFunctionKey,
            NSPageDownFunctionKey,
            chr(0x0003),
            u"\033",  # esc
            u"\r",
            u"\t",
        ]

        modifiers = event.modifierFlags()
        shiftDown = modifiers & NSShiftKeyMask
        commandDown = modifiers & NSCommandKeyMask

        newSelection = None

        # delete key. call the delete callback.
        if characters in deleteCharacters:
            self.vanillaWrapper()._removeSelection()
        # non key. reset the typing entry if necessary.
        elif characters in nonCharacters:
            self._lastKeyInputTime = None
            fieldEditor.setString_(u"")
        # arrow key. reset the typing entry if necessary.
        elif characters in arrowCharacters:
            self._lastKeyInputTime = None
            fieldEditor.setString_(u"")
            self._arrowKeyDown(characters, shiftDown, commandDown)
        else:
            # get the current time
            rightNow = time.time()
            # no time defined. define it.
            if self._lastKeyInputTime is None:
                self._lastKeyInputTime = rightNow
            # if the last input was too long ago,
            # clear away the old input
            if rightNow - self._lastKeyInputTime > 0.75:
                fieldEditor.setString_(u"")
            # reset the clock
            self._lastKeyInputTime = rightNow
            # add the characters to the fied editor
            fieldEditor.interpretKeyEvents_([event])
            # get the input string
            inputString = fieldEditor.string()
            inputUnicode = None

            match = None
            matchIndex = None
            lastResort = None
            lastResortIndex = None

            if len(inputString) == 1:
                inputUnicode = ord(inputString)
                glyphName = self._font.unicodeData.glyphNameForUnicode(inputUnicode)
                if glyphName and glyphName in self._glyphNames:
                    matchIndex = self._glyphNames.index(glyphName)

            if matchIndex is None:
                for index, glyphName in enumerate(self._glyphNames):
                    # if the item starts with the input string, it is considered a match
                    if glyphName.startswith(inputString):
                        if match is None:
                            match = glyphName
                            matchIndex = index
                            continue
                        # only if the item is less than the previous match is it a more relevant match
                        # example:
                        # given this order: sys, signal
                        # and this input string: s
                        # sys will be the first match, but signal is the more accurate match
                        if glyphName < match:
                            match = glyphName
                            matchIndex = index
                            continue
                    # if the item is greater than the input string,it can be used as a last resort
                    # example:
                    # given this order: vanilla, zipimport
                    # and this input string: x
                    # zipimport will be used as the last resort
                    if glyphName > inputString:
                        if lastResort is None:
                            lastResort = glyphName
                            lastResortIndex = index
                            continue
                        # if existing the last resort is greater than the item
                        # the item is a closer match to the input string
                        if lastResort > glyphName:
                            lastResort = glyphName
                            lastResortIndex = index
                            continue

            if matchIndex is not None:
                newSelection = matchIndex
            elif lastResortIndex is not None:
                newSelection = lastResortIndex
            if newSelection is not None:
                self._lastSelectionFound = newSelection
                selection = NSIndexSet.indexSetWithIndex_(newSelection)
                self.arrayController.setSelectionIndexes_(selection)
                self.scrollToCell_(newSelection)
                self.setNeedsDisplay_(True)

    @python_method
    def _arrowKeyDown(self, character, haveShiftKey, haveCommandKey):
        selection = NSMutableIndexSet.alloc().initWithIndexSet_(self.arrayController.selectionIndexes())
        if not selection.count():
            currentSelection = None
        else:
            currentSelection = self._lastSelectionFound

        if currentSelection is None:
            newSelection = 0

        if character == NSUpArrowFunctionKey:
            if currentSelection is None:
                currentSelection = 0
            elif haveShiftKey:
                currentSelection = selection.firstIndex()
            newSelection = currentSelection - self._columnCount
            if newSelection < 0:
                newSelection = 0

        elif character == NSDownArrowFunctionKey:
            if currentSelection is None:
                currentSelection = len(self._glyphNames) - 1
            elif haveShiftKey:
                currentSelection = selection.lastIndex()
            newSelection = currentSelection + self._columnCount
            if currentSelection is None or newSelection >= len(self._glyphNames):
                newSelection = len(self._glyphNames) - 1

        elif character == NSLeftArrowFunctionKey:
            if currentSelection is None or currentSelection == 0:
                newSelection = len(self._glyphNames) - 1
            else:
                if haveShiftKey:
                    currentSelection = selection.firstIndex()
                newSelection = currentSelection - 1

        elif character == NSRightArrowFunctionKey:
            if currentSelection is None or currentSelection == len(self._glyphNames) - 1:
                newSelection = 0
            else:
                if haveShiftKey:
                    currentSelection = selection.lastIndex()
                newSelection = currentSelection + 1

        elif character == NSHomeFunctionKey:
            newSelection = 0

        elif character == NSBeginFunctionKey:
            newSelection = 0

        elif character == NSEndFunctionKey:
            newSelection = len(self._glyphNames) - 1

        if haveShiftKey:
            self._linearSelection(newSelection, selection)
        else:
            if not haveCommandKey:
                selection.removeAllIndexes()
            selection.addIndex_(newSelection)
        self._lastSelectionFound = newSelection
        self.arrayController.setSelectionIndexes_(selection)
        self.setNeedsDisplay_(True)
        self.scrollToCell_(newSelection)

    # -------------
    # Drag and Drop
    # -------------

    # drag

    def ignoreModifierKeysWhileDragging(self):
        return True

    def draggingSourceOperationMaskForLocal_(self, isLocal):
        return NSDragOperationGeneric

    @python_method
    def _beginDrag(self, event):
        # hide the detail window
        self._handleDetailWindow(event=event, found=None, inDragAndDrop=True)
        # prep
        indexes = self.vanillaWrapper().getSelection()
        image = _makeGlyphCellDragIcon([self._font[self._glyphNames[i]] for i in indexes])

        eventLocation = event.locationInWindow()
        location = self.convertPoint_fromView_(eventLocation, None)
        w, h = image.size()
        location = (location[0] - 10, location[1] + 10)

        dragAndDropType = self.vanillaWrapper()._dragAndDropType
        pboard = NSPasteboard.pasteboardWithName_(NSDragPboard)
        pboard.declareTypes_owner_([dragAndDropType], self)
        pboard.setPropertyList_forType_(indexes, dragAndDropType)

        self.dragImage_at_offset_event_pasteboard_source_slideBack_(
            image, location, (0, 0),
            event, pboard, self, True
        )

    def getGlyphsFromDraggingInfo_(self, draggingInfo):
        source = draggingInfo.draggingSource()
        if source != self:
            return None
        dragAndDropType = self.vanillaWrapper()._dragAndDropType
        pboard = draggingInfo.draggingPasteboard()
        indexes = pboard.propertyListForType_(dragAndDropType)
        glyphs = self.getGlyphsAtIndexes_(indexes)
        return glyphs

    # drop

    def _getMouseLocation(self):
        window = self.window()
        mouseLocation = NSEvent.mouseLocation()
        mouseLocation = window.convertScreenToBase_(mouseLocation)
        mouseLocation = self.convertPoint_fromView_(mouseLocation, None)
        return mouseLocation

    @python_method
    def _handleDrop(self, draggingInfo, isProposal=False, callCallback=False):
        vanillaWrapper = self.vanillaWrapper()
        # quickly determine if a drop is even possible
        haveDropSettings = False
        if vanillaWrapper._selfDropSettings is not None:
            haveDropSettings = True
        elif vanillaWrapper._selfWindowDropSettings is not None:
            haveDropSettings = True
        elif vanillaWrapper._selfDocumentDropSettings is not None:
            haveDropSettings = True
        elif vanillaWrapper._selfApplicationDropSettings is not None:
            haveDropSettings = True
        elif vanillaWrapper._otherApplicationDropSettings is not None:
            haveDropSettings = True
        if not haveDropSettings:
            return
        # grab the dragging source
        draggingSource = draggingInfo.draggingSource()
        sourceForCallback = draggingSource
        if hasattr(draggingSource, "vanillaWrapper") and getattr(draggingSource, "vanillaWrapper") is not None:
            sourceForCallback = getattr(draggingSource, "vanillaWrapper")()
        # find the glyph that is being hovered over
        mouseLocation = self._getMouseLocation()
        rowIndex = self._findGlyphForLocation(mouseLocation)
        # make the info dict
        dropOnRow = rowIndex is not None
        dropInformation = dict(isProposal=isProposal, dropOnRow=dropOnRow, rowIndex=rowIndex, data=None, source=sourceForCallback)
        # drag from self
        if draggingSource == self and vanillaWrapper._selfDropSettings is not None:
            if vanillaWrapper._selfDropSettings is None:
                return NSDragOperationNone
            settings = vanillaWrapper._selfDropSettings
            return self._handleDropBasedOnSettings(settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback)
        # drag from same window
        window = self.window()
        if window is not None and draggingSource is not None and window == draggingSource.window() and vanillaWrapper._selfWindowDropSettings is not None:
            if vanillaWrapper._selfWindowDropSettings is None:
                return NSDragOperationNone
            settings = vanillaWrapper._selfWindowDropSettings
            return self._handleDropBasedOnSettings(settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback)
        # drag from same document
        document = self.window().document()
        if document is not None and document == draggingSource.window().document():
            if vanillaWrapper._selfDocumentDropSettings is None:
                return NSDragOperationNone
            settings = vanillaWrapper._selfDocumentDropSettings
            return self._handleDropBasedOnSettings(settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback)
        # drag from same application
        applicationWindows = NSApp().windows()
        if draggingSource is not None and draggingSource.window() in applicationWindows:
            if vanillaWrapper._selfApplicationDropSettings is None:
                return NSDragOperationNone
            settings = vanillaWrapper._selfApplicationDropSettings
            return self._handleDropBasedOnSettings(settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback)
        # fall back to drag from other application
        if vanillaWrapper._otherApplicationDropSettings is None:
            return NSDragOperationNone
        settings = vanillaWrapper._otherApplicationDropSettings
        return self._handleDropBasedOnSettings(settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback)

    @python_method
    def _handleDropBasedOnSettings(self, settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback):
        # rest the insertion positions
        self._dropTargetBetween = None
        self._dropTargetOn = None
        self._dropTargetSelf = False
        # get some settings
        allowDropOnRow = settings.get("allowsDropOnRows", False)
        allowDropBetweenRows = settings.get("allowsDropBetweenRows", True)
        rowIndex = dropInformation["rowIndex"]
        # drop on a specific cell
        if allowDropOnRow and allowDropBetweenRows and rowIndex is not None:
            mouseLocation = self._getMouseLocation()
            (x, y), (w, h) = self._indexToClickRects[rowIndex]
            _s = .35
            left = ((x, y), (w * _s, h))
            right = ((x + w * (1 - _s), y), (w * _s, h))
            if NSPointInRect(mouseLocation, left):
                target = (rowIndex - 1, rowIndex)
                self._dropTargetBetween = target
                dropInformation["dropOnRow"] = False
            elif NSPointInRect(mouseLocation, right):
                target = (rowIndex, rowIndex + 1)
                dropInformation["rowIndex"] += 1
                self._dropTargetBetween = target
                dropInformation["dropOnRow"] = False
            else:
                self._dropTargetOn = rowIndex
        elif allowDropOnRow and rowIndex is not None:
            self._dropTargetOn = rowIndex
        # drop between cells
        elif allowDropBetweenRows and rowIndex is not None:
            mouseLocation = self._getMouseLocation()
            (x, y), (w, h) = self._indexToClickRects[rowIndex]
            left = ((x, y), (w * .5, h))
            if NSPointInRect(mouseLocation, left):
                target = (rowIndex - 1, rowIndex)
            else:
                target = (rowIndex, rowIndex + 1)
                dropInformation["rowIndex"] += 1
            self._dropTargetBetween = target
        # drop on the view
        if not allowDropOnRow or not allowDropBetweenRows or rowIndex is None:
            self._dropTargetSelf = True
        # if no row index came in, and one is needed, set it to after all glyphs
        if (allowDropOnRow or allowDropBetweenRows) and rowIndex is None:
            dropInformation["rowIndex"] = len(self._glyphNames)
        # redraw
        self.setNeedsDisplay_(True)
        # sometimes the callback will need to be called
        if callCallback:
            dropInformation["data"] = self._unpackPboard(settings, draggingInfo)
            result = settings["callback"](vanillaWrapper, dropInformation)
            if result:
                return settings.get("operation", NSDragOperationCopy)
        # other times it won't
        else:
            return settings.get("operation", NSDragOperationCopy)
        return NSDragOperationNone

    @python_method
    def _unpackPboard(self, settings, draggingInfo):
        pboard = draggingInfo.draggingPasteboard()
        data = pboard.propertyListForType_(settings["type"])
        if isinstance(data, (NSString, objc.pyobjc_unicode)):
            data = data.propertyList()
        return data

    def draggingEntered_(self, sender):
        return self._handleDrop(sender, isProposal=True, callCallback=False)

    def draggingUpdated_(self, sender):
        return self._handleDrop(sender, isProposal=True, callCallback=False)

    def draggingExited_(self, sender):
        self._dropTargetBetween = None
        self._dropTargetOn = None
        self._dropTargetSelf = False
        self.setNeedsDisplay_(True)
        return None

    def prepareForDragOperation_(self, sender):
        result = self._handleDrop(sender, isProposal=True, callCallback=True)
        if not result:
            # turn off the insertion location display
            self._dropTargetBetween = None
            self._dropTargetOn = None
            self._dropTargetSelf = False
            self.setNeedsDisplay_(True)
        return result

    def performDragOperation_(self, sender):
        result = self._handleDrop(sender, isProposal=False, callCallback=True)
        # turn off the insertion location display
        self._dropTargetBetween = None
        self._dropTargetOn = None
        self._dropTargetSelf = False
        self.setNeedsDisplay_(True)
        return result

# -------------------------
# Information Pop Up Window
# -------------------------


class GlyphInformationPopUpWindow(InformationPopUpWindow):

    def __init__(self, screen=None):
        posSize = (200, 280)
        super(GlyphInformationPopUpWindow, self).__init__(posSize, screen=screen)
        self.glyphView = GlyphInformationGlyphView((5, 5, -5, 145))

        self.line = HUDHorizontalLine((0, 160, -0, 1))

        titleWidth = 100
        entryLeft = 105
        self.nameTitle = HUDTextBox((0, 170, titleWidth, 17), "Name:", alignment="right")
        self.name = HUDTextBox((entryLeft, 170, -5, 17), "")
        self.unicodeTitle = HUDTextBox((0, 190, titleWidth, 17), "Unicode:", alignment="right")
        self.unicode = HUDTextBox((entryLeft, 190, -5, 17), "")
        self.widthTitle = HUDTextBox((0, 210, titleWidth, 17), "Width:", alignment="right")
        self.width = HUDTextBox((entryLeft, 210, -5, 17), "")
        self.leftMarginTitle = HUDTextBox((0, 230, titleWidth, 17), "Left Margin:", alignment="right")
        self.leftMargin = HUDTextBox((entryLeft, 230, -5, 17), "")
        self.rightMarginTitle = HUDTextBox((0, 250, titleWidth, 17), "Right Margin:", alignment="right")
        self.rightMargin = HUDTextBox((entryLeft, 250, -5, 17), "")

    @python_method
    def set(self, glyph):
        # name
        name = glyph.name
        # unicode
        uni = glyph.unicode
        if uni is None:
            uni = ""
        else:
            uni = hex(uni)[2:].upper()
            if len(uni) < 4:
                uni = uni.zfill(4)
        # width
        width = glyph.width
        if width is None:
            width = 0
        width = round(width, 3)
        if width == int(width):
            width = int(width)
        # left margin
        leftMargin = glyph.leftMargin
        if leftMargin is None:
            leftMargin = 0
        leftMargin = round(leftMargin, 3)
        if leftMargin == int(leftMargin):
            leftMargin = int(leftMargin)
        # right margin
        rightMargin = glyph.rightMargin
        if rightMargin is None:
            rightMargin = 0
        rightMargin = round(rightMargin, 3)
        if rightMargin == int(rightMargin):
            rightMargin = int(rightMargin)
        # set
        self.name.set(name)
        self.unicode.set(uni)
        self.width.set(width)
        self.leftMargin.set(leftMargin)
        self.rightMargin.set(rightMargin)
        self.glyphView.set(glyph)
        self._window.invalidateShadow()


class DefconAppKitGlyphInformationNSView(NSView):

    def setGlyph_(self, glyph):
        self._glyph = glyph
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        if not hasattr(self, "_glyph"):
            return
        inset = 10
        bounds = self.bounds()
        bounds = NSInsetRect(bounds, inset, inset)
        vWidth, vHeight = bounds.size
        glyph = self._glyph
        font = glyph.font
        if font is None:
            upm = 1000
            descender = -250
        else:
            upm = font.info.unitsPerEm
            descender = font.info.descender
        scale = vHeight / upm
        centerOffset = (vWidth - (glyph.width * scale)) / 2
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(centerOffset + inset, inset)
        transform.scaleBy_(scale)
        transform.translateXBy_yBy_(0, -descender)
        transform.concat()
        NSColor.whiteColor().set()
        path = glyph.getRepresentation("defconAppKit.NSBezierPath")
        path.fill()


class GlyphInformationGlyphView(vanilla.VanillaBaseObject):

    def __init__(self, posSize):
        self._setupView(DefconAppKitGlyphInformationNSView, posSize)

    def set(self, glyph):
        self._nsObject.setGlyph_(glyph)
