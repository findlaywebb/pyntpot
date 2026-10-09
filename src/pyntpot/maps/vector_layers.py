"""The basemap's vector layers as a typed value, for a caller that draws its own map.

Key names: `vector_layers`, which reads the payloads the fetch cache holds under a
track's key and returns `VectorLayers`; `VectorLayers`, the basemap's areas, lines,
relief, trees, landmarks and places as SVG path data and plain values. Its entries,
`VectorArea`, `VectorLine`, `HillshadeBand` and `HillshadeImage`, are reached through it.

It does not fetch, paint or letter, and writes nothing: with neither the features nor
the elevation payload cached under the key it returns `None`. It does not carry the
generalisation thresholds behind the layers, the payload's element counts, the
elevation summary, the sea's wave lines or the landmark candidates; the candidate
export carries what a track passes.

Invariants: every path is SVG path data in card metres at 0.1 m, x east and y north,
with the track's first point at `origin`, or with none the track's south-west corner
at 0, 0. The style's picked landmarks replace the chosen landmarks, and a minor road
it picks is kept. The ground kept round the track is 900 m before the box's scale.
The same payloads, track, key, style, places and origin always give the same value,
read from the basemap's own assembly and never re-derived.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

from pyntpot.maps.layers import BasemapInputs, basemap

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pyntpot.maps.cache import Cache
    from pyntpot.maps.style import Style
    from pyntpot.maps.track import Track

#: A box in card metres: west, south, east, north.
Box = tuple[float, float, float, float]


@dataclass(frozen=True)
class VectorArea:
    """A filled area and the inner ring a wash dries back to.

    Attributes:
        path: The area's rings as SVG path data, empty when none lies in the box.
        inner: The inner rings a wash dries back to, empty when there are none.
    """

    path: str = ""
    inner: str = ""


@dataclass(frozen=True)
class VectorLine:
    """One line of a layer, with its class, name, weight and level.

    Attributes:
        path: The line as SVG path data.
        cls: For a road or a contour `"major"` or `"minor"`; for a watercourse
            `"river"` or `"stream"`; empty for a line with no class.
        name: The line's name, empty when it has none.
        weight: A hachure group's share of the relief opacity, 0 to 1; 1 for any
            other line.
        level_m: A contour's elevation in metres; `None` for any other line.
    """

    path: str
    cls: str = ""
    name: str = ""
    weight: float = 1.0
    level_m: float | None = None


@dataclass(frozen=True)
class HillshadeBand:
    """One posterised relief band.

    Attributes:
        path: The band's rings as SVG path data.
        sign: -1 for a shadow, 1 for a light.
        level: The shade level the band is traced at, 0 to 1.
    """

    path: str
    sign: int
    level: float


@dataclass(frozen=True)
class HillshadeImage:
    """The greyscale hillshade image and where it sits on the card.

    Attributes:
        href: The image as a `data:image/png` URI.
        x: The image's west edge in card metres.
        y: The image's south edge in card metres.
        w: The image's width in card metres.
        h: The image's height in card metres.
        px: The image's width in pixels.
        py: The image's height in pixels.
    """

    href: str
    x: float
    y: float
    w: float
    h: float
    px: int
    py: int


@dataclass(frozen=True)
class VectorLayers:
    """The basemap's layers for one track, as SVG path data in card metres.

    The value is read-only: the dataclass is frozen and each landmark and place entry,
    with any mapping nested in it, is a read-only view, so changing one raises
    `TypeError`. Those views cannot be pickled, deep-copied or hashed, so a value
    carrying any landmark or place cannot be either; a caller that needs that copies
    the entries out with `dict`.

    Attributes:
        key: The fetch cache's key the layers were read under.
        clip: The box drawn, west, south, east, north, in card metres.
        bounds: The track's own box, west, south, east, north, in card metres.
        span_m: The longer side of the track's box, in whole metres.
        scale: How much coarser than the reference span the box is drawn, 1 to 4.
        river_width_px: The width a river is drawn at, in display pixels.
        sea: The sea, from the elevation grid and the coast.
        mapped_sea: The sea polygons the features payload maps.
        park: The parks.
        wood: The woods, with the inner rings a wash dries back to.
        lakes: The lakes and other standing water.
        rivers: The watercourses kept, each `"river"` or `"stream"`, with its name.
        coastline: The coast's chains.
        roads: The roads kept, each `"major"` or `"minor"`, with its name.
        contours: The contours, each `"major"` or `"minor"`, with its level.
        hachures: The hachure groups, each with its weight.
        hillshade_bands: The posterised relief bands.
        hillshade_image: The greyscale hillshade image, or `None` when the style
            draws none.
        trees: Where the woods' tree marks sit, as x, y in card metres.
        landmarks: The landmarks chosen for the box, each a read-only mapping with
            `n`, `cls`, `d`, `x`, `y` and `tags`, and `picked` or `missing` for a pick.
        places: The supplied places inside the box, each a read-only mapping with
            `n`, `sym`, `kind`, `always`, `x`, `y` and `note`.
        sources: Where the layers came from, one line per cached payload read.
    """

    key: str
    clip: Box
    bounds: Box
    span_m: int
    scale: float
    river_width_px: float
    sea: VectorArea
    mapped_sea: VectorArea
    park: VectorArea
    wood: VectorArea
    lakes: VectorArea
    rivers: tuple[VectorLine, ...]
    coastline: tuple[VectorLine, ...]
    roads: tuple[VectorLine, ...]
    contours: tuple[VectorLine, ...]
    hachures: tuple[VectorLine, ...]
    hillshade_bands: tuple[HillshadeBand, ...]
    hillshade_image: HillshadeImage | None
    trees: tuple[tuple[float, float], ...]
    landmarks: tuple[Mapping[str, Any], ...]
    places: tuple[Mapping[str, Any], ...]
    sources: tuple[str, ...]


def vector_layers(
    track: Track,
    cache: Cache,
    key: str,
    style: Style,
    places: Sequence[Mapping[str, Any]] = (),
    *,
    origin: tuple[float, float] | None = None,
) -> VectorLayers | None:
    """Read one track's basemap layers from the fetch cache as a typed value.

    Nothing is fetched and nothing is written. The landmarks, roads and places the
    style's basemap group picks travel in the style, not in a parameter.

    Args:
        track: The track the layers are drawn round.
        cache: The fetch cache holding the payloads.
        key: The fetch cache's key for this track and the providers that filled it.
            It must be the track's: a key for another box reads that box's payloads.
        style: The style; its basemap group says what is drawn and what is picked.
        places: Places of interest, each with a `name`, `lat` and `lng`, and
            optionally `kind`, `symbol`, `always_label` and `note`.
        origin: Where the track's first point sits, in card metres. With none, the
            track's south-west corner is 0, 0.

    Returns:
        The vector layers, or `None` when neither the features nor the elevation
        payload is cached under `key`.
    """
    inputs = BasemapInputs(key, track, cache, [dict(place) for place in places])
    route = [origin] if origin is not None else None
    found = basemap(inputs, style.basemap, route=route)
    if found is None:
        return None
    return _layers(found)


def _layers(found: dict[str, Any]) -> VectorLayers:
    """The typed value of the assembled basemap's plain data."""
    derived = found.get("derived", {})
    return VectorLayers(
        key=found["id"],
        clip=_box(found["clip"]),
        bounds=_box(found["bounds"]),
        span_m=int(found["span_m"]),
        scale=float(derived.get("scale", 1.0)),
        river_width_px=float(derived.get("river_width", 0.0)),
        sea=_area(found.get("sea", {})),
        mapped_sea=_area(found.get("sea_osm", {})),
        park=_area(found.get("park", {})),
        wood=_area(found.get("wood", {})),
        lakes=_area(found.get("water_area", {})),
        rivers=tuple(_line(entry) for entry in found.get("rivers", [])),
        coastline=tuple(_line(entry) for entry in found.get("coastline", [])),
        roads=tuple(_line(entry) for entry in found.get("roads", [])),
        contours=tuple(_contour(entry) for entry in found.get("contours", [])),
        hachures=tuple(_hachure(entry) for entry in found.get("hachures", [])),
        hillshade_bands=tuple(_band(entry) for entry in found.get("hillshade_bands", [])),
        hillshade_image=_image(found.get("hillshade_raster")),
        trees=tuple((float(x), float(y)) for x, y in found.get("trees", [])),
        landmarks=tuple(_read_only(entry) for entry in found.get("landmarks", [])),
        places=tuple(_read_only(entry) for entry in found.get("places", [])),
        sources=tuple(found.get("sources", [])),
    )


