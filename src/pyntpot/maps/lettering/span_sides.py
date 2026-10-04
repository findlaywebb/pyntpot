"""Which side of the route a span's line stands on, and how strongly the route bends there.

Key names: `route_turn` and `bend_strength`, how far and how steadily a stretch bends;
`_convex_side`, `_curved_side` and `_freer_side`, the three readings of a side (the
outside of a bend, the outside weighed against clearance, and the clearer of two); the
`SPAN_CURVE_*` constants that weigh the bend.

It does not draw a line and does not resolve span requests.

Invariants: a side is `+1` or `-1`, positive towards the normal `(-dy, dx)`; a straight
or S-shaped stretch has no outside, and a bend never outweighs a clearly clearer side.
"""

import logging
import math
from typing import Any

from pyntpot.ink.polyline import Pt
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import Span
from pyntpot.maps.lettering.span_clear import SPAN_CLEAR_CAPS, clear_of_route
from pyntpot.maps.lettering.span_line import SPAN_OFFSET_CAPS, _resample, span_line

log = logging.getLogger(__name__)

#: The fewest points that have a middle one.
_FEWEST_WITH_A_MIDDLE = 3

#: The fewest points that make a segment.
_FEWEST_FOR_A_SEGMENT = 2

#: Below this a distance in pixels is zero.
_ZERO_PX = 1e-6

#: Below this a length is zero.
_ZERO_LENGTH = 1e-9

#: Whether the outside of a bend gets a say in which side of the route a span's
#: bracket is drawn on. There is a geometric
#: argument for it: **a bracket is an offset line, and an offset line
#: contracts on the inside of a bend and expands on the outside.** The inside
#: is where the contour crowds, kinks and closes on itself, which is the
#: failure that has produced a ring round the Keswick climb and a doubled-back
#: stub; the outside gives more arc length for the same stretch, so a name
#: fits along it more often and the mark stays an open gesture.
#:
#: On by default and named here so it can be turned off or reweighted without
#: a code change. Off, `place_spans` chooses exactly as it did before.
SPAN_CURVE_SIDE: bool = True

#: How much net turning a stretch has to do before it has an outside at all,
#: and where the vote reaches full strength, both in degrees over the whole
#: extent. Below the first, the stretch is straight enough that "the outside"
#: names nothing and the free-paper choice stands unopposed; between the two
#: the vote ramps, so a gentle bend is a gentle preference.
#:
#: Thirty-five degrees is a little over a third of a right angle over the whole
#: stretch, which is about where a road stops reading as a road that goes
#: somewhere and starts reading as a bend. It is also where the sweep settles:
#: over the four cached rides, 25 degrees moves 33 stretches for 24 better and
#: 8 worse, 35 moves 32 for 24 and 7, and 45 and 60 both drop a win to save
#: nothing. The A591 climb on the Dovedale card turns 11 degrees over its
#: whole extent and gets no vote: a span on a straight stretch staying where
#: the free paper put it is the threshold working, not the term failing.
SPAN_CURVE_MIN_TURN_DEG = 35.0

SPAN_CURVE_FULL_TURN_DEG = 75.0

#: How single-minded the bend has to be. `net / gross`: one long curve is near
#: 1, an S-bend that turns as far back as it turned out is near 0. A stretch
#: below this has no outside either, because half of it would be written on the
#: inside whichever side were chosen, so the vote is withheld and the free-paper
#: choice stands. Not a small number: the ambiguous case is the one where
#: forcing a side does harm, and a stretch that is two thirds one way is where
#: the eye starts calling it a bend.
SPAN_CURVE_MIN_COHERENCE = 0.62

