"""Windows of a line: the run a name is set along, how far it turns, and where a distance falls.

Key names: `_window`, the run of a line a name's width long from a start; `_turning`
and `_bow`, how far a run turns and how far it bows off its chord; `_on_line` and
`_bisect`, the point and bearing at a distance along a line.

It does not choose a window, price one or write along it.

Invariants: a window is `None` when the line is too short for it, and a point asked for
past either end of a line is the end.
"""

import math

from pyntpot.ink.polyline import Pt

#: Past this much turning across the run, text is not set along a line. The one
#: rule that separates elegant from unreadable.
MAX_TURN_DEG = 62.0


#: And past this much wander off the straight line between its ends.
MAX_BOW_FRAC = 0.09


def _window(line: list[Pt], start: int, want: float) -> list[Pt] | None:
    """The run of a line from one point that is `want` long, or None."""
    out = [line[start]]
    run = 0.0
    for i in range(start + 1, len(line)):
        run += math.dist(line[i - 1], line[i])
        out.append(line[i])
        if run >= want:
            return out
    return None


def _turning(pts: list[Pt]) -> float:
    """Total turning along a polyline, in degrees.

    The test that decides whether text can be set along something. Curvature at
    a point says nothing: what makes a run unreadable is how far round it goes
    from one end to the other.
    """
    total = 0.0
    for a, b, c in zip(pts, pts[1:], pts[2:], strict=False):
        u = math.atan2(b[1] - a[1], b[0] - a[0])
        v = math.atan2(c[1] - b[1], c[0] - b[0])
        total += abs((v - u + math.pi) % math.tau - math.pi)
    return math.degrees(total)


def _bow(pts: list[Pt]) -> float:
    """How far a run wanders off the straight line between its own ends."""
    (ax, ay), (bx, by) = pts[0], pts[-1]
    run = math.hypot(bx - ax, by - ay) or 1.0
    return max(abs((bx - ax) * (ay - y) - (ax - x) * (by - ay)) / run for x, y in pts)


def _on_line(line: list[Pt], cum: list[float], at: float) -> tuple[Pt, float]:
    """The point at an arc length along a line, and the tangent's angle there."""
    at = min(max(at, 0.0), cum[-1])
    i = min(_bisect(cum, at), len(line) - 2)
    run = max(cum[i + 1] - cum[i], 1e-9)
    t = (at - cum[i]) / run
    (ax, ay), (bx, by) = line[i], line[i + 1]
    return ((ax + (bx - ax) * t, ay + (by - ay) * t), math.atan2(by - ay, bx - ax))


def _bisect(cum: list[float], at: float) -> int:
    """The segment an arc length falls in."""
    lo, hi = 0, len(cum) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if cum[mid] <= at:
            lo = mid
        else:
            hi = mid
    return lo
