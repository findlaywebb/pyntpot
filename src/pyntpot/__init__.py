"""Hand-drawn watercolour and pen-and-ink painting, with route maps.

Public API: the map types `Track`, `Basemap`, `Style`, `Plates`, `Lettering`
and `Annotations`; the map functions `fetch`, `paint`, `letter` and `compose`;
and the painting engine's `Sheet`, `Brush`, `Canvas`, `stamp`, `wash`,
`composite` and `Hand`. The layer packages export more.

It does not re-export the layer packages' other names: `pyntpot.ink`,
`pyntpot.letters` and `pyntpot.maps` each list their public names in their own
`__all__`, and a name in no `__all__` is private. The providers and the cache
are reached through `pyntpot.maps`. `Sheet`, `Canvas`, `wash`, `composite`,
`Brush` and `stamp` are re-exported from `ink`; `Hand` from `letters`.
`__version__` is the installed distribution's version.
"""

import importlib.metadata

from pyntpot.ink import Brush, Canvas, Sheet, composite, stamp, wash
from pyntpot.letters import Hand
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

__version__ = importlib.metadata.version("pyntpot")

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
