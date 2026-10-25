"""The sea of a card, made from its coastline chains.

Key name: `sea_from_coast`, the card area outside every land region as rings that fill
with the nonzero rule: the card edge wound anticlockwise, and each land region wound
against it so that it cuts a hole.

OSM draws a coastline with the land on its left, so land is anticlockwise round a closed
ring (an island or an islet) and an open chain that crosses the card has land on its
left and sea on its right. A closed ring is a land region as it stands. Open chains are
joined end to start walking the card edge anticlockwise, which closes each landmass the
card cuts through, however many chains it takes. Where the winding is wrong in the
payload the chains are reversed whole, decided by probes just off the coast.

It does not fetch or clip a coast (see `cover.coastline_chains`) and does not paint. A
card with one open chain and no closed ring keeps the single closure ring round the sea
side that the painters have always had. A chain that neither closes nor reaches the card
edge at both ends is left out.
"""

from __future__ import annotations

import math

from pyntpot.ink.polyline import Pt, length
from pyntpot.maps.cover import JOIN_TOL_M, RING_POINTS_OVER, Clip
from pyntpot.maps.rings import point_in_ring

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


def _single_closure(chain: list[Pt], clip: Clip) -> list[list[Pt]]:
    """The sea side of one open chain, closed round the card edge.

    Both closures round the card are built and the one that holds most of a set of
    probes just off the coast is the sea: one probe is not enough, because a cove puts a
    single right-hand normal back on land.
    """
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


def _land_rings(opens: list[list[Pt]], closed: list[list[Pt]], clip: Clip) -> list[list[Pt]]:
    """Land regions, anticlockwise: closed rings as they are, open chains joined along the edge.

    Walking the card edge anticlockwise from where a chain leaves the card, the next
    chain to enter is the one the land boundary carries on along.
    """
    rings = [list(ring) for ring in closed]
    ends = [_perimeter_t(c[-1], clip) for c in opens]
    starts = [_perimeter_t(c[0], clip) for c in opens]
    follow = [min(range(len(opens)), key=lambda j, t=t: (starts[j] - t) % SIDES) for t in ends]
    seen: set[int] = set()
    for first in range(len(opens)):
        ring: list[Pt] = []
        path: list[int] = []
        i = first
        while i not in seen and i not in path:
            path.append(i)
            ring += opens[i] + _arc(ends[i], starts[follow[i]], clip, forward=True)
            i = follow[i]
        seen.update(path)
        if i == first and len(ring) > RING_POINTS_OVER:
            rings.append(ring)
    return rings


def _share_in_sea(chains: list[list[Pt]], land: list[list[Pt]]) -> float:
    """The share of probes just right of the chains that lie outside every land region."""
    probes = [p for c in chains for p in _probes(c)]
    if not probes:
        return 0.0
    dry = sum(1 for p in probes if sum(point_in_ring(p[0], p[1], r) for r in land) % 2 == 0)
    return dry / len(probes)


def sea_from_coast(chains: list[list[Pt]], clip: Clip) -> list[list[Pt]]:
    """The card area outside every land region, as rings that fill by the nonzero rule.

    Land regions are the closed coastline rings (islands and islets, anticlockwise
    around land) and the land side of the open chains that cross the card, joined along
    the card edge. A card with one open chain and no closed ring gets the one ring round
    the sea side of the chain. Otherwise the result is the card edge, anticlockwise,
    then every land region wound clockwise; a landmass inside another, such as an
    island in a lagoon, nests by winding. The chains are taken as they are if most of the
    probes just right of them are outside the land they make, else reversed whole, else
    there is no sea.

    Args:
        chains: Coastline chains in metres, already clipped to the card.
        clip: The card, in metres.

    Returns:
        The sea rings, or an empty list when no chain is a coast of the card or the
        winding agrees with the probes neither way.
    """
    opens = [
        c
        for c in chains
        if len(c) > RING_POINTS_OVER
        and _edge_gap(c[0], clip) < EDGE_GAP_M
        and _edge_gap(c[-1], clip) < EDGE_GAP_M
        and math.dist(c[0], c[-1]) >= JOIN_TOL_M
    ]
    opens = [[_snap(c[0], clip), *c[1:-1], _snap(c[-1], clip)] for c in opens]
    closed = [
        c for c in chains if len(c) > RING_POINTS_OVER and math.dist(c[0], c[-1]) < JOIN_TOL_M
    ]
    if len(opens) == 1 and not closed:
        return _single_closure(max(opens, key=length), clip)
    if not opens and not closed:
        return []
    xmin, ymin, xmax, ymax = clip
    card = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]
    for flip in (False, True):
        o = [c[::-1] for c in opens] if flip else opens
        k = [c[::-1] for c in closed] if flip else closed
        land = _land_rings(o, k, clip)
        if land and _share_in_sea([*o, *k], land) > SEA_SHARE:
            return [card, *(ring[::-1] for ring in land)]
    return []
