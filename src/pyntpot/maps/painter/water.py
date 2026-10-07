"""The water phase: the sea and the lakes filled, the lakes washed, the sea washed.

Key names: `paint_water`, which fills the sea's and the lakes' coverage and the water
mask into the stack; `paint_lakes`, which lays the lakes' wash among the trimmed
layers; `sea_layer`, the sea's wash, which the page lays over the ribbon rather than
trimming; and `sea_patches` and `coast_run`, which work the sea's density in broad
patches along the shore.

Water is cut out of every land pigment, so `paint_water` runs first. The lake wash is
trimmed with the rest of the land cover, so a reservoir two valleys away does not
float on the paper; the sea runs to the card edge and is never trimmed. Each wash
draws its blooms from the job's shared generator, so the order the phases call is the
order the generator is consumed.

It does not paint the land cover or the wood, and `sea_layer` returns nothing when the
sea is off, empty or not painted to the card edge.
"""

import math

import numpy as np

from pyntpot.ink.noise import F32, blur, edt, fbm, fbm_aniso
from pyntpot.ink.pigment import Layer
from pyntpot.ink.raster import fill_cov
from pyntpot.ink.sheet import rgb
from pyntpot.ink.style import WashStyle
from pyntpot.ink.wash import WashOptions, wash
from pyntpot.maps.painter.job import INSIDE, PaintJob, PlateStack, drawable

#: The radius of the blur the sea's distance field is smoothed by before its gradient.
_COAST_BLUR = 3.0
#: A distance gradient weaker than this has no direction worth reading.
_MIN_GRADIENT = 1e-3


def coast_run(d_sea: np.ndarray, wet: np.ndarray, band: float) -> float:
    """Which way the shore runs, in radians, from the sea's own distance field.

    The gradient of the distance into the sea points across the coast, so the
    coast itself runs at right angles to it. Orientation has no sign, so the
    angles are doubled before they are averaged and halved after, weighted by
    how much shore runs each way: a shore that turns a right angle gives the run
    of its longer side, and a gentler bend a mean that leans towards it.

    Args:
        d_sea: Distance in render pixels from the land into the sea.
        wet: Where the sea is.
        band: How far out from the shore to read the direction, in pixels.

    Returns:
        The angle, in image coordinates with the row axis downward. 0 when
        no sea pixel within `band` of the shore has a gradient to read.
    """
    gy, gx = np.gradient(blur(d_sea, _COAST_BLUR))
    near = wet & (d_sea > 1.0) & (d_sea < band)
    mag = np.hypot(gx, gy)
    sel = near & (mag > _MIN_GRADIENT)
    if not sel.any():
        return 0.0
    ang = np.arctan2(gx[sel], -gy[sel])
    return 0.5 * float(math.atan2(float(np.sin(2 * ang).mean()), float(np.cos(2 * ang).mean())))


def sea_patches(dens: np.ndarray, sea_cov: np.ndarray, mpp: float, style: WashStyle) -> np.ndarray:
    """Broad paler and deeper patches in the sea, worked along the shore.

    The sea is the largest single wash on the card and the one that has to
    stay flat everywhere it is not: a wash that big does not dry evenly, it
    dries in patches the width of the brush's own travel, and the pigment gets
    worked along the shore rather than across it. One low frequency field
    gives the patches, a second stretched along the coast's own run gives the
    streaking, and the streaking fades out to sea because that is where the
    brush stopped being dragged along an edge.

    Args:
        dens: The sea wash's density, in 0 to 1.
        sea_cov: The sea's coverage, for the shore the streaks follow.
        mpp: Metres per render pixel, so a patch is the same size on the
            ground whatever box the card holds.
        style: The wash style, for the cell, the swing and the streaking.

    Returns:
        The modulated density, in 0 to 1.
    """
    amount = float(np.clip(style.sea_variation_amount, 0.0, 1.0))
    if amount <= 0.0:
        return dens
    h, w = dens.shape
    rng = np.random.default_rng(style.sea_variation_seed)
    cell = max(style.sea_variation_cell_m / mpp, 8.0)
    wet = sea_cov > INSIDE
    if not wet.any():
        wet = np.ones_like(wet)

    def centred(f: np.ndarray) -> np.ndarray:
        """The field about its own mean over the sea, in about -1 to 1.

        Over the sea, because the patches move pigment about rather than add
        it: a field centred on the whole card would lighten or darken a sea
        that sits in one corner of it.
        """
        return (f - float(f[wet].mean())) * 2.0

    swing = centred(fbm(h, w, cell, 3, rng))
    streak_w = float(np.clip(style.sea_variation_streak, 0.0, 1.0))
    if streak_w > 0.0:
        d_sea = edt(~wet)
        band = max(style.sea_variation_band_m / mpp, 4.0)
        angle = coast_run(d_sea, wet, band)
        streak = fbm_aniso(
            (h, w), max(cell * 0.22, 3.0), 2, rng, max(style.sea_variation_elong, 1.0), angle
        )
        swing = swing + streak_w * centred(streak) * np.exp(-d_sea / F32(band))
        swing /= 1.0 + streak_w
    return np.clip(dens * (1.0 + amount * swing), 0.0, 1.0)


def paint_water(job: PaintJob, stack: PlateStack) -> None:
    """Fill the sea and the lakes: it is cut out of every land pigment, so it goes first."""
    layers = job.layers
    sea_rings = drawable(layers.sea)
    lake_rings = drawable(layers.lakes)
    if sea_rings:
        stack.sea_cov = fill_cov(sea_rings, job.canvas)
    if lake_rings:
        stack.lake_cov = fill_cov(lake_rings, job.canvas)
    stack.water = np.maximum(stack.sea_cov, stack.lake_cov) > INSIDE


def paint_lakes(job: PaintJob, stack: PlateStack) -> None:
    """Wash the lakes among the trimmed layers, so a reservoir two valleys away is trimmed too."""
    lake_cov = stack.lake_cov
    if not lake_cov.any():
        return
    stack.trimmed.append(
        (
            wash(
                lake_cov,
                job.sheet,
                0.62,
                0.32,
                WashOptions(
                    wobble=2.4,
                    dry=1.2,
                    rim_px=max(5.0, 70.0 / job.mpp),
                    gran=0.22,
                    gran_gamma=job.gran_gamma,
                    flow=job.flow,
                    blooms=job.bloom(lake_cov),
                ),
            ),
            rgb(job.style.cover.pigments["water"]),
            job.transp("water"),
        )
    )


def sea_layer(job: PaintJob, stack: PlateStack) -> Layer | None:
    """The sea's wash, laid over the ribbon to the card edge, or `None` when there is none."""
    sea_cov = stack.sea_cov
    if not (sea_cov.any() and job.style.ribbon.sea_to_edge):
        return None
    dens = wash(
        sea_cov,
        job.sheet,
        0.60,
        0.34,
        WashOptions(
            wobble=2.0,
            dry=1.0,
            rim_px=max(6.0, 110.0 / job.mpp),
            gran=0.22,
            gran_gamma=job.gran_gamma,
            flow=job.flow,
            blooms=job.bloom(sea_cov),
        ),
    )
    if job.style.wash.sea_variation:
        dens = sea_patches(dens, sea_cov, job.mpp, job.style.wash)
    return (dens, rgb(job.style.cover.pigments["water"]), job.transp("water"))
