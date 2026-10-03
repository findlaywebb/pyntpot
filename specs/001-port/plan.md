# 001-port: plan

How the port is built. What and why are in `spec.md`; the sequence is in
`tasks.md`. Upstream source commit ecfa41d.

## Files and boundaries

Tree after P1 (the `_port` layout), with the P4 target in brackets:

```
pyproject.toml            uv_build, src layout, MIT, >=3.13, pins per D22
LICENSE  LICENSE-FONT  README.md  CHANGELOG.md  CONTRIBUTING.md  SECURITY.md
GLOSSARY.md  BOUNDARIES.md  CLAUDE.md  (AGENTS.md symlink)
.github/workflows/ci.yml  golden.yml  publish.yml  codspeed.yml  mutation-nightly.yml
.github/dependabot.yml  CODEOWNERS  pull_request_template.md
.pre-commit-config.yaml
src/pyntpot/__init__.py  py.typed
src/pyntpot/_port/__init__.py
src/pyntpot/_port/paint.py        [-> ink/{noise,sheet,raster,io,wash,pigment,brush,tip,stamp,pad}.py + maps/painter/{plates,brushes,ribbon,paper}.py + letters/nib.py]
src/pyntpot/_port/outlinefont.py  [-> letters/{font,skeleton,trace}.py]
src/pyntpot/_port/labels.py       [-> letters/{setting,hand}.py + maps/lettering_marks.py + maps/lettering/{label,placement,placement_costs,placement_along,spans,span_sides,span_line,span_clear,picks,pipeline}.py]
src/pyntpot/_port/geo.py          [-> maps/{projection,layers,osm,cover,rings,relief,relief_strokes,generalise,rivers}.py + maps/candidates/* + maps/providers/overpass.py]
src/pyntpot/_port/mapcard.py      [-> maps/compose.py + maps/lettering/pipeline.py]
src/pyntpot/_port/card.py         [-> maps/card.py (Card frame) + maps/strands.py]
src/pyntpot/_port/style.py        [-> maps/style_groups.py]  (RouteInk + constants only)
src/pyntpot/_port/fonts/PatrickHand-Regular.ttf  [-> letters/fonts/ at P4.4]
src/pyntpot/_port/themes/default.json   (resolved default style, D23)  [-> maps/themes/default.toml at P3.11/P3.12]
New in P3 (final homes): ink/{__init__,polyline,chains,style}.py  letters/{__init__,style}.py
  maps/{__init__,card,projection,basemap,plates,track,cache,style,style_groups,pipeline,annotations,attribution,cli}.py
  maps/providers/{__init__,base,overpass,opentopodata}.py
tests/support/{golden,providers,http_server}.py  tests/golden/make_golden.py  tests/unit/{ink,letters,maps}/
tests/unit/test_geo.py  tests/unit/test_paint.py
tests/golden/test_parity.py  tests/golden/lynmouth/{paper,wash,pen,labels-centreline}.webp plates.json map.png
tests/fixtures/lynmouth/{track.gpx, overpass-lynmouth.json, landcover-lynmouth.json, elevation-lynmouth.json, README.md, style.json}
tests/architecture/  (template tests, edited per P0.6)
tests/architecture/exemptions/{line_budget.txt, gates_off.txt}
docs/{tutorials,how-to,reference,explanation}/  docs/explanation/references.md  docs/decisions/
specs/001-port/{spec.md,plan.md,tasks.md}   (scrubbed, added at P2.8)
```

Ownership per phase is disjoint: P0 owns scaffolding; P1 owns `src/` and
`tests/` content; P2 owns comment, docstring and test-string text plus the
spec copies; P3 owns the façade modules and the package `__init__` files;
P4 owns the split and the exemptions files; P5 owns `tests/{property,
benchmarks}` and the mutation and benchmark jobs; P6 owns docstring text,
prose and the bibliography; P7 owns docs and release; P8 owns the upstream
switchover.

## Plan of work

Each phase is one or more fresh sessions. A phase ends with its gate green
and a commit on `main`. Every brief states the gate command and the return
shape.

### P0. Scaffold the repo

1. Run the agentic Python project template's scaffold script with the
   project name `pyntpot` and the target directory.
2. Delete the web-app shape: `frontend/`, `backend/packages/api`,
   `backend/packages/adapters`, `docs/schemas/`, ADR 0003, the frontend CI
   job, the OpenAPI lines in the PR template, the `FAST` ruff rule,
   `pytest-asyncio` and `asyncio_mode`, `test_schema_descriptions.py`,
   `test_openapi.py`, `test_ports.py`, the sqlite tests and migrations,
   the `PYNTPOT_` env prefix note in `CLAUDE.md`, the typer CLI rule.
3. Collapse the workspace to one package: move
   `backend/packages/core/src/pyntpot` to `src/pyntpot`, `backend/tests`
   to `tests`, delete `backend/`. Edit every path:
   - `pyproject.toml`: remove `[tool.uv.workspace]` and `[tool.uv.sources]`;
     `[tool.ty.environment] root = ["src", "tests"]`, `[tool.ty.src] include = ["src", "tests"]`;
     `[tool.pytest.ini_options] testpaths = ["tests"]`, `pythonpath = ["tests"]`;
     `[tool.coverage.run] source = ["pyntpot"]`; delete `fail_under` for now
     (P5 sets it); `[tool.vulture] paths = ["src"]`;
     `[tool.ruff.lint.isort] known-local-folder = ["support"]` stays.
   - `.pre-commit-config.yaml`: the architecture-test hook path becomes `tests/architecture`.
   - `tests/architecture/_ast_checks.py:13-15`: `PACKAGES = REPO_ROOT / "src"`,
     `CORE_SRC = PACKAGES / "pyntpot"`, delete `ADAPTERS_SRC` and every use.
   - `tests/support/__init__.py:9`: `REPO_ROOT = Path(__file__).resolve().parents[2]`.
   - `tests/architecture/test_testing_discipline.py:22`: path to `src`.
   - `tests/architecture/test_boundaries.py`, `test_purity.py`,
     `test_docstring_conventions.py`: every `CORE_SRC`, `ADAPTERS_SRC` and
     `PACKAGES` use follows the new constants; drop the adapters clauses.
   - `.github/workflows/ci.yml`: see step 8.
   - `BOUNDARIES.md`, `CLAUDE.md`, `docs/architecture.md`, ADR 0002: rewrite
     the layer table for `ink`, `letters`, `maps` with `_port` as the
     interim, one paragraph each.
4. Runtime dependencies: `numpy==2.5.2`, `pillow==12.3.0`,
   `fonttools==4.63.0` (D22), `httpx>=0.28`, `pydantic>=2.13`. Dev group:
   the template's minus the deleted ones, plus `hypothesis>=6.168`,
   `pytest-benchmark>=5.3`, `pytest-codspeed>=5.0`, `mutmut>=3.8`.
5. Import-linter: delete the layers contract. Keep one forbidden contract:
   `pyntpot` may not import `matplotlib`, `pandas`, `jinja2`, `yaml`.
   The `maps -> letters -> ink` layers contract is added in P4.
6. Architecture tests and the exemptions mechanism, all under
   `tests/architecture/exemptions/`:
   - `line_budget.txt`: one repo-relative path per line; the 400-line test
     skips listed files. Empty at P0.
   - `gates_off.txt`: one test node id per line, nothing else; a small
     conftest hook marks those tests `skip` with reason "gate off, see
     exemptions". Empty at P0. Free-text notes for P4 go in
     `exemptions/NOTES.md`.
   - The banned-term list is **not in the repository**: it is personal
     content. It lives at `~/personal/pyntpot-private/banned_terms.txt`, one
     term or `re:` regex per line, and the test reads the path from the
     `personal_terms_file` pytest ini option (registered in
     `tests/conftest.py`). If the file is absent the test skips with a loud
     reason, so public CI does not run it. Plain terms match
     **case-sensitively on whole words**, so a short road number does not
     match inside a hex string. The test scans `src/`, `tests/`, `docs/`,
     `README.md`, `CHANGELOG.md`, `GLOSSARY.md` and `specs/`, excluding the
     `exemptions/` directory, `LICENSE`, `CODEOWNERS` and `uv.lock`. The
     list covers personal names, personal place names, road numbers,
     upstream product names and identifier patterns. The previous label
     font name is added in P3, not before.
   - `test_coordinates.py`: every decimal pair that looks like a British
     latitude and longitude (`5\d\.\d{3,}` near `-?[0-9]\.\d{3,}`) in the
     scanned set must fall inside the D10 box. Exempt by name:
     `tests/fixtures/lynmouth/{overpass,landcover,elevation}-lynmouth.json`
     and `tests/golden/lynmouth/plates.json`. Test and fixture code only
     ever uses Lynmouth coordinates.
   - Edit `test_purity.py`: the clock ban and the random ban apply to
     `src/pyntpot` except paths in `line_budget.txt` (P1 adds the port
     files there; P4 removes them and fixes the nine `perf_counter`
     calls by injecting a clock or dropping the timings from the manifest).
   - Keep `test_boundaries.py` (env, print, budget), the docstring test and
     `test_testing_discipline.py` (no mocks).
