# 009 — tasks

Slices and files are in `plan.md`. Order: S0; then S1, S2, S3a, S3b, S5a in turn, with S4
in a parallel worktree cut after S0 and S6 in one cut after S3a; merge gate A; S5b; merge
gate B; S7, S8, S9.

## Start

- [ ] Comment the branch and spec `009` on #72, #71 and #170. Name #104, #105 and #106 as
      generalised, closing in `009a`.
- [x] ADR 0070 amended to match the plan (review finding 15): two converters, the
      three-branch schema, the glow floor, the loader-only fields and their schema
      shape and ranges, binding down `extends`, off dropped after the final merge, the
      public names and the module rename.
- [ ] The plan-reviewer passes the revised plan.

## S0: Baseline

- [ ] `tests/golden/grid_hashes.py` (`record` and `check`, file and pixel sha256 per
      entry of the five grid scripts); `make_docs_images.fixture_options` made public.
- [ ] On the untouched base: `PYTHONPATH=tests uv run python tests/golden/grid_hashes.py record specs/009-line-effects-and-registry/grid-hashes.json`, committed alone.
- [ ] `check` passes; slice gate green.

## S1: The registry (#72)

- [ ] Red: `test_colour.py`, `test_pigment_registry.py`, `test_one_registry.py`, the
      property tests, and the maps default ties.
- [ ] `ink/colour.py`, `ink/naming.py`, `ink/pigment_table.py`,
      `ink/pigment_registry.py`.
- [ ] `git mv ink/pigment.py ink/compositing.py`; every importer repointed; no shim.
- [ ] The four tables (moved to `pigment_table.py`, exported from `pyntpot.ink`) and the
      two map defaults built from the registry, in today's order; `pigment()` delegates a
      name to `PigmentRegistry.get`, the one miss message.
- [ ] `Colour.parse` raises `ValueError` for any non-`str`; alias names drawn with
      `fullmatch=True`.
- [ ] `theme_dump._plain` writes a `str` subclass as `str`, so the theme-merge property
      dumps `Colour` values.
- [ ] Exports, `test_public_api.py`, `docs/reference/ink.md`; `test_pigment.py` pins
      unchanged; grid `check`; slice gate green.

## S2: The catalogues as typed tables (#71)

- [ ] Red: read-only tables, `brush_ids()`, nearest-id messages (ink and theme).
- [ ] `MappingProxyType` tables, `brush_ids`, the suggestion; slice gate green.

## S3a: `Colour` across every field

- [ ] Red: a hex-defaulted field typed `str` fails; the schema three-branch guard;
      pigment names in a theme; the located miss; upper-case hex lower-cased; `Style()`
      builds.
- [ ] Red: the coercion guard (`replace(...)` and `Style.model_validate` from a dict
      give a `Colour`); `test_one_hex_parser.py`.
- [ ] Fields retyped; `normalise_colours` and the five `__post_init__` hooks; `Colour`'s
      pydantic hook; `with_route_ink`; `compose_steps._rgb` removed; `ink.rgb` shares
      the arithmetic.
- [ ] Colour call sites wrapped in `Colour(...)` in the five grid scripts,
      `pigment_swatches.py` and `test_style.py`; `ty check` green over `examples` and
      `tests`.
- [ ] `test_theme_merge._is_colour` by `isinstance(value, Colour)`.
- [ ] `tests/unit/ink/test_style_colours.py` and `tests/unit/letters/test_style.py` cover
      `normalise_colours` and the `PaperStyle`, `WashStyle` and `NibStyle` hooks.
- [ ] Pure move of `_Check` and its helpers (`_sheet_and_colour`, `_MESSAGES`, `_TABLE`,
      `_COLOUR`, `_Path` included) to `theme_checker.py`, its own commit.
- [ ] `theme_scope.py` in its full shape (`Bound`, the four mappings, cached `registry`,
      `resolve_colour` order); the `theme_checker` adapter, context and messages;
      `COLOUR_FIELDS` retired; `ALIAS_PATTERN = "^[a-z][a-z0-9]*(_[a-z0-9]+)*$"`.
- [ ] Schema regenerated; pinned digests unchanged; grid `check`; slice gate green.
      S6's worktree is cut here.

## S3b: Aliases, theme pigments, palettes

- [ ] Red: each refusal (chain, built-in name, missing `override`, unknown alias, bad
      `.gpl` row, a `.gpl` name that is no alias, two `.gpl` names with one alias, a
      palette alias clashing with an inherited one), inheritance across `extends`, the
      binding rule, a theme pigment with `base` and `colour` both, `Palette.registry_gpl`,
      the CLI exiting 2 before any fetch, the two properties.
- [ ] `test_theme_schema.py`: the top-level order pinned, the `propertyNames` walk over
      the group subtrees only, the `colours` and `pigments` key-rule test.
