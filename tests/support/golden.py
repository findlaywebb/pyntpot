"""Paint the Lynmouth fixture and measure how far two images differ.

The one place golden tooling reaches the painter: `test_parity.py` and
`make_golden.py` both paint through `paint_fixture`, so they paint the same
way. It does not compare against goldens or decide pass and fail; callers
hold the bounds.
"""

import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot._port import geo, mapcard, paint
from pyntpot.maps.style import Style

from support.paths import FIXTURE_DIR, KEY

#: The painted plates, in painting order; the last is lettered by the compose step.
PLATES: tuple[str, ...] = ("paper.webp", "wash.webp", "pen.webp", "labels-centreline.webp")

#: Every compared image output: the plates and the composed card.
OUTPUTS: tuple[str, ...] = (*PLATES, "map.png")


def paint_fixture(work: Path) -> tuple[dict[str, Path], list[str]]:
    """Copy the fixture into `work`, paint and compose it in the default style, and save `map.png`.

    Returns:
        Each name in `OUTPUTS`, plus `plates.json` (the manifest), mapped to its path;
        and the names of the labels placed on the card, in placement order.

    Raises:
        RuntimeError: When painting yields nothing, or a plate was not freshly
            written in `work`.
    """
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    sentinel = work / "copied.marker"
    sentinel.write_text("")
    copied_ns = sentinel.stat().st_mtime_ns

    style = Style.default()
    lat, lng = geo.read_gpx(work / "track.gpx")

    painted = paint.paint_activity(KEY, lat, lng, style, cache_dir=work, places=[], force=True)
    if painted is None:
        raise RuntimeError("painting the fixture wrote no manifest")
    basemap, plates = painted
    _require_fresh([plates.directory / name for name in PLATES[:3]], copied_ns)

    card, placed = mapcard.compose(basemap, plates, style, None, True)
    _require_fresh([plates.directory / PLATES[3]], copied_ns)
    card.save(work / "map.png")

    paths = {name: plates.directory / name for name in PLATES}
    paths["map.png"] = work / "map.png"
    paths["plates.json"] = plates.directory / "plates.json"
    return paths, [label.name for label in placed]


def _require_fresh(paths: list[Path], since_ns: int) -> None:
    """Raise unless every path was written after `since_ns`, not copied from the fixture."""
    stale = [path.name for path in paths if path.stat().st_mtime_ns <= since_ns]
    if stale:
        raise RuntimeError(f"not repainted: {stale}")


def _pixels(path: Path) -> np.ndarray:
    """Decode an image to an array, keeping alpha when it has any."""
    with Image.open(path) as img:
        return np.asarray(img.convert("RGBA" if "A" in img.getbands() else "RGB"))


def differing_fraction(got: Path, want: Path, channel_delta: int) -> float:
    """Return the fraction of pixels whose largest channel difference exceeds `channel_delta`.

    Two images of different shapes or band counts differ everywhere: the result is 1.0.
    """
    a, b = _pixels(got), _pixels(want)
    if a.shape != b.shape:
        return 1.0
    delta = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=-1)
    return float((delta > channel_delta).mean())
