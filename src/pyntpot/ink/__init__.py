"""The ink engine: paper, washes, brushes and pigment.

Public names: `Sheet` and `Canvas` (the paper and what is painted on it), `Point` and
`Box` (a point and an axis-aligned box, in whatever units hold them), `Brush` and
`stamp` (a nib's marks), `wash` and `composite` (pigment laid and combined). A wash
takes its settings as `WashOptions`, whose flow rim is a `Flow` and whose backruns are
`Blooms`; `separated` turns one wash into the one or two pigments it is mixed from, and
`fluid_modulate` changes a whole stack of washes by one coarse shallow-water pass.
To build a mark and read it back: `BrushStyle` and `brush_from_id` (a brush from a
brush sheet cell) and `ink_density` (a stamped accumulator as density). To colour
and lay pigment: `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS`,
`PAINTERS_TRANSPARENCY`, `rgb`, `PigmentLayer`, and the style groups `PaperStyle`,
which `composite` reads, and `WashStyle`, which `separated` and `fluid_modulate`
read. To make and keep an image: `paper_plate` (the cream paper) and `save_image`
(a painted array written to a file).

It does not letter, read geographic data or touch the network.
"""

from pyntpot.ink.bloom import Blooms
from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.io import save_image
from pyntpot.ink.pad import ink_density
from pyntpot.ink.paper import paper_plate
from pyntpot.ink.pigment import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    PIGMENTS,
    TRANSPARENCY,
    PigmentLayer,
    composite,
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
    "TRANSPARENCY",
    "Blooms",
    "Box",
    "Brush",
    "BrushStyle",
    "Canvas",
    "Flow",
    "PaperStyle",
    "PigmentLayer",
    "Point",
    "Sheet",
    "WashOptions",
    "WashStyle",
    "brush_from_id",
    "composite",
    "fluid_modulate",
    "ink_density",
    "paper_plate",
    "rgb",
    "save_image",
    "separated",
    "stamp",
    "wash",
]
