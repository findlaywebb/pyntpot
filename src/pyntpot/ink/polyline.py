"""Polyline geometry: simplify, smooth, clip, measure, cross and wobble a line.

Key types: `Pt`, one point as an `(x, y)` pair of floats, and a polyline as a
list of them. The functions measure a line (`length`, `length_indexed`,
`running_length`, `cumulative_m`), reshape it (`simplify`, `smooth`,
`clip_line`, `eased`, `ease_along`, `deform_line`), and answer local questions
about it (`normal_at`, `normals`, `tangent_at`, `side`, `segments_cross`,
`meet`, `seg_gap`, `foot_on`, `point_to_segment`).

It knows no units: a line is in whatever space its caller works in, metres or
pixels, and every tolerance is in that same space. It paints nothing, reads no
style and holds no state; `deform_line` draws only from the generator it is
handed.

Invariants: no function changes its input; `Pt` is the one point alias outside the interim port code, and `maps`
and `letters` import it from here.
"""

import itertools
import math

import numpy as np
from numpy.typing import ArrayLike

Pt = tuple[float, float]

#: The fewest points a line needs to have one between its ends: a shorter line
#: has nothing to drop, cut or average and comes back as it was.
_FEWEST_WITH_A_MIDDLE = 3
#: A squared length or a cross product at or below this is treated as zero:
#: the segment is a point, or the two segments are parallel.
_DEGENERATE_AREA = 1e-12
#: A length at or below this is treated as zero: the segment has no direction.
_DEGENERATE_RUN = 1e-9
#: A line is an array of points with this many dimensions: rows of `(x, y)`.
_LINE_NDIM = 2
#: The fewest points a line needs to have a segment to displace.
_FEWEST_POINTS = 2
#: `deform_line` stops doubling once a line has more points than this.
_DEFORM_MAX_POINTS = 24000


def simplify(points: list[Pt], eps: float) -> list[Pt]:
    """Douglas-Peucker simplification, iterative so a long ring cannot recurse away.

    Args:
        points: Polyline in metres.
        eps: Tolerance in metres. Larger is more stylised.

    Returns:
        The kept subset; the first and last point are always kept.
    """
    if len(points) < _FEWEST_WITH_A_MIDDLE:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        lo, hi = stack.pop()
        if hi <= lo + 1:
            continue
        ax, ay = points[lo]
        bx, by = points[hi]
        dx, dy = bx - ax, by - ay
        den = math.hypot(dx, dy)
        best, bi = -1.0, lo
        for i in range(lo + 1, hi):
            px, py = points[i]
            if den == 0:
                d = math.hypot(px - ax, py - ay)
            else:
                d = abs(dy * px - dx * py + bx * ay - by * ax) / den
            if d > best:
                best, bi = d, i
        if best > eps:
            keep[bi] = True
            stack.append((lo, bi))
            stack.append((bi, hi))
    return [p for p, k in zip(points, keep, strict=True) if k]


def smooth(points: list[Pt], passes: int = 2, *, closed: bool = False) -> list[Pt]:
    """Chaikin corner cutting, which rounds a marching-squares staircase off.

    Args:
        points: Polyline in metres.
        passes: How many rounds of cutting.
        closed: Treat the polyline as a ring.

    Returns:
        The smoothed polyline.
    """
    out = list(points)
    for _ in range(passes):
        if len(out) < _FEWEST_WITH_A_MIDDLE:
            return out
        nxt: list[Pt] = [] if closed else [out[0]]
        span = len(out) if closed else len(out) - 1
        for i in range(span):
            (ax, ay), (bx, by) = out[i], out[(i + 1) % len(out)]
            nxt.append((ax + 0.25 * (bx - ax), ay + 0.25 * (by - ay)))
            nxt.append((ax + 0.75 * (bx - ax), ay + 0.75 * (by - ay)))
        if not closed:
            nxt.append(out[-1])
        out = nxt
    return out


