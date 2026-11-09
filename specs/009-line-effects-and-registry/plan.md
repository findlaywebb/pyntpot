# 009 — plan

## Approach

ADR 0070 is the design. This plan is how PR 1 lands it. Every fact was measured on
`ee8f321`. Read ADR 0070, the spec, `research.md`, `CLAUDE.md` and `CONTRIBUTING.md` first.

Four layers, in the ADR's order:

1. **The registry and the catalogues (S1, S2), in `ink`.** A frozen `Pigment`, a
   read-only `PigmentRegistry` and the one lookup `pigment()`. The four exported tables
   and the two map copies are built from the registry, keeping today's values and key
   order. The brush tables become read-only and the brush lookup suggests the nearest id.
2. **Colours (S3a, S3b), in `ink` for the type and `maps` for the theme.** `Colour` is
   the type of every colour field. A maps-side validator resolves a hex, an alias or a
   pigment name to a `Colour` at load. The theme gains `colours`, `pigments` and
   `palette`, and `.gpl` comes in and goes out at the maps boundary (ADR 0015).
3. **Effects (S4, S5a, S5b).** RGB primitives in `ink`. The model, presets and the
   `line_effects` and `effect_presets` tables in `maps`, split at load into two group
   fields named in `DIGEST_OMITS_AT_DEFAULT`. The painter and compose take them as
   no-ops at the default.
4. **The grid helper (S6)**, in `examples/`, proved pixel-identical.

Why nothing moves:

- Every value resolves to today's hex string at load. A `Colour` is a `str`, so `asdict`
  and `json.dumps` hash it as itself.
- The two new group fields are omitted from their digests at the default.
- With no effect set, the painter's `over` list is built by today's code, unchanged:
  there is one `composite` call, with no split.
- Compose takes today's path when `route_ink.effects` is empty.

No boundary changes. `ink` imports neither `pydantic` nor `ruamel`, `ink` reads no data
file, and `[tool.importlinter]` is untouched.

### Running the gates

- **Slice gate** (every slice, before its checkpoint commit):

  ```bash
  uv run pytest -n auto --dist loadgroup -m "not golden" -q   # add --golden-tolerance off the pinning machine
  uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run lint-imports
  prek run --all-files
  ```

  `tests/architecture/test_boundaries.py` (the 400-line budget) runs inside it.
- **Schema regeneration** (S3a, S3b, S5a):
  `PYTHONPATH=tests uv run python -m support.theme_schema`. This writes both committed
  copies, and `tests/unit/maps/test_theme_schema.py` checks them.
- **Grid identity** (end of S0, S1, S3a, S6, the merge gates and S9):
  `PYTHONPATH=tests uv run python tests/golden/grid_hashes.py check specs/009-line-effects-and-registry/grid-hashes.json`.
- **Golden docs subset** (S6 and S9):
  `uv run pytest -m golden tests/golden/test_docs_images.py -k "grid or glaze or route-ink or nib or brush-sheet or wash"`.
- **Full golden suite** (S9 only, about 27 min):
  `uv run pytest -m golden -n auto --dist loadgroup` (add `--golden-tolerance` off the
  pinning machine).

### Line budget (400 per file; split, never thin)

| File | Now | After | Plan |
|---|---|---|---|
| `maps/theme_check.py` | 295 | about 350 | The new top-level tables are checked in new `theme_*` modules; `theme_check` only dispatches. |
| `maps/theme_resolve.py` | 265 | about 320 | The chain is read first, then checked from the base up. |
| `maps/style_groups.py` | 336 | about 375 | Effect types live in `maps/line_effects.py`; only two fields and their docs land here. |
| `maps/style.py` | 319 | about 330 | Two omit names; `with_route_ink` uses `Colour.parse`. |
| `maps/theme_schema.py` | 214 | about 240 | The top-level table schemas go in `maps/theme_schema_tables.py`. |
| `maps/painter/pen.py` | 131 | about 190 | Per-class masks. |

New files, each written to stay under 250 lines:

- In `ink/`: `colour.py`, `naming.py`, `pigment_table.py`, `pigment_registry.py`,
  `effect_mask.py`, `effect_casing.py`, `effect_glow.py`, `effect_shadow.py`,
  `effect_pen_casing.py`.
- In `maps/`: `theme_scope.py`, `theme_colours.py`, `theme_pigments.py`,
  `theme_effects.py`, `theme_schema_tables.py`, `palette.py`, `palette_gpl.py`,
  `palettes/plain.yaml`, `line_effects.py`, `effect_pass.py`, `route_effects.py`,
  `painter/effects.py`.
- In `examples/`: `labelled_grid.py`.
- In `tests/golden/`: `grid_hashes.py`.

The module stems are prefixed (`effect_casing`, never `casing`) on purpose:
`tests/architecture/test_site.py` refuses a package that binds a name equal to one of its
submodules.

## Slices

Order: S0, S1, S2, S3a, S3b, S5a, merge gate A (S4 in), S5b, merge gate B (S6 in), S7, S8,
S9. S4 and S6 run in parallel worktrees cut from the branch base after S0. They own no
file any serial slice owns.

### S0: Baseline (serial, first)

- **Owns:** `tests/golden/grid_hashes.py` (new), `tests/golden/make_docs_images.py` (make
  `_fixture_options` public as `fixture_options`, with its one caller repointed) and
  `specs/009-line-effects-and-registry/grid-hashes.json`.