- [ ] `theme_pigments.py`, `theme_colours.py`, `theme_palette.py`,
      `theme_palette_gpl.py`, `palettes/plain.yaml`, in the wheel.
- [ ] `check_theme_scoped`; `theme_resolve` reads the chain then checks from the base up;
      `theme_scope.py` filled on S3a's shape.
- [ ] `Palette` exported and documented; schema tables; schema regenerated; slice gate
      green.

## S4: Effect primitives (worktree)

- [ ] Red: the property tests and unit tests of `casing`, `glow`, `shadow` (its rounded
      offset included) and `pen_casing`; each refuses `threshold <= 0`.
- [ ] `ink/effect_mask.py` and the four `effect_*` modules; no export yet; slice gate green
      in the worktree.

## S5a: The model, presets, theme fields

- [ ] Red: `test_line_effects.py` (ranges, off dropped, the Payne's grey default),
      `test_theme_effects.py` (out-of-range located; a child's `major: {}` turns off its
      parent's `cased`; the `LOADER_FIELDS` messages), `test_digest_omits.py`, the
      extended schema guard, a `BasemapStyle` key outside the seven classes refused, the
      two properties.
- [ ] `test_theme_schema.py` (top-level order with `effect_presets` and `line_effects`;
      key rules; field test leaves out `LOADER_FIELDS`) and `test_theme_vocab.py` (both
      dict-field tests leave out `LOADER_FIELDS`; no `VOCABULARIES` entry for
      `basemap.line_effects`).
- [ ] `maps/line_effects.py` (`EFFECT_RANGES`, the `__post_init__` hooks),
      `maps/theme_effects.py`, the two group fields, `BasemapStyle.__post_init__`,
      `DIGEST_OMITS_AT_DEFAULT`, `LOADER_FIELDS` (taken out in `check_theme_scoped`
      before the group check), the dispatch, presets in `theme_scope.py`.
- [ ] The prescribed `line_effects` and `effect_presets` schema shape; `style-fields.md`
      rows for `basemap.line_effects` and `route_ink.effects`; `_BASE` in
      `test_theme_merge.py` without the loader-only fields; `line_effects.py` in the
      theme import guard.
- [ ] Exports and `maps.md`; schema regenerated; every pinned digest unchanged; slice gate
      green.

## Merge gate A

- [ ] S4 merged; four names exported in `ink`, `ink.md` and `INK_PUBLIC`; slice gate green.

## S5b: Painter and compose wiring

- [ ] Red: locality of a road casing (exact with `km_glazing=True`, within 1e-6 in
      multiply mode) and a route casing; mask pads only when a water
      effect is set; the default path untouched; the shadow takes the hillshade azimuth.
- [ ] `effect_pass.py`, `painter/effects.py`, `pen_groups`, the `_wash_plate` branch,
      `route_effects.py`, the `compose_steps.route` branch and its docstring.
- [ ] `GOLDEN_HASH` and the route-ink pins unchanged; slice gate green.

## S6: The grid helper (#170; worktree)

- [ ] Red: `boxes()` literals for the five layouts, taken from the old code before any
      edit; the guard that no grid script calls `.convert("RGBa")`.
- [ ] `examples/labelled_grid.py`; the five scripts moved onto it; `run_example`
      `sys.path`; the `test_examples.py` sibling allowance; `"examples"` added to
      `[tool.ty.environment] root` in `pyproject.toml`.
- [ ] Grid `check`; golden docs subset; slice gate green.

## Merge gate B

- [ ] S6 merged; slice gate, grid `check` and golden docs subset green on the merged tree.

## Before S7

- [ ] Apply the user's ruling on the "effect" trap in `CONTRIBUTING.md`, if given, before
      S7. Until then S4 and S5a proceed, using "line effect", "casing", "glow",
      "shadow", "effect stack" and "effect preset" only as glossary terms; no slice edits
      `CLAUDE.md` or `CONTRIBUTING.md`.

## S7: Docs and notes

- [ ] `write-a-theme.md` (colours, aliases, palettes, theme pigments, binding down
      `extends`); the `pigments.md` Colour Index column and its comparator; the colour
      rows' text in `style-fields.md`.
- [ ] Glossary code columns; `PYTHONPATH=tests uv run python -m support.glossary`.
- [ ] Notes for #72, #71 and #170 deleted, links repointed; route casing, glow and shadow
      notes updated.
- [ ] `docs/features/maps-bridges-over-water.md` and `docs/features/maps-water-lining.md`
      cite ADR 0070, linked, in place of "not yet in `docs/decisions/`".
- [ ] `docs/features/ink-stroke-density-profile.md:8` cites `ink/compositing.py`, not
      `ink/pigment.py`.
- [ ] The em and en dash grep is empty; slice gate green.

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
