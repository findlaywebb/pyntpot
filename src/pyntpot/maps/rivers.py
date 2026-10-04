"""How wide a river is, measured off the water area it runs in.

Key names: `channel`, one watercourse re-centred in its channel with its width at
each sample; `measured_width_m`, the median width over the runs inside mapped
water; `painted_width_px`, the width to draw it at; `major_rivers`, which
watercourses of a box are the main ones.

OSM maps a big river twice, as a centreline and as a polygon, and only the polygon
says how much room it takes. This module reads both. It does not fetch or parse map
data, choose a colour or draw a stroke. Invariants: a width is None, never zero,
where no mapped area was met, and thin water is drawn at its class floor while wide
water is drawn at its own width.
"""

from pyntpot.ink.polyline import Pt, eased, length, normal_at
from pyntpot.maps.rings import point_in_ring
from pyntpot.maps.track_index import _densify

#: The fewest points that make a ring a water area.
MIN_RING_POINTS = 3

#: A ray and a bank closer to parallel than this never meet.
PARALLEL_EPS = 1e-12

#: The least distance along a ray that counts as ahead of its start.
AHEAD_EPS = 1e-6

#: How far apart the samples are when a watercourse is measured against the
#: water it flows in, in metres.
WIDTH_STEP_M = 25.0


#: How many samples either side the sideways correction is averaged over, so a
#: river slides into the middle of its channel rather than stepping into it.
CHANNEL_EASE_SAMPLES = 4


#: How far a watercourse has to run *inside* a mapped water area before that
#: area is taken as its own banks, in metres. A river is as wide as the water it
#: runs along, not as the water it runs into: a stream that meets a big river
#: inside the river's own polygon would otherwise measure 212 m and be drawn as
#: the main river of the sheet.
WIDTH_RUN_M = 250.0


def _ring_boxes(rings: list[list[Pt]]) -> list[tuple[list[Pt], tuple[float, ...]]]:
    """Each ring with its bounding box, so a point tests against few of them."""
    out = []
    for ring in rings:
        if len(ring) < MIN_RING_POINTS:
            continue
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        out.append((ring, (min(xs), min(ys), max(xs), max(ys))))
    return out


def _ray_to_ring(p: Pt, d: Pt, ring: list[Pt]) -> float | None:
    """Distance from `p` along the unit direction `d` to the first bank ahead."""
    best: float | None = None
    for a, b in zip(ring, ring[1:] + ring[:1], strict=False):
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < PARALLEL_EPS:
            continue
        t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
        u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if t > AHEAD_EPS and 0.0 <= u <= 1.0 and (best is None or t < best):
            best = t
    return best


def _ring_at(p: Pt, boxed: list[tuple[list[Pt], tuple[float, ...]]]) -> list[Pt] | None:
    """The mapped water area this point falls inside, or None."""
    for ring, (x0, y0, x1, y1) in boxed:
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and point_in_ring(p[0], p[1], ring):
            return ring
    return None


def _banks_at(
    p: Pt, n: Pt, boxed: list[tuple[list[Pt], tuple[float, ...]]]
) -> tuple[float | None, float]:
    """The width of the water at `p` and the sideways shift to its middle.

    The width is None where `p` is not in mapped water. Where only one bank is
    found the width is twice it and the shift is zero.
    """
    ring = _ring_at(p, boxed) if boxed else None
    if ring is None:
        return None, 0.0
    left = _ray_to_ring(p, n, ring)
    right = _ray_to_ring(p, (-n[0], -n[1]), ring)
    if left is not None and right is not None:
        return left + right, (left - right) / 2
    one = left if left is not None else right
    if one is not None:
        return 2.0 * one, 0.0
    return None, 0.0


def channel(line: list[Pt], rings: list[list[Pt]]) -> tuple[list[Pt], list[float | None]]:
    """One watercourse re-centred in its own channel, and how wide it is.

    OSM's centreline says where a river goes; it does not promise to run down
    the middle of it. A centreline can hug one bank for half its run, and a
    stroke a quarter of a kilometre wide centred on that line overshoots one
    bank and falls short of the other.

    So the banks are found rather than assumed. At each sample the local normal
    is cast both ways to the water's edge: the width is what the two rays
    together measure, and the middle of them is where the line should have been.
    Where only one ray lands the width is twice it and the point is left where
    it was, because one bank cannot say where the middle is. The sideways
    correction is eased along the line so the water does not step.

    Args:
        line: A watercourse centreline, in metres.
        rings: Every mapped water area on the card, in metres.

    Returns:
        The line resampled every `WIDTH_STEP_M` and re-centred where it could
        be, and the width in metres at each of those samples, or None at a
        sample that is not in mapped water.
    """
    pts = _densify(line, WIDTH_STEP_M)
    boxed = _ring_boxes(rings)
    widths: list[float | None] = []
    offsets: list[float] = []
    normals: list[Pt] = []
    for i, p in enumerate(pts):
        n = normal_at(pts, i)
        normals.append(n)
        width, offset = _banks_at(p, n, boxed)
        widths.append(width)
        offsets.append(offset)
    offsets = eased(offsets, CHANNEL_EASE_SAMPLES)
    moved = [
        (p[0] + n[0] * off, p[1] + n[1] * off)
        for p, n, off in zip(pts, normals, offsets, strict=False)
    ]
    return moved, widths


