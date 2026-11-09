"""Checking one theme's table against the model: every key, every value, strictly.

Key names: `check_theme`, which checks a read theme file's table against the style groups
and returns it converted, with every problem found; `build_group`, which builds one group
from a full, checked table; `RENAMED_KEYS`, the old key paths and what each is called now.

A theme's top level holds `extends`, a theme name or a `.yaml` path, and the group names.
Every key at every level is checked: a group's fields, a dict field's entries against its
vocabulary in `theme_vocab`, and a `brush_overrides` entry's keys. An unknown key is
refused with the nearest known one, and a renamed key with its new name. A group, a dict
field or a sub-table given a value that is not a mapping is refused. Each leaf is
validated by pydantic in strict mode against its field's type, so `"5"` is not a number,
`1` is not a boolean and `5.0` is not a whole number, while an integer for a float is
taken as that float. Brush ids must name a cell on the brush sheet, and colours must be
`#` and six hexadecimal digits. A field typed as a dataclass is a sub-table, checked by
the same rules, its entries a nested dict, and `build_group` builds it as that dataclass.

Does not read files, resolve `extends`, merge themes, check numeric ranges or raise; never
reports the reader's own problems, which the caller reports, and imports no style model:
the caller passes the groups.

Invariants: the returned table holds only valid, converted leaves, each the type its field
is built from; every problem names its dotted key path and the line of that key, or of its
nearest ancestor present in the file; problems are in line order.
"""

from collections.abc import Mapping
from typing import Any

from pyntpot.maps.theme_checker import TableCheck, group_hints, is_dataclass
from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_read import ThemeFile

#: Old key paths and what each is called now; a theme that uses one is told the new name.
RENAMED_KEYS: dict[tuple[str, ...], str] = {
    ("route_ink", "style"): "drawn_as",  # ADR 0069 (#182)
}

#: The top-level key naming the theme a theme overrides.
EXTENDS = "extends"


def check_theme(
    theme: ThemeFile,
    groups: Mapping[str, type],
    *,
    renamed: Mapping[tuple[str, ...], str] = RENAMED_KEYS,
) -> tuple[dict[str, object], tuple[ThemeProblem, ...]]:
    """Check `theme`'s table against `groups`, returning it converted and every problem in it.

    Args:
        theme: A read theme file; only its `table` and `lines` are read.
        groups: Each style group's dataclass, by its key in a theme.
        renamed: Old key paths and their new names.

    Returns:
        The table with each valid leaf converted to its field's type and each invalid one
        left out, and every problem found, in line order.
    """
    check = TableCheck(theme, renamed)
    table: dict[str, object] = {}
    for key, value in theme.table.items():
        path = (key,)
        if key == EXTENDS:
            if isinstance(value, str):
                table[key] = value
            else:
                check.problem(path, "extends is a theme name or a .yaml path")
        elif key in groups:
            checked = check.table(groups[key], value, path)
            if checked is not None:
                table[key] = checked
        else:
            check.unknown(path, (EXTENDS, *groups))
    return table, check.problems()


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
