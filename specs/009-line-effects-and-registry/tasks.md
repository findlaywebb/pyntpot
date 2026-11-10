# 009 — tasks

Slices and files are in `plan.md`. Order: S0; then S1, S2, S3a, S3b in turn, with S4
and S6 each in a parallel worktree cut after S3a; merge gate A (S4 in); S5a; S5b; merge
gate B (S6 in); S7, S8, S9.

## Start

- [x] Comment the branch and spec `009` on #72, #71 and #170. Name #104, #105 and #106 as
      generalised, closing in `009a`.
- [x] ADR 0070 amended to match the plan (review finding 15): two converters, the
      three-branch schema, the glow floor, the loader-only fields and their schema
      shape and ranges, binding down `extends`, off dropped after the final merge, the
      public names and the module rename.
- [x] The plan-reviewer passes the revised plan.

## S0: Baseline

- [x] `tests/golden/grid_hashes.py` (`record` and `check`, file and pixel sha256 per
      entry of the five grid scripts); `make_docs_images.fixture_options` made public.
- [x] On the untouched base: `PYTHONPATH=tests uv run python tests/golden/grid_hashes.py record specs/009-line-effects-and-registry/grid-hashes.json`, committed alone.
- [x] `check` passes; slice gate green.

## S1: The registry (#72)

- [x] Red: `test_colour.py`, `test_pigment_registry.py`, `test_one_registry.py`, the
      property tests (`pigment(hex)` anonymous, `transparency=None`, among them), and the
      maps default ties in `tests/unit/maps/test_registry_defaults.py` (new).
- [x] `ink/colour.py`, `ink/naming.py`, `ink/pigment_table.py`,
      `ink/pigment_registry.py`.
- [x] `git mv ink/pigment.py ink/compositing.py`; every importer repointed; no shim.
- [x] The four tables (moved to `pigment_table.py`, exported from `pyntpot.ink`) and the
      two map defaults built from the registry, in today's order; `pigment()` delegates a
      name to `PigmentRegistry.get`, the one miss message.
- [x] `Colour.parse(text: str)` annotated `str` (not `object`, which
      `test_public_signatures` refuses) and raises `ValueError` for any non-`str`; the
      `5` and `None` cases carry `# ty: ignore[invalid-argument-type]`; alias names drawn
      with `fullmatch=True`.
- [x] `theme_dump._plain` writes a `str` subclass as `str`, so the theme-merge property
      dumps `Colour` values.
- [x] Exports, `test_public_api.py`, `docs/reference/ink.md`; `test_pigment.py` pins
      unchanged; grid `check`; slice gate green.

## S2: The catalogues as typed tables (#71)

- [x] Red: read-only tables, `brush_ids()`, nearest-id messages (ink in `test_brush.py`;
      theme in `tests/unit/maps/test_theme_brush_ids.py`, new). Two rows of
      `test_theme_check.py` rewritten in place: :177-179 to "'LAN9-z' is not a brush on
      the sheet; did you mean LAN8-a?" and :182-183 to "'MAJ9-a' is not a brush on the
      sheet; did you mean MAJ8-a?" (`nearest` returns one name, `n=1`).
- [x] `MappingProxyType` tables, `brush_ids`, the suggestion; slice gate green.

## S3a: `Colour` across every field

- [x] Red: a hex-defaulted field typed `str` fails; the schema three-branch guard;
      pigment names in a theme; the located miss; upper-case hex lower-cased; `Style()`
      builds.
- [x] Red: the coercion guard (`replace(...)` and `Style.model_validate` from a dict
      give a `Colour`); `test_one_hex_parser.py`. New cases go in
      `tests/unit/maps/{test_colour_fields,test_theme_scope,test_theme_colour_names}.py`
      (new), never in `test_style.py` (384 lines) or `test_theme_check.py` (361).
