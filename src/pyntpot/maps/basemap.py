"""The basemap: one map's fetched and projected geometry, as a typed value.

Key types: `Basemap`, everything fetched and projected for one track, framed
by its `Card`; `Layers`, the part of it the painter reads, which is what the
base hash covers together with the card; `Road`, `River` and
`ElevationPatch`, the entries inside it. `Line` is a polyline in card metres.

`Basemap.canonical` writes the part of a basemap the base plates depend on,
the card frame and the `Layers`, as one fixed text that the base hash is taken
over.

It does not fetch, project, paint or hash anything: the fetch builds a
basemap, the painter reads one. It carries no cache key, because the cache
owns its keys. Geometry is carried as point lists in card metres, never as
path strings.

Invariants: every value here is immutable and compares by value; every point
is in the card metres of the basemap's own `card` and `projection`; `track`
holds every track point in recorded order, while `Layers.route` holds the
simplified track the painter draws. `canonical` writes every float to three
decimals, so two machines whose maths differ in the last bit write the same
text, and it reads nothing outside the card frame and the layers.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from pyntpot.ink.polyline import Pt

if TYPE_CHECKING:
    from pyntpot.maps.card import Card
    from pyntpot.maps.credit import Credit
    from pyntpot.maps.projection import Projection

#: A polyline or a ring, in card metres.
Line = tuple[Pt, ...]


@dataclass(frozen=True)
class Road:
    """One road as one brush stroke: the pieces of one named road chained.

    Attributes:
        line: The stroke, in card metres.
        cls: `major` for the classified roads, `minor` for the rest.
        band: Which brush paints it: `major`, `minor` or `path`.
        highway: The OpenStreetMap `highway` value.
        name: The road's name, empty when it has none.
        ref: The road's number, empty when it has none.
    """

    line: Line
    cls: str
    band: str
    highway: str
    name: str
    ref: str


@dataclass(frozen=True)
class River:
    """One watercourse as one brush stroke, at the width it is painted.

    Attributes:
        line: The stroke, in card metres.
        cls: `major`, `medium` or `minor`, which chooses the brush and the ink.
        name: The watercourse's name, empty when it has none.
        width_px: The widest it is painted, in display pixels.
        name_width_px: The width it is typically painted at, in display pixels,
            the one a name set on the water has to fit inside.
        profile: The width at each point of `line` as a share of `width_px`;
            empty when the watercourse is painted at one width throughout.
    """

    line: Line
    cls: str
    name: str
    width_px: float
    name_width_px: float
    profile: tuple[float, ...] = ()


@dataclass(frozen=True)
class ElevationPatch:
    """The elevation samples a basemap carries, placed in card metres.

    Attributes:
        n: Samples per side of the square lattice.
        x0: Card metres east of the first sample.
        y0: Card metres north of the first sample.
        x1: Card metres east of the last sample.
        y1: Card metres north of the last sample.
        values: The `n * n` elevations in metres, row by row from the first
            sample's corner.
        low: The lowest elevation, rounded to a whole metre.
        high: The highest elevation, rounded to a whole metre.
    """

    n: int
    x0: float
    y0: float
    x1: float
    y1: float
    values: tuple[float, ...]
    low: int
    high: int


@dataclass(frozen=True)
class Layers:
    """The geometry and measurements of a basemap that the painter reads.

    Attributes:
        route: The simplified track the ribbon and the pen follow.
        cover: The land-cover rings of each class, by class.
        cover_order: The classes in `cover` in the order they are painted.
        lakes: The inland water rings.
        sea: The sea rings.
        coastline: The coastline chains.
        roads: The road strokes.
        rivers: The watercourse strokes.
        elevation: The elevation samples, or None when none are cached.
        ribbon_m: The ribbon radius, in card metres.
        wet_px: The painted width floor of each watercourse class, in display
            pixels.
        minor_roads: Whether the lanes and tracks are painted at this scale.
        blotch_m: The wood texture's blotch size, in card metres.
        dab_spacing_m: The wood dabs' spacing, in card metres.
        gran_m: The paper granulation's cell size, in card metres.
    """

    route: Line
    cover: Mapping[str, tuple[Line, ...]]
    cover_order: tuple[str, ...]
    lakes: tuple[Line, ...]
    sea: tuple[Line, ...]
    coastline: tuple[Line, ...]
    roads: tuple[Road, ...]
    rivers: tuple[River, ...]
    elevation: ElevationPatch | None
    ribbon_m: int
    wet_px: Mapping[str, float]
    minor_roads: bool
    blotch_m: float
    dab_spacing_m: float
    gran_m: float


@dataclass(frozen=True)
class Basemap:
    """Everything fetched and projected for one track, framed by its card.

    Attributes:
        projection: The projection the track and every layer were put through.
        card: The frame the map is painted on.
        layers: What the painter reads.
        bounds: The track's own box in card metres, as x0, y0, x1, y1.
        span_m: The longer side of `bounds`, in whole metres.
        ribbon_fitted_m: The ribbon radius fitted to the span, before the
            style's multiplier, in whole metres.
        track: Every track point, projected and unrounded, in recorded order.
        track_time: Seconds from the first track point, when they are known.
        places: The places of interest marked on the map.
        candidates: The named things a label may be set on.
        sources: The data sources the layers were built from.
        credits: The attribution owed to those sources.
    """

    projection: Projection
    card: Card
    layers: Layers
    bounds: tuple[float, float, float, float]
    span_m: int
    ribbon_fitted_m: int
    track: Line
    track_time: tuple[float, ...] | None = None
    places: tuple[Mapping[str, Any], ...] = ()
    candidates: tuple[Mapping[str, Any], ...] = ()
    sources: tuple[str, ...] = ()
    credits: tuple[Credit, ...] = ()

    def canonical(self) -> str:
        """The card frame and the layers as one fixed text, the input of the base hash.

        Compact JSON with sorted keys of the card's box, display grid, render
        grid and both scales, and every layer field. Tuples are written as
        lists and every float as a string to three decimals, with negative
        zero written as zero; ints, bools and strings are kept as they are.
        The card's offset, the track, its times, the places, candidates,
        sources and credits are not in it.
        """
        card = self.card
        frame = [card.box, card.display, card.render, card.mpp, card.mpp_display]
        blob = {"card": frame, "layers": asdict(self.layers)}
        return json.dumps(_fixed(blob), sort_keys=True, separators=(",", ":"))


def _fixed(value: object) -> object:
    """Return a JSON-ready copy of `value` with every float written to three decimals."""
    if isinstance(value, float):
        text = format(value, ".3f")
        return "0.000" if text == "-0.000" else text
    if isinstance(value, Mapping):
        return {str(key): _fixed(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_fixed(item) for item in value]
    return value
