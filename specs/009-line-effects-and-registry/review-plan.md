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

## Re-review

Reviewer: fresh-context plan reviewer, on `f1b969e`. Each resolution was checked against the
code, not against its own claims. Experiments are in the session scratchpad (`rr/`).

### Verdict: BLOCK

Four BLOCKING findings remain, all new and all introduced or exposed by the revision: an
S1 gate that cannot go green, an S6 import that `ty` fails, existing guard tests that S3b
and S5a break but do not own, and a `ThemeScope` shape too small for S3b's own rules. Each
fix is a few lines of plan. Once they are applied, the plan can pass without another round
if the SHOULD-FIX items are folded in at the same time.

### Resolutions verified

- **1 (call sites).** The lines are right: `tutorial_grids.py:83`, `how_to_route_ink.py:112`
  and `pigment_swatches.py:70` are the constants. `ty` 0.0.97 does not flag
  `dataclasses.replace(..., colour="#..")` (checked), so `nib_stages.py:140` is a harmless
  wrap. "Any further site `ty` names is S3a's" closes the list.
- **2 (coercion).** Checked with pydantic 2.14.2 under `-W error`. The plain-dict hook
  builds `Style.model_validate` with a `Colour`, a bad value is `value_error` at
  `("route_ink", "colour")`, the strict `BeforeValidator` reads `info.context`, and
  `replace(...)` normalises through `__post_init__`. One gap remains: SHOULD-FIX 8.
  `Style.model_json_schema()` now raises, but nothing calls it.
- **3.** Holds from S3a on, but the dumper fix comes one slice too late (BLOCKING 1).
- **4.** `yaml_value` and `yaml_type` give `table` for both `{}` and `EffectStack()`, and an
  empty `| Key | Default |` table parses to no rows. The S5a rows pass the comparator.
- **5, 6, 13, 15, 16, 18, 19, 20.** Hold. `merge` replaces an `EffectStack`, because it is
  no `Mapping`, so a child's `major: {}` turns off its parent's stack
  (`theme_merge.py:33`).
- **7.** The schema shape is now prescribed, but the guards that pin it are unowned
  (BLOCKING 3).
- **8.** Holds, apart from an incomplete move list (SHOULD-FIX 7).
- **9 and 10.** The rules are prescribed, but the data shape to carry them is missing
  (BLOCKING 4).
- **11.** Holds. One stale path is missed (CONSIDER 1).
- **12.** "effect" is no retired word in `GLOSSARY.md`, so `test_retired_words.py` does not
  gate it.
- **14.** Checked over 200 random stacks: splitting `km_plate` is bit-exact (0 pixels
  differ), and multiply drifts by at most 6e-8.
- **17.** Holds. Only `ink/sheet.py:42` and `compose_steps.py:39` parse hex in `src`.

### Findings

#### BLOCKING

1. **[BLOCKING] S1's own gate fails on the YAML dumper (plan :146-148, :242-246).**
   - **Evidence:** in S1, `CoverStyle().pigments` is built from `Pigment.colour`, so its
     values are `Colour`.
   - `test_an_override_and_its_expanded_copy_give_one_digest`
     (`tests/property/test_theme_merge.py:194-203`, in the slice gate) dumps
     `merge(_BASE, override)` through `support/theme_dump._plain`.
   - ruamel's safe dumper raises `RepresenterError` on a `str` subclass (checked). The
     dumper fix is in S3a, two slices later.
   - **Fix:** move the `theme_dump._plain` change (a `str` subclass is written as
     `str(value)`) and the ownership of `tests/support/theme_dump.py` into S1, and drop
     them from S3a.
2. **[BLOCKING] S6's `from labelled_grid import ...` fails `ty` (plan :621-623, :725,
   :690-691).**
   - **Evidence:** `[tool.ty.environment] root` is `["src", "tests"]`, so the import is
     `import-not-found`.
   - `ty` 0.0.97 exits 1 on that warning (checked in a minimal project).
   - In a copy of the repo with the import added to `wash_stages.py`, adding `"examples"`
     to `root` gives "All checks passed!" (checked).
   - **Fix:** S6 owns `pyproject.toml` `[tool.ty.environment] root`, adding `"examples"`.
     Narrow "Files to leave alone" to `[tool.importlinter]`, which S9 already checks.
3. **[BLOCKING] S3b and S5a break existing guards they do not own (plan :295-296, :364-373,
   :455-463).**
   - **Evidence:**
     - `tests/unit/maps/test_theme_schema.py:170-178` pins the top-level keys to
       `["extends", *Style.model_fields]`. S3b adds three keys and S5a adds two.
     - `:144-155` requires every `propertyNames` node to equal
       `{"enum": sorted(VOCABULARIES[path])}`, and `entries == set(VOCABULARIES)`. That is a
       `KeyError` on the `colours`, `pigments`, `effect_presets` and `line_effects` nodes.
     - `:131-141` requires a group's schema properties to equal its fields. This fails once
       S5a skips the `LOADER_FIELDS`.
     - `tests/unit/maps/test_theme_vocab.py:82-106` requires a `VOCABULARIES` entry for every
       dict field, `basemap.line_effects` included. Adding one then contradicts the schema
       test above.
   - S3a owns both test files; S3b and S5a own neither.
   - **Fix:**
     - Add `test_theme_schema.py` to S3b and S5a, and `test_theme_vocab.py` to S5a.
     - Prescribe the top-level order, for example `extends, palette, pigments, colours,
       effect_presets, line_effects, <groups>`, and the pinned list.
     - `basemap.line_effects` gets no `VOCABULARIES` entry: `theme_effects` checks its keys
       against `LINE_CLASSES`.
     - The field-to-schema test and both dict-field vocabulary tests leave out
       `LOADER_FIELDS`.
     - The `propertyNames` test walks only the group subtrees, and a new test pins the four
       top-level tables' key rules.
