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
src/pyntpot/_port/paint.py        [-> ink/{sheet,noise,brush,stamp,wash,pigment,raster,io}.py + maps/{card,ribbon,plates}.py]
src/pyntpot/_port/outlinefont.py  [-> letters/{font,trace}.py]
src/pyntpot/_port/labels.py       [-> letters/hand.py + maps/{placement,landmarks,spans}.py]
src/pyntpot/_port/geo.py          [-> maps/{projection,geometry,providers/*,cache,layers,landmarks}.py]
src/pyntpot/_port/mapcard.py      [-> maps/compose.py]
src/pyntpot/_port/card.py         [-> maps/card.py]   (_Card, separate_strands and helpers)
src/pyntpot/_port/style.py        [-> maps/style.py]  (RouteInk + constants only)
src/pyntpot/_port/fonts/PatrickHand-Regular.ttf
src/pyntpot/_port/themes/default.json   (resolved default style, D23)
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

### P3. Façade, providers, policy, style, CLI

Preceded by D18: run the architecture review pass on `src/pyntpot/_port`,
work its candidates through, record ADRs. Its accepted candidates are
folded into the P3 and P4 task lists before P3 starts.

- `maps/track.py`: `Track(lat, lng, ele=None, time=None)` pydantic model
  (`time` as seconds from start, read from `<time>` when present, D21),
  `from_gpx(path)` via `xml.etree` reading `trkpt` only,
  `bounding_box(margin_m)`.
- `maps/providers/base.py`: `Features` and `Elevation` protocols;
  `Credit(text, url)` from every provider.
- `maps/providers/overpass.py`: `OverpassFeatures(contact, endpoints=DEFAULT)`,
  `DEFAULT = ("https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter")`.
  Sequential requests, `[timeout:]` and `[maxsize:]` from the box, 30 s
  back-off on 429, no blanket `except Exception`. User-Agent
  `pyntpot/<version> (<contact>)`.
- `maps/providers/opentopodata.py`: `OpenTopoData(contact, endpoint=PUBLIC, dataset="srtm30m")`,
  100 points per call, 1 call per second, `budget=1000` per process with
  `ElevationBudgetExceeded`.
- `maps/cache.py`: `Cache(dir)` keyed by `sha256(bbox, margin, provider.id)[:16]`.
- `maps/style.py`: `Style` pydantic model grouping the resolved fields into
  `paper`, `wash`, `pen`, `route`, `lettering`, `basemap`, loaded from
  TOML; `themes/default.toml` replaces `default.json`. `label_font` becomes
  the vendored face only. `Style.digest()` will differ from the old
  digest: regenerate the golden plates once from the new code after the
  P2 parity run, record old and new hash in an ADR, and add the previous
  label font name to the banned list.
- Façade in `pyntpot/maps/__init__.py`:
  `fetch(track, cache, features, elevation, places=()) -> Basemap`
  (places enter here, as today at `geo.py:1912`),
  `paint(basemap, style, out_dir) -> Plates`,
  `letter(plates, basemap, annotations, style) -> Lettering`,
  `compose(plates, lettering, track, style, attribution=True) -> PIL.Image`.
  `Basemap` exposes `projection` and `layers`; `Plates` exposes
  `manifest`, `paths`, `hash`, `card`, `route_px`, `strands`;
  `Lettering` exposes `labels`, `spans`, `plate_path` (D21).
- `compose` draws "© OpenStreetMap contributors (openstreetmap.org/copyright)
  · elevation: NASA SRTM" bottom-right in the hand face when
  `attribution` is true.
- `maps/cli.py`: `pyntpot map TRACK.gpx -o OUT.png --cache DIR --contact STR [--style FILE] [--no-attribution]`.
- Top-level `pyntpot/__init__.py` exports the D6 names and `__version__`.
- Parity test moves to the façade with `attribution=False` and stays exact
  against the regenerated goldens.

Each bullet becomes a `tasks.md` item with its own test before P3 starts.

### P4. Split and layer

1. Split every file over 400 lines with a mechanical module-split pass into
   the target modules in the tree above, pure moves only, parity exact
   after each move. Same for `tests/unit/test_paint.py`. The `Hand`/`Label`
   coupling found by the plan review is the one non-mechanical step: `Hand`
   takes a plain `Mark` sequence; the map code builds marks from labels.
   Design it with the design-it-twice pattern and record an ADR.
2. Add the `maps -> letters -> ink` layers contract and the forbidden
   contract (`ink` and `letters` may not import `httpx` or `pydantic`).
3. Fix the nine `perf_counter` calls (inject a clock or drop manifest
   timings) and delete `from_style`. Empty `line_budget.txt`,
   `gates_off.txt` and the `_port` per-file ignores and ty exclude.
   Delete `_port`. Relax the D22 pins to floors in one commit with parity
   exact.

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
   backruns), brush and nib stroke models. Today none of these carries a
   citation; the five modules contain no paper, blog or DOI reference.
2. **Recover the design inputs.** The papers and blogs read while
   designing the map rules are not recorded in the source tree. Recover
   them from whatever record exists (see the open question in `spec.md`)
   and match them to the inventory.
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
