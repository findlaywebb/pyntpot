# 009 PR 1: fresh-context diff review

Reviewed `git diff origin/main...HEAD` (merge base `dfc37472`, 46 commits, 145 files) against
`spec.md`, `plan.md`, `tasks.md`, ADR 0070, `CLAUDE.md`, `CONTRIBUTING.md` and `BOUNDARIES.md`.
Order: `src/`, `examples/`, `tests/`, `docs/`. Uncommitted work from the concurrent
mutation-test agent was ignored (the tree was clean when the review ran).

Note: a stale local `origin/main` first showed 91 golden PNG/WebP files as changed. After
`git fetch`, the real diff touches no image. Review against a fetched `origin/main`.

## Evidence gathered

- **Pins.** `git diff origin/main...HEAD --stat -- tests/golden docs/images` lists only
  `tests/golden/grid_hashes.py` (new) and `tests/golden/make_docs_images.py` (made
  `fixture_options` public). No PNG, WebP or JSON pin changed. The only 16-hex literals the diff
  adds are `DEFAULT_DIGESTS` in `tests/unit/maps/test_digest_omits.py:14`, equal to
  `DIGEST`, `BASE_DIGEST` and `LETTERING_DIGEST` in `test_style.py:56-58`, which the diff leaves
  unchanged. No packaged or example theme YAML is touched.
- **Gates run here.** `uv run pytest -n auto --dist loadgroup -m "not golden" --golden-tolerance`
  exit 0. `ruff check .` clean. `lint-imports`: 3 contracts kept. `pyproject.toml` changes
  only by S6's one `[tool.ty.environment] root` line. Not run: `ty`, `prek`, the golden suite.
- **Boundary.** No `pydantic` or `ruamel` import under `src/pyntpot/ink` or `letters`. `Colour`'s
  pydantic hook is a plain-dict core schema (`ink/colour.py:85-98`).
- **No silent fallbacks.** Bad themes were loaded through `Style.from_yaml` in the scratchpad,
  and one through the CLI. Every one failed at load with file, line, dotted key path and the
  nearest name:
  - pigment and alias misses: `ultramarin`, `lak`, `payns_grey`
  - brush id: `MAJ9-a`, did you mean `MAJ8-a`
  - line class: `majro`
  - effect key: `glo`
  - effect field: `strenght`
  - preset: `casd`
  - palette: `plan`, did you mean `plain`
  - range and non-finite values: `17`, `1.5`, `.nan`, `.inf`
  - built-in preset or pigment name reused
  - alias chains and a missing `override`
  - loader-only fields set inside their group
  - bad `.gpl` rows
  `pyntpot map ... --style p4.yaml` exited 2 and created no cache directory, so no fetch ran.
  `extends` behaved by rule 7: a child's `major: {}` turns off the parent's `cased`, and a
  rebound alias does not recolour the parent's `route_ink.colour` (`#2c3346` kept).
- **Hypothesis properties are present.**
  - Casing width 0 identity, `-0.0` included: `tests/property/test_line_effects.py:62`.
  - Glow never darkens: `:93`.
  - Shadow never paints over its line, bit for bit: `:121`.
  - Pen casing width 0 and reserve: `:150`, `:166`.
  - Empty extension identity: `tests/property/test_pigment_registry.py:37`.
  - Caller pigment never shadows a built-in: `:44`.
  - `Colour.rgb` equals `rgb`: `:63`.
  - `pigment(hex)` is anonymous: `:69`.
  - Off or empty `line_effects` moves no digest: `tests/property/test_line_effect_digests.py:42`.
  - Preset expansion: `tests/property/test_line_effect_presets.py`.
  - Alias and `.gpl` round trips: `tests/property/test_theme_colours.py`, `test_palette_gpl.py`.
