# 009a: plan

Stacked on PR 1 (`specs/009-line-effects-and-registry`). Slice P0 checks every PR 1 name
below against that branch's tip; where a name differs, this plan is updated first. Gates as
in CLAUDE.md: `uv run pytest -n auto --dist loadgroup -m "not golden and not benchmark"
--golden-tolerance`, `ruff check .`, `ruff format --check .`, `ty check`, `lint-imports`,
`prek run --all-files`. Golden-marked tests run per slice only for the images that slice
adds, and in full once in slice G.

## Approach

Four kinds of work, all on PR 1's model.

1. **#159, in `maps` only.** `Style.with_route_ink` also replaces `nib.label_route_ink`
   when a colour is fed (ADR 0070 rule 18). `letters/nib.py` and `KIND_INK` are not
   touched.
2. **D7, in `maps` and one `ink` field** (rule 17).
   - `PaperStyle.pigment_transparency` goes.
   - `CoverStyle.pigments` becomes `dict[str, CoverPigment]`. A `CoverPigment` is a
     resolved binding of a colour (a `Colour`) and a transparency (a float or `None`).
   - The theme gives each entry as a ref (`#rrggbb`, a registry name or an alias) or as
     `{pigment: <ref>, transparency: <float>}`. A maps-side `BeforeValidator` resolves it
     at load against the theme's extended registry (rules 2, 5 and 6).
   - The transparency is the entry's own, else the named pigment's own, else, for a bare
     `#rrggbb`, the transparency of the built-in pigment the role bound by default. Only
     when none of these gives one is it `None`, which means `km_transparency`, which
     `PaintJob.transp` applies. (ADR 0070 rule 17 refinement: see Decisions.)
   - The painter never reads the registry.
   - `CoverPigment` must be a **leaf** value (a `NamedTuple` or a frozen non-dataclass
     with a pydantic schema), not a dataclass, for rule 4's reason:
     - the checker reads a dataclass as a sub-table, and `theme_merge` would merge it key
       by key;
     - a child theme's binding must replace its parent's whole, or a hex rebinding would
       inherit a transparency the precedence rule does not grant.
   - The digest hashes the two values.
3. **Figures and docs.**
   - New example scripts, each with `main(out_dir, **options) -> Path` and `figure=`,
     using public names plus PR 1's private `examples/labelled_grid.py` (#170).
   - One page per Diataxis mode for line effects.
   - Two reference galleries and four setting grids.
4. **One bundled theme adopts an effect**: `bold` takes `line_effects: {road_major: cased}`.
   - Bold's saturated washes (`built` `#f0b86a`, `heath` `#e8a43c`, `farmland` `#f2e04a`)
     sit under brown `MAJ2-b` roads with little contrast, the case #104 names.
   - A cream casing is what every prior-art style does there.
   - One theme and one class bound the moved images to one map-styles card. The default
     look moves nowhere.
   - Rejected for other themes:
     - `pen-and-ink`: a pen casing is a stylistic leap, better left to an author;
     - `sepia` and `winter`: the P7 critique already read the route's colour as glowing,
       so a glow there was weighed and declined (`maps-route-glow.md`).

