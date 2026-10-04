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
