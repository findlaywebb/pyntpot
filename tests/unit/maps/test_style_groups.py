"""The style groups partition the painter's and the basemap's fields by reader.

Every painter field is in exactly one group or in `CONSUMER_ONLY`, every
basemap option is in `BasemapStyle`, each group's defaults are pinned (the
sourced groups by a digest of their fields, `BasemapStyle`'s as literals), and
each group's field names, in order, are pinned here as literals, which pins the
whole field-to-group table.
"""

import dataclasses
import hashlib
import json
from typing import Any

import pytest

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.letters.style import FaceStyle, HandStyle, NibStyle
from pyntpot.maps.style_groups import (
    CONSUMER_ONLY,
    BasemapStyle,
    CardStyle,
    CoverStyle,
    LetteringPolicy,
    RibbonStyle,
    RouteInks,
    RouteStyle,
)

#: Each group with its field names in order, copied from the pinned table.
PINNED: dict[type, tuple[str, ...]] = {
    PaperStyle: (
        "plate_lossless",
        "webp_quality",
        "paper_quality",
        "grid",
        "grid_spacing_px",
        "grid_opacity",
        "paper_hex",
        "paper_tooth",
        "paper_worn",
        "paper_vignette",
        "paper_foxing",
        "sheet_seed",
        "km_glazing",
        "pigment_transparency",
        "km_transparency",
        "paper_fibre",
        "paper_fibre_mix",
        "paper_fibre_stretch",
        "paper_fibre_angle",
        "paper_fibre_cell_px",
        "gran_gamma",
    ),
    WashStyle: (
        "wet_bleed",
        "wet_bleed_px",
        "wet_bleed_mix",
        "wet_rim_drop",
        "wet_bleed_edge_mult",
        "flow_rim",
        "flow_rim_exp",
        "flow_rim_ref_frac",
        "flow_rim_frac",
        "blooms",
        "bloom_density",
        "bloom_max",
        "bloom_radius_frac",
        "bloom_lift",
        "bloom_warp",
        "bloom_seed",
        "bloom_strength",
        "sea_variation",
        "sea_variation_cell_m",
        "sea_variation_amount",
        "sea_variation_streak",
        "sea_variation_elong",
        "sea_variation_band_m",
        "sea_variation_seed",
        "wet_close_px",
        "silhouette_deform",
        "silhouette_deform_amount",
        "silhouette_deform_decay",
        "silhouette_deform_depth",
        "silhouette_deform_max_m",
        "silhouette_deform_min_px",
        "silhouette_deform_seed",
        "pigment_separation",
        "separation_pigments",
        "separation_share",
        "separation_gamma",
        "separation_transparency",
        "fluid_pass",
        "fluid_grid",
        "fluid_steps",
        "fluid_relax",
        "fluid_amount",
        "fluid_gran",
        "fluid_seed",
    ),
    BrushStyle: (
        "ink_seed",
        "river_curve",
        "major_river_rel_frac",
        "minor_roads_mppd",
        "blotch_m",
        "dab_spacing_m",
        "gran_m",
        "river_mult",
        "brushes",
        "brush_width_px",
        "coast_width_frac",
        "brush_jitter_px",
        "brush_press_cell_px",
        "brush_wobble_px",
        "brush_step",
        "brush_profile_px",
        "pen_load_px_frac",
        "pen_pool_radius_frac",
        "pen_pool_gain",
        "brush_overrides",
        "ink_starve",
        "ink_reservoir",
        "ink_res_floor",
        "ink_dip_mult",
        "ink_knee",
        "dry_directional",
        "dry_dir_elong",
        "dry_dir_cell_px",
        "dry_dir_gain",
        "dry_dir_mix",
        "pen_starve",
        "pen_reservoir",
        "pen_thin",
        "ink_ss",
        "brush_organic",
        "organic_octaves",
        "organic_lacunarity",
        "organic_cell_mult",
        "ink_joins",
        "ink_join_tol_px",
        "stroke_smooth",
        "stroke_smooth_mult",
        "bristle_bandlimit_px",
        "bristle_contrast",
        "bristle_drift_coherence",
    ),
    FaceStyle: ("label_route", "label_face"),
    HandStyle: ("label_seed",),
    NibStyle: (
        "label_size_px",
        "label_ink",
        "label_brush",
        "label_pen_width_px",
        "label_outline_width_frac",
        "label_leader_brush",
        "label_leader_width_px",
        "label_pen_angle_deg",
        "label_pen_thin",
        "label_wash",
        "label_wash_alpha",
        "label_wash_dark_floor",
        "label_wash_spread",
        "label_route_ink",
        "label_water_ink",
        "label_in_water_ink",
    ),
    CardStyle: ("display_px", "supersample", "dark_grid"),
    RibbonStyle: (
        "ribbon_k",
        "ribbon_c",
        "ribbon_mult",
        "ribbon_min_m",
        "ribbon_max_m",
        "card_grow_mult",
        "card_pad_frac",
        "card_pad_ribbon_frac",
        "card_aspect_min",
        "card_aspect_max",
        "ribbon_fill",
        "ribbon_tear_frac",
        "ribbon_tear_floor_px",
        "rim_strength",
        "coast_hard_mask",
        "sea_to_edge",
    ),
    CoverStyle: (
        "dither_seed",
        "land_cover",
        "relief",
        "cover_cfg",
        "pigments",
        "pale_base",
        "pale_pool",
        "wood_texture",
        "wood_dabs",
        "wood_tex_scales",
        "wood_tex_strengths",
        "dab_spacings",
        "dab_strengths",
    ),
    RouteStyle: ("route_pen", "route_pen_brush", "route_pen_width_px"),
    BasemapStyle: (
        "hillshade_mode",
        "hillshade_levels",
        "hillshade_opacity",
        "hachure_spacing_m",
        "hachure_min_slope",
        "hachure_max_length_m",
        "sea_style",
        "contour_interval",
        "roads",
        "rivers",
        "interaction_m",
        "interaction_run_m",
        "landmarks",
        "landmark_max",
        "landmark_radius_m",
        "pick_landmarks",
        "pick_roads",
        "pick_places",
        "generalise",
        "cell_m",
        "morph_cells",
        "min_area_ha",
        "smooth_passes",
        "blob_jitter_m",
        "inset_cells",
        "tree_spacing_m",
        "all_variants",
    ),
    LetteringPolicy: (
        "label_max",
        "labels",
        "label_ground",
        "label_geom_tol_px",
        "home_glyph",
    ),
    RouteInks: ("run", "ride", "swim", "other"),
}

