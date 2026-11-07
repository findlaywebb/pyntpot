# 008 — plan

## Approach

ADR 0069 is the design; this plan is how it lands. Every fact below was measured on
`f34de97` (the branch base) unless it says otherwise. Read ADR 0069, the spec, `CLAUDE.md`
and `CONTRIBUTING.md` first; nothing else is needed.

Four moves, in this order:

1. **One source of defaults (S1).** The 25 disagreeing dataclass defaults take the
   default theme's values, `RouteInkStyle` gains defaults, every `Style` field gets a
   default, `default.toml` goes. Measured in a scratch copy: `Style()` then equals the old
   `Style.default()` and the three digests do not move, and all ten example themes resolve
   to the same digests as before. What does move is about 35 unit and property tests that
   used a no-argument group to mean "every flag off"; they move onto a named test
   configuration, `flags_off`, so their pins hold.
2. **The YAML loader (S2, S3).** New modules under `maps/` read a YAML theme with
   positions, reject the YAML features we do not allow, check every key and value against
   the model strictly, resolve `extends`, merge, and raise one `ThemeError` holding every
   problem. Then the JSON Schema.
3. **The themes (S4, S5, S6).** The ten example themes become override files (digests
   pinned before, checked after), four move into the package as named themes, the CLI
   takes a name or a path, `route_ink.style` becomes `drawn_as`.
