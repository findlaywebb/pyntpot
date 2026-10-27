# 002 — Parallel gates

GitHub issue: [#81](https://github.com/findlaywebb/pyntpot/issues/81) (the gates half; the
painter half is `specs/003-painter-hot-paths/`).

## Problem

Every test runs in one process, one at a time. On `main` the golden workflow takes about
25 minutes on each runner and the CI `checks` job about 3 to 4; locally the golden run
takes 31.6 minutes and the fast run 2 minutes 25 seconds on four cores (measured
2026-10-27). The runners have three or four cores and the tests are independent paints, so
most of that wait is idle cores. A trial run with `pytest-xdist -n 4` over the fast
selection passed all 1578 tests, in random order, in 50 seconds.

## Acceptance criteria

- [x] `pytest-xdist` is a dev dependency, locked in `uv.lock`.
- [x] Plain `uv run pytest` stays serial, so a local failure reads as it does today;
      parallelism is asked for with `-n`.
- [x] The CI `checks` job runs its test step with `-n auto`, coverage still collected and
      both coverage gates unchanged.
- [x] The golden workflow runs `-n auto` on both runners and passes on both.
- [x] A module that paints a whole map in a module-scoped fixture (the Lynmouth parity
      paint and five golden-marked unit modules) paints it once per run, not once per
      worker.
- [x] Benchmarks and the CodSpeed workflow stay serial: timing parallel workers measures
      contention, not code.
- [x] Peak memory per golden runner stays inside the runner's memory; if `-n auto`
      exceeds it on macOS, that runner uses a fixed lower `-n`, stated in the workflow.
- [x] Before and after run times (local fast, local golden, CI `checks`, CI golden on each
      OS) are recorded in the PR description and in `docs/features/tests-fast-gates.md`.
- [x] `CONTRIBUTING.md` and `CLAUDE.md`'s toolchain block name the parallel command.
- [x] Every pin stays exact: no golden, docs image or master is regenerated.

## Out of scope

- Any change under `src/`: the painter's speed is `specs/003-painter-hot-paths/`.
- Sharding the golden job across a matrix of runners or skipping it by path filter: only
  if the measured parallel time leaves a reason to, and then as its own change.
- Sharing one Lynmouth paint across the golden-marked unit tests that each repaint it
  (attribution, CLI, notes, route ink, pipeline): it changes fixture scope rules, so it
  belongs with 003's measurements.
- Mutation testing (`docs/issues/slow-tests-in-mutation-runs.md`, #62).
- A hard time budget on any job: the maintainer chose none (2026-10-27).
