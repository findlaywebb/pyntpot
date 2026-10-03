# 001-port: extract the map painting engine into `pyntpot`

Status: stable, after two plan-review passes. Upstream source commit ecfa41d.

## Goal

Create a public MIT Python library, `pyntpot`, that paints hand-drawn
watercolour and pen-and-ink raster images: paper, washes, brushes, nibs,
pigment compositing and hand lettering, with route maps from vector
OpenStreetMap data and elevation as its first application.

The code comes out of the upstream training-analysis repo, from its report
package (`geo.py`, `paint.py`, `labels.py`, `outlinefont.py`, `mapcard.py`,
small parts of `charts.py` and `style.py`, and the vendored `fonts/`). The
upstream repo then depends on `pyntpot` and deletes those modules. The map
for a reference activity, rendered with the upstream default theme, must be
pixel-identical before and after the switchover, with attribution off.

Current behaviour: the engine lives in five 800 to 4500 line modules keyed
by an upstream activity identifier, with personal coordinates, place names
and training anecdotes in the defaults, fixtures, tests and comments, and
with no citations for the techniques it implements.

Desired: a versioned package with a small façade, policy-compliant data
providers, no personal data anywhere in the tree or the git history,
400-line modules, property tests, a mutation score, benchmarks, a docs tree
and a bibliography.

## Key decisions (settled, do not re-decide)

