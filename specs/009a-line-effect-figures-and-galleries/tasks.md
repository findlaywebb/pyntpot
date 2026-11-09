# 009a: tasks

## P0: check and decide (main context)

- [ ] On PR 1's tip, confirm and record the exact names of:
      - `Colour`, `Pigment`, `pigment`, `PigmentRegistry` and `extended`;
      - `colour_index`;
      - `casing`, `glow`, `shadow` and `pen_casing` and their signatures;
      - `EffectStack`, `BUILT_IN_PRESETS` and the presets `cased`, `halo` and `lifted`;
      - `line_effects:`, `basemap.line_effects` and `route_ink.effects`;
      - `Palette` and `Palette.names()`;
      - `ThemeScope`, `resolve_colour`, `theme_checker.TableCheck` and its `leaf` context;
      - the `Colour` field walker;
      - `examples/labelled_grid.py`'s `GridSpec` and `label_grid`.
      Update the plan where a name differs.
- [ ] Confirm that PR 1's `theme_pigments` gives a derived `{base: x}` pigment `x`'s
      transparency when it sets none. If not, B's resolver follows `base` itself.
- [ ] Confirm route effects are wired into `compose_steps.route` and basemap effects into
      the painter's `over` list. If not, stop and report: that is PR 1's scope.
- [ ] Confirm the setting grids' fields: `wash(..., pool=)`, `Sheet.seed`, `Sheet.gran_px`,
      `Sheet.fibre`, `PaperStyle.paper_fibre_mix`, `BRUSH_OVERRIDE_KEYS` `dry` and
      `load`, the `brush_from_id` path that takes `brush_overrides`, and
      `CoverStyle.relief_strength`. Confirm whether 008a's preview images are on the
      base, and which registry notes PR 1 deleted. Take the next free ADR number.
- [ ] Confirm this machine reproduces the goldens exactly: on PR 1's tip,
      `PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/p0"` gives a
      `summary.json` with nothing `changed`, `added` or `removed`, and the Lynmouth
      compare logs byte-identical. If not, this is not the pinning machine: stop before C
      paints any master.
- [ ] Record every theme's base plate bytes on the Ambleside fixture and the per-class
      `(colour, transparency)` table of every theme, as literals for B.
- [ ] Comment the branch name on #159, #69, #70, #67, #104, #105 and #106 (CLAUDE.md,
      "Starting").
- [ ] Search the open issues for the `tests/support/docs_images.py` line budget (565
      lines); if none, write `docs/issues/tests-docs-images-over-budget.md` and file its
      issue (`chore`, `area: tests`).
- [ ] Dispatch the plan-reviewer; address findings until it passes.

## A: one route colour (#159)

