# 006 diff review (S11, fresh context)

**Verdict: FIX**

There are two must-fix items. Both are small text changes, not code faults. Once they land the
diff is READY: every acceptance criterion holds, all six issues are resolved, the gates
are absolute and fail on a regression, and no image moves.

Reviewed at `db8cd52`, against `git diff origin/main...HEAD` (26 commits, 202 files).
I read CLAUDE.md, BOUNDARIES.md, ADR 0068, the spec, plan, tasks, mutation.md and plan
reviews 1 to 4.

## Must fix

1. **`src/pyntpot/ink/sheet.py:50-53, 67, 71`: `Canvas` still talks in the card's
   metres.** The `x0`, `y0`, `x1` and `y1` entries under `Attributes:` say "in the card's
   metres". `scale` (line 67) says "Render pixels per metre" and `px` (line 71) says
   "Project metre points". The class summary (line 47), the module docstring (line 4) and
   `px`'s own `Args:` (line 74) say "world units". `ink` knows no card (the layering in
   BOUNDARIES.md), and one class should not use two units. Fix: write "in world units"
   for the four edges, "Render pixels per world unit." for `scale`, and "Project
   world-unit points into render pixels, north up." for `px`. Docstrings only, so no gate
   or golden moves.
2. **`specs/006-one-public-surface/spec.md`, "Changelog": the roads line lacks `!` and
   the title scope is out of date.** Before this change, `letter` accepted
   `Annotations(roads=("A591",))` and ignored it. Now the same call raises `ValueError`
   (`tests/unit/maps/test_pipeline_letter_compose.py:158`). A public call that used to
   succeed now fails, so under ADR 0042 it is a breaking change. Fix: change the line to
   `feat(maps)!: Annotations.roads letters the roads it names, ...`, and change the
   spec's PR title from `feat(ink)!` to the `feat(maps)!` the PR uses. Most of the newly
   public surface is in maps (31 of 40 names). The PR body draft already has both
   changes.

## Acceptance criteria

The rule and its gates:

- **Met.** ADR 0068 is written, indexed in `docs/decisions/README.md`, and amends 0004,
  0005, 0007, 0026 and 0027 (its title and sections).
- **Met.** `tests/architecture/test_public_signatures.py`: the self-tests on a synthetic
  `tmp_path` package cover unions, `Optional`, generics, `Annotated` metadata, quoted
  references, `TYPE_CHECKING`, re-exports, the façade rule and strings that fail closed
  (lines 46-292). The real checks are at 305-321, and the stale-`ALLOWED` check is at
  318. `ALLOWED` is a reviewed literal `frozenset` at `tests/architecture/_public_surface.py:30`
  with exact names and no prefixes. No ratchet or `_pending_*` file is left (searched
  `tests/architecture`). **Spot-checked in a throwaway worktree, since reverted.** Dropping
  `Blooms` from `pyntpot.ink.__all__` failed the walk (`Blooms` reached from
  `WashOptions.blooms`). Adding `"str | decimal.Decimal"` to `rgb` failed the external
  check, through a quoted annotation.
- **Met.** `tests/architecture/test_field_docs.py`: self-tests for a missing entry, order,
  a stray entry, `#:` and trailing comments, pragmas, and module attribute docstrings. The
  real check is at line 200. Spot-check: deleting `Canvas`'s `h:` entry failed it.
