# 0069 — Themes are YAML overrides of one model (supersedes 0020; amends 0002, 0005, 0015, 0037, 0046 and 0068)

Status: accepted

Supersedes ADR 0020 whole. Amends ADR 0002 (the YAML ban), 0005 (where the defaults live,
and the basemap's effective options), 0015 (`ruamel.yaml` joins pydantic at the boundary),
0037 (route ink `opacity` is a model default), 0046 (the route ink's `style` field is
renamed) and 0068 (the new public names below). Spec: `specs/008-themes-as-data/`.

## Context

A theme today is a TOML file that `Style.from_toml` hands to `model_validate`. Three
things are wrong with that.

1. **Two sets of defaults (#158).** The packaged `maps/themes/default.toml` holds the
   resolved default style, and each style group's dataclass holds another set of values:
   the port-era class defaults that ADRs 0005 and 0020 kept "verbatim" from `PaintStyle`
   and `GeoOptions`. They disagree on 25 fields (`paper.km_glazing`, `paper.paper_fibre`,
   14 `wash` fields, 6 `brush` flags, `basemap.landmarks`, `landmark_max` and
   `generalise`), and `RouteInkStyle()` cannot be built at all. A theme that leaves a key
   out takes the dataclass value with no error and no log line, so a trimmed theme paints
   with no blooms, no wet bleed and no Kubelka-Munk glazing. Engine users meet the same
   split: `PaperStyle()` multiplies where a map glazes.
2. **Every theme is a whole copy (#80).** Each of the ten example themes restates all 271
   leaf keys of the default to change 22 to 46 of them. A change to the default has to be
   copied into ten files by hand, and nothing says which lines a theme meant to change.
3. **Silent acceptance.** Keys inside the eight dict-valued fields (`cover_cfg`,
   `pigments`, `brush_overrides` and the rest) are not checked, string enums such as
   `hillshade_mode` and `[route_ink] style` accept any string (a typo `"pne"` draws a solid
   line), pydantic's lax mode turns `"5"` into `5.0`, and an error names a dotted path but
   no file or line.

Keeping the class defaults apart from the theme was a port-era convenience: it let the
port copy `PaintStyle` without deciding anything. It is weaker than one source of values,
because two sources can disagree, and they do.

Measured on `f34de97`: if every group's dataclass default is set to the default theme's
value, `Style()` built from those defaults equals `Style.default()`, and `digest()`,
`base_digest()` and `lettering_digest()` are unchanged (`1b08804a7f30026b`,
`d9c56c0811177b0f`, `d15ae2f30e9ca5ce`). Every example theme resolves to the same style
as before, because the five keys some of them leave out (`paper_edge`, `relief_strength`,
`min_patch_px`, `minor_road_classes`, `name_tags`) already default to the default theme's
values.

## Decision

### One source of defaults: the model

- Every field of every style group has a default, and that default is the default look:
  today's `default.toml` value. That holds for `PaperStyle`, `WashStyle` and `BrushStyle`
  (`ink`), `FaceStyle`, `NibStyle` and `HandStyle` (`letters`), and `CardStyle`,
  `RibbonStyle`, `CoverStyle`, `RouteStyle`, `RouteInkStyle`, `LetteringStyle` and
  `BasemapStyle` (`maps`). Each default sits in its group's dataclass at its own layer,
  because `ink` and `letters` cannot import `maps`. `RouteInkStyle()` builds:
  `drawn_as="solid"`, `px=5.4`, `colour="#c22050"`, `blend="normal"`, `opacity=1.0`.
- Every field of `Style` has a default, its group built with no arguments, so `Style()`
  is the default look. The `default` theme is the model's defaults with nothing
  overridden. `Style.default()` and `Style.named("default")` both return `Style()`.
- `maps/themes/default.toml` is deleted, and no `default.yaml` replaces it. Nothing needs
  a file: a file holding the defaults would be a second copy that can disagree.
- The digest rule `DIGEST_OMITS_AT_DEFAULT` leaves a named field out of its group's
  digest while the field equals its default. The four fields it names (`name_tags`,
  `minor_road_classes`, `relief_strength`, `min_patch_px`) already default to the default
  theme's values, so moving the other defaults changes nothing the rule omits, and no
  `digest()` of any theme moves because of this section.
- Adding a field moves the digest of every style that leaves it at its default, unless
  the field is named in `DIGEST_OMITS_AT_DEFAULT`: the group's fields are hashed, so a
  new name changes the hash. A field added later and named in the rule moves no digest
  of a style that leaves it at its default. The rule used to compare a field with its
  `default` only, which is `MISSING` for a field with a `default_factory` (a dict, or a
  sub-table built by its dataclass), so such a field could never be omitted; the rule now
  takes the factory's value as the default when there is no plain one. The four fields
  named today have plain defaults, so this moves no digest.
- **ADR 0020 is superseded** and **ADR 0005's** sentences "Each field's dataclass default
  is its source class default ... copied verbatim" and "The resolved and effective values
  belong to the theme, not to these defaults" no longer hold. The section "The basemap
  options are the effective ones" keeps its table of fields; its effective values are now
  `BasemapStyle`'s defaults. The candidate export (`CANDIDATE_BASEMAP`) keeps setting its
  own `landmarks`, `landmark_max` and `generalise` explicitly, so it draws what it drew.
- **ADR 0037's** reason for leaving `opacity` out of `default.toml` goes with the file:
  `opacity = 1.0` is a model default like any other.

### Tests that meant "the flags off"

About 35 unit and property tests build a group with no arguments to mean "every phase flag
off": the smoke plates (`SMOKE_SHA`), the stamping, deposit and wash mechanisms, and the
"off by default" checks. They now build it from one named test configuration,
`tests/support/flags_off.py`, which states the 25 values those tests were written
against. It is test data with a name that says what it is, not a default: no package code
reads it, and the guard below does not look at it. Their pinned values do not move.

### The format: YAML, merged over a base

A theme is a YAML file that names its base with a top-level `extends` key and gives only
what it changes:

```yaml
# yaml-language-server: $schema=https://findlaywebb.github.io/pyntpot/reference/theme.schema.json
extends: sepia
route_ink:
  colour: "#7b2335"
cover:
  relief_strength: 1.6
  pigments:
    wood: "#8f9f6a"
```

**Why YAML.** Readability, and the maintainer's preference. A theme is mostly nested
tables of a few keys each, and YAML's indentation shows the nesting where TOML repeats it
in every header (`[cover.pigments]`, `[brush.brush_overrides]`) or squeezes it into inline
tables. The maintainer reads and writes these files and prefers YAML; that is a reason in
its own right, and it is recorded as one.

**What was weighed against it.**

| | TOML (`tomllib`) | YAML (`ruamel.yaml`) |
|---|---|---|
| Dependency | none, stdlib | one more runtime dependency |
| Boundary | allowed today | banned by ADR 0002's contract; lifted for `maps` here |
| Implicit typing | none: `no` is a syntax error | YAML 1.1 reads `no`, `on` and `off` as booleans (the Norway problem) |
| Positions for errors | none: `tomllib` gives a line only for a syntax error | `ruamel.yaml`'s round-trip loader gives every key's line and column |
| Reuse mechanisms | none | anchors, aliases, merge keys and tags |
| Nesting | repeated table headers | indentation |
| Editor completion | Taplo `#:schema` | Red Hat YAML `# yaml-language-server: $schema=` |

The costs are answered as follows.

- **The Norway problem.** The parser is `ruamel.yaml` with the YAML 1.2 core schema, its
  default. Under it only `true` and `false` are booleans: `no`, `yes`, `on` and `off` are
  strings. A `%YAML 1.1` directive would turn the 1.1 rules back on (measured: it reads
  `no` as `False` and `010` as 8), so any `%` directive is rejected. Strict types are the
  second line of defence: a string where the model wants a boolean is an error, never a
  coercion.
- **Reuse mechanisms.** Duplicate keys, anchors (`&`), aliases (`*`), merge keys (`<<`),
  explicit tags (`!!str`, `!anything`), `%` directives and more than one document are
  rejected at load, each with the file, the key path and the line. `extends` is the one
  way to reuse a theme; there is no second merge mechanism.
- **Positions.** The round-trip loader is used only to read positions (`.lc`, zero-based
  line and column, reported one-based) and to see the parse events. The data is converted
  at once to plain dicts, tuples and scalars; nothing downstream sees a `CommentedMap`.
  Every YAML sequence becomes a tuple, since no style field is a list. No hand-written
  locator is needed.
- **The dependency.** `ruamel.yaml` (`>=0.19.1`) is pure Python, MIT-licensed, and needs
  nothing else at runtime. PyYAML stays banned: one YAML library, and it is the one that
  defaults to 1.2 and keeps positions.

Session F's data-driven brushes and pigments
(`docs/features/ink-data-driven-brushes-and-pigments.md`) also assumes YAML; this sets the
precedent, and whether its files are read in `ink` is that session's decision and ADR.

**Files and names.** `.yaml` is the one extension. A theme given as a value that ends in
`.yaml` is a path. Any other string is a name, which must match `^[a-z][a-z0-9-]*$` in
full and be one of the packaged themes. A value ending in `.yml` is an error that suggests
`.yaml`; one ending in `.toml` is an error saying themes are YAML since ADR 0069 and
pointing at the theme how-to's section on converting a TOML theme. The suffix is read the
same way whether the value is a string or a `pathlib.Path`, so `Path("old.toml")` gets the
same pointer; a `Path` is never a name. Anything else that is neither a valid name nor a
`.yaml` path is an error listing the available names. The same rule applies to `extends`,
with a relative path resolved against the extending file's directory. Other TOML data
files (`examples/places.toml`) are not themes and stay TOML. The code and its messages
say "a theme name or a .yaml path", never "reference", which the glossary keeps for an
entry of the references page.

### The boundary

`maps` may import `ruamel.yaml`, as it may import pydantic; `ink` and `letters` may not.
The forbidden contract, renamed "No plotting, dataframe, template or PyYAML dependencies", keeps
`yaml` (PyYAML) banned for the whole package, and the contract "ink and letters stay free
of httpx and pydantic" becomes "ink and letters stay free of httpx, pydantic and
ruamel", forbidding `ruamel` too. `BOUNDARIES.md` says the same. This amends ADR 0002's
"keeps ... YAML libraries out of the package" and ADR 0015's list of boundary libraries.

Inside `maps`, the loader modules (`theme_read`, `theme_check`, `theme_resolve` and the
rest) never import `pyntpot.maps.style` or the `pyntpot.maps` package: `Style` imports the
loader, and the loader takes the groups and the defaults table as arguments, so no import
cycle can form. The schema generator, `theme_schema`, is the one exception: nothing in
the package imports it. An architecture test checks the rule.

### Merge

- Tables deep-merge recursively: a key the override names replaces the base's value at
  that path, and every other key keeps the base's.
- Scalars, sequences and tuples, colours included, replace wholesale.
- A dict-valued field (`pigment_transparency`, `separation_pigments`, `river_curve`,
  `brushes`, `brush_width_px`, `brush_overrides`, `cover_cfg`, `pigments`) merges per
  entry: naming `cover.pigments.wood` changes the wood and keeps the other fourteen. An
  entry that is itself a table (`brush_overrides.lane`) deep-merges the same way.
- There is no removal. Every dict entry is one a painter reads, so a theme has no reason
  to remove one; converting the ten example themes needed none.
- `extends` chains resolve recursively. A missing `extends` means `default`. A chain that
  comes back to a file it has seen is an error naming the cycle.
- Each file is validated on its own against the model before anything is merged, so an
  error always names the file that holds the bad key. The merged result is then built into
  the groups; it is valid because each layer was.

**The shape is fixed, and the model fixes it.** Every key path of a theme is one of two
kinds, and which kind is a fact of the model, not of the file: a table (a group, a
dict-valued field, a table entry such as `brush_overrides.lane`, or a field typed as a
dataclass) or a leaf (every other field, and every entry of a dict field whose values are
not tables). Each file is checked against the model before it is merged, and a leaf where
a table belongs, or a table where a leaf belongs, is refused there. So `merge` never
meets a table on one side and a leaf on the other at the same path. That matters because
deep merge is associative only on such inputs: with `a = {k: {x: 1}}`, `b = {k: 5}` and
`c = {k: {y: 2}}`, merging left first gives `{k: {y: 2}}` and right first gives
`{k: {x: 1, y: 2}}`. The model rules `b` out, so the property is drawn over one fixed
shape, each key always a table or always a leaf.

On that domain merge is associative, an empty override gives its base, and an override
file and its fully expanded copy load to equal styles and so equal `digest()`
(Hypothesis properties). The merge reads the tables as the check converted them (an
integer in a float field already a float), so `5` and `5.0` merge to the same value.

### Validation, before any fetch

`Style.from_yaml` and `Style.named` check the whole theme when they are called, before a
caller can fetch or paint, and report every problem together, not the first:

- **Unknown keys** at every level, top level, group and inside dict fields, with the
  nearest valid key by `difflib.get_close_matches` (`wash.blom: unknown key; did you mean
  blooms?`). A dict field's keys are checked against a vocabulary: its model default's
  keys (cover classes, pigment keys, line classes, river classes), and for
  `brush_overrides` the line classes plus the brush-id prefixes, with each entry's own keys
  checked against `ink.brush.BRUSH_OVERRIDE_KEYS`, the fifteen keys `brush_from_id` reads.
- **Strict types**, leaf by leaf with pydantic's strict mode: `"5"` for a number, `1` for
  a boolean and `5.0` for an integer are errors. An integer is accepted for a float and
  stored as a float, so `5` and `5.0` give equal digests. A key with no value (`null`) is
  an error.
- **String enums** become `Literal` types: `paper.paper_edge` (already), `face.label_route`
  (`centreline`, `outline`), `basemap.hillshade_mode` (`bands`, `raster`, `contours`,
  `hachures`, `off`), `basemap.sea_style` (`fill`, `waves`), `basemap.roads` (`all`,
  `key`, `major`), `basemap.rivers` (`all`, `key`, `rivers`), `basemap.landmarks`
  (`heuristic`, `all`, `payload`), `route_ink.blend` (`normal`, `multiply`) and
  `route_ink.drawn_as` (`pen`, `solid`).
- **Brush ids** (`brush.brushes` values, `route.route_pen_brush`, `nib.label_brush`,
  `nib.label_leader_brush`) must name a sheet row and a colour that exist, by
  `ink.brush.brush_id_known`, the check `brush_from_id` already makes. **Colours** (every
  field whose default is `#rrggbb`, and every entry of `cover.pigments` and
  `wash.separation_pigments`) must be `#` and six hexadecimal digits.
- **Renamed keys** fail with what they are called now, from one table,
  `maps.theme_check.RENAMED_KEYS`, so the next rename (#181, `face.label_route`) adds a
  row: `route_ink.style: renamed to drawn_as`.
- **The YAML itself** is checked first, from the parser's events: syntax errors, duplicate
  keys (every one, with its key path, not only the first), anchors, aliases, merge keys,
  tags and directives. A file with such a problem is not loaded further, so its key and
  type checks do not run and its `extends` is not followed.
- Every problem names the file, the dotted key path and the line:
  `my-theme.yaml:7: route_ink.drawn_as: 'pne' is not one of 'pen', 'solid'`. They are
  raised together as one `ThemeError`, a `ValueError` whose `problems` are
  `ThemeProblem` records (`path`, `key`, `line`, `message`). Numeric ranges are not
  checked at load; the compose step's existing checks on `opacity` remain.

### The schema

A JSON Schema for a theme file is generated from the model by walking the group
dataclasses, in override form: every key optional, `additionalProperties: false` at every
level including dict fields (their `propertyNames` are the vocabularies above) and fields
typed as a dataclass (an object of that dataclass's own fields), enums for
the `Literal` fields, each field's default, its `Attributes:` text as the description,
and the top-level `extends`. It is committed twice, as package data
(`src/pyntpot/maps/themes/theme.schema.json`) and on the docs site
(`docs/reference/theme.schema.json`, served at
`https://findlaywebb.github.io/pyntpot/reference/theme.schema.json`). A test fails when
either differs from the regenerated schema and prints the command that rewrites both.
Theme files start with `# yaml-language-server: $schema=<path or URL>`, so the Red Hat
YAML extension completes and checks keys in an editor: the packaged themes name the
sibling file, the example themes the package file by relative path, and the how-to gives
the site URL.

### Named themes and the command line

- The package ships `default` (the model, no file) and four override files in
  `maps/themes/`: `pen-and-ink.yaml`, `sepia.yaml`, `bold.yaml` and `winter.yaml`, moved
  from `examples/themes/`, not copied. The six place themes (`ambleside`,
  `ambleside-hero`, `oxford`, `skye`, `y-fenni`, `yr-wyddfa`) stay examples: their
  landmark caps are curated against `examples/places.toml`.
- Python: `Style.named(name)` loads a packaged theme by name; `Style.themes()` lists the
  names, sorted, `default` included; `Style.from_yaml(path)` loads a file; and
  `Style.from_theme(theme, relative_to=None)` takes either, by the rule above, a relative
  path read from `relative_to` (the current directory when `None`). `from_theme` is
  public because three callers need "a name or a path": the command line, the examples
  that take a theme, and the theme preview card's script, which may use public names
  only. **`Style.from_toml` is removed** (breaking).
- Command line: `pyntpot map --style VALUE` takes a name or a `.yaml` path by the rule
  above, through `Style.from_theme`. A bad theme prints its problems, one per line, and exits with status 2. Nothing
  else about themes reaches the command line here (#68).

### The route ink's `style` becomes `drawn_as` (#182)

`RouteInkStyle.style` is renamed `drawn_as`, typed `Literal["pen", "solid"]`, and the
theme key with it. "Style" is the whole map's style and a glossary phrase in three other
terms; `drawn_as` names what the field chooses, and the glossary has no conflicting term
(`mode` would read as one of several modes in `BasemapStyle`, `treatment` is a brush-sheet
row). `"solid"` is the default. Any value other than the two is an error at load, where it
used to draw a solid line silently. This amends ADR 0046's field list. It moves `digest()`
of every style (the group's field name is hashed) and neither `base_digest()` nor
`lettering_digest()`, so no plate moves.

### Public names

Added to `pyntpot.maps`: `ThemeError` and `ThemeProblem` (`Style.from_yaml` and
`Style.named` raise the first, and its `problems` holds the second). New `Style` methods:
`from_yaml`, `from_theme`, `named`, `themes`. Removed: `Style.from_toml`. ADR 0068's rule covers the new
names; this ADR is the record of the change it requires.

### Forward compatibility

A new theme setting is a new field with a model default that leaves the look as it was,
plus a schema regeneration. No format change, and every existing theme stays valid. A new
field moves `digest()` (and `base_digest()` for a base group) of every style unless it is
named in `DIGEST_OMITS_AT_DEFAULT`; naming it there keeps every digest where it was for
styles that leave it at its default, a plain default or a factory's. A sub-table is built
now, not promised: the check, the merge, the building of a group and the schema all walk a
field typed as a dataclass as a table of its own fields, and tests show it on a planted
group, so a sub-table drops in with no change to the loader or the format.

- **C2.** Cover order (#147) is a sequence field and replaces wholesale, so a theme that
  sets it states the whole order. Pin icons (#149) are a field (or a small group table)
  that `lettering_marks._furniture` reads, defaulting to today's open ring.
- **D.** Route casing, glow and shadow (#104, #105, #106) are new `RouteInkStyle` fields
  or sub-tables typed as dataclasses (a table deep-merges, so a theme can set only a
  glow's colour), each defaulting to off and named in `DIGEST_OMITS_AT_DEFAULT` so that
  adding them moves no digest. Route labels (#159) are a field defaulting to today's behaviour.
- A field renamed later adds a row to `RENAMED_KEYS`; one removed fails as an unknown key
  with its nearest neighbour suggested.

### The guard

`tests/architecture/test_one_source_of_defaults.py` fails if a second set of values comes
back. Each check is a function over a class or a path, and each has a self-test that
plants its defect (a field with no default, a required `Style` field, a `default.yaml` or
a `.toml` file in a package written to a temporary directory, a theme that restates
`wash.blooms: true`) and shows the check reporting it, so a check cannot pass by reading
nothing:

- every field of every style group has a default (no `MISSING`), and every `Style` field
  is optional;
- `Style()` equals `Style.named("default")` and `Style.default()`;
- `src/pyntpot/maps/themes/` holds only `*.yaml` theme files and `theme.schema.json`, and
  none of them is called `default`; no `.toml` file is anywhere under `src/`;
- every theme file shipped in the package or kept in `examples/themes/` sets no key to the
  value its base already has: a file that restates a default fails, so a full copy of the
  defaults can never be reintroduced as a theme.

## Consequences

- A theme says only what it changes, and a key it leaves out paints as the default look.
  The ten example themes shrink from about 300 lines to tens.
- `PaperStyle()`, `WashStyle()`, `BrushStyle()` and `BasemapStyle()` are the house look,
  so engine examples built from them paint as a map does. The docs images those examples
  paint move once, in this feature's regeneration below.
- A bad theme fails at load, with every problem, its file and its line, before anything is
  fetched.
- `Style.from_toml` and TOML themes are gone; a caller's TOML theme fails with a pointer
  to the conversion steps.
- `maps` depends on `ruamel.yaml`.
- `vector_layers` and `basemap` called with no options now draw with the default look's
  basemap options (every landmark, cap 40, no generalisation), as a map does.

## Golden regeneration

Process as ADRs 0036 and 0052. The tolerance bound is not changed, no gate is loosened and
the hash input does not change. The goldens are regenerated once, in the plan's slice S10,
and this section is completed there with the measured values.

Expected, from the measurements on `f34de97`:

- **Do not move:** the manifest hash and `GOLDEN_HASH` (`base_digest` is unchanged), the
  Lynmouth goldens and `plates.json`, `BASE_DIGEST`, `LETTERING_DIGEST`, the place pins,
  the map-styles means, `SMOKE_SHA` (its tests read `flags_off`), and the command-line
  golden map.
- **Move:** the per-group default digests `SOURCED` for `PaperStyle`, `WashStyle` and
  `BrushStyle`, and a new `RouteInkStyle` row (their defaults changed or now exist);
  `BASEMAP_DEFAULTS` (`landmarks`, `landmark_max`, `generalise`); `DIGEST` in
  `test_style.py`, from the `drawn_as` rename only (`1b08804a7f30026b` to
  `88b356ada294ff60`), re-pinned in the rename's own slice, S8, not in S10; and each docs image whose example builds an ink or basemap group
  itself (with no arguments, or naming only some fields) or calls the basemap directly (up to 58 of the 71 registered, from the
  25 scripts the plan lists; measured by grep on `f34de97`). Each moved image is read
  against its caption and the paragraph it illustrates; a figure whose text a newly
  enabled effect contradicts either passes those flags off explicitly or has its text
  rewritten, and the regeneration lists every moved image with its fix.

(S10 replaces this list with the measured table: every moved pin and image, its old and new
value or differing fraction, and the reason.)
