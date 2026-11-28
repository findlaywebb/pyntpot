"""The preview fixture is its generator's output, lies in its box, and holds every feature meeting the others."""

import dataclasses
import json
import math
import shutil
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest
from architecture.test_coordinates import BOXES
from fixtures.make_preview import make
from fixtures.preview_payloads import PROJECTION

from pyntpot.ink.polyline import cumulative_length, foot_on, segments_cross
from pyntpot.maps import (
    Basemap,
    Cache,
    OpenTopoData,
    OverpassFeatures,
    Style,
    Track,
    fetch,
)
from pyntpot.maps.cache import MARGIN_M
from pyntpot.maps.rings import point_in_ring, signed_area

from support import REPO_ROOT
from support.paths import FIXTURES, PREVIEW_KEY

#: The committed fixture.
PREVIEW_DIR = FIXTURES / "preview"

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"

#: The names the spec allows on the fixture, each a real place or feature of the Lynmouth area.
NAMES = {
    "Lynmouth",
    "Lynton",
    "East Lyn River",
    "West Lyn River",
    "Countisbury",
    "Watersmeet",
    "Foreland Point",
}

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

#: The tags of every feature element in writing order, and of every land cover element.
FEATURE_TAGS = [
    {"natural": "coastline"},
    {"natural": "coastline"},
    {"type": "multipolygon", "natural": "water"},
    {"waterway": "river", "name": "East Lyn River"},
    {"waterway": "river", "name": "East Lyn River"},
    {"waterway": "stream", "name": "West Lyn River"},
    {"highway": "primary"},
    {"highway": "unclassified"},
    {"natural": "wood"},
    {"natural": "wood"},
    {"place": "village", "name": "Lynmouth"},
    {"place": "town", "name": "Lynton"},
    {"place": "hamlet", "name": "Countisbury"},
    {"man_made": "lighthouse", "name": "Foreland Point"},
    {"tourism": "attraction", "name": "Watersmeet"},
]
LANDCOVER_TAGS = [
    {"natural": "shingle"},
    {"landuse": "meadow"},
    {"natural": "heath"},
    {"landuse": "residential"},
    {"natural": "bare_rock"},
    {"landuse": "meadow"},
    {"natural": "heath"},
]


def _payload(kind: str) -> dict[str, Any]:
    """Return one committed Overpass payload, `overpass` or `landcover`."""
    return json.loads((PREVIEW_DIR / f"{kind}-{PREVIEW_KEY}.json").read_text())


def _elements(kind: str) -> list[dict[str, Any]]:
    """Return a committed payload's elements."""
    return _payload(kind)["elements"]


def _tagged(kind: str, **tags: str) -> dict[str, Any]:
    """Return the first element of a payload carrying all of these tags."""
    return next(e for e in _elements(kind) if tags.items() <= e["tags"].items())


def _metres(geometry: list[dict[str, float]]) -> list[tuple[float, float]]:
    """Return an Overpass geometry array in the generator's metres."""
    return [PROJECTION(g["lat"], g["lon"]) for g in geometry]


def _track() -> list[tuple[float, float]]:
    """Return the committed track in metres."""
    track = Track.from_gpx(PREVIEW_DIR / "track.gpx")
    return [PROJECTION(lat, lng) for lat, lng in zip(track.lat, track.lng, strict=True)]


def _pairs(node: Any) -> Iterator[tuple[float, float]]:
    """Yield every latitude and longitude pair in a parsed payload, at any depth."""
    if isinstance(node, dict):
        if "lat" in node and "lon" in node:
            yield float(node["lat"]), float(node["lon"])
        for value in node.values():
            yield from _pairs(value)
    elif isinstance(node, list):
        for item in node:
            yield from _pairs(item)


def _copy(tmp_path: Path) -> Path:
    """Copy the fixture beside a test, as a cache directory the providers cannot refill."""
    cache = tmp_path / "cache"
    shutil.copytree(PREVIEW_DIR, cache)
    return cache


def _fetched(cache: Path, theme: str | None, display_px: int) -> Basemap:
    """Fetch the preview's basemap from a cache directory in a theme at a card width."""
    features = OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0)
    elevation = OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0)
    style = Style.from_theme(theme, relative_to=REPO_ROOT) if theme is not None else Style()
    style = style.model_copy(
        update={"card": dataclasses.replace(style.card, display_px=display_px)}
    )
    track = Track.from_gpx(cache / "track.gpx")
    return fetch(track, Cache(cache), features, elevation, style)


