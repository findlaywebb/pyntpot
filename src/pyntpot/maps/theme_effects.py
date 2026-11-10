"""A theme's `effect_presets:` and `line_effects:` tables: effect stacks, by preset and by line class.

Key names: `check_effect_presets`, which checks one file's `effect_presets` table and binds its
presets in the scope; `check_line_effects`, which checks its `line_effects` table and returns the
partial group table that table sets; `EFFECT_PRESETS` and `LINE_EFFECTS`, the two top-level keys.

A stack is a table whose keys are `casing`, `glow` and `shadow`, applied in key order; each
effect is a sub-table of its dataclass in `ink`, checked by the same rules as a style group's, so
its colour resolves through the file's scope. A `line_effects` key is a line class, and its value
is a preset name (a built-in or one in scope) or a stack, never a mix: a `preset` key beside the
effects is refused. A theme preset takes an alias-shaped name that is no built-in preset, and
replacing an inherited one needs `override: true`, as for an alias.

Every number is checked against `ink`'s `EFFECT_RANGES` and a value outside, or not finite, is a
located problem at `line_effects.<class>.<kind>.<field>`; nothing is clipped. The result is
split into `basemap.line_effects` (the seven basemap classes) and `route_ink.effects` (`route`),
adding only the entries the file writes. Each entry the file writes is kept as an explicit
`EffectStack`, an empty or all-off one included, so in the merge it replaces the parent's stack
whole; nothing is dropped here.

Does not merge files, drop off effects or empty stacks (the stack and the basemap group do, once,
after the final merge), build a style, or raise; every problem is recorded on the check.

Invariants: every stack returned is valid; a stack with a refused effect keeps the others.
"""

import dataclasses
import math
import re
from typing import Any

from pyntpot.ink import Casing, Glow, Shadow
from pyntpot.ink.effect_types import EFFECT_RANGES
from pyntpot.ink.naming import nearest
from pyntpot.maps.line_effects import BUILT_IN_PRESETS, LINE_CLASSES, EffectStack
from pyntpot.maps.theme_checker import TableCheck
from pyntpot.maps.theme_scope import Bound, ThemeScope
from pyntpot.maps.theme_vocab import ALIAS_PATTERN

#: The top-level key of the preset table.
EFFECT_PRESETS = "effect_presets"

#: The top-level key of the per-class stacks.
LINE_EFFECTS = "line_effects"

#: The route's key in `line_effects`, set on `route_ink.effects`; the rest are basemap classes.
_ROUTE = "route"

#: The effect kinds a stack may hold, by key.
_KINDS: dict[str, type[Casing | Glow | Shadow]] = {"casing": Casing, "glow": Glow, "shadow": Shadow}

#: The key a preset entry may carry beside its effects, to replace an inherited preset.
_OVERRIDE = "override"

#: The message for a `line_effects` key that holds a stack and also names a preset.
_MIXED = "a line class takes a preset name or a stack, not both"

type _Path = tuple[str, ...]


def check_effect_presets(check: TableCheck, value: object, scope: ThemeScope) -> ThemeScope:
    """Check the `effect_presets` table `value` of the file under `check`, binding its presets.

    Args:
        check: The file's check; problems are recorded on it, and its scope resolves colours.
        value: The raw `effect_presets` value.
        scope: The names in force.

    Returns:
        `scope` with the file's valid presets bound, each over any it replaces.
    """
    path = (EFFECT_PRESETS,)
    if not isinstance(value, dict):
        check.problem(path, "is a table of keys")
        return scope
    presets = dict(scope.presets)
    for name, item in value.items():
        here = (EFFECT_PRESETS, name)
        override = _override(check, item, here)
        if not _name_free(check, name, scope, here, override=override):
            continue
        body = (
            {key: val for key, val in item.items() if key != _OVERRIDE}
            if isinstance(item, dict)
            else item
        )
        stack = _stack(check, body, here, mixed=False)
        if stack is not None:
            presets[name] = Bound(stack, check.theme.path, check.theme.lines[here])
    return dataclasses.replace(scope, presets=presets)


