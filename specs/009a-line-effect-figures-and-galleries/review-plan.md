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
