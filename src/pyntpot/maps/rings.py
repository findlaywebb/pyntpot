"""Rings in card metres: their winding, containment and clipping.

Key names: `Rings`, an outer-rings and hole-rings pair; `signed_area` and
`orient`, which wind a ring one way or the other; `point_in_ring`, an even-odd
containment test; `clip_ring`, a Sutherland-Hodgman clip to a rectangle.

It does not project coordinates, build rings from map data or write them as path
data. Invariants: a ring is a list of points with the closing edge implied, and
`orient` never changes which points a ring holds, only their order.
"""

from pyntpot.ink.polyline import Pt

#: A layer's outer rings and the holes punched through them.
Rings = tuple[list[list[Pt]], list[list[Pt]]]


def signed_area(ring: list[Pt]) -> float:
    """Twice the signed area of a ring; positive is counter-clockwise."""
    total = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        total += x1 * y2 - x2 * y1
    return total


def orient(ring: list[Pt], *, counter_clockwise: bool = True) -> list[Pt]:
    """The ring wound the way asked for.

    Every filled layer is drawn as one path with `fill-rule="nonzero"`, so an
    outer ring must wind one way and a hole the other. That is what stops two
    overlapping woods stacking their alpha into a darker patch.
    """
    if (signed_area(ring) > 0) != counter_clockwise:
        return list(reversed(ring))
    return list(ring)


def point_in_ring(x: float, y: float, ring: list[Pt]) -> bool:
    """Even-odd point-in-polygon test."""
    inside = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x < xc:
                inside = not inside
    return inside


def clip_ring(ring: list[Pt], box: tuple[float, float, float, float]) -> list[Pt]:
    """Sutherland-Hodgman clip of a ring to an axis-aligned rectangle.

    A wood relation that covers the whole sheet is not dropped for being big:
    it is cut down to the sheet, so a large wood still shades the corner of the
    sheet it covers.

    Args:
        ring: Closed ring in metres.
        box: (xmin, ymin, xmax, ymax) in metres.

    Returns:
        The clipped ring, empty when nothing survives.
    """
    xmin, ymin, xmax, ymax = box
    edges = (
        (lambda p: p[0] >= xmin, 0, xmin),
        (lambda p: p[0] <= xmax, 0, xmax),
        (lambda p: p[1] >= ymin, 1, ymin),
        (lambda p: p[1] <= ymax, 1, ymax),
    )
    out = list(ring)
    for keep, axis, at in edges:
        if not out:
            return []
        nxt: list[Pt] = []
        for i in range(len(out)):
            cur, prev = out[i], out[i - 1]
            cur_in, prev_in = keep(cur), keep(prev)
            if cur_in != prev_in:
                span = cur[axis] - prev[axis]
                t = 0.0 if span == 0 else (at - prev[axis]) / span
                nxt.append((prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])))
            if cur_in:
                nxt.append(cur)
        out = nxt
    return out
