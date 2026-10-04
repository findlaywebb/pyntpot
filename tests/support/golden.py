"""Paint the Lynmouth fixture and measure how far two images differ.

The one place golden tooling reaches the painter: `test_parity.py` and
`make_golden.py` both paint through `paint_fixture`, so they paint the same
way. It does not compare against goldens or decide pass and fail; callers
hold the bounds.
"""

import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot._port import geo, mapcard, paint
from pyntpot._port.style import RouteInk

from support.paths import FIXTURE_DIR, KEY

#: The painted plates, in painting order; the last is lettered by the compose step.
PLATES: tuple[str, ...] = ("paper.webp", "wash.webp", "pen.webp", "labels-centreline.webp")

#: Every compared image output: the plates and the composed card.
OUTPUTS: tuple[str, ...] = (*PLATES, "map.png")

_THEME = Path(paint.__file__).parent / "themes" / "default.json"


def paint_fixture(work: Path) -> dict[str, Path]:
    """Copy the fixture into `work`, paint and compose it, and save `map.png` there.

    Returns:
        Each name in `OUTPUTS`, plus `plates.json` (the manifest), mapped to its path.

    Raises:
        RuntimeError: When painting or composing yields nothing, or a plate was not
            freshly written in `work`.
    """
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    sentinel = work / "copied.marker"
    sentinel.write_text("")
    copied_ns = sentinel.stat().st_mtime_ns

    default = json.loads(_THEME.read_text())
    pstyle = paint.PaintStyle.from_resolved(default["paint"])
    route_ink = RouteInk(**default["route_ink"]["Ride"])
    lat, lng = geo.read_gpx(work / "track.gpx")

    manifest = paint.paint_activity(KEY, lat, lng, pstyle, cache_dir=work, places=[], force=True)
    if manifest is None:
        raise RuntimeError("painting the fixture wrote no manifest")
    plates = paint.plates_dir(KEY, work)
    _require_fresh([plates / name for name in PLATES[:3]], copied_ns)

    card = mapcard.compose(KEY, lat, lng, route_ink, pstyle, None, True, work)
    if card is None:
        raise RuntimeError("composing the fixture made no card")
    _require_fresh([plates / PLATES[3]], copied_ns)
    card.save(work / "map.png")

    paths = {name: plates / name for name in PLATES}
    paths["map.png"] = work / "map.png"
    paths["plates.json"] = plates / "plates.json"
    return paths


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
