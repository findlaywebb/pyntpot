"""Tests for the diff command: real tiny images in two trees or two commits, review images and summaries out."""

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from golden.diff_images import (
    SUMMARY_JSON,
    SUMMARY_MD,
    RefSide,
    TreeSide,
    changed_paths,
    images_under,
    main,
    run,
)
from golden.diff_report import Summary
from PIL import Image

from support.git_repos import commit_all, scratch_repo


def _save(path: Path, value: int = 90, *, spot: tuple[int, int] | None = None, **options) -> None:
    """Write a 40 by 30 flat image, with one bright 3 by 3 spot when asked, in the suffix's format."""
    pixels = np.full((30, 40, 3), value, dtype=np.uint8)
    if spot is not None:
        x, y = spot
        pixels[y : y + 3, x : x + 3] = 250
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels, "RGB").save(path, **options)


def _trees(tmp_path: Path) -> tuple[Path, Path]:
    """Return a before and an after tree: one image changed, one re-encoded, one equal, one added."""
    before, after = tmp_path / "before", tmp_path / "after"
    for root in (before, after):
        _save(root / "docs/images/same.webp", lossless=True)
        _save(root / "tests/golden/docs/reencoded.png", compress_level=9)
    _save(before / "docs/images/moved.webp", lossless=True)
    _save(after / "docs/images/moved.webp", spot=(30, 4), lossless=True)
    _save(after / "tests/golden/docs/reencoded.png", compress_level=1)
    _save(after / "tests/golden/docs/new.png")
    (after / "docs/images/notes.txt").write_text("not an image\n")
    return before, after


class TestTrees:
    """Two directories of one layout: the later tree names the images compared."""

    def test_only_images_whose_pixels_differ_are_reported(self, tmp_path: Path) -> None:
        """The changed image and the added one are listed; equal and re-encoded ones are not."""
        before, after = _trees(tmp_path)
        summary = run(tmp_path / "out", images_under(after), TreeSide(before), TreeSide(after))
        assert [(diff.path, diff.status) for diff in summary.files] == [
            ("docs/images/moved.webp", "changed"),
            ("tests/golden/docs/new.png", "added"),
        ]

    def test_a_changed_image_gets_both_review_images_beside_its_path(self, tmp_path: Path) -> None:
        """The diff image and the crop image are PNGs at the image's path; the crop is the spot, padded."""
        before, after = _trees(tmp_path)
        out = tmp_path / "out"
        summary = run(out, images_under(after), TreeSide(before), TreeSide(after))
        moved = summary.files[0]
        assert moved.diff_image == "docs/images/moved.webp.diff.png"
        assert moved.crop_image == "docs/images/moved.webp.crop.png"
        for drawn in (moved.diff_image, moved.crop_image):
            with Image.open(out / drawn) as img:
                assert img.format == "PNG"
        assert moved.measurement is not None
        assert moved.measurement.box == (30, 4, 33, 7)
        assert moved.measurement.extent == "local"

    def test_both_summaries_are_written_and_agree(self, tmp_path: Path) -> None:
        """`summary.json` reads back as the summary returned; `summary.md` links the review images relatively."""
        before, after = _trees(tmp_path)
        out = tmp_path / "out"
        summary = run(out, images_under(after), TreeSide(before), TreeSide(after))
        assert Summary.from_json((out / SUMMARY_JSON).read_text()) == summary
        text = (out / SUMMARY_MD).read_text()
        assert "](docs/images/moved.webp.diff.png)" in text
        assert "| `tests/golden/docs/new.png` | added |" in text

    def test_min_fraction_leaves_out_small_changes(self, tmp_path: Path) -> None:
        """A 9 of 1200 pixel change is left out at a bound of 0.01, review images and all."""
        before, after = _trees(tmp_path)
        out = tmp_path / "out"
        summary = run(out, images_under(after), TreeSide(before), TreeSide(after), 0.01)
        assert [diff.status for diff in summary.files] == ["added"]
        assert not list(out.rglob("*.diff.png"))

    def test_an_earlier_run_is_replaced_but_other_files_are_kept_safe(self, tmp_path: Path) -> None:
        """A second run empties its own earlier output; a directory of other files is refused."""
        before, after = _trees(tmp_path)
        out = tmp_path / "out"
        run(out, images_under(after), TreeSide(before), TreeSide(after))
        (out / "stale.png").write_bytes(b"")
        run(out, images_under(after), TreeSide(before), TreeSide(after))
        assert not (out / "stale.png").exists()
        precious = tmp_path / "precious"
        precious.mkdir()
        (precious / "keep.txt").write_text("keep\n")
        code = main([str(precious), "--before", str(before), "--after", str(after)])
        assert code == 2
        assert (precious / "keep.txt").is_file()


