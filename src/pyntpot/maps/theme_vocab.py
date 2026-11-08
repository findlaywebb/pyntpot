"""What a theme may name: each dict field's keys, the brush-id fields and the colour fields.

Key names: `VOCABULARIES`, the keys a theme may give each dict-valued field, by key path,
computed from the group defaults so a new class or pigment needs no edit here;
`BRUSH_ID_FIELDS`, the key paths whose values are brush ids; `COLOUR_FIELDS`, the key paths
whose values are `#rrggbb` colours. A `*` in a key path stands for every entry of a dict
field.

Checks nothing itself: the checker reads these. Imports the style groups, never the style
model or the `pyntpot.maps` package, which import the loader.

Invariants: each vocabulary is the set of keys its readers look up, and a `brush_overrides`
entry's keys are the keys the sheet brush reads; no key path appears twice in
`BRUSH_ID_FIELDS` or `COLOUR_FIELDS`.
"""

from pyntpot.ink.brush import BRUSH_OVERRIDE_KEYS
from pyntpot.ink.brush_sheet import BRUSH_COLOURS
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.maps.style_groups import CoverStyle

_COVER = CoverStyle()
_BRUSH = BrushStyle()

#: The pigment keys: a pigment's transparency and its separating partner are keyed alike.
_PIGMENTS = frozenset(_COVER.pigments)

#: The `brush_overrides` entries a caller names itself: the route's pen and the label nib.
_CALLER_OVERRIDES = frozenset({"route", "label"})

#: The keys a theme may give each dict-valued field, by key path; `*` is every entry.
VOCABULARIES: dict[tuple[str, ...], frozenset[str]] = {
    ("paper", "pigment_transparency"): _PIGMENTS,
    ("wash", "separation_pigments"): _PIGMENTS,
    ("cover", "pigments"): _PIGMENTS,
    ("cover", "cover_cfg"): frozenset(_COVER.cover_cfg),
    ("brush", "river_curve"): frozenset(_BRUSH.river_curve),
    ("brush", "brushes"): frozenset(_BRUSH.brushes),
    ("brush", "brush_width_px"): frozenset(_BRUSH.brush_width_px),
    ("brush", "brush_overrides"): frozenset(_BRUSH.brushes)
    | {cls.lower() for cls in BRUSH_COLOURS}
    | _CALLER_OVERRIDES,
    ("brush", "brush_overrides", "*"): BRUSH_OVERRIDE_KEYS,
}

#: The key paths whose values are brush ids, which must name a cell on the brush sheet.
BRUSH_ID_FIELDS: tuple[tuple[str, ...], ...] = (
    ("brush", "brushes", "*"),
    ("route", "route_pen_brush"),
    ("nib", "label_brush"),
    ("nib", "label_leader_brush"),
)

#: The key paths whose values are colours, `#` and six hexadecimal digits.
COLOUR_FIELDS: tuple[tuple[str, ...], ...] = (
    ("paper", "paper_hex"),
    ("wash", "separation_pigments", "*"),
    ("nib", "label_ink"),
    ("nib", "label_water_ink"),
    ("nib", "label_in_water_ink"),
    ("nib", "label_route_ink"),
    ("cover", "pigments", "*"),
    ("route_ink", "colour"),
)
