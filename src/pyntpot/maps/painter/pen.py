"""The pen phase: the watercourses, the coast and the roads laid as ink, and the route's own plate.

Key names: `paint_pen`, which lays every watercourse and the coast into one pad and each
road band into a pad of its own, and returns the ink layers the page lays over the
ribbon untrimmed; and `paint_route_pen`, which draws the route with the same brush
engine as alpha the page tints with whatever ink it is set to.

Roads and watercourses are painted with the same machinery as the wash: no vector
stroke is drawn over the top. A watercourse is drawn at its own width where the basemap
measured one, so a large river is as wide on the map as it is on the ground; the class
still chooses the brush and the ink, and the pad is still read back through the class
brush, so the water layer keeps that brush's reservoir and break texture at any
width. The coast is chained rather than profiled: it is one line round the land and has
no width of its own to vary.

The route's plate depends on base-group fields only: the route ink is in `digest()`
alone, so the pen merges the retraced legs of the route by its own width
(`route_pen_width_px`, whatever the route ink) and lays that one line.

`pen_groups` returns the same layers as two groups, water and road, each with the mask of
every class that has a line effect set: the road masks are the band densities already read,
and a water class's mask is read from a mask-only pad holding that class's lines, built only
when the class has an effect. Bristles are keyed by seed and points, so a mask matches the
strokes of the union pad.

Every watercourse and road draws from the job's ink generator, in the order laid; the
route's plate draws from the pen generator. It does not trim anything to the ribbon and
does not paint the washes.
"""

from typing import NamedTuple

import numpy as np

from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.compositing import PigmentLayer
from pyntpot.ink.io import save_alpha
from pyntpot.ink.noise import F32
from pyntpot.ink.pad import InkPad
from pyntpot.ink.sheet import rgb
from pyntpot.maps.basemap import Line
from pyntpot.maps.line_effects import WATER_GROUP
from pyntpot.maps.painter.brushes import plate_brushes
from pyntpot.maps.painter.job import PaintJob, PlateStack, drawable
from pyntpot.maps.strands import STRAND_MERGE_WIDTHS, merge_strands

#: The road classes the pen lays, each with the band of road it carries.
_ROAD_BANDS = {"road_major": "major", "lane": "minor", "track": "path"}


class PenGroup(NamedTuple):
    """One group's ink layers in laying order and the mask of each class that has an effect."""

    layers: list[PigmentLayer]
    masks: dict[str, np.ndarray]


class PenGroups(NamedTuple):
    """The pen's two groups, the water group (rivers and coast) and the road group."""

    water: PenGroup
    road: PenGroup


#: One watercourse stroke: its class, brush, pixel points and width profile.
type _Stroke = tuple[str, Brush, np.ndarray, np.ndarray | None]


def _lines_of(job: PaintJob, line: Line) -> list[np.ndarray]:
    """The drawable parts of a line, as the plate's pixel points."""
    return [job.canvas.px(r) for r in drawable((line,))]