- **Schema and size.** The `Colour` three-branch schema walk is in `test_theme_schema.py`, and
  both schema copies are regenerated and checked by it. No `src/` file is over 400 lines (largest
  `maps/osm_elements.py`, 387, untouched; `style_groups.py` is 342).

## Findings

### 1. BLOCKING: `PigmentRegistry.extended` does not point at the derived form

`src/pyntpot/ink/pigment_registry.py:74-86` and `:40`.

Spec, "One pigment registry": "A name that equals a built-in raises `ValueError`, and the message
points at the derived form (`base: <name>`)." The code reuses `__post_init__`'s duplicate check,
so `PIGMENT_REGISTRY.extended((Pigment(name="wood", ...),))` raises `duplicate pigment 'wood'`,
which was confirmed in the scratchpad. The theme path does point at the derived form
(`theme_pigments.py:69`, `my_wood: {base: wood}`), but the `ink` API the criterion names does not.
The tests pin the weaker message (`tests/unit/ink/test_pigment_registry.py:133`,
`tests/property/test_pigment_registry.py:47`).

Fix: in `extended`, before building, loop over `added` and refuse a name already in `self`:

```python
raise ValueError(
    f"{p.name!r} is already a pigment; derive one instead: my_{p.name}: {{base: {p.name}}}"
)
```

Leave `__post_init__` for repeats within `added`. Update both tests to match `base: wood`.

### 2. SHOULD-FIX: the `theme_check` module docstring is stale

`src/pyntpot/maps/theme_check.py:21-25`.

The docstring says "colours must be `#` and six hexadecimal digits" and "Does not ... check
numeric ranges". A colour field now takes a hex, a pigment name or an alias. This module now
dispatches `theme_effects`, which range-checks every effect number. Module docstrings are the
agent contract (CLAUDE.md).

Fix: "colours must be a hex, a pigment name or an alias in the file's scope". Change the "Does
not" line to "does not check a style group's numeric ranges (`theme_effects` checks a line
effect's, against `EFFECT_RANGES`)".

### 3. SHOULD-FIX: new test file over the 400-line budget

`tests/unit/maps/test_theme_effects.py` is 426 lines.

CLAUDE.md's soft budget is "400 lines/file". The plan put new cases in new files to keep tests
under it. Only `src/` is enforced, so the gate is green.

Fix: move `TestThePresets` (`:281-379`) and `TestTheMergeDownExtends` (`:380-`) to
`tests/unit/maps/test_theme_effect_presets.py`. This is a pure move.

### 4. SHOULD-FIX: `tasks.md` S4 boxes are unticked though S4 is merged

`specs/009-line-effects-and-registry/tasks.md:115-130`.

Both S4 task lines are `[ ]`, but merge gate A is `[x]` and the code and tests exist
(`ink/effect_*.py`, `tests/unit/ink/test_effect_types.py`, `test_effects.py`,
`tests/property/test_line_effects.py`).

Fix: tick both lines.

### 5. SHOULD-FIX: glossary code columns empty for the new effect terms

`GLOSSARY.md:39-45`.

S7's task "code columns" is ticked, but `line effect`, `effect stack`, `effect preset`, `casing`,
`glow` and `shadow` have empty code columns, though public names exist.

Fix:
- effect stack: `pyntpot.maps.EffectStack`
- casing: `pyntpot.ink.Casing`, `pyntpot.ink.casing`, `pyntpot.ink.PenCasing`, `pyntpot.ink.pen_casing`
- glow: `pyntpot.ink.Glow`, `pyntpot.ink.glow`
- shadow: `pyntpot.ink.Shadow`, `pyntpot.ink.shadow`

Then regenerate with `PYTHONPATH=tests uv run python -m support.glossary`.

### 6. CONSIDER: replace the `# noqa: RUF009` comments with `extend-immutable-calls`

`ink/style.py:84`, `letters/style.py:116,128-130`, `maps/style_groups.py:335,338`.

