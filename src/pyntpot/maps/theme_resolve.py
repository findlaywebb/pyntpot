"""Resolving a theme: its name or file, its `extends` chain, every problem, one merged table.

Key names: `resolve`, which turns a theme, given by its name or its `.yaml` file, into the
full table of every group, or raises one `ThemeError` holding every problem in the chain;
`names_in` and `theme_names`, the theme names a directory and the package hold; `NAME`,
the form of a theme name.

A `.yaml` path is read relative to the caller's directory unless absolute; a `.yml` or
`.toml` path, a `Path` with any other suffix, and a `str` that is no packaged name are
refused, each with what to write instead. `default` is the base table itself, with no
file. A theme's `extends`, `default` when absent, names the theme below it by the same
rule, a relative path read from the extending file's directory, until `default`. Each
file is read and, when the read found nothing, checked; every problem of every file in
the chain is collected, and the chain stops at a file whose read found a problem. A file
met twice in one chain is an `extends` cycle.

A theme an `extends` names that is refused, missing or a cycle is a problem of the
extending file, at its `extends` key and line, whose message names the target as written;
the caller's own theme, which no file names, is a problem of the name or path as given. A
file that is not UTF-8 text, or cannot be read, is a problem of that file.

Does not check keys or values itself, build a style, or log; imports no style model: the
caller passes the groups and the base table. The one place a file's read problems are
reported.

Invariants: the merged table is the base, then each theme of the chain from the one
nearest `default` to the one named, each over the table its check converted, so every
leaf is its field's own type; it holds no `extends`; a problem anywhere raises.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path, PurePath
from typing import NoReturn

from pyntpot.maps.theme_check import EXTENDS, check_theme
from pyntpot.maps.theme_errors import ThemeError, ThemeProblem
from pyntpot.maps.theme_merge import merge
from pyntpot.maps.theme_read import ThemeFile, read_theme

#: The form of a theme name: a lower-case letter, then lower-case letters, digits and `-`.
NAME = re.compile(r"[a-z][a-z0-9-]*")

#: The packaged theme with no file: the base table itself.
DEFAULT = "default"

#: The suffix of a theme file.
_YAML = ".yaml"


@dataclass(frozen=True, kw_only=True)
class _Named:
    """Where a theme was named: the key and line naming it, and the directory it is read from.

    Attributes:
        key: `""` for the caller's theme, `extends` for a theme an `extends` names.
        line: The `extends` key's line, or `None` for the caller's theme.
        directory: The directory a relative path is read from.
        by: The file whose `extends` names the theme, or `None` for the caller's theme.
    """

    key: str
    line: int | None
    directory: Path
    by: Path | None = None


def names_in(directory: Traversable) -> tuple[str, ...]:
    """`default` and the stem of every `.yaml` file in `directory`, sorted together.

    Args:
        directory: A themes directory; one that is not a directory holds no files.

    Returns:
        The theme names, `default` among them.
    """
    if not directory.is_dir():
        return (DEFAULT,)
    stems = {
        entry.name.removesuffix(_YAML)
        for entry in directory.iterdir()
        if entry.name.endswith(_YAML) and entry.is_file()
    }
    return tuple(sorted({DEFAULT, *stems}))


def theme_names() -> tuple[str, ...]:
    """The names of the packaged themes, `default` among them, sorted."""
    return names_in(_packaged())


def resolve(
    theme: str | Path,
    *,
    relative_to: Path,
    groups: Mapping[str, type],
    base: Mapping[str, object],
) -> dict[str, object]:
    """The full table `theme` describes: `base`, then its `extends` chain, then `theme`.

    Args:
        theme: A packaged theme's name, or a `.yaml` file as a `str` or a `Path`.
        relative_to: The directory a relative path is read from.
        groups: Each style group's dataclass, by its key in a theme.
        base: The default table, one entry per group.

    Returns:
        A table with every key of `base`, each theme's converted values laid over it.

    Raises:
        ThemeError: When `theme`, or any theme it extends, has a problem; every
            problem found in the chain is in its problems.
    """
    problems: list[ThemeProblem] = []
    tables: list[dict[str, object]] = []
    chain: list[Path] = []
    named: str | Path | None = theme
    where = _Named(key="", line=None, directory=relative_to)
    while named is not None:
        try:
            file = _load(named, where, chain)
        except ThemeError as exc:
            problems.extend(exc.problems)
            break
        if file is None:
            break
        problems.extend(file.problems)
        if file.problems:
            break
        table, found = check_theme(file, groups)
        problems.extend(found)
        tables.append(table)
        chain.append(file.path.resolve())
        extends = table.get(EXTENDS, DEFAULT)
        named = extends if isinstance(extends, str) else None
        where = _Named(
            key=EXTENDS, line=file.lines.get((EXTENDS,)), directory=file.path.parent, by=file.path
        )
    if problems:
        raise ThemeError(problems)
    merged = dict(base)
    for table in reversed(tables):
        merged = merge(merged, table)
    merged.pop(EXTENDS, None)
    return merged


def _load(theme: str | Path, where: _Named, chain: list[Path]) -> ThemeFile | None:
    """Read the file `theme` names, or `None` for `default`.

    Raises:
        ThemeError: When `theme` is refused, names no file, or closes a cycle in `chain`.
    """
    suffix = PurePath(theme).suffix
    if suffix == _YAML:
        return _read_path(theme, where, chain)
    given = f"'{theme}'"
    if suffix == ".yml":
        stem = PurePath(theme).stem
        _refuse(theme, where, f"{given}: theme files end in .yaml; did you mean '{stem}.yaml'?")
    if suffix == ".toml":
        _refuse(
            theme,
            where,
            f"{given}: themes are YAML since ADR 0069: "
            "see 'Convert a TOML theme' in the theme how-to",
        )
    if isinstance(theme, Path):
        _refuse(theme, where, f"{given}: a theme file ends in .yaml")
    return _read_name(theme, where)


def _read_path(theme: str | Path, where: _Named, chain: list[Path]) -> ThemeFile:
    """Read the `.yaml` file `theme`, relative to `where`'s directory unless absolute.

    Raises:
        ThemeError: When no such file exists, it cannot be read as UTF-8 text, or it is
            already in `chain`.
    """
    given = Path(theme)
    path = given if given.is_absolute() else where.directory / given
    if path.resolve() in chain:
        names = [*(seen.name for seen in chain), path.name]
        problem = ThemeProblem(
            path=where.by or path,
            key=where.key,
            line=where.line,
            message=f"extends cycle: {' -> '.join(names)}",
        )
        raise ThemeError([problem])
    try:
        return _read_file(path)
    except FileNotFoundError as exc:
        _refuse(theme, where, f"no such theme file: {path}", cause=exc)


def _read_name(theme: str, where: _Named) -> ThemeFile | None:
    """Read the packaged theme named `theme`, or `None` for `default`.

    Raises:
        ThemeError: When `theme` is not a name, or names no packaged theme.
    """
    names = theme_names()
    available = ", ".join(names)
    if not theme:
        _refuse(theme, where, f"an empty theme name; available: {available}")
    if NAME.fullmatch(theme) is None:
        _refuse(
            theme,
            where,
            f"'{theme}' is neither a theme name nor a .yaml path; available: {available}",
        )
    if theme not in names:
        _refuse(theme, where, f"no theme named '{theme}'; available: {available}")
    if theme == DEFAULT:
        return None
    with resources.as_file(_packaged() / f"{theme}{_YAML}") as path:
        return _read_file(path)


def _read_file(path: Path) -> ThemeFile:
    """Read the theme file at `path` as UTF-8 text.

    Raises:
        FileNotFoundError: When there is no file at `path`, for the caller to place.
        ThemeError: When the file is not UTF-8 text, at the first bad byte's line, or
            cannot be read.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise
    except UnicodeDecodeError as exc:
        line = exc.object.count(b"\n", 0, exc.start) + 1
        message = f"not UTF-8 text: cannot decode byte 0x{exc.object[exc.start]:02x}"
        raise ThemeError([ThemeProblem(path=path, key="", line=line, message=message)]) from exc
    except OSError as exc:
        message = f"cannot be read: {exc.strerror or exc}"
        raise ThemeError([ThemeProblem(path=path, key="", line=None, message=message)]) from exc
    return read_theme(path, text)


def _refuse(
    theme: str | Path, where: _Named, message: str, *, cause: Exception | None = None
) -> NoReturn:
    """Refuse `theme`, named at `where`, with `message`, which names `theme` as given.

    The problem is the extending file's, at its `extends` key and line; for the caller's
    theme, which no file names, it is `theme` itself, as the caller gave it.

    Raises:
        ThemeError: Always, holding the one problem, from `cause` when there is one.
    """
    problem = ThemeProblem(
        path=where.by or Path(theme), key=where.key, line=where.line, message=message
    )
    raise ThemeError([problem]) from cause


def _packaged() -> Traversable:
    """The package's themes directory."""
    return resources.files("pyntpot.maps") / "themes"
