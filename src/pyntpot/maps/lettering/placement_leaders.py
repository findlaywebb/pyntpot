"""Swapping two flat names over where their leaders cross, and the seat a swap moves.

Key names: `uncross_leaders`, the passes that swap crossing pairs; `reseat`, which moves
a placed flat block to a new middle and rebuilds what hangs off it; `_seat_cost`, a
seat priced on the ground terms the flat placer used; `LEADER_UNCROSS_PASSES`.

It does not place a name in the first place, and draws nothing.

Invariants: a swap is kept only when the pair no longer crosses and costs less
together; a refused swap leaves both names exactly where they were.
"""

import math
from typing import Any

from pyntpot.ink.polyline import Box, Point, meet
from pyntpot.maps.lettering.label import NO_LEADER, TIER_SPAN, Label
from pyntpot.maps.lettering.label_sizing import WRAP_LEADING
from pyntpot.maps.lettering.placement_costs import (
    ROUTE_REACH_PX,
    Backdrop,
    box_on_paper,
    darkness,
    leader_crossings,
    leader_route_crossings,
    near_route,
    off_own_feature,
    on_road,
    overlap,
    route_for,
)
from pyntpot.maps.lettering.placement_flat import (
    LEADER_COST_PX,
    LEADER_CROSS_LABEL_COST,
    LEADER_CROSS_ROUTE_COST,
    ROAD_CROSS_COST,
)
from pyntpot.maps.lettering.placement_water import water_cost

#: How many times the placer looks for two leaders that cross and swaps the
#: names over. The placer is greedy in tier order, so each name takes the
#: cheapest paper it can see and neither of two names knows the other's leader
#: exists; two of them reaching past each other is the result, and it joins
#: the wrong name to the wrong pin. Swapping
#: two crossing leaders always shortens them taken together, so the pass
#: converges, and three sweeps settle every arrangement a card of this size
#: produces.
LEADER_UNCROSS_PASSES = 3


def _leader_px(lb: Label) -> float:
    """How long one label's leader is, in display pixels."""
    return math.dist(lb.leader[0], lb.leader[1]) if lb.leader else 0.0


def _centre(box: Box) -> Point:
    """The middle of a box."""
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _seat(lb: Label) -> tuple[Any, ...]:
    """Everything `reseat` overwrites, so a refused swap can be put back."""
    return (lb.box, lb.tx, lb.ty, lb.anchor, lb.leader)


def _unseat(lb: Label, state: tuple[Any, ...]) -> None:
    """Put a label back where it was before a swap was tried."""
    lb.box, lb.tx, lb.ty, lb.anchor, lb.leader = state


def reseat(lb: Label, cx: float, cy: float) -> None:
    """Move a placed flat block so its middle sits at `(cx, cy)`.

    The block keeps its own width, its own wrap and its own size: only where it
    sits changes, and everything the placer derived from that (the text anchor,
    the first baseline, the leader's text end) is rebuilt from the new middle
    exactly as `_place_flat` derived it from the old one.
    """
    assert lb.box is not None
    assert lb.leader is not None
    x0, y0, x1, y1 = lb.box
    tw, th = x1 - x0, y1 - y0
    ax, ay = lb.leader[0]
    ox = 0 if abs(cx - ax) <= tw / 2 else (1 if cx > ax else -1)
    lb.box = (cx - tw / 2, cy - th / 2, cx + tw / 2, cy + th / 2)
    lb.tx = (cx + (tw / 2 if ox < 0 else -tw / 2)) if ox else cx
    lb.ty = cy + 6 - (len(lb.text_lines) - 1) * lb.size * WRAP_LEADING / 2
    lb.anchor = "middle" if not ox else ("end" if ox < 0 else "start")
    lb.leader = ((ax, ay), (cx - ox * tw / 2 if ox else cx, cy))


