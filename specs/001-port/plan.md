# 001-port: plan

How the port is built. What and why are in `spec.md`; the sequence is in
`tasks.md`. Upstream source commit ecfa41d.

## Files and boundaries

Tree after P1 (the `_port` layout), with each module's P3 and P4 homes in
brackets:

```
pyproject.toml            uv_build, src layout, MIT, >=3.13, pins per D22 (floors at P4.20)
LICENSE  LICENSE-FONT  README.md  CHANGELOG.md  CONTRIBUTING.md  SECURITY.md
GLOSSARY.md  BOUNDARIES.md  CLAUDE.md  (AGENTS.md symlink)
.github/workflows/ci.yml  golden.yml  publish.yml  codspeed.yml  mutation-nightly.yml
.github/dependabot.yml  CODEOWNERS  pull_request_template.md
.pre-commit-config.yaml
src/pyntpot/__init__.py  py.typed
src/pyntpot/_port/__init__.py                                    (deleted at P4.19)
src/pyntpot/_port/paint.py        [-> ink/{polyline,chains}.py (P3.3) + ink/{noise,sheet,raster,io,wash,pigment}.py (P4.2) + ink/{brush,tip,stamp,pad}.py incl. the brush-sheet tables (P4.3) + letters/nib.py (P4.6) + maps/cache.py plate cache (P4.7) + maps/painter/{job,brushes,water,cover,wood}.py (P4.8) + maps/painter/{relief,fluid,pen,ribbon,paper,plates}.py (P4.9); PaintStyle deleted at P4.11 with the file]
src/pyntpot/_port/outlinefont.py  [-> letters/{font,skeleton,trace}.py (P4.4)]
src/pyntpot/_port/labels.py       [-> ink/polyline.py (P3.3) + tests/support/measure.py flat_measure (P3.17) + letters/setting.py Mark, DEFAULT_LINE_PX (P4.1) + letters/hand.py + maps/lettering_marks.py (P4.5) + maps/lettering/{label,span_clear,span_line,span_sides,spans}.py (P4.16) + maps/lettering/{placement_costs,placement_along,placement}.py (P4.17) + maps/lettering/picks.py (P4.18)]
src/pyntpot/_port/geo.py          [-> ink/{polyline,chains}.py (P3.3) + maps/projection.py (P3.4) + query templates copied to maps/providers/overpass.py (P3.8) + maps/candidates/* except landmark_export (P4.13) + maps/{rings,svg_path,track_index,relief,relief_strokes,generalise,rivers}.py (P4.14) + maps/{osm,cover,layers}.py and maps/candidates/export.py landmark_export (P4.15)]
src/pyntpot/_port/mapcard.py      [-> maps/lettering.py (P3.17, -> maps/lettering/pipeline.py at P4.16) + maps/compose.py (P4.18)]
src/pyntpot/_port/card.py         [-> maps/card.py Card frame (P3.2) + ink/polyline.py helpers (P3.3) + maps/strands.py (P4.18)]
src/pyntpot/_port/style.py        [-> maps/style_groups.py (P4.18)]  (RouteInk + constants only)
src/pyntpot/_port/fonts/PatrickHand-Regular.ttf  [-> letters/fonts/ at P4.4]
src/pyntpot/_port/themes/default.json   (resolved default style, D23)  [read by P3.11b's tests, deleted at P3.12; maps/themes/default.toml replaces it]
New in P3 (final homes): ink/{__init__,polyline,chains,style}.py (+ ink/curves.py if polyline passes 400)
  letters/{__init__,style}.py
  maps/{__init__,credit,card,projection,basemap,plates,track,cache,style,style_groups,pipeline,annotations,lettering,attribution,cli}.py
  maps/themes/default.toml   maps/providers/{__init__,base,overpass,opentopodata}.py
New in P4: letters/{setting,hand,nib,font,skeleton,trace}.py  letters/fonts/
  maps/{lettering_marks,compose,strands,osm,cover,layers,rings,svg_path,track_index,relief,relief_strokes,generalise,rivers}.py
  maps/painter/*  maps/candidates/*  maps/lettering/*
tests/support/{paths,golden,manifests,providers,http_server,measure}.py  tests/golden/make_golden.py (run as PYTHONPATH=tests uv run python tests/golden/make_golden.py)
tests/unit/{ink,letters,maps,maps/providers}/  tests/unit/maps/test_import_order.py (import rule, ADAPTERS)
tests/unit/test_geo.py  tests/unit/test_paint.py   (shrink through P4; deleted at P4.15 and P4.18)
tests/golden/test_parity.py  tests/golden/make_golden_old.py (historical; deleted at P9.3)
tests/golden/lynmouth/{paper,wash,pen,labels-centreline}.webp plates.json map.png   (regenerated once at P3.15; labels-centreline.json deleted there)
tests/fixtures/lynmouth/{track.gpx, overpass-lynmouth.json, landcover-lynmouth.json, elevation-lynmouth.json, README.md, style.json}
  (style.json deleted at P3.12; the three payloads renamed to <kind>-<cache key>.json at P3.16; README.md follows both)
tests/architecture/  (template tests, edited per P0.6)
tests/architecture/exemptions/{line_budget.txt, gates_off.txt, NOTES.md}   (only shrink; emptied at P4.19, deleted at P9.2)
docs/{tutorials,how-to,reference,explanation}/  docs/explanation/references.md
docs/decisions/  0001, 0002 exist; 0003 to 0023 are assigned in "ADR numbers" under P3 and P4
specs/001-port/{spec.md,plan.md,tasks.md,architecture.md,design-sources.md}   (design-sources.md deleted at P9.4)
```

Ownership per phase is disjoint: P0 owns scaffolding; P1 owns `src/` and
`tests/` content; P2 owns comment, docstring and test-string text plus the
spec copies; P3 owns the façade modules and the package `__init__` files;
P4 owns the split and the exemptions files; P5 owns `tests/{property,
benchmarks,mutation}`, `tests/support/properties.py`, the mutation and benchmark jobs
and `docs/explanation/performance.md`; P6 owns docstring text,
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
     upstream product names and identifier patterns. The previous label font stack was removed from the code in P3.12; it is not added to the banned-term list.
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
at commit `69d485f`; this section was revised after the plan review of
`294cc69` (8 blockers, 11 majors, 12 minors) and again after the second
review of `33f12be` (4 blockers, 6 majors, 18 minors; the P9.1 finding was
rejected by the maintainer). Measurements quoted for the second revision
were taken at `33f12be`; the third review of `f63bb61` (2 blockers, 2
majors, 13 minors) pinned the style table in P3.11a, moved
`landmark_export` to its own module, and moved the golden harness onto
the façade at P3.16 and P3.17, and its measurements were taken at
`f63bb61`.

**Rules every slice follows.**

- Test first. Every new test has a one-line docstring saying what it proves,
  no mocks (`unittest.mock`/`pytest-mock` are banned; a hand-written class or
  function standing in for a provider is a real object), function-scoped
  fixtures except a module-scoped one for an immutable object, `ids=` on every
  `parametrize`, golden values pinned as literals. Tests use
  `tests/fixtures/lynmouth/` and synthetic coordinates inside 51.19 to 51.26 N,
  3.80 to 3.88 W (D10). Any place name in a test or example comes from the
  `CONTRIBUTING.md` list (D26).
- A unit test that paints or letters the whole Lynmouth fixture (30 to
  75 s; P3.16 to P3.19 add such tests) carries `@pytest.mark.golden`, the
  registered marker for slow parity tests, so `pytest -m "not golden"` and
  the mutation runs stay fast; G-here's golden stage still runs it. Inside
  one test module the painted result (`Basemap`, `Plates`, `Lettering`,
  all immutable) is one module-scoped fixture, the CLAUDE.md exception,
  and is never repainted per test. Its assertions are exact only on
  machine-independent values (the manifest hash, label names, point
  counts); a pixel comparison uses `differing_fraction` and the
  `golden_tolerance` fixture, as `test_parity.py` does.
- New test files mirror the package: `tests/unit/maps/`, `tests/unit/ink/`,
  `tests/unit/letters/`, each a package with `__init__.py`. New test files stay
  under 400 lines even though `test_no_oversized_files` scans `src/` only.
- New modules under `src/pyntpot/{ink,letters,maps}` get no per-file ruff
  ignores and are not excluded from `ty`. Code moved out of `_port` must pass
  the full rule set where it lands: fix the findings, behaviour-neutral, never
  add a `noqa` or an ignore. That includes `PLC0415`: outside `_port` every
  import is at module level, which is why the import rule below exists.
  Measured debt with the `_port` ignores removed: `paint.py` 110 ruff
  findings, `geo.py` 117, `labels.py` 162, `outlinefont.py` 24, `mapcard.py`
  8, `card.py` 5, `style.py` 4 (165 of them `PLR2004`, 14 `C901`, 10
  `PLR0912`, 9 `PLR0915`), plus about 59 `ty` diagnostics across `_port`. A
  function over the complexity or statement limits is decomposed into named
  helpers in the same commit, under parity.
- **Import rule.** P3.1 writes it into `tests/unit/maps/test_import_order.py`
  as an AST check over `src/pyntpot`, so a slice that breaks it goes red:
  1. `ink/*` never imports `pyntpot.letters`, `pyntpot.maps` or
     `pyntpot._port`. `letters/*` imports `ink` and nothing else from
     `pyntpot`. Neither ever imports `_port`, at any level.
  2. A module under `maps/` imports `pyntpot._port` only if it is in the
     pinned `ADAPTERS` tuple in `test_import_order.py`. An adapter imports at
     module level and binds the module (`from pyntpot._port import paint`),
     never a name from it, so a partially initialised `_port` module during a
     cold import is harmless. The one exception is `_port.style`, which
     imports nothing from `pyntpot` and may be imported by name. Adapters, in
     the slice that adds each: `maps/style_groups.py` (P3.11a, `_port.style`),
     `maps/style.py` (P3.11b, `_port.paint`), `maps/pipeline.py` (P3.16),
     `maps/lettering.py` (P3.17; `maps/lettering/pipeline.py` from P4.16),
     `maps/attribution.py` (P3.18, until P4.6 moves the label plate),
     `maps/lettering_marks.py` (P4.5, until P4.16 moves `Label` and `Span`).
     Each later slice that removes a module's last `_port` import also
     removes it from `ADAPTERS`. No slice adds an adapter not named here.
     Every other `maps` module is a leaf with no `_port` import: `credit`,
     `card`, `projection`, `basemap`, `plates`, `track`, `cache`,
     `annotations`, `cli`, `providers/*`, `painter/*`, `candidates/*`
     (including `candidates/export.py`, P4.15), `lettering/*` (except `lettering/pipeline.py`), `rings`, `svg_path`,
     `track_index`, `relief`, `relief_strokes`, `generalise`, `rivers`,
     `osm`, `cover`, `layers`, `compose`, `strands`. The P4 move order is
     bottom-up so that this holds: a slice moves a name out of `_port` only
     together with, or after, every `_port` name it reads (see **Placement
     rule**). A leaf may import an adapter module (for example a lettering
     leaf importing `maps.lettering_marks`); the AST check counts direct
     imports only, and the cold-import test proves the chain.
  3. `_port` may import `pyntpot.ink` and `pyntpot.letters` at module level,
     by name: rule 1 guarantees they never import `_port` or `maps`, so
     nothing re-enters. `_port` imports `pyntpot.maps` (any module under it)
     only inside a function (its existing `PLC0415` ignore permits that) or
     under `if TYPE_CHECKING:` for annotations (every `_port` module already
     has `from __future__ import annotations`). Reason: from P3.16
     `pyntpot.maps.__init__` imports the pipeline, which imports `_port`; a
     module-level `_port -> maps` edge would re-enter a module that is still
     initialising. A `_port` module-level statement that reads a name moving
     to `maps` (a constant built from it, a default argument, a class-body
     default or a `default_factory=lambda`) either moves with that name or
     becomes a named module function that imports it inside its body.
  4. Where the rule and a slice's text disagree, the rule wins; where
     neither can be met without a `noqa`, stop and report.
- **Placement rule** (every slice that moves names, P3.3 to P4.18). The
  slice text names the main names and their destination modules, and, where
  it creates several, their order, lowest first. Every name the slice text
  does not list goes with its only caller; with callers in two or more
  destination modules it goes to the lowest of them. A destination module
  imports only modules below it in that order, modules created by earlier
  slices, and `ink`/`letters`. A listed name that a lower module reads moves
  down to that module, and so does anything it reads, repeated until nothing
  points up. Before moving, compute the assignment with a scratch AST script
  over the `_port` module (top-level names, their readers, the order) and
  confirm that no destination module reads one above it; the hand-off lists
  every name that moved down from its listed home. A name with no caller in
  `src/` but a test caller goes beside its nearest neighbour in source order;
  a name with no caller anywhere is deleted and listed in the hand-off. The
  tables in P4.15 and P4.18 are this rule applied at commit `33f12be`,
  rechecked at `f63bb61` (which moved `_soften` to `osm`, `_crossfade` to
  `painter/wood`, `_quad_at` to `lettering_marks`, `draw_plate` to
  `lettering/pipeline` and `landmark_export` to `candidates/export`).
- **Owner files** implicitly include every module and test that imports,
  calls or reads a name the slice moves, renames or deletes, and every
  document that names a file the slice deletes or renames. The lists below
  name the ones found when this plan was written; a slice that finds
  another edits it and says so in the hand-off. The implementer agent's
  "report, don't make it" clause does not apply to these.
- Module and public docstrings state purpose, key types, non-goals and
  invariants as capability facts; no spec, phase or slice numbers in `src/`
  (enforced). Logging, never `print`. No `os.environ`. `raise ... from exc`.
  `pathlib`. No ABC or Protocol except `Features` and `Elevation`.
- New terms go into `GLOSSARY.md` in the slice that first uses them (card,
  manifest, layers, credit, elevation patch, elevation grid, span request,
  setting, mark, candidate are assigned below). Existing glossary rows that
  say "Today `paint.X`" are updated by the slice that moves `X`.
- Exemptions only shrink. When a `_port` file is deleted, its line leaves
  `tests/architecture/exemptions/line_budget.txt` in the same commit. The
  `src/pyntpot/_port/*` per-file-ignores block and the `_port` `ty` exclude
  are globs and leave with the package at P4.19. Nothing is added to
  `gates_off.txt`.
- ADRs: `docs/decisions/NNNN-kebab-title.md`, heading `# NNNN — Title`, a
  `Status:` line, then `## Context`, `## Decision`, `## Consequences`, as in
  `0002-hexagonal-layers.md`. Numbers are fixed by the table below; before
  writing, `ls docs/decisions` must show the number free, otherwise stop and
  report.
- No re-export shims. When a name moves, every importer (including tests) is
  repointed in the same commit.
- Commit when the slice's gate is green, message as given (imperative, one
  line, no trailers), then tick the slice's line in `tasks.md` in the same
  commit. Out-of-scope findings go to `docs/issues/`, not into the diff.
  **Who does what:** the implementer agent (`plan-slice-implementer`) edits,
  runs the gates and hands off; it never commits or pushes. The
  orchestrating session commits, ticks `tasks.md`, and does every push,
  backup-ref push and ref deletion below. Where a slice says "commit" or
  "push", it means the orchestrating session.
- **Pushing.** Everything lands on `main`. Outside the regeneration window a
  slice pushes `main` when its commit is in. **Inside the window (P3.12 to
  P3.15)** commits are made on local `main` and pushed to `origin/main`
  together only once P3.15 has landed with G-here green. A session that must
  end mid-window pushes its local `main` to the backup ref instead
  (`git push origin HEAD:refs/heads/wip/regeneration-window`) and names the
  last commit in its hand-off; the next session resumes with
  `git fetch origin wip/regeneration-window && git merge --ff-only FETCH_HEAD`
  on local `main`. P3.15 deletes the ref after pushing `main`
  (`git push origin --delete wip/regeneration-window`). CI on that ref is not
  a gate. No parallel slice runs inside the window: P3.2 to P3.11b have all
  landed on `main` before P3.12 starts.

**ADR numbers.** `docs/decisions` holds 0001 (agentic gates) and 0002
(hexagonal layers). Every ADR this plan writes has a fixed number:

| ADR | File stem | Written by |
|---|---|---|
| 0003 | `card-frame-and-typed-seam` | P3.2 |
| 0004 | `providers-and-fetch-cache` | P3.7 |
| 0005 | `style-groups` | P3.11a (table), P3.11b (digests) |
| 0006 | `golden-regeneration` | drafted P3.12, accepted P3.15 |
| 0007 | `public-api` | P3.20 |
| 0008 | `hand-writes-settings` | P4.1 |
| 0009 | `candidates` | P4.12 |
| 0010 | `layers-contract` | P4.19 |
| 0011 | `coverage-baseline` | P5.2 |
| 0012 | `mutation-threshold` | P5.3 |
| 0013 to 0021 | one per settled decision, in this order: D2, D5, D7, D8, D9, D20, D21, D23, D24 | P7.3 |
| 0022 | `retire-banned-term-test` | P9.1 |
| 0023 | `retire-exemptions` | P9.2 |

P7.3's list also names the coverage baseline, the mutation threshold and the
golden regeneration; those are 0011, 0012 and 0006. Where an earlier ADR
already records one of D2 to D24 (0004 covers D8 and D9, 0005 D23, 0007 D7
and D21, 0010 D2), the P7.3 ADR is a short pointer to it, so the numbers stay
fixed.

**Gate commands.** `$SCRATCH` is the session scratchpad directory. `$MG`
stands for `PYTHONPATH=tests uv run python tests/golden/make_golden.py`:
the script imports `support` (and the bound constants from
`golden.test_parity`), which only pytest's `pythonpath` puts on the path, so
this is the one sanctioned invocation and the script never edits `sys.path`.
Write it out in full in commands; it is abbreviated here only.

- **G-here** (this environment, every slice):
  `uv sync && uv run prek run --all-files && uv run pytest -m "not golden" && uv run pytest -m golden --golden-tolerance`.
  At `69d485f` the plain `uv run pytest` is red here only because four golden
  byte-exact cases differ (`paper.webp`, `wash.webp`,
  `labels-centreline.webp`, `map.png`); everything else passes (242 passed,
  1 skipped: `test_no_banned_terms`, private terms file absent), prek is
  green, and tolerance mode passes (6 passed, about 75 s). **From P3.15 on**
  G-here also runs `uv run pytest -m golden` byte-exact, because the
  regenerated goldens were made in this environment. If that exact run fails
  while tolerance mode and G-self pass, the slice still lands, and the
  hand-off reports it as a defect to root-cause (likely platform float
  behaviour) in `docs/issues/golden-exactness.md`. It is never a reason to
  regenerate.
- **G-exact** (the maintainer's machine): `uv sync && uv run prek run --all-files && uv run pytest`.
  Not a slice gate. It is the follow-up check that ADR 0006 records (P3.15);
  no slice claims it.
- **G-self** (from P3.1 on, this environment): before the first edit, on the
  slice's clean starting commit, run `$MG "$SCRATCH/before"`. The script
  writes `baseline.json` there with `{"commit": <git rev-parse HEAD>, "dirty": <bool>}`;
  the hand-off quotes it, and a dirty baseline is invalid. After the change,
  `uv run pytest -m golden --golden-dir="$SCRATCH/before"`. Pass `--golden-dir` with `=`; a space-separated path is read as a test path and the option is never registered.
  This is byte-exact (images and manifest hash) against the same machine's own
  output, so it proves a refactor moved no pixel even where committed goldens
  only hold in tolerance.
- **G-window** (P3.12 to P3.15, once per window step; a step is one commit):
  `uv sync && uv run prek run --all-files && uv run pytest -m "not golden"`,
  then the step compare. The first step's baseline is made on its starting
  commit (`$MG "$SCRATCH/step-0"`); every later step's baseline is the
  previous step's output; a session resuming mid-window remakes it on its
  starting commit, because the scratchpad does not survive sessions. After
  the step's change and before committing it:
  `$MG "$SCRATCH/step-N" --compare "$SCRATCH/step-(N-1)" --compare tests/golden/lynmouth <gate options>`.
  The first compare is the **gate**, and it is enforced by the exit status:
  each step below states its gate options (`--require-identical`,
  `--max-fraction 0.005`, `--require-hash`, `--require-labels-equal`).
  Every output not required identical must have a differing fraction
  (pixels off by more than `MAX_CHANNEL_DELTA`) of at most
  `MAX_DIFFERING_FRACTION` (0.005, passed as `--max-fraction 0.005`) against
  the previous step. From P3.13's second commit on, `labels.txt` (the placed
  label names, in order) must also equal the previous step's
  (`--require-labels-equal`; the first commit writes it for the first time).
  A non-zero exit means **stop**: do not commit, root-cause, and report. A bug must not become
  golden. The second compare (against the committed old goldens) is the
  cumulative record only; it is copied into ADR 0006 with the step's lines.
  Golden-marked tests are not run in the window: the goldens are known stale
  until P3.15.

**Parity rules.** *Exact, current goldens*: G-here plus G-self, before P3.12.
*Inside the regeneration window*: G-window, P3.12 to P3.15, each step bounded
against the previous one. *Exact, regenerated goldens*: G-here (with the
exact run) plus G-self, P3.15 onward. The tolerance bound
(`MAX_DIFFERING_FRACTION = 0.005`, `MAX_CHANNEL_DELTA = 2` in
`tests/golden/test_parity.py`) is never changed. The manifest-hash test is
exact everywhere: before P3.12 its inputs are quantised to 0.1 m, and from
P3.12 the hash input formats every float to three decimals, so a last-ulp
difference between two machines' maths libraries cannot move it.

