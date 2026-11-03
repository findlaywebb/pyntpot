# 006 — plan

## Approach

ADR 0068 settles every decision. This plan carries it out in serial mechanical slices,
then four parallel lanes, then serial integration. Every pixel stays where it is: the
golden suite, the pinned plate hashes and the docs images are the proof. Function bodies
change in exactly these places, and nowhere else:

- `ink.washing.wash` and `ink.bloom.bloom` read `Flow` and `Blooms` by field name in
  place of tuple positions (same values);
- `maps.painter.job.PaintJob.flow` and `.bloom` build those records in place of tuples
  (same values);
- `maps.projection.track_projection` computes the origin shift before it builds the now
  frozen `Projection`, in place of assigning it afterwards (same arithmetic);
- the named roads path in `maps.lettering` (`picks_roads`, `picks_lines`, `pipeline`),
  taken only when `Annotations.roads` is set.

Two facts shape the order:

- The commit hook runs `tests/architecture` (`.pre-commit-config.yaml`), so a new gate
  cannot be committed red. The two new gates land with a **strict ratchet**: a pending
  set of today's violations, split one file per lane. The test fails on any violation
  not in the set, and on any pending entry that no longer violates, so the set can only
  shrink. Each lane empties its own file; S8 deletes the ratchet. The contract is never
  loosened: the end state is the absolute rule.
- `test_reference_keys.py` resolves every `Implemented in:` dotted path to a file and
  site (`_resolve`), and `test_site.py` checks every directive points into a real module.
  So the module renames must repoint `docs/explanation/references.md` and the reference
  directives in the same slice, path strings only.

The new gates read the code with griffe (`griffelib`, already in `uv.lock` at 2.4.1 via
the `docs` group). It joins the `dev` group. The probe that measured the surface for this
plan resolved `TYPE_CHECKING` imports and quoted annotations correctly, and it showed that
griffe resolves `pyntpot.ink.wash` to the module, not the function: #164 hides
`WashOptions` from any scan until S1 lands.

**Commits.** Every slice ends with one commit (free-form message, CLAUDE.md "Branch
commits are free-form") once its gate is green, so the hook-green ratchet, the lane merges
and `tests/mutation/scope.py` (which diffs `origin/main...HEAD`) all see it. No slice
pushes; the orchestrator pushes and opens the PR.

**Searches.** Every search in a done criterion is `git grep -n -w` over tracked text files
only, never binaries (`tests/golden/` holds 24 binary images whose bytes contain `Pt`):

```bash
git grep -n -w -F -e <word> -- '*.py' '*.md' '*.toml' '*.yml' ':!docs/decisions' ':!specs' ':!CHANGELOG.md'
```

`docs/decisions/` (accepted ADRs are history), `specs/` (earlier specs, and this one,
which names the old names on purpose) and `CHANGELOG.md` are the standing allowed hits and
are excluded by pathspec. Any other hit must be listed as allowed in that slice's done
criterion, with the slice that removes it, or the criterion fails.

The four renamed module paths need one exception to the word form. After S1,
`pyntpot.ink.wash`, `pyntpot.ink.stamp`, `pyntpot.maps.compose` and
`pyntpot.maps.vector_layers` are correct public *function* paths (`::: pyntpot.ink.wash`
is the new directive), so a word search would flag correct text. The **old-module
search** matches only module-style uses: a member after the path, `import`/`as` after it,
or a closing quote or backtick (an import-order string, a prose module name such as
`` `ink.wash` ``):

```bash
git grep -n -E '\b(ink\.(wash|stamp)|maps\.(compose|vector_layers))(\.[A-Za-z_]|\s+(import|as)\b|["`])' \
  -- '*.py' '*.md' '*.toml' '*.yml' ':!docs/decisions' ':!specs' ':!CHANGELOG.md'
git grep -n -w -F -e ink/wash.py -e ink/stamp.py -e maps/compose.py -e maps/vector_layers.py \
  -- '*.py' '*.md' '*.toml' '*.yml' ':!docs/decisions' ':!specs' ':!CHANGELOG.md'
```

On today's tree the two find 59 lines, every one assigned to S1 or S8 or allowed below.

## Line budget (400; split, never thin)

The hard limit is the enforced 400. Measured now, plus the estimated growth when
`#:`/trailing comments become `Attributes:` entries (one entry per field, 8-space indent,
wrapped at 100):

| File | Now | After S0 | After this feature | Action |
| --- | --- | --- | --- | --- |
| `ink/brush.py` | 391 | ~262 | ~305 | split in S0 |
| `ink/brush_sheet.py` (new) | | ~145 | ~145 | |
| `ink/brush_style.py` | 239 | | ~240 | none |
| `ink/style.py` | 247 | | ~275 | none |
| `ink/sheet.py` | 174 | | ~195 | none |
| `ink/washing.py` (was `wash.py`) | 303 | | ~340 (with `Flow`) | none |
| `ink/bloom.py` | 156 | | ~180 (with `Blooms`) | none |
| `letters/style.py` | 128 | | ~140 | none |
| `letters/setting.py` | 113 | | ~125 | none |
| `maps/style_groups.py` | 278 | | ~325 | none |
| `maps/lettering/label.py` | 376 | ~216 | ~260 | split in S0 |
| `maps/lettering/label_sizing.py` (new) | | ~175 | ~175 | |
| `maps/lettering/placement_costs.py` | 397 | | 399 (S2 rename reflows one line) | none; rename only |
| `maps/lettering/span_line.py` | 385 | | ~385 | none; rename only |
| `maps/osm_elements.py` | 387 | | ~387 | none; rename only |
| `maps/lettering/picks_roads.py` | 142 | | ~230 | none |
| `maps/lettering/pipeline.py` | 261 | | ~275 | none |
| `maps/track.py` | 130 | | ~140 | none |

The split rule applies to a file a slice **grows** (docstrings or code) past 380: that
slice splits it along responsibility lines and reports the split. A file already past 380
that a slice only renames in (the three "rename only" rows) is not split; if a rename
would take one past 400, the slice splits it. Never trim text to fit.

## Slices

Serial in the main worktree: S0, S1, S2, S3. Then S4, S5, S6 and S7 in parallel, each in
its own worktree branched from S3's commit. Merge order: S5, S4, S7, S6 (largest last;
each rebases on the previous). Then serial: S8, S9, S10, S11.

The standard gate, unless a slice says otherwise:

```bash
uv run ruff format --check . && uv run ruff check . && uv run ty check && uv run lint-imports \
  && uv run pytest -n auto --dist loadgroup
```

On the pinning machine goldens are exact; elsewhere add `--golden-tolerance`. Slices that
edit `docs/reference/` also run `uv run --group docs mkdocs build --strict`.

### S0 — Mechanical splits (serial)

Pure moves: no logic, no rename, no docstring rewording beyond the module docstrings that
say what each file holds. Verify by diffing each moved block against its original text.

**S0a.** Move `BRUSH_TREATMENTS`, `PEN_ROWS` and `BRUSH_COLOURS`, with their `#:` comments,
from `ink/brush.py` to a new `ink/brush_sheet.py`. Its module docstring: the brush sheet
catalogue (the three tables, their keys), "It builds no brush." No function moves.
`brush.py` imports the three names and its module docstring drops the catalogue sentence
and points at `ink.brush_sheet`.

- Owned: `src/pyntpot/ink/brush.py`, `src/pyntpot/ink/brush_sheet.py`,
  `tests/unit/ink/test_brush.py`, `tests/unit/maps/test_lettering_marks.py`,
  `tests/architecture/test_reference_pages.py` (the import line only).

