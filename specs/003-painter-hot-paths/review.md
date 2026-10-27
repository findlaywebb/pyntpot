# 003 — plan review, round 1

**Verdict: BLOCK.** The approach holds up and the exactness arguments are sound (checked
below). The most important change: **R3 (the transposed row-loop blur) is very likely to
fail the spec's "no CodSpeed benchmark regresses" criterion.** The plan only checks this
in CI and says nothing about what to do if it fails. Three smaller blockers are about
whether the steps can be run and checked as written.

## What I checked, and what held

I applied the six real diffs to a clean copy of HEAD, plus W1 by hand. All of them apply
cleanly (`pad.diff`, `sheet.diff`, `noise.diff` and `km.diff` with `-p1`; `raster.diff`
and `deposit.diff` with `-p0`). `ruff check`, `ruff format --check` and `ty check` are
green. The touched files come to 260, 166, 280, 227, 171, 187 and 150 lines, all under 400.

I then ran the whole suite with `-m "not benchmark"`, exact goldens included. Exactly six
tests failed, all of them the expected paper/wash pins: `test_parity[paper.webp]`,
`test_parity[wash.webp]` and the four smoke tests that read `SMOKE_SHA["paper"]` or
`SMOKE_SHA["wash"]`. Everything else passed: pen, labels, `map.png`, docs images and
masters, places, map styles, the size test (lossless more than 4× lossy), and
`CLASSIC_PLATE_SHA` in `tests/unit/ink/test_paper.py`. The docs images use their own
encoder (`make_docs_images.py`, method 5) and docs budgets only shrink. Decoded Lynmouth
paper and wash pixels are identical to the committed goldens. The only `plates.json` keys
that change are `sizes` and `bytes`.

On this machine, peak RSS of `paint_fixture` falls from 1688 MB to 925 MB, and wall time
from 55.8 s to 22.1 s. R2 keeps about 94 MB per sheet alive, but R1 removes several
temporaries of the same size, so the 002 macOS memory concern does not get worse.

The exactness arguments, checked one by one:

- **R1.** Where `acc == 0`, `1 - exp(-0)` is exactly +0. The gate lies in `[1-dry, 1]`,
  so it is ≥ 0 when `dry ≤ 1`, and +0 × gate = +0. A NaN `dry` fails `<= 1.0`, so it takes
  the full path. The tooth statistics run over the same `acc > 0` elements in the same C
  order, so `mean` and `std` are bit-equal. This assumes the paper is finite: a NaN paper
  pixel gave NaN before and gives 0 now.
- **R3.** `add.accumulate` is sequential and float32 `+` is commutative, so the row loop
  gives the same sums as `cumsum`. A float64 input was already cast to F32 before the
  sum. The output is C-contiguous in old and new code alike, so later `.mean()`/`.sum()`
  calls are unaffected.
- **R4.** `xs - x0` (float32 minus int32) promotes to float64 in both versions. The
  operations per pixel are the same; only one addition swaps operand order, which is
  exact. The output stays float64.
- **R5.** At density 0, `sinh = 0` and `c = bf` (`bf ≥ 3.2e-5 > 1e-9`), so `r = 0` and
  `tr = 1`, both exactly, and `out` is unchanged (except that a -0 base pixel stays -0).
  On this machine `exp`, `sinh` and `cosh` give the same bits regardless of position,
  stride or tail.
- **R6.** Integer `add.at` gives the same result in any order, even when int16 wraps.
  Clipping r0 and r1 to `[0, hs]` skips the same edges as before. Old code divided in
  float64 then rounded to float32; new code divides in float32. These agree because
  53 ≥ 2·24+2.
- **R7.** Same elements in the same order; `copy=False` raises rather than writing into a
  copy.
- **RNG.** No rewrite adds, drops or reorders a draw.
- **W1.** An opaque image has no hidden RGB. Only `save_webp` changes, and its only
  writers are the paper and wash plates and `save_image`.

## [BLOCKING]

**B1. R3 will probably show as a CodSpeed regression, and the plan has no gate or
fallback for it.** CodSpeed runs in simulation mode, which counts instructions and cache
misses. R3 replaces one C `cumsum` with about `w + 2r + 1` Python-level ufunc calls per
pass.

I measured with callgrind on a 512² field at σ 2.4, the size the `tests/benchmarks/test_ink.py`
wash benchmarks use:

| Measure | Old | New |
|---|---|---|
| Instructions per `blur` | 18.7 M | 39.3 M |
| L1 misses per `blur` | 2.6 M | 3.5 M |
| Instructions per `wash()` | 86.7 M | 166.2 M (+92 %) |

Wall time does improve at that size (9.3 → 5.8 ms), but it gets worse for narrow fields
(40×2000: 2.5 → 5.3 ms). `test_laying_a_wash` and `test_laying_a_wet_wash` will probably
fail the acceptance criterion.

*Fix:*
- Add a local instruction-count check to step 4, run before and after R3:
  `valgrind --tool=callgrind` on the ink benchmarks' callables, or the two-run
  subtraction used here.
- Prescribe what to do if it regresses. Either dispatch by size — keep the `np.cumsum`
  `_box1` path below a threshold you measure (both paths are bit-identical), with a
  Hypothesis test that the two paths are `array_equal` — or drop R3.
- Say which benchmarks each rewrite touches, so a CodSpeed regression points to its
  rewrite.

**B2. The W1 re-pin checks itself, and the smoke plate has no regeneration script.**
- After `make_golden.py` rewrites the golden directory, the exact golden run compares the
  output against those new pins, so it no longer proves the spec's "unchanged as pixels".
- `make_golden.py --compare` cannot prove it either: `differing_fraction` uses
  `MAX_CHANNEL_DELTA = 2`, so it tolerates small pixel differences.
- `make_golden.py` also rewrites every output and the whole `plates.json`, so a
  `dark`-grid or hash change would be silently accepted.
- "Regenerated by the repo's own scripts" is not possible for `tests/golden/smoke/wash.webp`
  and the two `SMOKE_SHA` values: no script writes them.

*Fix:* prescribe the W1 step exactly.
- (a) Before re-pinning, decode the new `paper.webp`/`wash.webp` and compare them with
  `np.array_equal` against `git show HEAD:tests/golden/lynmouth/{paper,wash}.webp`.
- (b) `git diff --stat` must show only `paper.webp`, `wash.webp` and `plates.json`.
  In `plates.json`, only `sizes` and `bytes` may differ.
- (c) Give the exact snippet for the smoke box: `paint_plates(*smoke_box()…)` into a temp
  directory, copy `wash.webp`, sha256 paper and wash. Check that the new smoke wash
  decodes to the same pixels as the committed one.
- (d) Record (a) to (c) in the PR.

**B3. "Re-run the research capture scripts against the branch" does not work as worded.**
The scripts take "old" from `/home/user/pyntpot/src` (for example `pad/final_check.py`,
`raster/cmp_fill.py`, `noise/verify_proposed.py`) and "new" from scratch files. Once the
branch edits `src`, they compare the new code with itself, or with the scratch copy.

*Fix:*
- Name the old reference: a `git worktree` of `main`, or `git show main:<path>`, loaded by
  `spec_from_file_location`.
- Name, per rewrite, which script to run and its pass condition: bit-equal output, dtype,
  shape, and generator state.
- Run each one once more with `NPY_DISABLE_CPU_FEATURES=X86_V4` (the AVX2 dispatch, as
  ADR 0030 does). That is the only cheap check of the SIMD-position caveat, because CI's
  goldens are tolerance-only and cannot detect an exact drift.

**B4. The plan does not say which diff applies to which rewrite.** It refers to "the
scratchpad's hot/ folders" without an absolute path. There are two R2 variants,
`pad/sheet.diff` and `io/pad_grow_cache.diff`; the second is a fragment, a dataclass
field with a too-long line. `io/webp.diff` is also a fragment, not a patch, and its
comment says "ADR NNNN".

*Fix:* add a table mapping each rewrite to its absolute diff path and `-p` level:
- R1, R2: `pad/pad.diff` and `pad/sheet.diff`, `-p1`.
- R3, R4: `noise/noise.diff`, `-p1`.
- R5: `pigment/km.diff`, `-p1`.
- R6, R7: `raster/raster.diff` and `raster/deposit.diff`, `-p0`.
- W1: applied by hand.
- `io/pad_grow_cache.diff` and `io/fetch.diff` are not applied.

`noise.diff` changes R3 and R4 together, so the plan's one-commit-per-rewrite order needs
it split by hunk; say so. List the corrections by name: the `km_rt` 1-D docstring, and
ADR 0043 in the W1 comment.

## [SHOULD-FIX]

