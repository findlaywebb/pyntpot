"""Places: the settlements a route ran past, and the grounding of climbs in them.

Key names: `rank_places`, every settlement the route came near, in the order it
passed them; `ground_climbs`, which gives each climb the language a rider would
use for it; `place_view`, one settlement as the label step reads it.

A settlement is a `city`, `town`, `village`, `hamlet` or `suburb` node with a
name that the route came within `NEAR_ROUTE_M` of. This is the vocabulary a
rider uses for a climb: out of one village, up to the next. A straight-line
nearest place is not that, and picking one is how a climb gets named after
somewhere the route never went.

Settlements are read from the raw payload, which carries every place node, not
from the basemap. This module does not fetch the payload, rank climbs or
landmarks (it is handed them) or choose a name; a climb with nothing grounded is
honestly nameless. Invariants: `ground_climbs` returns new climbs and leaves its
input untouched; every grounding carries its own distance, so a settlement
kilometres behind the foot cannot be read as where the climb starts.
"""

import math
from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

from pyntpot.maps.basemap import Line
from pyntpot.maps.candidates.candidate import Candidate
from pyntpot.maps.candidates.climbs import bearing, compass, cumulative, haversine
from pyntpot.maps.candidates.roads import rank_roads
from pyntpot.maps.projection import Projection
from pyntpot.maps.track import Track

#: The `place` values that are a settlement.
SETTLEMENTS = ("city", "town", "village", "hamlet", "suburb")

#: How near the route a settlement has to come to count.
NEAR_ROUTE_M = 700.0

#: How near a climb a named feature has to be to be offered.
FEATURE_M = 600.0

#: A settlement this near the foot or the top, measured along the route, belongs
#: to that end rather than to the middle of the climb. A village at the bottom of
#: a hill is what the climb is out of, and a few metres either side of the first
#: pedal stroke should not decide that. `km_before_climb` and `km_after_top` go
#: slightly negative when it does, which is the honest reading: the route
#: reached it just inside the climb.
FOOT_M = 300.0

#: How many named features and nearest settlements a climb carries.
FEATURES_KEPT = 4
NEAREST_KEPT = 3

#: The keys of a settlement as the label step reads it.
VIEW_KEYS = ("name", "kind", "km", "off_route_m")


def _nearest_sample(line: Line, gx: float, gy: float) -> tuple[float, int]:
    """The distance to a point from the nearest track sample, and that sample."""
    best, at = math.inf, 0
    for i, (px, py) in enumerate(line):
        gap = math.hypot(px - gx, py - gy)
        if gap < best:
            best, at = gap, i
    return best, at


def rank_places(
    payload: Mapping[str, Any], projection: Projection, track: Track, line: Line
) -> list[Candidate]:
    """Every settlement the route ran past, in the order it passed them.

    Args:
        payload: The cached Overpass payload.
        projection: The track's projection into card metres.
        track: The track, for the metres travelled at each sample.
        line: The track in card metres, one point per track sample.

    Returns:
        One candidate per settlement within `NEAR_ROUTE_M` of the route, ranked
        by where the route came closest to it. `at_m` is the metres travelled
        there, `where` the settlement in card metres and `span` the nearest
        sample twice. `detail` is `{"name", "kind", "km", "off_route_m", "lat",
        "lng"}`.
    """
    dist = cumulative(track.lat, track.lng)
    found: list[tuple[int, Candidate]] = []
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        kind = tags.get("place", "")
        if kind not in SETTLEMENTS or not tags.get("name"):
            continue
        where = projection(entry["lat"], entry["lon"])
        gap, at = _nearest_sample(line, *where)
        if gap > NEAR_ROUTE_M:
            continue
        detail = {
            "name": tags["name"],
            "kind": kind,
            "km": round(dist[at] / 1000, 2),
            "off_route_m": round(gap),
            "lat": entry["lat"],
            "lng": entry["lon"],
        }
        found.append((at, Candidate("place", tags["name"], 0, dist[at], where, (at, at), detail)))
    found.sort(key=lambda row: row[0])
    return [replace(cand, rank=rank) for rank, (_at, cand) in enumerate(found, start=1)]


