"""The relief phase: the shaded relief laid among the trimmed layers when there is a grid."""

import dataclasses

from pyntpot.maps.basemap import ElevationPatch
from pyntpot.maps.painter.job import PlateStack
from pyntpot.maps.painter.relief import paint_relief

from .jobs import tiny_job, tiny_style


def _slope() -> ElevationPatch:
    """A hillside over the whole card, rising to the east."""
    n = 8
    values = tuple(float(40 * c) for _r in range(n) for c in range(n))
    return ElevationPatch(n=n, x0=0.0, y0=0.0, x1=320.0, y1=240.0, values=values, low=0, high=280)


def test_a_grid_lays_one_relief_layer_in_the_relief_pigment(tmp_path):
    """One layer lands among the trimmed layers, carrying some density."""
    job = tiny_job(tmp_path, elevation=_slope())
    stack = PlateStack.blank(job.shape)
    paint_relief(job, stack)
    assert len(stack.trimmed) == 1
    density = stack.trimmed[0][0]
    assert density is not None
    assert density.shape == job.shape
    assert density.max() > 0.0


def test_no_grid_lays_nothing(tmp_path):
    """A basemap without elevation leaves the trimmed layers empty."""
    job = tiny_job(tmp_path)
    stack = PlateStack.blank(job.shape)
    paint_relief(job, stack)
    assert stack.trimmed == []


def test_relief_switched_off_lays_nothing(tmp_path):
    """The style's relief switch stops the phase even over a grid."""
    base = tiny_style()
    style = base.model_copy(update={"cover": dataclasses.replace(base.cover, relief=False)})
    job = tiny_job(tmp_path, style, elevation=_slope())
    stack = PlateStack.blank(job.shape)
    paint_relief(job, stack)
    assert stack.trimmed == []
