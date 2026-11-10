"""Every colour field is typed `Colour`, and a plain `str` that reaches one is coerced."""

import dataclasses
import re
import typing
from typing import Any

import pydantic
import pytest

from pyntpot.ink import Casing, Colour, Glow, Shadow
from pyntpot.maps import CoverPigment, Style
from pyntpot.maps.style_groups import CoverStyle, RouteInkStyle
from pyntpot.maps.theme_schema import theme_schema
from pyntpot.maps.theme_vocab import ALIAS_PATTERN, COLOUR_PATTERN

from support.colour_fields import colour_paths

HEX = re.compile(r"#[0-9a-f]{6}")

type _Path = tuple[str, ...]


def _string_defaults(style: Style) -> dict[_Path, list[object]]:
    """Every string-valued path of `style` with its default values, a dict field as `*`."""
    paths: dict[_Path, list[object]] = {}
    for group in type(style).model_fields:
        value = getattr(style, group)
        for item in dataclasses.fields(value):
            held = getattr(value, item.name)
            if isinstance(held, str):
                paths[(group, item.name)] = [held]
            elif isinstance(held, dict) and all(isinstance(v, str) for v in held.values()):
                paths[(group, item.name, "*")] = list(held.values())
    return paths


class TestFieldTypes:
    """Which fields are `Colour`, in the model and in the schema."""

    def test_every_hex_defaulted_field_is_typed_colour(self):
        """A field whose defaults are all `#rrggbb` is typed `Colour`, and no other field is."""
        implied = {
            path
            for path, values in _string_defaults(Style()).items()
            if values and all(isinstance(v, str) and HEX.fullmatch(v) for v in values)
        }
        assert set(colour_paths(Style())) == implied
        assert len(implied) == 7

    def test_every_colour_path_has_the_three_branch_node(self):
        """Each `Colour` path, a dict field's values included, is the pigment, hex or alias node."""
        schema: Any = theme_schema()
        leaves = [_node_at(schema, path) for path in colour_paths(Style())]
        assert len(leaves) == 7
        for leaf in leaves:
            _assert_three_branches(leaf)

    def test_every_effect_colour_has_the_three_branch_node(self) -> None:
        """Each `Colour` field of `Casing` and `Shadow` is the three-branch node, under both tables."""
        schema: Any = theme_schema()
        stacks = {
            "line_effects": schema["properties"]["line_effects"]["additionalProperties"]["anyOf"][
                2
            ],
            "effect_presets": schema["properties"]["effect_presets"]["additionalProperties"],
        }
        checked = 0
        for table, stack in stacks.items():
            for kind in (Casing, Glow, Shadow):
                node = stack["properties"][kind.__name__.lower()]
                for name, hint in typing.get_type_hints(kind).items():
                    if hint is Colour:
                        _assert_three_branches(node["properties"][name])
                        checked += 1
                    else:
                        assert "anyOf" not in node["properties"][name], f"{table}.{kind}.{name}"
        assert checked == 4


def _assert_three_branches(leaf: Any) -> None:
    """Hold `leaf` to the pigment-name enum, the hex pattern and the alias pattern, in order."""
    branches = leaf["anyOf"]
    assert [b.get("pattern") for b in branches[1:]] == [COLOUR_PATTERN, ALIAS_PATTERN]
    assert branches[0]["enum"] == sorted(branches[0]["enum"])
    assert "paynes_grey" in branches[0]["enum"]


def _node_at(schema: Any, path: _Path) -> Any:
    """The schema node at `path`, `*` stepping into a dict field's `additionalProperties`."""
    node = schema
    for key in path:
        node = node["additionalProperties"] if key == "*" else node["properties"][key]
    return node


class TestCoercion:
    """A plain `str` reaching a colour field comes out a lower-case `Colour`."""

    def test_replace_coerces_a_scalar_colour(self):
        """`replace` with an upper-case hex gives a `Colour` equal to the lower-case string."""
        got = dataclasses.replace(RouteInkStyle(), colour="#ABCDEF").colour
        assert type(got) is Colour
        assert got == "#abcdef"

    def test_replace_coerces_a_dict_of_cover_pigments(self):
        """`replace` with an upper-case hex gives a `CoverPigment` with `built`'s own transparency."""
        got = dataclasses.replace(CoverStyle(), pigments={"built": "#ABCDEF"}).pigments["built"]
        assert type(got.colour) is Colour
        assert got == CoverPigment(Colour("#abcdef"), 0.26)

    def test_model_validate_builds_a_colour(self):
        """`Style.model_validate` from a dict holds a `Colour`, stored lower-case."""
        style = Style.model_validate({"route_ink": {"colour": "#C22050"}})
        assert type(style.route_ink.colour) is Colour
        assert style.route_ink.colour == "#c22050"

    def test_model_validate_refuses_a_name_at_the_field(self):
        """A pigment name is no hex, so `model_validate` fails at `("route_ink", "colour")`."""
        with pytest.raises(pydantic.ValidationError) as caught:
            Style.model_validate({"route_ink": {"colour": "red"}})
        errors = caught.value.errors()
        assert [e["loc"] for e in errors] == [("route_ink", "colour")]
        assert errors[0]["type"] == "value_error"

    def test_a_default_style_builds(self):
        """`Style()` builds, every colour field a `Colour`."""
        style = Style()
        assert type(style.paper.paper_hex) is Colour
        assert type(style.nib.label_ink) is Colour
