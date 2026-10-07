"""Tests for the mutation score: literal stats mappings in, summed counts and a score out."""

import pytest

from mutation.score import passes, score, total_counts

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


def test_no_tested_mutant_passes() -> None:
    """An untested run passes any floor."""
    assert passes(None, 0.9)


def test_the_score_divides_caught_by_every_tested_outcome() -> None:
    """Killed and timed-out mutants are caught; survivors, suspicious, untested and segfaults are not."""
    counts = total_counts(
        [_stats(killed=5, timeout=1, survived=1, suspicious=1, no_tests=1, segfault=1, total=40)]
    )
    assert score(counts) == 0.6


@pytest.mark.parametrize(
    ("result", "min_score", "expected"),
    [(0.59, 0.6, False), (0.6, 0.6, True), (0.61, 0.6, True)],
    ids=["below", "at", "above"],
)
def test_the_floor_is_inclusive(result, min_score, expected) -> None:
    """A score below the floor fails; at or above it passes."""
    assert passes(result, min_score) is expected


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
