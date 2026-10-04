"""Land cover, wood and coast rings from the cached Overpass payloads.

Key names: `cover_rings`, the land cover polygons by pigment class, clipped to the card
and simplified; `wood_rings`, the woods of the feature payload; `coastline_chains`, the
coast as surveyed, joined and never smoothed; `sea_from_coast`, one coastline closed
round the card edge into the sea; `COVER_TAGS` and `COVER_ORDER`, the tag-to-pigment
table and the painting order.

It does not fetch payloads, project a track, or paint anything: it reads the files the
cache already holds and returns rings in route metres. Invariants: a missing payload
is an empty result, never an error; the coast keeps its own vertices; a later entry of
`COVER_TAGS` wins where two polygons overlap, so a plate carries one class per pixel.
"""

from __future__ import annotations

import json
import logging
import math
from typing import TYPE_CHECKING

from pyntpot.ink.chains import join_chains
from pyntpot.ink.polyline import Pt, clip_line, simplify
from pyntpot.maps.osm_elements import _polygon_rings
from pyntpot.maps.rings import clip_ring, point_in_ring

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

#: A chain end this close to the card edge, in metres, was clipped by it.
EDGE_GAP_M = 30.0

#: How far off the coast the sea probes are set, in metres, and into how many steps
#: along the chain they are spread.
PROBE_OFFSET_M = 70.0
PROBE_STEPS = 20

#: The card edge is walked as four sides, and a closure passes at most this many corners.
SIDES = 4
CORNERS_PASSED = 5

#: The distance below which a point is on an edge, in metres, and the gap below which a
#: walk along the edge has reached its corner.
EDGE_EPS = 1e-6
CORNER_EPS = 1e-9

#: The share of the probes the chosen closure has to hold.
SEA_SHARE = 0.5


#: OSM tag to pigment class. Later in this list wins where two polygons overlap,
#: so the plate carries one class per pixel and no two land pigments can stack.
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

#: Painting order, low to high. A wood drawn over farmland replaces it.
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
        key: The activity, naming the cache file.
        proj: The activity's projection.
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
        outer, _inner = _polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > RING_POINTS_OVER:
                out.setdefault(cls, []).append(simplify(cut, eps))
    return out


def wood_rings(key: str, proj: Projection, clip: Clip, eps: float, cache: Cache) -> list[list[Pt]]:
    """Wood rings straight from the renderer's own Overpass cache."""
    path = cache.features_path(key)
    rings: list[list[Pt]] = []
    if not path.exists():
        return rings
    for entry in json.loads(path.read_text()).get("elements", []):
        tags = entry.get("tags") or {}
        if tags.get("landuse") != "forest" and tags.get("natural") != "wood":
            continue
        outer, _ = _polygon_rings(entry, proj)
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

    The coast is the one line on the sheet a reader would notice being wrong,
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


def _perimeter_t(p: Pt, clip: Clip) -> float:
    """Position of a point on the card edge, 0 to 4, anticlockwise."""
    xmin, ymin, xmax, ymax = clip
    x, y = p
    if abs(y - ymin) < EDGE_EPS:
        return (x - xmin) / max(xmax - xmin, EDGE_EPS)
    if abs(x - xmax) < EDGE_EPS:
        return 1 + (y - ymin) / max(ymax - ymin, EDGE_EPS)
    if abs(y - ymax) < EDGE_EPS:
        return 2 + (xmax - x) / max(xmax - xmin, EDGE_EPS)
    return 3 + (ymax - y) / max(ymax - ymin, EDGE_EPS)


def _arc(t0: float, t1: float, clip: Clip, *, forward: bool) -> list[Pt]:
    """The card corners passed walking the edge from t0 to t1."""
    xmin, ymin, xmax, ymax = clip
    corners = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    out: list[Pt] = []
    t = t0
    for _ in range(CORNERS_PASSED):
        nxt = (math.floor(t) + 1) if forward else (math.ceil(t) - 1)
        gap = (nxt - t) % SIDES if forward else (t - nxt) % SIDES
        want = (t1 - t) % SIDES if forward else (t - t1) % SIDES
        if gap >= want or gap <= CORNER_EPS:
            break
        out.append(corners[int(nxt) % SIDES])
        t = nxt % SIDES
    return out


def _edge_gap(p: Pt, clip: Clip) -> float:
    """How far a point is from the nearest card edge."""
    xmin, ymin, xmax, ymax = clip
    return min(abs(p[0] - xmin), abs(p[0] - xmax), abs(p[1] - ymin), abs(p[1] - ymax))


def _snap(p: Pt, clip: Clip) -> Pt:
    """Put an endpoint exactly on the card edge it was clipped against."""
    xmin, ymin, xmax, ymax = clip
    x, y = p
    gaps = [
        (abs(x - xmin), (xmin, y)),
        (abs(x - xmax), (xmax, y)),
        (abs(y - ymin), (x, ymin)),
        (abs(y - ymax), (x, ymax)),
    ]
    return min(gaps)[1]


def _probes(chain: list[Pt]) -> list[Pt]:
    """Points just to the right of the coast, where the sea is."""
    probes: list[Pt] = []
    for k in range(1, PROBE_STEPS):
        i = max(min(len(chain) * k // PROBE_STEPS, len(chain) - 2), 0)
        dx, dy = chain[i + 1][0] - chain[i][0], chain[i + 1][1] - chain[i][1]
        n = math.hypot(dx, dy)
        if n < EDGE_EPS:
            continue
        probes.append(
            (chain[i][0] + dy / n * PROBE_OFFSET_M, chain[i][1] - dx / n * PROBE_OFFSET_M)
        )
    return probes


def sea_from_coast(chains: list[list[Pt]], clip: Clip) -> list[list[Pt]]:
    """Close a coastline chain around the card edge to make the sea.

    OSM draws a coastline with the land on its left, so the sea is the side the
    right-hand normal points at. Both closures round the card are built and the
    one that holds most of a set of probes just off the coast is the sea: one
    probe is not enough, because a cove puts a single right-hand normal back on
    land.

    Args:
        chains: Coastline chains in metres, already clipped to the card.
        clip: The card, in metres.

    Returns:
        One closed ring, or an empty list when no chain crosses the card.
    """
    open_chains = [
        c
        for c in chains
        if len(c) > RING_POINTS_OVER
        and _edge_gap(c[0], clip) < EDGE_GAP_M
        and _edge_gap(c[-1], clip) < EDGE_GAP_M
    ]
    open_chains = [[_snap(c[0], clip), *c[1:-1], _snap(c[-1], clip)] for c in open_chains]
    if not open_chains:
        return []
    chain = max(open_chains, key=_chain_length)
    probes = _probes(chain)
    t0, t1 = _perimeter_t(chain[-1], clip), _perimeter_t(chain[0], clip)
    best: list[Pt] | None = None
    best_score = -1
    for forward in (True, False):
        ring = chain + _arc(t0, t1, clip, forward=forward)
        if len(ring) <= RING_POINTS_OVER:
            continue
        score = sum(1 for p in probes if point_in_ring(p[0], p[1], ring))
        if score > best_score:
            best, best_score = ring, score
    if best is None or best_score <= len(probes) * SEA_SHARE:
        return []
    return [best]