Layers: `maps` (style, theme checker, schema, painter's transparency lookup) and one `ink`
field. No boundary change. One new public name, `pyntpot.maps.CoverPigment`, is required
by ADR 0068 because `CoverStyle.pigments` names it. ADR 0070's "Public names" does not
list it, so the new ADR records it.

**New ADR**, numbered by P0 (expected 0071): "Golden regeneration: one route colour,
pigments that carry their transparency, and bold's cased roads". It holds:
- the `CoverPigment` public name and its leaf rule;
- the Lynmouth compare log;
- the moved-image table below, with differing fractions;
- an index row in `docs/decisions/README.md`.

## Moved pins and images (the PR body reuses this table)

A hash that moves with identical pixels counts as moved (ADR 0070 rule 16).

| Pin or image | Moves in | Pixels | Reason |
| --- | --- | --- | --- |
| `tests/unit/maps/test_style.py` `DIGEST` (`88b356ada294ff60`) | B | none | `paper` loses `pigment_transparency`; `cover.pigments` values become bindings |
| `tests/unit/maps/test_style.py` `BASE_DIGEST` (`d9c56c0811177b0f`) | B | none | same, both are base groups |
| `tests/unit/maps/test_style.py` `LETTERING_DIGEST` (`d15ae2f30e9ca5ce`) | does not move | none | `nib` unchanged at the default |
| New pin: `Style().with_route_ink(colour="#6a2c91").lettering_digest()` | A | n/a | rule 18; research measured `d4e48ea6fd28b786` before PR 1, re-measure |
| `tests/unit/maps/test_theme_named.py` `DIGESTS` for `pen-and-ink`, `sepia`, `winter` (digest and base) | B | none | D7 |
| `tests/unit/maps/test_theme_named.py` `DIGESTS["bold"]` (digest and base) | B, then F | F only | D7; then the `road_major` casing |
| `tests/unit/maps/test_example_themes.py` `DIGESTS`, six themes (digest and base) | B | none | D7 |
| New pin: `DIGESTS["ambleside-cased"]` | D | n/a | new example theme |
| `tests/unit/maps/test_pipeline_fetch_paint.py` `GOLDEN_HASH` second half | B | none | base digest |
| `tests/golden/lynmouth/plates.json` `hash` | G | none | base digest; `paper`, `wash`, `pen`, `labels-centreline` and `map.png` byte-identical |
| `src/pyntpot/maps/themes/theme.schema.json`, `docs/reference/theme.schema.json` | B | n/a | binding schema; `pigment_transparency` gone |
| `docs/images/how-to/route-ink.webp`, `tests/golden/docs/how-to/route-ink.png` | G | yes | #159: "start"/"finish" from pink (192, 52, 89) to violet (116, 63, 145); that is the fix |
| `docs/images/map-styles/bold.webp`, `tests/golden/docs/map-styles/bold.png` | G | yes | bold cases `road_major`; names may shift where the casing changes the darkness grid placement reads |
| `tests/golden/test_map_styles.py` `MEAN_RGB["bold"]` (212.9, 208.3, 182.8) | G | yes | same |
| `docs/images/preview/bold.webp` and master, only if 008a is on the base | G | yes | same |

Expected **not** to move:
- every other docs image: `how-to/route-ink-grid.webp` composes unlettered; the place
  cards, hero, social preview, the other three map-styles cards, the tutorials and
  command-line maps;
- every Lynmouth image;
- `PINNED_LABELS`, the place pins and the smoke lock.

Any other moved image is a defect: stop and find the slice that moved it.

### Images added (20, not moved)

| Image | Script, figure | Fixture | Width | Encoding | Slice |
| --- | --- | --- | --- | --- | --- |
| `reference/brush-gallery-riv-str-lan.webp` | `brush_gallery`, `riv-str-lan` | | 720 | lossy | `009a-galleries` |
| `reference/brush-gallery-maj.webp` | `brush_gallery`, `maj` | | 720 | lossy | `009a-galleries` |
| `reference/brush-gallery-trk.webp` | `brush_gallery`, `trk` | | 720 | lossy | `009a-galleries` |
| `reference/pigment-gallery-roles.webp` | `pigment_gallery`, `roles` | | 720 | lossy | `009a-galleries` |
| `reference/pigment-gallery-painters.webp` | `pigment_gallery`, `painters` | | 720 | lossy | `009a-galleries` |
| `reference/pigment-gallery-glazes.webp` | `pigment_gallery`, `glazes` | | 720 | lossy | `009a-galleries` |
| `reference/palettes.webp` | `pigment_gallery`, `palettes` | | 720 | lossy | `009a-galleries` |
| `how-to/line-effects.webp` | `how_to_line_effects`, `card` | `ambleside` | 720 | lossy | `009a-line-effects` |
| `how-to/line-effects-presets.webp` | `how_to_line_effects`, `presets` | `ambleside` | 720 | lossy | `009a-line-effects` |
| `how-to/casing-sweep.webp` | `line_effect_grids`, `casing` | | 720 | lossy | `009a-line-effects` |
| `how-to/glow-sweep.webp` | `line_effect_grids`, `glow` | | 720 | lossy | `009a-line-effects` |
| `how-to/shadow-sweep.webp` | `line_effect_grids`, `shadow` | | 720 | lossy | `009a-line-effects` |
| `how-to/pen-casing-sweep.webp` | `line_effect_grids`, `pen-casing` | | 600 | lossless (pen) | `009a-line-effects` |
| `explanation/line-effects-glaze-or-rgb.webp` | `line_effect_reasons`, `glaze-or-rgb` | | 720 | lossy | `009a-line-effects` |
| `explanation/line-effects-draw-order.webp` | `line_effect_reasons`, `draw-order` | | 720 | lossy | `009a-line-effects` |
| `painting-with-python/cased-stroke.webp` | `cased_stroke` | | 600 | lossy | `009a-line-effects` |
| `explanation/wash-pool-sweep.webp` | `setting_grids`, `pool` | | 720 | lossy | `009a-setting-grids` |
| `explanation/wash-granulation-sweep.webp` | `setting_grids`, `granulation` | | 720 | lossy | `009a-setting-grids` |
| `reference/brush-dryness-sweep.webp` | `setting_grids`, `dryness` | | 720 | lossy | `009a-setting-grids` |
| `how-to/relief-strength.webp` | `relief_grid` | `ambleside` | 720 | lossy | `009a-setting-grids` |

Each added image has a master in `tests/golden/docs/`. An added image is not a
regeneration, because no pinned value changes. Each figure slice therefore paints and
commits its own new images, so `tests/docs/test_docs_images.py` (files equal registry)
stays green per slice. Slice G repaints everything once and finds them byte-identical.

### Budgets

All sizes are decimal bytes.

- **Today.** `TOTAL_BUDGET_BYTES` is 7,000,000. Used: 3,482,207 B over 71 entries.
  P7.V12b is at 821,660 of 1,000,000, so this PR adds nothing to it.
- **New shares** in `SLICE_SHARE_BYTES`:
  - `009a-galleries`: 500,000, for 7 lossy figures, estimated 280,000;
  - `009a-line-effects`: 600,000, for 9 figures, estimated 430,000, of which the
    lossless pen casing sweep is about 140,000;
  - `009a-setting-grids`: 250,000, for 4 figures, estimated 120,000.
- **Kind budgets.** Each file stays within `page`, 250,000.
- **Projected total** about 4,310,000 B, so about 2,690,000 B stay spare.
- **Fallback.** A figure over its share goes lossy if it is a wash, else to a smaller
  width (the registry's rule). A share is never raised to fit.

## What each figure shows (a reference a painter would want)

All figures follow the same conventions:
- painted on `paper_plate` paper (never white);
- labels lettered in the default hand through `labelled_grid.label_grid`;
- each value lettered at its row or column, and repeated as real text on the page;
- seeds fixed and named in the caption.

- **Brush gallery.** Per figure, rows are treatments 1 to 8 lettered with their number
  and kind ("1 wet", "2 soft", "3 gritty", "4 dry", "5 nib", "6 pen", "7 driest",
  "8 light nib"). Columns are colour columns, lettered `a` to `f`, with the ink's hex in
  the page table. Each cell holds an S-stroke at 4 px above one at 12 px, because dryness
  reads only when big, and its id is lettered beneath (for example `TRK4-c`). Strokes of
  one ink are combined before one composite, as `brush_sheet._sheet` does. Nib rows take
  the same `brush_from_id` path. The ids come from a literal `PREFIX_COLUMNS` in the
  script, because the brush tables are private. A docs test pins it to `BRUSH_COLOURS` by
  `BRUSH_TREATMENTS`.
- **Pigment gallery `roles` and `painters`.** One row per pigment, in registry order. The
  canonical name is lettered at the left (`burnt_sienna`, as typed in a theme). Four
  columns:
  - washes at 0.3, 0.6 and 0.9, glazed by Kubelka-Munk at the pigment's own
    transparency;
  - "over ink": a 0.9 strip across a narrow grey-brown bar (the pigment card's device),
    so a staining pigment shows the bar and a covering one veils it.
  The right margin letters the transparency (`0.06`) and the Colour Index code (`PB29`).
  The code is left blank where the registry records none (rule 1). The page table holds
  name, hex, transparency, Colour Index code and row.
- **Pigment gallery `glazes`.** Six columns, each a pair lettered on two lines:
  - `ultramarine` and `burnt_sienna`;
  - `cerulean` and `yellow_ochre`;
  - `quinacridone_rose` and `ultramarine`;
  - `indigo` and `raw_sienna`;
  - `perylene_maroon` and `sap_green`;
  - `paynes_grey` and `yellow_ochre`.
  Three rows: "multiply", "A over B" and "B over A", each two overlapping discs, so the
  overlap shows the mix and the two glaze rows show that order matters. The pair painter
  is the script's own. `wash_stages._glaze_grid` is not lifted.
- **Palettes.** One row per bundled palette (named by PR 1, rule 7). Each alias is a 0.6
  wash swatch, lettered with the alias above and the pigment it names below.
- **Effect sweeps.** Each is a grid of one stroke over a wash that gives the effect
  something to separate. Every value is lettered with its unit.
  - Casing: a `MAJ2-b` road over a mixed farmland and wood wash. Width 0, 1, 2, 3 and
    5 px across; casing colour paper and `paynes_grey` down.
  - Glow: an `RIV1-a` river over a dark wood wash. Spread 0, 2, 4 and 6 px across; blur
    0, 3 and 6 px down.
  - Shadow: a solid `#c22050` line over farmland. Offset 0, 1.5, 3 and 5 px across; blur
    1 and 3 px down. Light from 315 degrees, north-west, so the shadow falls south-east,
    as the caption says.
  - Pen casing: two ink lines over a grey tint. Gap 1, 2, 3 and 4 px across; ink width
    thin and thick down.
  The zero cell of each sweep is painted with no effect. The example test asserts that
  it equals the plain stroke.
- **Presets.** The Ambleside loop cropped as in `route-ink-grid`, four cells: none,
  `cased`, `halo` and `lifted`. One paint, then four composes, because route effects are
  compose-only (rule 9).
- **Explanation figures.** `glaze-or-rgb` is a 2 by 2 grid ("casing" and "glow" across,
  "glaze" and "RGB" down) over a dark wood wash: the glazed cream barely shows (rule 11).
  `draw-order` has two cells, "each stroke cased" (a seam at the junction) and "casings
  first" (one road), each with a road crossing a river.
- **Setting grids.**
  - `pool`: wash `pool` 0, 0.1, 0.2 and 0.35, over two sheet seeds.
  - `granulation`: four granulation sizes, smooth and cold-press paper.
  - `dryness`: `dry` 0.1, 0.4, 0.7 and 0.9 across, darkness (load) low and high down.
  - `relief`: `relief_strength` 0.5, 1, 1.5 and 2 on the Ambleside crop, four small
    paints.
  P0 confirms the parameter names in `WashOptions`, `BRUSH_OVERRIDE_KEYS` and
  `CoverStyle`.

## Files to touch

**A (#159)**
- `src/pyntpot/maps/style.py`: `with_route_ink` feeds `nib.label_route_ink`; docstring says
  a fed colour moves `lettering_digest`, a fed width does not.
- `tests/property/test_route_colour.py` (new): the Hypothesis property.
- `tests/unit/maps/test_route_colour_feed.py` (new): the structural walk over `Colour`
  fields, the bold override and the digest pins.
- `tests/unit/maps/test_route_ink.py`: the pixel test, using its module `painted` fixture.
- `tests/benchmarks/test_maps.py`: `test_letter_after_route_colour`.
- `docs/how-to/change-the-route-ink.md`, `GLOSSARY.md` (route ink row) and the glossary
  outputs regenerated by `PYTHONPATH=tests uv run python -m support.glossary`.
- `docs/issues/maps-route-ink-leaves-marker-labels-pink.md` (deleted).

**B (D7)**
- `src/pyntpot/ink/style.py`: drop `pigment_transparency` and its docstring lines.
- `src/pyntpot/maps/style_groups.py`: `CoverPigment` and the new `CoverStyle.pigments`
  default, built from the registry's roles (rule 3).
- `src/pyntpot/maps/__init__.py`: export `CoverPigment`.
- `src/pyntpot/maps/painter/job.py` (`transp`) and the `.colour` reads at
  `painter/cover.py`, `water.py`, `wood.py`, `relief.py` and `plates.py`.
- `src/pyntpot/maps/theme_vocab.py`: drop the `pigment_transparency` vocabulary.
- `src/pyntpot/maps/theme_check.py`: the moved-key message and the binding as a leaf.
- `src/pyntpot/maps/theme_schema.py`: the binding is `anyOf` the ref schema of rule 5 and
  an object.
- The theme files: `src/pyntpot/maps/themes/{bold,pen-and-ink,sepia,winter}.yaml` and
  `examples/themes/*.yaml`. Migration rule: a role a theme only rebinds by hex stays a bare
  hex, because it keeps its role's default transparency. A role whose transparency the
  theme set in `pigment_transparency` is written
  `{pigment: <its hex or ref>, transparency: <that value>}`.
- Both `theme.schema.json` copies, via `PYTHONPATH=tests uv run python -m support.theme_schema`.
- Pins: `tests/unit/maps/test_style.py`, `test_theme_named.py`, `test_example_themes.py`
  and `test_pipeline_fetch_paint.py`.
- Field lists and checker tests: `test_style_groups.py`, `test_theme_vocab.py`,
  `test_theme_check.py`, `test_theme_schema.py`, `test_theme_merge.py`,
  `tests/architecture/test_one_source_of_defaults.py` and `tests/unit/test_public_api.py`.
- `tests/unit/maps/test_cover_pigments.py` (new).
- Docs: `docs/reference/style-fields.md` (including the `label_route_ink` row's new
  sentence from A), `docs/reference/pigments.md` and `docs/how-to/write-a-theme.md`
  (around line 247).

**C (galleries)**
- New scripts: `examples/brush_gallery.py`, `examples/pigment_gallery.py`.
- New pages: `docs/reference/brush-gallery.md`, `docs/reference/pigment-gallery.md`.
- Link lines in `docs/reference/{brushes,pigments,index}.md`; `mkdocs.yml` nav.
- `tests/support/docs_images.py`: the `009a-galleries` block and share.
- `tests/examples/test_galleries.py` (new); `tests/docs/test_reference_pages.py` (id,
  pigment and palette coverage); `tests/docs/test_reference_values.py` (the gallery
  table).
- The seven images and their masters.
- `docs/features/docs-brush-id-gallery.md` and `docs-pigment-gallery.md` (deleted).

**D (line effects)**
- New scripts: `examples/line_effect_grids.py`, `examples/line_effect_reasons.py`,
  `examples/how_to_line_effects.py`, `examples/cased_stroke.py`.
- `examples/themes/ambleside-cased.yaml`.
- `examples/labelled_grid.py`: add a `sweep_grid` only if PR 1 has no sweep loop;
  existing functions untouched.
- New pages: `docs/how-to/case-light-or-shadow-a-line.md`,
  `docs/reference/line-effects.md`, `docs/explanation/line-effects.md`,
  `docs/tutorials/painting-with-python/cased-strokes.md`.
- Their index pages and `mkdocs.yml` nav.
- `tests/support/docs_images.py`: the `009a-line-effects` block and share.
- `tests/examples/test_line_effect_figures.py`, `tests/examples/test_how_to_line_effects.py`
  (both new); `tests/docs/test_reference_values.py` (presets, classes, draw order);
  `tests/unit/maps/test_example_themes.py` (new `DIGESTS` entry).
- The nine images and their masters.
- `docs/features/maps-route-{casing,glow,shadow}.md` (deleted).

**E (setting grids)**
- New scripts: `examples/setting_grids.py`, `examples/relief_grid.py`.
- Sections in `docs/explanation/how-the-wash-works.md` (pool, granulation),
  `docs/reference/brushes.md` (dryness) and `docs/how-to/write-a-theme.md` (relief, under
  "What a theme can say").
- `tests/support/docs_images.py`: the `009a-setting-grids` block and share.
- `tests/examples/test_setting_grids.py` (new).
- The four images and their masters.
- `docs/features/docs-variable-effect-grids.md` (deleted).

**F (bold adopts a casing)**
- `src/pyntpot/maps/themes/bold.yaml`: `line_effects: {road_major: cased}` and its header
  comment.
- `docs/how-to/write-a-theme.md` ("Bold" section); `test_theme_named.py`
  `DIGESTS["bold"]`.

**G (closing)**
- Links in `docs/features/maps-bridges-over-water.md:45`,
  `ink-stroke-density-profile.md:31`, `ink-blank-paper-by-size.md:44` and
  `docs-examples-housekeeping.md:46`.
- Delete any of `ink-one-pigment-registry.md`, `ink-data-driven-brushes-and-pigments.md`
  and `docs-labelled-grid-helper.md` that PR 1 left.
- The new ADR and its `docs/decisions/README.md` row.
- `tests/golden/test_map_styles.py` (bold mean), `tests/golden/lynmouth/plates.json`, the
  moved images and their masters.

## Files to leave alone

- `src/pyntpot/letters/nib.py` and `src/pyntpot/maps/lettering_marks.py`. They are
  tempting places to recolour the markers, but rule 18 fixes this in the style;
  `_ink_colour` and `KIND_INK` stay, and so does the nib's refusal of halos (rule 14).
- `examples/tutorial_grids.py`, `nib_stages.py`, `brush_sheet.py`, `wash_stages.py`, and
  the grid code of `how_to_route_ink.py`. PR 1 proved these five grids pixel-identical;
  lifting `_glaze_grid` or `BRUSH_IDS` would re-open that proof. Galleries carry their
  own painters and literals.
- `examples/labelled_grid.py`'s existing functions: add only.
- The `ink` effect primitives, presets and the painter's `over` hook. Figures use them;
  retuning moves PR 1's properties.
- `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY`. They are
  public names under rule 3; D7 retires only the `paper` copy.
- `src/pyntpot/maps/themes/{pen-and-ink,sepia,winter}.yaml` beyond the D7 migration.
- `docs/gallery.md` and `tests/docs/test_gallery.py`; the 008a preview card.
- The bodies of ADRs 0027, 0046, 0069 and 0070. The index already records 0070's
  amendments, and ADRs are history.
- `MAX_DIFFERING_FRACTION`, `--golden-tolerance`, `KIND_BUDGET_BYTES` and existing shares.
- `CLAUDE.md`'s docs trap "never call what the engine does an effect". It conflicts with
  the glossary's "line effect"; changing it needs the maintainer (see Decisions).

## Test plan

| Criterion | Test |
| --- | --- |
| #159 property | `tests/property/test_route_colour.py::test_a_fed_route_colour_reaches_every_route_coloured_field` |
| #159 structural | `tests/unit/maps/test_route_colour_feed.py::test_every_colour_field_defaulting_to_the_route_colour_follows_a_fed_one` |
| #159 theme shade overridden | `test_route_colour_feed.py::test_a_fed_colour_overrides_a_themes_marker_shade` (bold, sepia, winter) |
| #159 digests | `test_route_colour_feed.py::test_a_fed_colour_moves_the_lettering_digest`, `::test_a_fed_width_alone_moves_only_the_full_digest` |
| #159 pixels | `tests/unit/maps/test_route_ink.py::TestFedColourLettersTheMarkers::test_the_start_label_is_lettered_in_the_fed_colour` (mean within 12 of `#6a2c91`; nib plate bytes differ from default's) |
| #159 cost | `tests/benchmarks/test_maps.py::test_letter_after_route_colour` |
| D7 precedence | `tests/unit/maps/test_cover_pigments.py`: `test_a_role_entry_transparency_wins`, `test_a_named_pigment_brings_its_own_transparency`, `test_a_bare_hex_keeps_its_roles_default_transparency`, `test_a_hex_with_none_takes_km_transparency`, `test_an_alias_resolves_like_its_pigment`, `test_the_default_bindings_are_the_registry_roles` |
| D7 merge | `tests/unit/maps/test_theme_merge.py::test_a_child_binding_replaces_its_parents_whole` |
| D7 errors | `tests/unit/maps/test_theme_check.py`: moved key `paper.pigment_transparency`; `cover.pigments.wood.pigment: ultramarin` (nearest name); transparency out of 0 to 1 |
| D7 no pixel moves | `tests/unit/maps/test_cover_pigments.py::test_every_theme_keeps_its_old_role_transparencies` (literal table per theme measured on PR 1's tip before migration); golden map-styles and docs images byte-identical in G |
| Digests | re-pinned literals in `test_style.py`, `test_theme_named.py`, `test_example_themes.py`, `test_pipeline_fetch_paint.py` |
| Schema | `tests/unit/maps/test_theme_schema.py` (committed copies current; every theme file within it) |
| Galleries | `tests/examples/test_galleries.py` (each figure at `size=`); `tests/docs/test_reference_pages.py::test_the_brush_gallery_paints_every_id`, `::test_the_pigment_gallery_paints_every_registry_pigment`, `::test_the_palettes_figure_shows_every_bundled_palette`; `tests/docs/test_reference_values.py::test_the_pigment_gallery_table_matches_the_registry` |
| Effect figures | `tests/examples/test_line_effect_figures.py`: each figure runs; `test_each_sweeps_zero_cell_is_the_plain_stroke`; `test_no_glow_cell_is_darker_than_the_plain_stroke`; `cased_stroke` runs. `tests/examples/test_how_to_line_effects.py` with the Ambleside fixture |
| Effect reference | `tests/docs/test_reference_values.py::test_the_line_effects_page_matches_the_presets_and_classes` |
| Setting grids | `tests/examples/test_setting_grids.py` (each figure; relief with the fixture) |
| Docs images | `tests/docs/test_docs_images.py` (registry equals files and masters, slices known, every shown image registered, kind budget, slice share and total) |
| Pins | `tests/golden/test_docs_images.py` (each new master; moved ones re-pinned in G); `tests/golden/test_map_styles.py`; `tests/golden/test_parity.py` |
| Examples | `tests/architecture/test_examples.py` (public imports, plus PR 1's allowance for the sibling helper) |
| Pages | `tests/docs/test_captions.py`, `test_nav.py`, `test_docs_links.py`, `test_tutorial_quotes.py`, `test_docs_signatures.py`, `test_retired_words.py`, `test_glossary.py`, `test_site_pages.py` |

**Mutation testing.**
- #159 changes no `letters` function. `nib._ink_colour` is untouched, and
  `letters/style.py` changes at most a docstring.
- D7 removes a class field in `ink/style.py`, which `scope.py` does not count.
- `maps` is outside `[tool.mutmut] only_mutate`. So the changed-mode list is expected to
  be empty, and the PR says so. Any `ink` or `letters` function a slice does change is
  run:

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/claude/quirky-hypatia-z2pii3 --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

Each survivor is killed by a focused test or listed as equivalent, with the reason. The
`maps` functions changed (`with_route_ink`, `PaintJob.transp`, the binding validator) are
covered by the focused tests above, each asserting the exact value, not only "changed".

## Delegation

- **Main context**: P0, integration, seam checks after each track, the full gates, slice
  G's regeneration (judgment on the pinning machine), the new ADR and the PR body.
- **plan-slice-implementer agents**, one per track, serial.
  - Opus for B: the checker leaf, merge, schema and migration are subtle.
  - Sonnet at high effort for A, C, D, E and F: well-specified scripts and pages.
  - Each gets this plan, the ADR rules it implements, and its owned files.
- **Fresh-context reviews.**
  - An Opus plan-reviewer before any code; it blocks.
  - An Opus diff review against this plan after G.
  - A Sonnet elegance pass.
  - Docs pages get one `ai-jargon-audit` and dash search.
- **Integrator's job after each track**:
  - the full non-golden gate;
  - `make_docs_images.py` for that track's new names only;
  - `diff_images.py --ref` to confirm nothing but the track's own images moved;
  - and after B, a byte compare of every theme's base plates on the Ambleside fixture
    against PR 1's tip.

## File-ownership partition

Dispatch order: **P0 -> A -> B -> C -> D -> E -> F -> G**, serial, so no worktrees are
needed.
- A precedes B: B owns `style-fields.md` and the `test_style.py` pins, and writes A's
  `label_route_ink` row.
- B precedes F: both edit `bold.yaml`.
- C, D and E each append their own commented block to `tests/support/docs_images.py`
  and their own lines to `mkdocs.yml` and the index pages (the registry's
  keep-both-blocks rule).
- Within a track, a file named in "Files to touch" under that track is owned by it
  alone; a file listed under two tracks is touched only by the later one, on the earlier
  one's result.

## Decisions

- **Binding shape (rule 17).** A ref or `{pigment, transparency}`, resolved at load to a
  leaf `CoverPigment(colour, transparency)`. The painter stays registry-free, and a
  pigment's retune repaints every theme naming it (rule 5).
- **Migration keeps pixels.**
  - A bare hex has no transparency of its own, but the precedence refinement (below) gives
    it the transparency of the built-in pigment its role bound by default, so a theme that
    only rebinds a hex keeps its look with no explicit transparency.
  - Only a role whose transparency the theme set in `pigment_transparency` is written
    with it, and D7 moves hashes only.
  - The changelog's breaking line and the theme how-to still warn third-party authors that
    `paper.pigment_transparency` is gone.
- **Orchestrator adjustment: transparency precedence (ADR 0070 rule 17 refinement).** A
  role entry's own transparency, else the named pigment's own, else, for a bare
  `#rrggbb`, the transparency of the built-in pigment the role bound by default, else
  `paper.km_transparency`. Reason: a bare hex in a third-party theme must not silently
  change look. Applied to the spec criterion, Approach item 2, the migration rule, the
  test names (`test_a_bare_hex_keeps_its_roles_default_transparency` added) and the
  "Migration keeps pixels" entry. The new ADR records the refinement.
- **Orchestrator adjustment: compose_steps docstring.** The `compose_steps.route`
  docstring change belongs to 009, which wires route effects into `compose_steps.route`
  (its S5b). It is removed from this plan, the spec and the tasks.
- **Orchestrator adjustment: size.** Size: past the usual review size; kept as one PR
  because the user fixed a two-PR split; tracks are separately committed and each track's
  images are listed so review can go track by track.
- **Bold adopts `cased` on `road_major`; no other theme adopts an effect** (Approach 4).
- **New images are added in their slice; moved ones in G.** The registration test needs
  the files. "Regenerate once" governs what moves.
- **Brush ids as a script literal**, pinned by a docs test, because `BRUSH_COLOURS` is
  private and no new public name is wanted.
- **The `effect` trap in CLAUDE.md** is flagged to the maintainer, not edited. The pages
  use "line effect", "casing", "glow" and "shadow" only as glossary terms.
- **PR title**: `feat(maps)!: pigments carry their own transparency, a fed route colour
  letters the markers, and line effects are shown`.
