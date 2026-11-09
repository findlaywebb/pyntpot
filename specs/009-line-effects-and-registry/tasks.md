# 009 — tasks

Slices and files are in `plan.md`. Order: S0; then S1, S2, S3a, S3b, S5a in turn, with S4
and S6 in parallel worktrees cut after S0; merge gate A; S5b; merge gate B; S7, S8, S9.

## Start

- [ ] Comment the branch and spec `009` on #72, #71 and #170. Name #104, #105 and #106 as
      generalised, closing in `009a`.
- [ ] The plan-reviewer passes the plan.

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
- [ ] The four tables and the two map defaults built from the registry, in today's order.
- [ ] Exports, `test_public_api.py`, `docs/reference/ink.md`; `test_pigment.py` pins
      unchanged; grid `check`; slice gate green.

## S2: The catalogues as typed tables (#71)

- [ ] Red: read-only tables, `brush_ids()`, nearest-id messages (ink and theme).
- [ ] `MappingProxyType` tables, `brush_ids`, the suggestion; slice gate green.

## S3a: `Colour` across every field

- [ ] Red: a hex-defaulted field typed `str` fails; the schema three-branch guard;
      pigment names in a theme; the located miss; upper-case hex lower-cased; `Style()`
      builds.
- [ ] Fields retyped; `Style` config; `with_route_ink`; `compose_steps._rgb` removed;
      `ink.rgb` shares the arithmetic.
- [ ] `theme_scope.py`; the `theme_check` adapter, context and messages; `COLOUR_FIELDS`
      retired; `ALIAS_PATTERN`.
- [ ] Schema regenerated; pinned digests unchanged; grid `check`; slice gate green.

## S3b: Aliases, theme pigments, palettes

- [ ] Red: each refusal (chain, built-in name, missing `override`, unknown alias, bad
      `.gpl` row), inheritance across `extends`, the CLI exiting 2 before any fetch, the
      two properties.
- [ ] `theme_pigments.py`, `theme_colours.py`, `palette.py`, `palette_gpl.py`,
      `palettes/plain.yaml`, in the wheel.
- [ ] `check_theme_scoped`; `theme_resolve` reads the chain then checks from the base up.
- [ ] `Palette` exported and documented; schema tables; schema regenerated; slice gate
      green.

## S4: Effect primitives (worktree)

- [ ] Red: the property tests and unit tests of `casing`, `glow`, `shadow` and
      `pen_casing`.
- [ ] `ink/effect_mask.py` and the four `effect_*` modules; no export yet; slice gate green
      in the worktree.

## S5a: The model, presets, theme fields

- [ ] Red: `test_line_effects.py`, `test_theme_effects.py`, `test_digest_omits.py`, the
      two properties.
- [ ] `maps/line_effects.py`, `maps/theme_effects.py`, the two group fields,
      `DIGEST_OMITS_AT_DEFAULT`, `LOADER_FIELDS`, the dispatch.
- [ ] Exports and `maps.md`; schema regenerated; every pinned digest unchanged; slice gate
      green.

## Merge gate A

- [ ] S4 merged; four names exported in `ink`, `ink.md` and `INK_PUBLIC`; slice gate green.

## S5b: Painter and compose wiring

- [ ] Red: locality of a road casing and a route casing; mask pads only when a water
      effect is set; the default path untouched; the shadow takes the hillshade azimuth.
- [ ] `effect_pass.py`, `painter/effects.py`, `pen_groups`, the `_wash_plate` branch,
      `route_effects.py`, the `compose_steps.route` branch and its docstring.
- [ ] `GOLDEN_HASH` and the route-ink pins unchanged; slice gate green.

## S6: The grid helper (#170; worktree)

- [ ] Red: `boxes()` literals for the five layouts, taken from the old code before any
      edit.
- [ ] `examples/labelled_grid.py`; the five scripts moved onto it; `run_example`
      `sys.path`; the `test_examples.py` sibling allowance.
- [ ] Grid `check`; golden docs subset; slice gate green.

## Merge gate B

- [ ] S6 merged; slice gate, grid `check` and golden docs subset green on the merged tree.

## S7: Docs and notes

- [ ] `write-a-theme.md` (colours, aliases, palettes, theme pigments); the `pigments.md`
      Colour Index column and its comparator; `style-fields.md` if needed.
- [ ] Glossary code columns; `PYTHONPATH=tests uv run python -m support.glossary`.
- [ ] Notes for #72, #71 and #170 deleted, links repointed; route casing, glow and shadow
      notes updated.
- [ ] `docs/features/maps-bridges-over-water.md` and `docs/features/maps-water-lining.md`
      cite ADR 0070, linked, in place of "not yet in `docs/decisions/`".
- [ ] ADR 0070 "Public names" names the concrete names; the em and en dash grep is empty;
      slice gate green.

## S8: Mutation testing

- [ ] Changed `ink` functions run with `tests/mutation/scope.py` (moved
      `compositing.py` functions dropped, with the reason); survivors killed or recorded
      as equivalent in `mutation.md`.

## S9: Final review and PR

- [ ] Full golden suite with no regeneration; grid `check`; slice gate; no change to
      `[tool.importlinter]`.
- [ ] Fresh-context diff review against the plan; elegance pass; every acceptance
      criterion ticked against evidence.
- [ ] PR opened with the spec's title and Changelog: `Closes #72` (#72), `Closes #71`
      (#71), `Closes #170` (#170); mutation equivalents; "no image moved" with the grid
      log.
