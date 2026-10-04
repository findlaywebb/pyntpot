"""The candidate export: the basemap style it draws with and what it reads off the fixture."""

import dataclasses

from pyntpot.maps.cache import Cache
from pyntpot.maps.candidates.export import (
    CANDIDATE_BASEMAP,
    CANDIDATE_CLIP_MARGIN_M,
    landmark_export,
)
from pyntpot.maps.layers import BasemapInputs
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR, KEY


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
    track = Track.from_gpx(FIXTURE_DIR / "track.gpx")
    export = landmark_export(BasemapInputs(KEY, track, Cache(FIXTURE_DIR), []))
    names = {c["name"] for c in export["candidates"]}
    assert {"Lynmouth", "Lynton", "Countisbury"} <= names
    assert all(c["distance_m"] is not None for c in export["candidates"])
    assert export["climbs"] == [], "the fixture track carries no elevation"
