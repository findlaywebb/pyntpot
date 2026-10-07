"""SVG path data for the vector map: point lists in, `d` strings out, and back.

Key names: `path_d`, one polyline; `stroke_d`, a short stroke as relative steps;
`rings_path`, every ring of a layer as one path wound for `fill-rule="nonzero"`;
`parse_path`, the inverse of `path_d`.

`path_d` writes coordinates to a tenth of a metre by default and `stroke_d` to a whole
metre, and that rounding is the format of the vector map's output: a reader recovers
points only to that precision. It does
not project, simplify or clip; the caller hands it finished points.
"""

from pyntpot.ink.polyline import Pt
from pyntpot.maps.rings import orient

#: The fewest points that make a line, and so a path.
MIN_LINE_POINTS = 2

#: The fewest points that make a ring worth filling.
MIN_RING_POINTS = 3


def path_d(points: list[Pt], *, close: bool = False, places: int = 1) -> str:
    """SVG path data for one polyline, rounded to `places` decimals."""
    if len(points) < MIN_LINE_POINTS:
        return ""
    d = "M" + " L".join(f"{x:.{places}f},{y:.{places}f}" for x, y in points)
    return d + "Z" if close else d


def stroke_d(points: list[Pt]) -> str:
    """Compact path data for a short stroke: absolute start, relative steps.

    A hachure field is thousands of short lines, and short deltas take far
    fewer characters than absolute coordinates. Each step is rounded to a whole
    metre on its own, so the rounding can add up along the stroke.
    """
    if len(points) < MIN_LINE_POINTS:
        return ""
    out = f"M{points[0][0]:.0f},{points[0][1]:.0f}"
    prev = points[0]
    for x, y in points[1:]:
        out += f"l{x - prev[0]:.0f},{y - prev[1]:.0f}"
        prev = (x, y)
    return out


def rings_path(rings: list[list[Pt]], holes: list[list[Pt]] | None = None) -> str:
    """One path holding every ring of a layer, wound for `fill-rule="nonzero"`.

    Args:
        rings: Filled rings.
        holes: Rings that punch through them.

    Returns:
        The concatenated path data, empty when there is nothing to fill.
    """
    parts = [
        path_d(orient(r, counter_clockwise=True), close=True)
        for r in rings
        if len(r) >= MIN_RING_POINTS
    ]
    parts += [
        path_d(orient(r, counter_clockwise=False), close=True)
        for r in (holes or [])
        if len(r) >= MIN_RING_POINTS
    ]
    return "".join(p for p in parts if p)


def parse_path(d: str) -> list[list[Pt]]:
    """The point lists inside one `M x,y L x,y` path, the inverse of `path_d`."""
    out: list[list[Pt]] = []
    for piece in d.split("M"):
        chunk = piece.strip().rstrip("Z").strip()
        if not chunk:
            continue
        pts: list[Pt] = []
        for token in chunk.replace("L", " ").split():
            if "," in token:
                a, b = token.split(",")
                pts.append((float(a), float(b)))
        if len(pts) > 1:
            out.append(pts)
    return out
