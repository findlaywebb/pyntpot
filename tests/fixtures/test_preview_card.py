"""The preview fixture's features meet each other on the painted basemap, theme by theme."""

from pathlib import Path

import pytest
from architecture.test_coordinates import BOXES

from pyntpot.ink.polyline import foot_on
from pyntpot.maps import Basemap, Style, Track
from pyntpot.maps.cache import MARGIN_M
from pyntpot.maps.rings import point_in_ring, signed_area

from support import REPO_ROOT
from support.examples import load_example
from support.preview_fixture import (
    committed_elements,
    committed_track,
    copy_fixture,
    fetch_preview,
    to_metres,
)

#: The smallest card's theme, and the one theme whose card drops the lanes by design.
SMALLEST = "examples/themes/y-fenni.yaml"
NO_LANES = "ambleside-hero"

#: The card width the preview is painted at, and the width small patches are judged at.
PREVIEW_PX = 600
JUDGED_PX = 900

#: A patch under this many display pixels squared is folded into its neighbour (`ambleside-hero`'s value).
MIN_PATCH_PX = 400

#: Every packaged theme and every example theme file.
THEMES = (
    *Style.themes(),
    *(
        f"examples/themes/{p.name}"
        for p in sorted((REPO_ROOT / "examples" / "themes").glob("*.yaml"))
    ),
)


@pytest.fixture(scope="module", params=[None, SMALLEST], ids=["default", "y-fenni"])
def preview_card(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Basemap:
    """The preview's basemap at the preview width, in the default style and the smallest card's."""
    cache = copy_fixture(tmp_path_factory.mktemp("preview"))
    return fetch_preview(cache, request.param, PREVIEW_PX)


@pytest.fixture(scope="module", params=[None, SMALLEST], ids=["default", "y-fenni"])
def judged_card(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Basemap:
    """The preview's basemap at the width small patches are judged at."""
    cache = copy_fixture(tmp_path_factory.mktemp("judged"))
    return fetch_preview(cache, request.param, JUDGED_PX)


class TestTheFeaturesMeet:
    """The painted basemap holds each feature, in the default style and in the smallest card's."""

    def test_the_sea_and_both_coasts_are_there(self, preview_card: Basemap) -> None:
        """The card has a sea, an open coast chain that crosses it, and a closed ring for the island."""
        layers = preview_card.layers
        assert layers.sea
        closed = [c for c in layers.coastline if c[0] == c[-1]]
        assert len(closed) == 1
        assert len(layers.coastline) - len(closed) == 1

    def test_the_lake_holds_an_island(self, preview_card: Basemap) -> None:
        """A lake ring has another inside it, wound the other way."""
        rings = [list(r) for r in preview_card.layers.lakes]
        assert any(
            point_in_ring(*inner[0], outer) and signed_area(outer) * signed_area(inner) < 0
            for outer in rings
            for inner in rings
            if outer is not inner
        )

    def test_each_cover_class_is_there(self, preview_card: Basemap) -> None:
        """The card has wood, meadow, heath, built-up and rock."""
        assert {"wood", "meadow", "heath", "built", "rock"} <= preview_card.layers.cover.keys()

    def test_both_road_classes_are_there(self, preview_card: Basemap) -> None:
        """The card has a major road and a minor road."""
        assert {r.cls for r in preview_card.layers.roads} == {"major", "minor"}

    def test_the_river_splits_and_the_stream_joins(self, preview_card: Basemap) -> None:
        """The East Lyn River is two chains and the West Lyn River is a minor stream."""
        rivers = preview_card.layers.rivers
        assert [r.name for r in rivers].count("East Lyn River") == 2
        assert [r.cls for r in rivers if r.name == "West Lyn River"] == ["minor"]

    def test_the_settlements_and_landmarks_are_candidates(self, preview_card: Basemap) -> None:
        """Every place and landmark of the spec is a candidate to be lettered."""
        names = {c["name"] for c in preview_card.candidates}
        assert {"Lynmouth", "Lynton", "Countisbury", "Foreland Point", "Watersmeet"} <= names

    def test_small_patches_are_under_the_fold_at_nine_hundred_pixels(
        self, judged_card: Basemap
    ) -> None:
        """A meadow and a heath patch are each smaller than 400 display px squared at 900 px."""
        mpp = judged_card.card.mpp_display
        small = {
            cls: [
                r
                for r in judged_card.layers.cover[cls]
                if abs(signed_area(list(r))) / 2 / mpp**2 < MIN_PATCH_PX
            ]
            for cls in ("meadow", "heath")
        }
        assert all(small.values())


@pytest.mark.parametrize("theme", THEMES, ids=[Path(t).stem for t in THEMES])
def test_each_theme_paints_its_card_inside_the_fetch_box_with_lanes(
    theme: str, tmp_path: Path
) -> None:
    """Every theme's card lies inside the fetch box and the preview box, and paints lanes but for ambleside-hero."""
    cache = copy_fixture(tmp_path)
    basemap = fetch_preview(cache, theme, PREVIEW_PX)
    south, west, north, east = Track.from_gpx(cache / "track.gpx").bounding_box(MARGIN_M)
    (x0, y0), (x1, y1) = basemap.projection(south, west), basemap.projection(north, east)
    card_x0, card_y0, card_x1, card_y1 = basemap.card.box
    assert x0 <= card_x0 <= card_x1 <= x1
    assert y0 <= card_y0 <= card_y1 <= y1
    box_south, box_west, box_north, box_east = BOXES["preview"]
    assert box_south <= south <= north <= box_north
    assert box_west <= west <= east <= box_east
    assert basemap.layers.minor_roads == (Path(theme).stem != NO_LANES)


def test_the_example_pins_its_note_on_the_riverside_away_from_the_coast() -> None:
    """The example's `NOTE_POINT` is a track point within 40 m of the East Lyn River and 300 m from the coast."""
    note_point = load_example("theme_preview", "example_theme_preview")["NOTE_POINT"]
    point = committed_track()[note_point]
    coast = to_metres(committed_elements("overpass")[0]["geometry"])
    rivers = [
        to_metres(e["geometry"])
        for e in committed_elements("overpass")
        if e["tags"].get("name") == "East Lyn River"
    ]
    assert min(foot_on(point, line)[0] for line in rivers) <= 40
    assert foot_on(point, coast)[0] >= 300
