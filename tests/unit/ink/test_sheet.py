"""Tests for the sheet: what a fibre of zero leaves alone, and the paper carried up to a finer grid."""

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.sheet import Canvas, Sheet


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

    def test_a_replaced_paper_is_grown_afresh(self):
        """A sheet given another paper array grows that one, not the copy kept from the first."""
        sheet = Sheet(30, 40, gran_px=6.0, seed=4)
        first = sheet._paper_on(60, 80)
        sheet.paper = np.zeros_like(sheet.paper)
        again = sheet._paper_on(60, 80)
        assert again is not first
        assert not again.any()


class TestCanvasPixels:
    """`Canvas.pixels` is a canvas that is only its pixel grid."""

    def test_it_equals_the_canvas_built_by_hand(self):
        """`Canvas.pixels(w=90, h=60)` is `Canvas(0, 0, 90, 60, 90, 60)`."""
        assert Canvas.pixels(w=90, h=60) == Canvas(0, 0, 90, 60, 90, 60)

    def test_one_world_unit_is_one_pixel(self):
        """The scale is exactly 1 and `px` returns its points unchanged."""
        canvas = Canvas.pixels(w=90, h=60)
        assert canvas.scale == 1.0
        points = np.array([[0.0, 0.0], [12.5, 30.0]])
        assert np.array_equal(canvas.px(points), np.array([[0.0, 60.0], [12.5, 30.0]]))

    @pytest.mark.parametrize(
        ("w", "h"),
        [(0, 60), (90, 0), (-1, 60)],
        ids=["zero-width", "zero-height", "negative-width"],
    )
    def test_a_side_under_one_is_refused(self, w: int, h: int):
        """A width or height under 1 raises ValueError."""
        with pytest.raises(ValueError, match="at least 1"):
            Canvas.pixels(w=w, h=h)
