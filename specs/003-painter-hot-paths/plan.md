# 003 — plan

## Approach

Seven bit-identical rewrites in `ink`, each found by profiling the Lynmouth paint and proven
on the arguments that paint passes in, plus one encoder setting that changes file bytes but
not pixels, under a new ADR. The research (2026-10-27) wrote each rewrite as a diff in the
session scratchpad (`$HOT` below); they are applied as written, with the corrections this
plan names. No `maps` or `letters` file changes; layering untouched; no public name is added
(the one new method is private), so no API ADR.

`$HOT` = `/tmp/claude-0/-home-user-pyntpot/0b03af6e-7af7-5cb5-85f8-fdca231f628b/scratchpad/hot`.

The shared idea: the painter spends most of its time on pixels that hold nothing (2.5 % of
an ink pad is laid; about 20 % of a pigment layer is painted), on strided memory and on
copies. Every rewrite keeps each pixel's float32 operations and their order, and every
generator is drawn exactly as before. The plan review (round 1) applied all of them to a copy
of `HEAD`: the Lynmouth `paint_fixture` fell from 55.8 s to 22.1 s and its peak RSS from
1688 MB to 925 MB.

| # | Rewrite | Diff (`git apply` level) | Saving per Lynmouth paint |
|---|---|---|---|
| R1 | `pad.ink_density`: evaluate saturate-and-gate only where `acc != 0` (all pixels when `b.dry > 1`), scatter into zeros, bleed over the full array as before | `$HOT/pad/pad.diff` (`-p1`), applied with R2 | ~10 s |
| R2 | `Sheet._paper_on(h, w)`: the bilinear grow of `paper` cached per shape on the sheet, read-only; `pad._grow` deleted | `$HOT/pad/sheet.diff` (`-p1`), renamed from `paper_on` to `_paper_on` in both files. `$HOT/io/pad_grow_cache.diff` is an alternative fragment: not applied | ~1.5 s |
| R3 | `noise.blur`/`_box1`: above a size threshold, each pass fills a transposed edge-padded buffer by slicing and runs the sequential sum as contiguous row adds; below it, the current `np.pad` + `np.cumsum` path, unchanged | `$HOT/noise/noise.diff` (`-p1`), the `_box1`/`blur` hunks, plus the threshold below | ~7.5 s |
| R4 | `noise.value_noise`, `_value_noise_at`, `fbm`: interpolate along x once per lattice row then gather rows (output stays float64, as today); flat `take` gathers; in-place octave add | `$HOT/noise/noise.diff`, the other hunks | ~2.2 s |
| R5 | `pigment.km_rt`, `km_plate`: glaze only painted pixels (zero density gives r = 0, tr = 1 exactly); in-place buffers in the same order | `$HOT/pigment/km.diff` (`-p1`) | ~3.3 s |
| R6 | `raster.fill_cov`: whole-ring vectorised crossings, one integer `np.add.at` per ring; supersample by strided `uint16` sums and one float32 division | `$HOT/raster/raster.diff` (`-p0`), plus the finite-coordinate check below | ~2.3 s |
| R7 | `deposit.deposit`: flat indices into flat views of the accumulators | `$HOT/raster/deposit.diff` (`-p0`), plus the contiguity fallback below | ~0.6 s |
| W1 | `io.save_webp`: lossless at `method=1, quality=40` instead of `method=5`. Opaque lossless decodes exactly at every method; files 0.2 to 1.6 % smaller. `save_alpha` and `save_rgba` stay at method 4 | by hand (`$HOT/io/webp.diff` is a fragment) | ~2.1 s |

### Corrections to the research diffs

- **R3 threshold (CodSpeed).** CodSpeed runs in simulation and counts instructions; the
  row loop costs more instructions on small fields (the review measured one 512² `blur` at
  18.7M → 39.3M instructions and one `wash()` at 86.7M → 166.2M). So `blur` keeps today's
  path for fields of fewer than `_ROW_SUM_MIN_CELLS` cells and uses the row loop at or
  above it. Set it by measurement (task list): the wall-time crossover on 2-D float32 fields
  from 256² to 1800×1457, rounded up to a power of two, and never below 2²⁰. Every ink
  benchmark field is 512² (2¹⁸) and the maps `paint` benchmark's plate, at 450 px with
  `supersample = 2`, is about 900 × 728 (655k cells), so both keep the old path; the
  Lynmouth plate (2.6M cells) takes the row loop. If no crossover exists below 1800×1457,
  use 2²¹. Both paths are bit-identical, and
  a property test says so.
