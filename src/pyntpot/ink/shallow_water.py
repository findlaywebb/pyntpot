"""Curtis' shallow water layer, cut down to a bounded number of steps.

Key function: `shallow_water`, which runs the water on a coarse grid and returns what has
been deposited. Pigment moves as a flux between cells, so it piles up against a contact
line the water cannot cross, and that pile is the edge darkening.

It reads the four `fluid_*` counts and settings of the wash group it is handed.

Invariants: every count is a count and not a tolerance, so the plate stays reproducible
from its seed; the deposit is normalised to 0 to 1, or left as it is when nothing settled.
"""

import numpy as np

from pyntpot.ink.noise import F32, blur
from pyntpot.ink.style import WashStyle

#: A cell with less water than this is dry.
_DRY = 0.05
#: A deposit whose peak is below this is left as it is rather than normalised.
_NO_DEPOSIT = 1e-6


def shallow_water(
    wet: np.ndarray,
    pig: np.ndarray,
    paper: np.ndarray,
    style: WashStyle,
) -> np.ndarray:
    """Curtis' shallow water layer, cut down to a bounded number of steps.

    Velocities come from the pressure gradient, `RelaxDivergence` hands each
    cell's divergence to its two neighbours a fixed number of times, the
    outward flow lifts the pressure at the wet boundary, and what settles
    follows the paper's own height. Pigment moves as a flux between cells
    rather than by sampling, which is what lets it pile up against a contact
    line the water cannot cross: that pile is the edge darkening.

    Every count here is a count and not a tolerance. A convergence test would
    make the number of iterations depend on the arithmetic, and the plate would
    stop being reproducible from its seed.

    Source: `shallow-water` in docs/explanation/references.md.

    Args:
        wet: The wet area on this grid, in 0 to 1.
        pig: Pigment in suspension at the start, in 0 to 1.
        paper: The paper's height on this grid, in 0 to 1.
        style: The wash group: `fluid_steps`, how many steps to run; `fluid_relax`,
            the relaxation iterations inside one step; `fluid_seed`, the generator's
            seed, for the water's own unevenness; and `fluid_gran`, how much the
            settling follows the paper's height.

    Returns:
        What has been deposited, normalised to 0 to 1.
    """
    h, w = wet.shape
    rng = np.random.default_rng(style.fluid_seed)
    hgt = (wet * (0.85 + 0.30 * rng.random((h, w)))).astype(F32)
    u = np.zeros((h, w), F32)
    v = np.zeros((h, w), F32)
    g = (pig * wet).astype(F32)
    dep = np.zeros((h, w), F32)
    tooth = (paper - float(paper.mean())).astype(F32)
    mask = (wet > _DRY).astype(F32)
    edge = np.clip(mask - blur(mask, 3.0), 0.0, 1.0)
    hold = (F32(0.05) * (1.0 + style.fluid_gran * (0.5 - paper) * 2.0)).astype(F32)
    #: Where pigment may pass: nothing crosses the edge of the wet area.
    wall_x = (mask * np.roll(mask, -1, 1)).astype(F32)
    wall_y = (mask * np.roll(mask, -1, 0)).astype(F32)

    def dx(a: np.ndarray) -> np.ndarray:
        return np.roll(a, -1, 1) - a

    def dy(a: np.ndarray) -> np.ndarray:
        return np.roll(a, -1, 0) - a

    for _ in range(max(int(style.fluid_steps), 0)):
        p = hgt + F32(0.40) * tooth
        u = (u - F32(0.35) * dx(p)) * F32(0.94) * mask
        v = (v - F32(0.35) * dy(p)) * F32(0.94) * mask
        for _ in range(max(int(style.fluid_relax), 0)):
            d = (F32(0.1) * (dx(u) + dy(v))).astype(F32)
            hgt += d
            u += d - np.roll(d, 1, 1)
            v += d - np.roll(d, 1, 0)
            u *= mask
            v *= mask
        np.clip(u, -0.45, 0.45, out=u)
        np.clip(v, -0.45, 0.45, out=v)
        hgt = np.maximum(hgt - F32(0.03) * edge, 0.0) * mask
        # Pigment moves as a flux between cells, upwind, and no flux crosses
        # the wet boundary. Advecting it by sampling instead would carry it
        # about without ever piling it up, and piling it up against a contact
        # line the water cannot cross is exactly what edge darkening is.
        fx = np.where(u > 0, g, np.roll(g, -1, 1)) * u * wall_x
        g = g - fx + np.roll(fx, 1, 1)
        fy = np.where(v > 0, g, np.roll(g, -1, 0)) * v * wall_y
        g = g - fy + np.roll(fy, 1, 0)
        settle = g * hold
        dep += settle
        g -= settle
    top = float(dep.max())
    return (dep / top).astype(F32) if top > _NO_DEPOSIT else dep