def _water_strokes(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> list[_Stroke]:
    """Every watercourse stroke as its class, brush, pixel points and width profile."""
    style = job.style
    strokes: list[_Stroke] = []
    wide: dict[tuple[str, float], Brush] = {}
    for r in job.layers.rivers:
        cls = r.cls
        brush, _hex = br.get(cls, br["minor"])
        px = float(r.width_px or 0.0) * style.brush.river_mult
        if px > brush.width / job.scale:
            key = (cls, round(px, 2))
            if key not in wide:
                wide[key] = brush_from_id(
                    style.brush.brushes[cls], px, job.scale, style.brush, cls
                )[0]
            brush = wide[key]
        # `r.profile` is the width along the river as a share of its widest point, so
        # an estuary narrows to a channel over its own length instead of being
        # drawn at one width throughout. The brush is built at the widest and
        # the profile only ever takes ink away.
        prof = r.profile
        for line in _lines_of(job, r.line):
            strokes.append(
                (
                    cls if cls in br else "minor",
                    brush,
                    line,
                    np.asarray(prof, F32) if prof else None,
                )
            )
    return strokes


def _lay_strokes(pad: InkPad, strokes: list[_Stroke], seed: int) -> None:
    """Lay `strokes` on `pad`, each with its brush and width profile."""
    pad.lay(
        [(brush, line) for _cls, brush, line, _prof in strokes],
        seed,
        profiles=[prof for _cls, _brush, _line, prof in strokes],
    )


def _coast_lines(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> list[tuple[Brush, np.ndarray]]:
    """Every coastline part with the coast's brush."""
    return [
        (br["coast"][0], line) for coast in job.layers.coastline for line in _lines_of(job, coast)
    ]


def _water_pad(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> list[PigmentLayer]:
    """Every watercourse and the coast in one pad, read back with the major river's brush."""
    pad = InkPad(job.shape, br["major"][0], job.style.brush)
    _lay_strokes(pad, _water_strokes(job, br), job.style.brush.ink_seed)
    coast_lines = _coast_lines(job, br)
    if coast_lines:
        pad.lay(coast_lines, job.style.brush.ink_seed)
    if not pad.any():
        return []
    return [(pad.read(br["major"][0], job.sheet), rgb(br["major"][1]))]


def _water_masks(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> dict[str, np.ndarray]:
    """The mask of each water class that has an effect, from a mask-only pad of its lines."""
    seed = job.style.brush.ink_seed
    strokes = _water_strokes(job, br)
    masks: dict[str, np.ndarray] = {}
    for cls in WATER_GROUP:
        if cls not in job.style.basemap.line_effects:
            continue
        pad = InkPad(job.shape, br["major"][0], job.style.brush)
        if cls == "coast":
            pad.lay(_coast_lines(job, br), seed)
        else:
            _lay_strokes(pad, [stroke for stroke in strokes if stroke[0] == cls], seed)
        masks[cls] = pad.read(br["major"][0], job.sheet)
    return masks


def _road_pads(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> PenGroup:
    """One pad per road band, the minor bands only when the card carries minor roads."""
    layers = job.layers
    out = PenGroup([], {})
    for key, band in _ROAD_BANDS.items():
        if key != "road_major" and not layers.minor_roads:
            continue
        pad = InkPad(job.shape, br[key][0], job.style.brush)
        pad.lay(
            [
                (br[key][0], line)
                for r in layers.roads
                if r.band == band
                for line in _lines_of(job, r.line)
            ],
            job.style.brush.ink_seed,
        )
        if pad.any():
            density = pad.read(br[key][0], job.sheet)
            out.layers.append((density, rgb(br[key][1])))
            out.masks[key] = density
    return out


def _brushes(job: PaintJob) -> dict[str, tuple[Brush, str]]:
    """Every class's brush for this job's plate."""
    return plate_brushes(job.style.brush, job.scale, dict(job.layers.wet_px))


def paint_pen(job: PaintJob) -> list[PigmentLayer]:
    """The watercourse, coast and road ink layers, in laying order, untrimmed."""
    br = _brushes(job)
    return [*_water_pad(job, br), *_road_pads(job, br).layers]


def pen_groups(job: PaintJob) -> PenGroups:
    """The pen's water and road groups: each one's layers and its classes' effect masks."""
    br = _brushes(job)
    return PenGroups(
        PenGroup(_water_pad(job, br), _water_masks(job, br)),
        _road_pads(job, br),
    )


def paint_route_pen(job: PaintJob, stack: PlateStack) -> None:
    """Write the route as an alpha plate, when the style draws it, and record it in the stack."""
    route = job.style.route
    if not route.route_pen:
        return
    brush, _ = brush_from_id(
        route.route_pen_brush, route.route_pen_width_px, job.scale, job.style.brush, "route"
    )
    pad = InkPad(job.shape, brush, job.style.brush)
    line = merge_strands(
        [(float(x), float(y)) for x, y in job.canvas.px(list(job.layers.route))],
        route.route_pen_width_px * STRAND_MERGE_WIDTHS * job.scale,
    )
    pad.lay([(brush, np.asarray(line, dtype=np.float64))], job.pen_seed)
    path = job.out_dir / "pen.webp"
    stack.sizes["pen"] = save_alpha(
        pad.read(brush, job.sheet), path, lossless=job.style.paper.plate_lossless
    )
    stack.files["pen"] = path.name
