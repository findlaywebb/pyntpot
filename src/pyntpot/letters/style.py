"""The hand: the face, the nib and the seed hand lettering is written with.

Key types: `FaceStyle`, which face the hand opens and how a glyph becomes a
pen path; `HandStyle`, the seed every random draw of a label starts from;
`NibStyle`, the nib, its inks, its angle and the backing wash under a name;
`NibGroups`, the groups the nib reads together.
Frozen dataclasses of plain values, each field documented by its `#:` comment.

It letters nothing and reads no theme. The defaults are the painter's own
class defaults, not a resolved theme. Which names a map letters, and how many,
is map policy and lives with the maps.

Invariants: every field belongs to exactly one style group across the
package; the module imports nothing from `pyntpot` but `ink`, for the brush and
paper groups `NibGroups` carries.
"""

from dataclasses import dataclass

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.style import PaperStyle


@dataclass(frozen=True)
class FaceStyle:
    """The face the hand is opened with, and how a glyph is turned into a pen path."""

    #: How a glyph is turned into something the pen follows. `centreline` thins
    #: the face's own outline to a written skeleton; `outline` draws round the
    #: contour itself. They are two different letters, not a choice and a
    #: fallback, and the second is what the first falls back to.
    label_route: str = "centreline"
    #: The face, under `analysis/report/fonts/`. Empty is the vendored one.
    label_face: str = ""


@dataclass(frozen=True)
class HandStyle:
    """The seed the hand draws every label's randomness from."""

    #: Every random draw a label makes comes from this plus the label's own
    #: name, so an unchanged map letters identically on every render and a
    #: deliberate reshuffle is one number.
    label_seed: int = 17


@dataclass(frozen=True)
class NibStyle:
    """The nib: size, inks, widths, angle, and the backing wash laid under a name."""

    #: The size the hand is written at, in display pixels.
    label_size_px: float = 20.0
    #: The ink the lettering is written in.
    label_ink: str = "#241c14"
    #: The nib the lettering is written with, and its width in display pixels.
    #: A nib, not a brush: a letter at fourteen pixels breaks up if the mark can
    #: break, and a broken letter is a wrong letter rather than a textured one.
    label_brush: str = "MAJ6-e"
    label_pen_width_px: float = 1.05
    #: The outline route draws two strokes where the centreline draws one, a
    #: stroke's width apart, so the same nib fills the counters and the letter
    #: comes out a bolder thing than the face is. It writes with a finer one.
    label_outline_width_frac: float = 0.62
    #: The leader and the span line, one step lighter, so the line recedes
    #: behind the name it points at.
    label_leader_brush: str = "MAJ6-e"
    label_leader_width_px: float = 0.85
    #: The pen's angle, anticlockwise from the writing line, and how much of the
    #: width it takes off a stroke drawn along it. Without this the letters come
    #: out one thickness the whole way round, which is a plotter and not a pen.
    label_pen_angle_deg: float = -38.0
    label_pen_thin: float = 0.52
    #: The backing wash: paper-coloured, laid through the wash machinery, and
    #: absent where the ground is already pale enough to read on.
    label_wash: bool = True
    label_wash_alpha: float = 0.5
    label_wash_dark_floor: float = 0.22
    label_wash_spread: float = 0.75
    #: The ink a name in the route's own colour is written in. The caller fills
    #: it from the sport's route ink; the default is what the route was.
    label_route_ink: str = "#c22050"
    label_water_ink: str = "#4a7691"
    #: The ink a name written *on* the water is set in. Reversed out of the
    #: river in the paper's own cream rather than written into it in a dark ink:
    #: the water is a mid-tone, so a dark ink is fighting it from the wrong side.
    #: Measured on a painted river, black holds 3.9:1 and this holds 4.7:1,
    #: and the difference on the sheet is larger than the ratio suggests because
    #: the letters no longer share a value with the bridges crossing them.
    label_in_water_ink: str = "#f8f4e9"


@dataclass(frozen=True)
class NibGroups:
    """The style groups the nib reads, passed as one value."""

    nib: NibStyle
    face: FaceStyle
    hand: HandStyle
    brush: BrushStyle
    paper: PaperStyle