- **What it does:** `grid_hashes.py` takes `record OUT.json` or `check OUT.json`. For
  every `support.docs_images.IMAGES` entry whose stem is `tutorial_grids`, `nib_stages`,
  `brush_sheet`, `wash_stages` or `how_to_route_ink` (21 entries, stage figures
  included), it runs `run_example` in a temporary directory. A fixture entry gets
  `fixture_options` in a copy of its fixture. It then records two hashes per entry, the
  sha256 of the written file's bytes and of its RGB pixels, keyed by `entry.image`.
  `check` logs one line per entry and exits 1 on any difference.
- **Command, run on the untouched base and committed:**
  `PYTHONPATH=tests uv run python tests/golden/grid_hashes.py record specs/009-line-effects-and-registry/grid-hashes.json`
- **Gate:** `check` passes on the base, and so does the slice gate.

### S1: The registry (#72; serial)

- **Owns:**
  - New: `ink/colour.py` (`Colour` and the shared channel arithmetic; the type is needed
    here because `Pigment.colour` is a `Colour`), `ink/naming.py`
    (`nearest(name, known) -> tuple[str, ...]`, difflib with cutoff 0.6, shared with
    `brush.py` and maps), `ink/pigment_table.py` (`Pigment`, plus `ROLE_PIGMENTS` and
    `TUBE_PIGMENTS` in today's order, and `role_transparencies()`) and
    `ink/pigment_registry.py` (`PigmentRegistry`, `PIGMENT_REGISTRY`, `pigment`).
  - Rename `ink/pigment.py` to `ink/compositing.py` (`git mv`, no shim), because the
    public function `pigment` cannot coexist with a submodule named `pigment`. Repoint
    every importer: `ink/__init__.py`, `ink/washing.py`, the six `maps/painter/{ribbon,
    pen, plates, job, water, cover}.py`, `tests/unit/ink/test_wash.py`,
    `tests/unit/ink/test_pigment.py`, `tests/unit/maps/test_import_order.py`,
    `tests/property/test_pigment.py`, `tests/benchmarks/test_ink.py`,
    `tests/architecture/test_reference_keys.py` and `docs/explanation/references.md`. Leave
    the ADR text as it is.
  - Defaults built from the registry: `PaperStyle.pigment_transparency` in
    `ink/style.py`, `CoverStyle.pigments` in `maps/style_groups.py`, and `_PIGMENTS` in
    `maps/theme_vocab.py` (from `ROLE_PIGMENTS` names).
  - Exports: `ink/__init__.py` (exports and docstring), `tests/unit/test_public_api.py`
    and `docs/reference/ink.md` (one directive per new name).
- **Shapes:**
  - `Colour(text)` accepts only lower-case `#rrggbb`. `Colour.parse` lower-cases; it
    defines `__slots__ = ()` and no `__init__`.
  - `Pigment` is `@dataclass(frozen=True, kw_only=True)`.
  - `PigmentRegistry(pigments: tuple[Pigment, ...])` refuses duplicate names. It offers
    `names()`, `get(name)` (`ValueError`: "no pigment 'ultramarin'; did you mean
    ultramarine?"), `__contains__` and `extended(added)`. A `functools.cached_property`
    holds the index.
  - `pigment(ref, registry=None)`.
- **Tests first:**
  - `tests/unit/ink/test_colour.py`: parse and refuse cases; `deepcopy`, `pickle`,
    `asdict` and `json.dumps` round trips.
  - `tests/unit/ink/test_pigment_registry.py`: 25 pinned entries; the lookups; the miss
    message; the four tables equal the registry projection.
  - In maps tests: `CoverStyle().pigments` and `PaperStyle().pigment_transparency` equal
    the registry, keys in pinned order.
  - `tests/property/test_pigment_registry.py`, strategies `st.from_regex(ALIAS)` names,
    lower-case hex and `st.none() | st.floats(0, 1)`:
    - `extended(())` resolves every name identically;
    - an extension naming any built-in raises;
    - a non-colliding extension leaves every built-in lookup equal and the base
      unchanged;
    - `Colour.parse(h).rgb.tobytes() == rgb(h).tobytes()`.
  - `tests/architecture/test_one_registry.py`: each built-in hex is a literal in one
    `src` module only.
- **Gate:** slice gate; `test_pigment.py` pins unchanged; grid `check`.

### S2: The catalogues as typed tables (#71; serial)

- **Owns:** `ink/brush_sheet.py`, `ink/brush.py`, and the brush-id branch of
  `maps/theme_check.py` (`_sheet_and_colour`, message gains "; did you mean X?"), with
  their tests in `tests/unit/ink/test_brush.py` and `tests/unit/maps/test_theme_check.py`.
- **Changes:**
  - Wrap `BRUSH_TREATMENTS` and `BRUSH_COLOURS` (outer and inner) in
    `types.MappingProxyType`, typed `Mapping[...]`. `PEN_ROWS` is already a `frozenset`.
  - Add `brush_ids() -> tuple[str, ...]`, every id `brush_id_known` accepts.
  - `brush_from_id` names `nearest(...)`.
- **Tests first:**
  - The tables refuse assignment.
  - `brush_ids()` equals the cross product the sheet implies, pinned by count and sample.
  - The miss suggests `RIV1-a` for `RIV1-z`.
- **Gate:** slice gate.

### S3a: `Colour` across every field (serial)

- **Owns:** `ink/style.py`, `ink/sheet.py`, `letters/style.py`, `maps/style_groups.py`,
  `maps/style.py`, `maps/compose_steps.py`, `maps/theme_scope.py` (new),
  `maps/theme_check.py`, `maps/theme_vocab.py`, `maps/theme_schema.py`, both
  `theme.schema.json` copies, `tests/unit/maps/test_theme_vocab.py`,
  `tests/unit/maps/test_theme_schema.py`, `tests/unit/maps/test_theme_check.py` and
  `tests/unit/maps/test_style.py`.
- **Retyping fields:**
  - Retype the fields: `paper_hex: Colour = Colour("#f3ead6")`,
    `separation_pigments: dict[str, Colour]`, the four nib inks, `pigments:
    dict[str, Colour]` and `route_ink.colour`.
  - `Style` gets `arbitrary_types_allowed=True`, because pydantic builds a schema for each
    stdlib-dataclass field and has none for `Colour`. Group instances pass unrevalidated.
  - `with_route_ink` uses `Colour.parse`, and its `ValueError` message is unchanged.
  - `compose_steps._rgb` is replaced by `Colour.rgb8`.
- **The checker** (`theme_check.py` is extended, not replaced):
  - `_adapter(Colour)` returns
    `Annotated[Colour, BeforeValidator(resolve_theme_colour)]` with
    `arbitrary_types_allowed`. The validator reads `info.context["scope"]`, so the cached
    adapter serves every theme. `_Check.leaf` passes `context={"scope": self.scope}`.
  - `_message` maps `value_error` to the validator's own text and `is_instance_of` to
    "is not a string".
  - The colour branch of `_sheet_and_colour` goes (the brush branch stays).
- **`theme_scope.py`** holds `ThemeScope(registry, aliases, presets)`, the frozen,
  scoped vocabulary, and `ThemeScope.built_in()`. It also holds `resolve_colour(text,
  scope) -> Colour`: a leading `#` goes to `Colour.parse`, anything else to an alias and
  then a registry name. A miss reads "'x' is not a pigment or a colour alias; did you
  mean y?".
- **`theme_vocab.py`:** `COLOUR_FIELDS` is retired. `COLOUR_PATTERN` stays, and
  `ALIAS_PATTERN = "^[a-z][a-z0-9_]*$"` is added.
- **`theme_schema.py`:** `_leaf_schema` emits for `Colour`:
  `{"anyOf": [{"enum": sorted names}, {"type": "string", "pattern": COLOUR_PATTERN},
  {"type": "string", "pattern": ALIAS_PATTERN}]}`. The third branch exists because the
  schema is static and cannot know a theme's aliases or pigments. The enum gives
  completion, and the checker gives the good error.
- **Tests first:**
  - Every field whose default is all `#rrggbb` is typed `Colour` (this replaces the
    `COLOUR_FIELDS` test).
  - Every `Colour`-typed path in the model (dict values included) has the three-branch
    node in the schema.
  - `cover.pigments.built: ultramarine` loads as `#2b3d8f`.
  - `ultramarin` is a located error with the suggestion.
  - Upper-case hex is stored lower-case.
  - `Style()` builds, and the pinned digests hold.
- **Gate:** slice gate; schema regenerated; grid `check`.

### S3b: Aliases, theme pigments and palettes (serial)

- **Owns:** `maps/theme_colours.py`, `maps/theme_pigments.py`, `maps/palette.py`,
  `maps/palette_gpl.py` and `maps/palettes/plain.yaml` (all new), plus
  `maps/theme_resolve.py`, `maps/theme_check.py` (top-level dispatch),
  `maps/theme_schema_tables.py` (new), `maps/theme_schema.py`, both schema copies,
  `maps/__init__.py` (exports `Palette`), `docs/reference/maps.md`,
  `tests/unit/test_public_api.py`, the new tests below, and `tests/unit/maps/test_cli.py`
  (one case).
- **Checking order.** `check_theme_scoped(theme, groups, scope) -> (table, problems,
  scope)` is new. `check_theme` keeps its signature and return as a wrapper. Each file is
  checked in this order: `pigments` (`theme_pigments`), then `palette` (`palette.py`),
  then `colours` (`theme_colours`), then the groups with the scope, then (S5a)
  `effect_presets` and `line_effects`. The top-level vocabulary for an unknown key is
  `extends`, `palette`, `pigments`, `colours`, `effect_presets`, `line_effects` and the
  groups.
- **Rules:**
  - A theme pigment name matches `ALIAS_PATTERN`. Its `base` names a built-in or an
    inherited pigment, and its `colour` is a hex; exactly one of `base` and `colour` is
    required.
  - A collision with a built-in reads "'ultramarine' is a built-in pigment; derive one:
    my_ultramarine: {base: ultramarine}".
  - An alias value is a pigment name or a hex, never an alias; an alias name is no
    pigment name.
  - Replacing an inherited or palette entry (alias, pigment, preset) without
    `override: true` is an error at the replacing key's line.
- **`theme_resolve.py`:**
  - Read the whole chain first, following the raw `extends` strings and stopping at a
    file whose read found a problem, as today.
  - Then check from the base-most file up, threading the scope.
  - Problems are collected and raised as today. The cycle, refusal and missing-file
    messages are unchanged.
- **`palette.py`:**
  - `Palette(name, colours: Mapping[str, Colour])`, frozen, with `Palette.names()`
    (packaged `maps/palettes/*.yaml` stems), `Palette.named(name)`,
    `Palette.from_file(path)` (`.yaml` or `.gpl`), `Palette.of_registry(registry)`,
    `to_gpl()`.
  - A palette `.yaml` holds only `colours:`, is read by `theme_read`, carries the theme
    schema directive, and is checked by the same alias rules.
  - Problems are `ThemeProblem`s at the palette file's own lines.
- **`palette_gpl.py`:**
  - Parse: the `GIMP Palette` header, then `Name:`, an optional `Columns:` and `#`
    comments, then `R G B name` rows (0 to 255).
  - A name is normalised to an alias (lower case; each run of other characters becomes
    `_`, stripped). A row with no name, or a name equal to a built-in pigment, is a
    located error.
  - Export writes `f"{r:3d} {g:3d} {b:3d}\t{name}"` rows. The registry export uses
    canonical names and drops transparency and Colour Index (rule 7).
- **`plain.yaml`:** `blue: ultramarine`, `sky: cerulean`, `green: sap_green`, `brown:
  burnt_sienna`, `orange: raw_sienna`, `ochre: yellow_ochre`, `red: quinacridone_rose`,
  `maroon: perylene_maroon`, `navy: indigo`, `grey: paynes_grey`.
- **Schema (`theme_schema_tables.py`, which must not import `maps.style`):**
  - `colours`: `propertyNames` `{pattern: ALIAS_PATTERN, not: {enum: names}}`; values are
    names or hex, or `{colour, override}`.
  - `pigments`: the same key rule; values are an object of `base` (enum names), `colour`
    (hex), `transparency` (0 to 1), `colour_index` and `override`.
  - `palette`: `anyOf` [enum packaged names, a `\.(yaml|gpl)$` pattern].
- **Tests first:**
  - `tests/unit/maps/test_theme_colours.py`, `test_theme_pigments.py`, `test_palette.py`
    and `test_palette_gpl.py` cover every refusal, located with file, key, line and
    suggestion, plus inheritance across `extends`.
  - CLI: a misspelt pigment in `--style` exits 2 and no provider is called.
  - `tests/property/test_theme_colours.py`: an alias (`from_regex(ALIAS)` filtered off
    names) to `sampled_from(names)` resolves to `pigment(name).colour`.
  - `tests/property/test_palette_gpl.py`: `st.dictionaries(alias names, lower hex)`
    survives export then import as equal.
- **Gate:** slice gate; schema regenerated; pinned digests of every theme unchanged.

### S4: Effect primitives (parallel worktree from base, after S0)

- **Owns:** `ink/effect_mask.py`, `ink/effect_casing.py`, `ink/effect_glow.py`,
  `ink/effect_shadow.py` and `ink/effect_pen_casing.py` (all new);
  `tests/unit/ink/test_effects.py`; `tests/property/test_line_effects.py`. It does **not**
  touch `ink/__init__.py`; merge gate A adds the four exports.
- **Building blocks:** `noise.chamfer_distance`, `noise.blur` and `noise.smoothstep`;
  `LINE_THRESHOLD = 0.3` lives in `effect_mask.py`. `rgb` is float32 `(h, w, 3)` in 0 to
  1. `mask` is float `(h, w)`. `paper` is `None` (wash space, where 1 is the paper) or an
  `(h, w, 3)` plate. Widths are in the array's own pixels.
- **The four functions:**
  - `casing(rgb, mask, *, width_px, colour, strength=1.0, threshold, paper=None)`
    returns `rgb` itself when `width_px <= 0`, `strength <= 0` or no mask pixel reaches
    `threshold`. Otherwise:
    `a = strength * smoothstep(width_px - chamfer_distance(mask >= threshold), 1.0)` and
    `out = rgb + a * (colour * paper - rgb)`, so white is the paper.
  - `glow(rgb, mask, *, spread_px, blur_px, strength, threshold, paper=None)` is the
    identity at `strength <= 0`. Otherwise
    `core = chamfer_distance(mask >= threshold) <= spread_px`,
    `a = strength * clip(blur(core, blur_px), 0, 1)` and
    `out = rgb + a * max(paper - rgb, 0)`. The floor at 0 is what makes "never darkens"
    hold for any input.
  - `shadow(rgb, mask, *, offset_px, blur_px, strength, colour, azimuth_deg, threshold)`
    shifts the mask (zero fill, never `np.roll`) by `offset_px` along bearing
    `azimuth_deg + 180`, with `dx = sin`, `dy = -cos` in image rows. Then
    `a = strength * blur(shifted) * (1 - clip(mask / threshold, 0, 1))` and
    `out = where(a > 0, rgb * (1 - a * (1 - colour)), rgb)`.
  - `pen_casing(rgb, mask, *, width_px, edge_px, threshold, paper=None) -> (rgb, edges)`
    knocks the wash to the paper inside the reserve (`d <= width_px`). It returns the
    density of the two ink edge lines (`width_px < d <= width_px + edge_px`). Width 0
    returns `(rgb, zeros)`.
  - No function draws a random number, and each returns a new float32 array clipped to 0
    to 1, except the identity returns.
- **Property strategies:**
  - Inputs: `hypothesis.extra.numpy.arrays(np.float32, (h, w, 3), elements=floats(0, 1,
    width=32))` with `h, w` in 8 to 40; a mask from the same strategy with shape `(h, w)`;
    `paper` as `None` or an array.
  - Casing: `width_px` in {0.0, -0.0, negatives} gives a bitwise-identical result
    (`view(np.uint32)`).
  - Glow: `out >= rgb` everywhere for any spread, blur, strength and paper.
  - Shadow: `out == rgb` bitwise where `mask >= threshold`, and `out <= rgb` everywhere.
  - Pen casing: width 0 is the identity and gives zero edges; inside the reserve, minus
    the edge band, `out == paper`.
- **Gate:** slice gate in the worktree. Mutation (S8) needs these tests under
  `tests/unit/ink` and `tests/property`, which is where they are.

### S5a: The line-effect model, presets and theme fields (serial)

- **Owns:**
  - New: `maps/line_effects.py` (`Casing`, `Glow`, `Shadow`, `EffectStack`,
    `LINE_CLASSES`, `WATER_GROUP`, `ROAD_GROUP`, `BUILT_IN_PRESETS`; it imports no style)
    and `maps/theme_effects.py`.
  - Edits: `maps/style_groups.py` (`BasemapStyle.line_effects: dict[str, EffectStack]`,
    default `{}`, and `RouteInkStyle.effects: EffectStack = EffectStack()`, with their
    docstrings; the module docstring loses "holds no casing, glow or shadow"),
    `maps/style.py` (`DIGEST_OMITS_AT_DEFAULT` gains `"line_effects"` and `"effects"`,
    with docs), `maps/theme_check.py` (dispatch `effect_presets` and `line_effects`;
    `LOADER_FIELDS` refusal), `maps/theme_vocab.py` (`LINE_CLASSES` vocabulary and
    `LOADER_FIELDS = {("basemap", "line_effects"): "line_effects.<class>", ("route_ink",
    "effects"): "line_effects.route"}`), `maps/theme_schema.py` (skips `LOADER_FIELDS`),
    `maps/theme_schema_tables.py`, both schemas, `maps/__init__.py`,
    `docs/reference/maps.md` and `tests/unit/test_public_api.py`.
- **Types:** frozen, `kw_only`, and default-constructible.
  - `Casing(width_px=0.0, colour=Colour("#ffffff"), strength=1.0)`
  - `Glow(spread_px=0.0, blur_px=0.0, strength=0.0)`
  - `Shadow(offset_px=0.0, blur_px=0.0, strength=0.0, colour=Colour("#3b4452"))`
  - `EffectStack(effects: tuple[Casing | Glow | Shadow, ...] = ())`, whose `__post_init__`
    refuses two of a kind.
  - Widths are in display pixels.
- **Presets** (provisional values, tuned with figures in PR 2; no PR 1 pin depends on
  them):
  - `cased = (Casing(width_px=1.2),)`
  - `halo = (Glow(spread_px=1.0, blur_px=2.5, strength=0.8),)`
  - `lifted = (Shadow(offset_px=1.2, blur_px=1.5, strength=0.35),)`
- **`theme_effects.py`:**
  - Checks `effect_presets` (no built-in name; the `override` rule).
  - Checks `line_effects`: keys against `LINE_CLASSES` with the nearest name. A string
    value is a preset name, with the nearest name on a miss. A mapping value has keys
    `casing`, `glow` and `shadow`, nearest name on a miss, applied in key order. A
    `preset` key reads "a line class takes a preset name or a stack, not both". Each
    effect is checked by `_Check.table` on its dataclass, so its colour resolves through
    the scope.
  - Drops off effects (casing width 0, glow or shadow strength 0) and empty stacks.
  - Splits the result into `{"basemap": {"line_effects": {...}}, "route_ink":
    {"effects": EffectStack}}` and merges it into the file's table. Stacks are objects,
    so `merge` replaces a class's stack whole down `extends`.
- **Tests first:**
  - `tests/unit/maps/test_line_effects.py`: types; at most one of a kind;
    `LINE_CLASSES == frozenset(BrushStyle().brushes) | {"route"}`.
  - `tests/unit/maps/test_theme_effects.py`: every refusal, located; the split; the
    `LOADER_FIELDS` refusal.
  - `tests/unit/maps/test_digest_omits.py`: the two names are in
    `DIGEST_OMITS_AT_DEFAULT`; each omit name matches exactly one field across all groups;
    a set basemap stack moves `base_digest` and `digest` but not `lettering_digest`; a set
    route stack moves `digest` only; the packaged and example themes keep their pins.
  - `tests/property/test_line_effect_presets.py`: `sampled_from(BUILT_IN_PRESETS)` and
    generated theme presets. The preset name and the written-out stack give equal styles
    and digests.
  - `tests/property/test_line_effect_digests.py`: `sampled_from(packaged and example
    themes)` and `st.sets(sampled_from(LINE_CLASSES))`. Each class gets `{}` or off
    effects in a temporary theme extending the sampled one, and the three digests equal
    the sampled theme's.
- **Gate:** slice gate; schema regenerated; every pinned digest unchanged.

### Merge gate A

Merge S4. Then:

- Add `casing`, `glow`, `shadow` and `pen_casing` to `ink/__init__.py`, to
  `docs/reference/ink.md` and to `INK_PUBLIC`.
- Run the slice gate on the merged tree.

### S5b: The painter and compose wiring (serial, after merge gate A)

- **Owns:** `maps/effect_pass.py`, `maps/painter/effects.py` and `maps/route_effects.py`
  (all new), plus `maps/painter/pen.py`, `maps/painter/plates.py`,
  `maps/compose_steps.py` (the `route` branch and the `route` docstring, which PR 2 does
  not touch), `tests/unit/maps/painter/test_effects.py` and
  `tests/unit/maps/test_route_effects.py`.
- **`effect_pass.lay_stack(rgb, mask, stack, *, scale, paper)`** runs a stack's effects
  in order through the `ink` primitives. It converts display pixels by `scale` and
  colours by `.rgb`. Shadows take `relief.DEFAULT_SUN.azimuth`, the hillshade's light; a
  test pins that this is the constant the relief shades with.
- **`pen.py`:** `paint_pen` keeps its return. A new `pen_groups(job)` returns each
  group's layers and its per-class masks: the road masks are the band densities already
  read. A water class's mask comes from a mask-only `InkPad` holding that class's lines,
  read with the major brush, and is built only when that class has an effect.
  Bristles are keyed by seed and points, so the mask matches the union pad's strokes.
- **`plates._wash_plate`:** today's body runs unchanged when
  `style.basemap.line_effects` is empty. Otherwise `painter/effects.lay_wash` composites
  the sea and rim over the ground, lays the water group's stacks in class order, glazes
  the water layer, lays the road group's stacks, then glazes the road layers. No
  `dither_rng` draw.
- **`compose_steps.route`:** when `ink.effects.effects` is empty, today's path runs.
  Otherwise `route_effects.lay` takes the mask: the pen alpha, thresholded at
  `LINE_THRESHOLD` before use, or the solid line's reduced mask. It lays the stack on the
  card as float, with `paper` from `plates.paths["paper"]` and `scale=k`, rounds back to
  8 bits, then lays the line as today. The docstring's "No casing, glow or shadow is
  drawn" changes to what is drawn, and states that the consumer's SVG page does not
  show route effects.
- **Tests first:**
  - On the tiny fixture, a set road casing changes the wash plate only within the ring
    of its mask, and a set water glow builds the mask pads.
  - With `line_effects` empty, `_wash_plate` runs one `composite` call (asserted by
    comparing arrays with the default path on the same job).
  - A route casing at compose changes only pixels within its ring and never `pen.webp`.
  - The pinned `GOLDEN_HASH` holds.
- **Gate:** slice gate; `test_pipeline_fetch_paint.py` and `test_route_ink.py` pins
  unchanged.

### S6: The grid helper (#170; parallel worktree from base, after S0)

- **Owns:** `examples/labelled_grid.py` (new), `examples/tutorial_grids.py`,
  `examples/nib_stages.py`, `examples/brush_sheet.py`, `examples/wash_stages.py`,
  `examples/how_to_route_ink.py`, `tests/support/examples.py`,
  `tests/architecture/test_examples.py` and `tests/examples/test_labelled_grid.py` (new).
- **`GridSpec`:** frozen, with `width, cols, rows, cell_h, left, top, gap=14,
  pad_right=14, pad_bottom=14, unit=1.0, trailing_gap=False`. It provides `.boxes()`,
  `.height` and `.cell_w`. Rounding is reproduced exactly for each layout. Where a layout
  cannot be reproduced, use an origin override rather than a flag. Do not tidy the 12 and
  14 offsets.
- **`label_grid`:** `label_grid(img, spec, columns, rows, *, px, ink, pen_px, col_dy=14,
  row_dx=12, row_dy=7, gran_px, seed, extra=())` holds the one nib-plate round trip (the
  `RGBa` Lanczos downsize kept).
- **`run_example`** puts `EXAMPLES_DIR` on `sys.path` for the call and restores it after.
  `test_examples.py` allows `from labelled_grid import ...` (an `_EXAMPLE_SIBLINGS`
  allowlist), and the helper itself imports only public names.
- **Tests first:** before any edit, run the old `_layout`, `_cells` and the three inline
  layouts in a scratch session and paste their boxes as literals into
  `test_labelled_grid.py`, one parametrised case per layout (`ids=`). The module is
  loaded with `runpy.run_path`.
- **Gate:** slice gate; grid `check`; the golden docs subset.

### Merge gate B

Merge S6. Then run the slice gate, grid `check` and the golden docs subset on the merged
tree.

### S7: Docs and notes (serial)

- **Owns:** `docs/how-to/write-a-theme.md`, `docs/reference/pigments.md`,
  `tests/docs/test_reference_values.py`, `docs/reference/style-fields.md` (if its
  comparator needs the two fields), `GLOSSARY.md` and the regenerated glossary files,
  the `docs/features/` notes listed below, and ADR 0070's "Public names" paragraph.
- **`write-a-theme.md`** (text only, no image): naming a colour by pigment or alias,
  `colours`, `palette` (and `.gpl`), and `pigments` with the derived form. Line effects
  get one sentence (the keys exist, all off) pointing at the schema; their guide comes
  with figures in PR 2.
- **`pigments.md`:** gains a Colour Index column, and the comparator checks it.
- **Glossary:** code columns for "pigment registry" (`pyntpot.ink.PIGMENT_REGISTRY`) and
  "palette" (`pyntpot.maps.Palette`); regenerate with
  `PYTHONPATH=tests uv run python -m support.glossary`.
- **Notes:**
  - Delete `docs/features/ink-one-pigment-registry.md`,
    `ink-data-driven-brushes-and-pigments.md` and `docs-labelled-grid-helper.md`, and
    repoint every link (`git grep`).
  - Update the facts in `maps-route-casing.md`, `maps-route-glow.md` and
    `maps-route-shadow.md`: the primitive and the stack exist; figures and docs come in
    PR 2.
  - In `maps-bridges-over-water.md:43-44` and `maps-water-lining.md:33-34`, replace
    "cited by the brief but not yet in `docs/decisions/` at the time of writing" with a
    link to `../decisions/0070-line-effects-and-one-pigment-registry.md`.
- **ADR 0070:** name the concrete public names (`PigmentRegistry`, `PIGMENT_REGISTRY`,
  `Casing`, `Glow`, `Shadow`, `EffectStack`, `Palette`). This is wording only; no rule
  changes.
- **Gate:** slice gate (the docs tests run inside it); grep for em and en dashes in human
  prose is empty.

### S8: Mutation testing (serial, local)

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

- **In scope:** `ink/colour.py`, `ink/naming.py`, `ink/pigment_table.py`,
  `ink/pigment_registry.py`, the `effect_*` modules, `ink/brush.py`
  (`brush_ids`, `brush_from_id`), `ink/sheet.rgb` and `ink/brush_sheet.py`.
- **Moved, not changed:** the functions of `ink/compositing.py` were moved unchanged
  (`git diff -M` shows them unchanged). Drop them from the pattern list and say so in
  `mutation.md`.
- **Letters:** `letters/style.py` changes types only, so there are no letters functions
  to mutate.
- **Survivors:** kill each with a test under `tests/unit/ink` or `tests/property`, or
  record it as equivalent, with the reason, in `specs/009-line-effects-and-registry/mutation.md`.

### S9: Final review and PR (serial, fresh context)

- **Gates:** the full golden suite with no regeneration, grid `check`, the slice gate,
  and `git diff origin/main -- pyproject.toml` showing no importlinter change.
- **Reviews:** a fresh-context diff review against this plan, then the elegance pass.
- **PR:** the spec's title and Changelog; `Closes #72`, `Closes #71`, `Closes #170`;
  the mutation equivalents; a "Golden and docs images" section stating none moved, with
  the grid `check` log.

## Files to touch

These are the files named in each slice above. The surface of the theme checker grows in
`maps/theme_check.py` (dispatch, Colour adapter, messages, brush suggestion,
`LOADER_FIELDS`), `maps/theme_vocab.py`, `maps/theme_resolve.py` and
`maps/theme_schema.py`, with the new `theme_*` modules beside them. Under ADR 0069's
import rule, none of them imports `pyntpot.maps.style` or the `pyntpot.maps` package
(`tests/architecture/test_theme_imports.py`).

## Files to leave alone

- `letters/nib.py`: it refuses halos by design. An effect there would move
  `lettering_digest` (rule 14).
- `src/pyntpot/maps/themes/*.yaml` and `examples/themes/*.yaml`: adopting names, aliases
  or effects is PR 2. Even a digest-neutral rewrite muddies the "nothing moved" proof.
- `docs/images/**`, `tests/golden/docs/**`, `tests/golden/lynmouth/**` and every pinned
  literal (`GOLDEN_HASH`, `DIGEST`, `BASE_DIGEST`, `LETTERING_DIGEST`, theme digests): a
  pin that wants to move is a bug in this PR.
- `PaperStyle.pigment_transparency` semantics and `Style.with_route_ink` behaviour: D7
  and #159 are PR 2 (only the parse changes here).
- `ink/paper.py` tints, `sheet.PAPER` and `maps/lettering_marks.py` note colours: these
  are not style fields.
- `maps/relief.py`: the shadow reads `DEFAULT_SUN`; it does not change it.
- `examples/` other than the five grid scripts: rewriting them onto `pigment()` would put
  docs images at risk; that is a later change.
- `pyproject.toml` `[tool.importlinter]`: the contracts do not change (ADR 0070 rule 1).
- `tests/support/docs_images.py` budgets: no image is added.

## Test plan

Each criterion maps to a test named in its slice. The Hypothesis properties, with their
modules and strategies:

| Property | Module | Strategy |
|---|---|---|
| Casing of width 0 is the identity, bit for bit | `tests/property/test_line_effects.py` | float32 RGB and mask arrays, `width_px` in {0, -0, negatives} |
| Glow never darkens | same | arrays, any spread, blur and strength, paper `None` or an array |
| Shadow never paints over its casting line | same | arrays, any offset, blur, strength, colour and azimuth |
| Pen casing: width 0 is the identity; the reserve is paper | same | arrays and widths |
| An empty registry extension is the identity | `tests/property/test_pigment_registry.py` | `sampled_from(names)` |
| A caller pigment never shadows a built-in | same | alias-pattern names, hex, `none() \| floats(0, 1)` |
| `Colour.rgb` equals `ink.rgb` bit for bit | same | `from_regex` hex, either case |
| An alias resolves to the same hex as its pigment | `tests/property/test_theme_colours.py` | alias names off the registry, `sampled_from(names)` |
| `.gpl` export then import round-trips | `tests/property/test_palette_gpl.py` | `dictionaries(alias names, lower hex)` |
| A preset expands to the stack it names | `tests/property/test_line_effect_presets.py` | built-in and generated presets |
| Default or off `line_effects` leaves every digest unchanged | `tests/property/test_line_effect_digests.py` | `sampled_from(themes)`, `sets(sampled_from(LINE_CLASSES))` |

Guards left behind:

- The registry ties and the single-literal check (`test_one_registry.py`).
- Every hex-defaulted field is typed `Colour`.
- Every `Colour` field has the three-branch schema node.
- The schema copies are regenerated and checked.
- The omit names are unique, and the new fields are omitted at the default.
- `LINE_CLASSES` equals the brush keys plus `route`.
- The shadow takes the hillshade azimuth.
- The import contracts are unchanged (lint-imports), and `ink` imports neither pydantic
  nor ruamel.
- Grid hashes, and `boxes()` against literals.

Purity proof: the golden suite and the golden docs tests pass with no regeneration; every
pinned digest and `GOLDEN_HASH` holds; the grid hashes recorded in S0 hold after every
slice.

## Delegation

- **Orchestrator (main context):** this plan, the plan-reviewer gate, the merge gates, the
  integrator's checks after each slice (the full slice gate, grid `check`, seams: exports,
  schema copies, digests), commits and the PR.
- **Plan-reviewer:** a fresh-context sceptical staff engineer reads this plan before S0 and
  blocks until it passes.
- **plan-slice-implementer agents:** one per slice, each briefed with its slice section,
  owned files, tests first and gate. S3b, S5a and S5b are design-heavy and go to the
  strongest model. S0, S2, S6 and S7 are mechanical and can go to a cheaper one. S4 is
  maths with property tests and goes to the strongest model.
- **Parallel:** S4 and S6 run in worktrees cut after S0, merged at gates A and B.
  Everything else is serial on the branch.
- **After green:** a fresh-context diff review against the plan, then the elegance pass;
  findings triaged by the orchestrator.

## File-ownership partition

| Track | Owns | After | Parallel |
|---|---|---|---|
| S0 | `tests/golden/grid_hashes.py`, `tests/golden/make_docs_images.py`, `grid-hashes.json` | base | no |
| S1 | `ink/{colour,naming,pigment_table,pigment_registry,compositing,style,__init__}.py`, importers of the old module, `maps/style_groups.py`, `maps/theme_vocab.py`, registry tests, `docs/reference/ink.md`, `test_public_api.py` | S0 | no |
| S2 | `ink/brush_sheet.py`, `ink/brush.py`, brush branch of `maps/theme_check.py` | S1 | no |
| S3a | `ink/{style,sheet}.py`, `letters/style.py`, `maps/{style_groups,style,compose_steps,theme_scope,theme_check,theme_vocab,theme_schema}.py`, schemas | S2 | no |
| S3b | `maps/{theme_colours,theme_pigments,palette,palette_gpl,theme_resolve,theme_schema_tables}.py`, `maps/palettes/`, `maps/__init__.py`, `docs/reference/maps.md`, schemas | S3a | no |
| S4 | `ink/effect_*.py`, `tests/unit/ink/test_effects.py`, `tests/property/test_line_effects.py` | S0 | yes, worktree |
| S5a | `maps/{line_effects,theme_effects}.py`, plus edits to `style_groups`, `style`, `theme_check`, `theme_vocab`, `theme_schema`, `theme_schema_tables` and `__init__` | S3b | no |
| Gate A | `ink/__init__.py` exports, `docs/reference/ink.md`, `test_public_api.py` | S4, S5a | no |
| S5b | `maps/{effect_pass,route_effects,compose_steps}.py`, `maps/painter/{effects,pen,plates}.py` | gate A | no |
| S6 | `examples/labelled_grid.py`, the five grid scripts, `tests/support/examples.py`, `tests/architecture/test_examples.py`, `tests/examples/test_labelled_grid.py` | S0 | yes, worktree |
| Gate B | the merged tree | S5b, S6 | no |
| S7 to S9 | docs, notes, ADR wording, `mutation.md`, the PR | gate B | no |

## Decisions

Forks picked with no human in the loop, each with its reason:

- **`ink/pigment.py` becomes `ink/compositing.py`.** The public `pigment` would shadow the
  submodule (`test_site.py`). Module paths are not public, so there is no `!`.
- **The `Colour` validator reads pydantic validation context.** The adapter stays cached
  and still sees each theme's aliases. `Style` allows arbitrary types, because pydantic
  must build a schema for every dataclass field.
- **The schema's `Colour` node has a third, identifier branch.** Without it every alias
  and theme pigment fails editor validation. The enum still gives completion.
- **Aliases, theme pigments, the palette and presets inherit down `extends`.** Replacing
  an inherited entry needs `override: true`, the same rule as for palette aliases.
- **A stack is a mapping keyed by effect kind, applied in key order.** Duplicate kinds are
  impossible (the reader refuses duplicate keys), and the existing sub-table checker
  checks each effect with no new machinery.
- **The two group fields are loader-only.** They are set only through `line_effects`, so
  one key path names each thing. `BasemapStyle` takes the basemap field because `brush`
  is ink's group and cannot hold maps types.
- **Off effects and empty stacks are dropped at load.** Writing "off" then equals writing
  nothing, digest included.
- **Casing colour is laid over the paper,** so white is the paper. Glow is floored at 0,
  so it cannot darken. `LINE_THRESHOLD` is 0.3, a constant, not a theme field. The shadow
  takes `DEFAULT_SUN.azimuth`.
- **Pen casing is a primitive only.** Wiring it into the model needs the line's own ink
  replaced, which is PR 2's design and figures.
- **`Palette` is public in maps.** Rule 7's import and export need a public entry. `plain`
  is the one bundled palette: the everyday names #72 asks for, kept out of the registry
  (rule 1).
- **A `.gpl` entry named like a built-in pigment is refused, never dropped.** The goal is
  "never silently".
- **A theme pigment's transparency is recorded but unused** until rule 17 (PR 2).
- **Orchestrator adjustment: compose_steps docstring.** This PR wires route effects into
  `compose_steps.route` (S5b), so the `route` docstring change ("No casing, glow or
  shadow is drawn" becomes what is drawn, and the consumer's SVG page does not show
  route effects) belongs here: it is in S5b's Files to touch above and in S5b's tasks.
  PR 2 does not touch it.
