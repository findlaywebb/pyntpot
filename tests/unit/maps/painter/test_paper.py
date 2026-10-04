"""The card and the relief: arrays painted from the sheet and the grid alone."""

import dataclasses

import numpy as np

from pyntpot.ink.sheet import Sheet
from pyntpot.maps.basemap import ElevationPatch
from pyntpot.maps.painter.paper import paper_plate, relief_density
from pyntpot.maps.style import Style

from .jobs import tiny_job


class TestPaperPlate:
    """The notebook card."""

    def test_the_card_is_the_plates_size_and_inside_the_unit_range(self, tmp_path):
        """The card is an RGB array of the plate's shape, within 0 to 1."""
        job = tiny_job(tmp_path)
        style = Style.default()
        card = paper_plate(job.sheet, job.canvas, style.paper, style.card.display_px)
        assert card.shape == (*job.shape, 3)
        assert card.min() >= 0.0 and card.max() <= 1.0

    def test_the_border_is_worn_darker_than_the_middle(self, tmp_path):
        """The edge of the card carries more wear than its centre."""
        job = tiny_job(tmp_path)
        style = Style.default()
        card = paper_plate(job.sheet, job.canvas, style.paper, style.card.display_px)
        rh, rw = job.shape
        assert (
            card[0, :, :].mean() < card[rh // 2 - 5 : rh // 2 + 5, rw // 2 - 5 : rw // 2 + 5].mean()
        )

    def test_a_grid_darkens_the_card_along_its_lines(self, tmp_path):
        """Turning the grid on makes the card darker overall."""
        job = tiny_job(tmp_path)
        style = Style.default()
        gridded = dataclasses.replace(style.paper, grid=True)
        plain = paper_plate(job.sheet, job.canvas, dataclasses.replace(style.paper, grid=False), 80)
        ruled = paper_plate(job.sheet, job.canvas, gridded, 80)
        assert ruled.mean() < plain.mean()


class TestReliefDensity:
    """The shaded relief."""

    def test_a_hillside_gives_density_within_its_ceiling(self, tmp_path):
        """A slope shades the plate, and no density exceeds the relief's own ceiling."""
        job = tiny_job(tmp_path)
        n = 8
        values = tuple(float(40 * c) for _r in range(n) for c in range(n))
        grid = ElevationPatch(
            n=n, x0=0.0, y0=0.0, x1=320.0, y1=240.0, values=values, low=0, high=280
        )
        sheet = Sheet(*job.shape, gran_px=6.0, seed=3)
        dens = relief_density(grid, job.canvas, sheet)
        assert dens.shape == job.shape
        assert dens.max() > 0.0
        assert dens.max() <= 0.5
        assert np.isfinite(dens).all()
