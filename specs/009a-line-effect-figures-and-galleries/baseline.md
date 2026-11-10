# 009a: P0 baseline

Recorded on PR 1's tip, `7c142c12` (PR #211), branch `claude/quirky-hypatia-z2pii3-stacked`,
no feature code. Data files beside this one: `baseline-base-plates.json` and
`baseline-class-table.json` (the literals below, as JSON).

## Names, signatures and publicness

All confirmed by importing PR 1's tip. "public" is membership of the package's `__all__`.

| Name | Import path | Public | Confirmed |
| --- | --- | --- | --- |
| `Colour`, `Pigment`, `pigment`, `PigmentRegistry`, `PIGMENT_REGISTRY` | `pyntpot.ink` | yes | `PigmentRegistry.extended(added: tuple[Pigment, ...]) -> PigmentRegistry`, `.get`, `.names()`, `.pigments`; 25 pigments (15 roles, then 10 tubes) |
| `colour_index` | field of `Pigment` (`name, colour, transparency, colour_index`) | via `Pigment` | not a function; `str` or `None` |
| `casing`, `glow`, `shadow`, `pen_casing` | `pyntpot.ink` | yes | below |
| `Casing`, `Glow`, `Shadow`, `PenCasing` | `pyntpot.ink` | yes | below |
| `EffectStack` | `pyntpot.maps` | yes | `EffectStack(*, effects: tuple[Casing \| Glow \| Shadow, ...] = ())`; drops off effects, refuses two of a kind |
| `BUILT_IN_PRESETS`, `LINE_CLASSES`, `WATER_GROUP`, `ROAD_GROUP` | `pyntpot.maps.line_effects` | no | `cased`, `halo`, `lifted`; provisional values as the plan: `Casing(width_px=1.2)`, `Glow(spread_px=1.0, blur_px=2.5, strength=0.8)`, `Shadow(offset_px=1.2, blur_px=1.5, strength=0.35)` |
| `Palette` | `pyntpot.maps` | yes | `Palette.names()` -> `('plain',)`; `Palette.named(name) -> Palette` exists (raises outside `names()`); `Palette.pigments: Mapping[str, Pigment]` (alias to `Pigment`); `Palette.from_file`, `.to_gpl` |
| `ThemeScope`, `Bound`, `resolve_pigment`, `resolve_colour` | `pyntpot.maps.theme_scope` | no | `ThemeScope(pigments, palette, aliases, presets)`; `aliases: Mapping[str, Bound[Pigment]]`; `resolve_pigment(text: str, scope: ThemeScope) -> Pigment`; the lookup is `#` hex, theme alias, palette alias, registry name |
| `TableCheck`, its `leaf` | `pyntpot.maps.theme_checker` | no | `leaf(hint, value, path)` validates with `context={"scope": self.scope}` only; B adds `cover_class` |
| `Style.basemap.line_effects` | `BasemapStyle.line_effects` (default `{}`) | via `Style` | |
| `Style.route_ink.effects` | `RouteInkStyle.effects` (default `EffectStack()`) | via `Style` | |
| the `Colour` field walker | `tests/unit/maps/test_colour_fields.py::_colour_paths` | no (test) | |
| `LINE_THRESHOLD`, `EFFECT_RANGES` | `pyntpot.ink.effect_mask`, `pyntpot.ink.effect_types` | **no**, and imported by no script under `examples/` | |

The four primitives, from `inspect.signature`, each with `threshold` a keyword-only
parameter defaulting to `LINE_THRESHOLD` (0.3):

```
casing(rgb, mask, effect: Casing, *, threshold=0.3, paper=None) -> np.ndarray
glow(rgb, mask, effect: Glow, *, threshold=0.3, paper=None) -> np.ndarray
shadow(rgb, mask, effect: Shadow, *, azimuth_deg, threshold=0.3) -> np.ndarray   # no paper
pen_casing(rgb, mask, effect: PenCasing, *, threshold=0.3, paper=None) -> tuple[np.ndarray, np.ndarray]
```

Value types (all `frozen`, `kw_only` dataclasses; numbers 0 to 16 for `*_px`, 0 to 1 for
`strength`):