#: What the vote is worth, in the units the free-paper choice is scored in,
#: which is mean darkness from 0 (clear paper) to 1 (solid ink). The vote can
#: only turn the side round when the darkness margin between the two sides is
#: under `SPAN_CURVE_WEIGHT` times the vote's strength. So this number is
#: exactly the answer to "how near a tie does the free-paper choice have to be
#: before the bend gets to decide it".
#:
#: Picked by measuring the margins, not by taste. Over the same 187 stretches,
#: the margin the free-paper rule wins by has a median of 0.042 and a ninetieth
#: percentile of 0.122. At 0.08 a fully committed bend overrules about four
#: margins in five and loses to the darkest fifth, which is the side that is
#: off the paper, under a wash or already carrying names; a half-strength bend,
#: which is a stretch turning about 50 degrees, overrules only about half.
#: That is the shape wanted: the outside of the curve **where there is one**,
#: and not otherwise.
SPAN_CURVE_WEIGHT = 0.08

#: At what scale the bend is read, as a multiple of the cap height. The single
#: most important number here, and the one the outside-of-the-bend rule
#: lives or dies on.
#:
#: The route in card pixels is sampled about a pixel apart, and per-vertex turn
#: at that spacing is mostly the sampling, so the stretch is resampled before
#: it is measured. **The right spacing is the offset the bracket will be drawn
#: at**, 1.7 cap heights, because contraction is what an offset line does at
#: its own offset: a bend the offset can see is a bend that squeezes it. Read
#: coarser, the measure answers a different question and stops predicting
#: anything. Over 187 stretches from the four cached rides, the share of the
#: decisive cases the outside gets right is 89% read at 1.5 caps, 79% at 2,
#: 60% at 3 and 46% at 4, which is a coin toss. 1.5 is under the offset and is
#: where the sweep peaks; the trend either side of it is the argument.
SPAN_CURVE_SCALE_CAPS = 1.5


def route_turn(line: list[Pt]) -> tuple[float, float]:
    """How far a polyline turns, net and gross, in degrees.

    Signed the way a turn is signed in card pixels, where y runs down:
    positive turning is towards the normal `(-dy, dx)`. Only the ratio of the
    two numbers is used to decide anything, because which drawn side the bend's
    outside corresponds to is settled by measuring the marks, in `_convex_side`.

    Args:
        line: The polyline, in card pixels, already sampled at the scale the
            bend is to be read at.

    Returns:
        `(net, gross)`: the signed sum of the turn at every interior vertex,
        and the sum of its absolute value. Their ratio says how single-minded
        the turning is; `(0.0, 0.0)` for a line with no interior vertex.
    """
    net = gross = 0.0
    for a, b, c in zip(line, line[1:], line[2:], strict=False):
        ux, uy = b[0] - a[0], b[1] - a[1]
        vx, vy = c[0] - b[0], c[1] - b[1]
        if math.hypot(ux, uy) < _ZERO_LENGTH or math.hypot(vx, vy) < _ZERO_LENGTH:
            continue
        turn = math.degrees(math.atan2(ux * vy - uy * vx, ux * vx + uy * vy))
        net += turn
        gross += abs(turn)
    return net, gross


def bend_strength(sub: list[Pt], scale_px: float) -> float:
    """How much of an outside a stretch has, from 0 to 1.

    Zero when the stretch is too straight for "the outside" to name anything,
    and zero when it turns both ways about equally, which is the same statement
    made twice: there is no one outside, so nothing is voted for and the
    free-paper rule keeps the choice. Otherwise the strength ramps from 0 to 1
    between `SPAN_CURVE_MIN_TURN_DEG` and `SPAN_CURVE_FULL_TURN_DEG` of net
    turning, so a gentle bend is a gentle preference.

    Unsigned on purpose. Which side the outside actually is, is settled by
    `_convex_side` on the drawn marks rather than from a normal, because this
    module signs a side two different ways: `_bracket` pushes off the chord's
    own normal and takes its chord from the widest pair of points rather than
    from the direction of travel, while the contour filters a ring with
    `_side_at`. The two do not agree, so nothing here relies on either.

    Args:
        sub: The stretch of route the span covers, in card pixels.
        scale_px: The spacing the stretch is read at, which should be about the
            offset the bracket will be drawn at.

    Returns:
        `0.0` to `1.0`.
    """
    if len(sub) < _FEWEST_WITH_A_MIDDLE or scale_px <= 0.0:
        return 0.0
    net, gross = route_turn(_resample(sub, scale_px))
    if gross <= _ZERO_LENGTH or abs(net) < SPAN_CURVE_MIN_TURN_DEG:
        return 0.0
    if abs(net) / gross < SPAN_CURVE_MIN_COHERENCE:
        return 0.0
    span_deg = SPAN_CURVE_FULL_TURN_DEG - SPAN_CURVE_MIN_TURN_DEG
    ramp = (abs(net) - SPAN_CURVE_MIN_TURN_DEG) / span_deg if span_deg > 0 else 1.0
    return min(max(ramp, 0.0), 1.0)