- **R6 non-finite coordinates.** The old code raised `ValueError` (NaN) or `OverflowError`
  (inf) from `math.ceil`; the vectorised code would warn on an invalid cast or clip
  silently. `fill_cov` raises `ValueError` naming the ring when any coordinate is not
  finite, before any work.
- **R7 contiguity.** The flat views need C-contiguous accumulators; `stamp` is public and
  accepted any `acc` before. When `acc` or an aux array is not C-contiguous, `deposit`
  takes today's 2-D `np.add.at` path, unchanged.
- **R2 naming.** `paper_on` → `_paper_on`: `Sheet` is exported (ADR 0007) and a new public
  method would need an ADR and a reference entry; a private helper shared inside `ink`
  needs neither.

Rejected in research, not revisited: `sinh`/`cosh` from one `exp`, `np.bincount` for
`np.add.at`, sliding-window sums, masked-sum statistics (all reorder float arithmetic);
`chamfer_distance` (no gain); one `Sheet` shared by `paint` and `letter` (their `gran_px`
differ, and a cross-call cache is module state); the `fetch` loops (0.3 s of wall time; the
2.7 s CodSpeed figure is its instruction-count simulation).

## Files to touch

- `src/pyntpot/ink/pad.py` — R1, R2's call site; module docstring updated (names `_grow`).
- `src/pyntpot/ink/sheet.py` — R2; docstring states the cache, that it is read-only, and
  that `paper` is never written after construction.
- `src/pyntpot/ink/noise.py` — R3 (with `_ROW_SUM_MIN_CELLS`), R4. `blur`'s docstring
  says it takes a 2-D field (every caller does).
- `src/pyntpot/ink/pigment.py` — R5; `km_rt`'s docstring: a 1-D density gives `(n, 3)`.
- `src/pyntpot/ink/raster.py` — R6 (`_edge` → `_crossings`; `import math` dropped; the
  finite check).
- `src/pyntpot/ink/deposit.py` — R7 with its fallback.
- `src/pyntpot/ink/io.py` — W1, with the reason in a comment.
- `docs/decisions/0043-lossless-plate-effort.md` — new ADR: opaque lossless plates trade
  encoder effort for speed at identical pixels; RGBA plates stay at method 4 because any
  other method changes the RGB stored under alpha 0; which pins moved, once.
- Re-pinned (W1 only): `tests/golden/lynmouth/paper.webp`, `wash.webp`, `plates.json`
  (only its `sizes` and `bytes` may change), by
  `PYTHONPATH=tests uv run python tests/golden/make_golden.py tests/golden/lynmouth`;
  `tests/golden/smoke/wash.webp` and `SMOKE_SHA["paper"]`, `SMOKE_SHA["wash"]` in
  `tests/unit/maps/painter/test_smoke.py`, from the smoke box painted by the snippet in the
  task list. Any other failing pin is a defect in a rewrite, never a re-pin.
- Tests: `tests/unit/ink/test_pad.py`, `test_sheet.py`, `test_pigment.py`, `test_raster.py`,
  `test_deposit.py`, `tests/property/test_noise.py` (below).
- `docs/explanation/performance.md` — drop "does not optimise it yet"; a section with the
  before and after profile and peak RSS of the Lynmouth paint and the Skye card, the CI
  times from 002 and from this change, and the local benchmark table re-measured on this
  commit.
- `docs/features/tests-fast-gates.md` — deleted; the PR says `Closes #81`.
- New notes, each with a GitHub issue (labels: `performance` + area), for the leads #81
  carried that this work does not do: `docs/features/tests-shared-lynmouth-paint.md`
  (about nine Lynmouth paints per golden run), `docs/features/tests-golden-shards.md`
  (macOS golden is now the slowest gate at about 16 minutes on two workers; sharding or
  path filters), `docs/features/ink-tip-row-sums.md` (`ink/tip.py`'s cumsums, the R3
  technique). Per-gate time budgets are rejected, as the maintainer chose (002).