def _seat_cost(lb: Label, ground: Backdrop, others: list[Box]) -> float:
    """What one flat block's position costs, leader length aside.

    The same ground terms `_place_flat` scored the candidate on, so a swap that
    would drop a name onto the route, into a wood or across a road is refused
    by the numbers that would have refused it at placement time, water
    included. The leader's
    length is left out because a swap is a trade between two of them and is
    priced over the pair; a leader drawn through a placed label is in, at
    `LEADER_CROSS_LABEL_COST` a label, and one drawn across the route, at
    `LEADER_CROSS_ROUTE_COST` a crossing.
    """
    box = lb.box
    assert box is not None
    cost = 0.0 if box_on_paper(box, ground.card) else 400.0
    route = route_for(lb, ground.route_px, ground.thin)
    cost += near_route(box, route, max(ROUTE_REACH_PX, lb.size))
    cost += overlap(box, others)
    cost += darkness(box, ground.card, ground.dark) * 150
    cost += on_road(box, ground.roads) * ROAD_CROSS_COST
    cost += off_own_feature(box, lb)
    if not lb.in_water:
        cost += water_cost(box, ground.water, lb.size)
    if lb.leader is not None and lb.tier != TIER_SPAN and lb.kind not in NO_LEADER:
        cost += leader_crossings(*lb.leader, others) * LEADER_CROSS_LABEL_COST
        cost += leader_route_crossings(*lb.leader, ground.segments) * LEADER_CROSS_ROUTE_COST
    return cost


def _pair_cost(a: Label, b: Label, ground: Backdrop, others: list[Box]) -> float:
    """What two names cost where they currently sit, leaders included.

    `b` is costed against `a`'s box as well as the rest of the map, so the
    overlap the two would make with each other is charged once rather than
    twice or not at all.
    """
    assert a.box is not None
    return (
        _seat_cost(a, ground, others)
        + _seat_cost(b, ground, [*others, a.box])
        + (_leader_px(a) + _leader_px(b)) * LEADER_COST_PX
    )


def _swap_seats(a: Label, b: Label, placed: list[Label], ground: Backdrop) -> bool:
    """Put each of two names where the other was, and keep it if it reads better.

    Returns True when the swap was kept.
    """
    others = [lb.box for lb in placed if lb is not a and lb is not b and lb.box is not None]
    was = (_seat(a), _seat(b))
    before = _pair_cost(a, b, ground, others)
    assert a.box is not None
    assert b.box is not None
    here, there = _centre(a.box), _centre(b.box)
    reseat(a, *there)
    reseat(b, *here)
    assert a.leader is not None
    assert b.leader is not None
    crossed = meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    after = _pair_cost(a, b, ground, others)
    if not crossed and after < before:
        return True
    _unseat(a, was[0])
    _unseat(b, was[1])
    return False


def uncross_leaders(placed: list[Label], ground: Backdrop) -> None:
    """Swap two names over where their leaders cross.

    The placer is greedy in tier order: each name takes the cheapest paper it
    can see, and neither of two names knows that the other has a leader at all.
    Two of them reaching past each other is what comes of that, and a reader
    meeting a crossing follows the wrong line to the wrong pin. Swapping the
    two names over is the fix rather than moving either of them away, because
    the paper each is sitting on was already the cheapest either could find and
    exchanging them strictly shortens the two leaders taken together.

    A swap is offered, not imposed. It is kept only when the pair no longer
    crosses *and* the two names together cost less than they did, on the same
    ground terms the placer priced them with, so a name is never swapped onto
    the route or into a wood to straighten a line.
    """
    seats = [lb for lb in placed if lb.flat and lb.leader is not None and lb.box is not None]
    for _ in range(LEADER_UNCROSS_PASSES):
        swapped = False
        for i, a in enumerate(seats):
            for b in seats[i + 1 :]:
                assert a.leader is not None
                assert b.leader is not None
                if meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is None:
                    continue
                swapped |= _swap_seats(a, b, placed, ground)
        if not swapped:
            return
