"""The furniture drawn beside a name: its pin, its leader and a town's underline.

Key names: `pin`, the ring a leader points at, open where the leader comes in or
closed when it is given no gap; `leader`, the curve from the pin's centre to the
name; `leader_angle`, the direction a leader leaves its pin's ring, which the
ring's gap faces; `pin_gap_px`, how wide that gap is for the pens that draw the
two; `pin_radius`, the ring's radius for a type size; `underline`, the rule under
a town's name. Each stroke is wandered by `Hand.stroke` from the generator the
name's glyphs were written with.

It draws nothing into a plate and it decides nothing about which label takes
which, nor which way a pin's gap turns: that is `maps.lettering_marks`. The
geometry is the map's, the wander is the hand's.

Invariants: the draws a stroke takes from the generator before it is wandered
(a leader's bend, an underline's rise) come first, in the order the leader, the
pin and the underline are called, so the same label draws the same strokes; a
wandered stroke keeps its ends, so a leader starts on the pin's centre and an
open ring's two ends bound its gap exactly; a pin given no gap is the closed
ring of fourteen sides it always was.
"""

import math

import numpy as np

from pyntpot.ink.polyline import Point
from pyntpot.letters.hand import Hand
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering.span_line import resample

#: How many segments the quadratic of a leader is cut into.
_LEADER_STEPS = 12


#: How many sides a closed pin ring is drawn with; an open one takes its share.
_PIN_SIDES = 14

#: The radius of a pin ring's centreline, as a share of the type size.
PIN_RADIUS_SIZE_FRAC = 0.14

#: The smallest radius of a pin ring's centreline, in display pixels.
PIN_RADIUS_MIN_PX = 2.2

#: How many ring pens a pin's gap is wider than the leader's pen: the arc's ink
#: runs half a ring pen past each end of its centreline, and another half a pen
#: each side is bare paper for the hand's wander.
PIN_GAP_RING_PENS = 2.0

#: The bare paper added to a pin's gap for the bristles, in display pixels:
#: twice the default brush's sideways jitter (`brush_jitter_px`, 0.55), once
#: each side. The jitter does not shrink with the pen, so without it a small
#: name's gap fills and its ring reads closed.
PIN_GAP_CLEAR_PX = 1.1


def pin_radius(lb: Label) -> float:
    """The radius of a label's pin ring at its centreline, in display pixels."""
    return max(lb.size * PIN_RADIUS_SIZE_FRAC, PIN_RADIUS_MIN_PX)


def pin_gap_px(leader_px: float, ring_px: float) -> float:
    """How wide a pin's gap is, end to end of the arc's centreline, in display pixels.

    Args:
        leader_px: The width the leader is drawn at.
        ring_px: The width the ring is drawn at.

    Returns:
        The leader's pen, `PIN_GAP_RING_PENS` ring pens and `PIN_GAP_CLEAR_PX`.
    """
    return leader_px + PIN_GAP_RING_PENS * ring_px + PIN_GAP_CLEAR_PX


def pin(
    hand: Hand,
    lb: Label,
    rng: np.random.Generator,
    *,
    gap_at: float | None = None,
    gap_px: float = 0.0,
) -> list[Point]:
    """The ring a leader points at, drawn round rather than filled, open where the leader comes in.

    An open ring is an arc of the circle with a gap of `gap_px` between its two
    ends, measured as the chord at the centreline and centred on `gap_at`, so
    the leader and the ring read as one mark, a callout drawn in one go. A gap
    as wide as the ring leaves half of it. The arc takes its share of the closed
    ring's sides.

    Args:
        hand: The hand that wanders the ring.
        lb: The label, for its anchor and type size.
        rng: The generator the wander is drawn from.
        gap_at: The direction the gap faces from the ring's centre, in radians
            with y down (`leader_angle` of the leader passing through it); None
            draws a closed ring.
        gap_px: The gap's width; a closed ring when it is not positive.

    Returns:
        The wandered ring or arc, in display pixels.
    """
    r = pin_radius(lb)
    if gap_at is None or gap_px <= 0:
        start, sweep, sides = 0.0, math.tau, _PIN_SIDES
    else:
        half = math.asin(min(gap_px / (2.0 * r), 1.0))
        start, sweep = gap_at + half, math.tau - 2.0 * half
        sides = max(round(_PIN_SIDES * sweep / math.tau), 2)
    ring = [
        (
            lb.px + r * math.cos(start + sweep * i / sides),
            lb.py + r * math.sin(start + sweep * i / sides),
        )
        for i in range(sides + 1)
    ]
    return hand.stroke(ring, rng, 0.2)