def clip_line(line: list[Pt], box: tuple[float, float, float, float]) -> list[list[Pt]]:
    """Split a polyline into the pieces that lie inside a rectangle."""
    xmin, ymin, xmax, ymax = box

    def inside(p: Pt) -> bool:
        return xmin <= p[0] <= xmax and ymin <= p[1] <= ymax

    out: list[list[Pt]] = []
    run: list[Pt] = []
    for p in line:
        if inside(p):
            run.append(p)
        else:
            if len(run) > 1:
                out.append(run)
            run = []
    if len(run) > 1:
        out.append(run)
    return out


def point_to_segment(p: Pt, a: Pt, b: Pt) -> float:
    """Distance from a point to a segment."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = dx * dx + dy * dy
    t = (
        0.0
        if run < _DEGENERATE_AREA
        else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / run))
    )
    return math.dist(p, (a[0] + dx * t, a[1] + dy * t))


def normal_at(pts: list[Pt], i: int) -> Pt:
    """The unit left normal of a polyline at one of its points."""
    a = pts[max(i - 1, 0)]
    b = pts[min(i + 1, len(pts) - 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = math.hypot(dx, dy)
    return (-dy / run, dx / run) if run > _DEGENERATE_RUN else (0.0, 1.0)


def eased(values: list[float], reach: int) -> list[float]:
    """A moving average over `reach` samples either side, ends held."""
    if reach < 1 or len(values) < _FEWEST_WITH_A_MIDDLE:
        return values
    out = []
    for i in range(len(values)):
        lo, hi = max(i - reach, 0), min(i + reach + 1, len(values))
        out.append(sum(values[lo:hi]) / (hi - lo))
    return out


def side(a: Pt, b: Pt, c: Pt) -> float:
    """Cross product of ab and ac; its sign says which side of ab c lies."""
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def segments_cross(a: Pt, b: Pt, c: Pt, d: Pt) -> bool:
    """True when segment ab properly crosses segment cd."""
    d1, d2 = side(c, d, a), side(c, d, b)
    d3, d4 = side(a, b, c), side(a, b, d)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def length(line: list[Pt]) -> float:
    """How long a polyline is, end to end along itself."""
    return sum(math.dist(a, b) for a, b in itertools.pairwise(line))


def length_indexed(pts: list[Pt]) -> float:
    """The length of a polyline."""
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def running_length(line: list[Pt]) -> list[float]:
    """Cumulative length at each point of a polyline."""
    out: list[float] = [0.0]
    for i in range(1, len(line)):
        out.append(out[-1] + math.dist(line[i - 1], line[i]))
    return out


def cumulative_m(route_px: list[Pt], scale: float) -> list[float]:
    """Metres covered at each route point, from the track drawn in card pixels."""
    out: list[float] = [0.0]
    for i in range(1, len(route_px)):
        out.append(out[-1] + math.dist(route_px[i - 1], route_px[i]) / max(scale, 1e-9))
    return out


def meet(a: Pt, b: Pt, c: Pt, d: Pt) -> Pt | None:
    """Where two segments cross, or None when they do not."""
    rx, ry = b[0] - a[0], b[1] - a[1]
    sx, sy = d[0] - c[0], d[1] - c[1]
    den = rx * sy - ry * sx
    if abs(den) < _DEGENERATE_AREA:
        return None
    t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den
    u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
    if not (0.0 < t < 1.0 and 0.0 < u < 1.0):
        return None
    return (a[0] + rx * t, a[1] + ry * t)


def seg_gap(a: Pt, b: Pt, c: Pt, d: Pt) -> float:
    """The distance between two segments. Zero when they cross."""
    if meet(a, b, c, d) is not None:
        return 0.0
    return min(
        foot_on(a, [c, d])[0],
        foot_on(b, [c, d])[0],
        foot_on(c, [a, b])[0],
        foot_on(d, [a, b])[0],
    )


def foot_on(p: Pt, poly: list[Pt]) -> tuple[float, Pt]:
    """The distance from a point to a polyline, and the point it lands on.

    Segments, not vertices. A track sampled every few pixels and a bracket
    sampled every one measure differently against the two, and it is the
    segment that is the road.
    """
    best = (float("inf"), poly[0])
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        bx, by = poly[i + 1]
        vx, vy = bx - ax, by - ay
        run = vx * vx + vy * vy
        if run <= _DEGENERATE_AREA:
            foot = (ax, ay)
        else:
            t = ((p[0] - ax) * vx + (p[1] - ay) * vy) / run
            t = 0.0 if t < 0.0 else min(t, 1.0)
            foot = (ax + t * vx, ay + t * vy)
        d = math.dist(p, foot)
        if d < best[0]:
            best = (d, foot)
    return best


def tangent_at(pts: list[tuple[float, float]], i: int) -> tuple[float, float]:
    """The unit direction of travel at one point, by central difference."""
    a = pts[max(i - 1, 0)]
    b = pts[min(i + 1, len(pts) - 1)]
    dx, dy = b[0] - a[0], b[1] - a[1]
    run = math.hypot(dx, dy)
    return (dx / run, dy / run) if run > _DEGENERATE_RUN else (1.0, 0.0)


def ease_along(push: list[float], cum: list[float], reach: float) -> list[float]:
    """A moving average of the displacement over `reach` of path either side.

    In path length rather than in samples, because the track is downsampled for
    display and a window counted in points is a different length of ground at
    each end of it.
    """
    if reach <= 0:
        return push
    out = [0.0] * len(push)
    lo = hi = 0
    total = 0.0
    for i, at in enumerate(cum):
        while hi < len(push) and cum[hi] <= at + reach:
            total += push[hi]
            hi += 1
        while cum[lo] < at - reach:
            total -= push[lo]
            lo += 1
        out[i] = total / max(hi - lo, 1)
    return out


def normals(pts: list[Pt]) -> list[Pt]:
    """A unit normal at every point of a run, from a smoothed tangent."""
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[max(i - 3, 0)], pts[min(i + 3, n - 1)]
        run = math.hypot(b[0] - a[0], b[1] - a[1]) or 1.0
        out.append((-(b[1] - a[1]) / run, (b[0] - a[0]) / run))
    return out


def deform_line(
    line: ArrayLike,
    deform: tuple[np.random.Generator, float, int, float, float, float],
) -> np.ndarray:
    """The same recursive midpoint displacement, on an open polyline.

    `deform_ring` is the closed version and the only thing closure changes is
    that the last point joins the first. A leader, an underline and a span line
    are all open, and they all want the same thing a wood's edge wants: a
    different wobble frequency in different parts of the line, so no two
    instances of the same gesture are the same curve.

    The ends are left where they were, because a leader that misses its pin is
    not a hand-drawn leader, it is a wrong one.

    Args:
        line: The polyline, `(n, 2)` in whatever units the caller works in.
        deform: `(rng, amount, depth, decay, cap, min_seg)`, the same tuple
            `deform_ring` is unpacked from. `rng` is the generator the
            displacements are drawn from; `amount` the first round's variance,
            as a share of a segment's length; `depth` how many rounds, each
            doubling the point count; `decay` what each round hands its
            children, before the randomisation; `cap` the largest one
            displacement may be, in the caller's units; `min_seg` stops it
            once the typical segment is shorter than this.

    Returns:
        The deformed line, `(m, 2)`, with the first and last points unmoved.
    """
    rng, amount, depth, decay, cap, min_seg = deform
    p = np.asarray(line, dtype=np.float64)
    if p.ndim != _LINE_NDIM or len(p) < _FEWEST_POINTS:
        return p
    var = np.full(max(len(p) - 1, 1), max(amount, 0.0))
    for _ in range(max(int(depth), 0)):
        n = len(p) - 1
        if n < 1 or len(p) > _DEFORM_MAX_POINTS:
            break
        a, b = p[:-1], p[1:]
        d = b - a
        seg = np.hypot(d[:, 0], d[:, 1])
        if float(np.median(seg)) < min_seg:
            break
        ln = np.maximum(seg, 1e-9)
        off = np.clip(rng.normal(0.0, 1.0, n) * var * seg, -cap, cap)
        mid = 0.5 * (a + b)
        mid[:, 0] -= d[:, 1] / ln * off
        mid[:, 1] += d[:, 0] / ln * off
        out = np.empty((2 * n + 1, 2))
        out[0::2] = p
        out[1::2] = mid
        p = out
        var = np.repeat(var, 2) * decay * rng.uniform(0.75, 1.25, 2 * n)
    return p
