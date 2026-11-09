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
      - `resolve_pigment(text, scope) -> Pigment` in `theme_scope.py`, which B's resolver
        calls for every ref (theme alias, then palette alias, then registry name);
      - the `Colour` field walker;
      - `examples/labelled_grid.py`'s `GridSpec` and `label_grid`.
      Update the plan where a name differs.
- [ ] Confirm that PR 1's `theme_pigments` gives a derived `{base: x}` pigment `x`'s
      transparency when it sets none. If not, B's resolver follows `base` itself.
- [ ] Confirm PR 1's tip has `ThemeScope.aliases: Mapping[str, Bound[Pigment]]` (a hex
      alias a pigment-less `Pigment` with transparency `None`) and `Palette.pigments`
      (alias to `Pigment`). If not, stop and report: B's alias rows and the palettes
      figure need them, and they are PR 1's scope.
- [ ] Check whether PR 1's `tests/property/test_line_effect_digests.py` draws only the
      classes the sampled theme does not set; record the answer for D3.
- [ ] Grep PR 1's tip for every 16-hex hash in the tests
      (`git grep -nwE '[0-9a-f]{16}' -- 'tests/*.py'`, which also finds both halves of
      `GOLDEN_HASH`), keep every hash of style data: a `digest()`, `base_digest()` or
      `lettering_digest()` pin, a `SOURCED` group pin, or any other hash of a group's or
      a theme's fields (not fixture cache keys, plate pixel hashes such as
      `CLASSIC_PLATE_SHA`, or placeholders). Record each file and pin, and add each file
      to B's pins (`test_style_groups.py` and `test_digest_omits.py` among them).
- [ ] Grep PR 1's tip for `pigment_transparency`, `cover.pigments` and `.pigments[` in
      `tests/`; record each hit for B, which owns them (`test_registry_defaults.py` and
      `test_theme_colour_names.py` among them).
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
- [ ] `test_style.py::test_a_fed_ink_moves_only_the_full_digest` becomes
      `test_a_fed_width_moves_only_the_full_digest` (`width_px=4.8` alone); the colour
      case lives in `test_route_colour_feed.py`.
- [ ] Repaint `how-to/route-ink.webp how-to/route-ink-grid.webp` with `--no-lynmouth`:
      `changed` is `route-ink` and its master only. Commit nothing from it.

## B: a pigment carries its transparency (D7)

- [ ] Red: `test_cover_pigments.py` and `test_theme_bindings.py` (every form by `ids=`,
      `palette-alias-to-name` among them; the `extends` child; Python-built `None`, `str`
      and a key outside the 15 classes; the dumped form loading back; each table error
      at its own key and line, with the nearest name for an unknown inner key and `bool`
      and `str` transparencies refused), the merge and schema tests, the migration
      literal table.
- [ ] Green: `maps/cover_pigment.py`; `maps/theme_bindings.py` (every ref through
      `resolve_pigment`, no direct alias or registry lookup); the `cover_class` context
      key in `TableCheck.leaf`; the table form checked key by key in `TableCheck.field`; the `RENAMED_KEYS` entry and the
      `test_theme_check.py:146` pin of `RENAMED_KEYS` (now two rows); drop
      `PaperStyle.pigment_transparency`; `CoverStyle.__post_init__`; `PaintJob.transp`;
      painter `.colour` reads; vocabulary; export, `maps.md` directive and public API pin.
- [ ] One written form, a ref or `{pigment, transparency}`, never a list: `theme_dump`
      (its writer public as `plain_table`), the schema `default` (`theme_schema._json`),
      `test_reference_values.py`'s `entry_value` and the `style-fields.md` Default cells.
      `test_theme_schema.py`: the default test builds its expected value with
      `plain_table`, and `keys_outside_the_schema` descends into an `anyOf`'s object
      branch. The merge property's walker draws a bare hex for a `CoverPigment`. Fix
      `test_smoke.py:246` and PR 1's coercion guard, `test_registry_defaults.py` and
      `test_theme_colour_names.py`.
