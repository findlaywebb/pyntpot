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
- [x] P3.17 Façade `letter` and raster `compose` on `Plates.strands`; `mapcard.compose` deleted; `paint_fixture` on the four stages; `Annotations`; lettering shims, `alphabet_sheet` and `sport_from_gpx` deleted; tests use `flat_measure` (A3 shape)
- [x] P3.18 Attribution drawn by `compose` from `Basemap.credits`
- [x] P3.19 `pyntpot map` CLI
- [x] P3.20 Top-level exports and `__version__`; ADR 0007
- [x] P3.21 Golden harness imports only the public names; no `_port` import under `tests/golden`

## P4. Split and layer

Renumbered after the plan review of `294cc69`; plan.md has the old-to-new table. After the second review (`33f12be`) P4.16 and P4.17 swapped content (spans before placement, bottom-up) and P3.11 split into P3.11a and P3.11b. After the third review (`f63bb61`) slice IDs are unchanged; `paint_activity`'s deletion moved from P3.21 to P3.16. After the fourth review (`7b55c7d`) slice IDs are unchanged.

- [x] P4.1 Design the hand's setting; ADR 0008 (A2)
- [x] P4.2 Ink engine part 1: noise, sheet, raster, io, wash, pigment (A1)
- [x] P4.3 Ink engine part 2: brush with the brush-sheet tables, tip, stamp, pad (A1)
- [x] P4.4 Split the outline font into `letters/{font,skeleton,trace}`
- [x] P4.5 The hand writes settings; map furniture moves to maps (A2)
- [x] P4.6 The nib plate moves into letters (A2); `NibSurface` carries the render `scale`, `plate` builds its own Sheet, `maps.plates.dark_array` builds the dark field for both callers
- [x] P4.7 One cache for fetches and plates (A7)
- [x] P4.8 Plate painter in maps part 1: job, brushes, water, cover, wood (A1)
- [x] P4.9 Plate painter in maps part 2: relief, fluid, pen, ribbon, paper (A1)
- [x] P4.10 Style groups part 1: basemap readers; `GeoOptions` deleted (A6)
- [x] P4.11 Style groups part 2: lettering readers; `PaintStyle` and `_port/paint.py` deleted (A6)
- [x] P4.12 Design the candidates facility; ADR 0009 (A8)
- [x] P4.13 Candidates facility in `maps/candidates/` (A8); `candidates/__init__.py` docstring and empty `__all__` only
- [x] P4.14 Split geo part 1: rings, SVG paths, track index, relief, generalisation, rivers
- [x] P4.15 Split geo part 2: OSM layers, cover, assembly; `landmark_export` into `maps/candidates/export.py`; delete `geo.py`
- [x] P4.16 Split labels part 1: label types and spans
- [x] P4.17 Split labels part 2: placement
- [x] P4.18 Split labels part 3: picks, compose, strands; delete the port modules (A3)
- [x] P4.19 Layers and forbidden contracts; empty exemptions; delete `_port`; ADR 0010
- [x] P4.20 Relax the D22 pins to floors

## P5. Property tests, coverage, mutation, benchmarks

Order: P5.0, P5.1, P5.2, P5.3a, P5.4, P5.3c on branch `p5-quality` (one PR). P5.3b (threshold from the first nightly) is superseded by P5.3c: mutation testing is manual and advisory (maintainer, 2026-10-07). Every slice records its numbers and choices in `p5-run-log.md`.

- [x] P5.0 Fatten P5 into slices; plan-reviewer pass; spec coverage question resolved
- [x] P5.1 Property tests; times and any `max_examples` cut in the run log
- [x] P5.2 Coverage baseline on 3.13 and 3.14 (lower gates), `Tests` deselects benchmarks; ADR 0011
- [x] P5.3a mutmut config, scope, shard and score scripts, PR job, sharded nightly; scope and shard count by rule; ADR 0012 proposed
- [x] P5.4 Benchmarks, `checks` smoke step and CodSpeed workflow; display ladder by rule
- [x] ~~P5.3b Mutation threshold from the first full sharded nightly (re-shard by rule if a shard runs over 255 min); ADR 0012 accepted~~ superseded by P5.3c
- [x] P5.3c Mutation testing manual and advisory: `mutation.yml` (`workflow_dispatch`, modes changed/pattern/all) replaces the PR job and the nightly; no `min_score`; ADR 0012 accepted

