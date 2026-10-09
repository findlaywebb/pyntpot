"""The candidate export: what a track passes, for a caller to choose names from.

Key names: `candidate_export`, one track's route totals, the settlements it passed,
each climb grounded in that route, and every landmark candidate beside it;
`CANDIDATE_BASEMAP`, the basemap style the export draws the landmarks with;
`CANDIDATE_CLIP_MARGIN_M`, the ground kept round the track for them.

Nothing here chooses a landmark. It states what the box holds, where the track
climbed, how hard each climb was and what the route passed on the way up it; which of
them is worth a label, and what to call it, is the caller's judgement.

It sits above the layer assembly, so no candidates module imports it; `pyntpot.maps`
exports `candidate_export`. It does not fetch anything: a box with nothing cached has no
landmarks, no settlements, and climbs that are not grounded. Invariants: the export is
a plain dictionary of numbers and strings; `climbs` are in the order of the route.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from pyntpot.ink.polyline import simplify
from pyntpot.maps.candidates.climbs import cumulative, rank_climbs
from pyntpot.maps.candidates.landmark_classes import LANDMARK_CAP
from pyntpot.maps.candidates.landmarks import rank_landmarks
from pyntpot.maps.candidates.places import ground_climbs, place_view, rank_places
from pyntpot.maps.candidates.roads import named_roads
from pyntpot.maps.layers import BasemapInputs, basemap
from pyntpot.maps.projection import track_projection
from pyntpot.maps.style_groups import BasemapStyle

if TYPE_CHECKING:
    from pyntpot.maps.cache import Cache
    from pyntpot.maps.track import Track

#: What the export draws: every landmark, no relief, no generalisation.
CANDIDATE_BASEMAP = replace(
    BasemapStyle(),
    hillshade_mode="off",
    landmarks="all",
    landmark_max=LANDMARK_CAP,
    generalise=False,
)

#: Metres of ground kept around the track's bounding box for the candidates.
CANDIDATE_CLIP_MARGIN_M = 2600.0

#: The track is simplified to this tolerance, in metres, before the candidates are placed.
ROUTE_EPS_M = 3.0

#: Metres in a kilometre.
KM = 1000


def candidate_export(track: Track, cache: Cache, key: str) -> dict[str, Any]:
    """What a track passes, for a caller to choose names from.

    It reads only the payloads cached under `key`. It chooses nothing and fetches
    nothing: a box with nothing cached has no candidates, no settlements and climbs
    that are not grounded. The export is a plain dictionary of numbers and strings,
    fresh on every call and the caller's to change; `climbs` are in the order of the
    route.

    Args:
        track: The recorded track; its elevations, when it carries them, find the
            climbs.
        cache: The fetch cache the payloads are read from.
        key: The fetch cache's key for this track and the providers that filled it. It
            must be the track's: a key for another box reads that box's payloads.

    Returns:
        `id` (the cache key), `points` (the track's point count), `route`
        (`total_km`, `sustained_ascent_m` and `settlements`, the settlements it
        passed in order, each with `name`, `kind`, `km` and `off_route_m`), `climbs`
        (each grounded in that route, with `approach_trimmed_km`, `avg_grade_pct`,
        `bearing_deg`, `bottom_ele_m`, `end_km`, `end_lat`, `end_lng`, `features`,
        `from`, `gain_m`, `heading`, `length_km`, `near_start`, `near_top`,
        `of_climbs`, `position_pct`, `rank_by_gain`, `rank_by_steepness`, `roads`,
        `runout_trimmed_km`, `share_of_climbing_pct`, `start_km`, `start_lat`,
        `start_lng`, `steepest_500m_km`, `steepest_500m_pct`, `through`, `to` and
        `top_ele_m`) and `candidates` (each landmark beside the track, with `class`,
        `distance_m`, `lat`, `lng`, `name`, `notable`, `reach_m`, `tags`, `x` and
        `y`).
    """
    inputs = BasemapInputs(key, track, cache, [])
    lat, lng = list(track.lat), list(track.lng)
    proj, pts = track_projection(lat, lng)
    line = tuple(pts)
    dist = cumulative(lat, lng)
    found = rank_climbs(track, line)
    landmarks = []
    base = basemap(
        inputs,
        CANDIDATE_BASEMAP,
        route=simplify(pts, ROUTE_EPS_M),
        clip_margin_m=CANDIDATE_CLIP_MARGIN_M,
    )
    if base is not None:
        landmarks = rank_landmarks(base.get("landmark_candidates", []), proj)
    settlements = []
    payload_path = inputs.cache.features_path(inputs.key)
    if payload_path.exists():
        payload = json.loads(payload_path.read_text())
        passed = rank_places(payload, proj, track, line)
        settlements = [place_view(p.detail) for p in passed]
        found = ground_climbs(found, passed, landmarks, named_roads(payload, proj), track, line)
    return {
        "id": inputs.key,
        "points": len(lat),
        "route": {
            "total_km": round(dist[-1] / KM, 2) if dist else 0.0,
            # Not the track's ascent: raw GPX sample-to-sample gain runs well
            # above the recorded figure, so the only climbing figure stated here
            # is the one this module actually defines.
            "sustained_ascent_m": round(sum(c.detail["gain_m"] for c in found)),
            "settlements": settlements,
        },
        "climbs": [dict(c.detail) for c in found],
        "candidates": [dict(c.detail) for c in landmarks],
    }
