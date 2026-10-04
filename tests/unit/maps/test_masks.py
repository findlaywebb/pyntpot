"""Binary masks: rasterising, morphology and speck removal."""

from pyntpot.maps.masks import _components, _spread, declutter, rasterise


def _square(x0: float, y0: float, side: float) -> list[tuple[float, float]]:
    """One axis-aligned square ring in metres."""
    return [(x0, y0), (x0 + side, y0), (x0 + side, y0 + side), (x0, y0 + side)]


CLIP = (0.0, 0.0, 1200.0, 1200.0)


def test_a_mask_is_the_union_of_its_rings():
    """Two overlapping woods rasterise to one shape, not to two stacked ones."""
    mask = rasterise([_square(100, 100, 400), _square(300, 300, 400)], [], CLIP, 50.0)
    filled = sum(sum(row) for row in mask)
    assert filled > (400 / 50) ** 2
    assert filled < 2 * (400 / 50) ** 2


def test_a_hole_is_cut_out_of_the_mask():
    """A ring passed as a hole erases what it covers."""
    solid = rasterise([_square(100, 100, 600)], [], CLIP, 50.0)
    holed = rasterise([_square(100, 100, 600)], [_square(250, 250, 200)], CLIP, 50.0)
    assert sum(sum(r) for r in holed) < sum(sum(r) for r in solid)


def test_declutter_drops_a_speck_and_fills_a_pinhole():
    """A wood too small to matter goes, and so does a clearing too small to matter."""
    mask = rasterise(
        [_square(100, 100, 500), _square(1000, 1000, 80)], [_square(300, 300, 80)], CLIP, 50.0
    )
    assert len(_components(mask, 1)) == 2
    inner = [
        b
        for b in _components(mask, 0)
        if all(0 < r < len(mask) - 1 and 0 < c < len(mask[0]) - 1 for r, c in b)
    ]
    assert inner, "the fixture is meant to carry a pinhole"
    cleaned = declutter(mask, min_cells=8)
    assert len(_components(cleaned, 1)) == 1
    assert not [
        b
        for b in _components(cleaned, 0)
        if all(0 < r < len(cleaned) - 1 and 0 < c < len(cleaned[0]) - 1 for r, c in b)
    ]


def test_the_close_joins_two_woods_a_field_apart():
    """Closing is what turns a scatter of inclosures into one forest."""
    apart = rasterise([_square(100, 100, 300), _square(460, 100, 300)], [], CLIP, 50.0)
    assert len(_components(apart, 1)) == 2
    closed = _spread(_spread(apart, 2, grow=True), 2, grow=False)
    assert len(_components(closed, 1)) == 1
