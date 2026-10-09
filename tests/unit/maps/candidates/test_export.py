"""The candidate export: the basemap style it draws with and what it reads off the fixture."""

import dataclasses
import math
from pathlib import Path

from pyntpot.maps.cache import Cache
from pyntpot.maps.candidates.export import (
    CANDIDATE_BASEMAP,
    CANDIDATE_CLIP_MARGIN_M,
    candidate_export,
)
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures

#: The export's top-level keys, sorted.
EXPORT_KEYS = ["candidates", "climbs", "id", "points", "route"]

#: The keys of the export's `route`, sorted.
ROUTE_KEYS = ["settlements", "sustained_ascent_m", "total_km"]

#: The keys of every settlement the route passed, sorted.
SETTLEMENT_KEYS = ["kind", "km", "name", "off_route_m"]

#: The keys of every grounded climb, sorted.
CLIMB_KEYS = [
    "approach_trimmed_km",
    "avg_grade_pct",
    "bearing_deg",
    "bottom_ele_m",
    "end_km",
    "end_lat",
    "end_lng",
    "features",
    "from",
    "gain_m",
    "heading",
    "length_km",
    "near_start",
    "near_top",
    "of_climbs",
    "position_pct",
    "rank_by_gain",
    "rank_by_steepness",
    "roads",
    "runout_trimmed_km",
    "share_of_climbing_pct",
    "start_km",
    "start_lat",
    "start_lng",
    "steepest_500m_km",
    "steepest_500m_pct",
    "through",
    "to",
    "top_ele_m",
]

#: The keys of every landmark candidate, sorted.
CANDIDATE_KEYS = [
    "class",
    "distance_m",
    "lat",
    "lng",
    "name",
    "notable",
    "reach_m",
    "tags",
    "x",
    "y",
]


def _fixture_track() -> Track:
    """Return the fixture track, which carries no elevation."""
    return Track.from_gpx(FIXTURE_DIR / "track.gpx")


def _climbing_track() -> Track:
    """Return the fixture track with one synthetic rise and fall, so a climb is grounded."""
    track = _fixture_track()
    count = len(track.lat)
    ele = tuple(100.0 + 300.0 * math.sin(math.pi * i / count) for i in range(count))
    return Track(lat=track.lat, lng=track.lng, ele=ele)


def test_the_candidate_basemap_is_the_old_candidate_options() -> None:
    """The export's basemap equals the options it drew with before the style groups."""
    assert dataclasses.asdict(CANDIDATE_BASEMAP) == {
        "hillshade_mode": "off",
        "hillshade_levels": 5,
        "hillshade_opacity": 0.5,
        "hachure_spacing_m": 75.0,
        "hachure_min_slope": 0.035,
        "hachure_max_length_m": 90.0,
        "sea_style": "fill",
        "contour_interval": 50.0,
        "roads": "key",
        "rivers": "key",
        "interaction_m": 60.0,
        "interaction_run_m": 100.0,
        "landmarks": "all",
        "landmark_max": 80,
        "landmark_radius_m": 300.0,
        "pick_landmarks": (),
        "pick_roads": (),
        "pick_places": (),
        "generalise": False,
        "cell_m": 60.0,
        "morph_cells": 2,
        "min_area_ha": 4.0,
        "smooth_passes": 3,
        "blob_jitter_m": 22.0,
        "inset_cells": 2,
        "tree_spacing_m": 450.0,
        "all_variants": False,
    }
    assert CANDIDATE_CLIP_MARGIN_M == 2600.0


def test_the_real_box_offers_candidates_and_no_climb_without_elevation() -> None:
    """What the label step reads: named things and how far off; no climbs without elevation."""
    export = candidate_export(_fixture_track(), Cache(FIXTURE_DIR), KEY)
    names = {c["name"] for c in export["candidates"]}
    assert {"Lynmouth", "Lynton", "Countisbury"} <= names
    assert all(c["distance_m"] is not None for c in export["candidates"])
    assert export["climbs"] == [], "the fixture track carries no elevation"


def test_the_export_keys_are_the_contract() -> None:
    """The export carries exactly the keys its contract names, at every level."""
    export = candidate_export(_climbing_track(), Cache(FIXTURE_DIR), KEY)
    settlements = export["route"]["settlements"]
    assert settlements, "the fixture route passes a settlement"
    assert export["climbs"], "the synthetic rise grounds a climb"
    assert export["candidates"], "the fixture box holds a landmark candidate"
    assert sorted(export) == EXPORT_KEYS
    assert sorted(export["route"]) == ROUTE_KEYS
    assert all(sorted(s) == SETTLEMENT_KEYS for s in settlements)
    assert all(sorted(c) == CLIMB_KEYS for c in export["climbs"])
    assert all(sorted(c) == CANDIDATE_KEYS for c in export["candidates"])


def test_the_export_is_keyed_by_the_cache_key() -> None:
    """The export's `id` is the fetch cache key it reads under."""
    track = _fixture_track()
    export = candidate_export(track, Cache(FIXTURE_DIR), KEY)
    assert export["id"] == KEY
    assert Cache(FIXTURE_DIR).key(track, FixtureFeatures(), FixtureElevation()) == KEY


def test_an_empty_cache_exports_no_candidates_or_settlements(tmp_path: Path) -> None:
    """A box with nothing cached has no candidates and passes no settlements."""
    track = _fixture_track()
    export = candidate_export(track, Cache(tmp_path), KEY)
    assert export["candidates"] == []
    assert export["route"]["settlements"] == []
    assert export["points"] == len(track.lat)
