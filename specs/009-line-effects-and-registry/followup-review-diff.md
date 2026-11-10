# Casing follow-up: diff review (PR 1)

Reviewer: fresh context, sceptical staff engineer. Diff: `git diff 46ee0d9b..38e3e8ee` (C0 to C6)
on `claude/quirky-hypatia-z2pii3`. Against: `followup-casing.md`, `followup-casing-tasks.md`,
ADR 0070 as amended, `CLAUDE.md`, `CONTRIBUTING.md`.

**Verdict: PASS after fixes.** No BLOCKING finding. Eight SHOULD-FIX findings, all fixed in this
commit. Two CONSIDER findings, one applied, one declined. Nothing the fixes touch moves a pixel:
the full golden suite and the grid hash check pass with no regeneration.

## Pass 1: plan compliance

Checked and fine:

- **`contour_distance`.** Sign bit for bit and the two caps: `tests/unit/ink/test_contour_distance.py`.
  Property 1, outside only, τ 0.2 to 0.5, 0.4 px, float32 masks, radius + 2 margin:
  `tests/property/test_contour_distance.py`. `ring_coverage` is the box filter as specified.
- **Radii.** `casing` passes `w + 1`, `pen_casing` `w + edge + 1`, `reserve` `w + 2`.
  `casing_union` passes each member its own kind's radius, not the members' maximum. That is
  output-identical (below, SHOULD-FIX 8) and is now recorded in the plan's "As built".
- **Casing and pen casing.** The quality pins (`tests/unit/ink/test_effect_quality.py`), the
  rewritten `TestTies`, `TestSoftStep` and `TestPenCasingWhite` (`test_effect_edges.py`), the
  `out[10, 7] == 0.6` pin (`test_effects.py`) and the painter `_ring` slack `w + 2.0`
  (`tests/unit/maps/painter/test_effects.py`). Property 4: `tests/property/test_line_effects.py`.
- **`Reserve` and `reserve`.** Defaults, the `pool` bound and `width_px=100` accepted:
  `test_effect_types.py`. Behaviour: `test_effect_reserve.py`, `test_effect_reserve_parts.py`.
  Exports and `INK_PUBLIC`: `tests/unit/test_public_api.py`. Glossary entries present.
- **Properties 2, 3, 5 to 9** (`tests/property/test_line_effect_rings.py`), **9 at the painter**
  and the junction test (`tests/unit/maps/painter/test_union_wash.py`), **10**
  (`tests/property/test_casing_union_digests.py`), **11** (`test_line_effect_digests.py`).
- **Located load errors.** Every row has a unit test in `tests/unit/maps/test_theme_unions.py`
  or `test_theme_effects.py`. Run offline through the CLI (`pyntpot map <track> --style
  <file>`, proxy pointed at a closed port, no cache written), each exits 2 with file and line:
  - `typo.yaml:2: casing_unions.0.1: 'lnae' is not a basemap line class; did you mean lane?`
  - `route.yaml:4: casing_unions.0.1: the route is cased at compose from its own mask and joins no union`
  - `mixed.yaml:5: casing_unions.0: mixes water (major) and road (road_major); a union lies within one group, so a road over a river still reads as a crossing`
  - `nocase.yaml:4: casing_unions.0: lane has no casing or reserve; give it one in line_effects, or drop it from the union`
  - `colour.yaml:5: casing_unions.0: road_major's casing is #ffffff at 0.9 and lane's is #fbf6e8 at 1; a union takes one colour and strength`
  - `both2.yaml:5: line_effects.lane.reserve: a stack takes a casing or a reserve, not both`
  - `preset.yaml:5: effect_presets.ringed.reserve: a stack takes a casing or a reserve, not both`
  - `both.yaml:5: line_effects.lane.reserve.pool: pool is 1.5; it must be from 0 to 1`
  - `ingroup.yaml:3: basemap.casing_unions: set only by the top-level casing_unions`
  - a child turning off a member's casing, located in the nearest file writing the table:
    `parent.yaml:5: casing_unions.0: lane has no casing or reserve; …`
- **Schema.** `reserve` in both stack tables with no range, `casing_unions` after
  `line_effects` with `minItems: 1`, `uniqueItems` and the seven-class enum; both copies
  regenerated (`test_theme_schema.py` pins the order).
- **No pin moved.** `git diff 8be0b017 -- tests | grep -E '^-.*\b[0-9a-f]{16}\b'` prints
  nothing. The grid hash check reports all 23 images identical.
