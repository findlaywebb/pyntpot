# 008 — tasks

Slices and their files are in `plan.md`. Order: S1, S2, then S3 and S4 in parallel, the
merge gate, then S5, S6, S7, S8, S9, S10 in turn. The preview card (#79) is
`specs/008a-theme-preview-card/`, after this PR.

## Start

- [ ] Start: comment the branch `claude/trusting-babbage-i3edsh` and spec `008` on #158, #80, #77, #182 and #186 (#79: spec `008a`).
- [ ] ADR 0069 and its index row (pointers on 0002, 0005, 0015, 0020, 0037, 0046); spec, plan, tasks; `specs/008a-theme-preview-card/` spec and plan.
- [ ] Plan-reviewer passes the plan (round 1 blocked; round 2 on the revised plan).

## S1 — One source of defaults (#158)

- [ ] Red: `tests/architecture/test_one_source_of_defaults.py`: the checks as functions (fields without a default, required `Style` fields, package files that restate the defaults), each with a self-test that plants the defect (a field with no default, a required field, `default.yaml`, a `.toml` file, a stray file) and sees it reported; `Style()` is the default theme.
- [ ] Red: a trimmed theme paints the default look; `RouteInkStyle()` builds.
- [ ] The 25 dataclass defaults set to the default look; `RouteInkStyle` defaults; every `Style` field defaulted; `Style.default()` is `Style()`.
- [ ] `default.toml` deleted; its three test callers repointed (`_theme_with` replaced by `_write_theme` and six inline TOML snippets).
- [ ] Docstrings say the defaults are the default look (grep empty).
- [ ] `tests/support/flags_off.py`; `class_style` renamed `flags_off_style`; the (A) and (C) tests on `flags_off`, pins unchanged.
- [ ] The four (B) default pins marked for the regeneration window.
- [ ] Digests unchanged (`1b08804a7f30026b`, `d9c56c0811177b0f`, `d15ae2f30e9ca5ce`); slice gate green.

## S2 — The YAML loader

- [ ] `ruamel.yaml>=0.19.1` added; import-linter forbids `ruamel` in `ink` and `letters`, keeps PyYAML banned; shown to bite on a scratch copy; `BOUNDARIES.md`.
- [ ] `ThemeProblem`, `ThemeError`; exported, documented, pinned in the public API test.
- [ ] `theme_read`: positions; the event walk reports anchors, aliases (once each), merge keys, tags, directives, extra documents, non-string keys, every duplicate key with its key path, and a syntax error from `parse()`, before any load or check; empty values refused; `no` is a string.
- [ ] `theme_merge` and its Hypothesis properties over one fixed shape (associative; empty override is the base; inputs unchanged); the leaf-between-tables counterexample pinned.
- [ ] `BRUSH_OVERRIDE_KEYS` and `brush_id_known` in `ink/brush.py`, each proved against what `brush_from_id` reads.
- [ ] `theme_vocab`: vocabularies confirmed against their readers; colour fields checked against the defaults.
- [ ] `Literal` types for the nine string enums; the two `ty` errors fixed in `test_nib.py:396` and `test_layers.py:77`.
- [ ] `theme_check`: unknown keys with suggestions, strict types (a short tuple reported from pydantic's `missing`), brush ids, colours, renamed-keys table, dataclass sub-tables (planted group), `build_group`; every problem in one error.
- [ ] `theme_resolve`: names by `NAME.fullmatch`, `.yaml` paths, `.yml` and `.toml` refusals for a `str` and a `Path`, a missing `themes/` directory, `extends` chains, cycles; merges the converted tables.
- [ ] `Style.from_yaml`; the digest rule reads a factory default; an override and its expanded copy give one digest (property: bools flipped, integers rounded).
- [ ] The theme-file guard and its planted-file self-tests; slice gate green.

## S3 — The schema

- [ ] Red: committed schemas equal the generated one; defaults, enums, `additionalProperties`, `extends`, nothing required; a dataclass sub-table is an object of its fields; theme keys are schema paths; directive lines resolve.
- [ ] `theme_schema.py`; regenerator `support.theme_schema`; both JSON files committed; slice gate green.

## S4 — The example themes as overrides (#80)

- [ ] The ten themes' digests pinned from the TOML files, green before conversion, committed alone.
- [ ] Ten `.yaml` override files with the schema directive; TOML files removed.
- [ ] Every caller repointed, the six docs pages' caption and command theme paths included; `Style.from_toml` removed with its two `ALLOWED` entries; `.yaml` scanned for retired words; TOML tests rewritten for YAML.
- [ ] Pinned digests unchanged after conversion; map-styles and place goldens unmoved; each acceptance grep prints what the plan states; slice gate green.

## Merge gate

- [ ] S3 and S4 merged; the whole slice gate green on the merged tree.

## S5 — Named themes and the command line (#77)

- [ ] pen-and-ink, sepia, bold and winter moved into `src/pyntpot/maps/themes/`; in the wheel.
- [ ] `Style.named`, `Style.themes`, public `Style.from_theme`; every named theme paints the Lynmouth card.
- [ ] `pyntpot map --style THEME`: name or `.yaml` path through `Style.from_theme`; problems logged, exit 2; `cli.md` synopsis and `--style` section; the examples load with `Style.from_theme`.
- [ ] Slice gate green.

## S6 — drawn_as (#182)

- [ ] Red: the old key says renamed; `drawn_as` takes pen or solid.
- [ ] Field, readers, tests, example and `RENAMED_KEYS` row; schema regenerated.
- [ ] `style-fields.md`'s `drawn_as` row.
- [ ] Example digests re-pinned to the plan's post-rename literals in `test_example_themes.py` and `test_theme_named.py`; `DIGEST` in the window; slice gate green.

## S7 — Docs

- [ ] Red: the style-fields comparator covers table-field keys and enum types (#186).
- [ ] `write-a-theme.md` with "Convert a TOML theme"; `style-fields.md` with table keys (#186); CLI, how-to, tutorial and landing pages on YAML and names.
- [ ] `GLOSSARY.md`: theme, base theme, route ink; glossary files regenerated.
- [ ] Notes for #158, #182, #80, #77 and #186 deleted, links repointed; related notes' facts updated; numeric-ranges note written if still true, its issue listed to file.
- [ ] Strict docs build and slice gate green.

## S8 — Golden regeneration

- [ ] `SOURCED` (with `RouteInkStyle`), `BASEMAP_DEFAULTS` and `DIGEST` (`88b356ada294ff60`) re-pinned; no window mark left.
- [ ] Docs images repainted; only the 25 listed scripts' images moved; each moved image judged against its caption and paragraph, each flagged one given fix A or B; the table of moved images recorded.
- [ ] The unmoved goldens shown unmoved: Lynmouth, `GOLDEN_HASH`, `BASE_DIGEST`, `LETTERING_DIGEST`, `SMOKE_SHA`, places, map styles, CLI map.
- [ ] ADR 0069's "Golden regeneration" holds the measured table; diffs published.

## S9 — Mutation testing

- [ ] Changed `ink` and `letters` functions run; survivors killed or named as equivalent; `mutation.md`.

## S10 — Final review and PR

- [ ] Fresh-context diff review (`review/diff-review.md`); every acceptance criterion ticked against evidence.
- [ ] Full gates green: golden run, `prek run --all-files`, strict docs build.
- [ ] PR opened: `Closes #158` (#158), `Closes #80` (#80), `Closes #77` (#77), `Closes #182` (#182), `Closes #186` (#186), Changelog block, the list of moved docs images, golden diffs, mutation equivalents.