4. **[BLOCKING] `ThemeScope(registry, aliases, presets)` cannot carry S3b's rules, and S3b
   and S5a do not own `theme_scope.py` (plan :260-264, :293-299, :317-332, :447-463).**
   - **Evidence:** the rules need four things the shape lacks:
     - the file each entry came from ("naming the alias and both files", :325-326);
     - which aliases came from the palette (":322-324", a new `palette:` removes them);
     - whether an entry is the file's own or inherited (the `override` rule);
     - a way to replace an inherited theme pigment, which `PigmentRegistry.extended` cannot
       do because it "refuses duplicate names" (:155).
   - **Fix:** prescribe the shape in S3a:
     - `ThemeScope(pigments: Mapping[str, Bound[Pigment]], palette: Bound[Palette] | None,
       aliases: Mapping[str, Bound[Colour]], presets: Mapping[str, Bound[object]])`, where
       `Bound(value, path, line)`;
     - `registry` is a cached property, `PIGMENT_REGISTRY.extended(...)`;
     - `resolve_colour` looks up a theme alias, then a palette alias, then a registry name.
   - Add `maps/theme_scope.py` to S3b's and S5a's Owns. S5a types presets as `EffectStack`.

#### SHOULD-FIX

The implementer can apply each of these as written.

5. **The `LOADER_FIELDS` refusal: mechanism and message (plan :456-458, :536).** Group keys
   are walked in `TableCheck.mapping`, in `theme_checker.py`, which S5a does not own.
   - **Fix:** in `check_theme_scoped`, before `check.table(...)`, take each
     `LOADER_FIELDS` key out of the group's mapping.
   - Record a pinned message at its path: "set only by the top-level line_effects.<class>".
6. **The `.gpl` round trip is false under `ALIAS_PATTERN = ^[a-z][a-z0-9_]*$` (plan :266,
   :353-358, :389-390).**
   - **Evidence:**
     - `a__b` normalises to `a_b`, and `a_` to `a`, so `to_gpl()` of a valid palette does
       not read back as itself.
     - Generated names may equal a built-in name.
   - **Fix:**
     - In S3a, set `ALIAS_PATTERN = "^[a-z][a-z0-9]*(_[a-z0-9]+)*$"`, so every alias is
       its own normal form.
     - Draw names with `from_regex(ALIAS_PATTERN, fullmatch=True)`, filtered off the
       registry's names. Use `fullmatch=True` in S1 and S3b too.
7. **The S3a pure move is incomplete (plan :247-249).** `_Check.leaf` and `_Check.mapping`
   also use `_sheet_and_colour`, `_MESSAGES`, `_TABLE`, `_COLOUR` and `_Path`. If
   `_sheet_and_colour` stays in `theme_check`, `theme_checker` must import `theme_check`,
   which is a cycle.
   - **Fix:** add them to the move list. The brush branch moves with `_sheet_and_colour`.
8. **`Colour.parse` on a non-`str` (plan :152-153, :220-228).** If `parse` calls `.lower()`
   on its input, both of these raise `AttributeError` instead of a `value_error`:
   - `Style.model_validate({"route_ink": {"colour": 5}})`;
   - `RouteInkStyle(colour=None)`.
   - **Fix:** state that `Colour.parse` raises `ValueError` for any non-`str`.
9. **Theme pigments: "exactly one of `base` and `colour`" (plan :311-312).** This
   contradicts ADR rule 6 and D4: "`base: <pigment>` plus the fields it overrides".
   - **Fix:** require `base` or `colour`, and allow both, where `colour` overrides the
     base's colour.
10. **S8's scope is wrong (plan :677-684).** S3a adds new functions in both layers:
    - `NibStyle.__post_init__` in letters;
    - `PaperStyle.__post_init__`, `WashStyle.__post_init__` and `normalise_colours` in
      ink.
    - mutmut selects only `tests/unit/ink`, `tests/unit/letters` and `tests/property`, but
      the coercion tests are in `tests/unit/maps`.
    - **Fix:** add these functions to S8's scope, with ink and letters unit tests for them.
11. **A typo key in `basemap.line_effects` is silently ignored (plan :480).** A Python
    caller's `BasemapStyle(line_effects={"route": ...})`, or a misspelt key, is accepted
    and the painter never reads it.
    - **Fix:** `__post_init__` raises `ValueError` for a key outside the seven basemap
      classes.

#### CONSIDER

12. **A stale path (plan :137-145).** `docs/features/ink-stroke-density-profile.md:8` cites
    `ink/pigment.py`. Add it to S1's repoint list.
13. **The S4 threshold (plan :403-421).** S4's primitives divide `mask / threshold`, and
    warnings are errors. Refuse `threshold <= 0`, or draw it from `(0, 1]`.
