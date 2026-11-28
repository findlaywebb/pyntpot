"""Record and check the full-size output hashes of the docs images' example scripts.

Run as `PYTHONPATH=tests uv run python tests/golden/output_hashes.py record OUT.json` or
`... check OUT.json`. For every `support.docs_images.IMAGES` entry (stage figures included)
it runs the script in a temporary directory (a fixture entry in a copy of its fixture, with
providers that cannot reach a network), at full size, before any downsizing or encoding. It
hashes two things per entry, keyed by `entry.image`: the sha256 of the written file's bytes
and the sha256 of its RGB pixels. `record` writes the JSON; `check` repaints, logs one line
per entry and exits 1 on any difference, a missing entry or an unexpected one.

`--stem STEM`, repeatable, narrows both commands to the entries of those stems. `record`
then writes only their entries. `check` measures only them, ignores every recorded entry of
another stem, and still fails on a selected entry that is missing from the JSON or differs.
A recorded entry whose image is no longer registered belongs to no stem, so only an
unnarrowed `check` reports it. A stem the registry does not hold is an argparse error
(exit 2), raised before anything is painted.

It proves a refactor leaves the output identical. It does not compare images by tolerance:
the hashes are exact on the machine that recorded them.
"""

import argparse
import hashlib
import json
import logging
import tempfile
from collections.abc import Collection
from pathlib import Path
from typing import cast

from golden.make_docs_images import fixture_options
from PIL import Image

from support.docs_image import DocsImage
from support.docs_images import IMAGES
from support.examples import run_example

logger = logging.getLogger("output_hashes")

Hashes = dict[str, dict[str, str]]


def select(stems: Collection[str] | None) -> list[DocsImage]:
    """Return the registry entries of `stems` in registry order, or all with `None`.

    Raises:
        ValueError: If a stem names no registered entry.
    """
    if stems is None:
        return list(IMAGES)
    unknown = sorted(set(stems) - {entry.stem for entry in IMAGES})
    if unknown:
        raise ValueError(f"no registered stem: {', '.join(unknown)}")
    return [entry for entry in IMAGES if entry.stem in stems]


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


def _measure(entries: list[DocsImage]) -> Hashes:
    """Return the hashes of `entries` keyed by image path."""
    return {entry.image: _hash_entry(entry) for entry in entries}


def record(out: Path, stems: Collection[str] | None = None) -> int:
    """Write the hashes of the selected entries to `out`; return 0."""
    hashes = _measure(select(stems))
    out.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n")
    logger.info("recorded %d entries to %s", len(hashes), out)
    return 0


def compare(
    expected: Hashes, actual: Hashes, *, selected: Collection[str] | None
) -> dict[str, str]:
    """Return each compared image's verdict; `selected` names the images a narrowed check covers.

    A narrowed comparison covers only `selected`; a recorded entry outside it is ignored.
    Without a selection every recorded and measured image is compared.
    """
    images = sorted(expected.keys() | actual.keys() if selected is None else selected)
    verdicts: dict[str, str] = {}
    for image in images:
        if image not in actual:
            verdicts[image] = "recorded but no longer an entry"
        elif image not in expected:
            verdicts[image] = "not recorded"
        else:
            verdicts[image] = "identical" if expected[image] == actual[image] else "DIFFERENT"
    return verdicts


def check(recorded: Path, stems: Collection[str] | None = None) -> int:
    """Repaint the selected entries and compare with `recorded`; return 1 on any difference."""
    expected = cast("Hashes", json.loads(recorded.read_text()))
    entries = select(stems)
    actual = _measure(entries)
    selected = None if stems is None else {entry.image for entry in entries}
    failed = False
    for image, verdict in compare(expected, actual, selected=selected).items():
        logger.info("%s: %s", image, verdict)
        failed = failed or verdict != "identical"
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    """Run `record` or `check` against a JSON path; return the exit status."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Record or check the docs images' output hashes.")
    parser.add_argument("command", choices=("record", "check"))
    parser.add_argument("path", type=Path, metavar="OUT.json")
    parser.add_argument(
        "--stem", action="append", metavar="STEM", help="narrow to this stem; repeatable"
    )
    args = parser.parse_args(argv)
    try:
        select(args.stem)
    except ValueError as exc:
        parser.error(str(exc))
    return record(args.path, args.stem) if args.command == "record" else check(args.path, args.stem)


if __name__ == "__main__":
    raise SystemExit(main())
