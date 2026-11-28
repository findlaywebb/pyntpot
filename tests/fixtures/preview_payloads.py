"""The preview fixture's writers: the projection, the rounding, and the five files.

Key names: `PROJECTION`, the one fixed projection that puts the generator's metres into
degrees; `Elements`, which numbers Overpass elements 1, 2, 3 in writing order across both
payloads; `payload_text`, `gpx_text` and `elevation_text`, the bytes of a payload, the track
and the elevation grid; `readme_text`, the fixture's README.

The layout in metres is `make_preview`; this module only turns it into bytes. It reads no
network and no environment. Invariants: every coordinate is rounded to seven decimals
(`DEGREE_PLACES`) before it is written, the elevation to whole metres, the track to six
decimals as GPX writes it; a payload is `json.dumps(..., separators=(",", ":"))` and a trailing
newline, so the same layout always gives the same bytes.
"""

import json
from collections.abc import Callable, Sequence
from typing import Any

from pyntpot.maps import BoundingBox, Projection
from pyntpot.maps.cache import ELEVATION_SAMPLES
from pyntpot.maps.providers.base import ElevationGrid

Point = tuple[float, float]

#: The latitude and longitude the generator's metre frame is centred on, inside the Lynmouth box.
CENTRE_LAT = 51.225
CENTRE_LNG = -3.84

#: The one projection every point passes through: x east and y north in metres from the centre.
PROJECTION = Projection(lat0=CENTRE_LAT, lat_ref=CENTRE_LAT, lng_ref=CENTRE_LNG)

#: Decimal places of a latitude or longitude in a payload, and in the GPX.
DEGREE_PLACES = 7
GPX_PLACES = 6

#: The `osm3s` block: the payloads are made up, not OpenStreetMap data.
OSM3S = {
    "timestamp_osm_base": "2026-11-28T00:00:00Z",
    "copyright": "Synthetic data made by tests/fixtures/make_preview.py; not OpenStreetMap data.",
}

#: What the payloads name as their maker.
GENERATOR = "tests/fixtures/make_preview.py"


def degrees(point: Point) -> tuple[float, float]:
    """Return a point in metres as a latitude and longitude rounded to `DEGREE_PLACES`."""
    lat, lng = PROJECTION.inverse(*point)
    return round(lat, DEGREE_PLACES), round(lng, DEGREE_PLACES)


def geometry(points: Sequence[Point]) -> list[dict[str, float]]:
    """Return points in metres as an Overpass `geometry` array."""
    out = []
    for point in points:
        lat, lng = degrees(point)
        out.append({"lat": lat, "lon": lng})
    return out


class Elements:
    """Overpass elements numbered 1, 2, 3 in the order they are made, across every payload."""

    def __init__(self) -> None:
        """Start numbering at 1."""
        self._last = 0

    def _next(self) -> int:
        """Return the next element id."""
        self._last += 1
        return self._last

    def node(self, tags: dict[str, str], at: Point) -> dict[str, Any]:
        """Make a node at a point in metres."""
        (lat, lng), ident = degrees(at), self._next()
        return {"type": "node", "id": ident, "lat": lat, "lon": lng, "tags": tags}

    def way(self, tags: dict[str, str], points: Sequence[Point]) -> dict[str, Any]:
        """Make a way along points in metres."""
        return {"type": "way", "id": self._next(), "geometry": geometry(points), "tags": tags}

    def relation(
        self, tags: dict[str, str], members: Sequence[tuple[str, Sequence[Point]]]
    ) -> dict[str, Any]:
        """Make a relation of way members, each a role and its points in metres."""
        ident = self._next()
        made = [
            {"type": "way", "ref": self._next(), "role": role, "geometry": geometry(points)}
            for role, points in members
        ]
        return {"type": "relation", "id": ident, "members": made, "tags": tags}


def payload_text(elements: Sequence[dict[str, Any]]) -> str:
    """Return an Overpass payload's bytes: compact JSON and a trailing newline."""
    document = {"version": 0.6, "generator": GENERATOR, "osm3s": OSM3S, "elements": list(elements)}
    return json.dumps(document, separators=(",", ":")) + "\n"