@pytest.fixture(scope="module", params=[None, SMALLEST], ids=["default", "y-fenni"])
def preview_card(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Basemap:
    """The preview's basemap at the preview width, in the default style and the smallest card's."""
    cache = _copy(tmp_path_factory.mktemp("preview"))
    return _fetched(cache, request.param, PREVIEW_PX)


@pytest.fixture(scope="module", params=[None, SMALLEST], ids=["default", "y-fenni"])
def judged_card(
    request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory
) -> Basemap:
    """The preview's basemap at the width small patches are judged at."""
    cache = _copy(tmp_path_factory.mktemp("judged"))
    return _fetched(cache, request.param, JUDGED_PX)


class TestTheCommittedFiles:
    """The fixture is the generator's output, named by the key, and every coordinate is in the box."""

    def test_the_generator_writes_the_committed_bytes(self, tmp_path: Path) -> None:
        """Running the generator into a new directory writes every committed file, byte for byte."""
        key = make(tmp_path)
        committed = sorted(p.name for p in PREVIEW_DIR.iterdir())
        assert sorted(p.name for p in tmp_path.iterdir()) == committed
        assert all((tmp_path / n).read_bytes() == (PREVIEW_DIR / n).read_bytes() for n in committed)
        assert key == PREVIEW_KEY

    def test_the_key_is_the_cache_key_of_the_committed_track(self) -> None:
        """`PREVIEW_KEY` is the key the default cache computes from the track read back from its GPX."""
        track = Track.from_gpx(PREVIEW_DIR / "track.gpx")
        key = Cache(PREVIEW_DIR).key(track, OverpassFeatures(CONTACT), OpenTopoData(CONTACT))
        assert key == PREVIEW_KEY

    def test_every_coordinate_is_in_the_preview_box(self) -> None:
        """Every latitude and longitude in the payloads, the elevation grid and the GPX is in the box."""
        south, west, north, east = BOXES["preview"]
        elevation = json.loads((PREVIEW_DIR / f"elevation-{PREVIEW_KEY}.json").read_text())
        track = Track.from_gpx(PREVIEW_DIR / "track.gpx")
        found = [
            *_pairs(_payload("overpass")),
            *_pairs(_payload("landcover")),
            *zip(track.lat, track.lng, strict=True),
            (elevation["bbox"][0], elevation["bbox"][1]),
            (elevation["bbox"][2], elevation["bbox"][3]),
            *((lat, elevation["bbox"][1]) for lat in elevation["lats"]),
            *((elevation["bbox"][0], lon) for lon in elevation["lons"]),
        ]
        assert found
        assert all(south <= lat <= north and west <= lon <= east for lat, lon in found)

    def test_the_fetch_box_is_in_the_preview_box(self) -> None:
        """The features fetch box of the default margin lies inside the preview box."""
        south, west, north, east = Track.from_gpx(PREVIEW_DIR / "track.gpx").bounding_box(MARGIN_M)
        box_south, box_west, box_north, box_east = BOXES["preview"]
        assert box_south <= south <= north <= box_north
        assert box_west <= west <= east <= box_east

    def test_every_name_is_one_the_spec_allows(self) -> None:
        """The names on the payloads are exactly the seven real names of the Lynmouth area."""
        names = {
            e["tags"]["name"]
            for kind in ("overpass", "landcover")
            for e in _elements(kind)
            if "name" in e["tags"]
        }
        assert names == NAMES

    def test_the_elements_carry_the_tags_of_their_table_rows(self) -> None:
        """Both payloads hold the tags the plan's element table names, in writing order, no road number."""
        assert [e["tags"] for e in _elements("overpass")] == FEATURE_TAGS
        assert [e["tags"] for e in _elements("landcover")] == LANDCOVER_TAGS

    def test_the_ids_run_one_up_across_both_payloads(self) -> None:
        """Element ids, relation members included, are 1, 2, 3 and so on in writing order, once each."""
        ids = [
            i
            for kind in ("overpass", "landcover")
            for e in _elements(kind)
            for i in (e["id"], *(m["ref"] for m in e.get("members", [])))
        ]
        assert ids == list(range(1, len(ids) + 1))

    def test_the_coast_and_the_island_are_wound_for_land_on_the_left(self) -> None:
        """The coast runs east to west, and the island is a long anticlockwise ring of 24 vertices or more."""
        coast, island = (e["geometry"] for e in _elements("overpass")[:2])
        assert coast[0]["lon"] > coast[-1]["lon"]
        ring = _metres(island)
        assert ring[0] == ring[-1]
        assert len(ring) > 24
        assert signed_area(ring[:-1]) > 0
        assert sum(math.dist(a, b) for a, b in pairwise(ring)) >= 600

    def test_the_elevation_grid_is_eighty_square_with_sea_and_a_hill(self) -> None:
        """The grid is 80 by 80 whole metres, 0 over the sea, and rises above its floor on a hill."""
        grid = json.loads((PREVIEW_DIR / f"elevation-{PREVIEW_KEY}.json").read_text())
        assert grid["n"] == 80
        assert len(grid["elev"]) == 80 * 80
        assert all(v == round(v) for v in grid["elev"])
        assert min(grid["elev"]) == 0
        assert max(grid["elev"]) > 250


class TestTheRoute:
    """The route is the size the plan frames the card from, keeps off the coast and doubles back."""

    def test_the_track_box_is_one_and_a_half_by_one_and_six_tenths_kilometres(self) -> None:
        """The track's box is 1.5 km east to west by 1.6 km north to south, each within 50 m."""
        points = _track()
        width = max(x for x, _ in points) - min(x for x, _ in points)
        height = max(y for _, y in points) - min(y for _, y in points)
        assert width == pytest.approx(1500, abs=50)
        assert height == pytest.approx(1600, abs=50)

    def test_every_track_point_is_three_hundred_metres_from_the_coast(self) -> None:
        """No track point lies within 300 m of the coast's line."""
        coast = _metres(_elements("overpass")[0]["geometry"])
        assert min(foot_on(p, coast)[0] for p in _track()) >= 300

    def test_the_route_doubles_back_beside_the_road_and_the_river(self) -> None:
        """Retraced stretches, points 400 m apart along the track within 30 m, run 300 m by the road and the river."""
        points = _track()
        along = cumulative_length(points)
        retraced = [
            any(
                abs(along[j] - along[i]) >= 400 and math.dist(p, points[j]) <= 30
                for j in range(len(points))
            )
            for i, p in enumerate(points)
        ]
        road = _metres(_tagged("overpass", highway="unclassified")["geometry"])
        rivers = [
            _metres(e["geometry"])
            for e in _elements("overpass")
            if e["tags"].get("name") == "East Lyn River"
        ]
        by_road = [foot_on(p, road)[0] <= 20 for p in points]
        by_river = [min(foot_on(p, line)[0] for line in rivers) <= 40 for p in points]
        assert any(retraced)
        assert (
            _longest_run(points, along, [r and b for r, b in zip(retraced, by_road, strict=True)])
            >= 300
        )
        assert (
            _longest_run(points, along, [r and b for r, b in zip(retraced, by_river, strict=True)])
            >= 300
        )

    def test_the_route_crosses_the_west_lyn_river_once(self) -> None:
        """The track crosses the stream at exactly one place."""
        stream = _metres(_tagged("overpass", waterway="stream")["geometry"])
        points = _track()
        crossings = sum(
            segments_cross(a, b, c, d) for a, b in pairwise(points) for c, d in pairwise(stream)
        )
        assert crossings == 1


def _longest_run(points: list[tuple[float, float]], along: list[float], flags: list[bool]) -> float:
    """Return the longest stretch of the track, in metres, whose consecutive points are all flagged."""
    best = run = 0.0
    for i in range(1, len(points)):
        run = run + along[i] - along[i - 1] if flags[i] and flags[i - 1] else 0.0
        best = max(best, run)
    return best


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
    cache = _copy(tmp_path)
    basemap = _fetched(cache, theme, PREVIEW_PX)
    south, west, north, east = Track.from_gpx(cache / "track.gpx").bounding_box(MARGIN_M)
    (x0, y0), (x1, y1) = basemap.projection(south, west), basemap.projection(north, east)
    card_x0, card_y0, card_x1, card_y1 = basemap.card.box
    assert x0 <= card_x0 <= card_x1 <= x1
    assert y0 <= card_y0 <= card_y1 <= y1
    box_south, box_west, box_north, box_east = BOXES["preview"]
    assert box_south <= south <= north <= box_north
    assert box_west <= west <= east <= box_east
    assert basemap.layers.minor_roads == (Path(theme).stem != NO_LANES)