### Handoff (2026-10-07)

P5 is complete and merged through PR #7. Every timing and choice is in
`p5-run-log.md`. Follow-ups outside P5: start the manual Mutation workflow
once on `main` to confirm it runs; trim the three duplicate benchmark pairs
(`docs/issues/duplicate-benchmarks.md`); keep slow end-to-end tests out of
mutation runs (`docs/issues/slow-tests-in-mutation-runs.md`). The next step is **P6.1**.

## P6. Docstrings, prose and references

Order: P6.0, P6.1, P6.2, P6.3 (two sub-agents in sequence, one commit), P6.4, then P6.5a to P6.5e in parallel worktrees, landed one commit each in order a to e, then P6.6, on branch `p6-docs` (one PR). P6 edits docstrings, comments and prose only (AST-neutral check, G-here plus G-self). Every slice records its timings and choices in `p6-run-log.md`.

- [x] P6.0 Fatten P6 into slices; plan-reviewer pass
- [x] P6.1 References inventory (`p6-inventory.md`), sites by dotted path
- [x] P6.2 Match `design-sources.md` to the inventory; spec open question resolved
- [x] P6.3 Fetch and check every source; write `docs/explanation/references.md`
- [x] P6.4 Citation line in each implementing docstring; `tests/architecture/test_reference_keys.py`
- [x] P6.5a Docstring audit, then prose: `ink`
- [x] P6.5b Docstring audit, then prose: `letters`
- [x] P6.5c Docstring audit, then prose: `maps` façade, data and furniture
- [x] P6.5d Docstring audit, then prose: `maps` geometry and painter
- [x] P6.5e Docstring audit, then prose: `maps` lettering
- [x] P6.6 Prose audit of the docs; the phase gate

## P7. Docs and first release

Order: after P10 part 2 (maintainer, 2026-10-07). P7.1 to P7.3, then P7.4 tags 0.1.0, a release candidate; later issues are fixed in 0.1.x patch releases. Depends on P11: P7.2, and ideally P7.1's quick start, run after it (plan.md, P11, "Order").

- [ ] P7.1 README with gallery images
- [ ] P7.2 Tutorial, how-to guides, reference and explanation pages
- [ ] P7.3 ADRs 0013 to 0021 for the settled decisions
- [ ] P7.4 Changelog 0.1.0, trusted publisher, confirm, tag and publish

## P8. Upstream migration

Order: after P10 part 1, P11 and P10.R; the upstream consumes the `v0.0.1` tag, made after P11 merges. At the hand-off the orchestrating session records "what upstream reads" in `p10-triage.md`; P10 part 2 follows.

- [ ] P8.1 The upstream consumer migrates to the public API, with the recorded render hash reproduced first

## P9. Post-port cleanup

Order: after P7.4, P8, P10 (both parts) and P11.

- [ ] P9.1 Retire the banned-term test and the `personal_terms_file` option; ADR 0022 supersedes D16's enforcement clause for the post-port tree (the rule stands)
- [ ] P9.2 Retire the exemptions mechanism; ADR 0023
- [ ] P9.3 Delete `make_golden_old.py` and the last `ty` exclude
- [ ] P9.4 Delete `design-sources.md` once `references.md` covers it

## P10. Triage and address the port's issues

