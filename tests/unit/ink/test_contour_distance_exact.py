"""`contour_distance` at pinned values: sub-pixel crossings, the search reach and the cap."""

import numpy as np
import pytest

from pyntpot.ink.effect_distance import contour_distance
from pyntpot.ink.noise import F32

CENTRE = 7


def _dot() -> np.ndarray:
    """A 15 by 15 float32 mask with one full pixel at its centre."""
    mask = np.zeros((15, 15), F32)
    mask[CENTRE, CENTRE] = 1.0
    return mask


class TestSubPixelCrossing:
    """The contour sits where the interpolated mask meets the threshold."""

    def test_a_ramp_puts_the_contour_halfway_between_its_pixels(self) -> None:
        """Between 0.1 and 0.5 at threshold 0.3 the contour is half a pixel from the 0.1."""
        d = contour_distance(np.array([[0.0, 0.1, 0.5, 1.0, 1.0]], F32), threshold=0.3, radius=3.0)
        assert d[0, 1] == pytest.approx(0.5, abs=1e-5)
        assert d[0, 0] == pytest.approx(1.5, abs=1e-5)

    def test_a_float64_mask_is_read_as_float32(self) -> None:
        """A float64 mask a hair under the threshold rounds to it in float32 and is the line."""
        mask = np.full((4, 4), 0.3 - 1e-9, np.float64)
        d = contour_distance(mask, threshold=0.3, radius=3.0)
        assert d.dtype == F32
        assert np.all(d == 0.0)

    def test_the_line_pixel_seeds_its_diagonal_neighbours(self) -> None:
        """A pixel diagonal to a one-pixel dot is reached from the dot, not only a neighbour."""
        d = contour_distance(_dot(), threshold=0.3, radius=3.0)
        assert d[CENTRE + 1, CENTRE + 1] == pytest.approx(0.7142, abs=1e-3)
        assert d[CENTRE - 2, CENTRE - 3] == pytest.approx(2.906, abs=1e-3)


class TestReachAndCap:
    """The search reaches `ceil(radius) + 1` pixels and reads `radius + 2` beyond."""

    @pytest.mark.parametrize(
        ("radius", "offset", "expected"),
        [(3.0, (-5, 0), 4.3), (3.0, (0, 5), 4.3), (3.0, (-4, -2), 3.906), (4.0, (-6, 0), 5.3)],
        ids=["above", "right", "off-axis", "radius-four"],
    )
    def test_the_far_edge_of_the_reach_is_measured(
        self, radius: float, offset: tuple[int, int], expected: float
    ) -> None:
        """The farthest pixels the search reaches carry their distance from the dot."""
        d = contour_distance(_dot(), threshold=0.3, radius=radius)
        assert d[CENTRE + offset[0], CENTRE + offset[1]] == pytest.approx(expected, abs=1e-3)

    @pytest.mark.parametrize(("radius", "cap"), [(3.0, 5.0), (4.0, 6.0)], ids=["three", "four"])
    def test_beyond_the_reach_is_the_cap(self, radius: float, cap: float) -> None:
        """A pixel past the circle of the reach reads `radius + 2`, not a longer search's value."""
        d = contour_distance(_dot(), threshold=0.3, radius=radius)
        assert d[CENTRE - int(radius) - 2, CENTRE - 2] == cap
        assert d[CENTRE - int(radius) - 2, CENTRE - 1] == cap
