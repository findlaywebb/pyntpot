"""Every colour field is typed `Colour`, and a plain `str` that reaches one is coerced."""

import dataclasses
import re
import typing
from collections.abc import Iterator
from typing import Any

import pydantic
import pytest

from pyntpot.ink import Colour
from pyntpot.maps import Style
from pyntpot.maps.style_groups import CoverStyle, RouteInkStyle
from pyntpot.maps.theme_schema import theme_schema
from pyntpot.maps.theme_vocab import ALIAS_PATTERN, COLOUR_PATTERN

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


def _colour_paths(style: Style) -> Iterator[_Path]:
    """Every path of `style` whose declared type is `Colour`, a dict field's values as `*`."""
    for group, info in type(style).model_fields.items():
        cls = info.annotation
        assert isinstance(cls, type)
        for name, hint in typing.get_type_hints(cls).items():
            if hint is Colour:
                yield (group, name)
            elif typing.get_origin(hint) is dict and typing.get_args(hint)[1] is Colour:
                yield (group, name, "*")


class TestFieldTypes:
    """Which fields are `Colour`, in the model and in the schema."""

    def test_every_hex_defaulted_field_is_typed_colour(self):
        """A field whose defaults are all `#rrggbb` is typed `Colour`, and no other field is."""
        implied = {
            path
            for path, values in _string_defaults(Style()).items()
            if values and all(isinstance(v, str) and HEX.fullmatch(v) for v in values)
        }
        assert set(_colour_paths(Style())) == implied
        assert len(implied) == 8

    def test_every_colour_path_has_the_three_branch_node(self):
        """Each `Colour` path, a dict field's values included, is the pigment, hex or alias node."""
        schema: Any = theme_schema()
        for path in _colour_paths(Style()):
            leaf = _node_at(schema, path)
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

    def test_replace_coerces_a_dict_of_colours(self):
        """`replace` with a dict of upper-case hexes gives a dict of `Colour` values."""
        got = dataclasses.replace(CoverStyle(), pigments={"built": "#ABCDEF"}).pigments["built"]
        assert type(got) is Colour
        assert got == "#abcdef"

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
