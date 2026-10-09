"""The relief: the density painted from the sheet and the elevation patch alone.

Key name: `relief_density`, a quiet shaded relief read from the basemap's elevation patch, in
pigment density. The paper plate is `pyntpot.ink.paper`.

It is a pure function of the sheet's noise, the plate's canvas and the patch: it draws from
no shared generator, so it does not move the order the phases consume the generators in.

It does not trim the relief to the ribbon or choose its pigment; the relief phase lays the
density.
"""

import numpy as np

from pyntpot.ink.noise import F32, blur
from pyntpot.ink.sheet import Canvas, Sheet
from pyntpot.maps.basemap import ElevationPatch


def relief_density(grid: ElevationPatch, plate: Canvas, sheet: Sheet) -> np.ndarray:
    """A quiet shaded relief from the elevation patch, in pigment density."""
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
