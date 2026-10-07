"""The candidate export: what a track passes, for a caller to choose names from.

Key names: `landmark_export`, one activity's route totals, the settlements it passed,
each climb grounded in that route, and every landmark candidate beside it;
`CANDIDATE_BASEMAP`, the basemap style the export draws the landmarks with;
`CANDIDATE_CLIP_MARGIN_M`, the ground kept round the track for them.

Nothing here chooses a landmark. It states what the box holds, where the track
climbed, how hard each climb was and what the route passed on the way up it; which of
them is worth a label, and what to call it, is the caller's judgement.

It sits above the layer assembly, so no candidates module imports it and the package
does not export it. It does not fetch anything: a box with nothing cached has no
landmarks, no settlements, and climbs that are not grounded. Invariants: the export is
a plain dictionary of numbers and strings; `climbs` are in the order of the route.
"""

from __future__ import annotations

import json
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from pyntpot.ink.polyline import Pt, simplify
from pyntpot.maps.candidates.climbs import cumulative, rank_climbs
from pyntpot.maps.candidates.landmark_classes import LANDMARK_CAP
from pyntpot.maps.candidates.landmarks import rank_landmarks
from pyntpot.maps.candidates.places import ground_climbs, place_view, rank_places
from pyntpot.maps.candidates.roads import named_roads
from pyntpot.maps.layers import basemap
from pyntpot.maps.projection import track_projection
from pyntpot.maps.style_groups import BasemapStyle

if TYPE_CHECKING:
    from pyntpot.maps.layers import BasemapInputs

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


def landmark_export(inputs: BasemapInputs, route: list[Pt] | None = None) -> dict[str, Any]:
    """What the caller reads: where the track went, and what is beside it.

    Args:
        inputs: The activity, its track (with elevations, when the GPX carries
            them), its cache and its places.
        route: The already-projected track, when the caller has one.

    Returns:
        `id` (the cache key), `points` (the track's point count), `route` (the
        track's totals and the settlements it passed, in order), `climbs` (each
        grounded in that route) and `candidates`.
    """
    track = inputs.track
    lat, lng = list(track.lat), list(track.lng)
    proj, pts = track_projection(lat, lng, route)
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
