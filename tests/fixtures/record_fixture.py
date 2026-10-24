"""Record a fixture's three provider payloads next to its `track.gpx`.

Run as `PYTHONPATH=tests uv run python tests/fixtures/record_fixture.py --contact CONTACT
--fixture DIR`. It reads `DIR/track.gpx`, then runs `Cache.ensure` for it through
`OverpassFeatures` (the `MIRROR` endpoint only) and `OpenTopoData`, writing the feature,
land cover and elevation payloads into `DIR`, one query at a time within each provider's
own budget and back-off. A failed fetch is tried again up to three times, after a wait;
`ensure` keeps the payloads already written, so a retry carries on where it stopped.

It then checks the three file names equal the default providers' key (the ids the
shipped providers carry), and logs each payload's size. It does not write the README,
parse the payloads or choose a track.
"""

import argparse
import logging
import time
from collections.abc import Sequence
from pathlib import Path

from fixtures.make_track import MIRROR

from pyntpot.maps import Cache, FetchError, OpenTopoData, OverpassFeatures, Track

log = logging.getLogger("record_fixture")

#: Tries before the recording gives up.
TRIES = 3

#: Seconds waited before the nth retry, per attempt already made.
RETRY_WAIT_S = 30.0


def _ensure(cache: Cache, track: Track, features: OverpassFeatures, elevation: OpenTopoData) -> str:
    """Run `Cache.ensure` up to `TRIES` times, waiting longer after each failure."""
    for attempt in range(1, TRIES):
        try:
            return cache.ensure(track, features, elevation)
        except FetchError:
            log.exception("try %d of %d failed", attempt, TRIES)
            time.sleep(RETRY_WAIT_S * attempt)
    return cache.ensure(track, features, elevation)


def record(contact: str, fixture: Path) -> str:
    """Record the payloads into a fixture directory and return the key.

    Raises:
        FetchError: When every try failed.
        RuntimeError: When the key differs from the default providers' key.
    """
    track = Track.from_gpx(fixture / "track.gpx")
    features = OverpassFeatures(contact, (MIRROR,))
    elevation = OpenTopoData(contact)
    cache = Cache(fixture)
    key = _ensure(cache, track, features, elevation)
    default = Cache(fixture).key(track, OverpassFeatures(contact), OpenTopoData(contact))
    if key != default:
        raise RuntimeError(f"key {key} differs from the default providers' key {default}")
    for path in (cache.features_path(key), cache.landcover_path(key), cache.elevation_path(key)):
        log.info("%s: %d bytes", path.name, path.stat().st_size)
    return key


def main(argv: Sequence[str] | None = None) -> int:
    """Record one fixture; return the exit status."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    parser = argparse.ArgumentParser(description="Record a fixture's provider payloads.")
    parser.add_argument("--contact", required=True, help="how the operators reach you")
    parser.add_argument("--fixture", required=True, type=Path, help="the fixture directory")
    args = parser.parse_args(argv)
    try:
        key = record(args.contact, args.fixture)
    except (FetchError, RuntimeError):
        log.exception("failed")
        return 1
    log.info("key %s", key)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
