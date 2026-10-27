"""Tests for the sheet: what a fibre of zero leaves alone, and the paper carried up to a finer grid."""

import numpy as np
from PIL import Image

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


class TestPaperOnAFinerGrid:
    """The paper carried up to a finer grid is made once per grid and is the bilinear grow of `paper`."""

    @staticmethod
    def _grown(sheet: Sheet, h: int, w: int) -> np.ndarray:
        """A fresh Pillow bilinear grow of the sheet's paper, as the pad made one per read."""
        img = Image.fromarray(np.asarray(sheet.paper, np.float32), "F")
        return np.asarray(img.resize((w, h), Image.Resampling.BILINEAR), np.float32)

    def test_it_is_the_bilinear_grow_and_is_made_once(self):
        """The same grid gives the same read-only array, equal to a fresh grow."""
        sheet = Sheet(30, 40, gran_px=6.0, seed=4)
        first = sheet._paper_on(90, 120)
        assert sheet._paper_on(90, 120) is first
        assert not first.flags.writeable
        assert np.array_equal(first, self._grown(sheet, 90, 120))

    def test_each_grid_gets_its_own(self):
        """A second grid is grown for itself, not handed the first."""
        sheet = Sheet(30, 40, gran_px=6.0, seed=4)
        twice, thrice = sheet._paper_on(60, 80), sheet._paper_on(90, 120)
        assert twice.shape == (60, 80)
        assert thrice.shape == (90, 120)
        assert np.array_equal(twice, self._grown(sheet, 60, 80))
