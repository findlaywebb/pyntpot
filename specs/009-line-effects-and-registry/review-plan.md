# 009 plan review (PR 1)

Reviewer: fresh-context plan reviewer. Measured on `e5578fe` (branch `claude/quirky-hypatia-z2pii3`).

## Verdict: BLOCK

The layering, slice order and purity proof are sound. Six findings would make an agent fail a
gate or ship wrong behaviour if it followed the plan as written. The most important change:
**retyping the fields to `Colour` is not a local change.** ty gates `examples/` and `tests/`,
plain `str` values still reach the fields at runtime, and two test-support files that no slice
owns break. S3a must own every site, S6 must be cut after S3a, and the plan must pick one
coercion rule.

## Answers to the eight flagged contradictions

1. **Rename `ink/pigment.py` to `ink/compositing.py`.** Sound. It needs no `!` and no edit to
   ADR 0070. ADR 0068 says "A module path is not part of the API ... may move without an ADR",
   and `stamp`/`wash` were renamed the same way (0068, "Module renames"). The module is only
   reachable as `pyntpot.ink.pigment` by deep import, and `docs/reference/*.md` uses no deep
   path (`test_site.py`). One gap: see finding 11.
2. **`arbitrary_types_allowed` and validation context.** Required. I checked it: with pydantic
   2.14.2, a `str`-subclass field in a stdlib dataclass raises `PydanticSchemaGenerationError`
   without it. But the plan does not own what it costs (finding 2).
3. **A third identifier branch in the schema.** Sound. The schema is static and cannot know a
   theme's aliases. ADR rule 5 ("anyOf an enum ... and the hex pattern") must be edited to match
   (finding 15).
4. **Effect fields in `basemap`, loader-only fields.** Sound. "Fails at load" holds through the
   `LOADER_FIELDS` refusal. "Schema covers every new field" holds only once the top-level
   `line_effects`/`effect_presets` schema shape is prescribed, and the plan does not prescribe it
   (finding 7).
5. **Glow floor.** Sound. On real inputs card ≤ paper, so the floor is a no-op there, and it makes
   the property hold for arbitrary arrays. ADR rule 11's formula must say so (finding 15).
