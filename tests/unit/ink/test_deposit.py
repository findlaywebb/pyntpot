"""Tests for `deposit`: what it lays into the accumulators, and where.

Each sample's weights go bilinearly into the ink, reservoir and break-texture accumulators,
on those of the four pixels around the sample that fall on the grid.
"""

import dataclasses

import numpy as np
import pytest

from pyntpot.ink.brush import brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.deposit import deposit, pool


def one_sample(x: float, y: float) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Deposit one sample of weight one at `(x, y)` into fresh 8 by 8 accumulators."""
    acc = np.zeros((8, 8), dtype=np.float32)
    aux = {"res": np.zeros((8, 8), dtype=np.float32), "tooth": np.zeros((8, 8), dtype=np.float32)}
    pos = (np.array([[x]]), np.array([[y]]))
    ones = np.ones((1, 1), dtype=np.float32)
    deposit(acc, aux, pos, ones, ones, ones)
    return acc, aux


@pytest.mark.parametrize("name", ["ink", "res", "tooth"], ids=["ink", "res", "tooth"])
def test_a_sample_off_the_accumulator_lays_nothing(name: str) -> None:
    """A sample wholly off the plate lays no ink on its edge pixels."""
    acc, aux = one_sample(-5.0, 3.0)
    laid = acc if name == "ink" else aux[name]
    assert laid.sum() == 0.0
    assert laid[3, 0] == 0.0


def test_a_sample_half_off_the_edge_keeps_only_its_share_on_the_plate() -> None:
    """Only the corners on the grid receive their bilinear share."""
    acc, _ = one_sample(-0.5, 3.0)
    assert acc[3, 0] == 0.5
    assert acc.sum() == 0.5


def test_a_wide_pool_has_faded_to_nothing_at_the_side_of_its_span() -> None:
    """A wide pool's deposit at the side midpoint of its span is under 1.5% of its centre."""
    brush, _ = brush_from_id("MAJ1-e", 3.0, 2.0, BrushStyle())
    brush = dataclasses.replace(brush, width=60.0, pool=1.0, pool_gain=1.0)
    acc = np.zeros((201, 201), dtype=np.float32)
    pool(acc, brush, 100.0, 100.0)
    row = acc[100]
    reach = int(np.count_nonzero(row)) // 2
    assert reach > 0
    assert row[100 - reach] < 0.015 * row[100]


class TestTheFlatIndex:
    """On a non-square plate the flat index lands each share where the row and column pair does."""

    @staticmethod
    def _deposit(contiguous: bool) -> tuple[np.ndarray, dict[str, np.ndarray]]:
        """Lay a scatter of samples into fresh 5 by 9 accumulators, or into transposed views."""
        def plate() -> np.ndarray:
            return np.zeros((5, 9), np.float32) if contiguous else np.zeros((9, 5), np.float32).T

        acc, aux = plate(), {"res": plate(), "tooth": plate()}
        rng = np.random.default_rng(3)
        px = rng.uniform(-1.0, 9.5, (4, 6))
        py = rng.uniform(-1.0, 5.5, (4, 6))
        wgt = rng.random((4, 6), dtype=np.float32)
        deposit(acc, aux, (px, py), wgt, wgt * np.float32(0.5), wgt * np.float32(0.25))
        return acc, aux

    def test_a_view_that_is_not_contiguous_lays_the_same_bits(self) -> None:
        """A caller's transposed view takes the pair and lays exactly what a plain plate does."""
        assert not self._deposit(contiguous=False)[0].flags.c_contiguous
        flat_acc, flat_aux = self._deposit(contiguous=True)
        pair_acc, pair_aux = self._deposit(contiguous=False)
        assert np.array_equal(flat_acc, pair_acc)
        for name in ("res", "tooth"):
            assert np.array_equal(flat_aux[name], pair_aux[name]), name

    def test_one_sample_lands_on_its_four_pixels_of_a_non_square_plate(self) -> None:
        """A sample at (7.25, 3.5) on a 5 by 9 plate shares itself among rows 3, 4 and columns 7, 8."""
        acc = np.zeros((5, 9), np.float32)
        aux = {"res": np.zeros((5, 9), np.float32), "tooth": np.zeros((5, 9), np.float32)}
        ones = np.ones((1, 1), np.float32)
        deposit(acc, aux, (np.array([[7.25]]), np.array([[3.5]])), ones, ones, ones)
        want = np.zeros((5, 9), np.float32)
        want[3:5, 7:9] = [[0.375, 0.125], [0.375, 0.125]]
        for laid in (acc, aux["res"], aux["tooth"]):
            assert np.array_equal(laid, want)
