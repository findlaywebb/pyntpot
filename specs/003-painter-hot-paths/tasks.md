# 003 — tasks

Each line follows `plan.md`. After every rewrite: its equivalence script, the fast suite and
the exact golden run (plan, Gates 1).

- [x] Plan passes the plan-reviewer gate (`review.md`: BLOCK, BLOCK, PASS in round 3).
- [ ] Reference tree: `git worktree add $SCRATCH/main-ref origin/main`; the area scripts
      edited to load old modules from it; each passes against itself (old == old).
- [ ] Baseline before any rewrite: `cProfile` and peak RSS of `paint_fixture` and the Skye
      card; local golden wall time; `uv run pytest -m benchmark --benchmark-enable`.
- [ ] R5 (`pigment.py`) + its invariant test in `test_pigment.py`.
- [ ] R6 (`raster.py`, with the finite-coordinate `ValueError`) + tests in `test_raster.py`.
- [ ] R7 (`deposit.py`, with the non-contiguous fallback) + the non-square test in
      `test_deposit.py`.
- [ ] R4 (`noise.py`, value-noise hunks) + the R4 oracle test.
- [ ] R3 (`noise.py`, blur hunks): measure the wall-time crossover from 256² to 1800×1457
      and set `_ROW_SUM_MIN_CELLS` by the plan's rule; the Hypothesis oracle test.
- [ ] R1 + R2 (`pad.py`, `sheet.py`, `paper_on` → `_paper_on`) + tests in `test_pad.py`
      and `test_sheet.py`.
- [ ] W1 (`io.py`) and `docs/decisions/0043-lossless-plate-effort.md`; re-pin:
      `PYTHONPATH=tests uv run python tests/golden/make_golden.py tests/golden/lynmouth`;
      the smoke box repainted with
      `style, basemap = smoke_box(); paint_plates(basemap, style, out)` (from
      `tests/unit/maps/painter/test_smoke.py`, run with `tests` on `sys.path`), its
      `wash.webp` copied to `tests/golden/smoke/` and the `paper` and `wash` sha256 set in
      `SMOKE_SHA`; the re-pin checks (plan, Verification: the W1 re-pin).
- [ ] SIMD run under `NPY_DISABLE_CPU_FEATURES="X86_V4 AVX512_ICL AVX512_SPR"`: both trees
      paint the fixture with `make_golden.py`, outputs compared tree against tree; R1 and R5
      scripts.
- [ ] Callgrind: one script per benchmark callable, old tree against branch, N minus 0
      calls; every benchmark within 5 % of the old or below.
- [ ] After: the same measurements as the baseline.
- [ ] `docs/explanation/performance.md`; `docs/features/tests-fast-gates.md` deleted; the
      three new notes, each with its GitHub issue and the issue link on its second line.
- [ ] `prek run --all-files`, `ruff`, `ty`, `lint-imports`.
- [ ] Fresh-context diff review against the plan; triage.
- [ ] PR `perf(ink): paint without the work on empty pixels` with `Closes #81`, the
      evidence and the measurements; CI green including both golden runners; CodSpeed.
