"""Strand separation: the two limbs of a doubled-back route drawn beside each other.

Key names: `separate_strands`, the route in card pixels with each doubled-back
stretch pushed apart; `STRAND_GAP_WIDTHS`, the gap as a multiple of the route's
stroke width.

It does not draw the route or choose its weight. Invariants: a route with no
stretch that comes back within the gap of itself is returned unchanged, and the
route keeps its points, in order, however far they are pushed.
"""

from __future__ import annotations

import math
from itertools import pairwise

from pyntpot.ink.polyline import ease_along, tangent_at

#: How far apart the two strands of one route are drawn where the track came
#: back along its own path, as a multiple of the route's own stroke width. A
#: doubled-back stretch drawn on its own true line is two sets of dots landing
#: in each other's gaps: the reader cannot tell an out-and-back from a single
#: pass, and the whole doubled-back stretch reads as one line.
#: A person drawing the same route by hand draws the two limbs beside each
#: other, and this is that gap. Two and a half stroke widths centre to centre
#: leaves a stroke and a half of clear paper between them at every route weight.
STRAND_GAP_WIDTHS = 2.5
#: How much path has to run between two points before they count as two strands
#: rather than one bend, as a multiple of the gap. Ten: a bend comes back to
#: itself within a few of its own widths, and a route that comes back on itself
#: after this much running has been somewhere.
STRAND_MIN_ARC = 10.0
#: How far the displacement is eased in and out along the path, as a multiple of
#: the gap. The strands have to part and rejoin somewhere, and a step there is a
#: kink in the line; over three gaps of running it is a curve.
STRAND_EASE_WIDTHS = 3.0
#: The fewest points a route needs before it can double back on itself.
MIN_STRAND_POINTS = 4


def separate_strands(
    route_px: list[tuple[float, float]], gap_px: float
) -> list[tuple[float, float]]:
    """Draw the two limbs of a doubled-back stretch beside each other.

    Where the track came back along a path it had already run, the two passes
    are the same line on the sheet and the reader has nothing to read: at the
    route's own weight the second pass lands in the first one's gaps and the
    out-and-back reads as a single street. This pushes each pass off that shared
    line onto its own side of it, which is what a hand drawing the same route
    does, and eases the displacement in and out so the strands part and rejoin
    as curves rather than steps.

    Which side each takes is decided by the direction of travel, not by where
    the other strand happens to lie, because on a stretch run twice the two are
    the same pixels and "away from the other one" has no direction in it. Two
    passes running against each other each keep their own left, so they end up
    on opposite sides of the line they share. Two passes running the same way,
    which is a lap repeated, are parted by the order they were run in.

    Args:
        route_px: The track in card pixels.
        gap_px: How far apart, centre to centre, two strands are drawn.

    Returns:
        The track, displaced. The same list back when nothing was doubled, so a
        route that never comes back within `gap_px` of itself is drawn on its
        own line exactly as it was.
    """
    n = len(route_px)
    if n < MIN_STRAND_POINTS or gap_px <= 0:
        return route_px
    cum = [0.0]
    for a, b in pairwise(route_px):
        cum.append(cum[-1] + math.dist(a, b))
    push = _pushes(route_px, cum, gap_px)
    push = ease_along(push, cum, gap_px * STRAND_EASE_WIDTHS)
    if not any(push):
        return route_px
    out: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(route_px):
        tx, ty = tangent_at(route_px, i)
        out.append((x - ty * push[i], y + tx * push[i]))
    return out


def _pushes(route_px: list[tuple[float, float]], cum: list[float], gap_px: float) -> list[float]:
    """How far each point is pushed off the line it shares with another pass, signed by side."""
    n = len(route_px)
    min_arc = gap_px * STRAND_MIN_ARC
    # The route's own points in cells the size of the gap, so each point is
    # measured against the handful that could be near it rather than all of them.
    cell = max(gap_px, 1e-6)
    grid: dict[tuple[int, int], list[int]] = {}
    for i, (x, y) in enumerate(route_px):
        grid.setdefault((int(x // cell), int(y // cell)), []).append(i)
    push = [0.0] * n
    for i, (x, y) in enumerate(route_px):
        gx, gy = int(x // cell), int(y // cell)
        near: tuple[float, int] | None = None
        for cx in (gx - 1, gx, gx + 1):
            for cy in (gy - 1, gy, gy + 1):
                for j in grid.get((cx, cy), ()):
                    if abs(cum[i] - cum[j]) < min_arc:
                        continue
                    d = math.dist(route_px[i], route_px[j])
                    if d < gap_px and (near is None or d < near[0]):
                        near = (d, j)
        if near is None:
            continue
        d, j = near
        tx, ty = tangent_at(route_px, i)
        ox, oy = tangent_at(route_px, j)
        # Against each other: each keeps its own left, which puts them on
        # opposite sides of the line they share however near it they are. The
        # same way: the earlier pass takes the left and the later one the right.
        side = -1.0 if tx * ox + ty * oy >= 0 and cum[i] > cum[j] else 1.0
        push[i] = side * (gap_px - d) / 2
    return push
