"""Placing every name on the card: the order, the leaders, and the swaps that uncross them.

Key names: `place`, which places every label and every span request in tier order and
then swaps leaders that cross; `_place`, one name's cheapest seat; `_seat`, `_unseat`
and `_reseat`, a name's seat and the state a move of it changes; `_uncross_leaders`,
the pairs of leaders swapped over.

It does not pick what is named (a caller hands in the labels), does not measure a name
(the caller's `measure` does) and draws nothing.

Invariants: labels come back in tier order each carrying its box, anchor and window;
a name that repeats another's place is dropped; no seat is left the leader of a pair
that crosses when swapping them over makes both cheaper.
"""

import math
from typing import Any

from pyntpot.ink.polyline import Pt, meet
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.lettering.label import WRAP_LEADING, Box, Label, Measure, Span
from pyntpot.maps.lettering.placement_along import _place_along
from pyntpot.maps.lettering.placement_costs import (
    ROUTE_REACH_PX,
    Backdrop,
    Terms,
    _darkness,
    _near_route,
    _off_own,
    _off_own_feature,
    _on_paper,
    _on_road,
    _overlap,
)
from pyntpot.maps.lettering.placement_flat import LEADER_COST_PX, ROAD_CROSS_COST, _best_flat
from pyntpot.maps.lettering.placement_lift import TILT_EXEMPT_KINDS
from pyntpot.maps.lettering.placement_names import dedupe_names
from pyntpot.maps.lettering.spans import SpanSurroundings, place_spans

#: How many times the placer looks for two leaders that cross and swaps the
#: names over. The placer is greedy in tier order, so each name takes the
#: cheapest paper it can see and neither of two names knows the other's leader
#: exists; two of them reaching past each other is the result, and it joins
#: the wrong name to the wrong pin. Swapping
#: two crossing leaders always shortens them both, so the pass converges, and
#: three sweeps settle every arrangement a card of this size produces.
LEADER_UNCROSS_PASSES = 3


#: What a span's own stretch of route counts for, against every other part of
#: the track. A quarter: enough to break a tie between two windows on the same
#: bracket, not enough to send the name away from the bracket altogether.
SPAN_OWN_ROUTE_FRAC = 0.25


#: What setting a name on the thing it names is worth, against setting it in
#: clear paper beside it. A river written along its water and a span written
#: along its bracket both say something a horizontal name cannot, so the curve
#: wins ties and wins near-ties; it does not win when the only window left puts
#: the name on top of two others.
ALONG_BONUS = 70.0


#: Under this many characters a curve is noise rather than a baseline. Three,
#: because "Eden" is a river name and the whole reason a river has a baseline is
#: that the water says which water it is.
MIN_CURVED_CHARS = 3


def place(
    labels: list[Label],
    spans: list[Span],
    ground: Backdrop,
    taken: list[Box],
    measure_fn: Measure,
) -> list[Label]:
    """Put every name somewhere, cheapest cost first, in tier order.

    Curved names are placed here too, which they were not: a river or a road or
    a span used to claim the box its anchor happened to fall in and then be set
    along a window chosen afterwards, at drawing time, by the hand. That is why
    "Derwent" sat over "Braemar Castle": the box the placer defended and the
    pixels the reader saw were in different places. The window is chosen here
    now, against everything already on the sheet, and the run of small boxes it
    really occupies goes back into the pile for the next name to avoid.

    It is also the one funnel every name on the sheet goes through, whichever
    pool found it, so it is where `dedupe_names` can see that the settlement
    "Elm" and the nearest-named-feature "Elm" are one village.

    Returns fewer labels than it was given where two of them named one place.

    Args:
        labels: The names to place, each with its anchor already in card pixels.
        spans: Spans to place first, so a span line is on the sheet before
            anything looks for room. Placed in place; their names join the
            queue and are placed with everything else.
        ground: The card, the track in card pixels, the painter's darkness
            grid and the named road centrelines. A name laid across a road is
            costed, never forbidden.
        taken: Boxes already spoken for, such as the home glyph's.
        measure_fn: How wide and tall a name is.

    Returns:
        The same labels, in tier order, each carrying its box, its text anchor
        and, when it is set along a line, the run of line it is set along.
    """
    boxes = list(taken)
    todo = list(labels)
    if spans:
        around = SpanSurroundings(
            ground.card, ground.route_px, ground.dark, _places_to_avoid(labels), ground.roads
        )
        place_spans(spans, around, measure_fn)
        todo += [span.label for span in spans if span.label is not None]
    ordered = sorted(dedupe_names(todo, ground.card), key=lambda lb: lb.tier)
    return _place(ordered, ground, boxes, measure_fn)


#: How far a settlement's own ground reaches, in multiples of the size its
#: name is lettered at. A town is lettered larger than a village and takes up
#: more of the sheet, so one number covers both. Three: on a 900 px card that
#: is about 70 px round a town, which is the built-up part of the corner a
#: span mark is drawn round rather than through.
SETTLEMENT_GROUND_SIZES = 3.0


def _places_to_avoid(labels: list[Label]) -> list[tuple[float, float, float, float]]:
    """The settlements a span mark would rather not be drawn through.

    `(x, y, weight, radius)` in card pixels, weighted by how large the name is
    set, which is how the sheet already says how big the place is.
    """
    return [
        (lb.px, lb.py, lb.size / DEFAULT_LINE_PX, lb.size * SETTLEMENT_GROUND_SIZES)
        for lb in labels
        if lb.kind == "settlement"
    ]


