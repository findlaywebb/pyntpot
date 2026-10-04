"""The Lynmouth fixture as the candidates read it: the track, its line and the payload."""

import json
from typing import Any, NamedTuple

import pytest

from pyntpot.maps.basemap import Line
from pyntpot.maps.projection import Projection, track_projection
from pyntpot.maps.track import Track

from support.paths import FIXTURE_DIR, KEY


class Lynmouth(NamedTuple):
    """The fixture track, its projection and line, and its cached Overpass payload."""

    track: Track
    projection: Projection
    line: Line
    payload: dict[str, Any]


@pytest.fixture(scope="module")
def lynmouth() -> Lynmouth:
    """The parsed fixture, built once per module: it is never mutated."""
    track = Track.from_gpx(FIXTURE_DIR / "track.gpx")
    projection, pts = track_projection(list(track.lat), list(track.lng))
    payload = json.loads((FIXTURE_DIR / f"overpass-{KEY}.json").read_text())
    return Lynmouth(track, projection, tuple(pts), payload)