- **Met.** `tests/architecture/test_site.py:94` (no package binds a submodule's name) and
  `:140` (every directive is `::: pyntpot.<layer>.<name>`). Spot-check: binding
  `projection` in `pyntpot/maps/__init__.py` failed the collision test.
- **Met.** `griffelib>=2.4.1` is in `dev` (`pyproject.toml:70`). `uv.lock` holds one
  `griffelib` 2.4.1, shared with `docs`.

The surface:

- **Met.** The `__all__` additions match the ADR table: 8 in ink, 1 in letters, 31 in
  maps. `pyntpot.__all__` gains only a `__version__` docstring. All four lists are pinned
  in `tests/unit/test_public_api.py:134,157`.
- **Met.** No `Pt`, `Anchor`, `LetteringPolicy` or `RouteInk` is left in `src` or `tests`.
  The only hits are the class names `TestFedRouteInk`. `Box` and `Point` live in
  `ink.polyline`.
- **Met.** `Flow` (`ink/washing.py`) and `Blooms` (`ink/bloom.py`) are frozen and
  keyword-only.
- **Met.** All seven map groups, `WashStyle`, `PaperStyle`, `BrushStyle`, the three
  letters groups and `WashOptions` are `frozen=True, kw_only=True`. `WashOptions` also
  keeps the `eq=False` it had on main.
- **Met.** The fourteen records are frozen and keyword-only. `Label` and `Span` are
  `kw_only=True`, and their docstrings say writing is unsupported
  (`maps/lettering/label.py:60,180`). Tests: `tests/unit/maps/test_records_keyword_only.py:134`
  (positional construction raises, `ids=`) and `:144` (frozen). Digests: the pinned
  literals in `tests/unit/maps/test_style.py:156` are unchanged in the diff.
- **Met.** `tests/unit/maps/test_providers_satisfy_protocols.py:14-15` assigns each
  provider to a typed variable, and `ty check` passes.
- **Met.** I checked by import: the four old modules are gone, `pyntpot.ink.stamp`,
  `.wash`, `pyntpot.maps.compose` and `.vector_layers` are functions, and
  `import pyntpot.ink.washing as w; w.WashOptions` resolves.
- **Met.** The strict docs build passes (`uv run --group docs mkdocs build --strict`).
  `test_site.py:100` proves every public name is rendered once.

Field docs:

- **Met.** `test_field_docs.py` is green. The splits `ink/brush_sheet.py` and
  `maps/lettering/label_sizing.py` exist. No `src` file is over 400 lines (the largest
  is `maps/lettering/placement_costs.py` at 399).

`Annotations.roads` (#161):

- **Met.** Unit tests on synthetic lines: `tests/unit/maps/lettering/test_picks_roads.py:135-197`
  cover any class, off the track, casefold, a name lettered by its number, a road named
  twice, the caller's order, no budget, too short and logged, and an unmatched name that
  raises. `test_ground.py:94-116` covers A66, A82 and A9. Lynmouth through `letter`, in
  `tests/unit/maps/test_pipeline_letter_compose.py:135-208`: `Annotations()` gives
  `PINNED_LABELS`, B3234 replaces both picked roads, Lynbridge Road gives B3234,
  Lydiate Lane is lettered, Lee Road falls back to `A39`/`B3234` with an INFO log, B3223
  is lettered through its unnamed pieces, A591 raises and writes no plate, and named roads
  are lettered when `label_ground` is false.
- **Met.** No image moves. `git diff --stat origin/main...HEAD -- '*.png' '*.webp'` is
  empty, no hash literal under `tests/golden` changed, and the full suite with goldens is
  green on this machine.

Process:

- **Met.** Mutation: see "mutation.md" below.
- **Met.** Retired words: the only hits are the two `"callouts"` key lines
  (`tests/golden/test_places.py:194`, `tests/unit/maps/test_example_themes.py:70`).
- **Met.** The six notes are deleted. The citing notes are repointed
  (`docs-missing-how-tos.md` and others), and the seven follow-up notes carry #188 to #194.
  The `Closes` lines are in the PR body draft.
- **Met.** `git diff --stat origin/main -- docs` touches only ADR 0068, its index row,
  notes, the three reference pages and `docs/explanation/references.md` (the path-only
  edits plan.md allows).

## Conventions

- No mocking, `print`, `os.environ` or oversized `src` file: the architecture tests
  enforce these and pass. Test docstrings: ruff `D` passes. The new parametrized tests
  carry `ids=` (spot-checked in `test_records_keyword_only.py` and the style-group tests).
- Places are real UK places on the Lynmouth fixture and the Lake District / Highland
  roads (A591, A66, A82, A9).
- Docstrings: the new module and package docstrings state purpose, key types, what they do
  not do and invariants. `test_docstring_conventions.py` (no roadmap numbers) passes.

## mutation.md

I checked three equivalents against the code, and all three hold:

- `x_bloom__mutmut_36`: `np.zeros(2, np.float32).astype(None).dtype` is `float64`.
- `x_wash__mutmut_156`: `blur` takes `max(1, round(sigma * 0.95))` (`ink/noise.py:219`),
  and 1.6 and 2.6 both round to 2.
- `x_track_projection__mutmut_31`: `base` has `lat_ref=lat[0]`, `lng_ref=lng[0]` and a
  zero origin, so `raw[0]` is `(0.0, 0.0)` and swapping its index changes nothing
  (`maps/projection.py:81-85`).

## Gates (run here at `db8cd52`)

- `uv run pytest -n auto --dist loadgroup -q`: 2444 tests, green, goldens included.
- `uv run ruff check .` and `ruff format --check .`: clean (616 files).
- `uv run ty check`: clean.
- `uv run lint-imports`: 3 contracts kept, 0 broken.
- `uv run --group docs mkdocs build --strict`: built with no warnings.

## Breaking changes (for the changelog)

Every one is in the PR body's Changelog:

- `PaperStyle` and `BrushStyle` are keyword-only (`feat(ink)!`).
- `FaceStyle`, `HandStyle` and `NibStyle` are keyword-only (`feat(letters)!`).
- `Annotations.roads` raises `ValueError` for a name no drawn road carries, and named
  roads replace the picked ones (`feat(maps)!`; must-fix 2).
- These are not breaking under ADR 0026, and are named in the Summary or a `fix` line:
  the four private module paths, and the private `Pt`, `Anchor`, `LetteringPolicy`,
  `RouteInk`, and the old tuple `Flow` and `Blooms`.

## Nice to have

1. Other `ink` docstrings outside `Canvas` still say metres (`ink/raster.py:8-9`,
   `ink/chains.py:46`, `ink/brush_style.py:31-43`, `ink/polyline.py:191`). The
   `brush_style` ones are about map scale, so the wording may be deliberate. File a note
   (`docs/issues/ink-units-wording.md`) rather than widen this diff.
2. `tests/unit/maps/lettering/test_placement.py` is 404 lines. That predates this branch
   (404 on `main`; the diff changes one line), and the 400-line test covers only `src`.
   It is still worth a split, or a note.
3. `src/pyntpot/maps/__init__.py` says "The other candidates modules"; "candidate
   modules" reads better.
4. Tick S11 in `tasks.md` once the two must-fix items land (plan.md S11).
