"""Checking one theme's table against the model: every key, every value, strictly.

Key names: `check_theme`, which checks a read theme file's table against the style groups
and returns it converted, with every problem found; `check_theme_scoped`, the same in the names
an `extends` chain has bound, returning the scope the next file up inherits; `build_group`,
which builds one group from a full, checked table; `RENAMED_KEYS`, the old key paths and what
each is called now.

A theme's top level holds `extends`, a theme name or a `.yaml` path, `pigments`, `palette` and
`colours` (each checked by its own `theme_*` module, in that order, into the scope), the group
names, `effect_presets` and `line_effects` (checked by `theme_effects` after the groups, the
second split into `basemap.line_effects` and `route_ink.effects` in the returned table) and
`casing_unions` (checked by `theme_unions` last, into `basemap.casing_unions`). A colour
field then resolves in the scope its own file sees. The three group fields that only `line_effects`
and `casing_unions` set, `LOADER_FIELDS` in `theme_vocab`, are refused inside their group, at their own key.
Every key at every level is checked: a group's fields, a dict field's entries against its
vocabulary in `theme_vocab`, and a `brush_overrides` entry's keys. An unknown key is
refused with the nearest known one, and a renamed key with its new name. A group, a dict
field or a sub-table given a value that is not a mapping is refused. Each leaf is
validated by pydantic in strict mode against its field's type, so `"5"` is not a number,
`1` is not a boolean and `5.0` is not a whole number, while an integer for a float is
taken as that float. Brush ids must name a cell on the brush sheet, and colours must be
a hex, a pigment name or an alias in the file's scope. A field typed as a dataclass is a sub-table, checked by
the same rules, its entries a nested dict, and `build_group` builds it as that dataclass.

Does not resolve `extends`, merge themes, check a style group's numeric ranges (`theme_effects` checks a line
effect's, against `EFFECT_RANGES`) or raise; never reports the
reader's own problems, which the caller reports, and imports no style model: the caller
passes the groups. The only file it reads is a palette a `palette:` key names, in
`theme_palette`.

Invariants: the returned table holds only valid, converted leaves, each the type its field
is built from; every problem names its dotted key path and the line of that key, or of its
nearest ancestor present in the file; problems are in line order.
"""

from collections.abc import Mapping
from typing import Any

from pyntpot.maps.theme_checker import TableCheck, group_hints, is_dataclass
from pyntpot.maps.theme_colours import COLOURS, check_colours
from pyntpot.maps.theme_effects import (
    EFFECT_PRESETS,
    LINE_EFFECTS,
    check_effect_presets,
    check_line_effects,
)
from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_merge import merge
from pyntpot.maps.theme_palette import PALETTE, check_palette
from pyntpot.maps.theme_pigments import PIGMENTS, check_pigments
from pyntpot.maps.theme_read import ThemeFile
from pyntpot.maps.theme_scope import ThemeScope
from pyntpot.maps.theme_unions import CASING_UNIONS, check_casing_unions
from pyntpot.maps.theme_vocab import LOADER_FIELDS

#: Old key paths and what each is called now; a theme that uses one is told the new name.
RENAMED_KEYS: dict[tuple[str, ...], str] = {
    ("route_ink", "style"): "drawn_as",  # ADR 0069 (#182)
    # Its value moved, so the error names where (a departure from ADR 0069's unknown-key rule).
    ("paper", "pigment_transparency"): "cover.pigments.<class>.transparency",
}

#: The top-level key naming the theme a theme overrides.
EXTENDS = "extends"

#: The top-level steps that fill the scope, in the order a file is checked.
_STEPS = (
    (PIGMENTS, check_pigments),
    (PALETTE, check_palette),
    (COLOURS, check_colours),
)

#: The top-level keys that are names, not groups.
_NAMES = (*(key for key, _ in _STEPS), EFFECT_PRESETS, LINE_EFFECTS, CASING_UNIONS)


