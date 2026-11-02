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

from pyntpot.ink.polyline import Pt, foot_on
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

#: The fewest points that make a ring.
_FEWEST_FOR_A_RING = 3


@dataclass(frozen=True)
class Water:
    """The lakes and watercourses a name is priced against, in display pixels.

    Attributes:
        lakes: The inland water rings.
        strokes: Each watercourse's line and the half width it is painted at.
        lake_boxes: The box each lake ring covers.
        stroke_boxes: The box each stroke covers, its width included.
    """

    lakes: list[list[Pt]] = field(default_factory=list)
    strokes: list[tuple[list[Pt], float]] = field(default_factory=list)
    #: The box each lake ring covers, in the order of `lakes`; worked out once.
    lake_boxes: list[Box] = field(init=False, repr=False)
    #: The box each stroke covers with its width, in the order of `strokes`.
    stroke_boxes: list[Box] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Work out the boxes the lakes and strokes cover, once."""
        object.__setattr__(self, "lake_boxes", [_extent(ring, 0.0) for ring in self.lakes])
        object.__setattr__(
            self, "stroke_boxes", [_extent(line, half) for line, half in self.strokes]
        )


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
    lakes = [
        ring for ring, ext in zip(water.lakes, water.lake_boxes, strict=True) if _meets(ext, grown)
    ]
    strokes = [
        stroke
        for stroke, ext in zip(water.strokes, water.stroke_boxes, strict=True)
        if _meets(ext, grown)
    ]
    if not lakes and not strokes:
        return 0.0
    points = _samples(grown)
    wet = sum(1 for p in points if _in_lake(p, lakes) or _on_stroke(p, strokes))
    return wet / len(points)


def _extent(line: list[Pt], pad: float) -> Box:
    """The box a line covers, grown by `pad` on every side."""
    xs = [x for x, _y in line]
    ys = [y for _x, y in line]
    return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)


def _meets(a: Box, b: Box) -> bool:
    """Whether two boxes share any area."""
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _samples(box: Box) -> list[Pt]:
    """Points spread evenly over a box, at most `_SAMPLE_STEP_PX` apart, edges included."""
    x0, y0, x1, y1 = box
    nx = max(math.ceil((x1 - x0) / _SAMPLE_STEP_PX), 1) + 1
    ny = max(math.ceil((y1 - y0) / _SAMPLE_STEP_PX), 1) + 1
    return [
        (x0 + (x1 - x0) * i / (nx - 1), y0 + (y1 - y0) * j / (ny - 1))
        for i in range(nx)
        for j in range(ny)
    ]


def _in_lake(p: Pt, rings: list[list[Pt]]) -> bool:
    """Whether a point is on a lake: inside an odd number of the rings."""
    x, y = p
    inside = False
    for ring in rings:
        for (ax, ay), (bx, by) in itertools.pairwise([*ring, ring[0]]):
            if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                inside = not inside
    return inside


def _on_stroke(p: Pt, strokes: list[tuple[list[Pt], float]]) -> bool:
    """Whether a point lies under one of the strokes, within its half width."""
    return any(foot_on(p, line)[0] <= half for line, half in strokes)
