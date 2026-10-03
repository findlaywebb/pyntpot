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
plan-reviewer agent on the fattened section before any code moves. Golden
parity is exact only on the maintainer's machine; CI runs tolerance mode.

## P3. Façade, providers, policy, style, CLI

- [x] P3.0a Architecture review pass: candidates recorded in `architecture.md`
- [ ] P3.0 Fatten P3 and P4 into slices from `architecture.md`; plan-reviewer pass
- [ ] P3.1 Golden harness (`make_golden.py`, `--golden-dir`) and the maps package skeleton
- [ ] P3.2 One card frame; ADR 0003 (A4)
- [ ] P3.3 One polyline module, moves only (A5)
- [ ] P3.4 Typed `Basemap` and `Projection` (A4)
- [ ] P3.5 Typed `Plates` and `Manifest` (A4)
- [ ] P3.6 `Track` with a GPX reader and `BoundingBox` (parallel line 2)
- [ ] P3.7 `Features`, `Elevation`, `Credit`; ADR 0004 (parallel line 2)
- [ ] P3.8 `OverpassFeatures` (parallel with P3.9, P3.10)
- [ ] P3.9 `OpenTopoData` with a call budget (parallel with P3.8, P3.10)
- [ ] P3.10 Fetch `Cache` keyed by box, margin and providers (parallel with P3.8, P3.9)
- [ ] P3.11 Style groups by layer and the TOML theme, unwired; ADR 0005 (parallel line 3, A6)
- [ ] P3.12 Wire the style, hash the typed inputs; opens the regeneration window (A6, A7)
- [ ] P3.13 Drop the one-decimal round trip, the second parser and `route0` (A4, window)
- [ ] P3.14 Merge the polyline duplicates (A5, window)
- [ ] P3.15 Regenerate the goldens once; ADR 0006 (closes the window)
- [ ] P3.16 Façade `fetch` and `paint`; fixture payloads renamed to cache keys
- [ ] P3.17 Façade `letter` and `compose`; lettering shims deleted (A3 shape)
- [ ] P3.18 Attribution drawn by `compose`
- [ ] P3.19 `pyntpot map` CLI
- [ ] P3.20 Top-level exports and `__version__`; ADR 0007
- [ ] P3.21 Golden parity driven through the façade

## P4. Split and layer

- [ ] P4.1 Design the hand's setting; ADR 0008 (A2)
- [ ] P4.2 The hand writes settings; map furniture moves to maps (A2)
- [ ] P4.3 The nib plate moves into letters (A2)
- [ ] P4.4 Split the outline font into `letters/{font,skeleton,trace}`
- [ ] P4.5 Ink engine part 1: noise, sheet, raster, io, wash, pigment (A1)
- [ ] P4.6 Ink engine part 2: brush, tip, stamp, pad (A1)
- [ ] P4.7 Plate painter in maps; the nine clock reads and manifest timings go (A1)
- [ ] P4.8 Style groups replace `PaintStyle`; `from_style` deleted (A6)
- [ ] P4.9 Design the candidates facility; ADR 0009; delete dead code (A8)
- [ ] P4.10 Candidates facility in `maps/candidates/` (A8)
- [ ] P4.11 Split geo part 1: relief, generalisation, rivers
- [ ] P4.12 Split geo part 2: OSM layers, cover, assembly; delete `geo.py`
- [ ] P4.13 One cache for fetches and plates (A7)
- [ ] P4.14 Split labels part 1: placement
- [ ] P4.15 Split labels part 2: spans
- [ ] P4.16 Split labels part 3: picks, compose, strands; delete the port modules (A3)
- [ ] P4.17 Layers and forbidden contracts; empty exemptions; delete `_port`; ADR 0010
- [ ] P4.18 Relax the D22 pins to floors

## P5. Property tests, coverage, mutation, benchmarks

- [ ] P5.1 Property tests
- [ ] P5.2 Coverage baseline and ADR
- [ ] P5.3 mutmut PR and nightly jobs, threshold ADR
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
- [ ] P7.3 ADRs for the settled decisions
- [ ] P7.4 Changelog 0.1.0, trusted publisher, confirm, tag and publish

## P8. Upstream migration

- [ ] P8.1 The upstream consumer migrates to the public API, with the recorded render hash reproduced first

## P9. Post-port cleanup

- [ ] P9.1 Retire the banned-term test and the `personal_terms_file` option; ADR
- [ ] P9.2 Retire the exemptions mechanism; ADR
- [ ] P9.3 Delete `make_golden_old.py` and the last `ty` exclude
- [ ] P9.4 Delete `design-sources.md` once `references.md` covers it
