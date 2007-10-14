import weakref
import time
from Foundation import *
from AppKit import *
import vanilla
from defconAppKit.notificationObserver import NSObjectNotificationObserver
from defconAppKit.tools.iconCountBadge import addCountBadgeToIcon


gridColor = backgroundColor = NSColor.colorWithCalibratedWhite_alpha_(.6, 1.0)
selectionColor = NSColor.colorWithCalibratedRed_green_blue_alpha_(.87, .87, .9, 1.0)


DefconAppKitGlyphPboardType = "DefconAppKitGlyphPboardType"


class DefconAppKitGlyphCellNSView(NSView):

    def initWithFrame_cellRepresentationName_detailRepresentationName_(self,
        frame, cellRepresentationName, detailRepresentationName):
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
        self._detailRepresentationName = detailRepresentationName
        self._cellRepresentationArguments = {}

        self._allowDrag = False

        self._glyphDetailMenu = None

        return self

    # --------------
    # custom methods
    # --------------

    def setAllowsDrag_(self, value):
        self._allowDrag = value

    def setAllowsDrop_(self, value):
        if value:
            self.registerForDraggedTypes_([DefconAppKitGlyphPboardType])
        else:
            self.unregisterDraggedTypes()

    def setGlyphs_(self, glyphs):
        self._unsubscribeFromGlyphs()
        self._glyphs = glyphs
        self._subscribeToGlyphs()
        self.recalculateFrame()

    def setCellSize_(self, (width, height)):
        self._cellWidth = width
        self._cellHeight = height
        self.recalculateFrame()

    def setCellRepresentationArguments_(self, **kwargs):
        self._cellRepresentationArguments = kwargs
        self.setNeedsDisplay_(True)

    def getCellRepresentationArguments(self):
        return dict(self._cellRepresentationArguments)

    def recalculateFrame(self):
        width, height = self.superview().frame().size
        if width == 0 or height == 0:
            return
        if self._glyphs:
            columnCount = int(width / self._cellWidth)
            rowCount = len(self._glyphs) / columnCount
            if columnCount * rowCount < len(self._glyphs):
                rowCount += 1
            newWidth = self._cellWidth * columnCount
            newHeight = self._cellHeight * rowCount
        else:
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

    # selection

    def getSelection(self):
        return list(sorted(self._selection))

    def setSelection_(self, selection):
        self._selection = set(selection)
        self.setNeedsDisplay_(True)

    # glyph change notification support

    def _subscribeToGlyphs(self):
        for glyph in self._glyphs:
            self._notificationObserver.add(self, "_glyphChanged", glyph, "Glyph.Changed")

    def _unsubscribeFromGlyphs(self):
        done = set()
        for glyph in self._glyphs:
            if glyph in done:
                continue
            self._notificationObserver.remove(self, glyph, "Glyph.Changed")
            done.add(glyphs)

    def _glyphChanged(self, notification):
        self.setNeedsDisplay_(True)

    # window resize notification support

    def clipViewFrameChangeNotification_(self, notification):
        self.recalculateFrame()

    def subscribeToScrollViewFrameChange_(self, scrollView):
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.addObserver_selector_name_object_(
            self, "clipViewFrameChangeNotification:", NSViewFrameDidChangeNotification, scrollView
        )
        scrollView.setPostsFrameChangedNotifications_(True)

    def unsubscribeToScrollViewFrameChange_(self, scrollView):
        notificationCenter = NSNotificationCenter.defaultCenter()
        notificationCenter.removeObserver_name_object_(
            self, NSViewFrameDidChangeNotification, scrollView
        )
        scrollView.setPostsFrameChangedNotifications_(False)

    def viewDidEndLiveResize(self):
        self.recalculateFrame()

    # --------------
    # NSView methods
    # --------------

    def dealloc(self):
        self._unsubscribeFromGlyphs()
        super(DefconAppKitGlyphCellNSView, self).dealloc()

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

        NSColor.whiteColor().set()
        for index, glyph in enumerate(self._glyphs):
            t = top-cellHeight
            rect = ((left, t), (cellWidth, cellHeight))

            self._clickRectsToIndex[rect] = index
            self._indexToClickRects[index] = rect

            if index in self._selection:
                selectionColor.set()
                NSRectFill(rect)
                NSColor.whiteColor().set()
            else:
                NSRectFill(rect)

            image = glyph.getRepresentation(representationName, width=cellWidth, height=cellHeight, **representationArguments)
            image.drawAtPoint_fromRect_operation_fraction_(
                (left, t), ((0, 0), (cellWidth, cellHeight)), NSCompositeSourceOver, 1.0
                )
            left += cellWidth

            if left + cellWidth > width:
                left = 0
                top += cellHeight

        path = NSBezierPath.bezierPath()
        for i in xrange(1, self._rowCount):
            top = (i * cellHeight) - .5
            path.moveToPoint_((0, top))
            path.lineToPoint_((width, top))
        for i in xrange(1, self._columnCount):
            left = (i * cellWidth) - .5
            path.moveToPoint_((left, 0))
            path.lineToPoint_((left, height))
        gridColor.set()
        path.setLineWidth_(1.0)
        path.stroke()

        if self._glyphDetailMenu is not None:
            shadow = NSShadow.alloc().init()
            shadow.setShadowOffset_((0, -3))
            shadow.setShadowColor_(NSColor.blackColor())
            shadow.setShadowBlurRadius_(10.0)
            shadow.set()

            point, image = self._getPositionForGlyphDetailMenu()
            image.drawAtPoint_fromRect_operation_fraction_(
                point, ((0, 0), image.size()), NSCompositeSourceOver, 1.0)

    def _getPositionForGlyphDetailMenu(self):
        (left, top), image = self._glyphDetailMenu
        width, height = image.size()
        right = left + width
        bottom = top + height

        (visibleLeft, visibleTop), (visibleWidth, visibleHeight) = self.superview().documentVisibleRect()
        visibleRight = visibleLeft + visibleWidth
        visibleBottom = visibleTop + visibleHeight

        if visibleBottom < bottom:
            bottom = visibleBottom
            top = bottom - height
        if visibleTop > top:
            top = visibleTop

        if visibleRight < right:
            right = visibleRight
            left = right - width
        if visibleLeft > left:
            left = visibleLeft

        return (left, top), image

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
        self._mouseSelection(event, mouseDown=True)
        if event.clickCount() > 1:
            self.vanillaWrapper()._doubleClick()
        self.autoscroll_(event)

    def mouseDragged_(self, event):
        self._mouseSelection(event)
        self.autoscroll_(event)

    def mouseUp_(self, event):
        if self._selection != self._oldSelection:
            self.vanillaWrapper()._selection()
        del self._oldSelection
        if self._glyphDetailMenu is not None:
            self._glyphDetailMenu = None
            self.setNeedsDisplay_(True)

    def _mouseSelection(self, event, mouseDown=False):
        if mouseDown:
            self._oldSelection = set(self._selection)

        eventLocation = event.locationInWindow()
        mouseLocation = self.convertPoint_fromView_(eventLocation, None)

        found = None

        for rect, index in self._clickRectsToIndex.items():
            if NSPointInRect(mouseLocation, rect):
                found = index
                break

        modifiers = event.modifierFlags()
        shiftDown = modifiers & NSShiftKeyMask
        commandDown = modifiers & NSCommandKeyMask
        optionDown = modifiers & NSAlternateKeyMask
        controlDown = modifiers & NSControlKeyMask

        # turn off glyph detail menu if necessary
        if (not controlDown or found is None) and self._glyphDetailMenu is not None:
            self._glyphDetailMenu = None
            self.setNeedsDisplay_(True)

        if found is None:
            return

        # dragging
        if self._allowDrag and mouseDown and optionDown and found in self._selection:
            if found is None:
                return
            else:
                self._beginDrag(event)
                return

        newSelection = None

        # detail menu
        if controlDown and found is not None and self._detailRepresentationName is not None:
            newSelection = set([found])
            x, y = mouseLocation
            x += 10
            y -= 10
            glyph = self._glyphs[found]
            self._glyphDetailMenu = ((int(x), int(y)), glyph.getRepresentation("defconAppKitGlyphCellDetail"))
            self.setNeedsDisplay_(True)
        # selecting
        elif commandDown:
            if found is None:
                return
            if mouseDown:
                if found in self._selection:
                    self._selection.remove(found)
                else:
                    self._selection.add(found)
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
            self.vanillaWrapper()._delete()
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
        s = " ".join([str(i) for i in sorted(self._selection)])
        image = addCountBadgeToIcon(len(self._selection))

        eventLocation = event.locationInWindow()
        location = self.convertPoint_fromView_(eventLocation, None)
        w, h = image.size()
        location = (location[0] - 10, location[1] + 10)

        pboard = NSPasteboard.pasteboardWithName_(NSDragPboard)
        pboard.declareTypes_owner_([DefconAppKitGlyphPboardType], self)
        pboard.setString_forType_(s, DefconAppKitGlyphPboardType)

        self.dragImage_at_offset_event_pasteboard_source_slideBack_(
            image, location, (0, 0),
            event, pboard, self, True
        )

    def getGlyphsFromDragPasteboard_(self, pboard):
        indexes = pboard.stringForType_(DefconAppKitGlyphPboardType)
        indexes = [int(i) for i in indexes.split(" ")]
        glyphs = [self._glyphs[i] for i in indexes]
        return glyphs

    # drop

    def draggingEntered_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        return NSDragOperationCopy

    def draggingUpdated_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        return NSDragOperationCopy

    def draggingExited_(self, sender):
        return None

    def prepareForDragOperation_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        glyphs = source.getGlyphsFromDragPasteboard_(sender.draggingPasteboard())
        return self.vanillaWrapper()._proposeDrop(glyphs, testing=True)

    def performDragOperation_(self, sender):
        source = sender.draggingSource()
        if source == self:
            return NSDragOperationNone
        glyphs = source.getGlyphsFromDragPasteboard_(sender.draggingPasteboard())
        return self.vanillaWrapper()._proposeDrop(glyphs, testing=False)


