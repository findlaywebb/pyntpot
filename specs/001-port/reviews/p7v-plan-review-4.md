# P7.V plan review 4

## Scope

This review covers "#### P7.V. Revision round 1" in `specs/001-port/plan.md` on
`p7-docs-release` at `92d7cde`, the revision after plan review 3. I read it against
review 3, the source at this commit, and `p7-research.md` sections 10 to 10.5. I checked
out nothing and edited nothing beyond this file.

Where a finding rests on arithmetic, I ran it. I built `Sheet`s with the library's own
code (`uv run --offline python`, scripts in the session scratchpad, nothing written to
the repo) and simulated the plan's `"warm"` formula against the paper code as it stands
(`paper.py:41-61`).

## Round-3 findings: status

| Finding | Status |
| --- | --- |
| B1 (the pen plate read the route ink) | **Resolved.** The pen's gap is `route_pen_width_px * STRAND_GAP_WIDTHS * job.scale`, which reads base-group fields only. `RouteStyle` holds `route_pen`, `route_pen_brush` and `route_pen_width_px` (`style_groups.py:157-159`). `brush_from_id(..., route_pen_width_px, job.scale, ...)` (`pen.py:113-115`) confirms the width is in display pixels, so `* job.scale` is the right render gap. The strand rules are all multiples of the gap (`strands.py:26-36`), so separating in render pixels at `gap * scale` matches the display-pixel separation. `compose.route` tints the pen plate only when `ink.style == "pen"` and draws `ink.px` otherwise (`compose.py:69-90`), so the helper's two branches match what is shown. The byte-identity test and the `pen.py` invariant are prescribed. `test_a_fed_width_respaces_the_strands_without_repainting` still holds, because the default ride is `"solid"` (`default.toml`, `[route_inks.ride]`). |
| B2 (the paper golden claim) | **Replaced, but the replacement unit test is false as written** (new B1 below). The golden paragraph is now a record, not a check, and decision 3's "foxing only" is gone. Both are good. |
| B3 (Yr Wyddfa simplified) | **Resolved.** Yr Wyddfa is never simplified. Its budget is the measured size rounded up to 0.5 MB, capped at today's 12 MB (`test_coordinates.py:47`), and over that it stops. "Simplification is Skye's alone." |
| S1 (route-ink grid) | **Resolved.** Owner row, the per-brush `plates_dir(key) / brush_id`, a per-row `paint`, unlettered cells (`Lettering` is public, `maps/__init__.py:17,32`), and the `MAJ4-e` fallback are all there. |
| S2 (callouts) | **Resolved.** Every callout carries `lat`/`lng` unless its exact name is matched. That is correct against `journal_picks` (`picks.py:60-73`): a coordinate entry bypasses the name lookup. Priority order and the drop rule are prescribed. |
| S3 (per-entry quality) | **Resolved.** The quality is always added and threaded through `_encode` (`make_docs_images.py:56-63`), with lossy-over-budget stopping. One wording defect remains (S2 below). |
| S4 (`.svg` marker) | **Resolved.** `vector-drawing.md` joins `_tutorial_pages()` (`test_tutorials.py:45-47`). Its one run command, `examples/svg_drawing.py`, exists, so `test_every_run_command_names_an_existing_script` stays green. |
| S5 (Keswick residues) | **Resolved.** Both the self-test (`test_coordinates.py:108-111`) and `docs/tutorials/index.md:8` are owned. |
| S6 (`--ref`) | **Resolved.** There is one ordered list with `ref=REF[:FROM:TO]`, a `--box`, failure on forks and closed ways, and the tests. `FROM:TO` is "walked from FROM to TO" today (`make_track.py:8-9`), so the out-and-back spurs are expressible. |
| C1 | Taken as a fallback, with `plates.py` owned only under it. |
| C2 | Taken. The speck numbers it supplied fail on both named sheets (new B2 below). |

## Findings

### Blocker