def _place(
    labels: list[Label], ground: Backdrop, boxes: list[Box], measure_fn: Measure
) -> list[Label]:
    """Place each label, curved along its own line where it has one.

    The cost is what the reader would complain about: text over the route, text
    on top of another label, text on a dark wash, text laid across a road. The
    card's edge is not in that list because it is not a cost: a candidate on
    the paper beats every candidate off it outright.
    """
    placed: list[Label] = []
    route_px, thin = ground.route_px, ground.thin
    # Where each name has already been set along its own line, so the major
    # river's second name lands somewhere else on the water rather than beside
    # its first.
    repeats: dict[str, list[float]] = {}
    for lb in labels:
        tw, th = measure_fn(lb.name, lb.size)
        mine = _route_for(lb, route_px, thin)
        terms = Terms(ground.card, ground.dark, boxes, _off_own(ground.roads, lb), mine)
        along = None
        if lb.baseline and len(lb.name) >= MIN_CURVED_CHARS:
            along = _place_along(lb, tw, th, terms, repeats.get(lb.name, []))
        flat = _best_flat(lb, terms, measure_fn)
        # Two real candidates, one scale. Setting a name on its own feature is
        # worth something in itself, and `ALONG_BONUS` is that something; past
        # it, a name jammed against three others on its river is worse than the
        # same name in clear paper beside it, and the placer should be able to
        # say so rather than always preferring the curve.
        #
        # A river is the exception: where its own water
        # offers any usable window at all the name goes on the water, whatever
        # the flat answer costs.
        if along is not None and lb.kind in TILT_EXEMPT_KINDS:
            flat = float("inf")
        if along is not None and along[0] - ALONG_BONUS < flat:
            cells, window = along[1], along[2]
            lb.window = window
            lb.lift = along[4]
            lb.flat = False
            # A name on a curve is one line by construction.
            lb.lines = []
            xs = [v for box in cells for v in (box[0], box[2])]
            ys = [v for box in cells for v in (box[1], box[3])]
            lb.box = (min(xs), min(ys), max(xs), max(ys))
            lb.tx, lb.ty = window[len(window) // 2]
            lb.anchor = "middle"
            lb.leader = None
            boxes.extend(cells)
            repeats.setdefault(lb.name, []).append(along[3])
        else:
            assert lb.box is not None
            boxes.append(lb.box)
        placed.append(lb)
    _uncross_leaders(placed, ground)
    return placed


def _leader_px(lb: Label) -> float:
    """How long one label's leader is, in card pixels."""
    return math.dist(lb.leader[0], lb.leader[1]) if lb.leader else 0.0


def _centre(box: Box) -> Pt:
    """The middle of a box."""
    return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)


def _seat(lb: Label) -> tuple[Any, ...]:
    """Everything `_reseat` overwrites, so a refused swap can be put back."""
    return (lb.box, lb.tx, lb.ty, lb.anchor, lb.leader)


def _unseat(lb: Label, state: tuple[Any, ...]) -> None:
    """Put a label back where it was before a swap was tried."""
    lb.box, lb.tx, lb.ty, lb.anchor, lb.leader = state


def _reseat(lb: Label, cx: float, cy: float) -> None:
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
    by the numbers that would have refused it at placement time. The leader is
    left out because a swap is a trade between two of them and is priced over
    the pair.
    """
    box = lb.box
    assert box is not None
    cost = 0.0 if _on_paper(box, ground.card) else 400.0
    route = _route_for(lb, ground.route_px, ground.thin)
    cost += _near_route(box, route, max(ROUTE_REACH_PX, lb.size))
    cost += _overlap(box, others)
    cost += _darkness(box, ground.card, ground.dark) * 150
    cost += _on_road(box, ground.roads) * ROAD_CROSS_COST
    cost += _off_own_feature(box, lb)
    return cost


def _pair_cost(a: Label, b: Label, ground: Backdrop, others: list[Box]) -> float:
    """What two names cost where they currently sit, leaders included.

    `b` is costed against `a`'s box as well as the rest of the sheet, so the
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
    _reseat(a, *there)
    _reseat(b, *here)
    assert a.leader is not None
    assert b.leader is not None
    crossed = meet(a.leader[0], a.leader[1], b.leader[0], b.leader[1]) is not None
    after = _pair_cost(a, b, ground, others)
    if not crossed and after < before:
        return True
    _unseat(a, was[0])
    _unseat(b, was[1])
    return False


def _uncross_leaders(placed: list[Label], ground: Backdrop) -> None:
    """Swap two names over where their leaders cross.

    The placer is greedy in tier order: each name takes the cheapest paper it
    can see, and neither of two names knows that the other has a leader at all.
    Two of them reaching past each other is what comes of that, and a reader
    meeting a crossing follows the wrong line to the wrong pin. Swapping the
    two names over is the fix rather than moving either of them away, because
    the paper each is sitting on was already the cheapest either could find and
    exchanging them strictly shortens both leaders.

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


def _route_for(lb: Label, route_px: list[Pt], thin: list[Pt]) -> list[tuple[list[Pt], float]]:
    """The route this label keeps off, and how much each part of it counts.

    A span's bracket is drawn beside its own extent, so its name is near that
    stretch by design, and charging the full price there would rule out the one
    position the span is meant to take. It is not free either: given two windows
    on the same bracket, the one that does not have the track running through
    the middle of the word is the better one, and at a quarter weight the placer
    can say so without the answer being decided by it.
    """
    if lb.span_range is None:
        return [(thin, 1.0)]
    i0, i1 = lb.span_range
    own = [p for j, p in enumerate(thin) if i0 <= j * 3 <= i1]
    rest = [p for j, p in enumerate(thin) if not (i0 <= j * 3 <= i1)]
    out: list[tuple[list[Pt], float]] = [(rest, 1.0)] if rest else []
    if own:
        out.append((own, SPAN_OWN_ROUTE_FRAC))
    return out or [(thin, 1.0)]
