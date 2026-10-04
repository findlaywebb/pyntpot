"""The cached Overpass payload, grouped into the vector layers of one map.

Key names: `_osm_layers`, which reads the payload once and returns the wood, park,
water, coast, road, river and landmark-candidate layers in route metres; `_dedupe`,
which keeps one landmark candidate per name; `BURIED_FRAC`, the share of a watercourse
underground that drops it.

Every filled layer comes back as one path wound for `fill-rule="nonzero"`, so two woods
that overlap fill once rather than stacking their alpha. Roads are kept or dropped per
road, not per way, and a watercourse OSM tags as underground is dropped whole.

It does not fetch, classify landmark tags, choose which landmarks the map labels, or
read relief. Invariants: everything is cut to the clip box; a layer's path is empty,
never missing, when nothing of it lies in the box; the order of the payload's
elements fixes the order of every list returned.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyntpot.maps.generalise import Finish, Generalisation, generalise_layer
from pyntpot.maps.osm_elements import Clip, Harvest, Scope, sort_element
from pyntpot.maps.svg_path import path_d, rings_path

if TYPE_CHECKING:
    from pathlib import Path

    from pyntpot.maps.projection import Projection
    from pyntpot.maps.style_groups import BasemapStyle
    from pyntpot.maps.track_index import TrackIndex

#: The share of a watercourse's own length OSM has to tag as underground before
#: none of it is drawn. Half: a river passing under a bridge or a short culvert
#: is an open river, and a river that is mostly in a pipe is a sewer.
BURIED_FRAC = 0.5

#: The park layer's grid is this much coarser than the wood's, and its smallest
#: blob this many times larger.
PARK_CELL_FACTOR = 1.5
PARK_AREA_FACTOR = 3

#: Shifts the park's edge wobble so it does not move in step with the wood's.
PARK_SEED = 9


def _dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per named thing, nearest the track kept."""
    best: dict[str, dict[str, Any]] = {}
    loose: list[dict[str, Any]] = []
    for entry in sorted(candidates, key=lambda c: c["d"]):
        if not entry["n"]:
            loose.append(entry)
        elif entry["n"] not in best:
            best[entry["n"]] = entry
    return sorted(list(best.values()) + loose, key=lambda c: c["d"])


def _kept_roads(found: Harvest) -> list[dict[str, Any]]:
    """The roads whose road earned a place, counting the ways dropped with the rest."""
    roads: list[dict[str, Any]] = []
    for road, entries in found.ways.items():
        if found.road_keep.get(road):
            roads += entries
        else:
            found.counts["road_dropped"] += len(entries)
    return roads


def _open_rivers(found: Harvest) -> list[dict[str, Any]]:
    """The watercourses that are on the ground, not in a sewer.

    **A buried river is not on the ground, so it is not drawn.** OSM maps a
    buried river as a watercourse because it still flows; it runs in a sewer
    under a street and there is nothing to see. The test is per watercourse
    and by length, not per way: a river that passes under one short culvert
    out of thirteen ways stays whole, and one that is `tunnel=yes` end to end
    goes.
    """
    gone = {
        key
        for key, run in found.overall.items()
        if run > 0 and found.under.get(key, 0.0) / run >= BURIED_FRAC
    }
    found.counts["river_buried"] = sum(1 for r in found.rivers if r["k"] in gone)
    return [{k: v for k, v in r.items() if k != "k"} for r in found.rivers if r["k"] not in gone]


def _fills(found: Harvest, scope: Scope) -> dict[str, Any]:
    """The wood and park layers, generalised into blobs or drawn as surveyed."""
    options = scope.options
    derived = scope.derived
    if not options.generalise:
        return {
            "wood": {
                "d": rings_path(found.wood, found.wood_holes),
                "inner": "",
                "n": len(found.wood),
            },
            "trees": [],
            "park": {"d": rings_path(found.park), "n": len(found.park)},
        }
    cell = derived["cell_m"]
    layer = generalise_layer(
        found.wood,
        found.wood_holes,
        scope.clip,
        Generalisation(cell, options.morph_cells, derived["min_area_ha"], options.smooth_passes),
        Finish(
            jitter_m=derived["blob_jitter_m"],
            inset_cells=options.inset_cells,
            seed_spacing_m=derived["tree_spacing_m"],
        ),
    )
    park_layer = generalise_layer(
        found.park,
        [],
        scope.clip,
        Generalisation(
            cell * PARK_CELL_FACTOR,
            options.morph_cells,
            derived["min_area_ha"] * PARK_AREA_FACTOR,
            options.smooth_passes,
        ),
        Finish(jitter_m=derived["blob_jitter_m"], inset_cells=0, seed=PARK_SEED),
    )
    return {
        "wood": {
            "d": "".join(path_d(r, close=True) for r in layer["outer"]),
            "inner": "".join(path_d(r, close=True) for r in layer["inner"]),
            "n": len(layer["outer"]),
        },
        "trees": layer["seeds"],
        "park": {
            "d": "".join(path_d(r, close=True) for r in park_layer["outer"]),
            "n": len(park_layer["outer"]),
        },
    }


def _osm_layers(
    path: Path,
    proj: Projection,
    clip: Clip,
    index: TrackIndex,
    options: BasemapStyle,
    derived: dict[str, Any],
) -> dict[str, Any]:
    """Group the cached Overpass payload into the map's layers.

    Every filled layer comes back as one path wound for `fill-rule="nonzero"`,
    so two woods that overlap fill once rather than stacking their alpha into a
    patch that reads as a third thing.

    Args:
        path: The cached Overpass payload.
        proj: The activity's projection.
        clip: (xmin, ymin, xmax, ymax) in metres; everything is cut to it.
        index: The track, for the interaction tests.
        options: What to draw.
        derived: The scale-aware thresholds from `_derived`.

    Returns:
        The vector layers, in metres.
    """
    scope = Scope(proj, clip, index, options, derived)
    found = Harvest()
    for entry in json.loads(path.read_text()).get("elements", []):
        sort_element(entry, scope, found)
    roads = _kept_roads(found)
    rivers = _open_rivers(found)
    fills = _fills(found, scope)
    return {
        "wood": fills["wood"],
        "trees": fills["trees"],
        "park": fills["park"],
        "water_area": {"d": rings_path(found.lakes), "n": len(found.lakes)},
        "sea_osm": {"d": rings_path(found.sea_polys), "n": len(found.sea_polys)},
        "coastline": found.coast,
        "roads": roads,
        "rivers": rivers,
        "landmark_candidates": _dedupe(found.candidates),
        "counts": found.counts,
    }
