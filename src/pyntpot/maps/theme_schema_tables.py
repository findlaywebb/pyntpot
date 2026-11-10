"""The schema of a theme's top-level tables: `palette`, `pigments` and `colours`.

Key names: `top_level_tables`, the schema nodes of the three tables in the order they sit in a
theme, after `extends`; `colour_schema`, the node of a `Colour` value, shared with
`theme_schema` so a colour field and a `colours` entry read alike.

A colour is `anyOf` three branches: an enum of the registry's pigment names, the hex pattern and
the alias pattern. The schema is static and cannot know a theme's own aliases or pigments, so
the third branch keeps them valid in an editor; the enum completes names, and the checker gives
the good error. `colours` and `pigments` take keys matching the alias pattern that are no
built-in pigment name; `colours` takes a colour, or a table of `colour` and `override`.

Does not import the style model or `theme_schema` (the schema imports this module), validate a
theme or write the committed copies.

Invariants: no node has `required`; every table node forbids other keys where its keys are
fixed.
"""

from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY
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


def top_level_tables() -> dict[str, object]:
    """The nodes of `palette`, `pigments` and `colours`, keyed in that order."""
    return {"palette": _palette(), "pigments": _pigments(), "colours": _colours()}


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
