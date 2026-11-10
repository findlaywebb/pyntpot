"""A palette: a named, shareable set of aliases, read from YAML or GIMP `.gpl`, and `palette:`.

Key names: `Palette`, a name and each alias mapped to the `Pigment` it stands for, with
`Palette.names`, `Palette.named`, `Palette.from_file`, `Palette.to_gpl` and
`Palette.registry_gpl`; `check_palette`, which checks a theme file's `palette:` key and puts the
palette in effect in the scope.

A palette `.yaml` holds only `colours:`, is read by the theme reader and checked by the same
alias rules as a theme's. A palette sees no theme, so its alias values are built-in pigment names
or hexes: an alias to a name holds that built-in pigment, transparency and Colour Index
included, and an alias to a hex holds the anonymous `pigment("#...")`. A `.gpl` imports as
anonymous pigments. The packaged palettes are the `.yaml` files in `maps/palettes`. A theme's
`palette:` is a packaged name or a `.yaml` or `.gpl` path relative to the theme's directory; the
nearest `palette:` in an `extends` chain is the one in effect, and an alias of it equal to an
inherited theme alias is an error at the `palette:` line unless the same file rebinds that
alias in `colours` with `override: true`.

Does not export a palette keyed by built-in names as one a theme can read back:
`Palette.registry_gpl` is text for other tools. A `.gpl` export drops transparency and Colour
Index. Does not bind `colours` (`theme_colours` does) or check colour fields.

Invariants: a palette is frozen; every alias matches `ALIAS_PATTERN` and is no built-in
pigment name; a palette that cannot be loaded raises `ThemeError` with its problems at the
palette file's own lines.
"""

from collections.abc import Mapping
from dataclasses import dataclass, replace
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path

from pyntpot.ink.naming import nearest
from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY, PigmentRegistry
from pyntpot.ink.pigment_table import Pigment
from pyntpot.maps.theme_checker import TableCheck
from pyntpot.maps.theme_colours import COLOURS, check_colours, overridden_aliases
from pyntpot.maps.theme_errors import ThemeError, ThemeProblem
from pyntpot.maps.theme_palette_gpl import parse_gpl, write_gpl
from pyntpot.maps.theme_read import read_theme
from pyntpot.maps.theme_scope import Bound, ThemeScope

#: The top-level key naming a palette.
PALETTE = "palette"

_YAML = ".yaml"
_GPL = ".gpl"


@dataclass(frozen=True)
class Palette:
    """A named set of aliases, each mapped to the pigment it stands for.

    Attributes:
        name: The packaged name, or the file's stem.
        pigments: Each alias and the `Pigment` it stands for: a built-in pigment for an alias
            to a name, the anonymous pigment of a hex otherwise.
    """

    name: str
    pigments: Mapping[str, Pigment]

    @staticmethod
    def names() -> tuple[str, ...]:
        """The names of the packaged palettes, sorted.

        Returns:
            The stem of every `.yaml` file in `maps/palettes`.
        """
        directory = _packaged()
        if not directory.is_dir():
            return ()
        return tuple(
            sorted(
                entry.name.removesuffix(_YAML)
                for entry in directory.iterdir()
                if entry.name.endswith(_YAML) and entry.is_file()
            )
        )

    @classmethod
    def named(cls, name: str) -> "Palette":
        """The packaged palette called `name`.

        Args:
            name: One of `Palette.names()`.

        Returns:
            The palette.

        Raises:
            ThemeError: When no packaged palette has this name, with the nearest name when
                one is close.
        """
        if name not in cls.names():
            raise ThemeError([_missing(Path(name), _unknown(name))])
        with resources.as_file(_packaged() / f"{name}{_YAML}") as path:
            return _from_yaml(path, name)

    @classmethod
    def from_file(cls, path: str | Path) -> "Palette":
        """The palette a `.yaml` or `.gpl` file holds.

        Args:
            path: A palette `.yaml` (only `colours:`) or a GIMP `.gpl` file.

        Returns:
            The palette, named by the file's stem.

        Raises:
            ThemeError: When the file is missing, unreadable, of another suffix, or has a
                problem; every problem is located at the file's own lines.
        """
        file = Path(path)
        if file.suffix not in (_YAML, _GPL):
            raise ThemeError([_missing(file, "a palette file ends in .yaml or .gpl")])
        if file.suffix == _YAML:
            return _from_yaml(file, file.stem)
        text = _text(file)
        aliases, problems = parse_gpl(file, text)
        if problems:
            raise ThemeError(problems)
        return cls(name=file.stem, pigments=aliases)

    def to_gpl(self) -> str:
        """This palette as GIMP `.gpl` text, each alias with its pigment's colour.

        Returns:
            The text; transparency and Colour Index are not in it.
        """
        return write_gpl(self.name, self.pigments)

    @staticmethod
    def registry_gpl(registry: PigmentRegistry = PIGMENT_REGISTRY) -> str:
        """`registry`'s pigments as GIMP `.gpl` text, under their canonical names.

        Args:
            registry: The pigments to list; the built-in registry when omitted.

        Returns:
            The text, in registry order, for other tools. The names are built-in names, so a
            theme cannot read it back as a palette.
        """
        return write_gpl("pyntpot", {name: registry.get(name) for name in registry.names()})