| Type | Fields (defaults) |
| --- | --- |
| `Casing` | `width_px=0.0`, `colour=Colour("#ffffff")`, `strength=1.0` |
| `Glow` | `spread_px=0.0`, `blur_px=0.0`, `strength=0.0` |
| `Shadow` | `offset_px=0.0`, `blur_px=0.0`, `strength=0.0`, `colour=pigment("paynes_grey").colour` |
| `PenCasing` | `width_px=0.0`, `edge_px=0.0` |

Exports used by the 009a scripts and found public: `Sheet`, `Canvas`, `PaperStyle`,
`BrushStyle`, `wash`, `WashOptions`, `composite`, `paper_plate`, `brush_from_id`, `stamp`,
`PigmentLayer`, `TRANSPARENCY`, `PIGMENTS`, `PAINTERS_PIGMENTS`, `PAINTERS_TRANSPARENCY`
(`pyntpot.ink`); `Style`, `Palette`, `EffectStack`, `CoverStyle`, `BasemapStyle`,
`RouteInkStyle`, `Track`, `Cache`, `fetch`, `paint`, `letter`, `compose` (`pyntpot.maps`);
`Setting`, `Mark`, `HandStyle`, `FaceStyle`, `NibStyle`, `Hand`, `NibSurface`
(`pyntpot.letters`). **Not public, so no script imports them:** `BRUSH_OVERRIDE_KEYS`,
`brush_ids`, `BUILT_IN_PRESETS`, `LINE_THRESHOLD`, `EFFECT_RANGES`, `ThemeScope`,
`resolve_pigment`, `CoverPigment` (new in B). No missing name blocks 009a.

### `examples/labelled_grid.py`

- `GridSpec(width, cols, rows, cell_h, left, top, gap=14, pad_right=14, pad_bottom=14,
  unit=1.0, trailing_gap=False)`, frozen; `cell_w`, `height`, `boxes()`.
- `LabelStyle(px, ink, pen_px, gran_px, seed, col_dy=14, row_dx=12, row_dy=7)`, frozen.
- `letter_over(img, settings, nib, *, gran_px, seed, ground=None)`.
- `label_grid(img, boxes, columns, rows, style, *, extra=())`.
- `sweep_grid` **does not exist**; D2 adds it.
- `tutorial_grids.LABELS = LabelStyle(px=21.0, ink=Colour("#4a3a2a"), pen_px=1.5,
  gran_px=12.0, seed=7, col_dy=12)` (`GRAN_PX 6.0 * NIB_SCALE 2`): the plan's literals match.

## Parameter names for the setting grids

All present: `wash(cover, sheet, base, pool, options=None)` (so `pool` is the fourth
positional parameter and `WashOptions` the fifth); `Sheet(h, w, gran_px, seed, ...)` with
`fibre`; `PaperStyle.paper_fibre_mix` (default 0.35); `BRUSH_OVERRIDE_KEYS` holds `dry` and
`load` (and `darkness`, `pool`, `gap`, `bleed`, `lift`, `solid`, `thr`, `texture`, `press`,
`bristles`, `jitter_px`, `press_cell_px`, `wobble_px`); `brush_from_id(brush_id,
width_display_px, scale, style, override=None)` reads `style.brush_overrides[override or
prefix.lower()]`; `CoverStyle.relief_strength` (default 1.0).

## Checks answered

- **Derived `{base: x}` pigment**: `theme_pigments._derive` takes `base.transparency` when the
  item sets none (`transparency if "transparency" in item else base.transparency`). B's
  resolver does not follow `base` itself.
- **`ThemeScope.aliases` and `Palette.pigments`**: present as the plan needs. A hex alias is
  `pigment("#...")`, transparency `None` (`test_theme_palette.py:92`).
- **`tests/property/test_line_effect_digests.py`** does **not** restrict its strategy: it draws
  any subset of all eight `LINE_CLASSES` for every sampled theme. D3 restricts it.
- **Route and basemap effects are wired**: `compose_steps.route` calls `_effects` /
  `route_effects.lay` for `ink.effects`; the basemap's stacks are laid by
  `maps/painter/effects.py::lay_wash` (called from `painter/plates.py`), not an "`over` list".
- **008a preview images are not on the base** (`docs/images/preview/` does not exist), so
  `preview/bold` never moves in this PR.