def _box(values: Sequence[float]) -> Box:
    """A box of four floats from the plain data's list."""
    west, south, east, north = values
    return (float(west), float(south), float(east), float(north))


def _area(entry: Mapping[str, Any]) -> VectorArea:
    """A filled area from its plain-data entry."""
    return VectorArea(path=entry.get("d", ""), inner=entry.get("inner", ""))


def _line(entry: Mapping[str, Any]) -> VectorLine:
    """A road, watercourse or coast chain from its plain-data entry."""
    return VectorLine(path=entry["d"], cls=entry.get("c", ""), name=entry.get("n", ""))


def _contour(entry: Mapping[str, Any]) -> VectorLine:
    """A contour from its plain-data entry: its class and its level."""
    cls = "major" if entry.get("major") else "minor"
    return VectorLine(path=entry["d"], cls=cls, level_m=float(entry["e"]))


def _hachure(entry: Mapping[str, Any]) -> VectorLine:
    """A hachure group from its plain-data entry: its share of the relief opacity."""
    return VectorLine(path=entry["d"], weight=float(entry["o"]))


def _band(entry: Mapping[str, Any]) -> HillshadeBand:
    """A relief band from its plain-data entry."""
    return HillshadeBand(path=entry["d"], sign=int(entry["s"]), level=float(entry["t"]))


def _image(entry: Mapping[str, Any] | None) -> HillshadeImage | None:
    """The hillshade image from its plain-data entry, or `None` when there is none."""
    if not entry:
        return None
    return HillshadeImage(
        href=entry["href"],
        x=float(entry["x"]),
        y=float(entry["y"]),
        w=float(entry["w"]),
        h=float(entry["h"]),
        px=int(entry["px"]),
        py=int(entry["py"]),
    )


def _read_only(entry: Mapping[str, Any]) -> Mapping[str, Any]:
    """A read-only view of a copy of an entry, its nested mappings read-only too."""
    return MappingProxyType(
        {k: _read_only(v) if isinstance(v, dict) else v for k, v in entry.items()}
    )
