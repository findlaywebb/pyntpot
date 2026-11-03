"""Cutting a polyline to a box: the pieces inside it, cut where the line crosses the edge.

Key function: `cut_line`, the pieces of a line inside a rectangle, each starting and ending
on the rectangle's edge where the line comes in or goes out, so a line that runs off a card
is drawn up to the card's edge. `pyntpot.ink.polyline.clip_line` is the coarser clip that
keeps or drops whole points.

It knows no units and holds no state; it does not simplify, smooth or join the pieces.

Invariants: every point of every piece lies in the box; a piece's end that is not a point
of the line lies exactly on the box's edge; a piece has at least two distinct points.
"""

import itertools

from pyntpot.ink.polyline import Point


def cut_line(line: list[Point], box: tuple[float, float, float, float]) -> list[list[Point]]:
    """Split a polyline into its pieces inside a rectangle, cut where it crosses the edge.

    Unlike `clip_line`, a piece that comes in from outside starts on the box's edge
    rather than at its first point inside, and one that goes out ends on it, so a
    line that runs off the box is drawn up to the edge. A piece that only touches the
    box at a point is dropped.
    """
    out: list[list[Point]] = []
    run: list[Point] = []
    for a, b in itertools.pairwise(line):
        cut = _cut_segment(a, b, box)
        if cut is None or cut[0] == cut[1]:
            continue
        if not run or run[-1] != cut[0]:
            if len(run) > 1:
                out.append(run)
            run = [cut[0]]
        run.append(cut[1])
    if len(run) > 1:
        out.append(run)
    return out


def _cut_segment(
    a: Point, b: Point, box: tuple[float, float, float, float]
) -> tuple[Point, Point] | None:
    """The part of segment `ab` inside the box, its cut ends held on the edge, or None.

    The segment is walked as `a + t (b - a)` and each of the box's four sides narrows
    the span of `t` that is inside (Liang and Barsky's clip).
    """
    xmin, ymin, xmax, ymax = box
    dx, dy = b[0] - a[0], b[1] - a[1]
    # Each side: how fast the segment walks out through it, how far it has to go,
    # and the side's own axis and value, which a cut through it is held to exactly.
    sides = (
        (-dx, a[0] - xmin, 0, xmin),
        (dx, xmax - a[0], 0, xmax),
        (-dy, a[1] - ymin, 1, ymin),
        (dy, ymax - a[1], 1, ymax),
    )
    lo, hi = (0.0, a), (1.0, b)
    for step, room, axis, value in sides:
        if step == 0:
            if room < 0:
                return None
            continue
        t = room / step
        cut = [min(max(a[0] + t * dx, xmin), xmax), min(max(a[1] + t * dy, ymin), ymax)]
        cut[axis] = value
        if step < 0 and t > lo[0]:
            lo = (t, (cut[0], cut[1]))
        elif step > 0 and t < hi[0]:
            hi = (t, (cut[0], cut[1]))
    if lo[0] > hi[0]:
        return None
    return lo[1], hi[1]
