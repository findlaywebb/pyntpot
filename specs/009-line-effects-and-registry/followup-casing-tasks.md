# Casing follow-up: tasks

PR 1 on `claude/quirky-hypatia-z2pii3` first, then merged into
`claude/quirky-hypatia-z2pii3-stacked`, then the PR 2 tracks.
Specs: `specs/009-line-effects-and-registry/followup-casing.md` (C slices) and
`specs/009a-line-effect-figures-and-galleries/followup-casing.md` (T tracks).

## PR 1 (#211), branch `claude/quirky-hypatia-z2pii3`

### C0: start
- [x] ADR 0070 amended in place: rules 8, 9, 10, 11, 12, 13, 15, public names, alternatives;
      header line naming this follow-up.
- [x] `followup-casing.md` committed; base `8be0b017` recorded.
- [x] Baseline slice gate green on the untouched tip (`-n 2`, never `-n auto`).

### C1: `contour_distance`
- [x] Red: property 1 (float32 masks, shapes a radius + 2 margin from the array edge; exact
      reference outside only, τ 0.2 to 0.5, 0.4 px; sign only inside, bit for bit); cap cases; τ-exact, one-pixel and array-edge units.
- [x] `ink/effect_distance.py`: `contour_distance`, `ring_coverage`; pure numpy.
- [x] Accuracy and cost at radius 3, 8, 16, 33 recorded in "Measured"; one form, no two-stage
      form; `docs/issues/ink-contour-distance-cost.md` written, with its GitHub issue #214.
- [x] Each caller's radius as prescribed: casing `w + 1`, pen casing `w + edge + 1`, reserve
      `w + 2`; a union passes each member its own kind's radius, which gives the same output
      as the members' maximum (see "As built" in `followup-casing.md`).
- [x] Benchmark smoke entry; slice gate green.

### C2: casing and pen casing anti-aliased
- [x] Red: `test_effect_quality.py` pins (casing edge at most 0.22 px; pen edge ink 0.70 to
      0.95; pen band wobble at most 0.10 px); `TestTies` and `TestSoftStep` rewritten in place;
      `TestPenCasingWhite` band and the `out[10, 7]` reserve test rewritten; the painter
      `test_effects.py` `_ring` slack set to `w + 2.0`; property 4; properties 2 and 3 for
      `casing`.
- [x] `casing` and `pen_casing` on `contour_distance`, with `_blend_casing` shared; docstrings
      say the width is from the line's edge.
- [x] Slice gate; golden docs subset passes with no regeneration.

### C3: `Reserve`, `reserve`, `casing_union`
- [x] Red: `Reserve` defaults, `pool` range, `check_effect_numbers` upper bound; properties 2,
      3, 5 to 9 at the ink level (float32 masks); `INK_PUBLIC` lists `Reserve` and `reserve`.
- [x] `effect_types.Reserve`, `EFFECT_RANGES["pool"]`; `ink/effect_reserve.py` with
      `_pool_band(d - width_px)` and `_lay_reserve` (pool deepens only where `b > 0`, taking
      `minimum(out, deepened)`); `ink/effect_union.py` (private), using
      both and `_blend_casing`.
- [x] Exports, `docs/reference/ink.md`; glossary terms reserve and casing union, pool and line
      effect updated; glossary regenerated.
- [x] Slice gate green.

### C4: the theme model
- [x] Red: `EffectStack` with a reserve; the casing-or-reserve refusal; every row of "Located
      load errors" incl. the CLI exit 2; a child replacing and `[]` clearing `casing_unions`;
      the preset casing-and-reserve row; `BasemapStyle` refusing a bad union (route, unknown,
      duplicate, mixed group, stack problems); members normalised to class order; property 10;
      off-reserve digests; schema order and nodes (reserve with no min or max); `PINNED`,
      `BASEMAP_DEFAULTS` and `tests/unit/maps/candidates/test_export.py:88-121` gain
      `casing_unions`; `casing_unions.py` in `BY_NAME`.
- [x] `BasemapStyle` line count checked: past 400 on either branch, pure move to
      `style_basemap.py` first.
- [x] `maps/casing_unions.py` (`membership_problems`, `union_problems`: every union message),
      `maps/theme_unions.py` (shape and location only); `line_effects`, `theme_effects`,
      `theme_check`, `theme_resolve` (post-merge check), `theme_vocab`, `style_groups`, `style`
      (`DIGEST_OMITS_AT_DEFAULT`), `theme_schema_tables`.
- [x] Both schema copies regenerated; `style-fields.md` row; slice gate green.

### C5: painter and compose
- [x] Red, in `test_union_wash.py`: union junction pixel test; union of one at the painter;
      ring skipped at later members; route reserve exact at compose; `pen_mask` floor cases.
- [x] `lay_stack(..., ring=)` and the reserve branch; `_lay_group` unions; soft `pen_mask`;
      `compose_steps.py` docstring sentence corrected.