6. **`ink.rgb` kept.** Sound and required: rule 3 removes no public name. ADR rule 4 ("replaces the
   three converters") and the Context ("three") are wrong: there are two converters,
   `ink/sheet.py:27` and `maps/compose_steps.py:36` (finding 15).
7. **A new public `Palette`.** Acceptable. But it is a public-API rule change under ADR 0068, not
   "wording", so it must be in the ADR before S3b, not added in S7 (finding 15). See also
   finding 10.
8. **The "effect" ban.** The plan is right not to edit `CONTRIBUTING.md` or `CLAUDE.md`. It is
   missing a sequencing gate (finding 12).

## Findings

### 1. [BLOCKING] The `Colour` retype breaks ty on files no slice owns, and collides with S6

- **Plan:** S3a "Retyping fields"; S4/S6 "parallel worktree from base, after S0"; "Files to leave
  alone: `examples/` other than the five grid scripts".
- **Evidence:** ty includes `examples` and `tests`, with `all = "error"` (`pyproject.toml:198-203`).
  I checked: ty reports `invalid-argument-type` when a `str` literal or `str` constant is passed
  to a `Colour` field. The sites are:
  - `examples/brush_sheet.py:152`
  - `examples/wash_stages.py:113`
  - `examples/tutorial_grids.py:110,190`
  - `examples/nib_stages.py:140,250,262,271`
  - `examples/how_to_route_ink.py:171` (with `LABEL_INK` at `:112`)
  - `examples/pigment_swatches.py:91`, which is on the leave-alone list
  - `tests/unit/maps/test_style.py:50`

  S6 rewrites four of those scripts from a base that has no `Colour`.
- **Fix:**
  - S3a owns wrapping each site in `Colour(...)`, imported from `pyntpot.ink`. This moves no pixel.
  - Take `pigment_swatches.py` and `how_to_route_ink.py` off the leave-alone list, for these
    lines only.
  - Cut S6's worktree after S3a, not after S0. Update "File-ownership partition" and `tasks.md`.

### 2. [BLOCKING] No rule for plain `str` reaching a `Colour` field at runtime

- **Plan:** S3a "Group instances pass unrevalidated"; "`compose_steps._rgb` is replaced by
  `Colour.rgb8`"; S5b "colours by `.rgb`".
- **Evidence (checked):**
  - `Style(g=G(c="#ABCDEF"))` keeps a plain `str` that is not lower-cased.
  - `dataclasses.replace(g, c="#123456")` gives a `str`. This is the variant idiom ADR 0068
    documents.
  - `Style.model_validate({"route_ink": {"colour": "#c22050"}})` now fails with
    `is_instance_of`. It works today (`style.py:24-28`, `test_style.py:160-178`).

  Compose would raise `AttributeError` on `.rgb8`.
- **Fix:** prescribe one rule.
  - Recommended: each group with a `Colour` field gets `__post_init__`, which normalises through
    `Colour.parse` (`object.__setattr__`; dict fields rebuilt). Add a guard test:
    `replace(RouteInkStyle(), colour="#ABCDEF").colour` is a `Colour` equal to `"#abcdef"`.
  - Then decide the `Style(...)`-from-dict case. Either accept the refusal and document it, or
    give `Colour` a `__get_pydantic_core_schema__` that returns a plain-dict core schema, which
    imports no pydantic.

### 3. [BLOCKING] `test_theme_merge.py` and `support/theme_dump.py` break, and no slice owns them

- **Evidence:**
  - `tests/property/test_theme_merge.py:21` imports `COLOUR_FIELDS`, which S3a retires.
  - `:103-105` builds `_BASE` from `asdict(Style())`, so it holds `Colour` values. ruamel's safe
    dumper raises `RepresenterError` on a `str` subclass (checked).
  - At S5a, `full.yaml` (`:198`) writes `basemap.line_effects` and `route_ink.effects`, which
    `LOADER_FIELDS` refuses.
  - `research.md:236` wrongly says no YAML writer exists.
- **Fix:**
  - S3a owns `theme_dump._plain`: write a `str` subclass as `str(value)`.
  - S3a owns `_is_colour`: decide it by the `Colour` hint, not the retired list.
  - S5a owns removing the `LOADER_FIELDS` from `_BASE`.

### 4. [BLOCKING] S5a's gate fails `test_reference_values.py`, which S7 owns

- **Evidence:**
  - `tests/docs/test_reference_values.py:141-205` requires a row (type, default) for every field
    of every group, and a key sub-table for every Mapping field.
  - `tests/docs/test_reference_pages.py:118-127` also checks the page.
  - S7 owns `style-fields.md` "if needed". It is needed, at S5a.
- **Fix:** move the two `style-fields.md` rows into S5a:
  - `basemap.line_effects`: table, `{}`, an empty key sub-table.
  - `route_ink.effects`: table.
  - Each row says the field is set only by the top-level `line_effects` table.

### 5. [BLOCKING] The `Shadow` default trips the plan's own single-literal guard

- **Evidence:**
  - The `Shadow` default `colour=Colour("#3b4452")` is `paynes_grey` (`ink/pigment.py:76`).
  - S1's `test_one_registry.py` allows each built-in hex in one `src` module only.
  - `maps/line_effects.py` would hold a second copy.
- **Fix:** `colour=pigment("paynes_grey").colour`, stated in S5a.

### 6. [BLOCKING] Dropping off effects per file means an inherited stack can never be turned off

- **Plan:** S5a "Drops off effects ... and empty stacks", "merges it into the file's table".
- **Evidence:**
  - `theme_merge.py` has "no syntax for removing a key".
  - Say a child writes `line_effects.major: {}` or `casing: {width_px: 0}`. It is dropped before
    the merge, so the parent's `cased` survives. The user wrote "off" and nothing changed, with
    no error.
  - `test_line_effect_digests` cannot catch this, because no packaged theme sets an effect.
- **Fix:**
  - Keep an explicit `EffectStack()` per file, so the merge replaces the parent's stack.
  - Drop off effects and empty stacks once, after the final merge, in `resolve` or `_build`.
  - Test: the parent sets `major: cased`, the child sets `major: {}`; the result has no stack
    and the default digests.

### 7. [SHOULD-FIX] The effect-table schema shape is unprescribed, and S3a's guard will fail at S5a

- **Fix:** prescribe the shape.
  - `line_effects`:
    - keys: `propertyNames` enum of `LINE_CLASSES`;
    - values: `anyOf` of the built-in preset enum, an `ALIAS_PATTERN` string, or a stack object;
    - the stack object has `additionalProperties: false` and `casing`/`glow`/`shadow`, each the
      dataclass walk (numbers, the `Colour` three-branch node, defaults).
  - `effect_presets`:
    - keys: the pattern, and not a built-in name;
    - values: the stack object.
  - State how `theme_schema_tables` reuses the walker without a cycle.
  - Have S5a extend the S3a guard to the `Casing.colour` and `Shadow.colour` nodes.

### 8. [SHOULD-FIX] An import cycle, and the new modules sit outside the import guard

- **Evidence:**
  - The new `theme_*` modules need `_Check` from `theme_check`, and `theme_check` dispatches into
    them.
  - `palette.py`, `palette_gpl.py` and `line_effects.py` escape the `theme_*.py` glob in
    `tests/architecture/test_theme_imports.py:30`.
- **Fix:**
  - Name the module that owns `_Check` (for example `theme_checker.py`) and the module that
    owns `check_theme_scoped`.
  - Prefix the palette modules `theme_`, or widen the guard.

### 9. [SHOULD-FIX] Binding down `extends` is unstated

- **Evidence:** checking from the base up resolves each file's names in its own scope. So a
  child that swaps `palette:`, or overrides `sky`, does not recolour inherited fields that name
  it. Nothing says whether a child's `palette:` replaces or joins the parent's aliases.
- **Fix:** state the rule in the plan, ADR rule 7 and `write-a-theme.md`, and pin it with a test.
  Changing it later moves users' digests.

### 10. [SHOULD-FIX] `.gpl` edge cases and `Palette.of_registry`

- **Evidence:**
  - Two names that normalise to the same alias, or a name with a leading digit, have no stated
    error.
  - `of_registry` builds a `Palette` keyed by built-in names. Its own `from_file` refuses those
    names, so the registry export can never be read back in.
- **Fix:**
  - Make both cases located errors.
  - Replace `of_registry` with `registry_gpl(registry) -> str`.

### 11. [SHOULD-FIX] Where the four tables live after S1 is unstated

- **Evidence:** `PIGMENTS` and the other three tables could stay in `compositing.py` or move to
  `pigment_table.py`. The importers' repoint list depends on which, for example
  `tests/unit/ink/test_wash.py:8` and `tests/benchmarks/test_ink.py:13`.
- **Fix:** say which module holds them.

### 12. [SHOULD-FIX] No gate on the user's "effect" ruling

- **Evidence:** `CONTRIBUTING.md:143-144` bans "effect", and `GLOSSARY.md:39-44` already uses it.
  If the ruling goes against the word, S4/S5a's public names, the theme keys, the module stems
  and the schema all rename.
- **Fix:** S4 and S5a do not start until the ruling is recorded. S0 to S3b go ahead.

### 13. [SHOULD-FIX] No numeric ranges on effects

- **Evidence:** the checker checks no ranges (`theme_check.py:18`). A negative strength leaves a
  non-empty stack that draws nothing: the digest moves with identical pixels. A strength over 1
  is clipped silently.
- **Fix:**
  - `__post_init__` refuses `px < 0` and strength outside [0, 1].
  - The loader reports it as a located problem.
  - The drop rule becomes `== 0`.

### 14. [SHOULD-FIX] S5b's locality test is not exact in multiply mode

- **Evidence:** the multiply path computes `base * prod` (`pigment.py:226-227`). Split across
  several calls, float32 rounding changes pixels outside the ring.
- **Fix:** pin `km_glazing=True` (the default, `ink/style.py:88`) for exact equality, or state a
  tolerance.

### 15. [SHOULD-FIX] Edit ADR 0070 before S0, not in S7

Implementers read the ADR as binding, so it must match the plan before work starts:

- **Rule 5:** the schema has three branches.
- **Rule 11:**
  - the glow is floored;
  - the casing blends toward colour × paper;
  - the threshold is `>= τ` (the casing text says `m > τ`).
- **Rule 4 and Context:**
  - `ink.rgb` stays and shares the arithmetic;
  - there are two converters, not three.
- **Rule 9:** the two group fields are loader-only.
- **Public names:**
  - `Palette`;
  - `PigmentRegistry` and `PIGMENT_REGISTRY`;
  - `Casing`, `Glow`, `Shadow` and `EffectStack`.
- **New rules:** findings 6 and 9.

### 16. [SHOULD-FIX] Changelog honesty

- **Evidence:** typed callers' `PaperStyle(paper_hex="#...")` becomes a type error. It is not a
  removal or a rename, so no `!` under the agreed rule, but it should be stated.
- **Fix:** add a Changelog line.

### 17. [CONSIDER] Guards for the duplicated converter and the duplicated grid code

The bar asks for a guard per defect class, and these two have none. Add:

- an architecture test that hex is parsed only in `ink/colour.py`;
- a test that no grid script keeps its own label round trip.

### 18. [CONSIDER] S0's entry count

There are 23 entries, not 21 (checked against `IMAGES`). Write "every entry of the five stems".

### 19. [CONSIDER] One lookup, one message

Make `pigment()` the one public name lookup, with `PigmentRegistry.get` as what it calls, so the
miss message has one source.

### 20. [CONSIDER] Shadow sub-pixel offset

Say how `offset_px × scale × (dx, dy)` rounds to whole pixels.

## Resolution

Revised on `682677f`; each fix was checked against the code first. ADR 0070 was amended in
place, its rule numbers unchanged.

1. S3a owns wrapping every `str` colour literal in `Colour(...)`, `pigment_swatches.py` and
   `how_to_route_ink.py` included; S6's worktree is cut after S3a (plan S3a "Call sites",
   S6, File-ownership partition, `tasks.md`).