- `specs/003-painter-hot-paths/tasks.md` — ticked as the work lands.

## Files to leave alone

- `src/pyntpot/maps/**`, `src/pyntpot/letters/**`, `ink/tip.py`, `chamfer_distance`.
- `save_alpha`, `save_rgba`, every lossy write.
- Docs images and masters, `map.png`, the pen and labels plates: if one changes, a rewrite
  is wrong.
- Tolerances, `--golden-tolerance`, every budget.

## Verification

### The reference tree

Before the first rewrite: `git worktree add $SCRATCH/main-ref origin/main`, where `$SCRATCH`
is the session scratchpad. The equivalence scripts import the old modules from
`$SCRATCH/main-ref/src` and the new from the branch, in one process, by loading each file
with `importlib.util.spec_from_file_location` under distinct names. The research scripts'
captured inputs (`$HOT/<area>/cap*`, `caps.pkl`, `calls.pkl`) are reused; each area's
check is its existing script (`$HOT/pad/final_check.py`, `$HOT/noise/verify_proposed.py`,
`$HOT/pigment/bench.py`, `$HOT/raster/cmp_fill.py` and `cmp_dep.py`) edited only to load old
from the reference tree. Pass condition, per rewrite: every captured call's outputs equal
bit for bit (`array_equal` on a `uint32`/`uint64` view), same dtype and shape, and the
generator state equal after each call where one is drawn.

### The SIMD caveat

R5 and R1 rely on an element-wise ufunc giving the same value for an element wherever it
sits in an array. CI's goldens are tolerance-only, so the one check off this machine's
AVX-512 path is local, under `NPY_DISABLE_CPU_FEATURES="X86_V4 AVX512_ICL AVX512_SPR"`
(numpy then reports `found: ['X86_V3']`, AVX2). The committed pins are not the reference
there (on AVX2 `main` itself differs from them, ADR 0030); the reference tree is:

- paint the fixture from each tree into its own directory:
  `PYTHONPATH=<tree>/src:<tree>/tests uv run python <tree>/tests/golden/make_golden.py <out>`;
- `pen.webp`, `labels-centreline.webp`, `map.png` and the label list are byte-identical
  between the two; `paper.webp` and `wash.webp` decode `np.array_equal` (their bytes differ
  by W1 alone);
- the R1 and R5 equivalence scripts pass under the same setting.

Recorded in the PR.

### The W1 re-pin

After `make_golden.py` rewrites the Lynmouth goldens and the smoke box is repainted:
`git diff --stat` lists only `paper.webp`, `wash.webp`, `plates.json`,
`tests/golden/smoke/wash.webp` and `test_smoke.py`; in `plates.json` only `sizes` and
`bytes` changed (diff the parsed JSON); and each re-pinned image decodes to an array equal
(`np.array_equal`) to the decode of its `git show HEAD:<path>` copy. Recorded in the PR.

### Invariant tests (no pinned hash, no mock)

- R1 (`test_pad.py`): with bleed off and no tooth aux, an accumulator laid in a patch gives
  density `+0.0` outside it (value and `np.signbit` false), and inside equals the same
  expressions evaluated by the test itself. The guard: with `dry = 1.2`, bleed off, no
  tooth aux and paper low enough that the gate's clip gives 0 (so the gate is
  `1 - dry < 0`), the density outside the patch is `-0.0` (`np.signbit` true), which is
  the full-grid result the guard keeps.
- R2 (`test_sheet.py`): `_paper_on(h, w)` returns the same object twice, is read-only,
  equals a test-local Pillow bilinear grow of `paper`, and a second shape gets its own
  entry. (New behaviour, so it is written with R2, not before it.)
- R3 (`tests/property/test_noise.py`): Hypothesis over 2-D float32 fields (shapes 1 to
  64 per side, radii 1 to 9): the row-loop path equals a test-local `np.pad` +
  `np.cumsum` box pass bit for bit, and `blur` on both sides of the threshold (calling the
  path functions directly, so the threshold need not be crossed) equals that oracle.
