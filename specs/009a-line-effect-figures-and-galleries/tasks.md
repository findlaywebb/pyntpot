# 009a: tasks

## P0: check and decide (main context)

- [ ] On PR 1's tip, confirm and record the exact names of:
      - `Colour`, `Pigment`, `pigment`, and the registry and its extension;
      - `colour_index`;
      - the casing, glow, shadow and pen casing primitives and their signatures;
      - the effect stack and preset types, the presets `cased`, `halo` and `lifted`;
      - `line_effects:`, and the basemap and `route_ink` effect fields;
      - the bundled palettes and their reader;
      - the `Colour` field walker;
      - `examples/labelled_grid.py`'s `GridSpec` and `label_grid`.
      Update this plan where a name differs.
- [ ] Confirm route effects are wired into `compose_steps.route` and basemap effects into
      the painter's `over` list. If not, stop and report: that is PR 1's scope.
- [ ] Confirm the `WashOptions`, `BRUSH_OVERRIDE_KEYS` and `CoverStyle` parameter names
      the setting grids use. Confirm whether 008a's preview images are on the base, and
      which registry notes PR 1 deleted. Take the next free ADR number.
- [ ] Record every theme's base plate bytes on the Ambleside fixture and the per-role
      `(colour, transparency)` table of every theme, as literals for B.
- [ ] Dispatch the plan-reviewer; address findings until it passes.

## A: one route colour (#159)

- [ ] Red: property, structural, override, digest and pixel tests; benchmark.
- [ ] Green: `with_route_ink` feeds `nib.label_route_ink`; docstring; pin the fed lettering
      digest.
- [ ] How-to text, glossary row and regenerated glossary; delete the #159 note. Gates.

## B: a pigment carries its transparency (D7)

- [ ] Red: `test_cover_pigments.py`, the checker, merge and schema tests, the migration
      literal table.
- [ ] Green: `CoverPigment` leaf and default from the registry; drop
      `PaperStyle.pigment_transparency`; `PaintJob.transp`; painter `.colour` reads;
      vocabulary; moved-key message; export and public API pin.
- [ ] Migrate the four bundled and six example themes; regenerate both schemas.
- [ ] Byte compare every theme's base plates with P0's record: identical.
- [ ] Re-pin `DIGEST`, `BASE_DIGEST`, theme `DIGESTS` and `GOLDEN_HASH` to measured
      literals. `LETTERING_DIGEST` unchanged.
- [ ] Docs: `style-fields.md`, `pigments.md`, `write-a-theme.md`. Gates.

## C: galleries (#69, #70)

- [ ] Red: `test_galleries.py`, and the coverage and table tests.
- [ ] Green: `brush_gallery.py` (`riv-str-lan`, `maj`, `trk`); `pigment_gallery.py`
      (`roles`, `painters`, `glazes`, `palettes`).
- [ ] Register seven entries under `009a-galleries` (share 500,000). Paint them with
      `PYTHONPATH=tests uv run python tests/golden/make_docs_images.py "$SCRATCH/c" <names>`
      and copy the images and masters in. Check the budgets.
- [ ] The two reference pages, links and nav. Delete the #69 and #70 notes. Gates and
      the golden pins of the seven.

## D: line effects (#104, #105, #106)

- [ ] Red: `test_line_effect_figures.py` (zero cell equals the plain stroke; glow never
      darker), `test_how_to_line_effects.py`, the reference values test, the
      `ambleside-cased` digest pin.
- [ ] Green: `line_effect_grids.py`, `line_effect_reasons.py`, `how_to_line_effects.py`,
      `cased_stroke.py`, `examples/themes/ambleside-cased.yaml`; `sweep_grid` only if
      needed.
- [ ] Register nine entries under `009a-line-effects` (share 600,000); paint, copy, check
      the budgets.
- [ ] The how-to, reference, explanation and tutorial pages, index pages and nav.
- [ ] Delete the #104, #105 and #106 notes. Gates and the golden pins of the nine.

## E: setting grids (#67)

- [ ] Red: `test_setting_grids.py`.
- [ ] Green: `setting_grids.py` (`pool`, `granulation`, `dryness`) and `relief_grid.py`.
- [ ] Register four entries under `009a-setting-grids` (share 250,000); paint, copy, check
      the budgets.
- [ ] Sections in `how-the-wash-works.md`, `brushes.md` and `write-a-theme.md`. Delete the
      #67 note. Gates.

## F: bold cases its main roads

- [ ] `bold.yaml` takes `line_effects: {road_major: cased}`; header comment; the "Bold"
      section; re-pin `DIGESTS["bold"]`. Gates. (Its image moves in G.)

## G: close, regenerate once, review

- [ ] Fix the links in the four notes; delete any registry note PR 1 left.
- [ ] Regenerate the goldens, once, from the repo root on the pinning machine:

      ```bash
      SCRATCH=$(mktemp -d)
      PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/repaint"
      PYTHONPATH=tests uv run python -c "import json,shutil,sys; from pathlib import Path; out=Path(sys.argv[1]); [shutil.copyfile(out / 'tree' / f['path'], f['path']) for f in json.load(open(out / 'diffs' / 'summary.json'))['files'] if f['status'] == 'changed']" "$SCRATCH/repaint"
      PYTHONPATH=tests uv run python tests/golden/make_golden.py tests/golden/lynmouth
      PYTHONPATH=tests uv run python tests/golden/diff_images.py "$SCRATCH/recheck" --ref "$(git merge-base HEAD origin/claude/quirky-hypatia-z2pii3)"
      ```

      The `summary.json` `changed` set must be exactly `how-to/route-ink` and
      `map-styles/bold` (plus `preview/bold` if 008a is on the base), with their masters.
      The `added` set is the 20 new images. `git diff --stat tests/golden/lynmouth` shows
      `plates.json` alone. Re-pin `MEAN_RGB["bold"]`. Run
      `uv run pytest -m golden -n auto --dist loadgroup`; it passes.
- [ ] The new ADR: the `CoverPigment` name, the Lynmouth compare log, the moved table with
      fractions. Index row.
- [ ] `publish_diffs.py "$SCRATCH/recheck" --push`; paste its block under "Golden and docs
      images".
- [ ] Mutation run (plan's command); record an empty list or each survivor.
- [ ] Fresh-context diff review against the plan, then the elegance pass. Dash search of
      human-facing prose finds none.
- [ ] PR `feat(maps)!: ...` against `claude/quirky-hypatia-z2pii3`, with the changelog
      lines, the moved table and `Closes #159, #69, #70, #67, #104, #105, #106`.
