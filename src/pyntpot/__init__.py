"""Hand-drawn watercolour and pen-and-ink painting, with route maps.

Public API: the map types `Track`, `Basemap`, `Style`, `Plates`, `Lettering`
and `Annotations`; the map functions `fetch`, `paint`, `letter` and `compose`;
and the painting engine's `Sheet`, `Brush`, `Canvas`, `stamp`, `wash`,
`composite` and `Hand`. Everything else is private.

It does not export the layer packages' contents or any provider, cache or
command-line name: those are reached through `pyntpot.maps`. `Sheet`, `Canvas`, `wash` and `composite` are re-exported from `ink`;
`Brush`, `stamp` and `Hand` from the interim `_port` code, so their
`__module__` is private. `__version__` is the installed distribution's version.
"""

from importlib.metadata import version

from pyntpot._port.labels import Hand
from pyntpot._port.paint import Brush, stamp
from pyntpot.ink.pigment import composite
from pyntpot.ink.sheet import Canvas, Sheet
from pyntpot.ink.wash import wash
from pyntpot.maps import (
    Annotations,
    Basemap,
    Lettering,
    Plates,
    Style,
    Track,
    compose,
    fetch,
    letter,
    paint,
)

__version__ = version("pyntpot")

__all__: list[str] = [
    "Annotations",
    "Basemap",
    "Brush",
    "Canvas",
    "Hand",
    "Lettering",
    "Plates",
    "Sheet",
    "Style",
    "Track",
    "__version__",
    "compose",
    "composite",
    "fetch",
    "letter",
    "paint",
    "stamp",
    "wash",
]