#: The groups that were copied from the flat painter style, each with the
#: pinned digest of its default fields: the first 16 hex digits of the SHA-256
#: of the fields as sorted-key JSON, which tells `0.2` from `0`.
SOURCED: dict[type, str] = {
    PaperStyle: "fe2d6474dad3b304",
    WashStyle: "e160d14a7793f90a",
    BrushStyle: "4160d6cacd208480",
    FaceStyle: "760ec6039a286528",
    HandStyle: "b25b34674433d32c",
    NibStyle: "76aa066043386bcf",
    CardStyle: "5e73ba4b178084f2",
    RibbonStyle: "6c8fdf4184013394",
    CoverStyle: "f201b60695520db7",
    RouteStyle: "e7af799eb721f445",
    LetteringPolicy: "252f33e095df0b01",
}

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
    "rivers": "key",
    "interaction_m": 60.0,
    "interaction_run_m": 100.0,
    "landmarks": "heuristic",
    "landmark_max": 8,
    "landmark_radius_m": 300.0,
    "pick_landmarks": (),
    "pick_roads": (),
    "pick_places": (),
    "generalise": True,
    "cell_m": 60.0,
    "morph_cells": 2,
    "min_area_ha": 4.0,
    "smooth_passes": 3,
    "blob_jitter_m": 22.0,
    "inset_cells": 2,
    "tree_spacing_m": 450.0,
    "all_variants": False,
}

GROUP_IDS = [group.__name__ for group in PINNED]
SOURCED_IDS = [group.__name__ for group in SOURCED]

#: The fields more than one layer reads, with the group the table puts each in.
MULTI_LAYER: tuple[tuple[str, type], ...] = (
    ("label_size_px", NibStyle),
    ("label_seed", HandStyle),
    ("label_route", FaceStyle),
    ("paper_hex", PaperStyle),
    ("sheet_seed", PaperStyle),
    ("display_px", CardStyle),
    ("brush_width_px", BrushStyle),
    ("label_geom_tol_px", LetteringPolicy),
)


def _names(cls: type[Any]) -> list[str]:
    """Return a dataclass's field names, in order."""
    return [spec.name for spec in dataclasses.fields(cls)]


def _grouped() -> list[str]:
    """Return every grouped field name plus `CONSUMER_ONLY`, repeats kept."""
    return [name for group in PINNED for name in _names(group)] + list(CONSUMER_ONLY)


def test_no_field_is_in_two_groups() -> None:
    """No field name appears in two groups or in a group and `CONSUMER_ONLY`."""
    grouped = _grouped()
    assert len(grouped) == len(set(grouped))


def test_clip_margin_is_not_a_style_field() -> None:
    """`clip_margin_m` is derived from the card per render, so no group holds it."""
    assert "clip_margin_m" not in _grouped()


def test_consumer_only_is_pinned() -> None:
    """`CONSUMER_ONLY` names the four fields no painter reads, in source order."""
    assert CONSUMER_ONLY == ("cover_order", "label_font", "label_pin_colour", "label_glow_colour")


@pytest.mark.parametrize(("group", "names"), PINNED.items(), ids=GROUP_IDS)
def test_group_fields_match_the_pinned_table(group: type, names: tuple[str, ...]) -> None:
    """Each group's field names, in order, equal the pinned table's row."""
    assert tuple(_names(group)) == names


@pytest.mark.parametrize(("group", "digest"), SOURCED.items(), ids=SOURCED_IDS)
def test_group_defaults_equal_the_pinned_digest(group: type, digest: str) -> None:
    """Each group's default fields, values and types, hash to the digest pinned for them."""
    blob = json.dumps(dataclasses.asdict(group()), sort_keys=True, default=str)
    assert hashlib.sha256(blob.encode()).hexdigest()[:16] == digest


@pytest.mark.parametrize(("name", "group"), MULTI_LAYER, ids=[name for name, _ in MULTI_LAYER])
def test_multi_layer_field_lands_in_its_table_group(name: str, group: type) -> None:
    """A field several layers read sits in the group the pinned table names."""
    assert name in _names(group)


def test_basemap_defaults_are_the_pinned_literals() -> None:
    """`BasemapStyle`'s defaults equal the pinned literals, value and type, field by field."""
    built = BasemapStyle()
    assert _names(BasemapStyle) == list(BASEMAP_DEFAULTS)
    for name, value in BASEMAP_DEFAULTS.items():
        assert getattr(built, name) == value, name
        assert type(getattr(built, name)) is type(value), name


@pytest.mark.parametrize("group", [*SOURCED, BasemapStyle], ids=[*SOURCED_IDS, "BasemapStyle"])
def test_groups_are_frozen(group: type) -> None:
    """A group refuses assignment, so a style value cannot change under a reader."""
    built: Any = group()
    first = _names(group)[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(built, first, getattr(built, first))
