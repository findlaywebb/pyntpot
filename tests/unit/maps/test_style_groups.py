"""The style groups partition the painter's and the basemap's fields by reader.

Every `PaintStyle` field is in exactly one group or in `CONSUMER_ONLY`, every
`GeoOptions` field but `clip_margin_m` is in `BasemapStyle`, each group's
defaults are its source class's defaults, and each group's field names, in
order, are pinned here as literals, which pins the whole field-to-group table.
"""

import dataclasses
from typing import Any

import pytest

from pyntpot._port.geo import GeoOptions
from pyntpot._port.paint import PaintStyle
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

#: The groups whose defaults copy a source class, with that class.
SOURCED: dict[type, type] = {
    group: GeoOptions if group is BasemapStyle else PaintStyle
    for group in PINNED
    if group is not RouteInks
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


def test_groups_cover_every_source_field() -> None:
    """The groups and `CONSUMER_ONLY` hold every source field and nothing else."""
    geo = set(_names(GeoOptions)) - {"clip_margin_m"}
    expected = set(_names(PaintStyle)) | geo | set(_names(RouteInks))
    assert set(_grouped()) == expected


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


@pytest.mark.parametrize(("group", "source"), SOURCED.items(), ids=SOURCED_IDS)
def test_group_defaults_equal_source_defaults(group: type, source: type) -> None:
    """Each group's dataclass defaults equal its source class's defaults, field by field."""
    built: Any = group()
    reference: Any = source()
    for name in _names(group):
        assert getattr(built, name) == getattr(reference, name), name


@pytest.mark.parametrize(("group", "source"), SOURCED.items(), ids=SOURCED_IDS)
def test_group_default_types_equal_source_types(group: type, source: type) -> None:
    """Each copied default has the same Python type as the source default, so 0.2 never reads as 0."""
    built: Any = group()
    reference: Any = source()
    for name in _names(group):
        assert type(getattr(built, name)) is type(getattr(reference, name)), name


@pytest.mark.parametrize(("name", "group"), MULTI_LAYER, ids=[name for name, _ in MULTI_LAYER])
def test_multi_layer_field_lands_in_its_table_group(name: str, group: type) -> None:
    """A field several layers read sits in the group the pinned table names."""
    assert name in _names(group)


@pytest.mark.parametrize("group", list(SOURCED), ids=SOURCED_IDS)
def test_groups_are_frozen(group: type) -> None:
    """A group refuses assignment, so a style value cannot change under a reader."""
    built: Any = group()
    first = _names(group)[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(built, first, getattr(built, first))
