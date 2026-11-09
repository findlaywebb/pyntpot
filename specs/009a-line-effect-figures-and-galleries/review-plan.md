# 009a plan review

Reviewer: fresh-context plan reviewer. Reviewed against `e5578fe` (PR 1 not yet built), ADR 0070,
PR 1's `plan.md` and `research.md`, `decisions.md`, CLAUDE.md, CONTRIBUTING.md and the code.

## Verdict: BLOCK

The overall approach holds. #159 belongs in the style, D7 belongs in a leaf binding, and
regenerating once in G works as written. Three things block. The zero-cell criterion is
false for three of the four sweeps. The transparency precedence leaves four ref forms
undefined and cannot be computed where the plan puts it. The #159 pixel tolerance is
contradicted by the research's own numbers. Fix those three, and preferably the
should-fixes, then re-review.

### Checked and sound (no action)

- Task G's scripts all exist with the CLIs used:
  - `repaint.py OUT [NAME...]`;
  - `make_golden.py OUT`;
  - `diff_images.py OUT --ref`;
  - `publish_diffs.py OUT --push`;
  - `make_docs_images.py OUT NAME...`.

  `summary.json` has `files[].path` and `status` (`tests/golden/diff_report.py:30,80,94`).
- Budgets are as stated: 71 entries, 3,482,207 B, and P7.V12b at 821,660.
- The pin list is complete. The base digest is pinned only in `test_style.py`,
  `test_pipeline_fetch_paint.py:30` and `plates.json`; the ADR copies are history.
- **Migration moves no pixel for the shipped themes:**
  - `PaintJob.transp` (`painter/job.py:149-152`) is only called with the 15 cover keys.
  - No shipped theme uses `extends`.
  - bold sets all 15 transparencies and pen-and-ink sets two. Every other role is a bare
    hex, which gets the same float as today.
- **Regenerate once is honoured.** An added image changes no pin. `test_docs_images.py`
  needs the files to exist, so each slice must commit its own.
- **Nothing breaks mid-stream outside golden.** Between A and G, the only tests that go
  stale are golden-marked:
  - `test_route_ink.py`, whose classes are `@pytest.mark.golden`;
  - `test_parity.py`;
  - `test_map_styles.py`;
  - `tests/golden/test_docs_images.py`.
- **PR 1's names match:**
  - the `compositing.py` rename, which PR 2 never cites by path;
  - the public `Palette`, with only `plain` bundled;
  - `basemap.line_effects` and `route_ink.effects`;
  - `GridSpec` and `label_grid`;
  - `cased`, `halo` and `lifted`;
  - `casing`, `glow`, `shadow` and `pen_casing`.
- The mutation claims hold: `only_mutate` is ink and letters only, and `scope.py` emits
  nothing for a class field.

## Findings

1. **[BLOCKING] The "zero cell equals the plain stroke" criterion is false or tautological.**
   - **Plan line:** plan 191-192; spec 109; test `test_each_sweeps_zero_cell_is_the_plain_stroke`.
   - **Evidence:** PR 1 plan S4.
     - `glow` is the identity only at `strength <= 0`. At spread 0, `core` is the line
       itself, so blur 3 and 6 still lift.
     - `shadow` at offset 0 still blurs outside the line.
     - The pen casing sweep has no zero column (gap 1 to 4).
     - "Painted with no effect" and then asserted equal tests nothing.
   - **Fix:**
     - Casing: paint the 0 column *through* `casing(width_px=0)` and assert it is
       byte-equal to an independently painted plain cell.
     - Glow, shadow and pen casing: add a lettered "none" cell painted through the
       primitive at `strength=0` (pen casing: `width_px=0`), and assert that cell instead.
     - Drop "zero cell" wording for those three in the spec.