**B1. P7.V7b's new equality test, B2's replacement, fails as written by three orders of
magnitude.**

- **The test.** "With `paper_vignette=0.0` and `paper_foxing=0.0`, on one seeded sheet,
  the `"warm"` and `"classic"` plates are equal (to 1e-6) more than a tenth of the width
  in."
- **Why it fails.**
  - The plan has `"warm"` darken "the worn border and the vignette … through a warm
    tint" (`1 - k * (1 - tint_channel)`). `"classic"` darkens by `1 - k`.
  - `paper_worn` stays at its default of 0.20 (`ink/style.py:51`).
  - The worn decay is `max(w * 0.012, 8)` (`paper.py:48`). A tenth of the width in, on a
    360 px sheet, that is `exp(-36/8) = 1.1%`, times up to 1.45 (`0.55 + 0.9 * n26`) and
    0.20. So the two plates differ there by `k * tint_c * value`.
- **Measured** (the plan's formula, seed 11): the largest |warm − classic| beyond a tenth
  in is 1.8e-3 on 360 by 240 and 4.2e-5 on 1800 by 1457. Both are far above 1e-6.
- **Effect.** The test is test-first and cannot pass against the prescribed
  implementation, so the slice either deviates from the plan or stops.
- **Fix.**
  - Add `paper_worn=0.0` to the test's style.
  - The plates are then equal everywhere (measured: 0.0 on both sizes), so state it as
    "equal everywhere". That still proves what the test is for: the base colour, the
    tooth and the two draws are unchanged.
- **Checked as sound.** The neighbouring "within 2% a tenth in" check, with
  `paper_tooth=0`, passes under the tint. The worst channel measured 1.5% on 360 px and
  1.35% on 1800 px, because the tint takes away part of the darkening.

**B2. P7.V7b's speck-size test fails on both named sheets under the plan's own speck
rule.**

- **The test.** "Every connected speck is under 0.8% of the width across (14.4 px on the
  job sheet)", on a 360 by 240 sheet at `gran_px` 3 and on the Lynmouth job sheet
  (1800 by 1457, `gran_px` 22.4, `sheet_seed` 11, `job.py:93-97`).
- **The rule.** The specks are pixels above `np.quantile(sheet.gran, 1 - 0.003)`.
  `sheet.gran` is `fbm(h, w, gran_px, 2, rng)` (`sheet.py:108`), so a speck's size
  scales with `gran_px`, as the plan intends ("the same share of every sheet … whatever
  its `gran_px`").
- **Measured** (seed 11, 4-connected components of the threshold mask):

  | Sheet | Largest speck | The plan's bound |
  | --- | --- | --- |
  | 1800 by 1457, `gran_px` 22.4 | 21 px (seed 7: 29 px) | 14.4 px |
  | 360 by 240, `gran_px` 3 | 4 px | 2.88 px |

  Over eight seeds, the largest speck is 1.0 to 1.33 × `gran_px` at 3, 1.25 to 1.62 × at
  8, and 1.07 to 1.88 × at 22.4.
- **No existing field meets the bound on both sheets.** `sheet.fine` (cell 5) gives 9 to
  12 px on the job sheet but 6 to 7 px on the 360 px sheet. A bound tied to the width
  cannot hold for a field tied to `gran_px`.
- **A second ambiguity.** "Weighted by `0.4 + 0.6 * n120` so the specks gather" can be
  read as thresholding the product `gran * (0.4 + 0.6 * n120)`. That gives 51 px blobs
  on the job sheet, which are the smudges the decision removes. The plan does not say
  whether the weight sets the strength or the mask.
- **Fix.**
  - State that the rank threshold is on `sheet.gran` alone, and that `0.4 + 0.6 * n120`
    scales each speck's strength only.
  - Restate the bound in the field's own unit: every connected speck is at most
    `2 * gran_px` across. That holds over the eight seeds at all three `gran_px` values.
    Keep "foxed pixels under 1%" (0.30% measured).
  - The run log records the job sheet's largest speck in display pixels (about 8 at
    seed 11) for P7.V13 to judge against decision 13's "small specks".

