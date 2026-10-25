"""Coordinate allowlist gate: every synthetic latitude/longitude pair lies in one fixture's box.

`BOXES` holds one box per fixture directory, each the track's box rounded outward to 0.01
degree, as Lynmouth's is. A latitude and a longitude close together must both lie in the
same fixture's box. The fixture budget test lives here too: each fixture directory stays
within its size in bytes (ADR 0032).
"""

import re

import pytest

from ._text_scan import scanned_text_files
from support import REPO_ROOT
from support.paths import (
    AMBLESIDE_KEY,
    FIXTURES,
    KEY,
    OXFORD_KEY,
    SKYE_KEY,
    Y_FENNI_KEY,
    YR_WYDDFA_KEY,
)

#: South, west, north, east degrees of each fixture's box, by directory name.
BOXES = {
    "lynmouth": (51.19, -3.88, 51.26, -3.80),
    "yr-wyddfa": (53.06, -4.13, 53.11, -4.02),
    "oxford": (51.74, -1.26, 51.76, -1.24),
    "y-fenni": (51.81, -3.03, 51.83, -3.01),
    "ambleside": (54.43, -3.02, 54.45, -2.96),
    "skye": (57.06, -6.78, 57.69, -5.74),
}

#: Each fixture's cache key, which names its payload files.
KEYS = {
    "lynmouth": KEY,
    "yr-wyddfa": YR_WYDDFA_KEY,
    "oxford": OXFORD_KEY,
    "y-fenni": Y_FENNI_KEY,
    "ambleside": AMBLESIDE_KEY,
    "skye": SKYE_KEY,
}

#: Budgets in bytes on disk: 6 MB for a fixture directory, more for the entries below (ADR 0032).
BUDGET_BYTES = 6_000_000
BUDGETS = {
    # Land cover on the Lake District fells is dense: 6.57 MB trimmed, unsimplified.
    "ambleside": 7_000_000,
    "yr-wyddfa": 8_000_000,
    # Skye is simplified and dropped but still over 12 MB; the maintainer ruled not to stop it
    # for a slight overrun (2026-10-25).
    "skye": 13_000_000,
}


def _fixture_files(name: str) -> list[str]:
    """Return the repo-relative paths of a fixture's three payloads, if recorded, and its README."""
    base = f"tests/fixtures/{name}"
    payloads = (
        [f"{base}/{kind}-{KEYS[name]}.json" for kind in ("overpass", "landcover", "elevation")]
        if name in KEYS
        else []
    )
    return [*payloads, f"{base}/README.md"]


# Provider payloads span degrees because they carry full geometry of every way touching the
# box; each README documents its boxes, whose margins lie outside the box by design. This
# file holds the boxes themselves, so it is exempt too.
_EXEMPT = frozenset(
    {
        "tests/golden/lynmouth/plates.json",
        "tests/architecture/test_coordinates.py",
        *(path for name in BOXES for path in _fixture_files(name)),
    }
)

_NUMBER = re.compile(r"(?<![\d.])-?\d{1,2}\.\d{2,}")
_WINDOW = 120


def _in_one_box(lat: float, lon: float) -> bool:
    """Return whether one fixture's box holds both the latitude and the longitude."""
    return any(s <= lat <= n and w <= lon <= e for s, w, n, e in BOXES.values())


def _out_of_box(text: str) -> list[tuple[float, float]]:
    """Return every nearby (lat, lon) pair in text that no single fixture box holds.

    A latitude is any decimal in 49..61 and a longitude any decimal in -8.5..2, with at
    least two decimal places. Magnitudes under 0.1 are arithmetic offsets, not longitudes. Each latitude is paired with every longitude within the
    window, in either order, so separate lists and arithmetic are both caught.
    """
    found = [(m.start(), float(m.group())) for m in _NUMBER.finditer(text)]
    lats = [(i, v) for i, v in found if 49.0 <= v <= 61.0]
    lons = [(i, v) for i, v in found if -8.5 <= v <= 2.0 and abs(v) >= 0.1]
    return [
        (lat, lon)
        for li, lat in lats
        for oi, lon in lons
        if abs(li - oi) <= _WINDOW and not _in_one_box(lat, lon)
    ]


def test_coordinates_stay_inside_one_fixture_box() -> None:
    """Every British-looking coordinate pair in the scanned tree lies inside one fixture's box."""
    found = [
        f"{rel}: {pairs}"
        for path, text in scanned_text_files()
        if (rel := str(path.relative_to(REPO_ROOT))) not in _EXEMPT and (pairs := _out_of_box(text))
    ]
    assert not found, f"coordinates outside any one fixture box: {found}"


def test_a_pair_split_across_two_boxes_is_caught() -> None:
    """A latitude from one fixture's box beside a longitude from another's is out of box."""
    assert _out_of_box("lat 54.44 lon -2.98") == []
    assert _out_of_box("lat 54.44 lon -6.28") == [(54.44, -6.28)]


@pytest.mark.parametrize("name", list(BOXES), ids=list(BOXES))
def test_a_fixture_directory_is_within_its_budget(name: str) -> None:
    """A fixture directory's files sum to within its budget in bytes."""
    files = [path for path in (FIXTURES / name).iterdir() if path.is_file()]
    size = sum(path.stat().st_size for path in files)
    budget = BUDGETS.get(name, BUDGET_BYTES)
    assert size <= budget, f"{name}: {size} bytes over the {budget} budget"
