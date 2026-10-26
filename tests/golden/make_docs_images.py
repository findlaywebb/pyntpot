"""Paint the registered docs images into a directory and compare it with others.

Run as `PYTHONPATH=tests uv run python tests/golden/make_docs_images.py OUT [NAME ...]
[--compare DIR ...]`. Each NAME is an entry's `image` path under `docs/images/`; none
means every entry. It runs each entry's script in `examples/` in a temporary directory
(a fixture entry in a copy of the fixture, with providers that cannot reach a network),
downsizes the image to the entry's width without enlarging it, encodes it as the entry's
encoding says and writes it under `OUT` at its `image` path. It also writes the entry's
lossless reference master (a PNG, at most `MASTER_WIDTH` wide) under `OUT/masters/` at
`master_path(image)`; commit those to `tests/golden/docs/`. Each `--compare DIR` covers both and logs one
line per file (byte-identical or not, and the fraction of pixels past the parity channel
bound) and exits 1 when an image of `OUT` is missing from DIR, differs in shape or is past
the parity bound.

`paint_entry` is the painting the pin test shares: the docs image's bytes and the master's. This module does not
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
from support.docs_images import IMAGES, MASTER_WIDTH, DocsImage, master_path
from support.examples import run_example
from support.golden import differing_fraction

logger = logging.getLogger("make_docs_images")

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"
#: Where under `OUT` the masters are written.
MASTERS_SUBDIR = "masters"
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


def _encode(img: Image.Image, encoding: str, quality: int | None = None) -> bytes:
    """Return the image's bytes in the named encoding; `quality` of `None` is its default."""
    buffer = io.BytesIO()
    match encoding:
        case "webp-lossless":
            img.save(buffer, "WEBP", lossless=True, method=5)
        case "webp-lossy":
            img.save(buffer, "WEBP", quality=90 if quality is None else quality, method=5)
        case "jpeg":
            img.save(buffer, "JPEG", quality=88 if quality is None else quality)
        case _:
            raise ValueError(f"unknown encoding {encoding!r}")
    return buffer.getvalue()


def _downsized(img: Image.Image, width: int) -> Image.Image:
    """Return `img` no wider than `width`, downsized with LANCZOS and never enlarged."""
    if img.width <= width:
        return img
    height = max(1, round(img.height * width / img.width))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def _master(img: Image.Image, entry: DocsImage) -> bytes:
    """Return the entry's lossless PNG reference master bytes."""
    buffer = io.BytesIO()
    _downsized(img, min(entry.width, MASTER_WIDTH)).save(
        buffer, "PNG", optimize=False, compress_level=9
    )
    return buffer.getvalue()


def paint_entry(entry: DocsImage, work: Path) -> tuple[bytes, bytes]:
    """Run an entry's script under `work` and return the docs image's and the master's bytes.

    Args:
        entry: The registered image.
        work: An empty directory the script and the fixture copy are written into.

    Returns:
        The docs file's bytes (the script's image, no wider than `entry.width`, in the
        entry's encoding) and the lossless PNG master's bytes.
    """
    options: dict[str, object] = dict(entry.options)
    if entry.fixture is not None:
        options.update(_fixture_options(entry.fixture, work / "cache"))
    written = run_example(entry.stem, work / "out", **options)
    with Image.open(written) as opened:
        img = opened.convert("RGB")
    return _encode(_downsized(img, entry.width), entry.encoding, entry.quality), _master(img, entry)


def _write(out: Path, entries: list[DocsImage]) -> None:
    """Paint each entry and write its file and its master under `out`."""
    for entry in entries:
        with tempfile.TemporaryDirectory() as tmp:
            data, master = paint_entry(entry, Path(tmp))
        for relative, content in (
            (entry.image, data),
            (f"{MASTERS_SUBDIR}/{master_path(entry.image)}", master),
        ):
            target = out / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            logger.info("%s: %s bytes", relative, len(content))


def _compare(out: Path, other: Path, entries: list[DocsImage]) -> list[str]:
    """Log one line per image and master against `other`; return the violations."""
    violations: list[str] = []
    for entry in entries:
        for relative in (entry.image, f"{MASTERS_SUBDIR}/{master_path(entry.image)}"):
            ours, theirs = out / relative, other / relative
            if not theirs.is_file():
                violations.append(f"{relative} is missing from {other}")
                continue
            identical = "yes" if ours.read_bytes() == theirs.read_bytes() else "no"
            fraction = differing_fraction(ours, theirs, MAX_CHANNEL_DELTA)
            logger.info(
                "%s against %s: identical %s, differing fraction %.6f",
                relative,
                other,
                identical,
                fraction,
            )
            if fraction > MAX_DIFFERING_FRACTION:
                violations.append(f"{relative} differing fraction {fraction:.6f}")
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
