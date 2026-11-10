"""The JSON Schema for a theme file, generated from the style model.

Key name: `theme_schema`, which walks the style groups and returns the schema as plain
JSON data, in override form: every key at every level is optional, and every level
forbids the keys the model does not have.

Each group is an object of its fields, less its loader-only fields (`LOADER_FIELDS`, set only
through the top-level `line_effects` table); a field typed as a dataclass is a sub-table, an
object of its own fields by the same walk, except the loader-only fields (`LOADER_FIELDS`),
which a theme sets through `line_effects` and which the schema leaves out. A dict field is an object whose keys are its
vocabulary in `theme_vocab` and whose values share one schema. A `bool` is a boolean, an
`int` an integer, a `float` a number, a `str` a string, a `Colour` a pigment name, a
`#rrggbb` string or an alias string (`anyOf` three branches, since the schema cannot know a
theme's own aliases or pigments), a `Literal` an enum of its values, a `tuple[X, ...]` an
array of `X` and a fixed tuple an array of exactly its items. Each field carries its default as
JSON and its description from the `Attributes:` section of its group's docstring; each group and
sub-table carries its class docstring's summary line. The top level also takes `extends`,
`palette`, `pigments`, `colours`, `effect_presets` and `line_effects`, whose schemas are in
`theme_schema_tables`.

Does not write the committed copies (the test support's regenerator does), validate a
theme, check numeric ranges or brush ids, or read any file. Nothing in `style.py` imports
this module, so importing the style here forms no cycle.

Invariants: no level has `required`; every object but a dict field's entries has
`additionalProperties` false; the schema is a pure function of the groups it is given.
"""

import dataclasses
import re
import typing
from collections.abc import Mapping
from typing import Literal

from pyntpot.ink.colour import Colour
from pyntpot.maps.style import Style
from pyntpot.maps.theme_check import EXTENDS
from pyntpot.maps.theme_schema_tables import colour_schema, top_level_tables
from pyntpot.maps.theme_vocab import LOADER_FIELDS, VOCABULARIES

#: The schema's address on the docs site.
SCHEMA_ID = "https://findlaywebb.github.io/pyntpot/reference/theme.schema.json"

#: The JSON Schema dialect the schema is written in.
DIALECT = "https://json-schema.org/draft/2020-12/schema"

#: The schema of the top-level key naming the theme a theme overrides.
_EXTENDS_SCHEMA = {
    "type": "string",
    "description": "A theme name or a .yaml path this theme overrides; default when absent.",
}

#: The schema of each scalar field type.
_SCALARS: dict[object, dict[str, object]] = {
    bool: {"type": "boolean"},
    int: {"type": "integer"},
    float: {"type": "number"},
    str: {"type": "string"},
}

#: An `Attributes:` entry's first line: its field name, a colon and the description's start.
_ENTRY = re.compile(r"(\w+):\s*(.*)")

#: How much deeper than `Attributes:` an entry starts.
_ENTRY_INDENT = 4

type _Path = tuple[str, ...]


def theme_schema(groups: Mapping[str, type] | None = None) -> dict[str, object]:
    """The JSON Schema of a theme file over `groups`.

    Args:
        groups: Each style group's dataclass, by its key in a theme; `None` for the style
            model's own groups.

    Returns:
        The schema as plain JSON data: dicts, lists, strings, numbers and booleans.
    """
    if groups is None:
        groups = _style_groups()
    properties: dict[str, object] = {
        EXTENDS: dict(_EXTENDS_SCHEMA),
        **top_level_tables(_object_schema),
    }
    for name, group in groups.items():
        properties[name] = _object_schema(group, (name,))
    return {
        "$schema": DIALECT,
        "$id": SCHEMA_ID,
        "title": "pyntpot theme",
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
    }


def _style_groups() -> dict[str, type]:
    """Each of the style model's groups, by its key in a theme."""
    return {
        name: info.annotation
        for name, info in Style.model_fields.items()
        if isinstance(info.annotation, type)
    }


