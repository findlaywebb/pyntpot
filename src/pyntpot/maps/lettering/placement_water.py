"""The water a name and its backing wash keep off: the lakes and the watercourses' strokes.

Key names: `Water`, the lake rings and the watercourse strokes in display pixels, with
the box each covers; `water_from`, which builds it from a basemap; `on_water`, the share
of a name's box, grown by the reach of its backing wash, that lies on water;
`water_cost`, what that share and the water under the letters cost; `WATER_COST`,
`WATER_UNDER_COST` and `UNDER_FULL_SHARE`, the prices; `WASH_REACH_EM`, how far round a name its
backing wash reaches.

It does not choose a position and does not move a box. It prices water for a name set
flat; a name written on the water, or set along its own line, is not priced here.

Invariants: `on_water` is a share between 0 and 1; an empty `Water` prices nothing; a
lake is read by the even-odd rule over its rings, so an island in a lake is dry.
"""

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

from pyntpot.ink.polyline import Pt
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.lettering.label import Box

#: How far round a name its backing wash reaches, in ems of the name's size. The
#: wash lifts the paper's colour over whatever it lands on, so a name whose wash
#: lands on a lake washes that part of the lake out: a lake under the wash is
#: as much a fault as a lake under the letters. The nib's default
#: `label_wash_spread`.
WASH_REACH_EM = 0.75

#: What a box wholly on water costs, against `ROAD_CROSS_COST` (90) for a road
#: under a name and 400 for a seat off the paper. A letter on a lake is hidden
#: by it and the lake is washed out by the name's backing, so a fifth of a box on
#: water is already dearer than a road under it.
WATER_COST = 480.0

#: What any water under the letters themselves costs on top of `WATER_COST`'s
#: share, so a name moves a rung further out rather than lose a letter to a lake.
WATER_UNDER_COST = 160.0

#: The share of a name's ink on water that costs the whole of `WATER_UNDER_COST`:
#: a tenth of the letters is a letter lost. Less costs in proportion, so a pond
#: grazing one serif does not outweigh a seat a long leader away.
UNDER_FULL_SHARE = 0.1

#: How much wider than its ink a name's box is, in ems: `box_size`'s padding.
BOX_PAD_EM = 0.5

#: How far apart the points a box is sampled at are, at most, in display pixels.
_SAMPLE_STEP_PX = 4.0

#: A segment this short, squared, is a point: `polyline.foot_on`'s threshold.
_DEGENERATE_AREA = 1e-12

#: The fewest points that make a ring.
_FEWEST_FOR_A_RING = 3