- **Budgets.** Largest `src` file 399 lines (`placement_costs.py`, untouched);
  `style_groups.py` 360, `theme_resolve.py` 285. Every new or changed signature has at most 6
  parameters (`lay_stack` has 6). No new `noqa`, no new `type: ignore` in `src`.

## Pass 2: quality

### BLOCKING

None.

### SHOULD-FIX (all fixed)

1. **`contour_distance`'s docstring misstates its search.** It said the minimum is over every
   pixel within `radius + 2`; the code searches `ceil(radius) + 1`. Fixed: the docstring states
   the reach the code uses.
2. **Dead code in `contour_distance`.** The final `np.where(~core & ~seeded & (best >= big),
   big, best)` never changes a value: every distance starts at or below `big` and the search only
   lowers it. `mutation.md` already named its three mutants equivalent for that reason. Fixed:
   removed; `mutation.md` says so.
3. **`effect_pass._scaled_ring` duplicated `_scaled`**, with two identical `if`/`else`
   branches kept only to satisfy the type checker. Fixed: `_scaled` is generic
   (`def _scaled[E: …](effect: E, …) -> E`), `lay_stack` scales the union's pairs with it, and
   `effect_union.Member` is `tuple[np.ndarray, Casing | Reserve]` (the old union of two tuple
   types claimed nothing a `Sequence` of them enforced; `_check_members` checks the kinds).
4. **The "casing or reserve of a stack" lookup was written twice**
   (`casing_unions._ring` and `painter/effects._ring_effect`). Fixed: one
   `line_effects.ring_effect(stack)`, used by both, with unit tests in `test_line_effects.py`.
5. **`pool_band`'s docstring described a plateau** ("1 from half a pixel past its edge"); it is
   a tent peaking there. Fixed.
6. **A survivor wrongly named equivalent.** `lay_reserve` 33 (`pool > 0` to `pool >= 0`) was
   called equivalent because "libm's `pow` returns to within one ulp". Within one ulp is not
   equal, and the plan's own re-check measured why: `ground * (out / ground)` is not `out` in
   float32, and `minimum` keeps the darker ulp. Fixed test-first:
   `test_a_pool_of_zero_leaves_the_band_bit_for_bit` fails on the mutant and passes on the code.
   `mutation.md` corrected (38 killed by new tests, 57 equivalent, 3 removed with dead code).
7. **An acceptance criterion with no test.** The union's ring is laid "at the place of the
   member that comes first in class order *and has a mask*"; nothing tested the second half.
   Added `test_a_union_whose_first_member_paints_nothing_is_laid_at_the_next`, which fails when
   `_union_rings` keys the ring on `union[0]`.
8. **Undocumented deviations from the plan.** The shared helpers are named `blend_casing`,
   `pool_band` and `lay_reserve`, not `_blend_casing` and so on (they cross modules and the
   tests pin them); `casing_union` passes each member its own radius rather than the maximum
   (output-identical: a member reads its distance only up to `w + 1.5`, where both radii are
   exact, and every further candidate exceeds that); the mutation run used `--base 46ee0d9b`
   and `--max-children 3` (the same `src` as `8be0b017`, so the same scope). Fixed: recorded
   under "As built" in `followup-casing.md`; the C1 radius task is ticked with that note, and
   the C1 issue task now cites #214, which is filed.

### CONSIDER

9. Applied. `BasemapStyle.__post_init__` raised from inside `for … in problems[:1]`; it now
   reads `if problems := …: raise …(problems[0][2])`. And `test_a_reserve_is_laid_against_the_paper_plate`
   compared the paper with `pytest.approx`; it now asserts the pixel equals the plate exactly,
   which is the claim.
10. Declined. A union problem found only after the merge is located at the key line of the
    nearest file writing `casing_unions`, even when the cause (a child turning a casing off) is
    in a child that does not write it. The plan prescribes this location, and the message says
    how to fix it; pointing at the child's `line_effects` key too would need a second location
    per problem, a `ThemeProblem` change beyond this follow-up.

## Gates after the fixes

- `uv run pytest -n 2 --dist loadgroup -m "not golden"`: pass.
- `uv run pytest -m golden -n 2 --dist loadgroup`: 123 passed, no regeneration.
- Grid hash check: 23 identical.
- `ruff check`, `ruff format --check`, `ty check`, `lint-imports` (3 kept),
  `mkdocs build --strict`, `prek run --all-files`: pass.