7. Public-library files: `LICENSE` (MIT, 2026, the maintainer's name; the
   one permitted use of a personal name, and the banned-term scan does not
   include `LICENSE`), `LICENSE-FONT` (OFL 1.1 text from the upstream
   repo's font directory), `CHANGELOG.md` (`Unreleased` only),
   `CONTRIBUTING.md` (gate command, spec flow, no co-authorship trailers,
   CodeQL default setup), `SECURITY.md`, `GLOSSARY.md` (vocabulary table),
   `.github/dependabot.yml` (uv and github-actions, weekly),
   `.github/workflows/publish.yml` (on tag `v*`: `uv build`, then
   `pypa/gh-action-pypi-publish@release/v1` with `environment: pypi`,
   `permissions: id-token: write`).
8. CI (`ci.yml`): job `checks` with matrix `["3.13", "3.14"]` on
   ubuntu-latest: locked sync with malware check, `uv audit`, ruff format
   check, ruff check, ty, lint-imports, `pytest -m "not golden"` with
   coverage (no gate until P5). Job `prerelease` on `3.15-dev` with
   `continue-on-error: true`. `golden.yml`: jobs on ubuntu-latest and
   `macos-15` running `pytest -m golden --golden-tolerance` (defined in
   P1.7). Exact comparison is the **local** gate only: goldens are made on
   one machine and a CI runner's macOS or BLAS build is not guaranteed to
   match bit for bit. `--golden-tolerance` is a pytest option in
   `tests/conftest.py`, not an environment variable (the ruff `banned-api`
   rule forbids `os.environ`).
9. `[project]` metadata: name, description "Hand-drawn watercolour and
   pen-and-ink painting for Python, with route maps", readme, license,
   `license-files = ["LICENSE", "LICENSE-FONT"]`, authors, classifiers
   (Development Status 3, Topic Multimedia Graphics, Typing Typed),
   keywords, `[project.urls]`, `[project.scripts] pyntpot = "pyntpot.maps.cli:main"`
   (the module arrives in P3; until then the script entry is absent).
   `[tool.pytest.ini_options] markers = ["golden: slow parity tests"]`.
   `[tool.mutmut] source_paths = ["src/"]`,
   `pytest_add_cli_args_test_selection = ["tests/", "-m", "not golden"]`.
10. `git init`, commit "Scaffold pyntpot from the toolkit template".
    **No remote.** No repo creation, no push, until P2.9 (D15). The
    `publish.yml` and `ci.yml` files are committed but cannot run until
    then.

Gate: `uv sync && uv run prek run --all-files && uv run pytest` green with
one placeholder test in `tests/unit/`.

### P1. Port with parity proof

Preconditions: read every source file from a clean checkout of the upstream
repo at the source commit, not from a working copy that may be mid-change.
Record its SHA in the run log; it is the upstream source commit named in
`spec.md`. Remove the checkout at the end of P1.

1. Dump the resolved style from the OLD code (D23). From the upstream repo
   root, a throwaway script (not committed there):
   `from analysis.report import render, paint, geo` then
   `cs = render._theme_style("cockpit")`,
   `ps = paint.PaintStyle.from_style(cs)`, `go = geo.GeoOptions.from_style(cs)`,
   `inks = {s: dataclasses.asdict(cs.route_ink(s)) for s in ("Run", "Ride", "Swim", "Other")}`,
   write `{"paint": asdict(ps), "geo": asdict(go), "route_ink": inks}` as
   `src/pyntpot/_port/themes/default.json` with sorted keys. Record
   `ps.digest()` in the run log; P1.6 checks the new code reproduces it.
2. Copy modules into `src/pyntpot/_port/` with these names:
   `paint.py`, `outlinefont.py`, `labels.py`, `geo.py`, `mapcard.py`,
   plus `card.py` holding `_Card`, `separate_strands`, `_ease_along`,
   `_tangent_at` and `STRAND_GAP_WIDTHS` lifted from `charts.py`, and
   `style.py` holding `RouteInk`, `ROUTE_INK`, `ROUTE_EFFECT_OFF`,
   `CASING_COLOURS`, `ROUTE_SHADOW`, `CREAM_PIGMENTS`, `CREAM_PAPER` from
   the upstream `style.py`. Copy `fonts/PatrickHand-Regular.ttf` to
   `_port/fonts/`. Run `ruff format` on the copies.
3. Allowed edits in P1, and no others. Each is mechanical:
   - Import paths repointed to `pyntpot._port.*`. Lazy imports stay lazy.
   - `labels.py`: delete the SVG label-placer section **by symbol name**
     (`_label_ink`, `_haloed`, `_MapLabelPlacer`; about lines 3571 to 3678
     before formatting, which shifts them) and the module-level import of
     `ChartStyle`, `_esc`, `HAND_STACK`. Only that import line references
     the section.
     Keep `CREAM_PIGMENTS` via `_port.style`. If any remaining function
     references a deleted name, stop and report; do not improvise.
   - `geo.py`: delete `CACHE_DIR` and `PLACES_PATH`. Every function that
     defaulted to them takes `cache_dir: Path` and `places: list[dict[str, Any]]`
     as explicit parameters; callers inside `_port` thread them through.
     `load_places(path)` becomes `places` passed in; the file read moves
     to the caller.
   - `activity_id: str` parameters renamed `key: str`; cache file names
     stay `overpass-<key>.json`, `elevation-<key>.json`,
     `landcover-<key>.json`, `plates/<key>/`.
   - `schema.Sport` replaced by `str`; `schema.MapPicks`, `Landmark`, `Span`
     type references replaced by `Any`.
   - `mapcard.compose(..., style: ChartStyle, ...)` becomes
     `compose(key, lat, lng, route_ink: RouteInk, pstyle: PaintStyle, picks, labels, cache_dir)`;
     the body's `style.route_ink(sport)` call becomes the `route_ink`
     argument and `PaintStyle.from_style(style)` becomes `pstyle`.
   - `mapcard.alphabet_sheet(out, style: ChartStyle, lines)` becomes
     `alphabet_sheet(out, pstyle: PaintStyle, lines)`.
   - `PaintStyle.from_style` and `GeoOptions.from_style` gain a sibling
     `from_resolved(d: dict)` that sets fields from the `default.json`
     sections. JSON turns tuples into lists; `from_resolved` restores the
     tuple fields (13 of them in `PaintStyle`) by coercing each value to
     the type of the same field on a default instance. A unit test asserts
     that for every field `type(getattr(from_resolved(d), f)) is type(getattr(PaintStyle(), f))`,
     because `digest()` alone cannot see a list where a tuple was.
     `from_style` is kept for now (dead) and removed in P4.
   - `outlinefont.DEFAULT_FONT` resolved via `importlib.resources.files("pyntpot._port") / "fonts" / ...`.
   - `tests/architecture/exemptions/line_budget.txt` lists the seven
     `_port` modules. `pyproject.toml` gains
     `[tool.ruff.lint.per-file-ignores] "src/pyntpot/_port/*" = ["PLR2004", "ANN401", "PLR0913", "PLR0917", "PLC0415", "C901", "PLR0912", "PLR0915", "FBT", "BLE001", "PLR0914", "PLR0911", "ERA001", "D"]`
     plus any further code the first run reports, each one listed; and
     `[tool.ty] ... exclude = ["src/pyntpot/_port"]` (or the ty
     equivalent; check `ty check --help`). `gates_off.txt` lists
     `tests/architecture/test_no_personal_content.py` and
     `tests/architecture/test_coordinates.py` until P2. If a numpy
     `RuntimeWarning` surfaces under `filterwarnings = ["error"]`, add a
     `filterwarnings` entry naming that exact message and list it in
     `gates_off.txt` as a note for P4. Never widen to `ignore::RuntimeWarning`.
4. Port tests. From the upstream `tests/`:
   - Move to `tests/unit/test_geo.py` and `tests/unit/test_paint.py` every
     test whose imports are only `geo`, `paint`, `labels`, `outlinefont`,
     `mapcard`, `card`, `style` symbols, numpy, PIL and pytest.
   - Leave behind (they stay upstream) every test that imports `charts`,
     `schema`, `normalise`, `render`, or uses upstream snapshot fixtures,
     or asserts SVG strings. List the left-behind test names in the run
     log so P8 keeps them.
   - Rewrite the `monkeypatch.setattr(geo, "CACHE_DIR" | "PLACES_PATH", ...)`
     sites (about 14) to pass `cache_dir=tmp_path` and `places=[...]`
     arguments.
   - Replace the synthetic track constants (`test_geo.py:21-22` and
     `test_paint.py:29`) with Lynmouth values (D10). Any expected value
     that changes as a result is recorded in the run log with the reason;
     if a test's expectation encodes geography rather than behaviour, say
     so and update it.
   - `needs_cache` skips become hard requirements on the Lynmouth fixture.
   - Delete the test that reads the real places file (`test_geo.py:491-497`).
5. Build the Lynmouth fixture. `tests/fixtures/lynmouth/track.gpx`: a
   synthetic 8 km loop of 400 `<trkpt>` through Lynmouth and Lynton inside
   the D10 box, no `<type>`. From the upstream repo with the OLD code, in a
   temporary working directory that has no places file, call
   `geo.fetch_activity("lynmouth", lat, lng, cache_dir=<fixture dir>, margin_m=1500, n=80)`
   with httpx's User-Agent set to `pyntpot-fixture/0.1 (<contact>)` (two
   Overpass queries and 64 OpenTopoData calls, inside both policies). Commit
   `overpass-lynmouth.json`, `landcover-lynmouth.json`,
   `elevation-lynmouth.json` and `README.md` stating source, date, the
   ODbL notice with the copyright URL, and the NASA SRTM citation.
   Copy `default.json` to `tests/fixtures/lynmouth/style.json`.
6. Produce the golden plates with the OLD code, from the same temporary
   working directory, with an exact script committed as
   `tests/golden/make_golden_old.py` (documented as historical; it imports
   `analysis.report` and only runs inside the upstream repo):
   `pstyle = PaintStyle.from_style(_theme_style("cockpit"))`,
   `manifest = paint.paint_activity("lynmouth", lat, lng, pstyle, route=None, cache_dir=<copy of fixture dir in tmp>, force=True)`,
   `img = mapcard.compose("lynmouth", lat, lng, "Ride", style=_theme_style("cockpit"), picks=None, labels=True, cache_dir=<same tmp>)`.
   Copy `plates/lynmouth/*.webp`, `plates.json` and the PNG to
   `tests/golden/lynmouth/`. Never run it against the fixture directory
   itself, so no plates land there. Record the manifest `hash` in the run
   log.
7. `tests/golden/test_parity.py`, marker `golden`: copy the fixture dir to
   `tmp_path`, build `pstyle = PaintStyle.from_resolved(default["paint"])`,
   `route_ink = RouteInk(**default["route_ink"]["Ride"])`, call
   `paint_activity("lynmouth", lat, lng, pstyle, cache_dir=tmp_path, force=True)`,
   assert the plate files were written in this run (mtime newer than the
   copy), assert `manifest["hash"] == golden["hash"]`, then `compose(...)`.
   Exact mode: every WebP and the PNG byte-identical. Tolerance mode
   (`--golden-tolerance`): decode each pair, require that no more than
   0.5 percent of pixels differ by more than 2/255 in any channel. The
   bound is fixed here; an agent that cannot meet it reports, it does not
   loosen it.
8. Commit "Port the painting engine with a parity fixture".

Gate: `uv run prek run --all-files && uv run pytest` green (with the
exemptions files populated), `uv run pytest -m golden` exact on the machine
that made the goldens.

### P2. Scrub personal content and narration (one session per file)

Sessions in this order, each ending in its own commit and an exact parity
run: `labels.py`, `geo.py`, `paint.py`, `mapcard.py` and `style.py`
together, `outlinefont.py` and `card.py` together, `tests/unit/test_paint.py`,
`tests/unit/test_geo.py`.

1. Remove the two tests from `gates_off.txt`. Run
   `uv run pytest tests/architecture/test_no_personal_content.py tests/architecture/test_coordinates.py`;
   the failing lines for the session's file are the worklist.
2. Keep the rule, drop the anecdote. A worked example keeps its numbers
   and gets invented names of the **same character length** so width
   assertions hold. A comment that attributes a rule to a user request
   becomes the rule stated as a fact. Comments that only make sense to
   someone who saw a specific rendered card are deleted. No field names,
   field values, defaults or file names change.
3. One manual pass per file over every capitalised multi-word string and
   every quoted string literal for names the list missed; add each new one
   to the private banned-term list.
4. `ALPHABET_LINES` in `mapcard.py`: replace the place-name lines with a
   pangram, a road-number line of the same length, and two invented span
   strings of the same length as the originals.
5. Test strings: same-length replacements. Any expected value that must
   change gets a one-line reason in the run log.
6. `label_font` (`paint.py:313`) is **not** touched; it feeds the digest.
   It changes in P3 with a recorded golden regeneration.
7. After each session: `uv run pytest -m golden` exact. The scrub changes
   no behaviour.
8. Last session: write `specs/001-port/{spec.md,plan.md,tasks.md}` as a
   scrubbed copy of the working plan, free of identifiers, personal place
   names (Lynmouth, Lynton, Countisbury and Devon are the only ones
   allowed) and personal names. The banned-term test scans `specs/`.
9. Publish as an orphan commit. The local P0 to P2 history contains the
   unscrubbed port by design and is never pushed.
   - Tree scan: with both personal-content tests green, run the same
     scanners over the whole tree once more, including `.github/`,
     `pyproject.toml` and `CONTRIBUTING.md`, excluding only
     `exemptions/`, `LICENSE`, `CODEOWNERS` and `uv.lock`. Whole-word,
     case-sensitive.
   - `git checkout --orphan public && git commit -m "Publish pyntpot"`
     on the scrubbed tree; rename it `main`; keep the old history on a
     local branch `port-history` that is never pushed and is deleted
     after P8.
   - Creating the public repo is outward-facing: state it, get an explicit
     yes, then `gh repo create <owner>/pyntpot --public --source . --push`.
   - Verify on the remote: `git log --format= -p origin/main | grep -nwE -f <(...)`
     returns nothing. Note `--format=` suppresses the author line, which
     legitimately carries the maintainer's name.

Gate: full gate green with both personal-content tests on; parity exact.

### P3 and P4: how to run a slice

P3 and P4 are cut into slices of one focused session each, about 600 changed
lines or fewer (lines moved verbatim between files do not count; their lint
fixes do). Each slice below is self-contained: an implementer reads this
section, the slice, `CLAUDE.md`, `CONTRIBUTING.md`, `GLOSSARY.md` and
`architecture.md` (for the A-item it implements), and nothing else is needed.
Line numbers drift; names are authoritative. Grounding counts below were taken
at commit `69d485f`.

**Rules every slice follows.**

- Test first. Every new test has a one-line docstring saying what it proves,
  no mocks (`unittest.mock`/`pytest-mock` are banned; a hand-written class or
  function standing in for a provider is a real object), function-scoped
  fixtures except a module-scoped one for an immutable object, `ids=` on every
  `parametrize`, golden values pinned as literals. Tests use
  `tests/fixtures/lynmouth/` and synthetic coordinates inside 51.19 to 51.26 N,
  3.80 to 3.88 W (D10). Any place name in a test or example comes from the
  `CONTRIBUTING.md` list (D26).
- New test files mirror the package: `tests/unit/maps/`, `tests/unit/ink/`,
  `tests/unit/letters/`, each a package with `__init__.py`. New test files stay
  under 400 lines even though `test_no_oversized_files` scans `src/` only.
- New modules under `src/pyntpot/{ink,letters,maps}` get no per-file ruff
  ignores and are not excluded from `ty`. Code moved out of `_port` must pass
  the full rule set where it lands: fix the findings, behaviour-neutral, never
  add a `noqa` or an ignore. Measured debt with the `_port` ignores removed:
  `paint.py` 110 ruff findings, `geo.py` 117, `labels.py` 162,
  `outlinefont.py` 24, `mapcard.py` 8, `card.py` 5, `style.py` 4 (165 of them
  `PLR2004`, 14 `C901`, 10 `PLR0912`, 9 `PLR0915`), plus about 59 `ty`
  diagnostics across `_port`. A function over the complexity or statement
  limits is decomposed into named helpers in the same commit, under parity.
- Module and public docstrings state purpose, key types, non-goals and
  invariants as capability facts; no spec, phase or slice numbers in `src/`
  (enforced). Logging, never `print`. No `os.environ`. `raise ... from exc`.
  `pathlib`. No ABC or Protocol except `Features` and `Elevation`.
- New terms go into `GLOSSARY.md` in the slice that first uses them (card,
  manifest, credit, setting, mark, candidate are assigned below). Existing
  glossary rows that say "Today `paint.X`" are updated by the slice that moves
  `X`.
- Exemptions only shrink. When a `_port` file is deleted, its line leaves
  `tests/architecture/exemptions/line_budget.txt` and its block leaves
  `[tool.ruff.lint.per-file-ignores]` in the same commit. Nothing is added to
  `gates_off.txt`.
- ADRs: `docs/decisions/NNNN-kebab-title.md`, heading `# NNNN — Title`, a
  `Status:` line, then `## Context`, `## Decision`, `## Consequences`, as in
  `0002-hexagonal-layers.md`. Numbers are pre-assigned below so parallel
  slices cannot collide: 0003 card frame and typed seam (P3.2), 0004
  providers and fetch cache (P3.7), 0005 style groups (P3.11), 0006 golden
  regeneration (drafted P3.12, accepted P3.15), 0007 public API (P3.20), 0008
  hand settings (P4.1), 0009 candidates (P4.9), 0010 layers contract (P4.17).
- No re-export shims. When a name moves, every importer (including tests) is
  repointed in the same commit.
- Commit when the slice's gate is green, message as given (imperative, one
  line, no trailers), then tick the slice's line in `tasks.md` in the same
  commit. Out-of-scope findings go to `docs/issues/`, not into the diff. Do not
  push between P3.12 and P3.15 (the regeneration window).

