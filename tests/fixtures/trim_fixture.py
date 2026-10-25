"""Trim recorded Overpass payloads to what the code reads.

Run as `PYTHONPATH=tests uv run python tests/fixtures/trim_fixture.py [--simplify-m M]
PATH...`. It rewrites each payload in place as minified JSON (`separators=(",", ":")`,
`ensure_ascii=False`, one trailing newline). The top-level `version`, `generator` and
`osm3s` stay; per element `nodes` and `bounds` are dropped, which nothing under
`src/pyntpot/maps` reads; `tags` keep the keys in `KEPT_TAG_KEYS` and every key starting
`name` (Welsh and Gaelic names).

`--simplify-m M` runs Douglas-Peucker on every way's and member's `geometry`, with
tolerance `M` metres in local equirectangular metres at the payload's mean latitude; the
first and last points are kept exactly, so ways still join.

Two drops are for a card far coarser than the data, and are used for the Skye fixture only.
`--drop-minor-roads` removes the ways of `MINOR_HIGHWAYS`, which the pen paints only below
`minor_roads_mppd` display metres per pixel. `--min-area-m2 A` removes closed ways and
multipolygon relations whose outer area is below `A`, unless they are `natural=water` or
`coastline`, carry a `place` tag or have a `name*` tag.

`KEPT_TAG_KEYS` is the string literals of `src/pyntpot/maps` that are tag keys present in
the payloads, plus the keys the landmark ranking reads that `src/` does not name yet.
The command and the resulting tuple are in `specs/001-port/p7-run-log.md`.

A second run changes nothing. It does not parse a payload into features, round
coordinates, or read the environment.
"""

import argparse
import json
import logging
import math
from collections.abc import Sequence
from itertools import pairwise
from pathlib import Path
from typing import Any

log = logging.getLogger("trim_fixture")

#: Tag keys the code reads (`grep -rhoE --include='*.py' '"[a-z_:]+"' src/pyntpot/maps |
#: sort -u`, intersected with the keys present in the payloads), plus the keys the landmark
#: ranking reads. Keys starting `name` are kept as well.
KEPT_TAG_KEYS: tuple[str, ...] = (
    "amenity",
    "artist_name",
    "artwork_type",
    "attraction",
    "boundary",
    "bridge",
    "building",
    "building:levels",
    "direction",
    "display",
    "ele",
    "footway",
    "garden",
    "heath",
    "height",
    "highway",
    "historic",
    "industrial",
    "landuse",
    "leisure",
    "man_made",
    "meadow",
    "memorial",
    "museum",
    "natural",
    "note",
    "peak",
    "place",
    "place_of_worship",
    "plaque",
    "ref",
    "residential",
    "service",
    "start_date",
    "tourism",
    "trees",
    "tunnel",
    "type",
    "water",
    "waterway",
    "wetland",
    "wikidata",
    "wikipedia",
    "heritage",
    "listed_status",
    "shop",
    "brand",
    "brand:wikidata",
)

#: Metres per degree of latitude (equirectangular).
_M_PER_DEG = 111_320.0

_DROPPED = ("nodes", "bounds")

#: Highway classes `--drop-minor-roads` drops: the minor roads the fetch query names
#: (`overpass.MINOR_ROADS`) and the footpaths the basemap's path band paints.
MINOR_HIGHWAYS: tuple[str, ...] = (
    "tertiary",
    "unclassified",
    "residential",
    "track",
    "service",
    "footway",
    "path",
    "cycleway",
    "pedestrian",
    "bridleway",
    "steps",
)

#: Tag values that keep a small area under `--min-area-m2`: water and the coast.
_KEPT_NATURAL = ("coastline", "water")


def _ring_area_m2(ring: list[dict[str, float]], cos_lat: float) -> float:
    """Return the shoelace area of a ring in square metres."""
    xy = [(p["lon"] * _M_PER_DEG * cos_lat, p["lat"] * _M_PER_DEG) for p in ring]
    twice = sum(a[0] * b[1] - b[0] * a[1] for a, b in pairwise(xy))
    return abs(twice) / 2.0


def _is_closed(ring: list[dict[str, float]]) -> bool:
    """Return whether a geometry list starts where it ends."""
    return len(ring) > 3 and ring[0] == ring[-1]


def _outer_area_m2(element: dict[str, Any], cos_lat: float) -> float | None:
    """Return a closed way's or multipolygon's outer area, or None when it has none.

    A relation whose outer members are not all closed rings is measured by the box of its
    outer geometry, an upper bound, so it is kept rather than dropped by mistake.
    """
    if element["type"] == "way":
        ring = element.get("geometry", [])
        return _ring_area_m2(ring, cos_lat) if _is_closed(ring) else None
    if element["type"] != "relation" or element.get("tags", {}).get("type") != "multipolygon":
        return None
    outers = [
        m["geometry"]
        for m in element.get("members", ())
        if m.get("role") == "outer" and m.get("geometry")
    ]
    if not outers:
        return None
    if all(_is_closed(ring) for ring in outers):
        return sum(_ring_area_m2(ring, cos_lat) for ring in outers)
    points = [p for ring in outers for p in ring]
    lats: list[float] = [p["lat"] for p in points]
    lons: list[float] = [p["lon"] for p in points]
    return (max(lats) - min(lats)) * _M_PER_DEG * (max(lons) - min(lons)) * _M_PER_DEG * cos_lat


