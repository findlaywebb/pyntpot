"""The value types of the line effects: what a casing, glow, shadow or pen casing is made of.

Key types: `Casing`, `Glow`, `Shadow`, `PenCasing` and `Reserve`, each a frozen, keyword-only dataclass
that is off at its default, and `EFFECT_RANGES`, the one table of the numbers' bounds, keyed by
field name. Each effect primitive in `effect_casing`, `effect_glow`, `effect_shadow`,
`effect_pen_casing` and `effect_reserve` takes its value type whole.

A `*_px` field is in pixels of the array the effect is laid on, and the types know nothing of
maps: no line class, no stack, no azimuth. They draw nothing and read no file.

Invariants: every number is finite; a `*_px` is not below 0; a `strength` and a `pool` are from 0 to 1. A type
does not refuse a `*_px` above 16, because its pixels are those of the array it is laid on and a
caller scales a theme's display pixels by the render scale; the 16 display-pixel bound is checked
where a theme is loaded. `Casing` and `Shadow` hold a `Colour`, and a plain `str` given for it is
normalised.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from pyntpot.ink.colour import Colour, normalise_colours
from pyntpot.ink.pigment_registry import pigment

_PX = (0.0, 16.0)
_UNIT = (0.0, 1.0)
_WHITE = Colour("#ffffff")

EFFECT_RANGES: Mapping[str, tuple[float, float]] = MappingProxyType(
    {
        "width_px": _PX,
        "edge_px": _PX,
        "spread_px": _PX,
        "blur_px": _PX,
        "offset_px": _PX,
        "strength": _UNIT,
        "pool": _UNIT,
    }
)


def check_effect_numbers(effect: object, *names: str) -> None:
    """Refuse a non-finite, a negative `*_px` or an out-of-range `strength` or `pool`.

    Args:
        effect: A dataclass instance holding the named numeric fields.
        *names: The fields to check, each a key of `EFFECT_RANGES`.

    Raises:
        ValueError: Naming the field and its range, when a value is not finite, a `*_px` is
            below 0, or a `strength` or `pool` is outside 0 to 1. A `*_px` above 16 is
            accepted.
    """
    for name in names:
        value = getattr(effect, name)
        lo, hi = EFFECT_RANGES[name]
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite, in {lo} to {hi}; got {value!r}")
        if value < lo or (not name.endswith("_px") and value > hi):
            raise ValueError(f"{name} must be in {lo} to {hi}; got {value!r}")


@dataclass(frozen=True, kw_only=True)
class Casing:
    """A ring of colour round a line, laid over the paper beneath it.

    Off at a width of 0 or a strength of 0.

    Attributes:
        width_px: The ring's width beyond the line's footprint, in pixels of the array it is laid
            on.
        colour: The ring's colour, laid over the paper, so white is the paper.
        strength: How far the ring blends toward its colour, 0 to 1.
    """

    width_px: float = 0.0
    colour: Colour = _WHITE
    strength: float = 1.0

    def __post_init__(self) -> None:
        """Normalise the colour and refuse an out-of-range number.

        Raises:
            ValueError: When a number is not finite, `width_px` is negative, `strength` is
                outside 0 to 1, or the colour is not a `#` and six hexadecimal digits.
        """
        normalise_colours(self, "colour")
        check_effect_numbers(self, "width_px", "strength")


@dataclass(frozen=True, kw_only=True)
class Glow:
    """A lift of the colour beneath a line toward the paper, with a hard spread and a soft fall.

    It has no colour of its own and never darkens. Off at a strength of 0.

    Attributes:
        spread_px: How far the hard core reaches beyond the line, in pixels of the array.
        blur_px: The softness of the falloff beyond the core, in pixels of the array.
        strength: How far the colour lifts toward the paper, 0 to 1.
    """

    spread_px: float = 0.0
    blur_px: float = 0.0
    strength: float = 0.0

    def __post_init__(self) -> None:
        """Refuse an out-of-range number.

        Raises:
            ValueError: When a number is not finite, a `*_px` is negative, or `strength` is
                outside 0 to 1.
        """
        check_effect_numbers(self, "spread_px", "blur_px", "strength")


@dataclass(frozen=True, kw_only=True)
class Shadow:
    """The line's mask offset away from the light, blurred and laid as a multiplying darken.

    Off at a strength of 0. The light's direction is not a field: it is the scene's.

    Attributes:
        offset_px: How far the shadow falls, in pixels of the array; rounded to whole pixels on
            each axis when laid.
        blur_px: The softness of the shadow's edge, in pixels of the array.
        strength: How dark the shadow lies, 0 to 1.
        colour: The colour the shadow multiplies toward; Payne's grey by default.
    """

    offset_px: float = 0.0
    blur_px: float = 0.0
    strength: float = 0.0
    colour: Colour = field(default_factory=lambda: pigment("paynes_grey").colour)

    def __post_init__(self) -> None:
        """Normalise the colour and refuse an out-of-range number.

        Raises:
            ValueError: When a number is not finite, a `*_px` is negative, `strength` is
                outside 0 to 1, or the colour is not a `#` and six hexadecimal digits.
        """
        normalise_colours(self, "colour")
        check_effect_numbers(self, "offset_px", "blur_px", "strength")


@dataclass(frozen=True, kw_only=True)
class PenCasing:
    """A reserve round a pen line: the paper left bare between two ink edge lines.

    Off at a width of 0.

    Attributes:
        width_px: The reserve's width beyond the line's footprint, in pixels of the array.
        edge_px: The width of each of the two edge lines, in pixels of the array.
    """

    width_px: float = 0.0
    edge_px: float = 0.0

    def __post_init__(self) -> None:
        """Refuse an out-of-range number.

        Raises:
            ValueError: When a number is not finite or is negative.
        """
        check_effect_numbers(self, "width_px", "edge_px")


@dataclass(frozen=True, kw_only=True)
class Reserve:
    """The paper laid back in a ring round a line, every pigment beneath it lifted.

    Off at a width of 0.

    Attributes:
        width_px: The ring's width beyond the line's footprint, in pixels of the array it is
            laid on.
        pool: How far the pigment gathers into a faint line just outside the ring, 0 to 1; 0
            leaves no pool.
    """

    width_px: float = 0.0
    pool: float = 0.0

    def __post_init__(self) -> None:
        """Refuse an out-of-range number.

        Raises:
            ValueError: When a number is not finite, `width_px` is negative, or `pool` is
                outside 0 to 1.
        """
        check_effect_numbers(self, "width_px", "pool")
