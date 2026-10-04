"""The furniture drawn beside a name: its pin, its leader and a town's underline.

Key names: `pin`, the ring a leader points at; `leader`, the curve from the pin
to the name; `underline`, the rule under a town's name. Each returns the points
of one stroke, wandered by `Hand.stroke` from the generator the name's glyphs
were written with.

It draws nothing into a plate and it decides nothing about which label takes
which: that is `maps.lettering_marks`. The geometry is the map's, the wander is
the hand's.

Invariants: the draws a stroke takes from the generator before it is wandered
(a leader's bend, an underline's rise) come first, in the order the pin, the
leader and the underline are called, so the card's pixels do not move.
"""

import math

import numpy as np

from pyntpot.ink.polyline import Pt
from pyntpot.letters.hand import Hand
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.lettering.span_line import _resample

#: How many segments the quadratic of a leader is cut into.
_LEADER_STEPS = 12


def pin(hand: Hand, lb: Label, rng: np.random.Generator) -> list[Pt]:
    """The dot the leader points at, drawn round rather than filled."""
    r = max(lb.size * 0.14, 2.2)
    ring = [
        (lb.px + r * math.cos(a * math.tau / 14), lb.py + r * math.sin(a * math.tau / 14))
        for a in range(15)
    ]
    return hand.stroke(ring, rng, 0.2)


def leader(hand: Hand, ends: tuple[Pt, Pt], rng: np.random.Generator) -> list[Pt]:
    """A curve from the pin to the name, bent a different way each time.

    A leader exists only to disambiguate a pin, so it is the quietest mark on
    the sheet and it never leaves at the same angle twice. It over-runs the pin
    very slightly, because a real pen does not stop on the dot.
    """
    (ax, ay), (bx, by) = ends
    run = math.hypot(bx - ax, by - ay) or 1.0
    over = 2.0 / run
    ax, ay = ax - (bx - ax) * over, ay - (by - ay) * over
    bend = float(rng.normal(0.0, 0.15)) * run
    mx, my = (ax + bx) / 2, (ay + by) / 2
    nx, ny = -(by - ay) / run, (bx - ax) / run
    quad = [(ax, ay), (mx + nx * bend, my + ny * bend), (bx, by)]
    return hand.stroke([_quad_at(quad, t / _LEADER_STEPS) for t in range(13)], rng, 0.5)


def underline(hand: Hand, lb: Label, width: float, rng: np.random.Generator) -> list[Pt]:
    """A hand-drawn rule under a town's name, never quite level.

    One stroke, not one a word, and it lifts very slightly to the right, which
    is what a rule drawn quickly under a word actually does.
    """
    x0 = lb.tx - (width if lb.anchor == "end" else width / 2 if lb.anchor == "middle" else 0.0)
    y0 = lb.ty + lb.size * 0.22
    rise = lb.size * (0.05 + abs(float(rng.normal(0.0, 0.04))))
    line = [(x0 - lb.size * 0.06, y0), (x0 + width + lb.size * 0.1, y0 - rise)]
    return hand.stroke(_resample(line, max(width / 10.0, 3.0)), rng, 0.45)


def _quad_at(quad: list[Pt], t: float) -> Pt:
    """One point on a three point quadratic."""
    u = 1.0 - t
    return (
        u * u * quad[0][0] + 2 * u * t * quad[1][0] + t * t * quad[2][0],
        u * u * quad[0][1] + 2 * u * t * quad[1][1] + t * t * quad[2][1],
    )