2. One rule: each group's `__post_init__` normalises through `Colour.parse`
   (`normalise_colours`), and `Colour.__get_pydantic_core_schema__` returns a plain-dict
   core schema, so `Style.model_validate` from a dict still builds and `Style` needs no
   `arbitrary_types_allowed` (checked with pydantic 2.14.2); guard test added (plan S3a,
   ADR rule 4).
3. S3a owns `theme_dump._plain` and `_is_colour` (by `isinstance(value, Colour)`, since
   `asdict` keeps the subclass); S5a drops the loader-only fields from `_BASE` (plan S3a,
   S5a). `research.md`'s "no YAML writer" is noted as stale in the plan's Approach.
4. The two `style-fields.md` rows, the empty key sub-table and the route sentence move to
   S5a (plan S5a "`style-fields.md`").
5. `Shadow` defaults to `pigment("paynes_grey").colour` (plan S5a "Types").
6. Each file keeps an explicit stack; off effects and empty stacks are dropped once, after
   the final merge, in `EffectStack.__post_init__` and `BasemapStyle.__post_init__`; the
   parent `cased`, child `{}` test added (plan S5a, ADR rule 9 "Off is nothing").
7. Schema shape prescribed; `theme_schema_tables.top_level_tables(sub_table)` takes the
   walker as an argument, so no cycle; the S3a guard extends to the effect colours (plan
   S3b and S5a "Schema", ADR rule 9).
