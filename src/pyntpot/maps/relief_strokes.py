"""Hand-drawn relief strokes: hachures down the slopes and waves over the sea.

Key names: `Field`, the elevation grid sampled in card metres; `Hatching`, the
spacing, slope threshold, length and track buffer of a hachure field; `hachures`,
lines of descent grouped by weight; `wave_strokes`, sparse S-curves over water.

Both strokes are drawn in metres, not in grid cells, so both ask the terrain a
question at an arbitrary point. It does not fetch elevations, shade terrain or
decide which strokes a page wants. Invariants: the jitter is repeatable, so two
builds of the same map draw the same strokes, and no hachure starts or runs within
the buffer of the track.
"""

import math
from dataclasses import dataclass
from typing import Any

from pyntpot.ink.polyline import Pt
from pyntpot.maps.projection import Projection
from pyntpot.maps.svg_path import stroke_d
from pyntpot.maps.track_index import TrackIndex

#: The fewest points a hachure needs to be drawn.
MIN_STROKE_POINTS = 2


@dataclass(frozen=True)
class Hatching:
    """How a field of hachures is laid out.

    Attributes:
        spacing_m: Metres between seeds.
        min_slope: Gradient below which no stroke is drawn.
        max_length_m: The longest a stroke gets, on the steepest ground.
        buffer_m: Metres of clear paper kept either side of the track.
        steps: Integration steps per stroke.
        buckets: How many opacity levels the strokes are grouped into, so the
            layer ships as a handful of paths rather than a thousand.
    """

    spacing_m: float = 55.0
    min_slope: float = 0.035
    max_length_m: float = 90.0
    buffer_m: float = 40.0
    steps: int = 5
    buckets: int = 4


DEFAULT_HATCHING = Hatching()


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

    def slope(self, x: float, y: float) -> tuple[Pt, float]:
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


def _near_track(index: TrackIndex | None, x: float, y: float, buffer_m: float) -> bool:
    """True when the track is within the buffer of a point."""
    return index is not None and index.distance(x, y, cap_m=buffer_m + 1) <= buffer_m


def _descent(
    x: float,
    y: float,
    length: float,
    field: Field,
    index: TrackIndex | None,
    hatching: Hatching,
) -> list[Pt]:
    """The line a stroke walks downhill from a seed, stopping at the track buffer."""
    line = [(x, y)]
    px, py = x, y
    steps = hatching.steps
    for _ in range(steps):
        (dx, dy), grad = field.slope(px, py)
        norm = math.hypot(dx, dy)
        if norm == 0 or grad < hatching.min_slope * 0.6:
            break
        px += dx / norm * (length / steps)
        py += dy / norm * (length / steps)
        if _near_track(index, px, py, hatching.buffer_m):
            break
        line.append((px, py))
    return line


def _stroke_at(
    i: int,
    j: int,
    clip: tuple[float, float, float, float],
    field: Field,
    index: TrackIndex | None,
    hatching: Hatching,
) -> tuple[float, list[Pt]] | None:
    """The weight and line of the hachure seeded in one cell, or None for none."""
    xmin, ymin, xmax, ymax = clip
    spacing_m = hatching.spacing_m
    jx, jy = _jitter(i, j)
    x = xmin + (i + 0.5 + jx * 0.8) * spacing_m
    y = ymin + (j + 0.5 + jy * 0.8) * spacing_m
    if not (xmin <= x <= xmax and ymin <= y <= ymax):
        return None
    _, grad = field.slope(x, y)
    min_slope = hatching.min_slope
    if grad < min_slope or _near_track(index, x, y, hatching.buffer_m):
        return None
    weight = min(1.0, (grad - min_slope) / max(min_slope * 3.0, 1e-6))
    length = hatching.max_length_m * (0.35 + 0.65 * weight)
    line = _descent(x, y, length, field, index, hatching)
    if len(line) < MIN_STROKE_POINTS or math.dist(line[0], line[-1]) < spacing_m * 0.15:
        return None
    return weight, line


def hachures(
    field: Field,
    clip: tuple[float, float, float, float],
    index: TrackIndex | None = None,
    hatching: Hatching = DEFAULT_HATCHING,
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
        hatching: Spacing, slope threshold, length, buffer and weight levels.

    Returns:
        One entry per weight, `{"o": opacity, "d": path}`, lightest first.
    """
    xmin, ymin, xmax, ymax = clip
    buckets = hatching.buckets
    groups: list[list[str]] = [[] for _ in range(buckets)]
    cols = int((xmax - xmin) / hatching.spacing_m) + 1
    rows = int((ymax - ymin) / hatching.spacing_m) + 1
    for j in range(rows):
        for i in range(cols):
            found = _stroke_at(i, j, clip, field, index, hatching)
            if found is not None:
                weight, line = found
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
