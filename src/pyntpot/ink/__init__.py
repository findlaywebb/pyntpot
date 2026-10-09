"""The ink engine: paper, washes, brushes and pigment.

Public names: `Sheet` and `Canvas` (the paper and what is painted on it), `Brush`
and `stamp` (a nib's marks), `wash` and `composite` (pigment laid and combined).
To build a mark and read it back: `BrushStyle` and `brush_from_id` (a brush from a
brush sheet cell) and `ink_density` (a stamped accumulator as density). To colour
and lay pigment: `PIGMENTS`, `TRANSPARENCY`, `rgb`, `PigmentLayer`, and
`PaperStyle`, which `composite` reads.

It does not letter, read geographic data or touch the network.
"""

from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle
from pyntpot.ink.pad import ink_density
from pyntpot.ink.pigment import PIGMENTS, TRANSPARENCY, PigmentLayer, composite
from pyntpot.ink.sheet import Canvas, Sheet, rgb
from pyntpot.ink.stamp import stamp
from pyntpot.ink.style import PaperStyle
from pyntpot.ink.wash import wash

__all__: list[str] = [
    "PIGMENTS",
    "TRANSPARENCY",
    "Brush",
    "BrushStyle",
    "Canvas",
    "PaperStyle",
    "PigmentLayer",
    "Sheet",
    "brush_from_id",
    "composite",
    "ink_density",
    "rgb",
    "stamp",
    "wash",
]
