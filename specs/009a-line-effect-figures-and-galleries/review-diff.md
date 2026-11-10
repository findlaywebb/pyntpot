# 009a diff review (fresh context)

Diff: `git diff origin/claude/quirky-hypatia-z2pii3...HEAD` (PR 2, stacked on #211).

Gates checked here: `ruff check`, `ruff format --check`, `ty check`, `lint-imports` all pass;
`pytest -n auto --dist loadgroup --golden-tolerance` passes in full.

Verified as met:

- **#159.** The guards are all present. `tests/property/test_route_colour.py` is the property,
  `test_route_colour_feed.py::test_every_colour_field_defaulting_to_the_route_colour_follows_a_fed_one`
  is the structural test, and `test_route_ink.py::TestFedColourLettersTheMarkers` is the pixel
  test. The digest pins are in `test_route_colour_feed.py`, the how-to text is updated and the
  note is deleted.
- **Retired key.** A theme that sets `paper.pigment_transparency` fails at load with
  `t1.yaml:3: paper.pigment_transparency: renamed to cover.pigments.<class>.transparency`
  (run in the scratchpad).
- **Table form errors.** Each one is located at its own key and line: the unknown key
  `transparancy` gets "did you mean transparency", and `true`, `"0.4"`, `1.4`, an unknown ref,
  a list and a missing `pigment` are each refused. An `extends` child that writes
  `{transparency: x}` alone is refused, so the entry is replaced whole and never merged.
- **Precedence.** It was checked by hand for a bare hex, `{pigment: hex}`, a derived `{base:}`
  pigment, a theme pigment with and without its own transparency, an alias to a hex, an alias
  to a name, a `.gpl` alias and a painter's pigment name. All match ADR 0070 rule 17, and
  `test_theme_bindings.py::FORMS` pins 11 forms.
- **Images and pins.** Exactly 4 images moved (route-ink and bold, each with its master), 20
  were added with masters and 1 was retired with its master. `plates.json` moved only in
  `hash`, and the only other pin that moved is `MEAN_RGB["bold"]`. This matches `images.md`.
  No budget was raised: the three new shares match the spec and `TOTAL_BUDGET_BYTES` stays
  7,000,000.
- **Notes.** The notes for #67, #69, #70, #104, #105, #106 and #159 are deleted, and no live
  doc links to them. ADR 0046 still names the old paths in code spans, as history.
- **Examples.** They import only names in each package's `__all__`.
- **Prose.** The added docs and examples contain no em or en dashes and no American spellings.

## Findings

1. **SHOULD-FIX: ADR 0071 contradicts the shipped bold theme.**
   - Where: `docs/decisions/0071-golden-regeneration-route-colour-pigment-transparency-cased-bold.md:16, :43, :70`.
   - Evidence: the ADR says "`bold.yaml` sets `line_effects: {route: cased}`" and that the
     route is "cased with `cased`". But `src/pyntpot/maps/themes/bold.yaml:57-61` defines and
     uses its own `bold_cased` preset (width 3.4, colour `#fbf6e8`, strength 1.0), following
     orchestrator decision 23. `write-a-theme.md:460` and `test_theme_named.py:58` already say
     `bold_cased`. The spec AC (`spec.md:171-172`), `plan.md:111, :156, :629, :817` and
     `tasks.md:221` still say `route: cased` too.
   - Fix: in the ADR, say that bold defines `bold_cased` in `effect_presets` and names it from
     `line_effects.route`, and give the reason (the built-in `cased`, tuned close up, is faint
     at card scale). Update the spec AC and the plan rows to match, or note the deviation
     beside them.

2. **SHOULD-FIX: the how-to result card lifts the route instead of haloing it.**
   - Where: `examples/themes/ambleside-cased.yaml:9`.
   - Evidence: the spec AC (`spec.md:149`) asks for "`road_major` cased and the route
     haloed", but the theme sets `route: lifted`. The how-to caption and alt text
     (`case-light-or-shadow-a-line.md:6-8, :47-57`) describe the lifted route consistently, so
     only the spec disagrees.
   - Fix: either set `route: halo` and repaint `how-to/line-effects.webp` and its master, or
     amend the spec AC and plan, with the reason, to say `lifted`.

3. **SHOULD-FIX: the relief sweep's values differ from the spec, and nothing records why.**
   - Where: `examples/relief_grid.py:49`.
   - Evidence: the script uses `STRENGTHS = (0.0, 2.0, 4.0, 8.0)`. `spec.md:182` and
     `plan.md:428` say 0.5, 1, 1.5 and 2. Decision 23 asks only that the figure be "measured
     visibly different", not for new values. In the published image the four cells differ only
     faintly, and the route dominates the window.
   - Fix: amend the spec and plan to the values used, with the ΔE reason the script's comment
     gives.
   - Consider also moving the window so less of the route and of the deckled card edge fall in
     it.

4. **SHOULD-FIX: a Python-built table with no transparency skips the class's built-in value.**
   - Where: `src/pyntpot/maps/cover_pigment.py:117-129`, reached from `coerce_cover_pigment`
     and `_parse`.
   - Evidence: `Style.model_validate({"cover": {"pigments": {"wood": {"pigment": "#112233"}}}})`
     gives `CoverPigment('#112233', None)`, which paints at `km_transparency` 0.06. A Python
     `str` gives 0.05, and the same table in a theme gives 0.05. Rule 17 says `{pigment: hex}`
     with no transparency takes the class's built-in, so Python-built input breaks the
     one-rule promise. The `CoverStyle.pigments` docstring says only a `None` transparency
     takes `km_transparency`.
   - Fix: pass `cover_class` into `_from_table` and default a missing transparency to
     `built_in_transparency(cover_class)`. `_parse` has no class key, so let it return the
     mapping as is and let `__post_init__`'s `coerce_cover_pigment` build it. Add a case to
     `TestPythonBuilt`.

5. **SHOULD-FIX: the #159 property does not test what the AC states.**
   - Where: `tests/property/test_route_colour.py:10`.
   - Evidence: the AC asks for "`#rrggbb` (either case)" with the result in lower case, but
     `HEX = st.from_regex("^#[0-9a-f]{6}$")` generates lower case only. The AC also asks for
     "the nib's resolved `route` ink", which the test never checks; it checks only
     `nib.label_route_ink`.
   - Fix: use `^#[0-9a-fA-F]{6}$`, assert `fed.route_ink.colour == colour.lower()`, and assert
     the nib's resolved route ink through the public path the lettering uses.

6. **SHOULD-FIX: the colour-field iterator is duplicated.**
   - Where: `tests/unit/maps/test_route_colour_feed.py:18-24`.
   - Evidence: `_colour_fields` repeats `test_colour_fields.py:36-45` (`_colour_paths`) without
     the dict branch. The structural AC says "every `Colour`-typed field of every style group".
   - Fix: move `_colour_paths` to `tests/support/` (for example `support/colour_fields.py`) and
     use it in both tests. Have the route test skip `*` paths explicitly, with a comment, or
     check them too.

7. **SHOULD-FIX: a test file has gone over the 400-line budget.**
   - Where: `tests/unit/maps/test_theme_schema.py`.
   - Evidence: the file is 444 lines; it was 397 on PR 1's tip. CLAUDE.md says to split a file
     that goes over budget. `test_no_oversized_files` scans `src/` only (#212), so nothing
     gates this.
   - Fix: move the new cover-pigment and `required` tests (`_object_branch`, `_required`,
     `colour_node`, the two new tests) into `tests/unit/maps/test_theme_schema_cover.py`.

8. **SHOULD-FIX: `tasks.md` disagrees with what is done.**
   - Where: `specs/009a-line-effect-figures-and-galleries/tasks.md:61, :63, :66, :82`.
   - Evidence: the #212 note and issue exist (`docs/issues/tests-docs-images-over-line-budget.md`)
     and the plan review exists (`review-plan.md`), but both lines are unticked. The planned
     note name `tests-docs-images-over-budget.md` also differs from the real one. The
     branch-name comments on the seven issues (:61) are still open, and CLAUDE.md requires
     them at "Starting".
   - Fix: tick :63 and :66 and correct the note name. Post the seven issue comments and tick
     :61. Tick or drop :82.

9. **CONSIDER: the ADR has a markdown gap.**
   - Where: ADR 0071:107-108.
   - Evidence: the table ends with no blank line before `## Retired image`, so some renderers
     swallow the heading into the table.
   - Fix: add a blank line.

10. **CONSIDER: the glow sweep's captions miss the "none" column.**
    - Where: `docs/how-to/case-light-or-shadow-a-line.md:33`, `:43` (shadow) and the matching
      `docs/gallery.md` captions.
    - Evidence: the captions say "The labels read 0, 2, 4 and 6 across", but the image letters
      five columns: none, 0 px, 2 px, 4 px and 6 px. The shadow sweep is the same.
    - Fix: "The labels read none, 0, 2, 4 and 6 across".

11. **CONSIDER: the tutorial's claim about the casing order contradicts the threshold rule.**
    - Where: `docs/tutorials/painting-with-python/cased-strokes.md:56`.
    - Evidence: the page says "a casing laid after the stroke would cover it". But a casing
      leaves every pixel at or above the threshold alone, as the reference
      (`line-effects.md:137`) and the explanation (`:19`) both say, so laid after the stroke it
      would cover only the stroke's soft edge.
    - Fix: "a casing laid after the stroke would eat into its soft edge, and the stroke would
      not glaze over the ring".

12. **CONSIDER: the prose shows the primitives' signatures positionally.**
    - Where: `cased-strokes.md` and `docs/explanation/line-effects.md:9`.
    - Evidence: they show `casing(rgb, mask, effect, threshold, paper)`, but `threshold` and
      `paper` are keyword-only.
    - Fix: write `casing(rgb, mask, effect, *, threshold, paper)`, as `reference/line-effects.md`
      does.

13. **CONSIDER: the brush gallery's table headers do not name the prefix.**
    - Where: `docs/reference/brush-gallery.md:13`.
    - Evidence: both columns are headed `` `a` `` (`` | `a` #255d80 | `a` #6b4423 | ``), which
      does not say which column is RIV = STR and which is LAN.
    - Fix: head them `` RIV = STR `a` #255d80 `` and `` LAN `a` #6b4423 ``.

14. **CONSIDER: some entry forms are not pinned.**
    - Where: `test_theme_bindings.py::FORMS`.
    - Evidence: a table naming a pigment with no transparency (`{pigment: cerulean}`, which
      should take 0.22) is not pinned, and neither is a derived pigment that sets its own
      transparency.
    - Fix: add both forms.

15. **CONSIDER: the #212 note's line count is stale.**
    - Where: `docs/issues/tests-docs-images-over-line-budget.md`.
    - Evidence: the note says the file is 565 lines; it is 511 after the `docs_image.py` split.
    - Fix: update the count, or mark the note partly addressed.

16. **CONSIDER: the shadow sweep barely shows below 5 px.**
    - Where: `how-to/shadow-sweep.webp`.
    - Evidence: below 5 px the shadow is hard to see at page width.
    - Fix: accept it, or raise the sweep's strength literal and repaint only this image.

## Resolution

SHOULD-FIX, all eight fixed:

1. ADR 0071, spec AC, plan rows and tasks now name `bold_cased` (cream `#fbf6e8`, 3.4 px, strength 1.0) and the reason (ΔE 3.6 against 16.9).
2. Spec AC and the how-to say `lifted`, kept, chosen by eye in D3.
3. Spec and plan amended to relief strengths 0, 2, 4, 8, with the ΔE reason. The window is left as it is.
4. Red test first (`TestPythonBuilt`), then `cover_pigment.py`: `_parse` passes a table on and `coerce_cover_pigment` builds it with the class's built-in transparency. `test_model_validate_from_a_dict_builds_cover_pigments` had pinned the old `None`; it now pins 0.3. The two committed schema files changed in one description line only. Bundled themes load by the loader path, so no theme, digest or image moves.
5. The property generates either case and asserts the route ink and `nib.label_route_ink` equal the lower-cased colour. The nib's resolved ink is read through `label_route_ink`; `_ink_colour` is private.
6. `tests/support/colour_fields.py` holds `colour_paths`, used by both tests; the route test skips `*` paths with a comment.
7. `test_theme_schema_cover.py` takes the colour-node, `required` and cover-pigment tests; `test_theme_schema.py` is 388 lines.
8. Tasks ticked for the #212 note (name corrected), the plan review, the route-ink repaint, and the branch comments (verified on all seven issues through the REST API).

CONSIDER applied: 9 (blank line), 10 (captions), 11, 12 (signatures; `azimuth_deg` is keyword-only too), 14 (two forms added to `FORMS`), 15 (line count). Declined: 13, because `test_gallery_values.py` parses the header as `letter` #ink and a longer header needs that parser changed; 16, the shadow sweep, because repainting an image is more than a few lines and no image may move here.

## Elegance pass

Simplification only, behaviour identical: every figure's PNG hashes the same before and after,
and the docs-image goldens, `test_tutorial_quotes` and `test_captions` stay green.

Applied:

- `labelled_grid.py` holds `LABELS`, the one `LabelStyle` literal that seven of the new scripts
  (and `how_to_line_effects.py` in a derived form, `6.0 * NIB_SCALE`) each repeated. Each script
  imports it; `how_to_line_effects.py` loses its local `NIB_SCALE`, `LABEL_PX` and `LABEL_INK`
  (the lettering-over-an-image note's count of `NIB_SCALE` copies drops to 12).
- `labelled_grid.grid_paper(sheet)` replaces eight copies of
  `paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)`, and
  `pigment_gallery._paper`.
- `labelled_grid.on_paper(laid, paper, at)` replaces the paper-crop multiply in
  `setting_grids`, `line_effect_grids` and `line_effect_reasons` (whose `_cell` goes).
  `cased_stroke.paint_cell` keeps it inline because the tutorial quotes that block verbatim.
- `line_effect_reasons._glaze_or_rgb`: the casing and glow branches each repeated the RGB-or-glaze
  split; one local `laid_under` picks the primitive and the split is written once.
- Docstrings' "Public names it uses" lists follow the imports; a stray duplicate comment line
  in `how_to_line_effects.py` goes; `relief_grid.SEED` says what it seeds now that the hand's
  seed comes from `LABELS`.

Rejected:

- A shared `_check(figure)`: five copies, but each is two lines and the helper would add an
  import for no clarity.
- A shared corner `Setting` (`setting_grids`, `line_effect_grids`) and the "later rows named in
  the gap above" settings (`cased_stroke`, `how_to_line_effects`): two uses each.
- A shared `_window` and the paste-resized-cells loop (`relief_grid`, `how_to_line_effects`), and
  `_scaled(LabelStyle, unit)` (`brush_gallery`, `pigment_gallery`): two uses each.
- A shared pigment-wash layer with the `km_transparency` fallback (four copies): it is not grid
  work, so it would need a second sibling module and an `_EXAMPLE_SIBLINGS` entry, and the
  copies differ in how they place the cover.
- A shared brushed-stroke helper: the four copies differ in line, seed, style and override.
- A cached `_spec(figure)` helper across the three figure scripts: each reads its own layout
  and size tables, so a shared one would take as many arguments as it saves.
