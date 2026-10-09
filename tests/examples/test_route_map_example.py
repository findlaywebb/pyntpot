"""The route map script paints the Lynmouth fixture from a full cache, with providers that cannot reach a network."""

import shutil
from pathlib import Path

import pytest
from PIL import Image

from pyntpot.maps import Cache, OpenTopoData, OverpassFeatures, Track

from support.examples import run_example
from support.paths import FIXTURE_DIR, KEY

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"


@pytest.mark.golden
def test_the_route_map_paints_from_the_cache_alone(tmp_path: Path) -> None:
    """From a cache holding the fixture's payloads, the script writes the map without a provider call."""
    cache = tmp_path / "cache"
    shutil.copytree(FIXTURE_DIR, cache)
    features = OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0)
    elevation = OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0)
    track = cache / "track.gpx"
    assert Cache(cache).key(Track.from_gpx(track), features, elevation) == KEY
    for payload in (f"overpass-{KEY}.json", f"landcover-{KEY}.json", f"elevation-{KEY}.json"):
        assert (cache / payload).is_file(), f"the fixture lacks {payload}"

    written = run_example(
        "route_map",
        tmp_path / "out",
        track=track,
        cache_dir=cache,
        features=features,
        elevation=elevation,
    )

    assert written == tmp_path / "out" / "map.png"
    with Image.open(written) as card:
        assert card.mode == "RGB"
    for prefix in ("overpass", "landcover", "elevation"):
        assert len(list(cache.glob(f"{prefix}-*.json"))) == 1, (
            f"the cache gained a {prefix} payload"
        )
