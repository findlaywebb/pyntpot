"""The theme schema: generated from the model, committed twice, and every theme file within it."""

import dataclasses
import json
import typing
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, Literal

import pytest

from pyntpot.ink import pigment
from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY
from pyntpot.maps import Style
from pyntpot.maps.line_effects import BUILT_IN_PRESETS, LINE_CLASSES
from pyntpot.maps.style import _groups
from pyntpot.maps.theme_schema import theme_schema
from pyntpot.maps.theme_vocab import ALIAS_PATTERN, LOADER_FIELDS, VOCABULARIES

from support import REPO_ROOT
from support.planted_groups import Ink
from support.theme_dump import plain_table
from support.theme_files import theme_file_at
from support.theme_schema import REGENERATE, SCHEMA_FILES

#: Where theme files live: the packaged themes and the example themes.
THEME_DIRS = (
    REPO_ROOT / "src" / "pyntpot" / "maps" / "themes",
    REPO_ROOT / "examples" / "themes",
)

#: The schema's address on the docs site, which a theme file's directive may name.
SITE_SCHEMA = "https://findlaywebb.github.io/pyntpot/reference/theme.schema.json"

#: What a theme file's first line starts with, before its schema's path or address.
DIRECTIVE = "# yaml-language-server: $schema="

#: What a stale committed schema's failure says to do.
STALE = f"regenerate: {REGENERATE}"


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Odd:
    """A test-local group with a field of a type the schema does not know."""

    x: complex = 0j


@dataclasses.dataclass(frozen=True, kw_only=True)
class _OddList:
    """A test-local group with a list of a type the schema does not know."""

    x: tuple[complex, ...] = ()


@dataclasses.dataclass(frozen=True, kw_only=True)
class _OddPair:
    """A test-local group with a pair of a type the schema does not know."""

    x: tuple[complex, complex] = (0j, 0j)


@dataclasses.dataclass(frozen=True, kw_only=True)
class _Described:
    """A test-local group whose docstring shapes its fields' descriptions.

    Attributes:
            A line deeper than an entry, before any entry.
        a: Alpha,

            continued after a blank line.
        b: Beta.

    Notes:
        c: Past the section's end.
    """

    a: int = 1
    b: int = 2
    c: int = 3


def _objects(
    node: Mapping[str, Any], path: tuple[str, ...] = ()
) -> Iterator[tuple[tuple[str, ...], Mapping[str, Any]]]:
    """Every object schema under `node` with its key path, a dict field's entries as `*`."""
    if node.get("type") == "object":
        yield path, node
    for key, child in node.get("properties", {}).items():
        yield from _objects(child, (*path, key))
    entries = node.get("additionalProperties")
    if isinstance(entries, Mapping):
        yield from _objects(entries, (*path, "*"))
    for child in (node.get("items"), *node.get("prefixItems", ())):
        if isinstance(child, Mapping):
            yield from _objects(child, path)


def _theme_files() -> list[Path]:
    """Every YAML theme file among the packaged themes and the example themes, sorted."""
    return sorted(path for directory in THEME_DIRS for path in directory.glob("*.yaml"))


def _object_branch(node: Mapping[str, Any]) -> Mapping[str, Any]:
    """The `"type": "object"` branch of an `anyOf` node, or `node` itself when it has none."""
    for branch in node.get("anyOf", ()):
        if branch.get("type") == "object":
            return branch
    return node


def keys_outside_the_schema(
    value: object, node: Mapping[str, Any], path: tuple[str, ...] = ()
) -> list[str]:
    """Name every key path of `value` the schema `node` has no property for, or whose enum refuses it."""
    if isinstance(value, Mapping):
        node = _object_branch(node)
        found: list[str] = []
        for key, item in value.items():
            here = (*path, str(key))
            properties = node.get("properties", {})
            entries = node.get("additionalProperties")
            names = node.get("propertyNames", {}).get("enum")
            if key in properties:
                found.extend(keys_outside_the_schema(item, properties[key], here))
            elif isinstance(entries, Mapping) and (names is None or key in names):
                found.extend(keys_outside_the_schema(item, entries, here))
            else:
                found.append(".".join(here))
        return found
    if "enum" in node and value not in node["enum"]:
        return [".".join(path)]
    return []