RUF009 honours `lint.flake8-bugbear.extend-immutable-calls`. With
`["pyntpot.ink.colour.Colour", "pyntpot.maps.line_effects.EffectStack"]` set, RUF009 passes on
`src` and RUF100 then flags the comments as unused, which was checked here. One config line is
better than seven comments, and it covers future `Colour` fields too. However, the plan
restricts `pyproject.toml` to S6's one line. So keep the comments in this PR and make the
config change a follow-up `chore` (a lint setting, not an import contract; no ADR needed).
Note also that `effect_types.py` already avoids the comment with a module constant (`_WHITE`).
The repo should pick one convention.

### 7. CONSIDER: water and road groups are split by position

`src/pyntpot/maps/line_effects.py:35,38`.

`WATER_GROUP = _BASEMAP[:4]` and `ROAD_GROUP = _BASEMAP[4:]` rely on `BrushStyle().brushes`'
insertion order. A brush class added or reordered there would silently move a class into the
wrong paint group.

Fix: write the two tuples as literals, and assert that their union equals `_BASEMAP` (or test
it).

### 8. CONSIDER: `override: true` with nothing to override is accepted silently

`theme_colours.py:110`, `theme_pigments.py:76-80`, `theme_effects.py:138-141`.

`colours: {lake: {colour: ultramarine, override: true}}` with no inherited `lake` loads cleanly,
as do the `pigments` and `effect_presets` equivalents. A misspelt alias under `override` then
binds a new name without warning, which is close to the "never silently" bar.

Fix: record a problem such as "'lake' overrides nothing; drop override". Or decide it is
harmless and say so in the three docstrings.

### 9. CONSIDER: `check_effect_presets` rebuilds the scope by hand

`src/pyntpot/maps/theme_effects.py:89-91`.

It builds `ThemeScope(pigments=..., palette=..., aliases=..., presets=...)` by hand, where the
sibling modules use `dataclasses.replace(scope, ...)`. A field added to `ThemeScope` would be
dropped silently here.

Fix: `return dataclasses.replace(scope, presets=presets)`.

### 10. CONSIDER: unreachable branch in `_derive`

`src/pyntpot/maps/theme_pigments.py:121-122`.

`if colour is None: return None` cannot be reached. `_pigment` already returns when neither
`base` nor `colour` is given, or when either failed (the problem count grew).

Fix: drop the branch, or assert it.

### 11. CONSIDER: misleading pen-casing test docstring

`tests/property/test_line_effects.py:173`.

"Inside the reserve, minus the edge band" is wrong: the band lies outside the reserve, and the
test asserts exactly that (`not edges[reserve].any()`).

Fix: "Inside the reserve the output is the paper, outside it the wash; the edge band lies
outside the reserve and is 0 or 1."

### 12. CONSIDER: overlong docstring line

`src/pyntpot/ink/brush.py:6`.

The module docstring line now runs to about 120 characters after `brush_ids` was inserted.

Fix: reflow the paragraph to the file's width.

### 13. CONSIDER: `.gpl` problems name only the palette file

`theme_palette.py` and `theme_palette_gpl.py`.

A bad `.gpl` row is reported as `bad.gpl:5: ...` and does not name the theme's `palette:` key
that loaded it. With a chain of themes, the user has to find which file chose the palette.

Fix: append "(chosen at <theme>:<line> palette)" to the problems, or add a leading problem at
the `palette:` line.

## Summary

| Severity | Count |
|---|---|
| BLOCKING | 1 |
| SHOULD-FIX | 4 |
| CONSIDER | 8 |

Everything else checked matches the spec and plan:
- The registry and its four tables are built from it, and the single-literal guard holds.
- The brush tables are read-only, with nearest-id messages.
- `Colour` is on every colour field, with `__post_init__` normalisation and no `COLOUR_FIELDS`.
- Aliases, pigments and palettes bind down `extends`.
- The effect primitives are pure, take at most 6 parameters and refuse a bad threshold.
- `EffectStack` and the presets are in place, with the loader-only split, off dropped after the
  merge and the range checks.