**S0b.** Move from `maps/lettering/label.py` to a new `maps/lettering/label_sizing.py`:
`_FEWEST_LINES_TO_WRAP`, `_FEWEST_WORDS_TO_SPLIT`, `MeasureTracked`, `KIND_TRACKING`,
`kind_measure`, `NO_WRAP_KINDS`, `MAX_LINES`, `WRAP_LEADING`, `WRAP_MIN_CHARS`,
`WRAP_MIN_SHARE`, `wrap_forms`, `block_size`, `WET_PX_DEFAULT`, `ROAD_PX_DEFAULT`,
`WET_SPREAD`, `feature_px` and `outboard`. `label.py` keeps `Anchor`, `Box`, the
`TIER_*` constants, `NO_LEADER`, `OFF_PAPER_DROPPED_KINDS`, `Measure`, `Label`,
`SPAN_GROUND`, `SPAN_EFFORT` and `Span`, and drops its `Basemap` import (and `math` or
`Callable` if nothing left uses them). `label_sizing.py` imports what the moved code uses:
`Measure`, `Span`, `TIER_LANDMARK` and `TIER_SPAN` from `label`; `Basemap` from
`maps.basemap`; `Pt` from `ink.polyline`; `Callable` from `collections.abc`; and `math`
(checked by AST against today's file; `ruff check` F821/F401 confirms). `label` never
imports `label_sizing`. Both module docstrings are split to match: "the rules that size
and wrap a name" goes to `label_sizing`.

- Owned: `src/pyntpot/maps/lettering/label.py`, `.../label_sizing.py`, and every module and
  test that imports a moved name from `label` (`git grep -n 'from pyntpot.maps.lettering.label import' -- '*.py'`;
  today `notes.py`, `picks_roads.py`, `placement_leaders.py`, `picks.py` and their tests
  among them). Repoint the import only.

- Gate: standard. Done: both splits are pure moves, every file is under 400, the suite is
  green, and `git diff -M` shows no changed line inside a moved function.

### S1 — Module renames and the collision gate (#164; serial)

Test first, in `tests/architecture/test_site.py`:

- `test_no_package_binds_a_name_that_is_one_of_its_submodules`. Read every `__init__.py`
  under `src/pyntpot` by AST. Collect the names bound by `import`, `from ... import`
  (`asname` or name), `def`, `class` and assignment. Collect the package's `*.py` stems
  and its sub-package directories. Assert the intersection is empty, parametrized by
  package with `ids=`. It fails today on `pyntpot.ink` (`stamp`, `wash`) and
  `pyntpot.maps` (`compose`, `vector_layers`).
- In `TestPage`: `test_each_name_directive_is_the_public_path`, asserting every name
  directive is exactly `f"{module}.{name}"`. It fails today on `ink.md` (stamp, wash)
  and `maps.md` (compose, vector_layers).
- `test_site.py`'s module docstring (line 6) still describes deep-path directives:
  rewrite it to say every name directive is `::: pyntpot.<layer>.<name>`.

Then `git mv` the four modules: `ink/stamp.py` to `ink/stamping.py`, `ink/wash.py` to
`ink/washing.py`, `maps/compose.py` to `maps/compose_steps.py`, `maps/vector_layers.py` to
`maps/vector_layer_build.py`. Repoint every importer:

- `pyntpot.ink.stamp`: `ink/__init__.py`, `ink/pad.py` (import and the docstring path on
  line 8), `ink/deposit.py` (docstring line 8), `tests/benchmarks/test_ink.py`,
  `tests/property/test_stamp.py`,
  `tests/unit/ink/{test_deposit,test_keyed,test_nib_reload,test_stamp,test_stamp_drift,test_stamp_pool}.py`,
  `tests/unit/maps/test_import_order.py`.
- `pyntpot.ink.wash`: `ink/__init__.py`, `ink/bloom.py` (docstring line 8, "`ink.wash`"
  becomes "`ink.washing`"), `letters/nib.py`, `maps/painter/{cover,fluid,water}.py`,
  `tests/benchmarks/test_ink.py`, `tests/unit/ink/{test_keyed,test_pigment,test_wash}.py`,
  `tests/unit/maps/painter/test_water.py`, `tests/unit/maps/test_import_order.py`.
- `pyntpot.maps.compose`: `maps/pipeline.py`, `tests/unit/maps/test_route_ink.py`,
  `tests/unit/maps/test_import_order.py`.
- `pyntpot.maps.vector_layers`: `maps/__init__.py`, `tests/unit/maps/test_import_order.py`,
  and the module's own docstring.
- Docs, path strings only: `docs/reference/ink.md` lines 40 and 42 become
  `::: pyntpot.ink.stamp` and `::: pyntpot.ink.wash`; `docs/reference/maps.md` lines 40
  and 48 become `::: pyntpot.maps.compose` and `::: pyntpot.maps.vector_layers`;
  `docs/explanation/references.md` lines 22, 59, 113, 127, 142, 149 and 175 get the new
  module names in their `Implemented in:` paths.

Test file names stay (`test_wash.py` tests `wash`). `tests/mutation/test_shard.py`'s
`"pyntpot.ink.wash"` (lines 18 and 26) is literal test data, not an import: leave it.

- Owned: the files listed above and `tests/architecture/test_site.py`.
- Gate: standard + mkdocs strict. Done: both new tests pass, no `__init__` shadows a
  submodule, `import pyntpot.ink.washing as w; w.WashOptions` works, and the old-module
  search (Approach, "Searches") finds only these allowed hits:
  `tests/mutation/test_shard.py:18,26` (literal data); `GLOSSARY.md:54` (S8's "vector
  layers" row); the notes S8 edits or deletes
  (`docs/features/{ink-public-wash-options,ink-stroke-density-profile,docs-examples-housekeeping,maps-route-casing,maps-route-glow,maps-route-shadow}.md`,
  `docs/issues/maps-public-functions-shadow-modules.md`).

### S2 — Aliases (serial)

Mechanical, no behaviour:

- Rename `Pt` to `Point` in tracked Python files only:
  `git grep -l -w Pt -- '*.py' | xargs sed -i 's/\bPt\b/Point/g'`, then
  `uv run ruff format .` (it reflows `placement_costs.py` line 379; the file ends at 399).
  Never run a replace over `tests/golden/` or any non-`.py` file. Lower-case `pt`
  parameters are untouched. Delete `maps/painter/job.py`'s own `Pt = tuple[float, float]`
  (now `Point = ...`) and import `Point` from `pyntpot.ink.polyline`.
- Define `Box = tuple[float, float, float, float]` once, in `ink/polyline.py` under
  `Point`. Delete the definitions in `maps/lettering/label.py`, `maps/vector_layer_build.py`
  and `maps/card_geometry.py`, and import `Box` from `pyntpot.ink.polyline` in those files
  and at every site `git grep -n -w Box -- '*.py'` shows importing it from one of them
  (10 in `src`, 2 in `tests` today).
- Delete `Anchor` from `maps/lettering/label.py`. `Label.anchor` is annotated `Align`,
  imported from `pyntpot.letters.setting`. Repoint any other `Anchor` user to `Align`, and
  fix `label.py`'s module docstring line 5 ("`Anchor`, `Box` and `Measure`" becomes
  "`Measure`").
- Attribute docstrings (a string literal on the next line) for `Point` ("A point `(x,
  y)`, in the units of whatever holds it."), `Box` ("An axis-aligned box `(x0, y0, x1,
  y1)`, in the units of whatever holds it.") and `Align` ("Which end of a line of text its
  anchor point is: `"start"`, `"middle"` or `"end"`."). The `#:` comments they replace go.

- Owned: every `.py` file the replace touches; `ink/polyline.py`, `letters/setting.py`.
- Gate: standard. Done: the search for `Pt` finds only
  `docs/features/maps-public-signature-types.md:14` (deleted in S8); the search for `Anchor`
  finds nothing; `git grep -n -E '^Box\s*=' -- 'src/*.py'` finds exactly one line
  (`ink/polyline.py`); no file is over 400; the suite is green.

### S3 — The gates, with the ratchet (serial)

- `pyproject.toml`: add `"griffelib>=2.4.1"` to `[dependency-groups] dev`; run `uv lock`.
  Check that `uv.lock` holds one `griffelib` entry at the version the docs group already
  resolves.
- `tests/architecture/_public_surface.py` (a helper module, like `_ast_checks.py`):
  - `load(search_path: Path, package: str) -> griffe.Module`:
    `griffe.load(package, search_paths=[search_path], docstring_parser="google", resolve_aliases=True)`.
  - `public_objects(package, layers) -> dict[str, str]`: each `__all__` name of each layer
    module, resolved through aliases to the defining object, mapped canonical path to the
    exporting layer (`"pyntpot.ink"`). A name is public only when the exporting layer is
    the layer its canonical path lives under (ADR 0068: "exported from the `__all__` of
    the layer package that defines it"); a name exported only from another layer's
    `__all__` is reported as a violation of its own.
  - `names_in(expr) -> set[str]`: the canonical paths of every `ExprName` and of every
    whole `ExprAttribute` chain (not its left parts), through subscripts, unions,
    `Optional[...]`, calls inside `Annotated` and quoted forward references at any depth
    (`list["_Private"]` included). String constants that are not forward references, and
    `None` (griffe keeps it as the plain string `'None'`), are skipped.
  - **What a public object contributes** (ADR 0068, "The rule"):
    - a function or method: its parameter annotations and return annotation (defaults
      excluded); its docstring's `Raises:` entries;
    - a class: its base classes; every public method (not starting with `_`, plus
      `__init__` and `__call__`, the dataclass `__init__` griffe synthesises included);
      every public field, annotated attribute and property (the property's return
      annotation); for a `typing.Protocol`, every member, as above;
    - a module attribute: it is a **type alias**, and contributes its value, exactly when
      it is (a) annotated `TypeAlias`, (b) a PEP 695 `type` statement (a griffe
      `TypeAlias` object, which the walker must not skip), or (c) unannotated with a value
      whose expression is a subscript, a `|` union, or a single name that resolves to a
      class. Every other module attribute (a constant such as `__version__ =
      importlib.metadata.version("pyntpot")`) contributes its annotation only, never its
      value.
  - `reached(module) -> dict[str, set[str]]`: canonical path to the set of `where`
    strings. It walks **transitively**: it starts from every public object, and every
    reached object under `pyntpot.` (public or private) is itself walked by the same
    rules, once. That is the ADR's "32 objects, and those name 8 more", found on the
    first run rather than lane by lane.
  - **Fail closed.** A reached path under `pyntpot.` that does not resolve to a loaded
    griffe object is a violation, never skipped. An alias griffe cannot resolve is the
    same.
  - `ALLOWED: frozenset[str]`: exactly the external (not `pyntpot.`) canonical paths the
    first transitive run on S3's tree reaches, each listed by name, with a one-line comment
    group per source (builtins, `collections.abc`, `typing`, `pathlib`, `json`, `numpy`,
    `httpx`, `pydantic`, `tomllib`). No hand-written guesses: an entry no run reaches is
    not added. Because the walk is transitive, the external names reached do not change
    when a lane exports a private name, so `ALLOWED` is complete from S3 and **no lane
    edits `_public_surface.py`**. No lane in this plan reaches a new external name or
    stops reaching one (S4's `Flow` and `Blooms` reach `float` and `int`, already
    reached); if `test_every_allowed_name_is_reached` or the unknown-name test goes red in
    a lane, the lane stops and reports to the orchestrator.
  - `field_doc_violations(cls) -> list[str]` and `attribute_doc_violations(attr) -> list[str]`
    for the field rule (ADR 0068, "Field documentation"):
    - **Which classes and attributes.** A class or module attribute is checked when it is
      public *or reached* (`public_objects` ∪ the violations of the signature gate). In the
      end state the two sets are equal; counting reached ones from S3 makes the pending
      sets complete on the first run, so exporting a name in a lane never adds an entry.
    - **Fields.** griffe attribute members not starting with `_`, not properties, not
      `ClassVar`, excluding pydantic's `model_config`. Attributes assigned in `__init__`
      count (`Hand.route`, `Hand.font`, `Hand.seed`, `OverpassFeatures.endpoints`,
      `OverpassFeatures.user_agent`, ...).
    - **Field order** is griffe's member order: the class body first, then `__init__`
      assignments, each in source order.
    - **Comments.** Read the class's source lines with `tokenize`. Any `COMMENT` token on a
      line inside the class body but outside every method body is a violation (`#:` and
      trailing comments alike), except pragmas (`# type:`, `# noqa`, `# pragma`).
    - Size: about 340 fields are missing entries today (ink 186, letters 38, maps 115).
- `tests/architecture/test_public_signatures.py`:
  - Self-tests, each writing a tiny package to `tmp_path` and loading it with `load`,
    each with a one-line docstring saying what it proves:
    `test_a_private_class_in_a_union_is_reached`,
    `test_a_private_class_in_an_optional_is_reached`,
    `test_a_private_class_in_a_generic_is_reached`,
    `test_a_quoted_reference_inside_a_generic_is_reached` (`list["_Private"]`),
    `test_a_constant_in_annotated_metadata_is_reached`,
    `test_a_quoted_forward_reference_is_reached`,
    `test_a_type_checking_import_is_resolved_to_its_defining_module`,
    `test_a_reexported_name_counts_as_public`,
    `test_a_name_exported_from_another_layer_is_reported`,
    `test_a_return_annotation_is_reached`,
    `test_a_public_method_signature_is_reached`,
    `test_a_property_return_is_reached`,
    `test_a_private_base_class_is_reached`, `test_a_raises_entry_is_reached`,
    `test_a_dataclass_field_is_reached_through_init`,
    `test_a_protocol_member_is_reached`,
    `test_a_type_alias_value_is_reached` (parametrized with `ids=` over the three alias
    forms: `TypeAlias` annotation, PEP 695 `type`, unannotated subscript),
    `test_a_constant_value_is_not_walked` (`__version__ = importlib.metadata.version(...)`
    reaches nothing),
    `test_a_private_name_reached_through_a_private_one_is_reached` (transitive),
    `test_an_unresolved_package_name_is_reported` (fail closed),
    `test_a_parameter_default_is_not_reached`,
    `test_an_allowed_third_party_name_is_not_reported`.
  - `test_no_public_signature_names_a_private_name`: the violations (reached canonical
    paths that are neither public nor `ALLOWED`) minus the pending set are empty. The
    message lists each violation with its `where`.
  - `test_no_public_signature_names_an_unknown_external_name`: every reached external path
    is in `ALLOWED`.
  - `test_every_pending_signature_entry_still_violates`: the ratchet.
  - `test_every_allowed_name_is_reached`: no stale allowlist entry.
- `tests/architecture/test_field_docs.py`: self-tests on synthetic packages
  (`test_a_missing_entry_is_reported`, `test_an_empty_entry_is_reported`,
  `test_entries_out_of_field_order_are_reported`, `test_a_stale_entry_is_reported`,
  `test_a_property_needs_no_entry`, `test_an_init_attribute_needs_an_entry`,
  `test_a_hash_colon_comment_in_a_public_class_is_reported`,
  `test_a_trailing_comment_in_a_public_class_is_reported`,
  `test_a_comment_inside_a_method_is_allowed`,
  `test_a_module_constant_without_a_docstring_is_reported`). Then
  `test_every_public_field_and_attribute_is_documented` (violations minus pending is
  empty) and `test_every_pending_field_docs_entry_still_violates`.
- The pending sets live in four files. Each defines `SIGNATURES: frozenset[str]`
  (private canonical paths) and `FIELD_DOCS: frozenset[str]` (checked object canonical
  paths), filled from the first run by these rules:
  - `tests/architecture/_pending_ink.py`: paths under `pyntpot.ink.`;
  - `tests/architecture/_pending_letters.py`: paths under `pyntpot.letters.` and the
    top-level `pyntpot.__version__`;
  - `tests/architecture/_pending_roads.py`: paths under `pyntpot.maps.lettering.pipeline.`
    (it may start empty; it exists so S7 never edits another lane's file);
  - `tests/architecture/_pending_maps.py`: every other path under `pyntpot.maps.`.
  The module-scoped fixture loading `pyntpot` once is allowed (an immutable parsed
  object).

- Owned (nine files): `pyproject.toml`, `uv.lock`, `tests/architecture/_public_surface.py`,
  `tests/architecture/test_public_signatures.py`, `tests/architecture/test_field_docs.py`
  and the four `tests/architecture/_pending_*.py`.
- Gate: `uv run pytest tests/architecture` + `uv run ruff check tests` + `uv run ty check`.
  Done: every self-test passes, the real tests pass with the pending sets, `ALLOWED`
  equals the external set reached, and the pending sets name nothing that does not
  violate.

### S4 — Lane: ink (#73, #168, #169; parallel)

Decisions:

- `Flow` becomes `@dataclass(frozen=True, kw_only=True) class Flow` in `ink/washing.py`
  with fields `exp: float`, `ref_frac: float`, `frac: float` (the suffixes of
  `WashStyle.flow_rim_exp`, `flow_rim_ref_frac`, `flow_rim_frac` and the names of
  `flow_edge`'s parameters; ADR 0068). `wash` calls
  `flow_edge(a, sheet, o.rim_px, o.flow.exp, o.flow.ref_frac, o.flow.frac)`.
- `Blooms` becomes `@dataclass(frozen=True, kw_only=True) class Blooms` in `ink/bloom.py`
  with fields `seed: int`, `count: int`, `radius_frac: float`, `lift: float`,
  `warp: float`. `bloom` reads the fields by name in place of the tuple unpack. Its
  `Args:` text for `blooms` points at `Blooms`' `Attributes:`. The name stays `Blooms`
  (ADR 0068, "Naming convention").
- No validation (`__post_init__`) is added to `Flow`, `Blooms` or any group: they gain
  `frozen`/`kw_only` and nothing else. `separated` and `fluid_modulate` are exported
  unchanged: their bodies are not edited.
- `maps/painter/job.py`: `PaintJob.flow` returns `Flow(exp=..., ref_frac=..., frac=...)`
  and `PaintJob.bloom` returns `Blooms(seed=..., count=..., ...)`, each with the values
  it returns today. Their annotations name `Flow` and `Blooms`.
- `WashOptions`, `WashStyle`, `PaperStyle` and `BrushStyle` become
  `@dataclass(frozen=True, kw_only=True)` (`WashOptions` keeps `eq=False`).
- `pyntpot.ink.__all__` adds `WashOptions`, `Flow`, `Blooms`, `WashStyle`, `separated`,
  `fluid_modulate`, `Point` and `Box`. No top-level change.
- `ink/__init__.py`'s module docstring (BOUNDARIES.md: kept current) names the new
  exports in its existing groups: `Point` and `Box` with the geometry; `WashOptions`,
  `Flow`, `Blooms`, `separated` and `fluid_modulate` in the sentence on `wash`;
  `WashStyle` with `PaperStyle` and `BrushStyle`.
- Field docs (ADR 0068): `Brush`, `BrushStyle`, `PaperStyle`, `WashStyle`, `Sheet`,
  `Canvas`, `WashOptions`, `Flow`, `Blooms` get `Attributes:` sections, every `#:` and
  trailing field comment moved into them and deleted, shared blocks split. Fields with no
  comment today (`Brush.pool_radius_frac`, `pool_gain`, `dir_elong`, `dir_mix`,
  `pen_thin`, `org_oct`, `org_lac`, `Canvas.x0` to `h`, and the rest the test reports)
  get text written from what the code does with them. `PIGMENTS`, `TRANSPARENCY`,
  `PAINTERS_PIGMENTS`, `PAINTERS_TRANSPARENCY` and `PigmentLayer` get attribute docstrings
  in place of their `#:` comments.
- `docs/reference/ink.md`: one directive per new name, in the page's order (constants,
  then classes and aliases alphabetically, then functions alphabetically).

Test first:

- `tests/unit/ink/test_wash.py::test_flow_and_blooms_take_only_keywords`: `Flow(0.125,
  0.02, 0.38)` and `Blooms(3, 6, 0.17, 0.45, 0.45)` raise `TypeError`; the keyword forms
  build.
- `tests/unit/ink/test_style_groups_keyword_only.py::test_an_ink_style_group_takes_only_keywords`,
  parametrized over `PaperStyle`, `WashStyle`, `BrushStyle`, `WashOptions` with `ids=`: a
  positional argument raises `TypeError`.
- `tests/unit/test_public_api.py`: `INK_PUBLIC` gains the eight names (red until exported).
- Every tuple use becomes keyword `Flow(...)`/`Blooms(...)` with the same numbers:
  `tests/unit/ink/test_wash.py` lines 30, 110, 121; `tests/unit/ink/test_bloom.py`: the
  `PINNED` table's bloom tuples (read at line 45), and lines 52, 55 (the `Blooms` annotation stays), 68,
  80; `tests/unit/ink/test_keyed.py` lines 132-133 and 153-157 (the `lay` helper's
  annotation becomes `Blooms | None`); `tests/benchmarks/test_ink.py` line 131. Their
  pinned values do not change: that is the proof that no pixel moves.
- `tests/unit/maps/painter/test_job.py` lines 51 and 62-63 read `big.count`,
  `wood.seed`, `again.seed`, `lake.seed` in place of `[1]` and `[0]`.

Empty `_pending_ink.py` of every entry as it goes green (the ratchet fails until you do).

- Owned: `src/pyntpot/ink/{__init__,washing,bloom,style,brush,brush_style,sheet,pigment}.py`
  and any other `ink` module `test_field_docs.py` reports for a checked class;
  `src/pyntpot/maps/painter/job.py`; `tests/unit/ink/**`; `tests/benchmarks/test_ink.py`;
  `tests/unit/maps/painter/test_job.py`; `tests/architecture/_pending_ink.py`;
  `tests/unit/test_public_api.py` (the `INK_PUBLIC` tuple only); `docs/reference/ink.md`.
  Not `tests/unit/maps/painter/test_water.py`: it already builds `WashOptions` by keyword
  and needs no change after S1.
- Gate: standard + mkdocs strict. Done: `_pending_ink.py` is empty, the goldens pass
  unchanged, and every file is under 400.

### S5 — Lane: letters (#168, #169; parallel)

Decisions:

- `FaceStyle`, `HandStyle` and `NibStyle` become `@dataclass(frozen=True, kw_only=True)`.
  `NibGroups` does not change: positional construction stays, because five examples and
  the tutorials quoting them use it.
- `pyntpot.letters.__all__` adds `Align`. `letters/__init__.py`'s module docstring names
  `Align` beside `Setting` ("`Setting`, one setting of text, and `Align`, which end of
  the line its anchor point is").
- Field docs: `FaceStyle`, `HandStyle`, `NibStyle`, `Setting`, `Mark`, `Hand` (its
  `__init__` attributes), and any other checked `letters` class the test reports, get
  `Attributes:` sections. `#:` and trailing comments go.
- `pyntpot.__version__` gets an attribute docstring in `src/pyntpot/__init__.py`.
- `docs/reference/letters.md`: a directive for `Align`, in alphabetical order.

Test first:

- `tests/unit/letters/test_style.py::test_a_letters_style_group_takes_only_keywords`,
  parametrized over the three groups with `ids=`.
- `tests/unit/test_public_api.py`: `LETTERS_PUBLIC` gains `Align`.
- `tests/unit/letters/test_nib.py` lines 227 and 330: `HandStyle(label_seed=...)` (the
  only positional style-group constructions in the tree, by AST scan).

- Owned: `src/pyntpot/letters/{__init__,style,setting,hand,nib}.py`,
  `src/pyntpot/__init__.py`, `tests/unit/letters/**`,
  `tests/architecture/_pending_letters.py`, `tests/unit/test_public_api.py` (the
  `LETTERS_PUBLIC` tuple only), `docs/reference/letters.md`.
- Gate: standard + mkdocs strict. Done: `_pending_letters.py` is empty.

### S6 — Lane: maps (#168, #78, #169; parallel)

Decisions:

- Rename `LetteringPolicy` to `LetteringStyle` and `RouteInk` to `RouteInkStyle` in
  `maps/style_groups.py`, `maps/style.py`, `maps/compose_steps.py` and every test that
  names them. The `Style` field names (`lettering`, `route_ink`) do not change. Every map
  style group becomes `@dataclass(frozen=True, kw_only=True)`.
- **Newly public records are frozen and keyword-only** (ADR 0068, "Records the pipeline
  returns"): `Card`, `Credit`, `Manifest`, `DarkGrid`, `Layers`, `River`, `Road`,
  `ElevationPatch`, `ElevationGrid`, `VectorArea`, `VectorLine`, `HillshadeBand`,
  `HillshadeImage` and `Projection` become `@dataclass(frozen=True, kw_only=True)` (each
  already frozen except `Projection`). `Label` and `Span` become
  `@dataclass(kw_only=True)` and stay mutable. `BoundingBox` stays a `NamedTuple`. The
  positional construction sites, all of them by AST scan, become keyword:
  `src/pyntpot/maps/providers/opentopodata.py:59` and `overpass.py:193` (`Credit`);
  `tests/support/providers.py:17,24` (`Credit`); `tests/property/test_projection.py:34`
  (`Projection`); `tests/unit/maps/lettering/test_picks.py:33,34,37` (`Road`, `River`);
  `tests/unit/maps/painter/test_smoke.py:86-88,93-94`; `tests/unit/maps/test_basemap.py:79,84`;
  `tests/unit/maps/test_lettering_furniture.py:46,181` (`Label`). Every `Label(` and
  `Span(` in `src` is already by keyword, so S7's files need no edit for this.
- `maps/projection.py` `track_projection`: compute `x0` and `y0` first (the same two
  branches, the same expressions as lines 84-88 today), then build
  `Projection(lat0=..., lat_ref=..., lng_ref=..., x0=..., y0=...)` once. Nothing else
  assigns a `Projection` field (`git grep -n -E '\.(x0|y0|lat0|lat_ref|lng_ref|ky)\s*=' -- '*.py'`
  finds only those four lines).
- `pyntpot.maps.__all__` adds the 31 names: `BasemapStyle`, `BoundingBox`, `Card`,
  `CardStyle`, `CoverStyle`, `Credit`, `DarkGrid`, `Elevation`, `ElevationGrid`,
  `ElevationPatch`, `Features`, `HillshadeBand`, `HillshadeImage`, `Label`, `Landmark`,
  `Layers`, `LetteringStyle`, `Line`, `MAX_NOTES`, `MAX_NOTE_CHARS`, `Manifest`,
  `Projection`, `RibbonStyle`, `River`, `Road`, `RouteInkStyle`, `RouteStyle`, `Span`,
  `SpanRequest`, `VectorArea`, `VectorLine`, in the order `ruff check --fix` (RUF022)
  gives, which puts the two constants first.
- `maps/__init__.py`'s module docstring loses "The provider protocols ... are reached
  through their own modules, not exported here" and gains one sentence per new group: the
  seven style groups beside `Style`; `Features`, `Elevation` and `ElevationGrid` as the
  protocols for a caller's own provider; `Landmark`, `SpanRequest`, `MAX_NOTES` and
  `MAX_NOTE_CHARS` beside `Annotations`; and the records `fetch`, `paint` and `letter`
  hand back (`Card`, `Credit`, `Manifest`, `DarkGrid`, `BoundingBox`, `Layers`, `River`,
  `Road`, `ElevationPatch`, `Line`, `Projection`, `Label`, `Span`, `VectorArea`,
  `VectorLine`, `HillshadeBand`, `HillshadeImage`).
- Field docs: the seven style groups, `Label`, `Span`, `BoundingBox`, `OverpassFeatures`
  and `OpenTopoData` (their `__init__` attributes), and every other checked `maps` class
  the test reports, get complete `Attributes:` sections. `#:` and trailing comments go.
  `Line`, `MAX_NOTES` and `MAX_NOTE_CHARS` get attribute docstrings. `Label`'s and
  `Span`'s class docstrings say: "The placer fills these fields in; a `Label` handed back
  by `letter` is a finished value, and writing to one is unsupported."
- `maps/annotations.py` (owned here, not by S7): the module docstring's lines 12 to 13
  become: "`Annotations.roads` names the roads to letter, by number or OSM name; a name no
  drawn road carries is an error at lettering time." The `roads` `Attributes:` entry
  becomes: "Roads to letter by number or OSM name, in place of the roads the lettering
  picks. Each must be a road the basemap draws."
- `maps/providers/base.py`: the module docstring states the provider contract from ADR
  0068's "Extension seams" as capability facts: the protocols are exported, a features
  provider returns Overpass JSON text, `id` enters the cache key, and failures are
  `ProviderError`s.
- `docs/reference/maps.md`: one directive per new name, in the page's order.

Test first:

- `tests/unit/maps/test_style_groups.py::test_a_map_style_group_takes_only_keywords`,
  parametrized over the seven groups with `ids=`.
- `tests/unit/maps/test_records_keyword_only.py::test_a_returned_record_takes_only_keywords`,
  parametrized with `ids=` over the fourteen frozen records plus `Label` and `Span`, each
  built from a minimal keyword dict: a positional call raises `TypeError`. And
  `test_a_returned_record_is_frozen` over the fourteen: assigning a field raises
  `dataclasses.FrozenInstanceError`.
- `tests/unit/maps/test_providers_satisfy_protocols.py::test_the_shipped_providers_satisfy_the_protocols`:
  `features: Features = OverpassFeatures(contact=CONTACT)` and
  `elevation: Elevation = OpenTopoData(contact=CONTACT)`, using the `CONTACT` pattern the
  provider tests already use, with no network, then asserts each `id` is a non-empty
  string. `ty check` makes the assignment the real check.
- `tests/unit/test_public_api.py`: `MAPS_PUBLIC` gains the 31 names.
- `test_style.py` digest literals (`DIGEST` and the rest) are not re-pinned. If one moves,
  stop: the rename leaked into a digest.

- Owned: `src/pyntpot/maps/{__init__,style_groups,style,compose_steps,annotations,basemap,projection,card,credit,plates,track,vector_layer_build,cache}.py`,
  `src/pyntpot/maps/providers/{base,overpass,opentopodata}.py`,
  `src/pyntpot/maps/lettering/label.py`, `tests/support/providers.py`,
  `tests/property/test_projection.py`, `tests/unit/maps/**` **except**
  `tests/unit/maps/painter/test_job.py` (S4), `tests/unit/maps/lettering/test_picks_roads.py`
  and `tests/unit/maps/test_pipeline_letter_compose.py` (S7);
  `tests/architecture/_pending_maps.py`, `tests/unit/test_public_api.py` (the
  `MAPS_PUBLIC` tuple only), `docs/reference/maps.md`.
- Gate: standard + mkdocs strict. Done: `_pending_maps.py` is empty, no digest literal
  moved, the AST scan for positional construction of the sixteen records finds nothing,
  and the search for `LetteringPolicy` and `RouteInk` finds only the S8 notes
  (`docs/features/{maps-lettering-label-placement-tuning,maps-public-signature-types,maps-route-casing,maps-route-glow,maps-route-shadow}.md`,
  `docs/issues/maps-theme-missing-keys-take-dataclass-defaults.md`) and the session A
  files (`docs/reference/style-fields.md:263,277`,
  `docs/issues/docs-style-fields-imports-and-reference-checks.md:11`).

### S7 — Lane: `Annotations.roads` (#161; parallel)

What the source data has, measured on the Lynmouth fixture: `Road.cls` is only `major`
or `minor` (`basemap.py:49`; `osm_elements.py:250`), the `minor` class covers both the
`minor` and `path` brush bands, and `"medium"` never occurs for a road. Today's filter
(`picks_roads.py:83`, `("major", "medium")`) keeps major roads only. `named_lines` files
only named roads under `roads`: a numbered piece with no name (five pieces of the A39 on
the fixture) goes to `crossings` as a bare line, so no number on it can be matched.

Decisions:

- `maps/lettering/picks_lines.py` `named_lines`: in the `else` branch (unnamed line), when
  the entry is a road with a non-empty `r`, also append the full entry
  (`{"n": "", "c": ..., "r": ..., "w": ..., "wn": ..., "d": line}`) to a new
  `geom["numbered"]` list. The `crossings` append stays as it is, and `geom` starts as
  `{"roads": [], "rivers": [], "coast": [], "crossings": [], "numbered": []}`. Only the
  named roads path reads `numbered`; `pick_roads`, `road_lines` and `pick_rivers` read
  the keys they read today, so no pixel can move. The module invariant becomes: "only
  named roads and rivers carry a name; an unnamed lane is kept as a bare crossing line so
  the cost can still see it, and an unnamed numbered road is also kept under `numbered`,
  which only the named roads read." `NamedLines`' attribute docstring and `named_lines`'
  Returns name `numbered`.
- `maps/lettering/picks_roads.py`:
  - Extract the gathering loop of `pick_roads` into
    `_road_pieces(basemap: Basemap, entries: list[dict[str, Any]], card: Card, classes: frozenset[str] | None) -> tuple[dict[str, list[list[Point]]], dict[str, float], dict[str, set[str]]]`,
    returning `(pieces, widths, osm_names)`. Per entry: `name = str(entry.get("n") or "")`;
    `key = road_ref(entry.get("r")) or name`; skip when `not key` or when `classes` is not
    `None` and `entry.get("c") not in classes`; the line, `pieces` and `widths` exactly as
    today; `osm_names.setdefault(key, set())`, adding `name.casefold()` when `name` is
    non-empty. Dict insertion order is first appearance, as today.
  - `pick_roads` calls `_road_pieces(basemap, lines.get("roads") or [], card, frozenset({"major", "medium"}))`
    and ignores `osm_names`. Every entry under `roads` carries a name (`picks_lines`
    invariant), so `not key` skips exactly what `not name` skipped: its result and the
    order of its dicts are unchanged. The `"medium"` in its filter is kept verbatim (no
    behaviour change in the pick path); its docstring's "Only major and medium roads are
    numbered" is untouched.
  - Add `named_roads(basemap: Basemap, lines: NamedLines, card: Card, names: tuple[str, ...]) -> list[Label]`.
    It calls `_road_pieces(basemap, (lines.get("roads") or []) + (lines.get("numbered") or []), card, None)`:
    **every road class** the basemap draws, named or numbered. Then, for each listed name
    in order, `wanted = name.casefold()`, the matching keys are those with
    `key.casefold() == wanted` or `wanted in osm_names[key]`, in dict order. Rules:
    - **Label text** is the key: the road's number when it has one, its name otherwise,
      even when the match was by OSM name (`"Lynbridge Road"` letters `B3234`).
    - **Duplicates:** a key is lettered once, at the position of the first listed name
      that matched it (listed twice, or matched by number and by name).
    - **One name, several keys:** a name that matches several keys (a street name carried
      by a numbered and an unnumbered piece) letters each, in dict order.
    - **Too short:** a matched key whose longest joined run is shorter than
      `road_min_px(size)` is not lettered and is logged at INFO (module logger):
      `"road %s is too short on this card to letter"`. It is not an error: the road is
      drawn, and whether its number fits depends on the card's size.
    - **Unmatched:** after the loop, if any listed names matched no key, raise
      `ValueError(f"no road the card draws is numbered or named {joined}")`, where
      `joined` is `", ".join(repr(n) for n in unmatched)` in listed order. Why an error
      and not a log: a caller annotation that cannot be honoured is a caller error,
      which is the journal notes' precedent (`notes.py:51`, a note off the card raises);
      silently lettering nothing is the defect #161 records; and `_ground` runs before
      `place` and `draw_plate`, so the error leaves no label plate written. It breaks no
      invariant: when the style letters nothing, `letter` returns before `_ground`, so
      nothing is checked (unchanged).
    - Each label is built as `pick_roads` builds one: `name=key`, `kind="road"`,
      `why="road the caller named"`, `px`/`py` the run's middle point, `tier=TIER_ROAD`,
      `size=DEFAULT_LINE_PX * 0.7`, `baseline` the run, `feature_px=widths[key]`. A minor
      road's width comes from `feature_px(basemap, "road", "minor")`, which falls back to
      the 3.4 default (`ROAD_PX_DEFAULT` has no `"minor"` key); that is the accepted
      width, not a change. No distance-to-route test, no budget.
  - The module docstring: key names add `named_roads`; the invariant at lines 9-10
    becomes "a numbered road is one road whatever its pieces are called; a road the track
    was never on is lettered only when the caller names it."
- `maps/lettering/pipeline.py` `_ground`:

  ```python
  named = (
      named_roads(basemap, lines, basemap.card, annotations.roads)
      if annotations is not None and annotations.roads
      else []
  )
  if not style.lettering.label_ground:
      return named
  card = basemap.card
  return (
      ground_labels(basemap, lines, card, strands, annotations)
      + (named or pick_roads(basemap, lines, card, strands))
      + route_markers(strands)
  )
  ```

  With `roads` empty this is today's list, element for element. Note `named or ...`:
  when every named road is too short, `named` is empty and the picked roads come back.
  That is deliberate and tested: the caller asked for roads, none could be set, and the
  card keeps its own, the way `letter` falls back to the leading candidates when none of
  the caller's landmarks lands (`_anchored`). `_ground`'s docstring becomes: "The caller's named roads always,
  and the settlements, rivers, picked road numbers and route markers when the style
  letters the ground; named roads replace the picked ones." `letter`'s docstring gains
  `Raises: ValueError: A journal note is off the card or has no seat, or a road named in
  `annotations.roads` is not drawn on the card.` (the note case is raised today and was
  undocumented). The module docstring adds one sentence: the caller's named roads replace
  the picked ones.
- `Lettering`'s docstring, if `test_field_docs.py` reports it, gets its missing entries.

Test first. Synthetic tests use card metres on `hung_card` (no coordinates, so no
fixture box applies) and real UK names from CONTRIBUTING.md ("Roads": A591, A66, A9,
A82) and real streets they carry (the A591 is Rydal Road through Ambleside; Lake Road is
Ambleside's unnumbered minor road). The Lynmouth tests use only names the fixture's
basemap draws (measured: `B3234` 173 px, `A39` 792 px, `Lydiate Lane` a `minor` road on
the `path` band at 123 px, `B3223` 83 px against a 89.6 px minimum, `Lynbridge Road` an
OSM name on a `B3234` piece).

- `tests/unit/maps/lettering/test_picks_roads.py`, built like the existing tests
  (`hung_card`, `label_basemap`, synthetic `lines` dicts), in a `TestNamedRoads` class:
  - `test_a_named_road_is_lettered_though_the_track_was_never_on_it` (`A66` 200 px off any
    route; `named_roads` takes no route at all);
  - `test_a_named_minor_road_is_lettered` (`{"n": "Lake Road", "c": "minor", "r": ""}`,
    named `"Lake Road"`: one label `Lake Road`; and `pick_roads` on the same lines
    letters nothing, which pins that the pick path still skips minor roads);
  - `test_a_road_is_matched_by_number_ignoring_case` (`"a591"` matches ref `A591`);
  - `test_a_road_matched_by_its_name_is_lettered_by_its_number`
    (`{"n": "Rydal Road", "r": "A591"}`, named `"rydal road"`: one label, text `A591`);
  - `test_a_road_named_twice_is_lettered_once_at_its_first_place`
    (`("A591", "A66", "Rydal Road")`: labels `["A591", "A66"]`);
  - `test_named_roads_come_in_the_callers_order` (`("A66", "A591")` gives that order);
  - `test_named_roads_are_not_held_to_the_budget` (`A591`, `A66`, `A82` all lettered);
  - `test_a_named_road_too_short_for_its_number_is_skipped_and_logged` (`caplog` at INFO
    holds the road's number; no error);
  - `test_an_unmatched_name_raises_naming_it` (`("A591", "A9", "B4521")` against lines
    carrying only `A591`: `pytest.raises(ValueError, match="'A9', 'B4521'")`);
  - `test_a_numbered_road_with_no_name_is_matched` (a `tiny_basemap` with
    a `Road` built with every field by keyword (S6 makes `Road` keyword-only in parallel),
    `cls="major"`, `ref="A9"`, `name=""`, through `named_lines`: `numbered` holds it,
    `roads` does not, and `named_roads(..., ("A9",))` letters `A9`);
  - `test_the_numbered_lines_change_nothing_the_picker_reads` (the same basemap:
    `named_lines`' `roads`, `rivers`, `coast` and `crossings` equal what they were before
    `numbered` existed, pinned as literals).
- `tests/unit/maps/test_pipeline_letter_compose.py`, in `TestLetter` (so each test carries
  `@pytest.mark.golden` and the module's `xdist_group`). **Every new `letter` call copies
  the plates directory first**, exactly as `test_a_span_in_seconds_lands_on_the_pinned_indices`
  does (`shutil.copytree(painted.plates.directory, tmp_path / "plates")` and
  `dataclasses.replace(painted.plates, directory=copy)`), because `draw_plate` writes
  `labels-<route>.webp` at a fixed name and the golden card test composes from the
  module's own plate:
  - `test_empty_annotations_letter_the_pinned_list`: `Annotations()` places exactly
    `PINNED_LABELS` (the #161 proof that does not need the pinning machine);
  - `test_named_roads_replace_the_picked_roads`: `Annotations(roads=("B3234",))`: the
    `kind == "road"` labels are exactly `["B3234"]`, so both picked roads (`A39` and
    `B3234`, `PINNED_LABELS` lines 29-30) are replaced;
  - `test_a_road_named_by_its_street_is_lettered_by_its_number`:
    `roads=("Lynbridge Road",)` gives road labels `["B3234"]`;
  - `test_an_unknown_named_road_raises_and_writes_no_plate`: `roads=("A591",)` raises
    `ValueError` matching `'A591'`, and the copied plates directory holds no
    `labels-*.webp` it did not hold before;
  - `test_named_roads_are_lettered_when_the_style_letters_no_ground`: a style with
    `label_ground` false and `roads=("B3234",)`: the placed labels include `B3234` and no
    settlement, river or route marker.
  - `test_a_named_minor_road_is_set_along_its_lane`: on the fixture's own basemap and
    `named_lines`, `named_roads(..., ("Lydiate Lane",))` returns one label, text
    `Lydiate Lane`, whose baseline is at least `road_min_px` long (a unit-level call; it
    writes nothing).
  - `test_a_named_road_too_short_on_the_card_falls_back_to_the_picked_roads`:
    `roads=("B3223",)` raises nothing, logs `B3223` at INFO, and the road labels equal
    the pinned picked roads `["A39", "B3234"]`.
  `PINNED_LABELS` and the golden card test stay as they are and must pass unchanged.

- Owned: `src/pyntpot/maps/lettering/{picks_roads,picks_lines,pipeline}.py`,
  `tests/unit/maps/lettering/test_picks_roads.py`,
  `tests/unit/maps/test_pipeline_letter_compose.py`,
  `tests/architecture/_pending_roads.py`.
- Gate: standard. Done: the new tests pass, `PINNED_LABELS` and every golden pass
  unchanged, `_pending_roads.py` is empty, and the search for `medium` in
  `picks_roads.py` finds only the pick path's filter and its docstring.

### S8 — Integrate: drop the ratchet, notes and root docs (serial, after the merges)

- Delete the four `_pending_*.py` files and remove the pending subtraction and both
  ratchet tests from `test_public_signatures.py` and `test_field_docs.py`. The rule is now
  absolute.
- `GLOSSARY.md`, three rows only: "brush sheet" cites `ink.brush_sheet` for the tables;
  "style group" adds "Each is a frozen, keyword-only dataclass named `<Group>Style`";
  "vector layers" cites `maps.vector_layer_build.VectorLayers`.
- `BOUNDARIES.md` line 29: add "Every name a public signature reaches is public (ADR 0068,
  `tests/architecture/test_public_signatures.py`)."
- Delete the notes `docs/features/maps-public-signature-types.md`,
  `docs/features/ink-public-wash-options.md`,
  `docs/features/maps-public-provider-protocols.md`,
  `docs/features/docs-field-docs-that-render.md`,
  `docs/issues/maps-public-functions-shadow-modules.md` and
  `docs/issues/maps-annotations-roads-ignored.md`.
- Notes that cite them or the old paths, path and fact edits only:
  `docs/features/docs-missing-how-tos.md` lines 38 to 45 (`Landmark`, `SpanRequest` and
  `Annotations.roads` now exist and work); `docs/features/maps-fetch-hands-back-the-plates-dir.md`
  line 41; `docs/features/ink-blank-paper-by-size.md` line 45;
  `docs/features/{maps-route-shadow,maps-route-glow,maps-route-casing}.md` line 6
  (`maps.compose_steps.route`) and the `RouteInk` in each one's "Possible shape" line
  (`maps-route-shadow.md:16`, `maps-route-glow.md:19`, `maps-route-casing.md:20`) becomes
  `RouteInkStyle`; `docs/features/ink-stroke-density-profile.md` line 5
  (`pyntpot.ink.stamping`); `docs/features/docs-examples-housekeeping.md` line 22
  (`ink/stamping.py`); `docs/features/ink-data-driven-brushes-and-pigments.md` line 5
  (the brush tables are in `ink/brush_sheet.py`, the brushes in `ink/brush.py`);
  `docs/features/maps-lettering-label-placement-tuning.md` line 82 and
  `docs/issues/maps-theme-missing-keys-take-dataclass-defaults.md` line 23
  (`LetteringStyle`, `RouteInkStyle`).
- File the seven follow-ups spec.md lists ("Out of scope, filed separately"): each note in
  `docs/features/` with its GitHub issue (CLAUDE.md, "Issues and features"), searching
  the open issues first. `maps-lettering-frozen-records.md` says `Label` and `Span` are
  keyword-only, mutable while the placer fills them, and that writing to a returned one is
  unsupported, so freezing them is not a breaking change. If the session cannot reach
  GitHub, commit the notes without issue links and list them for the orchestrator.
- Owned: the files above. Gate: standard + mkdocs strict. Done: no `_pending` file, the
  absolute gates pass, and the word search (Approach, "Searches") for each of
  `LetteringPolicy`, `RouteInk`, `Pt` and `Anchor`, plus the old-module search, find
  exactly these allowed hits and no others: `tests/mutation/test_shard.py:18,26` (literal
  data); `docs/reference/style-fields.md:263,277` and
  `docs/issues/docs-style-fields-imports-and-reference-checks.md:11` (session A's,
  handed over below).

### S9 — Docstring terminology sweep (serial)

The word list is "per `specs/007-docs-truth-and-glossary/spec.md`, Canonical terms
section"; the orchestrator hands it over. Known candidates: the 22 uses of "label plate",
`Track` described as a "recorded route", `compose` returning a "raster card", and
`Canvas` as the "card's metre box". Docstrings and comments under `src/pyntpot` only. No
code, no identifiers, no behaviour.

- Owned: `src/pyntpot/**` (docstrings and comments only).
- Gate: standard. Done: every listed non-canonical term is gone from `src/` docstrings,
  and `git diff` touches no line outside a docstring or comment.

### S10 — Mutation testing (serial, local only)

Per CONTRIBUTING.md, "Mutation testing", after S9 so the patterns cover the final code.
It runs locally; nothing is pushed and the Actions workflow is not used.

**Scope: functions whose behaviour changed in this diff.** Verbatim moves (S0), pure
renames (`Pt` to `Point`, `Anchor` to `Align`, the four module renames), docstring and
comment edits (S4, S5, S6, S9) and declaration-only changes (`frozen`, `kw_only`, a
dataclass replacing a tuple alias) are excluded. Survivors that predate this branch in a
function whose behaviour did not change are out of scope.

The expected list, from the "Approach" list of body changes:

| Function | mutmut pattern | Why |
| --- | --- | --- |
| `ink.washing.wash` | `pyntpot.ink.washing.x_wash*` | reads `Flow` by name |
| `ink.bloom.bloom` | `pyntpot.ink.bloom.x_bloom*` | reads `Blooms` by name |
| `maps.lettering.picks_roads.named_roads` | (maps, see below) | new |
| `maps.lettering.picks_roads._road_pieces` | (maps) | new, extracted |
| `maps.lettering.picks_roads.pick_roads` | (maps) | now calls `_road_pieces` |
| `maps.lettering.picks_lines.named_lines` | (maps) | files `numbered` |
| `maps.lettering.pipeline._ground` | (maps) | named roads wiring |
| `maps.projection.track_projection` | (maps) | builds a frozen `Projection` |
| `maps.painter.job.PaintJob.flow`, `.bloom` | (maps) | build records |

The rule that checks the list (a throwaway script in the scratchpad, not committed):

1. `uv run python tests/mutation/scope.py --base origin/main --out "$patterns"` lists every
   touched `ink`/`letters` function.
2. For each, take the old source from `git show origin/main:<old path>` (old path through
   the rename map: `ink/washing.py` was `ink/wash.py`, `ink/stamping.py` was
   `ink/stamp.py`) and the new source from `HEAD`. Parse both with `ast`, find the
   function by its qualified name, drop its docstring node, `ast.unparse` each (this drops
   comments and normalises whitespace and wrapping), and on the old text substitute
   `\bPt\b` to `Point`, `\bAnchor\b` to `Align`, `pyntpot.ink.wash\b` to
   `pyntpot.ink.washing`, `pyntpot.ink.stamp\b` to `pyntpot.ink.stamping`.
3. A function whose two texts are equal is excluded. The rest is the run list.

If the run list holds an `ink`/`letters` function the table does not, the slice stops and
reports it: either a body changed that the plan did not plan, or the table is wrong.

Run, for the `ink`/`letters` list:

```bash
xargs -r -a "$run_list" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

The maps rows are outside `[tool.mutmut] only_mutate` (`pyproject.toml:260`, ink and
letters) and its test selection (no `tests/unit/maps`). They are run in a throwaway
worktree (`git worktree add` in the scratchpad from `HEAD`) whose `pyproject.toml` alone
is edited, never committed: `only_mutate` set to the four files
(`src/pyntpot/maps/lettering/{picks_roads,picks_lines,pipeline}.py`,
`src/pyntpot/maps/projection.py`, `src/pyntpot/maps/painter/job.py`) and the selection
adding `tests/unit/maps/lettering/test_picks_roads.py`,
`tests/unit/maps/lettering/test_picks.py`, `tests/unit/maps/painter/test_job.py` and the
projection tests, still `-m "not golden"`. Patterns for those functions only. The worktree
is removed afterwards. The committed mutation config does not change.

For each survivor in a run-list function, write a focused test (`tests/unit/ink`,
`tests/unit/letters`, `tests/property`, or for the maps rows the S7/S4/S6 test files)
that kills it, or record it as equivalent with the reason in a list S11 puts in the PR
description. A `no tests` function gets a focused test. Time cap: four hours of mutmut
wall time; if it is reached, S10 reports the unrun patterns to the orchestrator instead of
widening anything.

- Owned: `tests/unit/ink/**`, `tests/unit/letters/**`, `tests/property/**`,
  `tests/unit/maps/lettering/test_picks_roads.py`, `tests/unit/maps/painter/test_job.py`,
  `tests/unit/maps/test_projection*.py`.
- Gate: the tests it adds pass, and the standard gate. Done: every run-list function has
  been run, and every survivor in one is killed or named as equivalent.

### S11 — Final review (serial, fresh context)

Review the full diff against this plan and the spec. Run every gate:
`prek run --all-files`, the full suite, `uv run --group docs mkdocs build --strict`. Check
that every acceptance criterion holds and tick `tasks.md`. Confirm that no prose
`docs/` page outside the lists below changed (`git diff --stat origin/main -- docs`).
Draft the PR body: the title and Changelog lines from spec.md, `Closes` for all six
issues, the mutation equivalents, the "Handed to session A" list, and the merge-order
note on the two links below. Commit the `tasks.md` ticks; report to the orchestrator; do
not push.

## Files to touch

Everything named in the slices' "Owned" lists, and:

- `docs/decisions/0068-one-public-surface.md` and its `docs/decisions/README.md` row
  (written with this plan).
- Path-only edits to docs under session A's prose, each one required for a gate:
  `docs/explanation/references.md` lines 22, 59, 113, 127, 142, 149 and 175 (S1, for
  `test_reference_keys.py`), and the reference directives in `docs/reference/ink.md`,
  `letters.md` and `maps.md` (S1, S4, S5, S6, for `test_site.py` and the strict build).

## Files to leave alone

- Prose under `docs/` that session A owns: `docs/explanation/**` beyond the seven path
  strings, `docs/how-to/**`, `docs/tutorials/**`, `docs/reference/style-fields.md` and
  the other hand-written reference pages, `docs/index.md`, `docs/architecture.md`,
  `docs/issues/docs-style-fields-imports-and-reference-checks.md` (#163).
- `docs/decisions/` except 0068 and the index row: accepted ADRs are history.
- `specs/001-*` to `specs/005-*`, `CHANGELOG.md` (drafted at release).
- `examples/**`: nothing in them changes. They build every style group by keyword, and
  `NibGroups` stays positional.
- `mkdocs.yml`: no option is needed for `Attributes:` sections.
- `tests/mutation/test_shard.py`: `"pyntpot.ink.wash"` is literal data.
- `[tool.mutmut]` in `pyproject.toml`: S10's maps run edits a throwaway copy only.
- The four private `Clip` aliases (filed separately), `Measure` and `MeasureTracked`,
  which no public signature names.
- `pyntpot.__all__`: no promoted name is top-level.
- The placer's in-place writes to `Label` and `Span` (`placement.py`,
  `placement_flat.py`, `placement_leaders.py`, `spans.py`): they stay; freezing is the
  filed follow-up.

## Handed to session A

B's changes make these prose statements stale. A owns them:

- `docs/explanation/how-the-wash-works.md` lines 125 to 142: "The public `wash` takes a
  body and a pool and nothing else" is false once `WashOptions` is public. Line 141 links
  the deleted note `ink-public-wash-options.md`.
- `docs/how-to/self-host-providers.md` lines 7 to 9: the protocols are now public, and
  line 9 links the deleted note `maps-public-provider-protocols.md`.
- Both links are absolute `github.com/.../blob/main/...` URLs, so the strict build does
  not see them; they go dead when this PR merges. Session A's PR lands first or in the
  same merge window, or A replaces the links; S11 puts this in the PR body so the
  orchestrator orders the merges.
- `docs/reference/style-fields.md` line 263 (`RouteInk` becomes `RouteInkStyle`) and line
  277 (`LetteringPolicy` becomes `LetteringStyle`). Every "`X`, from `pyntpot.Y`" claim
  becomes true: `WashStyle` from `pyntpot.ink`, the seven map groups from `pyntpot.maps`.
- `docs/how-to/letter-your-own-landmarks.md` line 36: `Landmark` and `SpanRequest` can be
  imported now (optional rewrite).
- `docs/architecture.md` lines 23 to 24: may add 0068's rule.
- `GLOSSARY.md` is shared: B edits only the "brush sheet", "style group" and "vector
  layers" rows (S8). A merges its canonical-terms edits around them.
- `docs/issues/docs-style-fields-imports-and-reference-checks.md` (#163) line 11 names
  `LetteringPolicy` and `RouteInk`.

## Delegation

- S0 to S3, S8 and S9: one `plan-slice-implementer` each, in the main worktree, serial.
- S4, S5, S6, S7: four `plan-slice-implementer`s, each in its own worktree from S3's
  commit, owning the disjoint file sets above. The only file two lanes share is
  `tests/unit/test_public_api.py`, and each lane edits only its own tuple, so the hunks
  do not overlap. No lane edits `_public_surface.py`. Merge S5, S4, S7, S6; rerun the
  standard gate after each merge.
- S10: one implementer, with a `gate-runner` for the long mutmut run.
- S11: a fresh-context reviewer.
- The plan-reviewer gate reviews this plan before S0.

## Decisions

All are in ADR 0068. Those that affect implementation order:

- The two splits come first, so field text never has to fit a full file.
- The renames (S1) come before the gates (S3), because griffe resolves a shadowed name to
  the module and would miss `wash`'s signature.
- The aliases (S2) come before the gates, so the pending sets name `Point`, never `Pt`.
- The ratchet, not `xfail`, keeps the hook green. Its entries are keyed by owner, so
  parallel lanes never edit the same pending file. The walk is transitive and the field
  rule counts reached classes, so the pending sets and `ALLOWED` are complete at S3 and
  only shrink.
- `annotations.py` belongs to S6 (exports and docstrings). S7 changes behaviour only in
  `picks_roads.py`, `picks_lines.py` and `pipeline.py`, so the two lanes stay disjoint.
- The positional-record rewrites sit in S6 because every site is in a file S6 owns; `Label`
  and `Span` need no site edits.

## Response to review 1

Every blocker was checked against the code at `c936970` and holds; each is fixed above
(1: S7; 2: S7's copied plates; 3: S4 owns `test_job.py`, not `test_water.py`; 4 and 5:
S3; 6 and 8: Approach "Searches", S1, S2, S6, S8; 7: S10).

Corrections and additions to the findings:

- **Blocker 1.** The review proposes `named_roads` pass `("major", "minor")`. It passes
  `None` (no class filter) instead, so a class added later is covered too. And the review
  missed a second gap: a numbered road piece with no name is filed under `crossings`, not
  `roads` (`picks_lines.py:71-95`; five A39 pieces on the fixture), so matching by number
  would miss a road numbered but never named. S7 adds the `numbered` key for it. The
  unmatched-name behaviour is a `ValueError`, not the INFO log the draft and the review
  assumed (S7 gives the reasons).
- **Blocker 7.** `[tool.mutmut]` mutates only `ink` and `letters` and selects no maps
  tests, so the maps rows run in a throwaway worktree config (S10). The 52 functions the
  `Point` rename touches are excluded by the normalised comparison, not run and filed.

Should-fixes:

- Adopted: 1 (in part; ADR "Records the pipeline returns" and S6: fourteen records frozen
  and keyword-only, `Projection` frozen, `Label` and `Span` keyword-only, writing to a
  returned one unsupported), 2 (decided, see below), 3 (package docstrings, S4/S5/S6),
  4 (field-rule definitions, S3), 5 (400 limit, split only on growth), 6 (S8 files the
  seven notes), 7 (a commit per slice), 8 (all eight slips), 9 (merge-order note).
  Consider items adopted: the defining-layer check, the `Annotations()` proof, and the
  spec wording on `A39`.
- Should-fix 1, rejected in part: `Label` and `Span` are not frozen. The placer writes
  them in place at about thirty sites in four files (`placement.py`, `placement_flat.py`,
  `placement_leaders.py`, `spans.py`). Freezing them would rewrite the placer's state flow
  in a surface change and risk the goldens. The ADR instead makes writing to a returned
  record unsupported, so the filed freeze is not a breaking change.
- Should-fix 2, decided rather than renamed: `Flow`'s fields keep `exp`, `ref_frac` and
  `frac` because they are the suffixes of `WashStyle.flow_rim_*` (theme keys that cannot
  change without moving digests) and `flow_edge`'s parameter names, so one maps onto the
  other. `Blooms` keeps its name because `bloom` is not public: `<Call>Options` names the
  settings record a public function takes, and a record nested inside one names what it
  sets (ADR 0068, "Naming convention").
- Skipped: the `@overload` and PEP 695 type-parameter extensions to the gate (none in
  `src` today; the gate fails closed on what it cannot resolve).
