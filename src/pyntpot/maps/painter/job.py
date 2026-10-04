"""The two values that cross the painter's phases: the job and the plate stack.

Key types: `PaintJob`, what one painting is made from (the basemap, the style, the
paper sheet, the plate's canvas, the output directory and the seeded random
generators the phases share), and `PlateStack`, the mutable accumulator of the
arrays one phase writes and a later one reads, plus the files written and their
sizes. `drawable` turns basemap lines into the point lists the painter fills and
strokes.

The generators are shared down a sequence of items on purpose: each phase draws
from its generator in the order the painting has always drawn, so a generator's
state at any point is what it has always been. `PaintJob.begin` builds them from
the style's seeds; a generator a style switches off is `None` or never drawn from.

`PaintJob` also states the options every wash on the plate is laid with (the
granulation, the flow rim, the rim width and the bloom of one wash), because they
are derived from the card and the style once and must be the same for each wash.

It paints nothing itself and never imports `_port`. A `PlateStack` has no meaning
until `paint_water` has filled its coverage.

Invariants: a job never changes once built; the stack's arrays all have the
plate's `(rows, columns)` shape.
"""

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Self

import numpy as np

from pyntpot.ink.noise import F32
from pyntpot.ink.pigment import Layer
from pyntpot.ink.sheet import Canvas, Sheet
from pyntpot.ink.wash import Blooms
from pyntpot.maps.basemap import Basemap, Layers, Line
from pyntpot.maps.style import Style

Pt = tuple[float, float]

#: Coverage above this is inside a wash.
INSIDE = 0.5

#: The fewest points a line needs to be drawn.
_MIN_POINTS = 2
#: A bloom's count grows with the square root of the wash's area over this many pixels.
_BLOOM_AREA_PX = 260.0
#: Below this many pixels of area a wash carries no bloom unless the count says so.
_BLOOM_FLOOR_AREA = 400


def drawable(lines: tuple[Line, ...]) -> list[list[Pt]]:
    """The lines long enough to draw, as the point lists the painter fills and strokes."""
    return [list(line) for line in lines if len(line) >= _MIN_POINTS]


