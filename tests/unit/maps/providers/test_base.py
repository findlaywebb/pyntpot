"""The provider protocols, the elevation grid's file format and the scripted test server."""

import httpx

from pyntpot.maps.providers.base import Elevation, ElevationGrid, Features

from support.http_server import serve
from support.paths import FIXTURE_DIR, KEY
from support.providers import FixtureElevation, FixtureFeatures


def test_fixture_features_is_a_features_provider() -> None:
    """`FixtureFeatures` satisfies `Features` and carries the Overpass provider's id."""
    provider: Features = FixtureFeatures()
    assert provider.id == "overpass"


def test_fixture_elevation_is_an_elevation_provider() -> None:
    """`FixtureElevation` satisfies `Elevation` and carries the OpenTopoData SRTM id."""
    provider: Elevation = FixtureElevation()
    assert provider.id == "opentopodata-srtm30m"


def test_elevation_grid_round_trips_the_fixture_file() -> None:
    """Reading then writing the fixture grid gives its bytes, less the final newline."""
    text = (FIXTURE_DIR / f"elevation-{KEY}.json").read_text()
    grid = ElevationGrid.from_json(text)
    assert grid.n == 80
    assert grid.to_json() == text.removesuffix("\n")


def test_fixture_providers_count_their_calls() -> None:
    """Each fixture provider records one entry per call, by method name."""
    features, elevation = FixtureFeatures(), FixtureElevation()
    box = ElevationGrid.from_json((FIXTURE_DIR / f"elevation-{KEY}.json").read_text()).box
    features.features(box)
    features.landcover(box)
    elevation.grid(box, 80)
    assert features.calls == ["features", "landcover"]
    assert elevation.calls == ["grid"]


def test_server_answers_in_script_order_and_records_requests() -> None:
    """The server answers a 429 then a 200 and records both requests."""
    with serve([(429, ""), (200, "ok")]) as server, httpx.Client(trust_env=False) as client:
        first = client.get(f"{server.url}/interpreter")
        second = client.post(f"{server.url}/interpreter", content=b"[out:json];")
    assert (first.status_code, second.status_code) == (429, 200)
    assert second.text == "ok"
    assert [(r.method, r.path) for r in server.requests] == [
        ("GET", "/interpreter"),
        ("POST", "/interpreter"),
    ]
    assert server.requests[1].body == b"[out:json];"
