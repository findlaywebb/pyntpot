"""Tests for the repaint command's own steps; painting itself is the golden scripts' and is not run here."""

from pathlib import Path

from golden.diff_images import SUMMARY_JSON
from golden.diff_report import Summary
from golden.repaint import main, place_docs

from support.docs_images import IMAGES_DIR, MASTERS_DIR


def test_docs_output_is_placed_at_the_repository_paths(tmp_path: Path) -> None:
    """Images go under `docs/images` and masters under `tests/golden/docs`, at their own paths."""
    painted = tmp_path / "painted"
    for relative in (
        "hero.webp",
        "places/oxford.webp",
        "masters/hero.png",
        "masters/places/oxford.png",
    ):
        (painted / relative).parent.mkdir(parents=True, exist_ok=True)
        (painted / relative).write_bytes(relative.encode())
    tree = tmp_path / "tree"
    place_docs(painted, tree)
    placed = sorted(path.relative_to(tree).as_posix() for path in tree.rglob("*") if path.is_file())
    assert placed == [
        f"{IMAGES_DIR}/hero.webp",
        f"{IMAGES_DIR}/places/oxford.webp",
        f"{MASTERS_DIR}/hero.png",
        f"{MASTERS_DIR}/places/oxford.png",
    ]
    assert (tree / MASTERS_DIR / "places/oxford.png").read_bytes() == b"masters/places/oxford.png"


def test_a_directory_in_use_is_refused(tmp_path: Path) -> None:
    """An `OUT` that already holds files is refused before anything is painted."""
    (tmp_path / "keep.txt").write_text("keep\n")
    assert main([str(tmp_path), "--no-lynmouth", "--no-docs"]) == 2


def test_skipping_both_halves_still_runs_the_diff(tmp_path: Path) -> None:
    """With nothing painted, the diff still runs on the empty tree and writes an empty summary."""
    out = tmp_path / "repaint"
    assert main([str(out), "--no-lynmouth", "--no-docs"]) == 0
    assert (out / "tree").is_dir()
    summary = Summary.from_json((out / "diffs" / SUMMARY_JSON).read_text())
    assert summary.after == str(out / "tree")
    assert summary.files == ()
