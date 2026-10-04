"""Setting a name flat beside its anchor, on the cheapest rung, broken over lines when that pays.

Key names: `_place_flat`, one horizontal name tried on every side of its anchor at every
rung of the ladder; `_best_flat`, the cheapest answer over every way the name may be
broken; `ROAD_CROSS_COST`, `LEADER_COST_PX`, `SEPARATION_WEIGHT` and `WRAP_COST`, the
prices the answers are weighed in.

It does not set a name along a line, choose the order names are placed in or swap
leaders afterwards, and it draws nothing.

Invariants: a position on the paper always beats one off it, and the label is left
holding the form and the position that won.
"""

from typing import Any

from pyntpot.maps.lettering.label import (
    NO_LEADER,
    TIER_SPAN,
    WRAP_LEADING,
    Label,
    Measure,
    block_size,
    wrap_forms,
)
from pyntpot.maps.lettering.placement_costs import (
    ROUTE_REACH_PX,
    Terms,
    _darkness,
    _near_route,
    _off_own_feature,
    _on_paper,
    _on_road,
    _overlap,
    _separation,
)
from pyntpot.maps.lettering.placement_marks import SPAN_MARK_COST_PX, _mark_gap, _mark_through

#: What a name laid across a road costs. Not a constraint: sometimes there is
#: nowhere else, and a name that vanished would be worse than one that crosses
#: a lane. It is priced against the leader, which costs `LEADER_COST_PX` a
#: pixel, so this buys about two hundred pixels of leader. That ratio is the
#: rule: a longer leader is a cheaper thing to spend than a road crossing, and "Braemar Castle" should step left rather than let
#: "Castle" sit on the tarmac.
ROAD_CROSS_COST = 90.0


#: What a pixel of leader costs, so the two are directly comparable.
LEADER_COST_PX = 0.4


#: How far a candidate may reach from its anchor before the leader is silly.
#: Four rungs, because with a road crossing priced at ninety the placer needs
#: somewhere further out to step to.
LEADER_RUNGS = (16.0, 30.0, 46.0, 64.0)


#: What clear space is worth. Absence of collision is not the same as being
#: legible: where several positions are all valid the one furthest from
#: everything already on the sheet is the one to take, and this is what a pixel
#: of that distance is worth against the rest of the cost.
SEPARATION_WEIGHT = 0.55


#: Where a leaderless name sits, in display pixels of clear space from the mark
#: it belongs to, and what a pixel of that gap costs. Far tighter than a
#: leadered label's, and for the reason the leader exists: with no line drawn
#: between them, the only thing joining a name to its mark is that they are
#: near each other, so the name has to stay near. A span, a settlement, a river
#: that could not be set along its water and a road all take these.
NEAR_RUNGS = (7.0, 12.0, 20.0, 30.0)


NEAR_GAP_COST_PX = 4.0


#: What a second line costs, so it is taken only when it buys a materially
#: better position rather than whenever it is marginally cheaper. Priced above
#: a rung of leader and below a road crossing: worth having to get off the
#: route, not worth having to save a few pixels of separation.
#:
#: Chosen by argument first and now measured against a card that exercises it.
#: On the Dovedale ride, "the long climb out of Keswick" costs 190.4 on
#: one line and 133.7 on its best two, so a break buys 56.7; "the A591 climb
#: past Ambleside" costs 107.1 against 105.5, so a break buys 1.6. Anything
#: from about 2 to about 56 separates those two cases, and 26 is the middle of
#: that window: the first wraps, the second does not, and neither is close to
#: the edge.
WRAP_COST = 26.0


