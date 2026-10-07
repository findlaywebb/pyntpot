# 0011 — Coverage baseline

Status: accepted

## Context

The project template demands 100 percent coverage. The spec left that as an open
question, and the maintainer answered it on 2026-10-07: a measured baseline that
ratchets, not 100 percent before the first release.

## Decision

Branch coverage of `ink` and `letters` together must be at least 95 percent, and of
`maps` at least 92 percent. CI enforces both in the `checks` job, on both matrix legs
(Python 3.13 and 3.14), as the steps `Coverage gate (ink, letters)` and
`Coverage gate (maps)`. Each is a `coverage report --include=... --fail-under=N` step.
`fail_under` is never set in `pyproject.toml`, because pytest-cov would apply it to the
whole package.

The coverage run is `pytest -m "not golden and not benchmark" --cov`, with `CI` set so
Hypothesis is derandomised. It excludes the golden tests and the benchmarks, so the
figures count only behavioural tests. That matters most for `maps`: a visual-refinement
change regenerates the goldens, so they do not guard it, and a benchmark runs `maps`
code without asserting anything.

Measured at P5.2, after the property tests, each figure identical across two runs per
interpreter (branch coverage, two decimals):

| Scope | Python 3.13 | Python 3.14 |
| --- | --- | --- |
| `ink` + `letters` | 95.49 | 95.38 |
| `maps` | 92.87 | 92.77 |
| whole package | 93.69 | 93.59 |

Each threshold is the lower interpreter's figure rounded down: 95 (3.14) and 92 (3.14).
`coverage report` compares the figure at its default precision of 0 decimals, so it
rounds to the nearest whole percent before comparing and can pass up to half a point
above the true figure. The thresholds are still the rounded-down figures.

## Ratchet

For both thresholds: a commit whose measurement (the lower of the two interpreters) is
`T + 1` or more raises that threshold to the new rounded-down figure in the same commit.
Lowering either needs a superseding ADR.

## Consequences

- Plain `uv run pytest` stays coverage-free, so local loops stay fast.
- A change that adds untested branches to `ink`, `letters` or `maps` fails CI on both
  legs until a behavioural test covers them.
- The whole-package figure is recorded but not gated.
