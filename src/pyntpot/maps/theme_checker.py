"""The checker behind `theme_check`: one theme's table checked key by key against the model.

Key types: `TableCheck`, one theme's check in progress, with `table`, `field`, `entries`,
`mapping` and `leaf`, and the problems it has found; `group_hints` and `is_dataclass`, which read a
style group's field types.

Every key at every level is checked: a group's fields, a dict field's entries against its
vocabulary in `theme_vocab`, and a `brush_overrides` entry's keys. Each leaf is validated by
pydantic in strict mode against its field's type, and a brush id must name a cell on the
brush sheet.

Does not read files, resolve `extends`, merge themes, check numeric ranges or raise, and
imports nothing from `theme_check`, so the modules `theme_check` dispatches to import this one.

Invariants: a refused leaf is left out of the returned table; every problem names its dotted
key path and the line of that key, or of its nearest ancestor present in the file.
"""

import dataclasses
import difflib
import functools
import typing
from collections.abc import Callable, Collection, Mapping
from typing import Annotated, Any, Literal

import pydantic
from pydantic import BeforeValidator

from pyntpot.ink.brush import brush_id_known, brush_ids
from pyntpot.ink.colour import Colour
from pyntpot.ink.naming import nearest
from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_read import ThemeFile
from pyntpot.maps.theme_scope import ThemeScope, resolve_colour
from pyntpot.maps.theme_vocab import BRUSH_ID_FIELDS, VOCABULARIES

#: The message for a value that should be a mapping.
_TABLE = "is a table of keys"

#: The message for each strict-mode error type, given the refused value.
_MESSAGES: dict[str, str] = {
    "bool_type": "{v!r} is not a boolean (true or false)",
    "float_type": "{v!r} is not a number",
    "int_type": "{v!r} is not a whole number",
    "string_type": "{v!r} is not a string",
    "tuple_type": "{v!r} is not a list",
}

type _Path = tuple[str, ...]


class TableCheck:
    """One theme's check in progress: where its keys are, and what has been found."""

    def __init__(
        self,
        theme: ThemeFile,
        renamed: Mapping[_Path, str],
        scope: ThemeScope | None = None,
    ) -> None:
        """Start checking `theme`, with `renamed` as the old key paths and `scope` as its names."""
        self.theme = theme
        self.renamed = renamed
        self.scope = ThemeScope.built_in() if scope is None else scope
        self.found: list[ThemeProblem] = []

    def problems(self) -> tuple[ThemeProblem, ...]:
        """Every problem found, in line order."""
        return tuple(sorted(self.found, key=lambda problem: problem.line or 0))

    def problem(self, path: _Path, message: str) -> None:
        """Record `message` at `path`, on the line of `path` or of its nearest present ancestor."""
        line = None
        for end in range(len(path), 0, -1):
            line = self.theme.lines.get(path[:end])
            if line is not None:
                break
        self.found.append(
            ThemeProblem(path=self.theme.path, key=".".join(path), line=line, message=message)
        )

    def unknown(self, path: _Path, known: typing.Iterable[str]) -> None:
        """Record the key at `path` as renamed, or as unknown with the nearest of `known`."""
        if path in self.renamed:
            self.problem(path, f"renamed to {self.renamed[path]}")
            return
        near = difflib.get_close_matches(path[-1], sorted(known), n=1, cutoff=0.6)
        self.problem(path, f"unknown key; did you mean {near[0]}?" if near else "unknown key")

    def table(self, group: type, value: object, path: _Path) -> dict[str, object] | None:
        """Check `value` as a table of `group`'s fields at `path`; None when it is no table."""
        fields = group_hints(group)
        return self.mapping(value, path, fields, fields.__getitem__)

    def field(self, hint: object, value: object, path: _Path) -> object | None:
        """Check `value` against the field type `hint` at `path`; None when it is refused."""
        if is_dataclass(hint):
            return self.table(hint, value, path)
        if typing.get_origin(hint) is dict:
            return self.entries(typing.get_args(hint)[1], value, path)
        return self.leaf(hint, value, path)

    def entries(self, hint: object, value: object, path: _Path) -> dict[str, object] | None:
        """Check `value` as a dict field's entries, each against `hint`; None when no table."""
        return self.mapping(value, path, _vocabulary(path), lambda _key: hint)

    def mapping(
        self,
        value: object,
        path: _Path,
        known: Collection[str] | None,
        hint_of: Callable[[str], object],
    ) -> dict[str, object] | None:
        """Check `value` as a table at `path` whose keys are `known` (any when None).

        Each key's value is checked against `hint_of(key)`; a renamed or unknown key is
        recorded and left out.

        Returns:
            The checked entries, or None when `value` is no table.
        """
        if not isinstance(value, dict):
            self.problem(path, _TABLE)
            return None
        checked: dict[str, object] = {}
        for key, item in value.items():
            here = (*path, key)
            if here in self.renamed or (known is not None and key not in known):
                self.unknown(here, known or ())
                continue
            converted = self.field(hint_of(key), item, here)
            if converted is not None:
                checked[key] = converted
        return checked

    def leaf(self, hint: object, value: object, path: _Path) -> object | None:
        """Validate the leaf `value` strictly against `hint` at `path`; None when refused."""
        try:
            converted = _adapter(hint).validate_python(value, context={"scope": self.scope})
        except pydantic.ValidationError as exc:
            for message in _messages(hint, value, exc):
                self.problem(path, message)
            return None
        message = _sheet_and_colour(converted, path)
        if message is not None:
            self.problem(path, message)
            return None
        return converted


