"""A span's end ticks and its name: where each is drawn beside the mark.

Key names: `_span_ticks`, the two short ticks at the ends of a span that point at the
stretch of route it covers; `_span_label`, the name a span carries, set along its line
when the span runs across the page and beside it when it does not.

It does not draw the span's line, choose its side or place the name among the others
(the placer does that with every other name).

Invariants: a tick is left off when even a short one would touch the route; a name
set along a line sits on the far side of the line from the route.
"""

import math

from pyntpot.ink.polyline import Pt, length
from pyntpot.maps.lettering.label import TIER_SPAN, Label, Measure, Span, _outboard
from pyntpot.maps.lettering.span_clear import (
    _FEWEST_FOR_A_SEGMENT,
    _ZERO_PX,
    SPAN_ALONG_MAX_BEARING_DEG,
    SPAN_CLEAR_CAPS,
    clear_of_route,
    span_bearing,
)

#: How long a span's end tick is, in cap heights. It runs from the end of the
#: mark towards the end of the stretch on the road, taking the direction of
#: the segment rather than standing exactly perpendicular to the local route.
#: A tick square to the route reads as wrong.
SPAN_TICK_CAPS = 0.85


def _span_ticks(span: Span, route_px: list[Pt], cap_px: float) -> list[list[Pt]]:
    """A tick from each end of the mark, pointing at the end of the stretch.

    The end marks run from the end of the line towards the end of the segment,
    not perpendicular to the local route. So the direction is the
    vector from where the mark stops to where the span stops on the road, and
    nothing else: not the route's own bearing at that index, which is a
    property of two GPS samples rather than of anything the reader can see, and
    not the mark's own bearing, which the smoothing chose.

    It is one stroke off the end of the line rather than a cross-mark on it,
    which is what "from the end of the line" says. A tick is part of the mark,
    so rule seven binds it too: it is shortened until its tip clears the road
    it points at, and left off when even a short one would touch it.
    """
    if len(span.line) < _FEWEST_FOR_A_SEGMENT:
        return []
    out = []
    length = cap_px * SPAN_TICK_CAPS
    clear = cap_px * SPAN_CLEAR_CAPS
    for end, at in ((span.line[0], span.i0), (span.line[-1], span.i1)):
        target = route_px[at]
        run = math.dist(end, target)
        if run < _ZERO_PX:
            continue
        ux, uy = (target[0] - end[0]) / run, (target[1] - end[1]) / run
        reach = min(length, max(run - clear, 0.0))
        while reach > length * 0.25:
            tick = [end, (end[0] + ux * reach, end[1] + uy * reach)]
            if clear_of_route(tick, route_px, clear):
                out.append(tick)
                break
            reach -= length * 0.1
    return out


def _span_label(
    span: Span,
    route_px: list[Pt],
    cap_px: float,
    measure_fn: Measure,
    along_max_deg: float = SPAN_ALONG_MAX_BEARING_DEG,
) -> Label:
    """The span's own name: along the line where that reads, beside it where not.

    A span whose line is too short to carry its own name falls back to the same
    horizontal treatment as a steep one, because the alternative is a name that
    runs off both ends of the bracket it belongs to.
    """
    mid = span.line[len(span.line) // 2] if span.line else (0.0, 0.0)
    size = cap_px * (1.0 if span.ground else 0.85)
    lift = _outboard(span, route_px)
    width, _h = measure_fn(span.name, size)
    along = (
        bool(span.line)
        and span_bearing(span.line) <= along_max_deg
        and length(span.line) >= width * 1.02
    )
    anchors: list[Pt] = []
    if not along and span.line:
        # Anchored on the outboard side of the line, so the placer looks for
        # its clear paper on the far side from the route rather than in the gap
        # between the route and the bracket. Offered at points along the whole
        # bracket rather than at its middle alone: the middle of a short
        # bracket in a busy corner may have another name sitting over it, and a
        # name pushed out of the way from there ends up further from the line
        # than one that simply slid along it.
        nx, ny = _span_normal(span.line)
        push = lift * cap_px * 0.9
        anchors = [_beside(span.line, f, (nx * push, ny * push)) for f in SPAN_ANCHOR_FRACS]
        mid = anchors[len(anchors) // 2]
    return Label(
        name=span.name,
        kind=span.kind,
        why=span.why,
        px=mid[0],
        py=mid[1],
        tier=TIER_SPAN,
        size=size,
        box=None,
        tx=mid[0],
        ty=mid[1],
        anchor="middle",
        intent=span.intent,
        lift=lift,
        span_range=(span.i0, span.i1),
        mark=list(span.line),
        anchors=anchors,
        baseline=list(span.line) if along else [],
    )


#: Where along its own bracket a span's name may be anchored, as fractions of
#: the bracket's run. The middle is one of them and is still what the label
#: carries as its anchor; the others let a name slide along the line it belongs
#: to instead of being pushed off it.
SPAN_ANCHOR_FRACS = (0.15, 0.325, 0.5, 0.675, 0.85)


def _beside(line: list[Pt], frac: float, push: Pt) -> Pt:
    """A point a fraction along a line, shifted by one offset.

    The shift is the same vector at every fraction, taken from the line's
    middle, and not a local normal. A bracket beside a stretch that doubles
    back turns right round inside its own length, so a local normal at one end
    of it points where a local normal at the other end came from: anchors built
    that way put a name on the far side of the road from its own mark.
    """
    run = length(line)
    want, walked = run * frac, 0.0
    at = len(line) - 1
    for i in range(len(line) - 1):
        step = math.dist(line[i], line[i + 1])
        if walked + step >= want:
            at = i
            break
        walked += step
    p = line[at]
    return (p[0] + push[0], p[1] + push[1])


def _span_normal(line: list[Pt]) -> Pt:
    """The unit normal to a span line at its middle, pointing to +1 lift."""
    i = len(line) // 2
    a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
    run = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
    return ((b[1] - a[1]) / run, -(b[0] - a[0]) / run)