14. **An uncommitted ADR edit.** The working tree holds an uncommitted edit to ADR 0070
    rule 17 (PR 2). Commit it before S0, so S0's base is clean.

## Re-review resolution

Applied on `d66c2d2`; each finding was checked against the code first.

1. `theme_dump._plain` writes a `str` subclass as `str`, and `tests/support/theme_dump.py`
   is S1's, dropped from S3a (plan S1 "Test support", S3a, ownership table, `tasks.md`).
2. S6 adds `"examples"` to `[tool.ty.environment] root` (`pyproject.toml:193-196`) and
   owns that one line; "Files to leave alone" narrows to the rest of `pyproject.toml`.
   This widens what `ty` checks and loosens no gate.
3. S3b owns `test_theme_schema.py` (top-level order pinned, the `propertyNames` walk over
   group subtrees only, a `colours` and `pigments` key-rule test); S5a owns it and
   `test_theme_vocab.py` (`effect_presets` and `line_effects` added; the field test and
   both dict-field tests leave out `LOADER_FIELDS`; no `VOCABULARIES` entry for
   `basemap.line_effects`).
4. S3a prescribes `Bound(value, path, line)` and `ThemeScope(pigments, palette, aliases,
   presets)`: palette and theme aliases split, own versus inherited read from
   `Bound.path`, theme pigments held by name so an inherited one is replaced in the
   mapping and the cached `registry` never meets a duplicate. S3b and S5a own
   `theme_scope.py` in turn; serial ownership is disjoint by sequencing, stated in the
   plan and above the ownership table.
5. `check_theme_scoped` takes each `LOADER_FIELDS` key out before `check.table(...)`, with
   the message "set only by the top-level line_effects.<class>" (or `.route`), pinned.
6. `ALIAS_PATTERN = "^[a-z][a-z0-9]*(_[a-z0-9]+)*$"`; strategies use `fullmatch=True` and
   filter off the registry's names (S1, S3b). ADR 0070 rule 5 carried the old pattern, so
   it is amended.
7. The move list adds `_sheet_and_colour` (brush branch with it), `_MESSAGES`, `_TABLE`,
   `_COLOUR` and `_Path` (`theme_check.py:51-65, 247`); `_COLOUR` goes with the colour
   branch.
8. `Colour.parse` raises `ValueError` for any non-`str` (plan S1, spec).
9. A theme pigment needs `base` or `colour` and may give both, `colour` overriding the
   base's (plan S3b, spec); ADR rule 6 already says so, unchanged.
10. S8 adds `normalise_colours` and the `PaperStyle`, `WashStyle` and `NibStyle` hooks,
    tested in `tests/unit/ink/test_style_colours.py` and `tests/unit/letters/test_style.py`
    (S3a).
11. `BasemapStyle.__post_init__` raises `ValueError` for a key outside the seven classes;
    at load `theme_effects` records it as a located problem first.
12. An S7 task fixes `docs/features/ink-stroke-density-profile.md:8` (not edited now).
13. Each S4 primitive refuses `threshold <= 0`; strategies draw it from `(0, 1]`.
14. Already committed in `d66c2d2`; nothing to do.

## Round 3

Reviewer: fresh-context plan reviewer, on `1b8950b`. Each "Re-review resolution" item was
checked against the code. Experiments are in the session scratchpad (`r3/`).

### Verdict: BLOCK

The fourteen re-review resolutions hold against the code, apart from a gap in item 4
(SHOULD-FIX 3). One new BLOCKING finding remains: S5a's two new fields fail a pinned-table
test file that no slice owns, and the obvious fix moves a pinned digest. The fix is a few
lines of plan. With it and the SHOULD-FIX items applied, the plan can pass without a
fourth round.

### Resolutions verified

- **1.** Only `tests/property/test_theme_merge.py:199-200` dumps YAML (`git grep`), so the
  `_plain` fix in S1 covers every dump site.
- **2.** `root` is `["src", "tests"]` (`pyproject.toml:193-196`).
- **3.** The named tests exist as described: `test_theme_schema.py:131,144,170` and
  `test_theme_vocab.py:82,98` (through `_unvocabularied`).
- **5.** The refusal happens in `check_theme_scoped`, ahead of the walk in
  `TableCheck.mapping` (`theme_check.py:173-200`).
- **6.** The new pattern is idempotent under the `.gpl` rule.
- **7.** The move list is complete for `leaf`, `mapping`, `_vocabulary` and
  `_sheet_and_colour` (`theme_check.py:124-295`). `build_group` keeps `_hints` and
  `_is_dataclass` through the no-underscore rule (`test_import_order.py`).
- **8 to 14.** Hold. Every `COLOUR_FIELDS` importer is S3a's. No packaged or example
  theme, and no example script, writes an upper-case hex, so lower-casing moves no digest.
  `BrushStyle().brushes` is the seven classes.
- **4.** The rules now have a shape to live in, but one type in that shape does not exist
  at S3a (SHOULD-FIX 3).

### Findings

#### BLOCKING