def _outward(sub: list[Pt]) -> tuple[Pt, Pt]:
    """The middle of a stretch's chord, and the unit vector out of its bend.

    The chord is the widest pair of points and not the two ends, for the reason
    `_bracket` uses the same pair: an out-and-back finishes where it started,
    and the middle of *that* chord says nothing about anything. The stretch's
    own middle of mass sits on the convex side of that chord, because that is
    what bending is, so the direction from the one to the other points out of
    the bend.

    Args:
        sub: The stretch of route, in card pixels.

    Returns:
        `(middle, outward)`: the chord's middle, and a unit vector, or a zero
        vector when the stretch is straight enough to have no bulge at all.
    """
    far = max(sub, key=lambda q: math.dist(sub[0], q))
    near = max(sub, key=lambda q: math.dist(far, q))
    middle = ((far[0] + near[0]) / 2.0, (far[1] + near[1]) / 2.0)
    cx = sum(p[0] for p in sub) / len(sub) - middle[0]
    cy = sum(p[1] for p in sub) / len(sub) - middle[1]
    run = math.hypot(cx, cy)
    return middle, ((cx / run, cy / run) if run > _ZERO_LENGTH else (0.0, 0.0))


def _mark_broken(line: list[Pt], route_px: list[Pt], clear_px: float) -> bool:
    """Whether a drawn mark failed as a mark rather than merely read worse."""
    if len(line) < _FEWEST_FOR_A_SEGMENT:
        return True
    return not clear_of_route(line, route_px, clear_px)


def _convex_side(span: Span, route_px: list[Pt], cap_px: float) -> tuple[int, dict[int, list[Pt]]]:
    """Which side draws the bracket on the outside of the bend, by measurement.

    The mark is drawn both ways and the two are compared, rather than a side
    being worked out from a normal. Two reasons. The convention is not settled
    in this module, as `bend_strength` says; and the answer wanted is about the
    mark, not about the route, so measuring the mark is the direct question.

    Each drawn line is measured by how far it stands *out of the bend*: the
    mean of its displacement from the chord's middle, projected onto the
    outward direction. Distance alone would not do, because the straight
    fallback is pushed out past the widest point of the stretch and stands a
    long way from the chord's middle on either flank; the projection is signed,
    so a mark pushed the wrong way scores negative rather than large.

    Args:
        span: The span, for its extent.
        route_px: The track in card pixels.
        cap_px: The lettering's cap height, which sets the probe offset.

    Returns:
        `(side, marks)`: `+1` or `-1`, or `0` when there is nothing to compare,
        and the line each side drew, so the caller can look at them without
        drawing them again.
    """
    sub = route_px[span.i0 : span.i1 + 1]
    marks = {
        side: span_line(route_px, span.i0, span.i1, side, cap_px * SPAN_OFFSET_CAPS)
        for side in (1, -1)
    }
    if len(sub) < _FEWEST_WITH_A_MIDDLE:
        return 0, marks
    (mx, my), (ox, oy) = _outward(sub)
    if ox == 0.0 and oy == 0.0:
        return 0, marks
    reach = {
        side: sum((p[0] - mx) * ox + (p[1] - my) * oy for p in line) / len(line)
        for side, line in marks.items()
        if line
    }
    if len(reach) < _FEWEST_FOR_A_SEGMENT:
        return next(iter(reach), 0), marks
    return (1 if reach[1] > reach[-1] else -1), marks