- **Registry notes PR 1 deleted**: `ink-one-pigment-registry.md` (#72),
  `ink-data-driven-brushes-and-pigments.md` (#71) and `docs-labelled-grid-helper.md`
  (#170's). None is left in `docs/features/`, so G has nothing to delete. The notes 009a
  deletes still exist: `docs-brush-id-gallery`, `docs-pigment-gallery`,
  `docs-variable-effect-grids`, `maps-route-{casing,glow,shadow}` and
  `docs/issues/maps-route-ink-leaves-marker-labels-pink.md`.
- **Next free ADR number: 0071** (`docs/decisions/` ends at `0070-line-effects-and-one-pigment-registry.md`).
- **Goldens reproduce on this machine.** `PYTHONPATH=tests uv run python
  tests/golden/repaint.py "$SCRATCH/p0"` on the tip: `summary.json` has `files: []`
  (nothing changed, added or removed; "0 images differ"); the Lynmouth compare logged
  `paper`, `wash`, `pen`, `labels-centreline` and `map.png` "identical yes, differing fraction
  0.000000" and `manifest hash: 90193bbb26f681bf-d9c56c0811177b0f` here and in the committed
  directory. This is the pinning machine's result: C may paint masters.
- **`docs_images.py` is 565 lines** and no open issue names it (searched the open issues,
  REST); `docs/issues/tests-docs-images-over-budget.md` and its issue are still to file
  (outside P0's owned files).
- **Issue comments (#159, #69, #70, #67, #104, #105, #106) not posted** (a remote write
  outside P0's owned files), nor the plan-reviewer dispatched.

## 16-hex pins of style data (B re-pins)

From `git grep -nwE '[0-9a-f]{16}' -- 'tests/*.py'`, style-data pins only.

| File | Pin | Moves in B |
| --- | --- | --- |
| `tests/unit/maps/test_style.py:56-58` | `DIGEST` `88b356ada294ff60`, `BASE_DIGEST` `d9c56c0811177b0f`, `LETTERING_DIGEST` `d15ae2f30e9ca5ce` | first two; lettering holds |
| `tests/unit/maps/test_digest_omits.py:14` | `DEFAULT_DIGESTS` the same three (the default style only; **no theme digest**) | first two |
| `tests/unit/maps/test_style_groups.py:256-267` | `SOURCED` for 12 groups: `PaperStyle` `0af5f9f84facb9e9`, `WashStyle` `42edd0f93fa39dea`, `BrushStyle` `0187926c89a1b075`, `FaceStyle` `760ec6039a286528`, `HandStyle` `b25b34674433d32c`, `NibStyle` `76aa066043386bcf`, `CardStyle` `5e73ba4b178084f2`, `RibbonStyle` `6c8fdf4184013394`, `CoverStyle` `8ff38fcbad0d7a6f`, `RouteStyle` `e7af799eb721f445`, `LetteringStyle` `252f33e095df0b01`, `RouteInkStyle` `6a536a78d3ad069a` | `PaperStyle`, `CoverStyle` |
| `tests/unit/maps/test_theme_named.py:21-24` | `DIGESTS`: bold, pen-and-ink, sepia, winter, each (digest, base, lettering) | digest and base |
| `tests/unit/maps/test_example_themes.py:22-27` | `DIGESTS`: ambleside-hero, ambleside, oxford, skye, y-fenni, yr-wyddfa, each (digest, base, lettering) | digest and base |
| `tests/unit/maps/test_pipeline_fetch_paint.py:30` | `GOLDEN_HASH` `90193bbb26f681bf-d9c56c0811177b0f` | second half |

Not style data, left alone: `tests/support/paths.py` and `test_cache*.py` cache keys,
`CLASSIC_PLATE_SHA` (`test_paper.py:48`), `test_plates.py` and `support/manifests.py`
placeholders, float literals and hypothesis alphabets.

## Tests reading the fields B changes (B owns every hit)

From `git grep -n "pigment_transparency\|cover\.pigments\|\.pigments\[\|\.pigments\b" -- tests`:

- `tests/unit/maps/test_registry_defaults.py:27-51` (both `CoverStyle().pigments` and
  `PaperStyle().pigment_transparency`, and the `("paper", "pigment_transparency")` row);
- `tests/unit/maps/test_theme_colour_names.py:20-38` (`cover.pigments.built`);
- `tests/unit/maps/test_colour_fields.py:119` (the coercion guard, `TestCoercion`);
- `tests/unit/maps/painter/test_effects.py:120` (`rgb(job.style.cover.pigments["rim"])`);
- `tests/architecture/test_one_source_of_defaults.py:235-238` (the `wood` entry written into a
  theme); `:174` counts ten themes;
- `tests/unit/maps/test_style_groups.py:51` (field list naming `pigment_transparency`);
- `tests/unit/maps/test_theme_vocab.py:92,99`; `tests/unit/maps/test_theme_merge.py:30-31`;
  `tests/unit/maps/test_theme_check.py:117-122,199`; `tests/unit/maps/test_theme_schema.py:387`;
- `tests/unit/maps/painter/test_smoke.py:246` reads through `read(style, "pigments")["wood"]`
  and passes to `rgb(...)`: B decides whether it needs `.colour`;
- not B's: `tests/architecture/test_one_registry.py:29`, `tests/unit/ink/test_pigment_registry.py`,
  `tests/unit/maps/test_theme_palette.py`, `tests/unit/maps/test_theme_pigments.py:70`,
  `tests/unit/maps/test_theme_scope.py:34` and `tests/property/test_palette_gpl.py:32` read
  the registry's or a palette's `.pigments`.

## Changes made to the 009a plan and tasks

Plan:
1. Intro: P0 ran against `7c142c12`; findings in this file.
2. Palettes figure: reaches pigments as `Palette.named(name).pigments` (it exists).
3. Primitive signatures: a page that quotes one quotes it in full, `threshold` and `paper`
   included; `pen_casing`'s return type stated.
4. Glow test: checks glow's output before the stroke goes on, or finished cells within `1e-6`.
5. "The painter's `over` hook" -> `maps/painter/effects.py` (`lay_wash`); PR 1 has no `over`
   list.
6. B's digest pins: `test_digest_omits.py` holds `DEFAULT_DIGESTS` only (not theme digests);
   the six files P0 found are named; a moved-pins row added for `DEFAULT_DIGESTS`.
7. B's tests: coercion guard path (`test_colour_fields.py:119`), `painter/test_effects.py:120`
   and `test_one_source_of_defaults.py:235` added.
8. D3: the property test is restricted unconditionally (P0 found it is not).
9. Track C: the over-ink bar decision (metric, test, threshold, fallback), the old card's
   retirement from `reference/pigments.md` (new "retired" table, "where shown" row, files
   list, test row) and a Decisions entry.

Tasks: P0 items ticked with outcomes; painter wording; `Palette.named`; `colour_index` and
`extended`; C red and green items for the bar test and the pigments page; D2 glow test; D3
and D4 full-signature items; D3 restriction unconditional.

## Over-ink bar measurement (for C)

Method: 120 by 60 sheet, `paper_plate` with `paper_foxing=0`, a 10 px bar across the middle,
a 40 px strip at density 0.9 laid by `composite` with `km_glazing=True` at each registry
pigment's own transparency; veil ratio = mean Rec. 709 luma of the bar rows under the strip
over the mean luma of the strip rows beside it.

| Bar | `water` (0.04) | `perylene_maroon` (0.04) | `paynes_grey` (0.10) | `yellow_ochre` (0.24) | `works` (0.28) | `relief` (0.30) | spread (`relief` less `water`) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `#6a625a` (old card) | 0.411 | 0.420 | 0.444 | 0.512 | 0.529 | 0.541 | 0.130 |
| `#141210` | 0.107 | 0.107 | 0.157 | 0.283 | 0.323 | 0.340 | 0.233 |

Threshold 0.20. The ratio rises with transparency in both; only the dark bar clears it.

### Base plates on the Ambleside fixture

Bytes are the size and the first 16 hex digits of the sha256 of each plate file `paint()` wrote (the manifest's `files`; two separate runs gave identical output), from `baseline-base-plates.json`. `hash` is the manifest hash (`<key>-<base_digest>`).

| theme | manifest hash | paper | pen | wash |
| --- | --- | --- | --- | --- |
| `default` | `02bbeba32ac10197-d9c56c0811177b0f` | 1244848 `ed80583b0ae3d4a7` | 26782 `93160e64c6d9bb60` | 765738 `ec53d1987bdef9eb` |
| `bold` | `02bbeba32ac10197-6d77f74215314006` | 1244618 `a7f28b1d2407c65d` | 26782 `c238c2e48e18cb64` | 822862 `dd36730852180823` |
| `pen-and-ink` | `02bbeba32ac10197-0d40a30d74c111e0` | 1242176 `5c2b76058cecc63d` | 26782 `93160e64c6d9bb60` | 623848 `b42502e1f0bc67a6` |
| `sepia` | `02bbeba32ac10197-3a2f5fbbd424e347` | 1301566 `0476d1ef8e18e4b8` | 26782 `93160e64c6d9bb60` | 757744 `d33eaa6b19b782b2` |
| `winter` | `02bbeba32ac10197-c1b7c47d4ea12d6c` | 1273466 `afdc843e4895d51b` | 26782 `93160e64c6d9bb60` | 740378 `0f41a841377e56d2` |
| `ambleside-hero` | `e2c1b30e408e9487-149792857eb4656a` | 1243676 `978a142f22453fa3` | 51746 `f29d08e4ad109154` | 1451096 `b0477613af454a58` |
| `ambleside` | `37285639f9693219-1fbd4375dceec789` | 1244848 `ed80583b0ae3d4a7` | 51078 `5dde5e751c93ff26` | 1540812 `22148f15a0565d85` |
| `oxford` | `00cb7d3fcba64501-0f73e166ba6ba263` | 1244848 `ed80583b0ae3d4a7` | 51156 `5ae950b0c19f4d96` | 1526706 `ed8638c7656af7c8` |
| `skye` | `dd81d715ab26c169-b54086dfe786d1f0` | 1244848 `ed80583b0ae3d4a7` | 46682 `f291b4bd90a12565` | 1739084 `c0da5851ad0182ff` |
| `y-fenni` | `baaa5aad95bbe719-90c968b5e78d7058` | 1083670 `ccae82da530413f3` | 64870 `f2e816c6b4488e7f` | 1300866 `58e12b002c5170d4` |
| `yr-wyddfa` | `777f5af240e3e0ae-58c70051932a610f` | 1284016 `29cc4ef190d90999` | 47828 `358a0f5b5744ba68` | 1796114 `83a1be79eaac70cf` |

### Per-class (colour, transparency), every theme

`cover.pigments` colour and the transparency `PaintJob.transp` reads today: `paper.pigment_transparency[class]`, else `paper.km_transparency` (0.06 in every theme; no theme's table has a key outside the 15 classes). From `baseline-class-table.json`.

**default**

```
farmland  #dfe0b0  0.1
meadow    #cfdfae  0.09
orchard   #d5dda2  0.09
scrub     #c9d5a4  0.08
heath     #e0cda2  0.14
sand      #ecdfbe  0.16
rock      #dcd6c6  0.22
wetland   #bfd2cd  0.08
built     #ddd3c3  0.26
works     #d2cbc0  0.28
wood      #a8c286  0.05
pale      #d5e0b4  0.12
water     #9ec4de  0.04
relief    #c9bda4  0.3
rim       #c2ad91  0.18
```

**bold**

```
farmland  #f2e04a  0.06
meadow    #8fe05a  0.05
orchard   #a8e068  0.05
scrub     #7ccf5a  0.05
heath     #e8a43c  0.08
sand      #ffd86a  0.1
rock      #d6c9b0  0.15
wetland   #5fcfb0  0.05
built     #f0b86a  0.2
works     #e9a26a  0.2
wood      #1f9a4a  0.03
pale      #b9dc72  0.07
water     #37a6e6  0.02
relief    #b79a6c  0.2
rim       #d6a46c  0.12
```

**pen-and-ink**

```
farmland  #e9e5da  0.1
meadow    #e9e5da  0.09
orchard   #e1ddd2  0.09
scrub     #e1ddd2  0.08
heath     #e1ddd2  0.14
sand      #e9e5da  0.16
rock      #d9d5ca  0.22
wetland   #d9dedc  0.08
built     #d6d1c5  0.26
works     #d6d1c5  0.28
wood      #4a4741  0.03
pale      #efebe1  0.2
water     #c9d1d4  0.04
relief    #6f6a60  0.3
rim       #bdb7a9  0.18
```

**sepia**

```
farmland  #d8c58f  0.1
meadow    #d6c48f  0.09
orchard   #cfba84  0.09
scrub     #c4ae78  0.08
heath     #c9b078  0.14
sand      #e0cf9f  0.16
rock      #cdbb93  0.22
wetland   #bfb08a  0.08
built     #c9b48a  0.26
works     #c2ad84  0.28
wood      #9a8658  0.05
pale      #d9c593  0.12
water     #b3a07c  0.04
relief    #a28a62  0.3
rim       #9c7f56  0.18
```

**winter**

```
farmland  #e4eaef  0.1
meadow    #dbe5ec  0.09
orchard   #d8e2e8  0.09
scrub     #c9d6de  0.08
heath     #d3dce4  0.14
sand      #e6ebef  0.16
rock      #cfd6dc  0.22
wetland   #c3d5de  0.08
built     #c9d0d8  0.26
works     #c3cad2  0.28
wood      #6f8696  0.05
pale      #dfe7ee  0.12
water     #8fb8d8  0.04
relief    #9fb0c0  0.3
rim       #a9b8c6  0.18
```

**ambleside-hero**

```
farmland  #cdd391  0.1
meadow    #bcd08a  0.09
orchard   #a2b868  0.09
scrub     #b2bd7c  0.08
heath     #d9b47c  0.14
sand      #e0cf9f  0.16
rock      #a39b8d  0.22
wetland   #86b0a4  0.08
built     #cdb899  0.26
works     #b9ad9c  0.28
wood      #7fa466  0.05
pale      #a8c27c  0.12
water     #3a86b5  0.04
relief    #b49a7c  0.3
rim       #8f7757  0.18
```

**ambleside**

```
farmland  #c0cf86  0.1
meadow    #a9cc78  0.09
orchard   #a2b868  0.09
scrub     #8fa862  0.08
heath     #d9b47c  0.14
sand      #e0cf9f  0.16
rock      #a39b8d  0.22
wetland   #86b0a4  0.08
built     #cdb899  0.26
works     #b9ad9c  0.28
wood      #5b8f50  0.05
pale      #a8c27c  0.12
water     #3a86b5  0.04
relief    #a98e6e  0.3
rim       #8f7757  0.18
```

**oxford**

```
farmland  #c0cf86  0.1
meadow    #a8c97c  0.09
orchard   #a2b868  0.09
scrub     #94ad69  0.08
heath     #d6b783  0.14
sand      #e8d6a2  0.16
rock      #c9c0b0  0.22
wetland   #8fb5a8  0.08
built     #ecc98a  0.26
works     #c4a98a  0.28
wood      #5c8a55  0.05
pale      #ead7a3  0.12
water     #5f95b5  0.04
relief    #a9906f  0.3
rim       #a58a5f  0.18
```

**skye**

```
farmland  #b9c480  0.1
meadow    #a7c077  0.09
orchard   #a2b868  0.09
scrub     #8f9a5c  0.08
heath     #9a7490  0.14
sand      #e8d9b0  0.16
rock      #9a948c  0.22
wetland   #8aa89a  0.08
built     #d2bfa6  0.26
works     #b9ad9c  0.28
wood      #587a4c  0.05
pale      #cdc39a  0.12
water     #4f86ad  0.04
relief    #b59a6c  0.3
rim       #c9b58a  0.18
```

**y-fenni**

```
farmland  #d4c36e  0.1
meadow    #b5c26e  0.09
orchard   #b7a95a  0.09
scrub     #9aa05c  0.08
heath     #c98a5a  0.14
sand      #ecd69a  0.16
rock      #cdb9a5  0.22
wetland   #93b3a0  0.08
built     #f1c9a6  0.26
works     #c79a82  0.28
wood      #7c8a4a  0.05
pale      #f0d9ae  0.12
water     #6fa3a6  0.04
relief    #b58a6a  0.3
rim       #b0805a  0.18
```

**yr-wyddfa**

```
farmland  #b4bd84  0.1
meadow    #abc57c  0.09
orchard   #a2b868  0.09
scrub     #8d8f62  0.08
heath     #cf9560  0.14
sand      #dccaa0  0.16
rock      #c0b3a6  0.22
wetland   #7fa0a0  0.08
built     #cbb9a2  0.26
works     #b3a79a  0.28
wood      #587a52  0.05
pale      #dccaa4  0.12
water     #2f6f9e  0.04
relief    #756f8c  0.3
rim       #8a7f96  0.18
```
