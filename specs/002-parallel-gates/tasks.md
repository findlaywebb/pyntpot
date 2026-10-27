# 002 — tasks

Each line follows `plan.md`; step numbers are its test plan's.

- [x] Measure the serial baseline: local fast, local golden, CI `checks`, CI golden (spec).
- [x] Profile one Lynmouth paint; record the hot paths in `specs/003-painter-hot-paths/spec.md`.
- [x] Plan passes the plan-reviewer gate (rounds 1 and 2 in `review.md`).
- [ ] Comment on #81 with the branch name.
- [ ] `pyproject.toml`: `pytest-xdist>=3.8` in the dev group and the `xdist_group` marker
      registered in `markers`; `addopts` unchanged; `uv lock`.
- [ ] `xdist_group("<module name>")` beside the `golden` mark in the six module-paint
      modules (`test_parity`, `test_attribution`, `test_pipeline_letter_compose`,
      `test_notes`, `test_route_ink`, `test_pipeline_fetch_paint`).
- [ ] Step 1: fast selection `-n auto --dist loadgroup` under seeds 1, 2, 3.
- [ ] Step 2: coverage gates under xdist equal the serial percentages.
- [ ] Step 3: golden tolerance timing `-n auto --dist loadgroup`, with RSS logged per process
      (controller and each worker) and cgroup `memory.peak`; apply the macOS rule.
- [ ] Step 4: golden exact `-n auto --dist loadgroup` as a separate pass/fail.
- [ ] Step 5: the six grouped modules `-n 4 --dist loadgroup -vv --durations=0
      --durations-min=10`: one `[gwN]` and one setup of 40 s or more per module.
- [ ] Step 6: `-p no:xdist --co` collects the marked modules.
- [ ] Step 7: plain serial run has no workers.
- [ ] Step 8: `-m benchmark` passes; `-m benchmark --benchmark-enable` exits 0 with a table.
- [ ] Step 9: `prek run --all-files`, `ruff`, `ty`, `lint-imports`.
- [ ] Workflows: `ci.yml` `checks` Tests step `-n auto --dist loadgroup`; `golden.yml`
      `-n ${{ matrix.workers || 'auto' }} --dist loadgroup` (with the macOS `include` only if
      the rule fired, else plain `-n auto`); `publish.yml` both test steps `-n auto --dist
      loadgroup`. Benchmark smoke, `prerelease` and `codspeed.yml` unchanged.
- [ ] Docs: `CONTRIBUTING.md` paragraph, `CLAUDE.md` toolchain line,
      `docs/features/tests-fast-gates.md` times.
- [ ] Fresh-context diff review against the plan; triage.
- [ ] Step 10: PR (title `ci(tests): run the test and golden gates in parallel`), CI green
      on both golden runners, times recorded in the PR body.
