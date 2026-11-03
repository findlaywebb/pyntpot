# 006 — plan

## Approach

ADR 0068 settles every decision. This plan carries it out in serial mechanical slices,
then four parallel lanes, then serial integration. Every pixel stays where it is: the
golden suite, the pinned plate hashes and the docs images are the proof. The only changes
that reach a function body are `Flow`/`Blooms` (same values, read by name) and the named
roads path (taken only when `Annotations.roads` is set).

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

## Line budget (400; split, never thin)

Measured now, plus the estimated growth when `#:`/trailing comments become `Attributes:`
entries (one entry per field, 8-space indent, wrapped at 100):

| File | Now | After S0 | After field docs | Action |
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
| `maps/lettering/label.py` | 376 | ~216 | ~240 | split in S0 |
| `maps/lettering/label_sizing.py` (new) | | ~175 | ~175 | |
| `maps/track.py` | 130 | | ~140 | none |

Any file a slice finds heading past 380 is split along responsibility lines in that slice
and reported. Never trim text to fit.

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
`SPAN_GROUND`, `SPAN_EFFORT` and `Span`, and drops its `Basemap` import.
`label_sizing.py` imports `Measure`, `Span` and `TIER_LANDMARK` from `label`. `label`
never imports `label_sizing`. Both module docstrings are split to match: "the rules that
size and wrap a name" goes to `label_sizing`.

- Owned: `src/pyntpot/maps/lettering/label.py`, `.../label_sizing.py`, and every module and
  test that imports a moved name from `label` (grep
  `from pyntpot.maps.lettering.label import`; today `notes.py`, `picks_roads.py`,
  `placement_leaders.py`, `picks.py` and their tests among them). Repoint the import
  only.

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

Then `git mv` the four modules: `ink/stamp.py` to `ink/stamping.py`, `ink/wash.py` to
`ink/washing.py`, `maps/compose.py` to `maps/compose_steps.py`, `maps/vector_layers.py` to
`maps/vector_layer_build.py`. Repoint every importer:

- `pyntpot.ink.stamp`: `ink/__init__.py`, `ink/pad.py` (import and the docstring path on
  line 8), `ink/deposit.py` (docstring line 8), `tests/benchmarks/test_ink.py`,
  `tests/property/test_stamp.py`,
  `tests/unit/ink/{test_deposit,test_keyed,test_nib_reload,test_stamp,test_stamp_drift,test_stamp_pool}.py`,
  `tests/unit/maps/test_import_order.py`.
- `pyntpot.ink.wash`: `ink/__init__.py`, `letters/nib.py`,
  `maps/painter/{cover,fluid,water}.py`, `tests/benchmarks/test_ink.py`,
  `tests/unit/ink/{test_keyed,test_pigment,test_wash}.py`,
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
`"pyntpot.ink.wash"` is literal test data, not an import: leave it.

- Owned: the files listed above and `tests/architecture/test_site.py`.
- Gate: standard + mkdocs strict. Done: both new tests pass, no `__init__` shadows a
  submodule, and `import pyntpot.ink.washing as w; w.WashOptions` works.

### S2 — Aliases (serial)

Mechanical, no behaviour:

- Rename `Pt` to `Point` everywhere under `src/` and `tests/` (word-boundary replace of
  `\bPt\b`; lower-case `pt` parameters are untouched). Delete `maps/painter/job.py`'s own
  `Pt = tuple[float, float]` and import `Point` from `pyntpot.ink.polyline`.
- Define `Box = tuple[float, float, float, float]` once, in `ink/polyline.py` under
  `Point`. Delete the definitions in `maps/lettering/label.py`, `maps/vector_layer_build.py`
  and `maps/card_geometry.py`, and import `Box` from `pyntpot.ink.polyline` in those files
  and in every `from pyntpot.maps.lettering.label import ... Box` site (8 today).
- Delete `Anchor` from `maps/lettering/label.py`. `Label.anchor` is annotated `Align`,
  imported from `pyntpot.letters.setting`. Repoint any other `Anchor` user to `Align`.
