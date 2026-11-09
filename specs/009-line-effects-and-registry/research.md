# 009 line effects and the pigment and brush registry: research

Status: complete (Phase 1), awaiting decisions. Merges scoped sessions D (route ink) and F (pigment and
brush registry) from `specs/005-feature-scoping/sessions.md`.

Issues: #104, #105, #106, #159, #72, #71, #170, #67, #69, #70.

## Summary

- Issue #71 as written (ink loads YAML) is ruled out by the import contract. Recommend frozen typed Python tables in `ink`, with user pigments parsed in `maps` by the theme reader and checker.
- One `Colour` value type in `ink` (a frozen `str` subclass, lower-case `#rrggbb`). Every theme colour field accepts `#rrggbb` or a canonical pigment name, resolved to hex at the boundary so digests do not move. The schema emits `anyOf` [enum of names, hex pattern].
- One registry of `Pigment(name, colour, transparency|None, aliases)` with one `pigment(ref)` lookup. Caller pigments that collide with a built-in are rejected.
- The map today paints from silent copies of the pigment tables (`CoverStyle.pigments`, `PaperStyle.pigment_transparency`) with no test tying them together.
- The golden hash includes `BASE_DIGEST`, so new fields must be listed in `DIGEST_OMITS_AT_DEFAULT` (names unique) and defaults kept as today's hex, so that PR 1 passes with no regeneration.
- Effects composite on RGB between layers, not as Kubelka-Munk glazes. Casing has an explicit early return at width 0. Glow lifts toward paper and never darkens. Shadow is masked out where line density is at or above tau.
- Draw order: water group, then road group. Within a group, all casings first, then all lines (this matches every prior-art system).
- Route effects live in `route_ink` (compose-time, `digest()` only, about 0.3 s), not in the brush table (`base_digest`, 22 to 59 s repaint).
- #159 root cause is two fields. Fix A (`with_route_ink` also sets `nib.label_route_ink`) moves nothing at the default but moves `docs/images/how-to/route-ink.webp`, which is the fix itself.
- #170 helper is a private sibling module in `examples/`. Prove identity by sha256 of the full-size script PNGs before and after.

## Conflicts with the settled decisions

- (a) #71 YAML in `ink` is ruled out by the import contract.
- (b) #159 moves one docs image, so either PR 2 carries it or it is an accepted exception.
- (c) Any new field moves digests unless it is omitted at its default.
- (d) Theme class keys in code are `major/medium/minor/coast/road_major/lane/track`, not `river/stream`.
- (e) Water is one pad, so per-class water effects cost extra pads.

## Registry and where data is parsed

### 1. Inventory today

**Pigment tables (ink).** `PIGMENTS` (15 map roles → hex, `ink/pigment.py:21-37`),
`TRANSPARENCY` (same 15 → float, `:42-58`), `PAINTERS_PIGMENTS` and
`PAINTERS_TRANSPARENCY` (10 tube names, `:66-93`). All four are exported
(`ink/__init__.py:27-44`) and pinned (`tests/unit/ink/test_pigment.py:120,137`;
`tests/unit/test_public_api.py:32-34`).

**Silent copies the maps actually read.** No `src/` painter reads `PIGMENTS` or
`TRANSPARENCY`. The map paints from `CoverStyle.pigments` (`maps/style_groups.py:160-176`,
a verbatim copy of `PIGMENTS`) and `PaperStyle.pigment_transparency`
(`ink/style.py:89-107`, a copy of `TRANSPARENCY`), via `cover.pigments[...]` at
`painter/cover.py:154,175`, `water.py:153,181`, `wood.py:54,84`, `relief.py:25`,
`plates.py:65`, and `job.transp` (`painter/job.py:152`, falling back to
`km_transparency`). **No test ties the copies to the tables**, so they can drift. The
theme vocabulary is built from the copy, `_PIGMENTS = frozenset(_COVER.pigments)`
(`maps/theme_vocab.py:26`).

**Other colour holders.** `WashStyle.separation_pigments` (`ink/style.py:255`);
`BRUSH_COLOURS`, 14 hex cells across 5 prefixes (`ink/brush_sheet.py:127-140`), returned by
`brush_from_id` (`ink/brush.py:203`) and laid as 2-tuples with **no transparency**
(`painter/pen.py:82,103`, so they take `km_transparency`); four `NibStyle` inks
(`letters/style.py:115-129`); `RouteInkStyle.colour` (`style_groups.py:334`); the four
note colours (`maps/lettering_marks.py:70-73`); `paper_hex` (`ink/style.py:81`) and
`sheet.PAPER` (`ink/sheet.py:24`); the paper tints (`ink/paper.py:26-29`). "Water" alone
has three unrelated colours: wash `#9ec4de`, river ink `#255d80`, label `#4a7691`.

**Count: about 12 places can name a colour** (4 ink tables, 2 style copies, separation,
brush sheet, nib inks, route ink, note colours, paper), of which the theme can reach 8
key paths (`theme_vocab.py:58-67`).

**Brush id tables.** `BRUSH_TREATMENTS` (rows `"1"`-`"8"`, `brush_sheet.py:14-121`),
`PEN_ROWS` (`:124`), `BRUSH_COLOURS`; `BRUSH_OVERRIDE_KEYS` (`ink/brush.py:26`); the
class → id binding `BrushStyle.brushes` (`ink/brush_style.py:181-190`).

**Readers (files / lines, `grep -w`).**

| Name | src | examples | docs | tests |
|---|---|---|---|---|
| `PIGMENTS` | 2 / 6 | 14 / 61 | 15 / 27 | 8 / 36 |
| `TRANSPARENCY` | 3 / 7 | 6 / 22 | 11 / 16 | 4 / 10 |
| `PAINTERS_PIGMENTS` | 2 / 5 | 9 / 34 | 12 / 16 | 4 / 12 |
| `PAINTERS_TRANSPARENCY` | 2 / 5 | 6 / 20 | 7 / 10 | 3 / 7 |
| any of the four | — | 18 files / 112 lines | 22 files | 8 files |
| `BRUSH_COLOURS` | 3 / 7 | 0 | 2 / 3 | 4 / 10 |
| `BRUSH_TREATMENTS` | 2 / 5 | 0 | 2 / 3 | 2 / 6 |
| `brush_from_id` | 5 / 14 | 14 / 54 | 13 / 60 | 11 / 68 |

The four pigment tables' cost is in `examples/` and `docs/`, not `src/`. Brush tables
are internal; `brush_from_id` is the public seam (`letters/nib.py:158`,
`maps/painter/pen.py:62,118`, `maps/painter/brushes.py:57`, `maps/theme_check.py:251`).

*Reconciliation: section B counts 31 lookups across 15 files, whereas this table counts 18 files and 112 lines. The counts measure different things (lookups versus lines mentioning the names), and `review/04-examples.md` is an older snapshot.*

### 2. Where the data is parsed

Constraint: `ink` and `letters` forbid `httpx`, `pydantic`, `ruamel`
(`pyproject.toml`, contract 3); PyYAML is banned package-wide (contract 1). So **#71's
literal shape, `ink/data/*.yaml` loaded by ink at import, cannot be built without loosening
a contract.** It is ruled out.

| | (a) stdlib file in ink (TOML/JSON) | (b) typed frozen literals in ink, user data parsed in maps | (c) packaged YAML read by maps, injected into ink |
|---|---|---|---|
| Contract | fits (`tomllib`, `json`, `importlib.resources` as `letters/font.py:37`) | fits | fits, but ink has no built-ins without maps: an engine-only caller loses `"ultramarine"` |
| Cost | a loader and validator in ink duplicating `theme_check`; package data | a `Pigment` dataclass and registry; the theme block reuses `theme_read`/`theme_check` | a second load path, and an init order |
| Errors | `tomllib` gives a line only for syntax errors (ADR 0069 table); semantic errors need hand-rolled line maps, as ADR 0069 rejected TOML for | built-ins are checked by `ty` and pinned tests; user data gets `path:line: key: …; did you mean …?` for free (`theme_errors.py:38-41`, `theme_check.py:153`) | as (b) for user data |
| Schema | separate JSON Schema to keep | `theme_schema` walks dataclass hints, so a `Pigment` field gets one | as (b) |
| Purity | float parsing is correctly rounded either way; pure, but a new pinned-file gate | values copied literally; pure | pure |

