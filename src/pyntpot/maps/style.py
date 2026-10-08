"""The map's whole style: every style group, loaded from a TOML theme, and its digests.

Key type: `Style`, a frozen pydantic model holding one value of each style group:
`paper`, `wash` and `brush` (ink), `face`, `nib` and `hand` (letters), `card`,
`ribbon`, `cover`, `route`, `route_inks`, `lettering` and `basemap` (maps).
`Style.from_toml` reads a theme file; `Style.default` reads the packaged default
theme, which is the resolved default style the reference sheets were painted with,
not the groups' dataclass defaults.

Three digests key what a style change repaints: `base_digest` over the groups the
base plates read, `lettering_digest` over the groups only the lettering reads, and
`digest` over every group, the route inks included. Each group digest is the first
16 hex digits of the SHA-256 of its fields as sorted-key JSON; a combined digest is
the first 16 hex digits of the SHA-256 of its group digests joined in field order.

`route_ink` hands `paint` and the compose step the route's ink, and the basemap group says what
the basemap draws. The style paints, letters and fetches nothing itself. The route ink
is always the ride ink; there is no sport selection.

Invariants: a theme naming an unknown key, at the top level, inside a group or
inside a route ink, is rejected; a style never changes once built; changing a route
ink moves `digest` and neither of the other two.
"""

import dataclasses
import hashlib
import json
import tomllib
import typing
from importlib import resources
from pathlib import Path
from typing import Self

import pydantic

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.letters.style import FaceStyle, HandStyle, NibStyle
from pyntpot.maps.style_groups import (
    BasemapStyle,
    CardStyle,
    CoverStyle,
    LetteringPolicy,
    RibbonStyle,
    RouteInk,
    RouteInks,
    RouteStyle,
)

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
        route_inks: One resolved route ink per sport, read only when the route
            is placed and drawn.
        lettering: Which names a map letters, and how many.
        basemap: What the basemap draws, and how much of it.
    """

    paper: PaperStyle
    wash: WashStyle
    brush: BrushStyle
    face: FaceStyle
    nib: NibStyle
    hand: HandStyle
    card: CardStyle
    ribbon: RibbonStyle
    cover: CoverStyle
    route: RouteStyle
    route_inks: RouteInks
    lettering: LetteringPolicy
    basemap: BasemapStyle

    @pydantic.model_validator(mode="before")
    @classmethod
    def _reject_unknown_group_keys(cls, data: object) -> object:
        """Reject a group table naming a key its dataclass does not have."""
        if isinstance(data, dict):
            for name, value in data.items():
                info = cls.model_fields.get(name)
                if info is not None and isinstance(info.annotation, type):
                    _check_keys(info.annotation, value, name)
        return data

    @classmethod
    def from_toml(cls, path: Path) -> Self:
        """Read a theme file: one table per style group.

        Args:
            path: A TOML theme with a table for every group.

        Returns:
            The style the theme describes.

        Raises:
            tomllib.TOMLDecodeError: When the file is not TOML.
            pydantic.ValidationError: When a group is missing, a key is unknown at
                any level, or a value has the wrong type.
        """
        with path.open("rb") as handle:
            table = tomllib.load(handle)
        return cls.model_validate(table)

    @classmethod
    def default(cls) -> Self:
        """Read the packaged default theme: the resolved default style."""
        theme = resources.files("pyntpot.maps") / "themes" / "default.toml"
        with resources.as_file(theme) as path:
            return cls.from_toml(path)

    def digest(self) -> str:
        """A short hash of every group, so any style change is seen."""
        return _combined(self, tuple(type(self).model_fields))

    def base_digest(self) -> str:
        """A short hash of the groups the base plates read, so only their change repaints."""
        return _combined(self, BASE_GROUPS)

    def lettering_digest(self) -> str:
        """A short hash of the groups only the lettering reads."""
        return _combined(self, LETTERING_GROUPS)

    def route_ink(self) -> RouteInk:
        """The route's ink: always the ride ink, as there is no sport selection."""
        return self.route_inks.ride


def _check_keys(group: type, value: object, where: str) -> None:
    """Raise when a table names a key `group` lacks, recursing into nested groups."""
    if not dataclasses.is_dataclass(group) or not isinstance(value, dict):
        return
    hints = typing.get_type_hints(group)
    known = {spec.name for spec in dataclasses.fields(group)}
    unknown = sorted(set(value) - known)
    if unknown:
        raise ValueError(f"[{where}] has unknown keys {unknown}")
    for name, inner in value.items():
        hint = hints.get(name)
        if isinstance(hint, type):
            _check_keys(hint, inner, f"{where}.{name}")


def _group_digest(style: Style, name: str) -> str:
    """Hash one named group's fields as sorted-key JSON."""
    blob = json.dumps(dataclasses.asdict(getattr(style, name)), sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:_DIGEST_HEX]


def _combined(style: Style, names: tuple[str, ...]) -> str:
    """Hash the named groups' digests, joined in the order given."""
    joined = "".join(_group_digest(style, name) for name in names)
    return hashlib.sha256(joined.encode()).hexdigest()[:_DIGEST_HEX]