- Attribute docstrings (a string literal on the next line) for `Point` ("A point `(x,
  y)`, in the units of whatever holds it."), `Box` ("An axis-aligned box `(x0, y0, x1,
  y1)`, in the units of whatever holds it.") and `Align` ("Which end of a line of text its
  anchor point is: `"start"`, `"middle"` or `"end"`."). The `#:` comments they replace go.

- Owned: every file the replace touches; `ink/polyline.py`, `letters/setting.py`.
- Gate: standard. Done: `grep -rnw Pt src tests` and `grep -rnw Anchor src` find
  nothing, there is one `Box =` under `src/pyntpot`, and the suite is green.

### S3 — The gates, with the ratchet (serial)

- `pyproject.toml`: add `"griffelib>=2.4.1"` to `[dependency-groups] dev`; run `uv lock`.
  Check that `uv.lock` holds one `griffelib` entry at the version the docs group already
  resolves.
- `tests/architecture/_public_surface.py` (a helper module, like `_ast_checks.py`):
  - `load(search_path: Path, package: str) -> griffe.Module`:
    `griffe.load(package, search_paths=[search_path], docstring_parser="google", resolve_aliases=True)`.
  - `public_objects(package, layers) -> dict[str, str]`: each `__all__` name of each layer
    module, resolved through aliases to the defining object, mapped canonical path to
    `"<layer>.<name>"` for messages.
  - `names_in(expr) -> set[str]`: the canonical paths of every `ExprName` and of every
    whole `ExprAttribute` chain (not its left parts), through subscripts, unions, calls
    inside `Annotated` and quoted forward references. Constants and strings are skipped.
  - `reached(obj) -> Iterator[tuple[str, str]]`: (canonical path, where) for everything
    the rule in ADR 0068 lists. Parameter defaults are excluded.
  - `ALLOWED: frozenset[str]`: `str`, `int`, `float`, `bool`, `bytes`, `None`, `object`,
    `tuple`, `list`, `dict`, `set`, `frozenset`, `type`, `Exception`, `ValueError`,
    `collections.abc.Callable`, `collections.abc.Iterator`, `collections.abc.Mapping`,
    `collections.abc.Sequence`, `typing.Annotated`, `typing.Any`, `typing.Literal`,
    `typing.Self`, `pathlib.Path`, `numpy.ndarray`, `numpy.random.Generator`,
    `numpy.typing.ArrayLike`, `httpx.Client`, `pydantic.Field`,
    `pydantic.ValidationError`, `tomllib.TOMLDecodeError`, plus any other exact name the
    branch's first run reaches that is stdlib or third-party (list each one).
  - `field_doc_violations(cls) -> list[str]` and `attribute_doc_violations(attr) -> list[str]`
    for the field rule (ADR 0068, "Field documentation"). Fields are griffe attribute
    members not starting with `_`, not properties, not `ClassVar`, excluding
    `model_config`. Entries come from the parsed `Attributes:` section. `#:` lines are
    found by reading the class's source lines.
- `tests/architecture/test_public_signatures.py`:
  - Self-tests, each writing a tiny package to `tmp_path` and loading it with `load`,
    each with a one-line docstring saying what it proves:
    `test_a_private_class_in_a_union_is_reached`,
    `test_a_private_class_in_a_generic_is_reached`,
    `test_a_constant_in_annotated_metadata_is_reached`,
    `test_a_quoted_forward_reference_is_reached`,
    `test_a_type_checking_import_is_resolved_to_its_defining_module`,
    `test_a_reexported_name_counts_as_public`,
    `test_a_private_base_class_is_reached`, `test_a_raises_entry_is_reached`,
    `test_a_dataclass_field_is_reached_through_init`,
    `test_a_parameter_default_is_not_reached`,
    `test_an_allowed_third_party_name_is_not_reported`.
  - `test_no_public_signature_names_a_private_name`: the violations (reached canonical
    paths that are neither public nor `ALLOWED`) minus the pending set are empty. The
    message lists each violation with its `where`.
  - `test_every_pending_signature_entry_still_violates`: the ratchet.
  - `test_every_allowed_name_is_reached`: no stale allowlist entry.
