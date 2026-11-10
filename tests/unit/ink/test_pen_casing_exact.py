"""`pen_casing` blends in float32: pinned pixels whose float64 blend would round differently."""

import numpy as np
import pytest

from pyntpot.ink.effect_pen_casing import pen_casing
from pyntpot.ink.effect_types import PenCasing
from pyntpot.ink.noise import F32


@pytest.mark.parametrize(
    ("level", "expected"),
    [(0.3, 0.6150000095367432), (0.7, 0.8350000381469727)],
    ids=["dark", "light"],
)
def test_a_partly_reserved_pixel_is_blended_in_float32(level: float, expected: float) -> None:
    """The pixel at the reserve's edge is the float32 blend of paper and wash, bit for bit."""
    mask = np.zeros((1, 6), F32)
    mask[0, 0] = 1.0
    rgb = np.full((1, 6, 3), level, F32)
    out, _ = pen_casing(rgb, mask, PenCasing(width_px=2.25, edge_px=1.0))
    assert float(out[0, 3, 0]) == expected