**Gate commands.** `$SCRATCH` is the session scratchpad directory.

- **G-here** (this environment, every slice):
  `uv sync && uv run prek run --all-files && uv run pytest -m "not golden" && uv run pytest -m golden --golden-tolerance`.
  At `69d485f` the plain `uv run pytest` is red here only because four golden
  byte-exact cases differ (`paper.webp`, `wash.webp`,
  `labels-centreline.webp`, `map.png`); everything else passes (242 passed,
  1 skipped: `test_no_banned_terms`, private terms file absent), prek is
  green, and tolerance mode passes (6 passed, about 75 s).
- **G-exact** (the maintainer's machine only):
  `uv sync && uv run prek run --all-files && uv run pytest`, which includes
  `uv run pytest -m golden` byte-exact. Slices do not claim it; the maintainer
  runs it after pulling.
- **G-self** (from P3.1 on, this environment): before the first edit, on the
  slice's starting commit, run
  `uv run python tests/golden/make_golden.py "$SCRATCH/before"`; after the
  change, `uv run pytest -m golden --golden-dir "$SCRATCH/before"`. This is
  byte-exact against the same machine's own output, so it proves a refactor
  moved no pixel even where committed goldens only hold in tolerance.
- **G-window** (P3.12 to P3.14): `uv sync && uv run prek run --all-files && uv run pytest -m "not golden"`,
  then `uv run python tests/golden/make_golden.py --compare tests/golden/lynmouth "$SCRATCH/after"`,
  whose logged per-output differing fraction and old and new manifest hash are
  copied into the draft ADR 0006. Golden failures are expected here and are
  recorded, not fixed by loosening anything.

**Parity rules.** *Exact, current goldens*: G-here plus G-self, before P3.12.
*Inside the regeneration window*: G-window, P3.12 to P3.14. *Exact, regenerated
goldens*: G-here plus G-self, P3.15 onward. The tolerance bound
(`MAX_DIFFERING_FRACTION = 0.005`, `MAX_CHANNEL_DELTA = 2` in
`tests/golden/test_parity.py`) is never changed. The manifest-hash test is
always exact: the hash is computed from inputs, not pixels, so it is
machine-independent.

**Order and parallelism.**

```
P3.1 ─ P3.2 ─ P3.3 ─ P3.4 ─ P3.5 ─┐
  ├─ P3.6 ─ P3.7 ─┬─ P3.8 ─┐       ├─ P3.12 ─ P3.13 ─ P3.14 ─ P3.15 ─ P3.16 ─ P3.17 ─ P3.18 ─ P3.19 ─ P3.20 ─ P3.21
  │               ├─ P3.9 ─┤       │      (regeneration window)
  │               └─ P3.10 ┘       │
  └─ P3.11 ────────────────────────┘
P3.21 ─ P4.1 ─ P4.2 ─ … ─ P4.18   (P4 is sequential)
```

Parallel-safe groups (disjoint owner files): {P3.2 to P3.5 in sequence},
{P3.6, then P3.7, then P3.8, P3.9 and P3.10 together}, {P3.11}. These three
lines may run at the same time after P3.1. Everything from P3.12 on is
sequential. P3.18 also needs P3.8 and P3.9; P3.16 also needs P3.10.
Two shared files are append-only for parallel slices: `GLOSSARY.md` (P3.2
adds card and manifest, P3.7 adds credit) and the module list in
`tests/unit/maps/test_import_order.py`. Each slice appends its own rows;
the second to land rebases over a one-line conflict and changes nothing else.

### P3. Façade, providers, policy, style, CLI

Preceded by D18 (done, P3.0a): the accepted architecture items A1 to A8 are
folded in here and in P4. A4 lands first, then the one regeneration, then the
façade. A3's shape lands with the façade (`letter`); its file split is P4.

#### P3.1 Golden harness and package skeleton

- Implements: tooling for D5 parity; predecessor P3.0. Parallel-safe: no
  (it is the root).
- Owner files: create `tests/support/golden.py`, `tests/golden/make_golden.py`,
  `src/pyntpot/maps/__init__.py`, `src/pyntpot/maps/providers/__init__.py`,
  `tests/unit/maps/__init__.py`, `tests/unit/maps/providers/__init__.py`,
  `tests/unit/maps/test_import_order.py`; edit `tests/golden/test_parity.py`,
  `tests/conftest.py`. Leave `tests/golden/make_golden_old.py` alone
  (historical, ty-excluded).
- Names: in `tests/support/golden.py`: `FIXTURE_DIR: Path`, `GOLDEN_DIR: Path`,
  `KEY: str = "lynmouth"`, `PLATES: tuple[str, ...]` (the four plate names),
  `OUTPUTS: tuple[str, ...]` (`PLATES` plus `"map.png"`),
  `paint_fixture(work: Path) -> dict[str, Path]` (copies the fixture into
  `work`, runs today's `paint.paint_activity` then `mapcard.compose`, exactly
  as `test_parity.py`'s `painted` fixture does now, saves `map.png`, returns
  output name to path), `differing_fraction(got: Path, want: Path) -> float`.
  `make_golden.py`: argparse, `OUT` positional; writes the five outputs plus
  `plates.json` and `labels-centreline.json` into `OUT`; `--compare DIR` logs
  (logging, not print) each output's `differing_fraction` against `DIR` and
  both manifest hashes. In `tests/conftest.py`: option `--golden-dir PATH`
  (default `tests/golden/lynmouth`) and fixture
  `golden_dir(request) -> Path`. `test_parity.py` uses `paint_fixture`,
  `golden_dir` and `differing_fraction`; its bound constants stay as they are.
  `src/pyntpot/maps/__init__.py` and `providers/__init__.py`: module docstring
  and `__all__: list[str] = []` only.
- Tests: `tests/unit/maps/test_import_order.py` runs, for each of
  `pyntpot.maps`, `pyntpot._port.paint`, `pyntpot._port.labels`,
  `pyntpot._port.mapcard`, a fresh interpreter
  (`subprocess.run([sys.executable, "-c", f"import {name}"], check=True)`),
  proving no import cycle breaks a cold import; later slices add their new
  modules to its parametrize list. Import rule from here on: a leaf module
  under `maps/`, `ink/` or `letters/` imports nothing from `_port` at module
  level; `_port` may import leaves.
- Parity: exact, current goldens. G-here; then G-self against a baseline made
  with the new script on this commit (the script's first use proves it).
- Commit: `Add a same-machine golden harness and the maps package skeleton`
- Done when: `uv run pytest -m golden --golden-dir "$SCRATCH/before"` passes
  byte-exact; `--compare` logs six lines; no test imports `_port` from the
  golden test except through `tests/support/golden.py`.

#### P3.2 One card frame (A4, part 1)

- Implements A4 (frame), D6, D21; predecessor P3.1.
- Owner files: create `src/pyntpot/maps/card.py`, `tests/unit/maps/test_card.py`,
  `docs/decisions/0003-card-frame-and-typed-seam.md`; edit
  `src/pyntpot/_port/card.py` (delete `_Card`), `src/pyntpot/_port/mapcard.py`
  (construct `Card`), `tests/unit/test_paint.py` (the `_Card` users near
  lines 1595 and 2105), `GLOSSARY.md` (add **card**, **manifest**).
- Names: `maps/card.py`:
  `@dataclass(frozen=True) class Card` with `box: tuple[float, float, float, float]`
  (card metres x0, y0, x1, y1), `display: tuple[int, int]`,
  `render: tuple[int, int]`, `mpp: float`, `mpp_display: float`,
  `offset: tuple[float, float] = (0.0, 0.0)`; properties `w`, `h` (display
  pixels), `scale: float` (display pixels per metre, `w / (x1 - x0)`),
  `render_scale: float` (`render[0] / max(display[0], 1)`), `mppd`
  (alias kept only because `labels.py` reads `card.mppd`; name it in the
  docstring as the display metres-per-pixel); methods
  `xy(x: float, y: float) -> tuple[float, float]` (metres to display pixels,
  computed in exactly `_Card.xy`'s operation order:
  `((x + dx - x0) * scale, (y1 - (y + dy)) * scale)`),
  `metres(px: float, py: float) -> tuple[float, float]` (inverse),
  `to_render(x, y)`, and `@classmethod from_manifest(manifest: Mapping[str, Any], offset=(0.0, 0.0)) -> Card`.
  `paint.Plate` (the glossary's canvas) is not touched; `Card.canvas()` is not
  added yet (P3.4 adds it if the painter needs it).
- ADR 0003 (Status: accepted) records A4's whole decision so P3.4 and P3.5
  implement it without re-deciding: one card frame; `Basemap` and `Plates`
  typed, geometry as point lists in card metres; the projection computed
  once and carried; `label_geom`, the second path parser and the `route0`
  patch removed inside the regeneration window; the manifest file keeps its
  JSON shape except that the painter's stage timings are dropped when the
  painter is split (P4.7).
- Tests: `test_card.py`: corners of `box` map to `(0, h)`/`(w, 0)`; `xy` then
  `metres` round-trips to within 1e-9; `from_manifest` on
  `tests/golden/lynmouth/plates.json` yields pinned `w`, `h`, `scale`
  (literal values computed once and pasted); `xy` of three pinned points
  equals pinned literals (parity with the deleted `_Card`).
- Parity: exact, current goldens. G-here plus G-self.
- Commit: `Replace the ad hoc card class with one card frame`
- Done when: `grep -rn "_Card" src tests` returns nothing; ADR 0003 exists.

#### P3.3 One polyline module, moves only (A5, part 1)

- Implements A5 (move half); predecessor P3.2.
- Owner files: create `src/pyntpot/ink/__init__.py` (docstring, empty
  `__all__`), `src/pyntpot/ink/polyline.py`, `src/pyntpot/ink/chains.py`,
  `tests/unit/ink/__init__.py`, `tests/unit/ink/test_polyline.py`,
  `tests/unit/ink/test_chains.py`; edit `_port/geo.py`, `_port/paint.py`,
  `_port/labels.py`, `_port/card.py`, `_port/outlinefont.py`, the two unit
  test files (repoint), `tests/unit/maps/test_import_order.py`.
- Moves (verbatim bodies, public names without the leading underscore where
  another module now imports them): into `ink/polyline.py`: `geo.simplify`,
  `geo.smooth`, `geo.clip_line`, `geo._point_to_seg` (as
  `point_to_segment`), `geo._segments_cross` (`segments_cross`),
  `geo._normal_at` (`normal_at`), `geo._eased` (`eased`), `geo._run` and
  `labels._run` (as `length`; merge only if the bodies are token-identical,
  otherwise keep both and leave the merge to P3.14), `labels._cum`,
  `labels.cumulative_m`, `labels._seg_gap`, `labels._meet`,
  `labels._unit_normal`, `labels._offset_curve`, `labels._spline`,
  `card._tangent_at`, `card._ease_along`, `outlinefont._normals`,
  `paint.deform_line`. Into `ink/chains.py`: `geo.join_ways`,
  `geo.join_strokes`, `geo._join_chains`, `paint.chain_lines`,
  `labels._joined`. `paint.parse_d` and `geo.parse_path` stay where they are
  (A4 deletes both in P3.13). If `ink/polyline.py` passes 400 lines, split
  curves (`spline`, `offset_curve`, `unit_normal`, `meet`) into
  `ink/curves.py`.
- This removes the `labels -> geo` lazy import at `labels.py` (the one that
  borrows `simplify`) and the `labels -> paint` one that borrows
  `chain_lines`. List any cross-module lazy import that remains under `_port`
  in `docs/issues/port-lazy-imports.md` for the P4 split.
- Tests: `test_polyline.py`: `simplify` keeps both endpoints and is
  idempotent on a pinned five-point line; `clip_line` of a line crossing a box
  returns the pinned pieces; `length` of a 3-4-5 polyline is 5.0;
  `cumulative_m` pinned. `test_chains.py`: two touching segments join into
  one; segments beyond `tol` stay apart; for `join_strokes` and `chain_lines`
  a pinned input showing where their tolerance handling differs (this is the
  evidence P3.14 needs).
- Parity: exact, current goldens. G-here plus G-self.
- Commit: `Move the polyline helpers into one ink module`
- Done when: no `def` of any moved name remains under `_port`; the moved
  code passes ruff and ty with no ignores.

#### P3.4 Typed basemap (A4, part 2)

- Implements A4 (basemap), D6, D21; predecessor P3.3.
- Owner files: create `src/pyntpot/maps/projection.py`,
  `src/pyntpot/maps/basemap.py`, `tests/unit/maps/test_basemap.py`,
  `tests/unit/maps/test_projection.py`; edit `_port/geo.py`
  (`Projection`, `track_projection` move out; `journal_layers` returns a
  `Basemap`), `_port/paint.py` (`paint`, `paint_hash`, `label_geom`,
  `paint_activity` read the `Basemap`), `tests/unit/test_paint.py`
  (`tiny_payload` becomes `tiny_basemap`, 28 call sites), `tests/unit/test_geo.py`,
  `tests/support/golden.py` only if a signature it calls changes.
- Names: `maps/projection.py`: `Projection` (moved verbatim from `geo.py`),
  `track_projection(lat, lng, route=None) -> tuple[Projection, list[Pt]]`.
  `maps/basemap.py`: `Pt = tuple[float, float]`, `Line = tuple[Pt, ...]`;
  frozen dataclasses `Road(line: Line, cls: str, band: str, highway: str, name: str, ref: str)`
  (today's keys `c`, `b`, `k`, `n`, `r`, `d`),
  `River(line: Line, cls: str, name: str, width_px: float, name_width_px: float, profile: tuple[float, ...] = ())`
  (`c`, `n`, `w`, `wn`, `wp`, `d`),
  `ElevationPatch(n: int, x0: float, y0: float, x1: float, y1: float, values: tuple[float, ...], low: float, high: float)`
  (`elev_grid`), and
  `Basemap(key: str, projection: Projection, card: Card, bounds: tuple[float, float, float, float], span_m: float, ribbon_m: float, ribbon_fitted_m: float, wet_px: Mapping[str, float], minor_roads: bool, blotch_m: float, dab_spacing_m: float, gran_m: float, route: Line, cover: Mapping[str, tuple[Line, ...]], cover_order: tuple[str, ...], lakes: tuple[Line, ...], sea: tuple[Line, ...], coastline: tuple[Line, ...], roads: tuple[Road, ...], rivers: tuple[River, ...], places: tuple[Mapping[str, Any], ...], candidates: tuple[Mapping[str, Any], ...], sources: tuple[str, ...], elevation: ElevationPatch | None)`
  with `to_json() -> str` (canonical: sorted keys, compact separators, used
  for hashing from P3.12). `Card` gains `canvas() -> paint.Plate` only if the
  painter needs it; otherwise the painter keeps building `Plate` from
  `basemap.card`.
- Parity rule for this slice: every coordinate stored in the `Basemap` is
  quantised exactly as the path strings did today
  (`float(f"{v:.1f}")`, the `path_d` formatting, and `round(v, 1)` where
  `journal_layers` used it), so painting from the typed fields is
  byte-identical. `paint_hash` keeps today's key list and today's values (build
  the same dict from the typed fields, including path strings via `path_d`)
  so the manifest hash is unchanged. The quantisation and the string form are
  removed in P3.13, not here.
- Tests: `test_basemap.py`: `journal_layers` on a copy of the Lynmouth
  fixture returns a `Basemap` whose road, river and cover counts equal pinned
  literals; every `Road.line` has at least two points; `to_json` is stable
  across two calls. `test_projection.py`: projecting the first fixture point
  gives the pinned metres; `inverse` round-trips within 1e-9.
- Parity: exact, current goldens. G-here plus G-self (the hash test proves the
  hash is unchanged).
- Commit: `Carry the basemap as a typed value instead of a payload dict`
- Done when: no `payload["…"]` or `payload.get(` read remains in
  `paint.py`; `journal_layers` returns `Basemap | None`.

#### P3.5 Typed plates and manifest (A4, part 3)

- Implements A4 (plates), D6, D21; predecessor P3.4.
- Owner files: create `src/pyntpot/maps/plates.py`,
  `tests/unit/maps/test_plates.py`; edit `_port/paint.py` (`paint` returns
  `Plates`, `load_plates`, `paint_activity`), `_port/mapcard.py`,
  `_port/labels.py` (readers of `manifest[...]`: `journal_picks`,
  `journal_heuristic`, `settlements`, `home_labels`, `road_lines`,
  `feature_px`, `draw_plate`), `tests/support/golden.py`, unit tests.
- Names: `maps/plates.py`: `DarkGrid(w: int, h: int, values: tuple[tuple[float, ...], ...])`;
  `Manifest` frozen dataclass mirroring today's `plates.json` keys one to one
  (`key` for `id`, `hash`, `route0`, `files`, `sizes`, `bytes`, `card: Card`,
  `span_m`, `ribbon_m`, `places`, `candidates`, `label_geom`, `wet_px`,
  `gran_px`, `labels_hash`, `sources`, `dark: DarkGrid`, `wood_px`,
  `water_px`, `timing`), with `to_json() -> str` producing the same bytes
  the painter writes today and `from_json(text: str) -> Manifest`;
  `Plates(directory: Path, manifest: Manifest)` with properties
  `paths: Mapping[str, Path]`, `hash: str`, `card: Card`. `route_px` and
  `strands` are added by P3.16.
- Tests: `test_plates.py`: `Manifest.from_json` of
  `tests/golden/lynmouth/plates.json` then `to_json` reproduces the file's
  bytes; `paths` lists `paper`, `wash`, `pen`; `load_plates` on a directory
  missing a plate returns `None`.
- Parity: exact, current goldens. G-here plus G-self.
- Commit: `Read painted plates through a typed manifest`
- Done when: `labels.py` and `mapcard.py` contain no `manifest[` or
  `manifest.get(` reads.

#### P3.6 Track

- Implements D6, D7, D21; predecessor P3.1. Parallel-safe with P3.2 to P3.5
  and P3.11.
- Owner files: create `src/pyntpot/maps/track.py`,
  `tests/unit/maps/test_track.py`; add `pyntpot.maps.track` to
  `test_import_order.py`'s list (one line; P3.7 to P3.11 do the same for
  theirs, so expect a trivial merge).
- Names: `BoundingBox(NamedTuple)`: `south`, `west`, `north`, `east` floats.
  `Track(pydantic.BaseModel, frozen=True)`: `lat: tuple[float, ...]`,
  `lng: tuple[float, ...]`, `ele: tuple[float, ...] | None = None`,
  `time: tuple[float, ...] | None = None` (seconds from the first point);
  validators: equal lengths, at least two points, latitudes in [-90, 90].
  `@classmethod from_gpx(path: Path) -> Track` with `xml.etree.ElementTree`,
  reading only `trkpt` elements (GPX 1.0 and 1.1 namespaces), `<ele>` and
  `<time>` when every point has them (`datetime.fromisoformat`, aware;
  nothing reads the clock). `bounding_box(margin_m: float) -> BoundingBox`
  using `geo.bounding_box`'s arithmetic in the same order.
- Tests: on `tests/fixtures/lynmouth/track.gpx` (400 `trkpt`, no `<time>`):
  400 points, `time is None`, first point equals the pinned
  `(51.230678, -3.828447)`, and `lat`/`lng` equal `geo.read_gpx`'s lists;
  `bounding_box(1500.0)` equals a pinned tuple; a synthetic three-point GPX
  written to `tmp_path` with `<time>` values gives `time == (0.0, 5.0, 12.0)`;
  mismatched lengths raise `ValidationError`.
- Parity: exact, current goldens. G-here.
- Commit: `Add the Track model with a GPX reader`
- Done when: `Track` is importable from `pyntpot.maps.track`.

#### P3.7 Provider protocols and credit

- Implements D8, D9 (design); predecessor P3.6. Parallel-safe with P3.2 to
  P3.5 and P3.11.
- Owner files: create `src/pyntpot/maps/providers/base.py`,
  `tests/support/providers.py`, `tests/unit/maps/providers/test_base.py`,
  `docs/decisions/0004-providers-and-fetch-cache.md`; edit `GLOSSARY.md`
  (add **credit**).
- Names: `Credit(text: str, url: str)` frozen dataclass.
  `ElevationGrid(n: int, box: BoundingBox, lats: tuple[float, ...], lons: tuple[float, ...], elev: tuple[float, ...])`
  with `to_json() -> str` byte-identical to `geo.fetch_elevation`'s file
  (`json.dumps({"n", "bbox", "lats", "lons", "elev"})`, default separators)
  and `from_json(text) -> ElevationGrid`.
  `class Features(Protocol)`: `id: str` and `credit: Credit` (read-only
  properties), `features(box: BoundingBox) -> str` (Overpass JSON text, the
  feature query) and `landcover(box: BoundingBox) -> str`.
  `class Elevation(Protocol)`: `id`, `credit`,
  `grid(box: BoundingBox, n: int) -> ElevationGrid`.
  `class ProviderError(RuntimeError)`. `tests/support/providers.py`:
  `FixtureFeatures`, `FixtureElevation` returning the Lynmouth fixture files'
  text, each counting its calls.
- ADR 0004 (accepted): the two protocols (the sanctioned exception to the
  rule of three); a required `contact` string; published limits enforced by
  default (Overpass: sequential, back-off on 429; OpenTopoData: 100 points a
  call, one call a second by a fixed pause, 1000 calls per process); credit
  per provider; the fetch cache keyed by `sha256` of the bounding box, the
  margin and both provider ids, first 16 hex characters (D9), and the
  fixture files renamed to that key in P3.16.
- Tests: assigning `FixtureFeatures()` to a `Features`-annotated variable
  type-checks (ty is the proof; the test asserts its `id`); `ElevationGrid`
  `from_json` then `to_json` of `elevation-lynmouth.json` is byte-identical.
- Parity: exact, current goldens. G-here.
- Commit: `Define the feature and elevation provider protocols`

#### P3.8 Overpass provider

- Implements D8; predecessor P3.7. Parallel-safe with P3.9, P3.10.
- Owner files: create `src/pyntpot/maps/providers/overpass.py`,
  `tests/unit/maps/providers/test_overpass.py`,
  `tests/support/http_server.py` (shared by P3.9; whichever of P3.8 or P3.9
  lands first creates it, the other only imports it).
- Names: `DEFAULT_ENDPOINTS = ("https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter")`
  (not `geo.OVERPASS_URLS`, which still lists the retired
  `overpass.kumi.systems`); `OverpassFeatures(contact: str, endpoints: tuple[str, ...] = DEFAULT_ENDPOINTS, *, client: httpx.Client | None = None, sleep: Callable[[float], None] = time.sleep)`;
  `id = "overpass"`; `credit = Credit("© OpenStreetMap contributors", "https://www.openstreetmap.org/copyright")`.
  Queries reuse `geo.OVERPASS_QUERY` and `geo.LANDCOVER_QUERY` formatted as
  `fetch_overpass`/`fetch_landcover` do (import the constants; P4.12 moves
  them), with the `[timeout:N]` and a `[maxsize:N]` header computed from the
  box area; one request at a time; on 429, `sleep(30.0)` then the next
  endpoint; any other HTTP error tries the next endpoint; when all fail,
  `ProviderError` raised from the last `httpx.HTTPError`. No blanket `except
  Exception`. User-Agent `pyntpot/<__version__> (<contact>)`; an empty
  `contact` raises `ValueError`.
- Tests: `tests/support/http_server.py` runs a real `http.server` on
  `127.0.0.1:0` in a thread (context manager yielding its URL and the
  recorded requests). Tests prove: the User-Agent carries the contact; a 429
  then a 200 calls `sleep` with 30.0 once (the injected `sleep` is a list's
  `append`) and returns the second endpoint's body; all endpoints failing
  raises `ProviderError`; the query body contains the box formatted as
  `fetch_overpass` does (pinned string for a Lynmouth box). No real network.
- Parity: exact, current goldens. G-here.
- Commit: `Add the Overpass feature provider with its usage limits`

#### P3.9 OpenTopoData provider

- Implements D8; predecessor P3.7. Parallel-safe with P3.8, P3.10.
- Owner files: create `src/pyntpot/maps/providers/opentopodata.py`,
  `tests/unit/maps/providers/test_opentopodata.py`; `tests/support/http_server.py`
  as in P3.8.
- Names: `PUBLIC = "https://api.opentopodata.org/v1"`;
  `class ElevationBudgetExceeded(ProviderError)`;
  `OpenTopoData(contact: str, endpoint: str = PUBLIC, dataset: str = "srtm30m", *, budget: int = 1000, client: httpx.Client | None = None, sleep: Callable[[float], None] = time.sleep)`;
  `id = f"opentopodata-{dataset}"`; `credit = Credit("Elevation: NASA SRTM via OpenTopoData", "https://www.opentopodata.org/")`;
  `grid(box, n)` samples the same `n` by `n` lattice as `geo.fetch_elevation`,
  100 points a call, `sleep(1.1)` after each call (no clock read), `None`
  elevations as `0.0`, status other than `OK` raises `ProviderError`; the
  per-process budget is a counter on the instance (the spec's open question:
  per process, no per-cache-dir state) and raises `ElevationBudgetExceeded`
  before the call that would exceed it.
- Tests (local server as P3.8): a 3 by 3 grid makes one call and returns the
  served values in order; `n = 11` (121 points) makes two calls and sleeps
  twice; `budget=1` with `n = 11` raises `ElevationBudgetExceeded` after one
  call; the User-Agent carries the contact.
- Parity: exact, current goldens. G-here.
- Commit: `Add the OpenTopoData elevation provider with a call budget`

#### P3.10 Fetch cache

- Implements D9, A7 (fetch half); predecessors P3.6, P3.7. Parallel-safe with
  P3.8, P3.9.
- Owner files: create `src/pyntpot/maps/cache.py`, `tests/unit/maps/test_cache.py`.
- Names: `MARGIN_M = 1500.0`, `LANDCOVER_MARGIN_M` equal to
  `geo.LANDCOVER_MARGIN_M`, `ELEVATION_SAMPLES = 80`;
  `Cache(directory: Path)` (explicit, never cwd-relative);
  `key(track: Track, features: Features, elevation: Elevation, margin_m: float = MARGIN_M) -> str`
  = first 16 hex of `sha256` over the canonical JSON of the rounded box
  (6 places), the margin and both provider ids;
  `features_path(key)`, `landcover_path(key)`, `elevation_path(key)` returning
  `directory / "overpass-<key>.json"` and so on (today's names, so the engine's
  `overpass_path(key, cache_dir)` keeps working with the hash as its key);
  `plates_dir(key) -> Path`;
  `ensure(track, features, elevation, *, force: bool = False) -> str` that
  fetches whatever is missing (landcover over `LANDCOVER_MARGIN_M`) and
  returns the key.
- Tests: the key for the Lynmouth track with the fixture providers is a pinned
  literal; changing the margin or a provider id changes it; `ensure` into an
  empty `tmp_path` calls each fixture provider once and writes three files
  whose bytes equal the fixture files; a second `ensure` calls nothing.
- Parity: exact, current goldens. G-here.
- Commit: `Key the fetch cache by box, margin and provider`

#### P3.11 Style groups and the TOML theme, unwired (A6, part 1)

- Implements A6 (grouping), D7, D23 (successor); predecessor P3.1.
  Parallel-safe with P3.2 to P3.10.
- Owner files: create `src/pyntpot/ink/style.py`,
  `src/pyntpot/letters/__init__.py` (docstring, empty `__all__`),
  `src/pyntpot/letters/style.py`, `src/pyntpot/maps/style.py`,
  `src/pyntpot/maps/style_groups.py`, `src/pyntpot/maps/themes/default.toml`,
  `tests/unit/maps/test_style.py`, `tests/unit/letters/__init__.py`,
  `docs/decisions/0005-style-groups.md`. Reads, never edits,
  `_port/themes/default.json`, `_port/paint.py`, `_port/geo.py`,
  `_port/style.py`. If P3.3 has not landed, create `src/pyntpot/ink/__init__.py`
  only if absent and coordinate by rebasing (both write the same two lines).
- Names: frozen stdlib dataclasses (ink and letters may never import
  pydantic): `ink/style.py`: `PaperStyle`, `WashStyle`, `BrushStyle`;
  `letters/style.py`: `FaceStyle`, `NibStyle`, `HandStyle`;
  `maps/style_groups.py`: `CardStyle`, `RibbonStyle`, `CoverStyle`,
  `RouteStyle` (with `sport: str = "Ride"` and `inks: Mapping[str, RouteInk]`
  for Run, Ride, Swim, Other; `RouteInk` imported from `pyntpot._port.style`),
  `LetteringPolicy`, `BasemapStyle` (the 28 `GeoOptions` fields).
  `maps/style.py`: `Style(pydantic.BaseModel, frozen=True)` with fields
  `paper, wash, brush, face, nib, hand, card, ribbon, cover, route, lettering, basemap`;
  `@classmethod from_toml(path: Path) -> Style` (`tomllib`, unknown keys
  rejected); `@classmethod default() -> Style` (reads the packaged
  `maps/themes/default.toml` through `importlib.resources`);
  `digest() -> str` (all groups); `base_digest() -> str` (the groups the
  base plates read: paper, wash, brush, card, ribbon, cover, route,
  basemap); `lettering_digest() -> str` (face, nib, hand, lettering); each
  group digest is `sha256(json.dumps(asdict(group), sort_keys=True, default=str))[:16]`
  and a combined digest hashes the group digests in field order;
  `paint_style() -> PaintStyle` and `route_ink() -> RouteInk` (adapters for
  the engine until P4.8).
- Assignment rule: a field goes to the group of the module that reads it
  (A6). The 173 `PaintStyle` fields fall under the class's own section
  comments (card 16, ribbon 16, land cover 7, wood 6, ink 19, route plate 3,
  "crisp layer read by `charts.route_track`" 28, phase 1 brush 13, phase 1
  compositing and paper 25, phase 2 sea 9, phase 2 wash 19, phase 2 brush
  quality 12). A field no module under `src/` reads except through
  `digest`, `paint_hash` or `labels_hash` key lists is consumer-only: it is
  left out of `Style` and named in a pinned `CONSUMER_ONLY` tuple in
  `maps/style.py` and in ADR 0005. `label_font` (a CSS font stack) is
  expected to be one of them. Each field keeps its `#:` comment as its
  documentation.
- Tests: `Style.default()` reproduces every non-consumer-only value in
  `_port/themes/default.json` (`paint`, `geo`, `route_ink` sections) field by
  field, with tuples as tuples; `set(group fields) | set(CONSUMER_ONLY)`
  equals the `PaintStyle` plus `GeoOptions` field names; `paint_style()` of
  the default has the same `digest()` as `PaintStyle.from_resolved(default["paint"])`
  except for the consumer-only fields (assert field by field);
  `from_toml` rejects an unknown key; the three digests of the default are
  pinned literals.
- Parity: exact, current goldens (nothing is wired yet). G-here.
- Commit: `Group the style by layer and load it from TOML`
- Done when: each new file is under 400 lines (split `maps/style_groups.py`
  further if needed); ADR 0005 lists every consumer-only field.

#### P3.12 Wire the style and hash the typed inputs (opens the window)

- Implements A6 (wiring), A7 (base-plate key form), D7, D9; predecessors
  P3.5 and P3.11. Opens the regeneration window: from here to P3.15 commit
  locally and do not push.
- Owner files: edit `_port/paint.py` (`paint_hash`, `paint_activity`,
  `paint`, the `label_font` default), `_port/mapcard.py` (`compose` takes
  `style: Style`), `_port/labels.py` (`hand`, `Hand`, `home_labels` read the
  adapter), `tests/support/golden.py`, `tests/golden/test_parity.py`
  (theme load), `tests/unit/test_paint.py`, `tests/unit/maps/test_style.py`;
  delete `src/pyntpot/_port/themes/default.json` and
  `tests/fixtures/lynmouth/style.json` (both carry the old font stack); edit
  `specs/001-port/design-sources.md` only if the banned entry below matches
  it; create `docs/decisions/0006-golden-regeneration.md` (Status: proposed).
- Changes: `paint_hash(basemap: Basemap, style_digest: str) -> str` =
  `sha256(basemap.to_json())[:16] + "-" + style_digest`, with no hand-kept
  key list; `paint_activity(key, lat, lng, style: Style, *, cache_dir, places, force=False) -> Plates | None`
  passes `style.paint_style()` to the engine and `style.base_digest()` to the
  hash; `compose(key, lat, lng, style: Style, picks, labels, cache_dir)`.
  `PaintStyle.label_font` default becomes `'"Patrick Hand",cursive'` (the
  vendored face) so the old stack leaves the tree; it is consumer-only and
  not in `Style`. Add the old stack as one `re:` entry to the private
  banned-term list at `~/personal/pyntpot-private/banned_terms.txt` if that
  file exists here; if it does not, say so in the hand-off so the maintainer
  adds it. Use the full quoted stack, not the bare first family name, which
  `design-sources.md` cites as a design input.
- `test_style.py`: the default-equality test now compares against pinned
  literals for a sample of fields (the JSON file is gone).
- Parity: inside the regeneration window. G-window. Expected: the hash test
  fails (style digest and hash form change); every pixel test still passes
  in tolerance and in G-self, because no pixel input changed. Record old hash
  `c034e1a4d60bad70-77dce82bec370944`, the new hash and the drift lines in
  ADR 0006's draft.
- Commit: `Hash plates from the typed basemap and the style groups`
- Done when: G-window shows only the hash test failing; `grep -rn "Segoe"
  src tests` is empty.

#### P3.13 Drop the one-decimal round trip, the second parser and the route patch (A4, pixels)

- Implements A4 (pixel half); predecessor P3.12. Inside the window.
- Owner files: `_port/geo.py` (`journal_layers` stops quantising; delete
  `parse_path` and the `path_d` calls that fed the seam; `path_d`,
  `stroke_d`, `rings_path` stay only if a non-seam caller remains),
  `_port/paint.py` (delete `parse_d`, `label_geom`; `paint` reads point
  lists), `maps/basemap.py`, `maps/plates.py` (`Manifest` loses `route0`
  and `label_geom`), `maps/card.py` (`offset` removed), `_port/mapcard.py`
  (`compose` takes the `Basemap` and builds `route_px` from `basemap.route`
  through `Card.xy`; no second `track_projection`), `_port/labels.py`
  (`road_lines`, `pick_roads`, `pick_rivers`, `feature_px` read
  `basemap.roads`, `basemap.rivers`, `basemap.coastline`, simplified with
  `polyline.simplify` at `label_geom_tol_px` times `mpp_display` as
  `label_geom` did), `tests/support/golden.py`, unit tests.
- Parity: inside the window. G-window; record each output's drift in ADR
  0006. Look at `$SCRATCH/after/map.png` beside
  `tests/golden/lynmouth/map.png` (open both images) and write one sentence
  per visible difference.
- Commit: `Keep basemap geometry as full-precision point lists`
- Done when: `grep -n "route0\|label_geom\|parse_d\|parse_path" -r src tests`
  is empty.

#### P3.14 Merge the polyline duplicates (A5, merges)

- Implements A5 (merge half); predecessor P3.13. Inside the window.
- Owner files: `src/pyntpot/ink/polyline.py`, `src/pyntpot/ink/chains.py`
  (and `ink/curves.py` if P3.3 made it), their tests, and the `_port`
  call sites of merged names.
- Merges, one commit each, each followed by the G-window compare with its
  drift appended to ADR 0006: the five chainers (`join_ways`,
  `join_strokes`, `_join_chains`, `chain_lines`, `_joined`) into one
  `chain(lines, tol, *, reverse: bool = True) -> list[list[Pt]]` (the
  tolerance handling difference that P3.3's test pinned is resolved in
  favour of `join_strokes`; say why in the ADR); the two arc-length
  functions into `cumulative`; any remaining duplicate normal or tangent
  helper (`normal_at`, `unit_normal`, `tangent_at`, `normals`) into one. A
  merge whose drift exceeds the tolerance bound is reverted and reported,
  not forced.
- Parity: inside the window. G-window per merge.
- Commits: `Merge the line chainers into one`, `Merge the arc-length helpers`,
  `Merge the polyline normal helpers`.
- Done when: `ink/chains.py` defines one public chainer.

#### P3.15 Regenerate the goldens once (closes the window)

- Implements D22/D23 succession, A4 and A5 parity; predecessor P3.14.
- Owner files: `tests/golden/lynmouth/{paper,wash,pen,labels-centreline}.webp`,
  `labels-centreline.json`, `plates.json`, `map.png`;
  `docs/decisions/0006-golden-regeneration.md`.
- Steps: G-window green apart from goldens;
  `uv run python tests/golden/make_golden.py --compare tests/golden/lynmouth "$SCRATCH/new"`;
  open old and new `map.png`; then
  `uv run python tests/golden/make_golden.py tests/golden/lynmouth`; then
  `uv run pytest -m golden` (byte-exact, passes here by construction) and
  G-here. Run the banned-term and coordinate tests over the new
  `plates.json`. ADR 0006 becomes Status: accepted with: old hash, new hash,
  per-output drift from each window slice and the final compare, what moved
  and why (rounding removal, route patch, chainer merge, style digest),
  the machine (`uname -a`, Python, numpy, Pillow versions), and this
  paragraph: the goldens were made in the agent container; they are the new
  baseline for tolerance runs everywhere; byte-exactness on the maintainer's
  machine is a follow-up check: the maintainer runs `uv run pytest -m golden`
  and, if bytes differ there, regenerates with the same script on that
  machine and appends the result here (the manifest hash must not change,
  since it is computed from inputs).
- Parity: exact against the regenerated goldens. G-here.
- Commit: `Regenerate the golden plates once for the typed seam and style`
- Done when: G-here green; pushing is allowed again.

#### P3.16 Façade: `fetch` and `paint`

- Implements D6, D8, D9, D21, A4; predecessors P3.15, P3.10.
- Owner files: create `src/pyntpot/maps/pipeline.py`,
  `tests/unit/maps/test_pipeline_fetch_paint.py`; edit
  `src/pyntpot/maps/__init__.py` (import leaves first, then the pipeline),
  `src/pyntpot/maps/plates.py` (`route_px`, `strands`),
  `tests/support/golden.py` (`KEY` becomes the cache key);
  `git mv` the three fixture payloads to `overpass-<key>.json`,
  `landcover-<key>.json`, `elevation-<key>.json` with the key from P3.10's
  pinned literal; edit `tests/architecture/test_coordinates.py` `_EXEMPT`
  (the same three files renamed: a rename, not a widening) and
  `tests/fixtures/lynmouth/README.md`.
- Names: `fetch(track: Track, cache: Cache, features: Features, elevation: Elevation, places: Sequence[Mapping[str, Any]] = ()) -> Basemap`
  (calls `cache.ensure`, then `journal_layers`; places enter here, today
  `geo._place_marks` called from `geo.basemap`); `paint(basemap: Basemap, style: Style, out_dir: Path) -> Plates`
  (reuses current plates when the manifest hash matches, as
  `paint_activity` does); `Plates.route_px: tuple[Pt, ...]` and
  `Plates.strands: tuple[Pt, ...]` (the route through `Card.xy`, then
  `separate_strands` at `style.route_ink().px * STRAND_GAP_WIDTHS`).
  `paint_activity` is deleted once nothing calls it.
- Tests: `fetch` with the fixture providers over a copy of the fixture dir
  calls no provider and returns a `Basemap` with the pinned road count;
  `paint` writes three plates and returns a `Plates` whose `hash` equals the
  regenerated golden's; a second `paint` repaints nothing (mtimes unchanged).
- Parity: exact, regenerated goldens. G-here plus G-self.
- Commit: `Add the fetch and paint façade over typed stages`

#### P3.17 Façade: `letter` and `compose` (A3 shape)

- Implements A3 (shape), D6, D21; predecessor P3.16.
- Owner files: `src/pyntpot/maps/pipeline.py`, create
  `src/pyntpot/maps/annotations.py`, `src/pyntpot/maps/lettering.py`,
  `tests/unit/maps/test_pipeline_letter_compose.py`; edit `_port/mapcard.py`
  (its eleven steps move into `letter`; `compose` becomes raster only),
  `_port/labels.py` (delete `_journal_picks`, `_journal_heuristic`,
  `_place_journal_labels`; `place` takes the hand's measure as a required
  argument, ending the flat 8 px default; one text measure remains).
- Names: `Annotations(pydantic.BaseModel)`: `landmarks`, `roads`, `places`,
  `spans` (today the `MapPicks` shape the `picks` argument carries);
  `Lettering` frozen dataclass: `labels: tuple[Label, ...]`,
  `spans: tuple[Span, ...]`, `plate_path: Path | None`;
  `letter(plates: Plates, basemap: Basemap, annotations: Annotations | None, style: Style) -> Lettering`;
  `compose(plates: Plates, lettering: Lettering, track: Track, style: Style, attribution: bool = True) -> PIL.Image.Image`
  (attribution is drawn in P3.18; until then the flag is accepted and
  `False` is the only tested value).
- Tests: `letter` on the fixture returns labels whose names are a pinned
  list; `labels.measure` and `labels._text_width` are gone; `compose` with
  `attribution=False` equals the regenerated `map.png` in G-self.
- Parity: exact, regenerated goldens. G-here plus G-self.
- Commit: `Add the letter and compose façade and delete the lettering shims`

#### P3.18 Attribution

- Implements D8; predecessors P3.17, P3.8, P3.9.
- Owner files: `src/pyntpot/maps/attribution.py`,
  `tests/unit/maps/test_attribution.py`, `src/pyntpot/maps/pipeline.py`
  (`compose` calls it).
- Names: `attribution_text(credits: Sequence[Credit]) -> str` giving
  `"© OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA SRTM"`
  for the two shipped providers; `draw_attribution(image, text, style: Style) -> None`
  bottom-right in the vendored hand face through `Hand`. The credits travel
  on `Basemap.sources` or a new `Basemap.credits: tuple[Credit, ...]` set by
  `fetch`.
- Tests: the text for the two shipped credits is the pinned string; with
  `attribution=True` the bottom-right 5 percent of the image differs from the
  `attribution=False` image and nothing else does.
- Parity: exact, regenerated goldens (parity runs `attribution=False`).
- Commit: `Draw the data attribution on composed maps`

#### P3.19 CLI

- Implements D19; predecessor P3.18.
- Owner files: `src/pyntpot/maps/cli.py`, `tests/unit/maps/test_cli.py`,
  `pyproject.toml` (`[project.scripts] pyntpot = "pyntpot.maps.cli:main"`).
- Names: `main(argv: Sequence[str] | None = None) -> int`; subcommand
  `map TRACK.gpx -o OUT.png --cache DIR --contact STR [--style FILE] [--no-attribution]`;
  logging setup only inside `main`.
- Tests: `main(["map", fixture gpx, "--cache", <copy of fixture dir>, "--contact", "test", "--no-attribution", "-o", tmp/"out.png"])`
  returns 0 offline and the PNG matches the golden within the tolerance
  bound (the spec's verification step 2); a missing `--contact` exits 2.
- Parity: exact, regenerated goldens. G-here.
- Commit: `Add the pyntpot map command`

#### P3.20 Top-level exports and `__version__`

- Implements D6; predecessor P3.19.
- Owner files: `src/pyntpot/__init__.py`, `src/pyntpot/maps/__init__.py`,
  `src/pyntpot/ink/__init__.py`, `src/pyntpot/letters/__init__.py`,
  `tests/unit/test_public_api.py`, `docs/decisions/0007-public-api.md`.
- Names: `pyntpot.__all__` holds exactly the D6 names: `Track`, `Basemap`,
  `Style`, `Plates`, `Lettering`, `Annotations`, `fetch`, `paint`, `letter`,
  `compose`, `Sheet`, `Brush`, `Canvas` (today's `paint.Plate`, exported
  under its glossary name), `stamp`, `wash`, `composite`, `Hand`, and
  `__version__` (from `importlib.metadata.version("pyntpot")`, not a second
  literal). Engine names still come from `_port` until P4; their
  `__module__` is fixed by P4.
- Tests: `set(pyntpot.__all__)` equals the pinned set; every name resolves;
  `pyntpot.Sheet(64, 64, 8.0)` constructs (spec verification 6).
- Parity: exact, regenerated goldens. G-here.
- Commit: `Export the public names from the top-level package`

#### P3.21 Parity test on the façade

- Implements D5, D21; predecessor P3.20.
- Owner files: `tests/support/golden.py`, `tests/golden/test_parity.py`,
  `tests/golden/make_golden.py`.
- Change: `paint_fixture` calls `fetch`, `paint`, `letter`, `compose(...,
  attribution=False)` only; no test under `tests/golden/` imports `_port`
  (except the historical `make_golden_old.py`).
- Parity: exact, regenerated goldens. G-here plus G-self.
- Commit: `Drive golden parity through the public façade`

### P4. Split and layer

Every P4 slice is a move or a merge under parity: exact against the
regenerated goldens, G-here plus G-self, unless stated. A P4 slice moves the
unit tests of the code it moves into the mirrored test file in the same
commit, so `tests/unit/test_paint.py` (3943 lines, 161 tests) and
`tests/unit/test_geo.py` (830 lines, 68 tests) shrink as the work goes and are
deleted by the last slice that empties them, together with their
per-file-ignores, `ty` excludes and `line_budget.txt` lines. Architecture
correction carried from `architecture.md`: `Hand` takes a **setting**, not
`Mark`s; `Mark` is what it produces.

#### P4.1 Design the hand's setting (A2, design)

- Implements A2 (design); predecessor P3.21.
- Owner files: `docs/decisions/0008-hand-writes-settings.md`,
  `src/pyntpot/letters/setting.py`, `tests/unit/letters/test_setting.py`,
  `GLOSSARY.md` (add **setting**, **mark**).
- Task: draft two interface shapes side by side in the ADR, pick one, record
  why, then create only the types. Starting points:
  - Shape 1, one value: `Setting(text, size, anchor: Pt, path: tuple[Pt, ...] | None, align, slant, tracking, ink: str, seed: int, lines: tuple[str, ...] = (), wash: bool = True)`
    and `Hand.write(setting) -> list[Mark]`, plus
    `Hand.stroke(points, *, role, ink, size, seed) -> list[Mark]` for map
    furniture through the same nib. For: one hashable value, so the label
    plate key (A7) is the settings tuple with no hand-kept list; trivially
    serialisable. Against: `path` and `anchor` mean different things in two
    modes, so invalid combinations are representable.
  - Shape 2, two primitives: `Hand.along(text, line, size, *, slant, tracking, ink, seed) -> list[Mark]`
    and `Hand.at(text, anchor, size, *, align, slant, tracking, ink, seed) -> list[Mark]`,
    plus the same `stroke`. For: no invalid modes, each call reads as what it
    does. Against: the plate key has to be assembled from call arguments,
    and a caller batching a plate must build its own record.
  - Pick by: no `Label`, `Span`, tier, kind or intent reaches `letters`; the
    plate key derives from the input without a key list; window choice
    (`Hand._baseline`) moves to maps placement; one test with a string and a
    line covers the interface; fewest public names; parity stays exact.
- `Mark` moves to `letters/setting.py` unchanged (fields `pts`, `role`,
  `ink`, `size`, `pen`, `wash`).
- Tests: constructing the chosen type, its equality and hashing; `Mark`
  defaults pinned.
- Parity: exact, regenerated goldens (types only).
- Commit: `Decide the hand's setting interface`

#### P4.2 The hand writes settings (A2, implementation)

- Implements A2; predecessor P4.1.
- Owner files: create `src/pyntpot/letters/hand.py`,
  `src/pyntpot/maps/lettering_marks.py` (furniture and Label-to-setting
  translation), `tests/unit/letters/test_hand.py`,
  `tests/unit/maps/test_lettering_marks.py`; edit `_port/labels.py` (delete
  `Hand`, `hand()`, `Mark`; `draw_plate` builds settings), the façade.
- Moves: `Hand.measure`, `_along`, `_flat`, `_vary`, `_wobble`, `_rng`,
  `_seed`, the per-instance variation, into `letters/hand.py`, reading
  `FaceStyle` and `HandStyle`. To maps: `KIND_INK`, `KIND_SLANT`,
  `KIND_TRACKING`, `SPAN_INTENT_INK`, `HOME_GLYPH`, `NO_LEADER`, `_ink`,
  `_span_marks`, `_label_marks`, `_baseline` (window choice), `_leader`,
  `_pin`, `_underline`, `_outboard`; the furniture is drawn with
  `Hand.stroke`.
- Tests: `Hand` writes "Grasmere" along a straight synthetic line and gives
  the same marks twice for the same seed and different marks for another
  seed; a setting with slant 0.22 leans (mean x drift of strokes is positive);
  maps furniture: a label with a leader yields one leader mark.
- Commit: `Make the hand write settings and move map furniture to maps`
- Done when: `letters/` imports nothing from `_port.labels` and no name in
  `letters/` mentions tier, kind, intent, span or label.

#### P4.3 The nib plate in letters (A2, raster half)

- Implements A2; predecessor P4.2.
- Owner files: create `src/pyntpot/letters/nib.py`,
  `tests/unit/letters/test_nib.py`; edit `_port/paint.py` (delete
  `label_brushes`, `_pen_profile`, `label_plate`, `_backing_wash`,
  `MARK_WEIGHT`), `_port/labels.py` (`draw_plate`), the façade.
- Names: `nib_brushes(style: NibStyle, scale: float) -> Callable[[str, float], Brush]`,
  `plate(marks: Sequence[Mark], canvas: Canvas, sheet: Sheet, dark: DarkGrid, style: NibStyle, path: Path) -> Path | None`
  (`_dark_field(manifest, ...)` becomes a `DarkGrid` argument, so letters
  never sees a manifest).
- Tests: a plate from three marks on a 64 by 48 canvas is written and has
  non-zero alpha only near the marks.
- Commit: `Move the nib and label plate into letters`

#### P4.4 Split the font and the trace (letters)

- Predecessor P4.3. Pure moves plus lint fixes (24 findings).
- Owner files: delete `src/pyntpot/_port/outlinefont.py`; create
  `letters/font.py` (`_Flatten`, `Glyph`, `OutlineFont`, `load`,
  `DEFAULT_FONT`), `letters/skeleton.py` (`_fill`, `thin`, `_ring`,
  `_crossings`, `_chains`, `_prune`, `_components`), `letters/trace.py`
  (`_half_width`, `_radii`, `_edge`, `_flank`, `_flanks`, `_from`,
  `_leaving`, `_dots`, `_centrelines`, `_extend`, `CENTRELINE`, `OUTLINE`);
  `git mv src/pyntpot/_port/fonts src/pyntpot/letters/fonts` and resolve
  `DEFAULT_FONT` through `importlib.resources.files("pyntpot.letters")`;
  `tests/unit/letters/test_font.py`, `test_trace.py`; `GLOSSARY.md` rows for
  hand and trace; `line_budget.txt` loses `_port/outlinefont.py`.
- `outlinefont -> paint.edt` becomes `letters.trace -> pyntpot._port.paint.edt`
  until P4.5 moves `edt`.
- Commit: `Split the outline font into letters modules`

#### P4.5 Ink engine, part 1: noise, sheet, raster, wash, pigment (A1)

- Implements A1 (engine half); predecessor P4.4.
- Owner files: create `ink/noise.py` (`value_noise`, `fbm`,
  `_value_noise_at`, `fbm_aniso`, `_box1`, `blur`, `edt`, `smoothstep`,
  `fill_holes`), `ink/sheet.py` (`Sheet`, `Canvas` renamed from `Plate`,
  `rgb`, `PAPER`), `ink/raster.py` (`fill_cov`, `stroke_mask`, `_edge`,
  `deform_ring`, `deform_rings`), `ink/io.py` (`to_img`, `save_webp`,
  `save_alpha`, `save_rgba`), `ink/wash.py` (`flow_edge`, `bloom`, `wash`,
  `separated`, `shallow_water`, `fluid_modulate`), `ink/pigment.py`
  (`PIGMENTS`, `TRANSPARENCY`, `multiply_plate`, `km_rt`, `km_plate`,
  `composite`); their tests under `tests/unit/ink/`; edit `_port/paint.py`,
  every importer, `GLOSSARY.md` (sheet, canvas rows).
- Engine functions that took `PaintStyle` take the ink style group they read
  (`WashStyle`, `PaperStyle`); the adapter in `Style.paint_style()` stays for
  the rest of `_port`.
- Commit: `Move noise, sheet, wash and pigment into ink`

#### P4.6 Ink engine, part 2: brush, stamp, pad (A1)

- Predecessor P4.5.
- Owner files: create `ink/brush.py` (`Brush`, `brush_from_id`,
  `scaled_brush`, `ink_aux`), `ink/tip.py` (`_tip_band`, `_tip_drift`,
  `_unfold`, `_fbm1`, `_spread`, `_smooth_path`), `ink/stamp.py` (`stamp`,
  decomposed into named steps to meet the complexity limits, 280 lines
  today), `ink/pad.py` (`InkPad`, `ink_density`, `_bleed`, `_grow`,
  `_reduce`); tests; edit `_port/paint.py`, importers, `GLOSSARY.md` (brush).
- `BRUSH_TREATMENTS` and `BRUSH_COLOURS` are keyed by map feature class: they
  stay in `_port/paint.py` for P4.7 to take to maps; brush ids in `ink` lose
  their class prefixes only if `brush_from_id`'s parsing allows without a
  pixel change, otherwise the class-to-id table moves to maps (A1).
- Commit: `Move the brush, stamp and ink pad into ink`

#### P4.7 Plate painter in maps; no clock reads (A1)

- Implements A1 (maps half); predecessor P4.6.
- Owner files: create `maps/painter/__init__.py`, `maps/painter/plates.py`
  (`paint_plates(basemap, style, out_dir) -> Plates`, the old `paint` split
  at its seven timing points into `_water`, `_cover`, `_wood`, `_relief`,
  `_fluid`, `_ink`, `_ribbon`), `maps/painter/brushes.py`
  (`plate_brushes`, `BRUSH_TREATMENTS`, `BRUSH_COLOURS`, `COVER_CFG`,
  `PEN_ROWS`), `maps/painter/ribbon.py` (`ribbon_alpha`, `coast_run`,
  `sea_patches`, `_crossfade`), `maps/painter/paper.py` (`paper_plate`,
  `relief_density`); tests; delete `_port/paint.py` and its exemption lines.
- The nine `time.perf_counter` reads (`paint.py` lines about 3674 to 4103)
  are deleted and the manifest's `timing` key dropped (ADR 0003 decided it);
  P5 benchmarks measure time instead. `Manifest.timing` is removed.
- Commit: `Move plate assembly to maps and drop the painter's clock reads`
- Done when: `test_reads_no_time_module` passes with `_port/paint.py` gone.

#### P4.8 Style groups replace PaintStyle (A6)

- Implements A6; predecessor P4.7.
- Owner files: every reader of `PaintStyle` or `GeoOptions`; delete
  `PaintStyle`, `GeoOptions`, both `from_style` and `from_resolved`,
  `with_display`, `coerce_like`, `Style.paint_style()`; `maps/style.py`.
- Readers take their group; `getattr(pstyle, ...)` with silent defaults
  disappears (6 sites in `labels.py`). The pinned digests from P3.11 must not
  change.
- Commit: `Read style groups directly and delete the flat paint style`

#### P4.9 Design the candidates facility; delete dead code (A8, design)

- Implements A8 (design), D27; predecessor P4.8.
- Owner files: `docs/decisions/0009-candidates.md`, `GLOSSARY.md` (add
  **candidate**); delete `mapcard.alphabet_sheet` and `ALPHABET_*` (no
  caller; P7 may add a specimen later through the public API),
  `mapcard.sport_from_gpx`; the three label shims went in P3.17 and
  `with_display` in P4.8: confirm with `grep`.
- Task: draft two shapes, pick one, record why. Starting points:
  - Shape 1, ranking functions: `rank_roads(basemap, track) -> list[Candidate]`,
    `rank_climbs(track) -> list[Candidate]`,
    `rank_places(basemap, track) -> list[Candidate]`,
    `rank_landmarks(basemap) -> list[Candidate]` over one
    `Candidate(kind, name, score, at_m, where: Pt, detail: Mapping[str, Any])`.
    For: flat, each function testable alone. Against: callers merge and
    re-rank by hand.
  - Shape 2, one value with queries: `Candidates.for_track(track, basemap) -> Candidates`
    with `top(kind=None, n=8)` and `along(start_m, end_m)`; the rankers are
    private. For: one entry point for "which span to name, which road to
    number, what to letter first". Against: computes every kind even when a
    caller wants one.
  - Pick by: today's real caller (`journal_candidates` feeds
    `manifest.candidates`, read by `journal_picks`, `journal_heuristic` and
    `settlements`) is served without the manifest; no Protocol (rule of
    three); testable on the Lynmouth fixture; parity exact.
- Commit: `Decide the candidates facility and delete dead map code`

#### P4.10 Candidates facility (A8)

- Predecessor P4.9.
- Owner files: create `maps/candidates/` (modules for roads, climbs, places,
  landmarks, under 400 lines each) from `geo.journal_candidates`,
  `landmark_export`, `climbs`, `_felt_span`, `_steepest`, `ground_climbs`,
  `route_places`, `_place_view`, `_near_places`, `road_run`,
  `named_roads`, `_cell_index`, `_point_to_line`, `read_gpx_elevation`
  (replaced by `Track.ele`), `haversine`, `bearing`, `compass`, `COMPASS`,
  `cumulative`, and `classify`, `height_m`, `landmark_reach`,
  `landmark_rank`, `pick_landmarks` with the landmark constants;
  `tests/unit/maps/candidates/`; the tests at `test_paint.py` about lines
  915 to 990 move here.
- Commit: `Generalise map candidates into one facility`

#### P4.11 Split geo, part 1: relief, generalisation, rivers

- Predecessor P4.10.
- Owner files: create `maps/relief.py` (`_png`, `_resample`, `_shade`,
  `hillshade_png`, `marching_squares`, `_stitch`, `_grid_line_to_metres`,
  `_pad`, `shade_bands`, `contour_lines`, `sea_rings`, `_ring_is_wet`,
  `Field`, `_jitter`, `hachures`, `wave_strokes`; split into
  `relief.py` and `relief_strokes.py` at 400), `maps/generalise.py`
  (`_fill_ring`, `rasterise`, `_spread`, `_components`, `declutter`,
  `trace_mask`, `generalise`, `jitter_ring`, `scatter`, `generalise_layer`),
  `maps/rivers.py` (`channel` and its helpers, `measured_width_m`,
  `painted_width_px`, `major_rivers`); tests.
- Commit: `Move relief, generalisation and river width out of geo`

#### P4.12 Split geo, part 2: OSM layers, cover, assembly

- Predecessor P4.11.
- Owner files: create `maps/osm.py` (`_osm_layers`, 241 lines today,
  decomposed per layer; `_geom`, `_polygon_rings`, `_dedupe`,
  `TrackIndex`, `_densify`), `maps/cover.py` (`LANDCOVER_*`, `COVER_TAGS`,
  `COVER_ORDER`, `cover_rings`, `wood_rings`, `coastline_chains`,
  `sea_from_coast`), `maps/layers.py` (`journal_geometry`, `journal_layers`
  renamed `build_basemap`, `basemap`, `_derived`, `scale_for`,
  `_place_marks`, `_relief_layers`, `_soften`, `_sea_path`), `maps/rings.py`
  (`signed_area`, `orient`, `point_in_ring`, `clip_ring`); move
  `OVERPASS_QUERY`, the road and landmark tag lists and `fetch_*` query
  formatting into `maps/providers/overpass.py`; delete the old `fetch_*`,
  `_get`, `read_gpx`, `fetch_activity` (replaced by providers, `Track` and
  `Cache`); delete `_port/geo.py`.
- Commit: `Split geo into map layer modules and delete it`

#### P4.13 One cache for fetches and plates (A7)

- Implements A7, D9; predecessor P4.12.
- Owner files: `maps/cache.py`, `maps/painter/plates.py`,
  `_port/labels.py` (`plate_key`, `draw_plate`), tests.
- `Cache` gains `plates_dir`, `load_plates`, `base_key(basemap, style)` (the
  P3.12 form, so the manifest hash does not move) and
  `lettering_key(settings, style)` derived from the settings and
  `style.lettering_digest()` with no field list; `labels_hash`,
  `plate_key` and the 27-name key list are deleted. A lettering-only style
  change no longer repaints base plates (test: change a `HandStyle` field,
  `paint` reports no repaint).
- Commit: `Key plate caches by what was painted`

#### P4.14 Split labels, part 1: placement

- Predecessor P4.13.
- Owner files: create `maps/lettering/__init__.py`, `maps/lettering/label.py`
  (`Label`, `Span`, tiers, `wrap_forms`, `block_size`),
  `maps/lettering/placement.py` (`place`, `_place`, seat and pair costs,
  `_uncross_leaders`), `maps/lettering/placement_costs.py` (`_crossings`,
  `_on_road`, `_seg_in_box`, `_overlap`, `_separation`, `_darkness`,
  `_on_paper`, own-feature and near-route costs),
  `maps/lettering/placement_along.py` (`_place_along`, `_place_flat`,
  `_best_flat`, `_curved_boxes`, lift helpers, `_tilt`), with the placement
  constants beside their readers; tests. `maps/lettering.py` from P3.17
  becomes `maps/lettering/pipeline.py`.
- Commit: `Move label placement into maps lettering`

#### P4.15 Split labels, part 2: spans

- Predecessor P4.14.
- Owner files: `maps/lettering/spans.py` (`resolve_spans`, `_span_index`,
  `place_spans`, `span_bearing`, `_drawn_side`, `_rung`, costs),
  `maps/lettering/span_sides.py` (`route_turn`, `bend_strength`,
  `_outward`, `_convex_side`, `_curved_side`, `_freer_side`),
  `maps/lettering/span_line.py` (`span_line`, `shape_curve`, `_corners_of`,
  `_turn_over`, folds, loops, `doubling_px`, `_mouth_path`),
  `maps/lettering/span_clear.py` (`clear_of_route`, `_route_near`,
  `_clear_of`, `_longest_clear`, `_span_ticks`, `_span_label`); tests.
- Commit: `Move span lettering into maps lettering`

#### P4.16 Split labels, part 3: picks, compose, card; delete the old modules (A3)

- Implements A3 (file split); predecessor P4.15.
- Owner files: `maps/lettering/picks.py` (`settlements`, `pick_settlements`,
  `dedupe_names`, `pick_rivers`, `pick_roads`, `road_ref`, `route_markers`,
  `home_places`, `home_labels`, `ground_labels`, `journal_picks`,
  `journal_heuristic`, renamed to say what they pick), `maps/compose.py`
  (`_plates`, `_route`, `_paste_labels`, raster compose), `maps/strands.py`
  (`separate_strands` and constants from `_port/card.py`), `RouteInk` and
  the route constants into `maps/style_groups.py`; delete
  `_port/labels.py`, `_port/mapcard.py`, `_port/card.py`,
  `_port/style.py`, the emptied `tests/unit/test_paint.py` and
  `tests/unit/test_geo.py`, their per-file-ignores, `ty` excludes and
  exemption lines.
- Commit: `Move picking and compose into maps and delete the port modules`

#### P4.17 Layers contract; delete `_port`

- Implements D2, D5 end state; predecessor P4.16.
- Owner files: `pyproject.toml` (`[[tool.importlinter.contracts]]` layers
  `pyntpot.maps`, `pyntpot.letters`, `pyntpot.ink`; a forbidden contract:
  `pyntpot.ink` and `pyntpot.letters` may not import `httpx` or
  `pydantic`; the `src/pyntpot/_port/*` per-file-ignores and the `_port`
  `ty` exclude removed); delete `src/pyntpot/_port/`; empty
  `tests/architecture/exemptions/line_budget.txt`, `gates_off.txt` and
  `NOTES.md` to their header comment only; `docs/decisions/0010-layers-contract.md`;
  `BOUNDARIES.md`, `docs/architecture.md`, the boundary paragraph of
  `CLAUDE.md`, `GLOSSARY.md` "Today" columns.
- Tests: `uv run lint-imports` passes both contracts; `test_import_order.py`
  lists the final modules.
- Commit: `Add the layers contract and delete the port package`

#### P4.18 Relax the parity pins

- Implements D22; predecessor P4.17.
- Owner files: `pyproject.toml` (`numpy>=2.5.2`, `pillow>=12.3.0`,
  `fonttools>=4.63.0`), `uv.lock`, `CONTRIBUTING.md` (the pin sentence),
  `.github/dependabot.yml` (drop the three ignores).
- One commit. G-here plus G-self with the relaxed lock (`uv lock` must keep
  the same resolved versions so parity is untouched); G-exact on the
  maintainer's machine.
- Commit: `Relax the parity pins to floors`

### P5. Property tests, coverage baseline, mutation, benchmarks

- Property tests (`hypothesis`, `hypothesis.extra.numpy`): projection
  round-trip, `simplify` idempotence and endpoint preservation, `clip_ring`
  stays within the box, `edt` equals brute force on small masks, `blur`
  preserves mass, `stamp` deterministic for a seed, pigment compositing in
  [0, 1], `Hand` output identical for identical input.
- Coverage: measure branch coverage on `ink` and `letters`, set
  `fail_under` to the measured figure rounded down, record in an ADR with
  the intent to ratchet.
- mutmut: PR job with git change detection; nightly full run uploading
  results; a script fails the nightly below the score set in the ADR
  after the first full run. Golden tests are excluded (P0.9).
- Benchmarks in `tests/benchmarks/`: sheet construction, `edt`, one
  `stamp` of a 2000-point path, `wash`, `paint` at `display_px=450`, full
  `compose`. `pytest-benchmark` locally; `codspeed.yml` runs them with
  the CodSpeed action on PRs. Baselines recorded in
  `docs/explanation/performance.md`.

### P6. Docstrings, prose and references (D24, D25)

1. **References inventory.** A read-only agent lists every technique the
   code implements by name or by recognisable algorithm, with
   `file:line` (against the upstream source commit): Kubelka-Munk glazing
   (`paint.py:39, 71`), Zhang-Suen thinning (`outlinefont.py:262`),
   marching squares (`geo.py:1113`), Lanczos reduction (`paint.py:2606`),
   fractional Brownian motion and value noise (`paint.py:755-868`),
   Euclidean distance transform (`paint.py:892`), hillshade and hachures
   (`geo.py` 2314 onward), Douglas-Peucker style simplification, label
   placement rules (clearance, set-along-a-line, one name a place),
   watercolour wash effects (edge darkening, granulation, bloom,
   backruns), brush and nib stroke models, Chaikin corner cutting
   (`geo.py`, the drawn road and river lines), Catmull-Rom splines (span
   marks), WCAG relative-luminance contrast (route and river-name inks,
   applied from memory). Today none of these carries a citation; the
   five modules contain no paper, blog or DOI reference.
2. **Recover the design inputs.** The papers and blogs read while
   designing the map rules are not recorded in the source tree. Recover
   them from whatever record exists (see the open question in `spec.md`)
   and match them to the inventory. Done 2026-10-04: the recovered list
   is `design-sources.md` in this directory. Two of the three design
   conversations read nothing external; the third read the papers and
   pages listed there. Every entry is unverified until step 3.
3. **Verify and write `docs/explanation/references.md`**: one entry per
   technique with the canonical source (author, year, title, DOI or URL),
   verified live, plus the design-input source where one was recovered.
   Each implementing docstring gains one line naming the entry's key.
   Where a design input cannot be recovered, the entry says "canonical
   source; original design reading not recorded".
4. **Docstring pass.** Run a docstring audit across `src/pyntpot` with the
   repo's Google convention, one session per subpackage. Public API
   first. The pass fixes accuracy and shape; it does not add caller
   obligations or narration. Parity exact after each session.
5. **Prose pass.** Run a prose audit over docstrings, comments,
   `README.md`, `docs/`, `GLOSSARY.md` and `CHANGELOG.md`.
   Behaviour-neutral by construction; parity exact after.

Gate: full gate green, parity exact, `references.md` has an entry for
every inventory item.

### P7. Docs and first release

- README: what it is, a route map image, a non-map image (a lettered word
  on a washed circle from `examples/word.py`), install, three-line quick
  start, data policy, attribution requirement, licence, and a pointer to
  `references.md`.
- `docs/tutorials/first-map.md`; `docs/how-to/{self-host-providers,
  write-a-theme,use-the-engine-without-maps}.md`; `docs/reference/`
  (public API, style fields, CLI, cache layout, manifest format);
  `docs/explanation/{how-the-wash-works,data-policy,performance,references}.md`.
- ADRs for D2, D5, D7, D8, D9, D20, D21, D23, D24, the coverage
  baseline, the mutation threshold, the golden regeneration.
- `CHANGELOG.md` 0.1.0. Configure the PyPI trusted publisher (manual,
  documented in CONTRIBUTING). Confirm with the maintainer before the tag
  and the publish.

### P8. The upstream consumer migrates to the public API

The upstream training-analysis repo records a reference render with the old
code, adds `pyntpot` as a dependency (git tag until PyPI), migrates its
cache to the new keys, replaces its local copies of the engine and their
tests with calls to the public API (`Basemap`, `Plates`, `Lettering`, D21),
and updates its documentation. Verification: the same activity rendered
through `pyntpot` with `attribution=False` produces a PNG with the recorded
hash, before anything is deleted. This phase touches only the upstream repo.

### P9. Post-port cleanup

Scaffolding the port needed and the finished port does not. Every slice here
deletes or simplifies; none adds behaviour. The slice rules and gate commands
are those of "P3 and P4: how to run a slice" (test first where a test
changes, no shims, G-here, commit message imperative on one line with no
trailers, tick `tasks.md` in the same commit). Nothing here removes a gate
that `CLAUDE.md` requires, touches the tolerance bound
(`MAX_DIFFERING_FRACTION`, `MAX_CHANNEL_DELTA`) or the D22 pin handling, or
edits a Key decisions row beyond the one appended note named in P9.1.

**Precondition for the whole phase.** P4.18, P7.4 and P8 are done and ticked,
and the maintainer has confirmed the release (P7.4 already requires that
confirmation). The order is P9.1, P9.2, P9.3, P9.4. P9.1 and P9.2 both edit
`tests/architecture/_text_scan.py`, `tests/conftest.py` and `BOUNDARIES.md`,
so they never run in parallel; P9.3 and P9.4 touch disjoint files and may run
in parallel with each other after P9.2.

**ADR numbers.** P3 and P4 pre-assign 0003 to 0010. P5.2, P5.3 and P7.3 also
write ADRs but assign no numbers, so by P9 `0011` will be taken. Before
writing, run `ls docs/decisions` and take the next free number: P9.1 takes it
(this plan calls it NNNN; 0011 if nothing else has landed) and P9.2 takes the
one after (MMMM).

#### P9.1 Retire the banned-term test

- Implements D16 (retires one of its enforcement mechanisms); predecessors
  P7.4 and P8.
- Dependencies found. Nothing in P3 to P8 needs the test to exist after P2.9,
  but three steps run it and must be finished first. P2.9 and the
  remote-history check use the private list; P3.12 adds one `re:` entry to
  it and P3.15 runs the test over the regenerated `plates.json`; the spec's
  Verification step 3 ("the banned-term, coordinate and remote-history scans
  return nothing") is satisfied at the P7.4 release. P7.1 to P7.3 add the
  README, `docs/` and ADRs, which the scan covers, so the retiring slice runs
  the test once more, on the maintainer's machine where the list exists, and
  records "green" in its hand-off. The test skips in public CI and in this
  environment (the `1 skipped` in G-here), so the gates here never relied on
  it.
- Owner files: delete `tests/architecture/test_no_personal_content.py`; edit
  `pyproject.toml` (remove `personal_terms_file` from
  `[tool.pytest.ini_options]`), `tests/conftest.py` (remove the
  `parser.addini("personal_terms_file", ...)` call; the
  `--golden-tolerance` and `--golden-dir` options stay),
  `tests/architecture/_text_scan.py` (module docstring says "banned terms,
  coordinates"; it becomes "coordinates"; `test_coordinates.py` stays its only
  caller), `BOUNDARIES.md` (the "No personal content" bullet keeps only the
  coordinate allowlist), `specs/001-port/spec.md` (append to the end of the
  D16 row only: ` Retired after the port by P9.1, ADR NNNN.`; no other word
  of the row or the table changes), create
  `docs/decisions/NNNN-retire-banned-term-test.md`. Leave alone:
  `tests/architecture/test_coordinates.py` (D10 allowlist, stays),
  `CLAUDE.md`, `CONTRIBUTING.md`, `docs/architecture.md` (none mentions the
  test or the option; confirm with the grep below), ADR 0002 (append-only; its
  sentence listing "the banned-term scan" stays true as history and the new
  ADR amends it), and plan.md P0 to P8 text.
- ADR NNNN: `# NNNN — Retire the banned-term test`, `Status: accepted`,
  `## Context` (D16 asked for a banned-term test, a manual pass and a history
  scan while the port carried personal content; the list is personal and never
  in the repository, so public CI always skipped the test), `## Decision`
  (delete the test and the `personal_terms_file` option; the list outside the
  repository stays the maintainer's to keep or delete; the D10 coordinate
  allowlist remains as the standing guard), `## Consequences` (a new
  contribution is not scanned for terms; review and the coordinate test carry
  that; G-here no longer reports a skip; the amendment to ADR 0002 is stated).
  Heading shape as `0002-hexagonal-layers.md`.
- Tests: no new test. The safety proof is that the suite still collects under
  `--strict-config` with the option gone, `uv run pytest
  tests/architecture` passes with no skips, and
  `grep -rnE "personal_terms|test_no_personal_content|banned_terms\.txt" --exclude-dir=.git --exclude-dir=.venv .`
  matches only `spec.md` (D16 and Verification), `plan.md`, ADR 0002 and ADR
  NNNN.
- Gate: G-here.
- Commit: `Retire the banned-term test and its pytest option`

#### P9.2 Retire the exemptions mechanism

- Implements the end state of D5's interim relaxation; predecessor P9.1
  (shared files), which itself follows P4.17.
- Why it is dead. P4.17 deletes `_port`, removes its per-file-ignores and `ty`
  exclude, and reduces `tests/architecture/exemptions/line_budget.txt`,
  `gates_off.txt` and `NOTES.md` to a header comment. P2 already removed the
  two entries from `gates_off.txt`, and nothing is added to it afterwards.
  What is left is code that reads empty files. The 400-line test and the
  clock and random bans stay; they simply run with no exceptions.
- Owner files: delete `tests/architecture/exemptions/` (all three files) and
  `tests/support/exemptions.py`; edit `tests/conftest.py` (remove
  `pytest_collection_modifyitems`, its `read_exemption_lines` import and the
  module docstring clause about the gates-off hook),
  `tests/architecture/test_boundaries.py` (`test_no_oversized_files` scans
  `src/` with no skip list), `tests/architecture/test_purity.py` (the clock
  and random bans apply to all of `src/pyntpot`), `tests/architecture/_text_scan.py`
  (drop the `EXEMPTIONS_DIR` import and the `EXEMPTIONS_DIR in path.parents`
  test), and their docstrings that mention the exemptions files; `CLAUDE.md`
  (the toolchain paragraph that calls the exemptions directory "the one
  sanctioned relaxation" and the line-budget bullet's last sentence, "Files in
  `exemptions/line_budget.txt` are exempt until they are split", are deleted;
  the rule that a red gate is fixed in code, never loosened, stays in full),
  `BOUNDARIES.md` (the two "exempt until they are split" clauses),
  `docs/architecture.md` (the `## Exemptions` section), `GLOSSARY.md` if it
  defines an exemption term; create
  `docs/decisions/MMMM-retire-exemptions.md` (Status accepted; context: the
  mechanism existed for `_port` only; decision: no relaxation mechanism
  remains, a future over-budget file is split, not listed; consequences: the
  budget and purity tests have no escape hatch). Leave alone: the 400-line
  limit, the clock and random bans, `test_docstring_conventions.py`,
  `test_testing_discipline.py` and every other gate.
- Tests: `uv run pytest tests/architecture` passes; `grep -rn "exemption"
  --include=*.py --include=*.md --include=*.toml --exclude-dir=.git
  --exclude-dir=.venv .` finds only the two ADRs, `spec.md`, `plan.md` and
  `tasks.md`; `test_no_oversized_files` and the purity tests still fail on a
  scratch 401-line file and a scratch `time.time()` call (run by hand, not
  committed), showing the gates were not weakened.
- Gate: G-here.
- Commit: `Retire the exemptions mechanism now that the port is split`

#### P9.3 Drop the historical golden script and the last `ty` exclude

- Implements nothing new; predecessors P9.2 and P8.
- Why it is dead. `tests/golden/make_golden_old.py` imports the pre-port
  package from the originating project, is documented as historical, and is
  the only entry left in `[tool.ty.src] exclude` after P4.16 and P4.17 remove
  the `_port` and ported-test entries. The goldens were regenerated once in
  P3.15 by `tests/golden/make_golden.py` and ADR 0006 records the old and new
  hashes, and P8 has reproduced the recorded render through the public API,
  so the script's provenance role is finished.
- Owner files: delete `tests/golden/make_golden_old.py`; edit `pyproject.toml`
  (remove `exclude` and its two comment lines from `[tool.ty.src]`, so `ty`
  checks all of `src` and `tests`; remove any `_port` per-file-ignore, ty
  exclude or comment P4.16 and P4.17 left behind, including the "Interim"
  comments). Leave alone: `tests/golden/make_golden.py`, `test_parity.py`,
  `tests/support/golden.py`, the `--golden-dir` and `--golden-tolerance`
  options and the bound constants (G-self stays available for future
  refactors), `uv.lock` and the D22 floors.
- Tests: `uv run ty check` is green with no `exclude`;
  `grep -rn "make_golden_old\|_port" pyproject.toml tests docs *.md` returns
  nothing outside ADRs and `specs/`; the golden tests are unchanged and pass.
- Gate: G-here.
- Commit: `Delete the historical golden script and the last ty exclude`

#### P9.4 Fold the design sources into the references

- Implements D24 and D25's end state; predecessors P6.3 and P9.2 (an
  ordering choice; the files are disjoint from P9.3).
- Why it is dead. `specs/001-port/design-sources.md` is a working list whose
  header says every entry stays unverified until P6.3 writes
  `docs/explanation/references.md`; P6.3 gives each technique its canonical
  source plus the recovered design input, or the line "canonical source;
  original design reading not recorded".
- Owner files: delete `specs/001-port/design-sources.md`. Leave alone every
  mention of it in `plan.md`, `tasks.md` and `spec.md` (they are the history of
  how the references were recovered), and `references.md` itself.
- Tests: before deleting, a scripted check that every URL in
  `design-sources.md` appears in `references.md`:
  `grep -oE 'https?://[^ )]+' specs/001-port/design-sources.md | while read -r u; do grep -qF "$u" docs/explanation/references.md || echo "missing $u"; done`
  prints nothing; any entry it names is added to `references.md` as "cited in
  design, not verified" in the same commit. The coordinate test and G-here
  still pass.
- Gate: G-here.
- Commit: `Delete the design sources list now folded into the references`

## Known facts

- Overpass mirror `overpass.openstreetmap.ru` is retired (502);
  `overpass.kumi.systems` is now `overpass.private.coffee`;
  `lz4.overpass-api.de` redirects. Do not carry the old list over.
- Overpass "regular use" is under 100 queries and 10 MB a day, one at a
  time. OpenTopoData public API: 100 locations per call, 1 call per
  second, 1000 calls per day. One fetch is 2 Overpass queries and 64
  OpenTopoData calls.
- A rendered map is an ODbL "produced work" and needs the OSM credit and
  copyright URL. A committed cache of OSM data is a derivative database;
  the fixture README carries the ODbL notice.
- `mutmut` needs `fork`; no native Windows. `uv_build` cannot derive a
  version from git tags.
- Paint takes about 30 s per box at display 900 on the reference machine;
  the golden test is the slowest test and runs in its own CI workflow.
- The lazy import graph is cyclic across the future layers:
  `paint -> geo` at `paint.py` 3100, 3142, 3727; `labels -> paint, geo, outlinefont`;
  `outlinefont -> paint.edt`; `mapcard -> charts`. Hence `_port` first.
- The ported code trips about 430 ruff errors, 59 ty diagnostics and nine
  clock reads under the template's rules. Hence the exemptions files.
- The five modules contain no citations. "et al" greps match "set along";
  do not mistake that for a reference.
