"""Setting a name along a road, river or bracket line at the cheapest window of it.

Key names: `_place_along`, the window of a line a name is set along, tried on both sides
of the line where the kind allows it; `_window_shape`, whether a window bends too far to
read; `_ground_cost`, what a window costs a reader, on the terms the flat answer is
scored on; the constants that say how far a window may turn and bow.

It does not set a name flat, choose the order names are placed in or swap leaders
afterwards, and it draws nothing.

Invariants: a window is used only when it is straight enough to read for its kind, and
the cost returned is on the same scale as the flat answer so the two can be compared.
"""

import math

from pyntpot.ink.polyline import Pt, cumulative_length, length
from pyntpot.maps.lettering.label import (
    TIER_SPAN,
    Box,
    Label,
)
from pyntpot.maps.lettering.placement_costs import (
    ROUTE_REACH_PX,
    Terms,
    _darkness,
    _near_route,
    _on_paper,
    _on_road,
    _overlap,
    _separation,
)
from pyntpot.maps.lettering.placement_flat import ROAD_CROSS_COST, SEPARATION_WEIGHT
from pyntpot.maps.lettering.placement_lift import (
    MAX_LOCAL_TILT_DEG,
    MAX_TILT_DEG,
    TILT_EXEMPT_KINDS,
    _curved_boxes,
    _reading,
    _tilt,
    _tilt_max,
)
from pyntpot.maps.lettering.placement_window import (
    MAX_BOW_FRAC,
    MAX_TURN_DEG,
    _bow,
    _turning,
    _window,
)
from pyntpot.maps.lettering.span_line import _resample

#: What a pixel of travel away from where a curved name started costs. Light,
#: because the freedom to slide along the whole feature is the point; not zero,
#: because with the separation reward and nothing pulling back, two names of one
#: river both run to opposite corners of the card and neither ends up where the
#: river is worth naming.
ANCHOR_PULL = 0.22


#: The kinds whose name may sit on either side of the line it follows. A river
#: and a road are lines on the ground with paper on both sides of them, and
#: which side reads better is a question about what is underneath, not about
#: the feature: it is answered by the same cost as everything else.
TWO_SIDED_KINDS = ("river", "road")


#: What the ground terms a river's window is scored on are discounted by. A
#: river follows its bend, so the only thing these terms decide is *which*
#: bend, and at full price they would decide it wrongly: a river
#: crossing a pale wash or a thin lane is ordinary cartography and should not
#: be priced like a name laid across a road. Overlap with another label is not
#: discounted, because two names on top of each other is still two names on top
#: of each other.
RIVER_GROUND_FRAC = 0.35


#: What a bridge under a name written on the water costs, per share of the name
#: that sits on one. Priced with the route rather than with `ROAD_CROSS_COST`:
#: a name in clear paper clipping a lane is ordinary and cheap to allow, and a
#: river's name with a bridge drawn through its letters is neither.
IN_WATER_ROAD_COST = 320.0


#: What a span's own bracket may do, which is more than a river's water may.
#: A river is a fact about the ground and the reader meets its name without
#: having been following the water; a span's name and its bracket are one
#: gesture drawn together, and the eye arrives at the name already travelling
#: along the line, so it forgives a curve a river's name could not take.
SPAN_MAX_TURN_DEG = 115.0


SPAN_MAX_BOW_FRAC = 0.19


def _window_shape(
    lb: Label, window: list[Pt], turn_max: float, bow_max: float
) -> tuple[float, float, float] | None:
    """How a window of the line bends, or None when the name may not be set on it.

    Returns:
        `(turn, tilt, bow)`: how far the window turns, how far its chord leaves
        the horizontal, and how far it bows off that chord as a share of it.
    """
    turn = _turning(window)
    if turn > turn_max:
        return None
    chord = math.dist(window[0], window[-1]) or 1.0
    bow = _bow(window) / chord
    if bow > bow_max:
        return None
    tilt = _tilt(window)
    # A river follows its own bend whatever the bearing. Everything else
    # still has a steep window refused outright: a name read by tilting the
    # head is a worse fault than a name that does not follow its feature,
    # and a span's bracket is a line the renderer drew rather than a fact
    # about the ground, so it earns less patience than water does.
    if lb.kind not in TILT_EXEMPT_KINDS and (
        tilt > MAX_TILT_DEG or _tilt_max(window) > MAX_LOCAL_TILT_DEG
    ):
        return None
    return turn, tilt, bow


