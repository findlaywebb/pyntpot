"""Exact checks on the paper plate: the warm edge's pinned pixels, its clips and the grid's lines."""

import dataclasses

import numpy as np
import pytest

from pyntpot.ink import Canvas, Sheet
from pyntpot.ink.paper import PAPER_EDGE_TINT, paper_plate
from pyntpot.ink.sheet import rgb
from pyntpot.ink.style import PaperStyle

#: Pixel values of the warm plate of `_plate(_STRONG)`, read from the code as it stands.
_PINS = {
    (0, 0): (0.6718849, 0.5331711, 0.3700249),
    (0, 7): (0.6554615, 0.5123263, 0.3473368),
    (3, 30): (0.7231022, 0.6007869, 0.4483889),
    (8, 45): (0.8487879, 0.7712075, 0.6537945),
    (30, 5): (0.7657468, 0.6577462, 0.5155638),
    (7, 28): (0.5788934, 0.3836071, 0.2478840),
    (8, 28): (0.5910897, 0.3957918, 0.2595933),
    (16, 40): (0.6324167, 0.4299972, 0.2901215),
}

_STRONG = PaperStyle(paper_tooth=0.0, paper_worn=0.5, paper_vignette=0.6, paper_foxing=0.9)


def _plate(style: PaperStyle, display_px: int = 90) -> np.ndarray:
    """The paper plate of a 90 by 60 canvas, painted on a fresh sheet."""
    sheet = Sheet(w=90, h=60, gran_px=4.0, seed=11)
    return paper_plate(sheet, Canvas(0, 0, 90, 60, 90, 60), style, display_px)


def _grid_ratio(spacing: float, display_px: int) -> np.ndarray:
    """The plate with a full-opacity grid over the same plate without one: the grid's factor."""
    bare = dataclasses.replace(PaperStyle(), paper_tooth=0.0, grid=False)
    ruled = dataclasses.replace(bare, grid=True, grid_spacing_px=spacing, grid_opacity=1.0)
    return (_plate(ruled, display_px) / _plate(bare, display_px))[..., 0]


class TestWarmPlatePins:
    """The warm plate at fixed pixels."""

    @pytest.mark.parametrize("pixel", list(_PINS), ids=[f"y{y}-x{x}" for y, x in _PINS])
    def test_a_pixel_of_the_strong_warm_plate_is_pinned(self, pixel: tuple[int, int]):
        """The wear, the vignette and the foxing give these RGB values, within 1e-5."""
        assert np.allclose(_plate(_STRONG)[pixel], _PINS[pixel], atol=1e-5, rtol=0)

    def test_full_wear_clips_to_the_tint_and_leaves_the_middle_alone(self):
        """At wear 1 no border pixel is darker than the paper times the tint, and the middle is clear."""
        style = PaperStyle(paper_tooth=0.0, paper_worn=1.0, paper_vignette=0.0, paper_foxing=0.0)
        plate = _plate(style)
        full = rgb(style.paper_hex) * PAPER_EDGE_TINT
        assert (plate[0] >= full - 1e-6).all()
        assert np.allclose(plate[0].min(axis=0), full, atol=1e-6)
        assert np.allclose(plate[30, 45], rgb(style.paper_hex), atol=0.02)

    def test_a_tooth_past_the_range_is_clipped_to_0_to_1(self):
        """A tooth of 4 would push the paper below 0 and above 1; the plate stays within 0 to 1."""
        plate = _plate(PaperStyle(paper_tooth=4.0))
        assert plate.min() == 0.0 and plate.max() == 1.0


class TestGridLines:
    """The grid's lines: where they fall and how dark they are."""

    def test_a_row_line_a_column_line_and_their_crossing(self):
        """A 10 pixel grid at full opacity darkens a row by 0.3, a column by 0.165 and both by 0.3."""
        ratio = _grid_ratio(10.0, 90)
        assert ratio[0, 5] == pytest.approx(0.7, abs=1e-5)
        assert ratio[5, 0] == pytest.approx(0.835, abs=1e-5)
        assert ratio[0, 0] == pytest.approx(0.7, abs=1e-5)
        assert ratio[5, 5] == pytest.approx(1.0, abs=1e-5)

    def test_a_line_is_one_pixel_wide_and_repeats_every_step(self):
        """The pixel after a line is clear, and the next line is a step on."""
        ratio = _grid_ratio(10.0, 90)
        assert ratio[1, 5] == pytest.approx(1.0, abs=1e-5)
        assert ratio[5, 1] == pytest.approx(1.0, abs=1e-5)
        assert ratio[10, 5] == pytest.approx(0.7, abs=1e-5)
        assert ratio[5, 10] == pytest.approx(0.835, abs=1e-5)

    def test_a_step_between_4_and_5_pixels_is_kept(self):
        """A 4.5 pixel step puts a row line at row 9, where a 5 pixel step would not."""
        assert _grid_ratio(4.5, 90)[9, 5] == pytest.approx(0.7, abs=1e-5)

    def test_a_display_width_of_zero_is_read_as_one(self):
        """At display width 0 the step is 45 pixels: a line at row 45, none at row 23."""
        ratio = _grid_ratio(0.5, 0)
        assert ratio[45, 5] == pytest.approx(0.7, abs=1e-5)
        assert ratio[23, 5] == pytest.approx(1.0, abs=1e-5)


class TestFoxingShare:
    """The foxed share of the sheet."""

    def test_the_pixel_at_the_speck_level_is_foxed(self):
        """On a 77 by 13 sheet the level sits on one pixel's grain; that pixel and three more are foxed."""
        sheet = Sheet(w=77, h=13, gran_px=2.0, seed=11)
        canvas = Canvas.pixels(w=77, h=13)
        bare = PaperStyle(paper_tooth=0.0, paper_worn=0.0, paper_vignette=0.0, paper_foxing=0.0)
        foxed = dataclasses.replace(bare, paper_foxing=0.9)
        clean = paper_plate(sheet, canvas, bare)
        sheet = Sheet(w=77, h=13, gran_px=2.0, seed=11)
        assert (np.abs(paper_plate(sheet, canvas, foxed) - clean).max(axis=2) > 0).sum() == 4
