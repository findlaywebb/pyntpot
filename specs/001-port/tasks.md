# 001-port: tasks

Sequence for `plan.md`. Tick a line when its gate is green and committed.

## P0. Scaffold

- [x] P0.1 Run the template scaffold script
- [x] P0.2 Delete the web-app shape
- [x] P0.3 Collapse the workspace to one package and fix every path
- [x] P0.4 Runtime and dev dependencies, with the D22 pins
- [x] P0.5 Import-linter: one forbidden contract, no layers yet
- [x] P0.6 Architecture tests and the exemptions mechanism
- [x] P0.7 Public-library files: LICENSE, LICENSE-FONT, CHANGELOG, CONTRIBUTING, SECURITY, GLOSSARY, dependabot, publish workflow
- [x] P0.8 CI: `checks`, `prerelease` and `golden` workflows
- [x] P0.9 Project metadata, pytest markers and mutmut settings
- [x] P0.10 Initial commit, no remote

## P1. Port with parity proof

- [x] P1.1 Dump the resolved default style from the old code
- [x] P1.2 Copy the modules into `_port` and format them
- [x] P1.3 Apply the listed mechanical edits and populate the exemptions
- [x] P1.4 Port the unit tests onto the Lynmouth geography
- [x] P1.5 Build the Lynmouth fixture from the old code
- [x] P1.6 Produce the golden plates with the old code
- [x] P1.7 Write the parity test, exact and tolerance modes
- [x] P1.8 Commit the port with its parity fixture

## P2. Scrub personal content and narration

- [x] P2.1 Turn the personal-content and coordinate gates on
- [x] P2.2 Keep the rule, drop the anecdote, per file
- [x] P2.3 Manual pass over capitalised and quoted strings
- [x] P2.4 Replace `ALPHABET_LINES` with same-length neutral lines
- [x] P2.5 Same-length test strings, changed expectations logged
- [x] P2.6 Leave `label_font` untouched until P3
- [x] P2.7 Exact golden run after each session
- [x] P2.8 Write the scrubbed `specs/001-port/` copy
- [x] P2.8a Review fix round: findings from the leak and rule-loss review cleared
- [x] P2.8b Move the private-terms list outside the repo; the test skips when it is absent
- [x] P2.8c Apply the naming convention: real UK countryside names, invented names out
- [x] P2.9 Tree scan, orphan commit, public repo, remote history scan

## Handoff (2026-10-03)

P0 to P2 are complete and published. The next step is **P3.0**: fatten P3
and P4 in `plan.md` into slices a sub-agent can execute, following
`architecture.md` (A1 to A8, all accepted under D27) and the sequencing
there: A4 first, one golden regeneration, A2 before the split. Run the
plan-reviewer agent on the fattened section before any code moves. Today
the committed goldens are exact only on the maintainer's machine and this
environment runs them in tolerance mode; the one regeneration (P3.15) is
made in this environment, after which G-here runs them byte-exact here, CI
stays in tolerance mode, and the maintainer's exact run is a follow-up check
recorded in ADR 0006, not a re-baseline.

## P3. Façade, providers, policy, style, CLI

- [x] P3.0a Architecture review pass: candidates recorded in `architecture.md`
- [x] P3.0 Fatten P3 and P4 into slices from `architecture.md`; plan-reviewer pass
- [x] P3.1 Golden harness (`make_golden.py` with provenance, `--golden-dir`), package skeletons, `Credit`, the import-rule test
- [x] P3.2 One card frame; ADR 0003 (A4)
- [x] P3.3 One polyline module, moves only; `Pt` in `ink.polyline` (A5)
- [x] P3.4 Typed `Basemap` with `Layers`, `Projection` (A4)
- [x] P3.5 Typed `Plates` and `Manifest` (A4)
- [x] P3.6 `Track` with a GPX reader and `BoundingBox` (parallel line 2)
- [x] P3.7 `Features`, `Elevation`, `ProviderBudgetExceededError`, fixture providers with the shipped ids, the local test server; ADR 0004 (parallel line 2)
- [x] P3.8 `OverpassFeatures` with a query budget and copied query templates (parallel with P3.9, P3.10)
- [x] P3.9 `OpenTopoData` with a call budget (parallel with P3.8, P3.10)
- [x] P3.10 Fetch `Cache` keyed by box, margin and providers; `ensure` fetches features, landcover, elevation in that order, each written before the next (parallel with P3.8, P3.9)
- [x] P3.11a Style groups from the field-to-group table pinned in the plan (base or lettering by reader, layer, section; `CONSUMER_ONLY` for `PaintStyle` only), effective basemap options (all 27), fixed route ink; ADR 0005 (parallel line 3, A6)
- [x] P3.11b `Style` model, the TOML theme, pinned digests, unwired (parallel line 3, A6)
- [x] P3.12 Wire the style, final hash form; opens the regeneration window, step 1 byte-identical (A6, A7)
- [x] P3.13 Lettering reads the basemap, final manifest keys (step 2, byte-identical); drop the seam's one-decimal round trip, `paint.parse_d` and `route0`, keeping `geo.parse_path` for `basemap()`'s output (step 3, bounded) (A4, window)
- [x] P3.14 Merge the polyline duplicates that compute the same thing, one gated step each; keep the rest apart, recorded (A5, window)
- [x] P3.15 Regenerate the goldens once; ADR 0006; push the window to `main` (closes the window)
- [x] P3.16 Façade `fetch` (takes the style, raises `FetchError`, tested through a hand-written `_VanishingElevation`) and `paint`; `Plates.route_px` and `strands` (the separated route, default `()`); `paint_fixture` on `fetch` and `paint`; `paint_activity` deleted; fixture payloads renamed to cache keys
- [ ] P3.17 Façade `letter` and raster `compose` on `Plates.strands`; `mapcard.compose` deleted; `paint_fixture` on the four stages; `Annotations`; lettering shims, `alphabet_sheet` and `sport_from_gpx` deleted; tests use `flat_measure` (A3 shape)
- [ ] P3.18 Attribution drawn by `compose` from `Basemap.credits`
- [ ] P3.19 `pyntpot map` CLI
- [ ] P3.20 Top-level exports and `__version__`; ADR 0007
- [ ] P3.21 Golden harness imports only the public names; no `_port` import under `tests/golden`

