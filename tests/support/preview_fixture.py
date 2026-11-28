"""Helpers the preview fixture's tests share: its committed files, in metres and as a basemap.

Key types: `PREVIEW_DIR`, the committed fixture; `CONTACT`, the caller name the offline
providers carry; `committed_payload`, `committed_elements`, `tagged` (the committed Overpass
and land cover payloads); `committed_track` and `to_metres` (the route and any geometry in the
generator's metres); `copy_fixture` and `fetch_preview` (a cache the providers cannot refill,
and the basemap fetched from it in a theme at a card width).

Invariants: every helper reads the committed fixture and never writes it; `copy_fixture` copies
it before any test fetches, so a fetch cannot change the committed files. It makes no request
and asserts nothing: the tests that import it hold every claim.
"""

import dataclasses
import json
import shutil
from pathlib import Path
from typing import Any

from fixtures.preview_payloads import PROJECTION

from pyntpot.maps import Basemap, Cache, OpenTopoData, OverpassFeatures, Style, Track, fetch

from support import REPO_ROOT
from support.paths import FIXTURES, PREVIEW_KEY

#: The committed fixture.
PREVIEW_DIR = FIXTURES / "preview"

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"


def committed_payload(kind: str) -> dict[str, Any]:
    """Return one committed Overpass payload, `overpass` or `landcover`."""
    return json.loads((PREVIEW_DIR / f"{kind}-{PREVIEW_KEY}.json").read_text())


def committed_elements(kind: str) -> list[dict[str, Any]]:
    """Return a committed payload's elements."""
    return committed_payload(kind)["elements"]


def tagged(kind: str, **tags: str) -> dict[str, Any]:
    """Return the first element of a payload carrying all of these tags."""
    return next(e for e in committed_elements(kind) if tags.items() <= e["tags"].items())


def to_metres(geometry: list[dict[str, float]]) -> list[tuple[float, float]]:
    """Return an Overpass geometry array in the generator's metres."""
    return [PROJECTION(g["lat"], g["lon"]) for g in geometry]


def committed_track() -> list[tuple[float, float]]:
    """Return the committed track in metres."""
    track = Track.from_gpx(PREVIEW_DIR / "track.gpx")
    return [PROJECTION(lat, lng) for lat, lng in zip(track.lat, track.lng, strict=True)]


def copy_fixture(tmp_path: Path) -> Path:
    """Copy the fixture beside a test, as a cache directory the providers cannot refill."""
    cache = tmp_path / "cache"
    shutil.copytree(PREVIEW_DIR, cache)
    return cache


def fetch_preview(cache: Path, theme: str | None, display_px: int) -> Basemap:
    """Fetch the preview's basemap from a cache directory in a theme at a card width."""
    features = OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0)
    elevation = OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0)
    style = Style.from_theme(theme, relative_to=REPO_ROOT) if theme is not None else Style()
    style = style.model_copy(
        update={"card": dataclasses.replace(style.card, display_px=display_px)}
    )
    track = Track.from_gpx(cache / "track.gpx")
    return fetch(track, Cache(cache), features, elevation, style)
