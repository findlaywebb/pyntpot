"""The relief: the density painted from the sheet and the elevation patch alone."""

import numpy as np

from pyntpot.ink.sheet import Sheet
from pyntpot.maps.basemap import ElevationPatch
from pyntpot.maps.painter.paper import relief_density

from .jobs import tiny_job


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

    def test_strength_two_darkens_a_slope(self, tmp_path):
        """A strength of 2 gives a slope more density than the default, up to a doubled ceiling."""
        job = tiny_job(tmp_path)
        n = 8
        values = tuple(float(40 * c) for _r in range(n) for c in range(n))
        grid = ElevationPatch(
            n=n, x0=0.0, y0=0.0, x1=320.0, y1=240.0, values=values, low=0, high=280
        )
        sheet = Sheet(*job.shape, gran_px=6.0, seed=3)
        plain = relief_density(grid, job.canvas, sheet)
        strong = relief_density(grid, job.canvas, sheet, strength=2.0)
        assert strong.mean() > 1.5 * plain.mean()
        assert strong.max() <= 1.0