def gpx_text(name: str, points: Sequence[Point]) -> str:
    """Return a GPX file in the Lynmouth `track.gpx` layout: no times, no elevations."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gpx version="1.1" creator="pyntpot-fixture" xmlns="http://www.topografix.com/GPX/1/1">',
        "  <trk>",
        f"    <name>{name}</name>",
        "    <trkseg>",
    ]
    for point in points:
        lat, lng = PROJECTION.inverse(*point)
        lines.append(f'      <trkpt lat="{lat:.{GPX_PLACES}f}" lon="{lng:.{GPX_PLACES}f}"/>')
    lines += ["    </trkseg>", "  </trk>", "</gpx>", ""]
    return "\n".join(lines)


def elevation_text(box: BoundingBox, height: Callable[[Point], float]) -> str:
    """Return the elevation grid over a box in the bytes `Cache.ensure` would write.

    Args:
        box: The south, west, north, east degrees the grid spans; rounded here to `DEGREE_PLACES`.
        height: A function from a point in metres to its elevation; rounded here to whole metres.

    Returns:
        `ElevationGrid.to_json()` of an `ELEVATION_SAMPLES` square grid, with the trailing
        newline every committed text file ends with (the end-of-file hook asks for it, and
        the recorded fixtures' elevation files end so).
    """
    n = ELEVATION_SAMPLES
    south, west, north, east = (round(v, DEGREE_PLACES) for v in box)
    lats = tuple(round(south + (north - south) * i / (n - 1), DEGREE_PLACES) for i in range(n))
    lons = tuple(round(west + (east - west) * j / (n - 1), DEGREE_PLACES) for j in range(n))
    elev = tuple(float(round(height(PROJECTION(lat, lng)))) for lat in lats for lng in lons)
    grid = ElevationGrid(
        n=n, box=BoundingBox(south, west, north, east), lats=lats, lons=lons, elev=elev
    )
    return grid.to_json() + "\n"


README = """\
# Preview fixture

A synthetic route and the provider payloads cached for it, made by
`tests/fixtures/make_preview.py`. Nothing here is recorded from OpenStreetMap: the track and
every element are made up, so none of it is ODbL data. The names are real names of the
Lynmouth area (Lynmouth, Lynton, East Lyn River, West Lyn River, Countisbury, Watersmeet,
Foreland Point) standing at made-up places, by design. Features with no real name there carry
no name tag. The card's credits read "© OpenStreetMap contributors" over this
data and "elevation: NASA SRTM" over the synthetic grid, because each is its provider's credit.

Regenerate with `PYTHONPATH=tests uv run python -m fixtures.make_preview OUT_DIR`; the fixture
test runs it into a temporary directory and compares every file byte for byte.

## Files

| File | What it is |
|---|---|
| `track.gpx` | {points} points every 20 m or less, no times or elevations. |
| `overpass-{key}.json` | The feature payload: coast, water, roads, woods, places and landmarks. |
| `landcover-{key}.json` | The land cover payload: the gravel bar and the cover patches. |
| `elevation-{key}.json` | An 80 by 80 grid over the features fetch box: sea at 0 m, land on a 20 m floor, one hill. |

Each payload is named `<kind>-<key>.json`, where the key is the fetch cache key of this track
with the shipped Overpass and OpenTopoData providers and the default `FetchMargins`, so a
cache over a copy of this directory finds every payload and fetches nothing.

## Frame

The track's box is 1.5 km east to west by 1.6 km north to south, centred inside the Lynmouth
box. The features fetch box (the track's box and 1500 m) is about 4.5 by 4.6 km and lies inside
the Lynmouth box; it holds every theme's card. Every element lies inside it, rounded inward by
a metre, and the land cover is written only inside it too (the land cover payload has no box
field). Every coordinate in the payloads, the elevation grid and the GPX lies inside the
Lynmouth box. The coast, the major road, the river, the stream and the minor road run to the
fetch box's edge, so each crosses every theme's card edge. Every feature listed below lies
within 350 m of the track's box, so it is inside the smallest card.

## Features and what each tests

| Feature | Payload | Tags | Name | What it tests |
|---|---|---|---|---|
| Coast | features | way `natural=coastline`, east to west, sea to the north | none | the sea, the shore and the coast's ink |
| Offshore island | features | closed anticlockwise way `natural=coastline` | none | land inside the sea |
| Lake with an island | features | relation `natural=water`, one `outer` and one `inner` | none | water with dry land in it |
| River | features | two ways `waterway=river` that part and rejoin | East Lyn River | a river that splits round a bar |
| Gravel bar | land cover | way `natural=shingle` | none | sand between the two channels |
| Stream | features | way `waterway=stream`, ending on the river | West Lyn River | a minor water joining a river |
| Major road | features | way `highway=primary` | none | a road over the river, the stream and the minor road |
| Minor road | features | way `highway=unclassified` | none | a lane the route runs along and crosses the river |
| Woods | features | ways `natural=wood`: one large, one 50 m square | none | wood, and a wood below `min_patch_px` |
| Meadow, heath, built-up, rock | land cover | `landuse=meadow`, `natural=heath`, `landuse=residential`, `natural=bare_rock` | none | each class, with 50 m squares of meadow and heath beside larger patches |
| Lynmouth, Lynton, Countisbury | features | nodes `place=village`, `place=town`, `place=hamlet` | as given | settlements near the route |
| Foreland Point, Watersmeet | features | nodes `man_made=lighthouse`, `tourism=attraction` | as given | named landmarks |
| Hill | elevation | a Gaussian 300 m high on the floor | none | relief |

## The route

It starts at Lynton's side, runs down to the minor road and along it to the river, walks up
the East Lyn River's bank beside the gravel bar and back down, then runs out east along the
road and back, and ends south of the stream. It crosses the East Lyn River twice and the West
Lyn River once. It keeps at least 300 m from the coast. It doubles back beside the minor road
(out to the east and back, within 20 m of the road) and beside the river (up the bank and
back, within 40 m of the channel).

The riverside stretch, the walk up the bank and back down it, is track points {river_first}
to {river_last} (counting from 0). A journal note lies on one of them.
"""


def readme_text(key: str, points: int, river_first: int, river_last: int) -> str:
    """Return the README, with the cache key, the track's size and the riverside stretch filled in."""
    return README.format(key=key, points=points, river_first=river_first, river_last=river_last)
