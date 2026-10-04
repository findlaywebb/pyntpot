"""Basemap geometry for the route chart.

OSM features, an SRTM hillshade and candidate landmarks, all built from files
cached under `data/geo/`.

Everything this module emits is in the route chart's own metre space, the one
`normalise.project_route` puts a `RoutePoint` in: x east, y north, origin at the
south-west corner of the track's bounding box. The chart therefore draws a road
and the track through exactly the same transform, and a test can check the
projection without rendering anything.

Nothing here reaches the network except `fetch_activity`, which is attended use
only: the renderer reads the cache and, when there is no cache, says so and
draws the bare track.
"""

from __future__ import annotations

import base64
import json
import logging
import math
import re
import struct
import time
import zlib
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pyntpot.ink.chains import join_chains, join_strokes
from pyntpot.ink.polyline import (
    clip_line,
    eased,
    length,
    normal_at,
    segments_cross,
    simplify,
    smooth,
)

if TYPE_CHECKING:
    from pyntpot.ink.brush_style import BrushStyle
    from pyntpot.maps.basemap import Basemap, ElevationPatch, Line
    from pyntpot.maps.projection import Projection
    from pyntpot.maps.style_groups import BasemapStyle, CardStyle, RibbonStyle

log = logging.getLogger(__name__)

#: Overpass mirrors, tried in order. A public endpoint returns 504 under load
#: often enough that one URL is not a fetch strategy.
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
OVERPASS_URL = OVERPASS_URLS[0]
ELEVATION_URL = "https://api.opentopodata.org/v1/srtm30m"

#: Metres of ground kept around the track's bounding box when fetching.
MARGIN_M = 1500.0
#: Samples per side of the SRTM grid. 80 x 80 over a 5 km box is a 60 m post,
#: which is finer than SRTM's own 30 m only in the sense that the interpolation
#: is smooth: it is the grid a hillshade reads well at, not new information.
ELEV_N = 80

#: Roads that are drawn whatever the track did.
MAJOR_ROADS = ("motorway", "trunk", "primary", "secondary")
#: Roads that are drawn only where the track interacted with them.
MINOR_ROADS = ("tertiary", "unclassified", "residential", "track", "service")

Pt = tuple[float, float]


# --------------------------------------------------------------------------- bounding box


def bounding_box(
    lat: list[float], lng: list[float], margin_m: float = MARGIN_M
) -> tuple[float, float, float, float]:
    """South, west, north, east degrees around a track, grown by `margin_m`."""
    mid = (min(lat) + max(lat)) / 2
    dlat = margin_m / 110540.0
    dlng = margin_m / (111320.0 * math.cos(math.radians(mid)))
    return (min(lat) - dlat, min(lng) - dlng, max(lat) + dlat, max(lng) + dlng)


# --------------------------------------------------------------------------- geometry


def signed_area(ring: list[Pt]) -> float:
    """Twice the signed area of a ring; positive is counter-clockwise."""
    total = 0.0
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        total += x1 * y2 - x2 * y1
    return total


def orient(ring: list[Pt], counter_clockwise: bool = True) -> list[Pt]:
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


def path_d(points: list[Pt], close: bool = False, places: int = 1) -> str:
    """SVG path data for one polyline, rounded to `places` decimals."""
    if len(points) < 2:
        return ""
    d = "M" + " L".join(f"{x:.{places}f},{y:.{places}f}" for x, y in points)
    return d + "Z" if close else d


def stroke_d(points: list[Pt]) -> str:
    """Compact path data for a short stroke: absolute start, relative steps.

    A hachure field is thousands of six-point lines. Written as absolute
    coordinates it is most of a megabyte; written as deltas of a dozen metres
    it is a fifth of that and draws identically.
    """
    if len(points) < 2:
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
    parts = [path_d(orient(r, True), close=True) for r in rings if len(r) > 2]
    parts += [path_d(orient(r, False), close=True) for r in (holes or []) if len(r) > 2]
    return "".join(p for p in parts if p)


# --------------------------------------------------------------------------- proximity


