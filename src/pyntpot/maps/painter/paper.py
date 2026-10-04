"""The card and the relief: the two arrays that are painted from the sheet and the grid alone.

Key names: `paper_plate`, the notebook card (cream rag, a worn border, a little foxing,
and a grid when the style asks for one); and `relief_density`, a quiet shaded relief
read from the elevation grid, in pigment density.

Both are pure functions of the sheet's noise, the plate's canvas and the style groups
they read: neither draws from a shared generator, so neither moves the order the phases
consume them in.

It does not write the card to disk, trim the relief to the ribbon or choose its
pigment; the plates phase writes the card and the relief phase lays the density.
"""

import numpy as np

from pyntpot.ink.noise import F32, blur
from pyntpot.ink.sheet import Canvas, Sheet, rgb
from pyntpot.ink.style import PaperStyle
from pyntpot.maps.basemap import ElevationPatch


def relief_density(grid: ElevationPatch, plate: Canvas, sheet: Sheet) -> np.ndarray:
    """A quiet shaded relief from the SRTM grid, in pigment density."""
    n = grid.n
    v = np.asarray(grid.values, F32).reshape(n, n)
    gx = (
        (np.arange(plate.w, dtype=F32) / plate.scale + plate.x0 - grid.x0)
        / (grid.x1 - grid.x0)
        * (n - 1)
    )
    gy = (
        (plate.y1 - np.arange(plate.h, dtype=F32) / plate.scale - grid.y0)
        / (grid.y1 - grid.y0)
        * (n - 1)
    )
    gx = np.clip(gx, 0, n - 1.001)
    gy = np.clip(gy, 0, n - 1.001)
    x0 = gx.astype(np.int32)
    y0 = gy.astype(np.int32)
    fx = (gx - x0)[None, :]
    fy = (gy - y0)[:, None]
    a, b = v[y0][:, x0], v[y0][:, x0 + 1]
    c, d = v[y0 + 1][:, x0], v[y0 + 1][:, x0 + 1]
    z = (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy
    z = blur(z, 3.0)
    mpp = 1.0 / plate.scale
    gyd, gxd = np.gradient(z, mpp)
    shade = np.clip((-0.6 * gxd + 0.6 * gyd + 0.55) / 1.2, 0.0, 1.0)
    dens = np.clip(0.30 * (1.0 - shade), 0.0, 0.40)
    dens *= 1.0 + 0.24 * np.clip((sheet.gran - 0.5) * 2.2, -0.7, 1.0)
    dens *= 1.0 - 0.30 * (sheet.paper - 0.5)
    return np.clip(blur(dens, 2.0), 0.0, 1.0)


def paper_plate(sheet: Sheet, plate: Canvas, style: PaperStyle, display_px: int) -> np.ndarray:
    """The notebook card: cream rag, a worn border, a little foxing, no grid."""
    h, w = plate.h, plate.w
    base = rgb(style.paper_hex)
    img = np.repeat(base[None, None, :], h, 0).repeat(w, 1).copy()
    img *= (1.0 + style.paper_tooth * (sheet.paper - 0.5))[..., None]
    yy = np.minimum(np.arange(h)[:, None], h - 1 - np.arange(h)[:, None])
    xx = np.minimum(np.arange(w)[None, :], w - 1 - np.arange(w)[None, :])
    edge_px = np.minimum(yy, xx).astype(F32)
    worn = np.exp(-edge_px / F32(max(w * 0.012, 8.0)))
    worn = worn * (0.55 + 0.9 * sheet.noise(26.0, 2))
    img *= (1.0 - style.paper_worn * np.clip(worn, 0, 1))[..., None]
    vign = np.exp(-edge_px / F32(w * 0.34))
    img *= (1.0 - style.paper_vignette * vign)[..., None]
    fox = np.clip((sheet.noise(120.0, 2) - 0.80) * 5.0, 0, 1)
    img *= (1.0 - style.paper_foxing * fox)[..., None]
    if style.grid:
        step = max(style.grid_spacing_px * plate.w / max(display_px, 1), 4.0)
        rows = (np.arange(h) % step < 1.0)[:, None]
        cols = (np.arange(w) % step < 1.0)[None, :]
        line = np.clip(rows * 1.0 + cols * 0.55, 0, 1).astype(F32)
        img *= (1.0 - style.grid_opacity * 0.30 * line)[..., None]
    return np.clip(img, 0, 1)