def _droppable(
    element: dict[str, Any], cos_lat: float, drop_minor_roads: bool, min_area_m2: float | None
) -> bool:
    """Return whether a scale-aware drop removes the element."""
    tags = element.get("tags", {})
    if drop_minor_roads and tags.get("highway") in MINOR_HIGHWAYS:
        return True
    if min_area_m2 is None:
        return False
    if tags.get("natural") in _KEPT_NATURAL or "place" in tags:
        return False
    if any(k.startswith("name") for k in tags):
        return False
    area = _outer_area_m2(element, cos_lat)
    return area is not None and area < min_area_m2


def _kept(tags: dict[str, str]) -> dict[str, str]:
    """Return the tags whose key is read or starts `name`."""
    return {k: v for k, v in tags.items() if k in KEPT_TAG_KEYS or k.startswith("name")}


def _distance_to_chord(
    p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]
) -> float:
    """Return the distance of `p` from segment `ab`, in the planar metres of the points."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    if length2 == 0.0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _simplify(
    geometry: list[dict[str, float]], tolerance_m: float, cos_lat: float
) -> list[dict[str, float]]:
    """Douglas-Peucker over a geometry list, keeping the first and last points."""
    if len(geometry) < 3:
        return geometry
    xy = [(p["lon"] * _M_PER_DEG * cos_lat, p["lat"] * _M_PER_DEG) for p in geometry]
    keep = [False] * len(geometry)
    keep[0] = keep[-1] = True
    stack = [(0, len(geometry) - 1)]
    while stack:
        first, last = stack.pop()
        far, far_i = -1.0, first
        for i in range(first + 1, last):
            d = _distance_to_chord(xy[i], xy[first], xy[last])
            if d > far:
                far, far_i = d, i
        if far > tolerance_m:
            keep[far_i] = True
            stack.append((first, far_i))
            stack.append((far_i, last))
    return [p for p, k in zip(geometry, keep, strict=True) if k]


def _mean_lat(elements: list[dict[str, Any]]) -> float:
    """Return the mean latitude of every geometry point and node in the payload."""
    lats: list[float] = []
    for element in elements:
        if "lat" in element:
            lats.append(element["lat"])
        lats.extend(p["lat"] for p in element.get("geometry", ()))
        for member in element.get("members", ()):
            lats.extend(p["lat"] for p in member.get("geometry", ()))
    return sum(lats) / len(lats) if lats else 0.0


def trim_payload(
    payload: dict[str, Any],
    simplify_m: float | None = None,
    drop_minor_roads: bool = False,
    min_area_m2: float | None = None,
) -> dict[str, Any]:
    """Return a trimmed copy of one Overpass payload.

    Drops `nodes` and `bounds` from every element, filters tags to `KEPT_TAG_KEYS` and
    `name*`, and, when `simplify_m` is given, simplifies every way's and member's geometry.
    `drop_minor_roads` drops the ways of `MINOR_HIGHWAYS`; `min_area_m2` drops closed ways and
    multipolygon relations whose outer area is below it, unless they are natural water or
    coast, a place or named.
    """
    elements: list[dict[str, Any]] = payload["elements"]
    cos_lat = math.cos(math.radians(_mean_lat(elements)))
    out_elements: list[dict[str, Any]] = []
    for element in elements:
        if _droppable(element, cos_lat, drop_minor_roads, min_area_m2):
            continue
        item = {k: v for k, v in element.items() if k not in _DROPPED}
        if "tags" in item:
            item["tags"] = _kept(item["tags"])
        if simplify_m is not None:
            if "geometry" in item:
                item["geometry"] = _simplify(item["geometry"], simplify_m, cos_lat)
            for member in item.get("members", ()):
                if "geometry" in member:
                    member["geometry"] = _simplify(member["geometry"], simplify_m, cos_lat)
        out_elements.append(item)
    return {**payload, "elements": out_elements}


def trim_file(
    path: Path,
    simplify_m: float | None = None,
    drop_minor_roads: bool = False,
    min_area_m2: float | None = None,
) -> None:
    """Rewrite one payload file in place, minified and trimmed."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    trimmed = trim_payload(payload, simplify_m, drop_minor_roads, min_area_m2)
    text = json.dumps(trimmed, separators=(",", ":"), ensure_ascii=False)
    before = path.stat().st_size
    path.write_text(text + "\n", encoding="utf-8")
    log.info("%s: %d -> %d bytes", path.name, before, path.stat().st_size)


def main(argv: Sequence[str] | None = None) -> int:
    """Trim each named payload; return the exit status."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Trim recorded Overpass payloads.")
    parser.add_argument("paths", nargs="+", type=Path, help="payload files to rewrite")
    parser.add_argument(
        "--simplify-m", type=float, default=None, help="Douglas-Peucker tolerance in metres"
    )
    parser.add_argument(
        "--drop-minor-roads",
        action="store_true",
        help="drop minor road and footpath ways (for a card coarser than minor_roads_mppd)",
    )
    parser.add_argument(
        "--min-area-m2",
        type=float,
        default=None,
        help="drop closed ways and multipolygons under this outer area, unless water or named",
    )
    args = parser.parse_args(argv)
    for path in args.paths:
        trim_file(path, args.simplify_m, args.drop_minor_roads, args.min_area_m2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
