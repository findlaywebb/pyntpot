"""Planted style groups for the loader's and the schema's tests: a group with a dataclass-typed field, which no real group has yet."""

from dataclasses import dataclass, field


@dataclass(frozen=True, kw_only=True)
class Glow:
    """A planted sub-table for the loader's tests, and no style group.

    Attributes:
        colour: The glow's colour.
        px: The glow's width in display pixels.
    """

    colour: str = "#ffffff"
    px: float = 2.0


@dataclass(frozen=True, kw_only=True)
class Ink:
    """A planted group holding a sub-table, for the loader's tests, and no style group.

    Attributes:
        glow: The planted sub-table.
        px: The ink's width in display pixels.
    """

    glow: Glow = field(default_factory=Glow)
    px: float = 5.4
