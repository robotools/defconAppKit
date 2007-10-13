from AppKit import NSBezierPath

def roundedRectBezierPath(rect, radius,
        roundUpperLeft=True, roundUpperRight=True, roundLowerLeft=True, roundLowerRight=True,
        closeTop=True, closeBottom=True, closeLeft=True, closeRight=True):

    (rectLeft, rectBottom), (rectWidth, rectHeight) = rect
    rectTop = rectBottom + rectHeight
    rectRight = rectLeft + rectWidth

    path = NSBezierPath.bezierPath()

    if roundUpperLeft:
        path.moveToPoint_((rectLeft, rectHeight-radius))
        path.appendBezierPathWithArcFromPoint_toPoint_radius_((rectLeft, rectTop), (rectLeft+radius, rectTop), radius)
    else:
        path.moveToPoint_((rectLeft, rectTop))

    if roundUpperRight:
        if closeTop:
            path.lineToPoint_((rectRight-radius, rectTop))
        else:
            path.moveToPoint_((rectRight-radius, rectTop))
        path.appendBezierPathWithArcFromPoint_toPoint_radius_((rectRight, rectTop), (rectRight, rectTop-radius), radius)
    else:
        if closeTop:
            path.lineToPoint_((rectRight, rectTop))
        else:
            path.moveToPoint_((rectRight, rectTop))

    if roundLowerRight:
        if closeRight:
            path.lineToPoint_((rectRight, rectBottom+radius))
        else:
            path.moveToPoint_((rectRight, rectBottom+radius))
        path.appendBezierPathWithArcFromPoint_toPoint_radius_((rectRight, rectBottom), (rectRight-radius, rectBottom), radius)
    else:
        if closeRight:
            path.lineToPoint_((rectRight, rectBottom))
        else:
            path.moveToPoint_((rectRight, rectBottom))

    if roundLowerLeft:
        if closeBottom:
            path.lineToPoint_((rectLeft+radius, rectBottom))
        else:
            path.moveToPoint_((rectLeft+radius, rectBottom))
        path.appendBezierPathWithArcFromPoint_toPoint_radius_((rectLeft, rectBottom), (rectLeft, rectBottom+radius), radius)
    else:
        if closeBottom:
            path.lineToPoint_((rectLeft, rectBottom))
        else:
            path.moveToPoint_((rectLeft, rectBottom))

    if closeLeft:
        if roundUpperLeft:
            path.lineToPoint_((rectLeft, rectHeight-radius))
        else:
            path.lineToPoint_((rectLeft, rectTop))

    return path