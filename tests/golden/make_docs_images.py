"""Paint the registered docs images into a directory and compare it with others.

Run as `PYTHONPATH=tests uv run python tests/golden/make_docs_images.py OUT [NAME ...]
[--compare DIR ...]`. Each NAME is an entry's `image` path under `docs/images/`; none
means every entry. It runs each entry's script in `examples/` in a temporary directory
(a fixture entry in a copy of the fixture, with providers that cannot reach a network),
downsizes the image to the entry's width without enlarging it, encodes it as the entry's
encoding says and writes it under `OUT` at its `image` path. Each `--compare DIR` logs one
line per image (byte-identical or not, and the fraction of pixels past the parity channel
bound) and exits 1 when an image of `OUT` is missing from DIR, differs in shape or is past
the parity bound.

`paint_entry` is the painting the pin test shares. This module does not
decide which images exist: `support.docs_images` does.
"""

import argparse
import io
import logging
import shutil
import tempfile
from pathlib import Path

from golden.test_parity import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION
from PIL import Image

from pyntpot.maps import OpenTopoData, OverpassFeatures

from support import REPO_ROOT
from support.docs_images import IMAGES, DocsImage
from support.examples import run_example
from support.golden import differing_fraction

logger = logging.getLogger("make_docs_images")

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"
_FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _fixture_options(fixture: str, cache: Path) -> dict[str, object]:
    """Copy a fixture into `cache` and return the keywords a fixture script takes."""
    shutil.copytree(_FIXTURES / fixture, cache)
    return {
        "track": cache / "track.gpx",
        "cache_dir": cache,
        "features": OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0),
        "elevation": OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0),
    }


def _encode(img: Image.Image, encoding: str) -> bytes:
    """Return the image's bytes in the named encoding."""
    buffer = io.BytesIO()
    match encoding:
        case "webp-lossless":
            img.save(buffer, "WEBP", lossless=True, method=5)
        case "webp-lossy":
            img.save(buffer, "WEBP", quality=90, method=5)
        case "jpeg":
            img.save(buffer, "JPEG", quality=88)
        case _:
            raise ValueError(f"unknown encoding {encoding!r}")
    return buffer.getvalue()


def paint_entry(entry: DocsImage, work: Path) -> bytes:
    """Run an entry's script under `work`, downsize its image and return the encoded bytes.

    Args:
        entry: The registered image.
        work: An empty directory the script and the fixture copy are written into.

    Returns:
        The file's bytes: the script's image, no wider than `entry.width`, in the entry's encoding.
    """
    options: dict[str, object] = dict(entry.options)
    if entry.fixture is not None:
        options.update(_fixture_options(entry.fixture, work / "cache"))
    written = run_example(entry.stem, work / "out", **options)
    with Image.open(written) as opened:
        img = opened.convert("RGB")
    if img.width > entry.width:
        height = max(1, round(img.height * entry.width / img.width))
        img = img.resize((entry.width, height), Image.Resampling.LANCZOS)
    return _encode(img, entry.encoding)


def _write(out: Path, entries: list[DocsImage]) -> None:
    """Paint each entry and write its file under `out`."""
    for entry in entries:
        with tempfile.TemporaryDirectory() as tmp:
            data = paint_entry(entry, Path(tmp))
        target = out / entry.image
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        logger.info("%s: %s bytes", entry.image, len(data))


def _compare(out: Path, other: Path, entries: list[DocsImage]) -> list[str]:
    """Log one line per image against `other`; return the violations."""
    violations: list[str] = []
    for entry in entries:
        ours, theirs = out / entry.image, other / entry.image
        if not theirs.is_file():
            violations.append(f"{entry.image} is missing from {other}")
            continue
        identical = "yes" if ours.read_bytes() == theirs.read_bytes() else "no"
        fraction = differing_fraction(ours, theirs, MAX_CHANNEL_DELTA)
        logger.info(
            "%s against %s: identical %s, differing fraction %.6f",
            entry.image,
            other,
            identical,
            fraction,
        )
        if fraction > MAX_DIFFERING_FRACTION:
            violations.append(f"{entry.image} differing fraction {fraction:.6f}")
    return violations


def main(argv: list[str] | None = None) -> int:
    """Paint the named entries (all when none are named) into OUT; return 1 when a compare fails."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Paint the registered docs images.")
    parser.add_argument("out", type=Path, metavar="OUT", help="directory to write into")
    parser.add_argument("names", nargs="*", metavar="NAME", help="image paths under docs/images/")
    parser.add_argument(
        "--compare", type=Path, action="append", default=[], metavar="DIR", help="compare with DIR"
    )
    args = parser.parse_args(argv)
    known = {entry.image: entry for entry in IMAGES}
    unknown = [name for name in args.names if name not in known]
    if unknown:
        parser.error(f"not registered: {unknown}")
    entries = [known[name] for name in args.names] or list(IMAGES)
    _write(args.out, entries)
    violations = [v for other in args.compare for v in _compare(args.out, other, entries)]
    for violation in violations:
        logger.error("gate violated: %s", violation)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