- `tests/architecture/test_field_docs.py`: self-tests on synthetic packages
  (`test_a_missing_entry_is_reported`, `test_an_empty_entry_is_reported`,
  `test_entries_out_of_field_order_are_reported`, `test_a_stale_entry_is_reported`,
  `test_a_property_needs_no_entry`, `test_a_hash_colon_comment_in_a_public_class_is_reported`,
  `test_a_module_constant_without_a_docstring_is_reported`). Then
  `test_every_public_field_and_attribute_is_documented` (violations minus pending is
  empty) and `test_every_pending_field_docs_entry_still_violates`.
- The pending sets live in four files. Each defines `SIGNATURES: frozenset[str]`
  (private canonical paths) and `FIELD_DOCS: frozenset[str]` (public object canonical
  paths), filled from the first run by these rules:
  - `tests/architecture/_pending_ink.py`: paths under `pyntpot.ink.`;
  - `tests/architecture/_pending_letters.py`: paths under `pyntpot.letters.` and the
    top-level `pyntpot.__version__`;
  - `tests/architecture/_pending_roads.py`: paths under `pyntpot.maps.lettering.pipeline.`;
  - `tests/architecture/_pending_maps.py`: every other path under `pyntpot.maps.`.
  The module-scoped fixture loading `pyntpot` once is allowed (an immutable parsed
  object).

- Owned: `pyproject.toml`, `uv.lock`, the six new test-side files above.
- Gate: `uv run pytest tests/architecture` + `uv run ruff check tests` + `uv run ty check`.
  Done: every self-test passes, both real tests pass with the pending sets, and the
  pending sets name nothing that does not violate.

### S4 — Lane: ink (#73, #168, #169; parallel)

Decisions:

- `Flow` becomes `@dataclass(frozen=True, kw_only=True) class Flow` in `ink/washing.py`
  with fields `exp: float`, `ref_frac: float`, `frac: float`. `wash` calls
  `flow_edge(a, sheet, o.rim_px, o.flow.exp, o.flow.ref_frac, o.flow.frac)`.
- `Blooms` becomes `@dataclass(frozen=True, kw_only=True) class Blooms` in `ink/bloom.py`
  with fields `seed: int`, `count: int`, `radius_frac: float`, `lift: float`,
  `warp: float`. `bloom` reads the fields by name in place of the tuple unpack. Its
  `Args:` text for `blooms` points at `Blooms`' `Attributes:`.
- `maps/painter/job.py`: `PaintJob.flow` returns `Flow(exp=..., ref_frac=..., frac=...)`
  and `PaintJob.bloom` returns `Blooms(seed=..., count=..., ...)`, each with the values
  it returns today. Their annotations name `Flow` and `Blooms`.
- `WashOptions`, `WashStyle`, `PaperStyle` and `BrushStyle` become
  `@dataclass(frozen=True, kw_only=True)` (`WashOptions` keeps `eq=False`).
- `pyntpot.ink.__all__` adds `WashOptions`, `Flow`, `Blooms`, `WashStyle`, `separated`,
  `fluid_modulate`, `Point` and `Box`. No top-level change.
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
- The existing tuple uses (`test_wash.py` lines 30, 110, 121; `test_keyed.py` 154;
  `tests/benchmarks/test_ink.py` 131) become keyword `Flow(...)`/`Blooms(...)` with the
  same numbers. Their pinned values do not change: that is the proof that no pixel moves.

Empty `_pending_ink.py` of every entry as it goes green (the ratchet fails until you do).

- Owned: `src/pyntpot/ink/{__init__,washing,bloom,style,brush,brush_style,sheet,pigment}.py`
  and any other `ink` module `test_field_docs.py` reports for a public class;
  `src/pyntpot/maps/painter/job.py`; `tests/unit/ink/**`; `tests/benchmarks/test_ink.py`;
  `tests/unit/maps/painter/test_water.py`; `tests/architecture/_pending_ink.py`;
  `tests/unit/test_public_api.py` (the `INK_PUBLIC` tuple only); `docs/reference/ink.md`.
- Gate: standard + mkdocs strict. Done: `_pending_ink.py` is empty, the goldens pass
  unchanged, and every file is under 400.

### S5 — Lane: letters (#168, #169; parallel)

Decisions:

