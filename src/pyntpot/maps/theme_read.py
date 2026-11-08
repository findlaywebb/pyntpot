"""Reading one theme file: YAML in, plain data and the line of every key out.

Key types: `ThemeFile`, one file read into plain dicts, tuples and scalars, with the
1-based line of every mapping key and every problem found; `read_theme`, which reads one.

A theme is plain YAML 1.2: one document, a mapping of style groups with string keys. The
reader runs the event walk of `theme_walk` first, which reports every YAML feature a theme
may not use, every key that is not a string, every duplicate key, nesting past its cap,
every value that cannot be read, and the character or syntax error that ends it. A file
with any such problem loads nothing. Otherwise it is loaded, and each key that holds no
value is reported and left out.

Does not check keys or values against the model, resolve `extends`, merge themes, read
files from disk, or raise: every problem is returned, and the caller reports them. With
`theme_walk`, the one module that touches `ruamel.yaml`. A mapping, a sequence, a bool, an
int, a float and a string come out as the built-in type; a null inside a sequence stays
`None`, for the checker to refuse.

Invariants: `read_theme` never raises for any text, because the load runs only on a text
the walk passed, whose every key is a string, unique in its mapping, whose every number
constructs and whose nesting is bounded; `table` is empty whenever the walk found a
problem; `problems` are in line order.
"""

from dataclasses import dataclass
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from pyntpot.maps.theme_errors import ThemeProblem
from pyntpot.maps.theme_walk import Found, walk


@dataclass(frozen=True, kw_only=True)
class ThemeFile:
    """One theme file read into plain data, with where each key sits.

    Attributes:
        path: The file, as the caller named it.
        table: The file's content as plain dicts, tuples and scalars; empty when the
            event walk found a problem.
        lines: The 1-based line of every mapping key, by key path.
        problems: What the walk, the load and the conversion found, in line order.
    """

    path: Path
    table: dict[str, object]
    lines: dict[tuple[str, ...], int]
    problems: tuple[ThemeProblem, ...]


def read_theme(path: Path, text: str) -> ThemeFile:
    """Read the theme file `path`, whose content is `text`, into plain data and its problems.

    Args:
        path: The file, as the caller names it; it is not opened.
        text: The file's content.

    Returns:
        The file's table, the line of every key, and every problem found. Never raises
        for any text.
    """
    found = walk(text)
    if found:
        return _file(path, {}, {}, found)
    loaded = YAML(typ="rt").load(text)
    if loaded is None:
        return _file(path, {}, {}, [])
    if not isinstance(loaded, CommentedMap):
        return _file(path, {}, {}, [((), 1, "a theme is a mapping of style groups")])
    lines: dict[tuple[str, ...], int] = {}
    table = _table(loaded, (), lines, found)
    return _file(path, table, lines, found)


def _file(
    path: Path, table: dict[str, object], lines: dict[tuple[str, ...], int], found: list[Found]
) -> ThemeFile:
    """Assemble the `ThemeFile` for `path`, placing each found problem in it, in line order."""
    problems = tuple(
        ThemeProblem(path=path, key=".".join(keys), line=line, message=message)
        for keys, line, message in sorted(found, key=lambda one: one[1] or 0)
    )
    return ThemeFile(path=path, table=table, lines=lines, problems=problems)


# ---------------------------------------------------------------------------
# The conversion
# ---------------------------------------------------------------------------


def _table(
    node: CommentedMap,
    prefix: tuple[str, ...],
    lines: dict[tuple[str, ...], int],
    found: list[Found],
) -> dict[str, object]:
    """`node` as a plain dict, recording each key's line and each key with no value."""
    table: dict[str, object] = {}
    for key, value in node.items():
        line = node.lc.key(key)[0] + 1
        here = (*prefix, str(key))
        lines[here] = line
        if value is None:
            found.append((here, line, "has no value"))
            continue
        table[str(key)] = _plain(value, here, lines, found)
    return table


def _plain(
    value: object,
    path: tuple[str, ...],
    lines: dict[tuple[str, ...], int],
    found: list[Found],
) -> object:
    """`value` as plain data: a mapping a dict, a sequence a tuple, a scalar its built-in type."""
    if isinstance(value, CommentedMap):
        return _table(value, path, lines, found)
    if isinstance(value, CommentedSeq):
        return tuple(_plain(item, path, lines, found) for item in value)
    for kind in (bool, int, float, str):
        if isinstance(value, kind):
            return kind(value)
    return value
