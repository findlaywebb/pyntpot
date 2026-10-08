"""Raster generalisation of rings."""

from pyntpot.maps.generalise import Generalisation, generalise


def _square(x0: float, y0: float, side: float) -> list[tuple[float, float]]:
    """One axis-aligned square ring in metres."""
    return [(x0, y0), (x0 + side, y0), (x0 + side, y0 + side), (x0, y0 + side)]


CLIP = (0.0, 0.0, 1200.0, 1200.0)


def test_generalise_returns_few_big_smooth_shapes():
    """The whole point: many intricate rings in, a handful of smooth ones out."""
    rings = [_square(100 + 60 * i, 100 + 40 * i, 220) for i in range(8)]
    rings += [_square(1100, 20, 30)]
    out = generalise(
        rings, [], CLIP, Generalisation(cell=50.0, morph_cells=2, min_area_ha=4.0, passes=3)
    )
    assert 1 <= len(out) <= 2
    assert all(len(ring) > 6 for ring in out)


def test_generalise_of_nothing_is_nothing():
    """An empty layer stays empty rather than becoming a full-map blob."""
    assert generalise([], [], CLIP, Generalisation(cell=50.0)) == []
