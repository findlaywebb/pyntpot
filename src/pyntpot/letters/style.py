"""The hand: the face, the nib and the seed hand lettering is written with.

Key types: `FaceStyle`, which face the hand opens and how a glyph becomes a
pen path; `HandStyle`, the seed every random draw of a label starts from;
`NibStyle`, the nib, its inks, its angle and the backing wash under a name;
`NibGroups`, the groups the nib reads together. The first three are frozen,
keyword-only dataclasses of plain values, their fields documented in each
class's `Attributes:` section; `NibGroups` is built positionally. `label_route` is a
`Literal` of its two words.

It letters nothing. The defaults are the default look a map is painted with; the
module reads no theme. Which names are lettered, and how many, is the caller's
policy; the `maps` package keeps it.

Invariants: every field belongs to exactly one style group across the
package; the module imports nothing from `pyntpot` but `ink`, for the brush and
paper groups `NibGroups` carries.
"""

from dataclasses import dataclass
from typing import Literal

from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.colour import Colour, normalise_colours
from pyntpot.ink.style import PaperStyle


@dataclass(frozen=True, kw_only=True)
class FaceStyle:
    """The face the hand is opened with, and how a glyph is turned into a pen path.

    Read by `Hand`, which opens the face, and by `nib_plate` through
    `NibGroups`. The defaults open the vendored face and write along its
    centreline. It opens no font itself.

    Attributes:
        label_route: How a glyph is turned into something the pen follows.
            `centreline` thins the face's own outline to a written skeleton;
            `outline` draws round the contour itself. They are two different
            letters, not a choice and a fallback: nothing falls back from one to
            the other.
        label_face: The path of the `.ttf` to open. Empty is the vendored one.
    """

    label_route: Literal["centreline", "outline"] = "centreline"
    label_face: str = ""


@dataclass(frozen=True, kw_only=True)
class HandStyle:
    """The seed the hand draws every label's randomness from.

    Read by `Hand`, which mixes `label_seed` into every generator it hands out,
    so one seed and one text write the same marks. It holds no generator itself.

    Attributes:
        label_seed: Every random draw a label makes comes from this plus the
            label's own name, so an unchanged set of names letters identically on
            every render and a deliberate reshuffle is one number.
    """

    label_seed: int = 17


@dataclass(frozen=True, kw_only=True)
class NibStyle:
    """The nib: size, inks, widths, angle, and the backing wash laid under a name.

    Read by `nib_plate` through `NibGroups`. Inks are `#rrggbb` strings, sizes
    and widths are in display pixels, the angle is in degrees. It draws nothing
    itself.

    Attributes:
        label_size_px: The size the hand is written at, in display pixels.
        label_ink: The ink the lettering is written in.
        label_brush: The nib the lettering is written with. A nib, not a brush:
            a letter at fourteen pixels breaks up if the mark can break, and a
            broken letter is a wrong letter rather than a textured one.
        label_pen_width_px: The nib's width, in display pixels.
        label_outline_width_frac: The outline trace draws two strokes where the
            centreline draws one, a stroke's width apart, so the same nib fills
            the counters and the letter comes out a bolder thing than the face
            is. It writes with a finer one: this share of the nib's width.
        label_leader_brush: The nib every mark that is not a glyph (a leader, a
            span line, a tick, an underline, a pin) is written with, one step
            lighter, so the line recedes behind the name.
        label_leader_width_px: The width of that lighter nib, in display pixels.
        label_pen_angle_deg: The pen's angle in degrees from the page's
            horizontal, in display pixels with y down, so a negative angle turns
            anticlockwise on the page. Without it the letters come out one
            thickness the whole way round, which is a plotter and not a pen.
        label_pen_thin: How much of the width the pen takes off a stroke drawn
            along its angle.
        label_wash: Whether the backing wash is laid: paper-coloured, laid
            through the wash machinery, and absent where the ground is already
            pale enough to read on.
        label_wash_alpha: The backing wash's strength, before the lift's own gain.
        label_wash_dark_floor: The ground darkness at and below which no backing
            wash is laid; it ramps in over the darker ground above it.
        label_wash_spread: How far out from the marks the backing wash reaches,
            as a share of the type size.
        label_route_ink: The ink a name in the route's own colour is written in,
            read from the theme like every other field; the default is the
            default route ink.
        label_water_ink: The ink the `water` token names.
        label_in_water_ink: The ink a name written *on* the water is set in.
            Reversed out of the river in the paper's own cream rather than
            written into it in a dark ink: the water is a mid-tone, so a dark ink
            is fighting it from the wrong side. Measured on a painted river,
            black holds 3.9:1 and this holds 4.7:1, and the difference on the
            plate is larger than the ratio suggests because the letters no longer
            share a value with the bridges crossing them.
    """

    label_size_px: float = 20.0
    label_ink: Colour = Colour("#241c14")  # noqa: RUF009 (an immutable str)
    label_brush: str = "MAJ6-e"
    label_pen_width_px: float = 1.05
    label_outline_width_frac: float = 0.62
    label_leader_brush: str = "MAJ6-e"
    label_leader_width_px: float = 0.85
    label_pen_angle_deg: float = -38.0
    label_pen_thin: float = 0.52
    label_wash: bool = True
    label_wash_alpha: float = 0.5
    label_wash_dark_floor: float = 0.22
    label_wash_spread: float = 0.75
    label_route_ink: Colour = Colour("#c22050")  # noqa: RUF009 (an immutable str)
    label_water_ink: Colour = Colour("#4a7691")  # noqa: RUF009 (an immutable str)
    label_in_water_ink: Colour = Colour("#f8f4e9")  # noqa: RUF009 (an immutable str)

    def __post_init__(self) -> None:
        """Normalise the four inks to `Colour`, so a plain `str` passed to `replace` is accepted."""
        normalise_colours(
            self, "label_ink", "label_route_ink", "label_water_ink", "label_in_water_ink"
        )


@dataclass(frozen=True)
class NibGroups:
    """The style groups the nib reads, passed as one value.

    One frozen value, so `nib_plate` takes one argument; it holds no defaults,
    and `NibGroups(NibStyle(), FaceStyle(), HandStyle(), BrushStyle(),
    PaperStyle())` is the default look throughout.

    Attributes:
        nib: The nib, its inks, widths and angle, and the backing wash.
        face: The face and how a glyph becomes a pen path.
        hand: The seed the marks' randomness starts from.
        brush: The ink engine's brush group, for the shared brush geometry.
        paper: The paper the plate is laid on, for its colour and encoder.
    """

    nib: NibStyle
    face: FaceStyle
    hand: HandStyle
    brush: BrushStyle
    paper: PaperStyle
