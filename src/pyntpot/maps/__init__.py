"""Route maps: fetching, painting, lettering and composing.

Exports the map types `Track`, `Basemap`, `Style`, `Plates`, `Lettering` and
`Annotations`, the stages `fetch`, `paint`, `letter` and `compose`, `FetchError`,
the fetch cache `Cache`, the shipped providers `OverpassFeatures` and
`OpenTopoData`, and a cache reader for a caller that draws for itself:
`vector_layers`, which builds `VectorLayers`, the basemap's layers as SVG path data.
The provider protocols, the candidates and the command line are reached through
their own modules, not exported here.
"""

from pyntpot.maps.annotations import Annotations
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering.pipeline import Lettering, letter
from pyntpot.maps.pipeline import FetchError, compose, fetch, paint
from pyntpot.maps.plates import Plates
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track
from pyntpot.maps.vector_layers import VectorLayers, vector_layers

__all__: list[str] = [
    "Annotations",
    "Basemap",
    "Cache",
    "FetchError",
    "Lettering",
    "OpenTopoData",
    "OverpassFeatures",
    "Plates",
    "Style",
    "Track",
    "VectorLayers",
    "compose",
    "fetch",
    "letter",
    "paint",
    "vector_layers",
]