def _messages(hint: object, value: object, exc: pydantic.ValidationError) -> list[str]:
    """What is wrong with `value` for `hint`, one message per distinct error, in error order."""
    messages: list[str] = []
    for error in exc.errors():
        kind, loc, given = error["type"], error["loc"], error["input"]
        if kind == "value_error":
            message = str(error.get("ctx", {}).get("error", error["msg"]))
        else:
            message = _message(hint, value, kind, loc, given) or error["msg"]
        if message not in messages:
            messages.append(message)
    return messages


def _message(
    hint: object, value: object, kind: str, loc: tuple[int | str, ...], given: object
) -> str | None:
    """The message for the strict-mode error `kind` at `loc` refusing `given` within `value`.

    Returns:
        The message, or None for an error type with no message of its own here.
    """
    if kind == "too_long" or (kind == "missing" and loc and isinstance(loc[-1], int)):
        size = len(value) if isinstance(value, tuple) else 0
        return f"a list of {len(typing.get_args(hint))} values, not {size}"
    if kind == "literal_error" and typing.get_origin(hint) is Literal:
        choices = ", ".join(map(repr, typing.get_args(hint)))
        return f"{given!r} is not one of {choices}"
    if kind in _MESSAGES:
        return _MESSAGES[kind].format(v=given)
    return None


def _sheet_and_colour(value: object, path: _Path) -> str | None:
    """What is wrong with `value` at `path` as a brush id or a colour, when its path is one."""
    if not isinstance(value, str):
        return None
    if any(_matches(path, pattern) for pattern in BRUSH_ID_FIELDS) and not brush_id_known(value):
        hint = "".join(f"; did you mean {name}?" for name in nearest(value, brush_ids()))
        return f"{value!r} is not a brush on the sheet{hint}"
    return None


def _matches(path: _Path, pattern: _Path) -> bool:
    """Whether `path` is `pattern`, a `*` in the pattern standing for any one key."""
    return len(path) == len(pattern) and all(
        want in ("*", have) for have, want in zip(path, pattern, strict=True)
    )


def _vocabulary(path: _Path) -> frozenset[str] | None:
    """The keys a theme may give the dict field at `path`, or None when any key will do."""
    for pattern, known in VOCABULARIES.items():
        if _matches(path, pattern):
            return known
    return None


def is_dataclass(hint: object) -> typing.TypeGuard[type]:
    """Whether the field type `hint` is a dataclass, and so a sub-table."""
    return isinstance(hint, type) and dataclasses.is_dataclass(hint)


@functools.cache
def group_hints(group: type) -> dict[str, object]:
    """The type of each field of the dataclass `group`, by field name.

    Raises:
        TypeError: When `group` is not a dataclass, a programming error.
    """
    if not dataclasses.is_dataclass(group):
        raise TypeError(f"{group!r} is not a dataclass")
    hints = typing.get_type_hints(group)
    return {item.name: hints[item.name] for item in dataclasses.fields(group)}


def resolve_theme_colour(value: object, info: pydantic.ValidationInfo) -> Colour:
    """The colour a theme's `value` names, resolved in the scope the check carries.

    Args:
        value: A hex, an alias or a pigment name.
        info: Pydantic's context; `info.context["scope"]` is the `ThemeScope`.

    Returns:
        The `Colour` it stands for.

    Raises:
        ValueError: When `value` is not a string, or names no colour.
    """
    if not isinstance(value, str):
        raise ValueError(_MESSAGES["string_type"].format(v=value))  # noqa: TRY004
    scope = ThemeScope.built_in() if info.context is None else info.context["scope"]
    return resolve_colour(value, scope)


@functools.cache
def _adapter(hint: object) -> pydantic.TypeAdapter[object]:
    """The strict pydantic validator for the field type `hint`."""
    form: Any = Annotated[Colour, BeforeValidator(resolve_theme_colour)] if hint is Colour else hint
    return pydantic.TypeAdapter(form, config=pydantic.ConfigDict(strict=True))