def _ground_cost(lb: Label, window: list[Pt], cells: list[Box], terms: Terms) -> float:
    """What a window costs a reader, per box, on the terms the flat answer is scored on.

    What it sits on, how near the route and the roads it is, how much room it
    has. That is what decides whether the name is set along the line at all.
    """
    n = len(cells)
    # A river's window is not choosing whether to follow the
    # water, only which reach of it, so the terms that describe the
    # ground under the name are discounted: crossing a pale wash or a
    # thin lane is ordinary cartography. Overlap with another label is
    # not discounted.
    soft = RIVER_GROUND_FRAC if lb.kind in TILT_EXEMPT_KINDS else 1.0
    ground = sum(_overlap(box, terms.boxes) for box in cells) / n
    # A name written on the water is not charged for the water being
    # dark: that is the ground it was sent to sit on, and charging it
    # would send the name off down the river to its palest reach.
    dark_frac = 0.0 if lb.in_water else soft
    ground += sum(_darkness(box, terms.card, terms.dark) for box in cells) / n * 150 * dark_frac
    # A curved name has to keep off the route as much as a flat one
    # does, or a span name is written straight across the track it
    # belongs to.
    reach = max(ROUTE_REACH_PX, lb.size)
    ground += sum(_near_route(box, terms.route, reach) for box in cells) / n
    # The share of the name that lies on tarmac, so a long name
    # clipping one lane at its tail is not scored as if the whole of it
    # were on a road.
    # A name on the water pays a route's price for a road under it. A
    # discount is right for a name in paper clipping a lane; a bridge
    # drawn through the letters of a river's name is not ordinary
    # cartography, and a name across a bridge is worse when there is a
    # clear reach of water just beside it.
    road_cost = IN_WATER_ROAD_COST if lb.in_water else ROAD_CROSS_COST * soft
    ground += (sum(_on_road(box, terms.roads) for box in cells) / n) * road_cost
    mid = window[len(window) // 2]
    ground += math.dist(mid, (lb.px, lb.py)) * ANCHOR_PULL
    ground -= min(_separation(box, terms.boxes) for box in cells) * SEPARATION_WEIGHT
    return ground


def _sides(lb: Label) -> tuple[float, ...]:
    """The sides of its line a curved name is tried on."""
    # A span's bracket is a contour and a contour can loop, so which side of it
    # is "away from the route" is not one answer for the whole line: read once
    # at the bracket's middle and applied everywhere, it can write "the long
    # climb out of Keswick" on the inside of its own bracket with the track
    # running through the word. Both sides are candidates and the route cost
    # decides, which is what it is for.
    # The same for a river and a road. A name set along its own water has two
    # sides to sit on and the better one is chosen rather than assumed; the
    # cost already knows what is under each, so both
    # are offered and it decides. Nothing here can reject a window for its
    # side: if the preferred side is blocked the other one is taken, and the
    # name still follows the bend.
    if lb.tier == TIER_SPAN or lb.kind in TWO_SIDED_KINDS:
        return (lb.lift, -lb.lift)
    return (lb.lift,)


def _read_side(window: list[Pt], side: float) -> tuple[list[Pt], float]:
    """The window the name reads along, and the side it lifts to once that is settled."""
    read = _reading(window)
    # Turning the window round turns its normal round with it, so the side the
    # name lifts to has to turn as well or the boxes the placer defended and
    # the pixels the hand writes are on opposite sides of the line.
    if read is not window:
        return read, -side
    return read, side


def _place_along(
    lb: Label,
    tw: float,
    th: float,
    terms: Terms,
    apart_from: list[float] | None = None,
) -> tuple[float, list[Box], list[Pt], float, float] | None:
    """The run of its own line a curved name is set on, and the boxes it takes.

    Every window of the right length along the whole feature is a candidate,
    not just the one nearest the anchor. A river label may go anywhere along
    its water and that freedom is the point: it is what lets the Derwent move
    upstream and out of the Braemar names rather than sit on top of them.

    Args:
        lb: The label, carrying the whole feature as its `baseline`.
        tw: How wide the name is.
        th: How tall it is.
        terms: The card, the darkness grid, what is already on the sheet, the
            named road centrelines for the crossing cost and the route in
            weighted parts for the route cost.
        apart_from: How far along this same line each window this name already
            took started, in pixels of run. This is what stops the major
            river's two names converging on the same reach of water. Measured
            along the water rather than across the sheet: a river doubles back,
            and two points half a kilometre apart on the water can be a
            hundred pixels apart on the paper, which is what left the second
            "Eden" with no window at all.

    Returns:
        `(cost, boxes, window, at, side)`: what the chosen window costs on the
        same scale the flat answer is scored on, the boxes the text would
        occupy, the run of line it would sit on, how far along the line it
        starts, and which side of it the name lifts to. None when no window on
        this line is usable.
    """
    want = tw * 1.02
    span = lb.tier == TIER_SPAN
    turn_max = SPAN_MAX_TURN_DEG if span else MAX_TURN_DEG
    bow_max = SPAN_MAX_BOW_FRAC if span else MAX_BOW_FRAC
    line = _resample(lb.baseline, max(want / 24.0, 2.0))
    if length(line) < want:
        return None
    apart = max(length(line) * RIVER_REPEAT_FRAC, want)
    cum = cumulative_length(line)
    sides = _sides(lb)
    best: tuple[float, list[Pt], list[Box], float, float, float] | None = None
    step = max(len(line) // 60, 1)
    for i in range(0, len(line), step):
        window = _window(line, i, want)
        if window is None:
            break
        shape = _window_shape(lb, window, turn_max, bow_max)
        if shape is None:
            continue
        turn, tilt, bow = shape
        here = cum[i]
        if any(abs(here - other) < apart for other in apart_from or []):
            continue
        for side in sides:
            cells = _curved_boxes(window, lb, th, side)
            if not all(_on_paper(box, terms.card) for box in cells):
                continue
            # Two scores, because two different questions are being asked.
            #
            # `ground` is what this position costs a reader. It is what decides
            # whether the name is set along the line at all.
            #
            # The shape terms are added only to choose between windows on the
            # same line. They must not go into the comparison with the flat
            # answer: a river that bends is not thereby better off in clear
            # paper, and pricing its own curvature against a horizontal
            # alternative meant nothing was ever set along anything.
            ground = _ground_cost(lb, window, cells, terms)
            tilt_term = 0.0 if lb.kind in TILT_EXEMPT_KINDS else tilt * 0.8
            pick = ground + turn * 1.5 + tilt_term + bow * 400.0
            if best is None or pick < best[0]:
                best = (pick, window, cells, ground, here, side)
    if best is None:
        return None
    _pick, window, cells, cost, at, side = best
    read, side = _read_side(window, side)
    return cost, cells, read, at, side


#: How far apart two names of the same river have to be before the second
#: is worth setting, as a share of the river's whole baseline and never less
#: than the name's own width. Under this the two would read as one repeated
#: name rather than as the same river met twice.
RIVER_REPEAT_FRAC = 0.35