8. `_Check` moves to `maps/theme_checker.py` (S3a, a pure move); `check_theme_scoped` lives
   in `theme_check`; the palette modules become `theme_palette.py` and
   `theme_palette_gpl.py`, and `line_effects.py` joins the guard by name (plan "Line
   budget", S3a, S3b, S5a).
9. A name binds in the file where it is written; aliases, pigments and presets accumulate;
   the nearest `palette:` is in effect; a palette alias clashing with an inherited one is
   a located error unless rebound with `override`; pinned by tests (plan S3b, ADR rule 7,
   S7 `write-a-theme.md`).
10. Both `.gpl` cases are located errors; `of_registry` is replaced by the static
    `Palette.registry_gpl(registry) -> str`, kept on `Palette` so palettes keep one
    public name (plan S3b, ADR rule 7).
11. The four tables move to `ink/pigment_table.py` and are imported from `pyntpot.ink` by
    the tests that used the old module (plan S1, ADR "Public names").
12. Not a gate, by the orchestrator's ruling: S4 and S5a proceed using the words only as
    glossary terms, no slice edits `CLAUDE.md` or `CONTRIBUTING.md`, and a task applies
    the user's ruling, if given, before S7 (plan Approach, `tasks.md` "Before S7").
13. `EFFECT_RANGES` drives both the `__post_init__` refusals and located load errors;
    nothing is clipped; off is `== 0`, so `-0.0` is off and a value equal to off moves no
    digest (plan S5a, ADR rule 9 "Ranges", "Off is nothing").
14. The locality test pins `km_glazing=True` for exactness; multiply mode asserts within
    1e-6 (plan S5b).
15. ADR 0070 amended before S0: Context and rule 4 (two converters, `ink.rgb` kept, the
    coercion rule), rule 5 (three branches), rule 7 (`.gpl` cases, registry export,
    binding down `extends`), rule 9 (the two loader-only fields, schema shape, ranges,
    off dropped after the merge), rule 11 (`m >= τ`, casing toward colour times paper,
    the glow floor, shadow rounding), "Public names" (every new name, `Palette`, the
    module rename); S7 no longer edits the ADR.
16. A Changelog line states typed callers now pass `Colour(...)`; the title keeps no `!`
    (spec "Changelog").
17. `tests/architecture/test_one_hex_parser.py` (S3a) and a `.convert("RGBa")` guard in
    `test_examples.py` (S6).
18. S0 says "every entry of the five stems" (23 on `e5578fe`).
19. `pigment()` is the one documented lookup and delegates a name to
    `PigmentRegistry.get`, the one place the miss message is written (plan S1, ADR rule
    2, spec).
20. The shadow offset rounds each axis with Python's `round`, half to even, then slices
    with zero fill (plan S4, ADR rule 11).
