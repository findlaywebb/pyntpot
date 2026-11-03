"""Draw before, after and difference review images of every changed golden and docs image.

Run from the repository root as one of

    PYTHONPATH=tests uv run python tests/golden/diff_images.py OUT --before DIR --after DIR
    PYTHONPATH=tests uv run python tests/golden/diff_images.py OUT --ref REF [--after-ref REF]

With `--before` and `--after`, the two directories share one layout, and each image under
`--after` is compared with the image at the same path under `--before` (an image only under
`--before` is not looked for). With `--ref`, the earlier side is the repository at that git
ref, read with `git show`, and the later side is the working tree, or `--after-ref`; the
images compared are those git lists as differing under `docs/images` and `tests/golden`,
untracked ones included when the later side is the working tree. Images are PNG, WebP and
JPEG files.

For each image whose pixels differ it writes, under `OUT` at the image's own path, a
diff image (`<path>.diff.png`: before, after, the heat map and a key, shrunk to fit a
phone-width PR body) and a 1:1 crop image of the most-changed region (`<path>.crop.png`),
then `summary.json` and `summary.md` (a table of every image that differs, and the
review images). `--min-fraction F` leaves out the review images and rows of changed images
whose changed fraction is at most `F` (CI passes the parity bound, so only failures are
drawn). An image
whose pixels are equal is skipped, whatever its bytes. `OUT` must be absent, empty, or an
earlier run's output (it holds `summary.json`), which is replaced.

Exit codes: 0 when the review images were written, whatever changed (the gate is
`test_parity.py`); 2 for a bad command line, a bad ref or an `OUT` that is not safe to
replace. Publishing the review images for a PR body is `publish_diffs.py`.
"""

import argparse
import logging
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from golden.diff_measure import changed_mask, channel_delta, crop_box, decode, measure
from golden.diff_render import crop_image, diff_image
from golden.diff_report import FileDiff, Summary, markdown
from PIL import Image

from support import REPO_ROOT

logger = logging.getLogger("diff_images")

#: The image file suffixes compared.
IMAGE_SUFFIXES = frozenset({".png", ".webp", ".jpg", ".jpeg"})

#: Where, in the repository, a `--ref` compare looks for changed images.
IMAGE_ROOTS = ("docs/images", "tests/golden")

SUMMARY_JSON = "summary.json"
SUMMARY_MD = "summary.md"


@dataclass(frozen=True)
class TreeSide:
    """One side of a compare read from a directory: an image is the file at its path.

    Attributes:
        root: The directory.
        name: What the summary calls the side; the directory's path when `None`.
    """

    root: Path
    name: str | None = None

    @property
    def label(self) -> str:
        """Name the side for the summary."""
        return str(self.root) if self.name is None else self.name

    def read(self, path: str) -> bytes | None:
        """Return the image's bytes, or `None` when the directory holds no such file."""
        file = self.root / path
        return file.read_bytes() if file.is_file() else None


@dataclass(frozen=True)
class RefSide:
    """One side of a compare read from a git ref of a repository."""

    repo: Path
    ref: str

    @property
    def label(self) -> str:
        """Name the side for the summary."""
        return self.ref

    def read(self, path: str) -> bytes | None:
        """Return the image's bytes at the ref, or `None` when the ref holds no such file."""
        done = subprocess.run(
            ["git", "show", f"{self.ref}:{path}"], cwd=self.repo, capture_output=True, check=False
        )
        return done.stdout if done.returncode == 0 else None


Side = TreeSide | RefSide


def is_image(path: str) -> bool:
    """Return whether a path names a compared image file."""
    return PurePosixPath(path).suffix.lower() in IMAGE_SUFFIXES


