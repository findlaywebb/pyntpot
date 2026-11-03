"""Strand merging: a stretch the route runs more than once drawn as one stroke.

Key names: `merge_strands`, the route in display pixels with each stretch it runs
again pulled onto one line; `STRAND_MERGE_WIDTHS`, how near a second pass has to
come to be drawn on the first, as a multiple of the route's stroke width;
`strand_merge_px`, the reach `pipeline.paint` merges the shown route by.

It does not draw the route or choose its weight, and it does not cut a repeated
pass out of the line: both passes are still drawn, on the same pixels. Invariants:
a route with no stretch that comes back within the reach of itself is returned
unchanged, a pass run on the very pixels of an earlier one is not moved, and the
route keeps its points, in order, however far they are pulled.
"""

from __future__ import annotations

import math
from itertools import pairwise
from typing import TYPE_CHECKING

from pyntpot.ink.polyline import ease_along, tangent_at

if TYPE_CHECKING:
    from pyntpot.maps.style import Style

#: How near a later pass has to come to an earlier one, centre to centre, to be
#: drawn on the same line, as a multiple of the route's own stroke width. A leg
#: retraced a few metres off its first line, on the other side of the road or
#: by a GPS that drifted, drawn where it was recorded is two strokes side by side
#: with the road showing between them, which reads as two roads rather than one
#: leg walked twice. Two and a half stroke widths is a stroke and a half of
#: paper between two passes: anything nearer is one leg, anything further a
#: second road beside it.
STRAND_MERGE_WIDTHS = 2.5
#: How much path has to run between two points before they count as two passes
#: rather than one bend, as a multiple of the reach. Ten: a bend comes back to
#: itself within a few of its own widths, and a route that comes back on itself
#: after this much running has been somewhere.
STRAND_MIN_ARC = 10.0
#: How far the pull is eased in and out along the path, as a multiple of the
#: reach. The passes have to meet and part somewhere, and a step there is a
#: kink in the line; over three reaches of running it is a curve.
STRAND_EASE_WIDTHS = 3.0
#: The fewest points a route needs before it can double back on itself.
MIN_STRAND_POINTS = 4
#: How much path, as a multiple of the reach, separates two runs of nearby points
#: before they count as two passes. Two: one pass has at most twice the reach of
#: itself within the reach of a point, so a longer break is the route leaving and
#: coming back.
PASS_BREAK_REACHES = 2.0


def strand_merge_px(style: Style) -> float:
    """The reach, in display pixels, within which two passes of the shown route are one line.

    When the style paints the route pen and its route ink is the `"pen"` treatment,
    the route shown is the pen plate, which the painter merged by the pen's own
    width, so this is `route_pen_width_px * STRAND_MERGE_WIDTHS`. Otherwise the
    route is drawn in the route ink's own width and this is `route_ink.px *
    STRAND_MERGE_WIDTHS`. Only `pipeline.paint` reads it: the pen plate itself
    reads base-group fields only.
    """
    ink = style.route_ink
    if style.route.route_pen and ink.style == "pen":
        return style.route.route_pen_width_px * STRAND_MERGE_WIDTHS
    return ink.px * STRAND_MERGE_WIDTHS


def merge_strands(
    route_px: list[tuple[float, float]], reach_px: float
) -> list[tuple[float, float]]:
    """Draw a stretch the route runs more than once as one stroke.

    Where the track came back along a path it had already run, the passes are
    one leg on the map, and the reader should see one line there, as on a hand
    drawn route map: an out-and-back reads as a spur, not as two roads. A pass
    that came back on the very same pixels is already that line and is left
    alone. One that came back a few pixels off, on the other side of the road or
    through a drifting GPS, is pulled across onto the line midway between it and
    the earlier pass, and the earlier pass is pulled to meet it, so the leg is
    drawn once where it lies between them. A leg run three times is pulled
    together the same way, every pass onto the middle of all three. The pull
    is eased in and out along the path so the passes meet and part as curves
    rather than steps.

    Args:
        route_px: The track in display pixels.
        reach_px: How near, centre to centre, a later pass has to come to an
            earlier one to be drawn on the same line.

    Returns:
        The track, pulled together. The same list back when nothing was pulled,
        so a route that never comes back within `reach_px` of itself, or comes
        back only on its own pixels, is drawn on its own line exactly as it was.
    """
    n = len(route_px)
    if n < MIN_STRAND_POINTS or reach_px <= 0:
        return route_px
    cum = [0.0]
    for a, b in pairwise(route_px):
        cum.append(cum[-1] + math.dist(a, b))
    pull = _pulls(route_px, cum, reach_px)
    if not any(pull):
        return route_px
    pull = ease_along(pull, cum, reach_px * STRAND_EASE_WIDTHS)
    out: list[tuple[float, float]] = []
    for i, (x, y) in enumerate(route_px):
        tx, ty = tangent_at(route_px, i)
        out.append((x - ty * pull[i], y + tx * pull[i]))
    return out


def _pulls(route_px: list[tuple[float, float]], cum: list[float], reach_px: float) -> list[float]:
    """How far each point is pulled along its left normal to the middle of the passes near it."""
    n = len(route_px)
    min_arc = reach_px * STRAND_MIN_ARC
    # The route's own points in cells the size of the reach, so each point is
    # measured against the handful that could be near it rather than all of them.
    cell = max(reach_px, 1e-6)
    grid: dict[tuple[int, int], list[int]] = {}
    for i, (x, y) in enumerate(route_px):
        grid.setdefault((int(x // cell), int(y // cell)), []).append(i)
    pull = [0.0] * n
    for i, (x, y) in enumerate(route_px):
        gx, gy = int(x // cell), int(y // cell)
        near = sorted(
            j
            for cx in (gx - 1, gx, gx + 1)
            for cy in (gy - 1, gy, gy + 1)
            for j in grid.get((cx, cy), ())
            if abs(cum[i] - cum[j]) >= min_arc and math.dist(route_px[i], route_px[j]) < reach_px
        )
        if not near:
            continue
        tx, ty = tangent_at(route_px, i)
        offsets = [
            # The other pass's offset across this one's line, on the left normal
            # (-ty, tx): only the part across the line is a second stroke, the
            # part along it is the same leg further on.
            -ty * (route_px[j][0] - x) + tx * (route_px[j][1] - y)
            for j in _nearest_per_pass(near, cum, route_px[i], route_px, reach_px)
        ]
        # The middle of every pass here, this one's own offset of nought included.
        pull[i] = sum(offsets) / (len(offsets) + 1)
    return pull


def _nearest_per_pass(
    near: list[int],
    cum: list[float],
    at: tuple[float, float],
    route_px: list[tuple[float, float]],
    reach_px: float,
) -> list[int]:
    """The nearest point of each other pass among `near`, sorted indices within the reach.

    A pass is a run of `near` with no more than `PASS_BREAK_REACHES` reaches of path
    between neighbours: the points one pass has within the reach lie together along it.
    """
    passes: list[list[int]] = [[near[0]]]
    for a, b in pairwise(near):
        if cum[b] - cum[a] > reach_px * PASS_BREAK_REACHES:
            passes.append([])
        passes[-1].append(b)
    return [min(run, key=lambda j: math.dist(at, route_px[j])) for run in passes]