- [x] Largest off-line Lynmouth pen alpha recorded, below 8/255.
- [x] Slice gate; golden docs subset passes with no regeneration.

### C6: mutation testing
- [x] `scope.py --base 8be0b017`; `mutmut run --max-children 2` under `prlimit`, with the
      out-of-repo `sitecustomize.py` (`Node._nodeid` alias).
- [x] Each survivor killed by a focused `tests/unit/ink/` test or named equivalent with its
      reason; `mutation.md` section added.

### C7: close PR 1
- [x] Full golden suite `-m golden -n 2 --dist loadgroup` passes with no regeneration; grid
      hash check passes.
- [x] `git diff 8be0b017 -- tests | grep -E '^-.*\b[0-9a-f]{16}\b'` prints nothing.
- [x] No `src` file over 400 lines; every new signature at most 6 parameters, no noqa.
- [x] Ticks and "Measured" filled; one pointer line in `tasks.md`.
- [ ] PR body: three Changelog lines, mutation survivors. Pushed.
- [ ] Merged into `claude/quirky-hypatia-z2pii3-stacked` (T0 below). Push both branches
      together once T6 is green.

## PR 2 (#213), branch `claude/quirky-hypatia-z2pii3-stacked`

### T0: merge and inventory
- [ ] PR 1's tip merged; conflicts resolved; schema copies regenerated, not hand-merged.
- [ ] Not-golden gate green.
- [ ] Scratch repaint: exactly the "Figures" images less the reserve, glow and shadow sweeps
      (still 1x and laying no casing, so byte-identical until T3), and their masters, move;
      Lynmouth and every other image byte-identical. Otherwise stop and report.

### T1: split `line_effect_grids.py`
- [ ] Pure move of the scene builders to `examples/line_effect_scenes.py`, imports repointed, no
      shim.
- [ ] The sweep tests moved from `test_line_effect_figures.py` to `test_line_effect_sweeps.py`
      (new, T1's); the source scan extended to `line_effect_scenes.py`.
- [ ] The four sweeps repaint byte-identical before and after; gate green.

### T2: the 2x helper
- [ ] Red: `scaled_boxes(spec, 2)` is each 1x box times 2 (no `GridSpec.scaled`: `cell_w`'s
      floor division would not double); `reduce` returns the 1x size, float32, within 0 to 1.
- [ ] `labelled_grid.py` gains `SUPERSAMPLE`, `scaled_boxes`, `reduce`; the five grid hashes
      unchanged; gate green.

### T3: sweeps at 2x and the reserve sweep (worktree after T2)
- [ ] Red: `test_line_effect_sweeps.py` (reduced size, off column; pool no lighter on the 2x
      float arrays before `reduce`; thin pen edge continuous on `reduce(band)`).
- [ ] Glow and shadow sweeps now move (2x); the lines `cased-strokes.md` quotes (`_reserved`,
      `paint_cell`) left unchanged.
- [ ] All five sweeps painted at 2x and reduced once, then lettered; `reserve` figure added.
- [ ] `_sweep("reserve-sweep", "reserve")` registered; how-to sections "Reserve the paper round
      a line" and "Case several classes as one".
- [ ] Added reserve sweep and master committed only if a non-golden test needs them; gate green.

### T4: cased stroke and the essay figures (worktree after T2)
- [ ] Red, on the 2x float arrays before `reduce`: the reserve cells (paper where whole; pooled
      no lighter); the union cell rules (equal outside, lighter nowhere);
      `TestDrawOrder` updated for three cells; 2x sizes.
- [ ] `cased_stroke.py` 3 × 2 with reserve cells at 2x; `line_effect_reasons.py` draw-order
      third cell and both figures at 2x.
- [ ] Tutorial page and explanation sections; gate green.

### T5: reference and theme how-to
- [ ] `reference/line-effects.md` reserve table, "Casing unions" table, draw order, primitives;
      `write-a-theme.md` paragraphs.
- [ ] No em or en dashes in human-facing prose; strict docs build; gate green.

### T6: judge, then regenerate once
- [ ] Scratch repaint of every "Figures" image; `diff_images.py` against the pre-follow-up tip.
- [ ] Each image opened at 2x zoom beside the research crops and judged for pixelation, dotted
      edges, ringing, the union cell and the reserve cells; verdicts in `images.md`; failures
      back to their track.
- [ ] Budgets checked: share under 600,000 bytes, every page image under 250,000, no budget
      edited.
- [ ] One regeneration: docs images, masters, `MEAN_RGB["bold"]`.
- [ ] `images.md` follow-up section; ADR 0071 amended in place (table, Lynmouth compare, added
      reserve sweep, closing line).
- [ ] `uv run pytest -m golden -n 2 --dist loadgroup` green with no further change; full gate
      green.

### T7: close PR 2
- [ ] Review images published by the orchestrator (`publish_diffs.py --push`) and the block
      pasted under "Golden and docs images".
- [ ] Two Changelog lines; ticks; both branches pushed together.