2. **[BLOCKING] The precedence is incomplete and not computable as placed.**
   - **Plan line:** plan 24-27, 417-423; spec 56-60.
   - **Evidence:**
     - Undefined cases:
       - an alias to a hex, which includes every `.gpl` palette alias (PR 1 `palette_gpl.py`
         gives alias to hex);
       - `{pigment: "#hex"}` with no `transparency`;
       - a theme pigment whose transparency is `None`;
       - a derived `{base: x}` pigment.
     - A value-level `BeforeValidator` never sees the dict key. PR 1's `_Check.leaf` passes
       only `context={"scope": ...}`, so "the role's default" has no role.
     - `test_a_hex_with_none_takes_km_transparency` names a case no theme can produce,
       because every cover class has a built-in transparency.
     - An `extends` child's bare hex silently drops its parent's transparency, and nothing
       says so.
   - **Fix:**
     - State one rule for every ref form: the entry's own, else the resolved pigment's own
       (a derived pigment inherits its base's), else the cover class's built-in pigment's.
     - `km_transparency` applies only to a Python-built `CoverPigment(colour, None)`.
     - Pass the class through context (`"cover_class": key`), or resolve in a checker pass
       over `cover.pigments` items.
     - Add tests for:
       - an alias to a hex;
       - a `.gpl` alias;
       - a theme pigment with no transparency;
       - a derived pigment;
       - an extends child taking the built-in transparency, not its parent's.
     - Document the extends case in the ADR and the how-to.
     - Record the new ADR as "amends 0070 rule 17" in its index row (D7 as approved said
       km_transparency).

3. **[BLOCKING] The #159 pixel tolerance contradicts the measurement.**
   - **Plan line:** spec 41-43; plan 334.
   - **Evidence:** `research.md:488,535`.
     - On the card, the default label (192, 52, 89) sits 20 off `#c22050` (194, 32, 80)
       in G.
     - The fed label (116, 63, 145) sits 19 off `#6a2c91` (106, 44, 145).
     - The plan does not say which image (nib plate or card), or how the "start" label is
       found.
   - **Fix:** measure on the nib plate RGBA: alpha ≥ 0.9 inside the "start" label's box
     from the `Lettering` labels. Assert either of these, and amend the spec:
     - the mean is nearer `VIOLET` than `#c22050` by RGB distance;
     - or it equals a mean measured in P0, pinned with a stated tolerance.

4. **[SHOULD-FIX] The 400-line budget.**
   - **Plan line:** plan 225.
   - **Evidence:**
     - PR 1 projects `style_groups.py` at about 375 lines. `CoverPigment` with its docstring
       and default builder passes 400, and `test_boundaries.py::test_no_oversized_files`
       covers `src/`.
     - `theme_check.py` reaches about 350 lines after PR 1, before the retired-key message
       and the binding.
     - `test_theme_check.py` is at 361, `test_reference_values.py` at 338, and
       `docs_images.py` at 565, already over.
   - **Fix:**
     - Put the type and default in a new `maps/cover_pigment.py`.
     - Put the resolver and the retired-key table in a new `maps/theme_bindings.py`. That
       table does not exist today: no moved or retired mechanism is in `theme_*.py`. Write
       its exact message in the plan.
     - Put the new D7, gallery and line-effect tests in new files.
     - Say how the 009a registry block avoids growing `docs_images.py`.

5. **[SHOULD-FIX] Breakage from the `CoverPigment` type is unlisted.**
   - **Plan line:** plan 223-248.
   - **Evidence:**
     - `tests/property/test_theme_merge.py:194-205` dumps `merge(_BASE, override)` through
       `tests/support/theme_dump.py`. That writes a NamedTuple as a list, which then will
       not load.
     - `tests/unit/maps/painter/test_smoke.py:246` calls `rgb(...pigments["wood"])`.
     - `docs/how-to/write-a-theme.md:52-53` shows `'#8f9f6a'`.
     - `docs/reference/maps.md` needs the `CoverPigment` directive
       (`tests/architecture/test_site.py:100`).
     - `ambleside-cased` must be added to `THEME_NAMES` (`test_example_themes.py:12`), not
       only to `DIGESTS`.
     - "NamedTuple or frozen non-dataclass" is left open.
   - **Fix:**
     - Choose NamedTuple: `asdict` keeps it, the digest hashes it as a list, and merge
       replaces it whole.
     - Make `theme_dump` write `{pigment, transparency}`.
     - Add the files above.
     - Add a glossary row ("cover pigment"). "Role" and "binding" are not glossary terms;
       use "cover class".

6. **[SHOULD-FIX] The preset values conflict between the two plans.**
   - **Plan line:** plan 314.
   - **Evidence:** PR 1 S5a says the presets are "provisional, tuned with figures in PR 2",
     but PR 2 lists the presets under "leave alone". F then adopts a provisional 1.2 px
     casing, which may not show on a 720 px card.
   - **Fix:** add a D step that tunes `BUILT_IN_PRESETS` (in maps; no PR 1 pin depends on
     them) against the presets figure before C to F paint, and record the values.

7. **[SHOULD-FIX] Bold's adoption is justified by the wrong issue.**
   - **Plan line:** plan 41-50.
   - **Evidence:** #104 is the *route* casing (`docs/features/maps-route-casing.md:1-17`).
     Bold's old value was a route `casing_px = 1.2`, which is exactly `cased`. Casing
     `road_major` repaints the base and shifts names.
   - **Fix:** either use `line_effects: {route: cased}`, which is compose-only, moves only
     `map-styles/bold` and matches history; or justify `road_major` with a measured
     before and after in P0 and list the names that move.

8. **[SHOULD-FIX] Pen casing's scope is unstated.**
   - **Evidence:** PR 1 Decisions say wiring pen casing into the model "is PR 2's design".
     PR 2 neither wires it nor rules it out.
   - **Fix:** add to Out of scope: pen casing stays an `ink` primitive with no theme key.
     The reference page states this as a capability fact.

9. **[SHOULD-FIX] The sweep units are ambiguous.**
   - **Plan line:** plan 180-190.
   - **Evidence:** the primitives take array pixels, while theme fields are display pixels,
     converted by `lay_stack` at `scale`.
   - **Fix:** paint the sweeps at scale 1, or through the model, so a lettered "2 px"
     equals `width_px: 2` in a theme.

10. **[SHOULD-FIX] The per-track `diff_images.py --ref` check proves nothing.**
    - **Plan line:** plan 386.
    - **Evidence:** it only diffs files the track wrote and never repaints.
    - **Fix:** run `repaint.py OUT <reachable names> --no-lynmouth`:
      - after A: `how-to/route-ink*.webp`;
      - after B and F: `map-styles/*`, `places/*` and `hero.webp`.

11. **[SHOULD-FIX] Task G's acceptance is ambiguous.**
    - **Plan line:** tasks 95-97.
    - **Evidence:**
      - In `repaint`'s summary, `added` is 0.
      - In `recheck`, `added` is 40 (20 images plus 20 masters).
      - The "exactly" check runs after the copy.
    - **Fix:**
      - Split the expected sets per summary.
      - Run the check before copying.
      - Have P0 confirm this machine reproduces the goldens exactly (the smoke test passes
        exact here) before C paints any master.

12. **[SHOULD-FIX] `Closes #159, #69, …` closes only #159.**
    - **Plan line:** spec 157; tasks 108.
    - **Evidence:** GitHub needs the keyword before each issue.
    - **Fix:** one `Closes #N` per issue. P0 also comments the branch on all seven issues
      (CLAUDE.md "Starting").

13. **[SHOULD-FIX] The setting grids are under-specified.**
    - **Plan line:** plan 200-207.
    - **Evidence:**
      - Granulation has no values.
      - "Smooth and cold-press" is unmapped to fields.
      - "Darkness (load)" conflates two separate `BRUSH_TREATMENTS` keys; the spec says load.
      - No image is mapped to a page or section. CONTRIBUTING.md:145-147 allows reference
        pages only swatch sheets.
    - **Fix:** a table of image to page and section, plus the exact values and fields.

14. **[CONSIDER]** `RIV` and `STR` are the same brush: the same `#255d80`, and neither
    `riv` nor `str` is a `brush_overrides` key (`brush_style.py:208-216`). Two identical
    columns are a dump, not a reference. Letter "RIV = STR" and keep both ids in the
    page table.

15. **[CONSIDER]**
    - The "effect" trap lives in CONTRIBUTING.md:143-144, not CLAUDE.md.
    - There is no `default` map-styles image (spec 68; `map_styles.FIGURES`).
    - Split D (4 scripts, 4 pages, 9 images) for Sonnet.
    - State that `separation_pigments` keeps `wash.separation_transparency`, as a designed
      gap.

## Resolution

1. Fixed as asked: casing's 0 column goes through `casing(width_px=0)`; glow, shadow and pen casing get a lettered "none" cell through the primitive (`strength=0`, pen casing `width_px=0`); each off cell is compared with an independently painted `paint_cell(None)` by `tobytes()`; "zero cell" is gone from the spec.
2. Fixed as asked (orchestrator ruling): one rule for every form (entry's own, else the resolved pigment's own, a derived pigment's base's, else the cover class's built-in pigment's), `km_transparency` only for a Python-built `None`, the class passed as `"cover_class"` in validation context, a parametrised test per form plus the `extends` child, and ADR 0070 rule 17 edited in place (no "amends" row, since 0070 is unmerged). Added beyond the review: a Python-built `str` takes the class's built-in, and `CoverPigment` carries a pydantic hook so `Style.model_validate` keeps working.
3. Fixed as asked: measured on the nib plate's RGBA, alpha at least 0.9 inside the "start" label's box from `Lettering.labels`, mean nearer `VIOLET` than `#c22050`; spec amended.
4. Fixed, one part differently: `CoverPigment` goes in `maps/cover_pigment.py` and the resolver in `maps/theme_bindings.py`, but the moved key reuses the existing `theme_check.RENAMED_KEYS` (one entry, exact message in the plan) rather than a new table, because the code already has that mechanism. New tests go in new files; the 009a registry blocks go in `tests/support/docs_images_009a.py` after `DocsImage` moves to `docs_image.py`; the pre-existing 565-line overrun is filed in P0.
5. Fixed as asked: NamedTuple chosen; `theme_dump` writes `{pigment, transparency}`; `test_theme_merge.py`, `test_smoke.py:246`, `write-a-theme.md:52-53`, the `maps.md` directive, `THEME_NAMES` and a "cover pigment" glossary row added; "role" replaced by "cover class".
6. Fixed (orchestrator ruling): D1 tunes `BUILT_IN_PRESETS` before any image naming a preset is painted, with PR 1's preset and effect property and unit tests as its gate; values recorded in Decisions and the ADR.
7. Fixed (orchestrator ruling): bold takes `line_effects: {route: cased}`, the route casing it declared until ADR 0046; it moves `digest()` only, so the moved rows are bold's digest (B then F), base digest (B only), `map-styles/bold` and its master, and `MEAN_RGB["bold"]`.
8. Fixed as asked: Out of scope says pen casing stays an `ink` primitive with no theme key, and the reference page states it; its sweep moves to the tutorial page.
9. Fixed: sweeps are painted at scale 1, so a lettered "2 px" is `width_px: 2` at scale 1.
10. Fixed as asked: `repaint.py OUT <names> --no-lynmouth` after A, B and F, with the expected `changed` set for each.
11. Fixed as asked: G checks the repaint summary (changed four, added none) before copying, and the recheck summary (changed four, added 40) after; P0 confirms the machine reproduces the goldens exactly.
12. Fixed as asked: one `Closes #N` line per issue in spec and tasks; P0 comments the branch on all seven issues.
13. Fixed as asked: a page-and-section table for every image and a table of exact fields and values (`pool` by `Sheet.seed`; `Sheet.gran_px` by `Sheet.fibre`; treatment `dry` by `load`; `relief_strength`); the dryness sweep and galleries are swatch sheets, which reference pages may show.
14. Adopted: "RIV = STR" shares one column, both ids lettered in the cell and listed in the page table.
15. Adopted: the trap is cited as CONTRIBUTING.md:143 and left for the user; the `default` map-styles image is dropped from the spec; D is split into D1 to D4; the separation transparency is a stated designed gap.

## Re-review

Reviewer: fresh-context plan reviewer, against `d0010e1` and the working-tree revision of
PR 1's `plan.md` (in flux; its `ThemeScope` and `Palette` shapes were rechecked there).

### Verdict: BLOCK

There is one blocking finding. Rule 17's "alias to a name" form cannot be computed from
the shapes PR 1 fixes, and neither can the palettes figure. All the other findings are
plan edits the implementer can apply trivially.

### Resolutions verified

- **1 (off cells).** Plan 263-279 and the test row at 489 are right in principle. Casing
  at `width_px <= 0` and glow at `strength <= 0` return `rgb` itself (009 plan:405-410).
  Shadow at `strength=0` gives `a == 0`, so the `where` keeps `rgb`. See finding 6 for the
  dtype and the pen casing.
- **2 (precedence).** The table at plan 31-43 covers every form of ref. ADR 0070 rule 17
  has been edited in place to match it. The context key reaches the resolver through
  `TableCheck.leaf`.
- **Migration moves no pixel.**
  - `PaintJob.transp` (`painter/job.py:149-152`) is called only with the 15 cover keys
    (`plates.py:66`, `wood.py:54,84`, `relief.py:26`, `water.py:154,181`,
    `cover.py:155,176`).
  - `theme_merge.merge` merges dict entries one by one, so pen-and-ink's unset classes
    keep the default transparencies.
  - bold sets all 15 classes, and pen-and-ink sets `pale` and `wood`. No example theme sets
    a transparency, and none uses `extends`. The rule "bare hex takes the class's built-in
    transparency" therefore reproduces today's floats exactly.
- **3 (pixel test).** `Label.kind`, `Label.box` and the `start` marker exist
  (`lettering/label.py:51-76`, `picks.py:188`).
- **4, 5.** The new modules, `theme_dump`, the merge property and `test_smoke.py:246` are
  all listed. The property in `tests/property/test_theme_merge.py:208-218` stays sound
  with a `{pigment, transparency}` dump.
- **7 (bold).** `map_styles.FIGURES` is bold's only image consumer, and `MEAN_RGB` is its
  only other pin. Rule 9 keeps a route stack out of `base_digest` and `lettering_digest`.
- **10, 11, 12, 13, 14, 15.** Applied. The six importers of `support.docs_images` named at
  plan 375-376 are complete: `tests/docs/test_gallery.py` imports only `IMAGES`, which
  stays. No budget or share is raised.

### Findings

1. **[BLOCKING] An alias keeps no pigment, so "alias to a name" and the palettes figure
   cannot be built.**
   - **Plan line:** plan 34, 52-54 and 252-254; the `alias-to-name` id at plan 479;
     spec 102-103.
   - **Evidence:**
     - PR 1 fixes `ThemeScope.aliases: Mapping[str, Bound[Colour]]` "so S3b and S5a fill
       it without changing it" (009 plan:280-284).
     - PR 1 fixes `Palette(name, colours: Mapping[str, Colour])` (009 plan:389).
     - With only the hex kept, `cover.pigments.water: blue` (plain's `blue: ultramarine`)
       cannot reach ultramarine's 0.06.
     - The public `Palette` cannot name "the pigment it names" either.
     - B would have to change PR 1's public `Palette` and the frozen scope shape, and no
       file list or ADR line covers that change.
   - **Fix:**
     - In PR 1's plan, which is unmerged: `aliases: Mapping[str, Bound[Pigment]]`, where
       a hex alias is an anonymous `Pigment` with transparency `None`.
     - In the same plan: `Palette.pigments: Mapping[str, Pigment]`, with `colours`
       derived from it.
     - `resolve_colour` returns `.colour`.
     - Add a P0 check for these shapes.
     - `resolve_cover_pigment` reads the bound `Pigment`.

2. **[SHOULD-FIX] Track A cannot go green.**
   - **Evidence:** `tests/unit/maps/test_style.py:347-352`,
     `test_a_fed_ink_moves_only_the_full_digest`, asserts that a fed colour keeps
     `LETTERING_DIGEST`. `test_style.py` is B's (plan 552-553, 561-563).
   - **Fix:** list that test under A: it becomes width-only, and the colour case lives in
     `test_route_colour_feed.py`.

3. **[SHOULD-FIX] PR 1's `tests/property/test_line_effect_digests.py` breaks in D3 and F.**
   - **Evidence:** the property is described at 009 plan:649-652. A child's `{}` replaces
     the parent's stack whole, so bold and `ambleside-cased` fail it.
   - **Fix:**
     - List the property under D3 and F.
     - Draw only the classes the sampled theme does not set.
     - Have P0 grep PR 1's tip for 16-hex digest literals (`test_digest_omits.py` "keeps
       their pins") and add each file to B's pins.

4. **[SHOULD-FIX] D1 runs scripts that D2 and D3 write.**
   - **Plan line:** plan 391-396 and 550.
   - **Evidence:**
     - D1 tunes against the presets figure and the sweeps, but D2 and D3 write those
       scripts.
     - The sweeps' held values are unstated: glow strength, shadow strength and colour,
       and the road width.
   - **Fix:**
     - Pin the held values as literals that are independent of the presets.
     - Order D2, then D1, then D3, with D1 drafting the presets figure in scratch.

5. **[SHOULD-FIX] The dryness grid's override is read under a different key.**
   - **Evidence:** `brush_from_id` reads `brush_overrides[override or "maj"]`
     (`ink/brush.py:199`), so setting `["major"]` does nothing.
   - **Fix:** state `brush_from_id("MAJ2-c", 12, 1.0, style, override="major")`.

6. **[SHOULD-FIX] The off-cell byte compare can fail.**
   - **Evidence:**
     - The primitives return float32 (009 plan:426-427).
     - `pen_casing` at width 0 returns `(rgb, zeros)`, and a zero-density composite may not
       be exact.
     - The plain pen cell is undefined.
   - **Fix:**
     - `paint_cell` returns float32.
     - The pen casing's edge layer is composited only when `edges.any()`.
     - Define the plain pen cell as the tint plus the centre ink line.

7. **[SHOULD-FIX] The `RENAMED_KEYS` entry departs from ADR 0069 and breaks a pin.**
   - **Evidence:**
     - ADR 0069:323 says a removed field "fails as an unknown key".
     - `test_theme_check.py:146` pins `RENAMED_KEYS` exactly.
   - **Fix:** record the departure in the new ADR, and list the pin under B.

8. **[SHOULD-FIX] The repaints after B and F miss images those tracks reach.**
   - **Plan line:** plan 542-544.
   - **Evidence:** the name list omits `gallery/route-map`, `tutorials/route-map`,
     `social-preview.jpg`, `how-to/command-line.webp` and `how-to/route-ink-grid.webp`.
   - **Fix:** pass every fixture-reading registry name except `how-to/route-ink.webp`.

9. **[CONSIDER]**
   - Spec "Images, budgets" still says the images register in `docs_images.py`. Name
     `docs_images_009a.py`.
   - State that a Python-built key outside the 15 classes gets `None`.

## Re-review resolution

1. Finding 1: PR 1 plan change, pending. PR 1's plan will make `ThemeScope.aliases` a `Mapping[str, Bound[Pigment]]` and give `Palette` its `pigments`; 009a is written against those shapes, with a P0 check that PR 1's tip has them, alias rows in the transparency table resolving through the bound `Pigment`, and the palettes figure reading `Palette.pigments`.
2. Fixed as asked (verified `tests/unit/maps/test_style.py:347-352`): A lists the test, which becomes `test_a_fed_width_moves_only_the_full_digest`, width-only; the colour case lives in `test_route_colour_feed.py`; the ownership note says A edits that one test and B re-pins the constants.
3. Fixed as asked: P0 checks whether PR 1's `test_line_effect_digests.py` draws only the classes the sampled theme does not set, and greps PR 1's tip for every quoted 16-hex digest literal, adding each file to B's pins; D3 restricts the property if needed, and F runs it with bold's route set.
4. Fixed as asked: the sweeps' held values are pinned literals (road width, glow strength, shadow strength, colour and azimuth, pen line and edge widths), never read from a preset; the order is D2, then D1, then D3, with D1 drafting the presets figure in scratch.
5. Fixed as asked (verified `ink/brush.py:199`): the dryness grid reads `brush_from_id("MAJ2-c", 12, 1.0, style, override="major")`.
6. Fixed as asked: `paint_cell` returns float32, the pen casing cell composites its edges only when `edges.any()`, and the plain pen cell is the tint plus the centre ink line.
7. Fixed as asked (verified ADR 0069:323 and `test_theme_check.py:146`): the new ADR records the departure, and B updates the `RENAMED_KEYS` pin.
8. Fixed as asked (verified from `DocsImage.fixture`): the repaints after B and F pass all 15 fixture-reading names except `how-to/route-ink.webp`.
9. Applied: the spec names `docs_images_009a.py`; a Python-built key outside the 15 classes gets `None`, so `paper.km_transparency`, with a test.

## Round 3

Reviewer: fresh-context plan reviewer, against `82cc5a9` and PR 1's revised `plan.md`
(`ThemeScope.aliases: Mapping[str, Bound[Pigment]]`, `Palette.pigments`, no `colours`).

### Verdict: BLOCK

The re-review resolutions hold. Three findings would fail a gate or break the bar as
written: a moved pin is missing from the table; a `CoverPigment` has no single written form,
so the docs and the schema would show a form the loader refuses; and the resolver bypasses
`resolve_pigment`, so palette aliases cannot resolve.

### Resolutions verified

- **1 (alias shapes).** PR 1 plan:311-316 gives `aliases: Mapping[str, Bound[Pigment]]` (a
  hex alias is `pigment("#...")`). PR 1 plan:436-442 gives `Palette(name, pigments)` with no
  `colours`. 009a plan:56, 263-264, spec:106 and tasks:18-21 use these. No `Palette.colours`
  is left.
- **2.** `test_style.py:348-352` is as cited.
- **3.** PR 1 plan:954 samples themes by classes. D3 and F restrict it.
- **4.** The order D2, then D1, then D3 holds. The provisional presets match PR 1 plan:630-632.
- **5.** `brush.py:199` reads `brush_overrides.get(override or cls.lower())`.
- **7.** ADR 0069:323 and `test_theme_check.py:146` are as cited. `TableCheck.unknown`
  writes "renamed to {new}" at the key's line (`theme_check.py:148-151`).
- **8.** The registry has 16 entries that read a fixture. All 15 listed are among them,
  and the plan leaves out only `route-ink`. Every example that imports `pyntpot.maps`
  writes only images that read a fixture. Only `map_styles` paints `bold`. So B's set (none)
  and F's set (`map-styles/bold`) are complete.
- **Names.** These match PR 1's plan:
  - `basemap.line_effects` and `route_ink.effects`;
  - `GridSpec` and `label_grid`;
  - `TableCheck.leaf`'s context;
  - `cased`, `halo` and `lifted`.

  `#c22050` is the default of `route_ink.colour` and `nib.label_route_ink` only, so the
  structural test needs no third field.

### Findings

1. **[BLOCKING] A moved pin is missing from the moved table.**
   - **Plan line:** plan 116-133; tasks 24-28.
   - **Evidence:**
     - `tests/unit/maps/test_style_groups.py:252,260` pins `SOURCED[PaperStyle]`
       `0af5f9f84facb9e9` and `SOURCED[CoverStyle]` `8ff38fcbad0d7a6f`. Each is the sha256
       of `json.dumps(asdict(group()))` (:348-351).
     - B removes a `PaperStyle` field and turns each `cover.pigments` value into a
       two-item list, so both pins move in B.
     - P0's filter keeps only pins of `digest()`, `base_digest()` or `lettering_digest()`,
       so it drops these two.
   - **Fix:**
     - Add two rows: these two pins move in B, with no pixels, for the D7 reason.
     - Widen P0's filter to any 16-hex hash of style data.

2. **[BLOCKING] A `CoverPigment` has no single written form.**
   - **Plan line:** plan 369-371, 391-393 and 397.
   - **Evidence:** three helpers in the tests write the NamedTuple as a list:
     - `tests/docs/test_reference_values.py:89-113,206-209`: `entry_value` makes
       `style-fields.md`'s `cover.pigments` Default cells read `["#dfe0b0", 0.06]`. The
       schema refuses that form. The file is not B's.
     - `test_theme_schema.py:136-140`: the schema `default` must equal the JSON dump (a
       list), which is invalid against the field's own `anyOf`.
     - `test_theme_schema.py:100-120,234`: the walker finds no `properties` under the
       `anyOf`, so bold's and pen-and-ink's migrated `pigment` and `transparency` keys
       are reported as outside the schema.
   - **Fix:**
     - One rule: the docs Default cells (`entry_value`), the schema `default`
       (`theme_schema._json`) and `theme_dump` all write a `CoverPigment` as
       `{pigment: "#hex", transparency: t}`.
     - Give `test_reference_values.py` to B.
     - The walker descends into the object branch of an `anyOf`.

3. **[BLOCKING] The resolver bypasses `resolve_pigment`.**
   - **Plan line:** plan 54-58; tasks 12.
   - **Evidence:**
     - PR 1 plan:313-314 says `aliases` holds theme aliases only. Palette aliases sit
       under `scope.palette`.
     - The prescribed lookup (`aliases`, then `scope.registry.get`) cannot resolve a
       `.gpl` alias (the `gpl-alias` row) or `palette: plain` with `water: blue`, the
       case at PR 1 plan:1072.
     - It also duplicates the lookup order and the text of a miss.
   - **Fix:**
     - `resolve_cover_pigment` calls `resolve_pigment(ref, scope)` for a bare ref and for
       the table's `pigment`.
     - P0 confirms `resolve_pigment` on PR 1's tip.
     - Add a test id, `palette-alias-to-name`.

4. **[SHOULD-FIX] B breaks PR 1 tests that it does not list.**
   - **Evidence:** PR 1 plan:181-182 and 368-370.
     - `test_registry_defaults.py` reads `PaperStyle().pigment_transparency`.
     - `test_theme_colour_names.py` expects `cover.pigments.built` to load as `#2b3d8f`.
   - **Fix:** list both files under B. P0 greps PR 1's tip for `pigment_transparency` and
     `cover.pigments` in `tests/`, and B owns every hit.

5. **[SHOULD-FIX] The presets figure cannot reach the presets.**
   - **Plan line:** plan 300-303.
   - **Evidence:** `BUILT_IN_PRESETS` is not public (ADR 0070:312-314), and
     `test_examples.py` refuses private imports. Literal values would drift from D1's
     tuning.
   - **Fix:** each cell loads a theme. The script writes `extends: <ambleside.yaml>` and
     `line_effects: {route: <name>}` to `out_dir`, then calls `Style.from_yaml`.

6. **[SHOULD-FIX] Errors in the table form have no stated location.**
   - **Plan line:** plan 529.
   - **Evidence:** a leaf's problem lands at `cover.pigments.<class>`
     (`theme_check.py:202-208`), not at `.pigment`. An unknown inner key gets no nearest
     name. A `bool` passes an `isinstance(int)` check.
   - **Fix:** check the table's keys with `pigment` and `transparency` as the known
     names, so each error is at its own line. `transparency` is a strict number from 0 to
     1, and a `bool` or `str` is refused.

7. **[CONSIDER]**
   - Move `Option` with `DocsImage` (`docs_images.py:59`).
   - After A, `style-fields.md:380` ("paints no plate again") is false for a fed colour.
   - `ambleside-cased.yaml` should `extends: ambleside.yaml`.

## Round 3 resolution

1. Fixed as asked (verified `test_style_groups.py:252,260,348-351`): two `SOURCED` rows move in B with no pixels; P0's grep is `git grep -nwE '[0-9a-f]{16}'`, keeping any hash of style data, which also finds both halves of `GOLDEN_HASH` (`test_pipeline_fetch_paint.py:30`) that the quoted pattern missed.
2. Fixed as asked (verified `test_reference_values.py:89-113,206-209`, `test_theme_schema.py:100-120,136-140`, `theme_schema.py:167-175`, `theme_dump.py:18-24`): one written form, a ref or `{pigment, transparency}`, never a list, in the dump (`plain_table`), schema default, Default cells and checker; B owns `test_reference_values.py`; the walker descends into an `anyOf`'s object branch; the hook refuses a list. ADR 0070 rule 17 already states both theme forms, so it is not edited.
3. Fixed as asked (verified PR 1 plan:311-336, 466, 506): `resolve_cover_pigment` calls `resolve_pigment(ref, scope)` only; P0 confirms it; new id `palette-alias-to-name` and an Approach table row.
4. Fixed as asked (verified PR 1 plan:181-182, 368-370): B owns `test_registry_defaults.py` and `test_theme_colour_names.py`; P0 greps PR 1's tip for `pigment_transparency`, `cover.pigments` and `.pigments[` in `tests/`.
5. Fixed as asked (verified `test_examples.py:1-8`, `Style.from_yaml` at `style.py:123`, relative `extends` per `theme_resolve.py:11-12`): each preset cell loads a theme file written under `out_dir` with an absolute `extends`.
6. Fixed as asked (verified `theme_check.py:148-153,201-208`, per-key lines at `theme_read.py:96-104`; a strict pydantic float with `ge=0, le=1` refuses `True` and `"0.5"`, checked here): `TableCheck.field` checks the table key by key; errors parametrised by `ids=`.
7. Applied: `Option` moves with `DocsImage` (`docs_images.py:59`); B corrects `style-fields.md:380`; `ambleside-cased.yaml` extends `ambleside.yaml`.

Sweep (tests/ grepped per track for touched symbols, fields and 16-hex hashes): one new gap, `test_one_source_of_defaults.py:173-175` counts ten theme files, assigned to D3 (eleven). Checked, no edit needed: `painter/test_job.py:131-134` (a key outside the classes still falls back), `test_route_ink.py` and `test_style.py:340-346` after A, `test_reference_pages.py`'s field coverage, `test_gallery.py` (imports only `IMAGES`), `CLASSIC_PLATE_SHA` and the cache keys (not style data).

## Round 4

Reviewer: fresh-context plan reviewer, against `70ccd61` and PR 1's revised `plan.md`
(effect value types in `ink/effect_types.py`, primitives taking their value type,
`label_grid(img, boxes, columns, rows, style, *, extra=())` with a `LabelStyle`, eight
`ink` effect exports at merge gate A, `maps` adding only `EffectStack`).

### Verdict: BLOCK

One finding would fail a gate as written. The figure scripts thread `LINE_THRESHOLD`,
which is not public. The other findings are signature drift from PR 1's latest revision,
which the implementer can absorb.

### Round 3 resolutions verified

- **1.** `test_style_groups.py:252,260` pin `0af5f9f84facb9e9` and `8ff38fcbad0d7a6f`.
  The hash is at :350, `json.dumps(asdict(group()), sort_keys=True, default=str)`. Plan
  rows 150-151 hold.
- **2.** These are as cited:
  - `test_reference_values.py:108-112` (`entry_value`) and :206-209;
  - `test_theme_schema.py:100-120` (the walker has no `anyOf` branch) and :136-140;
  - `theme_schema.py:167-175` (`_json` sends a tuple to a list, so the `CoverPigment`
    branch must come before the tuple branch);
  - `theme_dump.py:18-24`.
- **3.** `resolve_pigment(text, scope)` is at PR 1 plan:345-349 (the lines moved; the
  content holds). Theme alias, then palette alias, then registry.
- **4.** `test_registry_defaults.py` is at PR 1 plan:189 and `test_theme_colour_names.py`
  at :382.
- **5.** These are as cited:
  - `test_examples.py:1-8,58-64`: any `pyntpot.*` module that is not one of the four
    public `__init__`s is refused;
  - `Style.from_yaml` at `style.py:123`;
  - `theme_resolve.py:8-12`: an absolute path is allowed.
- **6.** `theme_check.py:148-153,201-208` and `theme_read.py:96-104` are as cited. Run
  here: `Annotated[float, Field(strict=True, ge=0, le=1)]` accepts `1` as `1.0` and
  refuses `True`, `"0.5"` and `1.5`.
- **7.** `docs_images.py:57-59` holds `Kind`, `Encoding` and `Option`, and
  `style-fields.md:380` is as quoted.
- **Merge.** `theme_resolve.py:133-146` merges *checked* tables, so a `CoverPigment` leaf
  (a tuple) replaces the parent's whole (`theme_merge.py:30-35`). The leaf rule holds.

### PR 1 names, against PR 1's current plan

These match:
- `Casing`, `Glow`, `Shadow` and `PenCasing`, with fields `width_px`, `colour`,
  `strength`, `spread_px`, `blur_px`, `offset_px` and `edge_px`;
- `Palette.names()` and `Palette.pigments`;
- `Style.from_yaml` and `line_effects: {route: <preset>}`;
- `road_major` as a line class;
- `BUILT_IN_PRESETS` used only in tests and D1.

The mismatches are findings 1 to 3.

### Findings

1. **[BLOCKING] `LINE_THRESHOLD` is not public, so no example can import it.**
   - **Plan line:** 307-309 ("Every sweep holds `threshold=LINE_THRESHOLD`"). The same
     need applies to `line_effect_reasons.py` and `cased_stroke.py`, since every
     primitive requires `threshold`.
   - **Evidence:**
     - PR 1 plan:578 puts it in `ink/effect_mask.py`.
     - Gate A exports exactly eight names (PR 1 plan:798-799), and ADR 0070 "Public
       names" (:312-316) does not list it.
     - `from pyntpot.ink.effect_mask import LINE_THRESHOLD` fails
       `test_examples.py::_is_bad_from_import` (:58-64).
     - Exporting it would be an unrecorded public-API change.
   - **Fix:**
     - Each effect script holds `THRESHOLD = 0.3` as a literal, consistent with the
       "held values are script literals" rule.
     - `test_line_effect_figures.py` gains
       `test_the_scripts_threshold_is_the_engines`, which loads each script with
       `load_example` and asserts its `THRESHOLD` equals
       `pyntpot.ink.effect_mask.LINE_THRESHOLD`.
     - Add this to D2 and D4 and the test-plan row.

2. **[SHOULD-FIX] The sweep calls are written in PR 1's old per-field form, and
   `shadow` has no `paper`.**
   - **Plan line:** 307-326, for example `casing(width_px=0)`, `glow(strength=0)`,
     `pen_casing(width_px=0)`, and "`paper=None`" for every sweep.
   - **Evidence:** PR 1 plan:582-601 gives:
     - `casing(rgb, mask, effect: Casing, *, threshold, paper=None)` (`glow` and
       `pen_casing` likewise);
     - `shadow(rgb, mask, effect: Shadow, *, azimuth_deg, threshold)`, which has no
       `paper`, so passing `paper=None` is a `TypeError` and a `ty` error.
     - `Casing(colour="paynes_grey")` fails, because `normalise_colours` parses hex only.
   - **Fix:** write each call in full:
     - `casing(rgb, mask, Casing(width_px=w, colour=c, strength=1.0), threshold=THRESHOLD, paper=None)`,
       with `c` either `Colour("#ffffff")` or `pigment("paynes_grey").colour`;
     - `glow(rgb, mask, Glow(spread_px=s, blur_px=b, strength=0.8), threshold=THRESHOLD, paper=None)`;
     - `shadow(rgb, mask, Shadow(offset_px=o, blur_px=b, strength=0.4), azimuth_deg=315, threshold=THRESHOLD)`;
     - `pen_casing(rgb, mask, PenCasing(width_px=g, edge_px=e), threshold=THRESHOLD, paper=None)`;
     - each off cell is the same call with the value type's default (`Glow()`,
       `Shadow()`, `PenCasing()`, `Casing(width_px=0, ...)`).
     - Any signature the pages quote with bare names lists all five parameters,
       because `test_docs_signatures.py:58-70` compares them in order.

3. **[SHOULD-FIX] `label_grid` now takes a `LabelStyle`, and the plan prescribes none.**
   - **Plan line:** 254 and 520-521; tasks 16.
   - **Evidence:** PR 1 plan:871-878 gives `label_grid(img, boxes, columns, rows, style,
     *, extra=())` and `LabelStyle(px, ink, pen_px, gran_px, seed, col_dy=14, row_dx=12,
     row_dy=7)`. Without a prescription, eight new scripts each pick label size, ink,
     grain and seed, so "the default hand" will differ figure to figure.
   - **Fix:**
     - Each new script holds one `LABELS = LabelStyle(...)` constant, copying
       `tutorial_grids`' values (PR 1 plan:889-890) as literals.
     - Per-cell ids and margin values go through `extra=`.
     - D2 adds `sweep_grid` (PR 1 has no sweep loop), so the condition on that step
       resolves.
     - Add `LabelStyle` and `letter_over` to P0's list.

4. **[SHOULD-FIX] `paint_cell` gives no layer order and no space.**
   - **Plan line:** 302-306, against the conventions at 253 ("painted on
     `paper_plate`").
   - **Evidence:**
     - PR 1 lays a stack on the ground *before* the line (PR 1 plan:820-830). A casing
       laid after the stroke covers the stroke, because the casing alpha is full inside
       the mask.
     - `paper=None` means wash space, where 1 is the paper. A cell already on the cream
       paper plate would get a pure `#ffffff` ring, not "paper".
   - **Fix:** state the order: the wash in wash space, then the effect (with mask = the
     stroke's density), then the stroke composited over it, then multiplication by the
     `paper_plate` crop. `paint_cell` returns the result after that last step.

5. **[SHOULD-FIX] P0 does not check that names are public.**
   - **Plan line:** tasks 5-16.
   - **Evidence:** finding 1 got through because P0 confirms names, not exports.
   - **Fix:** add the four value types, `LabelStyle` and `letter_over`, and the check
     "every `pyntpot` name an example imports is in a public `__all__` on PR 1's tip".

6. **[CONSIDER]**
   - The presets figure writes its theme files into `out_dir`. Other example tests
     expect one file per call (`test_explanation_figures.py:63`), so use a
     `tempfile.TemporaryDirectory()`, as `how_to_route_ink.py` already does.
   - Hold each swept axis as one numeric tuple literal, so captions pass
     `test_captions.py:197-210`.
   - Flag this to PR 1, which PR 2 does not use: PR 1 plan:636-637 imports
     `EFFECT_RANGES` "from `pyntpot.ink`", but gate A does not export it.

### Sweep

No new test file is broken without an owner. Checked:
- every `with_route_ink` caller (`test_route_ink.py` composes unlettered;
  `test_style.py:346` holds, since the default `label_route_ink` is `#c22050`);
- every `pigment_transparency` and `cover.pigments` consumer in `src`, `tests`,
  `examples` and `docs` (all owned by B; `site_theme.py` reads `PIGMENTS`, not cover);
- the `docs_images` importers (exactly C's six, plus `test_gallery.py`, which imports
  only `IMAGES`);
- the theme enumerators (`test_one_source_of_defaults.py:35-83`, owned by D3);
- `test_explanation_figures.py` (an explicit `FIGURES` dict, so new scripts are not
  pulled in).

## Round 4 resolution

1. Fixed by PR 1's ruling, not the literal workaround: PR 1's primitives take `threshold` as a keyword defaulting to `LINE_THRESHOLD`, so no script passes it. No script imports `LINE_THRESHOLD` or `EFFECT_RANGES`; both stay unexported. No `THRESHOLD` literal and no `test_the_scripts_threshold_is_the_engines`. P0 confirms the default on PR 1's tip.
2. Fixed as asked (verified PR 1 plan:582-601): every call is written in full with its value type; `shadow` takes `azimuth_deg=315` and no `paper`; colours are `Colour("#ffffff")` or `pigment("paynes_grey").colour`; off cells use the type's default. A quoted signature lists every parameter in order, `threshold=LINE_THRESHOLD` included. No script calls the private `lay_stack`.
3. Fixed as asked (verified PR 1 plan:871-890, `tutorial_grids.py:77-83`): each script holds `LABELS = LabelStyle(px=21.0, ink=Colour("#4a3a2a"), pen_px=1.5, gran_px=12.0, seed=7, col_dy=12)`; per-cell text goes through `extra=`; D2 adds `sweep_grid` and owns `labelled_grid.py` for that alone.
4. Fixed as asked: `paint_cell` lays the wash in wash space, then the effect, then the stroke, then multiplies by the `paper_plate` crop, and returns that; the spec states the order.
5. Fixed as asked: P0 confirms the four value types, `LabelStyle`, `letter_over` and `tutorial_grids`' label values, and checks every imported `pyntpot` name is in one of the four public `__all__`s on PR 1's tip.
6. Applied: the presets figure writes its theme files in a `tempfile.TemporaryDirectory()`; each swept axis is one numeric tuple literal. The `EFFECT_RANGES` note to PR 1 is not carried: PR 1 imports it from the submodule inside `maps`, and no figure needs it.
