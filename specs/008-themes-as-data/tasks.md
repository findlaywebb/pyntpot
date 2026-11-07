# 008 — tasks

Slices and their files are in `plan.md`. Order: S1, S2, then S3 and S4 in parallel, then
S5 and S6 in parallel, then S7, S8, S9, S10. The preview card (#79) is
`specs/008a-theme-preview-card/`, after this PR.

## Start

- [ ] Start: comment the branch `claude/trusting-babbage-i3edsh` and spec `008` on #158, #80, #77, #182 and #186 (#79: spec `008a`).
- [ ] ADR 0069 and its index row (pointers on 0002, 0005, 0015, 0020, 0037, 0046); spec, plan, tasks; `specs/008a-theme-preview-card/` spec and plan.
- [ ] Plan-reviewer passes the plan (round 1).

## S1 — One source of defaults (#158)

- [ ] Red: `tests/architecture/test_one_source_of_defaults.py` (every field has a default; `Style()` is the default theme; no `default.*` or `.toml` under `src/`; theme files restate nothing).
- [ ] Red: a trimmed theme paints the default look; `RouteInkStyle()` builds.
- [ ] The 25 dataclass defaults set to the default look; `RouteInkStyle` defaults; every `Style` field defaulted; `Style.default()` is `Style()`.
- [ ] `default.toml` deleted; its three test callers repointed.
- [ ] Docstrings say the defaults are the default look (grep empty).
- [ ] `tests/support/flags_off.py`; `class_style` renamed `flags_off_style`; the (A) and (C) tests on `flags_off`, pins unchanged.
- [ ] The four (B) default pins marked for the regeneration window.
- [ ] Digests unchanged (`1b08804a7f30026b`, `d9c56c0811177b0f`, `d15ae2f30e9ca5ce`); slice gate green.

## S2 — The YAML loader

- [ ] `ruamel.yaml>=0.19.1` added; import-linter forbids `ruamel` in `ink` and `letters`, keeps PyYAML banned; shown to bite on a scratch copy; `BOUNDARIES.md`.
- [ ] `ThemeProblem`, `ThemeError`; exported, documented, pinned in the public API test.
- [ ] `theme_read`: positions; anchors, aliases, merge keys, tags, directives, extra documents, duplicates and empty values refused; `no` is a string.
- [ ] `theme_merge` and its Hypothesis properties (associative; empty override is the base).
- [ ] `BRUSH_OVERRIDE_KEYS` and `brush_id_known` in `ink/brush.py`, each proved against what `brush_from_id` reads.
- [ ] `theme_vocab`: vocabularies confirmed against their readers; colour fields checked against the defaults.
- [ ] `Literal` types for the nine string enums.
- [ ] `theme_check`: unknown keys with suggestions, strict types, brush ids, colours, renamed-keys table; every problem in one error.
- [ ] `theme_resolve`: names, `.yaml` paths, `.yml` and `.toml` refusals, `extends` chains, cycles.
- [ ] `Style.from_yaml`; an override and its expanded copy give one digest (property).
- [ ] The theme-file guard implemented; slice gate green.

## S3 — The schema

- [ ] Red: committed schemas equal the generated one; defaults, enums, `additionalProperties`, `extends`, nothing required; theme keys are schema paths; directive lines resolve.
- [ ] `theme_schema.py`; regenerator `support.theme_schema`; both JSON files committed; slice gate green.

## S4 — The example themes as overrides (#80)

- [ ] The ten themes' digests pinned from the TOML files, green before conversion, committed alone.
- [ ] Ten `.yaml` override files with the schema directive; TOML files removed.
- [ ] Every caller repointed; `Style.from_toml` removed; TOML tests rewritten for YAML.
- [ ] Pinned digests unchanged after conversion; map-styles and place goldens unmoved; slice gate green.

## S5 — Named themes and the command line (#77)

- [ ] pen-and-ink, sepia, bold and winter moved into `src/pyntpot/maps/themes/`; in the wheel.
- [ ] `Style.named`, `Style.themes`; every named theme paints the Lynmouth card.
- [ ] `pyntpot map --style THEME`: name or `.yaml` path; problems logged, exit 2; `cli.md` synopsis.
- [ ] Slice gate green.

## S6 — drawn_as (#182)

- [ ] Red: the old key says renamed; `drawn_as` takes pen or solid.
- [ ] Field, readers, tests, example and `RENAMED_KEYS` row; schema regenerated.
- [ ] Example digests re-pinned to the plan's post-rename literals; `DIGEST` in the window; slice gate green.

## S7 — Docs

- [ ] Red: the style-fields comparator covers table-field keys and enum types (#186).
- [ ] `write-a-theme.md` with "Convert a TOML theme"; `style-fields.md` with table keys (#186); CLI, how-to, tutorial and landing pages on YAML and names.
- [ ] `GLOSSARY.md`: theme, base theme, route ink; glossary files regenerated.
- [ ] Notes for #158, #182, #80, #77 and #186 deleted, links repointed; related notes' facts updated; numeric-ranges note written if still true, its issue listed to file.
- [ ] Strict docs build and slice gate green.

## S8 — Golden regeneration

- [ ] `SOURCED` (with `RouteInkStyle`), `BASEMAP_DEFAULTS` and `DIGEST` (`88b356ada294ff60`) re-pinned; no window mark left.
- [ ] Docs images repainted; explanation figures checked against their prose; any explicit flags listed.
- [ ] The unmoved goldens shown unmoved: Lynmouth, `GOLDEN_HASH`, `BASE_DIGEST`, `LETTERING_DIGEST`, `SMOKE_SHA`, places, map styles, CLI map.
- [ ] ADR 0069's "Golden regeneration" holds the measured table; diffs published.

## S9 — Mutation testing

- [ ] Changed `ink` and `letters` functions run; survivors killed or named as equivalent; `mutation.md`.

## S10 — Final review and PR

- [ ] Fresh-context diff review (`review/diff-review.md`); every acceptance criterion ticked against evidence.
- [ ] Full gates green: golden run, `prek run --all-files`, strict docs build.
- [ ] PR opened: `Closes #158` (#158), `Closes #80` (#80), `Closes #77` (#77), `Closes #182` (#182), `Closes #186` (#186), Changelog block, golden diffs, mutation equivalents.
