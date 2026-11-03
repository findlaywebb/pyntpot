"""Repaint the Lynmouth goldens and the docs images into a scratch tree, and diff it with the repo.

Run from the repository root as
`PYTHONPATH=tests uv run python tests/golden/repaint.py OUT [NAME ...] [--no-lynmouth] [--no-docs]`.
Each NAME is a docs image's path under `docs/images/`, as `make_docs_images.py` takes it;
none means every registered image. `OUT` must be absent or empty.

It paints into `OUT/tree/`, laid out as the repository is: the Lynmouth outputs, manifest,
`labels.txt` and `baseline.json` in `tests/golden/lynmouth/` (by `make_golden.py`, whose
compare with the committed goldens it logs: byte-identical or not, the differing fraction and
both manifest hashes), the docs images in `docs/images/` and their masters in
`tests/golden/docs/` (by `make_docs_images.py`). Then it runs `diff_images.py` with the working
tree as the earlier side and `OUT/tree` as the later, writing the review images and the
summary to `OUT/diffs/`, which `publish_diffs.py` takes. This is the first step of a golden
regeneration (ADR 0048): what moved, and by how much, before anything is committed.

It does not write into the repository: committing a regeneration is `make_golden.py` and
`make_docs_images.py` run on the committed directories. Exit code: 0 when painted and
diffed, 2 for an `OUT` that is not empty, else the painting script's own non-zero code.
"""

import argparse
import logging
import shutil
import tempfile
from pathlib import Path

from golden import diff_images, make_docs_images, make_golden

from support import REPO_ROOT
from support.docs_images import IMAGES_DIR, MASTERS_DIR
from support.paths import GOLDEN_DIR

logger = logging.getLogger("repaint")


def place_docs(painted: Path, tree: Path) -> None:
    """Move a `make_docs_images.py` output into `tree` at the repository's paths.

    Images go to `IMAGES_DIR`; the masters, under `masters/` in `painted`, go to `MASTERS_DIR`.
    """
    masters = painted / make_docs_images.MASTERS_SUBDIR
    for file in sorted(path for path in painted.rglob("*") if path.is_file()):
        if file.is_relative_to(masters):
            target = tree / MASTERS_DIR / file.relative_to(masters)
        else:
            target = tree / IMAGES_DIR / file.relative_to(painted)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(file, target)


def main(argv: list[str] | None = None) -> int:
    """Repaint into `OUT/tree`, diff into `OUT/diffs`; return the first non-zero step's code."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Repaint the goldens and docs images, and diff.")
    parser.add_argument("out", type=Path, metavar="OUT", help="an absent or empty directory")
    parser.add_argument("names", nargs="*", metavar="NAME", help="docs image paths (default: all)")
    parser.add_argument("--no-lynmouth", action="store_true", help="skip the Lynmouth goldens")
    parser.add_argument("--no-docs", action="store_true", help="skip the docs images")
    args = parser.parse_args(argv)
    if args.out.exists() and any(args.out.iterdir()):
        logger.error("%s is not empty", args.out)
        return 2
    tree = args.out / "tree"
    if not args.no_lynmouth:
        lynmouth = tree / GOLDEN_DIR.relative_to(REPO_ROOT)
        code = make_golden.main([str(lynmouth), "--compare", str(GOLDEN_DIR)])
        if code:
            return code
    if not args.no_docs:
        with tempfile.TemporaryDirectory() as tmp:
            code = make_docs_images.main([tmp, *args.names])
            if code:
                return code
            place_docs(Path(tmp), tree)
    tree.mkdir(parents=True, exist_ok=True)
    diff_out = args.out / "diffs"
    return diff_images.main([str(diff_out), "--before", str(REPO_ROOT), "--after", str(tree)])


if __name__ == "__main__":
    raise SystemExit(main())