def check_palette(check: TableCheck, value: object, scope: ThemeScope) -> ThemeScope:
    """Check the `palette` key `value` of the file under `check`, putting its palette in effect.

    Args:
        check: The file's check; problems are recorded on it.
        value: The raw `palette` value.
        scope: The names inherited from the files below, this file's pigments included.

    Returns:
        `scope` with the palette in effect replaced, or `scope` itself when the value is
        refused.
    """
    path = (PALETTE,)
    if not isinstance(value, str):
        check.problem(path, "is a palette name or a .yaml or .gpl path")
        return scope
    palette = _load(check, value, path)
    if palette is None:
        return scope
    _clashes(check, palette, scope)
    line = check.theme.lines[path]
    return replace(scope, palette=Bound(palette, check.theme.path, line))


def _load(check: TableCheck, value: str, path: tuple[str, ...]) -> Palette | None:
    """The palette `value` names, or `None` with the problems recorded."""
    try:
        if value.endswith((_YAML, _GPL)):
            file = Path(value)
            file = file if file.is_absolute() else check.theme.path.parent / file
            if not file.is_file():
                check.problem(path, f"no such palette file: {file}")
                return None
            return Palette.from_file(file)
        if value not in Palette.names():
            check.problem(path, _unknown(value))
            return None
        return Palette.named(value)
    except ThemeError as exc:
        check.found.extend(exc.problems)
        return None


def _clashes(check: TableCheck, palette: Palette, scope: ThemeScope) -> None:
    """Record a problem at `palette:` for each alias of `palette` the scope already uses."""
    rebound = overridden_aliases(check.theme.table)
    registry = scope.registry
    for alias in palette.pigments:
        taken = scope.aliases.get(alias)
        if taken is not None and alias not in rebound:
            where = f"{taken.path}:{taken.line}"
            check.problem(
                (PALETTE,),
                f"palette alias {alias!r} is also an alias in {where}; "
                f"rebind it in {COLOURS} with override: true",
            )
        elif alias in registry:
            check.problem((PALETTE,), f"palette alias {alias!r} is a pigment name of the theme")


def _from_yaml(path: Path, name: str) -> Palette:
    """The palette the `.yaml` file `path` holds, called `name`.

    Raises:
        ThemeError: When the file has a problem.
    """
    file = read_theme(path, _text(path))
    if file.problems:
        raise ThemeError(file.problems)
    check = TableCheck(file, {})
    for key in file.table:
        if key != COLOURS:
            check.unknown((key,), (COLOURS,))
    scope = check_colours(check, file.table.get(COLOURS, {}), ThemeScope.built_in())
    if check.found:
        raise ThemeError(check.problems())
    return Palette(name=name, pigments={alias: b.value for alias, b in scope.aliases.items()})


def _text(path: Path) -> str:
    """The UTF-8 text of `path`.

    Raises:
        ThemeError: When the file is missing, unreadable or not UTF-8 text.
    """
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ThemeError([_missing(path, f"no such palette file: {path}")]) from exc
    except UnicodeDecodeError as exc:
        raise ThemeError([_missing(path, "not UTF-8 text")]) from exc
    except OSError as exc:
        raise ThemeError([_missing(path, f"cannot be read: {exc.strerror or exc}")]) from exc


def _missing(path: Path, message: str) -> ThemeProblem:
    """A problem of the file `path` as a whole."""
    return ThemeProblem(path=path, key="", line=None, message=message)


def _unknown(name: str) -> str:
    """The message for a packaged palette name that is none."""
    available = ", ".join(Palette.names())
    hint = "".join(f"; did you mean {near}?" for near in nearest(name, Palette.names()))
    return f"no palette named {name!r}{hint}; available: {available}"


def _packaged() -> Traversable:
    """The package's palettes directory."""
    return resources.files("pyntpot.maps") / "palettes"