1. **[BLOCKING] S5a fails `tests/unit/maps/test_style_groups.py`, which no slice owns, and
   the obvious fix moves a pinned digest (plan :515-536, :919; `tasks.md` :93-113).**
   - **Evidence:**
     - `PINNED[BasemapStyle]` and `PINNED[RouteInkStyle]` (`:207-245`) pin each group's
       field names in order, so `test_group_fields_match_the_pinned_table` fails when
       `line_effects` and `effects` are added.
     - `test_basemap_defaults_are_the_pinned_literals` (`:360-367`) requires
       `_names(BasemapStyle) == list(BASEMAP_DEFAULTS)`, so it fails too.
     - `test_group_defaults_equal_the_pinned_digest` (`:348-351`) hashes the raw
       `dataclasses.asdict(group())`, with no omit rule. I checked: adding `effects` moves
       `SOURCED[RouteInkStyle]` from `6a536a78d3ad069a` to `4ff7222687a4890e`. The plan's
       "Files to leave alone" forbids moving any pinned literal.
     - Switching that test to `_digest_fields` is no fix either: it moves `CoverStyle`'s
       pin, `8ff38fcbad0d7a6f`, to `f201b60695520db7` (checked).
   - **Fix:**
     - Add `tests/unit/maps/test_style_groups.py` to S5a's Owns, its row in the ownership
       table, and its `tasks.md` line.
     - Append `"line_effects"` to the `BasemapStyle` row, `"effects"` to the
       `RouteInkStyle` row, and `"line_effects": {}` to `BASEMAP_DEFAULTS`.
     - In the digest test, drop the fields named in `LOADER_FIELDS` before hashing, and
       say why in its docstring, so every `SOURCED` pin holds.
     - Add an assertion that `RouteInkStyle().effects == EffectStack()` and
       `BasemapStyle().line_effects == {}`.
     - The file is 399 lines now. Move `BASEMAP_DEFAULTS` and its test to a new file
       rather than pass 400.

#### SHOULD-FIX

2. **S3a meets an exact-type pin and could loosen it (plan :219, :255).**
   - **Evidence:** `test_style.py:84` asserts `type(got) is type(value)`. Its
     `RESOLVED_SAMPLE` pins `paper.paper_hex` (`:21`) and `nib.label_ink` (`:32`) as plain
     `str`, and both become `Colour` in S3a.
   - **Fix:** S3a pins `Colour("#f3ead6")` and `Colour("#241c14")`. The type assertion
     stays.
3. **`ThemeScope.palette: Bound[Palette]` names a class S3a does not have (plan :284-298).**
   - **Evidence:** `Palette` is created in S3b, so at S3a the annotation is unresolved and
     `ty` fails.
   - **Evidence:** importing it at runtime risks a cycle:
     `theme_scope -> theme_palette -> theme_colours -> theme_scope`.
   - **Fix:** S3a types the field `Bound[object] | None`, as it does `presets`. S3b
     narrows it to `Bound[Palette]`, with the import under `TYPE_CHECKING`. State the
     runtime import direction:
     `theme_palette -> theme_colours -> theme_scope`.
4. **Existing tests that S3a rewrites are unnamed, and their messages are unpinned (plan
   :161-165, :276-277).**
   - **Evidence:**
     - `test_theme_schema.py:186-192` asserts the old flat colour node.
     - `test_theme_check.py:186-191` pins the messages "'red' ..." and "'#a8c28' is not a
       # and six hexadecimal digits".
     - `test_theme_check.py:246-248` expects `#C22050` to be kept as written.
   - **Fix:**
     - Name all three as rewritten, not deleted.
     - `Colour.parse` keeps the text "{text!r} is not a # and six hexadecimal digits".
     - The non-string message is "{v!r} is not a string", matching
       `_MESSAGES["string_type"]`.

#### CONSIDER

5. **`pigment("#...")` (plan :172).** The plan says a hex "goes to `Colour.parse`". The
   spec (:36-38) and ADR rule 2 say it returns an anonymous `Pigment` named by the hex,
   with `transparency=None`. Say that in the plan.
6. **The `colours` value schema (plan :419-420).** "Names or hex" makes an editor refuse
   an alias to a theme pigment. Use the three-branch `Colour` node.
7. **Test file sizes.** `test_style.py` is 384 lines and `test_theme_check.py` 361. Put
   S2's and S3a's new cases in new files.

## Round 3 resolution

