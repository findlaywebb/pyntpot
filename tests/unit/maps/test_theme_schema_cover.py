"""The theme schema for a colour field and a cover pigment: the colour node, and what is required."""

from collections.abc import Mapping
from typing import Any

from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY
from pyntpot.maps.theme_schema import theme_schema


def colour_node(colour: Mapping[str, Any]) -> dict[str, Any]:
    """The bare three-branch colour node of the field schema `colour`, less its default and description."""
    return {"anyOf": colour["anyOf"]}


def _required(node: object) -> list[tuple[str, ...]]:
    """Every `required` list in the schema under `node`, as a tuple of its keys."""
    found: list[tuple[str, ...]] = []
    if isinstance(node, Mapping):
        if "required" in node:
            found.append(tuple(node["required"]))
        for child in node.values():
            found.extend(_required(child))
    elif isinstance(node, list):
        for child in node:
            found.extend(_required(child))
    return found


def test_no_key_is_required_but_a_cover_pigment_tables_pigment() -> None:
    """A theme names only what it overrides, so the one required key is a `{pigment, ...}` table's."""
    assert _required(theme_schema()) == [("pigment",)]


def test_a_colour_field_takes_the_three_branch_node() -> None:
    """A colour field, and each entry of a colour dict field, is a pigment name, a hex or an alias."""
    schema: Any = theme_schema()
    node = {
        "anyOf": [
            {"enum": sorted(PIGMENT_REGISTRY.names())},
            {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
            {"type": "string", "pattern": "^[a-z][a-z0-9]*(_[a-z0-9]+)*$"},
        ]
    }
    assert node["anyOf"] == schema["properties"]["paper"]["properties"]["paper_hex"]["anyOf"]
    pigments = schema["properties"]["cover"]["properties"]["pigments"]
    assert pigments["additionalProperties"]["anyOf"][0] == node


def test_a_cover_pigment_is_a_colour_node_or_a_pigment_and_transparency_table() -> None:
    """A `cover.pigments` entry is the colour node or `{pigment: <colour node>, transparency}`."""
    schema: Any = theme_schema()
    entry = schema["properties"]["cover"]["properties"]["pigments"]["additionalProperties"]
    colour = schema["properties"]["paper"]["properties"]["paper_hex"]
    assert entry["anyOf"] == [
        colour_node(colour),
        {
            "type": "object",
            "additionalProperties": False,
            "required": ["pigment"],
            "properties": {"pigment": colour_node(colour), "transparency": {"type": "number"}},
        },
    ]
    assert entry["anyOf"][0]["anyOf"] == colour["anyOf"]