class TestRefs:
    """A git ref as the earlier side, and the working tree or a second ref as the later."""

    @pytest.fixture
    def repo(self, tmp_path: Path) -> Path:
        """Return a repository whose second commit moves a spot in one docs image."""
        repo = scratch_repo(tmp_path / "repo")
        _save(repo / "docs/images/map.webp", lossless=True)
        _save(repo / "tests/golden/lynmouth/pen.webp", lossless=True)
        _save(repo / "src/ignored.png")
        commit_all(repo, "first")
        _save(repo / "docs/images/map.webp", spot=(10, 10), lossless=True)
        _save(repo / "src/ignored.png", value=10)
        commit_all(repo, "second")
        return repo

    def test_two_refs_compare_only_changed_images_under_the_image_roots(self, repo: Path) -> None:
        """Between two commits, the docs image is listed and an image outside the roots is not."""
        assert changed_paths(repo, "HEAD~1", "HEAD") == ["docs/images/map.webp"]

    def test_the_working_tree_side_includes_untracked_images(self, repo: Path) -> None:
        """Against the working tree, an edited golden and an untracked docs image are listed."""
        _save(repo / "tests/golden/lynmouth/pen.webp", value=91, lossless=True)
        _save(repo / "docs/images/fresh.webp", lossless=True)
        assert changed_paths(repo, "HEAD", None) == [
            "docs/images/fresh.webp",
            "tests/golden/lynmouth/pen.webp",
        ]

    def test_a_ref_side_reads_bytes_at_the_ref(self, repo: Path) -> None:
        """The earlier commit's bytes come back; a path missing at the ref reads as `None`."""
        side = RefSide(repo, "HEAD~1")
        assert side.read("docs/images/map.webp") == _blob(repo, "HEAD~1:docs/images/map.webp")
        assert side.read("docs/images/absent.webp") is None

    def test_main_draws_the_moved_image_between_two_refs(self, repo: Path, tmp_path: Path) -> None:
        """The command, given two refs, writes one changed row with both review images."""
        out = tmp_path / "out"
        code = main([str(out), "--ref", "HEAD~1", "--after-ref", "HEAD", "--repo", str(repo)])
        assert code == 0
        record = json.loads((out / SUMMARY_JSON).read_text())
        assert record["before"] == "HEAD~1"
        assert [item["path"] for item in record["files"]] == ["docs/images/map.webp"]
        assert (out / "docs/images/map.webp.crop.png").is_file()

    def test_main_against_the_working_tree_names_it(self, repo: Path, tmp_path: Path) -> None:
        """With no `--after-ref`, the later side is the working tree, by that name, edits included."""
        _save(repo / "docs/images/map.webp", value=91, lossless=True)
        out = tmp_path / "out"
        assert main([str(out), "--ref", "HEAD", "--repo", str(repo)]) == 0
        record = json.loads((out / SUMMARY_JSON).read_text())
        assert record["after"] == "working tree"
        assert [item["path"] for item in record["files"]] == ["docs/images/map.webp"]

    def test_main_refuses_a_ref_that_is_not_a_commit(self, repo: Path, tmp_path: Path) -> None:
        """A misspelt ref stops the command with exit code 2 and writes nothing."""
        code = main([str(tmp_path / "out"), "--ref", "no-such-ref", "--repo", str(repo)])
        assert code == 2
        assert not (tmp_path / "out").exists()


def _blob(repo: Path, spec: str) -> bytes:
    """Return the raw bytes git holds for `REF:path`."""
    done = subprocess.run(
        ["git", "cat-file", "blob", spec], cwd=repo, capture_output=True, check=True
    )
    return done.stdout


def test_the_command_line_needs_one_mode() -> None:
    """Mixing a directory and a ref, or giving neither, is a usage error."""
    for argv in (
        ["out"],
        ["out", "--before", "a", "--ref", "HEAD"],
        ["out", "--after-ref", "HEAD"],
    ):
        with pytest.raises(SystemExit) as stopped:
            main(argv)
        assert stopped.value.code == 2
