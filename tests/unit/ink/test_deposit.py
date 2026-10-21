"""Tests for `deposit`: what it lays into the accumulators, and where.

Each sample's weights go bilinearly into the ink, reservoir and break-texture accumulators,
on those of the four pixels around the sample that fall on the grid.
"""

import numpy as np
import pytest

from pyntpot.ink.deposit import deposit


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
