"""The ribbon phase: the trimmed extent of the ground, its pooled rim and the coast it never crosses."""

import numpy as np
import pytest

from pyntpot.ink.noise import edt
from pyntpot.ink.sheet import Sheet
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.ribbon import paint_ribbon, ribbon_alpha

from .jobs import tiny_job


def _loop_distance(size: int = 120) -> np.ndarray:
    """Distance to a square loop, so the inside of it is a hole."""
    mask = np.zeros((size, size), bool)
    mask[30, 30:90] = True
    mask[89, 30:90] = True
    mask[30:90, 30] = True
    mask[30:90, 89] = True
    return edt(mask)


class TestRibbonAlpha:
    """The extent and rim the ribbon trims the ground to."""

    def test_a_loop_is_filled_only_when_asked(self):
        """The inside of a loop is painted with fill on and left bare with it off."""
        sheet = Sheet(120, 120, gran_px=6.0, seed=4)
        d = _loop_distance()
        filled, _ = ribbon_alpha(d, 6.0, sheet, 1.0, fill=True)
        band, _ = ribbon_alpha(d, 6.0, sheet, 1.0, fill=False)
        assert filled[60, 60] > 0.9
        assert band[60, 60] < 0.1
        assert filled[5, 5] < 0.1

    def test_the_coast_stops_the_ribbon_and_its_rim(self):
        """Nothing the ribbon carries is laid on the sea side of a surveyed coast."""
        sheet = Sheet(120, 120, gran_px=6.0, seed=4)
        d = _loop_distance()
        land = np.ones((120, 120), np.float32)
        land[:, 70:] = 0.0
        free, _ = ribbon_alpha(d, 6.0, sheet, 1.0, fill=True)
        masked, rim = ribbon_alpha(d, 6.0, sheet, 1.0, fill=True, land=land)
        assert free[60, 80] > 0.5
        assert masked[:, 70:].max() == 0.0
        assert rim[:, 70:].max() == 0.0
        assert masked[60, 60] == pytest.approx(free[60, 60])


class TestPaintRibbon:
    """The ground the page multiplies over the card."""

    def test_an_empty_stack_is_white_ground_and_the_rim_is_on_the_plate(self, tmp_path):
        """With nothing laid the ground is white and the rim is a plate-sized density."""
        job = tiny_job(tmp_path)
        ground, rim = paint_ribbon(job, PlateStack.blank(job.shape))
        assert ground.shape == (*job.shape, 3)
        assert rim.shape == job.shape
        assert ground.min() == pytest.approx(1.0)