def place_view(place: Mapping[str, Any], keys: Sequence[str] = VIEW_KEYS) -> dict[str, Any]:
    """One settlement's row as the label step sees it, without its coordinates."""
    return {k: place[k] for k in keys}


def _near_places(places: Sequence[Candidate], plat: float, plng: float) -> list[dict[str, Any]]:
    """The nearest settlements to one point, with how far and which way."""
    ranked = sorted(
        ((haversine(plat, plng, p.detail["lat"], p.detail["lng"]), p) for p in places),
        key=lambda row: row[0],
    )[:NEAREST_KEPT]
    return [
        {
            "name": p.name,
            "kind": p.detail["kind"],
            "distance_m": round(gap),
            "direction": compass(bearing(plat, plng, p.detail["lat"], p.detail["lng"])),
        }
        for gap, p in ranked
    ]


def _ends(places: Sequence[Candidate], dist: Sequence[float], a: int, b: int) -> dict[str, Any]:
    """Where the route was before the climb, through it, and after it: `from`, `through`, `to`."""
    along = [(dist[p.span[0]], p) for p in places if p.span]
    foot, top = dist[a] + FOOT_M, dist[b] - FOOT_M
    before = [(m, p) for m, p in along if m <= foot]
    inside = [p for m, p in along if foot < m < top]
    after = [(m, p) for m, p in along if m >= top]
    return {
        "from": (
            {
                **place_view(before[-1][1].detail),
                "km_before_climb": round((dist[a] - before[-1][0]) / 1000, 2),
            }
            if before
            else None
        ),
        "through": [place_view(p.detail) for p in inside],
        "to": (
            {
                **place_view(after[0][1].detail),
                "km_after_top": round((after[0][0] - dist[b]) / 1000, 2),
            }
            if after
            else None
        ),
    }


def _features(landmarks: Sequence[Candidate], stretch: Line) -> list[dict[str, Any]]:
    """The nearest named features within `FEATURE_M` of a stretch of track."""
    features = []
    for cand in landmarks:
        row = cand.detail
        if row["class"] == "place" or row["x"] is None:
            continue
        gap = min(math.hypot(row["x"] - px, row["y"] - py) for px, py in stretch)
        if gap <= FEATURE_M:
            features.append({"name": row["name"], "class": row["class"], "distance_m": round(gap)})
    features.sort(key=lambda f: f["distance_m"])
    return features[:FEATURES_KEPT]


def ground_climbs(
    climbs: Sequence[Candidate],
    places: Sequence[Candidate],
    landmarks: Sequence[Candidate],
    roads: Sequence[Mapping[str, Any]],
    track: Track,
    line: Line,
) -> list[Candidate]:
    """Give every climb the language a rider would use for it.

    Four grounds, in the order they are worth having: where the route was before
    the climb and where it got to after it (`from`, `through`, `to`), the roads
    the climb runs on, the settlements nearest each end whichever way the route
    went, and any named feature beside the climb itself. None of them is a
    template to fill in. A climb with nothing but `from` and `to` is still
    nameable; a climb with none of them is honestly nameless and says so.

    Args:
        climbs: `rank_climbs` output.
        places: `rank_places` output.
        landmarks: `rank_landmarks` output.
        roads: `named_roads` output.
        track: The track, for the metres travelled at each sample.
        line: The track in card metres, one point per track sample.

    Returns:
        New climb candidates, in the order given, whose `detail` gains `from`,
        `through`, `to`, `near_start`, `near_top`, `roads` and `features`. The
        input is not changed.
    """
    dist = cumulative(track.lat, track.lng)
    out = []
    for climb in climbs:
        if climb.span is None:
            raise ValueError("a climb to ground needs its span")
        a, b = climb.span
        row = climb.detail
        grounds = {
            **_ends(places, dist, a, b),
            "near_start": _near_places(places, row["start_lat"], row["start_lng"]),
            "near_top": _near_places(places, row["end_lat"], row["end_lng"]),
            "roads": [c.detail for c in rank_roads(roads, line, dist, (a, b))],
            "features": _features(landmarks, line[a : b + 1] or line[a : a + 1]),
        }
        out.append(replace(climb, detail={**row, **grounds}))
    return out