class TrackIndex:
    """A grid index over the track, for asking how near a feature ran to it.

    A road is on the map because the session met it, not because it exists, so
    every minor road and every stream is asked this question once.
    """

    def __init__(self, points: list[Pt], cell_m: float = 120.0) -> None:
        """Index the track.

        Args:
            points: The track in metres.
            cell_m: Bucket size; queries scan the nine buckets around a point.
        """
        self.cell = cell_m
        self.points = points
        self.buckets: dict[tuple[int, int], list[Pt]] = {}
        for p in points:
            self.buckets.setdefault((int(p[0] // cell_m), int(p[1] // cell_m)), []).append(p)

    def distance(self, x: float, y: float, cap_m: float = 400.0) -> float:
        """Metres to the nearest track point, or `cap_m` when nothing is near.

        Args:
            x: Easting in metres.
            y: Northing in metres.
            cap_m: The answer given when no track point is within the scan.

        Returns:
            The distance, never more than `cap_m`.
        """
        rings = max(1, int(cap_m // self.cell) + 1)
        cx, cy = int(x // self.cell), int(y // self.cell)
        best = cap_m
        for i in range(-rings, rings + 1):
            for j in range(-rings, rings + 1):
                for px, py in self.buckets.get((cx + i, cy + j), ()):
                    d = math.hypot(px - x, py - y)
                    if d < best:
                        best = d
        return best

    def interacts(self, line: list[Pt], within_m: float, run_m: float) -> bool:
        """True when the track ran alongside this line, or crossed it.

        Args:
            line: The feature in metres.
            within_m: How close counts as alongside.
            run_m: How much of that contact is needed. A crossing needs none.

        Returns:
            Whether the feature is part of the session's story.
        """
        dense = _densify(line, step_m=20.0)
        near = [self.distance(x, y, cap_m=within_m + 1) <= within_m for x, y in dense]
        if not any(near):
            return False
        run = 0.0
        for i in range(1, len(dense)):
            if near[i] and near[i - 1]:
                run += math.dist(dense[i - 1], dense[i])
                if run >= run_m:
                    return True
            else:
                run = 0.0
        return self._crosses(line)

    def _crosses(self, line: list[Pt]) -> bool:
        """True when a feature segment intersects a track segment."""
        for a, b in zip(line, line[1:], strict=False):
            for c, d in zip(self.points, self.points[1:], strict=False):
                if max(c[0], d[0]) < min(a[0], b[0]) or min(c[0], d[0]) > max(a[0], b[0]):
                    continue
                if max(c[1], d[1]) < min(a[1], b[1]) or min(c[1], d[1]) > max(a[1], b[1]):
                    continue
                if segments_cross(a, b, c, d):
                    return True
        return False


def _densify(line: list[Pt], step_m: float) -> list[Pt]:
    """A polyline resampled so no two points are more than `step_m` apart."""
    out: list[Pt] = []
    for a, b in zip(line, line[1:], strict=False):
        steps = max(1, int(math.dist(a, b) // step_m))
        for k in range(steps):
            t = k / steps
            out.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
    out.append(line[-1])
    return out


#: How far apart the samples are when a watercourse is measured against the
#: water it flows in, in metres.
WIDTH_STEP_M = 25.0
#: The share of a watercourse's own length OSM has to tag as underground before
#: none of it is drawn. Half: a river passing under a bridge or a short culvert
#: is an open river, and a river that is mostly in a pipe is a sewer.
BURIED_FRAC = 0.5

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
        if len(ring) < 3:
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
        if abs(den) < 1e-12:
            continue
        t = ((a[0] - p[0]) * ey - (a[1] - p[1]) * ex) / den
        u = ((a[0] - p[0]) * d[1] - (a[1] - p[1]) * d[0]) / den
        if t > 1e-6 and 0.0 <= u <= 1.0 and (best is None or t < best):
            best = t
    return best


def _ring_at(p: Pt, boxed: list[tuple[list[Pt], tuple[float, ...]]]) -> list[Pt] | None:
    """The mapped water area this point falls inside, or None."""
    for ring, (x0, y0, x1, y1) in boxed:
        if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and point_in_ring(p[0], p[1], ring):
            return ring
    return None


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
        ring = _ring_at(p, boxed) if boxed else None
        if ring is None:
            widths.append(None)
            offsets.append(0.0)
            continue
        left = _ray_to_ring(p, n, ring)
        right = _ray_to_ring(p, (-n[0], -n[1]), ring)
        if left is not None and right is not None:
            widths.append(left + right)
            offsets.append((left - right) / 2)
        elif left is not None or right is not None:
            widths.append(2.0 * (left if left is not None else right))
            offsets.append(0.0)
        else:
            widths.append(None)
            offsets.append(0.0)
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


# --------------------------------------------------------------------------- osm


def _geom(entry: dict[str, Any], proj: Projection) -> list[Pt]:
    """Project one Overpass `geometry` array into metres."""
    return [proj(g["lat"], g["lon"]) for g in entry.get("geometry") or [] if g]


Rings = tuple[list[list[Pt]], list[list[Pt]]]


def _polygon_rings(entry: dict[str, Any], proj: Projection) -> Rings:
    """Outer and inner rings of one way or relation, in metres."""
    if entry.get("type") == "way":
        pts = _geom(entry, proj)
        return ([pts], []) if len(pts) > 3 else ([], [])
    outer, inner = [], []
    for member in entry.get("members") or []:
        pts = _geom(member, proj)
        if len(pts) < 2:
            continue
        (inner if member.get("role") == "inner" else outer).append(pts)
    return (
        [c for c in join_chains(outer, tol=1.0) if len(c) > 3],
        [c for c in join_chains(inner, tol=1.0) if len(c) > 3],
    )


# --------------------------------------------------------------------------- relief


def _png(width: int, height: int, rows: list[bytes], colour_type: int = 4) -> bytes:
    """Encode raster rows as a PNG.

    Args:
        width: Pixels across.
        height: Pixels down.
        rows: One `bytes` per row, already in the sample layout `colour_type` wants.
        colour_type: 0 for greyscale, 4 for greyscale plus alpha.

    Returns:
        The PNG file.
    """
    raw = b"".join(b"\x00" + row for row in rows)

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )


def _resample(grid: list[list[float]], factor: int) -> list[list[float]]:
    """Bilinear upsample of a square grid, so the shading has somewhere to bend."""
    if factor <= 1:
        return grid
    n = len(grid)
    out_n = (n - 1) * factor + 1
    out = [[0.0] * out_n for _ in range(out_n)]
    for r in range(out_n):
        fr = r / factor
        r0 = min(int(fr), n - 2)
        tr = fr - r0
        for c in range(out_n):
            fc = c / factor
            c0 = min(int(fc), n - 2)
            tc = fc - c0
            top = grid[r0][c0] * (1 - tc) + grid[r0][c0 + 1] * tc
            bot = grid[r0 + 1][c0] * (1 - tc) + grid[r0 + 1][c0 + 1] * tc
            out[r][c] = top * (1 - tr) + bot * tr
    return out


def _shade(
    fine: list[list[float]], sx: float, sy: float, azimuth: float, altitude: float, z_factor: float
) -> list[list[float]]:
    """Signed illumination per cell: positive is lit, negative is in shadow.

    numpy is used when it is installed and the plain loop when it is not; the
    two agree to within floating point, so the picture does not depend on which
    ran.
    """
    zen = math.radians(90.0 - altitude)
    az = math.radians(360.0 - azimuth + 90.0)
    flat = math.cos(zen)
    try:
        import numpy as np
    except ImportError:
        np = None
    if np is not None:
        z = np.asarray(fine, dtype=float)
        dzdy, dzdx = np.gradient(z, sy, sx)
        slope = np.arctan(z_factor * np.hypot(dzdx, dzdy))
        aspect = np.arctan2(dzdy, -dzdx)
        illum = np.cos(zen) * np.cos(slope) + np.sin(zen) * np.sin(slope) * np.cos(az - aspect)
        return np.clip((illum - flat) * 2.6, -1.0, 1.0).tolist()
    n = len(fine)
    out = [[0.0] * n for _ in range(n)]
    for r in range(n):
        r0, r1 = max(r - 1, 0), min(r + 1, n - 1)
        for c in range(n):
            c0, c1 = max(c - 1, 0), min(c + 1, n - 1)
            dzdx = (fine[r][c1] - fine[r][c0]) / ((c1 - c0) * sx)
            dzdy = (fine[r1][c] - fine[r0][c]) / ((r1 - r0) * sy)
            slope = math.atan(z_factor * math.hypot(dzdx, dzdy))
            aspect = math.atan2(dzdy, -dzdx)
            illum = math.cos(zen) * math.cos(slope) + math.sin(zen) * math.sin(slope) * math.cos(
                az - aspect
            )
            out[r][c] = max(-1.0, min(1.0, (illum - flat) * 2.6))
    return out


def hillshade_png(
    grid: list[list[float]],
    dx: float,
    dy: float,
    azimuth: float = 315.0,
    altitude: float = 42.0,
    z_factor: float = 1.4,
    upsample: int = 2,
) -> tuple[str, int, int]:
    """Shade a terrain grid and return it as a data URI.

    The image is greyscale plus alpha rather than plain grey: a lit slope paints
    white and a shaded one paints black, both over a transparent flat ground, so
    the same PNG reads as relief on a pale sheet and on a dark one and the page
    needs no blend mode to make it work.

    Args:
        grid: Elevation rows, row 0 southernmost.
        dx: Metres between columns.
        dy: Metres between rows.
        azimuth: Sun bearing in degrees clockwise from north.
        altitude: Sun height in degrees above the horizon.
        z_factor: Vertical exaggeration. Relief at this scale is gentle.
        upsample: Bilinear factor applied before shading.

    Returns:
        The `data:` URI, and the image's width and height in pixels.
    """
    fine = _resample(grid, upsample)
    n = len(fine)
    signal = _shade(fine, dx / upsample, dy / upsample, azimuth, altitude, z_factor)
    # Rows are emitted north first, because SVG y grows downward and the grid's
    # row 0 is its southern edge.
    rows = [
        bytes(
            bytearray(
                b
                for value in row
                for b in (255 if value > 0 else 0, min(255, int(abs(value) * 255)))
            )
        )
        for row in reversed(signal)
    ]
    png = _png(n, n, rows, colour_type=4)
    return "data:image/png;base64," + base64.b64encode(png).decode(), n, n


def marching_squares(grid: list[list[float]], level: float) -> list[list[Pt]]:
    """Contour polylines for one level, in fractional (column, row) grid space.

    Args:
        grid: Rows of samples, row 0 southernmost.
        level: The value to trace.

    Returns:
        Polylines; a ring comes back with its first and last point equal.
    """
    rows, cols = len(grid), len(grid[0])
    segs: list[tuple[Pt, Pt]] = []

    def interp(a: float, b: float) -> float:
        return 0.5 if b == a else (level - a) / (b - a)

    table = {
        1: ((0, 3),),
        2: ((0, 1),),
        3: ((3, 1),),
        4: ((1, 2),),
        5: ((0, 1), (3, 2)),
        6: ((0, 2),),
        7: ((3, 2),),
        8: ((3, 2),),
        9: ((0, 2),),
        10: ((0, 3), (1, 2)),
        11: ((1, 2),),
        12: ((3, 1),),
        13: ((0, 1),),
        14: ((0, 3),),
    }
    for r in range(rows - 1):
        for c in range(cols - 1):
            v = (grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c])
            idx = sum(1 << i for i, val in enumerate(v) if val >= level)
            if idx in (0, 15):
                continue
            edge = (
                (c + interp(v[0], v[1]), float(r)),
                (float(c + 1), r + interp(v[1], v[2])),
                (c + interp(v[3], v[2]), float(r + 1)),
                (float(c), r + interp(v[0], v[3])),
            )
            for a, b in table[idx]:
                segs.append((edge[a], edge[b]))
    return _stitch(segs)


def _stitch(segs: list[tuple[Pt, Pt]]) -> list[list[Pt]]:
    """Join contour segments end to end into polylines."""

    def key(p: Pt) -> tuple[float, float]:
        return (round(p[0], 4), round(p[1], 4))

    starts: dict[tuple[float, float], list[int]] = {}
    for i, (a, _) in enumerate(segs):
        starts.setdefault(key(a), []).append(i)
    ends: dict[tuple[float, float], list[int]] = {}
    for i, (_, b) in enumerate(segs):
        ends.setdefault(key(b), []).append(i)
    used = [False] * len(segs)
    out: list[list[Pt]] = []
    for i, (a, b) in enumerate(segs):
        if used[i]:
            continue
        used[i] = True
        line = [a, b]
        while True:
            nxt = next((j for j in starts.get(key(line[-1]), ()) if not used[j]), None)
            if nxt is None:
                break
            used[nxt] = True
            line.append(segs[nxt][1])
        while True:
            prev = next((j for j in ends.get(key(line[0]), ()) if not used[j]), None)
            if prev is None:
                break
            used[prev] = True
            line.insert(0, segs[prev][0])
        out.append(line)
    return join_chains(out, tol=1e-6)


def _grid_line_to_metres(
    line: list[Pt], lats: list[float], lons: list[float], proj: Projection, pad: int = 0
) -> list[Pt]:
    """Map a polyline in fractional grid space to route metres.

    Args:
        line: Points as (column, row), possibly fractional.
        lats: Grid latitudes, ascending.
        lons: Grid longitudes, ascending.
        proj: The activity's projection.
        pad: Rings of padding added around the grid before contouring.

    Returns:
        The polyline in metres.
    """
    dlat = lats[1] - lats[0]
    dlon = lons[1] - lons[0]
    out = []
    for col, row in line:
        out.append(proj(lats[0] + (row - pad) * dlat, lons[0] + (col - pad) * dlon))
    return out


def _pad(grid: list[list[float]], value: float) -> list[list[float]]:
    """A copy of the grid with one ring of `value` around it, so every level closes."""
    width = len(grid[0]) + 2
    edge = [value] * width
    return [edge] + [[value] + list(row) + [value] for row in grid] + [edge]


def shade_bands(
    grid: list[list[float]],
    lats: list[float],
    lons: list[float],
    proj: Projection,
    dx: float,
    dy: float,
    levels: int = 5,
    azimuth: float = 315.0,
    altitude: float = 42.0,
    z_factor: float = 1.4,
    upsample: int = 2,
    eps: float = 14.0,
) -> list[dict[str, Any]]:
    """Posterised hillshade as filled vector bands.

    The shade is computed exactly as the raster is, then cut into a few levels
    and traced. Nesting does the work a gradient would: every band is drawn at
    the same low opacity, so where four of them overlap the ground is four steps
    darker and the ramp costs no extra alpha bookkeeping.

    Args:
        grid: Elevation rows, row 0 southernmost.
        lats: Grid latitudes, ascending.
        lons: Grid longitudes, ascending.
        proj: The activity's projection.
        dx: Metres between columns.
        dy: Metres between rows.
        levels: Bands across the whole range, split between shadow and light.
        azimuth: Sun bearing in degrees clockwise from north.
        altitude: Sun height in degrees above the horizon.
        z_factor: Vertical exaggeration.
        upsample: Bilinear factor applied before shading.
        eps: Simplification tolerance in metres.

    Returns:
        Bands from the widest to the tightest, each `{"s": -1 or 1, "t": level,
        "d": path}`; `s` says whether the band is shadow or light.
    """
    fine = _resample(grid, upsample)
    signal = _pad(_shade(fine, dx / upsample, dy / upsample, azimuth, altitude, z_factor), 0.0)
    fine_lats = [lats[0] + (lats[-1] - lats[0]) * i / (len(fine) - 1) for i in range(len(fine))]
    fine_lons = [lons[0] + (lons[-1] - lons[0]) * i / (len(fine) - 1) for i in range(len(fine))]
    steps = max(1, levels // 2)
    out: list[dict[str, Any]] = []
    for sign in (-1, 1):
        for i in range(1, steps + 1):
            level = sign * (i / (steps + 0.35))
            flipped = signal if sign > 0 else [[-v for v in row] for row in signal]
            rings = marching_squares(flipped, abs(level))
            parts = []
            for ring in rings:
                metres = _grid_line_to_metres(ring, fine_lats, fine_lons, proj, pad=1)
                metres = simplify(smooth(metres, passes=1, closed=False), eps)
                if len(metres) > 3:
                    parts.append(path_d(metres, close=True))
            if parts:
                out.append({"s": sign, "t": round(abs(level), 3), "d": "".join(parts)})
    return out


def contour_lines(
    grid: list[list[float]],
    lats: list[float],
    lons: list[float],
    proj: Projection,
    interval: float,
    eps: float = 18.0,
) -> list[dict[str, Any]]:
    """Sparse, smoothed contours at one interval.

    Args:
        grid: Elevation rows, row 0 southernmost.
        lats: Grid latitudes, ascending.
        lons: Grid longitudes, ascending.
        proj: The activity's projection.
        interval: Metres between lines. Zero draws none.
        eps: Simplification tolerance in metres.

    Returns:
        One entry per traced line, `{"e": metres, "major": bool, "d": path}`.
    """
    if interval <= 0:
        return []
    flat = [v for row in grid for v in row]
    lo = math.floor(min(flat) / interval) * interval + interval
    hi = math.ceil(max(flat) / interval) * interval
    out = []
    level = lo
    while level < hi:
        for line in marching_squares(grid, level):
            metres = _grid_line_to_metres(line, lats, lons, proj)
            metres = simplify(smooth(metres, passes=2, closed=False), eps)
            if len(metres) > 2:
                out.append(
                    {
                        "e": int(level),
                        "major": int(level) % (interval * 5) == 0,
                        "d": path_d(metres),
                    }
                )
        level += interval
    return out


def sea_rings(
    grid: list[list[float]],
    lats: list[float],
    lons: list[float],
    proj: Projection,
    sea_level: float = 0.0,
    eps: float = 12.0,
) -> Rings:
    """Water and island rings traced from the elevation grid at the shoreline.

    SRTM reports the sea as exactly zero rather than as anything below it, so
    the shoreline is traced on a mask of "at or below sea level" rather than on
    the elevation itself: contouring the elevation at 0 m finds nothing, because
    the sea and the beach are both at 0 m.

    The mask is padded with a ring of dry ground first, so every sea region
    comes back as a closed loop rather than a line running off the sheet. The
    padding sits outside the fetched box, which is already 1.5 km wider than the
    track, so the seam is never on the drawn sheet.

    Args:
        grid: Elevation rows, row 0 southernmost.
        lats: Grid latitudes, ascending.
        lons: Grid longitudes, ascending.
        proj: The activity's projection.
        sea_level: Metres at or below which a cell is water.
        eps: Simplification tolerance in metres.

    Returns:
        Water rings and island rings, both in metres.
    """
    mask = [[1.0 if value <= sea_level else 0.0 for value in row] for row in grid]
    if not any(value for row in mask for value in row):
        return [], []
    padded = _pad(mask, 0.0)
    water: list[list[Pt]] = []
    islands: list[list[Pt]] = []
    for ring in marching_squares(padded, 0.5):
        if len(ring) < 4:
            continue
        wet = _ring_is_wet(ring, padded, 0.5)
        metres = _grid_line_to_metres(ring, lats, lons, proj, pad=1)
        metres = simplify(smooth(metres, passes=2, closed=True), eps)
        if len(metres) > 3:
            (water if wet else islands).append(metres)
    return water, islands


def _ring_is_wet(ring: list[Pt], padded: list[list[float]], level: float) -> bool:
    """True when the cells a ring encloses are on the wet side of `level`."""
    cols = [c for c, _ in ring]
    rows = [r for _, r in ring]
    lo_c, hi_c = int(min(cols)), int(max(cols)) + 1
    lo_r, hi_r = int(min(rows)), int(max(rows)) + 1
    below = above = 0
    for r in range(lo_r, min(hi_r + 1, len(padded))):
        for c in range(lo_c, min(hi_c + 1, len(padded[0]))):
            if not point_in_ring(c + 0.5, r + 0.5, ring):
                continue
            if padded[r][c] >= level:
                below += 1
            else:
                above += 1
    return below >= above


# --------------------------------------------------------------------------- fetch

OVERPASS_QUERY = """[out:json][timeout:240];
(
  way["highway"~"^({roads})$"]({box});
  way["landuse"="forest"]({box});
  way["natural"="wood"]({box});
  relation["landuse"="forest"]({box});
  relation["natural"="wood"]({box});
  way["boundary"~"^(national_park|protected_area)$"]({box});
  relation["boundary"~"^(national_park|protected_area)$"]({box});
  way["waterway"~"^(river|stream)$"]({box});
  way["natural"~"^(water|coastline|bay)$"]({box});
  relation["natural"="water"]({box});
  node["tourism"~"^({tourism})$"]({box});
  way["tourism"~"^({tourism})$"]["name"]({box});
  relation["tourism"~"^({tourism})$"]["name"]({box});
  node["historic"]({box});
  way["historic"]({box});
  node["man_made"~"^({manmade})$"]({box});
  way["man_made"~"^({manmade})$"]["name"]({box});
  way["building"~"^({buildings})$"]["name"]({box});
  node["amenity"~"^({amenities})$"]["name"]({box});
  way["amenity"~"^({amenities})$"]["name"]({box});
  way["leisure"~"^({leisure})$"]["name"]({box});
  relation["leisure"~"^({leisure})$"]["name"]({box});
  relation["amenity"~"^({amenities})$"]["name"]({box});
  relation["building"~"^({buildings})$"]["name"]({box});
  way["bridge"]["name"]({box});
  node["natural"~"^(peak|arch|cave_entrance)$"]({box});
  node["place"~"^(city|town|village|hamlet|suburb)$"]({box});
);
out geom;"""


GPX_POINT = re.compile(r'lat="([-\d.]+)"\s+lon="([-\d.]+)"')


def read_gpx(path: Path) -> tuple[list[float], list[float]]:
    """Latitudes and longitudes from a GPX track.

    The GPX is the source for where a session went; this is the same read the
    snapshot does.

    Args:
        path: The cached `route.gpx`.

    Returns:
        Latitudes and longitudes in recorded order.
    """
    rows = GPX_POINT.findall(path.read_text())
    return ([float(a) for a, _ in rows], [float(b) for _, b in rows])


def overpass_path(key: str, cache_dir: Path) -> Path:
    """Where the OSM payload for one activity is cached."""
    return cache_dir / f"overpass-{key}.json"


def elevation_path(key: str, cache_dir: Path) -> Path:
    """Where the SRTM grid for one activity is cached."""
    return cache_dir / f"elevation-{key}.json"


def _get(
    url: str,
    params: dict[str, str] | None = None,
    data: dict[str, str] | None = None,
    timeout: float = 240.0,
) -> str:
    """One HTTP call, imported late so the renderer never needs the client."""
    import httpx

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        if data is not None:
            response = client.post(url, data=data)
        else:
            response = client.get(url, params=params)
        response.raise_for_status()
        return response.text


def fetch_overpass(box: tuple[float, float, float, float], path: Path) -> int:
    """Fetch OSM features for one bounding box into the cache.

    Args:
        box: (south, west, north, east) in degrees.
        path: Cache file to write.

    Returns:
        Bytes written.
    """
    query = OVERPASS_QUERY.format(
        box=",".join(f"{value:f}" for value in box),
        roads="|".join(MAJOR_ROADS + MINOR_ROADS),
        tourism="|".join(TOURISM_LANDMARKS),
        manmade="|".join(MANMADE_LANDMARKS),
        buildings="|".join(BUILDING_LANDMARKS),
        amenities="|".join(AMENITY_LANDMARKS),
        leisure="|".join(LEISURE_LANDMARKS),
    )
    text = ""
    for attempt in range(3):
        for url in OVERPASS_URLS:
            try:
                text = _get(url, data={"data": query})
                json.loads(text)
            except Exception as exc:  # a mirror under load is not a failed fetch
                log.info("overpass %s attempt %d: %s", url, attempt + 1, exc)
                text = ""
                time.sleep(4.0)
                continue
            break
        if text:
            break
    if not text:
        raise RuntimeError("every Overpass mirror refused the query")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.stat().st_size


def fetch_elevation(
    box: tuple[float, float, float, float],
    path: Path,
    n: int = ELEV_N,
    chunk: int = 100,
    pause: float = 1.1,
) -> int:
    """Fetch an n by n SRTM grid for one bounding box into the cache.

    Args:
        box: (south, west, north, east) in degrees.
        path: Cache file to write.
        n: Samples per side.
        chunk: Points per request; the public endpoint takes 100.
        pause: Seconds between requests, to stay inside the endpoint's rate.

    Returns:
        Bytes written.
    """
    south, west, north, east = box
    lats = [south + (north - south) * i / (n - 1) for i in range(n)]
    lons = [west + (east - west) * j / (n - 1) for j in range(n)]
    points = [(la, lo) for la in lats for lo in lons]
    values: list[float] = []
    for start in range(0, len(points), chunk):
        batch = points[start : start + chunk]
        locations = "|".join(f"{a:.6f},{b:.6f}" for a, b in batch)
        payload = json.loads(_get(ELEVATION_URL, params={"locations": locations}))
        if payload.get("status") != "OK":
            raise RuntimeError(f"elevation endpoint said {payload.get('status')!r}")
        values.extend(
            0.0 if r["elevation"] is None else float(r["elevation"]) for r in payload["results"]
        )
        log.info("elevation %d/%d", len(values), len(points))
        time.sleep(pause)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"n": n, "bbox": list(box), "lats": lats, "lons": lons, "elev": values})
    )
    return path.stat().st_size


def fetch_activity(
    key: str,
    lat: list[float],
    lng: list[float],
    cache_dir: Path,
    force: bool = False,
    margin_m: float = MARGIN_M,
    n: int = ELEV_N,
    land_cover: bool = True,
) -> dict[str, Any]:
    """Fill the cache for one activity. Attended use only.

    Three payloads: the OSM features and the SRTM grid the vector map draws,
    and the land cover classes the painted map needs. The land cover is fetched
    over a wider box, because the painted card is grown by a ribbon radius
    before it is drawn.

    Args:
        key: The activity, naming the cache files.
        lat: Track latitudes.
        lng: Track longitudes.
        cache_dir: Where the payloads live.
        force: Refetch even when a cache file is already there.
        margin_m: Ground kept around the track's bounding box.
        n: Samples per side of the elevation grid.
        land_cover: Fetch the land cover classes too.

    Returns:
        What was written, by name, with byte counts.
    """
    box = bounding_box(lat, lng, margin_m)
    out: dict[str, Any] = {"box": [round(v, 6) for v in box]}
    osm = overpass_path(key, cache_dir)
    if force or not osm.exists():
        out["overpass"] = fetch_overpass(box, osm)
    else:
        out["overpass"] = f"cached, {osm.stat().st_size} bytes"
    elev = elevation_path(key, cache_dir)
    if force or not elev.exists():
        out["elevation"] = fetch_elevation(box, elev, n=n)
    else:
        out["elevation"] = f"cached, {elev.stat().st_size} bytes"
    if land_cover:
        cover = landcover_path(key, cache_dir)
        if force or not cover.exists():
            wide = bounding_box(lat, lng, LANDCOVER_MARGIN_M)
            out["landcover_box"] = [round(v, 6) for v in wide]
            out["landcover"] = fetch_landcover(wide, cover)
        else:
            out["landcover"] = f"cached, {cover.stat().st_size} bytes"
    return out


# --------------------------------------------------------------------------- landmarks

#: `historic` values that are a monument someone put there on purpose. The rest
#: of the tag's range is a site rather than a marker: a colliery, a station and
#: an earthwork are all history, but none of them is a thing to run past and see.
MONUMENT_HISTORIC = (
    "monument",
    "memorial",
    "castle",
    "wayside_cross",
    "cross",
    "tower",
    "cannon",
    "milestone",
    "boundary_stone",
)

#: `memorial` values that mark a wall, not a thing in the landscape. OSM tags a
#: blue plaque `historic=memorial` with the name of the building it is screwed
#: to, so a theatre, a hotel and a war name all arrive as monuments near the
#: route and one of them can end up naming a climb. A
#: plaque is a real record and a bad landmark; it is classed apart, not dropped.
PLAQUE_MEMORIAL = ("plaque", "blue_plaque")

#: The `tourism` values worth a place on a map, and the `man_made`, `building`,
#: `amenity` and `leisure` ones. These are what the box actually asks OSM for,
#: so widening the map's vocabulary is one edit here and not two.
#:
#: A query for monuments, artworks and history alone asks for nothing a person
#: would actually navigate by. It leaves the sheet naming a drinking fountain
#: and a statue while the zoo, the terraces along a ring road and every bridge
#: over the canal are never offered at all: the picks read as what
#: OpenStreetMap calls a monument rather than as what someone moving through
#: the place would pick out.
TOURISM_LANDMARKS = (
    "attraction",
    "viewpoint",
    "artwork",
    "museum",
    "zoo",
    "aquarium",
    "gallery",
    "theme_park",
)
MANMADE_LANDMARKS = (
    "lighthouse",
    "obelisk",
    "tower",
    "monument",
    "bridge",
    "water_tower",
    "chimney",
    "windmill",
    "pier",
    "mast",
)
BUILDING_LANDMARKS = (
    "cathedral",
    "church",
    "chapel",
    "mosque",
    "synagogue",
    "temple",
    "castle",
    "palace",
    "stadium",
    "train_station",
    "university",
    "hospital",
    "museum",
    "tower",
)
AMENITY_LANDMARKS = (
    "place_of_worship",
    "theatre",
    "arts_centre",
    "university",
    "townhall",
    "courthouse",
    "casino",
)
LEISURE_LANDMARKS = ("stadium", "sports_centre", "marina")

#: What a landmark tag means, and whether the heuristic keeps it. A village is
#: classed and offered but never kept: a place name is not a landmark, it is a
#: label, and a map crowded with them reads worse.
LANDMARK_CLASSES: dict[str, bool] = {
    "sculpture": True,
    "monument": True,
    "viewpoint": True,
    "summit": True,
    "building": True,
    "bridge": True,
    "tower": True,
    "worship": True,
    "attraction": True,
    "block": True,
    "sight": False,
    "ruin": False,
    "place": False,
    "plaque": False,
    "other": False,
}

#: How far off the route a class of thing is still worth naming, in metres, and
#: how notable it is against the other classes. A mountain or an unusually tall
#: building is notable from further off, and the corollary is that a fountain
#: eight metres away is not notable at all. One radius for everything made the
#: first half impossible and the second half inevitable.
#:
#: The tier is what a runner would pick out first, not what OSM thinks is
#: important: a hill, a tower, a spire, a named building and a bridge are the
#: things you navigate by, a monument or a statue is something you pass, and a
#: ruin or a plaque is something you would have to stop and read.
LANDMARK_REACH_M: dict[str, tuple[int, float]] = {
    "summit": (1, 6000.0),
    "tower": (1, 1200.0),
    "worship": (1, 700.0),
    "building": (1, 450.0),
    "viewpoint": (1, 450.0),
    "attraction": (1, 450.0),
    "bridge": (1, 250.0),
    "block": (2, 250.0),
    "monument": (2, 250.0),
    "sculpture": (2, 150.0),
    "sight": (2, 150.0),
    "ruin": (3, 200.0),
    "place": (3, 300.0),
    "plaque": (3, 30.0),
    "other": (3, 150.0),
}

#: The classes a named area is offered as a candidate for at all. A place name,
#: a plaque and anything unrecognised are drawn or dropped by other rules and
#: were never landmarks; everything else is offered and ranked.
OFFERED_CLASSES = frozenset(LANDMARK_REACH_M) - {"place", "plaque", "other"}

#: A building tag OSM puts on the fabric rather than on the institution: every
#: block of a campus and every wing of a hospital carries one, so "Ilam Hall"
#: and "Hartington Hall" arrive looking exactly like the cathedral next to them.
#: They are still worth offering, because one of them is sometimes the thing on
#: the corner; they are not worth ranking above a spire, a tower or a zoo.
FABRIC_BUILDINGS = ("university", "hospital", "museum")
#: What a landmark building is: something that has a name because of what it is.
NAMED_BUILDINGS = ("castle", "palace", "stadium", "train_station")
#: The `tourism` values that are a destination, and the ones that are a sign on
#: a railing. OSM tags every enclosure in a zoo `tourism=attraction`, which is
#: how an enclosure sign can outrank the zoo itself.
TOURISM_DESTINATIONS = ("zoo", "museum", "aquarium", "theme_park")

#: The reach a class with no entry gets, and the radius every reach above is
#: stated against. A card drawn at a coarser scale scales them all together.
LANDMARK_RADIUS_M = 300.0

#: How far something is notable from, per metre of its own height. A thing that
#: stands above what is around it is seen from further away than its footprint
#: says, which is the whole point of a cathedral or a radio mast. Sixty metres
#: of reach a metre of height puts a thirty-metre spire at 1.8 km and a 108 m
#: dome at about 6.5 km, and the card's own box
#: cuts anything the reader could not see on the sheet anyway.
VISIBLE_PER_M = 60.0
#: Past this, height stops buying reach. Nothing on a session's card is further
#: off than this and still the thing a person would name.
REACH_CAP_M = 8000.0

#: The tags a candidate carries forward, so the label agent can see what a thing
#: is and `landmark_reach` can see how tall it stands.
LANDMARK_TAG_KEYS = (
    "tourism",
    "historic",
    "natural",
    "place",
    "man_made",
    "building",
    "amenity",
    "leisure",
    "bridge",
    "height",
    "building:levels",
    "artwork_type",
    "artist_name",
    "ele",
    "start_date",
    "memorial",
)

#: How many named things the box offers the label agent. Forty was a distance
#: sort that stopped inside one town's plaques, so the settlements a climb had
#: to be named from were cut before the agent ever saw them.
LANDMARK_CAP = 80


def classify(tags: dict[str, str]) -> str:
    """The landmark class one OSM tag set belongs to."""
    historic = tags.get("historic", "")
    if historic == "memorial" and tags.get("memorial") in PLAQUE_MEMORIAL:
        return "plaque"
    if tags.get("tourism") == "artwork" or tags.get("artwork_type"):
        return "sculpture"
    if tags.get("natural") == "peak":
        return "summit"
    if tags.get("tourism") == "viewpoint":
        return "viewpoint"
    if (
        tags.get("man_made") in ("tower", "water_tower", "chimney", "mast")
        or tags.get("building") == "tower"
    ):
        return "tower"
    if historic in MONUMENT_HISTORIC or tags.get("man_made") in (
        "obelisk",
        "monument",
        "lighthouse",
    ):
        return "monument"
    if tags.get("amenity") == "place_of_worship" or tags.get("building") in (
        "cathedral",
        "church",
        "chapel",
        "mosque",
        "synagogue",
        "temple",
    ):
        return "worship"
    if tags.get("man_made") == "bridge" or tags.get("bridge"):
        return "bridge"
    if tags.get("tourism") in TOURISM_DESTINATIONS:
        return "attraction"
    if (
        tags.get("building") in NAMED_BUILDINGS
        or tags.get("amenity") in AMENITY_LANDMARKS
        or tags.get("leisure") in LEISURE_LANDMARKS
        or tags.get("man_made") in MANMADE_LANDMARKS
    ):
        return "building"
    if tags.get("tourism") in TOURISM_LANDMARKS:
        return "sight"
    if tags.get("building") in FABRIC_BUILDINGS:
        return "block"
    if historic:
        return "ruin"
    if tags.get("place"):
        return "place"
    return "other"


def height_m(tags: dict[str, str]) -> float:
    """How tall OSM says this thing is, in metres, or zero when it does not say.

    `height` is metres unless it names another unit, and `building:levels` is
    the only other statement of height that is common enough to be worth
    reading. Anything unparseable is no statement rather than a guess.
    """
    raw = str(tags.get("height", "")).strip().lower()
    if raw:
        number = re.match(r"([\d.]+)", raw)
        if number:
            try:
                value = float(number.group(1))
            except ValueError:
                value = 0.0
            if "'" in raw or "ft" in raw:
                value *= 0.3048
            if value > 0:
                return value
    levels = str(tags.get("building:levels", "")).strip()
    try:
        return float(levels) * 3.2 if levels else 0.0
    except ValueError:
        return 0.0


def landmark_reach(entry: dict[str, Any], scale: float = 1.0) -> float:
    """How far off the route this one thing is still worth naming, in metres.

    Its class says what it is; its own height says whether it stands above what
    is around it. The taller of the two answers wins, because a church tagged
    only as a church takes the class reach and one that states a 60 m spire
    takes the spire's.
    """
    cls = entry.get("cls") or entry.get("class") or "other"
    _tier, base = LANDMARK_REACH_M.get(cls, LANDMARK_REACH_M["other"])
    tall = height_m(entry.get("tags") or {}) * VISIBLE_PER_M
    return min(max(base, tall), REACH_CAP_M) * scale


def landmark_rank(entry: dict[str, Any], scale: float = 1.0) -> tuple[int, float]:
    """What order the candidates are offered in: notability, then comfort.

    Nearest-first was the old order and it is the wrong one in a city: eighty
    nearest things in one district are eighty blue plaques, and the label agent
    never saw the zoo it was standing next to. The first term is the tier, so
    the things a runner navigates by come before the things they pass; the
    second is how comfortably the thing sits inside its own reach, so within a
    tier the nearer and the taller both rise.
    """
    cls = entry.get("cls") or entry.get("class") or "other"
    tier, _base = LANDMARK_REACH_M.get(cls, LANDMARK_REACH_M["other"])
    d = entry.get("d")
    d = entry.get("distance_m") if d is None else d
    return (tier, (d if d is not None else 9e9) / max(landmark_reach(entry, scale), 1.0))


def pick_landmarks(
    candidates: list[dict[str, Any]],
    mode: str = "heuristic",
    radius_m: float = 300.0,
    cap: int = 8,
    picks: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    """Choose which candidates the map labels.

    The default is a heuristic, not a decision: everything whose class earns a
    place on a map and that sits inside its own reach of the track, most
    notable first, at most `cap` of them. A payload that names landmarks
    replaces it outright, which is how the coach agent overrides a rule it can
    see.

    **The reach is the thing's own, not one radius for the lot.** A statue is
    worth naming from a hundred metres and a hill from six kilometres, and the
    old flat radius could only be set for one of them; `landmark_reach` reads it
    off the class and off whatever height OSM states. `radius_m` is now the
    scale those reaches are stated at rather than the limit itself, so a card
    drawn over four times the ground still stretches them all together.

    Args:
        candidates: Everything the box offered, each with `n`, `cls` and `d`.
        mode: `heuristic`, `all`, or `payload`.
        radius_m: The scale the class reaches are read at, against
            `LANDMARK_RADIUS_M`.
        cap: How many the heuristic keeps.
        picks: Names the payload chose.

    Returns:
        The chosen candidates, most notable first.
    """
    scale = radius_m / LANDMARK_RADIUS_M
    named = {c["n"] for c in candidates if c["n"]}
    if picks:
        wanted = {p for p in picks}
        chosen = [c for c in candidates if c["n"] in wanted]
        missing = sorted(wanted - named)
        for entry in chosen:
            entry["picked"] = True
        if mode == "payload" or picks:
            return sorted(chosen, key=lambda c: landmark_rank(c, scale)) + [
                {"n": name, "cls": "missing", "d": 0.0, "x": None, "y": None, "missing": True}
                for name in missing
            ]
    if mode == "all":
        return sorted((c for c in candidates if c["n"]), key=lambda c: landmark_rank(c, scale))
    keep = [
        c
        for c in candidates
        if c["n"] and LANDMARK_CLASSES.get(c["cls"], False) and c["d"] <= landmark_reach(c, scale)
    ]
    keep.sort(key=lambda c: landmark_rank(c, scale))
    return keep[:cap]


# --------------------------------------------------------------------------- assembly

#: The box a run makes. Every generalisation threshold below is stated for this
#: span and scaled up from it, so a ride over four times the ground is drawn at
#: four times the tolerance rather than at a run's detail shrunk to fit.
REFERENCE_SPAN_M = 4000.0
MAX_SCALE = 4.0


def scale_for(span_m: float) -> float:
    """How much coarser than a run's map a box this big should be drawn."""
    return min(max(span_m / REFERENCE_SPAN_M, 1.0), MAX_SCALE)


def _derived(options: BasemapStyle, factor: float) -> dict[str, Any]:
    """The generalisation thresholds actually used, for the notes column."""
    return {
        "scale": round(factor, 2),
        "road_eps_m": round(10.0 * factor, 1),
        "wood_eps_m": round(22.0 * factor, 1),
        "river_eps_m": round(12.0 * factor, 1),
        "interaction_m": round(min(options.interaction_m * factor, 200.0), 1),
        "interaction_run_m": round(options.interaction_run_m * factor, 1),
        "landmark_radius_m": round(options.landmark_radius_m * factor, 1),
        "cell_m": round(options.cell_m * factor, 1),
        "blob_jitter_m": round(options.blob_jitter_m * factor, 1),
        "tree_spacing_m": round(options.tree_spacing_m * factor, 1),
        "river_width": round(min(14.0, 8.0 * factor**0.6), 1),
        "min_area_ha": round(options.min_area_ha * factor**2, 1),
        "hachure_spacing_m": round(options.hachure_spacing_m * factor, 1),
        "hachure_length_m": round(options.hachure_max_length_m * factor, 1),
        "landmark_cap": max(options.landmark_max, round(options.landmark_max * factor**0.5)),
    }


def basemap(
    key: str,
    lat: list[float],
    lng: list[float],
    options: BasemapStyle | None = None,
    route: list[Pt] | None = None,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
    clip_margin_m: float = 900.0,
) -> dict[str, Any] | None:
    """Assemble every basemap layer for one activity from the cache.

    Args:
        key: The activity, naming the two cache files.
        lat: Track latitudes in recorded order.
        lng: Track longitudes, same length.
        options: What to draw. The defaults are the basemap group's own.
        route: The already-projected track, when the caller has one. The
            snapshot's route is simplified before its origin is taken, so a road
            projected from scratch could sit a metre or two off the track it
            runs beside; passing the route pins the two to the same origin.
        cache_dir: Where the cached payloads live.
        places: User-supplied places of interest.
        clip_margin_m: Metres of ground kept around the track's bounding box
            when drawing, before the box's scale is applied.

    Returns:
        Layers in route metre space, or None when nothing is cached for this
        box, which is the renderer's signal to draw the bare track and say so.
    """
    from pyntpot.maps.projection import track_projection
    from pyntpot.maps.style_groups import BasemapStyle

    options = options or BasemapStyle()
    osm_file = overpass_path(key, cache_dir)
    elev_file = elevation_path(key, cache_dir)
    if not osm_file.exists() and not elev_file.exists():
        return None
    proj, pts = track_projection(lat, lng, route)
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    factor = scale_for(span)
    derived = _derived(options, factor)
    margin = clip_margin_m * factor
    clip = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    out: dict[str, Any] = {
        "id": key,
        "clip": [round(v, 1) for v in clip],
        "bounds": [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)],
        "span_m": round(span),
        "derived": derived,
        "sources": [],
    }
    # Simplified so the index is small, then densified so it is honest: the
    # index measures distance to a vertex, and a straight kilometre simplifies
    # to two of them, which would put a road running beside it half a field away.
    index = TrackIndex(_densify(simplify(pts, 6.0), 15.0))
    if osm_file.exists():
        out.update(_osm_layers(osm_file, proj, clip, index, options, derived))
        out["sources"].append(f"OSM via Overpass, {osm_file.stat().st_size // 1024} KB cached")
    if elev_file.exists():
        out.update(_relief_layers(elev_file, proj, clip, options, derived, index))
        out["sources"].append("SRTM 30 m via OpenTopoData")
    out["places"] = _place_marks(places, proj, clip)
    out["landmarks"] = pick_landmarks(
        out.get("landmark_candidates", []),
        mode=options.landmarks,
        radius_m=derived["landmark_radius_m"],
        cap=derived["landmark_cap"],
        picks=options.pick_landmarks,
    )
    return out


def _place_marks(
    places: list[dict[str, Any]], proj: Projection, clip: tuple[float, float, float, float]
) -> list[dict[str, Any]]:
    """Project the supplied places, keeping the ones inside the sheet."""
    xmin, ymin, xmax, ymax = clip
    out = []
    for place in places:
        if "lat" not in place or "lng" not in place:
            continue
        x, y = proj(float(place["lat"]), float(place["lng"]))
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            continue
        # `kind` and `always_label` are optional and default to what the file
        # has always meant: a glyph named by `symbol`, with the name under it,
        # chosen by the score like anything else. A `settlement` entry draws no
        # glyph, and an `always_label` one is lettered whenever the box holds it.
        kind = str(place.get("kind", "marker"))
        symbol = place.get("symbol", "" if kind == "settlement" else "pin")
        out.append(
            {
                "n": place.get("name", ""),
                "sym": symbol,
                "kind": kind,
                "always": bool(place.get("always_label", False)),
                "x": round(x, 1),
                "y": round(y, 1),
                "note": place.get("note", ""),
            }
        )
    return out


def _relief_layers(
    path: Path,
    proj: Projection,
    clip: tuple[float, float, float, float],
    options: BasemapStyle,
    derived: dict[str, Any],
    index: TrackIndex | None = None,
) -> dict[str, Any]:
    """Every relief and water layer the SRTM grid can carry."""
    data = json.loads(path.read_text())
    n = data["n"]
    values = data["elev"]
    grid = [[float(v) for v in values[r * n : (r + 1) * n]] for r in range(n)]
    lats, lons = data["lats"], data["lons"]
    dx = (lons[1] - lons[0]) * proj.kx
    dy = (lats[1] - lats[0]) * proj.ky
    x0, y0 = proj(lats[0], lons[0])
    x1, y1 = proj(lats[-1], lons[-1])
    water, islands = sea_rings(grid, lats, lons, proj)
    flat = [v for row in grid for v in row]
    mode = options.hillshade_mode
    every = options.all_variants
    out: dict[str, Any] = {
        "hillshade_bands": [],
        "hillshade_raster": None,
        "hachures": [],
        "contours": [],
        "sea_waves": "",
        "sea": _sea_path(water, islands, clip, options, derived),
        "elevation": {"min": round(min(flat)), "max": round(max(flat)), "grid": n},
    }
    if every or mode == "bands":
        levels = 2 if options.generalise else max(3, min(8, options.hillshade_levels))
        out["hillshade_bands"] = shade_bands(
            grid,
            lats,
            lons,
            proj,
            dx,
            dy,
            levels=levels,
            eps=derived["cell_m"] * 0.8 if options.generalise else derived["wood_eps_m"] * 0.6,
        )
    if every or mode == "raster":
        href, width, height = hillshade_png(grid, dx, dy)
        out["hillshade_raster"] = {
            "href": href,
            "x": round(x0, 1),
            "y": round(y0, 1),
            "w": round(x1 - x0, 1),
            "h": round(y1 - y0, 1),
            "px": width,
            "py": height,
        }
    if every or mode == "contours":
        out["contours"] = contour_lines(
            grid, lats, lons, proj, options.contour_interval, eps=derived["river_eps_m"] * 1.4
        )
    field = Field(grid, lats, lons, proj)
    if every or mode == "hachures":
        out["hachures"] = hachures(
            field,
            clip,
            index,
            spacing_m=derived["hachure_spacing_m"],
            min_slope=options.hachure_min_slope,
            max_length_m=derived["hachure_length_m"],
        )
    if out["sea"]["d"] and (every or options.sea_style == "waves"):
        out["sea_waves"] = wave_strokes(
            field,
            clip,
            spacing_m=derived["hachure_spacing_m"] * 2.4,
            length_m=derived["hachure_length_m"] * 0.8,
        )
    return out


def _soften(line: list[Pt], eps: float, options: BasemapStyle) -> list[Pt]:
    """Simplify a line, then round its corners off.

    A road drawn from OSM nodes is a survey; two Chaikin passes make it a line
    someone drew, which is what the rest of the sheet now looks like.
    """
    out = simplify(line, eps)
    if options.generalise and options.smooth_passes:
        # Chaikin quadruples the points, so the curve is simplified again at a
        # tolerance it cannot see: the line stays round and the layer stays small.
        out = simplify(smooth(out, passes=min(2, options.smooth_passes), closed=False), eps * 0.3)
    return out


def _sea_path(
    water: list[list[Pt]],
    islands: list[list[Pt]],
    clip: tuple[float, float, float, float],
    options: BasemapStyle,
    derived: dict[str, Any],
) -> dict[str, str]:
    """The sea as one wash, with a lighter dry-brush edge pulled in from it."""
    cut = [clip_ring(r, clip) for r in water]
    holes = [clip_ring(r, clip) for r in islands]
    if not options.generalise:
        return {"d": rings_path(cut, holes), "inner": ""}
    layer = generalise_layer(
        [r for r in cut if len(r) > 2],
        [r for r in holes if len(r) > 2],
        clip,
        derived["cell_m"],
        options.morph_cells,
        derived["min_area_ha"],
        options.smooth_passes,
        jitter_m=derived["blob_jitter_m"] * 0.6,
        inset_cells=options.inset_cells,
        seed=4,
    )
    return {
        "d": "".join(path_d(r, close=True) for r in layer["outer"]),
        "inner": "".join(path_d(r, close=True) for r in layer["inner"]),
    }


def _osm_layers(
    path: Path,
    proj: Projection,
    clip: tuple[float, float, float, float],
    index: TrackIndex,
    options: BasemapStyle,
    derived: dict[str, Any],
) -> dict[str, Any]:
    """Group the cached Overpass payload into the map's layers.

    Every filled layer comes back as one path wound for `fill-rule="nonzero"`,
    so two woods that overlap fill once rather than stacking their alpha into a
    patch that reads as a third thing.

    Args:
        path: The cached Overpass payload.
        proj: The activity's projection.
        clip: (xmin, ymin, xmax, ymax) in metres; everything is cut to it.
        index: The track, for the interaction tests.
        options: What to draw.
        derived: The scale-aware thresholds from `_derived`.

    Returns:
        The vector layers, in metres.
    """
    payload = json.loads(path.read_text())
    within = derived["interaction_m"]
    run_m = derived["interaction_run_m"]
    road_eps = derived["road_eps_m"]
    wood_eps = derived["wood_eps_m"]
    river_eps = derived["river_eps_m"]
    xmin, ymin, xmax, ymax = clip

    wood: list[list[Pt]] = []
    wood_holes: list[list[Pt]] = []
    park: list[list[Pt]] = []
    lakes: list[list[Pt]] = []
    sea_polys: list[list[Pt]] = []
    roads: list[dict[str, Any]] = []
    # Every way of one road, and whether any of it earned the road a place.
    ways: dict[tuple[str, str], list[dict[str, Any]]] = {}
    road_keep: dict[tuple[str, str], bool] = {}
    rivers: list[dict[str, Any]] = []
    # Metres of each watercourse OSM tags as underground, against its whole run.
    under: dict[str, float] = {}
    overall: dict[str, float] = {}
    coast: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    counts: dict[str, int] = {"road_dropped": 0, "stream_dropped": 0, "wood_relations": 0}

    def area_rings(entry: dict[str, Any], eps: float) -> Rings:
        outer, inner = _polygon_rings(entry, proj)
        cut = [clip_ring(r, clip) for r in outer]
        holes = [clip_ring(r, clip) for r in inner]
        return (
            [simplify(r, eps) for r in cut if len(r) > 3],
            [simplify(r, eps) for r in holes if len(r) > 3],
        )

    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        name = tags.get("name", "")
        if entry.get("type") == "node":
            x, y = proj(entry["lat"], entry["lon"])
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                continue
            candidates.append(
                {
                    "n": name,
                    "cls": classify(tags),
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "d": round(index.distance(x, y, cap_m=3000.0)),
                    "tags": {k: v for k, v in tags.items() if k in LANDMARK_TAG_KEYS},
                }
            )
            continue
        highway = tags.get("highway")
        waterway = tags.get("waterway")
        if highway:
            major = highway in MAJOR_ROADS
            ref = str(tags.get("ref") or "")
            # Kept or dropped per *road*, not per way. OSM cuts a street at
            # every junction, and the interaction test was answered separately
            # for each cut: the block that crosses the route was kept and the
            # next block along was not, so every side street came off the route
            # as a stub and the sheet read as a comb. A road the session ran
            # along or across is on the card for as long as the card holds it.
            # A way with neither a number nor a name has no road to belong to,
            # so it is still decided on its own.
            road = (ref or name or f"~{entry.get('id')}", highway)
            for piece in clip_line(_geom(entry, proj), clip):
                line = _soften(piece, road_eps, options)
                if len(line) < 2:
                    continue
                ways.setdefault(road, []).append(
                    {
                        "c": "major" if major else "minor",
                        "n": name,
                        # The road number, which is what a map calls a road:
                        # "A66" says where the route went and "Lake Road"
                        # says nothing at 26 m a pixel.
                        "r": ref,
                        "k": highway,
                        "d": path_d(line),
                    }
                )
                if road not in road_keep:
                    road_keep[road] = options.roads == "all" or major or name in options.pick_roads
                if not road_keep[road] and options.roads == "key":
                    road_keep[road] = index.interacts(piece, within, run_m)
        elif waterway in ("river", "stream"):
            buried = bool(tags.get("tunnel"))
            for piece in clip_line(_geom(entry, proj), clip):
                river = waterway == "river"
                keep = (
                    options.rivers == "all"
                    or river
                    or (options.rivers == "key" and index.interacts(piece, within, run_m))
                )
                if not keep:
                    counts["stream_dropped"] += 1
                    continue
                line = _soften(piece, river_eps, options)
                if len(line) < 2:
                    continue
                # How much of this watercourse OSM says is underground, gathered
                # by name so the question is asked of the river and not of each
                # way. A river passing under one bridge is not a buried river.
                run = length(line)
                key = name or f"~{entry.get('id')}"
                under[key] = under.get(key, 0.0) + (run if buried else 0.0)
                overall[key] = overall.get(key, 0.0) + run
                rivers.append(
                    {"c": "river" if river else "stream", "n": name, "k": key, "d": path_d(line)}
                )
        elif tags.get("natural") == "coastline":
            for piece in clip_line(_geom(entry, proj), clip):
                line = _soften(piece, river_eps * 0.6, options)
                if len(line) > 1:
                    coast.append({"n": name, "d": path_d(line)})
        elif tags.get("landuse") == "forest" or tags.get("natural") == "wood":
            outer, inner = area_rings(entry, wood_eps)
            if entry.get("type") == "relation" and outer:
                counts["wood_relations"] += 1
            wood += outer
            wood_holes += inner
        elif tags.get("boundary") in ("national_park", "protected_area"):
            outer, _ = area_rings(entry, wood_eps * 1.6)
            park += outer
        elif tags.get("natural") in ("water", "bay"):
            outer, _ = area_rings(entry, river_eps)
            target = sea_polys if tags.get("natural") == "bay" else lakes
            target += outer
        # A named area whose tags make it a landmark, at its own centre. History
        # was the only kind of way that could become one, so every named
        # building, bridge and church in the box was drawn and never offered;
        # and a relation could not become one at all, so a card could name a
        # statue and not the zoo the statue stands in. OSM holds a zoo as a
        # multipolygon, and a multipolygon is a relation.
        if name and entry.get("type") in ("way", "relation") and classify(tags) in OFFERED_CLASSES:
            rings, _holes = _polygon_rings(entry, proj)
            pts = [p for ring in rings for p in ring] if rings else _geom(entry, proj)
            if pts:
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                if xmin <= cx <= xmax and ymin <= cy <= ymax:
                    candidates.append(
                        {
                            "n": name,
                            "cls": classify(tags),
                            "x": round(cx, 1),
                            "y": round(cy, 1),
                            "d": round(index.distance(cx, cy, cap_m=3000.0)),
                            "tags": {k: v for k, v in tags.items() if k in LANDMARK_TAG_KEYS},
                        }
                    )
    for road, entries in ways.items():
        if road_keep.get(road):
            roads += entries
        else:
            counts["road_dropped"] += len(entries)
    # **A buried river is not on the ground, so it is not drawn.** OSM maps a
    # buried river as a watercourse because it still flows; it runs in a sewer
    # under a street and there is nothing to see. The test is per watercourse
    # and by length, not per way: a river that passes under one short culvert
    # out of thirteen ways stays whole, and one that is `tunnel=yes` end to end
    # goes.
    gone = {
        key for key, run in overall.items() if run > 0 and under.get(key, 0.0) / run >= BURIED_FRAC
    }
    counts["river_buried"] = sum(1 for r in rivers if r["k"] in gone)
    rivers = [{k: v for k, v in r.items() if k != "k"} for r in rivers if r["k"] not in gone]
    wood_inner, trees = "", []
    if options.generalise:
        cell = derived["cell_m"]
        layer = generalise_layer(
            wood,
            wood_holes,
            clip,
            cell,
            options.morph_cells,
            derived["min_area_ha"],
            options.smooth_passes,
            jitter_m=derived["blob_jitter_m"],
            inset_cells=options.inset_cells,
            seed_spacing_m=derived["tree_spacing_m"],
        )
        wood_path = "".join(path_d(r, close=True) for r in layer["outer"])
        wood_inner = "".join(path_d(r, close=True) for r in layer["inner"])
        trees = layer["seeds"]
        wood_n = len(layer["outer"])
        park_layer = generalise_layer(
            park,
            [],
            clip,
            cell * 1.5,
            options.morph_cells,
            derived["min_area_ha"] * 3,
            options.smooth_passes,
            jitter_m=derived["blob_jitter_m"],
            inset_cells=0,
            seed=9,
        )
        park_path = "".join(path_d(r, close=True) for r in park_layer["outer"])
        park_n = len(park_layer["outer"])
    else:
        wood_path, wood_n = rings_path(wood, wood_holes), len(wood)
        park_path, park_n = rings_path(park), len(park)
    return {
        "wood": {"d": wood_path, "inner": wood_inner, "n": wood_n},
        "trees": trees,
        "park": {"d": park_path, "n": park_n},
        "water_area": {"d": rings_path(lakes), "n": len(lakes)},
        "sea_osm": {"d": rings_path(sea_polys), "n": len(sea_polys)},
        "coastline": coast,
        "roads": roads,
        "rivers": rivers,
        "landmark_candidates": _dedupe(candidates),
        "counts": counts,
    }


def _dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per named thing, nearest the track kept."""
    best: dict[str, dict[str, Any]] = {}
    loose: list[dict[str, Any]] = []
    for entry in sorted(candidates, key=lambda c: c["d"]):
        if not entry["n"]:
            loose.append(entry)
        elif entry["n"] not in best:
            best[entry["n"]] = entry
    return sorted(list(best.values()) + loose, key=lambda c: c["d"])


# --------------------------------------------------------------------------- hachures


class Field:
    """The elevation grid sampled in route metre space.

    Hachures and waves are drawn in metres, not in grid cells, so both need to
    ask the terrain a question at an arbitrary point rather than at a post.
    """

    def __init__(
        self, grid: list[list[float]], lats: list[float], lons: list[float], proj: Projection
    ) -> None:
        """Wrap a grid with its geography.

        Args:
            grid: Elevation rows, row 0 southernmost.
            lats: Grid latitudes, ascending.
            lons: Grid longitudes, ascending.
            proj: The activity's projection.
        """
        self.grid = grid
        self.n = len(grid)
        self.proj = proj
        self.lat0, self.lon0 = lats[0], lons[0]
        self.dlat = lats[1] - lats[0]
        self.dlon = lons[1] - lons[0]
        self.dx = self.dlon * proj.kx
        self.dy = self.dlat * proj.ky
        x0, y0 = proj(lats[0], lons[0])
        x1, y1 = proj(lats[-1], lons[-1])
        self.box = (x0, y0, x1, y1)

    def at(self, x: float, y: float) -> float:
        """Bilinear elevation at a point in metres."""
        col = (x - self.box[0]) / self.dx
        row = (y - self.box[1]) / self.dy
        c0 = min(max(int(col), 0), self.n - 2)
        r0 = min(max(int(row), 0), self.n - 2)
        tc = min(max(col - c0, 0.0), 1.0)
        tr = min(max(row - r0, 0.0), 1.0)
        top = self.grid[r0][c0] * (1 - tc) + self.grid[r0][c0 + 1] * tc
        bot = self.grid[r0 + 1][c0] * (1 - tc) + self.grid[r0 + 1][c0 + 1] * tc
        return top * (1 - tr) + bot * tr

    def slope(self, x: float, y: float) -> tuple[float, float]:
        """Downhill direction and gradient magnitude at a point in metres."""
        h = max(self.dx, self.dy) * 0.5
        gx = (self.at(x + h, y) - self.at(x - h, y)) / (2 * h)
        gy = (self.at(x, y + h) - self.at(x, y - h)) / (2 * h)
        return (-gx, -gy), math.hypot(gx, gy)


def _jitter(i: int, j: int, salt: int = 0) -> tuple[float, float]:
    """Two repeatable pseudo-random numbers in [-0.5, 0.5) for one grid cell.

    Repeatable matters: a hachure field that moved every time the page was
    rebuilt would make two screenshots impossible to compare.
    """
    h = (i * 73856093) ^ (j * 19349663) ^ (salt * 83492791)
    h &= 0x7FFFFFFF
    return (((h % 1000) / 1000.0) - 0.5, (((h // 1000) % 1000) / 1000.0) - 0.5)


def hachures(
    field: Field,
    clip: tuple[float, float, float, float],
    index: TrackIndex | None = None,
    spacing_m: float = 55.0,
    min_slope: float = 0.035,
    max_length_m: float = 90.0,
    buffer_m: float = 40.0,
    steps: int = 5,
    buckets: int = 4,
) -> list[dict[str, Any]]:
    """Lines of descent, the way a hand-drawn sketch shows hills.

    Each stroke starts on a jittered grid and walks downhill; its length and its
    weight follow the slope, so flat ground stays empty paper and a steep face
    fills with dark strokes. Seeds near the track are skipped, because a hachure
    crossing the line is the one mark on the sheet that reads as an error.

    Args:
        field: The terrain.
        clip: (xmin, ymin, xmax, ymax) in metres.
        index: The track, for the buffer. None draws hachures everywhere.
        spacing_m: Metres between seeds.
        min_slope: Gradient below which no stroke is drawn.
        max_length_m: The longest a stroke gets, on the steepest ground.
        buffer_m: Metres of clear paper kept either side of the track.
        steps: Integration steps per stroke.
        buckets: How many opacity levels the strokes are grouped into, so the
            layer ships as a handful of paths rather than a thousand.

    Returns:
        One entry per weight, `{"o": opacity, "d": path}`, lightest first.
    """
    xmin, ymin, xmax, ymax = clip
    groups: list[list[str]] = [[] for _ in range(buckets)]
    cols = int((xmax - xmin) / spacing_m) + 1
    rows = int((ymax - ymin) / spacing_m) + 1
    for j in range(rows):
        for i in range(cols):
            jx, jy = _jitter(i, j)
            x = xmin + (i + 0.5 + jx * 0.8) * spacing_m
            y = ymin + (j + 0.5 + jy * 0.8) * spacing_m
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                continue
            (dx, dy), grad = field.slope(x, y)
            if grad < min_slope:
                continue
            if index is not None and index.distance(x, y, cap_m=buffer_m + 1) <= buffer_m:
                continue
            weight = min(1.0, (grad - min_slope) / max(min_slope * 3.0, 1e-6))
            length = max_length_m * (0.35 + 0.65 * weight)
            line = [(x, y)]
            px, py = x, y
            for _ in range(steps):
                (dx, dy), grad = field.slope(px, py)
                norm = math.hypot(dx, dy)
                if norm == 0 or grad < min_slope * 0.6:
                    break
                px += dx / norm * (length / steps)
                py += dy / norm * (length / steps)
                if index is not None and index.distance(px, py, cap_m=buffer_m + 1) <= buffer_m:
                    break
                line.append((px, py))
            if len(line) < 2 or math.dist(line[0], line[-1]) < spacing_m * 0.15:
                continue
            groups[min(buckets - 1, int(weight * buckets))].append(stroke_d(line))
    return [
        {"o": round((k + 1) / buckets, 3), "d": "".join(parts)}
        for k, parts in enumerate(groups)
        if parts
    ]


def wave_strokes(
    field: Field,
    clip: tuple[float, float, float, float],
    sea_level: float = 0.0,
    spacing_m: float = 130.0,
    length_m: float = 70.0,
) -> str:
    """Sparse S-curves over the water, for the hand-drawn sea.

    A flat fill states where the sea is; these state that it is sea. Both are
    offered, because which one belongs on the page is a judgement about the
    drawing rather than about the data.

    Args:
        field: The terrain, which is what says where the water is.
        clip: (xmin, ymin, xmax, ymax) in metres.
        sea_level: Metres at or below which a point is water.
        spacing_m: Metres between strokes.
        length_m: How long each stroke is.

    Returns:
        One path holding every stroke, empty when there is no water.
    """
    xmin, ymin, xmax, ymax = clip
    parts = []
    cols = int((xmax - xmin) / spacing_m) + 1
    rows = int((ymax - ymin) / spacing_m) + 1
    for j in range(rows):
        for i in range(cols):
            jx, jy = _jitter(i, j, salt=7)
            x = xmin + (i + 0.5 + jx) * spacing_m
            y = ymin + (j + 0.5 + jy) * spacing_m
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                continue
            if field.at(x, y) > sea_level:
                continue
            half = length_m / 2
            amp = length_m * 0.14
            parts.append(
                f"M{x - half:.0f},{y:.0f}"
                f"C{x - half / 2:.0f},{y + amp:.0f} {x - half / 4:.0f},{y - amp:.0f} "
                f"{x:.0f},{y:.0f}"
                f"C{x + half / 4:.0f},{y + amp:.0f} {x + half / 2:.0f},{y - amp:.0f} "
                f"{x + half:.0f},{y:.0f}"
            )
    return "".join(parts)


# --------------------------------------------------------------------------- generalise


def _fill_ring(
    mask: list[bytearray], ring: list[Pt], x0: float, y0: float, cell: float, value: int
) -> None:
    """Scanline-fill one ring into a mask, in place.

    Testing every cell against every ring is the obvious way and far too slow on
    a ride's sheet; a scanline costs one pass over the ring's own points per row
    it covers.

    Args:
        mask: Rows of cells, row 0 southernmost.
        ring: Closed ring in metres.
        x0: Metres at the mask's western edge.
        y0: Metres at the mask's southern edge.
        cell: Metres per cell.
        value: 1 to paint, 0 to erase.
    """
    rows, cols = len(mask), len(mask[0])
    ys = [p[1] for p in ring]
    lo = max(0, int((min(ys) - y0) / cell))
    hi = min(rows - 1, int((max(ys) - y0) / cell) + 1)
    for r in range(lo, hi + 1):
        y = y0 + (r + 0.5) * cell
        crossings = []
        for i in range(len(ring)):
            (ax, ay), (bx, by) = ring[i], ring[(i + 1) % len(ring)]
            if (ay > y) == (by > y):
                continue
            crossings.append(ax + (y - ay) * (bx - ax) / (by - ay))
        crossings.sort()
        row = mask[r]
        for a, b in zip(crossings[0::2], crossings[1::2], strict=False):
            ca = max(0, int(math.ceil((a - x0) / cell - 0.5)))
            cb = min(cols - 1, int((b - x0) / cell - 0.5))
            for c in range(ca, cb + 1):
                row[c] = value


def rasterise(
    rings: list[list[Pt]],
    holes: list[list[Pt]],
    clip: tuple[float, float, float, float],
    cell: float,
) -> list[bytearray]:
    """The union of a set of rings as a coarse binary mask.

    Rasterising is what turns "one hundred overlapping wood polygons" into one
    shape. Every later step, the smoothing and the speck removal, works on the
    shape rather than on the hundred.

    Args:
        rings: Filled rings in metres.
        holes: Rings that punch through them.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell.

    Returns:
        Rows of cells, row 0 southernmost.
    """
    xmin, ymin, xmax, ymax = clip
    cols = max(1, int((xmax - xmin) / cell) + 1)
    rows = max(1, int((ymax - ymin) / cell) + 1)
    mask = [bytearray(cols) for _ in range(rows)]
    for ring in rings:
        if len(ring) > 2:
            _fill_ring(mask, ring, xmin, ymin, cell, 1)
    for ring in holes:
        if len(ring) > 2:
            _fill_ring(mask, ring, xmin, ymin, cell, 0)
    return mask


def _spread(mask: list[bytearray], radius: int, grow: bool) -> list[bytearray]:
    """Dilate or erode a mask by a square of `radius` cells, separably."""
    if radius <= 0:
        return [bytearray(row) for row in mask]
    rows, cols = len(mask), len(mask[0])
    hit = 1 if grow else 0
    out = [bytearray(row) for row in mask]
    for r in range(rows):
        src, dst = mask[r], out[r]
        for c in range(cols):
            lo, hi = max(0, c - radius), min(cols - 1, c + radius)
            dst[c] = hit if any(src[i] == hit for i in range(lo, hi + 1)) else src[c]
    final = [bytearray(row) for row in out]
    for c in range(cols):
        column = [out[r][c] for r in range(rows)]
        for r in range(rows):
            lo, hi = max(0, r - radius), min(rows - 1, r + radius)
            if any(column[i] == hit for i in range(lo, hi + 1)):
                final[r][c] = hit
    return final


def _components(mask: list[bytearray], value: int) -> list[list[tuple[int, int]]]:
    """Four-connected components of the cells equal to `value`."""
    rows, cols = len(mask), len(mask[0])
    seen = [bytearray(cols) for _ in range(rows)]
    out = []
    for r0 in range(rows):
        for c0 in range(cols):
            if seen[r0][c0] or mask[r0][c0] != value:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = 1
            blob = []
            while stack:
                r, c = stack.pop()
                blob.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < rows
                        and 0 <= nc < cols
                        and not seen[nr][nc]
                        and mask[nr][nc] == value
                    ):
                        seen[nr][nc] = 1
                        stack.append((nr, nc))
            out.append(blob)
    return out


def declutter(mask: list[bytearray], min_cells: int) -> list[bytearray]:
    """Drop specks and fill pinholes below `min_cells` in area.

    A wood the size of four cells is noise on a sheet this size, and so is a
    clearing the same size. Both go, which is what leaves few big shapes.
    """
    out = [bytearray(row) for row in mask]
    for blob in _components(out, 1):
        if len(blob) < min_cells:
            for r, c in blob:
                out[r][c] = 0
    rows, cols = len(out), len(out[0])
    for blob in _components(out, 0):
        touches_edge = any(r in (0, rows - 1) or c in (0, cols - 1) for r, c in blob)
        if not touches_edge and len(blob) < min_cells:
            for r, c in blob:
                out[r][c] = 1
    return out


def trace_mask(
    mask: list[bytearray],
    clip: tuple[float, float, float, float],
    cell: float,
    eps: float = 18.0,
    passes: int = 3,
) -> list[list[Pt]]:
    """Trace a mask back into smooth rings.

    Args:
        mask: Rows of cells, row 0 southernmost.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell.
        eps: Douglas-Peucker tolerance in metres, applied before the smoothing.
        passes: Chaikin passes. Two or three is the difference between a
            staircase and a brush stroke.

    Returns:
        Closed rings in metres, filled rings and holes both, wound so one
        `fill-rule="nonzero"` path fills the union once.
    """
    xmin, ymin, _, _ = clip
    padded = [[0.0] * (len(mask[0]) + 2)]
    padded += [[0.0] + [float(v) for v in row] + [0.0] for row in mask]
    padded += [[0.0] * (len(mask[0]) + 2)]
    out = []
    for ring in marching_squares(padded, 0.5):
        if len(ring) < 4:
            continue
        wet = _ring_is_wet(ring, padded, 0.5)
        metres = [(xmin + (col - 1) * cell, ymin + (row - 1) * cell) for col, row in ring]
        metres = smooth(simplify(metres, eps), passes=passes, closed=True)
        metres = simplify(metres, eps * 0.3)
        if len(metres) > 3:
            out.append(orient(metres, wet))
    return out


def generalise(
    rings: list[list[Pt]],
    holes: list[list[Pt]],
    clip: tuple[float, float, float, float],
    cell: float,
    morph_cells: int = 2,
    min_area_ha: float = 4.0,
    passes: int = 3,
) -> list[list[Pt]]:
    """Raster generalisation: union, close, open, declutter, trace, smooth.

    This is the whole answer to "too intricate, too many greens". Everything
    that reaches the sheet has been through one grid, so what comes out is a
    few big shapes with soft edges rather than a hundred outlines stacked on
    each other.

    Args:
        rings: Filled rings in metres.
        holes: Rings that punch through them.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell of the working grid.
        morph_cells: Radius of the close and the open, in cells.
        min_area_ha: Hectares below which a blob or a hole is dropped.
        passes: Chaikin passes on the traced outline.

    Returns:
        Rings ready to concatenate into one filled path.
    """
    if not rings:
        return []
    mask = rasterise(rings, holes, clip, cell)
    mask = _spread(_spread(mask, morph_cells, grow=True), morph_cells, grow=False)
    mask = _spread(_spread(mask, morph_cells, grow=False), morph_cells, grow=True)
    min_cells = max(1, int(min_area_ha * 10000.0 / (cell * cell)))
    mask = declutter(mask, min_cells)
    return trace_mask(mask, clip, cell, eps=cell * 0.55, passes=passes)


def jitter_ring(ring: list[Pt], amplitude: float, seed: int = 0) -> list[Pt]:
    """Push a ring's outline in and out along its own normals.

    A generalised mask traces as a smooth but obviously computed curve. The
    hand-drawn maps do not have accurate edges, they have loose ones, so every vertex is moved along its outward normal by a low-frequency
    wave: the shape stays the shape and the edge stops looking measured.

    Args:
        ring: A closed ring in metres.
        amplitude: Metres of movement at the peak of the wave.
        seed: Shifts the wave, so two layers do not wobble in step.

    Returns:
        The moved ring, the same length.
    """
    n = len(ring)
    if n < 4 or amplitude <= 0:
        return ring
    outward = 1.0 if signed_area(ring) > 0 else -1.0
    phase = (seed % 17) * 0.37
    out = []
    for i, (x, y) in enumerate(ring):
        ax, ay = ring[i - 1]
        bx, by = ring[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        norm = math.hypot(dx, dy) or 1.0
        nx, ny = dy / norm * outward, -dx / norm * outward
        t = i / n * math.tau
        wave = 0.62 * math.sin(3 * t + phase) + 0.38 * math.sin(7 * t + phase * 2.3)
        out.append((x + nx * amplitude * wave, y + ny * amplitude * wave))
    return out


def scatter(
    mask: list[bytearray],
    clip: tuple[float, float, float, float],
    cell: float,
    spacing_m: float,
    salt: int = 3,
) -> list[Pt]:
    """Points on a jittered grid that fall well inside a mask.

    For the tree glyphs: a wood is a wash, and a handful of little conifers in
    it is what says the wash is a wood rather than a field.

    Args:
        mask: Rows of cells, row 0 southernmost.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell of the mask.
        spacing_m: Metres between seeds. Zero scatters nothing.
        salt: Shifts the jitter.

    Returns:
        Points in metres, repeatable between builds.
    """
    if spacing_m <= 0:
        return []
    inner = _spread(mask, 1, grow=False)
    xmin, ymin, xmax, ymax = clip
    out: list[Pt] = []
    cols = int((xmax - xmin) / spacing_m) + 1
    rows = int((ymax - ymin) / spacing_m) + 1
    for j in range(rows):
        for i in range(cols):
            jx, jy = _jitter(i, j, salt)
            x = xmin + (i + 0.5 + jx * 0.9) * spacing_m
            y = ymin + (j + 0.5 + jy * 0.9) * spacing_m
            c, r = int((x - xmin) / cell), int((y - ymin) / cell)
            if 0 <= r < len(inner) and 0 <= c < len(inner[0]) and inner[r][c]:
                out.append((round(x, 1), round(y, 1)))
    return out


def generalise_layer(
    rings: list[list[Pt]],
    holes: list[list[Pt]],
    clip: tuple[float, float, float, float],
    cell: float,
    morph_cells: int = 2,
    min_area_ha: float = 4.0,
    passes: int = 3,
    jitter_m: float = 0.0,
    inset_cells: int = 2,
    seed_spacing_m: float = 0.0,
    seed: int = 0,
) -> dict[str, Any]:
    """The generalisation stage, and the two extra passes a wash wants.

    Args:
        rings: Filled rings in metres.
        holes: Rings that punch through them.
        clip: (xmin, ymin, xmax, ymax) in metres.
        cell: Metres per cell of the working grid.
        morph_cells: Radius of the close and the open, in cells.
        min_area_ha: Hectares below which a blob, or a hole, is dropped.
        passes: Chaikin passes on the traced outline.
        jitter_m: Metres of loose-edge wobble. Zero draws the measured edge.
        inset_cells: Cells to pull in for the second, darker pass of pigment.
        seed_spacing_m: Metres between tree seeds. Zero scatters none.
        seed: Shifts the wobble, so two layers do not move in step.

    Returns:
        `outer` rings, the `inner` second-pass rings, and the tree `seeds`.
    """
    empty: dict[str, Any] = {"outer": [], "inner": [], "seeds": []}
    if not rings:
        return empty
    mask = rasterise(rings, holes, clip, cell)
    mask = _spread(_spread(mask, morph_cells, grow=True), morph_cells, grow=False)
    mask = _spread(_spread(mask, morph_cells, grow=False), morph_cells, grow=True)
    min_cells = max(1, int(min_area_ha * 10000.0 / (cell * cell)))
    mask = declutter(mask, min_cells)
    eps = cell * 0.55

    def traced(source: list[bytearray], salt: int) -> list[list[Pt]]:
        out = []
        for ring in trace_mask(source, clip, cell, eps=eps, passes=passes):
            out.append(jitter_ring(ring, jitter_m, salt) if jitter_m else ring)
        return out

    inner_mask = declutter(_spread(mask, max(1, inset_cells), grow=False), min_cells)
    return {
        "outer": traced(mask, seed),
        "inner": traced(inner_mask, seed + 5) if inset_cells > 0 else [],
        "seeds": scatter(mask, clip, cell, seed_spacing_m),
    }


# --------------------------------------------------------------------------- land cover

#: The land cover classes the journal map paints. The renderer's own Overpass
#: query asks for wood, water and roads and nothing else, so the cache cannot
#: say what the ground between them is; this is the second query that can.
LANDCOVER_LANDUSE = (
    "farmland|meadow|grass|orchard|vineyard|allotments|"
    "village_green|recreation_ground|cemetery|residential|"
    "industrial|commercial|retail|quarry|farmyard|"
    "greenhouse_horticulture"
)
LANDCOVER_NATURAL = "grassland|heath|moor|scrub|wetland|bare_rock|beach|sand|shingle|cliff|scree"
LANDCOVER_LEISURE = "park|golf_course|nature_reserve|pitch|garden"

LANDCOVER_QUERY = """[out:json][timeout:300];
(
  way["landuse"~"^({landuse})$"]({box});
  relation["landuse"~"^({landuse})$"]({box});
  way["natural"~"^({natural})$"]({box});
  relation["natural"~"^({natural})$"]({box});
  way["leisure"~"^({leisure})$"]({box});
  relation["leisure"~"^({leisure})$"]({box});
);
out geom;"""

#: OSM tag to pigment class. Later in this list wins where two polygons overlap,
#: so the plate carries one class per pixel and no two land pigments can stack.
COVER_TAGS: tuple[tuple[str, str, str], ...] = (
    ("landuse", "farmland", "farmland"),
    ("landuse", "farmyard", "built"),
    ("landuse", "meadow", "meadow"),
    ("landuse", "grass", "meadow"),
    ("landuse", "village_green", "meadow"),
    ("landuse", "recreation_ground", "meadow"),
    ("leisure", "park", "meadow"),
    ("leisure", "garden", "meadow"),
    ("leisure", "pitch", "meadow"),
    ("leisure", "golf_course", "meadow"),
    ("natural", "grassland", "meadow"),
    ("landuse", "orchard", "orchard"),
    ("landuse", "vineyard", "orchard"),
    ("landuse", "allotments", "orchard"),
    ("natural", "scrub", "scrub"),
    ("leisure", "nature_reserve", "scrub"),
    ("natural", "heath", "heath"),
    ("natural", "moor", "heath"),
    ("natural", "beach", "sand"),
    ("natural", "sand", "sand"),
    ("natural", "shingle", "sand"),
    ("natural", "bare_rock", "rock"),
    ("natural", "scree", "rock"),
    ("natural", "cliff", "rock"),
    ("natural", "wetland", "wetland"),
    ("landuse", "residential", "built"),
    ("landuse", "commercial", "built"),
    ("landuse", "retail", "built"),
    ("landuse", "cemetery", "built"),
    ("landuse", "industrial", "works"),
    ("landuse", "quarry", "works"),
    ("landuse", "greenhouse_horticulture", "works"),
    ("landuse", "forest", "wood"),
    ("natural", "wood", "wood"),
)

#: Painting order, low to high. A wood drawn over farmland replaces it.
COVER_ORDER: tuple[str, ...] = (
    "farmland",
    "meadow",
    "orchard",
    "scrub",
    "heath",
    "sand",
    "rock",
    "wetland",
    "built",
    "works",
    "wood",
)

#: Ground kept around the track when fetching land cover. Wider than the
#: feature margin, because the painted card is grown by a ribbon radius first.
LANDCOVER_MARGIN_M = 2600.0


def landcover_path(key: str, cache_dir: Path) -> Path:
    """Where the land cover payload for one activity is cached."""
    return cache_dir / f"landcover-{key}.json"


def fetch_landcover(box: tuple[float, float, float, float], path: Path) -> int:
    """Fetch the land cover classes for one bounding box into the cache.

    Args:
        box: (south, west, north, east) in degrees.
        path: Cache file to write.

    Returns:
        Bytes written.

    Raises:
        RuntimeError: When every mirror refused the query.
    """
    query = LANDCOVER_QUERY.format(
        box=",".join(f"{value:f}" for value in box),
        landuse=LANDCOVER_LANDUSE,
        natural=LANDCOVER_NATURAL,
        leisure=LANDCOVER_LEISURE,
    )
    text = ""
    for attempt in range(3):
        for url in OVERPASS_URLS:
            try:
                text = _get(url, data={"data": query}, timeout=300.0)
                json.loads(text)
            except Exception as exc:  # a mirror under load is not a failed fetch
                log.info("landcover %s attempt %d: %s", url, attempt + 1, exc)
                text = ""
                time.sleep(4.0)
                continue
            break
        if text:
            break
    if not text:
        raise RuntimeError("every Overpass mirror refused the land cover query")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.stat().st_size


def cover_rings(
    key: str, proj: Projection, clip: tuple[float, float, float, float], eps: float, cache_dir: Path
) -> dict[str, list[list[Pt]]]:
    """Land cover rings by pigment class, clipped to the card and simplified.

    Args:
        key: The activity, naming the cache file.
        proj: The activity's projection.
        clip: The card, in metres.
        eps: Simplification tolerance in metres.
        cache_dir: Where the payload lives.

    Returns:
        Rings by class; empty when there is no land cover cached.
    """
    path = landcover_path(key, cache_dir)
    out: dict[str, list[list[Pt]]] = {}
    if not path.exists():
        return out
    lookup = {(key, value): cls for key, value, cls in COVER_TAGS}
    payload = json.loads(path.read_text())
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        cls = None
        for tag_key in ("landuse", "natural", "leisure"):
            if tag_key in tags:
                cls = lookup.get((tag_key, tags[tag_key]), cls)
        if cls is None:
            continue
        outer, _inner = _polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > 3:
                out.setdefault(cls, []).append(simplify(cut, eps))
    return out


def wood_rings(
    key: str, proj: Projection, clip: tuple[float, float, float, float], eps: float, cache_dir: Path
) -> list[list[Pt]]:
    """Wood rings straight from the renderer's own Overpass cache."""
    path = overpass_path(key, cache_dir)
    rings: list[list[Pt]] = []
    if not path.exists():
        return rings
    for entry in json.loads(path.read_text()).get("elements", []):
        tags = entry.get("tags") or {}
        if tags.get("landuse") != "forest" and tags.get("natural") != "wood":
            continue
        outer, _ = _polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > 3:
                rings.append(simplify(cut, eps))
    return rings


def coastline_chains(
    key: str,
    proj: Projection,
    clip: tuple[float, float, float, float],
    cache_dir: Path,
    min_length_m: float = 300.0,
) -> list[list[Pt]]:
    """Coastline ways as surveyed: clipped, joined, and never smoothed.

    The coast is the one line on the sheet a reader would notice being wrong,
    so it keeps its own vertices. Offshore rocks come back as their own
    little rings and are ink specks at plate size, so only chains of real coast
    are kept.
    """
    path = overpass_path(key, cache_dir)
    if not path.exists():
        return []
    ways: list[list[Pt]] = []
    for entry in json.loads(path.read_text()).get("elements", []):
        if (entry.get("tags") or {}).get("natural") != "coastline":
            continue
        pts = [proj(g["lat"], g["lon"]) for g in entry.get("geometry", []) if g]
        ways += [p for p in clip_line(pts, clip) if len(p) > 1]
    joined = [c for c in join_chains(ways, tol=2.0) if len(c) > 3]
    return [
        c
        for c in joined
        if sum(math.dist(c[i], c[i + 1]) for i in range(len(c) - 1)) > min_length_m
    ]


def sea_from_coast(
    chains: list[list[Pt]], clip: tuple[float, float, float, float]
) -> list[list[Pt]]:
    """Close a coastline chain around the card edge to make the sea.

    OSM draws a coastline with the land on its left, so the sea is the side the
    right-hand normal points at. Both closures round the card are built and the
    one that holds most of a set of probes just off the coast is the sea: one
    probe is not enough, because a cove puts a single right-hand normal back on
    land.

    Args:
        chains: Coastline chains in metres, already clipped to the card.
        clip: The card, in metres.

    Returns:
        One closed ring, or an empty list when no chain crosses the card.
    """
    xmin, ymin, xmax, ymax = clip
    corners = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]

    def perimeter_t(p: Pt) -> float:
        """Position of a point on the card edge, 0 to 4, anticlockwise."""
        x, y = p
        if abs(y - ymin) < 1e-6:
            return (x - xmin) / max(xmax - xmin, 1e-6)
        if abs(x - xmax) < 1e-6:
            return 1 + (y - ymin) / max(ymax - ymin, 1e-6)
        if abs(y - ymax) < 1e-6:
            return 2 + (xmax - x) / max(xmax - xmin, 1e-6)
        return 3 + (ymax - y) / max(ymax - ymin, 1e-6)

    def arc(t0: float, t1: float, forward: bool) -> list[Pt]:
        """The card corners passed walking the edge from t0 to t1."""
        out: list[Pt] = []
        t = t0
        for _ in range(5):
            nxt = (math.floor(t) + 1) if forward else (math.ceil(t) - 1)
            gap = (nxt - t) % 4 if forward else (t - nxt) % 4
            want = (t1 - t) % 4 if forward else (t - t1) % 4
            if gap >= want or gap <= 1e-9:
                break
            out.append(corners[int(nxt) % 4])
            t = nxt % 4
        return out

    def length(chain: list[Pt]) -> float:
        return sum(math.dist(chain[i], chain[i + 1]) for i in range(len(chain) - 1))

    def edge_gap(p: Pt) -> float:
        return min(abs(p[0] - xmin), abs(p[0] - xmax), abs(p[1] - ymin), abs(p[1] - ymax))

    def snap(p: Pt) -> Pt:
        """Put an endpoint exactly on the card edge it was clipped against."""
        x, y = p
        gaps = [
            (abs(x - xmin), (xmin, y)),
            (abs(x - xmax), (xmax, y)),
            (abs(y - ymin), (x, ymin)),
            (abs(y - ymax), (x, ymax)),
        ]
        return min(gaps)[1]

    open_chains = [
        c for c in chains if len(c) > 3 and edge_gap(c[0]) < 30.0 and edge_gap(c[-1]) < 30.0
    ]
    open_chains = [[snap(c[0])] + c[1:-1] + [snap(c[-1])] for c in open_chains]
    if not open_chains:
        return []
    chain = max(open_chains, key=length)
    probes: list[Pt] = []
    for k in range(1, 20):
        i = max(min(len(chain) * k // 20, len(chain) - 2), 0)
        dx, dy = chain[i + 1][0] - chain[i][0], chain[i + 1][1] - chain[i][1]
        n = math.hypot(dx, dy)
        if n < 1e-6:
            continue
        probes.append((chain[i][0] + dy / n * 70.0, chain[i][1] - dx / n * 70.0))
    t0, t1 = perimeter_t(chain[-1]), perimeter_t(chain[0])
    best, best_score = None, -1
    for forward in (True, False):
        ring = chain + arc(t0, t1, forward)
        if len(ring) < 4:
            continue
        score = sum(1 for p in probes if point_in_ring(p[0], p[1], ring))
        if score > best_score:
            best, best_score = ring, score
    if best is None or best_score <= len(probes) * 0.5:
        return []
    return [best]


# --------------------------------------------------------------------------- the card


def journal_geometry(
    route: list[Pt], card: CardStyle, ribbon: RibbonStyle, brush: BrushStyle
) -> dict[str, Any]:
    """The card, its ribbon radius, and every size the plate is painted at.

    Every size on the sheet is derived from this, so a 13 km box and a 3 km box
    are drawn with the same weights on screen rather than the same weights on
    the ground. The ribbon is a constant times the square root of the box plus
    a small-box offset: that keeps a generous ribbon on a small box without
    swelling it to the whole sheet on a big one.

    Args:
        route: The track in metres.
        card: The card's display size and supersampling.
        ribbon: The ribbon's fit and the card's framing.
        brush: The widths and thresholds the sizes on the sheet are stated in.

    Returns:
        The card box, the render and display sizes, the ribbon radius, and the
        painted widths every layer is stated in.
    """
    xs = [p[0] for p in route]
    ys = [p[1] for p in route]
    bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
    span = max(bx1 - bx0, by1 - by0, 1.0)
    fitted = min(
        max(ribbon.ribbon_k * math.sqrt(span) + ribbon.ribbon_c, ribbon.ribbon_min_m),
        ribbon.ribbon_max_m,
    )
    ribbon_radius = fitted * ribbon.ribbon_mult
    grow = fitted * ribbon.card_grow_mult
    cx0, cy0, cx1, cy1 = bx0 - grow, by0 - grow, bx1 + grow, by1 + grow
    pad = max(
        ribbon.card_pad_frac * max(cx1 - cx0, cy1 - cy0), ribbon.card_pad_ribbon_frac * fitted
    )
    cx0, cy0, cx1, cy1 = cx0 - pad, cy0 - pad, cx1 + pad, cy1 + pad
    w, h = cx1 - cx0, cy1 - cy0
    aspect = w / h
    if aspect < ribbon.card_aspect_min:
        extra = (h * ribbon.card_aspect_min - w) / 2
        cx0, cx1 = cx0 - extra, cx1 + extra
    elif aspect > ribbon.card_aspect_max:
        extra = (w / ribbon.card_aspect_max - h) / 2
        cy0, cy1 = cy0 - extra, cy1 + extra
    w, h = cx1 - cx0, cy1 - cy0
    display_w = int(card.display_px)
    render_w = display_w * int(card.supersample)
    render_h = int(round(render_w * h / w))
    mpp = w / render_w
    disp = mpp * card.supersample
    return {
        "card": [round(cx0, 1), round(cy0, 1), round(cx1, 1), round(cy1, 1)],
        "bounds": [round(bx0, 1), round(by0, 1), round(bx1, 1), round(by1, 1)],
        "span_m": round(span),
        "ribbon_m": round(ribbon_radius),
        "ribbon_fitted_m": round(fitted),
        "render": [render_w, render_h],
        "display": [display_w, int(round(render_h / card.supersample))],
        "mpp": round(mpp, 3),
        "mpp_display": round(disp, 3),
        "wet_px": {
            cls: round(min(max(k * (span / 1000.0) ** e, lo), hi), 2)
            for cls, (k, e, lo, hi) in brush.river_curve.items()
        },
        "minor_roads": disp < brush.minor_roads_mppd,
        "blotch_m": round(max(brush.blotch_m[0], disp * brush.blotch_m[1]), 1),
        "dab_spacing_m": round(max(brush.dab_spacing_m[0], disp * brush.dab_spacing_m[1]), 1),
        "gran_m": round(max(brush.gran_m[0], disp * brush.gran_m[1]), 1),
    }


def _line(points: list[Pt]) -> Line:
    """A polyline as the basemap carries it: float pairs at full precision."""
    return tuple((float(x), float(y)) for x, y in points)


def _drawn(piece: list[Pt], tol: float) -> Line:
    """Simplify, then Chaikin: a line someone drew, not a line surveyed."""
    return _line(smooth(simplify(piece, tol), passes=2))


def _elevation_patch(key: str, proj: Projection, cache_dir: Path) -> ElevationPatch | None:
    """The cached elevation grid placed in card metres, or None when none is cached."""
    from pyntpot.maps.basemap import ElevationPatch

    elev = elevation_path(key, cache_dir)
    if not elev.exists():
        return None
    grid = json.loads(elev.read_text())
    gx0, gy0 = proj(grid["lats"][0], grid["lons"][0])
    gx1, gy1 = proj(grid["lats"][-1], grid["lons"][-1])
    return ElevationPatch(
        n=grid["n"],
        x0=gx0,
        y0=gy0,
        x1=gx1,
        y1=gy1,
        values=tuple(round(float(v), 1) for v in grid["elev"]),
        low=round(min(grid["elev"])),
        high=round(max(grid["elev"])),
    )


def journal_layers(
    key: str,
    lat: list[float],
    lng: list[float],
    card_style: CardStyle,
    ribbon_style: RibbonStyle,
    brush: BrushStyle,
    route: list[Pt] | None = None,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
    basemap_style: BasemapStyle,
) -> Basemap | None:
    """Everything the painter needs for one activity, from the cache.

    The land cover, the coast and the sea come from the two cached Overpass
    payloads; the roads and the watercourses come through `basemap`, so the
    same interaction rules decide what is drawn here as on the vector map.

    Args:
        key: The activity, naming the cache files.
        lat: Track latitudes in recorded order.
        lng: Track longitudes, same length.
        card_style: The card's display size and supersampling.
        ribbon_style: The ribbon's fit and the card's framing.
        brush: The brushes and widths the card's sizes are stated in.
        route: The already-projected track, when the caller has one.
        cache_dir: Where the cached payloads live.
        places: User-supplied places of interest.
        basemap_style: What the basemap draws; the clip margin is the card's
            own longer side, derived here.

    Returns:
        The basemap in card metres, or None when nothing is cached for this box.
    """
    from pyntpot.maps.basemap import Basemap, Layers, River, Road
    from pyntpot.maps.card import Card
    from pyntpot.maps.projection import track_projection

    if not overpass_path(key, cache_dir).exists():
        return None
    proj, pts = track_projection(lat, lng, route)
    track = simplify(pts, 3.0)
    geometry = journal_geometry(track, card_style, ribbon_style, brush)
    clip = tuple(geometry["card"])
    eps = max(geometry["mpp"] * 1.1, 2.0)

    base = basemap(
        key,
        lat,
        lng,
        options=basemap_style,
        cache_dir=cache_dir,
        places=places,
        route=track,
        clip_margin_m=max(clip[2] - clip[0], clip[3] - clip[1]),
    )
    if base is None:
        return None

    cover = cover_rings(key, proj, clip, eps, cache_dir)
    wood = wood_rings(key, proj, clip, eps, cache_dir)
    if wood:
        cover["wood"] = cover.get("wood", []) + wood
    coast = coastline_chains(key, proj, clip, cache_dir)
    sea = sea_from_coast(coast, clip)

    # Three brushes' worth of road: the A and B roads, the lanes, and the tracks
    # the session actually used, which get the scratchy dry brush.
    #
    # A street is one stroke. OSM hands it over cut at every junction, and
    # painting each cut as its own stroke gave every one of them a set-down blot
    # and a taper at both ends: `join_strokes` chains the pieces of one road
    # back together first, so the brush is set down where the street starts and
    # lifted where it ends.
    pieces: dict[tuple[Any, ...], list[list[Pt]]] = {}
    meta: dict[tuple[Any, ...], dict[str, Any]] = {}
    for r in base.get("roads", []):
        if r["c"] == "major":
            band = "major"
        elif r["k"] in ("track", "path", "footway", "bridleway"):
            band = "path"
        else:
            band = "minor"
        # What counts as one road: its band, and the name or number it is known
        # by. Unnamed pieces of a band are one group and chain on their ends
        # alone, which is the right answer for a pavement network that has no
        # names to gather by.
        road_key = (band, r["n"], r.get("r", ""))
        meta.setdefault(
            road_key, {"c": r["c"], "b": band, "k": r["k"], "n": r["n"], "r": r.get("r", "")}
        )
        for seg in parse_path(r["d"]):
            pieces.setdefault(road_key, []).extend(c for c in clip_line(seg, clip) if len(c) > 1)
    # And a stroke shorter than the brush that would draw it is a dab, not a
    # road. What is left after the chaining is mostly a slip lane or a link at a
    # junction that the chain could not take because it took the carriageway
    # instead: a hundred of them can be under one display pixel long, and each
    # still pays for a set-down blot the size of the brush.
    band_width = {"major": "road_major", "minor": "lane", "path": "track"}
    roads = []
    for road_key, lines in pieces.items():
        band = road_key[0]
        floor = brush.brush_width_px.get(band_width[band], 2.0) * geometry["mpp_display"]
        info = meta[road_key]
        for chain in join_strokes(lines, tol=max(eps, 1.0)):
            if length(chain) < floor:
                continue
            roads.append(
                Road(
                    line=_drawn(chain, eps),
                    cls=info["c"],
                    band=info["b"],
                    highway=info["k"],
                    name=info["n"],
                    ref=info["r"],
                )
            )

    lakes = [
        simplify(clip_ring(r, clip), eps)
        for r in parse_path(base.get("water_area", {}).get("d", ""))
    ]

    # The pieces of each watercourse, gathered by name so it is measured and
    # classed as one river rather than as the dozen ways OSM cut it into.
    pieces_by: dict[str, list[list[Pt]]] = {}
    for r in base.get("rivers", []):
        for seg in parse_path(r["d"]):
            pieces_by.setdefault(r["n"], []).extend(c for c in clip_line(seg, clip) if len(c) > 1)

    major, widths = major_rivers(pieces_by, lakes, brush.major_river_rel_frac)
    classed = {
        r["n"]: (("major" if r["n"] in major else "medium") if r["c"] == "river" else "minor")
        for r in base.get("rivers", [])
    }
    rivers = []
    for name, lines in pieces_by.items():
        cls = classed.get(name, "minor")
        floor = geometry["wet_px"].get(cls, 2.2)
        # The pieces of one watercourse are chained before they are measured or
        # drawn, exactly as a road's are, so the width runs continuously along
        # the river rather than restarting at every way OSM cut it at.
        for chain in join_strokes(lines, tol=max(eps, 1.0)):
            entry: dict[str, Any] = {"c": cls, "n": name, "w": floor, "wn": floor}
            if name in widths:
                # Re-centred in its own channel, and drawn at the width it
                # measures at each point rather than at one width throughout.
                centred, along = channel(chain, lakes)
                profile = [
                    painted_width_px(floor, w or 0.0, geometry["mpp_display"]) for w in along
                ]
                profile = eased(profile, CHANNEL_EASE_SAMPLES)
                widest = max(profile)
                entry["w"] = round(widest, 2)
                # And the width it is *typically* drawn at, which is the one a
                # name has to fit inside: `w` is the widest point and says how
                # far a name lifted clear of the water has to be lifted, but a
                # name set on the water could be set anywhere along it.
                entry["wn"] = round(sorted(profile)[len(profile) // 2], 2)
                entry["wp"] = [round(v / widest, 3) for v in profile]
                chain = centred
            rivers.append(
                River(
                    line=_drawn(chain, eps * 0.6),
                    cls=entry["c"],
                    name=entry["n"],
                    width_px=entry["w"],
                    name_width_px=entry["wn"],
                    profile=tuple(entry.get("wp", ())),
                )
            )

    layers = Layers(
        route=_line(track),
        cover={k: tuple(_line(r) for r in v) for k, v in cover.items()},
        cover_order=tuple(c for c in COVER_ORDER if c in cover),
        lakes=tuple(_line(r) for r in lakes if len(r) > 3),
        sea=tuple(_line(r) for r in sea),
        coastline=tuple(_line(c) for c in coast),
        roads=tuple(roads),
        rivers=tuple(rivers),
        elevation=_elevation_patch(key, proj, cache_dir),
        ribbon_m=geometry["ribbon_m"],
        wet_px=geometry["wet_px"],
        minor_roads=geometry["minor_roads"],
        blotch_m=geometry["blotch_m"],
        dab_spacing_m=geometry["dab_spacing_m"],
        gran_m=geometry["gran_m"],
    )
    bx0, by0, bx1, by1 = geometry["bounds"]
    return Basemap(
        projection=proj,
        card=Card.from_manifest(geometry),
        layers=layers,
        bounds=(bx0, by0, bx1, by1),
        span_m=geometry["span_m"],
        ribbon_fitted_m=geometry["ribbon_fitted_m"],
        track=tuple(pts),
        places=tuple(base.get("places", [])),
        candidates=tuple(journal_candidates(base, proj)),
        sources=tuple(base.get("sources", [])),
    )


def parse_path(d: str) -> list[list[Pt]]:
    """The point lists inside one `M x,y L x,y` path, the inverse of `path_d`."""
    out: list[list[Pt]] = []
    for chunk in d.split("M"):
        chunk = chunk.strip().rstrip("Z").strip()
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


# --------------------------------------------------------------------------- candidates


def journal_candidates(
    base: dict[str, Any], proj: Projection, cap: int = LANDMARK_CAP
) -> list[dict[str, Any]]:
    """Every named thing near the track, with its position both ways.

    This is the list the label agent picks from, so it carries latitude and
    longitude as well as metres, how far off the route each one sits, and how
    far off it could sit and still be worth naming.

    **The order is notability, not distance.** Nearest-first was what the list
    had always been, and in a city it is a list of plaques: eighty nearest
    things can fail to reach out of one district, so a zoo is not offered and a
    drinking fountain is. `landmark_rank` puts the things
    a runner navigates by first and, inside a tier, the ones sitting most
    comfortably inside their own reach.
    """
    out = []
    for c in base.get("landmark_candidates", []):
        if not c.get("n") or c.get("x") is None:
            continue
        clat, clng = proj.inverse(c["x"], c["y"])
        reach = landmark_reach(c)
        d = c.get("d")
        out.append(
            {
                "name": c["n"],
                "class": c.get("cls", ""),
                "lat": round(clat, 6),
                "lng": round(clng, 6),
                "x": c["x"],
                "y": c["y"],
                "distance_m": d,
                # How far off the route this thing is still worth naming,
                # and whether it is inside that. A tall thing well off the
                # route reads `notable: true` and a fountain at ten metres
                # reads it too; a plaque at forty does not.
                "reach_m": round(reach),
                "notable": d is not None and d <= reach,
                "tags": c.get("tags", {}),
            }
        )
    out.sort(key=landmark_rank)
    return out[:cap]


GPX_ELEVATION = re.compile(r'lat="([-\d.]+)"\s+lon="([-\d.]+)"[^>]*>\s*<ele>([-\d.]+)</ele>')


def read_gpx_elevation(path: Path) -> list[float]:
    """Elevations from a GPX track, or an empty list when it carries none."""
    return [float(e) for _, _, e in GPX_ELEVATION.findall(path.read_text())]


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in metres between two coordinates."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def bearing(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Initial compass bearing in degrees from one coordinate to another."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lng2 - lng1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


#: The eight points a rider actually says out loud. Sixteen is a chart bearing,
#: not a description of which way a road went.
COMPASS = ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")


def compass(bearing_deg: float) -> str:
    """The eight-point compass word for a bearing."""
    return COMPASS[int((bearing_deg + 22.5) // 45) % 8]


def cumulative(lat: list[float], lng: list[float]) -> list[float]:
    """Metres travelled at each track point, starting at zero."""
    out = [0.0]
    for i in range(1, min(len(lat), len(lng))):
        out.append(out[-1] + haversine(lat[i - 1], lng[i - 1], lat[i], lng[i]))
    return out


def _felt_span(
    dist: list[float], ele: list[float], a: int, b: int, flat_grade: float
) -> tuple[int, int]:
    """Trim ground flatter than `flat_grade` off both ends of a rise.

    The detector finds a rise by walking forward from the first sample that goes
    up at all, so a kilometre of valley floor that drifts up two metres is
    inside the climb and its start point is a kilometre before the pitch. This
    keeps the sub-span that maximises `gain - flat_grade * length`, which is the
    same as saying: ground flatter than `flat_grade` at either end is approach
    or run-out, not climb.

    Args:
        dist: Cumulative metres at each sample.
        ele: Elevation at each sample.
        a: First sample of the detected rise.
        b: Its summit sample.
        flat_grade: The gradient below which ground stops counting, as a fraction.

    Returns:
        The first and last sample of the felt climb.
    """
    best_start, best_value = a, flat_grade * dist[a] - ele[a]
    span, score = (a, b), -math.inf
    for e in range(a + 1, b + 1):
        gain = (ele[e] - ele[best_start]) - flat_grade * (dist[e] - dist[best_start])
        if gain > score:
            span, score = (best_start, e), gain
        value = flat_grade * dist[e] - ele[e]
        if value > best_value:
            best_value, best_start = value, e
    return span


def _steepest(
    dist: list[float], ele: list[float], a: int, b: int, window_m: float
) -> tuple[float, float]:
    """The steepest continuous `window_m` inside a span: its gradient and where.

    Returns:
        Percent gradient and the kilometre it starts at, or (0.0, 0.0) when the
        span is shorter than the window.
    """
    best, at, e = 0.0, 0.0, a
    for s in range(a, b):
        while e < b and dist[e] - dist[s] < window_m:
            e += 1
        run = dist[e] - dist[s]
        if run < window_m * 0.9:
            break
        grade = (ele[e] - ele[s]) / run
        if grade > best:
            best, at = grade, dist[s]
    return round(best * 100, 1), round(at / 1000, 2)


def climbs(
    lat: list[float],
    lng: list[float],
    ele: list[float],
    min_gain_m: float = 60.0,
    max_drop_m: float = 15.0,
    flat_grade: float = 0.01,
) -> list[dict[str, Any]]:
    """Sustained rises in a track: where it climbed, how far, and how steeply.

    Detection is an envelope: a rise of at least `min_gain_m` that never gives
    back `max_drop_m` on the way up. What is reported is the **felt** climb
    inside that envelope, with any approach or run-out flatter than `flat_grade`
    trimmed off, because the envelope's own start is wherever the ground first
    ticked upwards and that can be a kilometre of valley floor before the pitch.
    An envelope can begin 0.98 km and 0.6 m below a climb's real foot, which
    puts its label a kilometre up the road from the climb on the painted map.

    Naming a climb is the label agent's judgement; this says where it is, how
    hard it was, and how it ranks in the session.

    Args:
        lat: Track latitudes.
        lng: Track longitudes.
        ele: Track elevations in metres, the same length.
        min_gain_m: Metres of gain a rise needs before it counts.
        max_drop_m: Metres of give-back that ends one.
        flat_grade: Gradient, as a fraction, below which ground at either end of
            a rise is approach or run-out rather than climb.

    Returns:
        One entry per climb, in the order they were ridden or run, each carrying
        its felt span, its gradient shape, and its rank in the session.
    """
    n = min(len(lat), len(lng), len(ele))
    if n < 3:
        return []
    dist = cumulative(lat[:n], lng[:n])
    spans: list[tuple[int, int, int, int]] = []
    i = 0
    while i < n - 1:
        if ele[i + 1] <= ele[i]:
            i += 1
            continue
        start, peak_ele, peak = i, ele[i], i
        j = i + 1
        while j < n:
            if ele[j] > peak_ele:
                peak_ele, peak = ele[j], j
            elif peak_ele - ele[j] >= max_drop_m:
                break
            j += 1
        if peak_ele - ele[start] >= min_gain_m:
            a, b = _felt_span(dist, ele, start, peak, flat_grade)
            # A trim that eats the climb is a wrong trim: keep the envelope.
            if ele[b] - ele[a] < min_gain_m:
                a, b = start, peak
            spans.append((a, b, start, peak))
            i = peak + 1
        else:
            i += 1
    total_gain = sum(ele[b] - ele[a] for a, b, _s, _p in spans) or 1.0
    out: list[dict[str, Any]] = []
    for a, b, start, peak in spans:
        gain = ele[b] - ele[a]
        length = max(dist[b] - dist[a], 1.0)
        steep_pct, steep_km = _steepest(dist, ele, a, b, 500.0)
        out.append(
            {
                "start_km": round(dist[a] / 1000, 2),
                "end_km": round(dist[b] / 1000, 2),
                "gain_m": round(gain),
                "length_km": round(length / 1000, 2),
                "avg_grade_pct": round(gain / length * 100, 1),
                "steepest_500m_pct": steep_pct,
                "steepest_500m_km": steep_km,
                "bottom_ele_m": round(ele[a]),
                "top_ele_m": round(ele[b]),
                "approach_trimmed_km": round((dist[a] - dist[start]) / 1000, 2),
                "runout_trimmed_km": round((dist[peak] - dist[b]) / 1000, 2),
                "share_of_climbing_pct": round(gain / total_gain * 100),
                "position_pct": round(dist[a] / max(dist[-1], 1.0) * 100),
                "heading": compass(bearing(lat[a], lng[a], lat[b], lng[b])),
                "bearing_deg": round(bearing(lat[a], lng[a], lat[b], lng[b])),
                "start_lat": round(lat[a], 6),
                "start_lng": round(lng[a], 6),
                "end_lat": round(lat[b], 6),
                "end_lng": round(lng[b], 6),
                "_a": a,
                "_b": b,
            }
        )
    by_gain = sorted(out, key=lambda c: -c["gain_m"])
    by_grade = sorted(out, key=lambda c: -c["avg_grade_pct"])
    for climb in out:
        climb["rank_by_gain"] = by_gain.index(climb) + 1
        climb["rank_by_steepness"] = by_grade.index(climb) + 1
        climb["of_climbs"] = len(out)
    return out


# ------------------------------------------------------------------ climb grounding


def _cell_index(ways: list[dict[str, Any]], cell_m: float) -> dict[tuple[int, int], list[int]]:
    """Which ways touch which grid cell, so a point only tests its neighbours."""
    grid: dict[tuple[int, int], list[int]] = {}
    for wi, way in enumerate(ways):
        pts = way["pts"]
        for (ax, ay), (bx, by) in zip(pts, pts[1:], strict=False):
            steps = int(math.hypot(bx - ax, by - ay) // cell_m) + 1
            for s in range(steps + 1):
                t = s / steps
                key = (int((ax + (bx - ax) * t) // cell_m), int((ay + (by - ay) * t) // cell_m))
                bucket = grid.setdefault(key, [])
                if not bucket or bucket[-1] != wi:
                    bucket.append(wi)
    return grid


def _point_to_line(px: float, py: float, pts: list[Pt]) -> float:
    """Metres from a point to a polyline."""
    best = math.inf
    for (ax, ay), (bx, by) in zip(pts, pts[1:], strict=False):
        vx, vy = bx - ax, by - ay
        square = vx * vx + vy * vy
        t = 0.0 if square == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / square))
        best = min(best, math.hypot(px - (ax + t * vx), py - (ay + t * vy)))
    return best


def named_roads(payload: dict[str, Any], proj: Projection) -> list[dict[str, Any]]:
    """Every named or numbered road in the cached OSM payload, projected.

    Overpass already returns these: the map draws them, and the label agent was
    never shown them, which is why a climb could only ever be named after a
    monument that happened to sit near it. A road number is often the most
    honest name a climb has.
    """
    out = []
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        if not tags.get("highway"):
            continue
        name = tags.get("name") or tags.get("ref")
        geom = entry.get("geometry") or []
        if not name or len(geom) < 2:
            continue
        out.append(
            {
                "name": name,
                "ref": tags.get("ref", ""),
                "kind": tags["highway"],
                "pts": [proj(p["lat"], p["lon"]) for p in geom],
            }
        )
    return out


def road_run(
    ways: list[dict[str, Any]],
    grid: dict[tuple[int, int], list[int]],
    track: list[Pt],
    dist: list[float],
    a: int,
    b: int,
    cell_m: float = 200.0,
    snap_m: float = 25.0,
    step_m: float = 50.0,
) -> list[dict[str, Any]]:
    """The named roads one stretch of track actually runs along, in order.

    Args:
        ways: `named_roads` output.
        grid: Its `_cell_index`.
        track: The whole track in metres.
        dist: Cumulative metres per track point.
        a: First sample of the stretch.
        b: Last sample of the stretch.
        cell_m: The index's cell size.
        snap_m: How near a way has to be to count as the road being ridden.
        step_m: How often along the stretch to ask.

    Returns:
        One entry per named road, longest first, with the metres run on it.
    """
    metres: dict[str, float] = {}
    order: list[str] = []
    i, last = a, a
    while i <= b:
        px, py = track[i]
        cx, cy = int(px // cell_m), int(py // cell_m)
        near: set[int] = set()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.update(grid.get((cx + dx, cy + dy), ()))
        best, hit = snap_m, None
        for wi in near:
            gap = _point_to_line(px, py, ways[wi]["pts"])
            if gap < best:
                best, hit = gap, ways[wi]["name"]
        if hit:
            metres[hit] = metres.get(hit, 0.0) + (dist[i] - dist[last])
            if not order or order[-1] != hit:
                order.append(hit)
        last = i
        if i == b:
            break
        while i < b and dist[i] - dist[last] < step_m:
            i += 1
    ranked = sorted(metres.items(), key=lambda kv: -kv[1])
    return [
        {"name": name, "metres": round(run), "order": order.index(name) + 1}
        for name, run in ranked
        if run >= 100
    ]


def route_places(
    payload: dict[str, Any],
    proj: Projection,
    track: list[Pt],
    dist: list[float],
    near_route_m: float = 700.0,
) -> list[dict[str, Any]]:
    """Every settlement the route ran past, in the order it passed them.

    This is the vocabulary a rider uses for a climb: out of one village, up to
    the next. A straight-line nearest place is not that, and picking one is how
    a climb gets named after somewhere the route never went.

    Args:
        payload: The cached Overpass payload.
        proj: The activity's projection.
        track: The track in metres.
        dist: Cumulative metres per track point.
        near_route_m: How near the route a settlement has to come to count.

    Returns:
        One entry per settlement, ordered by where the route came closest to it.
    """
    out = []
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        kind = tags.get("place", "")
        if kind not in ("city", "town", "village", "hamlet", "suburb") or not tags.get("name"):
            continue
        gx, gy = proj(entry["lat"], entry["lon"])
        best, at = math.inf, 0
        for i, (px, py) in enumerate(track):
            gap = math.hypot(px - gx, py - gy)
            if gap < best:
                best, at = gap, i
        if best > near_route_m:
            continue
        out.append(
            {
                "name": tags["name"],
                "kind": kind,
                "km": round(dist[at] / 1000, 2),
                "off_route_m": round(best),
                "lat": entry["lat"],
                "lng": entry["lon"],
                "_at": at,
            }
        )
    out.sort(key=lambda p: p["_at"])
    return out


def _place_view(
    place: dict[str, Any], keys: tuple[str, ...] = ("name", "kind", "km", "off_route_m")
) -> dict[str, Any]:
    """One settlement as the label agent sees it, without the track index."""
    return {k: place[k] for k in keys}


def _near_places(
    places: list[dict[str, Any]], plat: float, plng: float, keep: int = 3
) -> list[dict[str, Any]]:
    """The nearest settlements to one point, with how far and which way."""
    ranked = sorted(
        ((haversine(plat, plng, p["lat"], p["lng"]), p) for p in places), key=lambda row: row[0]
    )[:keep]
    return [
        {
            "name": p["name"],
            "kind": p["kind"],
            "distance_m": round(gap),
            "direction": compass(bearing(plat, plng, p["lat"], p["lng"])),
        }
        for gap, p in ranked
    ]


def ground_climbs(
    climbs_: list[dict[str, Any]],
    places: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    ways: list[dict[str, Any]],
    track: list[Pt],
    dist: list[float],
    feature_m: float = 600.0,
    foot_m: float = 300.0,
) -> None:
    """Give every climb the language a rider would use for it, in place.

    Four grounds, in the order they are worth having: where the route was before
    the climb and where it got to after it (`from`, `through`, `to`), the roads
    the climb runs on, the settlements nearest each end whichever way the route
    went, and any named feature beside the climb itself. None of them is a
    template to fill in. A climb with nothing but `from` and `to` is still
    nameable; a climb with none of them is honestly nameless and says so.

    Every one of these carries its own distance, and that is the point:
    `from.km_before_climb` says how far back the route was when it passed that
    settlement, so a settlement kilometres behind the foot cannot be read as
    where the climb starts. Naming a climb after the last town the route went
    through, whatever the distance, is the error this block exists to stop.

    Args:
        climbs_: `climbs()` output, mutated.
        places: `route_places()` output.
        candidates: `journal_candidates()` output.
        ways: `named_roads()` output.
        track: The track in metres.
        dist: Cumulative metres per track point.
        feature_m: How near a climb a named feature has to be to be offered.
        foot_m: A settlement this near the foot or the top, measured along the
            route, belongs to that end rather than to the middle of the climb.
            A village at the bottom of a hill is what the climb is out of, and a
            few metres either side of the first pedal stroke should not decide
            that. `km_before_climb` and `km_after_top` go slightly negative when
            it does, which is the honest reading: the route reached it just
            inside the climb.
    """
    grid = _cell_index(ways, 200.0) if ways else {}
    for climb in climbs_:
        a, b = climb.pop("_a"), climb.pop("_b")
        foot, top = dist[a] + foot_m, dist[b] - foot_m
        before = [p for p in places if dist[p["_at"]] <= foot]
        inside = [p for p in places if foot < dist[p["_at"]] < top]
        after = [p for p in places if dist[p["_at"]] >= top]
        climb["from"] = (
            {
                **_place_view(before[-1]),
                "km_before_climb": round((dist[a] - dist[before[-1]["_at"]]) / 1000, 2),
            }
            if before
            else None
        )
        climb["through"] = [_place_view(p) for p in inside]
        climb["to"] = (
            {
                **_place_view(after[0]),
                "km_after_top": round((dist[after[0]["_at"]] - dist[b]) / 1000, 2),
            }
            if after
            else None
        )
        climb["near_start"] = _near_places(places, climb["start_lat"], climb["start_lng"])
        climb["near_top"] = _near_places(places, climb["end_lat"], climb["end_lng"])
        climb["roads"] = road_run(ways, grid, track, dist, a, b) if ways else []
        stretch = track[a : b + 1] or track[a : a + 1]
        features = []
        for cand in candidates:
            if cand["class"] == "place" or cand["x"] is None:
                continue
            gap = min(math.hypot(cand["x"] - px, cand["y"] - py) for px, py in stretch)
            if gap <= feature_m:
                features.append(
                    {"name": cand["name"], "class": cand["class"], "distance_m": round(gap)}
                )
        features.sort(key=lambda f: f["distance_m"])
        climb["features"] = features[:4]


#: Metres of ground kept around the track's bounding box for the candidates.
CANDIDATE_CLIP_MARGIN_M = 2600.0


def candidate_basemap() -> BasemapStyle:
    """What `landmark_export` draws: every landmark, no relief, no generalisation."""
    from pyntpot.maps.style_groups import BasemapStyle

    return replace(
        BasemapStyle(),
        hillshade_mode="off",
        landmarks="all",
        landmark_max=LANDMARK_CAP,
        generalise=False,
    )


def landmark_export(
    key: str,
    lat: list[float],
    lng: list[float],
    ele: list[float] | None = None,
    style: Any = None,
    route: list[Pt] | None = None,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
) -> dict[str, Any]:
    """What the label agent reads: where the session went, and what is beside it.

    Nothing here chooses a landmark. It states what the box holds, where the
    session climbed, how hard each climb was and what the route passed on the
    way up it; which of them is worth a label, and what to call it, is the
    agent's judgement and is written back into the payload.

    Args:
        key: The activity, naming the cache files.
        lat: Track latitudes.
        lng: Track longitudes.
        ele: Track elevations, when the GPX carries them.
        style: A `paint.PaintStyle`, for the card the candidates are inside.
        route: The already-projected track, when the caller has one.
        cache_dir: Where the cached payloads live.
        places: User-supplied places of interest.

    Returns:
        `route` (the session's totals and the settlements it passed, in order),
        `climbs` (each grounded in that route) and `candidates`.
    """
    from pyntpot.maps.projection import track_projection

    proj, pts = track_projection(lat, lng, route)
    dist = cumulative(lat, lng)
    found = climbs(lat, lng, ele or [])
    out: dict[str, Any] = {
        "id": key,
        "points": len(lat),
        "route": {
            "total_km": round(dist[-1] / 1000, 2) if dist else 0.0,
            # Not the session's ascent: raw GPX sample-to-sample gain runs well
            # above the recorded figure, so the only climbing figure stated here
            # is the one this module actually defines.
            "sustained_ascent_m": round(sum(c["gain_m"] for c in found)),
            "settlements": [],
        },
        "climbs": found,
        "candidates": [],
    }
    base = basemap(
        key,
        lat,
        lng,
        options=candidate_basemap(),
        cache_dir=cache_dir,
        places=places,
        route=simplify(pts, 3.0),
        clip_margin_m=CANDIDATE_CLIP_MARGIN_M,
    )
    if base is not None:
        out["candidates"] = journal_candidates(base, proj)
    payload_path = overpass_path(key, cache_dir)
    if payload_path.exists():
        payload = json.loads(payload_path.read_text())
        places = route_places(payload, proj, pts, dist)
        out["route"]["settlements"] = [
            _place_view(p, ("name", "kind", "km", "off_route_m")) for p in places
        ]
        ground_climbs(found, places, out["candidates"], named_roads(payload, proj), pts, dist)
    else:
        for climb in found:
            climb.pop("_a", None)
            climb.pop("_b", None)
    return out