- [ ] Red: property, structural, override, digest and pixel tests (the pixel test on the
      nib plate's RGBA, nearer `VIOLET` than `#c22050`); benchmark.
- [ ] Green: `with_route_ink` feeds `nib.label_route_ink`; docstring; pin the fed lettering
      digest.
- [ ] How-to text, glossary row and regenerated glossary; delete the #159 note. Gates.
- [ ] Repaint `how-to/route-ink.webp how-to/route-ink-grid.webp` with `--no-lynmouth`:
      `changed` is `route-ink` and its master only. Commit nothing from it.

## B: a pigment carries its transparency (D7)

- [ ] Red: `test_cover_pigments.py` and `test_theme_bindings.py` (every form by `ids=`,
      the `extends` child, Python-built `None` and `str`, the errors), the merge and
      schema tests, the migration literal table.
- [ ] Green: `maps/cover_pigment.py`; `maps/theme_bindings.py`; the `cover_class` context
      key in `TableCheck.leaf`; the `RENAMED_KEYS` entry; drop
      `PaperStyle.pigment_transparency`; `CoverStyle.__post_init__`; `PaintJob.transp`;
      painter `.colour` reads; vocabulary; export, `maps.md` directive and public API pin.
- [ ] Test support: `theme_dump` writes a `CoverPigment` as a table; the merge
      property's walker draws a bare hex for one. Fix `test_smoke.py:246` and PR 1's
      coercion guard.
- [ ] Migrate the four bundled and six example themes; regenerate both schemas.
- [ ] Byte compare every theme's base plates with P0's record: identical. Repaint the
      map-styles cards, place cards and hero with `--no-lynmouth`: nothing changed.
- [ ] Re-pin `DIGEST`, `BASE_DIGEST`, theme `DIGESTS` and `GOLDEN_HASH` to measured
      literals. `LETTERING_DIGEST` unchanged.
- [ ] Docs: `style-fields.md`, `pigments.md`, `write-a-theme.md` (the example, the merge
      line, the rule and the `extends` case), the "cover pigment" glossary row. Gates.

## C: galleries (#69, #70)

- [ ] Pure move: `DocsImage` and its helpers to `tests/support/docs_image.py`, importers
      repointed. Gates.
- [ ] Red: `test_galleries.py`, the coverage tests and `test_gallery_values.py`.
- [ ] Green: `brush_gallery.py` (`riv-str-lan` with "RIV = STR", `maj`, `trk`);
      `pigment_gallery.py` (`roles`, `painters`, `glazes`, `palettes`).
- [ ] Create `tests/support/docs_images_009a.py`; register seven entries under
      `009a-galleries` (share 500,000). Paint them with
      `PYTHONPATH=tests uv run python tests/golden/make_docs_images.py "$SCRATCH/c" <names>`
      and copy the images and masters in. Check the budgets.
- [ ] The two reference pages, links and nav. Delete the #69 and #70 notes. Gates and
      the golden pins of the seven.

## D1: tune the presets (main context)

- [ ] Paint the presets figure and the casing, glow and shadow sweeps into a scratch
      directory with the provisional presets; tune `BUILT_IN_PRESETS` until each reads on
      the 720 px card. Commit nothing painted.
- [ ] Gate: PR 1's `tests/property/test_line_effect_presets.py`,
      `test_line_effect_digests.py`, `test_line_effects.py`,
      `tests/unit/maps/test_line_effects.py` and `test_digest_omits.py` pass with the
      tuned values, then the full non-golden gate. Record the values in the plan's
      Decisions.

## D2: the sweeps (#104, #105, #106)

- [ ] Red: `test_line_effect_figures.py` (each off cell equals `paint_cell(None)` by
      `tobytes()`; glow never darker).
- [ ] Green: `line_effect_grids.py` at scale 1 (`casing`, `glow`, `shadow`,
      `pen-casing`); `sweep_grid` only if needed.
- [ ] Register four entries in the `009a-line-effects` block (share 600,000); paint,
      copy, check the budgets. Gates.

## D3: the how-to and reference

- [ ] Red: `test_how_to_line_effects.py`, `test_line_effect_values.py`, the
      `ambleside-cased` entry in `THEME_NAMES` and `DIGESTS`.
- [ ] Green: `how_to_line_effects.py` (`card`, `presets`) and
      `examples/themes/ambleside-cased.yaml`.
- [ ] Register two entries; paint, copy, check the budgets.
- [ ] `case-light-or-shadow-a-line.md` (the card and the three theme sweeps) and
      `reference/line-effects.md` (no image; pen casing has no theme key; pigment
      separation keeps its own transparency), index pages and nav. Gates.

## D4: the explanation and tutorial

- [ ] Green: `line_effect_reasons.py` (`glaze-or-rgb`, `draw-order`) and
      `cased_stroke.py`, each with a test that it runs.
- [ ] Register three entries; paint, copy, check the budgets.
- [ ] `explanation/line-effects.md` and `painting-with-python/cased-strokes.md` (the
      cased stroke and the pen casing sweep), index pages and nav.
- [ ] Delete the #104, #105 and #106 notes. Gates and the golden pins of the nine.

## E: setting grids (#67)

- [ ] Red: `test_setting_grids.py`.
- [ ] Green: `setting_grids.py` (`pool`, `granulation`, `dryness`, with the plan's fields
      and values) and `relief_grid.py`.
- [ ] Register four entries under `009a-setting-grids` (share 250,000); paint, copy, check
      the budgets.
- [ ] Sections in `how-the-wash-works.md`, `brushes.md` and `write-a-theme.md`, as the
      plan's page table says. Delete the #67 note. Gates.

## F: bold cases its route

- [ ] `bold.yaml` takes `line_effects: {route: cased}`; header comment; the "Bold"
      section; `test_bold_cases_its_route_and_nothing_else`; re-pin `DIGESTS["bold"]`'s
      digest, its base digest unchanged. Repaint the map-styles cards, place cards and
      hero with `--no-lynmouth`: `changed` is `map-styles/bold` and its master only.
      Gates. (Its image moves in G.)

## G: close, regenerate once, review

- [ ] Fix the links in the four notes; delete any registry note PR 1 left.
- [ ] Repaint everything, once, from the repo root on the pinning machine, and check the
      summary **before** copying anything:

      ```bash
      SCRATCH=$(mktemp -d)
      PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/repaint"
      ```

      In `$SCRATCH/repaint/diffs/summary.json`, against the working tree: `changed` is
      exactly `docs/images/how-to/route-ink.webp`, `tests/golden/docs/how-to/route-ink.png`,
      `docs/images/map-styles/bold.webp` and `tests/golden/docs/map-styles/bold.png`
      (plus `preview/bold` and its master if 008a is on the base); `added` and `removed`
      are empty, because each slice committed its own new images. The Lynmouth compare
      logs byte-identical images. Anything else: stop and find the slice.
- [ ] Copy the changed files, then regenerate the Lynmouth goldens:

      ```bash
      PYTHONPATH=tests uv run python -c "import json,shutil,sys; from pathlib import Path; out=Path(sys.argv[1]); [shutil.copyfile(out / 'tree' / f['path'], f['path']) for f in json.load(open(out / 'diffs' / 'summary.json'))['files'] if f['status'] == 'changed']" "$SCRATCH/repaint"
      PYTHONPATH=tests uv run python tests/golden/make_golden.py tests/golden/lynmouth
      ```

      `git diff --stat tests/golden/lynmouth` shows `plates.json` alone. Re-pin
      `MEAN_RGB["bold"]`.
- [ ] The review diff against the stack's base:

      ```bash
      PYTHONPATH=tests uv run python tests/golden/diff_images.py "$SCRATCH/recheck" --ref "$(git merge-base HEAD origin/claude/quirky-hypatia-z2pii3)"
      ```

      In `$SCRATCH/recheck/diffs/summary.json`: `changed` is the same four files (six
      with 008a); `added` is 40, the 20 new images and their 20 masters; `removed` is
      empty. Run `uv run pytest -m golden -n auto --dist loadgroup`; it passes.
- [ ] The new ADR: the `CoverPigment` name, the tuned presets, the Lynmouth compare log,
      the moved table with fractions. Index row (it does not claim to amend ADR 0070,
      whose rule 17 was edited in place).
- [ ] `publish_diffs.py "$SCRATCH/recheck" --push`; paste its block under "Golden and docs
      images".
- [ ] Mutation run (plan's command); record an empty list or each survivor.
- [ ] Fresh-context diff review against the plan, then the elegance pass. Dash search of
      human-facing prose finds none.
- [ ] PR `feat(maps)!: ...` against `claude/quirky-hypatia-z2pii3`, with the changelog
      lines, the moved table, and one line each: `Closes #159`, `Closes #69`,
      `Closes #70`, `Closes #67`, `Closes #104`, `Closes #105`, `Closes #106`.
