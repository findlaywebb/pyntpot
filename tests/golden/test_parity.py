"""Golden parity: the ported painter reproduces the pre-port Lynmouth plates."""

import json
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot._port import geo, mapcard, paint
from pyntpot._port.style import RouteInk

pytestmark = pytest.mark.golden

TESTS = Path(__file__).resolve().parents[1]
FIXTURE_DIR = TESTS / "fixtures" / "lynmouth"
GOLDEN_DIR = TESTS / "golden" / "lynmouth"
THEME = Path(paint.__file__).parent / "themes" / "default.json"
KEY = "lynmouth"
PLATES = ("paper.webp", "wash.webp", "pen.webp", "labels-centreline.webp")
MAX_DIFFERING_FRACTION = 0.005
MAX_CHANNEL_DELTA = 2


@pytest.fixture(scope="module")
def painted(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Paint and compose the fixture into a fresh copy, returning its directory."""
    work = tmp_path_factory.mktemp("lynmouth")
    shutil.copytree(FIXTURE_DIR, work, dirs_exist_ok=True)
    sentinel = work / "copied.marker"
    sentinel.write_text("")
    copied_ns = sentinel.stat().st_mtime_ns

    default = json.loads(THEME.read_text())
    pstyle = paint.PaintStyle.from_resolved(default["paint"])
    route_ink = RouteInk(**default["route_ink"]["Ride"])
    lat, lng = geo.read_gpx(work / "track.gpx")

    manifest = paint.paint_activity(KEY, lat, lng, pstyle, cache_dir=work, places=[], force=True)
    assert manifest is not None
    plates = paint.plates_dir(KEY, work)
    assert all((plates / name).stat().st_mtime_ns > copied_ns for name in PLATES[:3])

    card = mapcard.compose(KEY, lat, lng, route_ink, pstyle, None, True, work)
    assert card is not None
    assert (plates / PLATES[3]).stat().st_mtime_ns > copied_ns
    card.save(work / "map.png")
    return work


def _outputs(root: Path) -> dict[str, Path]:
    """Map each compared output name to its path under a painted directory."""
    paths = {name: paint.plates_dir(KEY, root) / name for name in PLATES}
    paths["map.png"] = root / "map.png"
    return paths


def _pixels(path: Path) -> np.ndarray:
    """Decode an image to an array, keeping alpha when it has any."""
    with Image.open(path) as img:
        return np.asarray(img.convert("RGBA" if "A" in img.getbands() else "RGB"))


def _compare(name: str, got: Path, want: Path, tolerant: bool) -> None:
    """Assert one output matches its golden, exactly or within the pixel bound."""
    if not tolerant:
        assert got.read_bytes() == want.read_bytes(), f"{name} differs byte for byte"
        return
    a, b = _pixels(got), _pixels(want)
    assert a.shape == b.shape, f"{name} changed shape: {a.shape} against {b.shape}"
    delta = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=-1)
    fraction = float((delta > MAX_CHANNEL_DELTA).mean())
    assert fraction <= MAX_DIFFERING_FRACTION, f"{name}: {fraction:.4%} of pixels differ"


def test_the_manifest_hash_matches_the_golden(painted: Path) -> None:
    """The layers and style hash to the value the pre-port code wrote."""
    want = json.loads((GOLDEN_DIR / "plates.json").read_text())["hash"]
    got = json.loads((paint.plates_dir(KEY, painted) / "plates.json").read_text())["hash"]
    assert got == want


@pytest.mark.parametrize("name", [*PLATES, "map.png"])
def test_each_output_matches_the_golden(painted: Path, golden_tolerance: bool, name: str) -> None:
    """Each plate and the composed card match the golden, exactly or within tolerance."""
    _compare(name, _outputs(painted)[name], GOLDEN_DIR / name, golden_tolerance)
