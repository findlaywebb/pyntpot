# 008 mutation run (S11)

Local and advisory (ADR 0012), on the functions this branch changed (plan.md "S11 —
Mutation testing"). mutmut 3.8.0, run from `HEAD` (S10's checkpoint) and re-run on each
survivor once its test was written. The base is `git merge-base HEAD origin/main`,
`f34de97`.

## A tooling defect met first

`uv run mutmut run` fails at its stats pass on this branch and on `main`: `failed to
collect stats. runner returned 1`. With `debug = true` the cause shows:
`mutmut/runners/harness.py:157` reads `item._nodeid`, which pytest 9.2 no longer has
(`AttributeError: 'Function' object has no attribute '_nodeid'`). `f34de97` (#205)
moved `uv.lock` to pytest 9.2.0. Both runs below were therefore made in throwaway
worktrees whose venv had `pytest<9.2` (9.1.1) put in by `uv pip install`, and ran
`uv run --no-sync` so `uv` did not put 9.2 back. No committed file changed for this. The
fix (a pytest pin or a mutmut upgrade) is out of this slice's scope.

## Run list

`ink` and `letters`: the repository's own rule,
`uv run python tests/mutation/scope.py --base f34de97 --out "$patterns"`, under the
committed `[tool.mutmut]`, lists two functions:

- `pyntpot.ink.brush.x_brush_from_id*`
- `pyntpot.ink.brush.x_brush_id_known*`

`maps`: outside the committed `only_mutate` (`ink` and `letters`). Like 006, a
throwaway worktree's `pyproject.toml` alone was edited: `only_mutate` set to
`theme_read.py`, `theme_check.py`, `theme_merge.py`, `theme_resolve.py`,
`theme_schema.py`, `theme_vocab.py` and `style.py` under `src/pyntpot/maps/`;
`also_copy = ["examples/", "docs/reference/"]` (the schema test reads the committed schema
and the example themes); and the test selection set to those modules' tests:
`tests/unit/maps/test_theme_{read,check,merge,resolve,schema,vocab,named,errors}.py`,
`test_style.py`, `test_style_groups.py`, `test_example_themes.py` and
`tests/property/test_theme_merge.py`, `-m "not golden"`. `scope.py` run there gives 69
changed functions, every one of the six modules' functions and these in `style.py`:
`Style.from_yaml`, `from_theme`, `named`, `themes`, `_build`, `default` and
`with_route_ink`, and `_groups`, `_base`, `_table`, `_digest_fields` and
`_group_digest`. `theme_vocab.py` holds module constants and no function, so it has no
mutants. Functions with a decorator other than
one `staticmethod` or `classmethod` (`theme_check._hints`, `_adapter`, both
`functools.cache`, and `Style._reject_unknown_group_keys`) have no mutants in mutmut 3.8.

Nothing was skipped. Wall time: `ink` 1 min 48 s, `maps` 17 min 46 s, the re-runs
under 5 min.

## Scores

Score as ADR 0012 defines it: `(killed + timeout) / tested`. An equivalent mutant still
counts as survived.

| Scope | Tested | Round 1 killed + timeout | Round 1 score | Killed by new tests | Equivalent | Final score |
| --- | --- | --- | --- | --- | --- | --- |
| `ink.brush` (2 functions) | 52 | 49 | 0.9423 | 1 | 2 | 0.9615 |
| `maps` theme loader and `Style` (69 functions) | 1166 | 1101 + 1 | 0.9451 | 32 | 32 | 0.9726 |

No mutant was `no tests`. The one timeout is `theme_resolve.x_resolve` (caught).

## Survivors killed, and their tests

`tests/unit/ink/test_brush.py`:

- `test_without_an_override_key_the_overrides_are_read_by_the_lower_case_prefix`:
  `x_brush_from_id__mutmut_17` (`cls.upper()`).

`tests/unit/maps/test_theme_read.py`:

- `test_the_message_is_the_problem_alone`: `x__located__mutmut_9` (`exc.problem and exc`).
- `test_an_empty_file_keeps_its_path`: `x_read_theme__mutmut_17` (path `None`).
- `test_a_top_level_that_is_not_a_mapping_records_no_lines`: `x_read_theme__mutmut_28`.
- `test_a_key_after_one_with_no_value_is_read`: `x__table__mutmut_17` (`break`).
- `test_no_value_in_a_mapping_inside_a_sequence`: `x__plain__mutmut_13` (`found` `None`).
- `test_unreadable_float` (`._`): `x__number__mutmut_11`, `x__number__mutmut_12`.
- `test_a_date_in_a_sequence_is_at_the_sequence_key`: `xǁ_Walkǁhere__mutmut_5`.
- `test_a_value_after_a_complex_key_is_at_the_mapping`: `xǁ_Walkǁhere__mutmut_11`.
- `test_a_non_specific_tag_is_refused_alone` (`! 2024-01-01`): `x__scalar__mutmut_1`.

`tests/unit/maps/test_theme_check.py`:

- `test_an_entry_after_an_unknown_entry_is_checked`: `xǁ_Checkǁentries__mutmut_20`.
- `test_a_problem_with_no_line_comes_before_line_one`: `xǁ_Checkǁproblems__mutmut_7`,
  `xǁ_Checkǁproblems__mutmut_8`.

`tests/unit/maps/test_theme_schema.py`:

- `test_a_group_that_is_no_dataclass_is_refused`: `x__object_schema__mutmut_3`.
- `test_a_type_with_no_schema_is_refused_at_its_path` (leaf, list, pair):
  `x__leaf_schema__mutmut_18`, `_19`, `_20`, `x__value_schema__mutmut_24`, `_37`.
- `test_a_description_is_read_from_the_attributes_section_alone`:
  `x__attributes__mutmut_13`, `_18`, `_21`, `_22`.

`tests/unit/maps/test_style.py`:

- `test_only_a_group_instance_has_digest_fields`: `x__digest_fields__mutmut_1`, `_4`.
- `test_a_group_entry_that_is_no_mapping_is_refused`: `x__table__mutmut_2`.
- `test_a_relative_path_is_read_from_the_working_directory`:
  `xǁStyleǁfrom_yaml__mutmut_3` (`relative_to=None`).
- `test_a_fed_width_under_one_is_taken`: `xǁStyleǁwith_route_ink__mutmut_13` (`<= 1`).

`tests/unit/maps/test_theme_named.py`:

- `test_named_refuses_a_file_at_the_name_alone`: `xǁStyleǁnamed__mutmut_3`, `_4`, `_11`,
  `_12`.

Each re-run shows every one of these `killed`.

## Equivalent mutants

### `ink.brush`

- `x_brush_id_known__mutmut_6` (`rest.rpartition("-")`): no sheet row or colour holds a
  `-` or is empty, so with no `-` or more than one, both splits give a part the sheet lacks,
  and with exactly one they are the same split.
- `x_brush_from_id__mutmut_9` (`rpartition`): it runs only after `brush_id_known` holds,
  so the id has exactly one `-`, where both splits agree.

### `maps.theme_read`

- `x_read_theme__mutmut_13`, `x__walk__mutmut_2` (`YAML(typ=None)`): ruamel reads a
  `None` typ as `["rt"]`, the round-trip loader it replaces.
- `x__file__mutmut_18`, `x__file__mutmut_20` (sort key `line and 0`, `line or 1`): the walk
  and the conversion each append in document order, so problems already arrive in line order
  and the sort never moves one, and every located problem has a line.
- `x__located__mutmut_2` (`mark` never `None`): every scanner and parser error carries a
  problem mark.
- `xǁ_Walkǁ_step__mutmut_1`, `_3` (`documents = 1`, `+= 2`): only `documents > 0` is read.
- `xǁ_Walkǁ_advance__mutmut_12` (`expect_key = None`): every reader tests its truth, and
  `None` is false as `False` is.
- `x__number__mutmut_2` (`ScalarNode(None, value)`): `construct_yaml_int` and
  `construct_yaml_float` never read the node's tag.

### `maps.theme_check`

- `xǁ_Checkǁproblem__mutmut_1` (`line = ""`): every path has at least one key, so the
  loop always sets `line` before it is read.
- `xǁ_Checkǁunknown__mutmut_13`, `_14`, `_18` (`n` dropped or 2, `cutoff` dropped):
  `get_close_matches` puts the best match first and its default cutoff is 0.6; only
  `near[0]` is read.
- `x__message__mutmut_12`, `_13` (`len(value)` always, `else 1`): pydantic in strict mode
  reports `too_long` or a missing index only for a tuple input, so `value` is always a tuple
  there.
- `x__matches__mutmut_8`, `_11`, `_12` (`strict=None`, dropped, `False`): the lengths are
  tested equal just before, so `zip` never meets unequal ones.

### `maps.theme_resolve`

- `x_resolve__mutmut_36`, `_38` (`extends` defaults to `None`): `default` loads no file,
  so a missing `extends` ends the chain either way.
- `x_resolve__mutmut_41` (`extends` taken whatever its type): `check_theme` keeps
  `extends` only when it is a string.
- `x__read_path__mutmut_2` (always `directory / theme`): `pathlib` joining an absolute
  path keeps the absolute path alone.
- `x__read_path__mutmut_36`, `x__read_name__mutmut_27` (`encoding=None`): the locale's
  encoding, UTF-8 on the machine that ran this; only a non-UTF-8 locale tells them apart.
- `x__read_path__mutmut_38`, `x__read_name__mutmut_29` (`"UTF-8"`): the same codec.
- `x__packaged__mutmut_2` (`resources.files(None)`): with no anchor it takes the calling
  module, whose package directory holds `themes/`; every named-theme test passes.

### `maps.theme_schema`

- `x__object_schema__mutmut_10`, `_39` (`__doc__ or "XXXX"`): `dataclass` gives a class
  with no docstring one, so `__doc__` is never empty and the fallback is never read.

### `maps.style`

- `x__digest_fields__mutmut_11` (`and` to `or`): it differs only for a field with neither a
  default nor a factory, and every style field has a default
  (`tests/architecture/test_one_source_of_defaults.py`).
- `x__group_digest__mutmut_4`, `_7` (`default=str` dropped): every group field is JSON
  data (strings, numbers, bools, tuples, dicts), so `json.dumps` never calls `default`.

## The branch review the plan asked for

S11 asked for the `maps/theme_*` tests to be read against each branch of the code. The
mutation run above does that check mechanically: every message string in `theme_read`,
`theme_check` and `theme_resolve` (S2 step 4, S3 step 4, S4 step 2) has its string
mutants killed, so each message has a test that reads it, and the only survivors left
are the equivalents listed.

## Commands

```bash
scratch=/tmp/claude-0/.../scratchpad
git worktree add --detach "$scratch/mut-ink" HEAD   # and mut-maps, edited as above
uv sync && uv pip install "pytest<9.2"              # in each worktree's venv only
uv run --no-sync python tests/mutation/scope.py --base "$(git merge-base HEAD origin/main)" --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run --no-sync mutmut run --max-children 3
uv run --no-sync mutmut results --all true | grep -v 'not checked'
xargs -a "$survivors" prlimit --as=3500000000 -- uv run --no-sync mutmut run --max-children 3
git worktree remove --force "$scratch/mut-ink"      # and mut-maps
```
