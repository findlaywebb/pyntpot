"""Small painted fixtures for the wash, pigment and water tests."""

import numpy as np

from pyntpot.ink.noise import fbm
from pyntpot.ink.sheet import Sheet


def two_squares(h: int = 200, w: int = 320) -> tuple[Sheet, np.ndarray, np.ndarray]:
    """Two land classes meeting along a seam, on a sheet, for the wash tests."""
    sheet = Sheet(h, w, gran_px=8.0, seed=5)
    left = np.zeros((h, w), np.float32)
    left[40:160, 40:160] = 1.0
    right = np.zeros((h, w), np.float32)
    right[40:160, 160:280] = 1.0
    return sheet, left, right


def fluid_fields(h: int = 96, w: int = 128) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A wet area, some pigment in it, and paper under it."""
    rng = np.random.default_rng(4)
    wet = np.zeros((h, w), np.float32)
    wet[12:84, 16:112] = 1.0
    pig = fbm(h, w, 20.0, 2, rng)
    paper = fbm(h, w, 4.0, 3, rng)
    return wet, pig, paper