def test_the_committed_schemas_are_the_generated_one() -> None:
    """Both committed schema files, parsed, are the schema the model generates."""
    generated = theme_schema()
    for path in SCHEMA_FILES:
        assert path.is_file(), STALE
        assert json.loads(path.read_text(encoding="utf-8")) == generated, STALE


def test_every_field_is_in_the_schema_with_its_default() -> None:
    """Every group field but the loader-only ones is a schema property whose default is its JSON."""
    schema: Any = theme_schema()
    style = Style()
    for group in Style.model_fields:
        values = plain_table(dataclasses.asdict(getattr(style, group)))
        assert isinstance(values, dict)
        values = {k: v for k, v in values.items() if (group, k) not in LOADER_FIELDS}
        properties = schema["properties"][group]["properties"]
        assert set(properties) == set(values), group
        for field, value in values.items():
            assert properties[field]["default"] == value, f"{group}.{field}"
            assert properties[field]["description"], f"{group}.{field}"


def test_every_level_forbids_other_keys() -> None:
    """Every object forbids other keys, but a dict field's entries, named from its vocabulary."""
    entries: set[tuple[str, ...]] = set()
    schema: Any = theme_schema()
    for group in Style.model_fields:
        for path, node in _objects(schema["properties"][group], (group,)):
            _check_level(path, node, entries)
    assert entries == set(VOCABULARIES)


def _check_level(
    path: tuple[str, ...], node: Mapping[str, Any], entries: set[tuple[str, ...]]
) -> None:
    """Hold one object of a group subtree to the level rule, noting a dict field's entries."""
    if "propertyNames" in node:
        entries.add(path)
        assert node["propertyNames"] == {"enum": sorted(VOCABULARIES[path])}, path
        assert isinstance(node["additionalProperties"], Mapping), path
    else:
        assert node["additionalProperties"] is False, path


def test_the_enums_are_the_literals() -> None:
    """Each `Literal` field's enum is its `Literal`'s values, in order."""
    schema: Any = theme_schema()
    literals = 0
    for group, cls in _groups().items():
        for field, hint in typing.get_type_hints(cls).items():
            if typing.get_origin(hint) is Literal:
                literals += 1
                node = schema["properties"][group]["properties"][field]
                assert node["enum"] == list(typing.get_args(hint)), f"{group}.{field}"
    assert literals > 0


def test_the_top_level_names_extends_the_five_tables_and_the_groups() -> None:
    """The top level names `extends`, the five tables and the groups, in order."""
    schema: Any = theme_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == SITE_SCHEMA
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert list(schema["properties"]) == [
        "extends",
        "palette",
        "pigments",
        "colours",
        "effect_presets",
        "line_effects",
        *Style.model_fields,
    ]
    assert schema["properties"]["extends"]["type"] == "string"


def test_the_alias_tables_take_alias_shaped_keys_that_are_no_pigment_name() -> None:
    """`colours` and `pigments` each take keys matching the alias pattern but no built-in name."""
    schema: Any = theme_schema()
    rule = {
        "pattern": "^[a-z][a-z0-9]*(_[a-z0-9]+)*$",
        "not": {"enum": sorted(PIGMENT_REGISTRY.names())},
    }
    for table in ("colours", "pigments"):
        assert schema["properties"][table]["propertyNames"] == rule, table