**S1. Some of the planned invariant tests don't hold on the old code, or can't run
against it.**
- **R3:** "blur of a constant is that constant everywhere" is false exactly. With c = 0.3
  the error reaches 3e-6, which is why the existing property test uses `approx`. The
  constant test and the input-unchanged test already exist in `tests/property/test_noise.py`.
  The tests R3 needs instead: a test-local oracle (`np.pad` edge plus `np.cumsum` along
  axis 1 then axis 0, three times) checked `array_equal` under Hypothesis. Include
  non-square shapes, `r` larger than the side, and a float64 input.
- **R1:** say `bleed=False`, or a brush with `bleed ≤ 0.4`; otherwise the area outside the
  patch is not 0. Use `aux=None` or `res`-only, because the tooth statistics are global.
  Assert `np.signbit` is False outside the patch, because `==` passes for -0. Replace the
  `dry > 1` test, which asserts nothing, with: low paper and `dry = 1.2` gives -0
  (signbit True) at an unlaid pixel, as the old code does.
- **R2:** these tests cannot pass on the old code. Say "red then green" here.

**S2. The R7 test cannot catch the bug R7 could introduce.** The existing deposit tests
are 8×8, so swapping h and w in the flat index would go unnoticed. *Fix:* use a
non-square accumulator (for example 5×9), with literal expected weights in `acc`,
`aux["res"]` and `aux["tooth"]`.

**S3. The plan says "no public API changes", but there are two.**
- `Sheet` is exported at the top level (ADR 0007), so `Sheet.paper_on` is a new public
  name, and `docs/reference/ink.md` renders `::: pyntpot.ink.Sheet`. It also adds a new
  contract to a mutable public dataclass: "`paper` is never written after construction".
- R7 makes public `stamp` raise on a non-contiguous `acc` (for example `acc[:, 10:50]`),
  which used to work.

*Fix:* make the Sheet method private, or record it in ADR 0043 or a separate ADR. For
`stamp`, either fall back to the 2-D `add.at` when `acc` is not C-contiguous, or state
the precondition in the docstrings of `stamp` and `deposit`.

