"""Record and check the full-size output hashes of the five grid example scripts.

Run as `PYTHONPATH=tests uv run python tests/golden/grid_hashes.py record OUT.json` or
`... check OUT.json`. For every `support.docs_images.IMAGES` entry whose stem is
`tutorial_grids`, `nib_stages`, `brush_sheet`, `wash_stages` or `how_to_route_ink`
(stage figures included) it runs the script in a temporary directory (a fixture entry in
a copy of its fixture, with providers that cannot reach a network), at full size, before
any downsizing or encoding. It hashes two things per entry, keyed by `entry.image`: the
sha256 of the written file's bytes and the sha256 of its RGB pixels. `record` writes the
JSON; `check` repaints, logs one line per entry and exits 1 on any difference, a missing
entry or an unexpected one.

It proves a refactor leaves the grid output identical. It does not compare images by
tolerance: the hashes are exact on the machine that recorded them.
"""

import argparse
import hashlib
import json
import logging
import tempfile
from pathlib import Path
from typing import cast

from make_docs_images import fixture_options
from PIL import Image

from support.docs_image import DocsImage
from support.docs_images import IMAGES
from support.examples import run_example

logger = logging.getLogger("grid_hashes")

#: The example scripts whose output the hashes pin.
GRID_STEMS = frozenset(
    {"tutorial_grids", "nib_stages", "brush_sheet", "wash_stages", "how_to_route_ink"}
)

Hashes = dict[str, dict[str, str]]


def _entries() -> list[DocsImage]:
    """Return the registry entries of the grid stems, in registry order."""
    return [entry for entry in IMAGES if entry.stem in GRID_STEMS]


def _hash_entry(entry: DocsImage) -> dict[str, str]:
    """Run the entry's script and return the file and pixel sha256 of what it wrote."""
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        options: dict[str, object] = dict(entry.options)
        if entry.fixture is not None:
            options.update(fixture_options(entry.fixture, work / "cache"))
        written = run_example(entry.stem, work / "out", **options)
        data = written.read_bytes()
        with Image.open(written) as opened:
            pixels = opened.convert("RGB").tobytes()
    return {"file": hashlib.sha256(data).hexdigest(), "pixels": hashlib.sha256(pixels).hexdigest()}


def _measure() -> Hashes:
    """Return the hashes of every grid entry keyed by image path."""
    return {entry.image: _hash_entry(entry) for entry in _entries()}


def record(out: Path) -> int:
    """Write the hashes of every grid entry to `out`; return 0."""
    hashes = _measure()
    out.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    logger.info("recorded %d entries to %s", len(hashes), out)
    return 0


def check(recorded: Path) -> int:
    """Repaint every grid entry and compare with `recorded`; return 1 on any difference."""
    expected = cast("Hashes", json.loads(recorded.read_text()))
    actual = _measure()
    failed = False
    for image in sorted(expected.keys() | actual.keys()):
        if image not in actual:
            logger.error("%s: recorded but no longer a grid entry", image)
            failed = True
        elif image not in expected:
            logger.error("%s: a grid entry that was not recorded", image)
            failed = True
        else:
            same = expected[image] == actual[image]
            logger.info("%s: %s", image, "identical" if same else "DIFFERENT")
            failed = failed or not same
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    """Run `record` or `check` against a JSON path; return the exit status."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Record or check the grid output hashes.")
    parser.add_argument("command", choices=("record", "check"))
    parser.add_argument("path", type=Path, metavar="OUT.json")
    args = parser.parse_args(argv)
    return record(args.path) if args.command == "record" else check(args.path)


if __name__ == "__main__":
    raise SystemExit(main())
