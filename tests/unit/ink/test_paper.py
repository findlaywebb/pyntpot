"""Tests for the paper plate: the cream paper painted from the sheet alone."""

import dataclasses

import numpy as np

from pyntpot.ink import Canvas, Sheet
from pyntpot.ink.paper import paper_plate
from pyntpot.ink.style import PaperStyle


def _paper(style: PaperStyle, display_px: int = 90) -> np.ndarray:
    """The paper plate of a 90 by 60 canvas, painted on a fresh sheet."""
    return paper_plate(Sheet(60, 90, 4.0, 11), Canvas(0, 0, 90, 60, 90, 60), style, display_px)


class TestPaperPlate:
    """The paper plate."""

    def test_the_paper_is_the_canvas_size_and_inside_the_unit_range(self):
        """The paper is an RGB array of the canvas's shape, within 0 to 1."""
        paper = _paper(PaperStyle())
        assert paper.shape == (60, 90, 3)
        assert paper.min() >= 0.0 and paper.max() <= 1.0

    def test_the_border_is_worn_darker_than_the_middle(self):
        """The edge of the paper carries more wear than its centre."""
        paper = _paper(PaperStyle())
        assert paper[0, :, :].mean() < paper[25:35, 40:50].mean()

    def test_a_grid_darkens_the_paper_along_its_lines(self):
        """Turning the grid on makes the paper darker overall."""
        plain = _paper(dataclasses.replace(PaperStyle(), grid=False), 80)
        ruled = _paper(dataclasses.replace(PaperStyle(), grid=True), 80)
        assert ruled.mean() < plain.mean()
