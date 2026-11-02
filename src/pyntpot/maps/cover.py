"""Land cover, wood and coast rings from the cached Overpass payloads.

Key names: `cover_rings`, the land cover polygons by pigment class, clipped to the card
and simplified; `wood_rings`, the woods of the feature payload; `coastline_chains`, the
coast as surveyed, joined and never smoothed; `COVER_TAGS` and `COVER_ORDER`, the
tag-to-pigment table and the painting order. The sea made from the coast is in `sea`.

It does not fetch payloads, project a track, or paint anything: it reads the files the
cache already holds and returns rings in card metres. Invariants: a missing payload
is an empty result, never an error; the coast keeps its own vertices; a class later in
`COVER_ORDER` is painted over an earlier one, so a plate carries one class per pixel.
"""

from __future__ import annotations

import json
import logging
import math
from typing import TYPE_CHECKING

from pyntpot.ink.chains import join_chains
from pyntpot.ink.polyline import Pt, clip_line, simplify
from pyntpot.maps.osm_elements import polygon_rings
from pyntpot.maps.rings import clip_ring

if TYPE_CHECKING:
    from pyntpot.maps.cache import Cache
    from pyntpot.maps.projection import Projection

log = logging.getLogger(__name__)

Clip = tuple[float, float, float, float]

#: A ring needs more points than this to be kept.
RING_POINTS_OVER = 3

#: Metres within which two coastline ways are joined into one chain.
JOIN_TOL_M = 2.0

#: Chains shorter than this are offshore rocks, in metres.
MIN_COAST_M = 300.0

#: OSM tag to pigment class. An element that matches on more than one key takes
#: the class of the last of `landuse`, `natural` and `leisure` that matches.
COVER_TAGS: tuple[tuple[str, str, str], ...] = (
    ("landuse", "farmland", "farmland"),
    ("landuse", "farmyard", "built"),
    ("landuse", "meadow", "meadow"),
    ("landuse", "grass", "meadow"),
    ("landuse", "village_green", "meadow"),
    ("landuse", "recreation_ground", "meadow"),
    ("leisure", "park", "meadow"),
    ("leisure", "garden", "meadow"),
    ("leisure", "pitch", "meadow"),
    ("leisure", "golf_course", "meadow"),
    ("natural", "grassland", "meadow"),
    ("landuse", "orchard", "orchard"),
    ("landuse", "vineyard", "orchard"),
    ("landuse", "allotments", "orchard"),
    ("natural", "scrub", "scrub"),
    ("leisure", "nature_reserve", "scrub"),
    ("natural", "heath", "heath"),
    ("natural", "moor", "heath"),
    ("natural", "beach", "sand"),
    ("natural", "sand", "sand"),
    ("natural", "shingle", "sand"),
    ("natural", "bare_rock", "rock"),
    ("natural", "scree", "rock"),
    ("natural", "cliff", "rock"),
    ("natural", "wetland", "wetland"),
    ("landuse", "residential", "built"),
    ("landuse", "commercial", "built"),
    ("landuse", "retail", "built"),
    ("landuse", "cemetery", "built"),
    ("landuse", "industrial", "works"),
    ("landuse", "quarry", "works"),
    ("landuse", "greenhouse_horticulture", "works"),
    ("landuse", "forest", "wood"),
    ("natural", "wood", "wood"),
)

#: Painting order, low to high. A later class replaces an earlier one where they
#: overlap, so the plate carries one class per pixel and no two land pigments stack.
COVER_ORDER: tuple[str, ...] = (
    "farmland",
    "meadow",
    "orchard",
    "scrub",
    "heath",
    "sand",
    "rock",
    "wetland",
    "built",
    "works",
    "wood",
)


def cover_rings(
    key: str, proj: Projection, clip: Clip, eps: float, cache: Cache
) -> dict[str, list[list[Pt]]]:
    """Land cover rings by pigment class, clipped to the card and simplified.

    Args:
        key: The track's cache key, naming the cache file.
        proj: The track's projection.
        clip: The card, in metres.
        eps: Simplification tolerance in metres.
        cache: Where the payload lives.

    Returns:
        Rings by class; empty when there is no land cover cached.
    """
    path = cache.landcover_path(key)
    out: dict[str, list[list[Pt]]] = {}
    if not path.exists():
        return out
    lookup = {(key, value): cls for key, value, cls in COVER_TAGS}
    payload = json.loads(path.read_text())
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        cls = None
        for tag_key in ("landuse", "natural", "leisure"):
            if tag_key in tags:
                cls = lookup.get((tag_key, tags[tag_key]), cls)
        if cls is None:
            continue
        outer, _inner = polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > RING_POINTS_OVER:
                out.setdefault(cls, []).append(simplify(cut, eps))
    return out


def wood_rings(key: str, proj: Projection, clip: Clip, eps: float, cache: Cache) -> list[list[Pt]]:
    """Wood rings from the cached feature payload, clipped to the card and simplified."""
    path = cache.features_path(key)
    rings: list[list[Pt]] = []
    if not path.exists():
        return rings
    for entry in json.loads(path.read_text()).get("elements", []):
        tags = entry.get("tags") or {}
        if tags.get("landuse") != "forest" and tags.get("natural") != "wood":
            continue
        outer, _ = polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > RING_POINTS_OVER:
                rings.append(simplify(cut, eps))
    return rings


def _chain_length(chain: list[Pt]) -> float:
    """The length of a chain, vertex by vertex."""
    return sum(math.dist(chain[i], chain[i + 1]) for i in range(len(chain) - 1))


def coastline_chains(
    key: str,
    proj: Projection,
    clip: Clip,
    cache: Cache,
    min_length_m: float = MIN_COAST_M,
) -> list[list[Pt]]:
    """Coastline ways as surveyed: clipped, joined, and never smoothed.

    The coast is the one line on the map a reader would notice being wrong,
    so it keeps its own vertices. Offshore rocks come back as their own
    little rings and are ink specks at plate size, so only chains of real coast
    are kept.
    """
    path = cache.features_path(key)
    if not path.exists():
        return []
    ways: list[list[Pt]] = []
    for entry in json.loads(path.read_text()).get("elements", []):
        if (entry.get("tags") or {}).get("natural") != "coastline":
            continue
        pts = [proj(g["lat"], g["lon"]) for g in entry.get("geometry", []) if g]
        ways += [p for p in clip_line(pts, clip) if len(p) > 1]
    joined = [c for c in join_chains(ways, tol=JOIN_TOL_M) if len(c) > RING_POINTS_OVER]
    return [c for c in joined if _chain_length(c) > min_length_m]
