"""Builders the lettering tests share: a card, a dark grid, a hand, and route shapes."""

import itertools
import math
from typing import Any

from pyntpot.ink.polyline import simplify
from pyntpot.letters.hand import Hand
from pyntpot.letters.style import FaceStyle, HandStyle
from pyntpot.maps.card import Card

Pt = tuple[float, float]


def map_card() -> Card:
    """The smallest card the placer will accept: 400 by 300 display pixels, one pixel a metre."""
    return Card(
        box=(0.0, 0.0, 400.0, 300.0),
        display=(400, 300),
        render=(400, 300),
        mpp=1.0,
        mpp_display=1.0,
    )


def flat_dark(w: int = 8, h: int = 8, v: float = 0.2) -> dict[str, Any]:
    """A dark grid with nothing dark in it, so it decides nothing."""
    return {"w": w, "h": h, "v": [[v] * w for _ in range(h)]}


def open_hand() -> Hand:
    """The default hand, as the style's face and seed open it."""
    return Hand(FaceStyle(), HandStyle())


def arc(turn_deg: float, n: int = 60, r: float = 100.0, start: float = 180.0) -> list[Pt]:
    """One circular arc turning `turn_deg`, centred so it sits on the map.

    Positive `turn_deg` turns towards side +1, which in display pixels is the
    normal `(-dy, dx)`, so the centre of the arc is on side +1 and side -1 is
    the outside of the bend.
    """
    out = []
    for i in range(n):
        a = math.radians(start + turn_deg * i / (n - 1))
        out.append((200.0 + r * math.cos(a), 150.0 + r * math.sin(a)))
    return out


def shapes() -> dict[str, list[Pt]]:
    """One route a case: the shapes a hand-drawn set of marks is made of."""
    straight = [(60.0 + i * 4.0, 150.0) for i in range(60)]
    bend = [(60.0 + i * 3.0, 120.0) for i in range(30)]
    bend += [(150.0 + i * 2.1, 120.0 + i * 2.1) for i in range(1, 25)]
    ess = [(80.0 + i * 3.0, 150.0 + 30.0 * math.sin(i / 9.0)) for i in range(60)]
    out = [(80.0 + i * 4.0, 150.0) for i in range(40)]
    return {
        "straight": straight,
        "bend": bend,
        "s-bend": ess,
        "hairpin": out + [(x, y + 6.0) for x, y in reversed(out)],
        "loop": out + [(x, y + 26.0) for x, y in reversed(out)],
        "crossed": straight + [(200.0, 90.0 + i * 4.0) for i in range(1, 30)],
    }


def crosses(line: list[Pt], route: list[Pt]) -> bool:
    """Whether a drawn line properly crosses a route polyline anywhere."""

    def side(p: Pt, q: Pt, r: Pt) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    for a, b in itertools.pairwise(line):
        for c, d in itertools.pairwise(route):
            d1, d2 = side(c, d, a), side(c, d, b)
            d3, d4 = side(a, b, c), side(a, b, d)
            if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
                return True
    return False


def corners(pts: list[Pt], tol: float = 3.0) -> int:
    """How many turns a drawn line has, at the tolerance a reader sees.

    A spline is a hundred points that each turn a degree; what a person counts
    is the corners left when the line is simplified to what it looks like.
    """
    return max(len(simplify(pts, tol)) - 2, 0)