def images_under(root: Path) -> list[str]:
    """Return the path, relative to `root`, of every image under it, in order."""
    found = (path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    return sorted(path for path in found if is_image(path))


def _git_lines(repo: Path, *args: str) -> list[str]:
    """Run one git command in `repo` and return its non-empty output lines."""
    done = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return [line for line in done.stdout.splitlines() if line]


def changed_paths(repo: Path, ref: str, after_ref: str | None) -> list[str]:
    """Return the images under `IMAGE_ROOTS` that differ between `ref` and the later side.

    The later side is `after_ref`, or the working tree (untracked images included) when it
    is `None`.
    """
    refs = [ref] if after_ref is None else [ref, after_ref]
    paths = set(_git_lines(repo, "diff", "--name-only", "--no-renames", *refs, "--", *IMAGE_ROOTS))
    if after_ref is None:
        paths |= set(
            _git_lines(repo, "ls-files", "--others", "--exclude-standard", "--", *IMAGE_ROOTS)
        )
    return sorted(path for path in paths if is_image(path))


def _write_png(image_path: Path, drawn: Image.Image) -> None:
    """Save a drawn review image as an optimised PNG, making its directory."""
    image_path.parent.mkdir(parents=True, exist_ok=True)
    drawn.save(image_path, "PNG", optimize=True)


def diff_one(
    path: str,
    before: bytes | None,
    after: bytes | None,
    out: Path,
    min_fraction: float | None = None,
) -> FileDiff | None:
    """Compare one image's two sides, drawing its review images under `out`; `None` when left out.

    Args:
        path: The image's path, relative to both sides.
        before: The earlier bytes, or `None` when the earlier side lacks the image.
        after: The later bytes, or `None` when the later side lacks the image.
        out: The output directory the review images are written under.
        min_fraction: When set, a changed image whose changed fraction is at most this is
            left out.

    Returns:
        The image's difference, or `None` when both sides decode to equal pixels or the
        change is at most `min_fraction`.
    """
    if before is None or after is None:
        if before is None and after is None:
            return None
        return FileDiff(path, "added" if before is None else "removed")
    if before == after:
        return None
    earlier, later = decode(before), decode(after)
    found = measure(earlier, later)
    if found is None or (min_fraction is not None and found.changed_fraction <= min_fraction):
        return None
    delta = None if found.shape_differs else channel_delta(earlier, later)
    diff_path = f"{path}.diff.png"
    _write_png(out / diff_path, diff_image(earlier, later, found, delta))
    crop_path = None
    box = None if delta is None else crop_box(changed_mask(delta))
    if delta is not None and box is not None:
        crop_path = f"{path}.crop.png"
        _write_png(out / crop_path, crop_image(earlier, later, delta, box))
    return FileDiff(path, "changed", found, diff_path, crop_path)


def _prepared(out: Path) -> None:
    """Make `out` an empty directory, replacing an earlier run's output.

    Raises:
        ValueError: When `out` holds files and is not an earlier run's output.
    """
    if out.exists() and any(out.iterdir()):
        if not (out / SUMMARY_JSON).is_file():
            raise ValueError(f"{out} is not empty and holds no {SUMMARY_JSON}; not replacing it")
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)


def run(
    out: Path, paths: list[str], before: Side, after: Side, min_fraction: float | None = None
) -> Summary:
    """Compare each path's two sides, write the review images and both summaries under `out`.

    Args:
        out: The output directory; see `_prepared` for what it may already hold.
        paths: The image paths to compare, relative to both sides.
        before: The earlier side.
        after: The later side.
        min_fraction: When set, a changed image whose changed fraction is at most this is
            left out, review images and row both.

    Returns:
        The summary written.
    """
    _prepared(out)
    files: list[FileDiff] = []
    for path in sorted(paths):
        diff = diff_one(path, before.read(path), after.read(path), out, min_fraction)
        if diff is None:
            continue
        files.append(diff)
        found = diff.measurement
        detail = "" if found is None else f" {found.changed_fraction:.6f}, {found.extent}"
        logger.info("%s: %s%s", path, diff.status, detail)
    summary = Summary(before=before.label, after=after.label, files=tuple(files))
    (out / SUMMARY_JSON).write_text(summary.to_json())
    (out / SUMMARY_MD).write_text(markdown(summary, lambda path: path))
    logger.info("%s images differ; summary in %s", len(files), out / SUMMARY_MD)
    return summary


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Draw diff images of changed images.")
    parser.add_argument("out", type=Path, metavar="OUT", help="directory to write into")
    parser.add_argument("--before", type=Path, metavar="DIR", help="the earlier directory")
    parser.add_argument("--after", type=Path, metavar="DIR", help="the later directory")
    parser.add_argument("--ref", metavar="REF", help="the earlier side, a git ref")
    parser.add_argument("--after-ref", metavar="REF", help="the later side, a git ref")
    parser.add_argument("--repo", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS)
    parser.add_argument(
        "--min-fraction", type=float, default=None, metavar="F", help="leave out changes up to F"
    )
    args = parser.parse_args(argv)
    by_dirs = args.before is not None and args.after is not None and args.ref is None
    by_ref = args.ref is not None and args.before is None and args.after is None
    if not (by_dirs or by_ref) or (args.after_ref is not None and not by_ref):
        parser.error("give --before DIR --after DIR, or --ref REF [--after-ref REF]")
    return args


def _ref_ok(repo: Path, ref: str) -> bool:
    """Return whether `ref` names a commit in `repo`."""
    done = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return done.returncode == 0


def main(argv: list[str] | None = None) -> int:
    """Compare, draw and summarise; return 0 when written, 2 for a bad ref or `OUT`."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    if args.ref is None:
        before: Side = TreeSide(args.before)
        after: Side = TreeSide(args.after)
        paths = images_under(args.after)
    else:
        for ref in (args.ref, args.after_ref):
            if ref is not None and not _ref_ok(args.repo, ref):
                logger.error("not a commit: %s", ref)
                return 2
        before = RefSide(args.repo, args.ref)
        after = (
            TreeSide(args.repo, "working tree")
            if args.after_ref is None
            else RefSide(args.repo, args.after_ref)
        )
        paths = changed_paths(args.repo, args.ref, args.after_ref)
    try:
        run(args.out, paths, before, after, args.min_fraction)
    except ValueError as exc:
        logger.error("%s", exc)  # noqa: TRY400 (the reason is the whole message)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