@dataclass(frozen=True)
class PaintJob:
    """One painting: what is painted, how, and the generators its phases share.

    Attributes:
        basemap: The basemap being painted.
        style: The style the plates are painted in.
        sheet: The paper's noise fields at the plate's size.
        canvas: The plate's pixel grid over the card's box.
        out_dir: Where the plates are written.
        bloom_rng: Places the blooms of every wash in turn; `None` when blooms are off.
        deform_rng: Deforms every cover ring in turn.
        dither_rng: Drives the wood's textures and dabs, then the plates' dither.
        ink_rng: Lays every watercourse and road in turn.
        pen_rng: Lays the route's pen plate.
    """

    basemap: Basemap
    style: Style
    sheet: Sheet
    canvas: Canvas
    out_dir: Path
    bloom_rng: np.random.Generator | None
    deform_rng: np.random.Generator
    dither_rng: np.random.Generator
    ink_rng: np.random.Generator
    pen_rng: np.random.Generator

    @classmethod
    def begin(cls, basemap: Basemap, style: Style, out_dir: Path) -> Self:
        """Build the job for one painting: the canvas, the sheet and the seeded generators."""
        card = basemap.card
        cx0, cy0, cx1, cy1 = card.box
        rw, rh = card.render
        paper = style.paper
        sheet = Sheet(
            rh,
            rw,
            gran_px=max(basemap.layers.gran_m / card.mpp, 3.0),
            seed=paper.sheet_seed,
            fibre=paper.paper_fibre_mix if paper.paper_fibre else 0.0,
            fibre_stretch=paper.paper_fibre_stretch,
            fibre_angle=paper.paper_fibre_angle,
            fibre_cell=max(paper.paper_fibre_cell_px * rw / 1800.0, 1.6),
        )
        wash = style.wash
        return cls(
            basemap=basemap,
            style=style,
            sheet=sheet,
            canvas=Canvas(cx0, cy0, cx1, cy1, rw, rh),
            out_dir=out_dir,
            bloom_rng=np.random.default_rng(wash.bloom_seed) if wash.blooms else None,
            deform_rng=np.random.default_rng(wash.silhouette_deform_seed),
            dither_rng=np.random.default_rng(style.cover.dither_seed),
            ink_rng=np.random.default_rng(style.brush.ink_seed),
            pen_rng=np.random.default_rng(style.brush.ink_seed + 1),
        )

    @property
    def layers(self) -> Layers:
        """The basemap's layers."""
        return self.basemap.layers

    @property
    def mpp(self) -> float:
        """Metres per render pixel."""
        return self.basemap.card.mpp

    @property
    def shape(self) -> tuple[int, int]:
        """The plate's rows and columns."""
        rw, rh = self.basemap.card.render
        return rh, rw

    @property
    def scale(self) -> float:
        """Render pixels per display pixel."""
        card = self.basemap.card
        return card.render[0] / max(card.display[0], 1)

    @property
    def gran_gamma(self) -> float:
        """The granulation gamma every wash on the plate is laid with."""
        paper = self.style.paper
        return paper.gran_gamma if paper.paper_fibre else 0.0

    @property
    def flow(self) -> tuple[float, float, float] | None:
        """The flow-rim option every wash is laid with, or `None` when it is off."""
        wash = self.style.wash
        if not wash.flow_rim:
            return None
        return (wash.flow_rim_exp, wash.flow_rim_ref_frac, wash.flow_rim_frac)

    @property
    def rim_cov(self) -> float:
        """The pooled rim of a cover wash, in pixels."""
        return max(5.0, 90.0 / self.mpp)

    def transp(self, key: str) -> float:
        """What this pigment shows over black, as a share of over white."""
        paper = self.style.paper
        return float(paper.pigment_transparency.get(key, paper.km_transparency))

    def bloom(self, cov: np.ndarray) -> Blooms | None:
        """The bloom argument for one wash, sized against its own area.

        `bloom_strength` scales the lift, which is the one number the whole
        bloom is built from: the centre gives up that share of its pigment and
        the ridge is laid from what the centre gave up. So one multiplier
        turns a demonstration of a backrun into a mark on the paper.
        """
        wash = self.style.wash
        if self.bloom_rng is None or wash.bloom_density <= 0:
            return None
        area = float((cov > INSIDE).sum())
        n = int(
            np.clip(
                round(wash.bloom_density * math.sqrt(area) / _BLOOM_AREA_PX),
                1 if area > _BLOOM_FLOOR_AREA else 0,
                wash.bloom_max,
            )
        )
        lift = wash.bloom_lift * max(wash.bloom_strength, 0.0)
        if not n:
            return None
        return (self.bloom_rng, n, wash.bloom_radius_frac, lift, wash.bloom_warp)


@dataclass
class PlateStack:
    """The arrays one phase writes and a later one reads, and what has been written.

    Attributes:
        sea_cov: The sea's coverage, in 0 to 1.
        lake_cov: The lakes' coverage, in 0 to 1.
        water: Where either is wet.
        label: One land-cover class index per pixel, 0 where there is none.
        wood_mask: Where the wood class is.
        trimmed: The pigment layers the ribbon trims, in laying order.
        files: The plate file name by plate name.
        sizes: The plate byte count by plate name.
    """

    sea_cov: np.ndarray
    lake_cov: np.ndarray
    water: np.ndarray
    label: np.ndarray
    wood_mask: np.ndarray
    trimmed: list[Layer] = field(default_factory=list)
    files: dict[str, str] = field(default_factory=dict)
    sizes: dict[str, int] = field(default_factory=dict)

    @classmethod
    def blank(cls, shape: tuple[int, int]) -> Self:
        """A stack with nothing painted: empty coverage and masks of the plate's shape."""
        return cls(
            sea_cov=np.zeros(shape, F32),
            lake_cov=np.zeros(shape, F32),
            water=np.zeros(shape, bool),
            label=np.zeros(shape, np.uint8),
            wood_mask=np.zeros(shape, bool),
        )
