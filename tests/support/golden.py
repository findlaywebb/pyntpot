"""Paint the Lynmouth fixture, and measure how far two images differ.

The one place golden tooling reaches the painter: `test_parity.py` and
`make_golden.py` both paint through `paint_fixture`, so they paint the same
way. It is also the one measurement every golden comparison shares: `decode`
reads an image as the gate does (RGB, or RGBA when it has alpha), `channel_delta`
is each pixel's largest absolute channel difference, and `differing_fraction` is
the share of pixels past a channel bound. The golden diff tooling
(`golden/diff_measure.py`) measures with the same two functions, so its numbers
are the gate's.

The bounds the parity gate holds (ADR 0030) live here, `MAX_CHANNEL_DELTA` and
`MAX_DIFFERING_FRACTION`, for the gates and the tooling to share. It does not
compare against goldens or decide pass and fail; callers apply the bounds.
"""

import io
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot import Style, Track, compose, fetch, letter, paint
from pyntpot.maps.cache import Cache

from support.paths import FIXTURE_DIR
from support.providers import FixtureElevation, FixtureFeatures

#: A pixel differs when its largest channel difference exceeds this (ADR 0030).
MAX_CHANNEL_DELTA = 2

#: The tolerance gate passes an image when at most this share of its pixels differ (ADR 0030).
MAX_DIFFERING_FRACTION = 0.005

#: The painted plates, in painting order; the last is lettered by the compose step.
PLATES: tuple[str, ...] = ("paper.webp", "wash.webp", "pen.webp", "labels-centreline.webp")

#: Every compared image output: the plates and the composed card.
OUTPUTS: tuple[str, ...] = (*PLATES, "map.png")


def paint_fixture(work: Path) -> tuple[dict[str, Path], list[str]]:
    """Copy the fixture into `work`, fetch, paint, letter and compose it in the default style, and save `map.png`.

    The fetch runs over the copied payloads with the fixture providers, so no
    provider is called. The card is lettered with no annotations and composed
    without an attribution.

    Returns:
        Each name in `OUTPUTS`, plus `plates.json` (the manifest), mapped to its path;
        and the names of the labels placed on the card, in placement order.

    Raises:
        RuntimeError: When a plate was not freshly written in `work`.
    """
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    sentinel = work / "copied.marker"
    sentinel.write_text("")
    copied_ns = sentinel.stat().st_mtime_ns

    style = Style.default()
    track = Track.from_gpx(work / "track.gpx")
    cache = Cache(work)
    features, elevation = FixtureFeatures(), FixtureElevation()

    basemap = fetch(track, cache, features, elevation, style)
    out_dir = cache.plates_dir(cache.key(track, features, elevation))
    plates = paint(basemap, style, out_dir)
    _require_fresh([plates.directory / name for name in PLATES[:3]], copied_ns)

    lettering = letter(plates, basemap, None, style)
    _require_fresh([plates.directory / PLATES[3]], copied_ns)
    card = compose(plates, lettering, basemap, style, attribution=False)
    card.save(work / "map.png")

    paths = {name: plates.directory / name for name in PLATES}
    paths["map.png"] = work / "map.png"
    paths["plates.json"] = plates.directory / "plates.json"
    return paths, [label.name for label in lettering.labels]


def _require_fresh(paths: list[Path], since_ns: int) -> None:
    """Raise unless every path was written after `since_ns`, not copied from the fixture."""
    stale = [path.name for path in paths if path.stat().st_mtime_ns <= since_ns]
    if stale:
        raise RuntimeError(f"not repainted: {stale}")


def decode(data: bytes) -> np.ndarray:
    """Decode an encoded image to an `(height, width, bands)` array, keeping alpha when it has any."""
    with Image.open(io.BytesIO(data)) as img:
        return np.asarray(img.convert("RGBA" if "A" in img.getbands() else "RGB"))


def channel_delta(before: np.ndarray, after: np.ndarray) -> np.ndarray:
    """Return each pixel's largest absolute channel difference, as an `(height, width)` uint8 array.

    The two arrays must share one shape, as `decode` returns them.
    """
    wide = np.abs(before.astype(np.int16) - after.astype(np.int16))
    return wide.max(axis=-1).astype(np.uint8)


def differing_fraction(got: Path, want: Path, channel_bound: int) -> float:
    """Return the fraction of pixels whose largest channel difference exceeds `channel_bound`.

    Two images of different shapes or band counts differ everywhere: the result is 1.0.
    """
    a, b = decode(got.read_bytes()), decode(want.read_bytes())
    if a.shape != b.shape:
        return 1.0
    return float((channel_delta(a, b) > channel_bound).mean())
