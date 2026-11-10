"""A theme's `colours:` table: aliases, each standing for the pigment it names.

Key names: `check_colours`, which checks one file's `colours` table and binds its aliases in the
scope; `overridden_aliases`, the aliases a file's raw `colours` marks `override: true`.

An alias is a key matching `ALIAS_PATTERN` that is no pigment name, built-in or the theme's. Its
value is a pigment name (built-in or the theme's own) or a hex, or a table of `colour` and
`override`. An alias never names another alias. The bound entry is the `Pigment` itself, so an
alias to a name keeps that pigment's transparency and Colour Index, and an alias to a hex is the
anonymous `pigment("#...")`. Replacing an alias the scope already holds, a theme's own from a
file below or the palette's, needs `override: true` and is an error at the replacing key's line
without it.

Does not resolve a colour field (`theme_checker` does, in the scope this fills), read palettes
or files, or raise; every problem is recorded on the check, at its key's line.

Invariants: every alias bound names this file and its key's line; an alias that fails is left
out; the scope returned is a new one, and the scope passed in is untouched.
"""

import dataclasses
import re
from collections.abc import Collection, Mapping

from pyntpot.ink.naming import nearest
from pyntpot.ink.pigment_table import Pigment
from pyntpot.maps.theme_checker import TableCheck
from pyntpot.maps.theme_scope import Bound, ThemeScope, resolve_pigment
from pyntpot.maps.theme_vocab import ALIAS_PATTERN

#: The top-level key of the alias table.
COLOURS = "colours"

#: The keys of an alias written as a table.
_ENTRY_KEYS = ("colour", "override")


def check_colours(check: TableCheck, value: object, scope: ThemeScope) -> ThemeScope:
    """Check the `colours` table `value` of the file under `check`, binding its aliases.

    Args:
        check: The file's check; problems are recorded on it.
        value: The raw `colours` value.
        scope: The names in force, this file's pigments and palette included.

    Returns:
        `scope` with the file's valid aliases bound, each over any it replaces.
    """
    path = (COLOURS,)
    if not isinstance(value, dict):
        check.problem(path, "is a table of keys")
        return scope
    aliases = dict(scope.aliases)
    for name, item in value.items():
        here = (COLOURS, name)
        entry = _entry(check, item, here)
        if entry is None:
            continue
        text, override = entry
        if not _name_free(check, name, scope, here, override=override):
            continue
        at = (*here, "colour") if isinstance(item, dict) else here
        bound = _pigment(check, text, scope, at, value)
        if bound is not None:
            aliases[name] = Bound(bound, check.theme.path, check.theme.lines[here])
    return dataclasses.replace(scope, aliases=aliases)


def overridden_aliases(table: Mapping[str, object]) -> frozenset[str]:
    """The aliases `table`'s raw `colours` marks `override: true`; none when it is no table."""
    colours = table.get(COLOURS)
    if not isinstance(colours, dict):
        return frozenset[str]()
    return frozenset(
        str(name)
        for name, item in colours.items()
        if isinstance(item, dict) and item.get("override") is True
    )


def _entry(check: TableCheck, item: object, here: tuple[str, ...]) -> tuple[str, bool] | None:
    """The colour text and the override flag of the alias value `item`, or `None` when refused."""
    if isinstance(item, str):
        return item, False
    if not isinstance(item, dict):
        check.problem(here, "is a pigment name, a hex or a table of colour and override")
        return None
    for key in item:
        if key not in _ENTRY_KEYS:
            check.unknown((*here, key), _ENTRY_KEYS)
    if "colour" not in item:
        check.problem(here, "needs a colour: a pigment name or a hex")
        return None
    text = check.leaf(str, item["colour"], (*here, "colour"))
    flag = check.leaf(bool, item.get("override", False), (*here, "override"))
    if not isinstance(text, str) or not isinstance(flag, bool):
        return None
    return text, flag


def _name_free(
    check: TableCheck, name: str, scope: ThemeScope, here: tuple[str, ...], *, override: bool
) -> bool:
    """Whether `name` may be bound as an alias here; the problem is recorded when not."""
    message = _refusal(name, scope)
    if message is None:
        replaces = _replaces(name, scope)
        if override and replaces is None:
            message = f"{name!r} overrides no alias; drop override: true"
        elif not override:
            message = replaces
    if message is not None:
        check.problem(here, message)
    return message is None


def _refusal(name: str, scope: ThemeScope) -> str | None:
    """Why `name` can be no alias at all, or `None`."""
    if re.fullmatch(ALIAS_PATTERN, name) is None:
        return f"{name!r} is not an alias: lower-case words joined by single _"
    if name in scope.registry:
        return f"{name!r} is a pigment name; an alias needs a name of its own"
    return None


def _replaces(name: str, scope: ThemeScope) -> str | None:
    """The problem of binding `name` over an alias the scope holds, or `None` when none."""
    taken = scope.aliases.get(name)
    if taken is not None:
        return f"{name!r} is already an alias ({taken.path}:{taken.line}); add override: true"
    palette = scope.palette
    if palette is not None and name in scope.palette_aliases:
        where = f"{palette.path}:{palette.line}"
        message = f"{name!r} is already an alias of palette {palette.value.name!r} ({where}); "
        return message + "add override: true"
    return None


def _pigment(
    check: TableCheck, text: str, scope: ThemeScope, at: tuple[str, ...], table: Collection[str]
) -> Pigment | None:
    """The pigment `text` names, a hex or a pigment name, or `None` with the problem recorded."""
    bare = ThemeScope(pigments=scope.pigments)
    try:
        if text.startswith("#") or text in bare.registry:
            return resolve_pigment(text, bare)
    except ValueError as exc:
        check.problem(at, str(exc))
        return None
    if text in scope.aliases or text in scope.palette_aliases or text in table:
        check.problem(at, f"{text!r} is an alias; an alias names a pigment or a hex")
        return None
    hint = "".join(f"; did you mean {name}?" for name in nearest(text, bare.registry.names()))
    check.problem(at, f"{text!r} is not a pigment or a hex{hint}")
    return None