- **1 (BLOCKING).** S5a owns `test_style_groups.py` (`PINNED` rows gain `line_effects` and `effects`; the digest test drops `LOADER_FIELDS` names before hashing, so `6a536a78d3ad069a` and every `SOURCED` pin hold; two default asserts), and `BASEMAP_DEFAULTS` and its test move to new `test_basemap_defaults.py` with `"line_effects": {}` (plan :685-710, ownership row, `tasks.md` S5a).
- **1, further pin found.** `tests/unit/maps/candidates/test_export.py:88-121` pins `asdict(CANDIDATE_BASEMAP)` (`maps/candidates/export.py:39`) in full; assigned to S5a, gaining `"line_effects": {}` (plan :702). `test_theme_check.py:358-361`, `test_style.py:91-106` and `painter/test_smoke.py:31-37` pass unchanged (checked against `theme_check.py:103-121`).
- **2.** S3a pins `Colour("#f3ead6")` and `Colour("#241c14")` in `RESOLVED_SAMPLE`; the `type(got) is type(value)` assertion (`test_style.py:84`) stays (plan :268).
- **3.** S3a types `palette` as `Bound[object] | None`; S3b narrows it to `Bound[Palette] | None` under `TYPE_CHECKING`; runtime direction `theme_palette -> theme_colours -> theme_scope` stated (plan :311-319, :383-385, :432).
- **4.** The three tests are named as rewritten in place; `Colour.parse` keeps "{text!r} is not a # and six hexadecimal digits" (`theme_check.py:254`); non-`str` reads "{v!r} is not a string" (`theme_check.py:61`); `'red'` has no difflib match, so its miss has no suggestion clause (plan :297-306).
- **5.** `pigment("#...")` returns an anonymous `Pigment` named by the hex, `transparency=None`, `colour_index=None`, with a property (plan :172).
- **6.** The `colours` value schema is the three-branch `Colour` node or `{colour: <node>, override}` (plan :474).
- **7.** New cases go in new files: S1 `test_registry_defaults.py` (the unnamed maps ties; `test_style_groups.py` is 399 lines), S2 `test_theme_brush_ids.py` (the `MAJ9-a` row at `test_theme_check.py:182-183` rewritten in place), S3a `test_colour_fields.py`, `test_theme_scope.py` and `test_theme_colour_names.py`; each named in its slice and ownership row.
- **PR 2 re-review 1.** `ThemeScope.aliases: Mapping[str, Bound[Pigment]]` and `Palette(name, pigments: Mapping[str, Pigment])`, a hex alias the anonymous `pigment("#...")`, no separate `colours` mapping; `resolve_pigment` added, `resolve_colour` is its `.colour`, so no digest moves; `.gpl` import yields anonymous pigments and export writes names and hexes; properties revised; ADR rules 5 and 7, the Public names paragraph and the spec updated; no public name changes (plan :311-336, :436-466, :1070).

## Round 4

Reviewer: fresh-context plan reviewer, on `89db1d9`. I checked each "Round 3 resolution" item
against the code, then swept every slice's source changes against `tests/`. Experiments are
in the session scratchpad (`r4/`).

### Verdict: BLOCK

The Round 3 resolutions hold, and so does the alias-holds-`Pigment` change. Two new BLOCKING
findings came out of the sweep. S6 breaks two docs tests that it does not own, and three of
S4's prescribed signatures, plus S6's `label_grid`, fail `ruff check`. Both fixes are a
few lines of plan.

### Resolutions verified

- **1.** Dropping the `LOADER_FIELDS` names from `asdict(RouteInkStyle())` gives back
  today's dict, so `6a536a78d3ad069a` holds (`test_style_groups.py:348-351`). The
  `CANDIDATE_BASEMAP` pin is a full literal (`candidates/test_export.py:88-121`).
  `build_group` builds `{"effects": ()}` into `EffectStack()` and passes `{}` through
  (`theme_check.py:113-121`).
- **2 to 7.** These hold, at the lines cited (plan :268, :311-336, :297-306, :171-175, :474-476).
- **Alias holds a `Pigment`.** `ThemeScope.aliases: Mapping[str, Bound[Pigment]]` (plan
  :311-320). `Palette.pigments` resolves against `PIGMENT_REGISTRY` only (plan :436-442),
  as ADR rule 7 says. `resolve_colour` is `resolve_pigment(...).colour` (plan :336).
- **No digest moves.** The digest is `json.dumps(asdict(...), sort_keys=True)`
  (`style.py:296-311`). A `str` subclass dumps as its text, and every packaged and example
  theme writes only lower-case hex, so the digests stay put.
- **No stale shapes.** No `Bound[Colour]` or `Palette.colours` is left in the spec, the
  plan, the tasks or the ADR.

### Sweep (test files at risk, per slice)

- **S0:** `make_docs_images.py` is owned, and it has one caller (`:100`).
- **S1:** the 11 importers and pins are owned. These stay green, because each value
  compares equal as a `str` and keeps today's order: `test_style_groups` `SOURCED`,
  `test_theme_vocab` `PIGMENTS`, `test_reference_values`, `test_reference_pages`,
  `test_site_theme`, the committed-schema test and `test_site`.
- **S2:** two rows of `test_theme_check.py` change. Only one is named (finding 3).
- **S3a:** every file it touches is owned. These stay green: `test_reference_values`
  (value-based), `test_one_source_of_defaults`, `test_import_order` (underscores dropped)
  and `test_tutorial_quotes` (no wrapped literal sits in a quoted block).
- **S3b:** these stay green: the top-level unknown-key pins (`wsh` still suggests `wash`)
  and `test_theme_resolve`, because `ThemeError` sorts its problems (`theme_errors.py:65`).
- **S5a:** every pinned table is owned. These stay green: `test_style.py` `route_ink.effect`
  and `casing_px` (they pin location only), `test_smoke`, `test_reference_values`
  (`EffectStack` reads as "table") and `test_one_source_of_defaults`.
- **S5b:** `paint_pen`'s return is kept, so `test_pen` and the pinned golden hashes stay
  green.
- **S6:** two failures (finding 1).

### Findings

