"""The schema of a theme's top-level tables: `palette`, `pigments`, `colours` and the effect tables.

Key names: `top_level_tables`, the schema nodes of the six tables in the order they sit in a
theme, after `extends`: `palette`, `pigments`, `colours`, `effect_presets`, `line_effects` and
`casing_unions`;
`colour_schema`, the node of a `Colour` value, shared with
`theme_schema` so a colour field and a `colours` entry read alike; `cover_pigment_schema`, the
node of a `CoverPigment`: that colour node, or an object of a required `pigment` and an optional
`transparency`.

A colour is `anyOf` three branches: an enum of the registry's pigment names, the hex pattern and
the alias pattern. The schema is static and cannot know a theme's own aliases or pigments, so
the third branch keeps them valid in an editor; the enum completes names, and the checker gives
the good error. `colours` and `pigments` take keys matching the alias pattern that are no
built-in pigment name; `colours` takes a colour, or a table of `colour` and `override`.

A stack is an object of the optional keys `casing`, `glow`, `shadow` and `reserve`, each the walk
of that effect's dataclass, which `top_level_tables` takes as an argument (`sub_table`) so this module
needs neither `theme_schema` nor the style. `line_effects` takes a line class for each key and,
for each value, `anyOf` a built-in preset name, an alias-shaped name (a theme preset) or a stack.
`effect_presets` takes alias-shaped keys that are no built-in preset name and a stack for each
value, which may also carry `override`. The schema holds no numeric range, a reserve's included:
the checker does. `casing_unions` is an array of non-empty arrays of the seven basemap classes,
each class once; the rules across members (one group, one colour, a ring each) and across unions
are load-only, and its description says so.

Does not import the style model or `theme_schema` (the schema imports this module), validate a
theme or write the committed copies.

Invariants: no node has `required`, but a `CoverPigment` object's `pigment`; every table node
forbids other keys where its keys are fixed.
"""

from collections.abc import Callable

from pyntpot.ink import Casing, Glow, Reserve, Shadow
from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY
from pyntpot.maps.line_effects import BUILT_IN_PRESETS, LINE_CLASSES, ROAD_GROUP, WATER_GROUP
from pyntpot.maps.theme_palette import Palette
from pyntpot.maps.theme_vocab import ALIAS_PATTERN, COLOUR_PATTERN


def colour_schema() -> dict[str, object]:
    """The node of a `Colour` value: a pigment name, a hex or an alias."""
    return {
        "anyOf": [
            {"enum": sorted(PIGMENT_REGISTRY.names())},
            {"type": "string", "pattern": COLOUR_PATTERN},
            {"type": "string", "pattern": ALIAS_PATTERN},
        ]
    }


def cover_pigment_schema() -> dict[str, object]:
    """The node of a `CoverPigment` value: a colour node or `{pigment, transparency}`."""
    table: dict[str, object] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["pigment"],
        "properties": {
            "pigment": colour_schema(),
            "transparency": {"type": "number"},
        },
    }
    return {"anyOf": [colour_schema(), table]}


type SubTable = Callable[[type, tuple[str, ...]], dict[str, object]]


def top_level_tables(sub_table: SubTable) -> dict[str, object]:
    """The nodes of the six top-level tables, keyed in the order they sit in a theme.

    Args:
        sub_table: The walk of a dataclass at a key path as an object schema, with each
            field's default and description; `theme_schema` passes its own.

    Returns:
        `palette`, `pigments`, `colours`, `effect_presets`, `line_effects` and `casing_unions`.
    """
    return {
        "palette": _palette(),
        "pigments": _pigments(),
        "colours": _colours(),
        "effect_presets": _effect_presets(sub_table),
        "line_effects": _line_effects(sub_table),
        "casing_unions": _casing_unions(),
    }


def _names() -> dict[str, object]:
    """The rule for a table's keys: an alias-shaped name that is no built-in pigment."""
    return {"pattern": ALIAS_PATTERN, "not": {"enum": sorted(PIGMENT_REGISTRY.names())}}


def _palette() -> dict[str, object]:
    """The node of `palette`: a packaged name or a `.yaml` or `.gpl` path."""
    return {
        "description": "A packaged palette name, or a .yaml or .gpl palette file.",
        "anyOf": [
            {"enum": list(Palette.names())},
            {"type": "string", "pattern": r"\.(yaml|gpl)$"},
        ],
    }


def _pigments() -> dict[str, object]:
    """The node of `pigments`: new pigments, each derived from a base and its own fields."""
    return {
        "type": "object",
        "description": "Pigments of this theme, by name; each needs a base or a colour.",
        "propertyNames": _names(),
        "additionalProperties": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "base": {"enum": sorted(PIGMENT_REGISTRY.names())},
                "colour": {"type": "string", "pattern": COLOUR_PATTERN},
                "transparency": {"type": "number", "minimum": 0, "maximum": 1},
                "colour_index": {"type": "string"},
                "override": {"type": "boolean"},
            },
        },
    }


def _colours() -> dict[str, object]:
    """The node of `colours`: aliases, each a colour or a colour with `override`."""
    return {
        "type": "object",
        "description": "Colour aliases, by name; each stands for a pigment name or a hex.",
        "propertyNames": _names(),
        "additionalProperties": {
            "anyOf": [
                colour_schema(),
                {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "colour": colour_schema(),
                        "override": {"type": "boolean"},
                    },
                },
            ]
        },
    }


def _stack(
    sub_table: SubTable, path: tuple[str, ...], *, override: bool = False
) -> dict[str, object]:
    """The node of an effect stack at `path`: the optional `casing`, `glow`, `shadow`, `reserve`.

    A preset entry also takes `override`, to replace an inherited preset.
    """
    kinds = {"casing": Casing, "glow": Glow, "shadow": Shadow, "reserve": Reserve}
    properties: dict[str, object] = {
        name: sub_table(kind, (*path, name)) for name, kind in kinds.items()
    }
    if override:
        properties["override"] = {"type": "boolean"}
    return {"type": "object", "additionalProperties": False, "properties": properties}


def _effect_presets(sub_table: SubTable) -> dict[str, object]:
    """The node of `effect_presets`: stacks by name, each with an optional `override`."""
    return {
        "type": "object",
        "description": "Effect presets of this theme, by name; each is a stack of effects.",
        "propertyNames": {"pattern": ALIAS_PATTERN, "not": {"enum": sorted(BUILT_IN_PRESETS)}},
        "additionalProperties": _stack(sub_table, ("effect_presets", "*"), override=True),
    }


def _line_effects(sub_table: SubTable) -> dict[str, object]:
    """The node of `line_effects`: a preset name or a stack for each line class."""
    return {
        "type": "object",
        "description": "The effects of each line class, and of the route: a preset or a stack.",
        "propertyNames": {"enum": sorted(LINE_CLASSES)},
        "additionalProperties": {
            "anyOf": [
                {"enum": sorted(BUILT_IN_PRESETS)},
                {"type": "string", "pattern": ALIAS_PATTERN},
                _stack(sub_table, ("line_effects", "*")),
            ]
        },
    }


def _casing_unions() -> dict[str, object]:
    """The node of `casing_unions`: arrays of basemap line classes, each class once."""
    return {
        "type": "array",
        "description": (
            "Groups of basemap line classes whose casings or reserves are laid as one ring. "
            "At load, a union lies within water or road, holds a class once across all unions, "
            "and its members share one casing colour and strength (or all reserves with one pool)."
        ),
        "items": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"enum": [*WATER_GROUP, *ROAD_GROUP]},
        },
    }
