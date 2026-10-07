"""Named roads: which roads a stretch of track runs along, longest first.

Key names: `named_roads`, every named or numbered road in a cached Overpass
payload projected into card metres; `rank_roads`, the roads one stretch of the
track runs along as candidates.

Roads are read from the raw payload, never from the painted strokes: the painted
roads are chained and simplified to the drawing tolerance, so a run measured
along them gives different metres. A road counts as run along where the track
comes within `SNAP_M` of it, sampled every `STEP_M`, and a road run for under
`MIN_RUN_M` is dropped.

It does not fetch the payload, draw roads, or name a stretch; the caller picks
from the ranking. Invariants: the ranking is longest run first, and each
candidate's `span` is the stretch that was asked about.
"""

import math
from collections.abc import Mapping, Sequence
from itertools import pairwise
from typing import Any

from pyntpot.ink.polyline import Pt
from pyntpot.maps.basemap import Line
from pyntpot.maps.candidates.candidate import Candidate
from pyntpot.maps.projection import Projection

#: Side of one cell of the index that finds the roads near a track point.
CELL_M = 200.0

#: How near a road has to be to count as the road being run along.
SNAP_M = 25.0

#: How often along the stretch to ask which road it is on.
STEP_M = 50.0

#: The least run, in metres, that makes a road worth ranking.
MIN_RUN_M = 100.0

#: The fewest points a way needs to be a line.
MIN_POINTS = 2

Index = dict[tuple[int, int], list[int]]


def named_roads(payload: Mapping[str, Any], projection: Projection) -> list[dict[str, Any]]:
    """Every named or numbered road in the cached OSM payload, projected.

    A road number is often the name a rider gives a climb, so a road with no
    name but a `ref` is named by it. Ways with fewer than two points are left
    out.

    Args:
        payload: The cached Overpass payload.
        projection: The track's projection into card metres.

    Returns:
        One row per road: `name`, `ref`, `kind` (the `highway` value) and `pts`.
    """
    out = []
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        if not tags.get("highway"):
            continue
        name = tags.get("name") or tags.get("ref")
        geom = entry.get("geometry") or []
        if not name or len(geom) < MIN_POINTS:
            continue
        out.append(
            {
                "name": name,
                "ref": tags.get("ref", ""),
                "kind": tags["highway"],
                "pts": [projection(p["lat"], p["lon"]) for p in geom],
            }
        )
    return out


def _cell_index(roads: Sequence[Mapping[str, Any]]) -> Index:
    """Which roads touch which grid cell, so a point only tests its neighbours."""
    grid: Index = {}
    for wi, way in enumerate(roads):
        pts = way["pts"]
        for (ax, ay), (bx, by) in pairwise(pts):
            steps = int(math.hypot(bx - ax, by - ay) // CELL_M) + 1
            for s in range(steps + 1):
                t = s / steps
                key = (int((ax + (bx - ax) * t) // CELL_M), int((ay + (by - ay) * t) // CELL_M))
                bucket = grid.setdefault(key, [])
                if not bucket or bucket[-1] != wi:
                    bucket.append(wi)
    return grid


def _point_to_line(px: float, py: float, pts: Sequence[Pt]) -> float:
    """Metres from a point to a polyline."""
    best = math.inf
    for (ax, ay), (bx, by) in pairwise(pts):
        vx, vy = bx - ax, by - ay
        square = vx * vx + vy * vy
        t = 0.0 if square == 0 else max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / square))
        best = min(best, math.hypot(px - (ax + t * vx), py - (ay + t * vy)))
    return best


def _road_at(roads: Sequence[Mapping[str, Any]], grid: Index, point: Pt) -> str | None:
    """The name of the nearest road within `SNAP_M` of a point, or `None`."""
    px, py = point
    cx, cy = int(px // CELL_M), int(py // CELL_M)
    near: set[int] = set()
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            near.update(grid.get((cx + dx, cy + dy), ()))
    best = SNAP_M
    hit: str | None = None
    for wi in near:
        gap = _point_to_line(px, py, roads[wi]["pts"])
        if gap < best:
            best, hit = gap, str(roads[wi]["name"])
    return hit


def _road_run(
    roads: Sequence[Mapping[str, Any]],
    grid: Index,
    line: Line,
    dist: Sequence[float],
    a: int,
    b: int,
) -> list[dict[str, Any]]:
    """The named roads the track samples `a` to `b` run along, longest first."""
    metres: dict[str, float] = {}
    order: list[str] = []
    i, last = a, a
    while i <= b:
        hit = _road_at(roads, grid, line[i])
        if hit:
            metres[hit] = metres.get(hit, 0.0) + (dist[i] - dist[last])
            if not order or order[-1] != hit:
                order.append(hit)
        last = i
        if i == b:
            break
        while i < b and dist[i] - dist[last] < STEP_M:
            i += 1
    ranked = sorted(metres.items(), key=lambda kv: -kv[1])
    return [
        {"name": name, "metres": round(run), "order": order.index(name) + 1}
        for name, run in ranked
        if run >= MIN_RUN_M
    ]


def rank_roads(
    roads: Sequence[Mapping[str, Any]],
    line: Line,
    dist: Sequence[float],
    span: tuple[int, int],
) -> list[Candidate]:
    """The named roads one stretch of track runs along, longest first.

    Args:
        roads: `named_roads` output.
        line: The whole track in card metres.
        dist: Cumulative metres at each track point.
        span: The first and last track sample of the stretch.

    Returns:
        One candidate per road run for at least `MIN_RUN_M`, ranked by metres
        run. `detail` is `{"name", "metres", "order"}`, where `order` is the
        order the stretch met the roads in; `at_m` and `where` are `None`.
    """
    if not roads:
        return []
    rows = _road_run(roads, _cell_index(roads), line, dist, *span)
    return [
        Candidate(
            kind="road", name=row["name"], rank=rank, at_m=None, where=None, span=span, detail=row
        )
        for rank, row in enumerate(rows, start=1)
    ]
