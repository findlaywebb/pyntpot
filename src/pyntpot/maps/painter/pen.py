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

Every watercourse and road draws from the job's ink generator, in the order laid; the
route's plate draws from the pen generator. It does not trim anything to the ribbon and
does not paint the washes.
"""

import numpy as np

from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.io import save_alpha
from pyntpot.ink.noise import F32
from pyntpot.ink.pad import InkPad
from pyntpot.ink.pigment import PigmentLayer
from pyntpot.ink.sheet import rgb
from pyntpot.maps.basemap import Line
from pyntpot.maps.painter.brushes import plate_brushes
from pyntpot.maps.painter.job import PaintJob, PlateStack, drawable

#: The road classes the pen lays, each with the band of road it carries.
_ROAD_BANDS = {"road_major": "major", "lane": "minor", "track": "path"}


def _lines_of(job: PaintJob, line: Line) -> list[np.ndarray]:
    """The drawable parts of a line, as the plate's pixel points."""
    return [job.canvas.px(r) for r in drawable((line,))]


def _water_pad(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> list[PigmentLayer]:
    """Every watercourse and the coast in one pad, read back with the major river's brush."""
    layers = job.layers
    style = job.style
    pad = InkPad(job.shape, br["major"][0], style.brush)
    water_lines: list[tuple[Brush, np.ndarray]] = []
    wide: dict[tuple[str, float], Brush] = {}
    profiles: list[np.ndarray | None] = []
    for r in layers.rivers:
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
            water_lines.append((brush, line))
            profiles.append(np.asarray(prof, F32) if prof else None)
    pad.lay(water_lines, job.ink_rng, profiles=profiles)
    coast_lines = [
        (br["coast"][0], line) for coast in layers.coastline for line in _lines_of(job, coast)
    ]
    if coast_lines:
        pad.lay(coast_lines, job.ink_rng)
    if not pad.any():
        return []
    return [(pad.read(br["major"][0], job.sheet), rgb(br["major"][1]))]


def _road_pads(job: PaintJob, br: dict[str, tuple[Brush, str]]) -> list[PigmentLayer]:
    """One pad per road band, the minor bands only when the card carries minor roads."""
    layers = job.layers
    out: list[PigmentLayer] = []
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
            job.ink_rng,
        )
        if pad.any():
            out.append((pad.read(br[key][0], job.sheet), rgb(br[key][1])))
    return out


def paint_pen(job: PaintJob) -> list[PigmentLayer]:
    """The watercourse, coast and road ink layers, in laying order, untrimmed."""
    br = plate_brushes(job.style.brush, job.scale, dict(job.layers.wet_px))
    return [*_water_pad(job, br), *_road_pads(job, br)]


def paint_route_pen(job: PaintJob, stack: PlateStack) -> None:
    """Write the route as an alpha plate, when the style draws it, and record it in the stack."""
    route = job.style.route
    if not route.route_pen:
        return
    brush, _ = brush_from_id(
        route.route_pen_brush, route.route_pen_width_px, job.scale, job.style.brush, "route"
    )
    pad = InkPad(job.shape, brush, job.style.brush)
    pad.lay([(brush, job.canvas.px(list(job.layers.route)))], job.pen_rng)
    path = job.out_dir / "pen.webp"
    stack.sizes["pen"] = save_alpha(
        pad.read(brush, job.sheet), path, lossless=job.style.paper.plate_lossless
    )
    stack.files["pen"] = path.name
