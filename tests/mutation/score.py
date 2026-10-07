"""Sum mutmut's CI stats across runs and report the mutation score, advisory.

Run from the repository root as
`uv run python tests/mutation/score.py STATS [STATS ...] [--summary PATH]`, each `STATS`
a `mutmut-cicd-stats.json` from `mutmut export-cicd-stats`. It sums the counts, logs them
and the score, and appends a Markdown summary to `PATH` when given. The score is advisory:
there is no threshold, and a low score never fails the run. Exit codes: 0 when the stats
were read (whatever the score, and also when no mutant was tested), 1 when a stats file
cannot be read, 2 when no `STATS` is given.

Key types: a stats mapping holds mutmut's per-status counts (`killed`, `survived`,
`no_tests`, `timeout`, ...). The score is
`(killed + timeout) / (killed + timeout + survived + suspicious + no_tests + segfault)`:
a timeout counts as caught, and a mutant no test reaches counts against the score,
because an untested mutant is an untested line.

Invariants: `total` is never summed, because a pattern-restricted run counts every
generated mutant there, tested or not; the counts summed here are only the tested ones,
so several shards' files add up to one full run's counts.

It does not read mutmut's `.meta` files or run mutmut.
"""

import argparse
import json
import logging
from collections.abc import Iterable, Mapping
from pathlib import Path

logger = logging.getLogger("mutation.score")

#: The mutant outcomes caught by the tests.
CAUGHT = ("killed", "timeout")
#: The tested outcomes the score divides by: the caught ones and the rest.
COUNTED = (*CAUGHT, "survived", "suspicious", "no_tests", "segfault")


def total_counts(stats: Iterable[Mapping[str, int]]) -> dict[str, int]:
    """Sum the counted outcomes across stats files; `total` is left out."""
    totals = dict.fromkeys(COUNTED, 0)
    for one in stats:
        for key in COUNTED:
            totals[key] += one[key]
    return totals


def score(counts: Mapping[str, int]) -> float | None:
    """Return the share of tested mutants caught, or `None` when none was tested."""
    tested = sum(counts[key] for key in COUNTED)
    if tested == 0:
        return None
    return sum(counts[key] for key in CAUGHT) / tested


def summary(counts: Mapping[str, int]) -> str:
    """Return the Markdown run summary: score, survivor count and the tested outcomes."""
    title = "## Mutation score (advisory)\n\n"
    result = score(counts)
    if result is None:
        return title + "- No mutants tested.\n"
    tested = sum(counts[key] for key in COUNTED)
    detail = ", ".join(f"{key} {counts[key]}" for key in COUNTED)
    return (
        f"{title}- Score: {result:.4f}\n- Survivors: {counts['survived']}\n"
        f"- Tested: {tested} ({detail})\n"
    )


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Sum mutmut CI stats and report the score.")
    parser.add_argument("stats", nargs="+", type=Path, metavar="STATS", help="stats JSON")
    parser.add_argument("--summary", type=Path, metavar="PATH", help="append a Markdown summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Log the summed counts and the score; return 1 for an unreadable file, else 0."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    stats = []
    for path in args.stats:
        try:
            one = json.loads(path.read_text(encoding="utf-8"))
            total_counts([one])
        except (OSError, ValueError, KeyError):
            logger.exception("cannot read stats %s", path)
            return 1
        stats.append(one)
    counts = total_counts(stats)
    logger.info("counts: %s", ", ".join(f"{key} {value}" for key, value in counts.items()))
    result = score(counts)
    if result is None:
        logger.info("no mutants tested")
    else:
        logger.info("mutation score %.4f (advisory)", result)
    if args.summary is not None:
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(summary(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