- The painter's default path is one `composite`, and compose's default path is unchanged.
- Route effects never write `pen.webp`.
- The grid helper is in place, with the `labelled_grid` sibling.
- Nothing the plan excludes is in the diff.

## Resolution

- 1: `PigmentRegistry.extended` refuses a built-in name with "to change it, name a new pigment with base: <name>"; both tests updated; the theme path already carried file, key path and line.
- 2: `theme_check` docstring now says colours are a hex, pigment name or alias, and names `theme_effects` for effect ranges.
- 3: `TestThePresets` and `TestTheMergeDownExtends` moved to `tests/unit/maps/test_theme_effect_presets.py`; both files under 400 lines.
- 4: S4 task lines ticked.
- 5: Glossary code columns filled for effect stack, casing, glow, shadow; glossary outputs regenerated.
- 6: `extend-immutable-calls` for `Colour` and `EffectStack` added to `pyproject.toml`; all seven `# noqa: RUF009` removed; ruff passes.
- 7: `WATER_GROUP` and `ROAD_GROUP` are literals; the existing test pins their union to `BrushStyle().brushes`.
- 8: `override: true` with nothing to override is a located error for aliases, pigments and presets; new tests for each.
- 9: `check_effect_presets` uses `dataclasses.replace`.
- 10: the unreachable `_derive` branch is now an assert; `_derive` returns `Pigment`.
- 11: pen-casing test docstring corrected.
- 12: `brush.py` module docstring reflowed.
- 13: a bad palette file adds a problem at the theme's `palette:` line before the palette file's own problems.

## Elegance pass

Reviewed `git diff origin/main...HEAD -- src examples tests` for simplification only. Behaviour
is unchanged: no pixel, hash, digest, message or public name moved, and every gate passed after
the edits.

Applied:

- **One `did_you_mean` suffix.** Nine sites built `; did you mean X?` by hand (one through
  `difflib` directly, bypassing `nearest`). `ink/naming.py` now has `did_you_mean(name, known)`,
  and `brush`, `pigment_registry`, `line_effects`, `theme_checker` (twice), `theme_scope`,
  `theme_effects`, `theme_palette` and `theme_colours` use it. The messages are byte for byte
  the same.
- **Pen water strokes.** `painter/pen.py` names the stroke tuple (`_Stroke`) and adds
  `_lay_strokes` and `_coast_lines`, so `_water_pad` and `_water_masks` no longer repeat the
  unzip-and-lay and the coastline comprehension. The order in which strokes are laid and the
  seeds stay as they were.
- **Theme test helpers.** Five test modules each had their own `_write` and two their own
  `_scope`. These are now `write_theme` and `scope_of` in `tests/support/theme_files.py`.

Rejected:

- A `paper_ground(paper)` helper for `F32(1.0) if paper is None else paper` in the casing, glow
  and pen-casing primitives: it is one expression, clearer inline than as a name in
  `effect_mask`.
- A `TableCheck` method for the five top-level `is a table of keys` guards: each returns a
  different fallback (`scope`, `{}`, `None`), so a shared guard would need a type-narrowing
  return and save little.
- Sharing `_problems`, `_style` and `_check` between `test_theme_effects.py` and
  `test_theme_effect_presets.py`: there are only two copies, and the problem tuple shape differs
  from module to module.
- Folding `effect_pass._scaled`'s `hasattr` filter into per-type field lists: it is driven by
  `EFFECT_RANGES`, so a new `*_px` field scales without an edit.
- `pen_groups` computes `_water_strokes` twice, once for the pad and once for the masks. It
  draws no random number and is cheap, so threading it through would only widen the signatures.
- Examples: S6 already moved the shared grid layout into `labelled_grid.py`, and nothing
  further was worth changing.
