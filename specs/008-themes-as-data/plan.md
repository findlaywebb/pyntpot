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
2. **The YAML loader (S2, S3, S4), then the schema (S5).** New modules under `maps/`:
   S2 reads a YAML theme with positions and rejects the YAML features we do not allow;
   S3 checks every key and value against the model strictly; S4 resolves `extends`,
   merges, and raises one `ThemeError` holding every problem, behind `Style.from_yaml`.
   Then the JSON Schema.
3. **The themes (S6, S7, S8).** The ten example themes become override files (digests
   pinned before, checked after), four move into the package as named themes, the CLI
   and the examples take a name or a path through the public `Style.from_theme`,
   `route_ink.style` becomes `drawn_as`.
4. **Docs, goldens, mutation (S9, S10, S11)**, then the final review (S12). The preview card
   (#79) is `specs/008a-theme-preview-card/`, its own PR.

### The regeneration window

From S1 to S10 the defaults have moved but pinned literals that hash the defaults are not
re-pinned (ADR 0006's window): they are re-measured once, in S10. During the window:

- The four non-golden tests that pin group defaults are marked
  `@pytest.mark.xfail(strict=True, reason=WINDOW)` with
  `WINDOW = "regeneration window: re-pinned in 008 S10 (ADR 0069)"`, written in each test
  module, not shared. Strict, so a pin that unexpectedly holds fails. S10 removes every
  mark: `git grep -n "regeneration window" tests` must be empty at the end of S10.
- One default pin is not in the window: `DIGEST` in `tests/unit/maps/test_style.py`.
  S1 leaves it unmoved (measured), and only the `drawn_as` rename moves it, so S8, the
  rename slice, re-pins it to the measured `88b356ada294ff60` in the same commit, with no
  `xfail`.
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
- **Coverage gate** (S2, S3, S4, the merge gate, S7 and S12, in addition to the slice
  gate): CI's own test and coverage steps, copied from `.github/workflows/ci.yml`:

  ```bash
  uv run pytest -m "not golden and not benchmark" --cov --golden-tolerance -n auto --dist loadgroup
  uv run coverage report --include="src/pyntpot/ink/*,src/pyntpot/letters/*" --fail-under=95 --precision=2
  uv run coverage report --include="src/pyntpot/maps/*" --fail-under=92 --precision=2
  ```

  Measured on `f34de97`: 97.32% for `ink` and `letters`, 94.80% for `maps`. These slices
  add most of the new `maps` code; a module whose tests leave it under the bar is a
  missing test, never a lower `--fail-under`.
- **Merge gate** (after the parallel pair S5 ∥ S6 is merged, as its own step, before S7
  starts): merge both worktrees into the branch, run the whole slice gate and the
  coverage gate above on the merged tree, and commit the merge only when it is green. A
  failure here that neither slice shows alone is a defect of the pair: fix it on the
  merged tree in the files of the slice that owns them, and name the fix in the merge
  commit.
- **Golden run** (S10, S12): `uv run pytest -n auto --dist loadgroup --golden-tolerance`
  (about 27 minutes on four cores; exact, without `--golden-tolerance`, only on the pinning
  machine).
- **Strict docs build** (S9, S12), from the repo root:
  `NO_MKDOCS_2_WARNING=1 uv run --locked --group docs mkdocs build --strict -d "$SCRATCH/site"`,
  `$SCRATCH` being your scratchpad.
- **Glossary regeneration** (S9): `PYTHONPATH=tests uv run python -m support.glossary`.
- **Schema regeneration** (S5 on): `PYTHONPATH=tests uv run python -m support.theme_schema`.
- Every test written first: write it, run it, see it fail for the stated reason, then
  make it pass. Every test has a one-line docstring saying what it proves; `parametrize`
  carries `ids=`; no mocking; no `autouse`; no `print`.
- Commit a checkpoint at the end of each slice (free-form message ending with the
  attribution lines in force).

## Line budget (400; split, never thin)

| File | Now | After | Note |
| --- | --- | --- | --- |
| `src/pyntpot/maps/style.py` | 236 | ~310 | +field defaults, `from_yaml`, `from_theme`, `named`, `themes`, `_build`, `_digest_fields`, `_groups`, `_base`; −`from_toml`, `resources` |
| `src/pyntpot/maps/style_groups.py` | 336 | ~345 | three defaults, `Literal`s, docstring; no loader code here |
| `src/pyntpot/ink/style.py` | 266 | ~268 | values only |
| `src/pyntpot/ink/brush_style.py` | 244 | ~244 | values only |
| `src/pyntpot/ink/brush.py` | — | +~25 | `BRUSH_OVERRIDE_KEYS`, `brush_id_known` |
| `src/pyntpot/letters/style.py` | 150 | ~152 | `Literal` for `label_route`, docstring |
| `src/pyntpot/maps/theme_errors.py` | new | ~90 | `ThemeProblem`, `ThemeError` |
| `src/pyntpot/maps/theme_read.py` | new | ~200 | YAML in, plain tree and lines out; YAML features, syntax errors and duplicate keys reported from the event walk |
| `src/pyntpot/maps/theme_merge.py` | new | ~40 | `merge` |
| `src/pyntpot/maps/theme_check.py` | new | ~270 | keys, strict types, renamed keys, dataclass sub-tables, `build_group` |
| `src/pyntpot/maps/theme_vocab.py` | new | ~110 | dict-field vocabularies, brush ids, colours |
| `src/pyntpot/maps/theme_resolve.py` | new | ~180 | names and paths, `extends` chain, cycle |
| `src/pyntpot/maps/theme_schema.py` | new | ~220 | JSON Schema from the model, dataclass sub-tables included |
| `src/pyntpot/maps/cli.py` | 90 | ~105 | `--style VALUE`, `ThemeError` to exit 2 |

If a new module passes 360 lines while you write it, split it along a responsibility
before going on (for example `theme_check.py` into key checks and value checks), and
update this table in the same commit.

## Slices

Order: **S1 → S2 → S3 → S4 → (S5 ∥ S6) → merge gate → S7 → S8 → S9 → S10 → S11 →
S12**. S2, S3 and S4 are the loader in three serial slices with disjoint owned files, each
building on the one before through the interface its "Gives" line states. S5 and S6
own disjoint files and may run in parallel worktrees branched from the S4 checkpoint;
merge both and pass the merge gate before S7. Everything else is serial: S8 runs after
S7 because both pin the named themes' digests (S7 moves four `DIGESTS` rows into
`test_theme_named.py`; S8 re-pins them there and in `test_example_themes.py`).

---

### S1 — One source of defaults (#158; serial)

**Owned files.** `src/pyntpot/ink/style.py`, `src/pyntpot/ink/brush_style.py`,
`src/pyntpot/maps/style_groups.py`, `src/pyntpot/maps/style.py`,
`src/pyntpot/letters/style.py` (docstring only), `src/pyntpot/maps/layers.py` (the
`basemap` docstring's `options` line only), `src/pyntpot/maps/themes/default.toml`
(deleted), `tests/support/flags_off.py` (new), `tests/support/basemaps.py`,
`tests/architecture/test_one_source_of_defaults.py` (new),
`tests/unit/maps/test_style.py`, `tests/unit/maps/test_cli.py`,
`tests/unit/maps/test_cache_margins.py` (step 7), and the tests listed in step 6.

**Leave alone.** `src/pyntpot/maps/candidates/export.py` (`CANDIDATE_BASEMAP` already
sets `landmarks`, `landmark_max` and `generalise` itself: it must not change), every
example script, every docs page, the example themes, `cli.py`.

Steps:

1. **Red: the guard.** Write `tests/architecture/test_one_source_of_defaults.py`. Each
   check is a plain function in that module, over a class or a directory, returning the
   problems it finds as sorted strings (empty when it holds). The real-tree tests call the
   checks on the real model and the real `src/pyntpot/`; the self-tests plant each defect
   and show the check reporting it, as `tests/architecture/test_field_docs.py` does. The
   theme-file check needs the loader, so S4 adds it (step 5 there).

   ```python
   def fields_without_a_default(groups: Mapping[str, type]) -> list[str]: ...
   def required_style_fields(model: type[pydantic.BaseModel]) -> list[str]: ...
   def files_that_restate_the_defaults(package: Path) -> list[str]: ...
   ```

   - `fields_without_a_default`: for each `name, group` and each `dataclasses.fields(group)`
     entry whose `default` and `default_factory` are both `dataclasses.MISSING`,
     `"{name}.{field}"`; a field whose type (from `typing.get_type_hints`) is itself a
     dataclass is walked the same way, as `"{name}.{field}.{inner}"`.
   - `required_style_fields`: the names in `model.model_fields` whose
     `info.is_required()` is true.
   - `files_that_restate_the_defaults`: paths relative to `package`, POSIX form, sorted
     and without repeats, of every `*.toml` file anywhere under it
     (`package.rglob("*.toml")`), every file named `default.*` anywhere under it
     (`package.rglob("default.*")`: the spec bans a `default.*` file under `src/`, not
     only among the themes), and, under `package / "maps" / "themes"` when that directory
     exists, every file that is neither `*.yaml` nor `theme.schema.json`. A missing
     `maps/themes/` is not a problem: after this slice deletes `default.toml`, a fresh
     checkout has no such directory until S5 commits the schema.

   Real-tree tests:
   - `test_every_style_group_field_has_a_default`: `fields_without_a_default({name:
     info.annotation for name, info in Style.model_fields.items()}) == []` and
     `required_style_fields(Style) == []`.
   - `test_the_default_theme_is_the_model_with_nothing_overridden`: `Style() ==
     Style.default()`; from S7 also `== Style.named("default")` (S7 adds that line).
     This is a direct equality: a regression fails it with no planted file.
   - `test_no_package_file_restates_the_defaults`:
     `files_that_restate_the_defaults(REPO_ROOT / "src" / "pyntpot") == []`.

   Self-tests, in a class `TestTheChecksFindAPlantedDefect` (one-line docstrings saying
   what each proves):
   The planted classes are defined at module level in the test module (so
   `typing.get_type_hints` resolves them), private, and used by no other test:
   - `test_a_field_with_no_default_is_found`: `@dataclass(frozen=True, kw_only=True)
     class _NoDefault` with `blooms: bool` and `flow_rim: bool = True` gives
     `fields_without_a_default({"wash": _NoDefault}) == ["wash.blooms"]`; `class _Outer`
     with `inner: _NoDefault = dataclasses.field(default_factory=lambda:
     _NoDefault(blooms=True))` gives `["wash.inner.blooms"]` for `{"wash": _Outer}`.
   - `test_a_required_style_field_is_found`: `class _RequiredStyle(pydantic.BaseModel)`
     with `paper: PaperStyle` and `wash: WashStyle = pydantic.Field(default_factory=WashStyle)`
     gives `["paper"]`.
   - `test_a_default_theme_file_is_found(tmp_path)`: write
     `tmp_path / "maps/themes/default.yaml"`; the check returns
     `["maps/themes/default.yaml"]`.
   - `test_a_toml_file_anywhere_is_found(tmp_path)`: write `tmp_path / "ink/old.toml"`;
     the check returns `["ink/old.toml"]`.
   - `test_a_default_file_outside_the_themes_is_found(tmp_path)`: write
     `tmp_path / "ink/default.json"`; the check returns `["ink/default.json"]`.
   - `test_a_stray_file_among_the_themes_is_found(tmp_path)`: write
     `tmp_path / "maps/themes/notes.txt"`; the check returns `["maps/themes/notes.txt"]`.
   - `test_a_clean_package_has_nothing_to_report(tmp_path)`: with
     `maps/themes/sepia.yaml`, `maps/themes/theme.schema.json` and `maps/style.py`
     written, and again with no `maps/themes/` at all, the check returns `[]`.

   Self-tests and models never write under the repository; only `tmp_path`. Do not spell
   `default.toml` in this module (S9's acceptance grep counts it): plant `default.yaml`
   and `old.toml`.

   Run with the three functions as stubs returning `[]`: the self-tests fail (nothing is
   reported). Write the functions: the self-tests pass and the real-tree tests fail
   (`RouteInkStyle` fields and every `Style` field have no default, so `Style()` cannot
   be built; `files_that_restate_the_defaults` reports `maps/themes/default.toml`).
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
   stays (S6 removes it); its docstring loses "with a table for every group" and its
   `Raises:` loses "a group is missing". Delete `src/pyntpot/maps/themes/default.toml`
   (`git rm`). The directory is now empty: create no placeholder; S5 commits the schema
   there and S7 the named themes.
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
   flags off, (A); if it pins a default, (B) and add it to S10's list in this file; if it
   is neither, stop: it is a behaviour change the plan did not foresee. Tests that call
   `basemap(inputs)` or `basemap(inputs, BasemapStyle(roads=...))` in
   `tests/unit/maps/test_layers.py` passed in the measurement; if one fails, it is (A)
   with `flags_off(BasemapStyle, ...)`.
7. **Callers of `default.toml`.**
   - `tests/unit/maps/test_style.py`: delete `THEME`, `_theme_with` and
     `test_packaged_theme_reads_from_a_path` (the file is gone). Add
     `_write_theme(tmp_path: Path, text: str) -> Path`, docstring "Write a theme file
     holding exactly `text`.", which writes `tmp_path / "theme.toml"` and returns it. Each
     of the six rejection tests in `TestThemeIsStrict` then writes an inline TOML snippet
     naming only the bad key, which loads now that every group has defaults (measured on
     a scratch copy with steps 3 and 4 applied: each raises `pydantic.ValidationError`
     whose text contains the matched word, with one error):

     | Test | Snippet | `match=` |
     | --- | --- | --- |
     | `test_unknown_top_level_key_is_rejected` | `"[weather]\nwind = 3\n"` | `"weather"` |
     | `test_misspelt_wash_key_is_rejected` | `"[wash]\nwet_bleed_pz = 20.0\n"` | `"wet_bleed_pz"` |
     | `test_misspelt_route_ink_key_is_rejected` | `'[route_ink]\nstile = "solid"\n'` | `"stile"` |
     | `test_an_effect_key_in_the_route_ink_is_rejected` | `'[route_ink]\nblend = "normal"\ncasing_px = 0.25\n'` | `"casing_px"` |
     | `test_an_effect_table_in_the_route_ink_is_rejected` | `'[route_ink.effect]\nblend = "normal"\n'` | `"effect"` |
     | `test_the_four_sport_inks_are_rejected` | `"[route_inks.ride]\n"` | `"route_inks"` |

     The other tests keep reading `Style.default()`. S6 rewrites these six as YAML.
   - `tests/unit/maps/test_cli.py:60` and `tests/unit/maps/test_cache_margins.py:172`:
     write the small theme as `"[card]\ndisplay_px = 120\n"` instead of copying the
     default (S6 turns these into YAML).

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

### S2 — The reader: dependency, errors, YAML in (#80; serial)

**Gives S3 and S4** (the interface; nothing else of this slice is used later):
`pyntpot.maps.theme_errors.ThemeProblem` and `ThemeError` (also exported from
`pyntpot.maps`), `pyntpot.maps.theme_read.ThemeFile` and `read_theme(path, text)`, and the
test helper `support.theme_files.theme_file(text, name="t.yaml")`.

**Owned files.** `pyproject.toml` (dependency and import-linter only), `uv.lock`,
`BOUNDARIES.md`, `src/pyntpot/maps/theme_errors.py` and `src/pyntpot/maps/theme_read.py`
(new), `src/pyntpot/maps/__init__.py`, `docs/reference/maps.md` (two directives),
`tests/unit/test_public_api.py`, `tests/unit/maps/test_theme_errors.py` and
`tests/unit/maps/test_theme_read.py` (new), `tests/support/theme_files.py` (new),
`tests/architecture/test_theme_imports.py` (new).

**Leave alone.** `style.py`, `style_groups.py` and every other `src/` file (S3, S4); the
example themes and every caller of `from_toml` (S6); `cli.py` (S6, S7); `maps/themes/`
(S7); the route ink field name (S8).

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
   - Prove the contract bites, in a scratch copy of the tree (not the branch). A scratch
     copy means `git worktree add <dir>` then `uv sync` in it, never `cp -r` (its shebangs
     point at the old venv, so `lint-imports` would check the real tree and report KEPT
     even with `httpx` imported in `ink`). In it, add
     `import ruamel.yaml` to `src/pyntpot/ink/noise.py`, run `uv run lint-imports`, see it
     fail naming the third contract; repeat with `import yaml` in `maps/style.py` and see
     the first fail. Forbid `"ruamel"`, not `"ruamel.yaml"`: import-linter rejects
     subpackages of external packages (measured), so there is no fallback form.
   - `BOUNDARIES.md`: the intro sentence says the second contract keeps `httpx`,
     `pydantic` and `ruamel.yaml` out of `ink` and `letters` (ADRs 0010, 0069); the hard
     rules read "`pyntpot` imports no `matplotlib`, `pandas`, `jinja2` or `yaml`
     (PyYAML)." and "`ink` and `letters` import neither `httpx`, `pydantic` nor
     `ruamel.yaml`; `maps` reads theme files with `ruamel.yaml` (ADR 0069)." Add a third
     rule: "No `maps/theme_*` module but `theme_schema` imports `pyntpot.maps.style` or
     the `pyntpot.maps` package: `style.py` imports the loader, so the loader must not
     import `style.py` (enforced by `tests/architecture/test_theme_imports.py`)."
   - `tests/architecture/`: no test encodes the YAML ban (checked: `git grep -ni yaml
     tests/architecture` is empty); nothing to change there for it.
   - `ty check` with `ruamel.yaml`: if ty reports missing stubs or unknown attributes on
     `ruamel.yaml` objects, confine every `ruamel` touch to `theme_read.py`, type the
     loaded objects as `object` and narrow with `isinstance(..., CommentedMap /
     CommentedSeq)`; do not add a ty ignore rule to `pyproject.toml`.
2. **Red, then green: the import rule**, `tests/architecture/test_theme_imports.py`.
   Why: `style.py` will import `theme_resolve`, which imports `theme_check`, which imports
   `theme_vocab`; a `theme_*` module that imported `pyntpot.maps.style` (or
   `from pyntpot.maps import ...`, which runs the package `__init__` and so `style.py`)
   would close a cycle that fails at import time. The rule holds by construction and this
   test keeps it:

   ```python
   #: The modules a loader module may not import: the style, and the package that imports it.
   FORBIDDEN = frozenset({"pyntpot.maps", "pyntpot.maps.style"})


   def theme_modules_importing_the_style(maps: Path) -> list[str]: ...
   ```

   For each `maps.glob("theme_*.py")`, sorted, except `theme_schema.py`: parse it with
   `ast`, and for each `ast.Import` alias name and each `ast.ImportFrom` module, report
   `"{file name}:{lineno}: {module}"` when the module is in `FORBIDDEN` or the import is
   relative (`level > 0`, spelled as that many dots plus the module). The real-tree test
   `test_no_loader_module_imports_the_style` asserts
   `theme_modules_importing_the_style(REPO_ROOT / "src" / "pyntpot" / "maps") == []`
   (it holds from the first `theme_*` module on, and covers every later one by the glob).
   Self-tests in `TestTheCheckFindsAPlantedImport`, files in `tmp_path`: `theme_a.py`
   holding `from pyntpot.maps.style import Style` gives `["theme_a.py:1:
   pyntpot.maps.style"]`; `from pyntpot.maps import Style` gives `[... pyntpot.maps]`;
   `import pyntpot.maps.style` is found; `from . import style` gives
   `["theme_a.py:1: ."]`; `theme_schema.py` holding `from pyntpot.maps.style import
   Style` and `theme_a.py` holding `from pyntpot.maps.style_groups import CoverStyle`
   give `[]`. (Prototyped on a scratch copy: those outputs, and `[]` on the real tree.)
3. **Red, then green: `theme_errors.py`** (module docstring per CLAUDE.md: purpose, key
   types, what it does not do, invariants):

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
       """A theme that cannot be loaded: every problem found, in file then line order.

       Attributes:
           problems: Every problem found, sorted by file, then line, then key; never empty.
       """

       problems: tuple[ThemeProblem, ...]

       def __init__(
           self, problems: Sequence[ThemeProblem]
       ) -> None: ...  # message: the problems' str, one per line
   ```

   Sorted by `(str(path), line or 0, key)`; `ThemeError` with no problems is a
   `ValueError("a theme error needs a problem")` (programming error). Tests in
   `tests/unit/maps/test_theme_errors.py`: the four `str` forms (line and key, line only,
   key only, neither); problems given out of order come back sorted; the message is one
   line per problem in that order; `ThemeError(())` raises `ValueError` with that message;
   `ThemeError` is a `ValueError`.
4. **Red, then green: `theme_read.py`.** One function and one record:

   ```python
   @dataclass(frozen=True, kw_only=True)
   class ThemeFile:
       """One theme file read into plain data, with where each key sits.

       Attributes:
           path: The file, as the caller named it.
           table: The file's content as plain dicts, tuples and scalars; empty when the
               event walk found a problem.
           lines: The 1-based line of every mapping key, by key path.
           problems: What the walk, the load and the conversion found, in line order.
       """

       path: Path
       table: dict[str, object]
       lines: dict[tuple[str, ...], int]
       problems: tuple[ThemeProblem, ...]


   def read_theme(path: Path, text: str) -> ThemeFile: ...
   ```

   `read_theme` never raises for a bad file: every problem is in `problems`, and S4's
   `resolve` is the one place that reports them (S3's `check_theme` never repeats them).
   ruff's complexity limits (`max-complexity` 10, `max-branches` 10) apply: give the
   event walk one small helper per rule below rather than one long loop body.
   Behaviour, in this order (each a test in `tests/unit/maps/test_theme_read.py`, inputs
   as inline strings, `path=Path("t.yaml")`):
   - **The event walk.** Iterate `YAML(typ="rt").parse(io.StringIO(text))` inside one
     `try`. Keep a stack with one frame per open mapping or sequence; a mapping frame
     holds the key path so far, whether the next event is a key or a value, and the set
     of keys seen. Report, with `event.start_mark.line + 1` and the key path being built:
     - an `AliasEvent`: "aliases are not allowed; use extends". An `AliasEvent` also
       carries `anchor` (the name it refers to; measured), so the anchor rule below skips
       it: one problem per alias, never two;
     - any other event with `anchor` not `None` (`ScalarEvent`, `MappingStartEvent`,
       `SequenceStartEvent`): "anchors are not allowed; use extends";
     - a mapping key `ScalarEvent` whose value is `<<`: "merge keys are not allowed; use
       extends";
     - any event whose `tag` is not `None`: "tags are not allowed";
     - a `DocumentStartEvent` with `version` or `tags` set: "directives are not allowed:
       a theme is YAML 1.2"; a second `DocumentStartEvent`: "one document per theme file";
     - a mapping key that is not a `ScalarEvent` (a `? [a, b]` key): "keys are strings";
     - a mapping key `ScalarEvent` whose value is already in the frame's set: "duplicate
       key", key path including that key, at the duplicate's line. Every duplicate is
       reported, at any depth, not only the first.
     A `ruamel.yaml.error.MarkedYAMLError` raised during the walk (measured: a syntax
     error such as `b: [1, 2` or a tab raises `ParserError` or `ScannerError` from
     `parse()`, not only from `load()`) ends the walk: append its `problem` at
     `problem_mark.line + 1` (line `None` when `problem_mark` is `None`), key the path
     being built when the error came, and keep the problems found before it.
     Measured with `ruamel.yaml` 0.19.1: plain and quoted scalars carry `tag=None`;
     `!!str 5` and `!foo 5` carry the tag; `&x`, `*x` and `<<` show as above; `%YAML 1.1`
     sets `version=(1, 1)` and would read `no` as `False`.
   - **Walk problems come first.** If the walk found any problem, return them with an
     empty table and empty lines: nothing is loaded, so no key or type check runs on that
     file, and S4's `resolve` does not follow its `extends`.
   - **The load.** `YAML(typ="rt").load(text)` inside `try`; a `MarkedYAMLError` (the
     walk has already caught syntax errors and duplicates, so this is a constructor
     error) → its `problem` at `problem_mark.line + 1`, key empty. Catch only
     `MarkedYAMLError`; the problem is returned, not raised, so there is no
     `raise ... from exc`.
   - An empty file is an empty table. A top level that is not a mapping: "a theme is a
     mapping of style groups", line 1.
   - **Convert:** `CommentedMap` → `dict` (a key that loaded as a non-string, such as
     `5:`, is "keys are strings"), `CommentedSeq` → `tuple`, scalars as they are,
     recording `lines[key_path] = node.lc.key(k)[0] + 1` for every key at every depth. A
     `None` value is reported "has no value" at the key's line and its key dropped.
   - Tests pin each bullet, and also: `blooms: no` reads as the string `"no"` (so the
     checker rejects it); `n: 5` is the int 5; a nested key's line is right three levels
     deep (`cover.pigments.wood`); a flow mapping `{jitter_px: 0.4}`'s keys get the flow's
     line; `a: &x 1\nb: *x\n` gives exactly two problems (an anchor on line 1, an alias
     on line 2); `wash:\n  blooms: true\n  blooms: false\ncard:\n  display_px: 1\n  display_px: 2\n`
     gives two "duplicate key" problems, `wash.blooms` line 3 and `card.display_px` line
     6; `wash:\n  blooms: [1, 2\n` gives one problem from the parser with a line and an
     empty table; an alias before a syntax error gives both problems.
5. **Export and the test helper.**
   - Export `ThemeError` and `ThemeProblem` from `pyntpot.maps` (`__init__.py` import from
     `pyntpot.maps.theme_errors`, and `__all__`, sorted). `docs/reference/maps.md` lists
     its directives alphabetically and has no errors section: add
     `::: pyntpot.maps.ThemeError` and `::: pyntpot.maps.ThemeProblem` after
     `::: pyntpot.maps.Style` and before `::: pyntpot.maps.Track`, each followed by a blank
     line as the others are. Add both names to `tests/unit/test_public_api.py`'s pinned
     `MAPS_PUBLIC`, in its order. `tests/architecture` (the field-docs and
     public-signature checks) and `tests/docs` must stay green: `ThemeProblem`'s fields
     have `Attributes:` entries and reach only `pathlib.Path`, `str` and `int`.
   - `tests/support/theme_files.py`, module docstring "Theme files for the loader's tests:
     `theme_file` reads inline YAML as the loader does.":
     `theme_file(text: str, name: str = "t.yaml") -> ThemeFile`, returning
     `read_theme(Path(name), text)`. S3 and S4 read their inputs through it.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_errors.py tests/unit/maps/test_theme_read.py tests/architecture/test_theme_imports.py tests/unit/test_public_api.py tests/architecture tests/docs -q
uv run lint-imports   # every contract kept
uv run ty check       # 0 diagnostics
git grep -n "ruamel" src | grep -v "^src/pyntpot/maps/theme_read.py"   # empty: no output
```

and the slice gate and the coverage gate green.

---

### S3 — The checker: vocabularies, strict values, sub-tables (#80; serial)

**Takes from S2:** `ThemeFile`, `ThemeProblem`, `support.theme_files.theme_file`.
**Gives S4 and S5:** `pyntpot.maps.theme_check.check_theme(theme, groups, *,
renamed=RENAMED_KEYS) -> tuple[dict[str, object], tuple[ThemeProblem, ...]]`,
`build_group(group, table)`, `RENAMED_KEYS`; `pyntpot.maps.theme_vocab`'s vocabularies,
`BRUSH_ID_FIELDS` and `COLOUR_FIELDS`; the planted groups `Glow` and `Ink` in
`support.planted_groups`.

**Owned files.** `src/pyntpot/maps/theme_vocab.py` and `src/pyntpot/maps/theme_check.py`
(new), `src/pyntpot/ink/brush.py`, `src/pyntpot/maps/style_groups.py` (the `Literal`s),
`src/pyntpot/letters/style.py` (the `label_route` `Literal`),
`tests/unit/ink/test_brush.py` (two new tests), `tests/unit/maps/test_theme_vocab.py` and
`tests/unit/maps/test_theme_check.py` (new), `tests/support/planted_groups.py` (new),
`tests/unit/letters/test_nib.py` (the parameter annotation at line 393 only; line numbers in this file may shift by one after S1 adds an import, so find them by content) and
`tests/unit/maps/test_layers.py` (the parameter annotation at line 77 only).

**Leave alone.** `style.py`, `theme_read.py`, `theme_errors.py` (S2's, used as they are);
`theme_merge.py` and `theme_resolve.py` (S4); every caller of `from_toml` (S6).

Steps:

1. **Red, then green: `ink/brush.py`.** `BRUSH_OVERRIDE_KEYS: frozenset[str]`, with an
   attribute docstring, the fifteen keys `_sheet_brush` reads from `over`: `jitter_px`,
   `press_cell_px`, `wobble_px`, `darkness`, `bristles`, `gap`, `dry`, `thr`, `texture`,
   `press`, `load`, `pool`, `bleed`, `lift`, `solid`. `brush_id_known(brush_id: str) ->
   bool`: the existing check of `brush_from_id` (`row in BRUSH_TREATMENTS and col in
   BRUSH_COLOURS.get(cls, {})`), which `brush_from_id` then calls. Tests in
   `tests/unit/ink/test_brush.py`: `test_every_override_key_changes_the_brush` (for each
   key, a `brush_overrides` entry setting it to a distinct value builds a different
   `Brush` than without it; proves the set is what is read, both ways: add a key to the
   set that nothing reads and it fails) and `test_a_brush_id_is_known_only_on_the_sheet`
   (`"MAJ6-e"` and `"TRK4-d"` known; `"MAJ9-e"`, `"XXX1-a"`, `"MAJ6"` not).
2. **Red, then green: `theme_vocab.py`.** It imports `pyntpot.maps.style_groups`,
   `pyntpot.ink.*` and `pyntpot.letters.*` group classes as it needs them, never
   `pyntpot.maps.style` or the `pyntpot.maps` package (S2's import rule).
   - For each dict-valued field, the set of keys a theme may give, computed from the
     group defaults (`CoverStyle()`, `BrushStyle()` and so on), never written out:

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
   - `BRUSH_ID_FIELDS = (("brush", "brushes", "*"), ("route", "route_pen_brush"),
     ("nib", "label_brush"), ("nib", "label_leader_brush"))`.
   - `COLOUR_FIELDS`, a literal tuple of key paths like `BRUSH_ID_FIELDS` (a literal, so
     the module needs no `Style()` and so no import of `style.py`), with an attribute
     docstring:

     ```python
     COLOUR_FIELDS = (
         ("paper", "paper_hex"),
         ("wash", "separation_pigments", "*"),
         ("nib", "label_ink"),
         ("nib", "label_water_ink"),
         ("nib", "label_in_water_ink"),
         ("nib", "label_route_ink"),
         ("cover", "pigments", "*"),
         ("route_ink", "colour"),
     )
     ```

     (measured on a scratch copy with S1 applied: these are exactly the paths whose
     `Style()` value fullmatches `#[0-9a-f]{6}`; no tuple field holds one, and no other
     dict field's values do). Test in `tests/unit/maps/test_theme_vocab.py`,
     `test_the_colour_fields_are_what_the_model_implies`: walk `Style()` (the test may
     import it); for each group field, a `str` value is the path `(group, field)` and a
     `dict` value whose values are all `str` is the path `(group, field, "*")`; the set of
     those paths whose value (every value, for a dict) fullmatches `#[0-9a-f]{6}` equals
     `set(COLOUR_FIELDS)`, and `len(COLOUR_FIELDS) == len(set(COLOUR_FIELDS))`. A new
     colour field fails it until it is added to the literal. Also
     `test_each_vocabulary_is_its_default_s_keys` (each table row above, from the
     defaults).
3. **The `Literal` types.** Eight new ones (`paper.paper_edge` already is one, so nine in
   all, as ADR 0069 lists): `basemap.hillshade_mode`, `sea_style`, `roads`, `rivers`,
   `landmarks`; `route_ink.blend` and (until S8) `style` as `Literal["pen", "solid"]`;
   `face.label_route` (`Literal["centreline", "outline"]`). Values exactly as ADR 0069
   lists; confirm each against its readers (`relief_layers.py:144,191`,
   `osm_elements.py:262-295`, `layers.py` for `landmarks`, `compose_steps.py:109-112`
   for `blend`, `letters/nib.py:160` for `label_route`). Write the `Literal` inline in
   the annotation (no new alias: ADR 0068 would make an alias public). Fix any `ty`
   error in a caller that passes a plain `str` by annotating that caller's value with
   the same `Literal`, never with a cast. Measured on a scratch copy with the eight
   applied (re-measured for this revision, with the two annotations then giving 0
   diagnostics and ruff clean): `uv run ty check` reports exactly two errors, both in
   tests:
   `tests/unit/letters/test_nib.py:396` (the call `FaceStyle(label_route=route)`; annotate
   the test method's parameter at line 393, `route: Literal["centreline", "outline"]`)
   and `tests/unit/maps/test_layers.py:90` (the call `BasemapStyle(roads=roads)`;
   annotate `_road_names`'s parameter at line 77, `roads: Literal["all", "key",
   "major"]`). Add `Literal` to each module's `typing` import (`letters/style.py` and
   `test_nib.py` have none yet: add `from typing import Literal`). Any other error is
   unforeseen: stop.
4. **Red, then green: `theme_check.py`.**

   ```python
   #: Old key paths and what each is called now; a theme that uses one is told the new name.
   RENAMED_KEYS: dict[tuple[str, ...], str] = {}  # S8 adds a row


   def check_theme(
       theme: ThemeFile, groups: Mapping[str, type], *, renamed: Mapping[tuple[str, ...], str] = RENAMED_KEYS
   ) -> tuple[dict[str, object], tuple[ThemeProblem, ...]]: ...
   ```

   `groups` is `{name: info.annotation for name, info in Style.model_fields.items()}`,
   passed by the caller (S4's `style.py`; tests build it the same way): this module
   imports no `Style`. It checks `theme.table` only and returns the problems it finds
   there. It never copies `theme.problems` into its result: S4's `resolve` reports those,
   and calls `check_theme` only on a file whose read found none, so no problem is
   reported twice. Returns the table with every valid leaf converted to its field type
   (ints to floats where the field is a float, through the adapter) and invalid leaves
   dropped, plus every problem:
   - top-level keys: `extends` (must be a `str`: "extends is a theme name or a .yaml
     path") and the group names; anything else unknown.
   - Unknown key at any level (group, dict field entry, `brush_overrides` entry key):
     "unknown key; did you mean {near}?" with `difflib.get_close_matches(key, known, n=1,
     cutoff=0.6)`, else "unknown key". A key in `renamed`: "renamed to {new}" (and no
     suggestion).
   - A group or dict field given a non-mapping: "is a table of keys".
   - Each leaf: `pydantic.TypeAdapter(hint, config=pydantic.ConfigDict(strict=True))`,
     cached per hint with `functools.cache`; a dict field validates each entry with its
     value type, so each entry has its own path and line. Messages from the pydantic
     error `type`: `bool_type` "{v!r} is not a boolean (true or false)"; `float_type`
     "{v!r} is not a number"; `int_type` "{v!r} is not a whole number"; `string_type`
     "{v!r} is not a string"; `tuple_type` "{v!r} is not a list"; `literal_error`
     "{v!r} is not one of {choices}" (`choices = ", ".join(map(repr, choices))` over
     `typing.get_args`, so they read `'pen', 'solid'`);
     a fixed-length tuple of the wrong length "a list of {n} values, not {m}" ({n} from
     `typing.get_args` of the hint, {m} the tuple's length), reported once per leaf: a
     tuple that is too long gives one `too_long` error, and one that is too short gives a
     `missing` error for each absent position, at an integer `loc` (measured, pydantic
     strict: `(1.0,)` for `tuple[float, float]` is `missing` at `(1,)`, never
     `too_short`), so every `missing` error at an integer `loc` and every `too_long` error
     of one leaf collapse into that one message; any other type, pydantic's `msg`.
     Measured: strict mode accepts `5` for a `float` and returns the plain `float` `5.0`
     (also for `ruamel`'s `ScalarFloat`), returns a plain `int` for `ScalarInt` and
     `HexInt`, and rejects `"5"`, `True` for a number, `1` for a `bool`, `5.0` for an
     `int` and a list for a tuple (the reader already made sequences tuples).
   - **Dataclass-typed fields** (no real group has one yet; the parameter `groups` lets
     the tests plant one): a field whose type is a dataclass is checked as a table of that
     dataclass's fields, recursively, with the same rules (unknown keys with a
     suggestion, "is a table of keys" for a non-mapping, strict leaves, lines), and its
     converted entries are a nested `dict`. One code path walks a group and a sub-table:
     `_check_table(group: type, value, key_path)`, called for each group and again for
     each dataclass-typed field. The module docstring states this as a capability ("a
     field typed as a dataclass is a sub-table, checked by the same rules") with no issue
     or roadmap number (`tests/architecture` enforces that rule on docstrings).
   - Brush ids at `BRUSH_ID_FIELDS`: "{v!r} is not a brush on the sheet", by
     `brush_id_known`.
   - Colours at `COLOUR_FIELDS`: "{v!r} is not a # and six hexadecimal digits".
   - Lines from `theme.lines[path]`; the line of the nearest present ancestor otherwise.
   Tests (`tests/unit/maps/test_theme_check.py`, one class per family, inputs from
   `support.theme_files.theme_file`, `groups` built from `Style.model_fields` as above):
   every bullet above, including `wash.blom` suggesting `blooms`, `cover.cover_cfg.wod`
   suggesting `wood`, `brush.brush_overrides.lane.jiter_px` suggesting `jitter_px`,
   `blooms: no` → "'no' is not a boolean (true or false)", `display_px: "900"`,
   `bloom_max: 5.5`, `cover.cover_cfg.wood: [0.1, 0.2, 0.3]`, `basemap.roads: some`,
   `brush.brushes.lane: LAN9-z`, `route_ink.colour: red`; a file with three problems
   reports all three in line order; a renamed key, using a local table passed as
   `renamed={("wash", "bloom"): "blooms"}`, says "renamed to blooms" (the real table is
   empty until S8); the valid leaves of a file with an error are still returned
   converted; `card.dark_grid: [80]` → "a list of 2 values, not 1" (one problem) and
   `card.dark_grid: [80, 60, 40]` → "a list of 2 values, not 3"; `wash.wet_bleed_px: 20`
   returns the `float` `20.0` (`type(...) is float`);
   `test_the_reader_s_problems_are_not_repeated`: a `ThemeFile(path=Path("t.yaml"),
   table={}, lines={}, problems=(one ThemeProblem,))` gives `({}, ())`.
   Sub-table tests, `TestASubTable`, through `groups`: two planted groups in
   `tests/support/planted_groups.py` (module docstring "Planted style groups for the
   loader's and the schema's tests: a group with a dataclass-typed field, which no real
   group has yet."), so S5's schema test reuses them,
   `@dataclass(frozen=True, kw_only=True) class Glow` (`colour: str = "#ffffff"`,
   `px: float = 2.0`) and `class Ink` (`glow: Glow = field(default_factory=Glow)`,
   `px: float = 5.4`), each with a docstring saying it is a planted sub-table for the
   loader's tests and no style group, and an `Attributes:` entry per field;
   `groups = {"route_ink": Ink}`:
   `route_ink:\n  glow:\n    px: 3\n` → table `{"route_ink": {"glow": {"px": 3.0}}}`,
   no problems; `glo:` suggests `glow`; `glow: 5` → "is a table of keys";
   `glow:\n    pxx: 1\n` suggests `px` with key `route_ink.glow.pxx` and its line.

   `build_group(group: type[G], table: Mapping[str, object]) -> G`, also in
   `theme_check.py`: builds `group(**kwargs)` from a full, checked table, building each
   dataclass-typed field from its sub-table with `build_group`, recursively, and passing
   every other value as it is. Test: `build_group(Ink, {"glow": {"colour": "#ffffff",
   "px": 3.0}, "px": 5.4}) == Ink(glow=Glow(px=3.0))`, and for every real group,
   `build_group(G, dataclasses.asdict(G())) == G()`.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_vocab.py tests/unit/maps/test_theme_check.py tests/unit/ink/test_brush.py tests/unit/letters/test_nib.py tests/unit/maps/test_layers.py tests/architecture/test_theme_imports.py -q
uv run ty check       # 0 diagnostics
PYTHONPATH=src uv run python -c "from pyntpot.maps import Style; s=Style(); print(s.digest(), s.base_digest(), s.lettering_digest())"
# 1b08804a7f30026b d9c56c0811177b0f d15ae2f30e9ca5ce   (a Literal annotation moves no value)
```

and the slice gate and the coverage gate green.

---

### S4 — Merge, resolve and `Style.from_yaml` (#80; serial)

**Takes from S2 and S3:** `read_theme`, `ThemeFile`, `ThemeProblem`, `ThemeError`,
`check_theme`, `build_group`, `COLOUR_FIELDS`, `support.theme_files.theme_file`.
**Gives S5 to S8:** `pyntpot.maps.theme_merge.merge`, `pyntpot.maps.theme_resolve`
(`NAME`, `names_in`, `theme_names`, `resolve`), `Style.from_yaml`, `Style._build`, the
theme-file guard `keys_set_to_their_base_value` and `theme_files()`.

**Owned files.** `src/pyntpot/maps/theme_merge.py` and `src/pyntpot/maps/theme_resolve.py`
(new), `src/pyntpot/maps/style.py`, `tests/unit/maps/test_theme_merge.py`,
`tests/property/test_theme_merge.py` and `tests/unit/maps/test_theme_resolve.py` (new),
`tests/support/theme_dump.py` (new), `tests/unit/maps/test_style.py` (`TestFromYaml` and
the digest-rule test), `tests/architecture/test_one_source_of_defaults.py` (the theme-file
check).

**Leave alone.** The S2 and S3 modules and their tests (fix a defect found there in that
slice's files, as "Running the gates" says); `cli.py` (S6, S7); `maps/themes/` (S7); the
example themes (S6).

Steps:

1. **Red, then green: `theme_merge.py`.**
   `merge(base: Mapping[str, object], over: Mapping[str, object]) -> dict[str, object]`:
   a new dict; for each key of `over`, when both values are `Mapping`, the merge of the
   two, else `over`'s value; every other key of `base` kept. Never mutates its inputs.
   Unit tests (`tests/unit/maps/test_theme_merge.py`): a nested key replaces only itself;
   a tuple replaces whole; a dict entry merges per key (`cover.pigments.wood` keeps the
   other fourteen); a table entry deep-merges (`brush.brush_overrides.lane.pool` keeps
   `lane.jitter_px`); inputs unchanged.

   Hypothesis, `tests/property/test_theme_merge.py`. Merge is associative only where a
   key path is a table in every input or a leaf in every input: with `a = {"k": {"x":
   1}}`, `b = {"k": 5}`, `c = {"k": {"y": 2}}` the two sides differ (`{"k": {"y": 2}}`
   against `{"k": {"x": 1, "y": 2}}`). The model fixes that shape: each key path is a
   table (a group, a dict field, a `brush_overrides` entry, a dataclass-typed field) or a
   leaf, and `check_theme` refuses a leaf where a table belongs and a table where a leaf
   belongs, before anything is merged (ADR 0069, "Merge"). So the strategy draws one
   shape and then the inputs as partial fillings of it. The `isinstance` narrowing is
   needed: `shape.items()` gives `object` values, and `ty` refuses an `object` for
   `filling`'s `Mapping` parameter (measured: one diagnostic without it, none with it;
   the property below passes with this strategy):

   ```python
   LEAF = None  # marks a leaf in a shape
   _KEYS = st.sampled_from(("a", "b", "c", "d"))
   _LEAVES = st.one_of(
       st.integers(), st.floats(allow_nan=False), st.text(max_size=3),
       st.tuples(st.integers(), st.integers()),
   )
   shapes = st.dictionaries(
       _KEYS,
       st.recursive(st.just(LEAF), lambda inner: st.dictionaries(_KEYS, inner, min_size=1, max_size=3), max_leaves=8),
       min_size=1, max_size=3,
   )


   @st.composite
   def filling(draw: st.DrawFn, shape: Mapping[str, object]) -> dict[str, object]:
       """Draw a table that names some of `shape`'s keys, a leaf where it has a leaf and a table where it has a table."""
       table: dict[str, object] = {}
       for key, inner in shape.items():
           if not draw(st.booleans()):
               continue
           if inner is LEAF:
               table[key] = draw(_LEAVES)
           elif isinstance(inner, Mapping):
               table[key] = draw(filling(inner))
       return table
   ```

   Tests, each `@given(st.data())` drawing `shape` first and then `a`, `b`, `c` as
   `filling(shape)`: `test_merge_is_associative` (`merge(merge(a, b), c) == merge(a,
   merge(b, c))`); `test_an_empty_override_gives_the_base` (`merge(a, {}) == a`);
   `test_an_override_of_nothing_is_the_override` (`merge({}, a) == a`);
   `test_merge_never_mutates_its_inputs` (`copy.deepcopy` of `a` and `b` before, equal
   after). The counterexample above is pinned as a unit test in `test_theme_merge.py`,
   `test_a_leaf_between_two_tables_is_outside_the_model`, which asserts the two sides
   differ, so the reason for the fixed shape stays visible.
2. **Red, then green: `theme_resolve.py`.**

   ```python
   NAME = re.compile(r"[a-z][a-z0-9-]*")


   def names_in(directory: Traversable) -> tuple[str, ...]: ...  # "default" plus its *.yaml stems, sorted
   def theme_names() -> tuple[str, ...]: ...  # names_in(resources.files("pyntpot.maps") / "themes")
   def resolve(
       theme: str | Path, *, relative_to: Path, groups: Mapping[str, type], base: Mapping[str, object]
   ) -> dict[str, object]: ...
   ```

   It imports `theme_read`, `theme_check`, `theme_merge` and `theme_errors`, and never
   `style.py` (S2's import rule): `groups` and `base` come from the caller. The parameter
   is `theme`, a theme given by its name or its file, and no name or message here says
   "reference": `GLOSSARY.md` gives "reference" to an entry of the references page.
   `base` is the defaults table `style.py` passes (`{name:
   dataclasses.asdict(getattr(Style(), name))}`).

   `names_in(directory)` (`Traversable` from `importlib.resources.abc`): when `directory`
   is not a directory, `("default",)`, which is the packaged state from S1 until S5
   commits the schema (git keeps no empty directory); otherwise `"default"` plus the
   stems of its `*.yaml` files, sorted together. `theme_names()` calls it on the
   package's `themes` directory.

   The rule for `theme`, in this order. The suffix is read the same way for a `str` and a
   `Path`, as `PurePath(theme).suffix`, so `Path("old.toml")` gets the same pointer as
   `"old.toml"`:
   1. suffix `.yaml`: a path, relative to `relative_to` unless absolute;
   2. suffix `.yml`: "theme files end in .yaml; did you mean '{stem}.yaml'?";
   3. suffix `.toml`: "themes are YAML since ADR 0069: see 'Convert a TOML theme' in the
      theme how-to";
   4. a `Path` with any other suffix, or none: "a theme file ends in .yaml" (a `Path` is
      never a name);
   5. a `str` with `NAME.fullmatch(theme)` and in `theme_names()`: that packaged theme
      (`default` is `base` itself, no file). `fullmatch`, not `match`: `"sepia_2"` must not
      pass as `"sepia"`;
   6. a `str` with `NAME.fullmatch(theme)` not in `theme_names()`: "no theme named
      '{theme}'; available: {names}" (names comma-joined);
   7. anything else: "'{theme}' is neither a theme name nor a .yaml path; available:
      {names}".
   Ruff's `max-returns = 5` (PLR0911) forbids one `return` per rule in `resolve`: write one
   small helper per rule (or raise `ThemeError` from the rule), so no function has more
   than 5 returns.
   A refusal in rules 2 to 7 is a `ThemeProblem` with `path` the given value as a `Path`,
   key `""` for the top-level call and `extends` for a chained one, at the `extends`
   line (line `None` for the top-level call). Packaged files are read through
   `resources.as_file`. A missing file: "no such theme file", key `""`, line `None`.

   The chain, and **the one reporter of a file's problems**: for each file, read it
   (`read_theme`) and add its `ThemeFile.problems` to the collected problems. When that
   file's read found none, check it (`check_theme(file, groups)`) and add the problems
   `check_theme` returns (which never include the read's own: S3 step 4); when it found
   some, do not check it and stop the chain there (its `extends` was never loaded).
   Follow the checked table's `extends` (default `"default"`, relative paths from the
   extending file's directory) by the same rule, until `default`. A resolved path seen
   before is "extends cycle: a.yaml -> b.yaml -> a.yaml" on the `extends` key's line.
   If any problem was collected, `raise ThemeError(problems)`. Otherwise fold `merge` from
   `base` through the chain, base first, over the **converted tables `check_theme`
   returned**, never the raw `ThemeFile.table`, so every leaf is the field's own type (a
   raw `5` in a float field would dump as `5`, not `5.0`, and move `digest()`), then drop
   `extends`.

   Tests (`tests/unit/maps/test_theme_resolve.py`, files in `tmp_path`): each rule above,
   including `"old.toml"`, `Path("old.toml")` and `Path("old.yml")` (the TOML ones as
   `test_a_toml_theme_is_refused_with_the_conversion_pointer`), `Path("sepia")` refused
   by rule 4, and `"Sepia"`, `"sepia_2"`, `"2sepia"` refused by rule 7; a three-file chain
   (`c.yaml` extends `b.yaml` extends `a.yaml`) applies in order; a relative
   `extends: ../shared/base.yaml` resolves from the extending file; a two-file cycle and a
   self-cycle; problems in two files of a chain are both reported;
   `test_a_read_problem_is_reported_once`: a file holding `a: &x 1\n` raises `ThemeError`
   with exactly one problem; a missing `extends` means `default`; `extends: default` with
   `card:\n  display_px: 120` gives `card.display_px == 120`, and `wash:\n
   wet_bleed_px: 20` gives the `float` `20.0` in the result;
   `names_in(tmp_path / "absent") == ("default",)`, and for a directory holding `b.yaml`,
   `a.yaml` and `theme.schema.json`, `("a", "b", "default")`. Tests build `groups` and
   `base` from `Style` as `style.py` does.
3. **Green: `Style`.** In `maps/style.py`:
   - Two private module helpers, `_groups() -> dict[str, type]` (`{name: info.annotation
     for name, info in Style.model_fields.items()}`) and `_base() -> dict[str, object]`
     (`{name: dataclasses.asdict(getattr(Style(), name)) for name in Style.model_fields}`),
     each with a one-line docstring; `from_yaml`, S7's `from_theme` and S4's guard use
     them, so every caller builds `groups` and `base` one way.
   - `from_yaml(cls, path: Path) -> Self`: `resolve(Path(path), relative_to=Path.cwd(),
     groups=_groups(), base=_base())` then `cls._build(table)`. Always a path: a `.toml`
     or `.yml` file gets rule 3 or 2 of step 2. Docstring with `Raises: ThemeError: When
     the file or any theme it extends has a problem; every problem is in its problems.`
   - `_build(cls, table) -> Self`: `cls(**{name: build_group(groups[name], table[name])
     for name in groups})`, so a dataclass-typed sub-table is built as its dataclass.
   - **The digest rule and factory defaults.** `DIGEST_OMITS_AT_DEFAULT` compares a field
     with `spec.default`, which is `MISSING` for a field with a `default_factory` (a
     dict, a tuple built by a factory, a sub-table): such a field named in the rule would
     never be omitted. Move the per-group dict into
     `_digest_fields(group: object) -> dict[str, object]` (the group's
     `dataclasses.asdict`, minus each field named in the rule that equals its default,
     where the default is `spec.default` or, when that is `MISSING`,
     `spec.default_factory()`), and have `_group_digest` hash it. The four fields named
     today all have plain defaults, so no digest moves (the acceptance prints the three
     digests). Test in `test_style.py`,
     `test_a_factory_default_counts_for_the_digest_rule`: a test-local dataclass with
     `name_tags: tuple[str, ...] = field(default_factory=lambda: ("name",))` and `px:
     float = 1.0` gives `_digest_fields(...) == {"px": 1.0}` at its defaults and keeps
     `name_tags` when it is `("name:cy", "name")`. Update the rule's attribute docstring
     ("... equals its default, or what its default factory builds ...").
   - Keep `_reject_unknown_group_keys` and `_check_keys`: `model_validate` of a dict stays
     a supported pydantic entry point.
   - Tests in `test_style.py`, `TestFromYaml`: a minimal file loads; a file with an error
     raises `ThemeError` whose `problems[0].line` is right; `Style.from_yaml` on a
     file holding only `extends: default` equals `Style()`; `Style.from_yaml(Path("old.toml"))`
     raises `ThemeError` with the ADR 0069 pointer (the suffix rule on a `Path`).
4. **Green: the property that matters.** In `tests/property/test_theme_merge.py`,
   `test_an_override_and_its_expanded_copy_give_one_digest`: draw a set of leaf paths
   from `Style()`'s table (dict-field entries and `brush_overrides` entry keys included)
   and a factor in `[0.5, 2.0]`, and give each drawn leaf a new value by its default's
   type, checked in this order:
   - `bool` (checked first: `bool` is a subclass of `int`, and a bool is never scaled):
     `not value`;
   - `int`: `round(value * factor)`, an `int`, because strict mode refuses a float for an
     integer field;
   - `float`: `value * factor`;
   - a tuple of numbers: each element by the two rules above;
   - a `str` at a `COLOUR_FIELDS` path: a drawn `#rrggbb` (lower-case hex);
   - anything else (other strings, empty tuples): not drawn; filter the candidate paths
     to the kinds above before drawing.
   Write the drawn leaves as an override YAML and the expanded copy (the whole
   `merge(base, override)`) with `dump_theme`, into a `tempfile.TemporaryDirectory()` per
   example (function-scoped `tmp_path` and Hypothesis do not mix), load both with
   `Style.from_yaml`: equal styles and equal `digest()`.
   `@settings(max_examples=50, deadline=None)`. `tests/support/theme_dump.py` (module
   docstring "Write a plain theme table as YAML text, for the loader's property tests.")
   holds `dump_theme(table: Mapping[str, object]) -> str`: a `ruamel.yaml` dump of the
   plain tree, tuples as lists.
5. **Guard: the theme-file check.** In `tests/architecture/test_one_source_of_defaults.py`
   add

   ```python
   def keys_set_to_their_base_value(theme: Path) -> list[str]: ...
   def theme_files() -> list[Path]: ...  # sorted *.yaml of src/pyntpot/maps/themes and examples/themes
   ```

   `keys_set_to_their_base_value(theme)`: first `resolve(theme, relative_to=theme.parent,
   groups=_groups(), base=_base())`; a `ThemeError` returns `["{file name}: does not
   load: {problem}" for each problem]` (so each problem is reported once, by `resolve`).
   Otherwise read the file with `read_theme` and take its converted table from
   `check_theme` (no problems now), resolve its base table with `resolve` (the file's
   `extends`, relative to the file's directory, or `"default"`), and walk every leaf the
   converted table sets (into groups, dict-field entries, `brush_overrides` entry keys
   and dataclass-typed sub-tables, skipping `extends`), returning
   `"{file name}: {dotted key path}"` for each leaf equal to the base's value at that
   path. The real-tree test, `test_no_theme_file_sets_a_key_to_its_base_value`, loops
   over `theme_files()` (one test, not a parametrize: the list is empty until S6) and
   asserts the joined result is empty, naming each file and key.

   Self-tests (in `TestTheChecksFindAPlantedDefect`, files in `tmp_path`):
   - `test_a_theme_restating_a_default_is_found`: `t.yaml` holding
     `wash:\n  blooms: true\n` gives `["t.yaml: wash.blooms"]`; with `blooms: false`,
     `[]`.
   - `test_a_restated_value_is_found_after_conversion`: `wash:\n  wet_bleed_px: 20\n`
     (an int for the default `20.0`) gives `["t.yaml: wash.wet_bleed_px"]`.
   - `test_a_restated_dict_entry_is_found`: `cover:\n  pigments:\n    wood: "<the
     default wood colour, read from CoverStyle().pigments>"\n` gives
     `["t.yaml: cover.pigments.wood"]`.
   - `test_the_base_is_the_extended_theme`: `base.yaml` holding `wash:\n  blooms:
     false\n` and `child.yaml` holding `extends: base.yaml\nwash:\n  blooms: false\n`
     gives `["child.yaml: wash.blooms"]`; with the child setting `blooms: true` (the
     default, but not the base's value), `[]`.
   - `test_a_theme_that_does_not_load_is_reported`: `wash:\n  blom: true\n` gives one
     entry starting `"t.yaml: does not load:"`.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_merge.py tests/property/test_theme_merge.py tests/unit/maps/test_theme_resolve.py tests/unit/maps/test_style.py tests/architecture -q
uv run ty check       # 0 diagnostics
git grep -n "ruamel" src | grep -v "^src/pyntpot/maps/theme_read.py"   # empty: no output
PYTHONPATH=src uv run python -c "from pyntpot.maps import Style; s=Style(); print(s.digest(), s.base_digest(), s.lettering_digest())"
# 1b08804a7f30026b d9c56c0811177b0f d15ae2f30e9ca5ce
```

and the slice gate and the coverage gate green.

---

### S5 — The schema (parallel with S6)

**Takes from S3 and S4:** `theme_vocab` (the vocabularies and `COLOUR_FIELDS`),
`support.planted_groups` (`Glow`, `Ink`), `Style`. `theme_schema` is the one `theme_*`
module S2's import rule lets import `pyntpot.maps.style`: nothing in `src/` imports
`theme_schema`, so no cycle can form.

**Owned files.** `src/pyntpot/maps/theme_schema.py` (new),
`src/pyntpot/maps/themes/theme.schema.json` (new), `docs/reference/theme.schema.json`
(new), `tests/support/theme_schema.py` (new, the regenerator),
`tests/unit/maps/test_theme_schema.py` (new), `mkdocs.yml` (only if the build excludes
`.json`; it does not by default).

**Leave alone.** Every theme file (S6 adds their directive lines), `style.py`.

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
     `examples/themes/` (empty until S6/S7), walk the file's keys through the schema
     (`properties`, then `additionalProperties` for dict entries) and check enum values;
     a test-local walker, no new dependency. Add `test_the_theme_files_name_a_schema`:
     each file's first line is `# yaml-language-server: $schema=<target>` and `<target>`,
     resolved from the file's directory, is an existing file or is
     `https://findlaywebb.github.io/pyntpot/reference/theme.schema.json`. Both theme-file
     tests loop over the files in one test each (no parametrize: the list is empty in
     this slice's worktree, and the merge gate runs them on S6's ten files).
   - `test_a_sub_table_is_an_object_of_its_fields`: with `Glow` and `Ink` from
     `support.planted_groups` (S3 step 4; `groups={"route_ink": Ink}`), the schema's
     `properties.route_ink.properties.glow` has `"type": "object"`,
     `"additionalProperties": false`, `properties.px` with `"type": "number"` and
     `"default": 2.0`, and its own `"default"` `{"colour": "#ffffff", "px": 2.0}`.
2. **Green.** `theme_schema.py`: `theme_schema(groups: Mapping[str, type] | None = None)
   -> dict[str, object]` (`None` means `Style.model_fields`' groups; the parameter exists
   for the sub-table test), hand-walked over the groups and each group's
   `dataclasses.fields` with
   `typing.get_type_hints`: `bool` → `{"type": "boolean"}`; `int` → `"integer"`;
   `float` → `"number"`; `str` → `"string"` (`"pattern": "^#[0-9a-fA-F]{6}$"` at each
   `theme_vocab.COLOUR_FIELDS` path, a `"*"` meaning every entry of that dict field); `Literal` → `"enum"`; `tuple[X, ...]` → `"array"` with `items`;
   `tuple[X, Y]` → `"array"`, `prefixItems`, `minItems` = `maxItems` = 2;
   `dict[str, V]` → `"object"` with `propertyNames` and `additionalProperties` = V's
   schema; a dataclass → `"object"`, `"additionalProperties": false` and `properties`
   from its own fields by the same walk, recursively (one function, `_object_schema(group:
   type)`, serves a group and a sub-table). Each field: `"default"` (JSON form) and `"description"`: its `Attributes:`
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

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_schema.py tests/architecture/test_theme_imports.py -q
PYTHONPATH=tests uv run python -m support.theme_schema && git status --porcelain   # after the commit: prints nothing
```

and the slice gate green.

---

### S6 — The ten example themes as overrides (#80; parallel with S5)

**Owned files.** `examples/themes/*` (ten `.toml` deleted, ten `.yaml` added),
`examples/map_styles.py`, `examples/place_card.py`, `examples/social_preview.py`,
`examples/how_to_route_ink.py` (the theme loader, docstrings and help text),
`tests/unit/maps/test_example_themes.py`, `tests/support/docs_images.py` (theme paths
and the module docstring's loader sentence), `tests/golden/test_places.py` (theme paths
and the `Style.from_toml` call at line 207), `tests/fixtures/sweep_span_scale.py` (theme
paths and the `Style.from_toml` call at line 79), `src/pyntpot/maps/style.py` (remove
`from_toml` and `tomllib`), `src/pyntpot/maps/cli.py` (line 77 only: `Style.from_yaml`),
`tests/unit/maps/test_style.py` (the TOML tests), `tests/unit/maps/test_cli.py`,
`tests/unit/maps/test_cache_margins.py`, `tests/architecture/test_one_source_of_defaults.py` (the
count check), `tests/architecture/_public_surface.py` (two `ALLOWED` entries),
`tests/docs/test_retired_words.py` (`_SUFFIXES`), and, for the theme path in each
caption and command only (`examples/themes/<name>.toml` → `examples/themes/<name>.yaml`,
nothing else on the page): `docs/gallery.md`, `docs/index.md`,
`docs/tutorials/first-map.md`, `docs/explanation/data-policy.md`,
`docs/how-to/change-the-route-ink.md`, `docs/how-to/letter-your-own-landmarks.md`.

**Leave alone.** `theme_schema.py` and the JSON (S5), `maps/themes/` (S7), every other
docs page and every other line of the six pages above (S9), the notes (S9), the four
named themes' move (S7: in this slice they are converted in `examples/themes/`).

**Docs tests this slice moves**, checked on `f34de97` before assigning (every test under
`tests/docs/` and `tests/architecture/` that names a `.toml` path, `from_toml` or a theme
field this slice changes):

| Test | Why it moves | Fix in this slice |
| --- | --- | --- |
| `tests/docs/test_captions.py::test_every_caption_names_its_figure_and_theme` | a caption must contain the registry entry's `theme` string, which becomes `.yaml` | the six pages' theme paths |
| `tests/architecture/test_public_signatures.py::test_every_allowed_name_is_reached` | `pydantic.ValidationError` and `tomllib.TOMLDecodeError` were reached only through `from_toml`'s `Raises:` (measured: `git grep -n "ValidationError\|TOMLDecodeError" src` names only `style.py:136-137`) | remove both entries, and the `# tomllib` comment above the second, from `ALLOWED` in `_public_surface.py` |
| `tests/docs/test_retired_words.py` | does not fail, but scans `.toml` files under `examples/` and so would stop scanning the themes' comments | `_SUFFIXES = frozenset({".py", ".toml", ".yaml", ".md"})` and the docstring's list says `.yaml` |

Checked and unaffected here: `test_docs_commands.py` (parses options, never opens the
files a command names), `test_docs_links.py` (no `blob/main` link names a theme file;
`tree/main/examples/themes/` stays a directory), `test_docs_imports.py` and
`test_docs_signatures.py` (no page spells `pyntpot.maps.Style.from_toml`; the signature
check reads `__all__` callables, not methods), `test_tutorial_quotes.py` (no quoted
block holds a theme path), `test_reference_pages.py` and `test_reference_values.py`
(`cli.md`'s help text is unchanged until S7; the style-field rows are unchanged until S8).

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
   loading `examples/themes/{name}.toml` with `Style.from_toml`. Run it: green on the S4
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
   # <the TOML file's header comment lines, rewritten as below>
   ```

   The header comments say what the theme is, and stay, with two rewrites: the sentence
   "A copy of default.toml with <list> changed" becomes "It overrides <list>." and a
   following "; every other value is the default" is dropped (an override file says only
   what it changes); `ambleside-hero`'s "a calmer copy of ambleside.toml" becomes "a
   calmer version of ambleside.yaml". Rewrap to 100 columns. After the rewrite,
   `git grep -n "default\.toml\|\.toml" examples/themes` prints nothing.

   No `extends` line (the base is `default`). Hand-check one file against its TOML
   (`ambleside-hero` has the extra `brush.brush_overrides.major.pool`). Delete the TOML
   files with `git rm`.
3. **Switch the loaders and the callers.** Change the pinned-digest test to load
   `{name}.yaml` with `Style.from_yaml`; it must stay green with the same literals.
   Then repoint every `examples/themes/*.toml` path to `.yaml`:
   `tests/support/docs_images.py:168,343-346,375,386,397,495` and its docstring lines
   16-17 (`Style.from_yaml`), `tests/golden/test_places.py:109,129,146,164,182` and the
   loader at line 207 (`Style.from_yaml(REPO_ROOT / place.theme)`),
   `tests/fixtures/sweep_span_scale.py:65-67` and the loader at line 79, the example
   scripts (`place_card.py:108` and `how_to_route_ink.py:120` load with
   `Style.from_yaml(REPO_ROOT / theme)`; S7 moves them to `Style.from_theme`; their and
   `social_preview.py`'s docstrings and `--theme` help say "a .yaml theme file";
   `map_styles.py` reads `Style.from_yaml(THEMES_DIR / f"{figure}.yaml")` and its
   docstring says the themes are override files), and `cli.py:77`
   (`Style.from_yaml(args.style)`; S7 rewrites it). Then the six docs pages: replace each
   `examples/themes/<name>.toml` with `examples/themes/<name>.yaml` and change nothing
   else (`sed -i -E 's#(examples/themes/[a-z-]+)\.toml#\1.yaml#g'` on exactly those six
   files).
4. **Remove `from_toml`.** Delete the method and `import tomllib` from `style.py`, and the
   module docstring's `Style.from_toml` sentence becomes "`Style.from_yaml` reads a theme
   file." Remove the two `ALLOWED` entries. In `test_style.py`, the six TOML rejection
   tests S1 rewrote become YAML snippets through `Style.from_yaml`, asserting `ThemeError`
   with the key path and line (`weather:\n  wind: 3\n` → key `weather`, line 1;
   `wash:\n  wet_bleed_pz: 20.0\n` → `wash.wet_bleed_pz`, line 2; and so on for
   `route_ink.stile`, `route_ink.casing_px`, `route_ink.effect`, `route_inks`);
   `_write_theme` writes `theme.yaml`; S1's `test_a_trimmed_theme_paints_the_default_look`
   reads a YAML file (`wash:\n  flow_rim: true\n`). `test_cli.py` and
   `test_cache_margins.py` write `small.yaml` holding `card:\n  display_px: 120\n`.
   (S4 already wrote `test_a_toml_theme_is_refused_with_the_conversion_pointer`.)
5. **Rewrite `test_example_themes.py`'s framing:** module docstring "The example themes
   in `examples/themes/` are YAML overrides that load and differ from the default and
   each other."; `test_the_directory_holds_exactly_these_themes` pins the ten `.yaml`
   stems; `TestShowcaseThemes` unchanged in substance.
6. **Guard.** Add `test_the_theme_file_checks_see_every_theme` to
   `tests/architecture/test_one_source_of_defaults.py`: `len(theme_files()) == 10` (ten
   now, ten after S7's move: six examples plus four packaged). Run
   `test_no_theme_file_sets_a_key_to_its_base_value` on the converted files: green.

**Acceptance.** Each grep states what it must print.

```bash
uv run pytest tests/unit/maps/test_example_themes.py tests/architecture tests/docs tests/unit/maps/test_style.py tests/unit/maps/test_cli.py tests/unit/maps/test_theme_resolve.py -q
git grep -n "from_toml" src tests examples          # prints nothing
git grep -n "tomllib" src                           # prints nothing (tests and examples keep tomllib for places.toml and pyproject.toml)
git grep -nE "themes/[a-z-]+\.toml" src tests examples   # prints nothing
git grep -nE "examples/themes/[a-z-]+\.toml" -- docs README.md ':!docs/decisions' ':!docs/features' ':!docs/issues'   # prints nothing
git grep -n "\.toml" examples/themes               # prints nothing
wc -l examples/themes/*.yaml   # each under 100
uv run pytest tests/golden/test_map_styles.py tests/golden/test_places.py --golden-tolerance -q   # the theme-dependent goldens: unmoved
```

and the slice gate green.

---

### S7 — Named themes, `from_theme` and the command line (#77; serial, after the merge gate)

**Owned files.** `src/pyntpot/maps/themes/{pen-and-ink,sepia,bold,winter}.yaml` (moved
from `examples/themes/` with `git mv`), `src/pyntpot/maps/style.py` (`named`, `themes`,
`from_theme`), `src/pyntpot/maps/cli.py`, `examples/map_styles.py`,
`examples/place_card.py`, `examples/how_to_route_ink.py` and `examples/social_preview.py`
(the theme loader, docstrings and `--theme` help only),
`tests/unit/maps/test_example_themes.py`, `tests/unit/maps/test_theme_named.py` (new),
`tests/unit/maps/test_cli.py`, `tests/architecture/test_one_source_of_defaults.py` (the
`named` line), and in `docs/reference/cli.md` the synopsis block and the `### --style`
section only.

**Leave alone.** `style_groups.py`, `strands.py`, `compose_steps.py`, `theme_check.py`
(S8); every other docs page and the rest of `cli.md` (S9). Measured: no entry of
`tests/support/docs_images.py` and no golden test names one of the four theme paths
(`map_styles.py` takes them by `figure`), so neither file changes here.

**Docs tests this slice moves** (checked on `f34de97`):
`tests/docs/test_reference_values.py::TestCliSynopsis::test_the_synopsis_is_the_parser_usage`
(the usage line becomes `[--style THEME]`) and
`tests/docs/test_reference_pages.py::TestCli::test_page_names_every_option_and_help_text`
(every parser help string must be on `cli.md`, and `--style`'s help changes). Both are
fixed by this slice's `cli.md` edit.

Steps:

1. **Red.** `tests/unit/maps/test_theme_named.py`:
   `test_the_packaged_themes_are_listed` (`Style.themes() == ("bold", "default",
   "pen-and-ink", "sepia", "winter")`); `test_default_is_the_model` (`Style.named("default")
   == Style()`); `test_each_named_theme_keeps_its_digests` (the four, against their rows
   of S6's `DIGESTS`, moved out of `test_example_themes.py` into this module as its own
   `DIGESTS`, since the files moved; the comment above them says they were measured from
   the TOML files on `f34de97`; S8 re-pins their first elements);
   `test_an_unknown_name_lists_the_names` (`ThemeError` message contains "available:
   bold, default, pen-and-ink, sepia, winter"); `test_a_name_must_be_lower_case_and_hyphenated`
   (`"Sepia"`, `"sepia_2"`, `"2sepia"` refused by rule 7's message);
   `test_a_theme_can_extend_a_named_theme` (a `tmp_path` file `extends: sepia` with one
   override equals `Style.named("sepia")` with that field replaced);
   `test_every_named_theme_paints_the_lynmouth_card` (parametrized over the five names,
   `ids=` the names; each writes `tmp_path / "small.yaml"` holding
   `extends: {name}\ncard:\n  display_px: 120\n`, copies `FIXTURE_DIR` to
   `tmp_path / "cache"` and runs `pyntpot.maps.cli.main` with `--style` that file and
   `--no-attribution`, exactly as `test_cli.py`'s
   `test_a_small_display_style_paints_a_map_quickly` does: exit 0 and a PNG 240 pixels
   wide. The 120-pixel card is what keeps it fast, about 1.5 s a theme, measured on that
   test; a named theme alone paints at its 900 px, about 19 s);
   `test_named_refuses_a_file` (`Style.named("sepia.yaml")` raises `ThemeError` whose
   message contains "Style.named takes a name; use Style.from_yaml for a file");
   `test_each_named_theme_is_package_data` (for each name,
   `resources.files("pyntpot.maps").joinpath("themes", f"{name}.yaml").is_file()`; the
   built wheel is checked by the acceptance command). And `TestFromTheme`:
   `Style.from_theme("sepia") == Style.named("sepia")`; `Style.from_theme("t.yaml",
   relative_to=tmp_path)` loads `tmp_path / "t.yaml"`; `Style.from_theme(tmp_path /
   "t.yaml")` (a `Path`) loads the same; `Style.from_theme("old.toml")` and
   `Style.from_theme(Path("old.toml"))` both raise `ThemeError` with the ADR 0069
   pointer.
2. **Green.** `git mv examples/themes/{pen-and-ink,sepia,bold,winter}.yaml
   src/pyntpot/maps/themes/`; change their first line to
   `# yaml-language-server: $schema=theme.schema.json`. In `style.py`:
   - `from_theme(cls, theme: str | Path, *, relative_to: Path | None = None) -> Self`:
     "A style from a theme given by its name or by its .yaml file." `relative_to` is the
     directory a relative path is read from, the current directory when `None`. It calls
     `theme_resolve.resolve(theme, relative_to=relative_to or Path.cwd(), groups=_groups(),
     base=_base())` and `_build`, so the rule of S4 step 2 applies whole.
     `Raises: ThemeError`. This is the one public entry for "a name
     or a path": the command line, three examples and 008a's `theme_preview.py` call it.
     The name follows `GLOSSARY.md`: a "theme" is a file or a packaged name, and
     "reference" is a different term there, so no `_from_reference`.
   - `named(cls, name: str) -> Self`: a `name` with a suffix (`PurePath(name).suffix`
     not empty) raises `ThemeError((ThemeProblem(path=Path(name), key="", line=None,
     message="Style.named takes a name; use Style.from_yaml for a file"),))`; otherwise
     `from_theme(name)`, so a bad name gets rule 6 or 7. The parameter is typed `str`, so
     the refusal is tested with a `str` (`ty` would refuse a `Path` argument in the test).
   - `themes(cls) -> tuple[str, ...]`: `theme_resolve.theme_names()`.
   - Docstrings name the methods by what they take, with `Args:`, `Returns:`, `Raises:`.
   `examples/map_styles.py` loads `Style.named(figure)` and its docstring says the four
   are packaged themes. `place_card.py`, `how_to_route_ink.py` load with
   `Style.from_theme(theme, relative_to=REPO_ROOT) if theme else Style()`; their and
   `social_preview.py`'s docstrings and `--theme` help say "a theme name or a .yaml file
   relative to the repository's top directory". `test_example_themes.py` pins the six
   remaining stems; S1's guard adds `== Style.named("default")`.
3. **The command line.** `cli.py`: `--style` is `type=str`, `metavar="THEME"`, help
   "a theme name or a .yaml theme file; the default look when absent". `main` loads it
   with `Style.from_theme(args.style)` when given, else `Style()`. Catch `ThemeError`
   only around that call, log `"pyntpot map: %s"` per problem with `log.error`, return 2.
   Update the module docstring synopsis. Tests in `test_cli.py`:
   `test_a_named_style_paints_a_map`, `--style sepia` exits 0 and writes the PNG, marked
   `@pytest.mark.golden` (a name cannot shrink the card, so it paints at 900 px, about
   19 s, which is why `test_a_full_cache_makes_no_request` is golden-marked too);
   `test_a_small_theme_extending_a_name_paints_quickly`, `--style small.yaml` holding
   `extends: sepia\ncard:\n  display_px: 120\n` writes a 240-pixel-wide PNG (not golden);
   S6's `small.yaml` test stays; `--style missing` returns 2 and logs the available names
   (read with `caplog`); `--style old.toml` returns 2 and logs the ADR 0069 pointer.
   `docs/reference/cli.md`: the synopsis line reads `[--style THEME]` (the parser's
   usage, whitespace collapsed); the `### --style` section's "Argument:" says "`THEME`, a
   theme name or a path", "Help text:" is the new help verbatim, and "Description:" says
   "a packaged theme by name (`Style.themes()` lists them) or a `.yaml` theme file, loaded
   with `Style.from_theme`. A theme with a problem prints each problem and exits with
   status 2."

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_theme_named.py tests/unit/maps/test_cli.py tests/unit/maps/test_example_themes.py tests/architecture tests/docs -q
uv build --wheel -o "$SCRATCH/dist" && unzip -l "$SCRATCH"/dist/*.whl | grep -E "maps/themes/(bold|pen-and-ink|sepia|winter)\.yaml|theme\.schema\.json"   # exactly five lines
uv run pyntpot map --help | grep -c -- "^  --style THEME"   # prints 1 (the option row; the usage line also holds "[--style THEME]")
git grep -n "_from_reference" src tests examples      # prints nothing
uv run pytest tests/unit/maps/test_cli.py -m golden -k named --golden-tolerance -q   # the golden-marked --style sepia test: 1 passed
```

and the slice gate and the coverage gate green.

---

### S8 — The route ink's `drawn_as` (#182; serial, after S7)

**Owned files.** `src/pyntpot/maps/style_groups.py`, `src/pyntpot/maps/strands.py`,
`src/pyntpot/maps/compose_steps.py`, `src/pyntpot/maps/style.py` (`with_route_ink`
docstring only), `src/pyntpot/maps/theme_check.py` (`RENAMED_KEYS` row),
`examples/how_to_route_ink.py`, `tests/unit/maps/test_route_ink.py`,
`tests/unit/maps/painter/test_pen_strands.py`, `tests/unit/maps/test_style_groups.py`
(the `RouteInkStyle` rows of `PINNED`, line 245, and of `MAP_GROUPS`, line 386),
`tests/unit/maps/test_style.py` (`ROUTE_INK`, line 53; `DIGEST`, line 56; line 239), `tests/unit/maps/test_theme_check.py`,
`tests/unit/maps/test_example_themes.py` and `tests/unit/maps/test_theme_named.py` (the
`DIGESTS` literals in both), `docs/reference/style-fields.md` (the `route_ink` table's
`style` row only), `src/pyntpot/maps/themes/theme.schema.json` and
`docs/reference/theme.schema.json` (regenerated).

**Leave alone.** `cli.py` (S7), the theme files (none sets `route_ink.style`, measured:
every TOML theme said `"solid"`, which S6's converter dropped as the default), every
other docs page and every other line of `style-fields.md` (S9).

**Docs tests this slice moves** (checked on `f34de97`):
`tests/docs/test_reference_values.py` (the group rows must be the group's fields, with
the model's default and type) and
`tests/docs/test_reference_pages.py::TestStyleFields::test_every_field_of_every_group_is_named`.
Both read `style-fields.md:266`, the `style` row. Rewrite that row as
``| `drawn_as` | string | `"solid"` | How the route is drawn: `"pen"` tints the pen plate when the `route` group painted one; `"solid"` draws a line. Any other value is an error at load. |``
(Type stays `string`: S9 changes the Type column to the YAML vocabulary). No other docs
test names a route ink field: the glossary's "route ink" sentence is prose (S9), and
`change-the-route-ink.md`'s quoted block from `how_to_route_ink.py` does not hold the
renamed line.

Steps:

1. **Red.** `test_theme_check.py`: `test_the_old_route_ink_key_says_it_was_renamed`
   (`route_ink:\n  style: pen\n` → one problem, key `route_ink.style`, message
   "renamed to drawn_as", line 2); `test_drawn_as_takes_pen_or_solid`
   (`drawn_as: pne` → "'pne' is not one of 'pen', 'solid'"). `test_style.py`:
   `ROUTE_INK` uses `drawn_as="solid"`.
2. **Green.** Rename the field (`drawn_as: Literal["pen", "solid"] = "solid"`), its
   `Attributes:` entry ("`pen` tints the painted pen plate when one was painted; `solid`
   draws the line."), the two readers (`strands.py:64`, `compose_steps.py:74`), the
   `with_route_ink` docstring ("when `drawn_as` is `"pen"`"), and every test and example
   use, found with

   ```bash
   git grep -nE "route_ink\.style\b|(^|[^.[:alnum:]_])ink\.style\b|style=\"(pen|solid)\"|style=ink_style|\"style\": \"solid\"|\(\"style\", \"px\"|_inked_as" src tests examples
   ```

   The anchor `(^|[^.[:alnum:]_])` keeps out every `pyntpot.ink.style` import, and the
   unanchored `route_ink\.style` still finds `painted.style.route_ink.style`. Measured on
   `f34de97`, it prints exactly 15 lines (earlier slices may shift their line numbers):
   `examples/how_to_route_ink.py:146`, `compose_steps.py:74`, `strands.py:64`,
   `test_pen_strands.py:23,25,58,73,81,82` (`_inked_as` and its calls: rename its
   parameter `ink_style` to `drawn_as`; the helper keeps its name),
   `test_route_ink.py:113,159`, `test_style.py:53,239`, and `test_style_groups.py:245`
   (`PINNED`'s field names) and `:386` (`MAP_GROUPS`' keywords). Change every one but
   the helper's name and its call sites.
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

   Replace the first element of each `DIGESTS` row with these: the six rows in
   `test_example_themes.py` and the four (`bold`, `pen-and-ink`, `sepia`, `winter`) S7
   moved into `test_theme_named.py`. The `base_digest` and `lettering_digest` elements
   stay. If a value differs, stop and find out why: the
   rename must move nothing else.

   **Re-pin `DIGEST`** in `test_style.py` to `DIGEST = "88b356ada294ff60"`, in this
   commit, with no `xfail` (it is measured, not a golden; S10 does not touch it). Four
   tests compare with it, and all four fail after the rename until it is re-pinned
   (measured on a scratch copy with S1's defaults and the rename, and green with the new
   value): `TestDigests::test_default_digests_are_pinned`,
   `TestDigests::test_a_non_default_name_tags_moves_the_base_and_full_digests`,
   `TestDigests::test_a_default_showcase_field_leaves_every_digest` and
   `TestFedRouteInk::test_equal_fed_values_give_equal_digests`. `BASE_DIGEST` and
   `LETTERING_DIGEST` do not move.
4. Regenerate the schema.

**Acceptance.**

```bash
uv run pytest tests/unit/maps/test_route_ink.py tests/unit/maps/painter/test_pen_strands.py tests/unit/maps/test_theme_check.py tests/unit/maps/test_example_themes.py tests/unit/maps/test_theme_schema.py -q
uv run pytest tests/unit/maps/test_theme_named.py tests/unit/maps/test_style.py tests/docs -q   # no xfail in test_style.py's digest tests
git grep -nE "route_ink\.style\b|(^|[^.[:alnum:]_])ink\.style\b" src tests examples
# prints only lines of tests/unit/maps/test_theme_check.py: the assertion that the
# problem's key is "route_ink.style" (the RENAMED_KEYS row is spelled ("route_ink", "style")
# and does not match, and no docstring names the old key)
git grep -nE "style=\"(pen|solid)\"|style=ink_style|\"style\": \"solid\"|\(\"style\", \"px\"" src tests examples   # prints nothing
```

and the slice gate green.

---

### S9 — Docs (serial)

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
   `--style my-theme.yaml`); "Choose a theme by name" (`Style.themes()`, `Style.named`, `Style.from_theme` for a
   value that may be either,
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
   args); rename its `toml_value` and `toml_type` helpers `yaml_value` and `yaml_type`,
   with `yaml_type` giving `list` where `toml_type` gave `array`. Write the test change
   first and see it fail on the old page.
3. **`cli.md`** (the rest of the page: S7 wrote the synopsis and the `--style`
   section), **`map-from-the-command-line.md`** (its known-message list loses the
   pydantic traceback and gains a `ThemeError` example; `--style my-theme.yaml`),
   **`change-the-route-ink.md`** (`drawn_as`, and "The theme's `route_ink` table"),
   **`first-map.md`** (line 157: "`--style` takes a theme name or a `.yaml` theme"),
   **`index.md`**, **`gallery.md`**, **`data-policy.md`**,
   **`letter-your-own-landmarks.md`**: every TOML theme sentence and `from_toml` becomes
   the YAML form or a name. S6 already changed the `examples/themes/*.toml` paths. The
   check covers the site pages and the README only (the ADRs keep their history and the
   notes are step 5's):

   ```bash
   git grep -n -i "toml" -- 'docs/*.md' README.md ':!docs/decisions' ':!docs/features' ':!docs/issues' | grep -viE "pyproject\.toml|places\.toml"
   ```

   `-i`, because the prose says "TOML" (measured on `f34de97`, case-insensitively and
   besides the theme paths S6 changes: `write-a-theme.md:3,20,21,24,27,30,45,111,114`,
   `cli.md:65,66` (S7 rewrites both), `style-fields.md:3,8,10`, `first-map.md:157`,
   `map-from-the-command-line.md:53`, `glossary.md:80` (regenerated from `GLOSSARY.md:86`
   in step 4) and the three `letter-your-own-landmarks.md` lines below). After this
   slice it prints only these lines: in `docs/how-to/letter-your-own-landmarks.md`, the
   two ```` ```toml ```` fences of the `places.toml` snippets (lines 19 and 56) and the
   sentence saying the landmarks are read with `tomllib` (line 40); in
   `docs/how-to/write-a-theme.md`, lines inside the "Convert a TOML theme" section, its
   heading included; and on any page, a line whose only TOML mention is a link to that
   section (`write-a-theme.md#convert-a-toml-theme`). Any other line is a page still on
   TOML.
   **`docs/architecture.md`**: the style row names the `theme_*` modules and says
   `maps` reads YAML with `ruamel.yaml`.
4. **`GLOSSARY.md`**: "theme" becomes "A YAML file that names a base theme with
   `extends` and gives only the style fields it changes; a theme name such as `sepia`
   chooses a packaged one. The default theme is the model's defaults with nothing
   overridden." (In the code: `pyntpot.maps.Style.named`, `pyntpot.maps.Style.from_yaml`,
   `pyntpot.maps.Style.from_theme`;
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
   by name), `maps-cover-layering-order.md` (a list field replaces wholesale; lines 9 and
   54 stop naming `default.toml` and `from_toml`), `letters-route-means-trace.md` (line
   12 stops naming `default.toml`; add: "A rename adds a row to
   `maps.theme_check.RENAMED_KEYS`."), and `maps-route-ink-leaves-marker-labels-pink.md`
   (line 12: "is `#c22050`, the model default").
6. **File** `docs/issues/maps-numeric-ranges-unchecked.md` (heading "A theme's numeric
   values are not range-checked at load", second line the GitHub issue link) only if
   `display_px: -5` still loads at this point (check). The GitHub issue is the
   orchestrator's (no remote writes from the slice): list it in the commit message as
   "to file".

**Acceptance.** `uv run pytest tests/docs tests/architecture -q`; the strict docs build;
`git grep -nE "default\.toml|from_toml" -- ':!specs' ':!docs/decisions' ':!CHANGELOG.md'`
prints nothing (measured on `f34de97`, its hits are the five deleted notes,
`maps-cover-layering-order.md`, `letters-route-means-trace.md`,
`maps-route-ink-leaves-marker-labels-pink.md`, `write-a-theme.md`, `cli.md` and
`style-fields.md`, which this slice owns, and files S1, S6 and S7 have already changed;
the conversion section's snippet uses `tomllib`, not `from_toml`); the step 3 check
prints only the lines it lists; the slice gate green.

---

### S10 — Golden regeneration (serial)

**Owned files.** `tests/unit/maps/test_style_groups.py` (`SOURCED`, `BASEMAP_DEFAULTS`,
a `RouteInkStyle` row), every module holding a window mark, `docs/images/**`, `tests/golden/docs/**` (the masters), any other golden S1
listed, ADR 0069's "Golden regeneration" section, and only for a fix step 3 names: the
example script of a flagged figure (fix A), the caption or sentence of a flagged figure
(fix B), and a tutorial block that quotes a line fix A changed.

**Leave alone.** `src/`, every theme file, every other example line and docs sentence.

Steps:

1. Process as ADRs 0036 and 0052 on the pinning machine (exact) if available, else under
   `--golden-tolerance` and say so in the ADR. The tolerance bound is not changed.
2. **The pins.** Re-measure and re-pin `SOURCED` (`PaperStyle`, `WashStyle`,
   `BrushStyle`; add `RouteInkStyle`, which now builds) and `BASEMAP_DEFAULTS`. `DIGEST`
   is not here: S8 re-pinned it with the rename. Remove every window mark:
   `git grep -n "regeneration window" tests` empty.
3. **The docs images: a bounded review.**
   1. **Which may move.** Measured on `f34de97` with
      `git grep -lE "PaperStyle\(|WashStyle\(|BrushStyle\(|BasemapStyle\(|vector_layers\(|basemap\(" examples`:
      25 scripts build an ink or basemap group themselves or call the basemap directly,
      and paint 58 of the 71 registered images: `brush_sheet`, `brush_stroke`,
      `composition`, `curves`, `derwentwater`, `fern`, `fern_family`, `glyph_sheet`,
      `how_to_own_shapes`, `how_to_route_ink`, `kaleidoscope`, `lettering`, `nib_line`,
      `nib_stages`, `paper`, `pigment_swatches`, `pigments`, `site_theme`,
      `social_preview`, `svg_drawing`, `trees`, `tutorial_grids`, `wash`, `wash_stages`,
      `word`. The other 13 images (`map_styles`, `place_card`, `route_map`) read a theme
      or `Style()` only and must not move.
   2. **Measure** with the repository's own tooling (CONTRIBUTING.md, "Golden and docs
      images"; flags as `tests/golden/repaint.py --help` states them):

      ```bash
      PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/repaint" --no-lynmouth
      ```

      It paints every registered docs image (no NAME means all) into
      `$SCRATCH/repaint/tree/docs/images/` and its master into
      `$SCRATCH/repaint/tree/tests/golden/docs/`, the repository's own paths, and diffs that
      tree with the working tree into `$SCRATCH/repaint/diffs/` (`summary.md`,
      `summary.json`, and a `.diff.png` and `.crop.png` per moved image). `--no-lynmouth`,
      because the Lynmouth goldens are step 4's and must not move. `OUT` must be absent or
      empty (exit 2 otherwise). It writes nothing into the repository. (Do not use
      `make_docs_images.py OUT --compare docs/images`: it also compares `OUT/masters/`
      with `docs/images/masters/`, which does not exist, so every master is reported
      missing and it exits 1.) The moved set is the `files` of `summary.json`; list each
      with its registry `stem` and changed fraction:

      ```bash
      PYTHONPATH=tests uv run python -c "import json,sys; from support.docs_images import IMAGES, master_path; s={**{f'docs/images/{e.image}': e.stem for e in IMAGES}, **{f'tests/golden/docs/{master_path(e.image)}': e.stem for e in IMAGES}}; [print(f['path'], s.get(f['path'], 'NOT REGISTERED'), f.get('changed_fraction')) for f in json.load(open(sys.argv[1]))['files']]" "$SCRATCH/repaint/diffs/summary.json"
      ```

      (Tried on a scratch copy with S1's defaults, for two images: `tutorials/wash.webp`
      and its master are listed with stem `wash`; `gallery/paper.webp` did not move.) A
      moved image whose stem is not in the list of step 3.1, or `NOT REGISTERED`, is a
      defect: stop and find the slice that caused it. The list of step 3.1 is an upper
      bound: an image of a listed script that does not move needs no review. On a
      non-pinning machine, pixel noise can move other images: a change with
      `changed_fraction`/mean difference at most 0.005 is noise, not a defect, and is
      neither reviewed nor committed.
   3. **Judge each moved image against its text, and nothing more.** For each one, find
      every page that shows it (`git grep -n "<path under docs/images>" docs`) and read
      its caption (the `*Painted by ...*` paragraph) and the paragraph before the image.
      Flag the figure only when the text and the new picture disagree because one of the
      25 fields of S1 step 3 changed:
      - the text says an effect is off, absent or shown on its own ("no blooms", "a flat
        wash", "plain multiply", "without glazing", "the wash body alone"), and the new
        picture shows one of the newly enabled effects; or
      - the text states an old value of one of the 25 fields (`wet_bleed_px` 5,
        `landmark_max` 8, "heuristic" landmarks, and so on).
      A change of colour, texture or edge that the text does not describe is accepted
      unflagged.
   4. **One named fix per flagged figure.**
      - **Fix A, the figure keeps its point**: when the figure isolates one mechanism and
        the newly enabled effect hides it, the script passes that figure the flags-off
        values of exactly the contradicted fields, written as literals in the script
        (examples import no test code; the values are `FLAGS_OFF`'s, for example
        `WashStyle(blooms=False, wet_bleed=False)`), and any tutorial block quoting a
        changed line is updated so `test_tutorial_quotes.py` stays green.
      - **Fix B, the text follows the picture**: otherwise, rewrite the flagged sentence
        or caption to say what the figure now shows; the caption still names its script,
        figure, theme, label lists and name, as `test_captions.py` checks.
   5. **Repaint, commit, recheck.** After the step 4 fixes, repaint into a fresh
      directory and take the moved files into the repository:

      ```bash
      PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/repaint-2" --no-lynmouth
      PYTHONPATH=tests uv run python -c "import json,shutil,sys; from pathlib import Path; out=Path(sys.argv[1]); [shutil.copyfile(out / 'tree' / f['path'], f['path']) for f in json.load(open(out / 'diffs' / 'summary.json'))['files'] if f['status'] == 'changed']" "$SCRATCH/repaint-2"
      ```

      run from the repository root. This copies each moved docs image and master from
      `tree/` to the same path in the repository, as CONTRIBUTING describes, and only
      those: an image whose pixels did not move keeps its committed bytes. (Never run
      `make_docs_images.py docs/images`: it writes the 71 masters into
      `docs/images/masters/`, which breaks `test_docs_images.py`, and leaves
      `tests/golden/docs/` stale.) Then recheck the working tree against the branch base:

      ```bash
      PYTHONPATH=tests uv run python tests/golden/diff_images.py "$SCRATCH/recheck" --ref "$(git merge-base HEAD origin/main)"
      ```

      Its `summary.json` lists the step 2 set, minus any image a fix A put back, plus
      nothing; a repaint into a third empty directory then diffs to `0 images differ`.
   6. **Record.** A table of every moved image: its path, its master's differing
      fraction, flagged or not, and for a flagged one the fix (A with the fields passed,
      or B with the new sentence). It goes in ADR 0069's "Golden regeneration" (step 5)
      and, as the list of all moved images, in the PR description.
4. **The goldens that must not move**: run the full golden suite. The Lynmouth parity
   (and `plates.json`), `GOLDEN_HASH`, `BASE_DIGEST`, `LETTERING_DIGEST`, `SMOKE_SHA`, the
   place pins, the map-styles means and the CLI golden map pass unchanged. A failure among
   these is a defect: stop and fix it in the slice that caused it.
5. **Record**: replace the expected list in ADR 0069's "Golden regeneration" with a
   table: each moved pin (old, new, reason: "default is the default look", "field renamed
   drawn_as", "now buildable"), each moved image with its master's differing fraction and
   reason ("built from `PaperStyle()`: glazing and fibre on", and so on per script), the
   step 3 table with its fixes, and the unmoved list with their values. Publish the
   review images for the PR body (ADR 0052) from the step 3.5 repaint, whose diffs are
   the final images against the branch base:

   ```bash
   PYTHONPATH=tests uv run python tests/golden/publish_diffs.py "$SCRATCH/repaint-2/diffs"           # dry run: writes pr-body.md
   PYTHONPATH=tests uv run python tests/golden/publish_diffs.py "$SCRATCH/repaint-2/diffs" --push    # pushes to pr-assets
   ```

   `--pr-branch` defaults to the branch checked out. The push writes only the orphan
   `pr-assets` branch (never this branch, the index or the working tree); if this slice
   runs where remote writes are not allowed, run the dry run, keep `pr-body.md`, and leave
   the `--push` to the orchestrator before S12's PR. The printed block goes under "Golden
   and docs images" in the PR description, unchanged.

**Acceptance.** `uv run pytest -n auto --dist loadgroup --golden-tolerance -q` green
(`test_docs_images.py` among it: each committed master within the bound of a fresh
paint); `git grep -n "regeneration window" tests` empty; `git status --porcelain
docs/images tests/golden/docs` names only files in the step 3.5 summary and nothing under
`docs/images/masters/`; ADR 0069's section has no "Expected" wording left.

---

### S11 — Mutation testing (serial, local only)

Per `CONTRIBUTING.md` "Mutation testing". The changed `ink` and `letters` functions are
`brush_id_known`, `brush_from_id` (its check now calls it; both S3's) and any function
S1 or S10 touched; the default-value edits are not functions. Run:

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

Kill each survivor with a focused test in `tests/unit/ink` or `tests/unit/letters`, or
name it as equivalent in the PR description with the reason. The `maps/theme_*` modules
are outside mutmut's scope (`only_mutate` is `ink` and `letters`); instead, review their
tests against each branch of the code by reading (every message in S2 step 4, S3 step 4
and S4 step 2 has a test), and record the result in `specs/008-themes-as-data/mutation.md` as 006 did.

---

### S12 — Final review (serial, fresh context)

A fresh-context reviewer reads the spec, ADR 0069 and the diff, ticks each acceptance
criterion against evidence, and writes `specs/008-themes-as-data/review/diff-review.md`.
Then the full gates (golden run, the coverage gate, `prek run --all-files`, strict docs
build), and the PR:
title `feat(maps)!: themes are YAML overrides of one model, chosen by name`, the spec's
Changelog block, `Closes #158`, `Closes #80`, `Closes #77`, `Closes #182`, `Closes #186`,
the list of every moved docs image with its S10 fix (A, B or none),
the golden-diff images, the mutation equivalents, the files filed in S9.

Known and left as is: the prek `docs-tests` hook's file pattern omits `.yaml`, so a
theme-only edit does not trigger it locally; CI runs the docs tests regardless.

## Files to touch

Everything named under a slice's "Owned files", and nothing else. New files:
`src/pyntpot/maps/theme_{errors,read,merge,check,vocab,resolve,schema}.py`,
`src/pyntpot/maps/themes/{bold,pen-and-ink,sepia,winter}.yaml`,
`src/pyntpot/maps/themes/theme.schema.json`, `docs/reference/theme.schema.json`,
`examples/themes/{ambleside,ambleside-hero,oxford,skye,y-fenni,yr-wyddfa}.yaml`,
`tests/support/{flags_off,theme_files,planted_groups,theme_dump,theme_schema}.py`,
`tests/architecture/test_one_source_of_defaults.py`,
`tests/architecture/test_theme_imports.py`,
`tests/unit/maps/test_theme_{errors,read,vocab,merge,check,resolve,schema,named}.py`,
`tests/property/test_theme_merge.py`, `specs/008-themes-as-data/mutation.md`,
`specs/008-themes-as-data/review/*`. Deleted: `src/pyntpot/maps/themes/default.toml`,
`examples/themes/*.toml`, the five notes of S9.

## Files to leave alone

- `examples/places.toml` and every other TOML data file: not themes.
- `src/pyntpot/maps/candidates/export.py`: its basemap options are explicit already.
- `src/pyntpot/maps/cache.py`, `pipeline.py`, `painter/*`: the digests they read do not
  change shape.
- `tests/golden/test_parity.py` and the Lynmouth goldens: nothing they record moves.
- The `DIGEST_OMITS_AT_DEFAULT` tuple: its four fields already default to the default
  look. S4 changes only how the rule reads a field's default (a factory's value counts),
  which moves no digest today.
- `CONSUMER_ONLY`: cover order and pin icons are C2.
- `mkdocs.yml` nav (no new page: the schema is a file, the how-to and reference pages
  exist).
- `.pre-commit-config.yaml`, CI workflows: no new gate.

## Delegation

S1, S2, S3, S4 and S6 carry the design risk: give each to one implementer with this plan
and ADR 0069 only. Each loader slice's "Takes" and "Gives" lines are its whole interface
with the others. S5 ∥ S6 is the one parallel pair: two worktrees branched from the S4
checkpoint, which share no file, then the merge gate on the merged tree before S7. S7
and S8 are serial (both pin the named themes' digests). S9 is docs only and can be a
cheaper model with the pages listed. S10 needs the pinning machine or a long run; S11 is
local. S12 is a fresh reviewer.

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
- **`Style.from_theme` is public.** "A name or a `.yaml` path" has three callers: the
  command line, the examples that take `--theme` (`place_card.py`, `how_to_route_ink.py`,
  `social_preview.py` through `place_card`) and 008a's `theme_preview.py`, which may
  import only public names. The rule of three makes it one public method, not a private
  one copied into scripts. Its name uses the glossary's "theme" (a file, or a packaged
  name); "reference" is another glossary term, so it appears in no name or message.
- **The model fixes the shape a merge sees**, so the associativity property draws inputs
  from one shape (S4 step 1); a table and a leaf at one path never reach `merge`.
- **Sub-tables are built now, not promised.** `check_theme`, `build_group`,
  `theme_schema` and the guard walk dataclass-typed fields, tested on a planted group,
  so #104 to #106 can add a sub-table with no loader or format change. (Issue numbers
  stay in the plan: module docstrings state the capability only.)
- **The loader is three slices** (S2 reader, S3 checker, S4 merge and resolve), serial,
  with disjoint files: S4's `resolve` calls S3's `check_theme`, which reads S2's
  `ThemeFile`, so that is the only order that builds.
- **One reporter of a file's read problems**: `resolve`. `check_theme` reports only what
  it finds in the table, and runs only on a file whose read found nothing.
- **`COLOUR_FIELDS` is a literal**, tested against the model, so `theme_vocab` needs no
  `Style()` and the loader never imports `style.py` (S2's import rule).
- **`DIGEST` moves with the rename and is re-pinned there (S8)**, not in the window: its
  value is measured and only the rename moves it.
- **#186 is folded in**: the style-fields page pointed at `default.toml`, which goes.
- **#79 is `specs/008a-theme-preview-card/`**: a new fixture and an example script, judged
  on its own, after this PR.