| # | Decision |
|---|---|
| D1 | Scope: the whole pipeline. Fetch, cache, layers, plates, lettering, composed PNG. The upstream SVG `journal_map`, its HTML page, `MapPicks`, its themes' CSS, its SVG label placer (`labels.py` 3571 to 3678) and its places file stay upstream. |
| D2 | Name `pyntpot` (reads "paint pot"; free on PyPI and GitHub on 2026-10-03). One distribution. Target subpackages `pyntpot.ink`, `pyntpot.letters`, `pyntpot.maps` with import-linter layers `maps -> letters -> ink`. **The layering is a P4 outcome.** P1 to P3 ship one private subpackage `pyntpot._port` with no layer contract. |
| D3 | Licence MIT (SPDX `license = "MIT"`, PEP 639 `license-files`). The vendored Patrick Hand face stays under SIL OFL 1.1 and is listed in `license-files`. |
| D4 | Python floor `>=3.13`. CI matrix 3.13, 3.14, plus a 3.15 pre-release job allowed to fail. Raising the floor is one later ADR. |
| D5 | Port strategy: move with `ruff format` applied and only the listed edits, prove parity with a golden-plate test, scrub, build the façade, then split. Lint, type and line-budget gates carry an explicit exemptions file for `_port` until P4 empties it. |
| D6 | Public API (P3): `Track`, `Basemap`, `Style`, `Plates`, `Lettering`, `Annotations`, functions `fetch`, `paint`, `letter`, `compose`; engine names `Sheet`, `Brush`, `Canvas` (today's `Plate`), `stamp`, `wash`, `composite`, `Hand`. Everything else is private. `Lettering` and the projection on `Basemap` exist because the upstream SVG page consumes them (D21). |
| D7 | Pydantic v2 is a runtime dependency, used only at the boundary: `Style` (from TOML), `Track`, `Annotations`. Internals stay numpy arrays and dataclasses. |
| D8 | Providers are protocols `Features` and `Elevation`. Shipped: `OverpassFeatures`, `OpenTopoData`. A contact string is a required constructor argument. Published limits are enforced by default. `compose` draws attribution unless `attribution=False`. |
| D9 | Cache keyed by a hash of bounding box, margin and provider id, never by activity ID. Cache directory is always an explicit argument; no cwd-relative module globals. |
| D10 | Fixture and test geography: Lynmouth, Devon (latitude 51.23, longitude -3.83, to two places). Every **synthetic** coordinate in `src/`, `tests/` and `docs/` lies inside the box 51.19 to 51.26 N, 3.80 to 3.88 W. A test enforces this as an allowlist. The three provider JSON files under `tests/fixtures/lynmouth/` and `tests/golden/lynmouth/plates.json` are exempt by name: Overpass returns full geometry for every way and relation touching the box, so those payloads span degrees. |
| D11 | The upstream repo consumes a git tag until the first PyPI release, then a PyPI pin. A path source is allowed only in an uncommitted local override. |
| D12 | Type gate `ty`. Lint `ruff` with the template's rule set. Hooks via `prek`. |
| D13 | Docs: README with a gallery and `docs/` in Diátaxis layout. No docs site at v0.1. |
| D14 | Process carried from the template: `specs/NNN-name/`, plan review before code, ADRs in `docs/decisions/`, keep-a-changelog, trusted publishing on tag `v*`. |
| D15 | No remote exists until P2.9. P0 to P2 are local commits only. At P2.9, after the scrub gate and the tree scan pass, the scrubbed tree is published as one orphan commit to a new public GitHub repo. The local working history is never pushed. |
| D16 | No personal content crosses over: no home coordinates, no personal place names, no activity identifiers, no training anecdotes, no attributions to a user request. Enforced by a banned-term test, the D10 coordinate allowlist test, a manual capitalised-string pass in P2, and a history scan before the repo goes public. The banned-term list is itself personal content and is never committed: it lives outside the repository at `~/personal/pyntpot-private/banned_terms.txt`, the test reads it from the path set by the `personal_terms_file` pytest ini option, and skips when the file is absent (public CI). |
| D17 | Quality tooling: `hypothesis` property tests, `mutmut` (changed functions on PR, full nightly, golden tests excluded), `pytest-benchmark` locally and `pytest-codspeed` in CI. |
| D18 | After the port and the scrub (end of P2), run the repo's architecture review pass over the ported code, before the mechanical split. Its output shapes P3 and P4. |
| D19 | CLI is argparse, stdlib only. One entry point `pyntpot`. |
| D20 | Build backend `uv_build`, static version, bumped with `uv version --bump`. |
| D21 | The upstream `charts.journal_map` keeps its own SVG pipeline and consumes public pipeline stages: `Basemap` (projection, layers), `Plates` (manifest, plate paths, card geometry, route pixels, strands, since these derive from the manifest and the route ink width), `Lettering` (placed labels, spans, label plate path). `Track` carries optional `time` (seconds from start) so time-stated spans still resolve. It never imports a private name. P8 enumerates the exact attributes from the call sites the plan review lists. Rejected: embedding the composed PNG in the page, because the page would lose its vector route marks. |
| D22 | Parity stack pin: `numpy==2.5.2`, `pillow==12.3.0`, `fonttools==4.63.0` from P1 to the end of P4, then relaxed to floors in one commit with the parity test still exact. |
| D23 | Style for P1 to P3 is the **resolved** default-theme style dumped from the old code (`PaintStyle`, `GeoOptions`, `RouteInk` per sport), not the theme JSON. No `ChartStyle` and no theme merge logic is ported. |
| D24 | Every technique the code implements cites its source: a `docs/explanation/references.md` bibliography with one entry per technique, and the implementing docstring names the entry's key. Sources are verified live, never from memory. Techniques whose design input was a paper or blog read during the original design get that source if it can be recovered, otherwise the canonical source for the technique. |
| D25 | Two quality passes run after P4 and before the docs: a docstring audit over every public and private docstring, then a prose audit over docstrings, comments, README and `docs/`. |
| D26 | Example and test place names are real UK countryside names spread across regions (Monmouth, Abergavenny, St Ives, the Lake District, the Peak District, the Yorkshire Dales, the Highlands, the Cairngorms), with a few landmark city names such as Regent's Park. Invented names are not used. Coordinates still follow D10. The convention is written in `CONTRIBUTING.md`. |
| D27 | Architecture round outcome, decided 2026-10-03: all eight candidates in `architecture.md` are accepted (A1 to A8). A7 brings the plate cache under D9. A8 keeps the candidate logic in scope, split out and generalised into a reusable `candidates` facility; the six zero-caller functions are deleted. |

Approaches rejected: painter-only extraction (leaves the policy problem
upstream and keeps the activity-ID cache); two distributions (doubles
release work for one user); rewrite from the digest (no safety net for 16k
lines of numeric code); layering from the first commit (the lazy import
graph is cyclic between what would be `ink`, `letters` and `maps`; the plan
review lists the sites).

## Vocabulary

Settle these in `GLOSSARY.md` during P0 and use them everywhere new. The
ported code keeps its old names until P4.

| Term | Meaning |
|---|---|
| sheet | The paper's noise fields, seeded. Today `paint.Sheet`. |
| canvas | A world-unit box and the pixel grid it paints to. Today `paint.Plate`. |
| plate | One painted raster layer written to disk: paper, wash, pen, labels. |
| plates | The set of plates plus its manifest for one render. Today `plates.json`. |
| brush | One mark-making tool. Today `paint.Brush`. |
| wash | A pigment field laid on the sheet. |
| hand | The lettering writer. Today `labels.Hand`. |
| trace | How a glyph becomes strokes: centreline or outline. Today `outlinefont.route`. |
| track | The GPS path being mapped. Today `lat, lng` lists. |
| route | The painted line of the track on the map. |
| basemap | The fetched and projected layers for a bounding box. |
| lettering | Placed labels and spans plus their painted plate. |
| annotations | Caller-supplied landmarks, roads, places and spans. Today `MapPicks`. |
| span | A stretch of the route with a name and an intent. |

## Out of scope

- Any change to how the upstream HTML page or SVG `journal_map` looks.
- New painting features, layers or themes. Parity first.
- A docs site, a conda package, Windows support (mutmut needs fork; the
  library is pure Python and should run there, untested).
- Replacing OpenTopoData with a DEM reader. The `Elevation` protocol makes
  that a later feature.
- Performance work. P5 measures; it does not optimise.
- Any upstream change beyond the switchover edits in P8.

## Verification (end-to-end)

1. In the repo: `uv run prek run --all-files && uv run pytest` green on 3.13
   and 3.14; `uv run pytest -m golden` exact on the machine that made the
   goldens and within tolerance on both CI runners.
2. Offline: `uv run pyntpot map tests/fixtures/lynmouth/track.gpx --cache tests/fixtures/lynmouth --contact test --no-attribution -o out.png`
   succeeds with the network disabled and matches
   `tests/golden/lynmouth/map.png` within the CI tolerance.
3. The banned-term, coordinate and remote-history scans return nothing, and
   the local working history was never pushed (`git branch -r` shows no
   trace).
4. `docs/explanation/references.md` covers every item in the P6 inventory,
   and every cited docstring names an entry that exists.
5. In the upstream repo after P8: the recorded PNG hash reproduces, its
   test suite is green, and no import of the old paint module remains.
6. `uv build` produces a wheel that installs into a clean venv and
   `python -c "import pyntpot; pyntpot.Sheet(64, 64, 8.0)"` runs.

## Open questions

- Coverage target: the template demands 100 percent branch on core. P5
  sets a measured baseline and ratchets. Confirm that is acceptable rather
  than blocking the first release on 100 percent.
- The OpenTopoData daily budget is enforced per process only. A
  per-cache-dir counter adds state. Default is per process.
- Design-input sources (P6.2): the papers and blogs read while designing
  the wash, brush, lettering and label rules are not recorded in the
  source tree. Recover them where possible; otherwise each entry cites the
  canonical source only.