1. **[BLOCKING] S6 fails `test_tutorial_quotes.py` and `test_reference_pages.py`, and neither
   is S6's (plan :800-829).**
   - **Evidence, the tutorial quotes:**
     - `docs/tutorials/paint-a-watercolour.md` quotes seven `tutorial_grids.py` grid
       functions verbatim (markers at :92, :172, :265, :369, :468, :573 and :690).
     - Each of them calls `_layout(...)`, `_labels(...)` or `_letter(...)`, and the prose at
       :36 names all three.
     - `tests/docs/test_tutorial_quotes.py:24-34` requires every quoted block to appear
       unchanged in its script.
   - **Evidence, `test_reference_pages.py`:**
     - `tests/docs/test_reference_pages.py:230` runs `runpy.run_path(brush_sheet.py)`.
     - I checked: `run_path` on a single file does not put the file's directory on
       `sys.path`, so `from labelled_grid import` raises `ModuleNotFoundError`.
   - **Evidence, the `RGBa` guard:** each `.convert("RGBa")` sits in a script's `_letter`
     (for example `tutorial_grids.py:151` and `nib_stages.py:215`). Those functions letter
     cell content with a nib, seed and `ground` that change per cell, so `label_grid` alone
     cannot replace them, and the guard fails.
   - **Fix:**
     - `tutorial_grids.py` keeps `_layout`, `_labels` and `_letter` with today's signatures,
       each a one-line delegate.
     - `labelled_grid.py` exposes the round trip as its own function, which `label_grid`
       and every script's `_letter` call.
     - S6 owns that one test in `test_reference_pages.py`. It loads `brush_sheet.py` through
       a `support.examples` helper that puts `EXAMPLES_DIR` on `sys.path`, the same helper
       `run_example` uses.
     - Label tuples and lettered names stay literals in each script, because
       `test_captions.py:185-205` reads them from the script's syntax tree.
2. **[BLOCKING] Prescribed signatures fail `ruff check` with PLR0913 (plan :533-551,
   :812-814).**
   - **Evidence:**
     - `max-args = 6` (`pyproject.toml`), and PLR0913 counts keyword-only parameters. A
       probe of `casing` gave "7 > 6".
     - The counts: `casing` 7, `glow` 7, `shadow` 8 and `label_grid` 13.
     - `src` has no PLR0913 noqa today. The only ones are on the examples' `main`
       functions, each with a stated reason.
   - **Fix:** put the decision in the plan, because S4 and S5b share these signatures. Either
     use a recorded `# noqa: PLR0913 (reason)` on the three primitives, or reshape them to at
     most 6 parameters. For `label_grid`, use a frozen label-style record, for example
     `label_grid(img, spec, columns, rows, style, *, extra=())`. The round-trip function in
     finding 1 also needs at most 6 parameters.
3. **[SHOULD-FIX] S2 names one of the two brush rows that change (plan :204-207, `tasks.md`
   :44-46).**
   - **Evidence:** `test_theme_check.py:177-179` (`LAN9-z`) changes too. I checked the
     nearest ids at cutoff 0.6: `LAN9-z` gets `LAN8-a`, and `MAJ9-a` gets `MAJ8-a`.
   - **Fix:** name both rows, with their exact new messages, and state that `nearest`
     returns one name for these messages.
4. **[CONSIDER] `Colour.parse`'s parameter type.** If it is annotated `object`,
   `test_public_signatures` reports it, because `object` is not in `ALLOWED`
   (`_public_surface.py:30-69`). Annotate it `str` and check the type at runtime.
5. **[CONSIDER] The glossary entry.** S7 should rewrite `GLOSSARY.md`'s "colour alias" entry
   to say that an alias stands for a pigment.
6. **[CONSIDER] A chain whose parent cannot be read.** When the child is checked from the base
   up, it would report a cascade of "is not a pigment or a colour alias" problems for names
   the unreadable parent defines. State whether the files below a failed read are still
   checked.

## Round 4 resolution

