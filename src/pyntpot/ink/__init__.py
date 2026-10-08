"""The ink engine: paper, washes, brushes and pigment.

Public names: `Sheet` and `Canvas` (the paper and what is painted on it), `Brush`
and `stamp` (a nib's marks), `wash` and `composite` (pigment laid and combined).
It does not letter, read geographic data or touch the network.
"""

from pyntpot.ink.brush import Brush
from pyntpot.ink.pigment import composite
from pyntpot.ink.sheet import Canvas, Sheet
from pyntpot.ink.stamp import stamp
from pyntpot.ink.wash import wash

__all__: list[str] = ["Brush", "Canvas", "Sheet", "composite", "stamp", "wash"]
