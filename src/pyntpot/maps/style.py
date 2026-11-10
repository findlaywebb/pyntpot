"""The map's whole style: every style group, loaded from a YAML theme, and its digests.

Key type: `Style`, a frozen pydantic model holding one value of each style group:
`paper`, `wash` and `brush` (ink), `face`, `nib` and `hand` (letters), `card`,
`ribbon`, `cover`, `route`, `route_ink`, `lettering` and `basemap` (maps).
`Style.from_yaml` reads a theme file, `Style.named` a packaged theme by its name, and
`Style.from_theme` either; `Style.themes` lists the packaged names. A theme names only
what it changes over the theme it extends, and a theme with problems raises one
`ThemeError` holding every problem in it. `Style()` is the default look: every group's
defaults are the default theme, with nothing overridden.

Three digests key what a style change repaints: `base_digest` over the groups the
base plates read, `lettering_digest` over the groups only the lettering reads, and
`digest` over every group, the route ink included. Each group digest is the first
16 hex digits of the SHA-256 of its fields as sorted-key JSON; a combined digest is
the first 16 hex digits of the SHA-256 of its group digests joined in field order.
A field named in `DIGEST_OMITS_AT_DEFAULT` is left out of its group's digest while it
equals its default, or what its default factory builds, so adding such a field moves no
digest of a style that keeps it.

`route_ink` holds the route's ink for `paint` and the compose step, and the basemap group
says what the basemap draws. The style paints, letters and fetches nothing itself. The route ink
is the theme's, unless a caller feeds its colour and width with `with_route_ink`, and a fed
colour also letters the route's markers; the
style knows nothing of what a track records.

Invariants: a theme naming an unknown key, at the top level, inside a group or
inside the route ink, is rejected, and so is such a key given to `Style(...)` directly,
by pydantic itself (`extra="forbid"` here, and its refusal of an unexpected keyword for
each group dataclass); a style never changes once built; changing the route ink's width, drawing
or blend moves `digest` and neither of the other two, and a fed colour moves `digest` and
`lettering_digest`.
"""

import dataclasses
import hashlib
import json
import math
import typing
from collections.abc import Mapping
from pathlib import Path, PurePath
from typing import Self

import pydantic

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.colour import Colour
from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.letters.style import FaceStyle, HandStyle, NibStyle
from pyntpot.maps.style_groups import (
    BasemapStyle,
    CardStyle,
    CoverStyle,
    LetteringStyle,
    RibbonStyle,
    RouteInkStyle,
    RouteStyle,
)
from pyntpot.maps.theme_check import build_group
from pyntpot.maps.theme_errors import ThemeError, ThemeProblem
from pyntpot.maps.theme_resolve import resolve, theme_names

#: The groups whose fields feed the base plates, in field order.
BASE_GROUPS: tuple[str, ...] = (
    "paper",
    "wash",
    "brush",
    "card",
    "ribbon",
    "cover",
    "route",
    "basemap",
)
#: The groups only the lettering reads, in field order.
LETTERING_GROUPS: tuple[str, ...] = ("face", "nib", "hand", "lettering")
_DIGEST_HEX = 16
#: Fields left out of a group digest while they equal their default, or what its default
#: factory builds, so a field added later moves no digest of a style that leaves it alone:
#: the basemap's `name_tags` and `minor_road_classes`, and the cover's `relief_strength` and
#: `min_patch_px`, and the basemap's `line_effects` and the route ink's `effects` (off by
#: default; each name is unique across the groups, because the rule matches by name).
DIGEST_OMITS_AT_DEFAULT: tuple[str, ...] = (
    "name_tags",
    "minor_road_classes",
    "relief_strength",
    "min_patch_px",
    "line_effects",
    "effects",
)