@dataclass(frozen=True)
class Water:
    """The lakes and watercourses a name is priced against, in display pixels.

    The rings and strokes are also held as flat arrays of their edges and segments,
    worked out once, so a box is priced against all of them in a few array
    operations rather than point by point.

    Attributes:
        lakes: The inland water rings.
        strokes: Each watercourse's line and the half width it is painted at.
        lake_boxes: The box each lake ring covers, one row a ring.
        stroke_boxes: The box each stroke covers, its width included, one row a stroke.
        edges: Every lake ring's edges, closing edge included: `ax, ay, bx, by, ring`.
        segments: Every stroke's segments: `ax, ay, bx, by, half, stroke`, then the box
            the segment reaches with its half width, `x0, y0, x1, y1`.
        reach: One cell a display pixel, set where some segment's reach box covers
            it, from `reach_origin`: a point in a cell not set is under no stroke, so
            only the points in set cells are measured.
        reach_origin: The display pixel the first cell of `reach` starts at.
    """

    lakes: list[list[Pt]] = field(default_factory=list)
    strokes: list[tuple[list[Pt], float]] = field(default_factory=list)
    lake_boxes: np.ndarray = field(init=False, repr=False)
    stroke_boxes: np.ndarray = field(init=False, repr=False)
    edges: np.ndarray = field(init=False, repr=False)
    segments: np.ndarray = field(init=False, repr=False)
    reach: np.ndarray = field(init=False, repr=False)
    reach_origin: tuple[int, int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Work out the boxes, edges and segments of the lakes and strokes, once."""
        lake_boxes = [_extent(ring, 0.0) for ring in self.lakes]
        stroke_boxes = [_extent(line, half) for line, half in self.strokes]
        edges = [
            (*a, *b, k)
            for k, ring in enumerate(self.lakes)
            for a, b in zip(ring, [*ring[1:], ring[0]], strict=True)
        ]
        segments = [
            (*a, *b, half, k, *_extent([a, b], half))
            for k, (line, half) in enumerate(self.strokes)
            for a, b in itertools.pairwise(line)
        ]
        object.__setattr__(self, "lake_boxes", np.array(lake_boxes, float).reshape(-1, 4))
        object.__setattr__(self, "stroke_boxes", np.array(stroke_boxes, float).reshape(-1, 4))
        object.__setattr__(self, "edges", np.array(edges, float).reshape(-1, 5))
        object.__setattr__(self, "segments", np.array(segments, float).reshape(-1, 10))
        self._grid_reach()

    def _grid_reach(self) -> None:
        """Mark every display pixel some segment's reach box covers, once."""
        boxes = self.segments[:, 6:10]
        if not boxes.size:
            object.__setattr__(self, "reach", np.zeros((0, 0), bool))
            object.__setattr__(self, "reach_origin", (0, 0))
            return
        ox, oy = math.floor(boxes[:, 0].min()), math.floor(boxes[:, 1].min())
        cells = np.floor(boxes - (ox, oy, ox, oy)).astype(int)
        grid = np.zeros((cells[:, 3].max() + 1, cells[:, 2].max() + 1), bool)
        for cx0, cy0, cx1, cy1 in cells.tolist():
            grid[cy0 : cy1 + 1, cx0 : cx1 + 1] = True
        object.__setattr__(self, "reach", grid)
        object.__setattr__(self, "reach_origin", (ox, oy))

    def near_stroke(self, xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
        """Which points lie in a cell some segment's reach box covers."""
        ox, oy = self.reach_origin
        cx = np.floor(xs - ox).astype(int)
        cy = np.floor(ys - oy).astype(int)
        rows, cols = self.reach.shape
        inside = (cx >= 0) & (cx < cols) & (cy >= 0) & (cy < rows)
        out = np.zeros(xs.shape, bool)
        out[inside] = self.reach[cy[inside], cx[inside]]
        return out


def water_from(basemap: Basemap) -> Water:
    """The basemap's lakes and watercourse strokes, moved into display pixels."""
    card = basemap.card
    layers = basemap.layers
    lakes = [[card.xy(x, y) for x, y in ring] for ring in layers.lakes]
    strokes = [
        ([card.xy(x, y) for x, y in river.line], river.width_px / 2)
        for river in layers.rivers
        if len(river.line) > 1
    ]
    return Water(
        [ring for ring in lakes if len(ring) >= _FEWEST_FOR_A_RING],
        [(line, half) for line, half in strokes if len(line) > 1],
    )


def water_cost(box: Box, water: Water, size: float) -> float:
    """What the water under a name and its backing wash costs it.

    `WATER_COST` for each share of the grown box on water, and up to
    `WATER_UNDER_COST` more for water under the letters themselves, in full once
    `UNDER_FULL_SHARE` of the ink lies on it: a sliver of wash on a stream's edge
    is a small fault, a letter on the water is a hidden letter.
    """
    share = on_water(box, water, size)
    if share == 0.0:
        return 0.0
    # The letters, not the box: a box is half an em wider than its ink.
    inset = min(size * BOX_PAD_EM / 2, (box[2] - box[0]) / 2)
    ink = (box[0] + inset, box[1], box[2] - inset, box[3])
    under = on_water(ink, water, 0.0)
    return share * WATER_COST + WATER_UNDER_COST * min(under / UNDER_FULL_SHARE, 1.0)


def on_water(box: Box, water: Water, size: float) -> float:
    """The share of a box, grown by its backing wash's reach, that lies on water.

    Args:
        box: The name's box.
        water: The lakes and strokes.
        size: The name's type size, which sets how far its backing wash reaches.

    Returns:
        A share between 0 and 1 of points sampled evenly over the grown box.
    """
    if not water.lakes and not water.strokes:
        return 0.0
    pad = size * WASH_REACH_EM
    grown = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
    rings = _meets(water.lake_boxes, grown)
    strokes = _meets(water.stroke_boxes, grown)
    if not rings.any() and not strokes.any():
        return 0.0
    xs, ys = _samples(grown)
    wet = _in_lake(xs, ys, water.edges, rings)
    if strokes.any():
        near = water.near_stroke(xs, ys) & ~wet
        if near.any():
            wet[near] = _on_stroke(xs[near], ys[near], water.segments, strokes, grown)
    return float(np.count_nonzero(wet)) / xs.size


def _extent(line: list[Pt], pad: float) -> Box:
    """The box a line covers, grown by `pad` on every side."""
    xs = [x for x, _y in line]
    ys = [y for _x, y in line]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _meets(boxes: np.ndarray, b: Box) -> np.ndarray:
    """Which of the boxes, one a row, share any area with a box."""
    return (boxes[:, 0] < b[2]) & (b[0] < boxes[:, 2]) & (boxes[:, 1] < b[3]) & (b[1] < boxes[:, 3])


def _samples(box: Box) -> tuple[np.ndarray, np.ndarray]:
    """Points spread evenly over a box, at most `_SAMPLE_STEP_PX` apart, edges included."""
    x0, y0, x1, y1 = box
    nx = max(math.ceil((x1 - x0) / _SAMPLE_STEP_PX), 1) + 1
    ny = max(math.ceil((y1 - y0) / _SAMPLE_STEP_PX), 1) + 1
    i, j = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    return (x0 + (x1 - x0) * i.ravel() / (nx - 1), y0 + (y1 - y0) * j.ravel() / (ny - 1))


def _in_lake(xs: np.ndarray, ys: np.ndarray, edges: np.ndarray, rings: np.ndarray) -> np.ndarray:
    """Which points are on a lake: inside an odd number of the rings marked, by their edges."""
    if not rings.any():
        return np.zeros(xs.shape, bool)
    mine = edges[rings[edges[:, 4].astype(int)]]
    ax, ay, bx, by = (mine[:, k][None, :] for k in range(4))
    x, y = xs[:, None], ys[:, None]
    spans = (ay > y) != (by > y)
    rise = np.broadcast_to(by - ay, spans.shape)
    cut = np.divide((y - ay) * (bx - ax), rise, out=np.zeros(spans.shape), where=spans)
    crossings = spans & (x < ax + cut)
    return np.count_nonzero(crossings, axis=1) % 2 == 1


def _on_stroke(
    xs: np.ndarray, ys: np.ndarray, segments: np.ndarray, strokes: np.ndarray, near: Box
) -> np.ndarray:
    """Which points lie under one of the strokes marked, within its half width.

    Only the segments that could reach the box `near` are measured: a point
    within half a stroke's width of a segment lies inside that segment's box
    grown by the half width.
    """
    if not strokes.any():
        return np.zeros(xs.shape, bool)
    lo_x, lo_y, hi_x, hi_y = (segments[:, k] for k in range(6, 10))
    reach = (lo_x <= near[2]) & (near[0] <= hi_x) & (lo_y <= near[3]) & (near[1] <= hi_y)
    seg = segments[reach & strokes[segments[:, 5].astype(int)]]
    if not seg.size:
        return np.zeros(xs.shape, bool)
    ax, ay, bx, by, half = (seg[:, k][None, :] for k in range(5))
    vx, vy = bx - ax, by - ay
    run = vx * vx + vy * vy
    flat = run <= _DEGENERATE_AREA
    px, py = xs[:, None], ys[:, None]
    dot = (px - ax) * vx + (py - ay) * vy
    t = np.divide(dot, np.broadcast_to(run, dot.shape), out=np.zeros(dot.shape), where=~flat)
    t = np.clip(t, 0.0, 1.0)
    dx = px - (ax + t * vx)
    dy = py - (ay + t * vy)
    return np.any(np.hypot(dx, dy) <= half, axis=1)
