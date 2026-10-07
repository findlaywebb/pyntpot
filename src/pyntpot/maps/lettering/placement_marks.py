"""What a span's name pays for sitting near its own mark.

Key names: `_mark_gap`, how far a name sits from the mark beside the route;
`_mark_through`, what the mark running through the name costs.

It does not choose a position or move a mark.

Invariants: a name that is not a span's is charged its rung's distance by `_mark_gap`
and nothing by `_mark_through`.
"""

import math

from pyntpot.ink.polyline import foot_on
from pyntpot.maps.lettering.label import TIER_SPAN, Box, Label

#: Below this a distance in pixels is zero.
_ZERO_PX = 1e-6

#: How far the middle of a span's name may sit from its own bracket before the
#: gap starts costing, as a multiple of the type size.
#:
#: A block set immediately beside the middle of a bracket has its middle about
#: one line height off it however tight the placement is, so a gap cost with no
#: slack in it is a magnet: it pulls the name onto the bracket and then onto
#: the road the bracket belongs to, whose own cost is at a quarter weight over
#: the span's own stretch. With the first line height and a half free, the
#: proximity cost says nothing at all about the placements that are already
#: near enough and everything about the ones that are not, and the route cost
#: still decides between the near ones.
SPAN_MARK_SLACK = 1.5


#: What a pixel of that gap costs a span, once the slack is used up. Heavier
#: than the leaderless cost every other kind pays, because a bracket is a mark
#: the renderer drew and a reader has nothing else to go on: a river name near
#: the wrong bend is still on the right river, and a span name near the wrong
#: bracket belongs to nothing at all.
SPAN_MARK_COST_PX = 14.0


#: What writing a name across its own bracket costs. The proximity cost above
#: pulls a name towards its mark and, on its own, pulls it right onto it: the
#: cheapest block of all is the one centred on the line, and the reader gets
#: the bracket struck through the middle of the words. Priced a little above a
#: road crossing, so a name beside its own line always beats a name over it.
SPAN_MARK_THROUGH_COST = 110.0


#: What sitting on the route's side of its own bracket costs a span's name.
#: The order the eye crosses should be route, line, name: the bracket is what
#: says which stretch of road the name is about, and a name in the gap between
#: the bracket and the road it belongs to has the mark reading as a rule drawn
#: under it rather than as a bracket beside the route. The anchors are outboard
#: already; without this the rungs walk the block straight back over them.
SPAN_INBOARD_COST = 150.0


def _mark_gap(box: Box, lb: Label, fallback: float) -> float:
    """How far a block sits from the mark it names, for the leaderless cost.

    A rung is the clear space between the anchor and the near edge of the
    block, which is the right measure for a name beside a point and the wrong
    one beside a line. Off the end of a short bracket a wide block clears the
    anchor by one rung and then runs on for its own width, and nothing in the
    cost notices, so a name can read as belonging to nothing.

    A span is measured over the whole block instead: its middle and its four
    corners, each against the nearest point of its own bracket, each allowed
    the slack, and the five averaged. The middle alone is not enough, because
    a long single line centred on a short bracket has its middle on the mark
    and both its ends in open country; charging the corners is what makes a
    compact two-line block beside the line the cheap answer and a banner across
    it the dear one.
    """
    if lb.tier != TIER_SPAN or not lb.mark:
        return fallback
    x0, y0, x1, y1 = box
    slack = lb.size * SPAN_MARK_SLACK
    at = [((x0 + x1) / 2, (y0 + y1) / 2), (x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    gaps = [
        max((foot_on(p, lb.mark)[0] if len(lb.mark) > 1 else math.dist(p, lb.mark[0])) - slack, 0.0)
        for p in at
    ]
    return sum(gaps) / len(gaps)


def _mark_through(box: Box, lb: Label) -> float:
    """What a block across, or inboard of, its own bracket costs.

    Two faults with one measure, because both are about where the block sits
    relative to the line rather than how far off it is: the bracket struck
    through the words, and the block sitting in the gap between the bracket and
    the road it brackets.
    """
    if lb.tier != TIER_SPAN or not lb.mark:
        return 0.0
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    hw, hh = (box[2] - box[0]) / 2, (box[3] - box[1]) / 2
    cost = 0.0
    for px, py in lb.mark:
        if abs(px - cx) <= hw and abs(py - cy) <= hh:
            cost += SPAN_MARK_THROUGH_COST
            break
    mid = lb.mark[len(lb.mark) // 2]
    out = (lb.px - mid[0], lb.py - mid[1])
    run = math.hypot(*out)
    if run < _ZERO_PX:
        return cost
    _d, foot = foot_on((cx, cy), lb.mark)
    side = ((cx - foot[0]) * out[0] + (cy - foot[1]) * out[1]) / run
    if side < 0.0:
        cost += SPAN_INBOARD_COST
    return cost
