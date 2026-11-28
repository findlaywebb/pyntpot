# Mutation testing: spec 010 (S5)

Local, advisory (ADR 0012). mutmut 3.8.1 from `HEAD` on `work-010` (base `origin/main`
`e89eff3e`), run in the worktree under `prlimit --as=3500000000`, with the repo's own
`[tool.mutmut]` config and no throwaway worktree.

- **Harness.** mutmut 3.8.1 runs under pytest 9.2.0: its stats pass no longer reads
  `item._nodeid`, so the `pytest<9.2` workaround of #207 was not needed. No test was
  excluded from the run (the #225 property did not interfere).

## The rule (plan S5, implementation note 2)

- **In full:** `Canvas.pixels` and `paper_plate`.
- **Spelling-only, proved by AST, not mutated:** `wash` (body), `letters.nib.nib_brushes`,
  `_sheet`, `_backing_wash`.
- **Mutated and checked against recorded equivalents:** `wash` (the signature that changed)
  and `brush_from_id` (it gains `style = BrushStyle() if style is None else style`).
- **Kept out of the run:** `nib_brushes`, `_sheet` and `_backing_wash` are in `letters` and
  spelling-only; the AST proof below is their evidence, and a mutation run would only
  re-measure the pre-existing `letters` tests.

## Spelling-only proof

Method: parse each function from `origin/main` (`git show`) and from the branch, drop the
docstring, and compare `ast.dump` after normalising the rewrite S2 made. Calls to `Sheet`,
`brush_from_id` and `wash` have their positional arguments turned into keywords by the old
signature's parameter names (the first two of `wash` and `brush_from_id` stay positional, as
they still are) and their keywords sorted; the name `base` is read as `body`. Script: a throwaway in the scratchpad.

| Function | Result |
| --- | --- |
| `letters.nib.nib_brushes` | identical |
| `letters.nib._sheet` | identical (`Sheet(rh, rw, ...)` is `Sheet(w=rw, h=rh, ...)`) |
| `letters.nib._backing_wash` | identical |
| `ink.washing.wash` | body identical; the whole function differs only in its parameter list (`*` before `body`, `pool`, `options`), which is the change itself |

## Scores

Score as ADR 0012 defines it: `(killed + timeout) / tested`; an equivalent still counts as
survived.

| Function | Pattern | Mutants | Killed by the existing suite | Killed by new tests | Equivalent |
| --- | --- | --- | --- | --- | --- |
| `Canvas.pixels` | `…xǁCanvasǁpixels*` | 22 | 18 | 4 | 0 |
| `paper_plate` | `…paper.x_paper_plate*` | 238 | 196 | 30 | 12 |
| `wash` | `…washing.x_wash__mutmut_*` | 203 | 195 | 0 | 8 |
| `brush_from_id` | `…brush.x_brush_from_id__mutmut_*` | 47 | 46 | 0 | 1 |

Round 1 left 4 `Canvas.pixels` and 42 `paper_plate` survivors. No survivor revealed a bug in
`src`. No `no tests`.

## Killed (new tests)

- `tests/unit/ink/test_sheet.py`: `test_a_side_of_one_is_taken` (`Canvas.pixels` 2 to 5, the
  `< 1` bounds).
- `tests/unit/ink/test_paper_exact.py` (new, 105 lines):
  - `test_a_pixel_of_the_strong_warm_plate_is_pinned`: eight pinned RGB values of a strong warm
    plate (the vignette divisor and width, the speck weight, the foxing, the wear).
  - `test_full_wear_clips_to_the_tint_and_leaves_the_middle_alone`: the wear's clip bounds.
  - `test_a_tooth_past_the_range_is_clipped_to_0_to_1`: the final clip.
  - `TestGridLines`: the row and column lines, their crossing, their width, the period, the
    4 pixel floor on the step (a 4.5 step), `max(width, 1)` (display width 0), the opacity
    constant, the line weights and the clip.
  - `test_the_pixel_at_the_speck_level_is_foxed`: `>=` against `>` at the speck level, on a
    77 by 13 sheet where the quantile lands on one pixel's grain.

## Equivalent

- **`wash`** (the same eight as 006's list, whose mutant numbers happen to be unchanged; each
  reason re-checked against the code):
  - 54, 64 (`np.clip(a - blur(a, rim_px), 0.0, None)` and `…, 2.0)`): `a` is in 0 to 1 and a
    blur is non-negative, so `a - blur(a)` never exceeds 1.
  - 67 (`peak >= _RIM_PEAK`): `peak` is a float32 value and `1e-5` is not representable in
    float32, so `peak == 1e-5` never holds.
  - 145 (`bloom(dens, a, None, ...)`): `bloom` names `sheet` in its signature and docstring and
    never reads it.
  - 156 (`blur(dens, 2.6)`): `blur` takes `max(1, round(sigma * 0.95))`; 1.6 and 2.6 both give 2.
  - 166 (`np.clip(m * 2.0, None, 1)`): `sheet.wet` is `fbm`, normalised to 0 to 1, so
    `m * 2.0` is never below 0.
  - 178, 187 (`np.clip(m * 2.0 - 1.0, 0, None)` and `…, 0, 2)`): `sheet.wet` is at most 1.
- **`brush_from_id`** 14 (`rest.rpartition("-")`): the same as 008's `x_brush_from_id__mutmut_9`.
  It runs only after `brush_id_known` holds, so the id has exactly one `-`, where both splits
  agree. The new `style = BrushStyle() if style is None else style` line had no survivor.
- **`paper_plate`:**
  - 54, 79 (`sheet.noise(26.0, )`, `sheet.noise(120.0, )`): `octaves` defaults to 2, the value
    removed.
  - 103, 145 (`np.clip(worn, None, 1)`): `worn` is an exponential times a positive factor, so it
    is never below 0. 212 (`np.clip(..., None, 1)` on the grid line): `rows * 1.0 + cols * 0.55`
    is never below 0.
  - 167, 176 (`fox` upper clip `None` and `2`): `n120` is `fbm` normalised to 0 to 1, so
    `(n120 - 0.80) * 5.0` peaks at 1 less a float32 ulp and the upper clip never acts.
  - 218 (`rows / 1.0`): a boolean divided by 1.0 is the boolean as a float, as `rows * 1.0` is.
    219 (`rows * 2.0`): the sum is clipped to 1 where it was 1 and where it is 2, so the line
    is the same.
  - 45, 138, 210 (`astype(None)` for `astype(F32)`): NumPy reads `None` as float64. Each
    result feeds an in-place multiply into the float32 plate, so it is rounded back to float32;
    the difference is one float32 ulp, which no test of ours can resolve across machines
    (ADR 0051's tolerance is 400 times larger).

## Tests added

About 105 lines for `paper_plate`, 5 for `Canvas.pixels`; under the 150-line bound, so nothing
was filed as an issue note. No test file is past 400 lines.
