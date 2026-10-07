"""What the hand is asked to write, and the marks it writes.

Key types: `Setting`, one request to the hand: a text at a size, set either
along a line or beside an anchor, with its slant, tracking, ink and whether the
backing wash is lifted under it; `Mark`, one stroke for the nib to run along, in
card pixels. `DEFAULT_LINE_PX` is the type size a mark belongs to when nothing
says otherwise.

It writes nothing and chooses nothing. A setting is the outcome of placement,
not an input to it: which line a name follows, which way along it the name
reads, how far it is lifted off the feature, which ink a class of feature takes
and how far it leans are all decided by whoever builds the setting. The random
draws that make one instance differ from the next are not part of a setting;
they come from the generator the writer is handed alongside it.

Invariants: a setting is frozen and hashable, and exactly one of `anchor` and
`path` is given; a setting along a path writes one line, starting at the path's
first point, so it carries no `lines` and no `align` but `start`. The module
imports nothing from `pyntpot` but `ink`.
"""

from dataclasses import dataclass
from typing import Literal

from pyntpot.ink.polyline import Pt

#: The type size of a line of lettering, in display pixels, when nothing else
#: says what it is.
DEFAULT_LINE_PX = 20.0

#: Which edge of a flat block sits on its anchor: its left end, its middle, or
#: its right end.
Align = Literal["start", "middle", "end"]

#: The fewest points a path can be written along: a line needs two ends.
_PATH_ENDS = 2


@dataclass(frozen=True)
class Setting:
    """One text for the hand to write, and how it is set.

    A setting with a `path` is written along it, each glyph on its own tangent,
    from the path's first point; the path is the line the letters sit on, so a
    caller that wants the name lifted off a feature or read the other way passes
    the lifted, reoriented line. A setting with an `anchor` is written flat
    from it, one row per entry of `lines` (or the `text` alone), each row
    aligned on the widest by `align`.

    Args:
        text: What is written; the whole name, even when `lines` wraps it.
        size: The type size, in card pixels.
        anchor: Where a flat block is set from: its baseline and its `align` edge.
        path: The line a name is written along, at least two points.
        align: Which edge of a flat block sits on `anchor`.
        slant: How far the letters lean, as a shear of x by y.
        tracking: Extra letter spacing, in em units.
        ink: The ink token or colour the marks are written in.
        lines: The rows of a wrapped flat block; empty writes `text` as one row.
        wash: Whether the backing wash is lifted under the marks.

    Raises:
        ValueError: When both or neither of `anchor` and `path` is given, when a
            path has fewer than two points, or when a setting along a path
            carries `lines` or an `align` other than `start`.
    """

    text: str
    size: float
    anchor: Pt | None = None
    path: tuple[Pt, ...] | None = None
    align: Align = "start"
    slant: float = 0.0
    tracking: float = 0.0
    ink: str = "map"
    lines: tuple[str, ...] = ()
    wash: bool = True

    def __post_init__(self) -> None:
        """Refuse a setting that does not say plainly how it is set."""
        if (self.anchor is None) == (self.path is None):
            msg = "a setting is set from an anchor or along a path, exactly one"
            raise ValueError(msg)
        if self.path is None:
            return
        if len(self.path) < _PATH_ENDS:
            msg = "a path to write along needs at least two points"
            raise ValueError(msg)
        if self.lines or self.align != "start":
            msg = "a setting along a path writes one line from the path's start"
            raise ValueError(msg)


@dataclass
class Mark:
    """One stroke for the nib to run along, in card pixels.

    `role` sets the weight and whether the pen's angle modulates it, `ink`
    its ink token or a `#rrggbb` colour, `size` the type size it belongs to, and
    `pen` the per-instance wobble on the nib's angle, so no two words are
    written with the hand held at exactly the same tilt.
    """

    pts: list[Pt]
    role: str = "glyph"
    ink: str = "map"
    size: float = DEFAULT_LINE_PX
    pen: float = 0.0
    #: Whether the backing wash is lifted under this mark. A name written on
    #: its own water does not want one: the wash is there to make a name
    #: readable on ground it was not meant to be on, and a pale blob on a river
    #: reads as a hole in the water rather than as paint lifted off the paper.
    wash: bool = True
