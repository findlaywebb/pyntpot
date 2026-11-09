# 009 — Line effects and one pigment registry (PR 1)

GitHub issues: [#72](https://github.com/findlaywebb/pyntpot/issues/72) (one pigment
registry), [#71](https://github.com/findlaywebb/pyntpot/issues/71) (brushes and pigments
declared as data), [#170](https://github.com/findlaywebb/pyntpot/issues/170) (one
labelled-grid helper). This PR closes those three. It generalises #104, #105 and #106
(route casing, glow and shadow), which close in PR 2.

Decision record: ADR 0070 (`docs/decisions/0070-line-effects-and-one-pigment-registry.md`),
rules 1 to 16. Evidence: `research.md` in this directory. PR 2 is the stacked
`specs/009a-*`: #159, retiring `paper.pigment_transparency` (ADR 0070 rule 17), #67, #69,
#70, every figure and docs image, and any bundled theme that adopts an effect.

## Problem

The map paints from silent copies of the pigment tables. `CoverStyle.pigments` copies
`PIGMENTS` and `PaperStyle.pigment_transparency` copies `TRANSPARENCY`, and no test ties
either copy to its table. The ten painter's pigments form a second namespace that no theme
can name, and a misspelt pigment or brush id fails with no suggestion. A theme colour is an
untyped hex string. The colour fields are listed twice (`COLOUR_FIELDS`), `#C22050` and
`#c22050` hash differently, and two functions turn hex into RGB. Nothing draws a casing,
a glow or a shadow on any line. Five docs scripts each carry their own copy of the grid
layout and label code.

## Acceptance criteria

### One pigment registry (#72)

- [ ] `pyntpot.ink` exports `Pigment`, `PigmentRegistry`, `PIGMENT_REGISTRY` and
      `pigment`. `PIGMENT_REGISTRY` holds today's 15 role pigments and 10 painter's
      pigments under their current names, each a frozen
      `Pigment(name, colour, transparency, colour_index)`. Each entry equals a pinned
      literal: role pigments carry `colour_index=None`; the painter's pigments carry
      `PB29`, `PB35`, `PBr7`, `PBr7`, `PY43`, `None`, `None`, `PR179`, `PV19`, `None`, in
      `PAINTERS_PIGMENTS` order.
- [ ] `pigment(ref)` returns a `Pigment` given as itself. Given a canonical name, it
      returns the registry entry. Given a `#rrggbb`, it returns an anonymous pigment whose
      name is the hex, with `transparency=None`. Anything else raises `ValueError` naming
      the nearest names (`difflib`). It is the one documented lookup; a name goes on to
      `PigmentRegistry.get`, the one place the miss message is written.
- [ ] `PigmentRegistry.extended(pigments)` returns a new registry and never changes the
      one it was called on. A name that equals a built-in raises `ValueError`, and the
      message points at the derived form (`base: <name>`).
- [ ] `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` are
      built from the registry and still equal their pinned literals
      (`tests/unit/ink/test_pigment.py`). They live in `ink/pigment_table.py` and stay
      exported from `pyntpot.ink`. The defaults of `CoverStyle().pigments` and
      `PaperStyle().pigment_transparency` are built from the registry, in today's key
      order, and a test ties each to it. No public name is removed or renamed.
- [ ] Each built-in pigment's hex appears as a string literal in exactly one module under
      `src/`, `ink/pigment_table.py`, so no silent copy can come back
      (`tests/architecture/test_one_registry.py`).

### The catalogues as typed Python tables (#71)

- [ ] `BRUSH_TREATMENTS`, `PEN_ROWS` and `BRUSH_COLOURS` are typed and read-only: an
      assignment into them raises `TypeError`. Their values equal pinned literals.
- [ ] `brush_from_id` with an unknown id raises `ValueError` naming the nearest brush id.
      The theme checker's brush message names it too.
- [ ] `ink` reads no data file, and the import contracts in `pyproject.toml` are
      unchanged.

### One `Colour` type across every colour field

- [ ] `pyntpot.ink.Colour` is a frozen `str` subclass that holds a lower-case `#rrggbb`.
      It has `Colour.parse(text)` (strict: `#` and six hexadecimal digits in either case,
      lower-cased; no `#abc`, no CSS names; a non-`str` raises `ValueError`), `.rgb`
      (bit-identical to `ink.rgb` for every hex: a Hypothesis property) and `.rgb8`. It
      survives `==`, `json.dumps`, `dataclasses.asdict`, `copy.deepcopy` and pickling as
      the same string.
- [ ] Every colour field of every style group is typed `Colour`: `paper.paper_hex`,
      `wash.separation_pigments.*`, the four `nib` inks, `cover.pigments.*`,
      `route_ink.colour`, and the new effect colours. `COLOUR_FIELDS` is gone. A test fails
      when a field whose default is a `#rrggbb` is not typed `Colour`.