def test_the_effect_tables_take_their_own_keys() -> None:
    """`effect_presets` takes alias keys that are no built-in preset; `line_effects` the classes."""
    schema: Any = theme_schema()
    presets = schema["properties"]["effect_presets"]
    assert presets["propertyNames"] == {
        "pattern": ALIAS_PATTERN,
        "not": {"enum": sorted(BUILT_IN_PRESETS)},
    }
    assert schema["properties"]["line_effects"]["propertyNames"] == {"enum": sorted(LINE_CLASSES)}


def test_a_line_effects_value_is_a_preset_name_or_a_stack() -> None:
    """A `line_effects` value is `anyOf` the built-in names, an alias name or a stack object."""
    schema: Any = theme_schema()
    names, theme_preset, stack = schema["properties"]["line_effects"]["additionalProperties"][
        "anyOf"
    ]
    assert names == {"enum": ["cased", "halo", "lifted"]}
    assert theme_preset == {"type": "string", "pattern": ALIAS_PATTERN}
    assert stack["additionalProperties"] is False
    assert list(stack["properties"]) == ["casing", "glow", "shadow"]


def test_an_effect_is_the_walk_of_its_dataclass() -> None:
    """Each effect in a stack is an object of its fields with their defaults, colours as the node."""
    schema: Any = theme_schema()
    stack = schema["properties"]["line_effects"]["additionalProperties"]["anyOf"][2]
    casing, glow, shadow = (stack["properties"][name] for name in ("casing", "glow", "shadow"))
    assert list(casing["properties"]) == ["width_px", "colour", "strength"]
    assert casing["properties"]["width_px"] == {
        "type": "number",
        "default": 0.0,
        "description": casing["properties"]["width_px"]["description"],
    }
    assert casing["properties"]["colour"]["default"] == "#ffffff"
    assert list(glow["properties"]) == ["spread_px", "blur_px", "strength"]
    assert shadow["properties"]["colour"]["default"] == pigment("paynes_grey").colour
    assert shadow["additionalProperties"] is False
    assert "minimum" not in json.dumps(stack)


def test_an_effect_preset_is_a_stack_that_may_override() -> None:
    """An `effect_presets` value is a stack object that also takes `override`."""
    schema: Any = theme_schema()
    entry = schema["properties"]["effect_presets"]["additionalProperties"]
    assert list(entry["properties"]) == ["casing", "glow", "shadow", "override"]
    assert entry["properties"]["override"] == {"type": "boolean"}
    assert entry["additionalProperties"] is False


def test_a_loader_only_field_is_not_a_schema_property() -> None:
    """`basemap.line_effects` and `route_ink.effects` are left out of the group subtrees."""
    schema: Any = theme_schema()
    assert "line_effects" not in schema["properties"]["basemap"]["properties"]
    assert "effects" not in schema["properties"]["route_ink"]["properties"]


def test_a_colours_entry_is_a_colour_or_a_colour_with_override() -> None:
    """A `colours` value is the three-branch colour node, or an object of `colour` and `override`."""
    schema: Any = theme_schema()
    colour = {"anyOf": schema["properties"]["paper"]["properties"]["paper_hex"]["anyOf"]}
    branches = schema["properties"]["colours"]["additionalProperties"]["anyOf"]
    assert branches[0] == colour
    assert set(branches[1]["properties"]) == {"colour", "override"}
    assert branches[1]["properties"]["colour"] == colour
    assert branches[1]["additionalProperties"] is False


def test_a_pigments_entry_takes_base_colour_transparency_index_and_override() -> None:
    """A `pigments` value is an object of exactly its five keys, `base` an enum of the registry."""
    schema: Any = theme_schema()
    entry = schema["properties"]["pigments"]["additionalProperties"]
    assert set(entry["properties"]) == {
        "base",
        "colour",
        "transparency",
        "colour_index",
        "override",
    }
    assert entry["properties"]["base"] == {"enum": sorted(PIGMENT_REGISTRY.names())}
    assert entry["properties"]["transparency"] == {"type": "number", "minimum": 0, "maximum": 1}
    assert entry["additionalProperties"] is False


