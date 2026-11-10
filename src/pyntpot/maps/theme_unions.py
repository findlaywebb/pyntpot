"""A theme's `casing_unions:` table: the shape of one file's unions, and where a problem sits.

Key names: `check_casing_unions`, which checks one file's `casing_unions` value and returns the
partial `basemap` table that sets it; `merged_union_problems`, which checks the merged basemap
table against its stacks and locates each problem in the nearest file that wrote
`casing_unions`; `CASING_UNIONS`, the top-level key.

`casing_unions` is a list of lists of basemap line classes. A child's list replaces its
parent's whole, and `[]` turns an inherited set off. A valid table is put in the group's class
order, each union's members first and the unions by their first member, so two themes that
paint one picture share a digest. This module checks the shape only ("is a list of lists of
line classes"); every other message is written by `casing_unions`, and this module gives it a
place. The reader records no line for a list entry, so every problem of a union carries the
line of the `casing_unions` key, and the key path names the union and the member.

A union that is fine alone can fail once the files are merged, because a child may turn off a
member's stack or change its colour. Those problems are located at `casing_unions.<i>` in the
nearest file of the chain that writes `casing_unions`, `<i>` being the union's place in that
file as written.

Does not merge files, read a file, drop a stack or raise: every problem is recorded or
returned. Imports no style model.

Invariants: the returned unions are tuples of tuples of class names; a problem names a file,
a dotted key path and a line.
"""

from collections.abc import Mapping, Sequence

from pyntpot.maps.casing_unions import membership_problems, union_problems
from pyntpot.maps.line_effects import ROAD_GROUP, WATER_GROUP, EffectStack
from pyntpot.maps.theme_checker import TableCheck
from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_read import ThemeFile

#: The top-level key of the union table.
CASING_UNIONS = "casing_unions"

_ORDER = {name: place for place, name in enumerate((*WATER_GROUP, *ROAD_GROUP))}
_SHAPE = "is a list of lists of line classes"


def check_casing_unions(check: TableCheck, value: object) -> dict[str, object]:
    """Check the `casing_unions` value of the file under `check` and normalise it.

    Args:
        check: The file's check; problems are recorded on it.
        value: The raw `casing_unions` value.

    Returns:
        `{"basemap": {"casing_unions": unions}}` with each union's members in class order and
        the unions by their first member, or `{}` when the value is no list of lists.
    """
    if not isinstance(value, list | tuple):
        check.problem((CASING_UNIONS,), _SHAPE)
        return {}
    unions: list[tuple[str, ...]] = []
    written: list[int] = []
    for index, union in enumerate(value):
        if not isinstance(union, list | tuple) or not all(isinstance(m, str) for m in union):
            check.problem((CASING_UNIONS, str(index)), _SHAPE)
            continue
        unions.append(tuple(union))
        written.append(index)
    for index, member, message in membership_problems(unions):
        at = (CASING_UNIONS, str(written[index]))
        check.problem(at if member is None else (*at, str(member)), message)
    return {"basemap": {CASING_UNIONS: _normalised(unions)}}


def _normalised(unions: Sequence[tuple[str, ...]]) -> tuple[tuple[str, ...], ...]:
    """`unions` with members in class order and the unions in the order of their first members."""
    sorted_members = [tuple(sorted(union, key=_place)) for union in unions]
    return tuple(sorted(sorted_members, key=lambda union: _place(union[0]) if union else 0))


def _place(name: str) -> int:
    """The place of the class `name` in the group's order; an unknown name sorts last."""
    return _ORDER.get(name, len(_ORDER))


def merged_union_problems(
    merged: Mapping[str, object], files: Sequence[ThemeFile]
) -> tuple[ThemeProblem, ...]:
    """The problems of the merged basemap's unions against its stacks, each located in a file.

    Args:
        merged: The merged table, its `basemap` holding `line_effects` and `casing_unions`.
        files: The chain's files, the named theme first.

    Returns:
        One problem per entry of `union_problems`, at `casing_unions.<i>` in the nearest file
        that writes `casing_unions`, on the line of that key.
    """
    basemap = merged.get("basemap")
    if not isinstance(basemap, Mapping):
        return ()
    unions = basemap.get(CASING_UNIONS, ())
    stacks = basemap.get("line_effects", {})
    if not unions or not isinstance(stacks, Mapping):
        return ()
    typed: dict[str, EffectStack] = {
        key: stack for key, stack in stacks.items() if isinstance(stack, EffectStack)
    }
    writer = next((file for file in files if CASING_UNIONS in file.table), files[0])
    return tuple(
        ThemeProblem(
            path=writer.path,
            key=f"{CASING_UNIONS}.{_written(writer, unions, index)}",
            line=writer.lines.get((CASING_UNIONS,)),
            message=message,
        )
        for index, _, message in union_problems(typed, unions)
    )


def _written(file: ThemeFile, unions: Sequence[Sequence[str]], index: int) -> int:
    """The place in `file` as written of the merged union `index`, or `index` if it is not found."""
    raw = file.table.get(CASING_UNIONS)
    if not isinstance(raw, list | tuple):
        return index
    wanted = set(unions[index])
    for place, union in enumerate(raw):
        if isinstance(union, list | tuple) and set(union) == wanted:
            return place
    return index