class GlyphCellView(vanilla.ScrollView):

    def __init__(self, posSize, allowDrag=False,
        selectionCallback=None, doubleClickCallback=None, deleteCallback=None, dropCallback=None,
        cellRepresentationName="defconAppKitGlyphCell", detailRepresentationName="defconAppKitGlyphCellDetail"):
        self._glyphCellView = DefconAppKitGlyphCellNSView.alloc().initWithFrame_cellRepresentationName_detailRepresentationName_(
            ((0, 0), (400, 400)), cellRepresentationName, detailRepresentationName)
        self._glyphCellView.vanillaWrapper = weakref.ref(self)
        super(GlyphCellView, self).__init__(posSize, self._glyphCellView, hasHorizontalScroller=False, autohidesScrollers=True, backgroundColor=backgroundColor)
        self._glyphCellView.subscribeToScrollViewFrameChange_(self._nsObject)
        self._glyphCellView.setAllowsDrag_(allowDrag)
        self._glyphCellView.setAllowsDrop_(dropCallback is not None)
        self._selectionCallback = selectionCallback
        self._doubleClickCallback = doubleClickCallback
        self._deleteCallback = deleteCallback
        self._dropCallback = dropCallback
        self._glyphs = []

    def _breakCycles(self):
        if hasattr(self, "_glyphCellView"):
            self._glyphCellView.unsubscribeToScrollViewFrameChange_(self._nsObject)
            del self._glyphCellView.vanillaWrapper
            del self._glyphCellView
        self._selectionCallback = None
        self._doubleClickCallback = None
        self._deleteCallback = None
        super(GlyphCellView, self)._breakCycles()

    def _selection(self):
        if self._selectionCallback is not None:
            self._selectionCallback(self)

    def _doubleClick(self):
        if self._doubleClickCallback is not None:
            self._doubleClickCallback(self)

    def _delete(self):
        if self._deleteCallback is not None:
            self._deleteCallback(self)

    def _proposeDrop(self, glyphs, testing):
        if self._dropCallback is not None:
            return self._dropCallback(self, glyphs, testing)
        return False

    def __getitem__(self, index):
        return self._glyphs[index]

    def set(self, glyphs):
        self._glyphCellView.setGlyphs_(glyphs)
        self._glyphs = glyphs

    def setCellSize(self, (width, height)):
        self._glyphCellView.setCellSize_((width, height))

    def getSelection(self):
        return self._glyphCellView.getSelection()

    def setSelection(self, selection):
        self._glyphCellView.setSelection_(selection)

    def setCellRepresentationArguments(self, **kwargs):
        self._glyphCellView.setCellRepresentationArguments_(**kwargs)

    def getCellRepresentationArguments(self):
        return self._glyphCellView.getCellRepresentationArguments()

