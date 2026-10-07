"""Sorting the elements of a cached Overpass payload into the map's layers.

Key names: `sort_element`, which files one payload element under the layer it belongs
to; `Harvest`, the layers collected so far; `Scope`, what every element is read against;
`_geom` and `_polygon_rings`, which project one element's geometry; `_soften`, the line
tidying the road, river and coast layers share; `LANDMARK_TAG_KEYS`, the tags a
landmark candidate carries forward.

A road is kept or dropped per road, not per way, and a watercourse's underground length
is gathered by name so the layer above can drop a buried one whole. It does not read
the payload file, generalise the filled layers, or choose which landmarks the map
labels. Invariants: everything is cut to the clip box; elements are sorted in payload
order, so the order of every list is the payload's.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, NamedTuple

from pyntpot.ink.chains import join_chains
from pyntpot.ink.polyline import Pt, clip_line, length, simplify, smooth
from pyntpot.maps.candidates.landmark_classes import OFFERED_CLASSES, classify
from pyntpot.maps.providers.overpass import MAJOR_ROADS
from pyntpot.maps.rings import Rings, clip_ring
from pyntpot.maps.svg_path import path_d

if TYPE_CHECKING:
    from pyntpot.maps.projection import Projection
    from pyntpot.maps.style_groups import BasemapStyle
    from pyntpot.maps.track_index import TrackIndex

log = logging.getLogger(__name__)

#: The tags a candidate carries forward, so the label agent can see what a thing
#: is and `landmark_reach` can see how tall it stands.
LANDMARK_TAG_KEYS = (
    "tourism",
    "historic",
    "natural",
    "place",
    "man_made",
    "building",
    "amenity",
    "leisure",
    "bridge",
    "height",
    "building:levels",
    "artwork_type",
    "artist_name",
    "ele",
    "start_date",
    "memorial",
)

#: Fewer points than this is not a line.
MIN_LINE_POINTS = 2

#: A ring needs more points than this to enclose anything.
RING_POINTS_OVER = 3

#: How far a landmark's distance from the track is measured, in metres.
DISTANCE_CAP_M = 3000.0

#: Metres within which two chains of one polygon's members are joined.
JOIN_TOL_M = 1.0

#: A coastline is simplified at this share of the river tolerance.
COAST_EPS_SHARE = 0.6


#: A protected area is simplified this much coarser than a wood.
PARK_EPS_FACTOR = 1.6

#: The Overpass element type of a multipolygon.
RELATION = "relation"

Clip = tuple[float, float, float, float]


class Scope(NamedTuple):
    """What every element is read against."""

    proj: Projection
    clip: Clip
    index: TrackIndex
    options: BasemapStyle
    derived: dict[str, Any]


@dataclass
class Harvest:
    """The layers collected so far, in payload order."""

    wood: list[list[Pt]] = field(default_factory=list)
    wood_holes: list[list[Pt]] = field(default_factory=list)
    park: list[list[Pt]] = field(default_factory=list)
    lakes: list[list[Pt]] = field(default_factory=list)
    sea_polys: list[list[Pt]] = field(default_factory=list)
    # Every way of one road, and whether any of it earned the road a place.
    ways: dict[tuple[str, str], list[dict[str, Any]]] = field(default_factory=dict)
    road_keep: dict[tuple[str, str], bool] = field(default_factory=dict)
    rivers: list[dict[str, Any]] = field(default_factory=list)
    # Metres of each watercourse OSM tags as underground, against its whole run.
    under: dict[str, float] = field(default_factory=dict)
    overall: dict[str, float] = field(default_factory=dict)
    coast: list[dict[str, Any]] = field(default_factory=list)
    candidates: list[dict[str, Any]] = field(default_factory=list)
    counts: dict[str, int] = field(
        default_factory=lambda: {"road_dropped": 0, "stream_dropped": 0, "wood_relations": 0}
    )


def _geom(entry: dict[str, Any], proj: Projection) -> list[Pt]:
    """Project one Overpass `geometry` array into metres."""
    return [proj(g["lat"], g["lon"]) for g in entry.get("geometry") or [] if g]


def _polygon_rings(entry: dict[str, Any], proj: Projection) -> Rings:
    """Outer and inner rings of one way or relation, in metres."""
    if entry.get("type") == "way":
        pts = _geom(entry, proj)
        return ([pts], []) if len(pts) > RING_POINTS_OVER else ([], [])
    outer, inner = [], []
    for member in entry.get("members") or []:
        pts = _geom(member, proj)
        if len(pts) < MIN_LINE_POINTS:
            continue
        (inner if member.get("role") == "inner" else outer).append(pts)
    return (
        [c for c in join_chains(outer, tol=JOIN_TOL_M) if len(c) > RING_POINTS_OVER],
        [c for c in join_chains(inner, tol=JOIN_TOL_M) if len(c) > RING_POINTS_OVER],
    )


def _soften(line: list[Pt], eps: float, options: BasemapStyle) -> list[Pt]:
    """Simplify a line, then round its corners off.

    A road drawn from OSM nodes is a survey; up to two Chaikin passes, when the
    options generalise, make it a line someone drew, like the rest of the sheet.
    """
    out = simplify(line, eps)
    if options.generalise and options.smooth_passes:
        # Chaikin quadruples the points, so the curve is simplified again at a
        # tolerance it cannot see: the line stays round and the layer stays small.
        out = simplify(smooth(out, passes=min(2, options.smooth_passes), closed=False), eps * 0.3)
    return out


def _inside(x: float, y: float, clip: Clip) -> bool:
    """Whether a point lies in the clip box."""
    xmin, ymin, xmax, ymax = clip
    return xmin <= x <= xmax and ymin <= y <= ymax


def _candidate(name: str, tags: dict[str, Any], at: Pt, index: TrackIndex) -> dict[str, Any]:
    """One landmark candidate at a point, with how far off the track it sits."""
    x, y = at
    return {
        "n": name,
        "cls": classify(tags),
        "x": round(x, 1),
        "y": round(y, 1),
        "d": round(index.distance(x, y, cap_m=DISTANCE_CAP_M)),
        "tags": {k: v for k, v in tags.items() if k in LANDMARK_TAG_KEYS},
    }


def _area_rings(entry: dict[str, Any], eps: float, scope: Scope) -> Rings:
    """Outer and inner rings of an area, cut to the box and simplified."""
    outer, inner = _polygon_rings(entry, scope.proj)
    cut = [clip_ring(r, scope.clip) for r in outer]
    holes = [clip_ring(r, scope.clip) for r in inner]
    return (
        [simplify(r, eps) for r in cut if len(r) > RING_POINTS_OVER],
        [simplify(r, eps) for r in holes if len(r) > RING_POINTS_OVER],
    )


def _road(entry: dict[str, Any], tags: dict[str, Any], scope: Scope, found: Harvest) -> None:
    """File the pieces of one way under its road, and decide whether the road is kept."""
    options = scope.options
    within = scope.derived["interaction_m"]
    run_m = scope.derived["interaction_run_m"]
    name = tags.get("name", "")
    highway = tags["highway"]
    major = highway in MAJOR_ROADS
    ref = str(tags.get("ref") or "")
    # Kept or dropped per *road*, not per way. OSM cuts a street at
    # every junction, and answering the interaction test for each cut
    # alone would keep the block that crosses the route and drop the
    # next block along, so every side street would come off the route
    # as a stub and the sheet would read as a comb. A road the track ran
    # along or across is on the card for as long as the card holds it.
    # A way with neither a number nor a name has no road to belong to,
    # so it is decided on its own.
    road = (ref or name or f"~{entry.get('id')}", highway)
    for piece in clip_line(_geom(entry, scope.proj), scope.clip):
        line = _soften(piece, scope.derived["road_eps_m"], options)
        if len(line) < MIN_LINE_POINTS:
            continue
        found.ways.setdefault(road, []).append(
            {
                "c": "major" if major else "minor",
                "n": name,
                # The road number, which is what a map calls a road:
                # "A66" says where the route went and "Lake Road"
                # says nothing at 26 m a pixel.
                "r": ref,
                "k": highway,
                "d": path_d(line),
            }
        )
        if road not in found.road_keep:
            found.road_keep[road] = options.roads == "all" or major or name in options.pick_roads
        if not found.road_keep[road] and options.roads == "key":
            found.road_keep[road] = scope.index.interacts(piece, within, run_m)


def _waterway(entry: dict[str, Any], tags: dict[str, Any], scope: Scope, found: Harvest) -> None:
    """Collect the pieces of a river, always kept, or of a stream the options keep."""
    options = scope.options
    within = scope.derived["interaction_m"]
    run_m = scope.derived["interaction_run_m"]
    name = tags.get("name", "")
    waterway = tags["waterway"]
    buried = bool(tags.get("tunnel"))
    for piece in clip_line(_geom(entry, scope.proj), scope.clip):
        river = waterway == "river"
        keep = (
            options.rivers == "all"
            or river
            or (options.rivers == "key" and scope.index.interacts(piece, within, run_m))
        )
        if not keep:
            found.counts["stream_dropped"] += 1
            continue
        line = _soften(piece, scope.derived["river_eps_m"], options)
        if len(line) < MIN_LINE_POINTS:
            continue
        # How much of this watercourse OSM says is underground, gathered
        # by name so the question is asked of the river and not of each
        # way. A river passing under one bridge is not a buried river.
        run = length(line)
        key = name or f"~{entry.get('id')}"
        found.under[key] = found.under.get(key, 0.0) + (run if buried else 0.0)
        found.overall[key] = found.overall.get(key, 0.0) + run
        found.rivers.append(
            {"c": "river" if river else "stream", "n": name, "k": key, "d": path_d(line)}
        )


def _coastline(entry: dict[str, Any], tags: dict[str, Any], scope: Scope, found: Harvest) -> None:
    """Collect the pieces of a coastline way."""
    eps = scope.derived["river_eps_m"] * COAST_EPS_SHARE
    for piece in clip_line(_geom(entry, scope.proj), scope.clip):
        line = _soften(piece, eps, scope.options)
        if len(line) >= MIN_LINE_POINTS:
            found.coast.append({"n": tags.get("name", ""), "d": path_d(line)})


def _area(entry: dict[str, Any], tags: dict[str, Any], scope: Scope, found: Harvest) -> None:
    """Collect a wood, a protected area or a lake into its layer."""
    wood_eps = scope.derived["wood_eps_m"]
    if tags.get("landuse") == "forest" or tags.get("natural") == "wood":
        outer, inner = _area_rings(entry, wood_eps, scope)
        if entry.get("type") == RELATION and outer:
            found.counts["wood_relations"] += 1
        found.wood += outer
        found.wood_holes += inner
    elif tags.get("boundary") in ("national_park", "protected_area"):
        outer, _ = _area_rings(entry, wood_eps * PARK_EPS_FACTOR, scope)
        found.park += outer
    elif tags.get("natural") in ("water", "bay"):
        outer, _ = _area_rings(entry, scope.derived["river_eps_m"], scope)
        target = found.sea_polys if tags.get("natural") == "bay" else found.lakes
        target += outer


def _area_landmark(
    entry: dict[str, Any], tags: dict[str, Any], scope: Scope, found: Harvest
) -> None:
    """Offer a named way or relation as a landmark, at the mean of its points.

    Any way whose tags put it in an offered class counts, and so does a relation: OSM holds a
    zoo as a multipolygon, and a multipolygon is a relation, so a card can
    offer the zoo as well as the statue that stands in it.
    """
    rings, _holes = _polygon_rings(entry, scope.proj)
    pts = [p for ring in rings for p in ring] if rings else _geom(entry, scope.proj)
    if not pts:
        return
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    if _inside(cx, cy, scope.clip):
        found.candidates.append(_candidate(tags.get("name", ""), tags, (cx, cy), scope.index))


def sort_element(entry: dict[str, Any], scope: Scope, found: Harvest) -> None:
    """Sort one payload element into the layer it belongs to."""
    tags = entry.get("tags") or {}
    name = tags.get("name", "")
    if entry.get("type") == "node":
        x, y = scope.proj(entry["lat"], entry["lon"])
        if _inside(x, y, scope.clip):
            found.candidates.append(_candidate(name, tags, (x, y), scope.index))
        return
    if tags.get("highway"):
        _road(entry, tags, scope, found)
    elif tags.get("waterway") in ("river", "stream"):
        _waterway(entry, tags, scope, found)
    elif tags.get("natural") == "coastline":
        _coastline(entry, tags, scope, found)
    else:
        _area(entry, tags, scope, found)
    if name and entry.get("type") in ("way", RELATION) and classify(tags) in OFFERED_CLASSES:
        _area_landmark(entry, tags, scope, found)
