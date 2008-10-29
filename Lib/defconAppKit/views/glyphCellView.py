import weakref
import time
import objc
from Foundation import *
from AppKit import *
import vanilla
from defconAppKit.notificationObserver import NSObjectNotificationObserver
from defconAppKit.tools.iconCountBadge import addCountBadgeToIcon
from defconAppKit.windows.popUpWindow import InformationPopUpWindow, HUDTextBox, HUDHorizontalLine


gridColor = backgroundColor = NSColor.colorWithCalibratedWhite_alpha_(.6, 1.0)
selectionColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.82, .82, .9, 1.0)
selectionColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.62, .62, .7, .5)

def _makeGlyphCellDragIcon(glyphs):
    font = None
    glyphRepresentation = None
    glyphWidth = None
    for glyph in glyphs:
        rep = glyph.getRepresentation("NSBezierPath")
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


class DefconAppKitGlyphCellNSView(NSView):

    def initWithFrame_cellRepresentationName_detailWindowClass_(self,
        frame, cellRepresentationName, detailWindowClass):
        self = super(DefconAppKitGlyphCellNSView, self).initWithFrame_(frame)
        self._cellWidth = 50
        self._cellHeight = 50
        self._glyphs = []

        self._notificationObserver = NSObjectNotificationObserver()

        self._clickRectsToIndex = {}
        self._indexToClickRects = {}

        self._selection = set()
        self._lastKeyInputTime = None

        self._columnCount = 0
        self._rowCount = 0

        self._cellRepresentationName = cellRepresentationName
        self._cellRepresentationArguments = {}

        self._allowDrag = False

        self._glyphDetailWindowClass = detailWindowClass
        self._glyphDetailWindow = None
        self._glyphDetailRequiredModifiers = [NSControlKeyMask]
        self._glyphDetailOnMouseDown = True
        self._glyphDetailOnMouseUp = False
        self._glyphDetailOnMouseDragged = True
        self._glyphDetailOnMouseMoved = False

        self._windowIsClosed = False

        return self

    # --------------
    # custom methods
    # --------------

    def setAllowsDrag_(self, value):
        self._allowDrag = value

    def preloadGlyphCellImages(self):
        representationName = self._cellRepresentationName
        representationArguments = self._cellRepresentationArguments
        cellWidth = self._cellWidth
        cellHeight = self._cellHeight
        for glyph in self._glyphs:
            glyph.getRepresentation(representationName, width=cellWidth, height=cellHeight, **representationArguments)

    def setGlyphs_(self, glyphs):
        currentSelection = [self._glyphs[index] for index in self._selection]
        newSelection = set([glyphs.index(glyph) for glyph in currentSelection if glyph in glyphs])
        self._selection = newSelection
        self._glyphs = glyphs
        self.recalculateFrame()

    def getGlyphsAtIndexes_(self, indexes):
        return [self._glyphs[i] for i in indexes]

    def setCellSize_(self, (width, height)):
        self._cellWidth = width
        self._cellHeight = height
        self.recalculateFrame()

    def getCellSize(self):
        return self._cellWidth, self._cellHeight

    def setCellRepresentationArguments_(self, **kwargs):
        self._cellRepresentationArguments = kwargs
        self.setNeedsDisplay_(True)

    def getCellRepresentationArguments(self):
        return dict(self._cellRepresentationArguments)

    def recalculateFrame(self):
        superview = self.superview()
        if superview is None:
            return
        width, height = superview.frame().size
        if width == 0 or height == 0:
            return
        if self._glyphs:
            columnCount = int(width / self._cellWidth)
            if columnCount == 0:
                columnCount = 1
            rowCount = len(self._glyphs) / columnCount
            if columnCount * rowCount < len(self._glyphs):
                rowCount += 1
            newWidth = self._cellWidth * columnCount
            newHeight = self._cellHeight * rowCount
        else:
            columnCount = 0
            rowCount = 0
            newWidth = newHeight = 0
        if not self.inLiveResize():
            if width > newWidth:
                newWidth = width
            if height > newHeight:
                newHeight = height
        self.setFrame_(((0, 0), (newWidth, newHeight)))
        self._columnCount = columnCount
        self._rowCount = rowCount
        self.setNeedsDisplay_(True)

    def setGlyphDetailConditions_(self, modifiers=[], mouseDown=False, mouseUp=False, mouseDragged=False, mouseMoved=False):
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
        return self._glyphDetailWindow

    # selection

    def getSelection(self):
        return list(sorted(self._selection))

    def setSelection_(self, selection):
        self._selection = set(selection)
        self.setNeedsDisplay_(True)

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
                self._glyphDetailWindow.close()
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

    # --------------
    # NSView methods
    # --------------

    def viewDidMoveToWindow(self):
        # if window() returns an object, open the detail window
        if self.window() is not None:
            if self._glyphDetailWindow is None and self._glyphDetailWindowClass is not None:
                self._glyphDetailWindow = self._glyphDetailWindowClass()
            self.subscribeToWindow()
            self.subscribeToScrollViewFrameChange()
            self.recalculateFrame()

    def isFlipped(self):
        return True

    def acceptsFirstResponder(self):
        return True

    def drawRect_(self, rect):
        backgroundColor.set()
        NSRectFill(self.frame())

        representationName = self._cellRepresentationName
        representationArguments = self._cellRepresentationArguments

        cellWidth = self._cellWidth
        cellHeight = self._cellHeight
        width, height = self.frame().size
        left = 0
        top = height
        top = cellHeight

        self._clickRectsToIndex = {}
        self._indexToClickRects = {}

        visibleRect = self.visibleRect()

        NSColor.whiteColor().set()
        for index, glyph in enumerate(self._glyphs):
            t = top - cellHeight
            rect = ((left, t), (cellWidth, cellHeight))

            NSRectFill(rect)

            self._clickRectsToIndex[rect] = index
            self._indexToClickRects[index] = rect

            if NSIntersectsRect(visibleRect, rect):
                image = glyph.getRepresentation(representationName, width=cellWidth, height=cellHeight, **representationArguments)
                image.drawAtPoint_fromRect_operation_fraction_(
                    (left, t), ((0, 0), (cellWidth, cellHeight)), NSCompositeSourceOver, 1.0
                    )

                if index in self._selection:
                    selectionColor.set()
                    r = ((left+1, t+1), (cellWidth-3, cellHeight-3))
                    NSRectFillUsingOperation(r, NSCompositePlusDarker)
                    NSColor.whiteColor().set()

            left += cellWidth
            if left + cellWidth > width:
                left = 0
                top += cellHeight

        path = NSBezierPath.bezierPath()
        for i in xrange(1, self._rowCount+1):
            top = (i * cellHeight) - .5
            path.moveToPoint_((0, top))
            path.lineToPoint_((width, top))
        for i in xrange(1, self._columnCount+1):
            left = (i * cellWidth) - .5
            path.moveToPoint_((left, 0))
            path.lineToPoint_((left, height))
        gridColor.set()
        path.setLineWidth_(1.0)
        path.stroke()

    # ---------
    # Selection
    # ---------

    def _linearSelection(self, index):
        if index in self._selection:
            newSelection = None
        elif not self._selection:
            newSelection = set([index])
        else:
            minEdge = min(self._selection)
            maxEdge = max(self._selection)
            if index < minEdge:
                newSelection = set(range(index, maxEdge + 1))
            elif index > maxEdge:
                newSelection = set(range(minEdge, index + 1))
            else:
                if abs(index - minEdge) < abs(index - maxEdge):
                    newSelection = self._selection | set(range(minEdge, index + 1))
                else:
                    newSelection = self._selection | set(range(index, maxEdge + 1))
        return newSelection

    def scrollToCell_(self, index):
        superview = self.superview()
        rect = self._indexToClickRects[index]
        self.scrollRectToVisible_(rect)

    # mouse

    def mouseDown_(self, event):
        found = self._findGlyphForEvent(event)
        self._mouseSelection(event, found, mouseDown=True)
        self._handleDetailWindow(event, found, mouseDown=True)
        if event.clickCount() > 1:
            vanillaWrapper = self.vanillaWrapper()
            if vanillaWrapper._doubleClickCallback is not None:
                vanillaWrapper._doubleClickCallback(vanillaWrapper)
        self.autoscroll_(event)

    def mouseDragged_(self, event):
        found = self._findGlyphForEvent(event)
        self._mouseSelection(event, found, mouseDragged=True)
        self._handleDetailWindow(event, found, mouseDragged=True)
        self.autoscroll_(event)

    def mouseMoved_(self, event):
        found = self._findGlyphForEvent(event)
        self._handleDetailWindow(event, found, mouseMoved=True)

    def mouseUp_(self, event):
        found = self._findGlyphForEvent(event)
        self._mouseSelection(event, found, mouseUp=True)
        self._handleDetailWindow(event, found, mouseUp=True)
        if self._selection != self._oldSelection:
            vanillaWrapper = self.vanillaWrapper()
            if vanillaWrapper._selectionCallback is not None:
                vanillaWrapper._selectionCallback(vanillaWrapper)
        del self._oldSelection

    def _findGlyphForEvent(self, event):
        eventLocation = event.locationInWindow()
        mouseLocation = self.convertPoint_fromView_(eventLocation, None)
        found = None
        for rect, index in self._clickRectsToIndex.items():
            if NSPointInRect(mouseLocation, rect):
                found = index
                break
        return found

    def _handleDetailWindow(self, event, found, mouseDown=False, mouseMoved=False, mouseDragged=False, mouseUp=False, inDragAndDrop=False):
        # no window
        if self._windowIsClosed:
            return
        if self._glyphDetailWindow is None:
            return
        # determine show/hide
        shouldBeVisible = True
        ## event is None
        if event is None:
            shouldBeVisible = False
        ## window is not key
        elif NSApp().keyWindow() != self.window():
            shouldBeVisible = False
        ## XXX work around an issue that causes mouseDragged
        ## to be called after a drop from the view has occurred
        ## outside of the view.
        elif mouseDragged and not self._glyphDetailWindow.isVisible():
            shouldBeVisible = False
        ## event requirements
        else:
            eventLocation = event.locationInWindow()
            mouseLocation = self.convertPoint_fromView_(eventLocation, None)
            ## drag and drop
            if inDragAndDrop:
                shouldBeVisible = False
            ## modifiers
            modifiers = event.modifierFlags()
            for modifier in self._glyphDetailRequiredModifiers:
                if not modifiers & modifier:
                    shouldBeVisible = False
                    break
            ## mouse conditions
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
            ## glyph hit
            if found is None:
                shouldBeVisible = False
            ## mouse position is visible
            if not NSPointInRect(mouseLocation, self.visibleRect()):
                shouldBeVisible = False
        # set the position
        if shouldBeVisible:
            x, y = eventLocation
            windowX, windowY = event.window().frame().origin
            detailX = windowX + x
            detailY = windowY + y
            glyph = self._glyphs[found]
            self._glyphDetailWindow.setPositionNearCursor((detailX, detailY))
            self._glyphDetailWindow.set(glyph)
            if not self._glyphDetailWindow.isVisible():
                self._glyphDetailWindow.show()
        else:
            self._glyphDetailWindow.hide()

    def _mouseSelection(self, event, found, mouseDown=False, mouseDragged=False, mouseUp=False, mouseMoved=False):
        if mouseDown:
            self._oldSelection = set(self._selection)
        if found is None:
            return

        modifiers = event.modifierFlags()
        shiftDown = modifiers & NSShiftKeyMask
        commandDown = modifiers & NSCommandKeyMask
        optionDown = modifiers & NSAlternateKeyMask
        controlDown = modifiers & NSControlKeyMask

        # dragging
        if mouseDragged and self._allowDrag and found in self._selection and not commandDown and not shiftDown and not controlDown:
            if found is None:
                return
            else:
                self._beginDrag(event)
                return
        # selecting
        newSelection = None
        if commandDown:
            if found is None:
                return
            if mouseDown:
                if found in self._selection:
                    self._selection.remove(found)
                else:
                    self._selection.add(found)
            elif mouseUp:
                pass
            else:
                if found in self._selection and found in self._oldSelection:
                    self._selection.remove(found)
                elif found not in self._selection and found not in self._oldSelection:
                    self._selection.add(found)
            newSelection = set(self._selection)
        elif shiftDown:
            if found is None:
                return
            else:
                newSelection = self._linearSelection(found)
        else:
            if found is None:
                newSelection = set()
            elif mouseDown and found in self._selection:
                pass
            else:
                newSelection = set([found])
        if newSelection is not None:
            self._selection = newSelection
            self.setNeedsDisplay_(True)

    # key

    def selectAll_(self, sender):
        newSelection = set(xrange(len(self._glyphs)))
        self.setSelection_(newSelection)
        self.vanillaWrapper()._selection()

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
            unichr(NSDeleteCharacter),
        ]
        arrowCharacters = [
            NSUpArrowFunctionKey,
            NSDownArrowFunctionKey,
            NSLeftArrowFunctionKey,
            NSRightArrowFunctionKey
        ]
        nonCharacters = [
            NSPageUpFunctionKey,
            NSPageDownFunctionKey,
            unichr(NSEnterCharacter),
            unichr(NSCarriageReturnCharacter),
            unichr(NSTabCharacter),
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
            self._arrowKeyDown(characters, shiftDown)
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

            match = None
            matchIndex = None
            lastResort = None
            lastResortIndex = None
            inputLength = len(inputString)
            for index, glyph in enumerate(self._glyphs):
                item = glyph.name
                # if the item starts with the input string, it is considered a match
                if item.startswith(inputString):
                    if match is None:
                        match = item
                        matchIndex = index
                        continue
                    # only if the item is less than the previous match is it a more relevant match
                    # example:
                    # given this order: sys, signal
                    # and this input string: s
                    # sys will be the first match, but signal is the more accurate match
                    if item < match:
                        match = item
                        matchIndex = index
                        continue
                # if the item is greater than the input string,it can be used as a last resort
                # example:
                # given this order: vanilla, zipimport
                # and this input string: x
                # zipimport will be used as the last resort
                if item > inputString:
                    if lastResort is None:
                        lastResort = item
                        lastResortIndex = index
                        continue
                    # if existing the last resort is greater than the item
                    # the item is a closer match to the input string 
                    if lastResort > item:
                        lastResort = item
                        lastResortIndex = index
                        continue

            if matchIndex is not None:
                newSelection = matchIndex
            elif lastResortIndex is not None:
                newSelection = lastResortIndex

        if newSelection is not None:
            self.setSelection_(set([newSelection]))
            self.vanillaWrapper()._selection()
            self.scrollToCell_(newSelection)

    def _arrowKeyDown(self, character, haveShiftKey):
        if not self._selection:
            currentSelection = None
        else:
            if character == NSUpArrowFunctionKey or character == NSLeftArrowFunctionKey:
                currentSelection = sorted(self._selection)[0]
            else:
                currentSelection = sorted(self._selection)[-1]

        if character == NSUpArrowFunctionKey or character == NSDownArrowFunctionKey:
            if currentSelection is None:
                newSelection = 0
            else:
                if character == NSUpArrowFunctionKey:
                    newSelection = currentSelection - self._columnCount
                    if newSelection < 0:
                        newSelection = 0
                elif character == NSDownArrowFunctionKey:
                    newSelection = currentSelection + self._columnCount
                    if newSelection >= len(self._glyphs):
                        newSelection = len(self._glyphs) - 1
        else:
            if currentSelection is None:
                newSelection = 0
            if character == NSLeftArrowFunctionKey:
                if currentSelection is None or currentSelection == 0:
                    newSelection = len(self._glyphs) - 1
                else:
                    newSelection = currentSelection - 1
            elif character == NSRightArrowFunctionKey:
                if currentSelection is None or currentSelection == len(self._glyphs) - 1:
                    newSelection = 0
                else:
                    newSelection = currentSelection + 1

        newSelectionIndex = newSelection
        if haveShiftKey:
            newSelection = self._linearSelection(newSelection)
            if newSelection is None:
                return
        else:
            newSelection = set([newSelection])

        self._selection = newSelection
        self.setNeedsDisplay_(True)
        self.vanillaWrapper()._selection()
        self.scrollToCell_(newSelectionIndex)

    # -------------
    # Drag and Drop
    # -------------

    # drag

    def ignoreModifierKeysWhileDragging(self):
        return True

    def draggingSourceOperationMaskForLocal_(self, isLocal):
        return NSDragOperationGeneric

    def _beginDrag(self, event):
        # hide the detail window
        self._handleDetailWindow(event=event, found=None, inDragAndDrop=True)
        # prep
        indexes = [i for i in sorted(self._selection)]
        image = _makeGlyphCellDragIcon([self._glyphs[i] for i in self._selection])

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

    def _handleDrop(self, draggingInfo, isProposal=False, callCallback=False):
        vanillaWrapper = self.vanillaWrapper()
        draggingSource = draggingInfo.draggingSource()
        sourceForCallback = draggingSource
        if hasattr(draggingSource, "vanillaWrapper") and getattr(draggingSource, "vanillaWrapper") is not None:
            sourceForCallback = getattr(draggingSource, "vanillaWrapper")()
        # make the info dict
        dropOnRow = False # XXX support in future
        rowIndex = len(self._glyphs)
        dropInformation = dict(isProposal=isProposal, dropOnRow=dropOnRow, rowIndex=rowIndex, data=None, source=sourceForCallback)
        # drag from self
        if draggingSource == self:
            # XXX not supported yet
            return NSDragOperationNone
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

    def _handleDropBasedOnSettings(self, settings, vanillaWrapper, dropOnRow, draggingInfo, dropInformation, callCallback):
        # XXX validate drop position in future
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
        return None

    def prepareForDragOperation_(self, sender):
        return self._handleDrop(sender, isProposal=True, callCallback=True)

    def performDragOperation_(self, sender):
        return self._handleDrop(sender, isProposal=False, callCallback=True)


# -------------------------
# Information Pop Up Window
# -------------------------


class GlyphInformationPopUpWindow(InformationPopUpWindow):

    def __init__(self):
        posSize = (200, 280)
        super(GlyphInformationPopUpWindow, self).__init__(posSize)
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
        font = glyph.getParent()
        if font is None:
            upm = 1000
            descender = -250
        else:
            upm = font.info.unitsPerEm
            descender = font.info.descender
        scale = vHeight / upm
        centerOffset = (vWidth - (glyph.width * scale)) / 2
        transform = NSAffineTransform.transform()
        transform.translateXBy_yBy_(centerOffset+inset, inset)
        transform.scaleBy_(scale)
        transform.translateXBy_yBy_(0, -descender)
        transform.concat()
        NSColor.whiteColor().set()
        path = glyph.getRepresentation("NSBezierPath")
        path.fill()


class GlyphInformationGlyphView(vanilla.VanillaBaseObject):

    def __init__(self, posSize):
        self._setupView(DefconAppKitGlyphInformationNSView, posSize)

    def set(self, glyph):
        self._nsObject.setGlyph_(glyph)

