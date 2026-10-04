"""The card frame: card metres to display and render pixels, and back."""

import pytest

from pyntpot.maps.card import Card

#: A manifest's frame keys, written here rather than read from a golden file.
MANIFEST = {
    "card": [-1234.5, -876.25, 1965.5, 1311.25],
    "display": [1024, 700],
    "render": [3072, 2100],
    "mpp": 1.0416667,
    "mpp_display": 3.125,
}

#: Points in card metres and the display pixels the replaced card class put them at.
PINNED_XY = (
    ((0.0, 0.0), (395.04, 419.6)),
    ((512.3, -77.7), (558.976, 444.464)),
    ((1800.125, 1250.875), (971.08, 19.32)),
)


def test_box_corners_map_to_the_display_corners() -> None:
    """The box's lower-left corner is the display's bottom-left and its upper-right the top-right."""
    card = Card.from_manifest(MANIFEST)
    x0, y0, x1, y1 = card.box
    assert card.xy(x0, y0) == pytest.approx((0.0, card.h), abs=1e-9)
    assert card.xy(x1, y1) == pytest.approx((card.w, 0.0), abs=1e-9)


@pytest.mark.parametrize("offset", [(0.0, 0.0), (13.5, -6.25)], ids=["no-offset", "offset"])
def test_xy_then_metres_round_trips(offset: tuple[float, float]) -> None:
    """Metres taken to display pixels and back come home to within 1e-9."""
    card = Card.from_manifest(MANIFEST, offset=offset)
    for (x, y), _ in PINNED_XY:
        assert card.metres(*card.xy(x, y)) == pytest.approx((x, y), abs=1e-9)


def test_from_manifest_yields_the_pinned_frame() -> None:
    """A manifest's frame keys give the pinned display size, scales and fields."""
    card = Card.from_manifest(MANIFEST)
    assert (card.w, card.h) == (1024, 700)
    assert card.scale == 0.32
    assert card.render_scale == 3.0
    assert card.box == (-1234.5, -876.25, 1965.5, 1311.25)
    assert card.render == (3072, 2100)
    assert (card.mpp, card.mpp_display) == (1.0416667, 3.125)
    assert card.offset == (0.0, 0.0)


@pytest.mark.parametrize(("point", "want"), PINNED_XY, ids=["origin", "inside", "near-top-right"])
def test_xy_matches_the_replaced_card_class(
    point: tuple[float, float], want: tuple[float, float]
) -> None:
    """`xy` puts each pinned point exactly where the replaced card class did."""
    assert Card.from_manifest(MANIFEST).xy(*point) == want


def test_xy_with_an_offset_matches_the_replaced_card_class() -> None:
    """An offset shifts the point before projecting, exactly as the replaced card class did."""
    card = Card.from_manifest(MANIFEST, offset=(13.5, -6.25))
    assert card.xy(512.3, -77.7) == (563.296, 446.464)


def test_to_render_scales_display_pixels_to_the_render_grid() -> None:
    """A point in render pixels is its display pixel times the render scale."""
    card = Card.from_manifest(MANIFEST)
    assert card.to_render(1800.125, 1250.875) == pytest.approx((2913.24, 57.96), abs=1e-9)
