"""Tests for the sheet: what a fibre of zero leaves alone, and the paper carried up to a finer grid."""

import numpy as np
import pytest
from PIL import Image

from pyntpot.ink.sheet import Canvas, Sheet


def test_a_sheet_with_no_fibre_is_the_sheet_it_always_was():
    """The fibre draws last, so the five fields and the stream after them hold."""
    plain = Sheet(w=90, h=60, gran_px=6.0, seed=4)
    same = Sheet(w=90, h=60, gran_px=6.0, seed=4, fibre=0.0)
    laid = Sheet(w=90, h=60, gran_px=6.0, seed=4, fibre=0.35)
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
        sheet = Sheet(w=40, h=30, gran_px=6.0, seed=4)
        first = sheet._paper_on(90, 120)
        assert sheet._paper_on(90, 120) is first
        assert not first.flags.writeable
        assert np.array_equal(first, self._grown(sheet, 90, 120))

    def test_each_grid_gets_its_own(self):
        """A second grid is grown for itself, not handed the first."""
        sheet = Sheet(w=40, h=30, gran_px=6.0, seed=4)
        twice, thrice = sheet._paper_on(60, 80), sheet._paper_on(90, 120)
        assert twice.shape == (60, 80)
        assert thrice.shape == (90, 120)
        assert np.array_equal(twice, self._grown(sheet, 60, 80))

    def test_a_replaced_paper_is_grown_afresh(self):
        """A sheet given another paper array grows that one, not the copy kept from the first."""
        sheet = Sheet(w=40, h=30, gran_px=6.0, seed=4)
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
        """The scale is exactly 1 and `px` maps `(x, y)` to `(x, h - y)`: no scaling, north up."""
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

    @pytest.mark.parametrize(
        ("w", "h"), [(1, 1), (1, 5), (5, 1)], ids=["one", "one-wide", "one-high"]
    )
    def test_a_side_of_one_is_taken(self, w: int, h: int):
        """A width or height of exactly 1 is a canvas of that grid."""
        assert Canvas.pixels(w=w, h=h) == Canvas(0, 0, w, h, w, h)


class TestSheetTakesKeywords:
    """`Sheet` is keyword-only, width first, and the order of the keywords does not matter."""

    def test_a_positional_call_is_refused(self):
        """`Sheet(240, 360, 8.0, 11)` raises TypeError."""
        with pytest.raises(TypeError, match="positional"):
            Sheet(240, 360, 8.0, 11)  # ty: ignore[too-many-positional-arguments, missing-argument]

    def test_the_five_fields_are_height_by_width(self):
        """Each field of `Sheet(w=360, h=240, ...)` has shape `(240, 360)`."""
        sheet = Sheet(w=360, h=240, gran_px=8.0, seed=11)
        for name in ("paper", "coarse", "fine", "wet", "gran"):
            assert getattr(sheet, name).shape == (240, 360)

    def test_keyword_order_cannot_matter(self):
        """`Sheet(h=240, w=360, ...)` gives the same five arrays, bit for bit."""
        width_first = Sheet(w=360, h=240, gran_px=8.0, seed=11)
        height_first = Sheet(h=240, w=360, seed=11, gran_px=8.0)
        for name in ("paper", "coarse", "fine", "wet", "gran"):
            assert np.array_equal(getattr(width_first, name), getattr(height_first, name))