**Recommend (b).** The shipped catalogue stays Python literals in `ink` (a frozen `Pigment`
and a read-only registry); the "declare as data" need of #71 is met by the theme's
`pigments:`/`brushes:` blocks, parsed and checked in `maps` beside every other theme key,
and by an engine call (`registry.extended(...)`) for direct callers. Two gaps to close
whatever is chosen: an unknown name passed in engine code must raise `ValueError` with a
`difflib` suggestion (stdlib, allowed in ink; today `PAINTERS_PIGMENTS["ultramarin"]` is a
bare `KeyError`), and **brush ids get no suggestion today** (`theme_check.py:251-252`,
`ink/brush.py:196`). Theme loading already precedes any fetch, so "fail at load" holds.

### 3. Roles and painter's names in one lookup

There is no role → pigment indirection: a role *is* a key, and its colour and
transparency live in two different groups (`cover` and `paper`). Painter's names are a
disjoint second namespace that no theme may name (vocabulary is roles only).

Proposal: one registry keyed by canonical name, each `Pigment(name, colour,
transparency: float | None, aliases)`. Today's 15 roles and 10 tubes are all entries
(role names canonical for now, so nothing renames). One function,
`pigment(ref: str | Pigment) -> Pigment`, resolves a `Pigment` as itself, then a name, then
an alias, then a `#rrggbb` (an anonymous pigment with `transparency=None`); otherwise
`ValueError` with the nearest name. `None` means "take `km_transparency`", which is what
2-tuples and brush ink do now; a default of 0.06 instead would move pen pixels. The map
role stays a **binding** (`cover.pigments[role]` → a pigment ref) owned by the theme, not a
registry entry the theme rewrites.

### 4. Override semantics

