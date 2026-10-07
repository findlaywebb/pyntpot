"""Sum mutmut's CI stats across runs and gate the mutation score.

Run from the repository root as
`uv run python tests/mutation/score.py STATS [STATS ...]`, each `STATS` a
`mutmut-cicd-stats.json` from `mutmut export-cicd-stats`. It sums the counts, logs them
and the score, and exits 1 when the score is below `[tool.pyntpot.mutation] min_score`
in `pyproject.toml`; with no mutant tested it logs "no mutants tested" and exits 0.

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
import tomllib
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


def passes(result: float | None, min_score: float) -> bool:
    """Return whether a score meets the floor; no mutant tested always passes."""
    return result is None or result >= min_score


def _parse(argv: list[str] | None) -> argparse.Namespace:
    """Parse the command line."""
    parser = argparse.ArgumentParser(description="Sum mutmut CI stats and gate the score.")
    parser.add_argument("stats", nargs="+", type=Path, metavar="STATS", help="stats JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Log the summed counts and the score; return 1 below `min_score`, else 0."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = _parse(argv)
    counts = total_counts(json.loads(path.read_text(encoding="utf-8")) for path in args.stats)
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    min_score = float(pyproject["tool"]["pyntpot"]["mutation"]["min_score"])
    logger.info("counts: %s", ", ".join(f"{key} {value}" for key, value in counts.items()))
    result = score(counts)
    if result is None:
        logger.info("no mutants tested")
    else:
        logger.info("mutation score %.4f, min_score %.4f", result, min_score)
    if not passes(result, min_score):
        logger.error("mutation score is below min_score")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