4. **Docs, goldens, mutation (S7, S8, S9)**, then the final review (S10). The preview card
   (#79) is `specs/008a-theme-preview-card/`, its own PR.

### The regeneration window

From S1 to S8 the defaults have moved but pinned literals that hash the defaults are not
re-pinned (ADR 0006's window): they are re-measured once, in S8. During the window:

- The four non-golden tests that pin group defaults are marked
  `@pytest.mark.xfail(strict=True, reason=WINDOW)` with
  `WINDOW = "regeneration window: re-pinned in 008 S8 (ADR 0069)"`, written in each test
  module, not shared. Strict, so a pin that unexpectedly holds fails. S8 removes every
  mark: `git grep -n "regeneration window" tests` must be empty at the end of S8.
- Golden-marked tests (`-m golden`) are not run per slice, except the ones a slice names.
- Each slice's gate is the **slice gate** below. A failure there that the slice did not
  cause is a defect in an earlier slice: stop and fix it in that slice's files, never mark
  it.

## Running the gates

- **Slice gate** (every slice, before its checkpoint commit):

  ```bash
  uv run pytest -n auto --dist loadgroup --golden-tolerance -m "not golden" -q
  uv run ruff check . && uv run ruff format --check . && uv run ty check && uv run lint-imports
  prek run --all-files
  ```

  plus no file under `src/` over 400 lines (`tests/architecture/test_boundaries.py`, in
  the run above). The non-golden suite takes about a minute on four cores.
- **Golden run** (S8, S10): `uv run pytest -n auto --dist loadgroup --golden-tolerance`
  (about 27 minutes on four cores; exact, without `--golden-tolerance`, only on the pinning
  machine).
- **Strict docs build** (S7, S10), from the repo root:
  `NO_MKDOCS_2_WARNING=1 uv run --locked --group docs mkdocs build --strict -d "$SCRATCH/site"`,
  `$SCRATCH` being your scratchpad.
- **Glossary regeneration** (S7): `PYTHONPATH=tests uv run python -m support.glossary`.
- **Schema regeneration** (S3 on): `PYTHONPATH=tests uv run python -m support.theme_schema`.
- Every test written first: write it, run it, see it fail for the stated reason, then
  make it pass. Every test has a one-line docstring saying what it proves; `parametrize`
  carries `ids=`; no mocking; no `autouse`; no `print`.
- Commit a checkpoint at the end of each slice (free-form message ending with the
  attribution lines in force).

## Line budget (400; split, never thin)

| File | Now | After | Note |
| --- | --- | --- | --- |
| `src/pyntpot/maps/style.py` | 236 | ~270 | +field defaults, `from_yaml`, `named`, `themes`, `_build`; −`from_toml`, `resources` |
| `src/pyntpot/maps/style_groups.py` | 336 | ~345 | three defaults, `Literal`s, docstring; no loader code here |
| `src/pyntpot/ink/style.py` | 266 | ~268 | values only |
| `src/pyntpot/ink/brush_style.py` | 244 | ~244 | values only |
| `src/pyntpot/ink/brush.py` | — | +~25 | `BRUSH_OVERRIDE_KEYS`, `brush_id_known` |
| `src/pyntpot/letters/style.py` | 150 | ~152 | `Literal` for `label_route`, docstring |
| `src/pyntpot/maps/theme_errors.py` | new | ~80 | `ThemeProblem`, `ThemeError` |
| `src/pyntpot/maps/theme_read.py` | new | ~170 | YAML in, plain tree and lines out, YAML features rejected |
| `src/pyntpot/maps/theme_merge.py` | new | ~40 | `merge` |
| `src/pyntpot/maps/theme_check.py` | new | ~220 | keys, strict types, renamed keys |
| `src/pyntpot/maps/theme_vocab.py` | new | ~110 | dict-field vocabularies, brush ids, colours |
| `src/pyntpot/maps/theme_resolve.py` | new | ~180 | references, names, `extends` chain, cycle |
| `src/pyntpot/maps/theme_schema.py` | new | ~200 | JSON Schema from the model |
| `src/pyntpot/maps/cli.py` | 90 | ~105 | `--style VALUE`, `ThemeError` to exit 2 |

If a new module passes 360 lines while you write it, split it along a responsibility
before going on (for example `theme_check.py` into key checks and value checks), and
update this table in the same commit.

## Slices

Order: **S1 → S2 → (S3 ∥ S4) → (S5 ∥ S6) → S7 → S8 → S9 → S10**. "∥" slices own disjoint
files and may run in parallel worktrees branched from the previous checkpoint; merge both
before the next slice. Everything else is serial.

---

### S1 — One source of defaults (#158; serial)

**Owned files.** `src/pyntpot/ink/style.py`, `src/pyntpot/ink/brush_style.py`,
`src/pyntpot/maps/style_groups.py`, `src/pyntpot/maps/style.py`,
`src/pyntpot/letters/style.py` (docstring only), `src/pyntpot/maps/layers.py` (the
`basemap` docstring's `options` line only), `src/pyntpot/maps/themes/default.toml`
(deleted), `tests/support/flags_off.py` (new), `tests/support/basemaps.py`,
`tests/architecture/test_one_source_of_defaults.py` (new), and the tests listed in step 6.

**Leave alone.** `src/pyntpot/maps/candidates/export.py` (`CANDIDATE_BASEMAP` already
sets `landmarks`, `landmark_max` and `generalise` itself: it must not change), every
example script, every docs page, the example themes, `cli.py`.

Steps:

1. **Red: the guard.** Write `tests/architecture/test_one_source_of_defaults.py` with
   these tests (the theme-file test is written now and finds no theme files to check
   until S4; it asserts nothing vacuous: see below):
   - `test_every_style_group_field_has_a_default`: for each `Style.model_fields` entry,
     the annotation is a dataclass whose every `dataclasses.fields()` entry has a
     `default` or `default_factory` other than `dataclasses.MISSING`, and the
     `Style` field is not required (`not info.is_required()`).
   - `test_the_default_theme_is_the_model_with_nothing_overridden`: `Style() ==
     Style.default()`; from S5 also `== Style.named("default")` (S5 adds that line).
   - `test_no_package_file_restates_the_defaults`: under `src/pyntpot/`, no file named
     `default.*` under `maps/themes/`, no `*.toml` anywhere, and `maps/themes/` holds only
     `*.yaml` and `theme.schema.json`. Today `default.toml` makes it fail.
   - `test_no_theme_file_sets_a_key_to_its_base_value`: parametrized over
     `sorted((REPO_ROOT / "src/pyntpot/maps/themes").glob("*.yaml"))` and
     `sorted((REPO_ROOT / "examples/themes").glob("*.yaml"))`, ids the file stems; until
     S2 lands the reader, skip with `pytest.skip("no reader before 008 S2")` only when
     `pyntpot.maps.theme_read` does not import (S2 removes the skip). A second test,
     `test_the_theme_file_checks_see_every_theme`, asserts the parametrized list is
     non-empty once S4 has converted the themes (S4 adds it).
   Run: the first two fail (`RouteInkStyle` fields and `Style` fields have no default;
   `Style()` cannot be built), the third fails on `default.toml`.
2. **Red: the default look.** In `tests/unit/maps/test_style.py`, add
   `TestTheModelIsTheDefaultLook` with
   `test_a_trimmed_theme_paints_the_default_look` (a TOML file holding only
   `[wash]\nflow_rim = true\n` loads with `Style.from_toml` to a style whose
   `wash.blooms`, `paper.km_glazing` and `basemap.landmarks` are `True`, `True` and
   `"all"`: #158's reproduction) and
   `test_route_ink_builds_with_no_arguments` (`RouteInkStyle() == ROUTE_INK`, the
   module's existing pinned literal).
3. **Green: the values.** Set these dataclass defaults (every other field already
   agrees; `fluid_amount` takes the theme's literal `0.051429`):

   | Field | Old | New |
   | --- | --- | --- |
   | `PaperStyle.km_glazing`, `paper_fibre` | `False` | `True` |
   | `WashStyle.wet_bleed`, `flow_rim`, `blooms`, `sea_variation`, `silhouette_deform`, `pigment_separation`, `fluid_pass` | `False` | `True` |
   | `WashStyle.wet_bleed_px` | `5.0` | `20.0` |
   | `WashStyle.wet_bleed_mix` | `0.55` | `0.7` |
   | `WashStyle.wet_rim_drop` | `0.7` | `1.0` |
   | `WashStyle.bloom_strength` | `1.0` | `0.65` |
   | `WashStyle.wet_close_px` | `0.0` | `5.0` |
   | `WashStyle.separation_share` | `0.22` | `0.05` |
   | `WashStyle.fluid_amount` | `0.30` | `0.051429` |
   | `BrushStyle.ink_starve`, `dry_directional`, `pen_starve`, `brush_organic`, `ink_joins`, `stroke_smooth` | `False` | `True` |
   | `BasemapStyle.landmarks` | `"heuristic"` | `"all"` |
   | `BasemapStyle.landmark_max` | `8` | `40` |
   | `BasemapStyle.generalise` | `True` | `False` |
   | `RouteInkStyle.style`, `px`, `colour` | none | `"solid"`, `5.4`, `"#c22050"` |

   Check each field's `Attributes:` entry: where it says "off by default" or names the
   old value, say the new one. Reorder nothing (field order is pinned and hashed).
4. **Green: `Style`.** Each field becomes
   `paper: PaperStyle = pydantic.Field(default_factory=PaperStyle)` (and so on for all
   13). `Style.default()` becomes `return cls()`, docstring "The default look: every group
   at its model defaults, nothing overridden." Drop the `resources` import. `from_toml`
   stays (S4 removes it); its docstring loses "with a table for every group" and its
   `Raises:` loses "a group is missing". Delete `src/pyntpot/maps/themes/default.toml`
   (`git rm`). The directory is now empty: create no placeholder; S5 fills it.
5. **Green: docstrings.** Replace the "class defaults / not a resolved theme" sentences:
   `maps/style.py:6-8` ("`Style.default` reads the packaged default theme ... not the
   groups' dataclass defaults") becomes "`Style()` is the default look: every group's
   defaults are the default theme, with nothing overridden."; `maps/style_groups.py:13-16`
   becomes "The defaults are the default look; the default theme is these defaults with
   nothing overridden."; `ink/style.py:8-11` and `letters/style.py:10-12` likewise ("The
   defaults are the default look a map is painted with; the module reads no theme.");
   `letters/style.py:134-136` (`NibGroups`) says the no-argument groups are the default
   look; `maps/layers.py` `basemap`'s `options:` line says "None draws with the default
   look's basemap options." `ink/brush_style.py`'s module docstring if it names class
   defaults. Grep: `git grep -nE "class default|not a resolved theme|resolved default style" src`
   must be empty.
6. **Green: the flags-off tests.** Write `tests/support/flags_off.py`:

   ```python
   """The style groups with every phase flag off: the values the engine's mechanism tests pin.

   Key names: `FLAGS_OFF`, the field values by group, and `flags_off`, which builds one
   group with them. These are test data, named for what they are: the 25 values the
   style groups held before ADR 0069 made the defaults the default look. No package code
   reads them. Not a second set of defaults: the guard in
   `tests/architecture/test_one_source_of_defaults.py` checks package files only.
   """
   ```

   `FLAGS_OFF: dict[type, dict[str, object]]` holds exactly the "Old" column of step 3
   for `PaperStyle`, `WashStyle`, `BrushStyle` and `BasemapStyle` (not `RouteInkStyle`).
   `flags_off(group: type[G], **over: object) -> G` returns
   `group(**{**FLAGS_OFF.get(group, {}), **over})`.
   In `tests/support/basemaps.py`, rename `class_style` to `flags_off_style`, building
   each painted group with `flags_off(group, **mine)`; docstring "The packaged style with
   every painted group's phase flags off and `over` moved."; repoint its 20 callers
   (`git grep -l class_style tests`). `tiny_style` keeps its name and calls
   `flags_off_style`.

   Then run the slice gate. These tests failed in the measurement (scratch copy of
   `f34de97` with step 3 applied). Treat each by its docstring:

   - **(A) mechanism or approved plate painted with the flags off**: replace each
     no-argument `PaperStyle()`, `WashStyle()`, `BrushStyle()` or `BasemapStyle()` the
     test relies on (and a keyword-only call such as `BrushStyle(ink_starve=True)`, which
     now also turns the others on) by `flags_off(PaperStyle)`,
     `flags_off(BrushStyle, ink_starve=True)` and so on. Pins unchanged.
     `tests/unit/ink/test_keyed.py` (`TestDecoupled::test_a_stroke_that_changes_moves_no_other_stroke`,
     `TestPadStreams::test_a_repeated_stroke_takes_the_next_count`,
     `::test_joined_strokes_keep_each_its_own_brush`,
     `::test_a_join_tolerance_of_zero_joins_nothing`),
     `tests/unit/ink/test_pad.py` (`test_the_drift_along_a_stroke_repeats_and_the_flag_stops_it`,
     `test_a_road_split_into_ways_is_one_mark_again`),
     `tests/property/test_stamp.py` (`TestBlotAgainstWidth::test_the_blot_s_ink_does_not_fall_as_the_pen_widens`),
     `tests/unit/ink/test_deposit.py` (the two `test_a_wide_pool_*` and
     `test_a_narrow_pool_keeps_its_floor_radius`),
     `tests/unit/ink/test_stamp.py` (`test_a_starved_brush_runs_out_along_the_stroke`,
     `test_the_reservoir_is_read_off_the_final_density_not_the_deposits`,
     `test_a_directional_break_follows_the_stroke_not_the_sheet`,
     `test_a_nib_thins_and_lightens_as_it_runs_down`, `test_a_nib_comes_back_at_the_reload`,
     `test_both_tip_knobs_are_wired_and_each_one_earns_its_place`),
     `tests/unit/ink/test_stamp_pool.py` (`test_the_pen_sets_down_where_it_touches_and_nowhere_else`),
     `tests/unit/ink/test_wash.py` (`test_the_heavy_pigment_settles_in_the_tooth_and_the_light_one_floats`),
     `tests/unit/ink/test_pigment.py` (`test_multiply_is_still_multiply_when_glazing_is_off`),
     `tests/unit/letters/test_nib.py` (`TestBackingWash::test_the_lift_is_the_pinned_one`),
     and the eight in `tests/unit/maps/painter/test_smoke.py` (most go green from
     `flags_off_style` alone).
   - **(C) "X is off by default"**: `tests/unit/ink/test_brush.py`
     (`test_every_phase_1_brush_flag_is_off_by_default`,
     `test_every_phase_2_brush_flag_but_the_ink_grid_is_off_by_default`) and
     `test_smoke.py` (`test_every_phase_one_option_is_off_by_default`,
     `test_every_phase_two_wash_option_is_off_by_default`,
     `test_every_phase_two_tuning_field_is_inert_by_default`): rename to say "with the
     flags off" (for example `test_every_phase_1_brush_flag_off_builds_a_plain_brush`),
     build from `flags_off`, keep the assertions. The rule they guarded ("a field added
     must not move a plate until a theme asks") is now the field-default rule of ADR 0069
     and is enforced by the goldens.
   - **(B) pins a group's defaults**: mark `xfail(strict=True, reason=WINDOW)`:
     `tests/unit/maps/test_style_groups.py::test_group_defaults_equal_the_pinned_digest`
     for the `PaperStyle`, `WashStyle` and `BrushStyle` params only (use
     `pytest.param(..., marks=...)` in the parametrize list), and
     `::test_basemap_defaults_are_the_pinned_literals`.

   Any other test that fails: read its docstring; if it is about the engine with the
   flags off, (A); if it pins a default, (B) and add it to S8's list in this file; if it
   is neither, stop: it is a behaviour change the plan did not foresee. Tests that call
   `basemap(inputs)` or `basemap(inputs, BasemapStyle(roads=...))` in
   `tests/unit/maps/test_layers.py` passed in the measurement; if one fails, it is (A)
   with `flags_off(BasemapStyle, ...)`.
7. **Callers of `default.toml`.** `tests/unit/maps/test_style.py` (`THEME`, and
   `test_packaged_theme_reads_from_a_path`: delete that test, the file is gone; keep the
   others, reading `Style.default()`); `tests/unit/maps/test_cli.py:60` and
   `tests/unit/maps/test_cache_margins.py:172`: write the small theme as
   `"[card]\ndisplay_px = 120\n"` instead of copying the default (S5 turns these into
   YAML).

**Acceptance.**

```bash
uv run pytest tests/architecture/test_one_source_of_defaults.py tests/unit/maps/test_style.py -q
git grep -nE "class default|not a resolved theme|resolved default style" src   # empty
test ! -e src/pyntpot/maps/themes/default.toml
PYTHONPATH=src uv run python -c "from pyntpot.maps import Style; s=Style(); print(s==Style.default(), s.digest(), s.base_digest(), s.lettering_digest())"
# True 1b08804a7f30026b d9c56c0811177b0f d15ae2f30e9ca5ce
```

and the slice gate green, with exactly the four (B) tests reported `xfailed`.

---

### S2 — The YAML loader: read, check, merge, resolve, report (#80; serial)

**Owned files.** `pyproject.toml` (dependency and import-linter only), `uv.lock`,
`BOUNDARIES.md`, `src/pyntpot/maps/theme_errors.py`, `theme_read.py`, `theme_merge.py`,
`theme_check.py`, `theme_vocab.py`, `theme_resolve.py` (all new),
`src/pyntpot/maps/style.py`, `src/pyntpot/maps/style_groups.py` (`Literal`s),
`src/pyntpot/letters/style.py` (`label_route` `Literal`), `src/pyntpot/ink/brush.py`,
`src/pyntpot/maps/__init__.py`, `docs/reference/maps.md` (two directives),
`tests/unit/test_public_api.py`, `tests/unit/maps/test_theme_read.py`,
`test_theme_merge.py`, `test_theme_check.py`, `test_theme_resolve.py`,
`tests/unit/ink/test_brush.py` (two new tests), `tests/property/test_theme_merge.py`,
`tests/support/theme_files.py` (new), `tests/architecture/test_one_source_of_defaults.py`
(remove the skip).

**Leave alone.** The example themes and every caller of `from_toml` (S4); `cli.py` (S4,
S5); `maps/themes/` (S5); the route ink field name (S6).

Steps:

1. **Dependency and boundary.**
   - `uv add "ruamel.yaml>=0.19.1"` (repo practice is a `>=` floor in
     `[project] dependencies`, as `pydantic>=2.13`). Check `uv.lock` resolved `0.19.1`
     or later and pulled no C extension (`ruamel.yaml.clib*` must not be in the lock's
     dependency list for it).
   - `pyproject.toml` import-linter: keep the first contract's `forbidden_modules` as is
     (PyYAML's `yaml` stays banned for all of `pyntpot`); rename it "No plotting,
     dataframe, template or PyYAML dependencies". The third contract becomes
     `name = "ink and letters stay free of httpx, pydantic and ruamel"`,
     `forbidden_modules = ["httpx", "pydantic", "ruamel"]`. Comment above it:
     `# ruamel.yaml reads theme files in maps only (ADR 0069), as pydantic (ADR 0015).`
   - Prove the contract bites, in a scratch copy of the tree (not the branch): add
     `import ruamel.yaml` to `src/pyntpot/ink/noise.py`, run `uv run lint-imports`, see it
     fail naming the third contract; repeat with `import yaml` in `maps/style.py` and see
     the first fail. `ruamel` is a namespace package: if import-linter cannot see it as an
     external package, the contract fails to load; then forbid `ruamel.yaml` instead and
     record which form worked in the commit message.
   - `BOUNDARIES.md`: the intro sentence says the second contract keeps `httpx`,
     `pydantic` and `ruamel.yaml` out of `ink` and `letters` (ADRs 0010, 0069); the hard
     rules read "`pyntpot` imports no `matplotlib`, `pandas`, `jinja2` or `yaml`
     (PyYAML)." and "`ink` and `letters` import neither `httpx`, `pydantic` nor
     `ruamel.yaml`; `maps` reads theme files with `ruamel.yaml` (ADR 0069)."
   - `tests/architecture/`: no test encodes the YAML ban (checked: `git grep -ni yaml
     tests/architecture` is empty); nothing to change there.
   - `ty check` with `ruamel.yaml`: if ty reports missing stubs or unknown attributes on
     `ruamel.yaml` objects, confine every `ruamel` touch to `theme_read.py`, type the
     loaded objects as `object` and narrow with `isinstance(..., CommentedMap /
     CommentedSeq)`; do not add a ty ignore rule to `pyproject.toml`.
2. **`theme_errors.py`** (module docstring per CLAUDE.md: purpose, key types, what it
   does not do, invariants):

   ```python
   @dataclass(frozen=True, kw_only=True)
   class ThemeProblem:
       """One thing wrong with a theme file.

       Attributes:
           path: The theme file, as the caller named it (a packaged theme's path inside the package).
           key: The dotted key path, such as `wash.blooms`; empty for the file as a whole.
           line: The 1-based line of the key, or `None` when the problem has no place in the file.
           message: What is wrong, and what to write instead when that is known.
       """

       path: Path
       key: str
       line: int | None
       message: str

       def __str__(
           self,
       ) -> str: ...  # "{path}:{line}: {key}: {message}", dropping ":{line}" and "{key}: " when absent


   class ThemeError(ValueError):
       """A theme that cannot be loaded: every problem found, in file then line order."""

       problems: tuple[ThemeProblem, ...]

       def __init__(
           self, problems: Sequence[ThemeProblem]
       ) -> None: ...  # message: the problems' str, one per line
   ```

   Sorted by `(str(path), line or 0, key)`; `ThemeError` with no problems is a
   `ValueError("a theme error needs a problem")` (programming error).
3. **Red, then green: `theme_read.py`.** One function and one record:

   ```python
   @dataclass(frozen=True, kw_only=True)
   class ThemeFile:
       path: Path
       table: dict[str, object]  # plain dicts, tuples and scalars only
       lines: dict[tuple[str, ...], int]  # 1-based line of every mapping key, by key path
       problems: tuple[ThemeProblem, ...]


   def read_theme(path: Path, text: str) -> ThemeFile: ...
   ```

   Behaviour (each a test in `tests/unit/maps/test_theme_read.py`, inputs as inline
   strings, `path=Path("t.yaml")`):
   - Parse with `YAML(typ="rt")`. First walk `yaml.parse(io.StringIO(text))` events and
     report, with the event's `start_mark.line + 1` and the key path being built: an
     `AliasEvent` ("aliases are not allowed; use extends"), any event with an `anchor`
     ("anchors are not allowed; use extends"), a mapping key `ScalarEvent` whose value is
     `<<` ("merge keys are not allowed; use extends"), any event whose `tag` is not
     `None` ("tags are not allowed"), a `DocumentStartEvent` with `version` or `tags` set
     ("directives are not allowed: a theme is YAML 1.2"), a second `DocumentStartEvent`
     ("one document per theme file"). Measured with `ruamel.yaml` 0.19.1: plain scalars
     carry `tag=None`; `!!str 5` and `!foo 5` carry the tag; `&x`, `*x` and `<<` show as
     above; `%YAML 1.1` sets `version=(1, 1)` and would read `no` as `False`.
   - If the walk found problems, return them with an empty table (do not load).
   - Load with `YAML(typ="rt").load(text)`. `DuplicateKeyError` → "duplicate key" at
     `problem_mark.line + 1` with the key path; any other `ruamel.yaml.error.MarkedYAMLError`
     → its `problem` at `problem_mark.line + 1`, key empty. Catch narrowly, and
     `raise ... from exc` nowhere (the problem is returned, not raised).
   - An empty file is an empty table. A top level that is not a mapping: "a theme is a
     mapping of style groups", line 1.
   - Convert: `CommentedMap` → `dict` (keys must be strings: "keys are strings" otherwise),
     `CommentedSeq` → `tuple`, scalars as they are, recording `lines[path] =
     node.lc.key(k)[0] + 1` for every key at every depth. A `None` value is reported
     "has no value" at the key's line and its key dropped.
   - Tests also pin: `blooms: no` reads as the string `"no"` (so the checker rejects it);
     `n: 5` is the int 5; a nested key's line is right three levels deep
     (`cover.pigments.wood`); a flow mapping `{jitter_px: 0.4}`'s keys get the flow's
     line.
4. **Red, then green: `theme_merge.py`.**
   `merge(base: Mapping[str, object], over: Mapping[str, object]) -> dict[str, object]`:
   a new dict; for each key of `over`, when both values are `Mapping`, the merge of the
   two, else `over`'s value; every other key of `base` kept. Never mutates its inputs.
   Unit tests (`tests/unit/maps/test_theme_merge.py`): a nested key replaces only itself;
   a tuple replaces whole; a dict entry merges per key (`cover.pigments.wood` keeps the
   other fourteen); a table entry deep-merges (`brush.brush_overrides.lane.pool` keeps
   `lane.jitter_px`); inputs unchanged. Hypothesis (`tests/property/test_theme_merge.py`,
   a strategy of nested dicts up to depth 3, string keys from a small alphabet, leaves
   ints, floats without NaN, strings and tuples): `merge(merge(a, b), c) ==
   merge(a, merge(b, c))`; `merge(a, {}) == a`; `merge({}, a) == a`.
5. **Red, then green: vocabularies and value checks, `theme_vocab.py` and `ink/brush.py`.**
   - In `ink/brush.py`: `BRUSH_OVERRIDE_KEYS: frozenset[str]`, with an attribute
     docstring, the fifteen keys `_sheet_brush` reads from `over`: `jitter_px`,
     `press_cell_px`, `wobble_px`, `darkness`, `bristles`, `gap`, `dry`, `thr`, `texture`,
     `press`, `load`, `pool`, `bleed`, `lift`, `solid`. `brush_id_known(brush_id: str) ->
     bool`: the existing check of `brush_from_id` (`row in BRUSH_TREATMENTS and col in
     BRUSH_COLOURS.get(cls, {})`), which `brush_from_id` then calls. Tests in
     `tests/unit/ink/test_brush.py`: `test_every_override_key_changes_the_brush` (for each
     key, a `brush_overrides` entry setting it to a distinct value builds a different
     `Brush` than without it; proves the set is what is read, both ways: add a key to the
     set that nothing reads and it fails) and `test_a_brush_id_is_known_only_on_the_sheet`
     (`"MAJ6-e"` and `"TRK4-d"` known; `"MAJ9-e"`, `"XXX1-a"`, `"MAJ6"` not).
   - `theme_vocab.py`: for each dict-valued field, the set of keys a theme may give,
     computed from the model, never written out:

     | Field | Vocabulary |
     | --- | --- |
     | `paper.pigment_transparency`, `wash.separation_pigments` | keys of `CoverStyle().pigments` |
     | `cover.pigments`, `cover.cover_cfg`, `brush.river_curve`, `brush.brushes`, `brush.brush_width_px` | keys of the field's own default |
     | `brush.brush_overrides` (entry names) | keys of `BrushStyle().brushes` plus `cls.lower()` for every key of `BRUSH_COLOURS` |
     | `brush.brush_overrides.<entry>` (entry keys) | `BRUSH_OVERRIDE_KEYS` |

     Before writing the table into code, confirm each row by reading its readers:
     `maps/painter/job.py:152`, `ink/washing.py:235`, `maps/painter/cover.py:136,154`,
     `maps/card_geometry.py:94`, `maps/painter/brushes.py:52-57`,
     `maps/painter/pen.py:62,118`, `letters/nib.py:158`, `ink/brush.py:163`. If a reader
     reads a key outside its row, widen the row and say so in the commit.
     `BRUSH_ID_FIELDS = (("brush", "brushes", "*"), ("route", "route_pen_brush"),
     ("nib", "label_brush"), ("nib", "label_leader_brush"))`.
     `COLOUR_FIELDS`: every `str` field whose `Style()` value matches `#[0-9a-f]{6}`
     (`paper.paper_hex`, the four `nib.label_*ink` fields, `route_ink.colour`) plus
     `cover.pigments.*` and `wash.separation_pigments.*`. Test
     `test_every_colour_default_is_a_colour_field`: walking every `str` leaf of `Style()`
     (dict entries included), a value matching the pattern has its path in
     `COLOUR_FIELDS`, and every `COLOUR_FIELDS` path's default matches.
   - `Literal` types (step 5b): `basemap.hillshade_mode`, `sea_style`, `roads`, `rivers`,
     `landmarks`; `route_ink.blend` and (until S6) `style` as `Literal["pen", "solid"]`;
     `face.label_route` (`Literal["centreline", "outline"]`). Values exactly as ADR 0069
     lists; confirm each against its readers (`relief_layers.py:144,191`,
     `osm_elements.py:262-295`, `layers.py` for `landmarks`, `compose_steps.py:109-112`
     for `blend`, `letters/nib.py:160` for `label_route`). Write the `Literal` inline in
     the annotation (no new alias: ADR 0068 would make an alias public). Fix any `ty`
     error in a caller that passes a plain `str` by annotating that caller's value with
     the same `Literal`, never with a cast.
6. **Red, then green: `theme_check.py`.**

   ```python
   RENAMED_KEYS: dict[tuple[str, ...], str] = {}  # S6 adds route_ink.style


   def check_theme(
       theme: ThemeFile, groups: Mapping[str, type]
   ) -> tuple[dict[str, object], tuple[ThemeProblem, ...]]: ...
   ```

   `groups` is `{name: info.annotation for name, info in Style.model_fields.items()}`,
   passed by `style.py` (no import of `Style` here: no cycle). Returns the table with
   every valid leaf converted to its field type (ints to floats where the field is a
   float, through the adapter) and invalid leaves dropped, plus every problem:
   - top-level keys: `extends` (must be a `str`: "extends is a theme name or a .yaml
     path") and the group names; anything else unknown.
   - Unknown key at any level (group, dict field entry, `brush_overrides` entry key):
     "unknown key; did you mean {near}?" with `difflib.get_close_matches(key, known, n=1,
     cutoff=0.6)`, else "unknown key". A key in `RENAMED_KEYS`: "renamed to {new}" (and no
     suggestion).
   - A group or dict field given a non-mapping: "is a table of keys".
   - Each leaf: `pydantic.TypeAdapter(hint, config=pydantic.ConfigDict(strict=True))`,
     cached per hint with `functools.cache`; a dict field validates each entry with its
     value type, so each entry has its own path and line. Messages from the pydantic
     error `type`: `bool_type` "{v!r} is not a boolean (true or false)"; `float_type`
     "{v!r} is not a number"; `int_type` "{v!r} is not a whole number"; `string_type`
     "{v!r} is not a string"; `tuple_type` "{v!r} is not a list"; `literal_error`
     "{v!r} is not one of {choices}" (choices quoted, comma-joined, from `typing.get_args`);
     `too_long` / `too_short` "a list of {n} values, not {m}"; any other type, pydantic's
     `msg`. Measured: strict mode accepts `5` for a `float` (as `5.0`) and rejects `"5"`,
     `True` for a number, `1` for a `bool`, `5.0` for an `int`, a list for a tuple (the
     reader already made sequences tuples).
   - Brush ids at `BRUSH_ID_FIELDS`: "{v!r} is not a brush on the sheet".
   - Colours at `COLOUR_FIELDS`: "{v!r} is not a # and six hexadecimal digits".
   - Lines from `theme.lines[path]`; the line of the nearest present ancestor otherwise.
   Tests (`tests/unit/maps/test_theme_check.py`, one class per family, inputs from
   `tests/support/theme_files.py`'s `theme_file(text: str, name: str = "t.yaml") ->
   ThemeFile`, a thin call of `read_theme`): every bullet above, including
   `wash.blom` suggesting `blooms`, `cover.cover_cfg.wod` suggesting `wood`,
   `brush.brush_overrides.lane.jiter_px` suggesting `jitter_px`, `blooms: no` →
   "'no' is not a boolean (true or false)", `display_px: "900"`, `bloom_max: 5.5`,
   `cover.cover_cfg.wood: [0.1, 0.2, 0.3]`, `basemap.roads: some`,
   `brush.brushes.lane: LAN9-z`, `route_ink.colour: red`; a file with three problems
   reports all three in line order; a renamed key, using a local table passed through a
   `renamed` keyword argument of `check_theme` (default `RENAMED_KEYS`), says
   "renamed to"; the valid leaves of a file with an error are still returned converted.
7. **Red, then green: `theme_resolve.py`.**

   ```python
   NAME = re.compile(r"[a-z][a-z0-9-]*")


   def theme_names() -> tuple[str, ...]: ...  # "default" plus the stems of maps/themes/*.yaml, sorted
   def resolve(
       ref: str | Path, *, relative_to: Path, groups: Mapping[str, type], base: Mapping[str, object]
   ) -> dict[str, object]: ...
   ```

   `base` is the defaults table `style.py` passes (`{name: dataclasses.asdict(group)}`
   of `Style()`). Reference rule, in order: a `Path` or a `str` ending `.yaml` is a path
   (relative to `relative_to`); ending `.yml`: "theme files end in .yaml; did you mean
   '{stem}.yaml'?"; ending `.toml`: "themes are YAML since ADR 0069: see 'Convert a TOML
   theme' in the theme how-to"; matching `NAME` and in `theme_names()`: that packaged
   theme (`default` is `base` itself, no file); matching `NAME` but not known: "no theme
   named '{ref}'; available: {names}"; anything else: "'{ref}' is neither a theme name
   nor a .yaml path; available: {names}". Packaged files are read through
   `importlib.resources.files("pyntpot.maps") / "themes"` with `resources.as_file`.
   A missing file: "no such theme file". The chain: read and check the file, follow its
   `extends` (default `"default"`, relative paths from the extending file's directory),
   until `default`; a resolved path seen before is "extends cycle: a.yaml -> b.yaml ->
   a.yaml" on the `extends` key's line. Every file's problems are collected; if any,
   `raise ThemeError(problems)`; else fold `merge` from `base` through the chain, base
   first, and drop `extends`. Tests (`tests/unit/maps/test_theme_resolve.py`, files in
   `tmp_path`): each rule above; a three-file chain (`c.yaml` extends `b.yaml` extends
   `a.yaml`) applies in order; a relative `extends: ../shared/base.yaml` resolves from
   the extending file; a two-file cycle and a self-cycle; problems in two files of a chain
   are both reported; a missing `extends` means `default`.
8. **Green: `Style`.** In `maps/style.py`:
   - `from_yaml(cls, path: Path) -> Self`: `resolve(path, relative_to=Path.cwd(), ...)`
     then `cls._build(table)`. Docstring with `Raises: ThemeError: When the file or any
     theme it extends has a problem; every problem is in its problems.`
   - `_build(cls, table) -> Self`: `cls(**{name: groups[name](**table[name]) for name in
     groups})`.
   - Keep `_reject_unknown_group_keys` and `_check_keys`: `model_validate` of a dict stays
     a supported pydantic entry point.
   - Export `ThemeError` and `ThemeProblem` from `pyntpot.maps` (`__init__.py` import and
     `__all__`, sorted), add `::: pyntpot.maps.ThemeError` and
     `::: pyntpot.maps.ThemeProblem` to `docs/reference/maps.md` in the section the other
     maps errors sit in, and add both to `tests/unit/test_public_api.py`'s pinned list.
   - Tests in `test_style.py`, `TestFromYaml`: a minimal file loads; a file with an error
     raises `ThemeError` whose `problems[0].line` is right; `Style.from_yaml` on a
     packaged-default reference (`extends: default` and nothing else) equals `Style()`.
9. **Green: the property that matters.** In `tests/property/test_theme_merge.py`,
   `test_an_override_and_its_expanded_copy_give_one_digest`: draw a set of leaf paths
   from `Style()`'s table (bools flipped, numbers scaled by a drawn factor in (0.5, 2),
   colours from a strategy of `#rrggbb`), write them as an override YAML (`ruamel.yaml`
   dump of the plain tree, tuples as lists) in `tmp_path`, write the expanded copy (the
   whole merged table dumped), load both with `Style.from_yaml`: equal `digest()`. Use a
   `tmp_path_factory` per example or `tempfile.TemporaryDirectory()` (function-scoped
   `tmp_path` and Hypothesis do not mix). `tests/support/theme_files.py` gets
   `dump_theme(table: Mapping[str, object]) -> str`.
10. **Guard.** Remove the skip from `test_no_theme_file_sets_a_key_to_its_base_value` and
    implement it: read the file with `read_theme`, resolve its base (the `extends`
    reference via `resolve`, or `Style()`'s table), and for every leaf the file sets
    (walking dict fields to their entries), assert it differs from the base's value at
    that path after type conversion; on failure name the file and the key path.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_read.py tests/unit/maps/test_theme_merge.py tests/unit/maps/test_theme_check.py tests/unit/maps/test_theme_resolve.py tests/property/test_theme_merge.py tests/unit/ink/test_brush.py tests/unit/maps/test_style.py tests/unit/test_public_api.py -q
uv run lint-imports
git grep -n "ruamel" src | grep -v "^src/pyntpot/maps/theme_read.py"   # empty
```

and the slice gate green.

---

### S3 — The schema (parallel with S4)

**Owned files.** `src/pyntpot/maps/theme_schema.py` (new),
`src/pyntpot/maps/themes/theme.schema.json` (new), `docs/reference/theme.schema.json`
(new), `tests/support/theme_schema.py` (new, the regenerator),
`tests/unit/maps/test_theme_schema.py` (new), `mkdocs.yml` (only if the build excludes
`.json`; it does not by default).

**Leave alone.** Every theme file (S4 adds their directive lines), `style.py`.

Steps:

1. **Red.** `tests/unit/maps/test_theme_schema.py`:
   - `test_the_committed_schemas_are_the_generated_one`: both JSON files, parsed, equal
     `theme_schema()`; on failure the assertion message is
     "regenerate: PYTHONPATH=tests uv run python -m support.theme_schema".
   - `test_every_field_is_in_the_schema_with_its_default`: for every group field,
     `schema["properties"][group]["properties"][field]["default"]` equals the field's
     `Style()` value in JSON form (tuples as lists).
   - `test_every_level_forbids_other_keys`: every object in the schema has
     `"additionalProperties": false`, except dict fields' entry objects, which have
     `propertyNames` `{"enum": [...]}` from `theme_vocab` and `additionalProperties`
     set to the entry's value schema.
   - `test_the_enums_are_the_literals`: each `Literal` field has `"enum"` equal to its
     `typing.get_args`.
   - `test_extends_is_the_one_extra_top_level_key`, `test_no_key_is_required` (no
     `"required"` anywhere).
   - `test_every_theme_key_is_a_schema_path`: for every `*.yaml` under `maps/themes/` and
     `examples/themes/` (empty until S4/S5), walk the file's keys through the schema
     (`properties`, then `additionalProperties` for dict entries) and check enum values;
     a test-local walker, no new dependency. Add `test_the_theme_files_name_a_schema`:
     each file's first line is `# yaml-language-server: $schema=<target>` and `<target>`,
     resolved from the file's directory, is an existing file or is
     `https://findlaywebb.github.io/pyntpot/reference/theme.schema.json`.
2. **Green.** `theme_schema.py`: `theme_schema() -> dict[str, object]`, hand-walked over
   `Style.model_fields` and each group's `dataclasses.fields` with
   `typing.get_type_hints`: `bool` → `{"type": "boolean"}`; `int` → `"integer"`;
   `float` → `"number"`; `str` → `"string"` (`"pattern": "^#[0-9a-fA-F]{6}$"` at
   `COLOUR_FIELDS`); `Literal` → `"enum"`; `tuple[X, ...]` → `"array"` with `items`;
   `tuple[X, Y]` → `"array"`, `prefixItems`, `minItems` = `maxItems` = 2;
   `dict[str, V]` → `"object"` with `propertyNames` and `additionalProperties` = V's
   schema. Each field: `"default"` (JSON form) and `"description"`: its `Attributes:`
   entry from the group's docstring (parse the Google section: an entry starts at 8
   spaces and `name:`, continuation lines are deeper; join with spaces). Each group:
   `"description"`, its class docstring's summary line. Top level: `"$schema":
   "https://json-schema.org/draft/2020-12/schema"`, `"$id":
   "https://findlaywebb.github.io/pyntpot/reference/theme.schema.json"`, `"title":
   "pyntpot theme"`, `"type": "object"`, `"additionalProperties": false`, `extends`
   (`"type": "string"`, description "A theme name or a .yaml path this theme overrides;
   default when absent."). `theme_schema` imports `Style` (one direction: `style.py` does
   not import `theme_schema`).
   `tests/support/theme_schema.py`: `main()` writes `json.dumps(theme_schema(),
   indent=2, sort_keys=False) + "\n"` to both paths, logging each (no `print`).
3. Run the regenerator; commit both JSON files.

**Acceptance.** `uv run pytest tests/unit/maps/test_theme_schema.py -q`; the regenerator
run twice leaves `git status` clean; the slice gate green.

---

### S4 — The ten example themes as overrides (#80; parallel with S3)

**Owned files.** `examples/themes/*` (ten `.toml` deleted, ten `.yaml` added),
`examples/map_styles.py`, `examples/place_card.py`, `examples/social_preview.py`,
`examples/how_to_route_ink.py`, `tests/unit/maps/test_example_themes.py`,
`tests/support/docs_images.py` (theme paths only), `tests/golden/test_places.py` (theme
paths only), `tests/fixtures/sweep_span_scale.py` (theme paths only),
`src/pyntpot/maps/style.py` (remove `from_toml`), `src/pyntpot/maps/cli.py` (line 77
only: `Style.from_yaml`), `tests/unit/maps/test_style.py` (TOML tests),
`tests/unit/maps/test_cli.py`, `tests/unit/maps/test_cache_margins.py`,
`tests/architecture/test_one_source_of_defaults.py` (the non-empty check).

**Leave alone.** `theme_schema.py` and the JSON (S3), `maps/themes/` (S5), docs pages
(S7), the four named themes' move (S5: in this slice they are converted in
`examples/themes/`).

Steps:

1. **Pin before converting.** Add to `tests/unit/maps/test_example_themes.py`:

   ```python
   #: Each example theme's digests, measured from the TOML files on f34de97 and unchanged by 008 S1.
   DIGESTS = {
       "ambleside-hero": ("86ee79977c816d4e", "149792857eb4656a", "6331518a202c936d"),
       "ambleside": ("dbf735ec2626eea1", "1fbd4375dceec789", "6331518a202c936d"),
       "bold": ("93dfd74809cc40ae", "6d77f74215314006", "2a7a209c41fe7df8"),
       "oxford": ("eb46db87c3080b61", "0f73e166ba6ba263", "36480f1b92757e09"),
       "pen-and-ink": ("0295772c0971d18a", "0d40a30d74c111e0", "9c4b7732ec2b6d7d"),
       "sepia": ("5f385631c67344df", "3a2f5fbbd424e347", "9f7523b1ae707038"),
       "skye": ("3a172bc9c6816e7a", "b54086dfe786d1f0", "1976288541cb3b07"),
       "winter": ("6fd3e5385f7bd0c0", "c1b7c47d4ea12d6c", "68d9f8d8810bd9bb"),
       "y-fenni": ("d2e1c4c2ddacb647", "90c968b5e78d7058", "3c27e8f97c00b9c4"),
       "yr-wyddfa": ("53e17a182a7d962b", "58c70051932a610f", "6331518a202c936d"),
   }
   ```

   (`digest`, `base_digest`, `lettering_digest`), and
   `test_each_theme_resolves_to_its_pinned_digests`, parametrized with `ids=` the names,
   loading `examples/themes/{name}.toml` with `Style.from_toml`. Run it: green on the S2
   checkpoint (measured: identical before and after S1's defaults). Commit this alone
   ("pin the example themes' digests before conversion"). If any value differs, stop: S1
   changed what a theme resolves to.
2. **Convert.** In your scratchpad (not committed), a script that for each TOML theme:
   loads it with `Style.from_toml`, takes `Style()`'s table as the base, and emits every
   leaf whose value differs from the base (dict entries one by one, a `brush_overrides`
   entry key by key), as YAML through `ruamel.yaml` with block style for mappings, flow
   style for sequences, strings quoted only where YAML needs it plus every `#rrggbb`
   colour double-quoted. Groups in `Style` field order, keys in the group's field order,
   dict entries sorted. The file starts:

   ```yaml
   # yaml-language-server: $schema=../../src/pyntpot/maps/themes/theme.schema.json
   # <the TOML file's own header comment lines, kept verbatim, # included>
   ```

   No `extends` line (the base is `default`). Hand-check one file against its TOML
   (`ambleside-hero` has the extra `brush.brush_overrides.major.pool`). Delete the TOML
   files with `git rm`.
3. **Switch the loaders and the callers.** Change the pinned-digest test to load
   `{name}.yaml` with `Style.from_yaml`; it must stay green with the same literals.
   Then repoint every `examples/themes/*.toml` path to `.yaml`
   (`git grep -n "themes/[a-z-]*\.toml"` over `examples/` and `tests/` must be empty):
   `tests/support/docs_images.py:168,343-346,375,386,397,495`,
   `tests/golden/test_places.py:109,129,146,164,182`,
   `tests/fixtures/sweep_span_scale.py:65-67`, the example scripts' docstrings and
   `THEMES_DIR` globbing (`map_styles.py` reads `{name}.yaml`), and `cli.py:77`
   (`Style.from_yaml`; S5 rewrites it).
4. **Remove `from_toml`.** Delete the method and `import tomllib` from `style.py`. In
   `test_style.py`, the TOML-based rejection tests (`test_unknown_top_level_key_is_rejected`,
   the misspelt-key tests, the effect and sport-ink tests) become YAML equivalents
   through `Style.from_yaml`, asserting `ThemeError` with the key path and line; S1's
   `test_a_trimmed_theme_paints_the_default_look` reads a YAML file
   (`wash:\n  flow_rim: true\n`). `test_cli.py` and `test_cache_margins.py` write
   `small.yaml` holding `card:\n  display_px: 120\n`. Add
   `test_a_toml_theme_is_refused_with_the_conversion_pointer` to `test_theme_resolve.py`
   if S2 did not already.
5. **Rewrite `test_example_themes.py`'s framing:** module docstring "The example themes
   in `examples/themes/` are YAML overrides that load and differ from the default and
   each other."; `test_the_directory_holds_exactly_these_themes` pins the ten `.yaml`
   stems; `TestShowcaseThemes` unchanged in substance.
6. **Guard.** Add `test_the_theme_file_checks_see_every_theme` to
   `tests/architecture/test_one_source_of_defaults.py` (the parametrized list has 10
   entries now, 10 after S5's move too: 6 examples plus 4 packaged), and run
   `test_no_theme_file_sets_a_key_to_its_base_value` on the converted files: green.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_example_themes.py tests/architecture/test_one_source_of_defaults.py tests/unit/maps/test_style.py tests/unit/maps/test_cli.py -q
git grep -nE "from_toml|tomllib" src tests examples   # empty
git grep -nE "themes/[a-z-]+\.toml" src tests examples   # empty
wc -l examples/themes/*.yaml   # each well under 100
uv run pytest tests/golden/test_map_styles.py tests/golden/test_places.py --golden-tolerance -q   # the theme-dependent goldens: unmoved
```

and the slice gate green.

---

### S5 — Named themes and the command line (#77; parallel with S6)

**Owned files.** `src/pyntpot/maps/themes/{pen-and-ink,sepia,bold,winter}.yaml` (moved
from `examples/themes/` with `git mv`), `src/pyntpot/maps/style.py` (`named`, `themes`),
`src/pyntpot/maps/cli.py`, `examples/map_styles.py`, `tests/unit/maps/test_example_themes.py`,
`tests/unit/maps/test_theme_named.py` (new), `tests/unit/maps/test_cli.py`,
`tests/architecture/test_one_source_of_defaults.py` (the `named` line),
`tests/support/docs_images.py` (only if an entry names one of the four paths),
`tests/golden/test_map_styles.py` (only if it names a path).

**Leave alone.** `style_groups.py`, `strands.py`, `compose_steps.py`, `theme_check.py`
(S6); docs pages (S7).

Steps:

1. **Red.** `tests/unit/maps/test_theme_named.py`:
   `test_the_packaged_themes_are_listed` (`Style.themes() == ("bold", "default",
   "pen-and-ink", "sepia", "winter")`); `test_default_is_the_model` (`Style.named("default")
   == Style()`); `test_each_named_theme_keeps_its_digests` (the four, against their rows
   of S4's `DIGESTS`, moved out of `test_example_themes.py` into this module, since the
   files moved; the comment above them says they were measured from the TOML files on
   `f34de97`); `test_an_unknown_name_lists_the_names`
   (`ThemeError` message contains "available: bold, default, pen-and-ink, sepia, winter");
   `test_a_name_must_be_lower_case_and_hyphenated` (`"Sepia"`, `"sepia_2"`, `"2sepia"`
   refused by the rule's message); `test_a_theme_can_extend_a_named_theme` (a `tmp_path`
   file `extends: sepia` with one override equals `Style.named("sepia")` with that
   field replaced); `test_every_named_theme_paints_the_lynmouth_card` (each name, through
   `fetch`, `paint`, `letter`, `compose` on the Lynmouth fixture cache at
   `display_px: 120`, as `tests/unit/maps/test_cli.py` does: returns an image of the
   card's size); `test_each_named_theme_is_package_data` (for each name,
   `resources.files("pyntpot.maps").joinpath("themes", f"{name}.yaml").is_file()`; the
   built wheel is checked by the acceptance command).
2. **Green.** `git mv examples/themes/{pen-and-ink,sepia,bold,winter}.yaml
   src/pyntpot/maps/themes/`; change their first line to
   `# yaml-language-server: $schema=theme.schema.json`. `Style.named(cls, name: str) ->
   Self` and `Style.themes(cls) -> tuple[str, ...]` delegate to `theme_resolve`
   (`named` refuses a `.yaml` value: "Style.named takes a name; use Style.from_yaml for a
   file"). `examples/map_styles.py` loads `Style.named(figure)` and its docstring says the
   four are packaged themes; `test_example_themes.py` pins the six remaining stems;
   S1's guard adds `== Style.named("default")`.
3. **The command line.** `cli.py`: `--style` is `type=str`, `metavar="THEME"`, help
   "a theme name or a .yaml theme file; the default look when absent". `main` resolves it
   with the private class method `Style._from_reference(value: str) -> Self`, which calls
   `theme_resolve.resolve(value, relative_to=Path.cwd(), ...)` and `_build` (the CLI is
   its only caller, so it is not API). Catch `ThemeError` only around that call, log
   `"pyntpot map: %s"` per problem with `log.error`, return 2. Update the module
   docstring synopsis. Tests in `test_cli.py`: `--style sepia` paints;
   `--style small.yaml` paints; `--style missing` returns 2 and logs the available names
   (read with `caplog`); `--style old.toml` returns 2 and logs the ADR 0069 pointer.
   `tests/docs/test_reference_values.py` checks the `cli.md` synopsis against the parser:
   update `docs/reference/cli.md`'s synopsis line for `--style THEME` in this slice so the
   docs tests stay green (the rest of that page is S7's).

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_named.py tests/unit/maps/test_cli.py tests/unit/maps/test_example_themes.py tests/architecture tests/docs -q
uv build --wheel -o "$SCRATCH/dist" && unzip -l "$SCRATCH"/dist/*.whl | grep -E "maps/themes/(bold|pen-and-ink|sepia|winter)\.yaml|theme\.schema\.json"   # five lines
uv run pyntpot map --help | grep -- "--style THEME"
```

and the slice gate green.

---

### S6 — The route ink's `drawn_as` (#182; parallel with S5)

**Owned files.** `src/pyntpot/maps/style_groups.py`, `src/pyntpot/maps/strands.py`,
`src/pyntpot/maps/compose_steps.py`, `src/pyntpot/maps/style.py` (`with_route_ink`
docstring only), `src/pyntpot/maps/theme_check.py` (`RENAMED_KEYS` row),
`examples/how_to_route_ink.py`, `tests/unit/maps/test_route_ink.py`,
`tests/unit/maps/painter/test_pen_strands.py`, `tests/unit/maps/test_style_groups.py`
(`PINNED` field names, line 386), `tests/unit/maps/test_style.py` (`ROUTE_INK`, line 239,
the rename tests), `tests/unit/maps/test_theme_check.py`,
`tests/unit/maps/test_example_themes.py` (the digest literals),
`src/pyntpot/maps/themes/theme.schema.json` and `docs/reference/theme.schema.json`
(regenerated).

**Leave alone.** `cli.py` and `test_theme_named.py` (S5). If S5 has not merged, the four
named themes are still in `examples/themes/`; neither slice edits them (none sets
`route_ink.style`, measured: every theme says `"solid"`, which the converter dropped as
the default).

Steps:

1. **Red.** `test_theme_check.py`: `test_the_old_route_ink_key_says_it_was_renamed`
   (`route_ink:\n  style: pen\n` → one problem, key `route_ink.style`, message
   "renamed to drawn_as", line 2); `test_drawn_as_takes_pen_or_solid`
   (`drawn_as: pne` → "'pne' is not one of 'pen', 'solid'"). `test_style.py`:
   `ROUTE_INK` uses `drawn_as="solid"`.
2. **Green.** Rename the field (`drawn_as: Literal["pen", "solid"] = "solid"`), its
   `Attributes:` entry ("`pen` tints the painted pen plate when one was painted; `solid`
   draws the line."), the two readers (`strands.py:64`, `compose_steps.py:74`), the
   `with_route_ink` docstring ("when `drawn_as` is `"pen"`"), every test and example use
   (`git grep -nE "ink\.style\b|route_ink\.style\b|style=\"(pen|solid)\"|\"style\": \"solid\"|_inked_as"`),
   `_inked_as`'s parameter in `test_pen_strands.py`, `PINNED` in `test_style_groups.py`.
   Add `RENAMED_KEYS[("route_ink", "style")] = "drawn_as"` (as a literal entry in the
   dict, with the comment `# ADR 0069 (#182)`).
3. **Re-pin the example digests**, because the rename moves every `digest()` (the field
   name is hashed) and neither of the other two. Measured on a scratch copy with S1's
   defaults and the rename:

   | Theme | `digest()` after the rename |
   | --- | --- |
   | ambleside-hero | `57ddfa002ea48593` |
   | ambleside | `afccd911c2e29ce4` |
   | bold | `2b765c09e23cbcb2` |
   | oxford | `379133aed2dd33bb` |
   | pen-and-ink | `0034f4055bb18feb` |
   | sepia | `1ea34b096b744d93` |
   | skye | `8d80163e184edea7` |
   | winter | `0e767aa91ac66511` |
   | y-fenni | `7161092827e066b7` |
   | yr-wyddfa | `79f5230efc0d75e4` |

   Replace the first element of each `DIGESTS` row (in `test_example_themes.py`, and, when
   S5 has merged, the four rows it moved into `test_theme_named.py`) with these; the `base_digest` and
   `lettering_digest` elements stay. If a value differs, stop and find out why: the
   rename must move nothing else. `test_style.py`'s `DIGEST` is a window pin: mark
   `test_default_digests_are_pinned` `xfail(strict=True, reason=WINDOW)` (expected new
   value `88b356ada294ff60`, re-pinned in S8).
4. Regenerate the schema.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_route_ink.py tests/unit/maps/painter/test_pen_strands.py tests/unit/maps/test_theme_check.py tests/unit/maps/test_example_themes.py tests/unit/maps/test_theme_schema.py -q
git grep -nE "ink\.style\b|route_ink\.style\b" src tests examples   # only the RENAMED_KEYS row and its test
```

and the slice gate green.

---

### S7 — Docs (serial)

**Owned files.** `docs/how-to/write-a-theme.md`, `docs/reference/style-fields.md`,
`docs/reference/cli.md`, `docs/how-to/map-from-the-command-line.md`,
`docs/how-to/change-the-route-ink.md`, `docs/how-to/letter-your-own-landmarks.md`,
`docs/tutorials/first-map.md`, `docs/index.md`, `docs/gallery.md`,
`docs/explanation/data-policy.md`, `docs/architecture.md`, `docs/reference/index.md`,
`GLOSSARY.md`, `docs/reference/glossary.md` and `docs/includes/abbreviations.md`
(regenerated), `tests/docs/test_reference_values.py`, `README.md` (only if it names TOML
themes), the notes listed below, `docs/features/docs-missing-how-tos.md`,
`docs/features/cli-wider-commands.md`, `docs/features/ink-data-driven-brushes-and-pigments.md`,
`docs/features/docs-examples-housekeeping.md`, `docs/features/maps-cover-layering-order.md`,
`docs/issues/letters-route-means-trace.md`,
`docs/issues/maps-route-ink-leaves-marker-labels-pink.md` (facts only), and the new
`docs/issues/maps-numeric-ranges-unchecked.md`.

**Leave alone.** `src/`, every test outside `tests/docs/`, the images.

Steps (write every page as if themes had always been YAML overrides; no "now", no "since
this feature", no history; ADR numbers only where a page already cites ADRs):

1. **`write-a-theme.md`**, sections in this order: Steps (write `my-theme.yaml` with the
   directive line, `extends: sepia`, two overrides; load with `Style.from_yaml`; or pass
   `--style my-theme.yaml`); "Choose a theme by name" (`Style.themes()`, `Style.named`,
   `--style sepia`); "What a theme can say" (merge rules: tables merge, lists and
   colours replace, table fields merge per entry; `extends` chains; what is refused:
   anchors, aliases, merge keys, tags, directives; `no` is a string); "Editor completion"
   (the directive line with the site URL; the Red Hat YAML extension); "When a theme
   does not load" (an example `ThemeError` output, three lines, with file, line and key);
   "Convert a TOML theme" (heading text exactly that: the resolver's message names it;
   steps: load the old file's values, keep the ones that differ from the default, write
   them as YAML; a 10-line Python snippet using `tomllib`, `Style()` and
   `dataclasses.asdict`); "Four packaged themes" (the existing four pictures and their
   prose, now naming `src/pyntpot/maps/themes/<name>.yaml` and `--style <name>`). Drop
   the "feature is not built" link.
2. **`style-fields.md`**: Type column in YAML terms (`boolean`, `integer`, `number`,
   `string`, `list`, `table`, `one of a, b, c` for a `Literal`); Default is "the model's
   default, which is the default look"; the "Reading the tables" bullets rewritten (a
   theme names only what it changes; every key is checked; see the schema at
   `reference/theme.schema.json`); each table field gets a sub-table of its keys and
   default values (#186). `tests/docs/test_reference_values.py`: extend the style-field
   comparator to the sub-tables (every key of each dict field's default has one row with
   its value, and no other row) and to the `one of` types (equal to the `Literal`'s
   args). Write the test change first and see it fail on the old page.
3. **`cli.md`, `map-from-the-command-line.md`** (its known-message list loses the
   pydantic traceback and gains a `ThemeError` example), **`change-the-route-ink.md`**
   (`drawn_as`), **`first-map.md`**, **`index.md`**, **`gallery.md`**,
   **`data-policy.md`**, **`letter-your-own-landmarks.md`**: every `.toml` theme path and
   `from_toml` becomes the YAML form or a name (`git grep -nE "\.toml|from_toml|toml" docs/*.md docs/*/*.md README.md`
   leaves only `examples/places.toml` and the conversion section).
   **`docs/architecture.md`**: the style row names the `theme_*` modules and says
   `maps` reads YAML with `ruamel.yaml`.
4. **`GLOSSARY.md`**: "theme" becomes "A YAML file that names a base theme with
   `extends` and gives only the style fields it changes; a theme name such as `sepia`
   chooses a packaged one. The default theme is the model's defaults with nothing
   overridden." (In the code: `pyntpot.maps.Style.named`, `pyntpot.maps.Style.from_yaml`;
   Tooltip `no`.) Add "base theme": "The theme an override theme's `extends` names; its
   values hold wherever the override is silent. `default` when `extends` is absent."
   (Tooltip `base theme`.) "route ink": "its `drawn_as` (`pen` or `solid`)". Regenerate
   the glossary files.
5. **Notes.** Delete `docs/issues/maps-theme-missing-keys-take-dataclass-defaults.md`
   (#158), `docs/issues/maps-route-ink-style-key.md` (#182),
   `docs/features/maps-themes-as-overrides.md` (#80), `docs/features/maps-named-themes.md`
   (#77), `docs/features/docs-style-field-table-keys.md` (#186): the docs now describe
   each. Repoint or drop every link to them (`git grep -n` each file name outside
   `specs/` and `docs/decisions/`). Update facts in the notes that cite the old format:
   `docs-missing-how-tos.md:40-46`, `cli-wider-commands.md` (themes are YAML, `--style`
   takes names; `theme clone` and `theme check` remain), `ink-data-driven-brushes-and-pigments.md:11`
   (YAML is the theme format, ADR 0069), `docs-examples-housekeeping.md` (themes named
   by name), `maps-cover-layering-order.md` (a list field replaces wholesale),
   `letters-route-means-trace.md` (add: "A rename adds a row to
   `maps.theme_check.RENAMED_KEYS`."), and `maps-route-ink-leaves-marker-labels-pink.md`
   if it names `default.toml`.
6. **File** `docs/issues/maps-numeric-ranges-unchecked.md` (heading "A theme's numeric
   values are not range-checked at load", second line the GitHub issue link) only if
   `display_px: -5` still loads at this point (check). The GitHub issue is the
   orchestrator's (no remote writes from the slice): list it in the commit message as
   "to file".

**Acceptance.** `uv run pytest tests/docs tests/architecture -q`; the strict docs build;
`git grep -nE "default\.toml|from_toml" -- ':!specs' ':!docs/decisions' ':!CHANGELOG.md'`
empty; the slice gate green.

---

### S8 — Golden regeneration (serial)

**Owned files.** `tests/unit/maps/test_style_groups.py` (`SOURCED`, `BASEMAP_DEFAULTS`,
a `RouteInkStyle` row), `tests/unit/maps/test_style.py` (`DIGEST`), every module holding a
window mark, `docs/images/**`, `tests/golden/docs/**` (the masters), any other golden S1
listed, and ADR 0069's "Golden regeneration" section.

**Leave alone.** `src/`, examples (unless step 3 says otherwise), every theme file.

Steps:

1. Process as ADRs 0036 and 0052 on the pinning machine (exact) if available, else under
   `--golden-tolerance` and say so in the ADR. The tolerance bound is not changed.
2. **The pins.** Re-measure and re-pin `SOURCED` (`PaperStyle`, `WashStyle`,
   `BrushStyle`; add `RouteInkStyle`, which now builds), `BASEMAP_DEFAULTS`, and `DIGEST`
   (expected `88b356ada294ff60`: if it differs, stop). Remove every window mark:
   `git grep -n "regeneration window" tests` empty.
3. **The docs images.** `PYTHONPATH=tests uv run python tests/golden/make_docs_images.py "$SCRATCH/docs-new" --compare docs/images`
   then `tests/golden/diff_images.py` on the moved ones. For each moved image under
   `explanation/` or `reference/`, read the paragraph the image illustrates: if the prose
   describes an effect shown alone and the new default turns another effect on in that
   figure (for example blooms in a figure about the wash body), make the example pass
   that field explicitly (`WashStyle(blooms=False)`), update any tutorial block that
   quotes the changed lines, and repaint; otherwise accept the move. List every such
   edit. Then regenerate in place with `make_docs_images.py docs/images` (and the masters
   per the script's options) and compare once more.
4. **The goldens that must not move**: run the full golden suite. The Lynmouth parity
   (and `plates.json`), `GOLDEN_HASH`, `BASE_DIGEST`, `LETTERING_DIGEST`, `SMOKE_SHA`, the
   place pins, the map-styles means and the CLI golden map pass unchanged. A failure among
   these is a defect: stop and fix it in the slice that caused it.
5. **Record**: replace the expected list in ADR 0069's "Golden regeneration" with a
   table: each moved pin (old, new, reason: "default is the default look", "field renamed
   drawn_as", "now buildable"), each moved image with its master's differing fraction and
   reason ("built from `PaperStyle()`: glazing and fibre on", and so on per script), the
   explicit edits from step 3, and the unmoved list with their values. Publish the image
   diffs for the PR body with `tests/golden/publish_diffs.py --push` (ADR 0052).

**Acceptance.** `uv run pytest -n auto --dist loadgroup --golden-tolerance -q` green;
`git grep -n "regeneration window" tests` empty; ADR 0069's section has no "Expected"
wording left.

---

### S9 — Mutation testing (serial, local only)

Per `CONTRIBUTING.md` "Mutation testing". The changed `ink` and `letters` functions are
`brush_id_known`, `brush_from_id` (its check now calls it) and any function S1 or S8
touched; the default-value edits are not functions. Run:

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

Kill each survivor with a focused test in `tests/unit/ink` or `tests/unit/letters`, or
name it as equivalent in the PR description with the reason. The `maps/theme_*` modules
are outside mutmut's scope (`only_mutate` is `ink` and `letters`); instead, review their
tests against each branch of the code by reading (every message in S2 steps 3 to 7 has a
test), and record the result in `specs/008-themes-as-data/mutation.md` as 006 did.

---

### S10 — Final review (serial, fresh context)

A fresh-context reviewer reads the spec, ADR 0069 and the diff, ticks each acceptance
criterion against evidence, and writes `specs/008-themes-as-data/review/diff-review.md`.
Then the full gates (golden run, `prek run --all-files`, strict docs build), and the PR:
title `feat(maps)!: themes are YAML overrides of one model, chosen by name`, the spec's
Changelog block, `Closes #158`, `Closes #80`, `Closes #77`, `Closes #182`, `Closes #186`,
the golden-diff images, the mutation equivalents, the files filed in S7.

## Files to touch

Everything named under a slice's "Owned files", and nothing else. New files:
`src/pyntpot/maps/theme_{errors,read,merge,check,vocab,resolve,schema}.py`,
`src/pyntpot/maps/themes/{bold,pen-and-ink,sepia,winter}.yaml`,
`src/pyntpot/maps/themes/theme.schema.json`, `docs/reference/theme.schema.json`,
`examples/themes/{ambleside,ambleside-hero,oxford,skye,y-fenni,yr-wyddfa}.yaml`,
`tests/support/{flags_off,theme_files,theme_schema}.py`,
`tests/architecture/test_one_source_of_defaults.py`,
`tests/unit/maps/test_theme_{read,merge,check,resolve,schema,named}.py`,
`tests/property/test_theme_merge.py`, `specs/008-themes-as-data/mutation.md`,
`specs/008-themes-as-data/review/*`. Deleted: `src/pyntpot/maps/themes/default.toml`,
`examples/themes/*.toml`, the five notes of S7.

## Files to leave alone

- `examples/places.toml` and every other TOML data file: not themes.
- `src/pyntpot/maps/candidates/export.py`: its basemap options are explicit already.
- `src/pyntpot/maps/cache.py`, `pipeline.py`, `painter/*`: the digests they read do not
  change shape.
- `tests/golden/test_parity.py` and the Lynmouth goldens: nothing they record moves.
- `DIGEST_OMITS_AT_DEFAULT`: its four fields already default to the default look.
- `CONSUMER_ONLY`: cover order and pin icons are C2.
- `mkdocs.yml` nav (no new page: the schema is a file, the how-to and reference pages
  exist).
- `.pre-commit-config.yaml`, CI workflows: no new gate.

## Delegation

S1, S2 and S4 carry the design risk: give each to one implementer with this plan and ADR
0069 only. S3 ∥ S4 and S5 ∥ S6 run in parallel worktrees branched from the previous
checkpoint and merge before the next slice (the only shared file between S5 and S6 is
`style.py`, in different methods; between S3 and S4, none). S7 is docs only and can be a
cheaper model with the pages listed. S8 needs the pinning machine or a long run; S9 is
local. S10 is a fresh reviewer.

## Decisions

The plan's own choices, beyond ADR 0069:

- **`flags_off` keeps the mechanism tests' pins** instead of re-pinning ~35 tests to the
  default look. The tests are about mechanisms with the flags off; the default look is
  covered by the goldens. `SMOKE_SHA` therefore does not move.
- **Validation per file, then merge**, so every problem names its own file and the merged
  table needs no second check.
- **Vocabularies from the model's defaults**, plus one ink constant for the brush-override
  keys, so no key list is written twice.
- **No `jsonschema` dependency**: a test-local walker checks theme files against the
  schema.
- **No removal syntax**: the ten example themes need none.
- **The CLI's resolver is a private `Style._from_reference`**: one caller, not API.
- **#186 is folded in**: the style-fields page pointed at `default.toml`, which goes.
- **#79 is `specs/008a-theme-preview-card/`**: a new fixture and an example script, judged
  on its own, after this PR.
