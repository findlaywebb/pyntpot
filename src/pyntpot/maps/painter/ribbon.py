"""The ribbon phase: the ground laid over white and faded out toward the torn edge.

Key names: `ribbon_alpha`, the trimmed extent of the painted ground and its pooled rim;
and `paint_ribbon`, which turns the stack's trimmed layers into the ground the page
multiplies over the card, and returns it with the rim's density.

The stack is laid over white, because the page multiplies the wash plate over the card;
the ribbon then fades the ground out toward the tear. Where the style asks for a hard
coast, the surveyed shore stops the ribbon and the sea, which is painted separately and
never trimmed, takes over there.

It draws from no shared generator, and it does not lay the sea, the rim or the ink on
top of the ground: the plates phase does.
"""

import numpy as np

from pyntpot.ink.noise import F32, blur, edt, fill_holes, smoothstep
from pyntpot.ink.pigment import composite
from pyntpot.ink.raster import stroke_mask
from pyntpot.ink.sheet import Sheet
from pyntpot.maps.painter.job import PaintJob, PlateStack


def ribbon_alpha(
    d_route: np.ndarray,
    r_px: float,
    sheet: Sheet,
    tear_px: float,
    *,
    fill: bool,
    land: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """The trimmed extent of the painted ground, and its pooled edge.

    Args:
        d_route: Distance in pixels to the route.
        r_px: The ribbon radius in pixels.
        sheet: The paper's noise fields.
        tear_px: How far the torn edge wanders.
        fill: Fill the inside of a loop rather than dilating the line alone.
        land: The land side of a surveyed coast, when there is one.

    Returns:
        The ribbon's alpha, and the density of its pooled rim.
    """
    if fill:
        core = d_route < r_px
        core = fill_holes(core, step=max(4, int(r_px / 12)))
        s = (blur(core.astype(F32), r_px * 0.34) - 0.5) * (r_px * 0.9)
    else:
        s = blur(np.asarray(r_px - d_route, F32), r_px * 0.30)
    sig = s + (sheet.coarse - 0.5) * (r_px * 0.30) + (sheet.fine - 0.5) * tear_px
    alpha = smoothstep(sig, 2.6)
    rim = np.exp(-np.abs(sig) / F32(max(r_px * 0.045, 3.0))) * alpha
    if land is not None:
        # The coast is a hard edge, not a wash edge. Nothing the ribbon carries
        # is allowed over it: the torn edge stops at the surveyed line, and the
        # sea, which is painted separately and never trimmed, takes over there.
        alpha = alpha * land
        rim = rim * land
    return alpha, rim


def paint_ribbon(job: PaintJob, stack: PlateStack) -> tuple[np.ndarray, np.ndarray]:
    """The ground over white, faded out toward the tear, and the density of the pooled rim."""
    style = job.style
    ribbon = style.ribbon
    layers = job.layers
    rh, rw = job.shape
    route_mask = stroke_mask([list(layers.route)], job.canvas, 2.0)
    d_route = edt(route_mask)
    tear_px = max(rw * ribbon.ribbon_tear_frac, ribbon.ribbon_tear_floor_px)
    land = None
    if ribbon.coast_hard_mask and stack.sea_cov.any():
        # The land side of the surveyed coast, antialiased by one pixel, no more.
        land = np.clip(1.0 - blur(stack.sea_cov, 0.8) * 1.6, 0.0, 1.0)
    r_px = layers.ribbon_m / job.mpp
    alpha, rim = ribbon_alpha(d_route, r_px, job.sheet, tear_px, fill=ribbon.ribbon_fill, land=land)
    ground = composite(stack.trimmed, np.ones((rh, rw, 3), F32), style.paper)
    return 1.0 - alpha[..., None] * (1.0 - ground), rim