### Should fix

**S1. P7.V6 moves the smoke lock, and no slice owns it.**

- **What moves.** `stamp.py:287` calls `pool` at the start of every stroke, so P7.V6's
  span change moves the `pen` and `wash` hashes in `SMOKE_SHA`
  (`tests/unit/maps/painter/test_smoke.py:113-117`) and the committed
  `tests/golden/smoke/wash.webp`.
- **The precedent.** ADR 0025 recorded exactly this as part of a regeneration
  (`0025-second-golden-regeneration.md:110-111`).
- **The gap.** P7.V6's owner files do not name `test_smoke.py`, and the round's "every pin
  it moves" list names only the goldens, `test_places.py` and the docs images.
- **Fix.**
  - Add `test_smoke.py` (`SMOKE_SHA`) and `tests/golden/smoke/wash.webp` to P7.V6's
    owners.
  - Add the generic line "and `SMOKE_SHA`, if it moves" to the engine-slice rule.
  - Add a shared-files row for `test_smoke.py`: P7.V6, then P7.V7b, sequential.

**S2. "Would pass its budget" reads backwards.**

- P7.V7b says "a lossless entry that would pass either goes to lossy WebP".
- P7.V11 says "a lettered thumbnail that would pass its kind's budget … falls back to
  lossy".
- "Pass" reads as "be within". An agent can read this as "convert entries that fit",
  which contradicts P7.V11's "lossless already and stay so".
- **Fix:** replace "pass" with "exceed" in both places.

### Consider

- **C1. P7.V7's pen call.**
  - **The name clash.** In `paint_route_pen`, `route` is already `job.style.route`
    (`pen.py:110`), and the plan's sentence uses `route` for both the style and the line.
  - **The types.** `separate_strands` takes and returns `list[tuple[float, float]]`
    (`strands.py:41-43`), but `job.canvas.px` returns an `ndarray` (`sheet.py:60`), and ty
    will flag the mismatch.
  - **Fix:** prescribe the line as
    `np.asarray(separate_strands([tuple(p) for p in job.canvas.px(list(job.layers.route))], gap))`.
    On a route that does not double back the values are unchanged, so the smoke `pen`
    hash (a sine, no doubling) does not move in P7.V7.

## Fresh pass: checked and sound

- **The route-ink grid.** The solid row and the `MAJ1-e` row share a base digest, so
  after B1 the pen plate is byte-identical whichever style paints it first. Three
  `paint` calls make two real paints.
- **`journal_picks` and `label_max`.** With every callout carrying coordinates, none is
  dropped before the cap, and Y Fenni's six fit its `label_max`.
- **Budgets.** `yr-wyddfa/` is 10.59 MB untrimmed today. "Never simplified, up to
  12 MB" is consistent with the budgets bullet and with `BUDGETS` today.
- **Generator order.** The `"warm"` rule keeps the generator state, the classic hash pin
  and the 2% edge check, and these are consistent with `paper.py`. The red-over-blue
  checks hold by construction: both tints darken blue more than red.

## Verdict

**BLOCK.** Two findings, both in P7.V7b's prescribed tests, and both one-line fixes:

- **B1:** the warm and classic equality test needs `paper_worn=0.0`. Without it the
  plates differ by 1.8e-3 against a 1e-6 tolerance. This came in with round 3's B2 fix.
- **B2:** the speck-size bound of 0.8% of the width fails on both named sheets (21 px
  against 14.4, and 4 px against 2.88). Bound the specks by `2 * gran_px` instead, and
  state that the threshold is on `sheet.gran` alone. This came in with round 3's C2.

Every round-3 blocker and should-fix item is otherwise resolved, with no other new
defect. S1 and S2 can be absorbed by their slices.