def _curved_side(span: Span, route_px: list[Pt], base: int, margin: float, cap_px: float) -> int:
    """The side the bracket goes on once the bend has had its say.

    A weighted term and never an override. The free-paper choice arrives with
    the margin it won by, in mean darkness; the bend arrives with a strength
    from 0 to 1; and the bend only turns the answer round when the outside is
    not already where the paper put it **and** `SPAN_CURVE_WEIGHT` times its
    strength beats that margin. So the outside wins a near-tie, and a side that
    is off the paper, under a wash or already carrying names keeps the span.

    One thing outranks the bend outright, and it is not a preference: **the
    bend may not break the mark.** Both marks are drawn to find the outside, so
    what the outside would actually look like is already in hand, and where the
    outside comes back as a ring or as the straight fallback standing well off
    the offset while the free-paper side came back as a proper contour, the
    move is refused. Measured over the four cached rides this refusal is what
    turns the term from roughly even into clearly worth having.

    Args:
        span: The span, for its extent.
        route_px: The track in card pixels.
        base: The side the free-paper rule chose, +1 or -1.
        margin: How far apart the two sides' mean darkness was.
        cap_px: The lettering's cap height, which sets the reading scale.

    Returns:
        `base`, or `-base` when the bend overrules it.
    """
    strength = (
        bend_strength(route_px[span.i0 : span.i1 + 1], cap_px * SPAN_CURVE_SCALE_CAPS)
        if SPAN_CURVE_SIDE
        else 0.0
    )
    if strength <= 0.0:
        return base
    outside, marks = _convex_side(span, route_px, cap_px)
    if outside in (0, base):
        return base
    if SPAN_CURVE_WEIGHT * strength <= margin:
        log.info(
            "span %r keeps the inside of its bend: darkness margin %.3f beats the bend's %.3f",
            span.name,
            margin,
            SPAN_CURVE_WEIGHT * strength,
        )
        return base
    clear = cap_px * SPAN_CLEAR_CAPS
    if _mark_broken(marks[outside], route_px, clear) and not _mark_broken(
        marks[base], route_px, clear
    ):
        log.info(
            "span %r keeps the inside of its bend: the outside draws no usable mark", span.name
        )
        return base
    log.info(
        "span %r moves to the outside of its bend (strength %.2f, darkness margin %.3f)",
        span.name,
        strength,
        margin,
    )
    return outside


def _freer_side(
    span: Span, route_px: list[Pt], dark: dict[str, Any], card: Card, cap_px: float
) -> tuple[int, float]:
    """Which side of its own extent has the more free paper, and by how much.

    Returns:
        `(side, margin)`: +1 for left and -1 for right, and the difference in
        mean darkness between the two sides, from 0 to 1. The margin is what
        the bend's vote is weighed against.
    """
    gw, gh, grid = dark["w"], dark["h"], dark["v"]
    score = {1: [], -1: []}
    step = max((span.i1 - span.i0) // 12, 1)
    for i in range(span.i0, span.i1, step):
        (ax, ay), (bx, by) = route_px[i], route_px[min(i + step, len(route_px) - 1)]
        run = math.hypot(bx - ax, by - ay)
        if run < _ZERO_PX:
            continue
        nx, ny = -(by - ay) / run, (bx - ax) / run
        for side in (1, -1):
            x = ax + nx * side * cap_px * 3.0
            y = ay + ny * side * cap_px * 3.0
            if not (0 <= x < card.w and 0 <= y < card.h):
                score[side].append(1.0)
                continue
            c = min(int(x / card.w * gw), gw - 1)
            r = min(int(y / card.h * gh), gh - 1)
            score[side].append(grid[r][c])
    left = sum(score[1]) / len(score[1]) if score[1] else 0.5
    right = sum(score[-1]) / len(score[-1]) if score[-1] else 0.5
    return (1 if left <= right else -1), abs(left - right)