class Style(pydantic.BaseModel, frozen=True, extra="forbid"):
    """Every style group a map is painted, lettered and composed with.

    Attributes:
        paper: The paper, its encoder and the compositing over it.
        wash: How a wash wets, bleeds, rims, blooms, separates and flows.
        brush: The brushes each line class takes and how they behave.
        face: The face the hand opens and how a glyph becomes a pen path.
        nib: The nib, its inks, its angle and the backing wash under a name.
        hand: The seed every label's randomness starts from.
        card: The card's display size, supersampling and dark grid.
        ribbon: The trimmed extent of the painted ground and the card around it.
        cover: Land cover and the wood.
        route: The route's own painted plate.
        route_ink: The route's ink, read only when the route is placed and drawn.
        lettering: Which names a map letters, and how many.
        basemap: What the basemap draws, and how much of it.
    """

    paper: PaperStyle = pydantic.Field(default_factory=PaperStyle)
    wash: WashStyle = pydantic.Field(default_factory=WashStyle)
    brush: BrushStyle = pydantic.Field(default_factory=BrushStyle)
    face: FaceStyle = pydantic.Field(default_factory=FaceStyle)
    nib: NibStyle = pydantic.Field(default_factory=NibStyle)
    hand: HandStyle = pydantic.Field(default_factory=HandStyle)
    card: CardStyle = pydantic.Field(default_factory=CardStyle)
    ribbon: RibbonStyle = pydantic.Field(default_factory=RibbonStyle)
    cover: CoverStyle = pydantic.Field(default_factory=CoverStyle)
    route: RouteStyle = pydantic.Field(default_factory=RouteStyle)
    route_ink: RouteInkStyle = pydantic.Field(default_factory=RouteInkStyle)
    lettering: LetteringStyle = pydantic.Field(default_factory=LetteringStyle)
    basemap: BasemapStyle = pydantic.Field(default_factory=BasemapStyle)

    @classmethod
    def from_yaml(cls, path: Path) -> Self:
        """Read a YAML theme: the theme it extends, with what it names laid over it.

        Args:
            path: A `.yaml` theme file, relative to the working directory unless absolute.

        Returns:
            The style the theme describes.

        Raises:
            ThemeError: When the file or any theme it extends has a problem; every
                problem is in its problems.
        """
        return cls.from_theme(Path(path))

    @classmethod
    def from_theme(cls, theme: str | Path, *, relative_to: Path | None = None) -> Self:
        """A style from a theme given by its name or by its .yaml file.

        Args:
            theme: A packaged theme's name, such as `sepia`, or a `.yaml` theme file as a
                `str` or a `Path`.
            relative_to: The directory a relative path is read from; the current
                directory when `None`.

        Returns:
            The style the theme describes.

        Raises:
            ThemeError: When the theme is neither a packaged name nor a `.yaml` file, or
                it or any theme it extends has a problem; every problem is in its problems.
        """
        table = resolve(
            theme, relative_to=relative_to or Path.cwd(), groups=_groups(), base=_base()
        )
        return cls._build(table)

    @classmethod
    def named(cls, name: str) -> Self:
        """A style from the packaged theme with this name.

        Args:
            name: A packaged theme's name, one of `Style.themes()`.

        Returns:
            The style the packaged theme describes.

        Raises:
            ThemeError: When `name` has a file suffix, is not a theme name, or names no
                packaged theme.
        """
        if PurePath(name).suffix:
            problem = ThemeProblem(
                path=Path(name),
                key="",
                line=None,
                message="Style.named takes a name; use Style.from_yaml for a file",
            )
            raise ThemeError((problem,))
        return cls.from_theme(name)

    @classmethod
    def themes(cls) -> tuple[str, ...]:
        """The names of the packaged themes, `default` among them, sorted.

        Returns:
            Every name `Style.named` takes.
        """
        return theme_names()

    @classmethod
    def _build(cls, table: Mapping[str, object]) -> Self:
        """Build the style from a full, checked table, each group by `build_group`."""
        groups = _groups()
        return cls(
            **{name: build_group(group, _table(table[name])) for name, group in groups.items()}
        )

    @classmethod
    def default(cls) -> Self:
        """The default look: every group at its model defaults, nothing overridden."""
        return cls()

    def digest(self) -> str:
        """A short hash of every group, so any style change is seen."""
        return _combined(self, tuple(type(self).model_fields))

    def base_digest(self) -> str:
        """A short hash of the groups the base plates read, so only their change repaints."""
        return _combined(self, BASE_GROUPS)

    def lettering_digest(self) -> str:
        """A short hash of the groups only the lettering reads."""
        return _combined(self, LETTERING_GROUPS)

    def with_route_ink(self, *, colour: str | None = None, width_px: float | None = None) -> Self:
        """A copy of the style whose route is inked in this colour and spaced for this width.

        Only the colour and the width are fed: the route's `drawn_as`, blend and
        opacity stay the theme's. A fed colour is also the ink of the "start" and
        "finish" markers: it replaces `nib.label_route_ink`, a shade a theme gave
        them. The compose step draws the route line at the fed
        width, except when `drawn_as` is `"pen"` and a pen plate was painted: then
        it tints that plate, whose stroke width is the `route` group's
        `route_pen_width_px`, so the fed width changes nothing drawn. Otherwise the
        fed width also sets how far apart `paint` draws the strands of a
        doubled-back route; the pen plate always separates by its own width.

        A fed colour moves `digest()` and `lettering_digest()`, so the nib plate is
        stroked again (about 4.5 s), and never `base_digest()`, so no base plate is
        repainted. A fed width alone moves `digest()` only.

        Args:
            colour: The route's colour as `#rrggbb`, or `None` to keep the theme's.
                It is stored in lower case, so colours that differ only in case give
                equal styles and equal digests.
            width_px: The route's width in display pixels, or `None` to keep the
                theme's. It is stored as a float, so `5` and `5.0` give equal styles
                and equal digests.

        Returns:
            A copy whose `route_ink` has the fed colour and width; with neither
            fed, a copy equal to this style.

        Raises:
            ValueError: When `colour` is not a `#` and six hexadecimal digits, or
                `width_px` is a bool, or is not a finite number above zero.
        """
        try:
            fed_colour = None if colour is None else Colour.parse(colour)
        except ValueError as exc:
            raise ValueError(
                f"route colour {colour!r} is not a # and six hexadecimal digits"
            ) from exc
        if width_px is not None and (
            isinstance(width_px, bool) or not math.isfinite(width_px) or width_px <= 0
        ):
            raise ValueError(f"route width {width_px!r} px is not a finite number above zero")
        ink = self.route_ink
        fed = dataclasses.replace(
            ink,
            colour=ink.colour if fed_colour is None else fed_colour,
            px=ink.px if width_px is None else float(width_px),
        )
        update: dict[str, object] = {"route_ink": fed}
        if fed_colour is not None:
            update["nib"] = dataclasses.replace(self.nib, label_route_ink=fed_colour)
        return self.model_copy(update=update)


