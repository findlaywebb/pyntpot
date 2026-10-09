"""The plates phase: every phase run in order, the plates written, and the manifest beside them.

Key names: `paint_plates`, which builds the job and runs the phases (water, cover, wood,
lakes, relief, fluid, pen), lays the ribbon over the ground, writes the card and the
wash and, when the style draws it, the route's pen plate, and writes the manifest.

Two plates carry the picture. `paper` is the card itself, drawn as it is. `wash` carries
every pigment, white where it lays down nothing, and the page multiplies it over the
card: the land cover and the relief are trimmed to the ribbon, the sea runs to the card
edge, and the ink is drawn over the whole map. The dark grid, a coarse grid of how dark
the map is, goes into the manifest, so a label can be placed on light ground rather
than across a wood.

The phases draw from the job's shared generators, so the order they are called in here
is fixed, and the plates' dither continues the sequence the wood left. It does not
letter anything, and it does not read the cache.
"""

from pathlib import Path

import numpy as np

from pyntpot.ink.io import save_webp, to_img
from pyntpot.ink.paper import paper_plate
from pyntpot.ink.pigment import PigmentLayer, composite
from pyntpot.ink.sheet import rgb
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.painter.cover import paint_cover
from pyntpot.maps.painter.fluid import paint_fluid
from pyntpot.maps.painter.job import PaintJob, PlateStack
from pyntpot.maps.painter.pen import paint_pen, paint_route_pen
from pyntpot.maps.painter.relief import paint_relief
from pyntpot.maps.painter.ribbon import paint_ribbon
from pyntpot.maps.painter.water import paint_lakes, paint_water, sea_layer
from pyntpot.maps.painter.wood import paint_wood
from pyntpot.maps.plates import DarkGrid, Manifest, Plates
from pyntpot.maps.style import Style


def _dark_grid(job: PaintJob, lum: np.ndarray) -> DarkGrid:
    """How dark the map is, in the style's grid of cells, from its mean luminance."""
    rh, rw = job.shape
    gw, gh = job.style.card.dark_grid
    ys = np.linspace(0, rh, gh + 1).astype(int)
    xs = np.linspace(0, rw, gw + 1).astype(int)
    dark = [
        [round(float(1.0 - lum[ys[r] : ys[r + 1], xs[c] : xs[c + 1]].mean()), 3) for c in range(gw)]
        for r in range(gh)
    ]
    return DarkGrid(w=gw, h=gh, values=tuple(tuple(row) for row in dark))


def _wash_plate(job: PaintJob, stack: PlateStack) -> np.ndarray:
    """The wash: the ground, then the sea, the pooled rim and the ink over it."""
    style = job.style
    ground, rim = paint_ribbon(job, stack)
    over: list[PigmentLayer] = []
    sea = sea_layer(job, stack)
    if sea is not None:
        over.append(sea)
    over.append(
        (
            np.clip(rim * style.ribbon.rim_strength, 0, 1),
            rgb(style.cover.pigments["rim"]),
            job.transp("rim"),
        )
    )
    over.extend(paint_pen(job))
    return composite(over, ground, style.paper)


def _write(
    job: PaintJob, stack: PlateStack, plates: tuple[tuple[str, np.ndarray, int], ...]
) -> None:
    """Dither and write each plate as WebP, recording its file and size."""
    lossless = job.style.paper.plate_lossless
    for name, arr, quality in plates:
        path = job.out_dir / f"{name}.webp"
        stack.sizes[name] = save_webp(to_img(arr, job.dither_rng), path, quality, lossless=lossless)
        stack.files[name] = path.name


def paint_plates(basemap: Basemap, style: Style, out_dir: Path) -> Plates:
    """Paint one basemap's plates and write them, with a manifest beside them.

    Args:
        basemap: The basemap from `layers.build_basemap`.
        style: The style the plates are painted in; its base digest is appended
            to the basemap's hash in the manifest.
        out_dir: Where to write; created when missing.

    Returns:
        The plates, with their manifest: files, byte counts, measurements and
        the dark grid.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    job = PaintJob.begin(basemap, style, out_dir)
    stack = PlateStack.blank(job.shape)
    layers = basemap.layers

    # Water first: it is cut out of every land pigment, then the land cover, the
    # wood and the lakes, which are trimmed with it.
    paint_water(job, stack)
    paint_cover(job, stack)
    paint_wood(job, stack)
    paint_lakes(job, stack)
    paint_relief(job, stack)
    paint_fluid(job, stack)

    wash_plate = _wash_plate(job, stack)
    paper = paper_plate(job.sheet, job.canvas, style.paper, style.card.display_px)
    _write(
        job,
        stack,
        (
            ("paper", paper, style.paper.paper_quality),
            ("wash", wash_plate, style.paper.webp_quality),
        ),
    )
    paint_route_pen(job, stack)
    dark = _dark_grid(job, (paper * wash_plate).mean(axis=2))

    manifest = Manifest(
        hash=Cache.base_key(basemap, style),
        files=stack.files,
        sizes=stack.sizes,
        bytes=sum(stack.sizes.values()),
        card=basemap.card,
        ribbon_m=layers.ribbon_m,
        span_m=basemap.span_m,
        # How wide each class of watercourse was actually painted, in display
        # pixels, so a river's name can be set clear of its own water rather
        # than in it. The label layer has no other way to know: it sees the
        # centreline and not the brush that was run along it.
        wet_px=dict(layers.wet_px),
        # The paper the ink was gated on, so a plate painted later gates on the
        # same sheet rather than on a second one that only looks similar.
        gran_px=round(max(layers.gran_m / job.mpp, 3.0), 3),
        dark=dark,
        wood_px=int(stack.wood_mask.sum()),
        water_px=int(stack.water.sum()),
    )
    (out_dir / "plates.json").write_text(manifest.to_json())
    return Plates(out_dir, manifest)
