"""`contour_distance` and `ring_coverage` at their edges: ties, caps, thin lines, the array edge."""

import numpy as np
import pytest

from pyntpot.ink.effect_distance import contour_distance, ring_coverage
from pyntpot.ink.noise import F32


def _row(*values: float, width: int = 9) -> np.ndarray:
    """A five-row mask whose every row is `values` padded with zeros to `width` columns."""
    row = np.zeros(width, F32)
    row[: len(values)] = values
    return np.tile(row, (5, 1))


class TestCaps:
    """A mask with no outside or no line gets the documented value."""

    def test_a_mask_with_no_line_is_the_cap_everywhere(self) -> None:
        """With no pixel at the threshold the distance is radius + 2 everywhere."""
        d = contour_distance(np.zeros((6, 7), F32), threshold=0.3, radius=4.0)
        assert np.all(d == 6.0)

    def test_a_mask_that_is_all_line_is_zero_everywhere(self) -> None:
        """With no pixel below the threshold the distance is 0 everywhere."""
        d = contour_distance(np.ones((6, 7), F32), threshold=0.3, radius=4.0)
        assert np.all(d == 0.0)


class TestTies:
    """A mask exactly at the threshold counts as the line."""

    def test_a_mask_at_the_threshold_is_inside(self) -> None:
        """A value of 0.25 at threshold 0.25 is not positive, and its neighbour is."""
        d = contour_distance(_row(0.0, 0.25), threshold=0.25, radius=3.0)
        assert d[2, 1] <= 0.0
        assert d[2, 0] > 0.0

    def test_the_contour_of_a_tie_lies_on_the_pixel(self) -> None:
        """The neighbour of a pixel exactly at the threshold is a whole pixel from the contour."""
        d = contour_distance(_row(0.0, 0.25), threshold=0.25, radius=3.0)
        assert d[2, 0] == pytest.approx(1.0)


class TestThinLines:
    """A one-pixel line has its contour inside the pixel."""

    def test_distance_grows_one_pixel_a_column_from_the_contour(self) -> None:
        """A full column puts its contour 0.3 px into the next, then a pixel per column."""
        d = contour_distance(_row(0, 0, 0, 0, 1.0), threshold=0.3, radius=5.0)
        assert d[2, 3] == pytest.approx(0.3)
        assert d[2, 2] == pytest.approx(1.3)
        assert d[2, 1] == pytest.approx(2.3)
        assert d[2, 5] == pytest.approx(0.3)

    def test_the_line_itself_is_not_positive(self) -> None:
        """Every pixel of the line has a distance of at most 0."""
        d = contour_distance(_row(0, 0, 0, 0, 1.0), threshold=0.3, radius=5.0)
        assert np.all(d[:, 4] <= 0.0)


class TestArrayEdge:
    """The array's edge is no contour."""

    def test_a_line_on_the_edge_still_measures_beside_it(self) -> None:
        """A line in the first column puts the next column 0.3 px out, with no false edge."""
        d = contour_distance(_row(1.0), threshold=0.3, radius=3.0)
        assert d[2, 1] == pytest.approx(0.3)
        assert d[2, 2] == pytest.approx(1.3)

    def test_a_search_wider_than_the_array_is_safe(self) -> None:
        """A radius beyond the array's size still gives the distance of a nearby pixel."""
        d = contour_distance(_row(1.0, width=3), threshold=0.3, radius=20.0)
        assert d[2, 1] == pytest.approx(0.3)


class TestRingCoverage:
    """The box-filter coverage of the ring [0, width]."""

    @pytest.mark.parametrize(
        ("distance", "expected"),
        [
            (-1.0, 0.0),
            (-0.5, 0.0),
            (-0.25, 0.25),
            (0.0, 0.5),
            (0.5, 1.0),
            (1.0, 1.0),
            (1.75, 0.75),
            (2.25, 0.25),
            (2.5, 0.0),
            (4.0, 0.0),
        ],
        ids=[
            "inside",
            "inner-edge",
            "straddling-in",
            "contour",
            "contour-out",
            "mid",
            "quarter-in",
            "quarter-out",
            "outer-edge",
            "far",
        ],
    )
    def test_coverage_at_a_distance_for_a_width_of_two(
        self, distance: float, expected: float
    ) -> None:
        """A width of 2 covers wholly from 0 to 1.5 and falls to nothing at 2.5."""
        out = ring_coverage(np.array([distance], F32), 2.0)
        assert out[0] == pytest.approx(expected)
        assert out.dtype == F32
