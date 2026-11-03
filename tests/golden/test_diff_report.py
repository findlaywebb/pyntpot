"""Tests for the golden diff summary: literal measurements in, JSON and Markdown out."""

import json

import pytest
from golden.diff_measure import Measurement
from golden.diff_report import OPEN_LIMIT, FileDiff, Summary, image_tag, markdown, table_row

LOCAL = Measurement(
    width=1200,
    height=854,
    changed_fraction=0.000645,
    max_delta=37,
    box=(10, 20, 110, 90),
    extent="local",
)
OVER = Measurement(
    width=240,
    height=171,
    changed_fraction=0.012,
    max_delta=200,
    box=(0, 0, 240, 171),
    extent="widespread",
)
RESIZED = Measurement(
    width=50, height=30, changed_fraction=1.0, max_delta=None, box=None, extent="widespread"
)


def _changed(path: str, found: Measurement = LOCAL) -> FileDiff:
    """Return a changed image's difference with both review images beside its path."""
    return FileDiff(path, "changed", found, f"{path}.diff.png", f"{path}.crop.png")


class TestJson:
    """`summary.json` round-trips and records the bounds."""

    def test_a_summary_reads_back_equal(self) -> None:
        """Every status, a resized image included, survives `to_json` and `from_json`."""
        summary = Summary(
            before="origin/main",
            after="working tree",
            files=(
                _changed("docs/images/hero.webp"),
                FileDiff("docs/images/old.webp", "removed"),
                FileDiff("tests/golden/docs/new.png", "added"),
                FileDiff("tests/golden/lynmouth/map.png", "changed", RESIZED, "m.diff.png"),
            ),
        )
        assert Summary.from_json(summary.to_json()) == summary

    def test_the_record_carries_the_bounds_and_the_over_bound_flag(self) -> None:
        """The JSON names the channel delta and the parity bound, and flags a change past it."""
        record = json.loads(Summary("a", "b", (_changed("x.png", OVER),)).to_json())
        assert record["channel_delta"] == 2
        assert record["max_differing_fraction"] == 0.005
        assert record["files"][0]["over_bound"] is True
        assert record["files"][0]["box"] == [0, 0, 240, 171]

    def test_an_unknown_status_is_refused(self) -> None:
        """A hand-edited record with a status the summary does not know fails loudly."""
        text = Summary("a", "b", (FileDiff("x.png", "added"),)).to_json().replace("added", "lost")
        with pytest.raises(ValueError, match="unknown status"):
            Summary.from_json(text)


class TestMarkdown:
    """The Markdown block: a table row per image, then each changed image's review images."""

    @pytest.mark.parametrize(
        ("diff", "row"),
        [
            (
                _changed("docs/images/hero.webp"),
                "| `docs/images/hero.webp` | 1200x854 | 0.000645 | 37 | 10,20 to 110,90 | local |",
            ),
            (
                _changed("tests/golden/docs/hero.png", OVER),
                (
                    "| `tests/golden/docs/hero.png` | 240x171 | 0.012000 (over 0.005) | 200 "
                    "| 0,0 to 240,171 | widespread |"
                ),
            ),
            (FileDiff("a.png", "added"), "| `a.png` | | added | | | |"),
            (FileDiff("r.png", "removed"), "| `r.png` | | removed | | | |"),
            (
                FileDiff("m.png", "changed", RESIZED),
                "| `m.png` | 50x30 | 1.000000 (size differs) | | | widespread |",
            ),
        ],
        ids=["local", "over-bound", "added", "removed", "resized"],
    )
    def test_each_row(self, diff: FileDiff, row: str) -> None:
        """A row gives the size, the changed fraction (flagged past the bound), max delta, box, extent."""
        assert table_row(diff) == row

    def test_review_images_are_linked_through_the_callers_link(self) -> None:
        """Each review image's path goes through `link`, so a PR body can carry URLs."""
        text = markdown(Summary("a", "b", (_changed("x.png"),)), lambda path: f"https://h/{path}")
        diff_tag = '<img src="https://h/x.png.diff.png" alt="x.png: before, after and difference" width="720">'
        crop_tag = (
            '<img src="https://h/x.png.crop.png" alt="x.png: the most-changed region, close up">'
        )
        assert f"\n\n{diff_tag}\n\n" in text
        assert f"\n\n{crop_tag}\n\n" in text
        assert "1 changed, 0 added, 0 removed" in text

    def test_no_markdown_image_syntax_survives(self) -> None:
        """Review images are `<img>` tags only, the one form the PR-posting tools leave intact."""
        text = markdown(Summary("a", "b", (_changed("x.png"),)), str)
        assert "![" not in text
        assert text.count("<img ") == 2

    def test_the_diff_image_width_is_the_callers(self) -> None:
        """A given width sizes the diff image; the crop image stays at its natural size."""
        text = markdown(Summary("a", "b", (_changed("x.png"),)), str, width=480)
        assert (
            '<img src="x.png.diff.png" alt="x.png: before, after and difference" width="480">'
            in text
        )
        assert '<img src="x.png.crop.png" alt="x.png: the most-changed region, close up">' in text

    def test_a_tag_escapes_its_attributes(self) -> None:
        """A quote or angle bracket in a path cannot end an attribute or the tag early."""
        assert image_tag('a"b<c>.png', 'say "x"', 10) == (
            '<img src="a&quot;b&lt;c&gt;.png" alt="say &quot;x&quot;" width="10">'
        )

    def test_many_changed_images_are_collapsed(self) -> None:
        """Up to the open limit the blocks start open; past it they start collapsed."""
        few = tuple(_changed(f"{n}.png") for n in range(OPEN_LIMIT))
        many = (*few, _changed("last.png"))
        assert markdown(Summary("a", "b", few), str).count("<details open>") == OPEN_LIMIT
        assert markdown(Summary("a", "b", many), str).count("<details open>") == 0

    def test_an_empty_summary_says_nothing_differs(self) -> None:
        """No differing image gives no table."""
        text = markdown(Summary("a", "b", ()), str)
        assert "No image differs." in text
        assert "|---|" not in text