def _object_schema(group: type, path: _Path) -> dict[str, object]:
    """The schema of the dataclass `group` at `path`: a group or a sub-table.

    Raises:
        TypeError: When `group` is not a dataclass, a programming error.
    """
    if not dataclasses.is_dataclass(group):
        raise TypeError(f"{group!r} is not a dataclass")
    defaults = group()
    hints = typing.get_type_hints(group)
    described = _attributes(group.__doc__ or "")
    properties: dict[str, object] = {}
    for spec in dataclasses.fields(group):
        if len(path) == 1 and (path[0], spec.name) in LOADER_FIELDS:
            continue
        node = _value_schema(hints[spec.name], (*path, spec.name))
        node["default"] = _json(getattr(defaults, spec.name))
        if spec.name in described:
            node["description"] = described[spec.name]
        properties[spec.name] = node
    return {
        "type": "object",
        "description": _summary(group.__doc__ or ""),
        "additionalProperties": False,
        "properties": properties,
    }


def _value_schema(hint: object, path: _Path) -> dict[str, object]:
    """The schema of a value of the field type `hint` at `path`, with no default."""
    if isinstance(hint, type) and dataclasses.is_dataclass(hint):
        return _object_schema(hint, path)
    origin, args = typing.get_origin(hint), typing.get_args(hint)
    if origin is tuple and len(args) == 2 and args[1] is Ellipsis:  # noqa: PLR2004
        return {"type": "array", "items": _value_schema(args[0], path)}
    if origin is tuple:
        return {
            "type": "array",
            "prefixItems": [_value_schema(arg, path) for arg in args],
            "minItems": len(args),
            "maxItems": len(args),
        }
    if origin is dict:
        return _entries_schema(args[1], path)
    return _leaf_schema(hint, path)


def _leaf_schema(hint: object, path: _Path) -> dict[str, object]:
    """The schema of a scalar or `Literal` value of the field type `hint` at `path`.

    Raises:
        TypeError: When `hint` is a type the walk does not know, a programming error.
    """
    if hint is Colour:
        return colour_schema()
    if hint in _SCALARS:
        return dict(_SCALARS[hint])
    if typing.get_origin(hint) is Literal:
        return {"enum": list(typing.get_args(hint))}
    raise TypeError(f"{hint!r} at {'.'.join(path)} has no schema")


def _entries_schema(hint: object, path: _Path) -> dict[str, object]:
    """The schema of a dict field at `path` whose entries are of type `hint`."""
    node: dict[str, object] = {"type": "object"}
    known = VOCABULARIES.get(path)
    if known is not None:
        node["propertyNames"] = {"enum": sorted(known)}
    node["additionalProperties"] = _value_schema(hint, (*path, "*"))
    return node


def _json(value: object) -> object:
    """`value` as JSON data: a dataclass as a dict of its fields, a tuple as a list."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {spec.name: _json(getattr(value, spec.name)) for spec in dataclasses.fields(value)}
    if isinstance(value, Mapping):
        return {str(key): _json(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json(item) for item in value]
    return value


def _summary(doc: str) -> str:
    """The summary line of the docstring `doc`."""
    return doc.strip().partition("\n")[0].strip()


def _attributes(doc: str) -> dict[str, str]:
    """Each field's description in the `Attributes:` section of the docstring `doc`.

    An entry starts one indent deeper than `Attributes:` with `name:`; its continuation
    lines are deeper still, and are joined to it with spaces. The section ends at the next
    line no deeper than `Attributes:`.
    """
    lines = doc.expandtabs().splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip() == "Attributes:"]
    if not starts:
        return {}
    section = _indent(lines[starts[0]])
    entries: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in lines[starts[0] + 1 :]:
        if not line.strip():
            continue
        depth = _indent(line)
        if depth <= section:
            break
        entry = _ENTRY.fullmatch(line.strip())
        if depth == section + _ENTRY_INDENT and entry is not None:
            current = entries.setdefault(entry.group(1), [])
            current.append(entry.group(2))
        elif current is not None:
            current.append(line.strip())
    return {name: " ".join(part for part in parts if part) for name, parts in entries.items()}


def _indent(line: str) -> int:
    """How many spaces `line` starts with."""
    return len(line) - len(line.lstrip(" "))