def leader(hand: Hand, ends: tuple[Point, Point], rng: np.random.Generator) -> list[Point]:
    """A curve from the pin's centre to the name, bent a different way each time.

    A leader exists only to disambiguate a pin, so it is the quietest mark on
    the map and it never leaves at the same angle twice. It runs into the
    middle of its pin's ring, through the ring's gap, so the two read as one
    pointer; it stops on the centre rather than over-running it.

    Args:
        hand: The hand that wanders the leader.
        ends: The pin's centre, then the name's end.
        rng: The generator the bend and the wander are drawn from.

    Returns:
        The wandered leader, from the pin's centre to the name, in display pixels.
    """
    (ax, ay), (bx, by) = ends
    run = math.hypot(bx - ax, by - ay) or 1.0
    bend = float(rng.normal(0.0, 0.15)) * run
    mx, my = (ax + bx) / 2, (ay + by) / 2
    nx, ny = -(by - ay) / run, (bx - ax) / run
    quad = [(ax, ay), (mx + nx * bend, my + ny * bend), (bx, by)]
    steps = range(_LEADER_STEPS + 1)
    return hand.stroke([_quad_at(quad, t / _LEADER_STEPS) for t in steps], rng, 0.5)


def leader_angle(line: list[Point], centre: Point, radius: float) -> float:
    """The direction a leader leaves its pin's ring, in radians with y down.

    It is where the wandered leader first reaches `radius` from the centre,
    not the straight line to the name, so a leader bent near its pin still
    passes through the middle of the gap. A leader that never reaches the ring
    gives the direction of its far end.

    Args:
        line: The leader, from the pin's centre outwards.
        centre: The pin's centre.
        radius: The ring's radius.

    Returns:
        The angle from the centre to the crossing.
    """
    cx, cy = centre
    last = line[0]
    for pt in line:
        out = math.hypot(pt[0] - cx, pt[1] - cy)
        if out >= radius:
            was = math.hypot(last[0] - cx, last[1] - cy)
            t = (radius - was) / (out - was) if out > was else 1.0
            x, y = last[0] + (pt[0] - last[0]) * t, last[1] + (pt[1] - last[1]) * t
            return math.atan2(y - cy, x - cx)
        last = pt
    return math.atan2(last[1] - cy, last[0] - cx)


def underline(hand: Hand, lb: Label, width: float, rng: np.random.Generator) -> list[Point]:
    """A hand-drawn rule under a town's name, never quite level.

    One stroke, not one a word, and it lifts very slightly to the right, which
    is what a rule drawn quickly under a word actually does.
    """
    x0 = lb.tx - (width if lb.anchor == "end" else width / 2 if lb.anchor == "middle" else 0.0)
    y0 = lb.ty + lb.size * 0.22
    rise = lb.size * (0.05 + abs(float(rng.normal(0.0, 0.04))))
    line = [(x0 - lb.size * 0.06, y0), (x0 + width + lb.size * 0.1, y0 - rise)]
    return hand.stroke(resample(line, max(width / 10.0, 3.0)), rng, 0.45)


def _quad_at(quad: list[Point], t: float) -> Point:
    """One point on a three point quadratic."""
    u = 1.0 - t
    return (
        u * u * quad[0][0] + 2 * u * t * quad[1][0] + t * t * quad[2][0],
        u * u * quad[0][1] + 2 * u * t * quad[1][1] + t * t * quad[2][1],
    )
