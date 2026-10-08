"""The water phase: the sea and the lakes filled and washed, and the sea worked along its shore."""

import dataclasses
import math

import numpy as np

from pyntpot.ink.noise import blur, chamfer_distance
from pyntpot.ink.sheet import Sheet
from pyntpot.ink.style import WashStyle
from pyntpot.ink.wash import WashOptions, wash
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.water import coast_run, paint_lakes, paint_water, sea_layer, sea_patches

from .jobs import square, tiny_job, tiny_style


def _sea_cover(h: int = 160, w: int = 220) -> np.ndarray:
    """A coast running down the card, sea to the left of it."""
    cov = np.zeros((h, w), np.float32)
    for r in range(h):
        cov[r, : 90 + int(12 * math.sin(r / 22.0))] = 1.0
    return cov


class TestSeaPatches:
    """The sea dries in patches along the shore."""

    def test_the_sea_dries_in_broad_patches_rather_than_flat(self):
        """The largest wash on the card stops reading as a fill."""
        cov = _sea_cover()
        sheet = Sheet(*cov.shape, gran_px=8.0, seed=5)
        style = WashStyle(sea_variation=True)
        flat = wash(cov, sheet, 0.60, 0.34, WashOptions(rim_px=7.0))
        varied = sea_patches(flat, cov, 3.0, style)
        body = cov > 0.5
        assert varied.min() >= 0.0 and varied.max() <= 1.0
        # Broader variation than the wash had, and still the same sea.
        coarse = blur(varied, 24.0)[body].std() / blur(flat, 24.0)[body].std()
        assert coarse > 1.5
        assert abs(float(varied[body].mean() - flat[body].mean())) < 0.06
        # Deterministic: the same card paints the same sea every time.
        assert np.array_equal(varied, sea_patches(flat, cov, 3.0, style))
        # And the amount is the dial: at 0 the wash comes back untouched.
        off = dataclasses.replace(style, sea_variation_amount=0.0)
        assert sea_patches(flat, cov, 3.0, off) is flat

    def test_the_streaking_runs_along_the_coast_not_across_it(self):
        """The direction is read off the shore, not chosen in advance."""
        cov = _sea_cover()
        angle = coast_run(chamfer_distance(cov <= 0.5), cov > 0.5, 40.0)
        # The shore runs down the card, so the run of it is about a quarter turn.
        assert abs(abs(angle) - math.pi / 2) < 0.35
        turned = coast_run(chamfer_distance(cov.T <= 0.5), cov.T > 0.5, 40.0)
        assert abs(turned) < 0.35  # the same coast laid the other way

    def test_no_shore_has_no_direction(self):
        """A card with no sea in reach of the band gives a run of zero."""
        cov = np.zeros((40, 40), np.float32)
        assert coast_run(chamfer_distance(cov <= 0.5), cov > 0.5, 20.0) == 0.0


class TestPaintWater:
    """The coverage and the water mask."""

    def test_the_sea_and_a_lake_are_filled_and_masked(self, tmp_path):
        """Each ring is filled into its own coverage and both mark the water."""
        job = tiny_job(
            tmp_path,
            sea=(square(0.0, 0.0, 80.0, 240.0),),
            lakes=(square(200.0, 100.0, 260.0, 160.0),),
        )
        stack = PlateStack.blank(job.shape)
        paint_water(job, stack)
        assert stack.sea_cov[60, 20] > 0.5 and stack.sea_cov[60, 120] == 0.0
        assert stack.lake_cov[65, 115] > 0.5 and stack.lake_cov[60, 20] == 0.0
        assert stack.water[60, 20] and stack.water[65, 115] and not stack.water[10, 80]

    def test_a_card_with_no_water_has_none(self, tmp_path):
        """No rings leave the coverage at zero and the mask empty."""
        job = tiny_job(tmp_path)
        stack = PlateStack.blank(job.shape)
        paint_water(job, stack)
        assert not stack.sea_cov.any() and not stack.lake_cov.any() and not stack.water.any()


class TestWashes:
    """The lakes' wash and the sea's wash."""

    def test_a_lake_is_washed_among_the_trimmed_layers(self, tmp_path):
        """A lake adds one layer in the water pigment; no lake adds none."""
        job = tiny_job(tmp_path, lakes=(square(200.0, 100.0, 260.0, 160.0),))
        stack = PlateStack.blank(job.shape)
        paint_water(job, stack)
        paint_lakes(job, stack)
        assert len(stack.trimmed) == 1
        density = stack.trimmed[0][0]
        assert density is not None
        assert density[65, 115] > density[10, 80]
        empty = PlateStack.blank(job.shape)
        paint_lakes(job, empty)
        assert empty.trimmed == []

    def test_the_sea_is_washed_to_the_card_edge_when_there_is_sea(self, tmp_path):
        """The sea's layer carries density over the sea, and is absent without sea."""
        job = tiny_job(tmp_path, sea=(square(0.0, 0.0, 80.0, 240.0),))
        stack = PlateStack.blank(job.shape)
        paint_water(job, stack)
        layer = sea_layer(job, stack)
        assert layer is not None
        assert layer[0] is not None
        assert layer[0][60, 10] > layer[0][60, 140]
        assert sea_layer(job, PlateStack.blank(job.shape)) is None

    def test_a_sea_not_painted_to_the_edge_has_no_layer(self, tmp_path):
        """With `sea_to_edge` off the sea lays no wash."""
        base = tiny_style()
        style = base.model_copy(
            update={"ribbon": dataclasses.replace(base.ribbon, sea_to_edge=False)}
        )
        job = tiny_job(tmp_path, style, sea=(square(0.0, 0.0, 80.0, 240.0),))
        stack = PlateStack.blank(job.shape)
        paint_water(job, stack)
        assert sea_layer(job, stack) is None
