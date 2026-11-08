# Diff review: 008 themes as data (claude/trusting-babbage-i3edsh vs f34de97)

Read-only review. Targeted suites run green with `-p no:randomly`: theme_*, property merge, architecture, reference values, style, cli, example themes. lint-imports is green, and the wheel holds the four YAML themes and the schema. Every finding below was reproduced with a real file in the scratchpad.

## Blocking

### B1. Control characters escape `read_theme` as a raw ruamel `ReaderError`; the CLI prints a traceback
- `src/pyntpot/maps/theme_read.py:210` catches only `MarkedYAMLError`. `ruamel.yaml.reader.ReaderError` (raised for NUL and the other disallowed characters) is a plain `YAMLError`, so it gets past that handler.
- Repro: `printf 'wash:\n  blooms: tr\x00ue\n' > t.yaml; pyntpot map n.gpx -o x.png --cache c --contact a@b --style t.yaml` gives a traceback ending `ruamel.yaml.reader.ReaderError: unacceptable character #x0000`.
- What this breaks: the module invariant "read_theme never raises for a bad file". It also breaks the spec criterion "A bad theme prints every problem and exits 2, with no traceback", and the bar's "no silent or raw failures".
- Fix: catch `ReaderError` as well, which carries `.position` (or catch `YAMLError` and locate it when a mark exists). Add a test with a NUL and with a C1 control character.

### B2. Duplicate keys with different spellings get past the walk, and the load raises `DuplicateKeyError`
- `theme_read.py:264` `_duplicate` compares raw scalar text. Keys that resolve to the same value but are spelled differently are not seen as duplicates, so the round-trip load at `theme_read.py:96` raises.
- Repro: `null: 1\n~: 2\n`, `true: 1\nTrue: 2\n`, `card:\n  1: a\n  0x1: b\n`. Each gives `ruamel.yaml.constructor.DuplicateKeyError` out of `Style.from_yaml`, not a `ThemeError`.
- Quoted and escaped duplicates (`"blooms"`, `"blooms"`) are caught correctly, because those are string keys.
- Fix: compare keys after resolving them: (resolved tag, constructed value). Alternatively, since a non-string key is always an error, report any plain key whose resolved tag is not `str` as "keys are strings" in the walk, so the load never sees it.

## Should-fix

### S1. A non-UTF-8 theme raises a raw `UnicodeDecodeError`
- `theme_resolve.py:187` and `:209` call `path.read_text(encoding="utf-8")` with nothing around them.
- Repro: `printf 'wash:\n  blooms: \xff\n'` gives `UnicodeDecodeError` from `from_yaml` and a traceback from the CLI.
- Fix: catch `UnicodeDecodeError` (and `OSError`) and turn it into a `ThemeProblem` ("is not UTF-8 text" at the byte's line, or with no line).

### S2. A wrong `extends` is reported against the wrong file
- `theme_resolve.py:219` (`_refuse`) uses `path=Path(theme)` for chained refusals. The same happens at `:186` for a missing target.
- Repro: a file `badname.yaml` holding `extends: Bold` reports `Bold:1: extends: 'Bold' is neither a theme name…`. The error names a file that does not exist, at the extending file's line. With `extends: old.toml` the report is `old.toml:1: …`.
- With `extends: missing.yaml` the report is `…/missing.yaml: no such theme file`, which names neither the extending file nor its line.
- Only the cycle case uses `where.by`.
- This follows plan.md lines 952-956 as written, but it fails the spec's "each with file, dotted key path and line" and the bar's "the file".
- Fix: use `where.by or Path(theme)` as the problem path in `_refuse`, and in the missing-file case use `where.by` / `where.key` / `where.line`, with a message naming the target ("no such theme file: missing.yaml"). Pin both cases in `test_theme_resolve.py`.

## Nits

- N1. Deep flow nesting raises `RecursionError` out of `read_theme`. `a: [[[…` with 2000 levels, or 600 nested `{b: …}`, does it. It is adversarial, but it breaks the "never raises" invariant. Bound the depth in the walk (for example, more than 32 levels is "too deeply nested").
- N2. Stale theme-TOML wording, which matters for forward compatibility with #149:
  - `docs/features/maps-lettering-pin-icons.md:20-21` says "under `[lettering]` in the theme TOML".
  - `docs/features/maps-lettering-label-placement-tuning.md:162` says "theme's TOML".
  - Both should say YAML (`lettering:`).
- N3. `_refuse` builds `Path(theme)`, which normalises `./bold` to `bold`, so the CLI prints `bold: './bold' is neither…`, and `''` comes out as `.`.
- N4. `Style._reject_unknown_group_keys` / `_check_keys` (`style.py`) are left over from the TOML loader. `_build` passes built dataclasses, so the loader never reaches them; only a direct `Style(wash={...})` dict does. Delete them, or say in the docstring which path they guard.

## Checked and fine

- YAML 1.2 `no`, strict types (`5.0` for an int, `true` for a float and `"5"` all refused; an int for a float accepted), enums, colours, brush ids, renamed key, unknown-key suggestions at every level, and dict-entry vocabularies all behave as specified.
- Anchors, aliases, tags, directives, a second document, empty and comment-only files (both give the default), a top-level list or scalar (refused), a relative `extends` two directories up, and a self-cycle all behave correctly.
- All problems in a file come back together, sorted by line.
- The one-source-of-defaults guard with planted self-tests, the schema drift test, the Hypothesis properties (associativity, empty override, expanded-copy digest), the import guards and the PyYAML ban are in place.
- Digests: base and lettering are unchanged; `digest()` re-pinned to `88b356ada294ff60` with ADR row.
- No `route_ink.style` / `style="pen"` leftovers; no `from_toml`/`default.toml` outside specs/ADRs; no TODO/print.
- Notes deleted as listed.

## Closes

- #158, #80, #77, #182 and #186 are substantively met.
- I would not claim "a wrong theme fails at load with file, key, line" for #80/#77 until B1, B2, S1 and S2 are fixed, because the CLI can still crash with a traceback, or point at a file that does not exist.
- tasks.md lines 61 and 98-100 are still unticked: the merge gate, the diff review, the full gates and the PR.

## Resolution

All eight findings were fixed in commit 0a52f1e, each with a test that failed first. A Hypothesis property (`tests/property/test_theme_read.py`) now guards that loading a theme raises nothing but `ThemeError`. Item 7 is partly done: the message quotes the name as given, but the location prefix is a `Path` and so is normalised.