- **1 (BLOCKING).** `tutorial_grids.py` keeps `_layout`, `_labels` and `_letter` with today's names and signatures (`tutorial_grids.py:92`, :119, :162), each a delegate. The seven quoted grid functions are not edited, so every block `test_tutorial_quotes.py:24-34` checks stays a substring, and `paint-a-watercolour.md` (quotes and the prose at :36) is not edited; no image moves (plan :879-901). The round trip is `letter_over(img, settings, nib, *, gran_px, seed, ground=None)`, called by `label_grid` and by every script's `_letter` or `_lettered` (`nib_stages.py:195`, `brush_sheet.py:138`, `wash_stages.py:99`, `how_to_route_ink.py:157`), so the `RGBa` guard holds (plan :862-870, :896-902). `support.examples.load_example` puts `EXAMPLES_DIR` on `sys.path` for the call; `run_example` uses it, and S6 owns `test_sheet_script_lists_exactly_the_table_ids` (`test_reference_pages.py:227-232`), which loads `brush_sheet.py` through it (plan :906-915). Label tuples, lettered names and `BRUSH_IDS` stay literals (`test_captions.py:185-205`; plan :903-905). The `change-the-route-ink.md:79` quote is left byte-identical.
- **2 (BLOCKING).** No `# noqa: PLR0913`. The effect value types `Casing`, `Glow`, `Shadow` and the new `PenCasing` move to `ink/effect_types.py` (S4), with `EFFECT_RANGES`, because `maps` cannot define a type the `ink` primitives take. Each primitive takes its value type plus the arrays: `casing(rgb, mask, effect, *, threshold, paper=None)`, `glow(...)` the same, `shadow(rgb, mask, effect, *, azimuth_deg, threshold)`, `pen_casing(rgb, mask, effect, *, threshold, paper=None)`, 5 parameters each (plan :557-614). `label_grid(img, boxes, columns, rows, style, *, extra=())` takes a frozen `LabelStyle` (6); `letter_over` has 6; `lay_stack` has 5, scaling `*_px` by `dataclasses.replace`. Probed with ruff in the scratchpad (`r4fix/probe.py`): only the old `casing` shape fails (7 > 6). Every other planned function is at most 6. Knock-on: S4 is cut after S3a (it needs `Colour` and `normalise_colours`), merge gate A moves before S5a and exports eight names, `maps` exports only `EffectStack`. Spec :127-140 and the Changelog, ADR 0070 rule 11 and "Public names", and the ownership table and Decisions follow (plan :77, :102-106, :794-801, :1163-1168).
- **3.** Both rows named with exact messages: :177-179 "'LAN9-z' is not a brush on the sheet; did you mean LAN8-a?" and :182-183 "'MAJ9-a' ... did you mean MAJ8-a?", checked with difflib over the 112 ids; `nearest` is `n=1`, so it returns one name (plan :135, :221-226).
- **4.** `Colour.parse(text: str)`, annotated `str` with a runtime check; the `5` and `None` test calls carry `# ty: ignore[invalid-argument-type]`, as `test_wash.py:40` does (plan :167-172).
- **5.** S7 rewrites `GLOSSARY.md:95` ("colour alias") to say an alias stands for a pigment (plan :950; `tasks.md` S7). The glossary is not edited now.
- **6.** Rule: a chain whose read stops checks no file, those above the stop included; only the read and `extends` problems are reported. Tested in `test_theme_resolve.py` (a child with a bad field and an unbound alias, extending a missing file, reports one problem). No existing case combines the two, so all pass unchanged (`test_theme_resolve.py:184-226`; plan :445-458).

## Round 5

Reviewer: fresh-context plan reviewer, on `70ccd61`. I checked each "Round 4 resolution" item
against the code, probed the signatures with ruff, and swept every slice against `tests/`
once more. Experiments are in the session scratchpad (`r5/`).

### Verdict: PASS

There are no BLOCKING findings. Round 4's two blockers are fixed, and the sweep found no
existing test that a slice breaks without owning it. Five SHOULD-FIX items are listed below.
An implementer can absorb each of them, but finding 1 will turn S4's property tests red if
it is executed literally.

### Resolutions verified

- **Effect value types in `ink`.** `ink/effect_types.py` holds `Casing`, `Glow`, `Shadow`,
  `PenCasing` and `EFFECT_RANGES` (plan :557-576). The spec (:127-141), ADR 0070
  (:236, :312-317) and `tasks.md` (:117) agree, and no stale loose-field signature is
  left.
- **Parameter counts.**
  - `max-args = 6` (`pyproject.toml:162`). PLR0917 is preview-only and not selected.
  - I ran `ruff check --select PLR0913` on `r4fix/probe.py` inside `src/`. Only the old
    `casing` shape fails (7 > 6).
  - `casing`, `glow`, `pen_casing`, `shadow` and `lay_stack` have 5 parameters each.
    `letter_over` and `label_grid` have 6. The `_layout`, `_labels` and `_letter`
    delegates keep 5, 4 and 5.
  - `GridSpec` and `LabelStyle` are dataclasses, so their fields are exempt.
- **Cut points.** Every place that states the cut agrees: plan :103-106, :1095 and
  :1113-1117, and `tasks.md` :3-5. S4 needs only S1's `pigment` and `Colour` and S3a's
  `normalise_colours`. S4 owns only new files. S3b touches no `ink` file.
- **Eight `ink` exports.** The plan (:798), `tasks.md` (:124) and the ADR (:314-316) list
  the same names. `test_site.py`'s submodule rule holds: the stems are `effect_*`, and no
  `ink/{casing,glow,shadow}.py` exists.
- **`maps` exports.** `maps` exports only `EffectStack`, plus S3b's `Palette` (spec
  :140, ADR :316-317).
- **Tutorial quotes.**
  - I mapped every `<!-- from examples/... -->` block to the functions it covers.
  - In `tutorial_grids.py` the quotes cover :193-330 (the seven grid functions only). In
    `how_to_route_ink.py` the quote covers :214-228 (`_grid`).
  - S3a's wraps fall outside every quoted block: `tutorial_grids.py:83` and `:110`,
    `how_to_route_ink.py:112`, and the lines in `nib_stages`, `brush_sheet`, `wash_stages`
    and `pigment_swatches`. So do the helper bodies S6 rewrites (`tutorial_grids.py:92-190`).
  - Every block stays an exact substring.

### Sweep: checked and still green

- **Glossary code names.** `PIGMENTS`, `PigmentLayer` and `brush_sheet` still resolve, and
  each is still the exported name (`test_glossary.py:243-268`).
- **Dotted docs paths.** Only `references.md` names `pyntpot.ink.pigment.*`, and it is
  S1's.
- **Retired words and the docstring spec-number rule.** Neither is touched.
- **Other `runpy` callers** (`test_glyph_sheet`, `test_painting_with_python_*`). None of
  them loads the five scripts. `make_docs_images` and `test_explanation_figures` go
  through `run_example`.
