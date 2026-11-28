"""The preview fixture is its generator's output, lies in its box, and its route keeps to the README."""

import json
import math
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import Any

import pytest
from architecture.test_coordinates import (
    BOXES,
)  # the gate's table is the one source of the box; it must stay in the gate's exempt file
from fixtures.make_preview import make

from pyntpot.ink.polyline import cumulative_length, foot_on, segments_cross
from pyntpot.maps import Cache, OpenTopoData, OverpassFeatures, Track
from pyntpot.maps.cache import MARGIN_M
from pyntpot.maps.rings import signed_area

from support.paths import PREVIEW_KEY
from support.preview_fixture import (
    CONTACT,
    PREVIEW_DIR,
    committed_elements,
    committed_payload,
    committed_track,
    tagged,
    to_metres,
)

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
            *_pairs(committed_payload("overpass")),
            *_pairs(committed_payload("landcover")),
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
            for e in committed_elements(kind)
            if "name" in e["tags"]
        }
        assert names == NAMES

    def test_the_elements_carry_the_tags_of_their_table_rows(self) -> None:
        """Both payloads hold the tags the README's feature table names, in writing order, no road number."""
        assert [e["tags"] for e in committed_elements("overpass")] == FEATURE_TAGS
        assert [e["tags"] for e in committed_elements("landcover")] == LANDCOVER_TAGS

    def test_the_ids_run_one_up_across_both_payloads(self) -> None:
        """Element ids, relation members included, are 1, 2, 3 and so on in writing order, once each."""
        ids = [
            i
            for kind in ("overpass", "landcover")
            for e in committed_elements(kind)
            for i in (e["id"], *(m["ref"] for m in e.get("members", [])))
        ]
        assert ids == list(range(1, len(ids) + 1))

    def test_the_coast_and_the_island_are_wound_for_land_on_the_left(self) -> None:
        """The coast runs east to west, and the island is a long anticlockwise ring of 24 vertices or more."""
        coast, island = (e["geometry"] for e in committed_elements("overpass")[:2])
        assert coast[0]["lon"] > coast[-1]["lon"]
        ring = to_metres(island)
        assert ring[0] == ring[-1]
        assert len(ring) > 24
        assert signed_area(ring[:-1]) > 0
        assert sum(math.dist(a, b) for a, b in pairwise(ring)) >= 600

    def test_the_roads_cross_the_rivers_and_each_other(self) -> None:
        """In metres, the major road crosses the minor road, the East Lyn River and the stream; the minor road crosses the East Lyn River."""
        major = to_metres(tagged("overpass", highway="primary")["geometry"])
        minor = to_metres(tagged("overpass", highway="unclassified")["geometry"])
        east_lyn = [
            to_metres(e["geometry"])
            for e in committed_elements("overpass")
            if e["tags"].get("name") == "East Lyn River"
        ]
        stream = to_metres(tagged("overpass", waterway="stream")["geometry"])

        def crosses(one: list[tuple[float, float]], other: list[tuple[float, float]]) -> bool:
            return any(
                segments_cross(a, b, c, d) for a, b in pairwise(one) for c, d in pairwise(other)
            )

        assert crosses(major, minor)
        assert any(crosses(major, line) for line in east_lyn)
        assert crosses(major, stream)
        assert any(crosses(minor, line) for line in east_lyn)

    def test_the_elevation_grid_is_eighty_square_with_sea_and_a_hill(self) -> None:
        """The grid is 80 by 80 whole metres, 0 over the sea, and rises above its floor on a hill."""
        grid = json.loads((PREVIEW_DIR / f"elevation-{PREVIEW_KEY}.json").read_text())
        assert grid["n"] == 80
        assert len(grid["elev"]) == 80 * 80
        assert all(v == round(v) for v in grid["elev"])
        assert min(grid["elev"]) == 0
        assert max(grid["elev"]) > 250


class TestTheRoute:
    """The route is the size the card is framed from, keeps off the coast and doubles back."""

    def test_the_track_box_is_one_and_a_half_by_one_and_six_tenths_kilometres(self) -> None:
        """The track's box is 1.5 km east to west by 1.6 km north to south, each within 50 m."""
        points = committed_track()
        width = max(x for x, _ in points) - min(x for x, _ in points)
        height = max(y for _, y in points) - min(y for _, y in points)
        assert width == pytest.approx(1500, abs=50)
        assert height == pytest.approx(1600, abs=50)

    def test_every_track_point_is_three_hundred_metres_from_the_coast(self) -> None:
        """No track point lies within 300 m of the coast's line."""
        coast = to_metres(committed_elements("overpass")[0]["geometry"])
        assert min(foot_on(p, coast)[0] for p in committed_track()) >= 300

    def test_the_route_doubles_back_beside_the_road_and_the_river(self) -> None:
        """Retraced stretches, points 400 m apart along the track within 30 m, run 300 m by the road and the river."""
        points = committed_track()
        along = cumulative_length(points)
        retraced = [
            any(
                abs(along[j] - along[i]) >= 400 and math.dist(p, points[j]) <= 30
                for j in range(len(points))
            )
            for i, p in enumerate(points)
        ]
        road = to_metres(tagged("overpass", highway="unclassified")["geometry"])
        rivers = [
            to_metres(e["geometry"])
            for e in committed_elements("overpass")
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
        stream = to_metres(tagged("overpass", waterway="stream")["geometry"])
        points = committed_track()
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