- [ ] A plain `str` reaching a colour field at runtime is normalised: each group with a
      `Colour` field parses it in `__post_init__`, so
      `replace(RouteInkStyle(), colour="#ABCDEF").colour` is a `Colour` equal to
      `"#abcdef"`, and `Style.model_validate({"route_ink": {"colour": "#c22050"}})` still
      builds (through `Colour`'s own pydantic hook, which imports no pydantic). Every
      typed call site in `examples/` and `tests/` wraps its literal in `Colour(...)`, and
      `ty` is green.
- [ ] `compose_steps._rgb` is gone (it now uses `Colour.rgb8`). `ink.rgb` stays public, its
      behaviour unchanged, and shares `Colour`'s channel arithmetic. An architecture test
      fails when any `src` module but `ink/colour.py` parses hex.
- [ ] Every theme colour field takes a `#rrggbb`, a pigment name, or an alias. Names and
      aliases resolve to hex at load, so every packaged and example theme keeps its three
      pinned digests.
- [ ] The schema gives every `Colour` field
      `anyOf: [{enum: registry names}, {pattern: hex}, {pattern: alias}]`, and a test
      walks the model to find every `Colour`-typed field and checks its schema node.

### Aliases, theme pigments and palettes

- [ ] A theme's top-level `colours:` maps an alias to a pigment name or a hex, or to
      `{colour: ..., override: true}`. An alias that names another alias, equals a pigment
      name, or replaces an inherited or palette alias without `override` is a located
      error.
- [ ] A theme's top-level `pigments:` adds pigments
      (`{base, colour, transparency, colour_index}`, with `base`, `colour` or both; a field
      given overrides the base's) that its colour fields may name. A
      name equal to a built-in is refused, and the message points at
      `<new name>: {base: <built-in>}`. In PR 1, a theme pigment's transparency is recorded
      and not used (rule 17 is PR 2).
- [ ] A theme's top-level `palette:` takes a packaged palette name, or a `.yaml` or
      `.gpl` path relative to the theme file. The package ships the palette `plain`.
      `pyntpot.maps.Palette` reads a palette by name or path, lists the packaged names,
      imports a GIMP `.gpl`, and exports itself (`to_gpl`) or the registry
      (`Palette.registry_gpl`) as `.gpl`. A `.gpl` row with no name, a name that does not
      normalise to an alias, two rows that normalise to one alias, or a built-in pigment's
      name is a located error.
- [ ] Aliases, theme pigments, the palette and theme presets are inherited down an
      `extends` chain, by ADR 0070 rule 7: aliases, pigments and presets accumulate; the
      nearest `palette:` is the one in effect; a name binds in the file where it is
      written, so a child that rebinds an alias does not recolour a field its parent set
      (pinned by a test).
- [ ] Every unknown pigment, alias, palette, brush id, line class, effect key, effect
      field or preset fails at theme load, before any fetch. Each message names the file,
      the dotted key path, the line, and the nearest valid name. A CLI test shows exit 2
      with no request made.

### Line-effect primitives in `ink`

- [ ] `pyntpot.ink` exports `casing`, `glow`, `shadow` and `pen_casing`. Each is a pure
      function of float32 RGB and a float mask. None knows of maps, and none draws a random
      number.
- [ ] Each refuses a threshold at or below 0 with `ValueError`.
- [ ] Hypothesis properties, on arrays before any dither or encode: a casing of width 0
      is the identity, bit for bit; a glow never darkens a pixel; a shadow never paints
      over its casting line (where the mask is at or above the threshold, the output
      equals the input bit for bit); a pen casing of width 0 is the identity, and inside
      its reserve the output is the paper.

### The line-effect model, presets and theme fields (all off)

- [ ] `pyntpot.maps` exports `Casing`, `Glow`, `Shadow` and `EffectStack`. An
      `EffectStack` holds at most one of each kind, in order.
- [ ] A theme's top-level `line_effects:` is keyed by `major`, `medium`, `minor`,
      `coast`, `road_major`, `lane`, `track` and `route`. Each value is a preset name or a
      stack (a mapping whose keys are `casing`, `glow` and `shadow`, applied in key
      order), never a mix of the two. The built-in presets are `cased`, `halo` and
      `lifted`. A theme's `effect_presets:` may add presets but may not reuse a built-in
      preset name.
- [ ] At load, `line_effects` is split: the seven basemap classes go to
      `basemap.line_effects` (read by the painter, so `base_digest` moves) and `route`
      goes to `route_ink.effects` (read at compose, so `digest()` moves). Off effects and
      empty stacks are dropped once, after the final merge, so a child that writes
      `major: {}` turns off its parent's `major` stack. Neither field can be set inside
      its group in a theme. `BasemapStyle` refuses a `line_effects` key outside the seven
      basemap classes, and at load such a key is a located error.
- [ ] A negative width, spread, blur or offset, or a strength outside 0 to 1, is a located
      error at load, never clipped; the effect types refuse the same values.
- [ ] Hypothesis: expanding a preset gives the same style and the same digests as
      writing out the stack it names; empty or off `line_effects` leaves every digest of
      every packaged and example theme unchanged.
- [ ] `line_effects` and `effects` are named in `DIGEST_OMITS_AT_DEFAULT`, and every name
      there matches exactly one field across all groups (test). Every new field at its
      default leaves `digest()`, `base_digest()` and `lettering_digest()` of every packaged
      and example theme at its pinned value.
- [ ] Once set, basemap effects paint between the water pad and the road pads in the
      group order of ADR 0070 rule 10. Route effects paint at compose under the route,
      from the route's one merged mask, and never into `pen.webp`. With no effect set,
      the painter's `over` list and the compose code path are today's, unchanged. The
      lettering and leaders take no effect.

### The labelled-grid helper (#170)

- [ ] `examples/labelled_grid.py` (private: in no `__all__`) holds the grid layout
      (`GridSpec.boxes()`) and the one copy of the label round trip (`label_grid`). The
      five grid scripts use it.
- [ ] The sha256 of every full-size image the five scripts write, recorded on the branch
      base, is unchanged (`tests/golden/grid_hashes.py check`). `GridSpec.boxes()` equals
      the literal boxes of the old layout code for all five layouts.

### Whole feature

- [ ] No pinned image, docs image, master, golden or digest moves. The golden suite and
      the golden docs tests pass with no regeneration, and `GOLDEN_HASH`, `BASE_DIGEST`,
      `DIGEST`, `LETTERING_DIGEST` and every theme's digests are unchanged.
- [ ] Both committed `theme.schema.json` copies are regenerated and checked.
- [ ] Mutation testing has run on the changed `ink` functions. Each survivor is killed or
      named as equivalent, with its reason (`mutation.md`, PR description).
- [ ] No file under `src/` is over 400 lines; no mocking; logging only. Gates green:
      `uv run pytest -n auto --dist loadgroup`, `uv run ruff check .`, `uv run ty check`,
      `uv run lint-imports`, `prek run --all-files`, and the golden suite.
- [ ] `docs/features/maps-bridges-over-water.md` and `docs/features/maps-water-lining.md`
      cite ADR 0070 as written. The notes for #72, #71 and #170 are deleted and their
      links repointed.
- [ ] The PR body says `Closes #72`, `Closes #71` and `Closes #170`.

## Changelog

PR title (no `!`: no public name is removed or renamed, and a `str` passed to a colour
field still works at runtime):

```
feat(ink): one pigment registry, a Colour type for every colour field, and line effects off by default
```

Under "Changelog" in the PR description:

```
feat(ink): Pigment, PigmentRegistry, PIGMENT_REGISTRY and pigment(): one registry of the 25 built-in pigments, with the nearest names suggested on a miss
feat(ink): Colour, a lower-case #rrggbb value type, now the type of every colour field
feat(ink): casing, glow, shadow and pen_casing, line-effect primitives laid on RGB
feat(ink): brush_from_id suggests the nearest brush id on a miss
feat(maps): a theme colour may be a pigment name, or an alias from the theme's colours table or its palette
feat(maps): a theme may add pigments in a pigments table; a built-in pigment's name is refused
feat(maps): palettes, chosen by name or path and read from or written to GIMP .gpl files (Palette)
feat(maps): line_effects and effect_presets theme tables: a casing, glow or shadow per line class and for the route, with the presets cased, halo and lifted, all off by default
fix(maps): a theme's upper-case hex colour is stored in lower case, so it hashes as its lower-case form
refactor(ink): every colour field is typed Colour; a typed caller now passes Colour("#rrggbb") where it passed a str, and a str still works at runtime
```

## Out of scope

- #159 (`with_route_ink` also sets `nib.label_route_ink`), ADR 0070 rule 17 (a pigment
  carries its own transparency; `paper.pigment_transparency` retired), #67, #69, #70: PR 2.
- Every figure, gallery and docs image, and any bundled or example theme adopting an
  effect, a name or an alias: PR 2.
- Pen casing in the theme model: PR 1 ships the primitive only.
- Effects on lettering or leaders: refused by design (`letters/nib.py`).
- Theme-declared brushes; rewriting `examples/` onto `pigment()`; bridges (#209) and
  water-lining (#210).