- `FaceStyle`, `HandStyle` and `NibStyle` become `@dataclass(frozen=True, kw_only=True)`.
  `NibGroups` does not change: positional construction stays, because five examples and
  the tutorials quoting them use it.
- `pyntpot.letters.__all__` adds `Align`.
- Field docs: `FaceStyle`, `HandStyle`, `NibStyle`, `Setting`, `Mark`, and any other
  public `letters` class the test reports, get `Attributes:` sections. `#:` comments go.
- `pyntpot.__version__` gets an attribute docstring in `src/pyntpot/__init__.py`.
- `docs/reference/letters.md`: a directive for `Align`, in alphabetical order.

Test first:

- `tests/unit/letters/test_style.py::test_a_letters_style_group_takes_only_keywords`,
  parametrized over the three groups with `ids=`.
- `tests/unit/test_public_api.py`: `LETTERS_PUBLIC` gains `Align`.
- `tests/unit/letters/test_nib.py` lines 227 and 330: `HandStyle(seed=...)`.

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
- `pyntpot.maps.__all__` adds, sorted the way the list is sorted today: `BasemapStyle`,
  `BoundingBox`, `Card`, `CardStyle`, `CoverStyle`, `Credit`, `DarkGrid`, `Elevation`,
  `ElevationGrid`, `ElevationPatch`, `Features`, `HillshadeBand`, `HillshadeImage`,
  `Label`, `Landmark`, `Layers`, `LetteringStyle`, `Line`, `MAX_NOTES`,
  `MAX_NOTE_CHARS`, `Manifest`, `Projection`, `RibbonStyle`, `River`, `Road`,
  `RouteInkStyle`, `RouteStyle`, `Span`, `SpanRequest`, `VectorArea`, `VectorLine`.
  `maps/__init__.py`'s module docstring loses "The provider protocols ... are reached
  through their own modules, not exported here" and says the protocols are exported for
  a caller's own provider.
- Field docs: the seven style groups, `Label`, `Span`, `BoundingBox`, and every other
  public `maps` class the test reports, get complete `Attributes:` sections. `#:`
  comments go. `Line`, `MAX_NOTES` and `MAX_NOTE_CHARS` get attribute docstrings.
- `maps/annotations.py` (owned here, not by S7): the module docstring's sentence and the
  `roads` `Attributes:` entry become: "`roads`: Roads to letter by number or OSM name,
  in place of the roads the lettering picks. A named road the basemap does not draw is
  not lettered." Lines 12 to 13 of the module docstring become: "`Annotations.roads`
  names the roads to letter; a road the basemap does not draw cannot be lettered."
- `maps/providers/base.py`: the module docstring states the provider contract from ADR
  0068's "Extension seams" as capability facts: the protocols are exported, a features
  provider returns Overpass JSON text, `id` enters the cache key, and failures are
  `ProviderError`s.
- `docs/reference/maps.md`: one directive per new name, in the page's order.

Test first:

- `tests/unit/maps/test_style_groups.py::test_a_map_style_group_takes_only_keywords`,
  parametrized over the seven groups with `ids=`.
- `tests/unit/maps/test_providers_satisfy_protocols.py::test_the_shipped_providers_satisfy_the_protocols`:
  `features: Features = OverpassFeatures(...)` and `elevation: Elevation = OpenTopoData(...)`,
  built with their default arguments and no network, then asserts each `id` is a
  non-empty string. `ty check` makes the assignment the real check.
- `tests/unit/test_public_api.py`: `MAPS_PUBLIC` gains the 31 names.
- `test_style.py` digest literals (`DIGEST` and the rest) are not re-pinned. If one moves,
  stop: the rename leaked into a digest.

- Owned: `src/pyntpot/maps/{__init__,style_groups,style,compose_steps,annotations,basemap,projection,card,credit,plates,track,vector_layer_build,cache}.py`,
  `src/pyntpot/maps/providers/{base,overpass,opentopodata}.py`,
  `src/pyntpot/maps/lettering/label.py`, `tests/unit/maps/**` except S7's files,
  `tests/architecture/_pending_maps.py`, `tests/unit/test_public_api.py` (the
  `MAPS_PUBLIC` tuple only), `docs/reference/maps.md`.
