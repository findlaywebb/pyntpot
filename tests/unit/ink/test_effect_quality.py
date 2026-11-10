"""The look of the anti-aliased casing and pen casing: smooth edges on a slanted line.

Each test lays a straight, anti-aliased 3 px line at 7, 20 and 33 degrees and measures a
ring's edge against a fitted straight line. A thresholded, chamfer-measured ring staircases (the
casing's edge wobbled 0.24 to 0.41 px, and a pen casing's thin edge line broke to nothing in
columns), so these pins are the visual bar the exact-distance property does not set.
"""

import numpy as np
import pytest

from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_pen_casing import pen_casing
from pyntpot.ink.effect_types import Casing, PenCasing
from pyntpot.ink.noise import F32

HEIGHT, WIDTH = 120, 200
LINE_PX = 3.0
ANGLES = pytest.mark.parametrize("angle", [7.0, 20.0, 33.0], ids=["7deg", "20deg", "33deg"])


def _slanted_line(angle_deg: float) -> np.ndarray:
    """An anti-aliased 3 px line from the top-left, `angle_deg` below horizontal."""
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float64)
    a = np.radians(angle_deg)
    s = np.abs(-xx * np.sin(a) + (yy - 10.0) * np.cos(a))
    return np.clip(LINE_PX / 2 + 0.5 - s, 0.0, 1.0).astype(F32)


def _columns(angle_deg: float) -> list[tuple[int, float]]:
    """The interior columns, each with the line centre's row, whose lower side has room."""
    tan = np.tan(np.radians(angle_deg))
    return [(c, 10.0 + c * tan) for c in range(20, WIDTH - 20) if 10.0 + c * tan < HEIGHT - 25]


def _worst_deviation(values: list[float]) -> float:
    """The largest distance of `values` from their least-squares straight line."""
    x = np.arange(len(values))
    return float(np.abs(np.asarray(values) - np.polyval(np.polyfit(x, values, 1), x)).max())


def _half_crossing(column: np.ndarray, below: float) -> float:
    """The row, by linear interpolation, where `column` falls through 0.5 below row `below`."""
    start = int(below) + 2
    rows = np.flatnonzero((column[start:-1] >= 0.5) & (column[start + 1 :] < 0.5))
    r = start + int(rows[0])
    return float(r + (column[r] - 0.5) / (column[r] - column[r + 1]))


class TestCasingEdge:
    """The casing's outer edge runs straight."""

    @ANGLES
    @pytest.mark.parametrize("width_px", [1.8, 3.6], ids=["1.8px", "3.6px"])
    def test_the_half_weight_row_deviates_little_from_a_straight_line(
        self, angle: float, width_px: float
    ) -> None:
        """Per column the weight's 0.5 crossing lies within 0.22 px of a fitted straight line."""
        mask = _slanted_line(angle)
        weight = casing(np.zeros((HEIGHT, WIDTH, 3), F32), mask, Casing(width_px=width_px))[..., 0]
        edge = [_half_crossing(weight[:, c], yc) for c, yc in _columns(angle)]
        assert _worst_deviation(edge) <= 0.22


class TestPenEdge:
    """The pen casing's edge line is unbroken and runs straight."""

    @staticmethod
    def _lower_band(angle: float) -> list[tuple[int, float, np.ndarray]]:
        """For each column, the line's centre row and the edge band below it."""
        mask = _slanted_line(angle)
        effect = PenCasing(width_px=1.0, edge_px=0.75)
        _, band = pen_casing(np.zeros((HEIGHT, WIDTH, 3), F32), mask, effect)
        return [(c, yc, band[int(yc) + 2 :, c]) for c, yc in _columns(angle)]

    @ANGLES
    def test_the_ink_in_every_column_is_close_to_the_edge_width(self, angle: float) -> None:
        """A 0.75 px edge puts 0.70 to 0.95 of ink in every column on one side, never a gap."""
        ink = [float(rows.sum()) for _, _, rows in self._lower_band(angle)]
        assert min(ink) >= 0.70
        assert max(ink) <= 0.95

    @ANGLES
    def test_the_edge_position_wobbles_little_along_the_line(self, angle: float) -> None:
        """The spread of the per-column ink about its fitted straight line is at most 0.10 px."""
        ink = np.array([float(rows.sum()) for _, _, rows in self._lower_band(angle)])
        x = np.arange(ink.size)
        assert float((ink - np.polyval(np.polyfit(x, ink, 1), x)).std()) <= 0.10
