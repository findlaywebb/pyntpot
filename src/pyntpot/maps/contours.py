"""Contours of an elevation grid: marching squares, contour lines and the shoreline.

Key names: `marching_squares`, the polylines of one level in fractional grid space;
`contour_lines`, sparse smoothed contours at one interval as path data;
`sea_rings`, the water and island rings traced where the grid meets sea level.

SRTM reports the sea as exactly zero, so the shoreline is traced on a mask of "at
or below sea level" and not on the elevation. It does not fetch elevations, shade
terrain or choose which levels to draw. Invariants: a traced ring comes back with
its first and last point equal, and every sea region is a closed loop because the
mask is padded with a ring of dry ground first.
"""

import math
from typing import Any

from pyntpot.ink.chains import join_chains
from pyntpot.ink.polyline import Pt, simplify, smooth
from pyntpot.maps.projection import Projection
from pyntpot.maps.rings import Rings, point_in_ring
from pyntpot.maps.svg_path import path_d

#: The fewest points a traced contour needs to be drawn.
CONTOUR_MIN_POINTS = 3

#: The fewest points a traced loop needs to be a ring at all.
LOOP_MIN_POINTS = 4

#: The fewest points a simplified shoreline needs to be kept.
SHORE_MIN_POINTS = 4


def marching_squares(grid: list[list[float]], level: float) -> list[list[Pt]]:
    """Contour polylines for one level, in fractional (column, row) grid space.

    Source: `marching-squares` in docs/explanation/references.md.

    Args:
        grid: Rows of samples, row 0 southernmost.
        level: The value to trace.

    Returns:
        Polylines; a ring comes back with its first and last point equal.
    """
    rows, cols = len(grid), len(grid[0])
    segs: list[tuple[Pt, Pt]] = []

    def interp(a: float, b: float) -> float:
        """Where `level` falls between two samples, as a share of the way from `a` to `b`."""
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
        """A point rounded to four decimals, so two segment ends that meet compare equal."""
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
    """Map a polyline in fractional grid space to card metres.

    Args:
        line: Points as (column, row), possibly fractional.
        lats: Grid latitudes, ascending.
        lons: Grid longitudes, ascending.
        proj: The track's projection.
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
    return [edge, *[[value, *row, value] for row in grid], edge]


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
        proj: The track's projection.
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
            if len(metres) >= CONTOUR_MIN_POINTS:
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
        proj: The track's projection.
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
        if len(ring) < LOOP_MIN_POINTS:
            continue
        wet = _ring_is_wet(ring, padded, 0.5)
        metres = _grid_line_to_metres(ring, lats, lons, proj, pad=1)
        metres = simplify(smooth(metres, passes=2, closed=True), eps)
        if len(metres) >= SHORE_MIN_POINTS:
            (water if wet else islands).append(metres)
    return water, islands


def _ring_is_wet(ring: list[Pt], padded: list[list[float]], level: float) -> bool:
    """True when at least half the cells a ring encloses are at or above `level`."""
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