- **Strict pydantic at S1.** `dict[str, str]` turns a `Colour` back into a plain `str`
  (probed), so no group meets a type mismatch before S3a. `RESOLVED_SAMPLE` samples no
  `cover.pigments` entry.
- **`style-fields.md` comparator.**
  - An empty `### \`basemap.line_effects\`` table parses (`test_reference_values.py:40-50`).
  - Only `Mapping` fields need a key sub-table (:198-203), so `route_ink.effects` needs
    none.
  - A `Colour` field's Type cell stays "string".
- **Modules and packaging.** `test_import_order.MODULES` is not required to be exhaustive.
  `uv_build` packages `maps/palettes/`. No example stem clashes with the standard library,
  `tests/` or `src/` once `examples` is a ty root.

### Findings

1. **[SHOULD-FIX] `EFFECT_RANGES` has no upper bound, and the prescribed strategies fail
   the S4 gate (plan :569-573, :609-613).**
   - **Evidence, unbounded fields.** "Every `*_px` is at least 0" accepts `inf` and
     1e12.
     - Strict pydantic and ruamel both accept `.inf` (probed).
     - `noise.blur(m, 1e12)` raises `MemoryError`, because `np.pad` pads by `r`
       (`noise.py:179`). `blur(m, inf)` raises `OverflowError`, and so does
       `round(inf * sin b)` in `shadow`.
     - So strategies "drawn inside `EFFECT_RANGES`" go red under Hypothesis.
     - A theme's `blur_px: .inf` would pass the load check and then crash the painter.
   - **Evidence, `threshold`.** `floats(0, 1, exclude_min=True)` draws subnormals. In
     float32, `mask / threshold` overflows or divides by zero, and warnings are errors.
   - **Fix:**
     - Prescribe `EFFECT_RANGES: Mapping[str, tuple[float, float]]`, keyed by field name.
       All three slices read it.
     - Make every bound finite (for example `*_px` from 0 to 64, `strength` from 0 to 1).
     - The types refuse a value that is not finite.
     - Strategies use `allow_nan=False, allow_infinity=False`, and `threshold` is drawn
       from `floats(0.01, 1)`.
2. **[SHOULD-FIX] `from pyntpot.ink import EFFECT_RANGES` fails (plan :636-637, `tasks.md`
   :144-145).**
   - **Evidence:** `EFFECT_RANGES` is not one of the eight exports. No `maps` module imports
     the `pyntpot.ink` package: every one imports a submodule (`maps/*.py`, for example
     `theme_check.py:37`).
   - **Fix:** `line_effects.py` and `theme_effects.py` import from
     `pyntpot.ink.effect_types`, and S5b imports `LINE_THRESHOLD` from
     `pyntpot.ink.effect_mask`.
3. **[SHOULD-FIX] Gate A turns on two public-surface tests that S4's gate never ran (plan
   :794-800).**
   - **Evidence:**
     - Once exported, the four types fall under `test_field_docs` (an `Attributes:` entry
       per field, in order, and no class-body comments).
     - The primitives' `Raises:` entries fall under `test_public_signatures`.
     - Neither test applies in the worktree, and gate A owns only `ink/__init__.py`,
       `ink.md` and `test_public_api.py`.
   - **Fix:** S4 writes those docstrings to the public standard now. Alternatively, gate A
     is allowed to edit `effect_*.py` docstrings.
4. **[SHOULD-FIX] A non-string `extends` is not placed in the read-first chain (plan
   :441-452).**
   - **Evidence:** today `check_theme` drops `extends: 5` and reports it
     (`test_theme_check.py:67-73`). `resolve` then ends the chain
     (`theme_resolve.py:136-137`).
   - **The risk:** if an implementer counts it as a "stopped read", no file is checked and
     no read problem exists. The theme would then load silently.
   - **Fix:**
     - State that a non-`str` `extends` ends the chain without stopping the read, so the
       file is checked and reports "extends is a theme name or a .yaml path".
     - Add that case to `test_theme_resolve.py`.
5. **[SHOULD-FIX] The `line_effects` split must add only what the file writes (plan
   :703-704).**
   - **Evidence:** `test_theme_check.py:62-65` pins `check_theme`'s table exactly.
     Unconditionally adding `route_ink: {effects: EffectStack()}` would fail that test. It
     would also turn off a parent's route stack in every child.
   - **Fix:** a file without `line_effects`, or without its `route` key, adds no
     `basemap.line_effects` or `route_ink.effects` entry.
6. **[CONSIDER] The stated reason for S6's ty `root` edit is wrong (plan :917-921).**
   - **Evidence:** `unresolved-import = "warn"` (`pyproject.toml:200`), so `ty check`
     would not exit 1 on the sibling import.
   - **Fix:** the edit is still right, because it types `labelled_grid`'s names. Restate
     the reason. Also, `test_reference_pages.py` loses its only `runpy` use, so S6 drops
     `import runpy` (F401).
7. **[CONSIDER] `painter/effects.lay_wash` has no signature (plan :820-824).** It needs
   the ground, the sea and rim, the layers, the masks, the stacks, the scale and the paper.
   Bundle them (for example `job` and `style`) so it stays at most 6 parameters.