def _groups() -> dict[str, type]:
    """Each style group's dataclass, by its key in a theme."""
    return {
        name: info.annotation
        for name, info in Style.model_fields.items()
        if isinstance(info.annotation, type)
    }


def _base() -> dict[str, object]:
    """The default table: each group's defaults as plain data, by its key in a theme."""
    return {name: dataclasses.asdict(getattr(Style(), name)) for name in Style.model_fields}


def _table(value: object) -> Mapping[str, object]:
    """`value`, a group's entry in a resolved table, as the mapping it always is.

    Raises:
        TypeError: When `value` is not a mapping, a programming error.
    """
    if not isinstance(value, Mapping):
        raise TypeError(f"{value!r} is not a group table")
    return {str(key): item for key, item in value.items()}


def _digest_fields(group: object) -> dict[str, typing.Any]:
    """`group`'s fields as plain data, less each digest-rule field equal to its default.

    A field's default is its `default`, or, when it has a default factory, what the
    factory builds.

    Raises:
        TypeError: When `group` is not a dataclass instance, a programming error.
    """
    if not dataclasses.is_dataclass(group) or isinstance(group, type):
        raise TypeError(f"{group!r} is not a style group")
    fields = dataclasses.asdict(group)
    for spec in dataclasses.fields(group):
        if spec.name not in DIGEST_OMITS_AT_DEFAULT:
            continue
        default = spec.default
        if default is dataclasses.MISSING and spec.default_factory is not dataclasses.MISSING:
            default = spec.default_factory()
        if getattr(group, spec.name) == default:
            del fields[spec.name]
    return fields


def _group_digest(style: Style, name: str) -> str:
    """Hash one named group's fields as sorted-key JSON."""
    blob = json.dumps(_digest_fields(getattr(style, name)), sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:_DIGEST_HEX]


def _combined(style: Style, names: tuple[str, ...]) -> str:
    """Hash the named groups' digests, joined in the order given."""
    joined = "".join(_group_digest(style, name) for name in names)
    return hashlib.sha256(joined.encode()).hexdigest()[:_DIGEST_HEX]
