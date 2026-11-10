"""A straight pen stroke laid out by hand, for the tests of `deposit`'s set-down cover.

Key names: `straight_lay`, a `Lay` and its samples' positions with every field a literal, and
`all_live`, every sample laying ink. No package code reads them.
"""

import math

import numpy as np

from pyntpot.ink.stroke import Lay, Sampled, StrokeProfile, Tip, Trace


def straight_lay(
    squeeze: float = 1.0, m: int = 5, width: float = 2.0, slope: float = 0.0, n: int = 21
) -> tuple[Lay, tuple[np.ndarray, np.ndarray]]:
    """A stroke from (5, 20) or (5, 5), `width` px wide, its `n` stamps half a pixel apart.

    By default it is 10 px along y 20, 5 samples across, and each of its 21 stamps by 5
    samples stands for a quarter of a pixel. A `squeeze` of 2 lands the samples across half
    the width, so the paper under them is passed over twice. A `slope` of 1 runs it from
    (5, 5) at 45 degrees, down and to the right.
    """
    t = np.linspace(0.0, (n - 1) / 2, n).astype(np.float32)
    u = np.linspace(-width / 2, width / 2, m).astype(np.float32)
    along = np.float32(1.0 / math.hypot(1.0, slope))
    one = np.ones(n, np.float32)
    x, y = 5.0 + t * along, (20.0 if slope == 0.0 else 5.0) + t * along * slope
    tr = Trace(x, y, -one * along * slope, one * along, t, float(t[-1]))
    ink = StrokeProfile(one, np.full(n, width, np.float32), None)
    tip = Tip(m, u, np.ones(m), np.zeros((2, m)), np.zeros(m), np.ones(m), None, None, None, None)
    smp = Sampled(m, u, *(np.ones(m, np.float32),) * 5, None, np.ones(m, np.float32), width)
    off = np.broadcast_to(u[None, :], (n, m)).astype(np.float32)
    px = tr.x[:, None] + tr.nx[:, None] * off
    py = tr.y[:, None] + tr.ny[:, None] * off / squeeze
    return Lay(tr, ink, tip, smp, off), (px, py)


def all_live(pos: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    """Every sample laying ink, in the samples' shape."""
    return np.ones(pos[0].shape, dtype=bool)