**S4. Deleting `tests-fast-gates.md` and closing #81 drops leads nobody has handled:**
the Lynmouth map painted about nine times per golden run (named in the spec's Problem),
golden sharding, and per-gate time budgets. *Fix:* file a note and an issue for each, or
explicitly reject them, before the deletion. Not only `ink/tip.py`.

**S5. Record memory in step 4.** Add peak RSS (`ru_maxrss`) of `paint_fixture` and the
Skye card before and after, given the 7 GB / 2-worker macOS constraint. The measurement
here (1688 → 925 MB) suggests it is a win; put it in the docs table.

## [CONSIDER]

- The R3 oracle-test pattern also fits R4 (four-corner form), R6 (scalar `_edge`) and R7
  (2-D `add.at`). With it, "bit-identical in general" becomes a committed property instead
  of a one-off script on 2 GB of pickles that will be deleted with the scratchpad.
- W1's planned test duplicates `test_a_webp_is_written_lossless` in `tests/unit/ink/test_io.py`.
- R6 on NaN or inf ring coordinates: the old code raised `ValueError` from `math.ceil`.
  The new code clips inf silently, and a NaN casts to `INT_MIN`, which risks a huge
  `np.repeat`. A one-line `isfinite` check keeps it failing loudly.
- The re-pinned smoke paper SHA must also match on macOS CI (ADR 0030 keeps paper exact
  in tolerance mode). Method 5 is platform-stable today; say what to do if method 1 is
  not.

---

# Round 2

**Verdict: BLOCK, on one item that is a two-line fix.** Every round-1 blocker and
should-fix item has been taken properly. What remains is mostly about whether the
verification steps can actually be run as written. I checked the new claims against the
code and against runs on the patched copy from round 1.

## [BLOCKING]

**1. The SIMD check uses feature names that leave AVX-512 on, and it relies on a test that
fails on the old code too.**

The flags first. With numpy 2.5.2 and the plan's list
(`AVX512F AVX512CD AVX512_SKX AVX512_CLX AVX512_CNL AVX512_ICL AVX512_SPR`), numpy still
reports `found: ['X86_V3', 'X86_V4']`. Only ICL and SPR are switched off, and the X86_V4
(AVX-512) dispatch stays, so the run tests nothing new. The setting that does select AVX2
is `NPY_DISABLE_CPU_FEATURES="X86_V4 AVX512_ICL AVX512_SPR"`, which reports
`found: ['X86_V3']`.

Now the test. Under that correct setting, the **old** code (`main`) fails the exact
`test_parity.py`: `wash.webp`, `labels-centreline.webp` and `map.png` all differ from the
pins, as ADR 0030 records for wash. So "run `test_parity.py` under the flag, old and new
both under it" cannot pass.

*Fix (replace the "SIMD caveat" paragraph and its task line):*
- Under `NPY_DISABLE_CPU_FEATURES="X86_V4 AVX512_ICL AVX512_SPR"`, paint the fixture from
  the reference tree and from the branch:
  `PYTHONPATH=<tree>/src:<tree>/tests uv run python tests/golden/make_golden.py <out>`,
  once for each tree.
- Compare the two output directories, not the committed pins. `pen.webp`,
  `labels-centreline.webp`, `map.png` and the labels must be byte-identical. `paper.webp`
  and `wash.webp` must decode `np.array_equal`; their bytes differ by W1 alone.
- Run the R1 and R5 equivalence scripts under the same setting.

I ran this comparison on the round-1 patched copy. It passes: every output is
pixel-identical, the three non-W1 outputs are byte-identical, and the labels are equal.

## [SHOULD-FIX]

**2. The re-pin command will not run as written.** `make_golden.py` needs a positional
`OUT` and imports `golden.test_parity`, so it needs `tests` on the path. The `pythonpath`
setting in `pyproject.toml` applies only under pytest. Write it out:
`PYTHONPATH=tests uv run python tests/golden/make_golden.py tests/golden/lynmouth`.
Fix both the plan and `tasks.md`.

**3. The R3 threshold rests on a false statement.** The plan says "every maps benchmark
paints at 450 px, so they keep the old path". But `class_style` keeps `supersample = 2`,
so the `paint` benchmark renders at about 900 × 728, which is 655k cells and above 2¹⁹.
Its plate-size blurs take the row loop. Gate 3 still covers this, because `paint` is
measured as a whole and R1 dominates. But the sentence should be corrected so the
threshold decision isn't made on a wrong premise. Either state that `paint` exercises the
row loop, or set the floor above the benchmark plate, for example 2²⁰. The Lynmouth plate
at 2.6M cells stays above the fallback of 2²¹ either way.

**4. The callgrind gate points at scripts that measure the wrong code.** `cg.py` and
`cgw.py` in `$SCRATCH/review/` time my own scratch reimplementation of R3 (`layout.new_blur`,
no threshold), monkeypatched into `wash`. They do not run the branch. Prescribe instead:
one script per benchmark callable, run under `valgrind --tool=callgrind` once with
`PYTHONPATH` set to the reference tree and once to the branch. Take the per-call cost as
the total for N calls minus the total for 0 calls, as round 1 did.

The benchmark → rewrite map also needs corrections:
- washes touch R3 and R4, not R6 (`fill_cov` is called from `maps`);
- letters also touch R3, because the nib wash blurs;
- the sheet benchmark touches R3 only through `fbm`, which does not blur.

**5. The R1 `dry > 1` test still does not test what the guard protects.** "Paper above its
threshold gives a non-zero gate outside the patch" cannot be seen from outside: there the
saturate term is 0, so the density is ±0 whatever the gate is. The only observable
difference between the paths is the sign of zero, and that needs paper **below** the
threshold. Write it as follows:
- paper low enough that the clip gives 0, so the gate is `1 - dry < 0`;
- `dry = 1.2`, bleed off, no tooth aux;
- assert `np.signbit` is True outside the patch, which is the full-grid result.

## Verified and accepted

- **Diff table and `-p` levels:** match what applies cleanly.
- **`_paper_on`:** private, so no API ADR is needed.
- **R7 fallback:** the 2-D `add.at` path on a non-contiguous `acc` or aux.
- **R6 finite check:** raises `ValueError` on NaN or inf coordinates.
- **New tests:**
  - R3 Hypothesis oracle;
  - R4 test-local four-gather oracle with a generator-state check;
  - R7 non-square test with `res` and `tooth`;
  - W1 relies on the existing `test_a_webp_is_written_lossless`.
- **W1 re-pin checks:** `git show HEAD:` decodes, the `diff --stat` allow-list, and
  parsed-JSON `sizes`/`bytes` only.
- **Bookkeeping:** RSS in gate 4; three new notes with issues; per-gate budgets rejected
  with a reason.
- **`tasks.md`:** follows the plan's order line for line.
