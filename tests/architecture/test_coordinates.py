"""Coordinate allowlist gate — every synthetic latitude/longitude lies in the fixture box."""

import re

from ._text_scan import scanned_text_files
from support import REPO_ROOT

LAT_RANGE = (51.19, 51.26)
LON_RANGE = (-3.88, -3.80)

# Provider payloads span degrees because they carry full geometry of every way touching the box.
_EXEMPT = frozenset(
    {
        "tests/fixtures/lynmouth/overpass-lynmouth.json",
        "tests/fixtures/lynmouth/landcover-lynmouth.json",
        "tests/fixtures/lynmouth/elevation-lynmouth.json",
        "tests/golden/lynmouth/plates.json",
        # Documents the box and its margins, which lie outside the box by design.
        "tests/fixtures/lynmouth/README.md",
    }
)

_NUMBER = re.compile(r"(?<![\d.])-?\d{1,2}\.\d{2,}")
_WINDOW = 120


def _out_of_box(text: str) -> list[tuple[float, float]]:
    """Return every nearby (lat, lon) pair in text that falls outside the fixture box.

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
        if abs(li - oi) <= _WINDOW
        and not (LAT_RANGE[0] <= lat <= LAT_RANGE[1] and LON_RANGE[0] <= lon <= LON_RANGE[1])
    ]


def test_coordinates_stay_inside_the_fixture_box() -> None:
    """Every British-looking coordinate pair in the scanned tree lies inside the Lynmouth box."""
    found = [
        f"{rel}: {pairs}"
        for path, text in scanned_text_files()
        if (rel := str(path.relative_to(REPO_ROOT))) not in _EXEMPT and (pairs := _out_of_box(text))
    ]
    assert not found, f"coordinates outside the fixture box: {found}"