- [x] Rewritten in place, not deleted: `test_theme_schema.py:186-192` (three-branch
      node), `test_theme_check.py:186-191` (`'red'` reads "is not a pigment or a colour
      alias"; `'#a8c28'` keeps "is not a # and six hexadecimal digits"),
      `test_theme_check.py:246-248` (`#C22050` stored as `#c22050`); `RESOLVED_SAMPLE` in
      `test_style.py` pins `Colour("#f3ead6")` and `Colour("#241c14")`, the
      `type(got) is type(value)` assertion kept.
- [x] Fields retyped; `normalise_colours` and the five `__post_init__` hooks; `Colour`'s
      pydantic hook; `with_route_ink`; `compose_steps._rgb` removed; `ink.rgb` shares
      the arithmetic.
- [x] Colour call sites wrapped in `Colour(...)` in the five grid scripts,
      `pigment_swatches.py` and `test_style.py`; `ty check` green over `examples` and
      `tests`.
- [x] `test_theme_merge._is_colour` by `isinstance(value, Colour)`.
- [x] `tests/unit/ink/test_style_colours.py` and `tests/unit/letters/test_style.py` cover
      `normalise_colours` and the `PaperStyle`, `WashStyle` and `NibStyle` hooks.
- [x] Pure move of `_Check` and its helpers (`_sheet_and_colour`, `_MESSAGES`, `_TABLE`,
      `_COLOUR`, `_Path` included) to `theme_checker.py`, its own commit.
- [x] `theme_scope.py` in its full shape (`Bound`, the four mappings with `aliases:
      Mapping[str, Bound[Pigment]]` and `palette: Bound[object] | None`, cached
      `registry`, `resolve_pigment` and `resolve_colour` order); the `theme_checker`
      adapter, context and messages (non-`str`: "{v!r} is not a string");
      `COLOUR_FIELDS` retired; `ALIAS_PATTERN = "^[a-z][a-z0-9]*(_[a-z0-9]+)*$"`.
- [x] Schema regenerated; pinned digests unchanged; grid `check`; slice gate green.
      S6's worktree is cut here.

## S3b: Aliases, theme pigments, palettes

- [x] Red: each refusal (chain, built-in name, missing `override`, unknown alias, bad
      `.gpl` row, a `.gpl` name that is no alias, two `.gpl` names with one alias, a
      palette alias clashing with an inherited one), inheritance across `extends`, the
      binding rule, a theme pigment with `base` and `colour` both, `Palette.registry_gpl`,
      the CLI exiting 2 before any fetch, `Palette.pigments` holding the aliased pigment
      (transparency included) and `.gpl` imports anonymous, the two properties (alias to a
      name yields its colour and transparency; `.gpl` round trip at the colour level).
- [x] `test_theme_schema.py`: the top-level order pinned, the `propertyNames` walk over
      the group subtrees only, the `colours` and `pigments` key-rule test.
- [x] `theme_pigments.py`, `theme_colours.py`, `theme_palette.py`,
      `theme_palette_gpl.py`, `palettes/plain.yaml`, in the wheel.
- [x] A chain whose read stops checks no file: red case in `test_theme_resolve.py` (a
      child with a bad field and an unbound alias, extending a missing file, reports
      only the missing-file problem); the `theme_resolve` docstring says so. A non-`str`
      `extends` ends the chain without stopping the read: red case (`extends: 5` with
      `card: {display_px: '5'}` reports both problems, the `extends` one at line 1).
- [x] `check_theme_scoped`; `theme_resolve` reads the chain then checks from the base up;
      `theme_scope.py` filled on S3a's shape, `palette` narrowed to `Bound[Palette] |
      None` under `TYPE_CHECKING` (runtime direction `theme_palette -> theme_colours ->
      theme_scope`); `Palette(name, pigments)`; the `colours` value schema is the
      three-branch `Colour` node or `{colour, override}`.
- [x] `Palette` exported and documented; schema tables; schema regenerated; slice gate
      green.

## S4: Effect value types and primitives (worktree cut after S3a)

- [ ] Red: `tests/unit/ink/test_effect_types.py` (defaults, `EFFECT_RANGES` pinned,
      ranges and `nan`/`inf` refused, `Casing(width_px=100.0)` accepted, the Payne's grey
      default, a `str` colour normalised); the property tests (fields drawn finite over
      `EFFECT_RANGES`, `threshold` from `floats(0.01, 1)`) and unit tests of `casing`,
      `glow`, `shadow` (its rounded offset included) and `pen_casing`; each refuses
      `threshold <= 0`; each `threshold` defaults to `LINE_THRESHOLD`.
- [ ] `ink/effect_types.py` (`Casing`, `Glow`, `Shadow`, `PenCasing`, `EFFECT_RANGES:
      Mapping[str, tuple[float, float]]` keyed by field name, `*_px` 0 to 16, `strength`
      0 to 1); `ink/effect_mask.py` (`LINE_THRESHOLD`, unexported) and the four
      `effect_*` modules, each primitive taking its value type and
      `threshold=LINE_THRESHOLD` (at most 6 parameters, no `# noqa: PLR0913`);
      docstrings to the `test_field_docs` and `test_public_signatures` standard; no
      export yet; slice gate green in the worktree.

## Merge gate A (after S3b, before S5a)

- [x] S4 merged; eight names (`casing`, `glow`, `shadow`, `pen_casing`, `Casing`, `Glow`,
      `Shadow`, `PenCasing`) exported in `ink`, `ink.md` and `INK_PUBLIC`; slice gate
      green.

## S5a: The model, presets, theme fields

- [x] Red: `test_line_effects.py` (at most one of a kind, off dropped, `LINE_CLASSES`),
      `test_theme_effects.py` (out-of-range and non-finite located; a child that sets
      only `major` keeps its parent's route stack; a child's `major: {}` turns off its
      parent's `cased`; the `LOADER_FIELDS` messages), `test_digest_omits.py`, the
      extended schema guard, a `BasemapStyle` key outside the seven classes refused, the
      two properties.
- [x] Pinned field tables: `test_style_groups.py` (`PINNED` rows gain `line_effects` and
      `effects`; the digest test drops `LOADER_FIELDS` before hashing, so every `SOURCED`
      pin holds; the two default asserts), `BASEMAP_DEFAULTS` and its test moved to
      `tests/unit/maps/test_basemap_defaults.py` (new) with `"line_effects": {}`, and
      `tests/unit/maps/candidates/test_export.py` gaining `"line_effects": {}`.
- [x] `test_theme_schema.py` (top-level order with `effect_presets` and `line_effects`;
      key rules; field test leaves out `LOADER_FIELDS`) and `test_theme_vocab.py` (both
      dict-field tests leave out `LOADER_FIELDS`; no `VOCABULARIES` entry for
      `basemap.line_effects`).
- [x] `maps/line_effects.py` (`EffectStack` and the `BasemapStyle` key helper, on `ink`'s
      `Casing`, `Glow` and `Shadow`, and `EFFECT_RANGES` from `pyntpot.ink.effect_types`),
      `maps/theme_effects.py` (the same import; the split adds only the entries the file
      writes), the two group fields, `BasemapStyle.__post_init__`,
      `DIGEST_OMITS_AT_DEFAULT`, `LOADER_FIELDS` (taken out in `check_theme_scoped`
      before the group check), the dispatch, presets in `theme_scope.py`.
- [x] The prescribed `line_effects` and `effect_presets` schema shape; `style-fields.md`
      rows for `basemap.line_effects` and `route_ink.effects`; `_BASE` in
      `test_theme_merge.py` without the loader-only fields; `line_effects.py` in the
      theme import guard.
- [x] `EffectStack` exported and in `maps.md`; schema regenerated; every pinned digest
      unchanged; slice gate green.

## S5b: Painter and compose wiring

- [x] Red: locality of a road casing (exact with `km_glazing=True`, within 1e-6 in
      multiply mode) and a route casing; mask pads only when a water
      effect is set; the default path untouched; the shadow takes the hillshade azimuth.
- [x] `effect_pass.py` (`lay_stack` scales each `*_px` by `dataclasses.replace` and
      passes each effect whole, `threshold` left at its default), `painter/effects.py`
      (`lay_wash(job, ground, under, groups)`), `pen_groups`, the `_wash_plate` branch,
      `route_effects.py` (`LINE_THRESHOLD` from `pyntpot.ink.effect_mask`), the `compose_steps.route` branch and its docstring.
- [x] `GOLDEN_HASH` and the route-ink pins unchanged; slice gate green.

## S6: The grid helper (#170; worktree)

- [x] Red: `boxes()` literals for the five layouts, taken from the old code before any
      edit; the guard that no grid script calls `.convert("RGBa")`.
- [x] `examples/labelled_grid.py`: `GridSpec`, `LabelStyle`, `letter_over(img, settings,
      nib, *, gran_px, seed, ground=None)` (the one round trip) and `label_grid(img,
      boxes, columns, rows, style, *, extra=())`, each at most 6 parameters.
- [x] `tutorial_grids.py` keeps `_layout`, `_labels` and `_letter` with today's
      signatures as one-line delegates; its seven quoted grid functions byte-identical, so
      `test_tutorial_quotes.py` passes and `paint-a-watercolour.md` is not edited. The
      other scripts' `_letter` / `_lettered` call `letter_over`; label tuples, names and
      `BRUSH_IDS` stay literals.
- [x] `support.examples.load_example` (puts `EXAMPLES_DIR` on `sys.path` for the call);
      `run_example` uses it; `test_reference_pages.py`'s
      `test_sheet_script_lists_exactly_the_table_ids` loads `brush_sheet.py` through it,
      and the file drops its `import runpy`;
      the `test_examples.py` sibling allowance; `"examples"` added to
      `[tool.ty.environment] root` in `pyproject.toml`, so `ty` types the sibling's
      names (an unresolved import only warns).
- [x] Grid `check`; golden docs subset; slice gate green.

## Merge gate B

- [x] S6 merged; slice gate, grid `check` and golden docs subset green on the merged tree.

## Before S7

- [x] Apply the user's ruling on the "effect" trap in `CONTRIBUTING.md`, if given, before
      S7 (no ruling given; files untouched). Until then S4 and S5a proceed, using "line effect", "casing", "glow",
      "shadow", "effect stack" and "effect preset" only as glossary terms; no slice edits
      `CLAUDE.md` or `CONTRIBUTING.md`.

## S7: Docs and notes

- [x] `write-a-theme.md` (colours, aliases, palettes, theme pigments, binding down
      `extends`); the `pigments.md` Colour Index column and its comparator; the colour
      rows' text in `style-fields.md`.
- [x] Glossary: the "colour alias" entry says an alias stands for a pigment (a named one,
      or a hex's anonymous pigment, transparency included), not "a pigment name or a
      hex"; code columns; `PYTHONPATH=tests uv run python -m support.glossary`.
- [x] Notes for #72, #71 and #170 deleted, links repointed; route casing, glow and shadow
      notes updated.
- [x] `docs/features/maps-bridges-over-water.md` and `docs/features/maps-water-lining.md`
      cite ADR 0070, linked, in place of "not yet in `docs/decisions/`".
- [x] `docs/features/ink-stroke-density-profile.md:8` cites `ink/compositing.py`, not
      `ink/pigment.py`.
- [x] The em and en dash grep is empty; slice gate green.

## S8: Mutation testing

- [ ] Changed `ink` and `letters` functions (the `PaperStyle`, `WashStyle` and
      `NibStyle` hooks and `normalise_colours` included) run with
      `tests/mutation/scope.py` (moved
      `compositing.py` functions dropped, with the reason); survivors killed or recorded
      as equivalent in `mutation.md`.

## S9: Final review and PR

- [ ] Full golden suite with no regeneration; grid `check`; slice gate; no change to
      `[tool.importlinter]`.
- [ ] Fresh-context diff review against the plan; elegance pass; every acceptance
      criterion ticked against evidence.
- [ ] PR opened with the spec's title and Changelog (the typed-caller `Colour(...)` line
      included): `Closes #72` (#72), `Closes #71`
      (#71), `Closes #170` (#170); mutation equivalents; "no image moved" with the grid
      log.