def check_line_effects(check: TableCheck, value: object) -> dict[str, object]:
    """Check the `line_effects` table `value` of the file under `check` and split it.

    Args:
        check: The file's check, its scope holding the presets in force.
        value: The raw `line_effects` value.

    Returns:
        A partial group table: `basemap.line_effects` holding the basemap classes written, and
        `route_ink.effects` when `route` is; a part nothing wrote is absent.
    """
    path = (LINE_EFFECTS,)
    if not isinstance(value, dict):
        check.problem(path, "is a table of keys")
        return {}
    basemap: dict[str, EffectStack] = {}
    table: dict[str, object] = {}
    for name, item in value.items():
        here = (LINE_EFFECTS, name)
        if name not in LINE_CLASSES:
            check.unknown(here, sorted(LINE_CLASSES))
            continue
        stack = _class_stack(check, item, here)
        if stack is None:
            continue
        if name == _ROUTE:
            table["route_ink"] = {"effects": stack}
        else:
            basemap[name] = stack
    if basemap:
        table["basemap"] = {"line_effects": basemap}
    return table


def _override(check: TableCheck, item: object, here: _Path) -> bool:
    """Whether the preset entry `item` is marked `override: true`; a non-boolean is refused."""
    if not isinstance(item, dict) or _OVERRIDE not in item:
        return False
    flag = check.leaf(bool, item[_OVERRIDE], (*here, _OVERRIDE))
    return flag is True


def _name_free(
    check: TableCheck, name: str, scope: ThemeScope, here: _Path, *, override: bool
) -> bool:
    """Whether `name` may be bound as a preset here; the problem is recorded when not."""
    message = None
    taken = scope.presets.get(name)
    if re.fullmatch(ALIAS_PATTERN, name) is None:
        message = f"{name!r} is not a preset name: lower-case words joined by single _"
    elif name in BUILT_IN_PRESETS:
        message = f"{name!r} is a built-in effect preset; give a preset a name of its own"
    elif override and taken is None:
        message = f"{name!r} overrides no effect preset; drop override: true"
    elif taken is not None and not override:
        message = f"{name!r} is already an effect preset ({taken.path}:{taken.line}); "
        message += "add override: true"
    if message is not None:
        check.problem(here, message)
    return message is None


def _class_stack(check: TableCheck, item: object, here: _Path) -> EffectStack | None:
    """The stack a `line_effects` value stands for: a preset name or a table of effects."""
    if isinstance(item, str):
        return _preset(check, item, here)
    if isinstance(item, dict):
        return _stack(check, item, here, mixed=True)
    check.problem(here, "is a preset name or a table of casing, glow and shadow")
    return None


def _preset(check: TableCheck, name: str, here: _Path) -> EffectStack | None:
    """The stack the preset `name` stands for in the check's scope, or `None` when it misses."""
    if name in BUILT_IN_PRESETS:
        return BUILT_IN_PRESETS[name]
    if name in check.scope.presets:
        return check.scope.presets[name].value
    known = (*BUILT_IN_PRESETS, *check.scope.presets)
    hint = "".join(f"; did you mean {near}?" for near in nearest(name, known))
    check.problem(here, f"{name!r} is not an effect preset{hint}")
    return None


def _stack(check: TableCheck, item: object, here: _Path, *, mixed: bool) -> EffectStack | None:
    """The stack the table `item` at `here` holds, each effect in key order, or `None` if no table.

    A stack with a refused effect keeps the effects that were valid; `mixed` marks a
    `line_effects` stack, whose `preset` key has its own message.
    """
    if not isinstance(item, dict):
        check.problem(here, "is a table of keys")
        return None
    effects: list[Casing | Glow | Shadow] = []
    for key, value in item.items():
        at = (*here, key)
        if key in _KINDS:
            effect = _effect(check, _KINDS[key], value, at)
            if effect is not None:
                effects.append(effect)
        elif mixed and key == "preset":
            check.problem(at, _MIXED)
        else:
            check.unknown(at, tuple(_KINDS))
    return EffectStack(effects=tuple(effects))


def _effect(
    check: TableCheck, kind: type[Casing | Glow | Shadow], value: object, at: _Path
) -> Casing | Glow | Shadow | None:
    """The effect of `kind` the table `value` at `at` holds, or `None` with problems recorded."""
    fields = check.table(kind, value, at)
    if fields is None:
        return None
    ranged = [_in_range(check, name, number, (*at, name)) for name, number in fields.items()]
    if not all(ranged):
        return None
    arguments: dict[str, Any] = dict(fields)
    return kind(**arguments)


def _in_range(check: TableCheck, name: str, number: object, at: _Path) -> bool:
    """Whether the field `name` is within its range in `EFFECT_RANGES`; the problem if not."""
    if name not in EFFECT_RANGES or not isinstance(number, float | int):
        return True
    low, high = EFFECT_RANGES[name]
    if math.isfinite(number) and low <= number <= high:
        return True
    check.problem(at, f"{name} is {number:.12g}; it must be from {low:g} to {high:g}")
    return False
