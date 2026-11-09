"""The shipped pigments as frozen entries, and the four tables projected from them.

Key types: `Pigment`, one pigment with its colour, transparency and Colour Index code;
`ROLE_PIGMENTS`, the fifteen a map names by role, and `TUBE_PIGMENTS`, the ten a painter names by
tube, each in the order the registry holds them. `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS`
and `PAINTERS_TRANSPARENCY` are the exported tables, built from those two tuples;
`role_transparencies` is a fresh copy of the role transparencies, for a style default.

It looks nothing up and reads no style; `pigment_registry.py` holds the lookup.

Invariants: every hex in `ink` that names a shipped pigment is written here and nowhere else; a
name appears once across the two tuples; the tables keep the order of the tuples.
"""

from dataclasses import dataclass

from pyntpot.ink.colour import Colour


@dataclass(frozen=True, kw_only=True)
class Pigment:
    """One pigment: a name, the colour a full-strength wash transmits, and how it glazes.

    Attributes:
        name: The canonical name, or the lower-case hex for an anonymous pigment.
        colour: What a full-strength wash of the pigment transmits.
        transparency: What the pigment shows over black as a share of what it shows over white,
            near 0 for a transparent glaze and near 1 for a covering body colour. `None` means
            take `PaperStyle.km_transparency`.
        colour_index: The Colour Index generic code (`PB29` for ultramarine), metadata only, or
            `None` when the pigment has none. It is never a lookup key.
    """

    name: str
    colour: Colour
    transparency: float | None
    colour_index: str | None


def _entry(name: str, hex_s: str, transparency: float, colour_index: str | None = None) -> Pigment:
    return Pigment(
        name=name,
        colour=Colour(hex_s),
        transparency=transparency,
        colour_index=colour_index,
    )


ROLE_PIGMENTS: tuple[Pigment, ...] = (
    _entry("farmland", "#dfe0b0", 0.10),
    _entry("meadow", "#cfdfae", 0.09),
    _entry("orchard", "#d5dda2", 0.09),
    _entry("scrub", "#c9d5a4", 0.08),
    _entry("heath", "#e0cda2", 0.14),
    _entry("sand", "#ecdfbe", 0.16),
    _entry("rock", "#dcd6c6", 0.22),
    _entry("wetland", "#bfd2cd", 0.08),
    _entry("built", "#ddd3c3", 0.26),
    _entry("works", "#d2cbc0", 0.28),
    _entry("wood", "#a8c286", 0.05),
    _entry("pale", "#d5e0b4", 0.12),
    _entry("water", "#9ec4de", 0.04),
    _entry("relief", "#c9bda4", 0.30),
    _entry("rim", "#c2ad91", 0.18),
)
"""The map's pigments, named by role. Their colours are multiply colours: what a full-strength wash
of each transmits. The inks are darker than the washes, because a mark is not a wash. Their
transparency is what each shows over black as a share of over white; the wood green and the water
blue stain, and the relief grey and the built greys sit on the surface."""

TUBE_PIGMENTS: tuple[Pigment, ...] = (
    _entry("ultramarine", "#2b3d8f", 0.06, "PB29"),
    _entry("cerulean", "#2a7ab0", 0.22, "PB35"),
    _entry("burnt_sienna", "#8a3b1c", 0.20, "PBr7"),
    _entry("raw_sienna", "#b8692a", 0.18, "PBr7"),
    _entry("yellow_ochre", "#c99a3a", 0.24, "PY43"),
    _entry("sap_green", "#3f6b2a", 0.07),
    _entry("indigo", "#2c3346", 0.05),
    _entry("perylene_maroon", "#5a1f27", 0.04, "PR179"),
    _entry("quinacridone_rose", "#b8215e", 0.05, "PV19"),
    _entry("paynes_grey", "#3b4452", 0.10),
)
"""A painter's pigments, named by the tube a painter buys rather than by map role. Ultramarine,
cerulean and the sienna earths sit nearer a covering body; the quinacridone, the maroon and the
indigo stain."""


def _colours(pigments: tuple[Pigment, ...]) -> dict[str, Colour]:
    return {p.name: p.colour for p in pigments}


def _transparencies(pigments: tuple[Pigment, ...]) -> dict[str, float]:
    return {p.name: p.transparency for p in pigments if p.transparency is not None}


def role_transparencies() -> dict[str, float]:
    """A fresh dict of each map-role pigment's transparency, in registry order.

    Returns:
        Role name to transparency, the default of `PaperStyle.pigment_transparency`.
    """
    return _transparencies(ROLE_PIGMENTS)


PIGMENTS: dict[str, Colour] = _colours(ROLE_PIGMENTS)
"""Multiply colours: what a full-strength wash of each map-role pigment transmits."""

TRANSPARENCY: dict[str, float] = role_transparencies()
"""What each map-role pigment shows over black, as a share of what it shows over white. This is the
one number Kubelka-Munk glazing needs beyond the hex, and it is where a pigment is recorded as
staining or covering: near 0 is a transparent glaze that lets the layer under it through, near 1
is a covering body colour. Anything not named here takes `km_transparency`."""

PAINTERS_PIGMENTS: dict[str, Colour] = _colours(TUBE_PIGMENTS)
"""Painter's pigments: the same meaning as `PIGMENTS`, keyed by the tube a painter names rather than
by map role. No map style reads this table; it is for whoever paints with the engine directly."""

PAINTERS_TRANSPARENCY: dict[str, float] = _transparencies(TUBE_PIGMENTS)
"""What each painter's pigment shows over black, as a share of what it shows over white, the same
meaning as `TRANSPARENCY`."""
