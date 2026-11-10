"""`BasemapStyle`'s defaults are pinned as literals, value and type, field by field."""

import dataclasses
from typing import Any

from pyntpot.maps.style_groups import BasemapStyle

#: `BasemapStyle`'s defaults, the basemap options' class defaults, as pinned literals.
BASEMAP_DEFAULTS: dict[str, Any] = {
    "hillshade_mode": "off",
    "hillshade_levels": 5,
    "hillshade_opacity": 0.5,
    "hachure_spacing_m": 75.0,
    "hachure_min_slope": 0.035,
    "hachure_max_length_m": 90.0,
    "sea_style": "fill",
    "contour_interval": 50.0,
    "roads": "key",
    "minor_road_classes": ("tertiary", "unclassified", "residential", "track", "service"),
    "rivers": "key",
    "interaction_m": 60.0,
    "interaction_run_m": 100.0,
    "landmarks": "all",
    "landmark_max": 40,
    "landmark_radius_m": 300.0,
    "pick_landmarks": (),
    "pick_roads": (),
    "pick_places": (),
    "name_tags": ("name",),
    "generalise": False,
    "cell_m": 60.0,
    "morph_cells": 2,
    "min_area_ha": 4.0,
    "smooth_passes": 3,
    "blob_jitter_m": 22.0,
    "inset_cells": 2,
    "tree_spacing_m": 450.0,
    "all_variants": False,
    "line_effects": {},
}


def test_basemap_defaults_are_the_pinned_literals() -> None:
    """`BasemapStyle`'s defaults equal the pinned literals, value and type, field by field."""
    built = BasemapStyle()
    assert [spec.name for spec in dataclasses.fields(BasemapStyle)] == list(BASEMAP_DEFAULTS)
    for name, value in BASEMAP_DEFAULTS.items():
        assert getattr(built, name) == value, name
        assert type(getattr(built, name)) is type(value), name