- Gate: standard + mkdocs strict. Done: `_pending_maps.py` is empty and no digest literal
  moved.

### S7 — Lane: `Annotations.roads` (#161; parallel)

Decisions:

- `maps/lettering/picks_roads.py`: extract the gathering loop of `pick_roads` (from
  `geom = ...` to the `widths` fill) into `_road_pieces(basemap, lines, card) ->
  tuple[dict[str, list[list[Point]]], dict[str, float]]`, statement for statement.
  `pick_roads` calls it. Its result and the order of its dicts are unchanged.
- Add `named_roads(basemap, lines, card, names: tuple[str, ...]) -> list[Label]`. Using
  `_road_pieces`, it keeps each key whose number or OSM name equals a listed name under
  `str.casefold`, joins its pieces with `joined` and takes the longest run. It skips a
  run shorter than `road_min_px(size)`, with no distance-to-route test and no budget, and
  builds the `Label` exactly as `pick_roads` does with `why="road the caller named"`.
  Labels come in the order of `names`. To match on the OSM name, `_road_pieces` also
  returns, per key, the set of OSM names its pieces carry. For each listed name that
  matched nothing, it logs at INFO (module logger):
  `"no road on the card is named %s"`.
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

  With `roads` empty this is today's list, element for element.
- `Lettering`'s docstring, if `test_field_docs.py` reports it, gets its missing entries.

Test first:

- `tests/unit/maps/lettering/test_picks_roads.py`, built like the existing tests
  (`hung_card`, `label_basemap`, synthetic lines):
  `test_a_named_road_is_lettered_though_the_track_was_never_on_it` (`A66` 200 px off
  the route), `test_a_road_is_matched_by_number_or_name_ignoring_case` (`"a591"` matches
  ref `A591`), `test_named_roads_are_not_held_to_the_budget` (three named roads, all
  lettered), `test_a_named_road_too_short_for_its_number_is_skipped`,
  `test_an_unmatched_name_is_logged_and_lettered_nowhere` (`"A9"`, `caplog` at INFO).
- `tests/unit/maps/test_pipeline_letter_compose.py`, on the module's `painted` fixture:
  `test_named_roads_replace_the_picked_roads` (`Annotations(roads=("B3234",))`: road
  labels are exactly `B3234`, and `A39` is not lettered),
  `test_an_unknown_named_road_letters_no_road` (`roads=("A591",)`: no `kind == "road"`
  label; `caplog` holds `A591`), and
  `test_named_roads_are_lettered_when_the_style_letters_no_ground`.
  `PINNED_LABELS` and the golden card test stay as they are and must pass unchanged.

- Owned: `src/pyntpot/maps/lettering/{picks_roads,pipeline}.py`,
  `tests/unit/maps/lettering/test_picks_roads.py`,
  `tests/unit/maps/test_pipeline_letter_compose.py`,
  `tests/architecture/_pending_roads.py`.
- Gate: standard. Done: the new tests pass, `PINNED_LABELS` and every golden pass
  unchanged, `_pending_roads.py` is empty.

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
  (`maps.compose_steps.route`); `docs/features/ink-stroke-density-profile.md` line 5
  (`pyntpot.ink.stamping`); `docs/features/docs-examples-housekeeping.md` line 22
  (`ink/stamping.py`); `docs/features/maps-lettering-label-placement-tuning.md` and
  `docs/issues/maps-theme-missing-keys-take-dataclass-defaults.md` (`LetteringStyle`,
  `RouteInkStyle`).
- Owned: the files above. Gate: standard + mkdocs strict. Done: no `_pending` file, the
  absolute gates pass, and `grep -rn "ink\.wash\b\|ink\.stamp\b\|maps\.compose\b\|LetteringPolicy\|RouteInk\b"`
  over `src tests docs/features docs/issues GLOSSARY.md BOUNDARIES.md` finds nothing but
  the `test_shard.py` literal.

### S9 — Docstring terminology sweep (serial)

The word list is "per `specs/007-docs-truth-and-glossary/spec.md`, Canonical terms
section"; the orchestrator hands it over. Known candidates: the 22 uses of "label plate",
`Track` described as a "recorded route", `compose` returning a "raster card", and
`Canvas` as the "card's metre box". Docstrings and comments under `src/pyntpot` only. No
code, no identifiers, no behaviour.

