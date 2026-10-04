"""Golden parity: the ported painter reproduces the pre-port Lynmouth plates."""

import json
from pathlib import Path

import pytest

from support.golden import OUTPUTS, differing_fraction, paint_fixture

pytestmark = pytest.mark.golden

MAX_DIFFERING_FRACTION = 0.005
MAX_CHANNEL_DELTA = 2


@pytest.fixture(scope="module")
def painted(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Paint and compose the fixture into a fresh copy, returning each output's path."""
    paths, _placed = paint_fixture(tmp_path_factory.mktemp("lynmouth"))
    return paths


def _compare(name: str, got: Path, want: Path, tolerant: bool) -> None:
    """Assert one output matches its golden, exactly or within the pixel bound."""
    if not tolerant:
        assert got.read_bytes() == want.read_bytes(), f"{name} differs byte for byte"
        return
    fraction = differing_fraction(got, want, MAX_CHANNEL_DELTA)
    assert fraction <= MAX_DIFFERING_FRACTION, f"{name}: {fraction:.4%} of pixels differ"


def test_the_manifest_hash_matches_the_golden(painted: dict[str, Path], golden_dir: Path) -> None:
    """The layers and style hash to the value the pre-port code wrote."""
    want = json.loads((golden_dir / "plates.json").read_text())["hash"]
    got = json.loads(painted["plates.json"].read_text())["hash"]
    assert got == want


@pytest.mark.parametrize("name", OUTPUTS, ids=OUTPUTS)
def test_each_output_matches_the_golden(
    painted: dict[str, Path], golden_dir: Path, golden_tolerance: bool, name: str
) -> None:
    """Each plate and the composed card match the golden, exactly or within tolerance."""
    _compare(name, painted[name], golden_dir / name, golden_tolerance)