Order (maintainer, 2026-10-07; `plan.md` P10, "Order and parallelism"): P10.0, P10.1, P10.2 (the one stop point), then part 1 (the release blockers and every fix no upstream render can reach) on `p10-triage`, one PR; then P11, which starts only after part 1 has landed on `main`; then P10.R tags 0.0.1 (own `release-0.0.1` branch and PR, after P11 merges); then P8 consumes it, and the orchestrating session records "what upstream reads" in `p10-triage.md`; then part 2 (every fix an upstream render may reach, the private-name renames, the golden group) on `p10-fixes`, branched from `main` at the tag or later (and `p10-golden`); then P7 and P9. Part-1 slices whose rows are `fix` at P10.1 may run while the P10.2 list is open. Conditional slices run only under the answers `plan.md` names.

- [x] P10.0 Fatten P10 into slices; plan-reviewer pass
- [x] P10.1 Triage table `specs/001-port/p10-triage.md`: one row and one outcome per issue; dispatch the Mutation workflow once on `main`
- [x] P10.2 Maintainer decisions Q1 to Q14: answers recorded and re-triaged

### Part 1 (before P8)

- [x] P10.3a The labels switch no longer gates the attribution (release blocker, D8)
- [x] P10.3b prek in the dev group, and the hooks in CI (release blocker, Verification 1)
- [ ] P10.3c Cite the ink reservoir and pigment separation, and the blurred-mask rim if Q7 (C) or (A) (release blocker, D24)
- [ ] P10.3d One commit trailer rule (Q1)
- [x] P10.4a Delete the duplicate benchmarks
- [ ] P10.4b Rename `edt` to `chamfer_distance`; delete `point_to_segment`
- [ ] P10.5a The outline route narrows the nib; delete `_radii`
- [x] P10.8 Mark the slow CLI test golden
- [ ] P10.9 Docs and terms: non-canonical terms, the OpenTopoData question, rule seven in tests; display pixels (Q2), "sheet" and "map" kept apart everywhere (Q10, widened)

### Release

- [ ] P10.R Tag 0.0.1 after P11 merges: version and changelog on `release-0.0.1`, `v0.0.1` pushed after the maintainer confirms (PyPI only if Q14 (2)); ticked by the tag record on `p10-fixes`

### Part 2 (after P8 and its "what upstream reads" record)

- [ ] P10.4c The deposit drops corners off the accumulator
- [ ] ~~P10.5b Route-ink names follow the route ink (if Q5 (2); ADR 0024); a missing glyph advances as the face's space (if Q3 (2))~~ Not run: Q5 and Q3 were answered (1), so both members are closed (P10.2)
- [ ] P10.6 Maps lettering: landmark cap, span side sign, `Label.as_dict` (by the upstream-read record); ~~rung order if Q11 (1)~~ (removed: Q11 answered (2), row closed)
- [ ] P10.7 Other maps: `tunnel=no`; route constants if Q8 (a), by the upstream-read record
- [ ] P10.10a Public names for what other modules import: `ink` (if Q9 (a))
- [ ] P10.10b Public names for what other modules import: `letters` (if Q9 (a))
- [ ] P10.10c Public names for what other modules import: other `maps` (if Q9 (a) or (b))
- [ ] P10.10d Public names for what other modules import: `maps.lettering` (if Q9 (a))
- [ ] P10.11 Golden group, one regeneration window; ADR 0025 (if a row is `fix-golden` and Q12 yes). Empty after P10.2 (Q4 and Q6 closed): runs only if a fix slice's G-self moves a row

## P11. Widen the public API for primitive-first tutorials

Order: after P10 part 1 has landed on `main` (not merely after P10.1), and before P10.R, P8 and P7.1 (plan.md, P11, "Order").

- [ ] P11.0 Fatten P11 into slices; plan-reviewer pass
- [ ] P11.1 ADR 0026 amending 0007; widened `__all__` pinned in `test_public_api.py`
- [ ] P11.2 Promote the `ink` primitives: brush building, density, paper style, pigments, image writing
- [ ] P11.3 Promote the `letters` primitives: setting, face and hand styles, the nib plate
- [ ] P11.4 Promote the fetch cache and providers through `pyntpot.maps`
- [ ] P11.5 Tutorial scripts import only public names: architecture test, offline run against the fixture
