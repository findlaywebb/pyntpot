# 008 — Themes as data

GitHub issues: [#158](https://github.com/findlaywebb/pyntpot/issues/158) (a theme that
leaves out a key paints with the dataclass default, not the default theme),
[#80](https://github.com/findlaywebb/pyntpot/issues/80) (a theme could declare only what
it changes), [#77](https://github.com/findlaywebb/pyntpot/issues/77) (themes could ship
in the package and be chosen by name),
[#182](https://github.com/findlaywebb/pyntpot/issues/182) (the route ink's `style` key
overloads Style) and [#186](https://github.com/findlaywebb/pyntpot/issues/186) (the
style-fields page could list the keys of its table fields: folded in, because the page
points at `default.toml`, which this feature deletes). The preview card,
[#79](https://github.com/findlaywebb/pyntpot/issues/79), is the sub-spec
`specs/008a-theme-preview-card/`, its own PR after this one.

Branch: `claude/trusting-babbage-i3edsh`. Decision record: ADR 0069
(`docs/decisions/0069-themes-are-yaml-overrides-of-one-model.md`). Scope source:
`specs/005-feature-scoping/sessions.md` section C.

## Problem

A theme is a TOML file holding every key of every style group, and the style groups hold a
second, different set of values as their dataclass defaults. A key a theme leaves out is
filled from the dataclass, silently, and 25 of those values are not the default look
(#158). So every theme is a full copy of the default: ten example themes of about 300 lines
each, changing 22 to 46 values (#80). Only one theme ships, and nothing chooses another by
name (#77). Keys inside dict-valued fields and the values of string enums are not checked,
`"5"` loads as a number, and errors name no file or line. The route ink's `style` field
reuses the word the whole style goes by (#182).

## Acceptance criteria

### One source of defaults (#158)

- [ ] Every field of every style group has a dataclass default equal to the default look
      (the value `src/pyntpot/maps/themes/default.toml` holds on `f34de97`);
      `RouteInkStyle()` builds; `opacity` is an explicit default.
- [ ] Every `Style` field has a default; `Style()`, `Style.default()` and
      `Style.named("default")` are equal, and `Style().digest()`, `base_digest()` and
      `lettering_digest()` equal `1b08804a7f30026b`, `d9c56c0811177b0f` and
      `d15ae2f30e9ca5ce` until the rename below moves `digest()` alone.
- [ ] `src/pyntpot/maps/themes/default.toml` is deleted and no file restates the defaults.
- [ ] `tests/architecture/test_one_source_of_defaults.py` fails when a group field has no
      default or a `Style` field is required, when `Style()` differs from the default
      theme, when a `default.*` file or any `.toml` file appears under `src/`, or when a
      shipped or example theme sets a key to the value its base already has. Each check
      is a function over a class or a path, and a self-test plants its defect and shows
      the check reporting it: a planted dataclass field and `Style` field, and planted
      files in `tmp_path` (a `default.yaml` and a `.toml` file under a package, a theme
      restating `wash.blooms: true`). `Style()` equal to the default theme is asserted
      directly.
- [ ] Docstrings of `ink/style.py`, `ink/brush_style.py`, `letters/style.py`,
      `maps/style_groups.py` and `maps/style.py` say the defaults are the default look;
      none says "class defaults" or "not a resolved theme".

### Themes as YAML overrides (#80)

- [ ] A theme is a `.yaml` file read with `ruamel.yaml` (YAML 1.2) that names its base in
      a top-level `extends` and gives only overrides; a missing `extends` means `default`;
      chains resolve recursively and a cycle is an error naming it.
- [ ] Merge: tables deep-merge; scalars, sequences and tuples replace; dict fields merge
      per entry, a table entry deep-merging. Hypothesis properties: merge is associative
      over inputs of one fixed shape (each key always a table or always a leaf, as the
      model fixes it); an empty override gives its base; an override file and its fully
      expanded copy give equal `digest()`.
- [ ] Rejected at load, each with file, dotted key path and line: duplicate keys, anchors,
      aliases, merge keys (`<<`), explicit tags, `%` directives, more than one document,
      a key with no value, unknown keys at every level (dict-field entries and
      `brush_overrides` entry keys included) with a `difflib` suggestion, wrong types
      under strict rules (`"5"` for a number, `1` for a boolean, `5.0` for an integer),
      enum values outside their `Literal`, unknown brush ids, colours that are not
      `#rrggbb`, and renamed keys. All problems in a file are reported together in one
      `ThemeError`, every duplicate key included; problems of the YAML itself (syntax,
      duplicates, anchors, aliases, merge keys, tags, directives) are reported before any
      key or type check.
- [ ] A field typed as a dataclass (a sub-table, none today) is checked, merged, built and
      written into the schema as a table of its own fields, shown on a planted group, so
      a later sub-table needs no loader or format change.
- [ ] YAML 1.2 typing: `blooms: no` is an error ("'no' is not a boolean"), never `False`.
- [ ] `ink` and `letters` cannot import `ruamel` (import-linter); `maps` can; PyYAML stays
      banned everywhere; `BOUNDARIES.md` says so.
- [ ] `Style.from_toml` is gone; `Style.from_yaml(path)` loads a file; a `.toml` theme
      path, given as a `str` or a `Path`, fails with "themes are YAML since ADR 0069" and
      the how-to's conversion section; `.yml` fails suggesting `.yaml`.
- [ ] Each of the ten example themes is a YAML override file setting no key to its base's
      value, and resolves to the `digest()`, `base_digest()` and `lettering_digest()`
      pinned in `plan.md` (S6) from the TOML files before conversion.

### The schema

- [ ] `src/pyntpot/maps/themes/theme.schema.json` and `docs/reference/theme.schema.json`
      are the JSON Schema generated from the model in override form (every key optional,
      `additionalProperties: false`, enums, defaults, field docs, `extends`); a test fails
      when either differs from the regenerated schema and prints the regenerating command.
- [ ] Every theme file's first line is a `# yaml-language-server: $schema=...` directive
      naming a schema that exists; every key path of every shipped and example theme is a
      property path of the schema, and every enum value it sets is in the schema's enum
      (test; no new dependency).

### Named themes and the command line (#77)

- [ ] `pen-and-ink`, `sepia`, `bold` and `winter` live in `src/pyntpot/maps/themes/` as
      override files, moved from `examples/themes/` (not copied), and are in the built
      wheel.
- [ ] `Style.named(name)` and `Style.themes()` (`("bold", "default", "pen-and-ink",
      "sepia", "winter")`); a bad name lists the available names.
      `Style.from_theme(theme, relative_to=None)` takes a name or a `.yaml` path by the
      rule below; the command line and the examples that take a theme use it.
- [ ] `pyntpot map --style VALUE`: a value ending `.yaml` is a path, anything else a name
      matching `^[a-z][a-z0-9-]*$`; `extends` follows the same rule, relative paths from
      the extending file. A bad theme prints every problem and exits 2, with no traceback.
- [ ] Every named theme loads and paints the Lynmouth fixture card (test).

### The route ink's drawn_as (#182)

- [ ] `RouteInkStyle.drawn_as: Literal["pen", "solid"] = "solid"` replaces `style`; the
      two readers use it; `route_ink.style` in a theme fails with
      "`route_ink.style: renamed to drawn_as`" from the `RENAMED_KEYS` table.

### Docs

- [ ] `docs/how-to/write-a-theme.md` teaches writing an override theme, `extends`, the
      named themes, editor completion with the schema, reading an error, and converting a
      TOML theme, as if the feature had always existed.
- [ ] `docs/reference/style-fields.md` states each field's YAML type and model default,
      lists each dict field's keys and default values (#186), and is checked against the
      model by `tests/docs/test_reference_values.py`; `docs/reference/cli.md` and the
      map-styles pages name themes by name.
- [ ] `GLOSSARY.md`: "theme" redefined; "base theme" added; "route ink" says `drawn_as`;
      the site glossary regenerated.
- [ ] Notes deleted: `docs/issues/maps-theme-missing-keys-take-dataclass-defaults.md`,
      `docs/issues/maps-route-ink-style-key.md`, `docs/features/maps-themes-as-overrides.md`,
      `docs/features/maps-named-themes.md`, `docs/features/docs-style-field-table-keys.md`;
      every link to them repointed.

### Whole feature

- [ ] Goldens regenerated once, in S10; ADR 0069's "Golden regeneration" section lists
      every moved pin and image with its value or differing fraction and reason; the
      Lynmouth goldens, `GOLDEN_HASH`, `BASE_DIGEST`, `LETTERING_DIGEST`, `SMOKE_SHA`, the
      place pins and the map-styles means do not move.
- [ ] Mutation testing run on the changed `ink` and `letters` functions; survivors killed
      or named as equivalent in the PR description.
- [ ] No file under `src/` over 400 lines; no mocking; logging only; full gates green:
      `uv run pytest -n auto --dist loadgroup --golden-tolerance`, `prek run --all-files`,
      the strict docs build.
- [ ] The PR body says `Closes #158`, `Closes #80`, `Closes #77`, `Closes #182`,
      `Closes #186`.

## Changelog

PR title:

```
feat(maps)!: themes are YAML overrides of one model, chosen by name
```

Under "Changelog" in the PR description:

```
fix(maps): a theme that leaves out a key paints the default look, not a port-era class default
feat(ink)!: PaperStyle, WashStyle and BrushStyle default to the default look (glazing, fibre, wet bleed, blooms and the brush flags on)
feat(maps)!: BasemapStyle and RouteInkStyle default to the default look; RouteInkStyle() builds
feat(maps)!: themes are YAML files that extend a base and give only overrides; Style.from_toml is replaced by Style.from_yaml
feat(maps): Style.named and Style.themes load the packaged themes pen-and-ink, sepia, bold and winter by name, and Style.from_theme takes a name or a .yaml path
feat(cli): pyntpot map --style takes a theme name or a .yaml path
feat(maps): every theme problem is reported at load with its file, key and line, in one ThemeError
feat(maps): a JSON Schema for theme files, for editor completion
feat(maps)!: the route ink's style field is renamed drawn_as and takes pen or solid only
docs(docs): the style-fields page lists the keys of its table fields
```

## Out of scope, filed separately

Already filed, not done here:

- #147 cover order (`docs/features/maps-cover-layering-order.md`) and #149 pin icons
  (`docs/features/maps-lettering-pin-icons.md`): session C2, new fields in this format.
- #104, #105, #106 route casing, glow and shadow (`docs/features/maps-route-casing.md`,
  `maps-route-glow.md`, `maps-route-shadow.md`) and #159 marker labels
  (`docs/issues/maps-route-ink-leaves-marker-labels-pink.md`): session D.
- #68 wider CLI (`docs/features/cli-wider-commands.md`): `pyntpot theme clone` and
  `theme check`, more map options; session G. S9 updates that note's facts only.
- #181 `face.label_route` means the trace (`docs/issues/letters-route-means-trace.md`):
  S8 leaves a `RENAMED_KEYS` table it can reuse; S9 adds that sentence to the note.
- #79 the preview card: `specs/008a-theme-preview-card/`.

Found while planning, to be filed in S9 if still true (note plus issue):

- `maps-numeric-ranges-unchecked.md` (enhancement, area: maps): numeric ranges
  (`display_px: -5`, `opacity: 2`) are not checked at load.