def check_theme(
    theme: ThemeFile,
    groups: Mapping[str, type],
    *,
    renamed: Mapping[tuple[str, ...], str] = RENAMED_KEYS,
) -> tuple[dict[str, object], tuple[ThemeProblem, ...]]:
    """Check `theme`'s table against `groups` in the built-in scope.

    Args:
        theme: A read theme file; only its `table` and `lines` are read.
        groups: Each style group's dataclass, by its key in a theme.
        renamed: Old key paths and their new names.

    Returns:
        The table with each valid leaf converted to its field's type and each invalid one
        left out, and every problem found, in line order.
    """
    table, problems, _ = check_theme_scoped(theme, groups, ThemeScope.built_in(), renamed=renamed)
    return table, problems


def check_theme_scoped(
    theme: ThemeFile,
    groups: Mapping[str, type],
    scope: ThemeScope,
    *,
    renamed: Mapping[tuple[str, ...], str] = RENAMED_KEYS,
) -> tuple[dict[str, object], tuple[ThemeProblem, ...], ThemeScope]:
    """Check `theme`'s table against `groups`, in the names `scope` holds, and bind its own.

    The file's `pigments` are checked first, then its `palette`, then its `colours`, then the
    groups, then its `effect_presets` and `line_effects`, each in the scope the earlier steps
    built.

    Args:
        theme: A read theme file; only its `table` and `lines` are read.
        groups: Each style group's dataclass, by its key in a theme.
        scope: The names the files below this one bound.
        renamed: Old key paths and their new names.

    Returns:
        The table with each valid leaf converted and each invalid one left out (the
        `pigments`, `palette`, `colours` and `effect_presets` keys are consumed into the scope,
        not kept; `line_effects` is split into the group fields and merged into the table),
        every problem found in line order, and the scope the files above this one inherit.
    """
    check = TableCheck(theme, renamed, scope)
    table: dict[str, object] = {}
    for key, value in theme.table.items():
        if key == EXTENDS:
            if isinstance(value, str):
                table[key] = value
            else:
                check.problem((key,), "extends is a theme name or a .yaml path")
        elif key not in _NAMES and key not in groups:
            check.unknown((key,), (EXTENDS, *_NAMES, *groups))
    for key, step in _STEPS:
        if key in theme.table:
            scope = step(check, theme.table[key], scope)
    check.scope = scope
    for key, value in theme.table.items():
        if key in groups:
            checked = check.table(groups[key], _without_loader_fields(check, key, value), (key,))
            if checked is not None:
                table[key] = checked
    scope, table = _check_effects(check, theme, table, scope)
    return table, check.problems(), scope


def _check_effects(
    check: TableCheck, theme: ThemeFile, table: dict[str, object], scope: ThemeScope
) -> tuple[ThemeScope, dict[str, object]]:
    """Check the file's `effect_presets`, `line_effects` and `casing_unions`, merging into `table`."""
    if EFFECT_PRESETS in theme.table:
        scope = check_effect_presets(check, theme.table[EFFECT_PRESETS], scope)
        check.scope = scope
    if LINE_EFFECTS in theme.table:
        table = merge(table, check_line_effects(check, theme.table[LINE_EFFECTS]))
    if CASING_UNIONS in theme.table:
        table = merge(table, check_casing_unions(check, theme.table[CASING_UNIONS]))
    return scope, table


def _without_loader_fields(check: TableCheck, group: str, value: object) -> object:
    """`value`, the group's raw table, less each loader-only field, each refused where written."""
    if not isinstance(value, dict):
        return value
    kept = dict(value)
    for (owner, name), setter in LOADER_FIELDS.items():
        if owner == group and name in kept:
            del kept[name]
            check.problem((group, name), f"set only by the top-level {setter}")
    return kept


def build_group[G](group: type[G], table: Mapping[str, object]) -> G:
    """Build `group` from the full, checked `table`, each sub-table as its own dataclass.

    Args:
        group: The group's dataclass.
        table: A value for every field, as `check_theme` converts them.

    Returns:
        The group, every dataclass-typed field built from its sub-table.
    """
    fields = group_hints(group)
    kwargs: dict[str, Any] = {}
    for name, value in table.items():
        hint = fields[name]
        if is_dataclass(hint) and isinstance(value, Mapping):
            kwargs[name] = build_group(hint, value)
        else:
            kwargs[name] = value
    return group(**kwargs)
