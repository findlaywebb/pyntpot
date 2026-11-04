"""Route maps: fetching, painting, lettering and composing.

Exports the map types `Track`, `Basemap`, `Style`, `Plates`, `Lettering`,
`Annotations` and its `JournalNote`, the stages `fetch`, `paint`, `letter` and `compose`, `FetchError`, the
fetch cache `Cache` and its `FetchMargins`, the shipped providers `OverpassFeatures` and `OpenTopoData` and the
errors they raise, `ProviderError` and `ProviderBudgetExceededError`, and two cache
readers for a caller that chooses or draws for itself: `candidate_export`, what a track
passes, and `vector_layers`, which builds `VectorLayers`, the basemap's layers as SVG
path data. The other candidates modules and the command line are reached through their
own modules, not exported here.

The seven map style groups sit beside `Style`, one per field of it: `CardStyle`,
`RibbonStyle`, `CoverStyle`, `RouteStyle`, `BasemapStyle`, `LetteringStyle` and
`RouteInkStyle`. `Features` and `Elevation` are the protocols a caller's own provider
satisfies, and `ElevationGrid` is what an elevation provider returns. `Landmark`,
`SpanRequest`, `MAX_NOTES` and `MAX_NOTE_CHARS` sit beside `Annotations`, the parts and
limits of a caller's request. The records `fetch`, `paint` and `letter` hand back are
exported so a caller can read them: `Card`, `Credit`, `Manifest`, `DarkGrid`,
`BoundingBox`, `Layers`, `River`, `Road`, `ElevationPatch`, `Line`, `Projection`, `Label`,
`Span`, `VectorArea`, `VectorLine`, `HillshadeBand` and `HillshadeImage`.
"""

from pyntpot.maps.annotations import (
    MAX_NOTE_CHARS,
    MAX_NOTES,
    Annotations,
    JournalNote,
    Landmark,
    SpanRequest,
)
from pyntpot.maps.basemap import Basemap, ElevationPatch, Layers, Line, River, Road
from pyntpot.maps.cache import Cache, FetchError, FetchMargins
from pyntpot.maps.candidates.export import candidate_export
from pyntpot.maps.card import Card
from pyntpot.maps.credit import Credit
from pyntpot.maps.lettering.label import Label, Span
from pyntpot.maps.lettering.pipeline import Lettering, letter
from pyntpot.maps.pipeline import compose, fetch, paint
from pyntpot.maps.plates import DarkGrid, Manifest, Plates
from pyntpot.maps.projection import Projection
from pyntpot.maps.providers.base import (
    Elevation,
    ElevationGrid,
    Features,
    ProviderBudgetExceededError,
    ProviderError,
)
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.style import Style
from pyntpot.maps.style_groups import (
    BasemapStyle,
    CardStyle,
    CoverStyle,
    LetteringStyle,
    RibbonStyle,
    RouteInkStyle,
    RouteStyle,
)
from pyntpot.maps.track import BoundingBox, Track
from pyntpot.maps.vector_layer_build import (
    HillshadeBand,
    HillshadeImage,
    VectorArea,
    VectorLayers,
    VectorLine,
    vector_layers,
)

__all__: list[str] = [
    "MAX_NOTES",
    "MAX_NOTE_CHARS",
    "Annotations",
    "Basemap",
    "BasemapStyle",
    "BoundingBox",
    "Cache",
    "Card",
    "CardStyle",
    "CoverStyle",
    "Credit",
    "DarkGrid",
    "Elevation",
    "ElevationGrid",
    "ElevationPatch",
    "Features",
    "FetchError",
    "FetchMargins",
    "HillshadeBand",
    "HillshadeImage",
    "JournalNote",
    "Label",
    "Landmark",
    "Layers",
    "Lettering",
    "LetteringStyle",
    "Line",
    "Manifest",
    "OpenTopoData",
    "OverpassFeatures",
    "Plates",
    "Projection",
    "ProviderBudgetExceededError",
    "ProviderError",
    "RibbonStyle",
    "River",
    "Road",
    "RouteInkStyle",
    "RouteStyle",
    "Span",
    "SpanRequest",
    "Style",
    "Track",
    "VectorArea",
    "VectorLayers",
    "VectorLine",
    "candidate_export",
    "compose",
    "fetch",
    "letter",
    "paint",
    "vector_layers",
]
