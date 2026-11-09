# 009a: plan

Stacked on PR 1 (`specs/009-line-effects-and-registry`). The PR 1 names below are taken
from PR 1's revised `plan.md`; slice P0 checks each against that branch's tip, and where a
name differs, this plan is updated first. Gates as in CLAUDE.md:
`uv run pytest -n auto --dist loadgroup -m "not golden and not benchmark" --golden-tolerance`,
`ruff check .`, `ruff format --check .`, `ty check`, `lint-imports`,
`prek run --all-files`. Golden-marked tests run per slice only for the images that slice
adds, and in full once in slice G. The plan review and its resolution are in
`review-plan.md`.

## Approach

Four kinds of work, all on PR 1's model.

1. **#159, in `maps` only.** `Style.with_route_ink` also replaces `nib.label_route_ink`
   when a colour is fed (ADR 0070 rule 18). `letters/nib.py` and `KIND_INK` are not
   touched.
2. **D7, in `maps` and one `ink` field** (ADR 0070 rule 17).
   - `PaperStyle.pigment_transparency` goes.
   - `CoverStyle.pigments` becomes `dict[str, CoverPigment]`. A `CoverPigment` is a
     `NamedTuple` of `colour` (a `Colour`) and `transparency` (a float, or `None`).
   - The theme gives each entry as a ref (`#rrggbb`, a registry name or an alias) or as
     `{pigment: <ref>, transparency: <0 to 1>}`. A maps-side `BeforeValidator` resolves it
     at load against the theme's scope (`ThemeScope`, rules 2, 5 and 6).
   - **One transparency rule for every form** (rule 17): the entry's own; else the
     resolved pigment's own (a derived `{base: x}` pigment that sets none takes its
     base's); else the cover class's built-in pigment's, the registry role pigment of the
     same name. The forms, each with its result:

     | Entry | Transparency |
     | --- | --- |
     | `{pigment: <any ref>, transparency: t}` | `t` |
     | a pigment name, or a theme alias to one (its bound `Pigment`) | that pigment's |
     | a palette alias to a name (`palette: plain` with `water: blue`) | that pigment's (`ultramarine`'s) |
     | a theme pigment with a transparency | its own |
     | a theme pigment with none | the class's built-in |
     | a derived `{base: x}` pigment with none | `x`'s, by the same rule |
     | a bare `#rrggbb` | the class's built-in |
     | an alias to a hex, a `.gpl` palette alias included (a pigment-less `Pigment`, transparency `None`) | the class's built-in |
     | `{pigment: "#rrggbb"}` with no transparency | the class's built-in |
     | an `extends` child's bare hex over a parent's `{pigment, transparency}` | the class's built-in, not the parent's |
     | Python: `CoverPigment(colour, None)` | `paper.km_transparency`, applied by `PaintJob.transp` |
     | Python: a `str` or `Colour` value | the class's built-in |
     | Python: a key outside the 15 cover classes | `None`, so `paper.km_transparency` |

     Every cover class key (the 15 of `theme_vocab`'s `cover.pigments` vocabulary) is a
     role pigment with a float transparency, so a theme can never reach `None`. Only a
     `CoverPigment(colour, None)` built in Python, or a Python-built key outside the 15
     classes (`built_in_transparency` returns `None` for it), does.
   - **Where it is computed.** The value-level validator needs the dict key. PR 1's
     `TableCheck.leaf` passes `context={"scope": self.scope}`; for a leaf under
     `cover.pigments` it also passes `"cover_class": path[-1]`. The validator,
     `resolve_cover_pigment`, lives in the new `maps/theme_bindings.py` and reads both.
     It resolves a ref, a bare one or the table's `pigment`, by calling PR 1's
     `resolve_pigment(ref, scope) -> Pigment` (`theme_scope.py`), and never looks up
     `scope.aliases`, `scope.palette` or `scope.registry` itself. `resolve_pigment` owns
     the lookup order (`#` to the anonymous `pigment(ref)`, transparency `None`; then a
     theme alias, a palette alias and a registry name, an alias giving its bound
     `Pigment`) and the text of a miss, so a `.gpl` or bundled palette alias resolves as
     a theme alias does. P0 confirms `resolve_pigment` and these shapes on PR 1's tip.
   - **Python-built values.** `CoverStyle.__post_init__` rebuilds `pigments`: a
     `CoverPigment` keeps its transparency, with its colour through `Colour.parse`; a `str`
     or `Colour` becomes `CoverPigment(Colour.parse(v), <the class's built-in
     transparency>)`. `CoverPigment` carries a plain-dict pydantic hook, as `Colour` does
     (no pydantic import), accepting a `CoverPigment` (which `dataclasses.asdict` keeps),
     a `{pigment, transparency}` mapping, or a `str` passed on to `__post_init__`, so
     `Style.model_validate` from a dict keeps working. A list is refused.
   - **One written form.** Wherever a `CoverPigment` is written out for a reader or the
     loader, it is a ref string or the mapping `{pigment: "#rrggbb", transparency: t}`
     (`transparency` left out when `None`), never a list:
     - `tests/support/theme_dump.py` (the dumped form the merge property loads back);
     - the schema `default` (`theme_schema._json`);
     - the `cover.pigments` Default cells of `docs/reference/style-fields.md`, which
       `tests/docs/test_reference_values.py`'s `entry_value` checks;
     - the checker, which accepts exactly a ref or that mapping.
     Only the digest's internal JSON hashes it as a two-item list; that is no written
     form, and the hashes move in B regardless.
   - **Located errors for the table form.** `TableCheck.field` sends a `CoverPigment`
     hint whose value is a mapping through `mapping(value, path, ("pigment",
     "transparency"), ...)`, so each problem lands at its own key and line (`theme_read`
     records a line for every nested key):
     - an unknown inner key reads `unknown key; did you mean transparency?` (or
       `pigment`), by `TableCheck.unknown`'s nearest name, at
       `cover.pigments.<class>.<key>`;
     - the `pigment` value is checked at `cover.pigments.<class>.pigment`, its miss text
       `resolve_pigment`'s;
     - `transparency` is checked at `cover.pigments.<class>.transparency` as
       `Annotated[float, Field(strict=True, ge=0, le=1)]`, which refuses a `bool`, a
       `str` and a value outside 0 to 1 (an `int` such as `1` is accepted as `1.0`);
     - a table with no `pigment` is a problem at `cover.pigments.<class>`:
       `pigment is required`.
     `resolve_cover_pigment` then builds the leaf from the checked table, with the class
     from the context.
   - The painter never reads the registry. `PaintJob.transp(key)` reads
     `cover.pigments[key].transparency`, else `paper.km_transparency`.
   - **A leaf, as a `NamedTuple`.** `theme_checker._is_dataclass` would read a dataclass as
     a sub-table and `theme_merge` would merge it key by key; a child's entry must replace
     its parent's whole, or a hex rebinding would inherit a transparency the rule does not
     grant. A `NamedTuple` is a tuple: `dataclasses.asdict` keeps it, `merge` replaces it
     whole, and the digest hashes it as a two-item list.
3. **Figures and docs.**
   - New example scripts, each with `main(out_dir, **options) -> Path` and `figure=`,
     using public names plus PR 1's private `examples/labelled_grid.py` (#170).
   - One page per Diataxis mode for line effects.
   - Two reference galleries and four setting grids.
   - The three built-in effect presets are tuned in D1, against D2's sweeps and a
     scratch draft of the presets figure, before any image that names a preset is
     painted. The sweeps hold literal values and name no preset, so D2 paints first.
4. **One bundled theme adopts an effect**: `bold` takes `line_effects: {route: cased}`.
   - #104 is the route casing (`docs/features/maps-route-casing.md`). Until ADR 0046,
     bold's route ink declared `casing_px = 1.2`, a casing nothing read. The `cased`
     preset is that casing, so bold now shows what it always declared.
   - A route effect moves `digest()` only (rule 9): one compose, no repaint, no
     re-stroked nib plate. bold's base plates and lettering stay byte-identical, and the
     one moved image is the `map-styles/bold` card, which composes the route.
   - Rejected: casing bold's `road_major`. It repaints the base and moves `base_digest`,
     for a look no history declared.
   - Rejected for other themes:
     - `pen-and-ink`: a pen casing is a stylistic leap, better left to an author;
     - `sepia` and `winter`: the P7 critique already read the route's colour as glowing,
       so a glow there was weighed and declined (`maps-route-glow.md`).

Layers: `maps` (style, theme checker, schema, painter's transparency lookup, presets) and
one `ink` field. No boundary change. One new public name, `pyntpot.maps.CoverPigment`, is
required by ADR 0068 because `CoverStyle.pigments` names it. ADR 0070's "Public names"
does not list it, so the new ADR records it.

**New ADR**, numbered by P0 (expected 0071): "Golden regeneration: one route colour,
pigments that carry their transparency, and bold's cased route". It holds:
- the `CoverPigment` public name and its leaf rule;
- the `RENAMED_KEYS` row for `paper.pigment_transparency`, a recorded departure from ADR
  0069:323, under which a removed field fails as an unknown key: this field's value
  moved, so the error names where;
- the tuned preset values (D1);
- the Lynmouth compare log;
- the moved-image table below, with differing fractions;
- an index row in `docs/decisions/README.md`. ADR 0070 is unmerged, so its rule 17 is
  edited in place to the rule above; the new ADR's row does not claim to amend it.

## Moved pins and images (the PR body reuses this table)

A hash that moves with identical pixels counts as moved (ADR 0070 rule 16).

| Pin or image | Moves in | Pixels | Reason |
| --- | --- | --- | --- |
| `tests/unit/maps/test_style.py` `DIGEST` (`88b356ada294ff60`) | B | none | `paper` loses `pigment_transparency`; `cover.pigments` values become `CoverPigment`s |
| `tests/unit/maps/test_style.py` `BASE_DIGEST` (`d9c56c0811177b0f`) | B | none | same, both are base groups |
| `tests/unit/maps/test_style.py` `LETTERING_DIGEST` (`d15ae2f30e9ca5ce`) | does not move | none | `nib` unchanged at the default |
| New pin: `Style().with_route_ink(colour="#6a2c91").lettering_digest()` | A | n/a | rule 18; research measured `d4e48ea6fd28b786` before PR 1, re-measure |
| `tests/unit/maps/test_theme_named.py` `DIGESTS` for `pen-and-ink`, `sepia`, `winter` (digest and base) | B | none | D7 |
| `tests/unit/maps/test_theme_named.py` `DIGESTS["bold"]` digest | B, then F | F only, at compose | D7; then `line_effects: {route: cased}`, which moves `digest()` only |
| `tests/unit/maps/test_theme_named.py` `DIGESTS["bold"]` base digest | B only | none | D7; a route effect leaves `base_digest` alone |
| `tests/unit/maps/test_example_themes.py` `DIGESTS`, six themes (digest and base) | B | none | D7 |
| New pin: `DIGESTS["ambleside-cased"]`, and the name in `THEME_NAMES` | D3 | n/a | new example theme, pinned after D1's tuning |
| `tests/unit/maps/test_pipeline_fetch_paint.py` `GOLDEN_HASH` second half | B | none | base digest |
| `tests/golden/lynmouth/plates.json` `hash` | G | none | base digest; `paper`, `wash`, `pen`, `labels-centreline` and `map.png` byte-identical |
| `src/pyntpot/maps/themes/theme.schema.json`, `docs/reference/theme.schema.json` | B | n/a | `CoverPigment` schema; `pigment_transparency` gone |
| `docs/images/how-to/route-ink.webp`, `tests/golden/docs/how-to/route-ink.png` | G | yes | #159: "start" and "finish" from pink to violet; that is the fix |
| `docs/images/map-styles/bold.webp`, `tests/golden/docs/map-styles/bold.png` | G | yes | bold's route is cased with `cased`, laid at compose; its base plates and nib plate are byte-identical, so no name moves |
| `tests/golden/test_map_styles.py` `MEAN_RGB["bold"]` (212.9, 208.3, 182.8) | G | yes | same card; re-pinned to the measured mean |
| `docs/images/preview/bold.webp` and master, only if 008a is on the base | G | yes | same, if it composes bold's route |

Expected **not** to move:
- every other docs image: `how-to/route-ink-grid.webp` composes unlettered; the place
  cards, hero, social preview, the other three map-styles cards, the tutorials and
  command-line maps;
- every Lynmouth image;
- bold's base plates and nib plate;
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
| `painting-with-python/pen-casing-sweep.webp` | `line_effect_grids`, `pen-casing` | | 600 | lossless (pen) | `009a-line-effects` |
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

### Where each image is shown

CONTRIBUTING.md (images by page type) lets a reference page show only swatch sheets. The
galleries and the dryness sweep are swatch sheets: strokes and washes on paper, no map,
as `brush-sheet.webp` and `pigment-swatches.webp` already are. `docs/reference/line-effects.md`
shows no image. The pen casing sweep goes on the tutorial page, because pen casing has no
theme key (Out of scope) and so nothing for a theme how-to to say.

| Image | Page | Section |
| --- | --- | --- |
| the three `brush-gallery-*` | `docs/reference/brush-gallery.md` | one section per figure: "RIV, STR and LAN", "MAJ", "TRK" |
| `pigment-gallery-roles`, `-painters` | `docs/reference/pigment-gallery.md` | "Map pigments", "Painter's pigments" |
| `pigment-gallery-glazes` | same | "Glaze pairs" |
| `palettes` | same | "Palettes" |
| `line-effects` | `docs/how-to/case-light-or-shadow-a-line.md` | the result image, under the page's first paragraph |
| `casing-sweep` | same | "Case a line" |
| `glow-sweep` | same | "Lift a line with a glow" |
| `shadow-sweep` | same | "Cast a shadow" |
| `line-effects-presets` | same | "Use a preset" |
| `line-effects-glaze-or-rgb` | `docs/explanation/line-effects.md` | "Why a line effect is not a glaze" |
| `line-effects-draw-order` | same | "Casings first: the draw order" |
| `cased-stroke` | `docs/tutorials/painting-with-python/cased-strokes.md` | "Case, light and shadow one stroke" |
| `pen-casing-sweep` | same | "A pen casing" |
| `wash-pool-sweep` | `docs/explanation/how-the-wash-works.md` | "Edge darkening: pigment gathers where the water stopped" |
| `wash-granulation-sweep` | same | "Granulation: the pigment finds the paper" |
| `brush-dryness-sweep` | `docs/reference/brushes.md` | "Treatment rows" |
| `relief-strength` | `docs/how-to/write-a-theme.md` | new section "Strengthen or soften the relief" |

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
  - `RIV` and `STR` are one brush: both have the single column `#255d80`, and neither is
    a `brush_overrides` key (`ink/brush_style.py`). So `riv-str-lan` paints two columns,
    lettered "RIV = STR" and "LAN", 16 cells. Each "RIV = STR" cell is lettered with both
    ids (`RIV1-a = STR1-a`), and the page table lists all 24 ids, each with its cell, so
    the coverage test still finds every id.
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
- **Palettes.** One row per bundled palette (`Palette.names()`; PR 1 bundles `plain`,
  rule 7). Each alias is a 0.6 wash swatch, glazed at its pigment's transparency, lettered
  with the alias above and the pigment it names below, both read from PR 1's
  `Palette.pigments` (alias to `Pigment`). A hex alias, a pigment-less `Pigment`, is
  lettered with its hex below and glazed at `paper.km_transparency`.
- **Effect sweeps.** Each is a grid of one stroke over a wash that gives the effect
  something to separate. Every value is lettered with its unit.
  - **Units.** Each sweep is painted at scale 1, so one array pixel is one display pixel,
    and a cell lettered "2 px" shows what `width_px: 2` (or `spread_px`, `blur_px`,
    `offset_px`) does in a theme at scale 1. The caption says so.
  - **Cell painter.** Each script has `paint_cell(kind, **values) -> np.ndarray`, which
    returns the cell's float32 RGB `(h, w, 3)` before lettering and encoding, the
    primitives' own dtype (009 plan, "The four functions"); `paint_cell(None)` is the
    plain stroke, painted without calling any primitive: the wash plus the stroke, and for
    the pen casing sweep the grey tint plus the centre ink line. The tests below use it.
  - **Held values are script literals**, never read from `BUILT_IN_PRESETS`, so D1's
    tuning moves no sweep. Every sweep holds `threshold=LINE_THRESHOLD` and
    `paper=None`.
  - Casing: a `MAJ2-b` road at `width_display_px` 6 over a mixed farmland and wood wash,
    `strength` 1.0. Width 0, 1, 2, 3 and 5 px across, the 0 column painted through
    `casing(width_px=0)`; casing colour paper (`#ffffff` in wash space) and `paynes_grey`
    down.
  - Glow: an `RIV1-a` river at `width_display_px` 4 over a dark wood wash, `strength`
    0.8. A lettered "none" cell, painted through `glow(strength=0)`, then spread 0, 2, 4
    and 6 px across; blur 0, 3 and 6 px down.
  - Shadow: a solid `#c22050` line 4 px wide over farmland, `strength` 0.4, colour
    `paynes_grey`, `azimuth_deg` 315. A lettered "none" cell, painted through
    `shadow(strength=0)`, then offset 0, 1.5, 3 and 5 px across; blur 1 and 3 px down.
    Light from 315 degrees, north-west, so the shadow falls south-east, as the caption
    says.
  - Pen casing: one ink centre line 1.5 px wide over a grey tint (`paynes_grey` at
    wash strength 0.3). A lettered "none" cell, painted through `pen_casing(width_px=0)`,
    then gap (`width_px`) 1, 2, 3 and 4 px across; ink width (`edge_px`) 0.75 ("thin")
    and 1.5 ("thick") down. The cell composites the returned edge layer only when
    `edges.any()`, so the "none" cell never composites a zero-density layer.
  - The test asserts that each sweep's off cell (casing's 0 column; the "none" cell of
    the other three) equals `paint_cell(None)` byte for byte. Spread 0, offset 0 and the
    other values are real settings, not off: at spread 0 a glow still blurs, and at offset
    0 a shadow still spreads past the line.
- **Presets.** The Ambleside loop cropped as in `route-ink-grid`, four cells: none,
  `cased`, `halo` and `lifted`. One paint, then four composes, because route effects are
  compose-only (rule 9). D1 tunes the presets on a scratch draft of this figure, before
  D3 writes `how_to_line_effects.py`.
- **Explanation figures.** `glaze-or-rgb` is a 2 by 2 grid ("casing" and "glow" across,
  "glaze" and "RGB" down) over a dark wood wash: the glazed cream barely shows (rule 11).
  `draw-order` has two cells, "each stroke cased" (a seam at the junction) and "casings
  first" (one road), each with a road crossing a river.
- **Setting grids.** P0 confirms each field name below on PR 1's tip.

  | Figure | Across | Down | Held |
  | --- | --- | --- | --- |
  | `pool` | `wash(..., pool=)` 0, 0.1, 0.2 and 0.35 | `Sheet.seed` 11 and 29 | one `ultramarine` disc; `Sheet.gran_px` 60, as `wash-body` |
  | `granulation` | `Sheet.gran_px` 3, 6, 12 and 24 | `Sheet.fibre` 0 ("smooth") and 0.35 ("cold press", `PaperStyle.paper_fibre_mix`'s default) | the same disc, `pool` 0.2, seed 11 |
  | `dryness` | treatment `dry` 0.1, 0.4, 0.7 and 0.9 | treatment `load` 0.5 and 1.2 (the sheet's rows run from 0.4 to 1.6) | `MAJ2-c` at 12 px, every other treatment value row 2's, set in `BrushStyle.brush_overrides["major"]` and read by `brush_from_id("MAJ2-c", 12, 1.0, style, override="major")`; without `override=` it reads `brush_overrides["maj"]` (`ink/brush.py:199`) and the setting does nothing |
  | `relief` | `cover.relief_strength` 0.5, 1, 1.5 and 2 | one row | the Ambleside crop, default style otherwise, four small paints |

  `darkness` is not swept: it is a separate treatment value, and the spec's sweep is
  dryness by load.

## Files to touch

**A (#159)**
- `src/pyntpot/maps/style.py`: `with_route_ink` feeds `nib.label_route_ink`; docstring says
  a fed colour moves `lettering_digest`, a fed width does not.
- `tests/property/test_route_colour.py` (new): the Hypothesis property.
- `tests/unit/maps/test_route_colour_feed.py` (new): the structural walk over `Colour`
  fields, the bold override and the fed colour's digest pins.
- `tests/unit/maps/test_style.py:347-352`: `test_a_fed_ink_moves_only_the_full_digest`
  feeds `colour` and `width_px` and asserts `LETTERING_DIGEST` holds, which A breaks. It
  becomes `test_a_fed_width_moves_only_the_full_digest`, feeding `width_px=4.8` alone;
  the colour case lives in `test_route_colour_feed.py`. A edits only this test; B re-pins
  the file's constants.
- `tests/unit/maps/test_route_ink.py`: one new class, `@pytest.mark.golden` and in the
  `test_route_ink` xdist group like its siblings, using the module `painted` fixture.
- `tests/benchmarks/test_maps.py`: `test_letter_after_route_colour`.
- `docs/how-to/change-the-route-ink.md`, `GLOSSARY.md` (route ink row) and the glossary
  outputs regenerated by `PYTHONPATH=tests uv run python -m support.glossary`.
- `docs/issues/maps-route-ink-leaves-marker-labels-pink.md` (deleted).

**B (D7)**
- `src/pyntpot/ink/style.py`: drop `pigment_transparency` and its docstring lines.
- `src/pyntpot/maps/cover_pigment.py` (new, about 90 lines): `CoverPigment`, its pydantic
  hook, `built_in_transparency(cover_class)` and the default `pigments` builder from the
  registry's role pigments (rule 3). It imports no `maps.style` module, so
  `theme_bindings` may import it.
- `src/pyntpot/maps/style_groups.py`: `CoverStyle.pigments: dict[str, CoverPigment]`, its
  default from `cover_pigment`, and the `__post_init__` rebuild. PR 1 leaves it at about
  390 lines; the type lives in `cover_pigment.py` so this file grows by a few lines only.
  Past 400, `BasemapStyle` moves whole to `maps/style_basemap.py`, as PR 1's plan says.
- `src/pyntpot/maps/theme_bindings.py` (new, about 120 lines): `resolve_cover_pigment`.
- `src/pyntpot/maps/theme_checker.py`: `_adapter(CoverPigment)` returns
  `Annotated[CoverPigment, BeforeValidator(resolve_cover_pigment)]`; `TableCheck.leaf`
  adds `"cover_class": path[-1]` to the context under `cover.pigments`.
- `src/pyntpot/maps/theme_check.py`: one `RENAMED_KEYS` entry,
  `("paper", "pigment_transparency"): "cover.pigments.<class>.transparency"`, so a theme
  that sets it reads, at its line, `paper.pigment_transparency: renamed to
  cover.pigments.<class>.transparency`. The renamed-key mechanism exists already
  (`TableCheck.unknown`), so no new table is added. This departs from ADR 0069:323 (a
  removed field "fails as an unknown key with its nearest neighbour suggested"): this
  field's value moved, so the error names its new home, and the new ADR records the
  departure. `tests/unit/maps/test_theme_check.py:146`
  (`test_the_real_renamed_table_holds_the_route_ink_row`) pins `RENAMED_KEYS` exactly; B
  adds the new row to its literal and renames the test for what it then proves.
- `src/pyntpot/maps/__init__.py`: export `CoverPigment`; `docs/reference/maps.md`: its
  `::: pyntpot.maps.CoverPigment` directive (`tests/architecture/test_site.py`).
- `src/pyntpot/maps/painter/job.py` (`transp`) and the `.colour` reads at
  `painter/cover.py`, `water.py`, `wood.py`, `relief.py` and `plates.py`.
- `src/pyntpot/maps/theme_vocab.py`: drop the `pigment_transparency` vocabulary.
- `src/pyntpot/maps/theme_schema.py`: a `CoverPigment` leaf is `anyOf` the three-branch
  `Colour` node of rule 5 and an object `{pigment: <that node>, transparency: number}`,
  `additionalProperties: false`, `pigment` required.
- The theme files: `src/pyntpot/maps/themes/{bold,pen-and-ink,sepia,winter}.yaml` and
  `examples/themes/*.yaml`. Migration rule: a cover class a theme only rebinds by hex stays
  a bare hex, because it keeps its class's built-in transparency. A class whose
  transparency the theme set in `pigment_transparency` is written
  `{pigment: <its hex or ref>, transparency: <that value>}`.
- Both `theme.schema.json` copies, via `PYTHONPATH=tests uv run python -m support.theme_schema`.
- Pins: `tests/unit/maps/test_style.py`, `test_theme_named.py`, `test_example_themes.py`
  and `test_pipeline_fetch_paint.py`, plus every file P0's grep of PR 1's tip finds holding
  a 16-hex digest literal (among them `test_digest_omits.py`, whose "packaged and example
  themes keep their pins" check holds theme digests).
- Field lists and existing tests that read `cover.pigments` or `pigment_transparency`
  (edits only, no new tests there): `test_style_groups.py` (399 lines), `test_theme_vocab.py`,
  `test_theme_check.py` (361), `test_theme_schema.py`, `tests/unit/maps/test_theme_merge.py`,
  `tests/architecture/test_one_source_of_defaults.py`, `tests/unit/test_public_api.py`,
  PR 1's coercion guard (`replace(CoverStyle(), pigments={"built": "#ABCDEF"})` now gives a
  `CoverPigment` with `built`'s built-in transparency), and
  `tests/unit/maps/painter/test_smoke.py:246` (`rgb(...["wood"].colour)`).
- `tests/property/test_theme_merge.py`: the leaf walker treats a `CoverPigment` as one
  leaf and draws a bare `#rrggbb` for it; `_BASE` loses `paper.pigment_transparency`.
- `tests/support/theme_dump.py`: `_plain` writes a `CoverPigment` as
  `{"pigment": str(colour), "transparency": t}`, leaving `transparency` out when it is
  `None`, because a tuple written as a list would not load.
- New tests: `tests/unit/maps/test_cover_pigments.py` (the type, the default, Python-built
  values, `transp`) and `tests/unit/maps/test_theme_bindings.py` (every theme form, the
  `extends` child, the errors).
- Docs: `docs/reference/style-fields.md` (including the `label_route_ink` row's new
  sentence from A), `docs/reference/pigments.md`, `docs/how-to/write-a-theme.md` (the
  example at lines 52-53 becomes `CoverPigment(colour='#8f9f6a', transparency=0.05)`;
  "Table fields merge per entry" says a `cover.pigments` entry is replaced whole; the
  transparency rule and the `extends` case near line 247) and `GLOSSARY.md` (a "cover
  pigment" row, code `pyntpot.maps.CoverPigment`; regenerate the glossary outputs).

**C (galleries)**
- First, a pure move as its own commit: `DocsImage`, its `Kind` and `Encoding` aliases,
  `master_path`, `IMAGES_DIR`, `MASTERS_DIR` and `MASTER_WIDTH` go from
  `tests/support/docs_images.py` (565 lines) to `tests/support/docs_image.py`; every
  importer is repointed (`tests/golden/{repaint,make_docs_images,test_docs_images,test_repaint}.py`,
  `tests/docs/{test_captions,test_docs_images}.py`), with no re-export.
- `tests/support/docs_images_009a.py` (new): the three 009a blocks as `IMAGES_009A` and
  their shares as `SHARES_009A`, importing `support.docs_image`. `docs_images.py` grows by
  two lines: `**SHARES_009A` in `SLICE_SHARE_BYTES` and `IMAGES += IMAGES_009A`. C
  creates the module with its block; D and E append theirs.
- New scripts: `examples/brush_gallery.py`, `examples/pigment_gallery.py`.
- New pages: `docs/reference/brush-gallery.md`, `docs/reference/pigment-gallery.md`.
- Link lines in `docs/reference/{brushes,pigments,index}.md`; `mkdocs.yml` nav.
- `tests/examples/test_galleries.py` (new); `tests/docs/test_reference_pages.py` (238
  lines: id, pigment and palette coverage); `tests/docs/test_gallery_values.py` (new: the
  gallery tables; `test_reference_values.py` is at 338).
- The seven images and their masters.
- `docs/features/docs-brush-id-gallery.md` and `docs-pigment-gallery.md` (deleted).

**D (line effects), in four sub-slices**
- **D1, tune the presets** (after D2, before any image that names a preset is painted):
  `src/pyntpot/maps/line_effects.py` `BUILT_IN_PRESETS` only, and any PR 1 unit test that
  pins a preset's numbers. The integrator paints a draft of the presets figure (a scratch
  script, never committed; D3 writes the real one) and D2's casing, glow and shadow
  sweeps at each preset's values into a scratch directory, starting from the provisional
  values, then tunes until a
  `cased` casing reads on the 720 px card, `halo` lifts without a hard edge and `lifted`
  separates without a dark smear. The values are recorded in Decisions and the new ADR.
  No pin moves: no theme on PR 1's tip names a preset.
- **D2, the sweeps** (before D1): `examples/line_effect_grids.py`;
  `tests/examples/test_line_effect_figures.py`; the four sweep images.
- **D3, the how-to and reference:** `examples/how_to_line_effects.py`,
  `examples/themes/ambleside-cased.yaml`, `docs/how-to/case-light-or-shadow-a-line.md`,
  `docs/reference/line-effects.md`, `tests/examples/test_how_to_line_effects.py`,
  `tests/docs/test_line_effect_values.py` (new: presets, classes, draw order),
  `tests/unit/maps/test_example_themes.py` (`THEME_NAMES` and `DIGESTS`), the card and
  presets images.
  - `tests/property/test_line_effect_digests.py` (PR 1's): it sets `{}` or off effects on
    sampled classes in a child of a sampled theme and expects the sampled theme's
    digests. A child's `{}` replaces the parent's stack whole, so a class the theme sets
    (`ambleside-cased`'s `road_major` and `route`; bold's `route` after F) would fail it.
    Unless P0 found that PR 1's tip already does so, D3 restricts the strategy to the
    classes the sampled theme does not set. Any theme digest literal P0's grep found
    outside `test_example_themes.py` gains `ambleside-cased` here if it lists every
    example theme.
- **D4, the explanation and tutorial:** `examples/line_effect_reasons.py`,
  `examples/cased_stroke.py`, `docs/explanation/line-effects.md`,
  `docs/tutorials/painting-with-python/cased-strokes.md`, the three images, and
  `docs/features/maps-route-{casing,glow,shadow}.md` (deleted).
- Across D: `examples/labelled_grid.py` gains a `sweep_grid` only if PR 1 has no sweep
  loop, existing functions untouched; each sub-slice appends its entries to the
  `009a-line-effects` block of `docs_images_009a.py` and its lines to the index pages and
  `mkdocs.yml`.

**E (setting grids)**
- New scripts: `examples/setting_grids.py`, `examples/relief_grid.py`.
- Sections in `docs/explanation/how-the-wash-works.md` (pool, granulation),
  `docs/reference/brushes.md` (dryness) and `docs/how-to/write-a-theme.md` (relief, a new
  section "Strengthen or soften the relief").
- `tests/support/docs_images_009a.py`: the `009a-setting-grids` block and share.
- `tests/examples/test_setting_grids.py` (new).
- The four images and their masters.
- `docs/features/docs-variable-effect-grids.md` (deleted).

**F (bold cases its route)**
- `src/pyntpot/maps/themes/bold.yaml`: `line_effects: {route: cased}` and its header
  comment.
- `docs/how-to/write-a-theme.md` ("Bold" section); `test_theme_named.py`
  `DIGESTS["bold"]` digest (its base digest holds), and one test that bold's
  `route_ink.effects` is the `cased` stack and its basemap has no line effects.
- `tests/property/test_line_effect_digests.py`: no edit after D3's restriction; F runs it
  with bold's `route` set, and it draws no `route` for bold. Any bold digest literal P0's
  grep found in another file (`test_digest_omits.py` among them) is re-pinned here.

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
- The `ink` effect primitives (`ink/effect_*.py`) and the painter's `over` hook. Figures
  use them; changing them moves PR 1's properties. `BUILT_IN_PRESETS` changes in D1 only.
- `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY`. They are
  public names under rule 3; D7 retires only the `paper` copy.
- `wash.separation_pigments` and `wash.separation_transparency`: pigment separation keeps
  its own transparency (Out of scope).
- `src/pyntpot/maps/themes/{pen-and-ink,sepia,winter}.yaml` beyond the D7 migration.
- `docs/gallery.md` and `tests/docs/test_gallery.py`; the 008a preview card.
- The bodies of ADRs 0027, 0046 and 0069, which are history. ADR 0070 is unmerged: only
  its rule 17 is edited, in place.
- `MAX_DIFFERING_FRACTION`, `--golden-tolerance`, `KIND_BUDGET_BYTES` and existing shares.
- `CONTRIBUTING.md`'s docs trap (line 143), "Never call what the engine does a 'filter',
  an 'effect' or a 'shader'". The user is being asked whether it narrows; this PR does
  not edit `CONTRIBUTING.md` or `CLAUDE.md`, and its prose uses "line effect", "effect
  stack", "effect preset", "casing", "glow" and "shadow" only as the glossary terms they
  are.

## Test plan

| Criterion | Test |
| --- | --- |
| #159 property | `tests/property/test_route_colour.py::test_a_fed_route_colour_reaches_every_route_coloured_field` |
| #159 structural | `tests/unit/maps/test_route_colour_feed.py::test_every_colour_field_defaulting_to_the_route_colour_follows_a_fed_one` |
| #159 theme shade overridden | `test_route_colour_feed.py::test_a_fed_colour_overrides_a_themes_marker_shade` (bold, sepia, winter) |
| #159 digests | `test_route_colour_feed.py::test_a_fed_colour_moves_the_lettering_digest`; `tests/unit/maps/test_style.py::test_a_fed_width_moves_only_the_full_digest` (width-only since A) |
| #159 pixels | `tests/unit/maps/test_route_ink.py::TestFedColourLettersTheMarkers::test_the_start_label_is_lettered_in_the_fed_colour`: on the nib plate (`Lettering.plate_path`, RGBA) from `letter` after `with_route_ink(colour=VIOLET)`, the pixels with alpha at least 0.9 inside the box of the `Lettering.labels` entry named "start" of kind `marker` (scaled from display pixels to the plate's) have a mean RGB nearer `VIOLET` than `#c22050` by Euclidean distance; and the plate's bytes differ from the default's |
| #159 cost | `tests/benchmarks/test_maps.py::test_letter_after_route_colour` |
| D7 every form | `tests/unit/maps/test_theme_bindings.py::test_each_entry_form_resolves_its_transparency`, parametrised with `ids=` over the Approach table's theme rows: `entry-transparency`, `pigment-name`, `alias-to-name`, `theme-pigment-own`, `theme-pigment-none`, `derived-none`, `bare-hex`, `alias-to-hex`, `gpl-alias`, `pigment-table-hex-only` |
| D7 `extends` | `test_theme_bindings.py::test_an_extends_child_bare_hex_takes_the_built_in_not_its_parents` |
| D7 Python-built | `tests/unit/maps/test_cover_pigments.py`: `test_a_python_built_none_paints_at_km_transparency` (`PaintJob.transp`), `test_a_python_str_takes_the_classes_built_in_transparency`, `test_a_python_key_outside_the_cover_classes_takes_km_transparency`, `test_model_validate_from_a_dict_builds_cover_pigments`, `test_every_cover_class_is_a_role_pigment_with_a_transparency`, `test_the_default_bindings_are_the_registry_roles` |
| D7 merge | `tests/unit/maps/test_theme_merge.py::test_a_child_entry_replaces_its_parents_whole` |
| D7 errors | `test_theme_bindings.py`: `paper.pigment_transparency` reads "renamed to cover.pigments.<class>.transparency" at its line; `cover.pigments.wood.pigment: ultramarin` (nearest name); `transparency` outside 0 to 1; an unknown key in the table |
| D7 no pixel moves | `test_cover_pigments.py::test_every_theme_keeps_its_old_class_transparencies` (literal table per theme measured on PR 1's tip before migration); golden map-styles and docs images byte-identical in G |
| Digests | re-pinned literals in `test_style.py`, `test_theme_named.py`, `test_example_themes.py`, `test_pipeline_fetch_paint.py` |
| Schema | `tests/unit/maps/test_theme_schema.py` (committed copies current; every theme file within it) |
| Presets tuned | D1's gate: PR 1's `tests/property/test_line_effect_presets.py`, `test_line_effect_digests.py`, `test_line_effects.py`, `tests/unit/maps/test_line_effects.py` and `test_digest_omits.py` pass with the tuned values |
| Themes that set an effect | `tests/property/test_line_effect_digests.py`, drawing only the classes the sampled theme does not set, green after D3 and after F |
| Galleries | `tests/examples/test_galleries.py` (each figure at `size=`); `tests/docs/test_reference_pages.py::test_the_brush_gallery_paints_every_id`, `::test_the_pigment_gallery_paints_every_registry_pigment`, `::test_the_palettes_figure_shows_every_bundled_palette`; `tests/docs/test_gallery_values.py::test_the_pigment_gallery_table_matches_the_registry`, `::test_the_brush_gallery_table_lists_every_id` |
| Effect figures | `tests/examples/test_line_effect_figures.py`: each figure runs; `test_each_sweeps_off_cell_is_the_plain_stroke` (parametrised `ids=["casing", "glow", "shadow", "pen-casing"]`, float32 `paint_cell` arrays, dtype and shape asserted, compared by `tobytes()`); `test_no_glow_cell_is_darker_than_the_plain_stroke`; `cased_stroke` runs. `tests/examples/test_how_to_line_effects.py` with the Ambleside fixture |
| Effect reference | `tests/docs/test_line_effect_values.py::test_the_line_effects_page_matches_the_presets_and_classes` |
| bold | `test_theme_named.py::test_bold_cases_its_route_and_nothing_else` |
| Setting grids | `tests/examples/test_setting_grids.py` (each figure; relief with the fixture) |
| Docs images | `tests/docs/test_docs_images.py` (registry equals files and masters, slices known, every shown image registered, kind budget, slice share and total) |
| Pins | `tests/golden/test_docs_images.py` (each new master; moved ones re-pinned in G); `tests/golden/test_map_styles.py`; `tests/golden/test_parity.py` |
| Examples | `tests/architecture/test_examples.py` (public imports, plus PR 1's allowance for the sibling helper) |
| Pages | `tests/docs/test_captions.py`, `test_nav.py`, `test_docs_links.py`, `test_tutorial_quotes.py`, `test_docs_signatures.py`, `test_retired_words.py`, `test_glossary.py`, `test_site_pages.py` |

**Mutation testing.**
- #159 changes no `letters` function. `nib._ink_colour` is untouched, and
  `letters/style.py` changes at most a docstring.
- D7 removes a class field in `ink/style.py`, which `scope.py` does not count.
- D1 changes data in `maps`.
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
`maps` functions changed (`with_route_ink`, `PaintJob.transp`, `resolve_cover_pigment`,
`CoverStyle.__post_init__`) are covered by the focused tests above, each asserting the
exact value, not only "changed".

## Delegation

- **Main context**: P0, D1's tuning (a judgment on painted figures), integration, seam
  checks after each track, the full gates, slice G's regeneration (judgment on the
  pinning machine), the new ADR and the PR body.
- **plan-slice-implementer agents**, one per track or sub-slice, serial.
  - Opus for B: the checker leaf, the context key, merge, schema and migration are subtle.
  - Sonnet at high effort for A, C, D2, D3, D4, E and F: each is one or two scripts and
    one or two pages.
  - Each gets this plan, the ADR rules it implements, and its owned files.
- **Fresh-context reviews.**
  - An Opus plan-reviewer before any code; it blocks.
  - An Opus diff review against this plan after G.
  - A Sonnet elegance pass.
  - Docs pages get one `ai-jargon-audit` and dash search.
- **Integrator's job after each track**:
  - the full non-golden gate;
  - `make_docs_images.py` for that track's new names only;
  - a repaint of the existing images the track could reach, compared with the working
    tree: `PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/<track>" <names> --no-lynmouth`, then
    read `diffs/summary.json`:
    - after A, names `how-to/route-ink.webp how-to/route-ink-grid.webp`: `changed` is
      `route-ink` and its master only (the fix, committed in G);
    - after B, every registry name that reads a fixture except `how-to/route-ink.webp`
      (whose fix A moved): `gallery/route-map.webp tutorials/route-map.webp
      map-styles/{pen-and-ink,sepia,bold,winter}.webp hero.webp social-preview.jpg
      places/{ambleside,oxford,skye,y-fenni,yr-wyddfa}.webp how-to/route-ink-grid.webp
      how-to/command-line.webp` (15 names, from `DocsImage.fixture` on the base; add any
      fixture-reading name PR 1 or 008a registered): nothing changed;
    - after F, the same names: `changed` is `map-styles/bold` and its master only (plus
      `preview/bold` and its master if 008a is on the base);
  - and after B, a byte compare of every theme's base plates on the Ambleside fixture
    against P0's record.

## File-ownership partition

Dispatch order: **P0 -> A -> B -> C -> D2 -> D1 -> D3 -> D4 -> E -> F -> G**, serial, so
no worktrees are needed.
- A precedes B: B owns `style-fields.md` and the `test_style.py` pins, and writes A's
  `label_route_ink` row. A edits one `test_style.py` test (the fed width); B then re-pins
  the file's constants.
- B precedes F: both edit `bold.yaml`.
- D2 precedes D1: D1 tunes against D2's sweep script, whose held values are literals
  that name no preset, so D2's committed sweeps do not move when D1 tunes. D1 drafts the
  presets figure in scratch.
- D1 precedes D3, D4 and F, so every image and pin that names a preset is made with the
  tuned values. C's images name no preset, so C painting first is unaffected.
- C creates `tests/support/docs_images_009a.py`; D2 to D4 and E append their own
  commented blocks to it, and their own lines to `mkdocs.yml` and the index pages (the
  registry's keep-both-blocks rule).
- Within a track, a file named in "Files to touch" under that track is owned by it
  alone; a file listed under two tracks is touched by each in dispatch order, each only
  as its list says, the later on the earlier one's result.

## Decisions

- **Binding shape (rule 17).** A ref or `{pigment, transparency}`, resolved at load to a
  leaf `CoverPigment(colour, transparency)`, a `NamedTuple`. The painter stays
  registry-free, and a pigment's retune repaints every theme naming it (rule 5).
- **Orchestrator ruling: transparency precedence (ADR 0070 rule 17, edited in place).**
  The entry's own, else the resolved pigment's own (a derived pigment's base's), else the
  cover class's built-in pigment's; `paper.km_transparency` only for a Python-built
  `None`. Reason: a bare hex in a third-party theme must not silently change look, and
  every form needs one answer. The approved D7 named `km_transparency` as the last step;
  no theme can reach it, because every cover class has a built-in transparency, so it
  stays as the Python-built case only. The class key reaches the validator through
  validation context, beside PR 1's `scope`.
- **Migration keeps pixels.**
  - A bare hex takes its class's built-in transparency, so a theme that only rebinds a
    hex keeps its look with no explicit transparency.
  - Only a class whose transparency the theme set in `pigment_transparency` is written
    with it, and D7 moves hashes only.
  - The changelog's breaking line and the theme how-to still warn third-party authors that
    `paper.pigment_transparency` is gone, and that an `extends` child's bare hex no longer
    keeps the parent's transparency for that class.
- **The moved key uses `RENAMED_KEYS`.** The review asked for a retired-key table in a new
  module, but `theme_check.RENAMED_KEYS` and `TableCheck.unknown` already locate an old
  path and name its new one. One entry gives the error the spec asks for, with no second
  mechanism.
- **`docs_images.py` stops growing.** It is already at 565 lines, so the 009a blocks go in
  their own module and the registry type moves out first. Splitting the rest of the
  registry is out of scope; P0 files it.
- **Orchestrator adjustment: compose_steps docstring.** The `compose_steps.route`
  docstring change belongs to 009, which wires route effects into `compose_steps.route`
  (its S5b). It is not in this plan, the spec or the tasks.
- **Orchestrator adjustment: size.** Past the usual review size; kept as one PR because
  the user fixed a two-PR split; tracks are separately committed and each track's images
  are listed so review can go track by track.
- **Orchestrator ruling: bold adopts `route: cased`; no other theme adopts an effect**
  (Approach 4). It realises the route casing bold declared until ADR 0046 and #104 names,
  it moves `digest()` only, and one card moves.
- **Orchestrator ruling: presets are tuned in D1**, before any image that names one is
  painted, and PR 1's property and unit tests on effects and presets pass after tuning.
  The provisional values (`cased` width 1.2; `halo` spread 1.0, blur 2.5, strength 0.8;
  `lifted` offset 1.2, blur 1.5, strength 0.35) are the starting point; D1 records the
  tuned ones here and in the new ADR. bold takes whatever `cased` becomes.
- **New images are added in their slice; moved ones in G.** The registration test needs
  the files. "Regenerate once" governs what moves.
- **Brush ids as a script literal**, pinned by a docs test, because `BRUSH_COLOURS` is
  private and no new public name is wanted.
- **The `effect` trap** is in `CONTRIBUTING.md` (line 143). The user is being asked; no
  file is edited for it here.
- **PR title**: `feat(maps)!: pigments carry their own transparency, a fed route colour
  letters the markers, and line effects are shown`.