**What the window freezes.** By the end of P3.15 these are final, and no
later slice may change them; a later slice that would has to stop and report:
the hash input (`Basemap.canonical()`: card plus `Layers`, fixed-precision
floats), the `Layers` and `Card` fields, the manifest keys (P3.13's list), the
style digests (P3.11b's pinned literals), the field-to-group table (ADR 0005), the effective basemap options
(P3.12), and the golden file set (`tests/golden/lynmouth/` holds exactly
`paper.webp`, `wash.webp`, `pen.webp`, `labels-centreline.webp`, `map.png`,
`plates.json`). Golden `plates.json` is compared by its `hash` only. Two
pixel inputs are frozen in form though outside the hash: the drawn route is
`separate_strands(route_px, route_ink().px * STRAND_GAP_WIDTHS)` of the raw
`Card.xy` image of `Basemap.track`, exactly as `mapcard.compose` computes it
today (from P3.16 this is `Plates.strands`, which `compose`, label
placement and the span arc length read from P3.17); and `basemap()`'s vector output keeps
its 0.1 m `path_d` strings, which `journal_layers` parses with
`geo.parse_path`. That quantisation is a permanent property of the vector
map's output, not part of the seam: P4.14 and P4.15 move `path_d` and
`parse_path` verbatim and must not "clean them up". Fields outside the hash
input (`Basemap.places`, `candidates`, `sources`, `credits`, `track_time`;
`Plates.route_px`) and the label-plate sidecar `labels-<route>.json` (a
cache record, not a golden) may change later.

**Order and parallelism.**

```
P3.1 ─┬─ P3.2 ─ P3.3 ─ P3.4 ─ P3.5 ─────────┐
      ├─ P3.6 ─ P3.7 ─┬─ P3.8 ─┐            │
      │               ├─ P3.9 ─┤            ├─ P3.12 ─ P3.13 ─ P3.14 ─ P3.15 ─ P3.16 ─ … ─ P3.21
      │               └─ P3.10 ┘            │      (regeneration window, sequential, see Pushing)
      └─ P3.11a ─ P3.11b ───────────────────┘
P3.21 ─ P4.1 ─ P4.2 ─ … ─ P4.20   (P4 is sequential)
```

Parallel-safe groups (disjoint owner files): {P3.2 to P3.5 in sequence},
{P3.6, then P3.7, then P3.8, P3.9 and P3.10 together}, {P3.11a, then P3.11b}. These three
lines may run at the same time after P3.1. Each parallel line runs in its
own detached `git worktree` (`git worktree add --detach "$SCRATCH/line-N" main`;
no branch is created or pushed), never in a
shared checkout: a shared one would make the line's G-self baseline dirty
and let its G-here see another line's half-made edits. The orchestrating
session lands each slice by rebasing it onto `main` and re-running G-here
there before the fast-forward push, and removes the worktree when the line
is done. Every slice of all three lines
lands before P3.12 opens the window; everything from P3.12 on is sequential.
P3.1 creates every package `__init__.py` and P3.7 creates
`tests/support/http_server.py`, so no two parallel slices create the same
file. Two shared files are append-only for parallel slices: `GLOSSARY.md`
(P3.2 adds card and manifest, P3.4 layers and elevation patch, P3.7 credit
and elevation grid) and the `MODULES` and `ADAPTERS` tuples in
`tests/unit/maps/test_import_order.py`. Each slice appends its own rows; the
second to land rebases over a one-line conflict and changes nothing else.

### P3. Façade, providers, policy, style, CLI

Preceded by D18 (done, P3.0a): the accepted architecture items A1 to A8 are
folded in here and in P4. A4 lands first, then the one regeneration, then the
façade. A3's shape lands with the façade (`letter`); its file split is P4.

#### P3.1 Golden harness and package skeleton

- Implements: tooling for D5 parity; predecessor P3.0. Parallel-safe: no
  (it is the root).
- Owner files: create `tests/support/paths.py`, `tests/support/golden.py`, `tests/golden/make_golden.py`,
  `src/pyntpot/ink/__init__.py`, `src/pyntpot/letters/__init__.py`,
  `src/pyntpot/maps/__init__.py`, `src/pyntpot/maps/providers/__init__.py`,
  `src/pyntpot/maps/credit.py`, `tests/unit/ink/__init__.py`, `tests/unit/letters/__init__.py`,
  `tests/unit/maps/__init__.py`, `tests/unit/maps/providers/__init__.py`,
  `tests/unit/maps/test_import_order.py`; edit `tests/golden/test_parity.py`,
  `tests/conftest.py`, `tests/unit/test_geo.py` and `tests/unit/test_paint.py`
  (their `FIXTURE_KEY` and `FIXTURE_DIR` constants are deleted and every use
  reads `support.paths.KEY` and `FIXTURE_DIR`, so P3.16's rename touches one
  constant). Leave `tests/golden/make_golden_old.py` alone (historical,
  ty-excluded).
- Names: `tests/support/paths.py` imports only `pathlib` (never the
  package, so `tests/conftest.py` can import it without loading `pyntpot`
  in sessions such as the architecture tests): `FIXTURE_DIR: Path`,
  `GOLDEN_DIR: Path` (both absolute, resolved from `__file__`),
  `KEY: str = "lynmouth"`; the only source of the fixture key and
  directories. In `tests/support/golden.py` (imports `paths`):
  `PLATES: tuple[str, ...]` (the four plate names),
  `OUTPUTS: tuple[str, ...]` (`PLATES` plus `"map.png"`),
  `paint_fixture(work: Path) -> dict[str, Path]` (copies the fixture into
  `work`, runs today's `paint.paint_activity` then `mapcard.compose`, exactly
  as `test_parity.py`'s `painted` fixture does now, saves `map.png`, returns
  output name to path), `differing_fraction(got: Path, want: Path, channel_delta: int) -> float`.
  `make_golden.py`: argparse; `OUT` positional; `--compare DIR` repeatable;
  gate options that apply to the **first** `--compare` only and make the
  script exit 1 (after logging every line) when violated:
  `--require-identical NAME [NAME ...]` (outputs that must be byte-identical;
  `all` means the five outputs), `--max-fraction F` (every output not
  required identical has `differing_fraction` at most `F`),
  `--require-hash {equal,differ}` (the manifest hash against the compare
  dir's) and `--require-labels-equal` (`labels.txt` equal; from P3.13). With
  no gate option it only logs and exits 0.
  It paints into a temporary copy, writes the five outputs plus `plates.json`
  into `OUT`, and, when `OUT` is not `GOLDEN_DIR`, also `baseline.json`
  (`{"commit", "dirty"}` from `git rev-parse HEAD` and
  `git status --porcelain`, via `subprocess.run`) and, from P3.13 on,
  `labels.txt`. For each `--compare DIR` it logs (logging, not print) one
  line per output: name, byte-identical yes or no, and
  `differing_fraction(..., MAX_CHANNEL_DELTA)` with the constant imported
  from `golden.test_parity`; then both manifest hashes. In
  `tests/conftest.py`: option `--golden-dir PATH` (default
  `support.paths.GOLDEN_DIR`, absolute, not cwd-relative; `conftest.py`
  imports only `support.paths`, never `support.golden`) and fixture
  `golden_dir(request) -> Path`. `test_parity.py` uses `paint_fixture`,
  `golden_dir` and `differing_fraction`; its bound constants stay exactly as
  they are, in that file. The four package `__init__.py` files under `src/`:
  a module docstring of one sentence naming the layer (ink: "The ink engine:
  paper, washes, brushes and pigment."; letters: "Hand lettering: the face,
  the trace, the hand and the nib."; maps: "Route maps: fetching, painting,
  lettering and composing."; providers: "Feature and elevation data
  providers.") and `__all__: list[str] = []` only. The test-package
  `__init__.py` files are empty. `maps/credit.py`: `Credit(text: str, url: str, short: str)`
  frozen dataclass (`short` is the line drawn on the map) and its module
  docstring, created here because both
  parallel lines need it (P3.4's `Basemap.credits`, P3.7's providers).
- Tests: `tests/unit/maps/test_import_order.py`:
  1. `MODULES: tuple[str, ...]` starts as `pyntpot.ink`, `pyntpot.letters`,
     `pyntpot.maps`, `pyntpot.maps.credit`, `pyntpot._port.paint`, `pyntpot._port.labels`,
     `pyntpot._port.mapcard`, `pyntpot._port.geo`; each is imported in a
     fresh interpreter (`subprocess.run([sys.executable, "-c", f"import {name}"], check=True)`),
     proving no import cycle breaks a cold import. Later slices append their
     modules.
  2. `ADAPTERS: tuple[str, ...] = ()`, appended to by the slices named in
     the import rule.
  3. AST checks of the import rule over `src/pyntpot`: no `ink` or
     `letters` module imports a forbidden package; no `maps` module outside
     `ADAPTERS` imports `pyntpot._port`; adapters bind modules, not names
     (except from `_port.style`); no `_port` module has a module-level
     import of `pyntpot.maps` (or any module under it) outside
     `if TYPE_CHECKING:` (module-level imports of `pyntpot.ink` and
     `pyntpot.letters` are allowed, rule 3).
     Each check is one test with a one-line docstring.
- Parity: exact, current goldens. G-here; then G-self against a baseline made
  with the new script on this commit (the script's first use proves it).
- Commit: `Add a same-machine golden harness and the package skeletons`
- Done when: `uv run pytest -m golden --golden-dir="$SCRATCH/before"` passes
  byte-exact; `--compare` logs six lines; a second run with
  `--compare "$SCRATCH/before" --require-identical all --require-hash equal`
  exits 0, and the same run with `--require-hash differ` exits 1 (the gate
  options work); the `"$SCRATCH/before"` `baseline.json` names the
  starting commit with `"dirty": false`; no test under
  `tests/golden/` imports `_port` except through `tests/support/golden.py`;
  `grep -rn "FIXTURE_KEY" tests` is empty. After committing, the
  orchestrating session (not the implementer, which never commits) runs
  the script once more into `"$SCRATCH/after"` and checks that its
  `baseline.json` names the new P3.1 commit with `"dirty": false`.

#### P3.2 One card frame (A4, part 1)

- Implements A4 (frame), D6, D21; predecessor P3.1.
- Owner files: create `src/pyntpot/maps/card.py`, `tests/unit/maps/test_card.py`,
  `docs/decisions/0003-card-frame-and-typed-seam.md`; edit
  `src/pyntpot/_port/card.py` (delete `_Card`), `src/pyntpot/_port/mapcard.py`
  (construct `Card`, imported inside `compose`), `tests/unit/test_paint.py`
  (the `_Card` import near line 1595; the five local stand-in classes named
  `_Card` near lines 2105, 2588, 3436, 3477 and 3741 are renamed `FlatCard`,
  not replaced: they map without the y-flip a real `Card` applies (`2105`,
  `2588`, `3741`: `(0.1x, 0.1y + 40)`; `3436`, `3477`: identity), so a
  real `Card` would change what those tests assert), `GLOSSARY.md` (add **card**, **manifest**),
  `test_import_order.py` (append `pyntpot.maps.card`).
- Names: `maps/card.py`:
  `@dataclass(frozen=True) class Card` with `box: tuple[float, float, float, float]`
  (card metres x0, y0, x1, y1), `display: tuple[int, int]`,
  `render: tuple[int, int]`, `mpp: float`, `mpp_display: float`,
  `offset: tuple[float, float] = (0.0, 0.0)` (removed in P3.13); properties
  `w`, `h` (display pixels), `scale: float` (display pixels per metre,
  `w / (x1 - x0)`), `render_scale: float` (`render[0] / max(display[0], 1)`);
  no `mppd` (nothing reads `_Card.mppd`; `mpp_display` is the field); methods
  `xy(x: float, y: float) -> tuple[float, float]` (metres to display pixels,
  computed in exactly `_Card.xy`'s operation order:
  `((x + dx - x0) * scale, (y1 - (y + dy)) * scale)`),
  `metres(px: float, py: float) -> tuple[float, float]` (inverse),
  `to_render(x, y)`, and `@classmethod from_manifest(manifest: Mapping[str, Any], offset=(0.0, 0.0)) -> Card`.
  `card.py` is a leaf: it imports nothing from `_port`, and there is no
  `Card.canvas()`; the painter keeps building its `paint.Plate` from the
  card's fields.
- Glossary: **card**: "the coordinate frame of one map: a box in card metres
  and the display and render pixel grids it maps to; converts between them.
  A canvas (today `paint.Plate`) is the raster a plate is painted on; a card
  is the frame that says where things go on it." **manifest**: "the plates'
  sidecar record (`plates.json`): the base hash, the files written and the
  measurements later stages read."
- ADR 0003 (Status: accepted) records A4's whole decision so P3.4, P3.5,
  P3.12 and P3.13 implement it without re-deciding: one card frame;
  `Basemap` and `Plates` typed, geometry as point lists in card metres; the
  projection computed once and carried; `Basemap` carries no cache key (the
  cache owns keys, D9); the base hash covers the card and a typed `Layers`
  value holding exactly what the painter reads, in a canonical form with
  every float at three decimals; `label_geom`, the second path parser and
  the `route0` patch removed inside the regeneration window; the manifest
  keeps only painter outputs and measurements, and its final key set (P3.13)
  is fixed inside the window; golden `plates.json` is compared by `hash`
  only.
- Tests: `test_card.py`, all on a literal manifest mapping written in the
  test (not the golden file): corners of `box` map to `(0, h)`/`(w, 0)`; `xy`
  then `metres` round-trips to within 1e-9; `from_manifest` yields pinned
  `w`, `h`, `scale`; `xy` of three pinned points equals pinned literals
  computed once with the deleted `_Card` before deleting it.
- Parity: exact, current goldens. G-here plus G-self.
- Commit: `Replace the ad hoc card class with one card frame`
- Done when: `grep -rn "_Card" src tests` returns nothing (the test
  stand-ins are `FlatCard`); ADR 0003 exists.

#### P3.3 One polyline module, moves only (A5, part 1)

- Implements A5 (move half); predecessor P3.2.
- Owner files: create `src/pyntpot/ink/polyline.py`, `src/pyntpot/ink/chains.py`,
  `tests/unit/ink/test_polyline.py`, `tests/unit/ink/test_chains.py`; edit
  `_port/geo.py`, `_port/paint.py`, `_port/labels.py`, `_port/card.py`,
  `_port/outlinefont.py`, `_port/mapcard.py` (imports and calls
  `labels.cumulative_m`), the two unit test files (repoint),
  `test_import_order.py` (append the new modules).
- Names: `ink/polyline.py` defines `Pt = tuple[float, float]` (the one
  definition outside `_port`; `maps` and `letters` import it from here).
- Moves (verbatim bodies, public names without the leading underscore where
  another module now imports them): into `ink/polyline.py`: `geo.simplify`,
  `geo.smooth`, `geo.clip_line`, `geo._point_to_seg` (as
  `point_to_segment`), `geo._segments_cross` (`segments_cross`) with the
  helper it calls, `geo._side` (`side`), `geo._normal_at` (`normal_at`),
  `geo._eased` (`eased`), `geo._run` (as `length`) and `labels._run` (as
  `length` too only if the bodies are token-identical, otherwise as
  `length_indexed`, leaving the merge to P3.14), `labels._cum` (as
  `running_length`), `labels.cumulative_m`, `labels._seg_gap` (`seg_gap`),
  `labels._meet` (`meet`), `labels._unit_normal` (`unit_normal`),
  `labels._offset_curve` (`offset_curve`) with the constant it reads,
  `labels.MITER_LIMIT`, `labels._spline` (`spline`), `card._tangent_at`
  (`tangent_at`), `card._ease_along` (`ease_along`), `outlinefont._normals`
  (`normals`), `paint.deform_line`. Into `ink/chains.py`: `geo.join_ways`,
  `geo.join_strokes`, `geo._join_chains` (`join_chains`),
  `paint.chain_lines`, `labels._joined` (`joined`). Before moving, grep each
  moved body for other module-level names it reads and move those with it
  (constants beside their reader). `paint.parse_d` and `geo.parse_path` stay
  where they are (P3.13 deletes `parse_d`; `parse_path` stays in `geo` as
  the reader of `basemap()`'s vector output until P4.14 moves it to
  `maps/svg_path.py`). If `ink/polyline.py` passes 400
  lines, split curves (`spline`, `offset_curve`, `unit_normal`, `meet`,
  `MITER_LIMIT`) into `ink/curves.py`.
- `_port` callers import the moved names from `pyntpot.ink` at module level
  (import rule 3 allows `_port -> ink`). This replaces the `labels -> geo`
  lazy import that borrows `simplify` and the `labels -> paint` one that
  borrows `chain_lines`. List any cross-module lazy import that remains
  between `_port` modules in `docs/issues/port-lazy-imports.md` for the P4
  split.
- Tests: `test_polyline.py`: `simplify` keeps both endpoints and is
  idempotent on a pinned five-point line; `clip_line` of a line crossing a box
  returns the pinned pieces; `length` of a 3-4-5 polyline is 5.0;
  `cumulative_m` and `running_length` pinned on the same line.
  `test_chains.py`: two touching segments join into one; segments beyond
  `tol` stay apart; for `join_strokes` and `chain_lines` a pinned input
  showing where their tolerance handling differs (the evidence P3.14 needs).
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
  `Basemap`), `_port/mapcard.py` (`compose` calls `geo.track_projection`;
  repoint it, imported inside the function by rule 3), `_port/paint.py` (`paint`, `paint_hash`, `label_geom`,
  `paint_activity` read the `Basemap`), `tests/unit/test_paint.py`
  (`tiny_payload` becomes `tiny_basemap`: one definition, used on 11 lines),
  `tests/unit/test_geo.py`, `tests/support/golden.py` only if a signature it
  calls changes, `GLOSSARY.md` (add **layers**, **elevation patch**),
  `test_import_order.py`.
- Names: `maps/projection.py`: `Projection` (moved verbatim from `geo.py`),
  `track_projection(lat, lng, route=None) -> tuple[Projection, list[Pt]]`.
  `maps/basemap.py`: `Line = tuple[Pt, ...]` (`Pt` from `ink.polyline`);
  frozen dataclasses
  `Road(line: Line, cls: str, band: str, highway: str, name: str, ref: str)`
  (today's keys `c`, `b`, `k`, `n`, `r`, `d`),
  `River(line: Line, cls: str, name: str, width_px: float, name_width_px: float, profile: tuple[float, ...] = ())`
  (`c`, `n`, `w`, `wn`, `wp`, `d`),
  `ElevationPatch(n: int, x0: float, y0: float, x1: float, y1: float, values: tuple[float, ...], low: int, high: int)`
  (`elev_grid`; `low` and `high` are ints because today's `min`/`max` are
  `round()` ints, and a float would change the hash JSON),
  `Layers(route: Line, cover: Mapping[str, tuple[Line, ...]], cover_order: tuple[str, ...], lakes: tuple[Line, ...], sea: tuple[Line, ...], coastline: tuple[Line, ...], roads: tuple[Road, ...], rivers: tuple[River, ...], elevation: ElevationPatch | None, ribbon_m: int, wet_px: Mapping[str, float], minor_roads: bool, blotch_m: float, dab_spacing_m: float, gran_m: float)`
  (exactly today's `paint_hash` key list minus the card fields: what the
  painter reads; `ribbon_m`, like `span_m` and `ribbon_fitted_m` below, is
  `int` because `journal_geometry` stores `round(...)` ints, and the
  canonical form writes ints as ints, so the declared type must match), and
  `Basemap(projection: Projection, card: Card, layers: Layers, bounds: tuple[float, float, float, float], span_m: int, ribbon_fitted_m: int, track: Line, track_time: tuple[float, ...] | None = None, places: tuple[Mapping[str, Any], ...] = (), candidates: tuple[Mapping[str, Any], ...] = (), sources: tuple[str, ...] = (), credits: tuple[Credit, ...] = ())`.
  `track` is every track point projected (today `compose` projects the track
  a second time for this; from P3.13 it reads this field), unquantised.
  `track_time` and `credits` stay empty until `fetch` sets them (P3.16);
  `Credit` comes from `maps/credit.py` (P3.1). There is no `key` field: the cache owns keys (D9).
  `Basemap` has this shape from here to the end of the port.
- Parity rule for this slice: every coordinate stored in `Layers` is
  quantised exactly as the path strings did today (`float(f"{v:.1f}")`, the
  `path_d` formatting, and `round(v, 1)` where `journal_layers` used it), so
  painting from the typed fields is byte-identical. `paint_hash` keeps
  today's key list and today's values (build the same dict from the typed
  fields, including path strings via `path_d`) so the manifest hash is
  unchanged. The quantisation and the string form are removed in the window
  (P3.12 and P3.13), not here.
- Glossary: **layers**: "the typed geometry and measurements of a basemap
  that the painter reads; the base hash covers exactly these and the card."
  **elevation patch**: "the elevation samples a basemap carries, placed in
  card metres." (P3.7 adds **elevation grid** for the provider's grid in
  degrees.)
- Tests: `test_basemap.py`: `journal_layers` on a copy of the Lynmouth
  fixture returns a `Basemap` whose road, river and cover counts equal pinned
  literals; every `Road.line` has at least two points; `basemap.track` has
  400 points. `test_projection.py`: projecting the first fixture point gives
  the pinned metres; `inverse` round-trips within 1e-9.
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
  `_port/labels.py` (readers of `manifest[...]` or `manifest.get(`,
  measured at `f63bb61`: `journal_picks`, `journal_heuristic`,
  `settlements`, `pick_rivers`, `pick_roads`, `home_places`, `home_labels`,
  `ground_labels`, `road_lines`, `feature_px`, `draw_plate`; in
  `_port/mapcard.py`: `_plates`, `_route`, `compose`),
  `tests/support/golden.py`, create `tests/support/manifests.py`
  (`manifest_for_test(**over: Any) -> Manifest`: a small valid `Manifest`
  with every field set, overridden by keyword, so the hand-built manifest
  mappings in `tests/unit/test_paint.py`, about 14, at lines near 2096,
  2579, 3293, 3446, 3486 and 3731 among them, become one builder call each
  with the keys they set today), unit tests, `test_import_order.py`. Not converted here: `paint.label_plate` and
  `paint._dark_field` read a manifest mapping (`render`, `display`,
  `gran_px`, `dark`), and `mapcard.alphabet_sheet` hands `label_plate` a
  hand-built mapping; both keep taking a `Mapping[str, Any]` until P4.6
  gives `letters.nib.plate` typed parameters, and `draw_plate` passes
  `manifest.to_dict()`.
- Names: `maps/plates.py`: `DarkGrid(w: int, h: int, values: tuple[tuple[float, ...], ...])`;
  `Manifest` frozen dataclass mirroring today's 24 `plates.json` keys
  (`key` for `id`, `hash`, `route0`, `files`, `sizes`, `bytes`, `card: Card`,
  `span_m`, `ribbon_m`, `places`, `candidates`, `label_geom`, `wet_px`,
  `gran_px`, `labels_hash`, `sources`, `dark: DarkGrid`, `wood_px`,
  `water_px`, `timing`: 20 fields, because `card: Card` stands for five
  keys). `to_json` writes the `Card` as today's five top-level keys in
  today's positions: `card` (the box list), `display`, `render`, `mpp`,
  `mpp_display`, between `bytes` and `ribbon_m`; `Card.offset` is not
  written (it is not in `plates.json` today), and `from_json` rebuilds the
  `Card` from those five. `to_json() -> str` produces the same bytes
  the painter writes today, `to_dict() -> dict[str, Any]`
  (`json.loads(to_json())`, the mapping the label plate reads until P4.6)
  and `from_json(text: str) -> Manifest`;
  `Plates(directory: Path, manifest: Manifest)` with properties
  `paths: Mapping[str, Path]`, `hash: str`, `card: Card`. P3.13 removes the
  keys that are not painter outputs; P3.16 adds `route_px` and `strands`.
- Tests: `test_plates.py`: a small `Manifest` literal built in the test with
  every key, `to_json` then `from_json` round-trips to an equal value and
  `to_json` equals a pinned string (the golden `plates.json` is never read by
  a unit test: its shape changes in the window); `paths` lists `paper`,
  `wash`, `pen`; `load_plates` on a directory missing a plate returns `None`.
- Parity: exact, current goldens. G-here plus G-self.
- Commit: `Read painted plates through a typed manifest`
- Done when: `labels.py` and `mapcard.py` contain no `manifest[` or
  `manifest.get(` reads.

#### P3.6 Track

- Implements D6, D7, D21; predecessor P3.1. Parallel-safe with P3.2 to P3.5
  and P3.11a/P3.11b.
- Owner files: create `src/pyntpot/maps/track.py`,
  `tests/unit/maps/test_track.py`; append `pyntpot.maps.track` to
  `test_import_order.py`'s `MODULES`.
- Names: `BoundingBox(NamedTuple)`: `south`, `west`, `north`, `east` floats.
  `Track(pydantic.BaseModel, frozen=True)`: `lat: tuple[float, ...]`,
  `lng: tuple[float, ...]`, `ele: tuple[float, ...] | None = None`,
  `time: tuple[float, ...] | None = None` (seconds from the first point);
  validators: equal lengths, at least two points, latitudes in [-90, 90].
  No sport field (route ink is fixed in P3, see P3.11a).
  `@classmethod from_gpx(path: Path) -> Track` with `xml.etree.ElementTree`,
  reading only `trkpt` elements (GPX 1.0 and 1.1 namespaces), `<ele>` and
  `<time>` when every point has them (`datetime.fromisoformat`, aware;
  nothing reads the clock). `bounding_box(margin_m: float) -> BoundingBox`
  using `geo.bounding_box`'s arithmetic in the same order (copied, with a
  test that the two agree; `track.py` is a leaf).
- Tests: on `tests/fixtures/lynmouth/track.gpx` (400 `trkpt`, no `<time>`):
  400 points, `time is None`, first point equals the pinned
  `(51.230678, -3.828447)`, and `lat`/`lng` equal `geo.read_gpx`'s lists;
  `bounding_box(1500.0)` equals a pinned tuple and `geo.bounding_box`'s; a
  synthetic three-point GPX written to `tmp_path` with `<time>` values gives
  `time == (0.0, 5.0, 12.0)`; mismatched lengths raise `ValidationError`.
- Parity: exact, current goldens. G-here.
- Commit: `Add the Track model with a GPX reader`
- Done when: `Track` is importable from `pyntpot.maps.track`.

#### P3.7 Provider protocols, credit and the test server

- Implements D8, D9 (design); predecessor P3.6. Parallel-safe with P3.2 to
  P3.5 and P3.11a/P3.11b.
- Owner files: create `src/pyntpot/maps/providers/base.py`,
  `tests/support/providers.py`, `tests/support/http_server.py`,
  `tests/unit/maps/providers/test_base.py`,
  `docs/decisions/0004-providers-and-fetch-cache.md`; edit `GLOSSARY.md`
  (add **credit**, **elevation grid**), `test_import_order.py`.
- Names: `Credit` is imported from `maps/credit.py` (P3.1).
  `ElevationGrid(n: int, box: BoundingBox, lats: tuple[float, ...], lons: tuple[float, ...], elev: tuple[float, ...])`
  with `to_json() -> str` byte-identical to `geo.fetch_elevation`'s file
  (`json.dumps({"n", "bbox", "lats", "lons", "elev"})`, default separators)
  and `from_json(text) -> ElevationGrid`.
  `class Features(Protocol)`: `id: str` and `credit: Credit` (read-only
  properties), `features(box: BoundingBox) -> str` (Overpass JSON text, the
  feature query) and `landcover(box: BoundingBox) -> str`.
  `class Elevation(Protocol)`: `id`, `credit`,
  `grid(box: BoundingBox, n: int) -> ElevationGrid`.
  `class ProviderError(RuntimeError)`;
  `class ProviderBudgetExceededError(ProviderError)` (raised by both shipped
  providers before the call that would pass their budget).
  `tests/support/providers.py`: `FixtureFeatures` with `id = "overpass"` and
  `FixtureElevation` with `id = "opentopodata-srtm30m"` (the shipped
  providers' ids, so the cache key computed for the CLI's real providers
  finds the fixture files, and the shipped providers' `Credit` values
  written out as literals, since `tests/support` may not wait for P3.8 and
  P3.9), returning the Lynmouth fixture files' text, each
  counting its calls.
  `tests/support/http_server.py` (P3.8 and P3.9 only import it):
  `Request` frozen dataclass (`method: str`, `path: str`,
  `headers: Mapping[str, str]`, `body: bytes`); `Server` with `url: str` and
  `requests: list[Request]`; `@contextmanager serve(responses: Sequence[tuple[int, str]]) -> Iterator[Server]`
  running a real `http.server.ThreadingHTTPServer` on `127.0.0.1:0` in a
  daemon thread, answering the n-th request with the n-th `(status, body)`
  (the last one repeats), shut down and joined on exit.
- ADR 0004 (accepted): the two protocols (the sanctioned exception to the
  rule of three); a required `contact` string; published limits enforced by
  default: Overpass one request at a time, back-off on 429, at most 100
  queries per provider instance (regular use is under 100 a day), a
  `[maxsize:N]` header bounding each response; OpenTopoData 100 points a
  call, one call a second by a fixed pause, at most 1000 calls per provider
  instance. "Per process" in the spec is read as per instance: no global
  state, nothing shared between tests, and a caller who builds two
  instances has chosen to. Credit per provider. The fetch cache keyed by
  `sha256` of the bounding box, the margin and both provider ids, first 16
  hex characters (D9), the fixture providers carrying the shipped ids, and
  the fixture files renamed to that key in P3.16. The rename lands after
  the window and is safe there because the key is in neither the hash input
  nor the manifest.
- Tests: assigning `FixtureFeatures()` to a `Features`-annotated variable
  type-checks (ty is the proof; the test asserts its `id` is `"overpass"`);
  `ElevationGrid` `from_json` then `to_json` of `elevation-lynmouth.json` is
  byte-identical; `serve([(429, ""), (200, "ok")])` answers two `httpx`
  requests with those statuses and records both.
- Parity: exact, current goldens. G-here.
- Commit: `Define the provider protocols and a local test server`

#### P3.8 Overpass provider

- Implements D8; predecessor P3.7. Parallel-safe with P3.9, P3.10.
- Owner files: create `src/pyntpot/maps/providers/overpass.py`,
  `tests/unit/maps/providers/test_overpass.py`; append to
  `test_import_order.py`.
- Names: `DEFAULT_ENDPOINTS = ("https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter")`
  (not `geo.OVERPASS_URLS`, which still lists the retired
  `overpass.kumi.systems`); `OverpassFeatures(contact: str, endpoints: tuple[str, ...] = DEFAULT_ENDPOINTS, *, budget: int = 100, client: httpx.Client | None = None, sleep: Callable[[float], None] = time.sleep)`;
  `id = "overpass"`; `credit = Credit("© OpenStreetMap contributors", "https://www.openstreetmap.org/copyright", "© OpenStreetMap contributors (openstreetmap.org/copyright)")`.
  The module is a leaf, so it **copies** what the queries need from
  `geo.py` (verbatim values): `FEATURE_QUERY` (today `OVERPASS_QUERY`),
  `LANDCOVER_QUERY`, and the tuples and strings they are formatted with:
  `MAJOR_ROADS`, `MINOR_ROADS`, `TOURISM_LANDMARKS`, `MANMADE_LANDMARKS`,
  `BUILDING_LANDMARKS`, `AMENITY_LANDMARKS`, `LEISURE_LANDMARKS`,
  `LANDCOVER_LANDUSE`, `LANDCOVER_NATURAL`, `LANDCOVER_LEISURE`. P4.15
  deletes `geo`'s copies and points the layer code at these. Queries are
  formatted as `fetch_overpass`/`fetch_landcover` do, with their own
  `[timeout:N]`; the size bound is the pinned constant
  `MAXSIZE_BYTES = 67_108_864` (64 MiB, about 30 times the larger fixture
  payload), spliced at request time by replacing the query's leading
  `[out:json]` with `[out:json][maxsize:67108864]`, so the copied templates
  stay byte-equal to `geo`'s; one request at a
  time; on 429, `sleep(30.0)` then the next endpoint; any other HTTP error
  tries the next endpoint; when all fail, `ProviderError` raised from the
  last `httpx.HTTPError`; the 101st query on one instance raises
  `ProviderBudgetExceededError` before any request. No blanket
  `except Exception`. User-Agent `pyntpot/<version> (<contact>)` with the
  version from `importlib.metadata.version("pyntpot")` (not
  `pyntpot.__version__`: from P3.20 the top-level `__init__` imports `maps`
  before it can assign the version, E402); an empty `contact` raises
  `ValueError`.
- Tests (with `tests/support/http_server.serve`, no real network): the
  User-Agent carries the contact; a 429 then a 200 calls `sleep` with 30.0
  once (the injected `sleep` is a list's `append`) and returns the second
  endpoint's body; all endpoints failing raises `ProviderError`; `budget=1`
  makes the second query raise `ProviderBudgetExceededError` with one request
  recorded; the query body starts with `[out:json][maxsize:67108864]` and
  contains the box formatted as `fetch_overpass`
  does (pinned string for a Lynmouth box); each copied constant equals
  `geo`'s (this test imports `pyntpot._port.geo`; P4.15 deletes the
  comparison together with `geo`'s copies).
- Parity: exact, current goldens. G-here.
- Commit: `Add the Overpass feature provider with its usage limits`

#### P3.9 OpenTopoData provider

- Implements D8; predecessor P3.7. Parallel-safe with P3.8, P3.10.
- Owner files: create `src/pyntpot/maps/providers/opentopodata.py`,
  `tests/unit/maps/providers/test_opentopodata.py`; append to
  `test_import_order.py`.
- Names: `PUBLIC = "https://api.opentopodata.org/v1"`;
  `OpenTopoData(contact: str, endpoint: str = PUBLIC, dataset: str = "srtm30m", *, budget: int = 1000, client: httpx.Client | None = None, sleep: Callable[[float], None] = time.sleep)`;
  `id = f"opentopodata-{dataset}"`; `credit = Credit("Elevation: NASA SRTM via OpenTopoData", "https://www.opentopodata.org/", "elevation: NASA SRTM")`;
  `grid(box, n)` samples the same `n` by `n` lattice as `geo.fetch_elevation`,
  100 points a call, `sleep(1.1)` after each call (no clock read), `None`
  elevations as `0.0`, status other than `OK` raises `ProviderError`; the
  budget is a call counter on the instance (ADR 0004) and raises
  `ProviderBudgetExceededError` before the call that would exceed it. User-Agent
  and contact handling as P3.8.
- Tests (with `serve`): a 3 by 3 grid makes one call and returns the served
  values in order; `n = 11` (121 points) makes two calls and sleeps twice;
  `budget=1` with `n = 11` raises `ProviderBudgetExceededError` after one call;
  the User-Agent carries the contact.
- Parity: exact, current goldens. G-here.
- Commit: `Add the OpenTopoData elevation provider with a call budget`

#### P3.10 Fetch cache

- Implements D9, A7 (fetch half); predecessors P3.6, P3.7. Parallel-safe with
  P3.8, P3.9.
- Owner files: create `src/pyntpot/maps/cache.py`, `tests/unit/maps/test_cache.py`;
  append to `test_import_order.py`.
- Names: `MARGIN_M = 1500.0`, `LANDCOVER_MARGIN_M = 2600.0` (copied from
  `geo.LANDCOVER_MARGIN_M`; a test asserts they are equal),
  `ELEVATION_SAMPLES = 80`; `Cache(directory: Path)` (explicit, never
  cwd-relative);
  `key(track: Track, features: Features, elevation: Elevation, margin_m: float = MARGIN_M) -> str`
  = first 16 hex of `sha256` over the canonical JSON of the rounded box
  (6 places), the margin and both provider ids;
  `features_path(key)`, `landcover_path(key)`, `elevation_path(key)` returning
  `directory / "overpass-<key>.json"` and so on (today's names, so the engine's
  `overpass_path(key, cache_dir)` keeps working with the hash as its key);
  `plates_dir(key) -> Path`;
  `ensure(track, features, elevation, *, force: bool = False) -> str` that
  fetches whatever is missing (landcover over `LANDCOVER_MARGIN_M`) and
  returns the key. **Pinned order:** features, then landcover, then
  elevation (today's `geo.fetch_activity`, `geo.py:1597-1614`, does
  features, elevation, landcover; the order moves no byte of any payload),
  each payload written to its path as soon as its call
  returns, before the next call; the docstring states it, and P3.16's
  `FetchError` test relies on it.
- Tests: the key for the Lynmouth track with the fixture providers is a pinned
  literal; `key(track, OverpassFeatures("test"), OpenTopoData("test")) == key(track, FixtureFeatures(), FixtureElevation())`
  if P3.8 and P3.9 have landed (otherwise P3.16 adds this assertion; their
  constructors make no request); changing the margin or a provider id
  changes the key; `ensure` into an empty `tmp_path` calls each fixture
  provider once and writes three files whose bytes equal the fixture files;
  a second `ensure` calls nothing. Order: a test-local `_RecordingFeatures`
  and `_RecordingElevation` (hand-written real objects wrapping the fixture
  providers, forwarding `id` and `credit`, appending to one shared
  `calls: list[str]`; at each call they also record which of the three
  cache paths exist) prove `calls == ["features", "landcover", "elevation"]`
  and that the features file exists when `landcover` is called and the
  features and landcover files exist when `grid` is called.
- Parity: exact, current goldens. G-here.
- Commit: `Key the fetch cache by box, margin and provider`

#### P3.11a Style groups and the field table (A6, part 1a)

- Implements A6 (grouping), D7, D23 (successor); predecessor P3.1.
  Parallel-safe with P3.2 to P3.10. Split from the old P3.11 because the
  group dataclasses are copied, not moved, and count in full.
- Owner files: create `src/pyntpot/ink/style.py`,
  `src/pyntpot/letters/style.py`, `src/pyntpot/maps/style_groups.py`,
  `tests/unit/maps/test_style_groups.py`,
  `docs/decisions/0005-style-groups.md`; append to `test_import_order.py`
  (`MODULES`, and `ADAPTERS` for `maps.style_groups`). Reads, never edits,
  `_port/themes/default.json`, `_port/paint.py`, `_port/geo.py`,
  `_port/style.py`.
- Names: frozen stdlib dataclasses (ink and letters may never import
  pydantic): `ink/style.py`: `PaperStyle`, `WashStyle`, `BrushStyle`;
  `letters/style.py`: `FaceStyle`, `NibStyle`, `HandStyle`;
  `maps/style_groups.py`: `CardStyle`, `RibbonStyle`, `CoverStyle`,
  `RouteStyle` (the painter's route-plate fields), `RouteInks` (fields
  `run`, `ride`, `swim`, `other`, each a `RouteInk` imported by name from
  `pyntpot._port.style`), `LetteringPolicy`, `BasemapStyle`. Each field's
  dataclass default is its source class default (`PaintStyle` or
  `GeoOptions`, copied verbatim); the resolved and effective values live in
  the theme (P3.11b), not in the dataclass defaults. Each field keeps its
  `#:` comment as its documentation. Base groups (their fields feed the
  base plates): `PaperStyle`, `WashStyle`, `BrushStyle`, `CardStyle`,
  `RibbonStyle`, `CoverStyle`, `RouteStyle`, `BasemapStyle`. Lettering
  groups: `FaceStyle`, `NibStyle`, `HandStyle`, `LetteringPolicy`.
  `RouteInks` is neither (compose time only).
- **Basemap options are the effective ones.** `BasemapStyle` holds the 27
  `GeoOptions` fields other than `clip_margin_m`, read or not (rule 5
  below). The values the painter
  actually used are the `GeoOptions` class defaults plus the inline
  overrides in `journal_layers` (`hillshade_mode="off"`, `roads="key"`,
  `rivers="key"`, `generalise=False`, `landmarks="all"`,
  `landmark_max=40`); P3.11b's theme carries those. `clip_margin_m` is
  derived from the card per render and is not a style field. The resolved
  theme's `geo` section is **not** used: it differs from the effective
  values on `interaction_m` (80 against 60), `landmark_radius_m` (250
  against 300), `landmark_max` (3 against the painter's 40) and
  `hillshade_levels` (2 against 5), and those values belong to the upstream
  consumer's vector map; ADR 0005 lists them as such for P8.
  `landmark_export`'s own option set stays with the candidates code (P4.10
  `candidate_basemap()`, `CANDIDATE_BASEMAP` from P4.15), not in `Style`.
- **Route ink (the smaller option, chosen).** D23 fixes the resolved default
  style including `RouteInk` per sport, so `RouteInks` carries all four
  resolved inks, and `Style.route_ink()` (P3.11b) always returns
  `route_inks.ride`, the ink the goldens were painted with. P3 adds no sport
  selection: no `Style.route.sport`, no `Track.sport`, no `--sport`.
  `route_inks` is read only at compose time, so it is in `digest()` but in
  neither `base_digest()` nor `lettering_digest()`: changing an ink repaints
  no plate (A6, A7). The three `PaintStyle` "route plate" fields, which the
  painter does read, are `RouteStyle`, a base group. ADR 0005 records this;
  choosing an ink by sport is a later feature with its own ADR.
- **Assignment rule** (deterministic; every P4 slice reads the result and
  none regroups). The **pinned table below is authoritative**; the rule
  says how it was derived and is what ADR 0005 records as its reason. The
  implementer does not recompute it: a scratch AST script over `_port`
  (attribute reads on `style`, `pstyle`, `self.style`, and `getattr`
  strings) only confirms that the reader list matches, and any mismatch is
  a stop-and-report, not a regrouping. Measured at `f63bb61`.
  1. **Readers at their final homes.** A field's readers are the functions
     that read it, at the home the P4 slices give them (P4.2 to P4.9 name
     every `paint.py` function's module; P4.5, P4.6, P4.15 and P4.18 the
     rest). The readers that decide the table, and their homes:

     | Reader today | Final home | Kind |
     |---|---|---|
     | `paint.brush_from_id`, `InkPad.__init__` | `ink/brush.py`, `ink/pad.py` | ink |
     | `paint.composite`; `separated`, `fluid_modulate` | `ink/pigment.py`; `ink/wash.py` | ink |
     | `paint.label_brushes`, `label_plate`, `_backing_wash`, `_pen_profile` | `letters/nib.py` | letters |
     | `labels.Hand.__init__` | `letters/hand.py` | letters |
     | `paint.paint` (and its nested `transp`, `bloom_arg`), `paper_plate`, `plate_brushes`, `sea_patches` | `maps/painter/*` | maps base |
     | `geo.journal_geometry`, `journal_layers`, and every `GeoOptions` reader | `maps/layers.py`, `maps/osm.py` | maps base |
     | `mapcard.compose`, `labels.home_labels`, `labels.named_lines` (P3.13) | `maps/lettering/*`, `maps/compose.py` | maps lettering |
     | `labels.hand()` (`labels`), `mapcard.alphabet_sheet` | deleted (P4.5, P3.17); `letter` takes over the `labels` check in P4.5 | maps lettering |

     `paint._dark_field` reads no style field, so it decides nothing here;
     P4.6 moves it to `maps/plates.py` as `dark_array`.
     `label_geom_tol_px` is read today by `paint.paint` (for `label_geom`),
     but P3.13 moves that read into `labels.named_lines`, so its final
     reader is maps lettering.
  2. **Base or lettering.** A field with any ink or maps-base reader goes
     to a base group. A field whose readers are all `letters` or maps
     lettering goes to a lettering group, so no lettering-only field is in
     `base_digest()` (A6, A7).
  3. **Layer.** A base field with an ink or `letters` reader goes to an
     ink group (`letters` has no base group, and `letters` may import
     `ink`). A lettering field with a `letters` reader goes to a `letters`
     group: `FaceStyle` if `Hand` opens the face with it (`label_face`,
     `label_route`), `HandStyle` if `Hand` reads it otherwise
     (`label_seed`), else `NibStyle`. A lettering field read only in maps
     goes to `LetteringPolicy`.
  4. **Section.** Within what rules 2 and 3 allow, the `PaintStyle`
     section comment picks the group: the ribbon to `RibbonStyle`; land
     cover and the wood to `CoverStyle`; the ink, phase 1 brush and phase 2
     brush quality to `BrushStyle`; the route's own plate to `RouteStyle`;
     phase 2 tuning and sea and phase 2 wash to `WashStyle`. Three sections
     mix concerns and are assigned field by field in the table: the card
     (frame, paper, encoder, seeds), phase 1 compositing and paper (paper
     and compositing to `PaperStyle`, wet bleed, flow rim and blooms to
     `WashStyle`, beside `bloom_strength`), and the crisp layer (rules 2
     and 3; `dark_grid`, read only by the painter, to `CardStyle`).
  5. **Consumer-only** (`PaintStyle` fields only). A `PaintStyle` field no
     module under `src/` reads, except through `digest`, `paint_hash` or
     `labels_hash` key lists, is left out of `Style` and named in a pinned
     `CONSUMER_ONLY` tuple in `maps/style_groups.py` and in ADR 0005. Rule 5
     does not apply to `GeoOptions`: `BasemapStyle` carries all 27 fields
     other than `clip_margin_m`, read or not, because the effective basemap
     options are one value of D23's resolved default style and P3.11b's
     equality test pins all 27. Two of them have no reader in `src/`
     (`hillshade_opacity`, `geo.py` around 77; `pick_places`, around 103);
     they stay in `BasemapStyle` and so in `base_digest()`, and ADR 0005
     names them as unread, kept for the upstream consumer (P8).

  **The table** (173 `PaintStyle` fields plus 27 `GeoOptions` fields; each
  group's fields in source order):

  | Group | Layer | Fields |
  |---|---|---|
  | `PaperStyle` | ink, base | `plate_lossless`, `webp_quality`, `paper_quality`, `grid`, `grid_spacing_px`, `grid_opacity`, `paper_hex`, `paper_tooth`, `paper_worn`, `paper_vignette`, `paper_foxing`, `sheet_seed`, `km_glazing`, `pigment_transparency`, `km_transparency`, `paper_fibre`, `paper_fibre_mix`, `paper_fibre_stretch`, `paper_fibre_angle`, `paper_fibre_cell_px`, `gran_gamma` (21) |
  | `WashStyle` | ink, base | `wet_bleed`, `wet_bleed_px`, `wet_bleed_mix`, `wet_rim_drop`, `wet_bleed_edge_mult`, `flow_rim`, `flow_rim_exp`, `flow_rim_ref_frac`, `flow_rim_frac`, `blooms`, `bloom_density`, `bloom_max`, `bloom_radius_frac`, `bloom_lift`, `bloom_warp`, `bloom_seed`, `bloom_strength`, the seven `sea_variation*` fields, `wet_close_px`, the seven `silhouette_deform*` fields, `pigment_separation`, `separation_pigments`, `separation_share`, `separation_gamma`, `separation_transparency`, `fluid_pass`, `fluid_grid`, `fluid_steps`, `fluid_relax`, `fluid_amount`, `fluid_gran`, `fluid_seed` (44) |
  | `BrushStyle` | ink, base | `ink_seed`; every field of the ink section (`river_curve` to `brush_overrides`: `river_curve`, `major_river_rel_frac`, `minor_roads_mppd`, `blotch_m`, `dab_spacing_m`, `gran_m`, `river_mult`, `brushes`, `brush_width_px`, `coast_width_frac`, `brush_jitter_px`, `brush_press_cell_px`, `brush_wobble_px`, `brush_step`, `brush_profile_px`, `pen_load_px_frac`, `pen_pool_radius_frac`, `pen_pool_gain`, `brush_overrides`); every field of phase 1 brush (`ink_starve` to `pen_thin`, 13) and phase 2 brush quality (`ink_ss` to `bristle_drift_coherence`, 12) (45) |
  | `FaceStyle` | letters, lettering | `label_route`, `label_face` (2) |
  | `HandStyle` | letters, lettering | `label_seed` (1) |
  | `NibStyle` | letters, lettering | `label_size_px`, `label_ink`, `label_brush`, `label_pen_width_px`, `label_outline_width_frac`, `label_leader_brush`, `label_leader_width_px`, `label_pen_angle_deg`, `label_pen_thin`, `label_wash`, `label_wash_alpha`, `label_wash_dark_floor`, `label_wash_spread`, `label_route_ink`, `label_water_ink`, `label_in_water_ink` (16) |
  | `CardStyle` | maps, base | `display_px`, `supersample`, `dark_grid` (3) |
  | `RibbonStyle` | maps, base | the ribbon section: `ribbon_k`, `ribbon_c`, `ribbon_mult`, `ribbon_min_m`, `ribbon_max_m`, `card_grow_mult`, `card_pad_frac`, `card_pad_ribbon_frac`, `card_aspect_min`, `card_aspect_max`, `ribbon_fill`, `ribbon_tear_frac`, `ribbon_tear_floor_px`, `rim_strength`, `coast_hard_mask`, `sea_to_edge` (16) |
  | `CoverStyle` | maps, base | `dither_seed` (it seeds the wood dabs); land cover and the wood: `land_cover`, `relief`, `cover_cfg`, `pigments`, `pale_base`, `pale_pool`, `wood_texture`, `wood_dabs`, `wood_tex_scales`, `wood_tex_strengths`, `dab_spacings`, `dab_strengths` (13) |
  | `RouteStyle` | maps, base | `route_pen`, `route_pen_brush`, `route_pen_width_px` (3) |
  | `BasemapStyle` | maps, base | the 27 `GeoOptions` fields other than `clip_margin_m` (27) |
  | `LetteringPolicy` | maps, lettering | `label_max`, `labels`, `label_ground`, `label_geom_tol_px`, `home_glyph` (5) |
  | `CONSUMER_ONLY` | not in `Style` | `cover_order`, `label_font`, `label_pin_colour`, `label_glow_colour` (4) |

  21 + 44 + 45 + 2 + 1 + 16 + 3 + 16 + 13 + 3 + 5 + 4 = 173. Readers that
  cross groups, by design (each reader takes every group it reads as a
  parameter, P4.3, P4.6): `letters/nib.py` reads `NibStyle`, `FaceStyle`
  (`label_route`), `HandStyle` (`label_seed`), `BrushStyle` and
  `PaperStyle`; `Hand` reads `FaceStyle` and `HandStyle`; the maps
  lettering code reads `LetteringPolicy` and `NibStyle.label_size_px`
  (`home_labels`, `compose`); the painter reads every base group.
  Defaults that name a `_port.paint` constant (`PAPER`, `PIGMENTS`,
  `TRANSPARENCY`, `COVER_CFG`) are written as literal copies: `ink` and
  `letters` never import `_port`, and `style_groups` imports only
  `_port.style`. The default-equality test proves the copies; P4.2 and
  P4.8 replace them with imports of the moved constants.
- ADR 0005 (accepted) carries the full field-to-group table (all 173
  `PaintStyle` fields and 27 `GeoOptions` fields, one row each, with the
  reader modules that decided it, copied from the pinned table above), the
  rule above, `CONSUMER_ONLY`, the two unread `GeoOptions` fields kept in
  `BasemapStyle`, the four `geo` values left to the consumer, and the
  route-ink decision. The table
  is final: changing a field's group after P3.11b would move a pinned
  digest (and, for base groups, the frozen hash), so a later slice that
  finds a field it cannot reach adds a group *parameter* to its function,
  never moves the field, and stops if neither works.
- Tests (`test_style_groups.py`): `set(group fields) | set(CONSUMER_ONLY)`
  equals the `PaintStyle` field names plus the `GeoOptions` field names
  minus `clip_margin_m`, plus the four `RouteInks` fields; no field is in
  two groups; each group's dataclass defaults equal the source class
  defaults field by field; for each group, the tuple of its field names
  (`dataclasses.fields`, in order) equals a pinned literal copied from the
  table above, which pins the whole table; `CONSUMER_ONLY` equals its
  pinned four names; and, named for the reader, the multi-layer fields map
  as the table says: `label_size_px` to `NibStyle`, `label_seed` to
  `HandStyle`, `label_route` to `FaceStyle`, `paper_hex` and `sheet_seed`
  to `PaperStyle`, `display_px` to `CardStyle`, `brush_width_px` to
  `BrushStyle`, `label_geom_tol_px` to `LetteringPolicy`.
- Parity: exact, current goldens (nothing is wired). G-here.
- Commit: `Group the style fields by the layer that reads them`
- Done when: each new file is under 400 lines (split `maps/style_groups.py`
  or `ink/style.py`, which holds 110 fields with their `#:` comments, by
  group into sibling modules if needed); ADR 0005 has one row per field.

#### P3.11b Style model, TOML theme and digests, unwired (A6, part 1b)

- Implements A6 (model), D7, D23 (successor); predecessor P3.11a.
  Parallel-safe with P3.2 to P3.10.
- Owner files: create `src/pyntpot/maps/style.py`,
  `src/pyntpot/maps/themes/default.toml`, `tests/unit/maps/test_style.py`;
  edit `docs/decisions/0005-style-groups.md` (digests section); append to
  `test_import_order.py` (`MODULES`, and `ADAPTERS` for `maps.style`).
  Reads, never edits, `_port/themes/default.json`, `_port/paint.py`,
  `_port/geo.py`.
- Names: `maps/style.py`: `Style(pydantic.BaseModel, frozen=True)` with
  fields
  `paper, wash, brush, face, nib, hand, card, ribbon, cover, route, route_inks, lettering, basemap`;
  `@classmethod from_toml(path: Path) -> Style` (`tomllib`); unknown keys
  are rejected at every level: top-level by pydantic `extra="forbid"`,
  inside each group by an explicit check of the table's keys against
  `dataclasses.fields(group)` (stdlib dataclasses in `ink` and `letters`
  cannot carry pydantic config); `@classmethod default() -> Style` (reads
  the packaged `maps/themes/default.toml` through `importlib.resources`);
  `digest() -> str` (all groups); `base_digest() -> str` (the base groups:
  paper, wash, brush, card, ribbon, cover, route, basemap);
  `lettering_digest() -> str` (face, nib, hand, lettering); each group
  digest is `sha256(json.dumps(asdict(group), sort_keys=True, default=str))[:16]`
  and a combined digest hashes the group digests in field order;
  `paint_style() -> PaintStyle` and `route_ink() -> RouteInk` (adapters for
  the engine until P4.11). `default.toml` writes every non-consumer-only
  resolved value of `default.json`'s `paint` and `route_ink` sections and
  the effective basemap options (P3.11a), so `Style.default()` is the
  resolved style and the dataclass defaults are not.
- Tests: `Style.default()` reproduces every non-consumer-only value of the
  `paint` and `route_ink` sections of `_port/themes/default.json` field by
  field, with tuples as tuples;
  `asdict(Style.default().basemap)` equals
  `asdict(GeoOptions(hillshade_mode="off", roads="key", rivers="key", generalise=False, landmarks="all", landmark_max=40))`
  without `clip_margin_m`, field by field (the literal copied from
  `journal_layers`); `paint_style()` of the default equals
  `PaintStyle.from_resolved(default["paint"])` field by field on every
  non-consumer-only field; `from_toml` rejects an unknown top-level key and
  a misspelt key inside `[wash]`; changing a `route_inks` value leaves
  `base_digest()` and `lettering_digest()` unchanged; the three digests of
  the default are pinned literals.
- Parity: exact, current goldens (nothing is wired yet). G-here.
- Commit: `Load the grouped style from a TOML theme`
- Done when: each new file is under 400 lines; ADR 0005 lists the three
  pinned digests.

#### P3.12 Wire the style and fix the hash form (opens the window)

- Implements A6 (wiring), A7 (base-plate key form), D7, D9; predecessors
  P3.2 to P3.11b, all landed on `main`. Opens the regeneration window: from
  here to P3.15 follow **Pushing** above.
- Owner files: edit `_port/paint.py` (`paint_hash`, `paint_activity`,
  `paint`, the `label_font` default), `_port/geo.py` (`journal_layers`
  builds its `GeoOptions` from a `BasemapStyle` argument plus the derived
  `clip_margin_m`), `_port/mapcard.py` (`compose` takes `style: Style`),
  `_port/labels.py` (`hand`, `Hand`, `home_labels` read the adapter),
  `src/pyntpot/maps/basemap.py` (`canonical`), `tests/support/golden.py`,
  `tests/golden/test_parity.py` (theme load), `tests/unit/test_paint.py`,
  `tests/unit/test_geo.py`, `tests/unit/maps/test_style.py`,
  `tests/unit/maps/test_basemap.py`; delete
  `src/pyntpot/_port/themes/default.json` and
  `tests/fixtures/lynmouth/style.json` (both carry the old font stack); edit
  `tests/fixtures/lynmouth/README.md` (drop the `style.json` row) and
  `specs/001-port/design-sources.md` only if it still names the old stack; create `docs/decisions/0006-golden-regeneration.md` (Status: proposed).
- Changes:
  - `Basemap.canonical() -> str`: compact JSON (sorted keys, separators
    `(",", ":")`) of `{"card": [box, display, render, mpp, mpp_display], "layers": asdict(layers)}`
    with tuples as lists and **every float formatted as `format(v, ".3f")`**,
    `"-0.000"` written as `"0.000"` (ints and strings unchanged). Card `offset`, `track`, `track_time`,
    `places`, `candidates`, `sources` and `credits` are not in it. This is
    the final hash input form.
  - `paint_hash(basemap: Basemap, style_digest: str) -> str` =
    `sha256(basemap.canonical().encode()).hexdigest()[:16] + "-" + style_digest`,
    with no hand-kept key list.
  - `paint_activity(key, lat, lng, style: Style, *, cache_dir, places, force=False) -> Plates | None`
    passes `style.paint_style()` to the engine, `style.basemap` to
    `journal_layers` and `style.base_digest()` to the hash;
    `compose(key, lat, lng, style: Style, picks, labels, cache_dir)`.
  - `PaintStyle.label_font` default becomes `'"Patrick Hand",cursive'` (the
    vendored face) so the old stack leaves the tree; it is consumer-only and
    not in `Style`. The previous label font stack was removed from the code in P3.12; it is not added to the banned-term list.
- Tests: `test_style.py`: the default-equality test now compares against
  pinned literals for a sample of fields (the JSON file is gone).
  `test_basemap.py`: `canonical()` is unchanged when every float in a small
  synthetic `Basemap` (values chosen away from a three-decimal boundary) is
  moved one ulp with `math.nextafter`; unchanged when `places`, `candidates`,
  `sources`, `credits`, `track` or `track_time` change; changed when one
  road point moves by 0.01 m.
- Parity: inside the window, step 1. G-window with `step-0` made on this
  slice's starting commit and gate options
  `--require-identical all --require-hash differ`. **Expected: all five
  outputs byte-identical to step 0; the manifest hash differs** (new form
  and the style digest). Any
  pixel difference means the effective basemap options or the style adapter
  are wrong: stop. Record old hash `c034e1a4d60bad70-77dce82bec370944`, the
  new hash and the compare lines in ADR 0006's draft.
- Commit: `Hash plates from the typed basemap and the style groups`
- Done when: the step compare logs zero differing pixels and byte-identical
  files on all five outputs and a new hash; `grep -rn "Segoe" src tests` is
  empty.

#### P3.13 Read lettering geometry from the basemap, then drop the round trip (A4, pixels)

- Implements A4 (pixel half, manifest shape); predecessor P3.12. Inside the
  window, steps 2 and 3. Two commits, in this order, each with its own
  G-window compare. About 600 changed lines in all; if the first commit
  alone passes 450, stop after it and continue in a new session (pushing to
  the backup ref).
- Owner files: `_port/geo.py`, `_port/paint.py`, `_port/mapcard.py`,
  `_port/labels.py`, `src/pyntpot/maps/basemap.py`,
  `src/pyntpot/maps/plates.py`, `src/pyntpot/maps/card.py`,
  `tests/support/golden.py`, `tests/support/manifests.py` (the builder
  loses the removed fields), `tests/golden/make_golden.py`,
  `tests/golden/test_parity.py`, `tests/unit/maps/test_plates.py`,
  `tests/unit/maps/test_card.py`, `tests/unit/test_paint.py`,
  `tests/unit/test_geo.py`, `docs/decisions/0006-golden-regeneration.md`.
- **Commit 1 (step 2), pixel-neutral:** `Read lettering geometry from the basemap and settle the manifest`
  - `paint_activity(...) -> tuple[Basemap, Plates] | None`;
    `mapcard.compose(basemap: Basemap, plates: Plates, style: Style, picks: Any, labels: bool) -> tuple[Image, list[Label]]`
    (the placed labels are `letter_card`'s first element, in placement
    order; `[]` when `labels` is false),
    with its lettering steps split out as
    `mapcard.letter_card(basemap, plates, style, picks) -> tuple[list[Label], list[Span], Path | None]`
    (P3.17 moves this into `maps/lettering.py` as `letter`).
    `paint_fixture` returns the placed label names too, taken from
    `compose`'s second element (`label.name` for each), and `make_golden`
    writes them to `labels.txt`, one per line, in placement order. P3.17
    keeps the same names: there `paint_fixture` reads them from `letter`'s
    result.
  - `route_px` comes from `basemap.track` through the card with the offset
    `route0` gave: `basemap.layers.route[0]` minus `basemap.track[0]`. No
    second `track_projection`. It is then separated exactly as today,
    `separate_strands(route_px, ink.px * STRAND_GAP_WIDTHS)`, and that
    separated polyline is what `_route` draws and what `ground_labels`,
    `pick_roads`, `route_markers`, `place`, `draw_plate` and
    `cumulative_m(..., card.scale)` read, unchanged from
    `mapcard.py:158-199` today.
  - Readers of the manifest's `places`, `candidates`, `sources` and
    `label_geom` (`journal_picks`, `journal_heuristic`, `settlements`,
    `home_labels`, `road_lines`, `pick_roads`, `pick_rivers`, `feature_px`)
    read the `Basemap`. The named lines come from
    `labels.named_lines(basemap: Basemap, tol_px: float) -> dict[str, list[dict[str, Any]]]`,
    which does exactly what `label_geom` did (same tolerance, `simplify`,
    `round(v, 1)`), so nothing moves.
  - The manifest takes its final shape. Removed keys: `id`, `route0`,
    `places`, `candidates`, `label_geom`, `labels_hash`, `sources`, `timing`.
    Remaining, final: `hash`, `files`, `sizes`, `bytes`, `card`, `display`,
    `render`, `mpp`, `mpp_display`, `ribbon_m`, `span_m`, `wet_px`,
    `gran_px`, `dark`, `wood_px`, `water_px`. The nine `time.perf_counter`
    reads in `paint` go with `timing` (`import time` leaves `paint.py` if
    nothing else uses it), and `paint` loses its `labels` parameter, which
    only fed `labels_hash`. `Manifest` loses the same fields;
    `test_plates.py`'s literal follows. ADR 0006's draft lists the removed
    keys.
  - Gate options: `--require-identical all --require-hash equal`.
  - Expected (gate): all five outputs **byte-identical** to step 1; the
    manifest hash **equal** to step 1's (its inputs did not change);
    `labels.txt` written for the first time and copied into ADR 0006's draft
    as the window's pinned name list.
- **Commit 2 (step 3), pixels:** `Keep basemap geometry as full-precision point lists`
  - `journal_layers` stops quantising **its own output** (the seam): the
    `path_d` string round trip and `round(v, 1)` on the route, cover, lakes,
    sea, coastline, road and river points it hands to the painter, and on
    the elevation patch corners. Its **input** is untouched: `basemap()`
    (and `_osm_layers` inside it) still writes 0.1 m `path_d` strings, and
    `journal_layers` still reads roads, `water_area` and rivers through
    `geo.parse_path` (`geo.py` around 3494, 3513, 3520). That is the vector
    map's output format, frozen (see "What the window freezes"); no line of
    `basemap()` or `_osm_layers` changes in this commit. Unchanged too:
    `journal_geometry`'s rounding of the card, bounds, span and scales (that
    defines the frame, not the seam) and the rounding of widths, profiles
    and elevation values. Delete `paint.parse_d` (the painter's second copy
    of the parser), `paint.label_geom`, and the seam's `path_d` calls in
    `journal_layers` and `_drawn` (`path_d`, `stroke_d`, `rings_path`
    themselves stay: `basemap()`, the relief code and tests call them);
    `named_lines` drops its `round(v, 1)`; `Card.offset` and the route
    offset are removed, so `route_px` is `basemap.track` through `Card.xy`,
    still separated by `separate_strands` before anything reads it.
  - Gate options: `--max-fraction 0.005 --require-hash differ --require-labels-equal`.
  - Expected (gate): only the seam's own rounding goes, so each moved point
    shifts by at most 0.05 m (half the 0.1 m step; the clipping, chaining
    and simplification upstream of it run on unchanged input), a small
    fraction of a render pixel, so each of the five outputs stays within
    `MAX_DIFFERING_FRACTION` of step 2 (expected far below it; record the
    actual figures); `labels.txt` **equal** to step 2's; the hash differs.
    Over the bound, or any change in `labels.txt`: stop, do not start
    P3.14, root-cause and report. Look at `$SCRATCH/step-3/map.png` beside
    `$SCRATCH/step-2/map.png` (open both) and write one sentence per visible
    difference into ADR 0006.
- Done when: `grep -rn "route0\|label_geom\|parse_d\b" src tests`
  and `grep -rn "perf_counter" src` are empty; `geo.parse_path` has exactly
  the three `journal_layers` call sites left; `plates.json` written by `make_golden` has exactly the sixteen
  final keys.

#### P3.14 Merge the polyline duplicates (A5, merges)

- Implements A5 (merge half); predecessor P3.13. Inside the window, steps 4
  to 6, one commit and one G-window compare per merge, each against the
  previous step.
- Owner files: `src/pyntpot/ink/polyline.py`, `src/pyntpot/ink/chains.py`
  (and `ink/curves.py` if P3.3 made it), `tests/unit/ink/test_polyline.py`,
  `tests/unit/ink/test_chains.py`, the `_port` call sites of merged names,
  `docs/decisions/0006-golden-regeneration.md`.
- Merges. A merge joins only functions that compute the same thing; two
  that differ are kept as separate named functions, each with a docstring
  line saying how it differs from the other, and ADR 0006 records why they
  stay apart. Every step's gate is the bound, which is never loosened: a
  merge whose compare fails the gate is reverted (not committed), recorded
  in ADR 0006 as "kept apart: <figures>", and the window continues with the
  next step. A step with nothing to merge has no commit and no compare.
  1. Step 4, `Merge the ring and chain joiners`: `join_ways` and
     `join_chains` (was `geo._join_chains`) are the same greedy loop; merge
     them into `join_chains(lines, tol)` with `join_ways`'s copying pool
     (`[list(w) for w in lines if len(w) > 1]`; a copy never changes a
     value), and `join_ways`'s callers (`_polygon_rings` twice, with the
     default `tol=1.0`; `coastline_chains`, with
     `tol=2.0`; `test_geo.py` near line 545) apply its `len(chain) > 3`
     ring filter and pass the tolerance explicitly. Gate options:
     `--require-identical all --require-hash equal --require-labels-equal`
     (expected byte-identical: same loop, same order, same tolerances).
     `join_strokes` (grid lookup, grows both ends, `popitem` order),
     `chain_lines` (ndarrays) and `joined` (tolerance 8) are different
     algorithms and stay as separate functions in `ink/chains.py`; merge one
     of them into `join_chains` only if P3.3's pinned-input tests and a new
     pinned test on the Lynmouth fixture's own inputs show identical output,
     under the same gate.
  2. Step 5, `Merge the arc-length helpers`: `running_length` (was
     `labels._cum`) and `cumulative_m` (was `labels.cumulative_m`) into
     `cumulative_length(line: Sequence[Pt], scale: float = 1.0) -> list[float]`
     with `cumulative_m`'s body (each step divided by `max(scale, 1e-9)`;
     dividing by 1.0 is exact). The name does not collide with
     `geo.cumulative(lat, lng)`, which P4.13 moves to candidates. If
     `length` and `length_indexed` both exist from P3.3, merge them here
     too (same sum, same order). Gate options:
     `--require-identical all --require-hash equal --require-labels-equal`.
  3. Step 6, `Merge the polyline normal helpers`: of `normal_at`,
     `unit_normal`, `tangent_at` and `normals`, merge only those that
     compute the same quantity. Gate options:
     `--max-fraction 0.005 --require-labels-equal` (and
     `--require-hash equal` when no merged helper is on the base-plate
     path).
- Done when: `ink/chains.py` has one chainer per distinct algorithm, each
  with a docstring line naming how it differs from the others; ADR 0006
  lists every merge made and every pair kept apart with its figures.

#### P3.15 Regenerate the goldens once (closes the window)

- Implements D22/D23 succession, A4 and A5 parity; predecessor P3.14. This
  is the **only** golden regeneration in the port (architecture.md,
  Sequencing 2).
- Owner files: `tests/golden/lynmouth/{paper,wash,pen,labels-centreline}.webp`,
  `plates.json`, `map.png`; delete `tests/golden/lynmouth/labels-centreline.json`
  (a label-plate cache record whose key form changes in P4.7; no test
  compares it); `docs/decisions/0006-golden-regeneration.md`.
- Steps: G-window's non-golden gate green; then
  `$MG tests/golden/lynmouth` (regenerate in place; it writes no
  `baseline.json` or `labels.txt` there) and `git rm` the sidecar; then
  `uv run pytest -m golden` (byte-exact, passes here by construction) and
  G-here with the exact run; then
  `$MG "$SCRATCH/final" --compare tests/golden/lynmouth --compare "$SCRATCH/step-last" --require-identical all --require-hash equal`
  (the gate covers the first compare and must exit 0; the logged lines of
  the second must also all say byte-identical, which proves the regenerated
  files are the last step's). Open old and new `map.png`. Run the banned-term and
  coordinate tests over the new `plates.json`.
- ADR 0006 becomes Status: accepted with: old hash, new hash; the per-step
  table (step, commit, expected outcome, per-output differing fraction,
  hash, `labels.txt` equal or not); the cumulative drift against the old
  goldens; what moved and why (hash form, rounding removal, route patch,
  chainer and normal merges); the final manifest key list; the machine
  (`uname -a`, Python, numpy, Pillow versions). And this paragraph: the
  goldens were made in the agent container, which is from now on "the
  machine that made the goldens" in spec Verification 1, and G-here runs
  them byte-exact there. The maintainer's exact run (`uv run pytest -m golden`
  on their machine) is a **follow-up check**, recorded by appending its
  result to this ADR. If bytes differ there, that is a defect to root-cause
  (most likely platform float behaviour in a maths library or a numpy
  build) and is filed in `docs/issues/golden-exactness.md`; it is **not** a
  re-baseline, and tolerance mode remains the cross-machine gate. The
  manifest hash must match on every machine; if it does not, the canonical
  form has a defect.
- Then push `main` and delete `wip/regeneration-window` if it exists.
- Parity: exact against the regenerated goldens. G-here (with the exact run).
- Commit: `Regenerate the golden plates once for the typed seam and style`
- Done when: G-here green; `origin/main` has every window commit; the backup
  ref is gone.

#### P3.16 Façade: `fetch` and `paint`

- Implements D6, D8, D9, D21, A4; predecessors P3.15, P3.10.
- Owner files: create `src/pyntpot/maps/pipeline.py`,
  `tests/unit/maps/test_pipeline_fetch_paint.py`; edit
  `src/pyntpot/maps/__init__.py` (import leaves first, then the pipeline),
  `src/pyntpot/maps/plates.py` (`route_px`, `strands`),
  `tests/support/golden.py` (`paint_fixture` runs the new stages, below),
  `_port/paint.py` (delete `paint_activity`; its only callers are
  `tests/golden/test_parity.py:40`, which P3.1 already replaced with
  `paint_fixture`, and `tests/golden/make_golden_old.py:32`, which is left
  alone: it calls the pre-port `analysis.report.paint`, not
  `pyntpot._port.paint` (its line 17), is never run, only linted,
  `ty`-excluded and deleted at P9.3; `tests/unit/test_paint.py` has no
  `paint_activity` caller, and its `geo.journal_layers` and
  `geo.landmark_export` tests near lines 966 to 995 are not rewritten onto
  `fetch`: they only take the new key, below),
  `tests/support/paths.py` (`KEY` becomes the cache key; since P3.1 it is
  the only fixture-key constant, read by `tests/support/golden.py`,
  `tests/unit/test_geo.py` and `tests/unit/test_paint.py`, whose uses near
  `test_geo.py:801` and `test_paint.py:969-990` then pass the new key),
  `tests/unit/maps/test_cache.py` (the real-provider key assertion if P3.10
  could not add it), `test_import_order.py` (`maps.pipeline` in `MODULES`
  and `ADAPTERS`); `git mv` the three fixture payloads to
  `overpass-<key>.json`, `landcover-<key>.json`, `elevation-<key>.json` with
  the key from P3.10's pinned literal; edit
  `tests/architecture/test_coordinates.py` `_EXEMPT` (the same three files
  renamed: a rename, not a widening) and `tests/fixtures/lynmouth/README.md`.
  The rename moves no golden: the key is in neither the hash input nor the
  manifest, and the plates directory name is not compared.
- Names: `fetch(track: Track, cache: Cache, features: Features, elevation: Elevation, style: Style, places: Sequence[Mapping[str, Any]] = ()) -> Basemap`
  (calls `cache.ensure`, then `journal_layers` with `style.paint_style()`
  and `style.basemap`, because the card, ribbon and wet widths depend on the
  style; then sets `track_time` from `track.time` and `credits` from both
  providers with `dataclasses.replace`; places enter here, today
  `geo._place_marks` called from `geo.basemap`);
  `paint(basemap: Basemap, style: Style, out_dir: Path) -> Plates` (reuses
  current plates when the manifest hash matches, as `paint_activity` did).
  `paint` uses `basemap.card` and `basemap.layers` as given: a basemap
  fetched with one style and painted with another paints the first style's
  card. The docstring states this and ADR 0007 records it.
  `Plates` gains two fields set by `paint`, not in the manifest:
  `route_px: tuple[Pt, ...]`, the raw `Card.xy` image of `basemap.track`
  (today `[card.xy(x, y) for x, y in pts]` in `mapcard.compose`), and
  `strands: tuple[Pt, ...]`, **one** polyline of the same length,
  `separate_strands(route_px, style.route_ink().px * STRAND_GAP_WIDTHS)`
  (`separate_strands` returns a single polyline, `card.py:77-148`). Today
  `compose` draws, places and measures on that separated polyline, so
  `strands` is a pixel input (see "What the window freezes"); `route_px`
  is for consumers that want the unseparated route. Both fields default to
  `()`, so every other `Plates` construction (`load_plates`, and P4.7's
  `Cache.load_plates`) stays valid without a track; `pipeline.paint` fills
  them with `dataclasses.replace` on the `Plates` it painted or loaded.
  `pipeline.paint` replaces `paint_activity`, which is deleted here with
  its callers moved: from this slice `paint_fixture` is
  `Cache(work)`, `fetch` with the fixture providers
  (`tests/support/providers.py`, P3.7) and `Style.default()`, then
  `pipeline.paint`, then P3.13's
  `mapcard.compose(basemap, plates, style, None, labels=True)` (no picks,
  as today; it unpacks the image and the placed labels, P3.13), which still separates the route itself from `basemap.track`. G-self proves
  the switch is byte-identical before P3.17 makes `compose` read
  `plates.strands`.
- `fetch` raises `FetchError(RuntimeError)` (defined in
  `maps/pipeline.py`, message naming the key and the missing features
  path) when `journal_layers` returns `None`, which it does only when the
  features payload is absent after `cache.ensure`, for example a cache
  directory changed underneath.
- Tests: `fetch` with the fixture providers over a copy of the fixture dir
  calls no provider and returns a `Basemap` with the pinned road count and
  `credits` equal to the two fixture credits; `paint` writes three plates
  and returns a `Plates` whose `hash` equals the regenerated golden's and
  whose `route_px` and `strands` both have 400 points, with the first
  three `strands` points equal, by `pytest.approx(abs=1e-6)`, to pinned
  literals taken once from today's `mapcard.compose` (they pass through
  `Projection`'s `math.cos`, so they are not machine-independent and are
  not compared exactly; the pixel proof is P3.17's G-self run); a
  second `paint` repaints nothing (mtimes unchanged). `FetchError`: a
  test-local `_VanishingElevation(cache_dir: Path)` (a hand-written real
  provider, not golden-marked, fast because `journal_layers` returns
  before any geometry) wraps `FixtureElevation`, forwards `id` and
  `credit`, and its `grid()` unlinks every `overpass-*.json` in
  `cache_dir` before returning the fixture grid; since P3.10 pins
  `ensure`'s order (features written before `grid` is called),
  `fetch(track, Cache(tmp_path), FixtureFeatures(), _VanishingElevation(tmp_path), Style.default())`
  raises `FetchError` whose message contains the key and the features
  path.
- Parity: exact, regenerated goldens. G-here plus G-self.
- Commit: `Add the fetch and paint façade over typed stages`

#### P3.17 Façade: `letter` and `compose` (A3 shape)

- Implements A3 (shape), D6, D21; predecessor P3.16.
- Owner files: `src/pyntpot/maps/pipeline.py`, create
  `src/pyntpot/maps/annotations.py`, `src/pyntpot/maps/lettering.py`,
  `tests/unit/maps/test_annotations.py`,
  `tests/unit/maps/test_pipeline_letter_compose.py`; edit
  `tests/support/golden.py` (`paint_fixture` is now `fetch`, `paint`,
  `letter` with `annotations=None` (the parity run passes no picks today),
  `compose(..., attribution=False)`), `_port/mapcard.py`
  (`letter_card` moves into `maps/lettering.py`; `mapcard.compose` is
  deleted, because `pipeline.compose` now draws the raster by calling
  `mapcard._plates`, `mapcard._route` and `mapcard._paste_labels` through
  its `from pyntpot._port import mapcard` binding, with the arguments
  `mapcard.compose` passed them; P4.18 moves the three to
  `maps/compose.py`; delete `alphabet_sheet`, `ALPHABET_LINES`, `ALPHABET_W`,
  `ALPHABET_LEAD`, `ALPHABET_MARGIN` and `sport_from_gpx`, which have no
  caller), `_port/labels.py` (delete `_journal_picks`, `_journal_heuristic`,
  `_place_journal_labels`, `measure` with `DEFAULT_ADVANCE_PX` and
  `DEFAULT_SIDE_PX`, and `_text_width` with `CHAR_W`; `place`, `place_spans`
  and `home_labels` take the measure as a required argument, ending the
  flat default; one production text measure remains, `Hand.measure`),
  create `tests/support/measure.py` (`flat_measure(text, size)` with
  `measure`'s exact body and its two constants copied as literals, the
  deterministic measure the unit tests use), edit `tests/unit/test_paint.py`
  (every direct use of `lb.measure`, near lines 1971, 2713, 2714 and 2845,
  becomes `flat_measure`; every `lb.place(...)`, `lb.place_spans(...)` and
  `lb.home_labels(...)` call that relied on the default, near lines 2042,
  2073, 2080, 2267 to 2489, 2637, 2653, 2806 and 2875, passes
  `flat_measure` explicitly, so no expectation changes; the self-test at
  line 1753 that compares `lb.measure` with itself is deleted),
  `GLOSSARY.md` (add **span request**; the **span** row says it is the
  placed stretch), `test_import_order.py`.
- Names (`maps/annotations.py`, pydantic models, frozen, `extra="forbid"`;
  fields from what `labels.py` reads today):
  - `Landmark(name: str, kind: str = "", why: str = "", lat: float | None = None, lng: float | None = None)`;
    a bare string in `landmarks` is accepted as a name to look up among the
    basemap's candidates, as today.
  - `SpanRequest(name: str, kind: str = "climb", why: str = "", intent: str = "note", from_i: int | None = None, from_km: float | None = None, from_s: float | None = None, to_i: int | None = None, to_km: float | None = None, to_s: float | None = None)`
    with a validator requiring exactly one `from_*` and exactly one `to_*`.
  - `Annotations(landmarks: tuple[Landmark | str, ...] = (), places: tuple[str, ...] = (), roads: tuple[str, ...] = (), spans: tuple[SpanRequest, ...] = ())`.
    `roads` is accepted and not read: no road pick takes caller names
    today; the docstring says so as a capability fact.
  - `maps/lettering.py`: `Lettering` frozen dataclass:
    `labels: tuple[Label, ...]`, `spans: tuple[Span, ...]` (placed spans;
    the input is `SpanRequest`), `plate_path: Path | None`;
    `letter(plates: Plates, basemap: Basemap, annotations: Annotations | None, style: Style) -> Lettering`.
    Everything route-shaped it reads is `plates.strands`, exactly as
    `mapcard.compose` reads its separated `route_px` today: the inputs to
    `ground_labels`, `pick_roads`, `route_markers`, `place` and
    `draw_plate`, and the span arc length
    `cumulative_length(plates.strands, plates.card.scale)`. Spans resolve on
    that arc length, by point index (the same 400 indices as
    `basemap.track`) and, when `basemap.track_time` is set (D21), by time,
    so a span stated in seconds resolves. When `hand(...)` returns `None`
    (lettering off, or the face cannot be opened), `letter` logs it and
    returns `Lettering((), (), None)`; `compose` then hands over the bare
    card, which is what the output is today in that case (today labels are
    placed and never drawn).
  - `pipeline.compose(plates: Plates, lettering: Lettering, basemap: Basemap, style: Style, *, attribution: bool = True) -> PIL.Image.Image`
    (keyword-only flag, ruff `FBT`): `card = mapcard._plates(...)`, the
    route through `mapcard._route(card, ..., list(plates.strands), style.route_ink(), k)`
    with `k` the render-to-display ratio as today, then
    `mapcard._paste_labels(card, lettering.plate_path)` when the path is
    set (the route drawn from `plates.strands`, credits from `basemap.credits`;
    attribution is drawn in P3.18; until then the flag is accepted and
    `False` is the only tested value). `compose` takes no `Track`: nothing
    in it would read one.
- Tests: `SpanRequest` with two `from_*` values raises `ValidationError`;
  `letter` on the fixture returns labels whose names equal the window's
  pinned list (ADR 0006); a `Basemap` built with a synthetic `track_time`
  and a `SpanRequest(from_s=..., to_s=...)` lands on pinned indices;
  `labels.measure`, `labels._text_width`, `mapcard.alphabet_sheet` and
  `mapcard.sport_from_gpx` are gone (`hasattr` false); `compose` with
  `attribution=False` equals the regenerated `map.png` in G-self.
- Parity: exact, regenerated goldens. G-here plus G-self.
- Commit: `Add the letter and compose façade and delete the lettering shims`

#### P3.18 Attribution

- Implements D8; predecessors P3.17, P3.8, P3.9.
- Owner files: `src/pyntpot/maps/attribution.py`,
  `tests/unit/maps/test_attribution.py`, `src/pyntpot/maps/pipeline.py`
  (`compose` calls it), `test_import_order.py` (`MODULES`, `ADAPTERS`).
- Names: `attribution_text(credits: Sequence[Credit]) -> str` =
  `" · ".join(c.short for c in credits)` in the given order (features
  first, as `fetch` sets them), giving
  `"© OpenStreetMap contributors (openstreetmap.org/copyright) · elevation: NASA SRTM"`
  for the two shipped providers (`Credit.short`, P3.1, P3.8, P3.9);
  `draw_attribution(image, text, style: Style) -> None` bottom-right in the
  vendored hand face through `Hand` (from `_port.labels` until P4.5). The
  drawing recipe is the one `mapcard.alphabet_sheet` used before P3.17
  deleted it (`git show <P3.16 commit>:src/pyntpot/_port/mapcard.py`): the
  hand writes marks for each line, `paint.label_plate` rasterises them on a
  canvas the size of the text block, and the plate is pasted with its
  alpha; here the block is the attribution line at a pinned size
  `ATTRIBUTION_SIZE_PX = 11.0`, placed `ATTRIBUTION_MARGIN_PX = 8.0` from
  the bottom and right edges (module constants in `attribution.py`, which
  reads nothing else from `_port` than `Hand` and `label_plate`). The credits come from `Basemap.credits`, which exists since
  P3.4 and is set by `fetch`; no new `Basemap` field.
- Tests: the text for the two shipped credits is the pinned string; with
  `attribution=True` the bottom-right 5 percent of the image differs from the
  `attribution=False` image and nothing else does.
- Parity: exact, regenerated goldens (parity runs `attribution=False`).
- Commit: `Draw the data attribution on composed maps`

#### P3.19 CLI

- Implements D19; predecessor P3.18.
- Owner files: `src/pyntpot/maps/cli.py`, `tests/unit/maps/test_cli.py`,
  `pyproject.toml` (`[project.scripts] pyntpot = "pyntpot.maps.cli:main"`),
  `test_import_order.py`.
- Names: `main(argv: Sequence[str] | None = None) -> int`; subcommand
  `map TRACK.gpx -o OUT.png --cache DIR --contact STR [--style FILE] [--no-attribution]`;
  the flow is `Track.from_gpx`, `Cache(DIR)`, `OverpassFeatures(contact)`,
  `OpenTopoData(contact)`, `fetch`, `paint` into
  `cache.plates_dir(cache.key(track, features, elevation))`, `letter` with no
  annotations, `compose`; logging setup only inside `main`.
- Tests: `main(["map", fixture gpx, "--cache", <copy of fixture dir>, "--contact", "test", "--no-attribution", "-o", tmp/"out.png"])`
  returns 0 with no request made, observed without mocks: the cache
  directory's file listing and the three payloads' `st_mtime_ns` are the
  same before and after (`Cache.ensure` writes a payload for every fetch it
  makes, and fetches only what is missing; the fixture files are named by
  the key the real providers' ids give, P3.7 and P3.16, which P3.10's
  key-equality test proves), and the PNG matches the golden
  within the tolerance bound (the spec's verification step 2); a missing
  `--contact` exits 2.
- Parity: exact, regenerated goldens. G-here.
- Commit: `Add the pyntpot map command`

#### P3.20 Top-level exports and `__version__`

- Implements D6; predecessor P3.19.
- Owner files: `src/pyntpot/__init__.py`, `src/pyntpot/maps/__init__.py`,
  `tests/unit/test_public_api.py`, `docs/decisions/0007-public-api.md`,
  `test_import_order.py` (`pyntpot` in `MODULES`).
- Names: `pyntpot.__all__` holds exactly the D6 names: `Track`, `Basemap`,
  `Style`, `Plates`, `Lettering`, `Annotations`, `fetch`, `paint`, `letter`,
  `compose`, `Sheet`, `Brush`, `Canvas` (today's `paint.Plate`, exported
  under its glossary name), `stamp`, `wash`, `composite`, `Hand`, and
  `__version__`. `__version__` is today the literal `"0.1.0"`
  (`src/pyntpot/__init__.py:3`); it becomes
  `importlib.metadata.version("pyntpot")`, assigned after the imports
  (E402), not a second literal. Engine names still come from `_port` until
  P4; their `__module__` is fixed by P4. `pyntpot/__init__.py` is not in
  `maps` and is not an adapter; it may import `_port` names until P4 because
  nothing in `_port` imports `pyntpot.maps` or the top-level package at
  module level (rule 3). `ink/__init__.py` and `letters/__init__.py` do not
  change here: rule 1 forbids them re-exporting `_port` names; their
  `__all__` fills as P4 moves the engine in.
- ADR 0007 records the D6 names, D7's boundary, D21's attributes as built
  (`Basemap.projection`, `layers`, `track`, `track_time`; `Plates.manifest`,
  `paths`, `card`, `route_px` (the raw route in display pixels),
  `strands` (one polyline: the route separated where it runs twice, the
  line `compose` draws); `Lettering`), `fetch` taking the
  style (P3.16), `paint` using the basemap's card as given, and route ink
  fixed to the resolved default with no sport selection (P3.11a).
- Tests: `set(pyntpot.__all__)` equals the pinned set; every name resolves;
  `pyntpot.Sheet(64, 64, 8.0)` constructs (spec verification 6).
- Parity: exact, regenerated goldens. G-here.
- Commit: `Export the public names from the top-level package`

#### P3.21 Parity test on the façade

- Implements D5, D21; predecessor P3.20.
- Owner files: `tests/support/golden.py`, `tests/golden/test_parity.py`,
  `tests/golden/make_golden.py`.
- Change: `paint_fixture` has run `fetch`, `paint`, `letter`,
  `compose(..., attribution=False)` since P3.17, and `paint_activity` went
  in P3.16. This slice moves the golden harness onto the public names:
  `tests/support/golden.py` imports `fetch`, `paint`, `letter`, `compose`,
  `Style` and `Track` from `pyntpot` (P3.20) and `Cache` from
  `pyntpot.maps.cache`, never `pyntpot.maps.pipeline` or `_port`; no test
  under `tests/golden/` imports `_port` (except the historical
  `make_golden_old.py`).
- Done when: `grep -rn "_port" tests/golden tests/support/golden.py` lists
  only `make_golden_old.py`.
- Parity: exact, regenerated goldens. G-here plus G-self.
- Commit: `Drive golden parity through the public façade`

### P4. Split and layer

Every P4 slice is a move or a merge under parity: exact against the
regenerated goldens, G-here (with the exact run) plus G-self, unless stated.
Nothing in P4 changes the frozen items listed under "What the window
freezes"; a slice that would has to stop and report. A P4 slice moves the
unit tests of the code it moves into the mirrored test file in the same
commit, so `tests/unit/test_paint.py` (3943 lines, 161 tests) and
`tests/unit/test_geo.py` (830 lines, 68 tests) shrink as the work goes and are
deleted by the last slice that empties them (P4.18 at the latest), together
with their per-file-ignores, `ty` excludes and `line_budget.txt` lines.
A moved test leaves those interim exemptions behind: in its new file it
meets the `tests/**` rule set (only `PLR2004`, `ANN` and `FBT` ignored)
and `ty`, and the slice fixes what that raises, behaviour-neutral, as it
does for moved source. Measured at `f63bb61` over both files: 134 ruff
findings (111 `PLC0415`, 8 `RUF059`, 4 `D210`, 4 `RUF007`, the rest
single digits) and about 1269 `ty` diagnostics, 1221 of them
`invalid-argument-type` from the `PaintStyle(**kw)` helper pattern on 17
lines (`tiny_style(**over: object)` and its kin). The fix is to type those
helpers' keyword parameters `**over: Any` (or, once the code reads style
groups, to build groups with `dataclasses.replace`), never an ignore. The
fixes count toward the slice's line budget.
Architecture correction carried from `architecture.md`: `Hand` takes a
**setting**, not `Mark`s; `Mark` is what it produces.

Order and why. A2's design comes first (architecture Sequencing 3). The ink
engine moves next, so every `letters` module is built on `ink` and never on
`_port` (import rule 1). Then the letters slices, then the plate cache, then
the painter, then the style groups; the last style slice deletes
`_port/paint.py`, because `PaintStyle` is the last thing in it. Then
candidates, the geo split, the labels split, the contract and the pins.
The geo and labels splits run bottom-up (the lowest modules first) so that
no new `maps` module ever needs a `_port` import (import rule 2).

| New | Was (`294cc69`) | Slice |
|---|---|---|
| P4.1 | P4.1 | Design the hand's setting |
| P4.2 | P4.5 | Ink part 1: noise, sheet, raster, io, wash, pigment |
| P4.3 | P4.6 | Ink part 2: brush, tip, stamp, pad |
| P4.4 | P4.4 | Split the font and the trace |
| P4.5 | P4.2 | The hand writes settings |
| P4.6 | P4.3 | The nib plate in letters |
| P4.7 | P4.13 | One cache for fetches and plates |
| P4.8 | P4.7 (part) | Plate painter, part 1 |
| P4.9 | P4.7 (part) | Plate painter, part 2 |
| P4.10 | P4.8 (part) | Style groups, part 1: basemap readers |
| P4.11 | P4.8 (part) | Style groups, part 2: lettering readers; delete `paint.py` |
| P4.12 | P4.9 | Design candidates |
| P4.13 | P4.10 | Candidates facility |
| P4.14 | P4.11 | Split geo, part 1 (rings, paths, track index, relief, generalisation, rivers) |
| P4.15 | P4.12 | Split geo, part 2 (OSM, cover, assembly; `landmark_export`) |
| P4.16 | P4.14 | Split labels, part 1 (label types and spans; was part 2's content) |
| P4.17 | P4.15 | Split labels, part 2 (placement; was part 1's content) |
| P4.18 | P4.16 | Split labels, part 3 (picks, compose, strands) |
| P4.19 | P4.17 | Layers contract |
| P4.20 | P4.18 | Relax the pins |

#### P4.1 Design the hand's setting (A2, design)

- Implements A2 (design); predecessor P3.21.
- Owner files: `docs/decisions/0008-hand-writes-settings.md`,
  `src/pyntpot/letters/setting.py`, `tests/unit/letters/test_setting.py`,
  `GLOSSARY.md` (add **setting**, **mark**), `_port/labels.py` (imports
  `Mark` and `DEFAULT_LINE_PX` from `letters.setting` at module level, which
  rule 3 allows), `test_import_order.py`.
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
  `ink`, `size`, `pen`, `wash`) with `DEFAULT_LINE_PX`, which its `size`
  default reads (`labels.py` around 4040) and which `labels.py` keeps
  reading from there; `Pt` comes from `ink.polyline`.
- Tests: constructing the chosen type, its equality and hashing; `Mark`
  defaults pinned.
- Parity: exact, regenerated goldens (types only).
- Commit: `Decide the hand's setting interface`

#### P4.2 Ink engine, part 1: noise, sheet, raster, io, wash, pigment (A1)

- Implements A1 (engine half); predecessor P4.1.
- Owner files: create `ink/noise.py` (`value_noise`, `fbm`,
  `_value_noise_at`, `fbm_aniso`, `_box1`, `blur`, `edt`, `smoothstep`,
  `fill_holes`), `ink/sheet.py` (`Sheet`, `Canvas` renamed from `Plate`,
  `rgb`, `PAPER`), `ink/raster.py` (`fill_cov`, `stroke_mask`, `_edge`,
  `deform_ring`, `deform_rings`, the `Deform` alias), `ink/io.py`
  (`to_img`, `save_webp`, `save_alpha`, `save_rgba`), `ink/wash.py`
  (`flow_edge`, `bloom`, `wash`, `separated`, `shallow_water`,
  `fluid_modulate`), `ink/pigment.py` (`PIGMENTS`, `TRANSPARENCY`,
  `multiply_plate`, `km_rt`, `km_plate`, `composite`, the `Layer` alias);
  their tests under `tests/unit/ink/`; edit `_port/paint.py` (imports the
  moved names from `ink` at module level, which rule 3 allows; `PaintStyle`'s
  class-body default `paper_hex: str = PAPER` and its `pigments` and
  `pigment_transparency` default factories keep working unchanged), every
  importer (`_port/outlinefont.py` imports `ink.noise.edt` at module level),
  `src/pyntpot/__init__.py` (engine names from `ink`), `GLOSSARY.md`
  (sheet, canvas rows), `test_import_order.py`.
- Engine functions that took `PaintStyle` take the ink style group they read
  (`WashStyle`, `PaperStyle`). `_port.paint.paint` takes the `Style` that
  `pipeline.paint` already holds, passes `style.wash` and `style.paper` to
  the moved functions, and calls `style.paint_style()` once for its own
  remaining reads.
- Commit: `Move noise, sheet, wash and pigment into ink`

#### P4.3 Ink engine, part 2: brush, stamp, pad (A1)

- Predecessor P4.2.
- Owner files: create `ink/brush.py` (`Brush`, `brush_from_id`,
  `BRUSH_TREATMENTS`, `BRUSH_COLOURS`, `PEN_ROWS`, `scaled_brush`,
  `ink_aux`), `ink/tip.py` (`_tip_band`, `_tip_drift`,
  `_unfold`, `_fbm1`, `_spread`, `_smooth_path`), `ink/stamp.py` (`stamp`,
  decomposed into named steps to meet the complexity limits, 280 lines
  today), `ink/pad.py` (`InkPad`, `ink_density`, `_bleed`, `_grow`,
  `_reduce`); tests; edit `_port/paint.py` (its four `brush_from_id`
  callers: `plate_brushes`, `label_brushes` and the two near lines 3946 and
  4037), `_port/labels.py` (`draw_plate` gains a `brush: BrushStyle`
  parameter it passes to the label plate), `maps/lettering.py` (passes
  `style.brush`), `maps/attribution.py` if it reaches the label plate,
  other importers, `src/pyntpot/__init__.py`, `GLOSSARY.md` (brush, and a
  **brush sheet** row), `test_import_order.py`.
- The brush-sheet tables move **with** `brush_from_id`, because it reads all
  three (`paint.py` around 2028 to 2061) and both `ink` and `letters` call
  it. They are the brush-sheet catalogue: `BRUSH_TREATMENTS` is keyed by
  sheet row `"1"` to `"8"` (stroke treatment), `PEN_ROWS` names the rows
  that are a nib, and `BRUSH_COLOURS` is keyed by the id's three-letter
  prefix (`RIV`, `STR`, `MAJ`, `LAN`, `TRK`) and then the colour column.
  In `ink` a brush id `<PREFIX><row>-<column>` such as `MAJ2-a` is an
  opaque sheet cell name: `ink` never interprets the prefix as a map class.
  Which map class uses which cell (`style.brushes`, a `BrushStyle` or maps
  field per ADR 0005's table) stays where ADR 0005 put it.
  `brush_from_id(brush_id, width_display_px, scale, style: BrushStyle, override: str | None = None) -> tuple[Brush, str]`
  reads only `BrushStyle` fields (`brush_overrides`, `brush_jitter_px`,
  `brush_press_cell_px`, `brush_wobble_px`, `brush_step`,
  `brush_profile_px`, `pen_pool_radius_frac`, `pen_pool_gain`,
  `pen_load_px_frac`, `ink_starve` and the rest it reads today; P3.11a's
  pinned table puts every one of them in `BrushStyle`, because its
  reader's final home is `ink/brush.py`). If the code shows a read field
  the table puts elsewhere, add that group as a parameter; never regroup. `_port` callers that hold only a `PaintStyle`
  receive the `BrushStyle` from the façade (`style.brush`), passed down as
  a parameter, never rebuilt from `PaintStyle` fields.
- Parity: G-here plus G-self, byte-exact (the tables move verbatim).
- Commit: `Move the brush, stamp and ink pad into ink`

#### P4.4 Split the font and the trace (letters)

- Predecessor P4.3. Pure moves plus lint fixes (24 findings).
- Owner files: delete `src/pyntpot/_port/outlinefont.py`; create
  `letters/font.py` (`_Flatten`, `Glyph`, `OutlineFont`, `load`,
  `DEFAULT_FONT`), `letters/skeleton.py` (`_fill`, `thin`, `_ring`,
  `_crossings`, `_chains`, `_prune`, `_components`), `letters/trace.py`
  (`_half_width`, `_radii`, `_edge`, `_flank`, `_flanks`, `_from`,
  `_leaving`, `_dots`, `_centrelines`, `_extend`, `CENTRELINE`, `OUTLINE`;
  `edt` from `ink.noise`); `git mv src/pyntpot/_port/fonts src/pyntpot/letters/fonts`
  and resolve `DEFAULT_FONT` through `importlib.resources.files("pyntpot.letters")`;
  `tests/unit/letters/test_font.py`, `test_trace.py`; `GLOSSARY.md` rows for
  hand and trace; `line_budget.txt` loses `_port/outlinefont.py`;
  `test_import_order.py`.
- Commit: `Split the outline font into letters modules`

#### P4.5 The hand writes settings (A2, implementation)

- Implements A2; predecessor P4.4.
- Owner files: create `src/pyntpot/letters/hand.py`,
  `src/pyntpot/maps/lettering_marks.py` (furniture and Label-to-setting
  translation; an adapter while `Label` and `Span` live in `_port.labels`),
  `tests/unit/letters/test_hand.py`, `tests/unit/maps/test_lettering_marks.py`;
  edit `_port/labels.py` (delete `Hand`, `hand()`; `draw_plate` builds
  settings), `maps/lettering.py`, `maps/attribution.py` (now uses
  `letters.hand`; stays in `ADAPTERS` for `paint.label_plate` until P4.6),
  `src/pyntpot/__init__.py` (`Hand` from `letters`), `test_import_order.py`.
- Moves: `Hand.measure`, `_along`, `_flat`, `_vary`, `_wobble`, `_rng`,
  `_seed`, the per-instance variation, into `letters/hand.py`, reading
  `FaceStyle` (`label_face`, `label_route`, which open the face) and
  `HandStyle` (`label_seed`) per ADR 0005's table, and `letters.font`.
  `hand()` is deleted, and its one style read, the `labels` switch
  (`LetteringPolicy.labels`), moves to `letter` in `maps/lettering.py`,
  which returns `Lettering((), (), None)` when it is off, as P3.17's
  `letter` already does when `hand()` returns `None`. To maps: `KIND_INK`,
  `KIND_SLANT`, `KIND_TRACKING`, `SPAN_INTENT_INK`, `HOME_GLYPH`, `_ink`,
  `_span_marks`, `_label_marks`, `_baseline` (window choice), `_leader`,
  `_pin`, `_underline`; the furniture is drawn with `Hand.stroke` (or
  Shape 2's equivalent, per ADR 0008). `NO_LEADER` and `_outboard` stay in
  `_port.labels` (the placer and the span code read them too) and
  `lettering_marks` reads them through its module binding until P4.16
  moves them to `maps/lettering/label.py`. `_quad_at` goes to
  `maps/lettering_marks.py` with `_leader`, its only caller
  (`Hand._leader`, `labels.py` around 4375).
- Tests: `Hand` writes "Grasmere" along a straight synthetic line and gives
  the same marks twice for the same seed and different marks for another
  seed; a setting with slant 0.22 leans (mean x drift of strokes is positive);
  maps furniture: a label with a leader yields one leader mark.
- Commit: `Make the hand write settings and move map furniture to maps`
- Done when: `letters/` imports nothing outside `pyntpot.ink` and
  `pyntpot.letters`, and no name in `letters/` mentions tier, kind, intent,
  span or label.

#### P4.6 The nib plate in letters (A2, raster half)

- Implements A2; predecessor P4.5.
- Owner files: create `src/pyntpot/letters/nib.py`,
  `tests/unit/letters/test_nib.py`; edit `src/pyntpot/letters/style.py`
  (`NibGroups`), `src/pyntpot/maps/plates.py` and
  `tests/unit/maps/test_plates.py` (`dark_array`, below),
  `_port/paint.py` (delete
  `label_brushes`, `_pen_profile`, `_dark_field`, `label_plate`,
  `_backing_wash`, `MARK_WEIGHT`, `_HEX`), `_port/labels.py`
  (`draw_plate`), `maps/lettering.py`, `maps/attribution.py` (uses
  `letters.nib.plate`; leaves `ADAPTERS`), `_port/mapcard.py` if it still
  calls the label plate, `test_import_order.py`.
- Names: `nib_brushes(nib: NibStyle, face: FaceStyle, brush: BrushStyle, scale: float) -> Callable[[str, float], Brush]`;
  `NibSurface(canvas: Canvas, scale: float, dark: np.ndarray, gran_px: float)`
  (frozen dataclass, `eq=False`: what the nib writes on; `scale` is the
  display-to-render factor every mark is multiplied by and `nib_brushes`
  and `_backing_wash` take, which `Canvas` cannot give because it has no
  display width; callers pass `Card.render_scale`, P3.2's
  `render[0] / max(display[0], 1)`, exactly `label_plate`'s formula at
  `paint.py:3250` today) and
  `NibGroups(nib: NibStyle, face: FaceStyle, hand: HandStyle, brush: BrushStyle, paper: PaperStyle)`
  (frozen dataclass in `letters/style.py`: the groups the nib reads), so
  `plate(marks: Sequence[Mark], surface: NibSurface, groups: NibGroups, path: Path) -> Path | None`
  stays inside ruff's `max-args = 6` with no `noqa`.
  The group parameters are ADR 0005's table applied to what
  `label_brushes`, `_pen_profile`, `label_plate` and `_backing_wash` read
  (`_dark_field` reads no style field) (P3.11a, measured): `label_size_px`, the label pen,
  leader, wash and ink fields in `NibStyle`; `label_route` in `FaceStyle`;
  `label_seed` in `HandStyle`; the fields `brush_from_id` reads in
  `BrushStyle`; `paper_hex`, `sheet_seed`, `plate_lossless`,
  `paper_quality`, the five `paper_fibre*` fields and `gran_gamma` in
  `PaperStyle`. No field the nib reads is in a `maps` group; if the code
  shows one, stop and report (the table would be wrong, and fixing it moves
  a frozen digest).
  `render`, `display` and `gran_px`, read from the manifest mapping until
  now (P3.5), become `surface.canvas` (render `w` and `h`),
  `surface.scale` and `surface.gran_px`.
  **The Sheet is built in one place, `plate`.** `plate` builds its own
  `Sheet` exactly as `label_plate` does today (`paint.py:3251-3260`): size
  `surface.canvas.h` by `surface.canvas.w`, `gran_px=surface.gran_px`,
  and `seed`, `fibre`, `fibre_stretch`, `fibre_angle` and `fibre_cell`
  from `groups.paper` (`fibre_cell` scaled by `canvas.w / 1800.0`, floored at 1.6). This is
  not the painter's Sheet (`paint.py:3680`, `gran_px` from `gran_m / mpp`),
  so neither caller builds one, and the `PaperStyle` reads stay in the nib,
  as ADR 0005's table says.
  **The dark field is built in one place, `maps.plates.dark_array`.**
  `dark` is the darkness grid as an `h` by `w` float array in [0, 1].
  `letters` cannot import `maps.plates` (import rule 1), so the conversion
  lives beside `DarkGrid`:
  `dark_array(grid: DarkGrid | None, h: int, w: int) -> np.ndarray`, the
  body of today's `_dark_field` moved verbatim (bilinear resize of the
  grid; `np.full((h, w), 0.35, F32)` when the grid is `None` or its
  `values` are empty). The two callers of `plate` both call it, and
  nothing else converts a `DarkGrid`: `draw_plate` (in `_port/labels.py`,
  reached from `maps/lettering.py`'s `letter`, until P4.18 moves it to
  `maps/lettering/pipeline.py`; it imports `dark_array` inside its
  body, rule 3, and `letters.nib` at module level) and `maps/attribution.py`.
  `maps/plates.py` stays a leaf (numpy and PIL only).
- Tests: a plate from three marks on a 64 by 48 canvas with `scale=1.0` is
  written and has non-zero alpha only near the marks; the same marks with
  `scale=2.0` on a 128 by 96 canvas put the alpha near the doubled
  positions. `test_plates.py`: `dark_array(None, 4, 6)` and a `DarkGrid`
  with empty `values` are all 0.35 with shape `(4, 6)`; a uniform 2 by 2
  grid of 0.5 resizes to all 0.5.
- Commit: `Move the nib and label plate into letters`

#### P4.7 One cache for fetches and plates (A7)

- Implements A7, D9; predecessor P4.6.
- Owner files: `src/pyntpot/maps/cache.py`, `tests/unit/maps/test_cache.py`,
  `_port/paint.py` (delete `plates_dir`, `load_plates`, `PLATES_SUBDIR`,
  `paint_hash`, `labels_hash`), `_port/labels.py` (delete `plate_key`;
  `draw_plate` uses the new key), `src/pyntpot/maps/pipeline.py`,
  `src/pyntpot/maps/lettering.py`, `tests/unit/test_paint.py`.
- `Cache` gains `load_plates(directory: Path) -> Plates | None`,
  `base_key(basemap: Basemap, style: Style) -> str` (P3.12's form, moved
  verbatim, so the manifest hash does not move) and a lettering key derived
  from `style.lettering_digest()` and the lettering input, with no field
  list. Its input depends on ADR 0008: under Shape 1,
  `lettering_key(settings: Sequence[Setting], base_hash: str, style: Style) -> str`
  over the settings tuple; under Shape 2, the same signature over the
  sequence of call records the batching caller builds (name the record type
  as ADR 0008 does). `labels_hash`, `plate_key` and the 27-name key list are
  deleted. The label sidecar's `key` value changes form; it is a cache
  record, not a golden (P3.15).
- Tests: a lettering-only style change (`HandStyle.label_seed`, ADR 0005's one `HandStyle` field) leaves
  `base_key` unchanged and `paint` reports no repaint; a base-plate style
  change changes the lettering key (its base hash input moved).
- Commit: `Key plate caches by what was painted`

#### P4.8 Plate painter in maps, part 1: the job, brushes, water, cover, wood (A1)

- Implements A1 (maps half); predecessor P4.7.
- Owner files: create `maps/painter/__init__.py`, `maps/painter/job.py`,
  `maps/painter/brushes.py` (`plate_brushes`, `COVER_CFG`; the brush-sheet
  tables went to `ink/brush.py` in P4.3), `maps/painter/water.py` (the
  water phase, `sea_patches`, `coast_run`), `maps/painter/cover.py`,
  `maps/painter/wood.py` (with `_crossfade`, whose only caller is the wood
  phase, `paint.py` around 3836 and 3848), `tests/unit/maps/painter/__init__.py` and a test
  file per module; edit `_port/paint.py` (`paint` calls the three phases;
  `PaintStyle.cover_cfg`'s `default_factory=lambda: dict(COVER_CFG)`
  becomes the named module function `_default_cover_cfg()`, which imports
  `COVER_CFG` from `pyntpot.maps.painter.brushes` inside its body, rule 3),
  `test_import_order.py`.
- Shape (this is the hard part; follow it): `paint` today is 465 lines with
  about 30 locals shared across phases. State crosses phases through two
  values in `maps/painter/job.py`:
  - `@dataclass(frozen=True) class PaintJob`: `basemap: Basemap`,
    `style: Style`, `sheet: Sheet`, `canvas: Canvas`, `out_dir: Path`, and
    the seeded `np.random.Generator`s the phases share, as fields named for
    their use (one per seed expression in `paint` today, constructed in the
    same order so draws are unchanged).
  - `@dataclass class PlateStack` (mutable accumulator): the arrays one phase
    writes and a later one reads (`paper`, `wash_plate`, `water`,
    `wood_mask` and the others found in `paint`), plus `files` and `sizes`.
  - Each phase is `paint_<phase>(job: PaintJob, stack: PlateStack) -> None`
    and reads its fields from `job.style`'s groups as ADR 0005's table
    places them (A6 for painter fields happens here, as the code moves).
    No slice regroups a field: a phase that needs a field reads the group
    the table names.
- Commit: `Move the painter's water, cover and wood phases to maps`

#### P4.9 Plate painter in maps, part 2: relief, fluid, pen, ribbon, paper

- Implements A1; predecessor P4.8.
- Owner files: create `maps/painter/relief.py`, `maps/painter/fluid.py`,
  `maps/painter/pen.py` (today's ink phase; named for the pen plate so it
  does not read as the `ink` package), `maps/painter/ribbon.py`
  (`ribbon_alpha`; `_crossfade` went to `wood.py` in P4.8), `maps/painter/paper.py` (`paper_plate`,
  `relief_density`), `maps/painter/plates.py`
  (`paint_plates(basemap: Basemap, style: Style, out_dir: Path) -> Plates`:
  builds the job, runs the seven phases in today's order, writes the
  manifest with exactly the final keys); tests; edit `_port/paint.py`
  (delete `paint` and everything moved), `maps/pipeline.py` (`paint` calls
  `paint_plates`), `test_import_order.py`. Split any painter module that
  passes 400 lines.
- Where every remaining `_port/paint.py` name goes, by slice: `PaintStyle`,
  `from_style`, `from_resolved`, `with_display` stay until P4.11 deletes
  them with the file. Nothing else remains after this slice:
  `rgb`, `PAPER`, `Layer`, `Deform` went in P4.2; brushes and `InkPad` in
  P4.3; `label_*`, `_pen_profile`, `_dark_field`, `_backing_wash`,
  `MARK_WEIGHT`, `_HEX` in P4.6; `plates_dir`, `load_plates`,
  `PLATES_SUBDIR`, `paint_hash`, `labels_hash` in P4.7; `paint_activity` in
  P3.16; `chain_lines`, `deform_line` in P3.3; `parse_d`, `label_geom` in
  P3.13; `BRUSH_TREATMENTS`, `BRUSH_COLOURS`, `PEN_ROWS` with
  `brush_from_id` in P4.3; `COVER_CFG` and `plate_brushes` in P4.8.
- Commit: `Move the rest of plate assembly to maps`
- Done when: `grep -nE "^(def|class) " src/pyntpot/_port/paint.py` lists only
  `PaintStyle` (and its methods' module-level helpers, if any) and
  `with_display`.

#### P4.10 Style groups, part 1: basemap readers (A6)

- Implements A6; predecessor P4.9.
- Owner files: `_port/geo.py` (`journal_geometry` and `journal_layers` read
  `CardStyle`, `RibbonStyle` and `BrushStyle` instead of `PaintStyle`;
  `GeoOptions` is deleted and `basemap(...)` takes `BasemapStyle` plus a
  `clip_margin_m: float` argument), `maps/pipeline.py`, `maps/style.py`,
  `tests/unit/test_geo.py`, `tests/unit/maps/test_style.py`.
- `landmark_export` keeps its own option set beside it. In `_port/geo.py`
  it cannot be a module constant: building a `BasemapStyle` at module level
  needs a module-level `maps` import, which import rule 3 and P3.1's AST
  check forbid. So until P4.15 it is the function
  `candidate_basemap() -> BasemapStyle`, which imports `BasemapStyle` inside
  its body and returns
  `dataclasses.replace(BasemapStyle(), hillshade_mode="off", landmarks="all", landmark_max=LANDMARK_CAP, generalise=False)`,
  plus the plain constant `CANDIDATE_CLIP_MARGIN_M = 2600.0`, passed as
  `basemap`'s separate `clip_margin_m` argument (`BasemapStyle` has no
  margin field). P4.15 moves both to `maps/candidates/export.py`, where the
  function becomes the module constant `CANDIDATE_BASEMAP` (a leaf may
  build it at import) and the test follows.
  `BasemapStyle()`'s dataclass defaults are the `GeoOptions` class defaults
  (P3.11a), so `roads` and `rivers` keep the class defaults
  `landmark_export` uses today (`geo.py` around 4180), not the painter's
  `"key"`. Test: `asdict(geo.candidate_basemap())` equals the old
  `GeoOptions(hillshade_mode="off", landmarks="all", landmark_max=LANDMARK_CAP, generalise=False, clip_margin_m=2600.0)`
  field by field, without `clip_margin_m`, and the margin constant is
  2600.0 (literals copied before `GeoOptions` is deleted).
- The pinned digests from P3.11b and ADR 0005's field table must not change.
- Commit: `Read the basemap style groups directly in the layer code`

#### P4.11 Style groups, part 2: lettering readers; delete `PaintStyle` (A6)

- Implements A6; predecessor P4.10.
- Owner files: `_port/labels.py` (`home_labels`, `labels.py` around 4535
  and 4537, holds the last two of today's six `getattr(pstyle, ...)` sites
  with silent defaults, since P4.5 removed `Hand`'s three and `hand()`'s
  one: `home_glyph` reads `style.lettering` (`LetteringPolicy`) and
  `label_size_px` reads `style.nib` (`NibStyle`), with no defaults),
  `_port/mapcard.py`,
  `maps/lettering.py`, `maps/pipeline.py`, `maps/style.py` (delete
  `paint_style()`; `ADAPTERS` loses `maps.style` if it no longer imports
  `_port`), `_port/style.py` (delete `coerce_like`); delete
  `_port/paint.py` (`PaintStyle`, `from_style`, `from_resolved`,
  `with_display`) and its `line_budget.txt` line; `tests/unit/test_paint.py`,
  `test_import_order.py`.
- The pinned digests from P3.11b and ADR 0005's field table must not change.
- Commit: `Read style groups directly and delete the flat paint style`
- Done when: `grep -rn "PaintStyle\|GeoOptions\|paint_style" src` is empty.

#### P4.12 Design the candidates facility (A8, design)

- Implements A8 (design), D27; predecessor P4.11.
- Owner files: `docs/decisions/0009-candidates.md`, `GLOSSARY.md` (add
  **candidate**). Confirm with `grep` that the dead code is gone:
  `alphabet_sheet`, `sport_from_gpx` and the three label shims (P3.17),
  `with_display` (P4.11).
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
    `Basemap.candidates`, read by `journal_picks`, `journal_heuristic` and
    `settlements` since P3.13) is served; `Basemap.candidates` may change
    shape (it is outside the hash input); no Protocol (rule of three);
    testable on the Lynmouth fixture; parity exact.
- Commit: `Decide the candidates facility`

#### P4.13 Candidates facility (A8)

- Predecessor P4.12.
- Owner files: create `maps/candidates/` (modules for roads, climbs, places,
  landmarks, under 400 lines each, in that order lowest first; the facility
  shape is ADR 0009's) from `geo.journal_candidates`, `climbs`,
  `_felt_span`, `_steepest`, `ground_climbs`, `route_places`,
  `_place_view`, `_near_places`, `road_run`, `named_roads`, `_cell_index`,
  `_point_to_line`, `read_gpx_elevation` (replaced by `Track.ele`) with
  `GPX_ELEVATION`, `haversine`, `bearing`, `compass`, `COMPASS`,
  `cumulative`, and `classify`, `height_m`, `landmark_reach`,
  `landmark_rank`, `pick_landmarks` with these constants, which nothing
  else in `geo` reads at module level: `MONUMENT_HISTORIC`,
  `PLAQUE_MEMORIAL`, `LANDMARK_CLASSES`, `LANDMARK_REACH_M`,
  `OFFERED_CLASSES` (built from `LANDMARK_REACH_M` at module level, so it
  moves too; `_osm_layers` reads it inside its body, rule 3),
  `FABRIC_BUILDINGS`, `NAMED_BUILDINGS`, `TOURISM_DESTINATIONS`,
  `LANDMARK_RADIUS_M`, `VISIBLE_PER_M`, `REACH_CAP_M`, `LANDMARK_CAP`.
  The four query tuples the landmark code reads (`TOURISM_LANDMARKS`,
  `MANMADE_LANDMARKS`, `AMENITY_LANDMARKS`, `LEISURE_LANDMARKS`) are
  **not** moved: the candidates modules import them from
  `maps.providers.overpass` (P3.8's copies, equal by its test), and `geo`
  keeps its own copies for `fetch_overpass` until P4.15, so
  `test_overpass.py` is untouched. `landmark_export`,
  `candidate_basemap` and `CANDIDATE_CLIP_MARGIN_M` stay in `geo` (they call `basemap` and
  `overpass_path`, which move in P4.15) and import the moved names inside
  the function. `geo`'s remaining callers (`journal_layers` ->
  `journal_candidates`, `basemap` -> `pick_landmarks`, `_osm_layers` ->
  `classify`, `OFFERED_CLASSES`) import inside their bodies (rule 3).
  `tests/unit/maps/candidates/`; the climbs and `classify` tests at
  `test_paint.py` lines 907 to 962 (the `# --- climbs` section up to
  `# --- real data`) and the candidate tests in `test_geo.py` move here.
  The two real-data tests after it stay: the `journal_layers` test at 966
  until P4.15 moves it with `build_basemap`, the `landmark_export` test
  at 981 until P4.15 moves it to `test_export.py`;
  `test_import_order.py`. Every new module is a leaf (no `_port` import).
  `maps/candidates/__init__.py` holds a docstring and
  `__all__: list[str] = []` only, as `maps/lettering/__init__.py` does, and
  never imports `export` (P4.15) or re-exports anything: `osm` imports
  `candidates.landmarks`, which runs the package `__init__`, so a
  re-export of `landmark_export` would close the `export -> layers -> osm`
  cycle through the package. The cold-import test would catch it; this
  rule keeps it from being written.
- Commit: `Generalise map candidates into one facility`

#### P4.14 Split geo, part 1: rings, paths, track index, relief, generalisation, rivers

- Predecessor P4.13.
- Destination modules, lowest first (the **Placement rule** order):
  `maps/rings.py` (`Rings`, `signed_area`, `orient`, `point_in_ring`,
  `clip_ring`), `maps/svg_path.py` (`path_d`, `stroke_d`, `rings_path`,
  `parse_path`, moved verbatim: their 0.1 m formatting is the vector map's
  output format, frozen), `maps/track_index.py` (`TrackIndex`, `_densify`),
  `maps/relief.py` (`_png`, `_resample`, `_shade`, `hillshade_png`,
  `marching_squares`, `_stitch`, `_grid_line_to_metres`, `_pad`,
  `shade_bands`, `contour_lines`, `sea_rings`, `_ring_is_wet`),
  `maps/relief_strokes.py` (`Field`, `_jitter`, `hachures`,
  `wave_strokes`), `maps/generalise.py` (`_fill_ring`, `rasterise`,
  `_spread`, `_components`, `declutter`, `trace_mask`, `generalise`,
  `jitter_ring`, `scatter`, `generalise_layer`), `maps/rivers.py`
  (`channel`, `_ring_boxes`, `_ray_to_ring`, `_ring_at`, `_accepted`,
  `WIDTH_STEP_M`, `WIDTH_RUN_M`, `CHANNEL_EASE_SAMPLES`,
  `measured_width_m`, `painted_width_px`, `major_rivers`). Measured at
  `33f12be`: relief reads `Rings`, `TrackIndex`, `path_d`, `stroke_d`,
  `point_in_ring`; generalisation reads `orient`, `signed_area`,
  `_ring_is_wet`, `marching_squares`, `_jitter`; rivers read `_densify`,
  `point_in_ring`; everything else they read is already in `ink` (P3.3) or
  `maps.projection` (P3.4). So every new module is a leaf: none imports
  `_port`.
- Owner files: the seven modules above; their tests under
  `tests/unit/maps/` (the matching tests leave `test_geo.py` and
  `test_paint.py`); edit `_port/geo.py` (its remaining code imports the
  moved names inside function bodies, rule 3; a module-level reader of a
  moved name moves with it or becomes a function), `_port/labels.py` and
  `_port/mapcard.py` if they call a moved name, `test_import_order.py`.
- Commit: `Move rings, paths, relief, generalisation and river width out of geo`

#### P4.15 Split geo, part 2: OSM layers, cover, assembly

- Predecessor P4.14.
- Destination modules, lowest first: `maps/osm.py` (`_osm_layers`, 241
  lines today, decomposed per layer; `_geom`, `_polygon_rings`, `_dedupe`,
  `_soften` (its only reader is `_osm_layers`, `geo.py` around 2328),
  `BURIED_FRAC`, `LANDMARK_TAG_KEYS`), `maps/cover.py` (`COVER_TAGS`,
  `COVER_ORDER`, `cover_rings`, `wood_rings`, `coastline_chains`,
  `sea_from_coast`), `maps/layers.py` (`journal_geometry`, `_drawn`,
  `journal_layers` renamed `build_basemap`, `basemap`, `_derived`,
  `scale_for`, `REFERENCE_SPAN_M`, `MAX_SCALE`, `_place_marks`,
  `_relief_layers`, `_sea_path`), then a new top module
  `maps/candidates/export.py` (never imported by `candidates/__init__.py`,
  P4.13) with `landmark_export`, `CANDIDATE_BASEMAP`
  (P4.10's `candidate_basemap()` as a module constant) and
  `CANDIDATE_CLIP_MARGIN_M`. Not `maps/candidates/landmarks.py`: that
  would close a cycle, because `landmark_export` reads `basemap`
  (`layers`), `basemap` reads `_osm_layers` (`osm`), and `_osm_layers`
  reads `classify` and `OFFERED_CLASSES` (`candidates/landmarks`, P4.13).
  Measured at `f63bb61`: `landmark_export` reads `basemap`,
  `journal_candidates`, `climbs`, `ground_climbs`, `route_places`,
  `_place_view`, `named_roads`, `cumulative`, `LANDMARK_CAP`, `simplify`,
  `track_projection` and the cache paths; nothing under `src/` reads
  `landmark_export` (only `test_paint.py` near line 984, which moves to
  `tests/unit/maps/candidates/test_export.py`); no P4.13 candidates name
  reads an `osm`, `cover`, `layers` or `export` name. So the edges run
  `export -> layers -> cover/osm -> candidates/* -> ink/projection`, and
  nothing points back. Every module is a leaf; `_port/geo.py` is deleted
  at the end of this slice, so no edge to it remains.
- Where every remaining `geo` name goes (the **Placement rule** applied at
  `33f12be`; names moved by earlier slices are not repeated):

  | Name | Goes |
  |---|---|
  | `log` | each new module defines its own `logging.getLogger(__name__)` |
  | `Pt` | already `ink.polyline.Pt` |
  | `OVERPASS_QUERY`, `LANDCOVER_QUERY`, the ten tag tuples and strings P3.8 copied | deleted; `osm.py` and `cover.py` import the tuples from `maps.providers.overpass`; the copy-equality test in `test_overpass.py` goes |
  | `OVERPASS_URL`, `OVERPASS_URLS`, `ELEVATION_URL`, `MARGIN_M`, `ELEV_N`, `LANDCOVER_MARGIN_M`, `GPX_POINT`, `bounding_box`, `_get`, `fetch_overpass`, `fetch_elevation`, `fetch_landcover`, `fetch_activity`, `read_gpx` | deleted, replaced by the providers, `Track` and `Cache` (P3.6 to P3.10); `test_track.py` keeps its pinned `bounding_box` literal and drops the comparison with `geo.bounding_box` |
  | `overpass_path`, `elevation_path`, `landcover_path` | deleted; their readers (`basemap`, `wood_rings`, `coastline_chains`, `cover_rings`, `build_basemap`, `landmark_export`) take the paths from `Cache.features_path`, `landcover_path`, `elevation_path`, which give the same file names (P3.10) |
  | `GeoOptions` | already deleted (P4.10) |

- Owner files: the modules above and their tests (the `journal_layers`
  real-data test at `test_paint.py` near line 966 moves to
  `tests/unit/maps/test_layers.py`); delete `_port/geo.py`,
  its `line_budget.txt` line, and the emptied `tests/unit/test_geo.py` with
  its per-file-ignores block, `ty` exclude and `line_budget.txt` line;
  `tests/unit/maps/providers/test_overpass.py` (the copy-equality test),
  `tests/unit/maps/test_track.py`, `_port/labels.py` and `_port/mapcard.py`
  callers of `geo` names (inside function bodies, rule 3),
  `maps/pipeline.py` (calls `build_basemap`), `test_import_order.py`
  (`pyntpot._port.geo` leaves `MODULES`).
- Commit: `Split geo into map layer modules and delete it`

Labels split order (P4.16 to P4.18). The destination modules under
`maps/lettering/`, lowest first, are: `label`, `span_clear`, `span_line`,
`span_sides`, `spans`, `placement_costs`, `placement_along`, `placement`,
`picks`, then `pipeline` (the adapter, renamed from `maps/lettering.py`).
The three slices move them bottom-up in that order, so a module created by
one slice imports only modules created before it, `ink`, `letters`, and
`maps` leaves; none imports `_port`. `maps/lettering/__init__.py` holds a
docstring and `__all__: list[str] = []` only, so importing a leaf never
imports the adapter. The tables below are the **Placement rule** applied at
`33f12be` with this order (each module defines its own `log`); they list every `labels.py` top-level name the
slice text does not, so nothing is homeless. Names already gone by then:
the P3.3 polyline helpers, `measure`, `_text_width`, `CHAR_W`,
`DEFAULT_ADVANCE_PX`, `DEFAULT_SIDE_PX` and the three shims (P3.17), `Mark`
and `DEFAULT_LINE_PX` (P4.1, `letters.setting`), `Hand`, `hand`, `_seed`,
`_quad_at` and the furniture names (P4.5), `plate_key` (P4.7). Measured
cross-module reads that forced a name below its listed home: `_seg_in_box`
(read by `span_clear`), `span_bearing` (read by `span_clear._span_label`),
`dedupe_names` (read by `placement.place`), `feature_px` (read by a `label`
helper).

#### P4.16 Split labels, part 1: label types and spans

- Predecessor P4.15.
- Owner files: create `maps/lettering/__init__.py`;
  `maps/lettering/label.py` (`Label`, `Span`, `Anchor`, `Box`, `Measure`,
  the seven `TIER_*`, `wrap_forms`, `block_size`, `NO_LEADER`, `_outboard`,
  `feature_px`, and `NO_WRAP_KINDS`, `MAX_LINES`, `WRAP_LEADING`,
  `WRAP_MIN_CHARS`, `WRAP_MIN_SHARE`, `SPAN_GROUND`, `SPAN_EFFORT` (test
  caller only), `WET_PX_DEFAULT`, `ROAD_PX_DEFAULT`, `WET_SPREAD`); `maps/lettering/span_clear.py`
  (`clear_of_route`, `_route_near`, `_clear_of`, `_longest_clear`,
  `_span_ticks`, `_span_label`, `span_bearing`, `_seg_in_box`, `_foot_on`,
  `_nearest_on`, `_away_from`, `_blur`, `_beside`, `_span_normal`,
  `_side_at` (test caller only), `SPAN_TICK_CAPS`,
  `SPAN_ALONG_MAX_BEARING_DEG`, `SPAN_CLEAR_CAPS`, `CLEAR_PASSES`,
  `CLEAR_BLUR`, `CLEAR_PUSH_CAP`, `CLEAR_KEEP_FRAC`, `SPAN_ANCHOR_FRACS`);
  `maps/lettering/span_line.py` (`span_line`, `shape_curve`,
  `_corners_of`, `_turn_over`, `_drop_folds`, `_forward_only`, `_uncross`,
  `_first_loop`, `doubling_px`, `_mouth_path`, `_resample`,
  `SPAN_OFFSET_CAPS`, `SHAPE_SIMPLIFY_FRAC`, `SHAPE_STEP_FRAC`,
  `DOUBLED_BACK_OFFSETS`, `SHAPE_CORNER_DEG`, `FOLD_KEEP_FRAC`,
  `MOUTH_NEAR_FRAC`, `MOUTH_MIN_SPAN`); `maps/lettering/span_sides.py`
  (`route_turn`, `bend_strength`, `_outward`, `_convex_side`,
  `_curved_side`, `_freer_side`, `_mark_broken`, the six
  `SPAN_CURVE_*`); `maps/lettering/spans.py` (`resolve_spans`,
  `_span_index`, `place_spans`, `_drawn_side`, `_rung`, `_on_line_cost`,
  `_feature_cost`, `_nearest`, `SPAN_MAX`, `SPAN_RUNG_CAPS`,
  `SPAN_SIDE_SWAP_MARGIN`, `SPAN_FEATURE_COST`, `SPAN_LINE_REACH_CAPS`,
  `SPAN_LINE_COST`); delete `_side_of` (no caller anywhere); tests under
  `tests/unit/maps/lettering/`; `git mv` `maps/lettering.py` to
  `maps/lettering/pipeline.py`; edit `_port/labels.py` (callers import the
  moved names inside function bodies, rule 3), `maps/lettering_marks.py`
  (imports `Label`, `Span`, `NO_LEADER`, `_outboard` from
  `maps.lettering.label`; leaves `ADAPTERS` if nothing else of `_port`
  remains in it), `maps/pipeline.py`, `test_import_order.py` (`ADAPTERS`
  follows the rename), `tests/unit/test_paint.py` (the moved tests leave
  it).
- Commit: `Move label types and span lettering into maps lettering`

#### P4.17 Split labels, part 2: placement

- Predecessor P4.16.
- Owner files: `maps/lettering/placement_costs.py` (`_crossings`,
  `_on_road`, `_overlap`, `_separation`, `_darkness`, `_on_paper`,
  `_off_own`, `_off_own_feature`, `_is_own_feature`, `_near_route`,
  `SEPARATION_CAP_PX`, `ROUTE_REACH_PX`, `ROUTE_ON_COST`, `EDGE_PX`,
  `OWN_FEATURE_SLACK_PX`, `OWN_FEATURE_COST_PX`, `OWN_LINE_PX`,
  `OWN_LINE_FRAC`); `maps/lettering/placement_along.py` (`_place_along`,
  `_place_flat`, `_best_flat`, `_curved_boxes`, `lift_px`,
  `lift_baseline`, `lift_middle`, `_tilt`, `_tilt_max`, `_mark_gap`,
  `_mark_through`, `_reading`, `_offset_line`, `_window`, `_turning`,
  `_bow`, `_on_line`, `_bisect`, and `ROAD_CROSS_COST`, `LEADER_COST_PX`,
  `LEADER_RUNGS`, `SEPARATION_WEIGHT`, `ANCHOR_PULL`, `MAX_TURN_DEG`,
  `MAX_BOW_FRAC`, `MAX_TILT_DEG`, `MAX_LOCAL_TILT_DEG`,
  `TILT_EXEMPT_KINDS`, `TWO_SIDED_KINDS`, `RIVER_GROUND_FRAC`,
  `IN_WATER_ROAD_COST`, `SPAN_MAX_TURN_DEG`, `SPAN_MAX_BOW_FRAC`,
  `NEAR_RUNGS`, `NEAR_GAP_COST_PX`, `SPAN_MARK_SLACK`, `SPAN_MARK_COST_PX`,
  `SPAN_MARK_THROUGH_COST`, `SPAN_INBOARD_COST`, `WRAP_COST`, `LIFT_CAPS`,
  `LIFT_SPAN_CAPS`, `LIFT_FEATURE_FRAC`, `INK_ASCENT_CAPS`,
  `INK_DESCENT_CAPS`, `RIVER_REPEAT_FRAC`); `maps/lettering/placement.py`
  (`place`, `_place`, `_leader_px`, `_centre`, `_seat`, `_unseat`,
  `_reseat`, `_seat_cost`, `_pair_cost`, `_swap_seats`,
  `_uncross_leaders`, `_places_to_avoid`, `_route_for`, `dedupe_names`,
  `_words`, `_one_place`, `_stem`, `QUALIFIERS`, `MAJOR_RIVER_LABELS`,
  `NAME_FAMILY`, `NAME_FAMILY_DEFAULT`, `NAME_ALLOWANCE`,
  `NAME_ALLOWANCE_DEFAULT`, `NEAR_DUPLICATE_M`,
  `NEAR_DUPLICATE_EXTRA_WORDS`, `LEADER_UNCROSS_PASSES`,
  `SPAN_OWN_ROUTE_FRAC`, `ALONG_BONUS`, `MIN_CURVED_CHARS`,
  `SETTLEMENT_GROUND_SIZES`); tests; edit `_port/labels.py`,
  `_port/mapcard.py`, `maps/lettering/pipeline.py` (callers),
  `tests/unit/test_paint.py`, `test_import_order.py`.
- Commit: `Move label placement into maps lettering`

#### P4.18 Split labels, part 3: picks, compose, strands; delete the old modules (A3)

- Implements A3 (file split); predecessor P4.17.
- Owner files: `maps/lettering/picks.py` (`settlements`, `pick_settlements`,
  `pick_rivers`, `pick_roads`, `road_ref`, `route_markers`, `home_places`,
  `home_labels`, `ground_labels`, `journal_picks`, `journal_heuristic`,
  `named_lines`, `road_lines`, renamed to say what they pick, with
  `settlement_budget`, `_nearest_to_ends`, `river_name`, `road_min_px`,
  `IN_WATER_CAPS`, `SETTLEMENT_RANK`, `MERGE_M`, `SETTLEMENT_MAX_OFF_M`,
  `SETTLEMENT_FLOOR`, `SETTLEMENT_SEPARATION_PX`,
  `SETTLEMENT_ENDPOINT_FRAC`, `RIVER_MAX`, `RIVER_REL_FLOOR`,
  `MAJOR_RIVER_TWICE_FRAC`, `ROAD_MIN_CAPS`, `ROAD_MAX`,
  `HOME_NAME_DROP`), `maps/lettering/pipeline.py` gains `draw_plate`
  (its only caller is `letter` there, `letter_card` before P3.17),
  `maps/compose.py` (`_plates`, `_route`, `_paste_labels`, which
  `pipeline.compose` has called through its `mapcard` binding since
  P3.17), `maps/strands.py` (`separate_strands`,
  `STRAND_GAP_WIDTHS` and the rest of `_port/card.py`), `RouteInk` and the
  route constants into `maps/style_groups.py` (which then leaves
  `ADAPTERS`); delete `_port/labels.py`, `_port/mapcard.py`,
  `_port/card.py`, `_port/style.py`, the emptied `tests/unit/test_paint.py`,
  their `line_budget.txt` lines and the test file's per-file-ignores block
  and `ty` exclude; `maps/lettering/pipeline.py` and `maps/pipeline.py`
  import only `maps` modules and leave `ADAPTERS`, which is now empty;
  `test_import_order.py`.
- Commit: `Move picking and compose into maps and delete the port modules`

#### P4.19 Layers contract; delete `_port`

- Implements D2, D5 end state; predecessor P4.18.
- Owner files: `pyproject.toml` (`[[tool.importlinter.contracts]]` layers
  `pyntpot.maps`, `pyntpot.letters`, `pyntpot.ink`; a forbidden contract:
  `pyntpot.ink` and `pyntpot.letters` may not import `httpx` or
  `pydantic`; the `src/pyntpot/_port/*` per-file-ignores and the `_port`
  `ty` exclude removed); delete `src/pyntpot/_port/`; empty
  `tests/architecture/exemptions/line_budget.txt`, `gates_off.txt` and
  `NOTES.md` to their header comment only; `docs/decisions/0010-layers-contract.md`
  (records the contract and, as its A1 note, that the brush-sheet catalogue
  lives in `ink/brush.py` with brush ids as opaque sheet cell names, while
  the class-to-cell choice stays in the style groups, P4.3);
  `BOUNDARIES.md`, `docs/architecture.md`, the boundary paragraph of
  `CLAUDE.md`, `GLOSSARY.md` "Today" columns; `test_import_order.py` (the
  `_port` modules leave `MODULES`; the `ADAPTERS` tuple and its check are
  deleted, the contract replaces them).
- Tests: `uv run lint-imports` passes both contracts; `test_import_order.py`
  lists the final modules.
- Commit: `Add the layers contract and delete the port package`

#### P4.20 Relax the parity pins

- Implements D22; predecessor P4.19.
- Owner files: `pyproject.toml` (`numpy>=2.5.2`, `pillow>=12.3.0`,
  `fonttools>=4.63.0`), `uv.lock`, `CONTRIBUTING.md` (the pin sentence),
  `.github/dependabot.yml` (drop the three ignores).
- One commit. G-here (with the exact run) plus G-self with the relaxed lock
  (`uv lock` must keep the same resolved versions so parity is untouched).
  This slice claims nothing about the maintainer's machine: that exact run
  is ADR 0006's follow-up check, not a gate here.
- Commit: `Relax the parity pins to floors`

### P5. Property tests, coverage baseline, mutation, benchmarks

Implements D17 and the spec's coverage open question (answered by the
maintainer on 2026-10-07: a measured baseline that ratchets, not 100 percent
before the first release). Fattened at P5.0 from the four-bullet sketch;
every tool behaviour below was read from the installed packages (mutmut
3.8.0, pytest-codspeed 5.0.3, pytest-benchmark 5.3.0, hypothesis 6.168.3,
coverage 7.16.2, pytest-cov 7.1.0) and the CodSpeed action's current docs.

**Rules for the whole phase.**

- P5 adds tests, CI jobs, three helper scripts, two ADRs and one docs page.
  **It does not edit `src/`.** No slice needs G-self, because no pixel can
  move; every slice runs G-here.
- **A failing property is a finding, not a test to fix.** If a property in
  P5.1 fails against the current code, stop that property: do not weaken
  it, widen a bound, add `assume` to dodge the counterexample, or mark it
  `xfail`. Record the shrunk counterexample in `docs/issues/<name>.md` and
  in `specs/001-port/p5-run-log.md`. The fix is its own slice: it touches
  `src/`, runs G-here plus G-self, and may need a golden decision. P5.1
  lands without the failing property, and the issue file names it. This is
  a correctness stop, not a scope choice; the rest of P5 carries on.
- P5 measures and does not optimise (spec, out of scope).
- **Timings come before scope, and a stated rule makes every choice.** No
  slice stops to ask. Each slice measures first, then applies the rule
  written in it: mutation scope and shard count (P5.3a), which benchmarks
  stay and at what `display_px` (P5.4), the coverage thresholds (P5.2) and
  any `max_examples` cut (P5.1). Each slice's hand-off appends its measured
  numbers and the choice the rule made to `specs/001-port/p5-run-log.md`,
  so that file is in every slice's owner files. The final HTML report after
  P5 is built from that log and states every timing and every choice.
- **`maps` is not assumed covered by the goldens.** A golden test guards a
  change that should not move pixels. A visual-refinement change moves
  them on purpose and regenerates the goldens, which then accept whatever
  the code does. So `maps` needs its own behavioural checks. P5 measures
  `maps` alongside `ink` and `letters`. How deep `maps` testing goes is a
  later phase's decision, made from the numbers P5 records.
- Branch and PR: P5.1, P5.2, P5.3a and P5.4 land as one commit each on a
  branch `p5-quality` and go to `main` through one PR. That way the two
  PR-only jobs (mutation on changed functions, CodSpeed) each run once
  before the merge. P5.3b follows the first nightly run on `main`, as its
  own short PR.
- Order: P5.1 → P5.2 → P5.3a → P5.4 → (merge) → P5.3b. The order is
  sequential because P5.1's Hypothesis settings feed the mutation config,
  P5.2 measures coverage after the property tests exist, and P5.2, P5.3a
  and P5.4 all edit `pyproject.toml`, `.gitignore` or `ci.yml`.
- `.gitignore` is append-only across P5: each slice adds its own lines.

**Tool facts the slices rely on** (verified at P5.0; recheck only if a
version moves):

- Hypothesis auto-loads its built-in `ci` profile when `CI` is set (GitHub
  Actions sets it). That profile sets `derandomize=True`, `deadline=None`,
  `database=None`, `print_blob=True` and suppresses `too_slow`, so CI
  property runs are deterministic. `--hypothesis-profile=ci` selects the
  same profile anywhere.
- pytest-randomly does not seed Hypothesis: `--randomly-seed` does not
  reproduce a property failure. The printed `@reproduce_failure` blob or
  `--hypothesis-seed=N` does.
- `@given` refuses function-scoped fixtures (`FailedHealthCheck`). Property
  tests take module-scoped fixtures only (the `hand` fixture, as in
  `tests/unit/letters/test_hand.py:19`), or build inputs inside the test.
- With both plugins installed, `benchmark` is pytest-benchmark's fixture.
  Under `--codspeed`, or under the CodSpeed action (`CODSPEED_ENV`),
  pytest-codspeed blocks pytest-benchmark, takes over the `benchmark` name
  and deselects every test without the fixture or the `benchmark` marker.
  Both plugins register the `benchmark` marker, so `-m benchmark` and
  `-m "not benchmark"` are valid under `--strict-markers` before P5.4
  registers it in `pyproject.toml`.
- `--benchmark-disable` in `addopts` works with `--codspeed` (tried at
  P5.0): a plain run calls each benchmarked function once without timing,
  `--benchmark-enable` restores timing, and `--codspeed` benchmarks
  normally.
- pytest-benchmark warns `Benchmark fixture was not used at all` through
  `node.warn` when a test takes `benchmark` but never calls it. Under
  `filterwarnings = ["error"]` that test errors.
- pytest-cov reads `[tool.coverage.report] fail_under` as the threshold for
  the **whole** measured package. A per-package threshold therefore goes in
  a separate `coverage report --include=... --fail-under=N` step (exit 2
  below N), never in that table.
- `uv run --python 3.14` against the project re-creates `.venv` on that
  interpreter. A second interpreter is measured in its own environment,
  `UV_PROJECT_ENVIRONMENT="$SCRATCH/venv-3.14"`, so `.venv` stays on 3.13.
  CPython 3.14.6 is downloadable here.
- mutmut has **no** "mutate only the diff" mode. `use_git_change_detection`
  only invalidates its cache. What it does support:
  - It restricts which mutants are tested by fnmatch patterns over mutant
    names. A function `f` in `src/pyntpot/ink/polyline.py` is
    `pyntpot.ink.polyline.x_f`, and a method `m` of class `C` is
    `pyntpot.ink.sheet.xǁCǁm`. Each mutant appends `__mutmut_<n>`. The
    module part is built as `get_mutant_name` builds it: the path without
    `src/` and `.py`, `/` mapped to `.`, and a trailing `.__init__`
    dropped (`src/pyntpot/ink/__init__.py` gives `pyntpot.ink.x_f`).
  - It generates every mutant in `only_mutate` even under a pattern, and
    runs the stats collection, on every run; only the pattern's mutants
    are tested.
  - A pattern list that matches no mutant fails an `assert` in
    `collect_source_file_mutation_data` with the message
    `Filtered for specific mutants, but nothing matches`, and `mutmut run`
    exits non-zero. An empty pattern list means every mutant.
  - It does not mutate a function or method carrying any decorator except
    a single `staticmethod` or `classmethod` (`file_mutation.py:330`), so
    `@property`, `@functools.cache` and the like have no mutants.
  - It runs pytest with cwd `mutants/` on copied `tests/`, so
    `support.REPO_ROOT` resolves to `mutants/`. `copy_src_dir` copies
    every file under `source_paths`, data files included.
  - `mutmut run` exits 0 when mutants survive.
  - `mutmut export-cicd-stats` writes `mutants/mutmut-cicd-stats.json` with
    the keys `killed`, `survived`, `total`, `no_tests`, `skipped`,
    `suspicious`, `timeout`, `check_was_interrupted_by_user` and `segfault`.
    In a restricted run, the untested mutants count in `total` only, so the
    other counts of several restricted runs add up correctly.
  - It always passes `-p no:randomly`.
  - It needs `fork` (Linux and macOS).
  - `only_mutate` takes globs ending in `.py` or `*`, matched with
    `fnmatch.fnmatch(path, glob)` (`_should_include_for_mutation`), where
    `*` spans `/`.

#### P5.0 Fatten P5; plan-reviewer pass

- This section. A plan-reviewer agent reviews it, and P5.1 does not start
  until the review passes. `tasks.md` gains P5.0, and P5.3 splits into P5.3a
  and P5.3b.
- `spec.md`: the coverage open question is answered (see the P5 preamble).
  Move it to a resolved line that names ADR 0011.
- Commit: `Fatten P5 into slices`

#### P5.1 Property tests

- Implements D17 (Hypothesis); predecessor P5.0.
- Owner files:
  - `tests/property/__init__.py`, whose docstring is
    `"""Property tests: algorithmic invariants under generated inputs."""`.
    The package keeps basenames such as `test_noise.py` from clashing with
    `tests/unit`.
  - `tests/property/test_{projection,polyline,rings,noise,stamp,pigment,hand}.py`.
  - `tests/support/properties.py`. It holds only
    `UNTIMED = settings(deadline=None)`, with a docstring explaining why: a
    wall-clock deadline is a flake source on shared runners and under
    mutmut's trampolines, and these tests prove invariants, not speed.
    Every `@given` test is decorated `@UNTIMED`.
  - `CONTRIBUTING.md`: one paragraph on reproducing a property failure. Use
    the printed blob or `--hypothesis-seed`; `--randomly-seed` alone does
    not reproduce one. CI runs derandomised.
  - `specs/001-port/p5-run-log.md`: the hand-off entry.
- Leave alone:
  - `src/**`.
  - `tests/unit/**`. The pinned unit tests stay, including
    `TestSimplify.test_is_idempotent` and
    `test_the_same_seed_writes_the_same_marks`. A property generalises
    them; it does not replace them.
  - `pyproject.toml`. Property tests are ordinary tests: no marker, no
    profile registration. A `load_profile` call in conftest would override
    CI's automatic `ci` profile.
- House rules that apply to generated tests:
  - Every test has a one-line docstring.
  - Behaviour families sit in plain classes, one per function under test.
  - No `parametrize`; use `st.booleans()` or `st.sampled_from` for mode
    switches.
  - Coordinates: `tests/architecture/test_coordinates.py` scans test text.
    Latitude bounds are written as `51.19` and `51.26` and longitude bounds
    as `-3.88` and `-3.80`, inside the Lynmouth box, so the gate passes.
    No other lat/lon-like literals.
  - Place names come from `CONTRIBUTING.md`'s list.
  - Floats are finite: `allow_nan=False, allow_infinity=False`.
- The properties. Each bullet is one test, so each needs a docstring.
  Tolerances are stated; none may be widened.

  `test_projection.py` (`pyntpot.maps.projection`):
  - `inverse` undoes `__call__`:
    - Draw `lat0`, `lat_ref` and `lat` in [51.19, 51.26], and `lng_ref` and
      `lng` in [-3.88, -3.80].
    - Draw `x0` and `y0` in [-1e4, 1e4].
    - `Projection(lat0, lat_ref, lng_ref, x0, y0).inverse(*p(lat, lng))`
      equals `(lat, lng)` within `abs=1e-9`.
    - Note the argument order: `__call__(lat, lng)` returns `(x, y)`, and
      `inverse(x, y)` returns `(lat, lng)`.
  - With no route, `track_projection(lats, lngs)` puts the minimum projected
    x and y at 0 (`abs=1e-6` m). Draw 2 to 50 pairs in the box.
  - With a route, `track_projection(lats, lngs, route)` makes the first
    projected point equal `route[0]` (`abs=1e-6`). Draw `route` as 1 to 5
    points in [-1e4, 1e4]^2.

  `test_polyline.py` (`simplify`):
  - Draw points as lists of 0 to 60 points in [-1000, 1000]^2, and
    `eps` in [0, 50].
  - For 2 or more points, the first and last input points are the first and
    last output points (`is` identity, since `simplify` returns the same
    tuples). Fewer than 3 points return an equal copy.
  - The output is an order-preserving subsequence of the input, by
    identity.
  - `simplify(simplify(p, e), e) == simplify(p, e)`.
  - Every dropped point lies within `eps + 1e-9` of the infinite line
    through its nearest kept neighbours. This is the same metric
    `simplify` uses (`polyline.py:44`): perpendicular distance to the
    line, or distance to the kept point when the neighbours coincide. The
    test computes it with its own cross-product formula.

  `test_rings.py` (`clip_ring`, `signed_area` from `pyntpot.maps.rings`):
  - Rings are convex:
    - 3 to 12 distinct sorted angles in [0, 2π).
    - A centre in [-200, 200]^2 and a radius in [1, 300].
  - Boxes are `(xmin, ymin, xmax, ymax)` from [-250, 250], each side at
    least 1.
  - Every output point lies in the box within `1e-9 * (1 + max |coord|)`.
    Intersections are interpolated, not snapped, so the bound is not exact.
  - `|signed_area(out)| <= |signed_area(ring)| + tol` and
    `<= |signed_area(box ring)| + tol`, with `tol = 1e-9 * (1 + |signed_area(ring)|)`.
    Both sides use `signed_area`, so its scale (twice the area) cancels.
  - A ring scaled and shifted to lie strictly inside the box comes back
    equal to the input.
  - A ring translated so that its bounding box is disjoint from the box
    returns `[]`. Build it by shifting the ring along x or y until its
    bounding box clears the box's edge by at least 1; a ring separated
    only diagonally, near a corner, is a rounding edge case and is not
    generated.
  - Not tested: clipping twice. A second pass can add near-duplicate points
    at the boundary, so `clip_ring` is not idempotent by construction.

  `test_noise.py` (`edt`, `blur`):
  - `edt` is a two-pass 3x3 chamfer with weights 1 and √2, not exact.
    Masks are boolean, shapes 1 to 12 by 1 to 12.
  - Zero on every True cell, for masks with at least one True cell.
  - Bounded by the true distance. Brute force over all True cells gives the
    Euclidean distance `d`. Then `d - 1e-4 <= edt <= 1.0825 * d + 1e-4`.
    1.0825 rounds up √(4 - 2√2) ≈ 1.08239, the worst overestimate of a
    (1, √2) chamfer, reached at slope √2 - 1.
    - The bound is the property. If it fails, that is a finding (see the
      phase rules); do not raise the factor.
  - Monotone: `edt(mask | extra) <= edt(mask)` elementwise, for any second
    mask `extra` of the same shape.
  - An all-False mask returns `1e6` everywhere.
  - `edt` does not mutate its input (compare to a copy).
  - `blur` arrays are float32, shape 8 to 40 by 8 to 40, elements in
    [0, 1] (`st.floats(0, 1, width=32, allow_subnormal=False)`), and
    `sigma` in [0, 6]. Subnormals are excluded because a padded field
    holding a single `1e-45` blurs to sum 0 (the division by `2r+1`
    underflows), which is float arithmetic, not a `blur` defect.
  - Same shape; dtype float32.
  - The output stays within `[a.min() - 1e-5, a.max() + 1e-5]`.
  - A constant field comes back equal within `rel=1e-5`.
  - Mass is preserved away from the border:
    - Draw an interior field, then zero-pad it by `m = 3 * ceil(sigma) + 2`
      on every side. Three box passes of radius
      `max(1, round(0.95 * sigma))` spread at most 3r ≤ m, so edge
      replication only pads zeros.
    - Then `blur(a, s).sum()` equals `a.sum()` within `rel=1e-4`.
    - Do not claim mass preservation in general: `blur` pads with
      `mode="edge"` (`noise.py:144`).
  - `blur` does not mutate its input.

  `test_stamp.py` (`stamp`, `brush_from_id`):
  - Canvas `(60, 220)` float32 zeros.
  - Paths are `(N, 2)` float arrays with 2 to 30 points, x in [2, 218] and
    y in [2, 58], built as `tests/unit/ink/test_stamp.py:19` builds `line`.
  - The brush id is drawn from `("RIV1-a", "TRK4-d", "MAJ2-a")`;
    `brush, _ = brush_from_id(id, 3.0, 2.0, BrushStyle())` (it returns a
    `(Brush, str)` pair).
  - The seed is in [0, 2**32 - 1].
  - The same seed gives the same deposit. Two fresh canvases stamped with
    `np.random.default_rng(seed)` are `np.array_equal`.
  - The path array is not mutated.
  - A path whose total length is at most 2.0 px deposits nothing; the
    canvas stays all zero. `stamp` skips paths under 2.5 px; 2.0 keeps
    clear of the threshold.

  `test_pigment.py` (`composite`, `PaperStyle`):
  - `h` and `w` are in 1 to 16. `base` is `(h, w, 3)` **float32** in
    [0, 1], drawn as
    `hnp.arrays(np.float32, (h, w, 3), elements=st.floats(0, 1, width=32))`.
    The dtype matters: `km_plate` does `base.astype(F32, copy=True)`, so a
    float64 `base` comes back float32-rounded in glazing mode.
  - Draw 0 to 4 layers. Each layer is `(density, pigment)` or
    `(density, pigment, transparency)`:
    - `density` is `None` or `(h, w)` float32 in [0, 1].
    - `pigment` is `(3,)` in [0, 1].
    - `transparency` is in [0, 1].
  - Glazing is `st.booleans()`, giving `dataclasses.replace(PaperStyle(), km_glazing=g)`.
  - The output is in [0, 1] in both modes.
  - No layers returns `np.clip(base, 0, 1)` exactly (`np.array_equal`),
    in both modes, for the float32 `base` above.
  - Multiply mode (`km_glazing=False`) never lightens: `out <= base + 1e-6`.

  `test_hand.py` (`Hand.write`):
  - Module-scoped `hand` fixture, as in `tests/unit/letters/test_hand.py:19`.
  - Text is `st.sampled_from` six names from `CONTRIBUTING.md`'s list.
  - Size is in [6, 30]. The seed is in [0, 2**31 - 1].
  - Either an anchor setting, or a path setting on a straight 2 to 5 point
    line.
  - The same seed writes the same marks:
    `hand.write(s, hand.generator(seed)) == hand.write(s, hand.generator(seed))`.
- Budget: `uv run pytest tests/property` under the default profile (100
  examples per test) takes at most 30 s in this environment. Rule when
  over budget: take the slowest test (from `--durations=0`), halve its
  `max_examples` in its own `@settings`, never globally, and re-measure;
  repeat until under 30 s or that test is at 25, then move to the next
  slowest.
- Hand-off: append to the run log the suite time, each test's duration,
  any `max_examples` cut (test, from, to) and any finding filed.
- Gate: G-here, plus `CI=true uv run pytest tests/property --randomly-seed=1`
  and `CI=true uv run pytest tests/property --randomly-seed=2`, both green.
  Under the `ci` profile the examples are derandomised, so only the test
  order changes between the two runs, which is the point: it proves no
  property depends on another's state.
- Commit: `Add property tests for the ink, letters and projection invariants`

#### P5.2 Coverage baseline; ADR 0011

- Implements the spec's coverage decision; predecessor P5.1.
- Measure first, before any edit. Measure the way CI will, so the
  Hypothesis examples are derandomised and no benchmark counts:
  - On 3.13: `CI=true uv run pytest -m "not golden and not benchmark" --cov`,
    then
    `uv run coverage report --include='src/pyntpot/ink/*,src/pyntpot/letters/*' --format=total --precision=2`
    and `uv run coverage report --include='src/pyntpot/maps/*' --format=total --precision=2`.
    `--format=total` alone prints a figure already rounded to the nearest
    whole percent, which the round-down below cannot undo.
  - On 3.14, the same three commands with
    `UV_PROJECT_ENVIRONMENT="$SCRATCH/venv-3.14"` and `--python 3.14` on
    each `uv run` (see the tool facts), so `.venv` stays on 3.13.
  - Do each interpreter twice. If the two figures for one package on one
    interpreter differ, use the lower and log both in the run log.
  - Rule: `T` is the lower of the two interpreters' `ink`+`letters`
    figures, rounded down to a whole percent (95 at P5.0, on 3.13, before
    the property tests). `T_maps` is the lower `maps` figure, rounded down
    the same way. Branch arcs can differ between interpreter versions, and
    both matrix legs enforce the gate.
  - If 3.14 cannot be installed here, `T` and `T_maps` are the 3.13
    figures rounded down, minus 1, and the run log says so.
- Owner files:
  - `.github/workflows/ci.yml`, job `checks`:
    - The `Tests` step becomes
      `uv run pytest -m "not golden and not benchmark" --cov`. The
      `benchmark` term deselects nothing until P5.4 adds benchmarks; it is
      here so P5.4 does not touch the coverage run.
    - Directly after it, a step `Coverage gate (ink, letters)` runs
      `uv run coverage report --include="src/pyntpot/ink/*,src/pyntpot/letters/*" --fail-under=T`.
    - A second step, `Coverage gate (maps)`, runs
      `uv run coverage report --include="src/pyntpot/maps/*" --fail-under=T_maps`.
    - Both matrix legs run both steps. Leave job `prerelease` alone: it has
      no pytest-cov.
  - `pyproject.toml`: only the comment above `[tool.coverage.run]`, which
    becomes "the gate is the CI step in `checks`, see ADR 0011; never set
    `fail_under` here (pytest-cov would apply it to the whole package)".
  - `CONTRIBUTING.md`: the two local commands.
  - `docs/decisions/0011-coverage-baseline.md`. It records:
    - Context: the template's 100 percent demand and the spec's answered
      open question.
    - Decision: branch coverage of `ink` and `letters` at least `T`, and of
      `maps` at least `T_maps`, gated in CI only on both matrix legs. The
      coverage run excludes the golden tests and the benchmarks, so these
      figures count only behavioural tests. That matters most for `maps`:
      a visual-refinement change regenerates the goldens, so they do not
      guard it, and a benchmark runs `maps` code without asserting
      anything. The ADR also records the whole-package figure and the
      per-interpreter figures.
    - Ratchet, for `T` and `T_maps` alike: a commit whose measurement (the
      lower of the two interpreters) is `T + 1` or more raises that
      threshold to the new rounded-down figure in the same commit.
      Lowering either needs a superseding ADR.
    - Consequences: plain `uv run pytest` stays coverage-free.
  - `specs/001-port/p5-run-log.md`: the hand-off entry.
- Verify the gate bites: `--fail-under=T+1` exits 2 locally whenever the
  figure is below `T + 1`. Quote it in the hand-off.
- Hand-off: append to the run log the four figures (two packages, two
  interpreters), the whole-package figure, `T`, `T_maps`, and which
  interpreter set each.
- Gate: G-here.
- Commit: `Gate branch coverage at the measured baselines`

#### P5.3a Mutation testing: config, scripts, PR job, sharded nightly; ADR 0012 proposed

- Implements D17 (mutmut); predecessor P5.2.
- **Scope and shard count come from measured timings, by rule.** This
  slice starts with `ink` and `letters` in scope, because they are cheap
  and pure. Step 3 below measures all three subpackages, and the rule
  there sets the nightly scope and the shard count `N` in this same slice,
  before it commits. The scope lives in one place, `only_mutate`, which
  `scope.py` and `shard.py` read with `tomllib`; `N` lives in
  `[tool.pyntpot.mutation] shards`.
- Owner files:
  - `pyproject.toml`: **replace** the existing `[tool.mutmut]` table and
    the comment block above it (at P5.0, `source_paths` and a
    `pytest_add_cli_args_test_selection` of `["tests/", "-m", "not golden"]`;
    appending a second table is a `TOMLDecodeError`) with:
    ```toml
    source_paths = ["src/"]
    only_mutate = ["src/pyntpot/ink/*", "src/pyntpot/letters/*"]
    pytest_add_cli_args = ["--hypothesis-profile=ci"]
    pytest_add_cli_args_test_selection = ["tests/unit", "tests/property", "-m", "not golden"]
    ```
    The new comment says why the other test directories are left out.
    mutmut runs pytest inside `mutants/`, where `support.REPO_ROOT` is the
    mutated tree:
    - `tests/architecture` would scan trampolined source: the line budget
      fails on every mutated file, and the injected `mutmut` import and
      `# type: ignore` lines break other checks.
    - `tests/golden` is too slow per mutant; that is the exclusion the old
      comment gave.
    - `tests/mutation` tests the helper scripts, not `src`.
    - `tests/benchmarks` (from P5.4) times code and asserts nothing.

    `only_mutate` is rewritten at step 3 if the rule adds `maps`. Add a new
    table `[tool.pyntpot.mutation]` with `min_score = 0.0` (P5.3b sets it)
    and `shards = N` (step 3 sets it), the one place the jobs read both
    from.
  - `.gitignore`: `mutants/`.
  - `tests/mutation/__init__.py` (docstring only).
  - `tests/mutation/scope.py`:
    - `changed_functions(diff: str, sources: Mapping[str, str], only_mutate: Sequence[str]) -> list[str]`.
      It takes a `git diff --unified=0` text, the new source of each
      changed file (keyed by repo path), and the `only_mutate` globs, and
      returns sorted, de-duplicated mutmut patterns.
    - A path counts only if it ends `.py` and `fnmatch.fnmatch(path, glob)`
      holds for some glob in `only_mutate`, mutmut's own matching, where
      `*` spans `/` (so `src/pyntpot/letters/*` also matches
      `letters/fonts/`, which the `.py` test drops).
    - A deleted file, whose `+++` side is `/dev/null`, is skipped: it has
      no new source and no mutants.
    - It parses the `+c,d` hunk ranges. `+c,d` with `d > 0` changes lines
      `c` to `c + d - 1`, and `+c` alone means `d = 1`. A pure deletion,
      `+c,0`, touches lines `c` and `c + 1`, the new lines either side of
      the removed ones, so deleting a line inside a function still emits
      that function's pattern.
    - It parses the file's `ast`. For each
      top-level function, and each method of a top-level class, whose
      `[lineno incl. decorators, end_lineno]` intersects a changed range, it
      emits:
      - `pyntpot.<module>.x_<name>*` for a function;
      - `pyntpot.<module>.xǁ<Class>ǁ<name>*` for a method.
    - The module name follows mutmut's rule (see the tool facts): drop
      `src/` and `.py`, map `/` to `.`, drop a trailing `.__init__`.
    - It skips any function or method whose decorators are anything other
      than none or a single `staticmethod` or `classmethod`, mirroring
      mutmut 3.8 (`file_mutation.py:330`), which generates no mutants for
      them. Emitting a pattern for one would make `mutmut run` fail.
    - A change inside a nested function maps to its top-level enclosing
      function. A change outside any function emits nothing; that is the
      documented gap, and the nightly covers it.
    - A `main()` takes `--base REF` and `--out PATH`. It runs
      `git diff --unified=0 --diff-filter=d REF...HEAD -- src/pyntpot`
      via `subprocess.run([...], check=True, capture_output=True, text=True)`
      (`--diff-filter=d` leaves deleted files out, so no read of a missing
      file), reads each remaining `.py` file, reads `only_mutate` from
      `pyproject.toml` with `tomllib`, and writes one pattern per line to
      `--out`.
    - It logs through `logging`; no `print`. `main()` first calls
      `logging.basicConfig(level=logging.INFO)`, or its log lines do not
      show in CI.
  - `tests/mutation/shard.py`:
    - `shard_patterns(modules: Mapping[str, int], count: int) -> list[list[str]]`.
      `modules` maps each in-scope mutmut module name to its source line
      count, the cost proxy. It sorts modules by cost descending, ties by
      name ascending, and puts each on the shard with the lowest running
      cost, ties to the lowest shard index. It returns, per shard, sorted
      patterns: `<module>.x_*` and `<module>.xǁ*` for each module. Two
      patterns rather than `<module>.*`, because a package's `__init__`
      module name is a prefix of its submodules' names
      (`pyntpot.ink.*` would also match `pyntpot.ink.polyline.x_f`).
    - It raises `ValueError` when `count < 1` or `count > len(modules)`: an
      empty shard would run `mutmut run` with no pattern, which tests every
      mutant.
    - `main()` takes `--index I`, `--count N` and `--out PATH`. It reads
      `only_mutate` from `pyproject.toml` with `tomllib`, lists the `*.py`
      files under `src/` that match it (the same `fnmatch` rule; the `.py`
      test drops data files such as `letters/fonts/`), keeps the
      modules that define at least one function or method mutmut mutates
      (the same decorator rule as `scope.py`), and writes shard `I`'s
      patterns one per line to `--out`. `--count` defaults to `shards`.
      With `--matrix-out PATH` and no `--index`, it instead appends
      `indices=[0, …, N-1]` (JSON) to PATH, which the nightly's `plan` job
      passes as `$GITHUB_OUTPUT`.
    - It repeats `scope.py`'s path-to-module and decorator rules rather
      than importing them: each script runs standalone from CI, and only
      pytest's `pythonpath` would make a shared import resolve. Both test
      files pin the same `__init__` and decorator cases, so the two cannot
      drift silently.
    - It logs through `logging`; no `print`. `main()` first calls
      `logging.basicConfig(level=logging.INFO)`.
  - `tests/mutation/score.py`:
    - `total_counts(stats: Iterable[Mapping[str, int]]) -> dict[str, int]`
      sums `killed`, `timeout`, `survived`, `suspicious`, `no_tests` and
      `segfault` across stats files. It does not sum `total`: a
      pattern-restricted shard counts every generated mutant there.
    - `score(counts: Mapping[str, int]) -> float | None` returns
      `(killed + timeout) / (killed + timeout + survived + suspicious + no_tests + segfault)`,
      or `None` when that denominator is 0.
    - `main()` takes one or more stats paths and reads `min_score` from
      `pyproject.toml` with `tomllib`. It logs the summed counts and the
      score, and exits 1 below `min_score`. `None` logs "no mutants tested"
      and exits 0. `main()` first calls
      `logging.basicConfig(level=logging.INFO)`, so the score and "no
      mutants tested" show in CI.
  - `tests/mutation/test_scope.py`, `tests/mutation/test_shard.py` and
    `tests/mutation/test_score.py`. These are pure-function tests on
    literal diff, source, module-cost and stats values: no git, no mocks,
    no pyproject read, `ids=` on every parametrize. Cases:
    - `scope`: a function body edit; a decorator-only edit on a
      `@staticmethod` method (one pattern); an edit inside a
      `@functools.cache` function and inside a `@property` (no pattern);
      a method edit; a nested-function edit; a module-constant edit, which
      gives no pattern; a file outside the `only_mutate` globs; a file in
      a package `__init__.py` (no `.__init__` in the name); a deleted file
      (`+++ /dev/null`, absent from `sources`: no pattern and no error); a
      deletion-only hunk `+c,0` inside a function body (that function's
      pattern); a non-`.py` file under an `only_mutate` glob (no pattern).
    - `shard`: a deterministic assignment for a literal module table,
      including a cost tie broken by name; two shards balanced
      largest-first; `count` 1 returns every module; an `__init__` module
      gets the two-pattern form; `count` 0 and `count > len(modules)` raise.
    - `score`: a zero-denominator stats file; below, at and above the
      threshold; two shard files whose counts sum, with `total` ignored.
  - `.github/workflows/ci.yml`: a new job `mutation`.
    - It runs only on `if: github.event_name == 'pull_request'`, on
      ubuntu-latest, with `timeout-minutes: 60`.
    - Checkout uses `fetch-depth: 0`. Then the same setup-uv pins as
      `checks`, and `uv sync --locked`.
    - Next, `uv run python tests/mutation/scope.py --base origin/${{ github.base_ref }} --out "$RUNNER_TEMP/patterns"`.
    - When the file is empty, the job logs "no changed functions in the
      mutation scope" and ends green.
    - Otherwise it runs, in order:
      1. A step with `id: run` and `shell: bash`, whose script is exactly:
         ```bash
         if xargs -r -a "$RUNNER_TEMP/patterns" uv run mutmut run 2>&1 | tee "$RUNNER_TEMP/mutmut.log"; then
           echo tested=true >> "$GITHUB_OUTPUT"
         elif grep -q 'Filtered for specific mutants, but nothing matches' "$RUNNER_TEMP/mutmut.log"; then
           echo "changed functions have no mutants"; echo tested=false >> "$GITHUB_OUTPUT"
         else exit 1; fi
         ```
         GitHub runs `shell: bash` as `bash -eo pipefail`, so a bare
         failing pipeline would end the script before any `rc=$?` or
         `grep`; inside an `if` condition `-e` does not fire, and
         `pipefail` carries `mutmut run`'s failure through `tee`. `-r`
         stops `xargs` running `mutmut run` with no pattern, which would
         test every mutant, if the file is empty.
      2. `uv run mutmut export-cicd-stats`
      3. `uv run mutmut results | { grep -v ': not checked$' || true; }`
         (to the log). After a restricted run, `mutmut results` lists
         every untested mutant as `not checked`; the filter keeps only the
         tested ones, and `|| true` keeps an empty result from failing the
         step.
      4. `uv run python tests/mutation/score.py mutants/mutmut-cicd-stats.json`

      Steps 2 to 4 carry `if: steps.run.outputs.tested == 'true'`.
  - `.github/workflows/mutation-nightly.yml`, sharded from the start.
    - Triggers: `schedule: - cron: "23 2 * * *"` and `workflow_dispatch`.
    - Every job uses ubuntu-latest, the same checkout and setup-uv pins as
      `ci.yml`, and `uv sync --locked`. Pin `actions/upload-artifact` and
      `actions/download-artifact` to the latest release tag of their
      current major, in the same tag style as `ci.yml`. Look the tags up
      with `git ls-remote --tags https://github.com/actions/upload-artifact`
      (and the same for `download-artifact`); `gh api` on third-party
      repos returns 403 here. At plan review 2 they were `v7.0.1` and
      `v8.0.1`.
    - Job `plan` (`timeout-minutes: 10`):
      `uv run python tests/mutation/shard.py --matrix-out "$GITHUB_OUTPUT"`,
      exposing `indices` as a job output.
    - Job `shards` (`needs: plan`, `timeout-minutes: 300`,
      `strategy.fail-fast: false`,
      `matrix.index: ${{ fromJSON(needs.plan.outputs.indices) }}`):
      1. `uv run python tests/mutation/shard.py --index ${{ matrix.index }} --out "$RUNNER_TEMP/patterns"`
      2. The same `run` step as the PR job (`id: run`, the same script and
         "nothing matches" handling), plus `timeout-minutes: 270`, so a
         slow shard is stopped with 30 minutes of the job left for steps 3
         to 5.
      3. `uv run mutmut export-cicd-stats`
      4. `uv run mutmut results | { grep -v ': not checked$' || true; } > mutants/survivors.txt`
         (the filter as in the PR job: without it the file lists every
         mutant outside this shard, and P5.3b reads it).
      5. `actions/upload-artifact` (`if: always()`) uploads
         `mutants/mutmut-cicd-stats.json` and `mutants/survivors.txt` as
         `mutation-shard-${{ matrix.index }}`.

      Steps 3 and 4 carry
      `if: always() && (steps.run.outputs.tested == 'true' || steps.run.outcome == 'failure')`:
      they run after a tested run, and after a timed-out or failed one so
      its partial counts still upload, but not after "nothing matches".
      Every shard still generates all mutants and runs the stats
      collection; verify step 3 below measures that overhead.
    - Job `score` (`needs: shards`, `if: always()`, `timeout-minutes: 15`):
      1. `actions/download-artifact` with `pattern: mutation-shard-*` into
         `shards/`.
      2. `uv run python tests/mutation/score.py shards/*/mutmut-cicd-stats.json`.
      3. A last step, `if: needs.shards.result != 'success'`, logs
         "partial run: a shard failed or timed out" and exits 1, so a
         partial score is never mistaken for a full one.
  - `docs/decisions/0012-mutation-threshold.md`, status **Proposed**. It
    records:
    - the measured table, the scope and shard-count rule, and the scope
      and `N` it chose, with the reason if `maps` is left out;
    - the sharding mechanics (largest-first by line count, one artifact
      per shard, counts summed before dividing);
    - the PR mechanism and its gaps (module-level changes; functions with
      other decorators have no mutants);
    - the score formula, with why `no_tests` counts against it (an
      untested mutant is an untested line);
    - the Hypothesis `ci` profile under mutmut, and why `tests/architecture`
      is outside the test selection;
    - that the threshold is set by P5.3b from the first full run.
  - `CONTRIBUTING.md`: how to run mutmut locally on one module
    (`uv run mutmut run "pyntpot.ink.polyline*"`), and that it needs
    Linux or macOS.
  - `specs/001-port/p5-run-log.md`: the hand-off entry.
- Verify before committing, in this environment:
  1. Check the mutmut name format, data files and test selection:
     - Run `uv run mutmut run "pyntpot.ink.polyline*"`. The stats run
       must pass; with the old `tests/` selection it failed on
       `test_no_oversized_files` against `mutants/src`.
     - Confirm `mutants/src/pyntpot/ink/polyline.py` defines
       `x_simplify__mutmut_1`.
     - Confirm a `Hand` unit test passes inside `mutants/`; the font file
       must have been copied. `copy_src_dir` copies every file under
       `source_paths`, so no `also_copy` is expected; if a data file is
       missing all the same, add `also_copy` entries for
       `src/pyntpot/letters/fonts/` and `src/pyntpot/maps/themes/`, and
       record that in the ADR and the run log.
     - If the name format differs from the tool facts above, fix
       `scope.py`, `shard.py` and their tests to match the installed tool,
       and record it in the run log.
  2. Run the PR path end to end against a synthetic base. On a scratch
     commit that edits one line inside `simplify`, run
     `scope.py --base HEAD~1`, then the four commands above. Quote the
     patterns and the score. Then drop the scratch commit.
  3. Measure, per subpackage (`ink`, `letters`, `maps`), and record as a
     table in the run log and the ADR:
     - Counting. `export-cicd-stats` reads every `.meta` file and results
       persist across runs, so its counts after a second run include the
       first run's mutants, and it gives only a grand `total`. Step 3
       therefore counts from the `.meta` files directly, with a throwaway
       script in `$SCRATCH` (not committed): each
       `mutants/src/pyntpot/<pkg>/**/*.meta` file is JSON whose
       `exit_code_by_key` maps mutant name to exit code, `null` until
       tested.
     - The mutant count `M` per subpackage: the number of
       `exit_code_by_key` keys across that subpackage's `.meta` files.
       Generate first, with `only_mutate` temporarily set to all three;
       mutmut generates every mutant in `only_mutate` even under a
       pattern, so the cold run below does it.
     - The per-shard overhead `O`: wall time of a cold run (no `mutants/`)
       of one mutant, `uv run mutmut run "pyntpot.ink.polyline.x_simplify__mutmut_1"`,
       which is generation plus stats plus one mutant.
     - The wall-clock seconds per mutant `s`, from warm runs (after the
       cold run) on sample modules: `pyntpot.ink.polyline*`,
       `pyntpot.letters.hand*`, and for `maps` both `pyntpot.maps.rings*`
       (pure geometry, fast tests) and `pyntpot.maps.painter.cover*`
       (covered by slow paint tests).
       - Run each sample as `timeout 1200 uv run mutmut run "<pattern>"`,
         timing it with `date +%s` before and after. Each sample's wall
         time includes that run's stats collection, so `s` errs high.
       - The mutants a sample tested: the `exit_code_by_key` keys that
         match its pattern (`fnmatch`) and are no longer `null`. The
         sample patterns are disjoint, so earlier samples never count.
       - `s` is the sample's wall time over its tested mutants. For
         `maps`, `s` is the mutant-weighted mean of the two samples: their
         summed wall time over their summed tested mutants.
       - If `timeout` stops a sample (exit 124), narrow it to the module's
         function with the most mutants (counted from the `.meta` keys,
         pattern `<module>.x_<name>*`, or `<module>.xǁ<Class>ǁ<name>*` for
         a method) and re-run it under the same `timeout 1200`; if that
         also times out, take the next function down. Record each
         narrowing in the run log.
       - The score on each sample: run `uv run mutmut export-cicd-stats`
         and copy `mutants/mutmut-cicd-stats.json` before and after the
         sample, subtract the counts, and apply `score.py`'s formula to the
         difference. The difference's summed counts must equal the tested
         count from the `.meta` keys; if they differ, the `.meta` count is
         used and the run log records both.
       - This machine has 4 cores, as ubuntu-latest has.
     - The estimate `H = M * s / 3600` hours per subpackage.

     Then apply the rule:
     - `N_core = max(2, ceil((H_ink + H_letters) / 3.5))`.
     - `N_all = max(2, ceil((H_ink + H_letters + H_maps) / 3.5))`.
     - If `N_all <= 8`, the scope is `ink`, `letters` and `maps`
       (`only_mutate` gains `"src/pyntpot/maps/*"`) and `N = N_all`.
     - Otherwise the scope stays `ink` and `letters`, `N = N_core`, and ADR
       0012 and the run log record why `maps` is out (`H_maps` and
       `N_all`).
     - The 3.5 h target leaves 1.5 h of the 300-minute shard timeout for
       `O` and for imbalance from the line-count proxy. `s` is measured on
       this machine, not a runner; P5.3b corrects `N` from the first
       nightly's real shard times by its own rule.

     Write the scope into `only_mutate` and `N` into `shards`, restore
     anything else step 3 changed, and run
     `uv run python tests/mutation/shard.py --index 0 --out "$SCRATCH/p0"`
     to check shard 0's patterns are non-empty.
- Hand-off: append to the run log the step 3 table (`M`, `s`, `H` per
  subpackage, `O`, each sample's wall time, tested count and score), any
  sample narrowing, `N_core`, `N_all`, the chosen scope and `N`, and the
  step 2 patterns and score.
- Gate: G-here (the new script tests run in it) and `uv run ty check`
  covering `tests/mutation`.
- Commit: `Run mutation testing on changed functions and a sharded nightly`

#### P5.4 Benchmarks and the CodSpeed workflow

- Implements D17 (benchmarks); predecessor P5.3a.
- **Before any edit, reconcile with CodSpeed's onboarding.** The maintainer
  enabled the repo on codspeed.io on 2026-10-07, and its setup may open a
  PR or push a workflow.
  - List open PRs and `ls .github/workflows`.
  - If an onboarding PR is open, read its diff. Adopt any
    repository-specific setting it carries (a token input, a runner
    choice) into this slice.
  - Rule for its benchmarks: every benchmark the PR proposes is kept,
    rewritten into `tests/benchmarks/test_ink.py` or `test_maps.py` to the
    benchmark rules below and the repo's rules (docstring, no mocks,
    seeded inputs, Lynmouth fixture data, `brush, _ = ...`). One is left
    out only if it breaks a repo rule that no rewrite can fix (for
    example, it needs the network or a mock); the run log names it and
    the rule.
  - Do not push to, merge or close that PR. The run log and the PR
    description record that this slice supersedes it, so it can be closed.
  - If a CodSpeed workflow is already on `main`, this slice rewrites that
    file to the spec below rather than adding a second one.
- Owner files:
  - `tests/benchmarks/__init__.py` (docstring only).
  - `tests/benchmarks/test_ink.py` and `tests/benchmarks/test_maps.py`.
  - `pyproject.toml`:
    - `addopts` gains `--benchmark-disable`, so every plain or `-m`
      filtered run calls each benchmark once as a smoke test.
    - `markers` gains `"benchmark: performance benchmarks (timed by CodSpeed in CI, --benchmark-enable locally)"`.
  - `.gitignore`: `.benchmarks/` and `.codspeed/`.
  - `.github/workflows/codspeed.yml`.
  - `.github/workflows/ci.yml` job `checks`: one new step,
    `Benchmarks (smoke)`, running `uv run pytest -m benchmark`, after the
    coverage gates. The `Tests` step already deselects benchmarks (P5.2),
    so the coverage figures do not move. No other edit to `checks`.
  - `docs/explanation/performance.md`.
  - `CONTRIBUTING.md`: the local timing command.
  - `specs/001-port/p5-run-log.md`: the hand-off entry.
- Leave alone:
  - `ci.yml`'s `Tests` step and coverage gates (P5.2's).
  - `ci.yml` job `prerelease`. It already installs pytest-benchmark, which
    owns `--benchmark-disable`; its `-m "not golden"` run now smoke-runs
    the benchmarks too, which is harmless.
  - G-here's definition. Its `uv run pytest -m "not golden"` stage now
    smoke-runs the benchmarks as well; that is accepted, and the smoke
    budget below keeps it cheap.
- Benchmark rules:
  - Every module sets `pytestmark = pytest.mark.benchmark`.
  - Every test takes `benchmark` and calls it **exactly once**: an unused
    fixture warns, and warnings are errors.
  - Inputs are built outside the timed callable, from seeded generators.
  - A callable whose target mutates (`stamp`) or caches by directory
    (`paint`) builds its fresh state inside the callable.
  - Module-scoped fixtures hold only built, immutable inputs (a sheet, a
    basemap, painted plates), per the fixture rule.
- `test_ink.py`:
  - `test_sheet_construction`: `benchmark(Sheet, 512, 512, gran_px=6.0, seed=3)`.
  - `test_edt`: a 512×512 boolean mask, True with probability 0.01 from
    `default_rng(5)`. Benchmark `edt(mask)`.
  - `test_stamp_a_2000_point_path`:
    - The path is 2000 points of `x = linspace(20, 1180, 2000)` and
      `y = 200 + 120 * sin(x / 90)` on a `(400, 1200)` canvas.
    - The brush is `brush, _ = brush_from_id("RIV1-a", 3.0, 2.0, BrushStyle())`.
    - Benchmark
      `lambda: stamp(np.zeros((400, 1200), np.float32), path, brush, np.random.default_rng(7))`.
  - `test_wash`:
    - The sheet is `Sheet(512, 512, gran_px=6.0, seed=3)` (module fixture).
    - The cover is a float32 disc of radius 180 centred in 512×512.
    - `base` and `pool` take the values `tests/support/washes.py` uses.
    - Benchmark `wash(cover, sheet, base, pool)`.
- `test_maps.py`. The inputs are Lynmouth offline, as `paint_fixture`
  builds them (`tests/support/golden.py`). A module constant
  `DISPLAY_PX = 450` sets the size of every maps benchmark, so the ladder
  below edits one line; names carry no size.
  - Module fixture `basemap`:
    - Copy `FIXTURE_DIR` into a `tmp_path_factory` directory.
    - The style is `class_style(display_px=DISPLAY_PX)`.
    - Then `fetch(Track.from_gpx(...), Cache(dir), FixtureFeatures(), FixtureElevation(), style)`.
    - It returns `(basemap, style)`.
  - `test_paint`:
    - `rounds = itertools.count()`.
    - Benchmark
      `lambda: paint(basemap, style, out / f"round-{next(rounds)}")`.
    - Each round needs a fresh directory: `paint` skips work when the
      directory already holds plates with the current hash.
  - Module fixture `lettered`: paint once, then
    `letter(plates, basemap, None, style)`.
  - `test_compose`: benchmark
    `compose(plates, lettering, basemap, style)` (attribution on, the
    default).
  - Each maps benchmark belongs to one stage: `fetch`, `paint`, `letter`
    or `compose`. The ladder below uses that.
- `codspeed.yml`:
  ```yaml
  name: CodSpeed
  on:
    push:
      branches: [main]
    pull_request:
    workflow_dispatch:
  permissions:
    contents: read
    id-token: write
  jobs:
    benchmarks:
      runs-on: ubuntu-latest
      timeout-minutes: 60
      steps:
        - uses: actions/checkout@v7.0.1
        - uses: astral-sh/setup-uv@v10.2.0
          with:
            version: "0.11.21"
            enable-cache: true
            python-version: "3.13"
        - run: uv sync --locked
        - uses: CodSpeedHQ/action@v5.4.0
          with:
            mode: simulation
            run: uv run pytest tests/benchmarks --codspeed
  ```
  Authentication is OIDC, not a token: CodSpeed recommends OIDC for public
  repos, and a fork PR falls back to tokenless upload. Keep the checkout
  and setup-uv pins equal to `ci.yml`'s at the time of the edit; if
  dependabot has moved them, match `ci.yml`.
- `docs/explanation/performance.md`. This creates `docs/explanation/`,
  ahead of P7, which owns the rest of that tree.
  - What each benchmark measures and why it was chosen, and the final
    `DISPLAY_PX`.
  - The local baselines from
    `uv run pytest -m benchmark --benchmark-enable`: median and rounds
    per benchmark, with the commit, date, Python and numpy versions, and
    CPU model.
  - That CodSpeed's simulation mode counts instructions, so its numbers
    are not wall time, with the dashboard link
    `https://codspeed.io/findlaywebb/pyntpot`.
  - That these are measurements, not targets.
- **Smoke budget and the display ladder.** Before committing, measure the
  smoke run, `uv run pytest -m benchmark` (timing disabled, module
  fixtures included), here. It runs in every `checks` leg and every
  G-here, so its budget is 60 s total. Rule when over:
  1. Lower `DISPLAY_PX` for all maps benchmarks along 450 → 300 → 200,
     re-measuring at each step, and stop at the first size under 60 s.
  2. If still over at 200, drop maps benchmarks one at a time, slowest
     smoke time first, re-measuring after each. Never drop one that is the
     only benchmark of its stage (`fetch`, `paint`, `letter`, `compose`);
     skip it and take the next slowest.
  3. If only stage-unique maps benchmarks remain and the run is still
     over 60 s, keep them, file `docs/issues/benchmark-smoke-budget.md`
     with the measured time, and land the slice. The `ink` benchmarks are
     never dropped by this rule.
- **CodSpeed job budget.** After the PR's first CodSpeed run, if the job
  takes more than 30 min, apply the same `DISPLAY_PX` ladder (one step
  lower than the current value, then the next) in a follow-up commit on
  `p5-quality`, `Shrink the maps benchmarks to display_px=<N>`, until a
  run takes 30 min or less, or the ladder reaches 200.
- Hand-off: append to the run log a table of every benchmark (ours and
  any adopted from the onboarding PR) with its local median under
  `--benchmark-enable` and its smoke time with timing off; the smoke total
  at each `DISPLAY_PX` tried; the final `DISPLAY_PX`; any benchmark
  dropped or left out and why; the onboarding PR's number and what was
  adopted; and the first CodSpeed job time, with any follow-up commit.
- Gate: G-here (which now smoke-runs the benchmarks), plus
  `uv run pytest -m benchmark --benchmark-enable` and
  `uv run pytest tests/benchmarks --codspeed` locally green, plus the PR's
  `CodSpeed` job and `checks` `Benchmarks (smoke)` step green.
- Commit: `Add benchmarks and the CodSpeed workflow`

#### P5.3b Set the mutation threshold; ADR 0012 accepted

**Superseded by P5.3c (maintainer decision, 2026-10-07): do not run this
slice.** It is kept as the record of the threshold plan that was dropped.

- Predecessor: the merge of P5.1 to P5.4, then the first scheduled (or
  `workflow_dispatch`) run of `mutation-nightly.yml` on `main`.
- A run is **full** when every shard succeeded and each shard job took at
  most 255 min. Only a full run sets the threshold; never set one from a
  partial run. Rules for a run that is not full, applied in order:
  - **Slow shard.** If any shard timed out or took more than 255 min, set
    `shards = ceil(N × max_shard_min / 210)`, where `N` is the current
    `shards` and `max_shard_min` is the longest shard job's duration in
    minutes (a timed-out shard counts as its duration at the stop). This
    absorbs a runner slower than this machine and the line-count
    imbalance (up to 1.28x at review 2). Commit it on the P5.3b branch as
    `Re-shard the mutation nightly to <shards> shards`, re-dispatch with
    `gh workflow run mutation-nightly.yml --ref <P5.3b branch>`, and
    record `N`, `max_shard_min`, the new `shards` and both run ids in the
    run log and ADR 0012. Repeat on that run until one is full.
  - **Other shard failure.** A shard that failed for any other reason is
    re-dispatched once, unchanged. If the same shard fails again the same
    way, that is a finding, like a failing property in P5.1: file
    `docs/issues/mutation-nightly-failure.md` with the run ids, the shard
    and the log excerpt, record it in the run log, and fix it in its own
    slice. P5.3b then resumes from the first full run after that fix.
- From the full run, read the `score` job's log and the shard artifacts.
  Then `min_score` is the summed score rounded down to a whole percent, as
  a fraction (for example 0.71).
- Owner files: `pyproject.toml` (`[tool.pyntpot.mutation] min_score`, and
  `shards` if the slow-shard rule changed it),
  `specs/001-port/p5-run-log.md` (the run id, each shard's duration and
  counts, any re-shard, the score and the threshold), and
  `docs/decisions/0012-mutation-threshold.md`:
  - status becomes **Accepted**;
  - it records the run id, the counts, the score and the threshold, and
    any re-shard with its numbers;
  - the ratchet rule is the same as ADR 0011's.
- Gate: G-here, plus the next nightly on `main` after this lands green
  against the new `min_score` (trigger it with `workflow_dispatch`).
- Commit: `Set the mutation score threshold`

#### P5.3c Mutation testing becomes manual and advisory

- Implements the maintainer's decision of 2026-10-07 (binding), which
  supersedes P5.3b and amends D17. Predecessor P5.4 and the PR #7 review
  commits. It lands as one more commit on `p5-quality` (PR #7), before the
  merge, so the slow jobs never reach `main`. `mutation-nightly.yml` is not
  on `main` yet, so nothing scheduled has to be switched off there.
- **Why.** Mutation testing is too slow for automatic CI. Measured: the
  nightly took about 12 h of runner time over its 4 shards for `ink` and
  `letters`; the PR job took 26 min for one changed `polyline` function
  (one edited line of `simplify`, 72 mutants), so a PR that changes several
  functions hits the job's 60-min timeout. So mutation testing becomes a
  manual workflow, its score is advisory, and there is no threshold.
- **The tooling stays.** `[tool.mutmut]`, `scope.py`, `shard.py`, the shard
  run step and the score formula are unchanged; only the triggers, the
  threshold and the docs change.
- Owner files:
  - `.github/workflows/ci.yml`: delete the `mutation` job and the
    two-line comment above it (`# Mutation testing on the functions this
    pull request changed ...`), from that comment to the job's last line
    (the `Score` step's `run:`). One blank line stays between `checks`'s
    last step (`Benchmarks (smoke)`) and `prerelease:`. Nothing else in
    the file changes.
  - `.github/workflows/mutation-nightly.yml`: delete it (`git rm`).
  - `.github/workflows/mutation.yml`: new, exactly as below. It is the
    nightly's three jobs with a manual trigger and a mode-aware `plan`
    job. Carried over unchanged: the action pins (checkout `v7.0.1`,
    setup-uv `v10.2.0` with uv `0.11.21`, upload-artifact `v7.0.1`,
    download-artifact `v8.0.1`; if `ci.yml`'s pins have moved by the time
    of the edit, match `ci.yml`), the shard job's 300/270-min timeouts, the
    `run` step's "nothing matches" handling, the stats and survivors steps
    and their conditions, the artifact upload, the score job's stats glob
    and its "Partial run" step. What changes:
    - The only trigger is `workflow_dispatch`, with inputs `mode`
      (choice `changed`, `pattern`, `all`; default `changed`), `pattern`
      (string; space-separated mutmut patterns, read in mode `pattern`)
      and `base` (string, default `main`, read in mode `changed`).
    - `plan` emits `matrix`, `{"include": [{"index": I, "patterns": [...]}]}`
      with one entry per non-empty pattern list, and `count`, the number
      of entries. Mode `changed`: `scope.py --base origin/<base>` into one
      list (so the checkout needs `fetch-depth: 0`); an empty list gives
      `count=0`, a "nothing to run" line in the step summary, a green
      run, and no shard. Mode `pattern`: the input split on whitespace
      into one list; an empty input fails the job (`::error::`). Mode
      `all`: `shard.py --matrix-out` gives the indices for
      `[tool.pyntpot.mutation] shards`, and `shard.py --index I` fills
      each list.
    - The inputs reach the script through `env`, never interpolated into
      it, so a pattern cannot inject shell.
    - `shards` runs only when `count != '0'`; its patterns file comes from
      the matrix entry (`jq -r '.[]'`) instead of `shard.py`; the mutmut
      "nothing matches" message now reads "the patterns match no mutant".
    - `score` needs `plan` and `shards`, runs when `plan` succeeded with
      `count != '0'` (after failed shards too, as before), and passes
      `--summary "$GITHUB_STEP_SUMMARY"` to `score.py`. The "no shard
      stats" and "partial run" lines also go to the summary.

    ```yaml
    name: Mutation
    run-name: Mutation (${{ inputs.mode }})

    # Manual and advisory (ADR 0012): no schedule, no pull-request trigger, no threshold.
    on:
      workflow_dispatch:
        inputs:
          mode:
            description: "changed: functions changed against base; pattern: the pattern input; all: the whole scope, sharded"
            type: choice
            options: [changed, pattern, all]
            default: changed
          pattern:
            description: "mode pattern: space-separated mutmut patterns, e.g. pyntpot.ink.polyline*"
            type: string
            default: ""
          base:
            description: "mode changed: the branch to diff against (origin/<base>...HEAD)"
            type: string
            default: main

    jobs:
      plan:
        runs-on: ubuntu-latest
        timeout-minutes: 10
        outputs:
          matrix: ${{ steps.matrix.outputs.matrix }}
          count: ${{ steps.matrix.outputs.count }}
        steps:
          - uses: actions/checkout@v7.0.1
            with:
              fetch-depth: 0

          - uses: astral-sh/setup-uv@v10.2.0
            with:
              enable-cache: true
              version: "0.11.21"

          - name: Sync
            run: uv sync --locked

          # One matrix entry per non-empty pattern list: {"index": I, "patterns": [...]}.
          # Inputs reach the script through env, never interpolated into it.
          - name: Shard matrix
            id: matrix
            shell: bash
            env:
              MODE: ${{ inputs.mode }}
              PATTERN: ${{ inputs.pattern }}
              BASE: ${{ inputs.base }}
            run: |
              dir="$RUNNER_TEMP/shards"
              mkdir -p "$dir"
              case "$MODE" in
                changed)
                  uv run python tests/mutation/scope.py --base "origin/$BASE" --out "$dir/0" ;;
                pattern)
                  printf '%s\n' "$PATTERN" | tr -s ' \t' '\n' | sed '/^$/d' > "$dir/0"
                  if [ ! -s "$dir/0" ]; then echo "::error::mode pattern needs the pattern input"; exit 1; fi ;;
                all)
                  uv run python tests/mutation/shard.py --matrix-out "$dir/indices.txt"
                  for i in $(sed -n 's/^indices=//p' "$dir/indices.txt" | jq -r '.[]'); do
                    uv run python tests/mutation/shard.py --index "$i" --out "$dir/$i"
                  done ;;
                *) echo "::error::unknown mode $MODE"; exit 1 ;;
              esac
              for f in "$dir"/[0-9]*; do
                if [ -s "$f" ]; then
                  jq -Rsc --argjson index "$(basename "$f")" '{index: $index, patterns: (split("\n") | map(select(length > 0)))}' "$f"
                fi
              done | jq -sc '{include: .}' > "$dir/matrix.json"
              count=$(jq '.include | length' "$dir/matrix.json")
              echo "matrix=$(cat "$dir/matrix.json")" >> "$GITHUB_OUTPUT"
              echo "count=$count" >> "$GITHUB_OUTPUT"
              if [ "$count" -eq 0 ]; then
                echo "No changed functions in the mutation scope against origin/$BASE; nothing to run." | tee -a "$GITHUB_STEP_SUMMARY"
              else
                echo "Mode $MODE: $count shard(s)." | tee -a "$GITHUB_STEP_SUMMARY"
              fi

      shards:
        needs: plan
        if: needs.plan.outputs.count != '0'
        runs-on: ubuntu-latest
        timeout-minutes: 300
        strategy:
          fail-fast: false
          matrix: ${{ fromJSON(needs.plan.outputs.matrix) }}
        steps:
          - uses: actions/checkout@v7.0.1

          - uses: astral-sh/setup-uv@v10.2.0
            with:
              enable-cache: true
              version: "0.11.21"

          - name: Sync
            run: uv sync --locked

          - name: Shard patterns
            shell: bash
            env:
              PATTERNS: ${{ toJSON(matrix.patterns) }}
            run: |
              jq -r '.[]' <<< "$PATTERNS" > "$RUNNER_TEMP/patterns"
              cat "$RUNNER_TEMP/patterns"

          # `shell: bash` is `bash -eo pipefail`: inside the `if` condition `-e` does not fire,
          # and `pipefail` carries mutmut's failure through `tee`. `xargs -r` never runs
          # `mutmut run` with no pattern, which would test every mutant. Stopped at 270 minutes
          # so the steps after it keep 30.
          - name: Mutation run
            id: run
            shell: bash
            timeout-minutes: 270
            run: |
              if xargs -r -a "$RUNNER_TEMP/patterns" uv run mutmut run 2>&1 | tee "$RUNNER_TEMP/mutmut.log"; then
                echo tested=true >> "$GITHUB_OUTPUT"
              elif grep -q 'Filtered for specific mutants, but nothing matches' "$RUNNER_TEMP/mutmut.log"; then
                echo "the patterns match no mutant"; echo tested=false >> "$GITHUB_OUTPUT"
              else exit 1; fi

          # After a tested run, and after a failed or timed-out one so its partial counts
          # still upload; not after "nothing matches".
          - name: Export stats
            if: always() && (steps.run.outputs.tested == 'true' || steps.run.outcome == 'failure')
            run: uv run mutmut export-cicd-stats

          # Without the filter the file lists every mutant outside this shard as `not checked`.
          - name: Survivors
            if: always() && (steps.run.outputs.tested == 'true' || steps.run.outcome == 'failure')
            run: |
              uv run mutmut results | { grep -v ': not checked$' || true; } > mutants/survivors.txt

          - uses: actions/upload-artifact@v7.0.1
            if: always()
            with:
              name: mutation-shard-${{ matrix.index }}
              path: |
                mutants/mutmut-cicd-stats.json
                mutants/survivors.txt

      score:
        needs: [plan, shards]
        if: always() && needs.plan.result == 'success' && needs.plan.outputs.count != '0'
        runs-on: ubuntu-latest
        timeout-minutes: 15
        steps:
          - uses: actions/checkout@v7.0.1

          - uses: astral-sh/setup-uv@v10.2.0
            with:
              enable-cache: true
              version: "0.11.21"

          - name: Sync
            run: uv sync --locked

          - uses: actions/download-artifact@v8.0.1
            with:
              pattern: mutation-shard-*
              path: shards

          # Advisory: the score is reported, never compared with a threshold.
          - name: Score
            shell: bash
            run: |
              shopt -s nullglob
              stats=(shards/*/mutmut-cicd-stats.json)
              if [ ${#stats[@]} -eq 0 ]; then echo "no shard stats were uploaded" | tee -a "$GITHUB_STEP_SUMMARY"; exit 1; fi
              uv run python tests/mutation/score.py --summary "$GITHUB_STEP_SUMMARY" "${stats[@]}"

          - name: Partial run
            if: needs.shards.result != 'success'
            run: |
              echo "partial run: a shard failed or timed out" | tee -a "$GITHUB_STEP_SUMMARY"
              exit 1
    ```
    The plan step above was dry-run at plan time with the gate's snippet
    below: `changed` against `main` gave `count=0`, `changed` against the
    stub base gave one shard of 7 patterns, `pattern` with two patterns gave
    one shard of 2, an empty `pattern` exited 1, and `all` gave 4 shards
    of 12, 10, 10 and 10 patterns.
  - `pyproject.toml`: in `[tool.pyntpot.mutation]`, delete
    `min_score = 0.0` and keep `shards = 4`. The two-line comment above the
    table names the score floor, so it becomes one line:
    `# The shard count of the mutation workflow's "all" mode (set from measured timings; ADR 0012).`
    Nothing else in the file changes.
  - `tests/mutation/score.py`: advisory, no threshold.
    - Delete `passes` and the `tomllib` import; `main` no longer reads
      `pyproject.toml`.
    - Keep `CAUGHT`, `COUNTED`, `total_counts` and `score` unchanged.
    - Add `summary(counts: Mapping[str, int]) -> str`, the Markdown the
      workflow appends to the step summary. For the counts killed 5,
      timeout 1, survived 1, suspicious 1, no_tests 1, segfault 1 it
      returns exactly:
      ```text
      ## Mutation score (advisory)

      - Score: 0.6000
      - Survivors: 1
      - Tested: 10 (killed 5, timeout 1, survived 1, suspicious 1, no_tests 1, segfault 1)
      ```
      with a trailing newline (the `Tested` list follows `COUNTED`'s
      order). When `score` is `None` it returns exactly
      `"## Mutation score (advisory)\n\n- No mutants tested.\n"`.
    - `main(argv)` takes `STATS [STATS ...]` (argparse `nargs="+"`, so no
      path exits 2) and an optional `--summary PATH`. It reads each path
      in turn; an `OSError`, a `ValueError` (bad JSON) or a `KeyError` (a
      counted key missing, raised by `total_counts`) logs
      `cannot read stats <path>: <error>` and returns 1. Otherwise it logs
      the counts line as today, then `mutation score 0.6000 (advisory)` or
      `no mutants tested`, appends `summary(counts)` to `--summary` when
      given (open in `"a"` mode, UTF-8), and returns 0 whatever the score.
    - The module docstring: purpose (sum the CI stats, report the score,
      advisory with no threshold), the exit codes (0 when stats were read,
      1 when one cannot be read, 2 when none is given), the score formula
      and invariants as today; drop every `min_score` mention.
  - `tests/mutation/test_score.py`: remove `passes`,
    `test_no_tested_mutant_passes` and `test_the_floor_is_inclusive`. Keep
    the other three tests. Add, with pinned literal expectations (never
    built by calling `summary` on both sides):
    - the summary of the six-outcome counts above equals the literal
      block;
    - the summary of an untested run equals the literal
      `"## Mutation score (advisory)\n\n- No mutants tested.\n"`;
    - `main([str(stats), "--summary", str(out)])` on a `tmp_path` stats
      file written from `_stats(killed=3, survived=1, total=50)` returns 0
      and `out` then holds exactly
      `"## Mutation score (advisory)\n\n- Score: 0.7500\n- Survivors: 1\n- Tested: 4 (killed 3, timeout 0, survived 1, suspicious 0, no_tests 0, segfault 0)\n"`;
    - `main` on a score below any old floor (`_stats(survived=4)`) still
      returns 0 (the score is advisory);
    - `main` returns 1 for an unreadable stats file, parametrized with
      `ids=["missing", "not-json", "missing-key"]`: a path that does not
      exist, a file holding `not json`, and a file holding `{"killed": 1}`.
    - The module docstring says the score is advisory.
  - Docstring-only edits, so no text calls the job a nightly or a PR job
    (module docstrings are the agent contract); no logic, flag or test
    changes:
    - `tests/mutation/scope.py`: summary line `Turn a branch's diff into
      mutmut patterns for the functions it changed.`; `The PR job passes
      them to` becomes `The mutation workflow's changed mode passes them
      to`; `the nightly run covers it` becomes `the workflow's all mode
      covers it`.
    - `tests/mutation/shard.py`: summary line `Split the mutation scope
      into shards, largest module first.`; `which the nightly's plan job
      passes as` becomes `which the mutation workflow's plan job, in its
      all mode, passes as`; the argparse description becomes
      `Write one mutation shard's mutmut patterns.`
    - `tests/mutation/__init__.py`: `... the changed-function scope, the
      shards and the score.`
    - `tests/mutation/test_shard.py` module docstring: `Tests for the
      mutation shards: ...` (rest unchanged).
  - `docs/decisions/0012-mutation-threshold.md`: keep the filename (the
    ADR table under "P3 and P4: how to run a slice" keeps the slug
    `mutation-threshold`). Title
    `# 0012 — Mutation testing, manual and advisory`, `Status: accepted`.
    - Context: the spec (D17) asked for changed functions on every PR and
      the whole scope nightly; P5.3a built both and proposed a threshold
      from the first full nightly. The measured CI costs: the nightly
      about 12 h of runner time over 4 shards for `ink` and `letters`;
      the PR job 26 min for one changed `polyline` function (one edited
      line of `simplify`, 72 mutants), so a PR changing several functions
      that slow tests reach hits the 60-min timeout.
    - Decision (maintainer, 2026-10-07): mutation testing runs manually
      through `mutation.yml` (`workflow_dispatch` only; modes `changed`,
      `pattern`, `all`), and its score is advisory: reported in the run
      summary with the survivor count, never compared with a threshold.
      No nightly, no PR job, no `min_score`, no ratchet. When to run it:
      after writing tests for a module, before a release, and when a test
      feels weak.
    - Keep, updated to the new triggers, the existing sections:
      configuration (`[tool.mutmut]`, the test selection and why,
      `forkserver`, no `also_copy`); `[tool.pyntpot.mutation]` now holds
      only `shards`; the changed-function mechanism and its gaps (now the
      `changed` mode; "the nightly covers it" becomes "mode `all` covers
      it"); the sharding (now mode `all`); the score formula; the
      measured cost, scope and shard-count tables and rule as recorded.
      Replace the "Threshold" section with the decision above.
    - Consequences: no automatic CI signal for test strength; a run costs
      what the tables say, so mode `all` is for occasions, not every
      change; the `changed` mode inherits the PR job's gaps. Excluding
      slow end-to-end tests (such as
      `tests/unit/maps/test_cli.py::TestMap::test_a_full_cache_makes_no_request`,
      72 s) from the mutation test selection is a possible later
      improvement, not done here.
    - It amends ADR 0001's consequence "run mutation testing in CI": a
      sentence says so; ADR 0001 itself is not edited.
    - A short history line: proposed at P5.3a with a PR job, a sharded
      nightly and a threshold to come; accepted at P5.3c in this form
      instead.
  - `specs/001-port/spec.md`: append to the end of the D17 row only,
    inside the last cell before its closing ` |`, the sentence
    ` Superseded in part by ADR 0012 (2026-10-07): mutation testing runs manually, advisory, no nightly or PR job.`
    No other word of the row or the table changes.
  - `CONTRIBUTING.md`: replace the paragraph that starts `CI runs
    mutation testing (ADR 0012)` with the following, and keep the
    `uv run mutmut run "pyntpot.ink.polyline*"` block under it:

    > Mutation testing (ADR 0012) is manual and advisory: no pull-request
    > or scheduled job runs it, and its score has no threshold. Run it
    > after writing tests for a module, before a release, or when a test
    > feels weak. On GitHub, open Actions → Mutation → Run workflow, pick
    > the branch, and choose a mode: `changed` (the default) tests the
    > functions the branch changed against `base` (default `main`);
    > `pattern` tests the space-separated mutmut patterns in `pattern`,
    > such as `pyntpot.ink.polyline*`; `all` tests the whole scope in
    > `[tool.pyntpot.mutation] shards` parallel shards, about 12 hours of
    > runner time. The run's summary shows the score and the survivor
    > count, and each shard's artifact holds its stats and surviving
    > mutants. Locally, pass mutmut a pattern; it needs Linux or macOS,
    > because it forks. Results land in `mutants/`, which git ignores, and
    > `uv run mutmut results` lists them.

    (One line in the file, as the paragraph it replaces; the quote marks
    are not part of it.)
  - `specs/001-port/p5-run-log.md`: append one entry,
    `- <HH:MM> 2026-10-07 P5.3c: mutation testing manual and advisory
    (maintainer decision).`, with sub-bullets: the measured costs that
    drove it (nightly about 12 h over 4 shards; PR job 26 min for one
    function); the files changed; each mode's dry-run result from the gate
    (count and patterns per shard); the gate result; that P5.3b is
    superseded and `min_score` is gone.
  - `specs/001-port/tasks.md`: tick P5.3c in the same commit.
- Leave alone:
  - `tests/mutation/scope.py` and `shard.py` logic, flags and outputs, and
    `test_scope.py` / `test_shard.py` apart from the docstring above.
    The workflow uses their existing CLIs.
  - `[tool.mutmut]` and its comment block, `shards = 4`, every other
    `pyproject.toml` table, the ty and ruff config, and `uv.lock`.
  - `ci.yml`'s `checks` and `prerelease` jobs; `codspeed.yml`,
    `golden.yml`, `publish.yml`; `.gitignore` (`mutants/` stays).
  - ADR 0001 (append-only; ADR 0012 records the amendment) and every
    other ADR; the ADR table in this plan.
  - `spec.md` apart from the D17 row's appended sentence; `plan.md`
    (this slice and P5.3b's superseded note are the record).
- Gate, in this environment (`SCRATCH` is the session scratchpad):
  1. `uv sync && uv run ruff format --check . && uv run ruff check . && uv run ty check && uv run lint-imports && uv run pytest -m "not golden"`
  2. YAML parse and shape (each `yq -e` prints `true`):
     ```bash
     test ! -e .github/workflows/mutation-nightly.yml
     yq -e '(.on | keys == ["workflow_dispatch"]) and (.on.workflow_dispatch.inputs.mode.options == ["changed", "pattern", "all"]) and (.on.workflow_dispatch.inputs.mode.default == "changed") and (.on.workflow_dispatch.inputs.base.default == "main") and (.jobs | keys == ["plan", "score", "shards"])' .github/workflows/mutation.yml
     yq -e '.jobs | has("mutation") | not' .github/workflows/ci.yml
     ```
  3. Dry run of the plan job's matrix logic per mode. It extracts the
     `Shard matrix` and `Shard patterns` scripts from the committed
     workflow, so it tests the file, not a copy. `d44b420~1` is a stub
     base before a `letters` change; the stub ref is deleted afterwards.
     ```bash
     WF=.github/workflows/mutation.yml
     yq -r '.jobs.plan.steps[] | select(.id == "matrix") | .run' "$WF" > "$SCRATCH/plan-step.sh"
     yq -r '.jobs.shards.steps[] | select(.name == "Shard patterns") | .run' "$WF" > "$SCRATCH/shard-step.sh"
     dry() {  # dry MODE PATTERN BASE
       local rt="$SCRATCH/rt-$1"; rm -rf "$rt"; mkdir -p "$rt"; : > "$rt/out"; : > "$rt/summary"
       RUNNER_TEMP="$rt" GITHUB_OUTPUT="$rt/out" GITHUB_STEP_SUMMARY="$rt/summary" \
         MODE="$1" PATTERN="$2" BASE="$3" bash -eo pipefail "$SCRATCH/plan-step.sh" > /dev/null 2>&1
       echo "mode=$1 exit=$? count=$(sed -n 's/^count=//p' "$rt/out") summary=$(cat "$rt/summary")"
       sed -n 's/^matrix=//p' "$rt/out" | jq -c '.include[]' | while read -r entry; do
         RUNNER_TEMP="$rt" PATTERNS="$(jq -c '.patterns' <<< "$entry")" bash -eo pipefail "$SCRATCH/shard-step.sh" > /dev/null
         echo "  shard $(jq '.index' <<< "$entry"): $(wc -l < "$rt/patterns") patterns, first $(head -1 "$rt/patterns")"
       done
     }
     dry changed "" main
     git update-ref refs/remotes/origin/p5c-dry d44b420~1
     dry changed "" p5c-dry
     git update-ref -d refs/remotes/origin/p5c-dry
     dry pattern "pyntpot.ink.polyline.x_simplify*  pyntpot.letters.hand*" main
     dry pattern "   " main
     dry all "" main
     ```
     Expected: `changed`/`main` exit 0, `count=0` and the "nothing to
     run" summary (P5 does not touch `src/`); `changed`/stub exit 0,
     `count=1`, at least one `pyntpot.letters.` pattern; `pattern` exit 0,
     `count=1`, 2 patterns; empty `pattern` exit 1; `all` exit 0,
     `count` equal to `shards` (4), every shard non-empty. Paste the
     output into the run log.
  4. `grep -rn "mutation-nightly\|min_score" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=mutants --include=*.py --include=*.toml --include=*.yml --include=*.md .`
     matches only `specs/001-port/` (plan, tasks, run log: history) and
     ADR 0012's history line.
- After the merge (not a gate; whoever merges PR #7 records it in the run
  log): `workflow_dispatch` only works once the file is on the default
  branch, so dispatch `gh workflow run mutation.yml --ref main -f mode=pattern -f pattern='pyntpot.letters.nib.x__ink_colour*'`
  and check the run is green and its summary shows the score block.
- Commit: `Make mutation testing manual and advisory`

### P6. Docstrings, prose and references (D24, D25)

Implements D24 (every technique cites its source), D25 (a docstring audit,
then a prose audit) and acceptance criterion 4, and answers the spec's
design-sources open question. Fattened at P6.0 from the five-step sketch.
Measurements below were taken at commit `1154129` on branch `p6-docs`; line
numbers drift, so every site is named by its dotted path
(`pyntpot.ink.polyline.simplify`), and the line is only a hint.

**Measured at P6.0** (`wc -l` and an AST count over `src/pyntpot`):

| Subpackage | Modules | Lines | Classes and functions | Public of those | Docstring lines | `#` comment lines |
|---|---|---|---|---|---|---|
| `ink` | 19 | 3,905 | 117 | 87 | 1,178 | 433 |
| `letters` | 8 | 1,722 | 74 | 32 | 507 | 107 |
| `maps` (all) | 80 | 13,748 | 460 | 258 | 4,099 | 1,057 |
| `maps` top level | 35 | 5,964 | 222 | 139 | 1,869 | |
| `maps/lettering` | 21 | 4,765 | 129 | 48 | 1,369 | |
| `maps/candidates` | 8 | 1,241 | 36 | 18 | 346 | |
| `maps/painter` | 12 | 1,202 | 47 | 34 | 353 | |
| `maps/providers` | 4 | 576 | 26 | 19 | 162 | |
| `pyntpot/__init__.py` | 1 | 52 | 0 | 0 | 12 | |

Nine functions or classes have no docstring (4 in `ink`, 4 in `maps` top
level, 1 in `maps/lettering`). The two files nearest the 400-line budget are
`ink/brush.py` (391) and `maps/lettering/span_line.py` (385). No `src/` file
has an em-dash or en-dash; `docs/decisions/` has 15 and
`docs/runbooks/update-dependencies.md` 1. No `src/` or `tests/` code reads
`__doc__` or `inspect.getdoc`, so a docstring edit cannot reach a pixel. No
`src/` docstring cites a source today.

**Rules for the whole phase.**

- **P6 edits docstrings, `#` comments and prose only.** It adds one
  architecture test (P6.4) and three documents (`p6-inventory.md`,
  `references.md`, issue files). It never changes an executable statement,
  an identifier, a default, a file's location, the theme TOML or the
  vendored font. Every slice that touches `src/` proves it with the
  **AST-neutral check** below and with G-here plus G-self (see "P3 and P4:
  how to run a slice"; from P3.15 on G-here includes the byte-exact
  `uv run pytest -m golden`). Slices that touch no `src/` file run G-here.
- **AST-neutral check.** Write this script to `$SCRATCH/ast_neutral.py`
  (scratch only, never committed) and run it from the repo root as
  `cd /home/user/pyntpot && python3 -I "$SCRATCH/ast_neutral.py" BASE`, where
  `BASE` is the slice's starting commit. It must print `AST-neutral: N files`
  and exit 0. A non-zero exit means the slice changed code: revert that
  hunk, never commit it.
  ```python
  """Exit 1 unless every src/ file changed since BASE differs from it in docstrings and comments only."""
  import ast
  import subprocess
  import sys
  from pathlib import Path

  DOC_OWNERS = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)


  def blanked(source: str) -> str:
      tree = ast.parse(source)
      for node in ast.walk(tree):
          if isinstance(node, DOC_OWNERS) and node.body:
              first = node.body[0]
              if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                  first.value.value = ""
      return ast.dump(tree, include_attributes=False)


  base = sys.argv[1]
  changed = subprocess.run(["git", "diff", "--name-only", base, "--", "src"], capture_output=True, text=True, check=True).stdout.split()
  bad = []
  for name in changed:
      if not name.endswith(".py"):
          bad.append(f"{name}: not a Python file")
          continue
      old = subprocess.run(["git", "show", f"{base}:{name}"], capture_output=True, text=True, check=True).stdout
      if blanked(old) != blanked(Path(name).read_text()):
          bad.append(f"{name}: code changed")
  sys.stdout.write("\n".join(bad) + "\n" if bad else f"AST-neutral: {len(changed)} files\n")
  sys.exit(1 if bad else 0)
  ```
  Comments are not in the AST, so comment edits pass; a renamed name, a
  changed literal, a moved line of code or a touched TOML fails.
- **No stop points; a stated rule makes every choice, and the run log
  records it.** Each slice measures first, applies the rules below, and
  appends to `specs/001-port/p6-run-log.md` (in every slice's owner files):
  its start and end time (BST, `TZ=Europe/London date +%H:%M`), the wall
  time of each gate stage, the counts it names, and every choice as
  `choice: <what> | rule: <rule name> | inputs: <what it read>`. The final
  HTML report after P6 is built from that log.
- **Rule: behaviour wins.** When a docstring or comment disagrees with the
  code, the code is the truth (the goldens pin it). Rewrite the text to
  describe what the code does. If the gap looks like a code defect (the text
  describes the more plausible intent), also file
  `docs/issues/<kebab-slug>.md` with the site, what the text said, what the
  code does, and how to show it; never edit the code in P6.
- **Rule: fix now or file.** A finding is fixed in the slice when all hold:
  the edit is to a docstring, a `#` comment or a prose file in the slice's
  owner files; it renames, moves or deletes no identifier, file or test; it
  changes no executable statement; and the file stays within 400 lines.
  Otherwise it goes to `docs/issues/<kebab-slug>.md` (one file per finding,
  the format of the existing ones: a title, where, what, why it is out of
  scope, the proposed change). Out-of-scope discoveries of any kind go there
  too. The run log counts fixed and filed per slice.
- **Rule: line budget.** A split is out of P6 scope: it moves names and
  repoints importers and tests, which the AST-neutral check forbids and
  which is a G-self refactor slice of its own, not a docs pass. So: (1) the
  citation line of P6.4 is one line and always lands (the fullest file,
  `ink/brush.py` at 391, has room for nine); (2) a docstring or comment fix
  that keeps a file's line count or lowers it always lands; (3) a fix that
  adds lines lands while the file stays at or under 400; (4) the rest go to
  one `docs/issues/line-budget-<module>.md` per file, holding the exact text
  that could not be added and the responsibility line the file would split
  along. Never shorten, merge or delete other text to make room (CLAUDE.md:
  never trim to fit). Nothing is added to `exemptions/line_budget.txt`.
- **Rule: house rules beat the skills.** Where a skill and `CLAUDE.md`
  disagree, `CLAUDE.md` wins. In particular a module docstring keeps "what
  it does not do" and its invariants, though the `docstrings` skill says not
  to narrate non-goals; that skill rule applies to function and class
  docstrings only. Docstrings state capability facts, never spec, phase or
  slice numbers (`tests/architecture/test_docstring_conventions.py` catches
  `spec NNN`; the house rule bans `P6.3`-style numbers too).
- **Rule: British English.** Prose uses British spelling: `-ise`, `-our`,
  `-re`, `centreline`, `grey`. Never changed for British spelling:
  identifiers, string literals, quoted titles of cited works (Curtis's
  *Computer-Generated Watercolor* keeps its spelling), proper names and
  third-party API names.
- **Rule: which files the dash audit covers.** The `emdash-audit` skill
  skips agent-facing files. Here: `src/` docstrings and comments are covered
  (they are the published API reference P7 builds on); `README.md`,
  `GLOSSARY.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `docs/README.md`,
  `docs/architecture.md`, `docs/explanation/**` and `docs/runbooks/**` are
  covered. Not covered, and not edited by the prose pass at all:
  `CLAUDE.md`, `BOUNDARIES.md`, `specs/**`, `.claude/**` (agent-facing),
  `docs/decisions/**` (records: their heading form `# NNNN — Title` is
  fixed by this plan, and an accepted ADR changes only by a superseding
  one), `docs/issues/**` (working notes) and `tests/**`.
- **Branch and PR.** Every slice lands as one commit on `p6-docs`, in
  order, and the branch goes to `main` through one PR after P6.6. The
  implementer agent never commits; the orchestrating session commits with
  the slice's message (imperative, one line, no trailers) and ticks
  `tasks.md` in the same commit.
- **Order:** P6.0 → P6.1 → P6.2 → P6.3 → P6.4 → P6.5a → P6.5b → P6.5c →
  P6.5d → P6.5e → P6.6, sequential. Why: P6.2 matches against P6.1's
  inventory; P6.3 cites what P6.1 and P6.2 list; P6.4's test needs
  `references.md`, and it lands before the docstring audit so the audit
  cannot delete a citation line without going red; the docstring sessions
  run bottom-up through the layers (`ink`, `letters`, then `maps`), so a
  `maps` docstring that describes an `ink` call reads an already-corrected
  `ink` docstring; the prose pass comes last because it reads the audited
  docstrings' vocabulary and `references.md`. Every slice appends to the run
  log and most to `docs/issues/`, so none run in parallel.
- **Public API first**, within each docstring session: the module docstring
  of each `__init__.py` first, then the names in `pyntpot.__all__` and the
  session's subpackage `__all__` (`ink`: `Brush`, `Canvas`, `Sheet`,
  `composite`, `stamp`, `wash`; `letters`: `Hand`; `maps`: its `__all__`),
  then every other name without a leading underscore, module by module in
  path order, then the private names in the same order. The run log records
  the time at which the public names were done.

**Tool facts the slices rely on** (verified at P6.0 on 2026-10-07 from this
container; recheck only if a fetch behaves differently):

- **Fetch with `curl` through Bash.** `HTTPS_PROXY` is set and the proxy CA
  bundle covers every host. The `plan-slice-implementer` agent has Read,
  Glob, Grep, Bash, Edit and Write only: no WebFetch, no WebSearch, no Skill
  tool. WebFetch is not used for verification even where available: it
  returns a model's summary, not the bytes and the status the log needs,
  and it hits the same publisher block (tried: `dl.acm.org` 403).
- `curl -sS -o /dev/null -w '%{http_code} %{redirect_url}' https://doi.org/10.1145/357994.358023`
  gives `302 -> https://dl.acm.org/doi/10.1145/357994.358023`. Following it
  (`-L`) gives **403**: a Cloudflare challenge page (`cf-mitigated:
  challenge`, title "Just a moment..."). ACM landing pages are blocked from
  here; expect the same of other Cloudflare-fronted publishers.
- `curl -sS https://api.crossref.org/works/10.1145/357994.358023` gives
  **200** JSON: `.message.title[0]` "A fast parallel algorithm for thinning
  digital patterns", authors Zhang, T. Y. and Suen, C. Y., issued 1984-03,
  *Communications of the ACM* 27(3), 236-239. DOI content negotiation
  (`curl -sSL -H 'Accept: application/vnd.citationstyles.csl+json' https://doi.org/<DOI>`)
  also returns 200 CSL JSON, served by Crossref. Extract with
  `jq '.message | {title, author: [.author[]? | .family], year: .issued["date-parts"][0][0], container: ."container-title"[0], volume, issue, page}'`.
- Crossref answers **429** to a fast burst (seen on the 15th call of a
  loop with no pause). Pause 1 s between calls; on 429 or a connection
  reset retry after 5, 10 and 20 s. Do not add a `mailto=` parameter: it
  would send the maintainer's address to a third party.
- Crossref resolves these candidate DOIs to the listed metadata (200, read
  at P6.0; P6.3 re-fetches them all): `10.3138/FM57-6770-U75U-7727`
  (Douglas, Peucker 1973), `10.1016/0146-664X(74)90028-8` (Chaikin 1974),
  `10.1016/B978-0-12-079050-0.50020-5` (Catmull, Rom 1974),
  `10.1145/37402.37422` (Lorensen, Cline 1987),
  `10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2` (Duchon 1979),
  `10.1145/325165.325247` (Perlin 1985), `10.1137/1010093` (Mandelbrot,
  Van Ness 1968), `10.1016/S0734-189X(86)80047-0` (Borgefors 1986),
  `10.1109/TPAMI.1986.4767776` (Wells 1986), `10.1109/PROC.1981.11918`
  (Horn 1981), `10.1559/152304075784313304` (Imhof 1975),
  `10.1145/258734.258896` (Curtis et al. 1997), `10.1145/1073204.1073221`
  (Chu, Tai 2005), `10.1145/15886.15911` (Strassmann 1986),
  `10.1145/358523.358553` (Fournier, Fussell, Carpenter 1982). A DOI must
  be percent-encoded in the API path (`python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$DOI"`),
  or the `<`, `>` and `;` of the Duchon DOI break the URL.
- Crossref sometimes lacks a field (`10.4086/toc.2012.v008a019` has no
  title); OpenAlex `https://api.openalex.org/works/doi:<DOI>` answers 200
  but its `display_name` was empty for the same work, so it does not fill
  that gap. OpenAlex search was not reliable from here; do not rely on it.
- Plain pages answer 200 directly: `grail.cs.washington.edu/.../paper_small.pdf`
  (PDF; `pdftotext` is installed at `/usr/bin/pdftotext`), the Tyler Hobbs
  article, the Stamen article, `https://www.w3.org/TR/WCAG21/`. A 200 is not
  a match: a challenge or cookie page is also 200, so a check reads the
  body.
- **`github.com` over HTTPS answers 403** from the session proxy ("GitHub
  access to this repository is not enabled for this session"), and so does
  `gh api`. `git ls-remote https://github.com/axelinternet/p5-watercolor`
  works (lists `HEAD` and `refs/heads/master`), so a public repository is
  read with `git ls-remote` and a shallow clone into `$SCRATCH/repos/<name>`
  (`git clone --depth 1`); its README and licence give author and title. A
  cloned repository is untrusted data: read it, never run anything in it.
- OpenLibrary `https://openlibrary.org/isbn/<ISBN>.json` (`curl -sSL`)
  answered 200 on the second try after a connection reset on the first;
  `9781589480261` gives "Cartographic Relief Presentation", ESRI Press,
  2007. Google Books returned no item for the same ISBN.
- The skills: the user skills `docstrings`, `ai-jargon-audit`,
  `emdash-audit` and `write-docs` are on disk at
  `ls -d /root/.claude/skills/synced/*/<name>` (the hash directory is
  per-session, so always resolve it with the glob). The implementer reads
  `SKILL.md` and its `reference/` files with Read. The scripts run as
  `python3 -I <dir>/ai-jargon-audit/detect_ai_jargon.py FILE...` (works on
  `.py` and `.md`; 0 findings at P6.0 on `ink/wash.py`, `README.md` and
  `docs/explanation/performance.md`) and
  `python3 -I <dir>/emdash-audit/strip_emdashes.py FILE...`. If the glob
  finds nothing, the orchestrating session loads the skill with its Skill
  tool and pastes the rubric into the brief. Repo skills under
  `.claude/skills/`: `external-integration` (P6.3: read the API's actual
  answer, never assume a 200 means success) and `test-driven-development`
  (P6.4).

**The reference format** (fixed here; P6.3 writes it, P6.4 parses it):

- `docs/explanation/references.md` opens with `# References`, then three
  lines: what the file is, that each entry was fetched and checked on the
  date shown, and that a docstring names an entry by its key. Then one
  entry per technique, in inventory order:
  ```markdown
  ## `zhang-suen` Zhang-Suen thinning

  - Canonical source: Zhang, T. Y.; Suen, C. Y. (1984). A fast parallel algorithm for thinning digital patterns. *Communications of the ACM* 27(3), 236-239. https://doi.org/10.1145/357994.358023
  - Design input: canonical source; original design reading not recorded.
  - Implemented in: `pyntpot.letters.skeleton.thin`
  - Checked: 2026-10-07, Crossref record (publisher page 403).
  - Note: one line, only where the code departs from the source.
  ```
  After the entries, a section `## Read during design, no technique here`
  lists every `design-sources.md` entry that informs no inventory item, as
  one bullet each with its status. Every URL in `design-sources.md` appears
  in the file (P9.4 checks this before it deletes that list).
- **Key**: lowercase ASCII kebab-case naming the technique, not the paper,
  so a later change of source keeps the key: `zhang-suen`,
  `douglas-peucker`, `kubelka-munk`, `edge-darkening`. Matches
  `[a-z][a-z0-9-]*`, unique, no digits that read as a phase number.
- **Implemented in**: one or more backticked dotted paths to a module,
  class, function or method under `pyntpot`, comma-separated, or the bare
  word `none` followed by one clause saying where the technique shows
  instead (for a technique applied as a value choice, such as a contrast
  ratio that chose the default inks).
- **Citation line in a docstring**: exactly
  `` Source: `<key>` in docs/explanation/references.md. ``, on its own line
  as the last paragraph before the first Google section (`Args:`,
  `Returns:` ...), or as the last line when there is none. Not
  `References:` or `See Also:`, which pydocstyle's Google convention parses
  as sections. A site that implements two techniques carries two lines.

**The status of a checked entry** (P6.3 assigns one per source, by the
first route that matches; the log records every route tried):

1. `publisher page`: the DOI or URL, followed with `curl -sSL`, answers 200
   and the body matches (see *match*).
2. `Crossref record`: the publisher page is not 200 or is a challenge page,
   and the Crossref API record for the DOI matches. This is the rule for a
   paywalled or proxy-blocked landing page: the DOI registry's own record
   is the metadata of record, so the entry counts as checked, and the
   `Checked:` line names the publisher status (`Crossref record (publisher
   page 403)`).
3. `index record`: no DOI, and an OpenLibrary ISBN record matches (books).
4. `repository`: a public Git repository, read by `git ls-remote` and a
   shallow clone; its README names the title and author.
5. `cited by <key>`: a work with no DOI, ISBN or live page (such as
   Kubelka, Munk 1931) is checked when the reference list of a source
   already checked by routes 1 to 4 (its fetched PDF or Crossref
   `.message.reference`) gives the same authors, year and title.
6. `cited in design, not verified`: every route failed. Allowed only for a
   design input, never for a canonical source (see the canonical-source
   rule, step 6).

*Match*: every author family name in the entry appears in the record, the
year is equal, and the title is equal after lowercasing, stripping
punctuation and collapsing whitespace (a record's subtitle after a colon
may be extra). For a web page the title and the author name must appear in
the body; the year must appear in the body or its `<meta>` date, otherwise
the entry gives the year with "(year from the design record, not shown on
the page)". A mismatch in one field is corrected to the record and logged;
a mismatch in two or more means the source is not the one meant: try the
next candidate.

#### P6.0 Fatten P6; plan-reviewer pass

- This section. A plan-reviewer agent reviews it, and P6.1 does not start
  until the review passes. `tasks.md` gains P6.0 and the new slice ids.
- Tool facts above were fetched from this container at `1154129`.
- Owner files: `specs/001-port/plan.md` (this section), `specs/001-port/tasks.md`
  (the P6 list). The orchestrating session adds the review outcome to the
  run log.
- Commit: `Fatten P6 into slices`

#### P6.1 References inventory

- Implements D24, inventory step; predecessor P6.0. Touches no `src/` file.
- Owner files: `specs/001-port/p6-inventory.md` (new),
  `specs/001-port/p6-run-log.md`, `docs/issues/*.md` (new files only).
- Leave alone: `src/**`, `tests/**`, `design-sources.md`, `references.md`
  (not yet written).
- First, on the clean starting commit, run G-here and log each stage's wall
  time: it is P6's baseline, and every later slice compares to it.
- **Inclusion rule.** A technique enters the inventory when (a) the code
  names it in an identifier, docstring or comment by an eponym or a term of
  art with a published originating description (Zhang-Suen, Douglas-Peucker,
  Kubelka-Munk, marching squares, Lanczos, Catmull-Rom, Chaikin, fBm,
  chamfer distance, hillshade, hachures), or (b) `design-sources.md` names
  it and a code site implements it (backruns, granulation, edge darkening,
  midpoint deformation, the shallow-water pass, multiply compositing, the
  bristle brush). A single elementary formula with no technique name
  (`smoothstep`, linear interpolation, a clamp, a mitre limit) does not
  enter; each such near miss is logged as `considered, excluded:
  elementary`. Find candidates with
  `grep -rniE 'kubelka|munk|zhang|suen|thinning|marching|lanczos|fbm|brownian|value.noise|chamfer|distance|edt|blur|gaussian|box pass|hillshad|shade|hachur|douglas|peucker|chaikin|catmull|spline|midpoint|deform|granulat|bloom|backrun|edge darken|flow|shallow|multiply|bristle|reservoir|nib|luminance|contrast|wcag|placement|clearance' src/pyntpot --include=*.py`
  and read each hit's function body.
- **Site rule.** A site is the function, method or class whose body carries
  out the technique (read the body; a caller that only passes arguments is
  not a site). Where the code's name and its body disagree, the body
  decides, the inventory names what the body does, and the name mismatch is
  filed (known at P6.0: `pyntpot.ink.noise.edt` is a two-pass chamfer
  distance with weights 1 and 1.41421356, not a Euclidean transform; its
  docstring already says chamfer; the rename is
  `docs/issues/edt-is-a-chamfer-distance.md`). A technique that shows only as
  a chosen value gets site `none` and a clause naming where the value lives.
- **Split rule.** One inventory row per technique. A family the old sketch
  listed as one line ("watercolour wash effects", "brush and nib stroke
  models", "fBm and value noise") is split into one row per technique that
  has its own site; two techniques that share one site and one source stay
  one row.
- The seed, from the P6.0 grep (P6.1 confirms each by reading the body, adds
  what the inclusion rule finds, and drops a seed row only with a logged
  reason):

  | Key | Technique | Sites at `1154129` |
  |---|---|---|
  | `kubelka-munk` | Kubelka-Munk glazing | `pyntpot.ink.pigment.km_rt` (85), `km_plate` (124) |
  | `multiply-compositing` | multiply compositing | `pyntpot.ink.pigment.multiply_plate` (74) |
  | `zhang-suen` | Zhang-Suen thinning | `pyntpot.letters.skeleton.thin` (88) |
  | `douglas-peucker` | Douglas-Peucker simplification | `pyntpot.ink.polyline.simplify` (44) |
  | `chaikin` | Chaikin corner cutting | `pyntpot.ink.polyline.smooth` (83) |
  | `catmull-rom` | Catmull-Rom spline | `pyntpot.ink.curves.spline` (26) |
  | `marching-squares` | marching squares contours | `pyntpot.maps.contours.marching_squares` (33) |
  | `lanczos` | Lanczos reduction | `pyntpot.ink.pad._reduce` (118) |
  | `value-noise` | value noise | `pyntpot.ink.noise.value_noise` (26) |
  | `fbm` | fractional Brownian motion | `pyntpot.ink.noise.fbm` (48), `fbm_aniso` (101), `pyntpot.ink.tip._fbm1` (125) |
  | `chamfer-distance` | chamfer distance transform | `pyntpot.ink.noise.edt` (168) |
  | `box-blur` | Gaussian by three box passes | `pyntpot.ink.noise.blur` (156) |
  | `hillshade` | hillshade from slope and aspect | `pyntpot.maps.relief._shade` (128) |
  | `hachures` | hachures down the slope | `pyntpot.maps.relief_strokes.hachures` (171) |
  | `midpoint-displacement` | recursive midpoint displacement | `pyntpot.ink.raster.deform_ring` (61), `pyntpot.ink.polyline.deform_line` (302) |
  | `edge-darkening` | edge darkening as outward flow | `pyntpot.ink.wash.flow_edge` (57) |
  | `backruns` | backruns (blooms) | `pyntpot.ink.wash.bloom` (90) |
  | `granulation` | granulation following the paper | `pyntpot.ink.sheet.Sheet.pits` (98) |
  | `shallow-water` | the shallow-water pass | `pyntpot.maps.painter.fluid.paint_fluid` (20) |
  | `bristle-brush` | bristle brush tip and stamp | `pyntpot.ink.stamp.stamp` (248) |
  | `nib` | pen nib stroke | `pyntpot.letters.nib.plate` (273) |
  | `label-placement` | label placement (clearance, set along a line, one name a place) | `pyntpot.maps.lettering.placement.place` (70) |
  | `wcag-contrast` | WCAG contrast ratio | `none` (grep finds no luminance or contrast-ratio code; P6.1 checks the default theme's inks) |

- Write `p6-inventory.md` as that table with a fourth column, the
  candidate canonical source from P6.3's table, and a fifth, empty, for
  P6.2. Header: commit, date, the grep command.
- Hand-off: row count, each added or dropped row with its rule, the near
  misses, issues filed, G-here stage times.
- Gate: G-here (no `src/` change; `git diff --stat -- src tests` is empty).
- Commit: `Inventory the techniques the code implements`

#### P6.2 Match the design sources to the inventory

- Implements the spec's design-sources open question; predecessor P6.1.
  The recovery itself is done (2026-10-04, `design-sources.md`); this slice
  matches and checks it, it does not search for more records.
- Owner files: `specs/001-port/p6-inventory.md` (the design-input column),
  `specs/001-port/p6-run-log.md`, `specs/001-port/spec.md` (the open
  question moves to "Resolved questions": "Design-input sources
  (2026-10-07): recovered in `design-sources.md`; where none was recorded,
  the entry cites the canonical source and says so (D24).").
- Leave alone: `design-sources.md` (P9.4 deletes it; its text is the
  record), `src/**`, `tests/**`.
- **Match rule.** For each `design-sources.md` entry, in file order: it is
  the design input of an inventory row when its right-hand note names that
  row's technique or effect. One entry may serve several rows (Curtis 1997
  serves `edge-darkening`, `backruns`, `granulation`, `kubelka-munk` and
  `shallow-water`); a row may have several design inputs, listed in
  `design-sources.md` order. An entry that names a technique without a
  document read ("Lanczos resampling (named)", "Zhang, Suen ... named in
  the code", "Marching squares (named in the code)", "Euclidean distance
  transform; fractional Brownian motion and value noise (named in the
  code)", "WCAG AA contrast ratios ... (named)") is **not** a recovered
  reading: the row's design input is "canonical source; original design
  reading not recorded". An entry that informs no row (an upstream-only SVG
  filter, a rejected style such as Adventures in Mapping, Stadia's
  raster-only note, the Wainwright and line-and-wash idioms, the data
  providers, the font, "Named only, no source read" and the search terms)
  is marked `no technique here` and goes to the closing section of
  `references.md` in P6.3.
- Hand-off: per row, its design inputs or the not-recorded line; the
  `no technique here` list; any `design-sources.md` entry that matched
  nothing and was not on the no-technique list (expect none).
- Gate: G-here.
- Commit: `Match the design sources to the inventory`

#### P6.3 Fetch and check every source; write `references.md`

- Implements D24; predecessor P6.2. Touches no `src/` file. Load the
  `write-docs` skill (the file is reference-mode content under the
  `explanation/` path D24 and P7 fix; keep the path, write it as
  reference) and the repo skill `external-integration`.
- Owner files: `docs/explanation/references.md` (new), `docs/README.md`
  (add `explanation/: background and the references bibliography` to the
  subfolder list), `GLOSSARY.md` (new row: `reference | One entry of
  docs/explanation/references.md: a technique, its key, its canonical
  source and design input, and where the code implements it.`),
  `specs/001-port/p6-inventory.md` (status column),
  `specs/001-port/p6-run-log.md`, `docs/issues/*.md` (new files only).
- Leave alone: `src/**`, `tests/**`, `design-sources.md`, `README.md`
  (P7 adds its pointer).
- **Canonical-source rule** (which source, when several exist), applied in
  order until one verifies:
  1. The work that introduced the technique under the name the code uses
     (the eponym's paper: Zhang-Suen, Douglas-Peucker, Chaikin,
     Catmull-Rom, Kubelka-Munk).
  2. A technique with no eponym: the first peer-reviewed description of
     the algorithm the code's body carries out, not of the general idea
     (the body of `edt` is a chamfer, so Borgefors 1986, not a Euclidean
     transform paper).
  3. A 2-D or special case of a named family with no paper of its own:
     the family's introducing paper, with the note "the 2-D case"
     (marching squares from Lorensen, Cline 1987).
  4. A formula fixed by a standard: the current Recommendation of the
     standards body that defines it (WCAG 2.2 for the contrast ratio, W3C
     Compositing and Blending Level 1 for multiply).
  5. A composite of rules (label placement) or a model of the code's own
     (the nib): the foundational paper the rules follow, and a `Note:`
     line saying which parts are this library's own. Where no published
     work describes the technique as built, the `Canonical source:` line
     names the nearest checked work and begins "Nearest published work:".
  6. If no candidate verifies, use a checked design input or another
     entry's checked source that describes the technique, marked
     "canonical source not checked; described in `<key>`". A canonical
     line is never left `not verified`.
- The candidates, from the P6.0 Crossref checks and the literature; P6.3
  fetches each and the rule above replaces one that fails:

  | Key | Candidate canonical source |
  |---|---|
  | `kubelka-munk` | Kubelka, Munk (1931), "Ein Beitrag zur Optik der Farbanstriche", *Zeitschrift für technische Physik* 12, 593-601 (no DOI: route 5) |
  | `multiply-compositing` | W3C, *Compositing and Blending Level 1*, https://www.w3.org/TR/compositing-1/ |
  | `zhang-suen` | `10.1145/357994.358023` |
  | `douglas-peucker` | `10.3138/FM57-6770-U75U-7727` |
  | `chaikin` | `10.1016/0146-664X(74)90028-8` |
  | `catmull-rom` | `10.1016/B978-0-12-079050-0.50020-5` |
  | `marching-squares` | `10.1145/37402.37422`, the 2-D case |
  | `lanczos` | `10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2` |
  | `value-noise` | `10.1145/325165.325247` (Perlin 1985) |
  | `fbm` | `10.1137/1010093` |
  | `chamfer-distance` | `10.1016/S0734-189X(86)80047-0` |
  | `box-blur` | `10.1109/TPAMI.1986.4767776` |
  | `hillshade` | `10.1109/PROC.1981.11918` |
  | `hachures` | Imhof, *Cartographic Relief Presentation*, ESRI Press 2007, ISBN 9781589480261 (route 3) |
  | `midpoint-displacement` | `10.1145/358523.358553` |
  | `edge-darkening`, `backruns`, `granulation`, `shallow-water` | `10.1145/258734.258896` |
  | `bristle-brush` | `10.1145/15886.15911` |
  | `nib` | nearest published work, rule 5: `10.1145/15886.15911` |
  | `label-placement` | `10.1559/152304075784313304` |
  | `wcag-contrast` | W3C, *Web Content Accessibility Guidelines 2.2*, https://www.w3.org/TR/WCAG22/ |

- Steps: for every canonical and design-input source, fetch by the status
  routes in order (tool facts: curl, 1 s pause, retries) and log one line
  per source: `<key> | <source> | URL fetched | HTTP status (after
  redirects) | route that matched | fields matched | corrections`. Save
  each response under `$SCRATCH/refs/<key>-<n>.{json,html,pdf}` and grep
  the saved body, never the terminal summary. Then write `references.md`
  in the fixed format, the `Checked:` line giving the date and the status.
  A `Note:` line states where the code departs from the source, from
  reading the site's body (for example `hillshade`: slope by
  `numpy.gradient` central differences, not Horn's eight-neighbour
  weights), in one line.
- Mechanical checks before hand-off (paste the output into the log):
  ```bash
  cd /home/user/pyntpot
  # every inventory key has an entry
  grep -oE '^\| `[a-z][a-z0-9-]*`' specs/001-port/p6-inventory.md | grep -oE '[a-z][a-z0-9-]*' | sort -u > "$SCRATCH/keys-inventory"
  grep -oE '^## `[a-z][a-z0-9-]*`' docs/explanation/references.md | grep -oE '[a-z][a-z0-9-]*' | sort > "$SCRATCH/keys-refs"
  diff "$SCRATCH/keys-inventory" <(sort -u "$SCRATCH/keys-refs") && test "$(wc -l < "$SCRATCH/keys-refs")" = "$(sort -u "$SCRATCH/keys-refs" | wc -l)"
  # every design-sources URL appears (the P9.4 check, early)
  grep -oE 'https?://[^ )]+' specs/001-port/design-sources.md | while read -r u; do grep -qF "$u" docs/explanation/references.md || echo "missing $u"; done
  # no canonical line left unchecked
  ! grep -n 'Canonical source:.*not verified' docs/explanation/references.md
  ```
  The first prints nothing and exits 0, the second prints nothing, the
  third exits 0. `uv run pytest tests/architecture/test_coordinates.py`
  passes (it scans `docs/`; a DOI such as `10.1145` is not a coordinate).
- Hand-off: entries by status, every correction made to a design-sources
  entry, every candidate replaced and why, fetch counts and wall time.
- Gate: G-here.
- Commit: `Add the references, every source fetched and checked`

#### P6.4 Cite each key in its docstring, and gate it

- Implements D24's docstring half and acceptance criterion 4; predecessor
  P6.3. Load the repo skill `test-driven-development`.
- Owner files:
  - `tests/architecture/test_reference_keys.py` (new, under 400 lines),
    module docstring
    `"""Reference gate: every reference entry's sites cite its key, and every cited key has an entry."""`.
  - Each `src/` file holding an `Implemented in:` site: one citation line
    per technique in that site's docstring, nothing else.
  - `specs/001-port/p6-run-log.md`.
- Leave alone: every other line of `src/**`; `references.md` except an
  `Implemented in:` path P6.4 finds wrong (fix it there and log it); the
  other architecture tests; `exemptions/`.
- The test, written first and seen red for the right reason (no citation
  lines yet), then green:
  - Pure helpers: `entries(text) -> dict[str, list[str]]` parses
    `references.md` (heading key to its `Implemented in:` paths, `none`
    giving `[]`); `cited_keys(tree) -> dict[str, list[str]]` maps each
    qualified name under `pyntpot` to the keys its docstring cites, read
    with `ast.get_docstring` and the regex
    ``^Source: `([a-z][a-z0-9-]*)` in docs/explanation/references\.md\.$``
    (multiline). Resolve a dotted path by the longest module prefix that
    is a file under `src/`, then walk class and function names.
  - `test_every_site_cites_its_key`: every path in every entry resolves,
    and its docstring cites that key.
  - `test_every_cited_key_has_an_entry_listing_the_site`: every citation in
    `src/` names an entry, and that entry lists the citing site. Together
    the two make the mapping exact both ways.
  - `test_entries_parses_a_two_entry_file` and
    `test_cited_keys_reads_a_citation_line`: the helpers on literal text, so
    the gate cannot pass by parsing nothing.
  - One-line docstrings saying what each proves; no mocks; no fixtures
    beyond `tmp_path` if needed; `support.REPO_ROOT` for paths.
- Citation lines go where the reference format says. A line that would
  push a file over 400 lines cannot happen at P6.0's sizes (the fullest
  file has nine lines free); if drift makes it so, the line-budget rule
  applies and the slice stops that file only, filing it.
- This test is a new gate: ADR 0021 (D24, written at P7.3 by the ADR
  table) records it; P6.4 writes no ADR.
- Hand-off: citation lines added per file, the red run's failure message,
  the green run.
- Gate: `python3 -I "$SCRATCH/ast_neutral.py" <P6.3 commit>`, then G-here
  plus G-self.
- Commit: `Cite each technique's reference key in its docstring`

#### P6.5a to P6.5e Docstring audit, then prose, one session per group

Implements D25, both passes over `src/`; one slice per group below, each a
fresh session. **Group rule:** one subpackage is one session when it is at
most 5,000 lines (`ink` 3,905, `letters` 1,722). `maps` is 13,748 lines, so
it splits by responsibility into groups of at most 5,000 lines, fixed here
by path so no session re-decides them (paths under `src/pyntpot/`, counts at
`1154129`):

| Slice | Group | Files | Lines |
|---|---|---|---|
| P6.5a | `ink` | `ink/**` | 3,905 |
| P6.5b | `letters` | `letters/**/*.py` | 1,722 |
| P6.5c | `maps` façade, data and furniture | `__init__.py`; `maps/{__init__,pipeline,compose,cli,track,annotations,attribution,credit,card,card_geometry,projection,cache,plates,basemap,style,style_groups,lettering_furniture,lettering_marks,lettering_window}.py`; `maps/providers/**`; `maps/candidates/**` | 4,461 |
| P6.5d | `maps` geometry and painter | `maps/{basemap_strokes,contours,cover,generalise,layers,masks,osm,osm_elements,relief,relief_layers,relief_strokes,rings,rivers,strands,svg_path,track_index}.py`; `maps/painter/**` | 4,574 |
| P6.5e | `maps` lettering | `maps/lettering/**` | 4,765 |

A `maps` module created after `1154129` joins the group of the module it
was split from. P6.5c holds the façade, so the public API of `maps` and of
`pyntpot` is audited in the first `maps` session.

Every one of these slices:

- Predecessor: the slice before it in the order. Skills: read
  `docstrings/SKILL.md` and its `reference/rubric.md` and
  `reference/conventions.md`, then `ai-jargon-audit/SKILL.md` and
  `emdash-audit/SKILL.md` (paths per the tool facts). The repo convention
  is Google (`[tool.ruff.lint.pydocstyle] convention = "google"`).
- Owner files: the group's files (docstrings and `#` comments only),
  `GLOSSARY.md` (only a row whose `Today`/dotted name the audit finds
  wrong), `specs/001-port/p6-run-log.md`, `docs/issues/*.md` (new files
  only).
- Leave alone: every executable line; every citation line (P6.4's test
  fails if one goes); the theme TOML and the font; `tests/**`; every file
  outside the group.
- Pass 1, docstrings, in the public-API-first order: read each
  implementation, then fix the docstring for accuracy (it says what the
  code does now, per the behaviour-wins rule), shape (Google sections;
  `Args:` for every parameter of a public function and of a private one
  with three or more parameters; `Returns:` unless it returns `None`;
  `Raises:` only for what the body raises), and the house contract (module
  docstring: purpose, key types, non-goals, invariants, as capability
  facts). Add the missing docstrings (nine at P6.0 across the tree).
  It adds no caller obligations and no narration of how the code came to
  be.
- Pass 2, prose, over the same files' docstrings and comments: run
  `detect_ai_jargon.py` and fix each finding by rewording, then the
  semantic read the skill describes; British English; then
  `strip_emdashes.py` (expect nothing: the tree has no dashes). Terms come
  from `GLOSSARY.md`, one name a concept: a synonym is replaced by the
  glossary term.
- Triage and file by the fix-now rule; line-adding fixes by the line-budget
  rule.
- Hand-off: docstrings changed and added (public, private), comments
  changed, findings fixed and filed, the time at which the public API was
  done, each gate stage's wall time.
- Gate: `python3 -I "$SCRATCH/ast_neutral.py" <starting commit>`, then
  G-here plus G-self, then
  `python3 -I <dir>/ai-jargon-audit/detect_ai_jargon.py <group files>`
  reports 0 to rewrite, and `! grep -rn -e '—' -e '–' <group files>` exits 0 (literal
  characters: `grep -P '\x{2014}'` fails here because `LANG` is unset).
- Commits: P6.5a `Audit the ink docstrings and comments`; P6.5b `Audit the
  letters docstrings and comments`; P6.5c `Audit the maps facade and data
  docstrings and comments`; P6.5d `Audit the maps geometry and painter
  docstrings and comments`; P6.5e `Audit the maps lettering docstrings and
  comments`.

#### P6.6 Prose audit of the docs; the phase gate

- Implements D25's prose pass over the human-facing docs; predecessor
  P6.5e. Load `write-docs`, `ai-jargon-audit` and `emdash-audit`.
- Owner files: `README.md`, `GLOSSARY.md`, `CHANGELOG.md`,
  `CONTRIBUTING.md`, `docs/README.md`, `docs/architecture.md`,
  `docs/explanation/**` (including `references.md`: wording of the intro and
  `Note:` lines only, never a source's metadata or a key),
  `docs/runbooks/**`, `specs/001-port/p6-run-log.md`, `docs/issues/*.md`
  (new files only).
- Leave alone: the files the dash-audit rule excludes (`CLAUDE.md`,
  `BOUNDARIES.md`, `specs/**`, `.claude/**`, `docs/decisions/**`,
  `docs/issues/**` existing files, `tests/**`) and all of `src/`.
- Steps: per file, `detect_ai_jargon.py`, then the semantic read, then
  British English, then `strip_emdashes.py` (the one known dash is in
  `docs/runbooks/update-dependencies.md`). Content changes beyond wording
  (a wrong command, a stale fact) follow the behaviour-wins rule: correct
  the text to what the repo does, and file anything that needs code. The
  `CHANGELOG.md` gains no entry (P7 writes 0.1.0).
- **The phase gate**, run in order, every output pasted into the run log:
  1. `python3 -I "$SCRATCH/ast_neutral.py" <P6.0 commit>`: the whole branch
     changed no code.
  2. G-here plus G-self (baseline on this slice's starting commit, as
     every slice; the chain of per-slice G-self runs and step 1 together
     cover the branch).
  3. The P6.3 mechanical checks (inventory keys equal entry keys; every
     design-sources URL present; no unchecked canonical line).
  4. `uv run pytest tests/architecture/test_reference_keys.py -v`: every
     implementing docstring names its key and every key cited has an entry.
  5. `! grep -rn -e '—' -e '–' README.md GLOSSARY.md CHANGELOG.md CONTRIBUTING.md docs/README.md docs/architecture.md docs/explanation docs/runbooks src/pyntpot`
     exits 0.
- Hand-off: findings fixed and filed, the gate outputs, total P6 wall time
  from the log. The orchestrating session then opens the PR from
  `p6-docs`.
- Commit: `Audit the prose of the docs`

Gate for P6: full gate green, parity exact (G-here's byte-exact golden run
plus G-self), the whole branch AST-neutral, `references.md` has an entry for
every inventory item (P6.3 check), and every implementing docstring names
its key (`test_reference_keys.py`).

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

**Precondition for the whole phase.** P4.20, P7.4 and P8 are done and ticked,
and the maintainer has confirmed the release (P7.4 already requires that
confirmation). The order is P9.1, P9.2, P9.3, P9.4. P9.1 and P9.2 both edit
`tests/architecture/_text_scan.py`, `tests/conftest.py` and `BOUNDARIES.md`,
so they never run in parallel; P9.3 and P9.4 touch disjoint files and may run
in parallel with each other after P9.2.

**ADR numbers.** Fixed by the table under "P3 and P4: how to run a slice":
P9.1 writes 0022 and P9.2 writes 0023 (0003 to 0021 belong to P3, P4, P5.2,
P5.3 and P7.3). Before writing, `ls docs/decisions` must show the number
free; if it is taken, stop and report.

#### P9.1 Retire the banned-term test

- Implements the maintainer's decision (2026-10-04) to retire the
  banned-term test after the port. ADR 0022 supersedes **only the
  enforcement clause** of D16 (the banned-term test and its
  `personal_terms_file` option) for the post-port tree. D16's rule, that no
  personal content crosses over, still stands, and so do its other
  mechanisms: the D10 coordinate allowlist test stays, and the P2 manual
  pass and the pre-publication history scan are done. Predecessors P7.4 and
  P8.
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
  caller), `BOUNDARIES.md` (the "No personal content" bullet keeps the
  rule and names the coordinate allowlist as its standing test),
  `specs/001-port/spec.md` (append to the end of the D16 row only:
  ` For the post-port tree the banned-term test is superseded by ADR 0022; the rule stands.`;
  no other word of the row or the table changes), create
  `docs/decisions/0022-retire-banned-term-test.md`. Leave alone:
  `tests/architecture/test_coordinates.py` (D10 allowlist, stays),
  `CLAUDE.md`, `CONTRIBUTING.md`, `docs/architecture.md` (none mentions the
  test or the option; confirm with the grep below), ADR 0002 (append-only; its
  sentence listing "the banned-term scan" stays true as history and the new
  ADR amends it), and plan.md P0 to P8 text.
- ADR 0022: `# 0022 — Retire the banned-term test`, `Status: accepted`,
  `## Context` (D16 asked for a banned-term test, a manual pass and a history
  scan while the port carried personal content; the list is personal and never
  in the repository, so public CI always skipped the test; the maintainer
  decided on 2026-10-04 to retire the test once the port is published),
  `## Decision` (this ADR supersedes D16's enforcement clause for the
  banned-term test, for the post-port tree only; D16's rule that no personal
  content crosses over is unchanged and still binds every contribution;
  delete the test and the `personal_terms_file` option; the list outside the
  repository stays the maintainer's to keep or delete; the D10 coordinate
  allowlist remains as the standing automated guard), `## Consequences` (a
  new contribution is not scanned for terms; review against D16's rule and
  the coordinate test carry that; G-here no longer reports a skip; the
  amendment to ADR 0002's list of scans is stated).
  Heading shape as `0002-hexagonal-layers.md`.
- Tests: no new test. The safety proof is that the suite still collects under
  `--strict-config` with the option gone, `uv run pytest
  tests/architecture` passes with no skips, and
  `grep -rnE "personal_terms|test_no_personal_content|banned_terms\.txt" --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.ruff_cache --exclude-dir=.pytest_cache --exclude-dir=__pycache__ .`
  matches only `spec.md` (the D16 row; Verification step 3 says
  "banned-term" and does not match), `plan.md`, `tasks.md` and
  ADR 0022 (ADR 0002 says "banned-term scan" and does not match).
- Gate: G-here.
- Commit: `Retire the banned-term test and its pytest option`

#### P9.2 Retire the exemptions mechanism

- Implements the end state of D5's interim relaxation; predecessor P9.1
  (shared files), which itself follows P4.19.
- Why it is dead. P4.19 deletes `_port`, removes its per-file-ignores and `ty`
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
  `docs/decisions/0023-retire-exemptions.md` (Status accepted; context: the
  mechanism existed for `_port` only; decision: no relaxation mechanism
  remains, a future over-budget file is split, not listed; consequences: the
  budget and purity tests have no escape hatch). Leave alone: the 400-line
  limit, the clock and random bans, `test_docstring_conventions.py`,
  `test_testing_discipline.py` and every other gate.
- Tests: `uv run pytest tests/architecture` passes; `grep -rn "exemption"
  --include=*.py --include=*.md --include=*.toml --exclude-dir=.git
  --exclude-dir=.venv .` finds only files under `docs/decisions/` (ADR 0002,
  append-only, and ADR 0023), `spec.md`, `plan.md` and `tasks.md`;
  `test_no_oversized_files` and the purity tests still fail on a
  scratch 401-line file and a scratch `time.time()` call (run by hand, not
  committed), showing the gates were not weakened.
- Gate: G-here.
- Commit: `Retire the exemptions mechanism now that the port is split`

#### P9.3 Drop the historical golden script and the last `ty` exclude

- Implements nothing new; predecessors P9.2 and P8.
- Why it is dead. `tests/golden/make_golden_old.py` imports the pre-port
  package from the originating project, is documented as historical, and is
  the only entry left in `[tool.ty.src] exclude` after P4.15, P4.18 and P4.19
  remove the ported-test and `_port` entries. The goldens were regenerated once in
  P3.15 by `tests/golden/make_golden.py` and ADR 0006 records the old and new
  hashes, and P8 has reproduced the recorded render through the public API,
  so the script's provenance role is finished.
- Owner files: delete `tests/golden/make_golden_old.py`; edit `pyproject.toml`
  (remove `exclude` and its two comment lines from `[tool.ty.src]`, so `ty`
  checks all of `src` and `tests`; remove any `_port` per-file-ignore, ty
  exclude or comment P4.15, P4.18 and P4.19 left behind, including the "Interim"
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
