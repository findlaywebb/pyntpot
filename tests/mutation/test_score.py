"""Tests for the mutation score, which is advisory: literal stats in, counts, a score and a summary out."""

import json
from pathlib import Path

import pytest

from mutation.score import main, score, summary, total_counts

#: The keys of `mutmut-cicd-stats.json`.
STATS_KEYS = (
    "killed",
    "survived",
    "total",
    "no_tests",
    "skipped",
    "suspicious",
    "timeout",
    "check_was_interrupted_by_user",
    "segfault",
)


def _stats(**counts: int) -> dict[str, int]:
    """Return a stats mapping shaped like `mutmut-cicd-stats.json`, zero where not given."""
    assert set(counts) <= set(STATS_KEYS)
    return {key: counts.get(key, 0) for key in STATS_KEYS}


def test_no_tested_mutant_gives_no_score() -> None:
    """A stats file whose counted outcomes are all zero has no score, however large `total`."""
    assert score(total_counts([_stats(total=812)])) is None


def test_the_score_divides_caught_by_every_tested_outcome() -> None:
    """Killed and timed-out mutants are caught; survivors, suspicious, untested and segfaults are not."""
    counts = total_counts(
        [_stats(killed=5, timeout=1, survived=1, suspicious=1, no_tests=1, segfault=1, total=40)]
    )
    assert score(counts) == 0.6


def test_two_shard_files_sum_and_ignore_total() -> None:
    """Counts from two restricted runs add up; each file's `total` counts every generated mutant."""
    first = _stats(killed=3, survived=1, no_tests=1, total=900)
    second = _stats(killed=4, timeout=1, suspicious=1, segfault=1, total=900)
    assert total_counts([first, second]) == {
        "killed": 7,
        "timeout": 1,
        "survived": 1,
        "suspicious": 1,
        "no_tests": 1,
        "segfault": 1,
    }


def test_summary_lists_score_survivors_and_tested_outcomes() -> None:
    """The summary of the six-outcome counts is the pinned Markdown block."""
    counts = total_counts(
        [_stats(killed=5, timeout=1, survived=1, suspicious=1, no_tests=1, segfault=1)]
    )
    assert summary(counts) == (
        "## Mutation score (advisory)\n"
        "\n"
        "- Score: 0.6000\n"
        "- Survivors: 1\n"
        "- Tested: 10 (killed 5, timeout 1, survived 1, suspicious 1, no_tests 1, segfault 1)\n"
    )


def test_summary_of_an_untested_run_says_so() -> None:
    """With no mutant tested the summary says so and gives no score."""
    assert summary(total_counts([_stats(total=50)])) == (
        "## Mutation score (advisory)\n\n- No mutants tested.\n"
    )


def test_main_appends_the_summary_and_returns_zero(tmp_path: Path) -> None:
    """`main` reads a stats file, appends the pinned summary to `--summary` and returns 0."""
    stats = tmp_path / "stats.json"
    stats.write_text(json.dumps(_stats(killed=3, survived=1, total=50)), encoding="utf-8")
    out = tmp_path / "summary.md"
    assert main([str(stats), "--summary", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == (
        "## Mutation score (advisory)\n\n- Score: 0.7500\n- Survivors: 1\n"
        "- Tested: 4 (killed 3, timeout 0, survived 1, suspicious 0, no_tests 0, segfault 0)\n"
    )


def test_a_low_score_still_returns_zero(tmp_path: Path) -> None:
    """The score is advisory: a score of zero does not fail the run."""
    stats = tmp_path / "stats.json"
    stats.write_text(json.dumps(_stats(survived=4)), encoding="utf-8")
    assert main([str(stats)]) == 0


@pytest.mark.parametrize(
    "content",
    [None, "not json", '{"killed": 1}'],
    ids=["missing", "not-json", "missing-key"],
)
def test_main_returns_one_for_an_unreadable_stats_file(tmp_path: Path, content: str | None) -> None:
    """A missing file, invalid JSON or a missing counted key makes `main` return 1."""
    stats = tmp_path / "stats.json"
    if content is not None:
        stats.write_text(content, encoding="utf-8")
    assert main([str(stats)]) == 1
