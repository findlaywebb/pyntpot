"""Curves through and beside a polyline: a spline through it, an offset curve beside it.

Key functions: `spline`, a Catmull-Rom curve through every point of a line,
broken at its corners; `offset_curve`, a line pushed off to one side and
mitred at its corners, with `unit_normal` the segment normal it is built from
and `MITER_LIMIT` the mitre's cut-off.

It knows no units beyond its caller's and paints nothing.

Invariants: `spline` passes through every point it is given; `offset_curve`
returns at most one point for each point it is given; neither changes its
input.
"""

import itertools
import math

from pyntpot.ink.polyline import Pt

#: The fewest points a spline needs to curve: a shorter line comes back as it was.
_FEWEST_TO_SPLINE = 3
#: A length or a mitre share at or below this is treated as zero.
_DEGENERATE = 1e-9


def spline(pts: list[Pt], step: float, corners: set[int] | None = None) -> list[Pt]:
    """A Catmull-Rom curve through every one of `pts`, sampled every `step`.

    Through them and not near them: the points are the turns the road makes,
    and a curve that only approaches them has lost the shape it was given.

    Broken at every point in `corners`. A Catmull-Rom curve is smooth
    everywhere by construction, so a corner run through it comes out as an arc,
    and a corner drawn as an arc is too rounded where the route gives clear
    bends to follow. Splining each run between corners on its own leaves
    the corner as a corner and the rest as curve.

    Source: `catmull-rom` in docs/explanation/references.md.
    """
    if len(pts) < _FEWEST_TO_SPLINE:
        return list(pts)
    cuts = sorted(corners or set())
    if cuts:
        out: list[Pt] = []
        edges = [0, *cuts, len(pts) - 1]
        for a, b in itertools.pairwise(edges):
            run = spline(pts[a : b + 1], step)
            out.extend(run if not out else run[1:])
        return out
    ends = [pts[0], *pts, pts[-1]]
    out = [pts[0]]
    for i in range(len(pts) - 1):
        p0, p1, p2, p3 = ends[i], ends[i + 1], ends[i + 2], ends[i + 3]
        n = max(int(math.dist(p1, p2) / step), 2)
        for k in range(1, n + 1):
            t = k / n
            t2, t3 = t * t, t * t * t
            out.append(
                (
                    0.5
                    * (
                        (2 * p1[0])
                        + (-p0[0] + p2[0]) * t
                        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
                    ),
                    0.5
                    * (
                        (2 * p1[1])
                        + (-p0[1] + p2[1]) * t
                        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
                    ),
                )
            )
    return out


#: How far a mitred corner may reach past the offset before it is cut off, as
#: a multiple of the offset. A corner pushed off along its own bisector stands
#: out by one over the cosine of half its turn, which runs away as the turn
#: approaches a hairpin: two and a half offsets is about a 132 degree turn, and
#: past that the corner is bevelled instead.
MITER_LIMIT = 2.5


def offset_curve(shape: list[Pt], side: int, offset_px: float) -> list[Pt]:
    """The shape pushed off to one side by the offset, mitred at its corners.

    Point by point along the normals is right in the middle of a segment and
    wrong at a corner: the two offset limbs either side of a convex corner do
    not meet, and joining their end points cuts the corner off. Each point is
    pushed along the bisector of its two segments instead, far enough that both
    limbs stand off by the offset, which is a mitre and keeps the corner. Past
    `MITER_LIMIT` the mitre is cut back to a bevel, so a hairpin does not throw
    a spike across the sheet.

    `side` is +1 for the left of travel in card pixels and -1 for the right.
    """
    out: list[Pt] = []
    for i, p in enumerate(shape):
        before = unit_normal(shape, i - 1, i)
        after = unit_normal(shape, i, i + 1)
        n1 = before or after
        n2 = after or before
        if n1 is None or n2 is None:  # no segment either side of this point
            continue
        mx, my = n1[0] + n2[0], n1[1] + n2[1]
        share = 1.0 + n1[0] * n2[0] + n1[1] * n2[1]
        if share < _DEGENERATE:  # the line doubles back on itself: no mitre exists
            out.append((p[0] + side * n1[0] * offset_px, p[1] + side * n1[1] * offset_px))
            continue
        mx, my = mx / share, my / share
        reach = math.hypot(mx, my)
        if reach > MITER_LIMIT:
            # Cut the mitre back along its own bisector rather than replacing
            # it with the two limb ends: a pair of points either side of a turn
            # of a hundred and seventy degrees is a spike, not a corner, and
            # the junction by the river drew one.
            mx, my = mx / reach * MITER_LIMIT, my / reach * MITER_LIMIT
        out.append((p[0] + side * mx * offset_px, p[1] + side * my * offset_px))
    return out


def unit_normal(pts: list[Pt], i: int, j: int) -> Pt | None:
    """The unit normal of one segment, or None when there is no segment.

    Unlike `polyline.normal_at` it points right of the direction of travel, is
    taken along the one segment from `i` to `j`, and is None rather than a
    fallback when that segment is degenerate.
    """
    if i < 0 or j > len(pts) - 1:
        return None
    ax, ay = pts[i]
    bx, by = pts[j]
    run = math.hypot(bx - ax, by - ay)
    if run < _DEGENERATE:
        return None
    return ((by - ay) / run, -(bx - ax) / run)
