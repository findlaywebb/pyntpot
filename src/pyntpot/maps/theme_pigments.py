"""A theme's `pigments:` table: pigments of its own, each derived from a built-in or inherited one.

Key name: `check_pigments`, which checks one file's `pigments` table and adds its pigments to the
scope.

A pigment is a key matching `ALIAS_PATTERN`, its value a table of `base` (a built-in pigment or
one inherited from a file below), `colour` (a hex), `transparency` (0 to 1), `colour_index` and
`override`. At least one of `base` and `colour` is required, and both may be given: a field
given overrides the base's, and a field left out is the base's. A name equal to a built-in is
refused with the derived form to write instead, and a name equal to an alias is refused, since an
alias name is no pigment name. Replacing an inherited pigment needs `override: true` and is an
error at the replacing key's line without it.

Does not resolve colour fields or bind aliases, read files or raise; every problem is recorded on
the check, at its key's line. A pigment with no `colour` and no `base` has no colour to hold and
is refused.

Invariants: every entry bound names this file and its key's line; a pigment that fails is left
out; the scope returned is a new one, and the scope passed in is untouched.
"""

import dataclasses
import re

from pyntpot.ink.colour import Colour
from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY
from pyntpot.ink.pigment_table import Pigment
from pyntpot.maps.theme_checker import TableCheck
from pyntpot.maps.theme_scope import Bound, ThemeScope
from pyntpot.maps.theme_vocab import ALIAS_PATTERN

#: The top-level key of the pigment table.
PIGMENTS = "pigments"

#: The keys of a pigment.
_KEYS = ("base", "colour", "transparency", "colour_index", "override")


def check_pigments(check: TableCheck, value: object, scope: ThemeScope) -> ThemeScope:
    """Check the `pigments` table `value` of the file under `check`, adding its pigments.

    Args:
        check: The file's check; problems are recorded on it.
        value: The raw `pigments` value.
        scope: The names inherited from the files below.

    Returns:
        `scope` with the file's valid pigments added, each over any it replaces.
    """
    path = (PIGMENTS,)
    if not isinstance(value, dict):
        check.problem(path, "is a table of keys")
        return scope
    pigments = dict(scope.pigments)
    for name, item in value.items():
        here = (PIGMENTS, name)
        if not _name_free(check, name, item, scope, here):
            continue
        built = _pigment(check, name, item, scope, here)
        if built is not None:
            pigments[name] = Bound(built, check.theme.path, check.theme.lines[here])
    return dataclasses.replace(scope, pigments=pigments)


def _name_free(
    check: TableCheck, name: str, item: object, scope: ThemeScope, here: tuple[str, ...]
) -> bool:
    """Whether `name` may be added as a pigment here; the problem is recorded when not."""
    message = _refusal(name, item, scope)
    if message is not None:
        check.problem(here, message)
    return message is None


def _refusal(name: str, item: object, scope: ThemeScope) -> str | None:
    """Why `name` may not be added as a pigment, or `None`."""
    if name in PIGMENT_REGISTRY:
        return f"{name!r} is a built-in pigment; derive one: my_{name}: {{base: {name}}}"
    if re.fullmatch(ALIAS_PATTERN, name) is None:
        return f"{name!r} is not a pigment name: lower-case words joined by single _"
    if name in scope.aliases or name in scope.palette_aliases:
        return f"{name!r} is an alias; a pigment needs a name of its own"
    return _replacement(name, item, scope)


def _replacement(name: str, item: object, scope: ThemeScope) -> str | None:
    """Why `name` may not be bound given what the scope holds and `override`, or `None`."""
    taken = scope.pigments.get(name)
    override = isinstance(item, dict) and item.get("override") is True
    if override and taken is None:
        return f"{name!r} overrides no pigment; drop override: true"
    if taken is not None and not override:
        return (
            f"{name!r} is already a theme pigment ({taken.path}:{taken.line}); add override: true"
        )
    return None


def _pigment(
    check: TableCheck, name: str, item: object, scope: ThemeScope, here: tuple[str, ...]
) -> Pigment | None:
    """The pigment `item` describes under `name`, or `None` with the problems recorded."""
    if not isinstance(item, dict):
        check.problem(here, "is a table of base, colour, transparency, colour_index and override")
        return None
    for key in item:
        if key not in _KEYS:
            check.unknown((*here, key), _KEYS)
    if "base" not in item and "colour" not in item:
        check.problem(here, "needs a base pigment or a colour")
        return None
    before = len(check.found)
    base = _base(check, item, scope, here)
    colour = _colour(check, item, here)
    transparency = _transparency(check, item, here)
    index = _text(check, item, "colour_index", here)
    flag = check.leaf(bool, item.get("override", False), (*here, "override"))
    if len(check.found) > before or flag is None:
        return None
    return _derive(name, item, (base, colour, transparency, index))


def _derive(
    name: str,
    item: dict[str, object],
    given: tuple[Pigment | None, Colour | None, float | None, str | None],
) -> Pigment:
    """The pigment `name` from its checked `given` base, colour, transparency and index."""
    base, colour, transparency, index = given
    if base is None:
        assert colour is not None  # `_pigment` refused an item with neither base nor colour
        return Pigment(name=name, colour=colour, transparency=transparency, colour_index=index)
    return Pigment(
        name=name,
        colour=colour or base.colour,
        transparency=transparency if "transparency" in item else base.transparency,
        colour_index=index if "colour_index" in item else base.colour_index,
    )


def _base(
    check: TableCheck, item: dict[str, object], scope: ThemeScope, here: tuple[str, ...]
) -> Pigment | None:
    """The pigment `base` names, a built-in or an inherited one, or `None`."""
    if "base" not in item:
        return None
    at = (*here, "base")
    text = check.leaf(str, item["base"], at)
    if not isinstance(text, str):
        return None
    try:
        return scope.registry.get(text)
    except ValueError as exc:
        check.problem(at, str(exc))
        return None


def _colour(check: TableCheck, item: dict[str, object], here: tuple[str, ...]) -> Colour | None:
    """The hex `colour` gives, or `None` when absent or refused."""
    if "colour" not in item:
        return None
    at = (*here, "colour")
    text = check.leaf(str, item["colour"], at)
    if not isinstance(text, str):
        return None
    try:
        return Colour.parse(text)
    except ValueError as exc:
        check.problem(at, str(exc))
        return None


def _transparency(
    check: TableCheck, item: dict[str, object], here: tuple[str, ...]
) -> float | None:
    """The `transparency` given, 0 to 1, or `None` when absent or refused."""
    if "transparency" not in item:
        return None
    at = (*here, "transparency")
    number = check.leaf(float, item["transparency"], at)
    if not isinstance(number, float):
        return None
    if not 0.0 <= number <= 1.0:
        check.problem(at, f"{number!r} is not from 0 to 1")
        return None
    return number


def _text(
    check: TableCheck, item: dict[str, object], key: str, here: tuple[str, ...]
) -> str | None:
    """The string `key` gives, or `None` when absent or refused."""
    if key not in item:
        return None
    text = check.leaf(str, item[key], (*here, key))
    return text if isinstance(text, str) else None
