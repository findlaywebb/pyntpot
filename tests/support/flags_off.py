"""The style groups with every phase flag off: the values the engine's mechanism tests pin.

Key names: `FLAGS_OFF`, the field values by group, and `flags_off`, which builds one
group with them. These are test data, named for what they are: the 25 values the
style groups held before ADR 0069 made the defaults the default look. No package code
reads them. Not a second set of defaults: the guard in
`tests/architecture/test_one_source_of_defaults.py` checks package files only.
"""

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.maps.style_groups import BasemapStyle

#: The 25 field values, by group, that turn every phase flag off and its tuning inert.
FLAGS_OFF: dict[type, dict[str, object]] = {
    PaperStyle: {"km_glazing": False, "paper_fibre": False},
    WashStyle: {
        "wet_bleed": False,
        "flow_rim": False,
        "blooms": False,
        "sea_variation": False,
        "silhouette_deform": False,
        "pigment_separation": False,
        "fluid_pass": False,
        "wet_bleed_px": 5.0,
        "wet_bleed_mix": 0.55,
        "wet_rim_drop": 0.7,
        "bloom_strength": 1.0,
        "wet_close_px": 0.0,
        "separation_share": 0.22,
        "fluid_amount": 0.30,
    },
    BrushStyle: {
        "ink_starve": False,
        "dry_directional": False,
        "pen_starve": False,
        "brush_organic": False,
        "ink_joins": False,
        "stroke_smooth": False,
    },
    BasemapStyle: {"landmarks": "heuristic", "landmark_max": 8, "generalise": True},
}


def flags_off[G](group: type[G], **over: object) -> G:
    """Build `group` with its phase flags off, then `over` moved."""
    return group(**{**FLAGS_OFF.get(group, {}), **over})
