"""The names a theme file can write: its pigments, its palette, its aliases and its presets.

Key types: `Bound`, one entry with the file and line that wrote it; `ThemeScope`, the frozen
vocabulary a file is checked in; `resolve_pigment` and `resolve_colour`, which turn a hex, an
alias or a pigment name into the `Pigment` or `Colour` it stands for.

A name resolves to a hex at load, so a colour field still holds `#rrggbb` and no digest moves.
An alias holds the `Pigment` it stands for, so its transparency travels with it; an alias to a
hex holds the anonymous `pigment("#...")`. The one palette in effect keeps its aliases apart
from the theme's own, so a file's `palette:` can take the inherited palette's aliases out while
theme aliases stay.

Does not read files, bind names or check a theme: the modules that check `pigments`, `palette`
and `colours` fill a scope, and a scope only answers lookups. The scope built in has no theme
pigments, no palette, no aliases and no presets.

Invariants: a scope is frozen; every entry names the file and line that wrote it; a lookup tries
a theme alias, then a palette alias, then a registry name, in that order.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING

from pyntpot.ink.colour import Colour
from pyntpot.ink.naming import did_you_mean
from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY, PigmentRegistry, pigment
from pyntpot.ink.pigment_table import Pigment
from pyntpot.maps.line_effects import EffectStack

if TYPE_CHECKING:
    from pyntpot.maps.theme_palette import Palette


@dataclass(frozen=True)
class Bound[T]:
    """One entry of a scope: its value and where it was written.

    Attributes:
        value: The entry.
        path: The theme file that wrote it.
        line: The 1-based line of its key in that file.
    """

    value: T
    path: Path
    line: int


@dataclass(frozen=True)
class ThemeScope:
    """The names in force while one theme file is checked.

    Attributes:
        pigments: Theme pigments by name.
        palette: The one palette in effect, or `None`; its aliases are read from its
            `pigments` attribute.
        aliases: Theme aliases by name, each the `Pigment` it stands for.
        presets: Theme effect presets by name.
    """

    pigments: Mapping[str, Bound[Pigment]] = field(default_factory=dict)
    palette: "Bound[Palette] | None" = None
    aliases: Mapping[str, Bound[Pigment]] = field(default_factory=dict)
    presets: Mapping[str, Bound[EffectStack]] = field(default_factory=dict)

    @classmethod
    def built_in(cls) -> "ThemeScope":
        """The empty scope: no theme pigments, no palette, no aliases, no presets."""
        return cls()

    @cached_property
    def registry(self) -> PigmentRegistry:
        """The built-in pigments followed by this scope's theme pigments."""
        return PIGMENT_REGISTRY.extended(tuple(b.value for b in self.pigments.values()))

    @property
    def palette_aliases(self) -> Mapping[str, Pigment]:
        """The palette in effect's aliases, each the `Pigment` it stands for."""
        if self.palette is None:
            return dict[str, Pigment]()
        return self.palette.value.pigments


def resolve_pigment(text: str, scope: ThemeScope) -> Pigment:
    """The pigment `text` names in `scope`: a hex, a theme alias, a palette alias or a name.

    Args:
        text: A `#rrggbb` in either case, an alias or a pigment name.
        scope: The names in force.

    Returns:
        The anonymous pigment for a hex, or the bound pigment.

    Raises:
        ValueError: When `text` is a bad hex, or names no pigment or alias; the miss
            names the nearest known name when one is close.
    """
    if text.startswith("#"):
        return pigment(text)
    if text in scope.aliases:
        return scope.aliases[text].value
    palette = scope.palette_aliases
    if text in palette:
        return palette[text]
    if text in scope.registry:
        return scope.registry.get(text)
    known = (*scope.aliases, *palette, *scope.registry.names())
    raise ValueError(f"{text!r} is not a pigment or a colour alias{did_you_mean(text, known)}")


def resolve_colour(text: str, scope: ThemeScope) -> Colour:
    """The colour `text` names in `scope`; see `resolve_pigment`."""
    return resolve_pigment(text, scope).colour