## P4. Split and layer

Renumbered after the plan review of `294cc69`; plan.md has the old-to-new table. After the second review (`33f12be`) P4.16 and P4.17 swapped content (spans before placement, bottom-up) and P3.11 split into P3.11a and P3.11b. After the third review (`f63bb61`) slice IDs are unchanged; `paint_activity`'s deletion moved from P3.21 to P3.16. After the fourth review (`7b55c7d`) slice IDs are unchanged.

- [ ] P4.1 Design the hand's setting; ADR 0008 (A2)
- [ ] P4.2 Ink engine part 1: noise, sheet, raster, io, wash, pigment (A1)
- [ ] P4.3 Ink engine part 2: brush with the brush-sheet tables, tip, stamp, pad (A1)
- [ ] P4.4 Split the outline font into `letters/{font,skeleton,trace}`
- [ ] P4.5 The hand writes settings; map furniture moves to maps (A2)
- [ ] P4.6 The nib plate moves into letters (A2); `NibSurface` carries the render `scale`, `plate` builds its own Sheet, `maps.plates.dark_array` builds the dark field for both callers
- [ ] P4.7 One cache for fetches and plates (A7)
- [ ] P4.8 Plate painter in maps part 1: job, brushes, water, cover, wood (A1)
- [ ] P4.9 Plate painter in maps part 2: relief, fluid, pen, ribbon, paper (A1)
- [ ] P4.10 Style groups part 1: basemap readers; `GeoOptions` deleted (A6)
- [ ] P4.11 Style groups part 2: lettering readers; `PaintStyle` and `_port/paint.py` deleted (A6)
- [ ] P4.12 Design the candidates facility; ADR 0009 (A8)
- [ ] P4.13 Candidates facility in `maps/candidates/` (A8); `candidates/__init__.py` docstring and empty `__all__` only
- [ ] P4.14 Split geo part 1: rings, SVG paths, track index, relief, generalisation, rivers
- [ ] P4.15 Split geo part 2: OSM layers, cover, assembly; `landmark_export` into `maps/candidates/export.py`; delete `geo.py`
- [ ] P4.16 Split labels part 1: label types and spans
- [ ] P4.17 Split labels part 2: placement
- [ ] P4.18 Split labels part 3: picks, compose, strands; delete the port modules (A3)
- [ ] P4.19 Layers and forbidden contracts; empty exemptions; delete `_port`; ADR 0010
- [ ] P4.20 Relax the D22 pins to floors

## P5. Property tests, coverage, mutation, benchmarks

- [ ] P5.1 Property tests
- [ ] P5.2 Coverage baseline and ADR 0011
- [ ] P5.3 mutmut PR and nightly jobs, threshold ADR 0012
- [ ] P5.4 Benchmarks and CodSpeed workflow

## P6. Docstrings, prose and references

- [ ] P6.1 References inventory
- [ ] P6.2 Recover design-input sources
- [ ] P6.3 Verify sources and write `references.md`
- [ ] P6.4 Docstring audit, one session per subpackage
- [ ] P6.5 Prose audit

## P7. Docs and first release

- [ ] P7.1 README with gallery images
- [ ] P7.2 Tutorial, how-to guides, reference and explanation pages
- [ ] P7.3 ADRs 0013 to 0021 for the settled decisions
- [ ] P7.4 Changelog 0.1.0, trusted publisher, confirm, tag and publish

## P8. Upstream migration

- [ ] P8.1 The upstream consumer migrates to the public API, with the recorded render hash reproduced first

## P9. Post-port cleanup

- [ ] P9.1 Retire the banned-term test and the `personal_terms_file` option; ADR 0022 supersedes D16's enforcement clause for the post-port tree (the rule stands)
- [ ] P9.2 Retire the exemptions mechanism; ADR 0023
- [ ] P9.3 Delete `make_golden_old.py` and the last `ty` exclude
- [ ] P9.4 Delete `design-sources.md` once `references.md` covers it