Two operations must not be confused: **rebinding a role** (`cover.pigments.built:
"#f0b86a"`, done by `bold.yaml:46-47` and `pen-and-ink.yaml:39-40`; keep the per-entry merge)
and **adding a pigment** (a new registry name). For the second, **reject** a name or alias
that equals any built-in name or alias, with a located error that points at a derived form
(`my_blue: {base: ultramarine, transparency: 0.3}`, the theme's `Pigment.replace`).
Shadow-with-warning is out: warnings are errors in tests and the goal is "never silently";
namespacing (`user:ultramarine`) adds syntax for a collision that rejection already
prevents. The registry is immutable; extension returns a new one, so no module global
mutates under `pytest-randomly`/xdist.

Property tests: `extended({})` equals the base and resolves every name identically; any
extension containing a built-in name or alias raises; a non-colliding extension leaves
every built-in resolution unchanged and does not mutate the base; names and aliases are
unique across the registry.

### 5. What could move pixels, and the proof

- **The converter.** `rgb` divides in float64 then casts to float32
  (`ink/sheet.py:42`). A `Pigment` that precomputes channels another way (float32 division)
  can differ by one ulp. Keep `rgb` the one converter.
- **Transparency appearing.** Pen ink and many examples lay 2-tuples; resolving a name that
  attaches a transparency to them changes Kubelka-Munk output. Resolve to `None` where no
  transparency was given.
- **Colour-only rebinding.** A theme that changes a role's hex keeps that role's
  `pigment_transparency`; if a named pigment's own transparency rode along, theme pixels
  would move. Precedence must be `pigment_transparency[role]` → pigment's → `km_transparency`.
- **Order.** Layer order comes from the cover `order` list (`painter/cover.py:119-135`), not
  dict order; the digest is `sort_keys` JSON (`maps/style.py:312`). Low risk.
- **Floats.** `0.10` and `0.1` are the same double; no rounding risk in a literal copy.

Proof: the pinned literals in `test_pigment.py:120,137` stay and a new test asserts each
registry entry equals them; a test that `CoverStyle().pigments` and
`PaperStyle().pigment_transparency` equal the registry's roles (missing today); the
reference sheets painted old-tuple and by-name compared with `np.array_equal`; the
pinned digests (`tests/unit/maps/test_style.py:53-55`) and `GOLDEN_HASH`
(`test_pipeline_fetch_paint.py:30`) unchanged; `make_docs_images.py --compare` on the images
the rewritten examples paint.

### 6. Where the code disagrees with "moves no pinned image and no docs image"

Pixels can stay put, but **pinned hashes will not unless the style shape is held still.**
`GOLDEN_HASH = "90193bbb26f681bf-d9c56c0811177b0f"` embeds `BASE_DIGEST`, and the digest is
`asdict` of every base group (`style.py:298,312`), `cover` and `paper` included. Any of
these moves it: changing `CoverStyle.pigments` values from hex to names, turning them into
`Pigment` objects (`asdict` recurses), merging `pigment_transparency` into `cover`, or
adding a `pigments:`/`brushes:` field to a group (ADR 0069: a new field moves every digest
unless named in `DIGEST_OMITS_AT_DEFAULT`). A digest move invalidates plate caches and
fails `test_the_hash_is_the_golden_hash` even with identical pixels. The pure route:
keep the defaults' values as today's hex strings, sourced from the registry; name any new
field in `DIGEST_OMITS_AT_DEFAULT`. Also, `theme.schema.json` (`maps/themes/` and `docs/`)
regenerates if any theme field's type widens: not an image, but a pinned file. Docs
**text** moves for certain: `docs/reference/pigments.md` is checked against the tables
(`tests/docs/test_reference_values.py:292-305`), and 22 docs pages name the old tables.

## How a theme names a colour

### 1. Today's colour fields

Every colour in the theme model is a plain `str` holding `#rrggbb`. Nothing else: no RGB tuple, no pigment name. The set is listed twice, once by the field and once by hand in `COLOUR_FIELDS` (`src/pyntpot/maps/theme_vocab.py:58-67`).

| Field | Declared | Default |
|---|---|---|
| `paper.paper_hex` | `ink/style.py:81` | `"#f3ead6"` |
| `wash.separation_pigments.*` (class to hex) | `ink/style.py:255` | `{"wood": "#6e7f8b"}` |
| `nib.label_ink`, `label_route_ink`, `label_water_ink`, `label_in_water_ink` | `letters/style.py:115,127-129` | hex |
| `cover.pigments.*` (15 keys: 11 cover classes plus `pale water relief rim`) | `maps/style_groups.py:160` | hex |
| `route_ink.colour` | `maps/style_groups.py:334` | `"#c22050"` |

Related non-colour field: `paper.pigment_transparency` is a dict of class to float (`ink/style.py:89`). Its keys are the same 15 pigment keys, and it duplicates `TRANSPARENCY` (`ink/pigment.py:42`).

How each is expressed and validated:
- **YAML.** A quoted `"#rrggbb"` string, as in `themes/bold.yaml:7,40,68`.
- **Validation.** `theme_check._sheet_and_colour` matches the path against `COLOUR_FIELDS` and `re.fullmatch("^#[0-9a-fA-F]{6}$")` (`theme_check.py:262-271`). The message is "not a # and six hexadecimal digits". There is no case normalisation, so `#C22050` and `#c22050` are different strings and different digests.
- **Callers.** `Style.with_route_ink` has its own copy of the regex and lowercases (`style.py:85-86,247-256`).
- **Hex to RGB.** There are three converters: `ink.sheet.rgb` (`sheet.py:26`), `compose_steps._rgb` (`compose_steps.py:36`) and PIL in `compose_steps.py:118`.
- **Not in the theme.** `CONSUMER_ONLY` lists `label_pin_colour` and `label_glow_colour` (`style_groups.py:35-39`). They are not fields, so #149 and #105 add them fresh.
- **Digest.** `_group_digest` hashes `dataclasses.asdict(group)` as `json.dumps(..., sort_keys=True, default=str)` (`style.py:285-313`). A hex `str` therefore hashes as itself.
- **Pigment tables.** `PIGMENTS` and `TRANSPARENCY` are map-role keyed. `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` are painter-named (`pigment.py:21,42,66,82`). Neither is reachable from a theme by name.

### 2. Examples that look up pigments or hardcode colour

This matches `specs/005-feature-scoping/review/04-examples.md`, F5 (lines 166-190), which says 18 files and 18 lookups. My count today:
- `rgb(PIGMENTS[…])` or `rgb(PAINTERS_PIGMENTS[…])` appear 31 times across 15 files.
- `rgb(PIGMENTS[…])` alone appears in 12 files.
- There are 17 `…TRANSPARENCY[…]` lookups.
- The review's 18 and 18 are probably an older snapshot or counted differently. Quote "about 15 to 18" unless it matters.

Files looking up the pigment tables: `fern.py:144-158`, `fern_family.py:188`, `word.py:107`, `trees.py:342`, `curves.py:151,191,201`, `wash_stages.py:137-214`, `pigments.py:64`, `derwentwater.py:194-227`, `kaleidoscope.py:162`, `site_theme.py:293-304`, `wash.py:54`, `composition.py:92,114`, `tutorial_grids.py:219,264,314`, `how_to_own_shapes.py:146`, `nib_stages.py:135`, and `svg_drawing.py` (its own `_COLOURS` and `_TRANSPARENCY`, lines 189-266).

Hardcoded hex is found in:
- `how_to_route_ink.py:84,99,112`
- `tutorial_grids.py:83,110`
- `derwentwater.py:246`
- `brush_sheet.py:152`
- `wash_stages.py:113`
- `nib_stages.py:140,250,262,271`
- `examples/themes/*.yaml`, where `#7b2335` is the route colour in all six
- docs prose: `docs/gallery.md:169`, `docs/explanation/how-the-wash-works.md:106-107`, `the-hand-and-the-nib.md:102`

No example hardcodes an RGB float tuple as a colour.

### 3. Recommendation: both, in every colour field, through one type

**Accept both.** A theme colour is `#rrggbb` or a pigment name, in every colour field, through one type. Trade-offs:

- **Authoring.** Names read as intent (`sap_green`) and survive a registry retune. Hex is unavoidable for brand colours such as the route's `#7b2335`, which six example themes repeat.
- **Schema completion.** An enum of names gives completion. `anyOf: [{enum: names}, {pattern: hex}]` gives completion and still allows hex. A hex-only field gets no completion today.
- **Error quality.** yaml-language-server reports a failed `anyOf` badly. Our checker already has `difflib` nearest-name (`theme_check.py:163-168`), so unknown names get "did you mean `sap_green`?". Keep the checker as the quality path and the schema as the completion path.
- **Digest stability.** Resolve to canonical lower-case `#rrggbb` at the boundary. Existing hex themes then hash identically, provided they are already lower-case. I found no upper-case hex in the shipped or example themes. A name hashes as its hex, so retuning a pigment repaints, which is correct.
- **Round-tripping.** Resolving to hex loses the name. No YAML writer exists (grep finds no `dump`, `to_yaml` or `model_dump` use), so nothing round-trips today. Only revisit this if a theme writer is planned.
- **"One name per colour".** A hex literal is a value, not a name, so it does not break the rule. Aliases such as `blue` for `ultramarine` would break it in themes. Accept only canonical names in themes; aliases stay a Python-API convenience.

**The value type.** Define `Colour` in `ink`, as a frozen `str` subclass holding canonical `#rrggbb`, with `.rgb` and `Colour.parse(text)`. It is not a dataclass.
- `_is_dataclass(hint)` would treat a dataclass `Colour` as a sub-table (`theme_check.py:285`), and `asdict` would hash a dict instead of the string.
- A `str` subclass keeps `==`, `json.dumps`, `asdict`, `_json` and all existing defaults working.
- It replaces the three hex converters.
- It removes `COLOUR_FIELDS`: the schema walker tests `hint is Colour` instead of `path in COLOUR_FIELDS` (`theme_schema.py:121`), and `test_theme_vocab.py:62-69` retires.

**The maps adapter.** `ink` stays pydantic-free (`BOUNDARIES.md:21`).
- In `theme_check._adapter`, map `Colour` to `Annotated[Colour, BeforeValidator(parse_theme_colour)]`.
- `parse_theme_colour` is a maps function: `#`-prefixed goes to `Colour.parse`; anything else goes to the registry, with the nearest-name suggestion on a miss.
- Keep it strict: no `"#abc"` shorthand, no CSS names.

**Pigment-valued fields.** `cover.pigments` carries transparency on a parallel field, so it needs a fork.
- Option A: keep it colour-only and leave `pigment_transparency` as is.
- Option B: make it class to pigment, so a name brings its transparency. A hex then gets `km_transparency`, as ink does today (`ink/style.py:61`).
- Option B retires `pigment_transparency` for named pigments, but it moves `Style` fields and so needs an ADR (the 0069 amendment path).

### 4. Schema generation and checking

- **Generator.** `theme_schema()` walks the style dataclasses (`theme_schema.py:60-81`) and is pure.
- **Colour leaf.** `_leaf_schema` emits `{"type":"string","pattern":COLOUR_PATTERN}` for paths in `COLOUR_FIELDS` (lines 120-122).
- **Key enums.** Dict fields get `propertyNames.enum` from `VOCABULARIES` (`_entries_schema`, lines 135-142). Descriptions come from each `Attributes:` docstring.
- **Committed copies.** There are two: `src/pyntpot/maps/themes/theme.schema.json` and `docs/reference/theme.schema.json`.
- **Regeneration.** `PYTHONPATH=tests uv run python -m support.theme_schema` (`tests/support/theme_schema.py`).
- **Check.** `tests/unit/maps/test_theme_schema.py:122-128` fails if either committed copy differs from `theme_schema()`. It also checks every field has a default and description, and that every shipped theme has no keys outside the schema.
- **Editors.** Themes carry `# yaml-language-server: $schema=…` (`themes/bold.yaml:1`, `docs/how-to/write-a-theme.md:15`).

What the new fields need:
- **Colour fields.** Change `_leaf_schema` so a `Colour` hint emits `anyOf: [{enum: sorted pigment names}, {pattern}]`. Name the enum from the registry, so a new pigment appears with no edit.
- **Per-line-class effects.** The new `dict[str, EffectStyle]` gets its key enum via one `VOCABULARIES` entry computed from defaults, for example `frozenset(BrushStyle().brushes)`. The line-class keys are 7 today: `coast lane major medium minor road_major track` (`pen-and-ink.yaml` brushes). The entry schema comes for free from `_value_schema` on the nested dataclass. `EffectStyle` must be default-constructible, because `_object_schema` calls `group()`.
- **Registry-derived vocabularies.** `_PIGMENTS` in `theme_vocab.py:26` is built from `CoverStyle().pigments`. It should come from the registry.
- **Path caveat.** The schema looks up `VOCABULARIES` by exact path (`.get(path)`), while the checker uses `_matches`. Both work for the existing `"*"` literal paths. Keep new nested vocabulary paths literal-`*` shaped or they will disagree.

### 5. Error machinery

It is already in place, with line numbers plumbed.
- `ThemeProblem(path, key, line, message)` and `ThemeError` hold every problem found, sorted, one per line (`theme_errors.py`). Output reads `file:line: key.path: message`.
- `theme_read` records the 1-based line of every key via ruamel (`theme_read.py:43-49,72`). `_Check.problem` falls back to the nearest ancestor's line (`theme_check.py:157-165`).
- `unknown()` gives renamed-key hints and `difflib` nearest-name (cutoff 0.6).
- `theme_merge.merge` is a pure dict merge with no error role.
- **Gap.** The line is the key's line, not the value's column, so a bad value in a flow-style mapping shares its parent's line.
- **Gap.** The nearest-name logic is local to `_Check.unknown`. It must be factored out to suggest pigment names for a value, not just keys.

## Drawing order and the two drawing paths

### 1. How basemap lines are drawn today

All basemap lines are drawn in the pen phase, `paint_pen` (`src/pyntpot/maps/painter/pen.py:107-110`).
It returns a list of `PigmentLayer`s, which `_wash_plate` adds after the ground, the sea and the
rim and composites in one call (`src/pyntpot/maps/painter/plates.py:54-70`). Lines are never
painted straight onto the plate. Each one is stamped into an `InkPad` accumulator
(`src/pyntpot/ink/pad.py:165-246`), which `pad.read` turns into a density plane, and that plane
is glazed as a layer.

- **Water** is one pad for every watercourse class (`major`, `medium`, `minor`) plus the
  `coast`. It is read back once, with the major river's brush, giving a single layer
  (`pen.py:47-82`). No per-class density exists for water.
- **Roads** get one pad per band, in the fixed order `road_major` → `lane` → `track`
  (`pen.py:39`, `85-104`). Each band is a layer of its own. `lane` and `track` are drawn only
  when `layers.minor_roads` is set (`pen.py:90`).
- Brushes come from `plate_brushes`, keyed `major, medium, minor, coast, road_major, lane, track`
  (`src/pyntpot/maps/painter/brushes.py:47-58`; defaults in `src/pyntpot/ink/brush_style.py:181-191`).

**A mask we can reuse.** Each road band's `pad.read(...)` density (`pen.py:103`) is already the
per-class mask, and an effect can be computed from it without stamping again. For water, the
only mask is the union density (`pen.py:82`). A per-class water effect therefore needs extra
work. One option is a second mask-only pad holding just that class's lines, which reproduces
the same bristles because stroke generators are keyed by seed and points
(`pad.py:192-244`). The other is a geometric `stroke_mask` (`src/pyntpot/ink/raster.py:170`),
but its single width cannot follow a river's own `width_px` and `profile` (`pen.py:58-73`).

**The hook.** Effects go in between `_water_pad` and `_road_pads`, as separate steps in the
`over` list at `plates.py:69`, not inside `InkPad`. An effect never draws from
`job.dither_rng`, because the wood and the plate dither share it in a fixed order
(`src/pyntpot/maps/painter/job.py:10-16`). Blur, chamfer distance and shift draw no random
numbers, so this holds without extra care.

### 2. Drawing order and groups

Today the plate draws water, then major road, then lane, then track, each glazed over the one
before. The goal is that a junction reads as one road while a crossing of different kinds of
line still reads as a crossing. Both come from ordering **within a group**: every casing in the
group first, then every line. Groups are drawn one after another.

Proposed groups:

1. **Water**: `major, medium, minor, coast`. These classes already share one pad and one read,
   so the group's lines are a single layer. Water casings go under the water layer.
2. **Roads**: `road_major, lane, track`. Tracks and lanes join roads on the ground, so they
   share the road group. Casings are drawn for all three, then the three lines in today's order.

Water comes first, so the road group's casing is drawn over the river where a road crosses it.
That gives the bridge knockout for free (section 6). A single global order ("every casing on the
map, then every line") would let the river line cover the road's casing, so the crossing would
read as a junction. The route is not part of either group: it is drawn at compose time, above
everything in the base plate, so its casing knocks out every road and river under it, which is
what we want.

**No effect means no change.** With no effect set, nothing is added to the `over` list, so the
list matches today's exactly and every pixel stays bit-for-bit the same. The new order must not
change the line order: the effect pass must insert layers, never re-sort them.

Glow and shadow follow the same rule, but they change the composited RGB rather than adding a
pigment layer (section 5), so `composite` is split at each group boundary. Kubelka-Munk glazing is
already sequential bottom-first (`src/pyntpot/ink/pigment.py:166-209`) and multiply is
associative (`pigment.py:212-227`). Compositing below a group, applying the effect to that
result, and then glazing the group's lines over it with `composite(lines, base=...)` gives
exactly the same pixels as today wherever no effect is set.

### 3. The two drawing paths, and what each costs

**Basemap path (`base_digest`).** The cache key for base plates is
`Cache.base_key = sha256(basemap.canonical())[:16] + "-" + style.base_digest()`
(`src/pyntpot/maps/cache.py:211-224`). `pipeline.paint` repaints only when that key changes
(`src/pyntpot/maps/pipeline.py:124-128`). `base_digest` covers `BASE_GROUPS` = paper, wash,
**brush**, card, ribbon, cover, **route**, basemap (`src/pyntpot/maps/style.py:62-71`). A
basemap effect field in `brush` (next to `brushes`/`brush_overrides`) therefore moves
`base_digest`. The cost:

- every phase is repainted (`plates.py:104-121`): water, cover, wood, lakes, relief, fluid, pen,
  the WebP encode and the manifest;
- the nib plate is stroked again, because `lettering_key` hashes the base hash
  (`cache.py:227-245`).

Costs: `paint` 2.57 s vs `compose` 0.34 s at 450 px (`docs/runbooks/performance.md:59-61`);
Lynmouth 22.3 s, Skye 59 s (`:72-73`). One `chamfer_distance` or `blur` on a 2400×3600 plane
costs about 0.2 s (measured), so the effects themselves are cheap.

**Route path (`digest()` only).** `route_ink` is in `digest()` and in neither of the other two
digests (`style.py:12-30`, `206-216`). `compose` reads `style.route_ink`
(`pipeline.py:160-166`), and `compose_steps.route` draws the route straight onto the card image
(`src/pyntpot/maps/compose_steps.py:56-93`). Neither digest is a cache key: a route-effect change
costs one compose (about 0.3 s) and repaints nothing. Pinned digests: `tests/unit/maps/test_style.py:53-55`, `test_theme_named.py:48-51`.

**Traps.**

- **The route key cannot share the brush table.** The settled shape is "keyed by the brush class
  names plus the route as one more key". If that is literally one dict in `brush`, then changing
  the route's casing moves `base_digest`, repaints everything and re-strokes the nib. The route
  entry has to live in `route_ink` (as ADR 0046's feature notes already propose:
  `docs/features/maps-route-casing.md`, "Possible shape"). The same theme syntax could still be
  split into two groups at load time.
- **Glow lift at compose needs the paper.** `painted_map` returns paper × wash
  (`compose_steps.py:42-53`). "Lift towards paper" means `card + a·(paper − card)`, so `route`
  needs the paper plate's pixels (`plates.paths["paper"]`), not only the card. It must not lift
  towards white: white is brighter than the paper, and the glow would read as a sticker.
- **The pen plate is painted at base time from `route` group fields** (`pen.py:113-131`). Route
  effects must take that alpha as their input at compose, never be painted into `pen.webp`, or
  they would move `base_digest`.
- **The consumer's own page.** Per the compose-steps docstring (`compose_steps.py:3-8`), the
  upstream page draws the route in SVG itself. Compose-time route effects appear only in
  `compose` output, not on that page.

### 4. The pen route and doubled-back strands

The route is never split into per-pass strokes. `merge_strands` pulls each retraced stretch onto
the earlier pass and returns **one polyline** (`src/pyntpot/maps/strands.py:1-13`, `69-110`). The
pen plate lays that single line (`pen.py:122-126`, merged by `route_pen_width_px`). The solid
route draws `plates.strands` as one Pillow `line` on a 4× grid (`compose_steps.py:84-93`), merged
by `route_ink.px` (`strands.py:53-66`, `pipeline.py:131`). In both cases the mask is already the
**union** of the passes.

- **Casing: one mask, for the union.** Per-pass casings drawn as casing → line → casing → line
  would let the second pass's casing cover the first pass's line wherever two passes diverge
  slightly or cross. A casing computed from the union mask is free, because the union mask is
  the only mask there is.
- **Shadow: the union, with the line knocked out** (section 5), so one strand's shadow can never
  fall on another.
- **Glow on pen ink: blur the pen alpha.** Two cautions. Pen alpha may be lossy WebP
  (`plate_lossless`, `pen.py:128-130`), and it is LANCZOS-resized at compose
  (`compose_steps.py:75-77`). Near-zero noise and ringing would then glow faintly across the
  card, so threshold or clip the alpha before blurring.
- The same primitive has to handle three cases: `drawn_as == "pen"` with a plate, `"pen"` with no
  plate (it falls back to solid), and `"solid"` (`compose_steps.py:72-93`).

### 5. Effect maths in `ink`

Every effect is a plain function of the RGB under it and a float mask. `ink` gets three
primitives, none of which knows anything about maps:

- **casing**: `alpha = smoothstep(w − chamfer_distance(m > τ))`, a ring of width `w` that
  also covers the line's own footprint. It is applied as `rgb + alpha·(c − rgb)`, a lerp to the
  casing colour, which in wash space is the colour over the paper (`c = 1` gives paper). Not a KM glaze: ink glazes at `km_transparency = 0.06`
  (`src/pyntpot/ink/style.py:88,108`), so cream cannot cover a dark wood, and multiply cannot
  lighten at all (`pigment.py:108-119`). The line is then
  glazed over the casing as before; because the line is transparent, the casing shows through
  the line's dry breaks, which is the intended look.
- **glow**: `alpha = g·blur(m, σ)`, then `rgb + alpha·(1 − rgb)` in wash space (`paper − card`
  at compose).
- **shadow**: `alpha = s·blur(shift(m, d), σ)·(1 − clip(m/τ, 0, 1))`, then
  `rgb·(1 − alpha·(1 − p))`, a multiply darken by pigment `p`.

Hypothesis properties, and what makes each one hold:

| Property | Holds because | Hazard |
|---|---|---|
| Casing width 0 is identity | Short-circuit `w <= 0` → input returned unchanged | Without the short-circuit, `smoothstep(0 − 0)` is nonzero on the footprint; with no short-circuit the casing would show through the line's breaks. Test bit-equality. |
| Glow never darkens | `a·(1 − rgb) ≥ 0` for `a, rgb ∈ [0,1]`; an IEEE add of a non-negative number never decreases | A glow with its own colour could darken, so glow lifts only towards paper. Test on arrays, before the dither and lossy WebP (`plates.py:73-81`), which can move pixels. |
| Shadow never lightens | multiply by `1 − a(1 − p) ≤ 1` | It would fail if done as a KM glaze, which lightens when `R > under`. Keep effects off `km_plate`. |
| Shadow never paints over its line | knocked out by `(1 − clip(m/τ))`, so alpha is exactly 0 where `m ≥ τ` | Even full-density line pixels are glazed over the base under them (transparent KM), so a shadow merely laid *under* the line still tints it. The knockout is required. State it as "where line density ≥ τ, output equals the no-shadow output". |
| No effect is identity | an all-zero alpha is skipped, as `composite` already skips empty layers (`pigment.py:12-13`, `199-201`) | none |

### 6. Leaders and knockouts

- **Leaders** are nib-plate marks drawn with `label_leader_brush`/`label_leader_width_px`
  (`src/pyntpot/letters/style.py:119-120`, `src/pyntpot/letters/nib.py:107-123`). They are pasted
  over the route (`compose_steps.py:124-136`). `nib.py:200` rejects halos by design. Effects on
  leaders would be a letters-side change and would move `lettering_digest`. That is feasible
  with the same `ink` primitive, but it contradicts the settled exclusion, so leave it out.
- **Road over river** comes out right from the group order: the road casing is drawn after the
  water layer and lifts the river, which reads as a bridge. River over road (a culvert or ford)
  is not expressible without per-feature z-order, which the basemap does not carry
  (`Line.band`/`cls` only, `src/pyntpot/maps/basemap.py:49-80`).
- Basemap effects move the dark grid (`plates.py:122`) and so label placement.

### 7. Where the code disagrees with the settled decisions

1. **The class names.** The settled list says "river, stream, lane, road classes, track". The
   `brushes` keys are `major, medium, minor, coast, road_major, lane, track`
   (`brush_style.py:181-191`). There are no `river`/`stream` keys, and there is one road key,
   not several.
2. **One table cannot serve both paths** (section 3). The route key must live in `route_ink`.
3. **Turning effects off can still move a digest.** Any new field in `brush` changes every
   theme's `base_digest` even at its empty default. That invalidates every cached plate and fails
   `test_the_manifest_hash_matches_the_golden` (`tests/golden/test_parity.py:47`) with no pixel
   moved. The new field's name must go into `DIGEST_OMITS_AT_DEFAULT` (`style.py:79-84`), and it
   must be a unique name, because the list is matched by name across groups. New `route_ink`
   fields move `digest()` for every theme unless they are listed too.
4. **Water is one pad.** Per-class effects on water need new mask pads, which is more than "a
   mask primitive" alone.
5. **The docstring of `compose_steps.route`** says "No casing, glow or shadow is drawn"
   (`compose_steps.py:67-68`). It must change in the route PR.
6. **The split into two PRs follows the digests.** PR A: the `ink` primitives plus basemap
   effects (painter, `brush`, `base_digest`, golden-neutral at defaults). PR B: route effects
   (compose, `route_ink`, `digest()` only). PR B depends on A's primitives. The `ink` diff in A
   must be mutation-tested (CLAUDE.md, step 4).

## #159: one route colour in one place

### 1. Root cause

The route's colour is held in two fields, and only one of them is fed.

| Holder | Where | Read by |
|---|---|---|
| `RouteInkStyle.colour = "#c22050"` | `maps/style_groups.py:334` | `compose_steps.route` (`:72`), called from `pipeline.compose` (`pipeline.py:165`) |
| `NibStyle.label_route_ink = "#c22050"` | `letters/style.py:127` | `nib._ink_colour` (`letters/nib.py:274-281`), applied at `nib.py:341` |

The path to the pink "start" label goes like this. `picks.route_markers` (`maps/lettering/picks.py:175`) makes `kind="marker"` labels. `KIND_INK` (`maps/lettering_marks.py:56`) maps `marker` to the token `"route"` (`_ink`, `:198`). The nib then resolves that token to `nib.label_route_ink`. `Style.with_route_ink` (`maps/style.py:218-259`) replaces only `route_ink.colour`/`px`, and its docstring promises that `lettering_digest()` does not move. The marks also carry the token rather than the colour. So `Cache.lettering_key` (`cache.py:227-249`) is unchanged, and `draw_plate` (`lettering/pipeline.py:254`) reuses yesterday's pink plate.

Measured (Lynmouth fixture, 450 px card): the nib plate after `with_route_ink(colour="#6a2c91")` is **byte-identical** to the default one. On the composed card the "start" label's 168 opaque pixels average **(192, 52, 89)** (pink) next to a violet route line.

Other consumers:
- Pins and leaders take their label's ink (`lettering_marks.py:244-245`), but `marker` is in `NO_LEADER` (`lettering/label.py:39`), so no route-inked pin or leader is ever drawn.
- No legend exists.
- The attribution uses the nib/label ink, not the route colour.

So exactly two consumers exist today: the line and the marker labels.

Themes treat the two as separate on purpose. Three of the four packaged themes letter the markers a shade darker than the line:

| Theme | `label_route_ink` | `route_ink.colour` |
|---|---|---|
| bold | `#d4005f` | `#e6007a` |
| sepia | `#7a2e14` | `#8a3418` |
| winter | `#b3261a` | `#c8321e` |

pen-and-ink and all six example themes set both fields to the same value. ADR 0027 (`:56`) made this independence deliberate.

### 2. Design options

**A. `with_route_ink(colour=c)` also sets `nib.label_route_ink = c`.**
- The one public way to change the route colour then changes every route-coloured thing. Themes keep their darker shade.
- Cost: when a colour is fed, `lettering_digest` moves, so the nib plate is stroked again once. Measured: default `d15ae2f30e9ca5ce` becomes `d4e48ea6fd28b786`; `base_digest` stays `d9c56c0811177b0f`.
- Amends ADRs 0027 and 0046 and the `with_route_ink` docstring: only a fed *width* is compose-only now.
- It is still two fields. A theme author can still diverge, but now on purpose.

**B. Tint at compose.** Stroke the route-token marks into their own alpha plate and tint it with `route_ink.colour` in `compose`, like the pen plate. Only `digest()` moves.
- But the nib colours each ink layer as `colour × tint(dark)` per pixel (`nib.py:317, 341`), lays the layers over one another in ink order, and encodes the result lossily. Splitting out one layer changes the overlap compositing and the encode, so **default pixels move** and every golden is regenerated.
- It also needs a new plate in the manifest and on the page.
- Not a no-pixel PR.

**C. `label_route_ink: str | None = None`, where `None` means `route_ink.colour`.** This is truly one place by default.
- The lettering must see the resolved colour: the maps layer builds `NibGroups` with it (letters cannot import maps), and `lettering_digest` must cover it. That digest therefore depends on two groups.
- Serialising `None` in place of `"#c22050"` moves the pinned `DIGEST`, `LETTERING_DIGEST` and every theme's `DIGESTS` entry, unless the nib digest hashes the resolved value. That means special-casing `_digest_fields`.
- bold, sepia and winter keep an explicit override. A fed colour must clear it, so C includes A's behaviour anyway.

**Recommendation: A for #159.** It is the smallest change that fixes the public path and the how-to. It moves no digest or pixel at the default (§3), and its cost is one re-stroke per new colour (§4). Record in the ADR that a theme may still pick a different marker shade, and that a fed colour overrides it. C can be a follow-up if "one field" matters beyond "one public way". A theme loader could also warn when the two differ.

### 3. Does it move anything at the default?

No, with A. The new branch runs only when `colour` is fed, so `Style()` and every theme stay the same object and keep the same three digests.

Under C, the resolved style **equals** `Style()` (`==` is `True`, `lettering_digest` the same), and a re-stroked nib plate is **byte-identical**. The composed 1800×1457 default card hashes to `5c493c64220e17e7` before and after. So C moves pixels nowhere; it moves only the digest literals, as above.

The tests that call `with_route_ink(colour=…)` (`tests/unit/maps/test_route_ink.py`) compose with `UNLETTERED`, so they do not move.

The only image that changes is `docs/images/how-to/route-ink.webp` (`examples/how_to_route_ink.py:135-138`). Its "start" label turns from pink (192, 52, 89) to violet (116, 63, 145). That change is the fix. The grid cells carry no names.

`test_route_ink_change_moves_only_the_full_digest` (`tests/unit/maps/test_style.py:192`) changes `px` only, so it holds. A new test should pin that a fed colour moves `lettering_digest`.

### 4. What repainting costs

Machine: 4 vCPU Intel Xeon @ 2.10 GHz, Python 3.13 via uv. Default style (900 px display, supersample 2, card 1800×1457), Lynmouth fixture. Medians of 5 runs (compose: 7).

| Step | Median |
|---|---|
| `paint` cold | 14.06 s (one run) |
| `paint` after `with_route_ink` (cache hit, same hash) | 0.035 s |
| `letter` cold (plate stroked) | **4.47 s** (min 4.05, max 4.80) |
| `letter` warm (key hit) | 0.23 s |
| `letter` after `with_route_ink` today (key unchanged) | 0.24 s |
| `letter` under A, first call after a fed colour | **4.63 s** (one stroke), then 0.25 s warm |
| `compose` default | 0.99 s |
| `compose` with violet | 0.87 s |

So a route colour never forces a base plate repaint: the colour feeds only `digest()`, never `base_digest`. Under A it costs one nib re-stroke of about 4.5 s, which is about 25 % of a cold paint plus letter (≈19.5 s). Compose costs the same either way.

Caveat: the nib plate has one file per hand route (`labels-<route>.webp`). Alternating between two colours therefore re-strokes every time; there is no cache entry per colour. My first measurement tripped on this: `compose` reads the file at compose time, so a stale `Lettering` pastes the newest plate.

Benchmarks to reuse: `tests/benchmarks/test_maps.py` has `test_letter` and `test_compose` (450 px, `flags_off_style`). Add `test_letter_after_route_colour` to time the re-stroke under A. The scratch scripts are `d159.py` and `d159b.py` in the scratchpad.

### 5. Guard tests

- **Property (cheap, Hypothesis over `#rrggbb`).** For `s = Style().with_route_ink(colour=c)`, every route-coloured resolution equals `c`: `s.route_ink.colour == c` and `nib._ink_colour("route", s.nib) == c`.
- **Structural, to stop a third copy.** For each entry in `COLOUR_FIELDS` (`maps/theme_vocab.py`), if its default equals `RouteInkStyle().colour`, then `with_route_ink(colour=c)` must set it to `c`. A future route-coloured field cannot then be forgotten.
- **One end-to-end pixel test** on `tiny_style`, at fixed ids. After `with_route_ink(colour=VIOLET)` and then `letter` and `compose`, the marker label's opaque pixels average within a tolerance of `VIOLET`, and the nib plate is not byte-equal to the default's. This is the regression test the how-to's picture would have failed.

## The labelled grid helper and the galleries

### 1. The five grids today

All five are in `examples/`, write one PNG, and are registered in `tests/support/docs_images.py` (named in `docs/features/docs-labelled-grid-helper.md:7-16`).

| Script | Shows | Layout | Labels | Docs image |
|---|---|---|---|---|
| `tutorial_grids.py` | seven tutorial grids | `_layout` `:92`, gap 14, pad 14, width 720 | `_labels` `:162`, `_letter` `:116` | `tutorials/grid-*.webp` (3 lossless, 4 lossy) |
| `nib_stages.py` | `angles` 4x3, `hands` 3x3 | `_cells` `:221`, scaled by `size/GRID_W`, flat list | inline `:256-262`, `_letter` `:195` | `explanation/nib-angles`, `nib-hands`, lossless |
| `brush_sheet.py` | `grid`: 8 treatments by 3 widths | inline `_grid` `:165`, one density pass | inline `:196-215`, `_letter` `:138` | `reference/brush-sheet.webp`, lossy |
| `wash_stages.py` | `glaze`: 4 transparencies, multiply vs glaze | inline `:127`, everything times `unit` | inline `:171-190`, `_letter` `:99` | `explanation/wash-glaze.webp`, lossy |
| `how_to_route_ink.py` | six map cards, 2 pens by 3 colours | inline `:184`, cells are resized photographs | inline `:239-248`, `_lettered` `:157` | `how-to/route-ink-grid.webp`, lossy |

Labels are always `Setting(text, px, anchor, align="middle"|"end", wash=False)` in the default hand, `NibStyle(label_ink, label_pen_width_px)`, then the nib-plate round trip (Canvas at `NIB_SCALE` 2, `NibSurface`, `nib_plate` to a temp WebP, `RGBa` Lanczos downsize, alpha blend), copied 14 times (`specs/005-feature-scoping/review/04-examples.md` F1). Offsets are bare: rows `left-12`, `y+h/2+7`; columns `top-12` (tutorial, `:172`) or `top-14` (the rest).

Pinning: each is a docs image with a lossless 240 px PNG master in `tests/golden/docs/`, compared by `tests/golden/test_docs_images.py` (marker `golden`): exact on the pinning machine (docs file too), master only within `--golden-tolerance` elsewhere. No full-size hash exists.

### 2. The helper (#170)

**Where.** A sibling `examples/labelled_grid.py`, private by nature (not in any `__all__`, so ADR 0068 is untouched). `ink` would need an ADR for a documentation concern. The public `letters` call of #165 is the better home for the round trip, but it removes the lossy WebP step, so it moves pixels; do #170 first with one surviving copy, then #165 swaps it and re-pins separately. Cost: `runpy.run_path` (`tests/support/examples.py:23`) does not put `examples/` on `sys.path`, so `run_example` and each script's `__main__` need a path insert (and check `tests/architecture/test_examples.py:90-101` allows a sibling import).

**API.** Not a painter callback: `brush_sheet` composites one pass over the whole sheet, the route grid resizes finished images, `nib_stages` letters inside cells. Two pieces instead:

```python
@dataclass(frozen=True)
class GridSpec: width, cols, rows, cell_h, left, top, gap=14, pad_right=14,
                pad_bottom=14, unit=1.0, trailing_gap=False
    # .boxes() -> list[list[Box]], .height, .cell_w
def label_grid(img, spec, columns, rows, *, px, ink, pen_px, col_dy=14, row_dx=12,
               row_dy=7, gran_px, seed, extra=()) -> np.ndarray
```

`label_grid` builds the `Setting`s from the boxes and calls the one `letter_over(img, settings, nib, seed, gran_px)`. Scripts keep their painting. `extra` carries `brush_sheet`'s bottom kind labels (`:200`).

**Differences that block identity, and their parameter.**
- Column offset 12 vs 14: `col_dy`.
- Trailing gap, bottom pad 14 / 34 / `round(14*unit)`, and `round()` applied at different points (`_cells` rounds left, top, cell_h and gap separately; `wash_stages` differently): `unit`, `pad_bottom`, `trailing_gap`; `boxes()` must reproduce each rounding exactly, else keep an origin override rather than add flags.
- Absolute anchors in `nib_stages` (`38*unit`, `96*unit`): `col_y`/`row_x` overrides.
- `gran_px` (four formulas), pen width (`1.5`, `1.5*w/GRID_W`, `1.6*unit`), ink (`#4a3a2a`, `#3a2c20`, `#241c14`), px (20, 21, 22): plain parameters.
- Keep `RGBa` in the single copy (Pillow premultiplies either way, F1, but do not risk it).

Roughly ten parameters is the real variation. Do not "tidy" the 12/14 offsets in this PR.

**Proving identity.** The 240 px masters and lossy files hide a one-pixel label shift, so add a before/after harness:
1. Before editing, run every grid's `main` at its registry `options` (seven tutorial figures, `angles`, `hands`, `brush grid`, `glaze`, route grid with theme and fixture) and record `sha256` of the returned PNG, the exact output before the docs encode (`save_image(..., seed=SEED)` is deterministic).
2. After, compare byte for byte.
3. Run `tests/golden/make_docs_images.py --compare` and `pytest -m golden tests/golden/test_docs_images.py -k "grid or glaze or route-ink or nib-angles or nib-hands or brush-sheet"`; `tests/golden/repaint.py` and `diff_images.py` show any diff (CONTRIBUTING.md:60-85).
4. Unit-test `GridSpec.boxes()` against literal boxes taken from the old `_layout`/`_cells` for all five configurations (pinned literals, per CLAUDE.md). Keep step 1 as a golden test only if the maintainers want a permanent full-size pin; it is exact only on the pinning machine.

### 3. Docs image budgets

`tests/support/docs_images.py:95-125`: `KIND_BUDGET_BYTES` per file (thumbnail 60 kB, page 250 kB, hero 400 kB, preview 900 kB), `SLICE_SHARE_BYTES` per slice (18 keys), `TOTAL_BUDGET_BYTES` 7 MB (decimal). Enforced by `tests/docs/test_docs_images.py:115-159`. 71 entries use 3.48 MB, so 3.5 MB spare overall. `P7.9` (swatches, brush sheet) is at 53 of 500 kB; `P7.V12b` (tutorial and nib grids) at 822 of 1000 kB with only 178 kB spare because lossless nib grids weigh 140-220 kB; `glyph-sheet` 231 of 250 kB. #67, #69 and #70 need a new slice key with its own share. Lossy page figures here cost 6-50 kB, lossless lettered ones 50-220 kB; only pen, nib and lettering figures must be lossless (`:24-27`), so galleries stay lossy and 10 to 15 figures fit in about 0.5 MB.

### 4. What painters want, and how the helper serves it

A swatch on paper (`paper_plate`, not white), names in the library's hand, transparency (stain versus veil), wet versus dry, and how colours mix.

**#69 brush ids** (112 ids, `RIV/STR/LAN` one colour column, `MAJ` five, `TRK` six, by eight treatments, 5/6/8 nibs). One figure per prefix via `figure=`, one registry entry each. Columns are colour columns, rows treatments, each cell one S-line stroke from `brush_from_id(id, width, 1.0, BrushStyle())` as `brush_sheet._sheet` does; the id in the hand, treatment names down the side. The helper gives layout and labels; strokes are composited by ink in one pass (`brush_sheet.py:177-182`). Nib rows need `Mark`s, so the cell painter has two branches. Show two widths, since dryness only reads when big. Add the doc test that every id appears.

**#70 pigments**: rows are pigments from the registry, columns three strengths (`wash` 0.3/0.6/0.9) with `composite` and each `TRANSPARENCY`, so stains and veils differ. A second figure of pair glazes is `wash_stages._glaze_grid` with pairs as columns (multiply above, Kubelka-Munk below); lift its disc-pair painter into the shared module. Aliases need a two-line label, which `extra` or a `sub` argument handles. A granulating pigment over rough tooth could reuse the `paper_tooth` axis.

**#67 effect grids**: the helper's native use. Add a thin `effect_grid(values, paint_cell, spec)` over the same two pieces: one loop over `boxes()`, then `label_grid`; `paint_cell` may return a lettered cell (nib angle). The `paper`, `wash`, `brush` and `nib` tutorial grids already are this by hand. Relief strength needs map fixtures like the route grid.

### 5. Build and checks

Built by `tests/golden/make_docs_images.py`, not a mkdocs hook: `paint_entry` (`:87`) runs each entry's script through `run_example`, copies fixtures to a temp cache, downsizes to `entry.width`, encodes, and writes the docs file and master; `--compare` (`:124-140`) logs one line per image. Checked by `tests/docs/test_docs_images.py` (registry, files, Markdown links, budgets), `tests/golden/test_docs_images.py` (pins), `tests/architecture/test_examples.py` (public imports), and `tests/examples/` (each script at a small `size=`). Regenerating committed images needs an ADR (0006, 0036); PRs publish review images to `pr-assets` (ADR 0052).

## Prior art

Vector map engines (Mapnik, MapLibre) make a casing by drawing the same geometry twice,
and leave order to the layer list. Desktop and paint tools (QGIS, Photoshop, Affinity)
attach an ordered stack of effects to one symbol. The stack suits pyntpot better; the
engines hold the junction rule we must keep.

### Mapnik and CartoCSS

CartoCSS gets a casing from *attachments*: `#roads::casing { line-width: 9; }` and
`#roads::fill { line-width: 6; }` become two Mapnik styles on one layer. Attachments
draw in the order they first appear in the stylesheet, and each one draws *every*
feature before the next starts. That is why all the casings land beneath all the fills
and a crossroads reads as one road. Each symbolizer has `line-comp-op` (default
`src-over`, and 37 values in all, including `multiply`, `screen`, `dst-out` and
`grain-merge`); a style has `comp-op`, `opacity` (default 1.0; any other value renders
the style to its own buffer first) and `image-filters` such as `agg-stack-blur(rx,ry)`.
That buffer is Mapnik's only way to blur a glow or a shadow. `line-offset` (default 0,
marked unstable) moves a line sideways, parallel to its path; `line-smooth` (0 to 1)
rounds corners. Colours are `@variables` in the stylesheet: there is no palette object.
Source: [mapnik-reference 3.0.22](https://github.com/mapnik/mapnik-reference/blob/master/3.0.22/reference.json).

### openstreetmap-carto

The [project.mml](https://github.com/gravitystorm/openstreetmap-carto/blob/master/project.mml)
layer list is the clearest statement of road layering anywhere: `water-lines`, then
`water-areas`, then `tunnels` with their own casing, then
`turning-circle-casing`, `highway-area-casing`, `roads-casing`, `highway-area-fill`,
`roads-fill`, `turning-circle-fill`, and last `bridges`, which carries its own casing
and fill so that a bridge cuts cleanly over whatever runs under it. The casing, tunnel
and bridge queries share one `ORDER BY layernotnull, z_order, sort_score, osm_id`, and a
comment in each tells maintainers to change all three together.  Waterways that are bridges are pinned to
`z_order` 0, "consistent with waterways being rendered before roads/railways". Road
colours are generated: `road-colors.yaml` feeds `scripts/generate_road_colours.py`,
which writes `road-colors-generated.mss` by stepping through LCh space. That is a
palette kept as data and handed to the style.

### MapLibre / Mapbox GL style spec

In the [style spec](https://maplibre.org/maplibre-style-spec/layers/) a casing is just
another `line` layer beneath the fill layer, with a larger `line-width`. Styles in the
OSM Carto mould (OSM Liberty, OpenMapTiles) list every road casing layer, then every
road fill layer, the same rule as the attachments. There is also `line-gap-width`
(default 0), which "draws a line casing outside of a line's actual path" from a single
layer. It makes no junction merge because each feature draws its own pair of edges. `line-blur` (default 0, in px) feathers a line,
and is how a glow is faked: draw a wide blurred line beneath a sharp one. `line-offset`
(default 0; positive means to the right of the line's direction).
`line-sort-key` sorts the features within a layer in ascending order. `line-cap`
defaults to `butt` and `line-join` to `miter`. On text, `text-halo-color` (default
transparent), `text-halo-width` (default 0, "max … 1/4 of the font-size") and
`text-halo-blur` (default 0) make a halo. Colours are literal values or expressions:
there is no named-colour registry, and `sprite` holds icons, not colours.

### QGIS

A QGIS [symbol](https://docs.qgis.org/latest/en/docs/user_manual/style_library/symbol_selector.html)
is a stack of symbol layers ("stack as many symbols as you want"), drawn bottom to top
for each feature in turn. Left at that, a stack draws feature by feature and "similar
symbols do not merge". *Symbol levels* fix it: each symbol layer gets a level, and
"lower values levels are drawn first". Give every casing level 0 and every fill level 1
and the junctions merge. The attachment rule, as a visible number. Each symbol layer also takes a [draw effects
stack](https://docs.qgis.org/latest/en/docs/user_manual/working_with_vector/vector_properties.html):
**Drop Shadow** and **Inner Shadow** (Offset angle, Offset distance, Blur radius,
Colour), **Outer Glow** and **Inner Glow** (Spread, Blur radius, a single colour *or a
colour ramp*), **Blur** (stack or Gaussian, strength), **Colorise**, **Transform** and
**Source**. All but Transform take Opacity and Blend mode. Draw mode is "Render only",
"Modifier only" or "Render and Modify", so one effect can change the image the next one
receives. Palettes come in as GIMP `.gpl` files or
colour ramps (cpt-city, ColorBrewer).

### Painting and illustration tools

Photoshop's [layer styles](https://helpx.adobe.com/photoshop/using/layer-effects-styles.html)
are the common vocabulary. **Stroke**: Size, Position (Outside, Inside, Centre), Blend
Mode, Opacity, Fill Type. **Outer Glow**: Blend Mode (default Screen), Opacity, colour or gradient, Technique (Softer,
Precise), Spread, Size, Contour.
**Drop Shadow**: Blend Mode (default Multiply), Opacity, Angle with "Use Global Light"
(default 120°), Distance, Spread, Size, and "Layer Knocks Out Drop
Shadow". Two ideas are worth taking. *Spread and Size* split a halo into a hard part
(a dilation) and a soft part (a blur), and so does QGIS's Spread and Blur radius. *Global
light* gives every shadow on the canvas the same angle. Affinity's layer effects are the
same model, and its saved styles are presets a user can share.

Palettes travel as files. GIMP `.gpl` is plain text: a `GIMP Palette` header, `Name:`,
an optional `Columns:` line, then one `R G B name` row per colour
([GIMP docs](https://docs.gimp.org/en/gimp-concepts-palettes.html)). Krita reads `.gpl`
and its own `.kpl` (a zip of XML); Adobe `.ase` is binary and carries swatch groups;
Procreate `.swatches` is a zip of JSON. Of these only `.gpl` can be read and diffed in
a review. Watercolour paints have a standard name: the Colour Index generic name
(Society of Dyers and Colourists), such as **PB29** ultramarine blue, **PB27** Prussian
blue, **PBr7** burnt sienna and umbers, **PY43** yellow ochre, **PR101** synthetic iron
oxide and **PG18** viridian. Makers print it on the tube because tube names vary ([handprint.com pigment
database](https://www.handprint.com/HP/WCL/waterfs.html)). 

### Hand and Swiss cartography

In pen-and-ink a road casing is not a darker stroke beneath a lighter one. It is two
parallel ink lines with the paper left between them: a *reserve*, the hand drawing's
knockout. In watercolour the painter reserves the white with masking fluid or by
painting round it. Eduard Imhof's *Cartographic Relief Presentation* (1965; English
1982, [Esri Press reissue](https://www.esri.com/en-us/esri-press/browse/cartographic-relief-presentation))
sets out the Swiss school: light from the upper left (north-west) and colour kept in restrained bands. *Water-lining*,
a run of fine lines inside a coast or lake shore drawn closer at the shore and wider
apart farther out, was the engraver's way to tint water before colour printing. It is a
line effect shaped by distance from the edge, the same distance field a glow uses.
See also [reliefshading.com](http://www.reliefshading.com/) (ETH Zürich).

### Borrow / don't borrow

| Idea | Source | Verdict | Why |
| --- | --- | --- | --- |
| Casing under all fills (all casings drawn before any fill) | CartoCSS attachments, osm-carto, MapLibre layer lists, QGIS symbol levels | **Borrow** | It is the only way a junction reads as one road. Make it the default pass order, not an option |
| Explicit integer level per effect | QGIS symbol levels | **Borrow** (lightly) | A `level` on each effect in the theme lets a user choose what draws over what without a hidden order |
| `line-gap-width`, a casing made per feature | MapLibre | **Don't** | Each feature casings itself, so junctions show seams |
| Shared sort key across casing, tunnel and bridge passes | osm-carto `ORDER BY` | **Borrow** | A bridge or a crossing over a river needs one order shared by every pass |
| Bridge as its own late pass, with its own casing | osm-carto `bridges` | **Borrow later** | Fits the river-under-lane case; needs OSM `bridge` and `layer` tags |
| Effect stack on a symbol (stroke, glow, shadow; ordered) | QGIS draw effects, Photoshop/Affinity layer styles | **Borrow** | Maps straight onto mask primitives: dilate, blur, offset, composite |
| Spread (hard) plus size/blur (soft) halo split | Photoshop, QGIS glow | **Borrow** | Two numbers say everything a halo needs, and both are mask operations |
| One global light angle for every shadow | Photoshop Global Light, Imhof north-west light | **Borrow** | Shadows that disagree look wrong; tie it to the hillshade azimuth |
| Modifier-only draw mode, blend-mode enumeration (37 comp-ops) | QGIS, Mapnik | **Don't** | Too large for us. Keep the pigment model (glaze, multiply) and add modes only on a real need |
| Glow made by blurring a raster, glow by blurred wide line | Mapnik `agg-stack-blur`, MapLibre `line-blur` | **Borrow the idea** | Do it on the coverage mask before `wash`, not on the finished RGB |
| Named colour registry; themes name colours by key | Colour Index codes, osm-carto `road-colors.yaml` | **Borrow** | One registry and stable keys; a role (`river`) points at a pigment (`ultramarine`) |
| Palette as a shareable plain-text file (`.gpl`); not binary `.ase`/`.swatches` | GIMP, Krita, QGIS | **Borrow (export/import)** | Readable in review, opens in paint tools. RGB loses transparency, so YAML stays the source of truth |

| Colours as expressions, generated palettes | MapLibre expressions, osm-carto LCh script | **Don't (yet)** | Per-class literals are enough; generation earns its place only with many classes |
| Paper reserve as a casing (two ink lines, paper between) | Pen-and-ink practice | **Borrow** | A casing done as a knockout of the wash beneath suits our medium best |
| Water-lining as a distance-field line effect | Engraved and Swiss maps | **Consider** | Uses the same distance field as glow; a later feature |
| Named effect presets (`halo`, `cased`, `shadowed`) | Affinity styles, Photoshop presets | **Borrow** | A short name in a theme expands to a stack, so themes stay short |