def _accepted(widths: list[float | None]) -> list[float]:
    """The widths from runs long enough to be the watercourse's own banks.

    A river is as wide as the water it runs along, not as the water it runs
    into: a tributary's mouth inside the main river's polygon is a handful of
    samples and buys no measurement at all.
    """
    kept: list[float] = []
    run: list[float] = []
    for w in [*widths, None]:
        if w is not None:
            run.append(w)
            continue
        if len(run) * WIDTH_STEP_M >= WIDTH_RUN_M:
            kept += run
        run = []
    return kept


def measured_width_m(lines: list[list[Pt]], rings: list[list[Pt]]) -> float | None:
    """How wide one watercourse really is, from the water area it runs in.

    OSM maps a big river twice: a centreline that says where it goes and a
    polygon that says how much room it takes. The card only ever read the
    centreline, so a big river was drawn at the width the importance curve chose
    for it and not at the quarter kilometre it actually occupies.

    Args:
        lines: The watercourse's centrelines, in metres.
        rings: Every mapped water area on the card, in metres.

    Returns:
        The median width in metres over the accepted runs, or None where the
        watercourse never runs far enough inside a mapped area.
    """
    if not rings:
        return None
    kept: list[float] = []
    for line in lines:
        if len(line) > 1:
            kept += _accepted(channel(line, rings)[1])
    if not kept:
        return None
    kept.sort()
    return kept[len(kept) // 2]


def painted_width_px(floor_px: float, measured_m: float, mppd: float) -> float:
    """How wide one watercourse is drawn, in display pixels.

    **Thin water is exaggerated up to the class floor; wide water is drawn at
    its own width and never narrowed to fit.** The importance curve is what a
    watercourse is drawn at when nothing else says: a brook two metres across
    has to be exaggerated fortyfold to appear on the sheet at all, and every map
    ever drawn does that. It is a floor and not a target. A river that measures
    wider than its floor is drawn at what it measures, and is not exaggerated
    on top of that: a river wider than its floor is never narrowed and never
    exaggerated further.

    Args:
        floor_px: What this class is drawn at when nothing is measured.
        measured_m: The width off the water's own area, or zero for none.
        mppd: Metres per display pixel.

    Returns:
        The painted width in display pixels.
    """
    return round(max(floor_px, measured_m / max(mppd, 1e-9)), 2)


def major_rivers(
    pieces_by: dict[str, list[list[Pt]]], rings: list[list[Pt]], rel_frac: float
) -> tuple[set[str], dict[str, float]]:
    """Which watercourses are the main ones of a box, and how wide each is.

    **The main river of a box is the widest water in it, not the longest.** Run
    inside the box is a fact about the box rather than about the river: it can
    make a buried sewer with 4.8 km of culvert across the sheet the main river,
    and leave the wide river medium on the 2.6 km it clips off a corner.

    Width is measured off the water's own mapped area, which is what OSM maps
    for exactly the rivers that have one. Where the box holds no mapped area at
    all, which is the ordinary case away from a big river, the old rule stands
    and the longest run wins; and a river with no area of its own never outranks
    one that has been measured, because a measurement is evidence and a run
    length is a coincidence of framing.

    Args:
        pieces_by: The clipped centrelines of each watercourse, by name.
        rings: Every mapped water area on the card, in metres.
        rel_frac: The share of the winner a watercourse has to reach to share
            the title.

    Returns:
        The names drawn as major, and the measured width in metres of every
        watercourse that had one.
    """
    widths: dict[str, float] = {}
    for name, lines in pieces_by.items():
        if not name:
            continue
        found = measured_width_m(lines, rings)
        if found:
            widths[name] = found
    if widths:
        widest = max(widths.values())
        return ({n for n, w in widths.items() if w >= rel_frac * widest}, widths)
    lengths = {
        name: sum(length(line) for line in lines) for name, lines in pieces_by.items() if name
    }
    longest = max(lengths.values(), default=0.0)
    return ({n for n, ln in lengths.items() if longest > 0 and ln >= rel_frac * longest}, widths)