- R4: `value_noise` equals a test-local copy of today's four-gather formula on seeded
  inputs, and leaves the generator in the state one `random((gh, gw))` draw does.
- R5 (`test_pigment.py`): a zero-density layer leaves the base bit-identical; a layer
  painted in a patch leaves the rest bit-identical and inside equals `km_rt` of the full
  plate at those pixels.
- R6 (`test_raster.py`): a ring and its reversal fill the same coverage; a ring off the
  canvas fills nothing; a NaN or inf coordinate raises `ValueError`.
- R7 (`test_deposit.py`): on a non-square accumulator (for example 5 × 9) with `res` and
  `tooth`, a stamp's deposits land at the same pixels in all three accumulators as on a
  non-contiguous copy (which takes the 2-D path).
- W1: already covered by `tests/unit/ink/test_io.py::test_a_webp_is_written_lossless`; the
  RGBA setting is pinned by the exact golden bytes of `pen.webp` and
  `labels-centreline.webp`.

### Gates

1. After each rewrite: its equivalence script passes; `uv run pytest -n auto --dist
   loadgroup -m "not golden and not benchmark"` green; exact golden `uv run pytest -m
   golden -n auto --dist loadgroup` green (after W1, once re-pinned).
2. `prek run --all-files`, `ruff`, `ty`, `lint-imports`.
3. Instruction counts, local: one script per benchmark callable (built as
   `tests/benchmarks/` builds it), run under `valgrind --tool=callgrind` once with
   `PYTHONPATH=$SCRATCH/main-ref/src` and once with the branch's `src`; the per-call cost
   is the total for N calls minus the total for 0 calls. No benchmark may count more
   instructions than the old by more than 5 %. Benchmark → rewrite map: sheet → R4 (via
   `fbm`, no blur); distance transform → none; stamps → R7; washes → R3, R4;
   compositing → R5; letters → R1, R2, R3 (the nib wash blurs); maps `paint` → all;
   `fetch` → none.
4. Before and after: `cProfile` and peak RSS of `paint_fixture` and of the Skye card; wall
   time of the local golden run; `uv run pytest -m benchmark --benchmark-enable`.
5. CI: every check green; CodSpeed `paint` falls and no benchmark regresses past its
   threshold; the macOS golden (tolerance) passes with the re-pinned plates.

Acceptance map: profiles and RSS → gate 4 and the docs page; pixels exact → gate 1 and the
untouched docs pins; byte change under an ADR → W1, ADR 0043, the re-pin checks; CodSpeed →
gates 3 and 5; bit-identical evidence → the reference-tree scripts and the SIMD run in the
PR; invariants → the tests above; docs, note, issue → the docs page, the deleted note,
`Closes #81` and the three new notes.

## Delegation

The diffs exist, so applying them is mechanical and stays in the main context, one commit
per row of the table (R1 and R2 together, since one diff carries both; R3 and R4 in two
commits, split by hunk), so a failing gate names its rewrite. Golden runs and callgrind go
to background shells. A fresh-context diff review against this plan runs before the PR.

## File-ownership partition

One track: reference tree → R5 → R6 → R7 → R4 → R3 (with the threshold measurement) →
R1 + R2 → W1 with ADR 0043 and the re-pins → SIMD run → callgrind → measurements → docs and
notes → diff review → PR. No concurrent work.

## Decisions

- W1 at `method=1, quality=40`: methods 1 to 3 give identical bytes and quality 40 equals
  50, at under half the time and slightly smaller files.
- R2's cache lives on the `Sheet` (one per paint) and is private.
- No new pinned hashes (#86); invariants, oracles and the exact golden run instead.
- R3 keeps both paths behind a size threshold rather than being dropped: the row loop is
  the largest single saving at map sizes, and the old path stays where it is cheaper.
- R6 raises on non-finite coordinates, as the old code did by accident; R7 keeps the old
  path for non-contiguous accumulators.
- Plan review round 1: BLOCK (4 blocking, 6 should-fix); round 2: BLOCK (1 blocking, 4
  should-fix); round 3: PASS. All taken.
