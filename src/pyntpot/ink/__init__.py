"""The ink engine: paper, washes, brushes and pigment.

Public names: `Sheet` and `Canvas` (the paper and what is painted on it), `Point` and
`Box` (a point and an axis-aligned box, in whatever units hold them), `Brush` and
`stamp` (a nib's marks), `wash` and `composite` (pigment laid and combined). A wash
takes its settings as `WashOptions`, whose flow rim is a `Flow` and whose backruns are
`Blooms`; `separated` turns one wash into the one or two pigments it is mixed from, and
`fluid_modulate` changes a whole stack of washes by one coarse shallow-water pass.
To build a mark and read it back: `BrushStyle` and `brush_from_id` (a brush from a
brush sheet cell) and `ink_density` (a stamped accumulator as density). To colour
and lay pigment: `Colour` (a `#rrggbb` that is also a `str`), `Pigment` (a colour with its
transparency and Colour Index code), `PigmentRegistry` and `PIGMENT_REGISTRY` (the 25 shipped
pigments, read-only), `pigment` (the one lookup, by `Pigment`, name or hex), the tables
`PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` built from the
registry, `rgb`, `PigmentLayer`, and the style groups `PaperStyle`, which `composite` reads,
and `WashStyle`, which `separated` and `fluid_modulate` read. To make and keep an image: `paper_plate` (the cream paper) and `save_image`
(a painted array written to a file).
To lay an effect round a line: `casing`, `glow` and `shadow` (a ring of colour, a lift
toward the paper and a multiplying darken, set by `Casing`, `Glow` and `Shadow`) and
`pen_casing` (a reserve between two ink edge lines, set by `PenCasing`) and `reserve` (the
paper laid back in a ring, with an optional pool, set by `Reserve`).

It does not letter, read geographic data or touch the network.
"""

from pyntpot.ink.bloom import Blooms
from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.colour import Colour
from pyntpot.ink.compositing import PigmentLayer, composite
from pyntpot.ink.effect_casing import casing
from pyntpot.ink.effect_glow import glow
from pyntpot.ink.effect_pen_casing import pen_casing
from pyntpot.ink.effect_reserve import reserve
from pyntpot.ink.effect_shadow import shadow
from pyntpot.ink.effect_types import Casing, Glow, PenCasing, Reserve, Shadow
from pyntpot.ink.io import save_image
from pyntpot.ink.pad import ink_density
from pyntpot.ink.paper import paper_plate
from pyntpot.ink.pigment_registry import PIGMENT_REGISTRY, PigmentRegistry, pigment
from pyntpot.ink.pigment_table import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    PIGMENTS,
    TRANSPARENCY,
    Pigment,
)
from pyntpot.ink.polyline import Box, Point
from pyntpot.ink.sheet import Canvas, Sheet, rgb
from pyntpot.ink.stamping import stamp
from pyntpot.ink.style import PaperStyle, WashStyle
from pyntpot.ink.washing import Flow, WashOptions, fluid_modulate, separated, wash

__all__: list[str] = [
    "PAINTERS_PIGMENTS",
    "PAINTERS_TRANSPARENCY",
    "PIGMENTS",
    "PIGMENT_REGISTRY",
    "TRANSPARENCY",
    "Blooms",
    "Box",
    "Brush",
    "BrushStyle",
    "Canvas",
    "Casing",
    "Colour",
    "Flow",
    "Glow",
    "PaperStyle",
    "PenCasing",
    "Pigment",
    "PigmentLayer",
    "PigmentRegistry",
    "Point",
    "Reserve",
    "Shadow",
    "Sheet",
    "WashOptions",
    "WashStyle",
    "brush_from_id",
    "casing",
    "composite",
    "fluid_modulate",
    "glow",
    "ink_density",
    "paper_plate",
    "pen_casing",
    "pigment",
    "reserve",
    "rgb",
    "save_image",
    "separated",
    "shadow",
    "stamp",
    "wash",
]