def test_palette_is_a_packaged_name_or_a_palette_file() -> None:
    """`palette` is an enum of the packaged names or a `.yaml` or `.gpl` path."""
    schema: Any = theme_schema()
    names, path = schema["properties"]["palette"]["anyOf"]
    assert names == {"enum": ["plain"]}
    assert path == {"type": "string", "pattern": r"\.(yaml|gpl)$"}


def test_a_group_that_is_no_dataclass_is_refused() -> None:
    """A group that is not a dataclass is a programming error, named as such."""
    with pytest.raises(TypeError, match="is not a dataclass"):
        theme_schema({"odd": int})


@pytest.mark.parametrize("group", [_Odd, _OddList, _OddPair], ids=["leaf", "list", "pair"])
def test_a_type_with_no_schema_is_refused_at_its_path(group: type) -> None:
    """A field type the walk does not know, alone or in a list, names itself and its key path."""
    with pytest.raises(TypeError, match=r"^<class 'complex'> at odd\.x has no schema$"):
        theme_schema({"odd": group})


def test_a_description_is_read_from_the_attributes_section_alone() -> None:
    """An entry's description runs over blank and deeper lines, and stops at the section's end."""
    schema: Any = theme_schema({"described": _Described})
    fields = schema["properties"]["described"]["properties"]
    assert fields["a"]["description"] == "Alpha, continued after a blank line."
    assert fields["b"]["description"] == "Beta."
    assert "description" not in fields["c"]


def test_a_sub_table_is_an_object_of_its_fields() -> None:
    """A dataclass-typed field is an object of its own fields, each with its default."""
    schema: Any = theme_schema({"route_ink": Ink})
    glow = schema["properties"]["route_ink"]["properties"]["glow"]
    assert glow["type"] == "object"
    assert glow["additionalProperties"] is False
    assert glow["properties"]["px"]["type"] == "number"
    assert glow["properties"]["px"]["default"] == 2.0
    assert glow["default"] == {"colour": "#ffffff", "px": 2.0}


def test_every_theme_key_is_a_schema_path() -> None:
    """Every key path of every theme file is a schema property path, and every enum value is in its enum."""
    schema = theme_schema()
    for path in _theme_files():
        theme = theme_file_at(path)
        assert theme.problems == (), path.name
        assert keys_outside_the_schema(theme.table, schema) == [], path.name


def test_the_theme_files_name_a_schema() -> None:
    """Every theme file's first line is a schema directive naming a file that exists or the site's schema."""
    for path in _theme_files():
        first = path.read_text(encoding="utf-8").partition("\n")[0]
        assert first.startswith(DIRECTIVE), path.name
        target = first.removeprefix(DIRECTIVE)
        assert target == SITE_SCHEMA or (path.parent / target).is_file(), path.name


class TestTheWalkerFindsAKeyOutsideTheSchema:
    """The theme-file walker reports an unknown key and an enum value the schema refuses."""

    def test_unknown_group_key(self) -> None:
        """A key no group has is reported at its path."""
        table = {"paper": {"paper_hue": "#ffffff"}}
        assert keys_outside_the_schema(table, theme_schema()) == ["paper.paper_hue"]

    def test_unknown_entry_key(self) -> None:
        """A dict field's entry outside its vocabulary is reported at its path."""
        table = {"cover": {"pigments": {"heather": "#7b5c8a"}}}
        assert keys_outside_the_schema(table, theme_schema()) == ["cover.pigments.heather"]

    def test_enum_value(self) -> None:
        """A value outside its field's enum is reported at its path."""
        table = {"route_ink": {"blend": "screen"}}
        assert keys_outside_the_schema(table, theme_schema()) == ["route_ink.blend"]

    def test_known_keys(self) -> None:
        """Known keys, a vocabulary entry and an enum value in its enum report nothing."""
        table = {"extends": "default", "route_ink": {"blend": "multiply"}}
        assert keys_outside_the_schema(table, theme_schema()) == []