- Owned: `src/pyntpot/**` (docstrings and comments only).
- Gate: standard. Done: every listed non-canonical term is gone from `src/` docstrings,
  and `git diff` touches no line outside a docstring or comment.

### S10 — Mutation testing (serial)

Per CONTRIBUTING.md, "Mutation testing", after S9 so the patterns cover the final code:

```bash
patterns=$(mktemp)
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
xargs -r -a "$patterns" prlimit --as=3500000000 -- uv run mutmut run
uv run mutmut results | grep -v 'not checked'
```

Expect `washing.wash`, `bloom.bloom`, the moved `PaintJob` readers (in `maps`, so out of
scope), and every `ink` and `letters` function whose lines the `Point` rename or S9
touched. The renames themselves add little, because git detects them. If the pattern list
runs past about 150 functions, run it through the Actions "Mutation" workflow in
`changed` mode against `main`. For each survivor, write a focused test in
`tests/unit/ink`, `tests/unit/letters` or `tests/property` that kills it. A `no tests`
function gets a focused `ink` or `letters` test. A mutant that changes no behaviour is
recorded, with the reason, in a list the final slice puts in the PR description.

- Owned: `tests/unit/ink/**`, `tests/unit/letters/**`, `tests/property/**`.
- Gate: the tests it adds pass. Done: zero unexplained survivors.

### S11 — Final review (serial, fresh context)

Review the full diff against this plan and the spec. Run every gate:
`prek run --all-files`, the full suite, `uv run --group docs mkdocs build --strict`. Check
that every acceptance criterion holds and tick `tasks.md`. Confirm that no prose
`docs/` page outside the lists below changed (`git diff --stat origin/main -- docs`).
Draft the PR body: the title and Changelog lines from spec.md, `Closes` for all six
issues, the mutation equivalents, and the "Handed to session A" list. Report to the
orchestrator; do not commit or push.

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
- The four private `Clip` aliases (filed separately), `Measure` and `MeasureTracked`,
  which no public signature names.
- `pyntpot.__all__`: no promoted name is top-level.

## Handed to session A

B's changes make these prose statements stale. A owns them:

- `docs/explanation/how-the-wash-works.md` lines 125 to 142: "The public `wash` takes a
  body and a pool and nothing else" is false once `WashOptions` is public. Line 141 links
  the deleted note `ink-public-wash-options.md`.
- `docs/how-to/self-host-providers.md` lines 7 to 9: the protocols are now public, and
  the link to `maps-public-provider-protocols.md` points at a deleted note.
- `docs/reference/style-fields.md` line 263 (`RouteInk` becomes `RouteInkStyle`) and line
  277 (`LetteringPolicy` becomes `LetteringStyle`). Every "`X`, from `pyntpot.Y`" claim
  becomes true: `WashStyle` from `pyntpot.ink`, the seven map groups from `pyntpot.maps`.
- `docs/how-to/letter-your-own-landmarks.md` line 36: `Landmark` and `SpanRequest` can be
  imported now (optional rewrite).
- `docs/architecture.md` lines 23 to 24: may add 0068's rule.
- `GLOSSARY.md` is shared: B edits only the "brush sheet", "style group" and "vector
  layers" rows (S8). A merges its canonical-terms edits around them.
- `docs/issues/docs-style-fields-imports-and-reference-checks.md` (#163) names
  `LetteringPolicy` and `RouteInk`.

## Delegation

- S0 to S3, S8 and S9: one `plan-slice-implementer` each, in the main worktree, serial.
- S4, S5, S6, S7: four `plan-slice-implementer`s, each in its own worktree from S3's
  commit, owning the disjoint file sets above. The only file two lanes share is
  `tests/unit/test_public_api.py`, and each lane edits only its own tuple, so the hunks
  do not overlap. Merge S5, S4, S7, S6; rerun the standard gate after each merge.
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
  parallel lanes never edit the same pending file.
- `annotations.py` belongs to S6 (exports and docstrings). S7 changes behaviour only in
  `picks_roads.py` and `pipeline.py`, so the two lanes stay disjoint.