- [ ] Migrate the four bundled and six example themes; regenerate both schemas.
- [ ] Byte compare every theme's base plates with P0's record: identical. Repaint with
      `--no-lynmouth` every fixture-reading registry name except `how-to/route-ink.webp`
      (the plan's list of 15): nothing changed.
- [ ] Re-pin `DIGEST`, `BASE_DIGEST`, theme `DIGESTS`, `GOLDEN_HASH`,
      `SOURCED[PaperStyle]`, `SOURCED[CoverStyle]` and every other hash of style data
      P0's grep found to measured literals. `LETTERING_DIGEST` unchanged.
- [ ] Docs: `style-fields.md` (with the `route_ink` section's "paints no plate again"
      corrected for a fed colour), `pigments.md`, `write-a-theme.md` (the example, the merge
      line, the rule and the `extends` case), the "cover pigment" glossary row. Gates.

## C: galleries (#69, #70)

- [ ] Pure move: `DocsImage` and its helpers (`Kind`, `Encoding`, `Option` among them) to
      `tests/support/docs_image.py`, importers repointed. Gates.
- [ ] Red: `test_galleries.py`, the coverage tests and `test_gallery_values.py`.
- [ ] Green: `brush_gallery.py` (`riv-str-lan` with "RIV = STR", `maj`, `trk`);
      `pigment_gallery.py` (`roles`, `painters`, `glazes`, `palettes`).
- [ ] Create `tests/support/docs_images_009a.py`; register seven entries under
      `009a-galleries` (share 500,000). Paint them with
      `PYTHONPATH=tests uv run python tests/golden/make_docs_images.py "$SCRATCH/c" <names>`
      and copy the images and masters in. Check the budgets.
- [ ] The two reference pages, links and nav. Delete the #69 and #70 notes. Gates and
      the golden pins of the seven.

## D2: the sweeps (#104, #105, #106)

- [ ] Red: `test_line_effect_figures.py` (each off cell equals `paint_cell(None)`, both
      float32, by `tobytes()`; glow never darker).
- [ ] Green: `line_effect_grids.py` at scale 1 (`casing`, `glow`, `shadow`,
      `pen-casing`) with the plan's held literals, none read from a preset; `paint_cell`
      returns float32; the pen casing cell composites its edges only when `edges.any()`,
      and its plain cell is the tint plus the centre ink line; `sweep_grid` only if
      needed.
- [ ] Register four entries in the `009a-line-effects` block (share 600,000); paint,
      copy, check the budgets. Gates.

## D1: tune the presets (main context)

- [ ] After D2: paint a scratch draft of the presets figure (D3 writes the real script)
      and D2's casing, glow and shadow cells at each preset's values into a scratch
      directory, starting from the provisional presets; tune `BUILT_IN_PRESETS` until
      each reads on the 720 px card. Commit nothing painted.
- [ ] Gate: PR 1's `tests/property/test_line_effect_presets.py`,
      `test_line_effect_digests.py`, `test_line_effects.py`,
      `tests/unit/maps/test_line_effects.py` and `test_digest_omits.py` pass with the
      tuned values, then the full non-golden gate. Record the values in the plan's
      Decisions.

## D3: the how-to and reference

- [ ] Red: `test_how_to_line_effects.py`, `test_line_effect_values.py`, the
      `ambleside-cased` entry in `THEME_NAMES` and `DIGESTS`, and the theme count in
      `test_one_source_of_defaults.py::test_the_theme_file_checks_see_every_theme`
      (ten to eleven).
- [ ] Unless P0 found it already does, restrict PR 1's
      `tests/property/test_line_effect_digests.py` to the classes the sampled theme does
      not set; it passes with `ambleside-cased`.
- [ ] Green: `how_to_line_effects.py` (`card`, `presets`; each preset cell loads a theme
      file the script writes under `out_dir`, `extends:` the absolute path of
      `ambleside.yaml` with `line_effects: {route: <name>}`, through `Style.from_yaml`;
      no private import) and `examples/themes/ambleside-cased.yaml`
      (`extends: ambleside.yaml`).
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

- [ ] Red: `test_setting_grids.py` (the dryness grid reads its overrides through
      `override="major"`).
- [ ] Green: `setting_grids.py` (`pool`, `granulation`, `dryness`, with the plan's fields
      and values) and `relief_grid.py`.
- [ ] Register four entries under `009a-setting-grids` (share 250,000); paint, copy, check
      the budgets.
- [ ] Sections in `how-the-wash-works.md`, `brushes.md` and `write-a-theme.md`, as the
      plan's page table says. Delete the #67 note. Gates.

## F: bold cases its route

- [ ] `bold.yaml` takes `line_effects: {route: cased}`; header comment; the "Bold"
      section; `test_bold_cases_its_route_and_nothing_else`; re-pin `DIGESTS["bold"]`'s
      digest and any bold digest P0's grep found elsewhere, its base digest unchanged.
      `test_line_effect_digests.py` passes with bold's `route` set. Repaint B's 15 names
      with `--no-lynmouth`: `changed` is `map-styles/bold` and its master only (plus
      `preview/bold` if 008a is on the base). Gates. (Its image moves in G.)

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
- [ ] The new ADR: the `CoverPigment` name, the `RENAMED_KEYS` departure from ADR
      0069:323, the tuned presets, the Lynmouth compare log,
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
