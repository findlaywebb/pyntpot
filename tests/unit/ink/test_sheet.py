"""Tests for the sheet: what a fibre of zero leaves alone."""

import numpy as np

from pyntpot.ink.sheet import Sheet


def test_a_sheet_with_no_fibre_is_the_sheet_it_always_was():
    """The fibre draws last, so the five fields and the stream after them hold."""
    plain = Sheet(60, 90, gran_px=6.0, seed=4)
    same = Sheet(60, 90, gran_px=6.0, seed=4, fibre=0.0)
    laid = Sheet(60, 90, gran_px=6.0, seed=4, fibre=0.35)
    for name in ("paper", "coarse", "fine", "wet", "gran"):
        assert np.array_equal(getattr(plain, name), getattr(same, name))
        if name != "paper":
            assert np.array_equal(getattr(plain, name), getattr(laid, name))
    assert np.array_equal(plain.noise(20.0), same.noise(20.0))
    assert not np.array_equal(plain.paper, laid.paper)
