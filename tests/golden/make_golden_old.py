"""Produce the Lynmouth golden plates with the original project's code.

Historical: this imports `analysis.report` and runs only inside the
original project's checkout. Run it from a working directory with no
project-data subdirectory, against a copy of the fixture directory, never the fixture
itself, so no plates land there.

Usage:
    python make_golden_old.py <copy-of-fixture-dir> <golden-out-dir>
"""

import re
import shutil
import sys
from pathlib import Path

from analysis.report import mapcard, paint
from analysis.report.render import _theme_style


def read_track(gpx: Path) -> tuple[list[float], list[float]]:
    """Return the latitudes and longitudes of every track point."""
    pts = re.findall(r'lat="([-0-9.]+)" lon="([-0-9.]+)"', gpx.read_text())
    return [float(a) for a, _ in pts], [float(b) for _, b in pts]


def main() -> None:
    """Paint, compose and copy the golden outputs."""
    cache_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
    lat, lng = read_track(cache_dir / "track.gpx")
    pstyle = paint.PaintStyle.from_style(_theme_style("cockpit"))
    manifest = paint.paint_activity(
        "lynmouth", lat, lng, pstyle, route=None, cache_dir=cache_dir, force=True
    )
    if manifest is None:
        raise SystemExit("nothing painted: the fixture cache is empty")
    img = mapcard.compose(
        "lynmouth",
        lat,
        lng,
        "Ride",
        style=_theme_style("cockpit"),
        picks=None,
        labels=True,
        cache_dir=cache_dir,
    )
    if img is None:
        raise SystemExit("compose returned no image")
    out.mkdir(parents=True, exist_ok=True)
    plates = paint.plates_dir("lynmouth", cache_dir)
    for path in sorted(plates.glob("*.webp")):
        shutil.copy2(path, out / path.name)
    shutil.copy2(plates / "plates.json", out / "plates.json")
    img.save(out / "map.png")
    sys.stdout.write(f"hash {manifest['hash']}\n")


if __name__ == "__main__":
    main()