def _best_flat(lb: Label, terms: Terms, measure_fn: Measure) -> float:
    """The cheapest horizontal answer over every way the name may be broken.

    A second line is charged `WRAP_COST`, so it is taken when it buys a
    materially better position and not when it merely ties. The label is left
    holding whichever form won, with the block's own box.
    """
    best: tuple[float, list[str], Any] | None = None
    for form in wrap_forms(lb.name, lb.kind, lb.tier):
        tw, th = block_size(form, lb.size, measure_fn)
        cost = _place_flat(lb, tw, th, terms, len(form))
        cost += WRAP_COST * (len(form) - 1)
        state = (lb.box, lb.tx, lb.ty, lb.anchor, lb.leader)
        if best is None or cost < best[0]:
            best = (cost, form, state)
    assert best is not None
    cost, form, state = best
    lb.lines = form if len(form) > 1 else []
    lb.box, lb.tx, lb.ty, lb.anchor, lb.leader = state
    lb.window = []
    lb.flat = True
    return cost


def _seat_block(
    lb: Label,
    chosen: tuple[float, float, float, float, float, int, float, float],
    tw: float,
    th: float,
    nlines: int,
) -> None:
    """Fill the label in with the position the cheapest rung chose."""
    _cost, cx, cy, x0, y0, ox, ax, ay = chosen
    lb.window = []
    lb.flat = True
    lb.box = (x0, y0, x0 + tw, y0 + th)
    lb.tx = (cx + (tw / 2 if ox < 0 else -tw / 2)) if ox else cx
    # The first baseline, not the block's middle: a two-line name is written
    # downwards from here and the block has to stay centred on the box.
    lb.ty = cy + 6 - (nlines - 1) * lb.size * WRAP_LEADING / 2
    lb.anchor = "middle" if not ox else ("end" if ox < 0 else "start")
    lb.leader = ((ax, ay), (cx - ox * tw / 2 if ox else cx, cy))


def _place_flat(
    lb: Label,
    tw: float,
    th: float,
    terms: Terms,
    nlines: int = 1,
) -> float:
    """One horizontal name beside its anchor, on the cheapest rung that fits.

    Fills the label in and returns what that answer cost, so the caller can
    hold it against setting the same name along its own line.
    """
    offs = [(1, 0), (-1, 0), (1, -1), (-1, -1), (1, 1), (-1, 1), (0, -1), (0, 1)]
    near_mark = lb.tier == TIER_SPAN or lb.kind in NO_LEADER
    rungs = NEAR_RUNGS if near_mark else LEADER_RUNGS
    per_px = NEAR_GAP_COST_PX if near_mark else LEADER_COST_PX
    best = None
    on_paper = None
    for ax, ay in lb.anchors or [(lb.px, lb.py)]:
        for ox, oy in offs:
            for dist in rungs:
                cx = ax + ox * (dist + tw / 2 if ox else 0)
                cy = ay + oy * (dist + th / 2 if oy else 0)
                if not ox:
                    cx = ax
                x0, y0 = cx - tw / 2, cy - th / 2
                box = (x0, y0, x0 + tw, y0 + th)
                cost = 0.0
                inside = _on_paper(box, terms.card)
                if not inside:
                    cost += 400
                cost += _near_route(box, terms.route, max(ROUTE_REACH_PX, lb.size))
                cost += _overlap(box, terms.boxes)
                cost += _darkness(box, terms.card, terms.dark) * 150
                cost += _on_road(box, terms.roads) * ROAD_CROSS_COST
                cost += _off_own_feature(box, lb)
                gap_px = SPAN_MARK_COST_PX if lb.tier == TIER_SPAN else per_px
                cost += _mark_gap(box, lb, dist) * gap_px
                cost += _mark_through(box, lb)
                cost -= _separation(box, terms.boxes) * SEPARATION_WEIGHT
                here = (cost, cx, cy, x0, y0, ox, ax, ay)
                if best is None or cost < best[0]:
                    best = here
                if inside and (on_paper is None or cost < on_paper[0]):
                    on_paper = here
    chosen = on_paper or best
    assert chosen is not None
    _seat_block(lb, chosen, tw, th, nlines)
    return chosen[0]
