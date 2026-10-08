# P10 run log

Orchestrated run (orchestrator-mode). Branch `p10-triage`; one PR to `main`.

User instructions (2026-10-07):

- "In this session we will do p10 of the port tasks."
- Order from `plan.md` P10: P10.0 to P10.2 run now (P6 has merged, P7.1 has not
  started); fix slices after P8 unless release-blocking. P10.2 is the one sanctioned
  stop point.

## Log

- Branch `p10-triage` from `main` at `91ff457` (P6 merged, #8). `docs/issues/` holds 29
  files, the same set as at `d82f732`. P10.0 investigation fanned out to five read-only
  agents (ink and references; letters; maps lettering; other maps and src terms; tooling,
  process and the run logs), each writing a per-issue dossier to the scratchpad.
- Investigation done (5 agents, about 6 to 7 min each). Dossiers in the scratchpad
  (`p10/dossier-{ink,letters,maps-lettering,maps-other,tooling}.md`). Proposed:
  29 files plus 3 non-file items plus 3 run-log items (all `close`). Release blockers:
  `maps-style-groups-labels-switch-also-drops-the-attribution` (D8),
  `prek-not-in-the-environment` (Verification 1; CI also never runs prek),
  `unlisted-technique-ink-reservoir` and `unlisted-technique-pigment-separation` (D24).
  No proposed fix moves a golden: the golden path letters with no annotations (no spans,
  no landmarks), composes with `attribution=False`, uses `label_route = "centreline"`,
  `label_route_ink` equals every route ink, no deposit sample lands off the accumulator
  (3.38 M samples probed), and no fixture way carries `tunnel=no`. Only the `decide` rows
  for the pen angle and held stroke ends would be `fix-golden`.
  - choice: P10.0 cuts slices from the dossiers; P10.1 re-verifies and writes the table
    | rule: plan P10 "P10.0 fattens it into slices" and "Triage (P10.1)" | inputs: dossiers.
- P10.0 plan committed (`177a9f5`), 14 min planner, about 1,140 lines. Slices P10.3a to
  P10.3d (release blockers and the trailer rule), P10.4a to c (ink), P10.5a and b
  (letters), P10.6 (maps lettering), P10.7 (other maps), P10.8 (slow test), P10.9 (docs
  and terms), P10.10a to d (private names, if Q9), P10.11 (golden group, empty unless
  answers move rows). Planner departures kept: the route-ink cache key cannot come from
  `LETTERING_GROUPS` (it would change the frozen `lettering_digest`), so Q5 now
  recommends close; the deposit mask multiplies last to stay byte-identical; Q13 keeps
  every fix reachable by an upstream render after P8; new row `point_to_segment` (no
  caller). Plan review 1 running.
- Plan review 1: BLOCK (3 blocking, 10 should-fix, 11 nits; `reviews/p10-plan-review-1.md`).
  Blocking: parallel marks put slices sharing `letters/trace.py` and `letters/nib.py` side
  by side; P10 is never ordered against P9 and its ADR numbers collide with 0022/0023;
  "P8's list of what upstream reads" has no author or location. Fix round held for the
  maintainer's answer on phase order (asked: P8 before P7? P9 before P7?), since B2 and
  B3 depend on it.
- Maintainer on phase order (2026-10-07): "maybe we split these into multiparty so we do
  most of p10 now, 0.0.1+ as the release, then p8, then the rest of p10, then the p7
  docs, then the 0.1.0, then p9". Also: "0.1.0 can be candidate release and then 0.1.x
  can be fixes". Adopted the split: P10 part 1 (release blockers and every fix no
  upstream render can reach), tag 0.0.1, P8 against 0.0.1, P10 part 2 (fixes an upstream
  render may reach, private-name renames, golden group), P7 docs and 0.1.0, then P9.
  Plan-fix round 1 dispatched with this order and the review-1 findings.
- Plan fixes for review 1 landed (`6506569`), all 24 findings resolved and the phase
  order applied. Fix-agent choices kept: rule-seven test text moves to P10.9 (part 1, so
  `test_spans.py` line 64 is edited once); P10.R sets `version = "0.0.1"` plus `uv lock`
  and a CHANGELOG entry, and P7.4 sets 0.1.0; a `v*` tag runs `publish.yml`, and
  `pyntpot` is not on PyPI, so Q14 asks tag-only (recommended) or PyPI; ADRs 0024 and
  0025 fixed for P10.5b and P10.11. Plan review 2 running.
- Merged `main` (`1bae755`, the P11 sketch: widen the public API) into `p10-triage`;
  conflicts in the P7 order lines and the P10/P11 task lists kept both sides. Notes from
  the P7/P11 session, for the next plan-fix round: (1) P10 must claim its ADR numbers
  explicitly (it does: 0024 for P10.5b, 0025 for P10.11), so P11 takes the next free
  above those; (2) a P10 rename of a name P11 makes public is simpler before P11. P11's
  "Order": after P10.1, before P7.1, and P8 starts after it, so 0.0.1 (P10.R) comes
  after P11 and the order becomes P10.0 to P10.2, part 1, P11, P10.R, P8, part 2, P7, P9.
- Plan review 2: BLOCK (2 blocking, 5 should-fix, 9 nits; `reviews/p10-plan-review-2.md`);
  23 of 24 round-1 findings confirmed resolved, S9 partly. Blocking: P10.10a renames
  `ink.tip._fbm1`, which `references.md` cites, without owning `references.md`; P11 is
  not yet in P10's order. Plan-fix round 2 dispatched with the review-2 findings and the
  P11 integration (order part 1, P11, P10.R, P8, part 2; ADR claim; renames P11 touches
  move before P11).
- Plan fixes for review 2 landed (`dd828d4`), all 16 findings resolved; P11 placed: part 1,
  P11, P10.R (`release-0.0.1` branch), P8, part 2 (`p10-fixes`), golden group
  (`p10-golden`), P7, P9. ADR 0026 fixed for P11.1. No overlap between what P10 renames
  or deletes and P11's 20 promoted names (AST scan at `4e316a3`). Plan review 3 running.
- Plan review 3: PASS (0 blocking, 3 should-fix carried, 4 nits;
  `reviews/p10-plan-review-3.md`). All 16 review-2 findings confirmed; the 58-name scan
  re-run at HEAD agrees and shares no module with P11's 20 names. Carried into a plan
  touch-up commit: re-measure part-2 facts at `p10-fixes`'s base and stop a slice whose
  before-check differs (S1); P10.10's renamed names join no `__all__` and need no ADR
  (S2); route issues found in P11 and fixes cut after `p10-fixes` merges (`p10-late-<id>`)
  (S3); N1 to N4. P10.0 ticked. P10.1 started: a drafting agent re-runs every
  reproduction and writes `p10-triage.md`; the orchestrating session checks and commits.
- P10.1 triage written at `656f4a4` (drafting agent, every reproduction re-run; probes in
  the scratchpad `p10/p101_repro.py`). 38 rows: fix 19, decide 12 (Q1 to Q11, Q13),
  defer 4, close 3 (the run-log rows), fix-golden 0. No row differs from the seed; every
  filed claim reproduces, so no issue file is deleted. One reproduction wider than the
  plan: the "sheet" sense of Q10 is also on 9 test docstring lines in 4 lettering test
  files, not only `test_spans.py` line 64; put to the maintainer inside Q10.
  Gate: `git diff --stat -- src tests` empty; prek on the new file passed.
- Mutation workflow dispatched on `main` (`mode: pattern`,
  `pattern: pyntpot.ink.polyline.x_simplify*`), GitHub returned 204 (queued); run URL,
  wall time and score to be recorded when it finishes.
- P10.2 list put to the maintainer. Meanwhile, as the plan allows, P10.3a, P10.3b and
  P10.3c (first commit: reservoir and pigment separation only) dispatched to implementers
  in detached worktrees from `d30ff4b`, under the interim trailer rule.
- P10.3b landed (`cbaeff3`): `prek>=0.5` in the dev group (prek 0.5.5 locked), a `Hooks` step
  in `ci.yml`. Gates in the worktree: `uv run prek run --all-files` exit 0, 9 s (all 9
  hooks); not-golden 172 s (1043 passed, 1 skipped); golden tolerance 294 s and exact
  288 s (17 passed each); no `src/` change, so no G-self. Issue file deleted; rows done.
  Re-checked on the branch: `uv run prek run --all-files` green.
- P10.3c first commit landed (`119484b`): `ink-reservoir` and `pigment-separation` entries
  in `references.md`, `Source:` lines in `ink.deposit.spend` and `ink.wash.separated`.
  Red: `test_every_site_cites_its_key` named both sites; green after the two lines.
  Baseline `{"commit": "d30ff4b...", "dirty": false}`; AST-neutral 2 files; prek exit 0;
  not-golden 169 s (1043 passed, 1 skipped); tolerance 287 s; G-self 293 s (17 passed,
  byte-identical). The blurred-mask-rim member waits on Q7; P10.3c stays unticked.
- P10.3a landed (`ab74d1c`): `draw_attribution` opens its hand without the `labels` gate;
  `LetteringPolicy.labels` comment reworded; new
  `TestLabelsOff::test_written_when_the_map_is_not_lettered`, red first (`assert None is
  not None` on the bbox), then green. Baseline `{"commit": "d30ff4b...", "dirty": false}`;
  prek exit 0; not-golden 167 s (1044 passed, 1 skipped); tolerance 292 s; G-self 295 s
  (17 passed, byte-identical). D8 release blocker cleared.
- Mutation run 1 on `main` (https://github.com/findlaywebb/pyntpot/actions/runs/37689849941,
  head `1bae755`): `plan` passed; shard 0 reached 42 of the pattern's mutants (38 killed,
  4 survived) and died at 9 min 14 s with "The runner has received a shutdown signal"
  (exit 143), not the 270-minute step timeout; `score` failed with no stats. Runner loss
  counts as death outside a test body, so the failed jobs were re-run once (attempt 2).
  A second failure is real and is filed under "Later issues".
- P10.4a landed (`a16c6bc`): `test_sheet_construction`, `test_edt`, `test_wash` and `_disc`
  deleted from `tests/benchmarks/test_ink.py`; their three rows dropped from
  `performance.md` with a sentence that their CodSpeed history ends. Check grep 4 then 0;
  prek exit 0; not-golden 172 s (1041 passed, 1 skipped); tolerance 320 s.
- P10.2 answers (maintainer, 2026-10-07, verbatim):
  "4. Do note it somewhere as a candidate. Maybe a new features dir that mirrors the
  issues dir. and or add as a gh feature
  6. Keep current look but add new possible feature to make it togglable
  10. Ensure map and sheet are distinct everywhere. Sheet is a primative concept and map
  is only for the map implementation side
  Otherwise as recommended"
  Read as: Q1 (2), Q2 (1), Q3 (1), Q4 (1) plus a candidate-feature file, Q5 (1), Q6 (B)
  plus a candidate feature (a style switch that holds the stroke ends, off by default),
  Q7 (C), Q8 (a), Q9 (a), Q10 (1) widened from the lettering scope to every `src`, test
  and docs use ("sheet" only for `ink.sheet.Sheet` and its noise fields; "map" for the
  drawn card on the maps side), Q11 (2), Q12 yes for a row a fix slice's G-self moves,
  Q13 (1), Q14 (1). Candidate features go in a new `docs/features/`, mirroring
  `docs/issues/`; GitHub issues are optional ("and or") and not created.
- P10.8 landed (`743b3bf`): `@pytest.mark.golden` on
  `TestMap::test_a_full_cache_makes_no_request`; the marker alone dropped `maps` coverage
  to 90.87 (gate 92, exit 2), so per the slice a fast non-golden CLI test
  (`test_a_small_display_style_paints_a_map_quickly`, `display_px = 120`, about 3.5 s) was
  added: ink+letters 95.49 to 95.59, maps 93.18 to 93.30; no gate touched. Not-golden
  111 s (1044 passed, 1 skipped; was about 170 s); tolerance 364 s (18 passed). The issue
  file is narrowed to part (b). Bookkeeping slip: the commit also carries the five
  issue-file deletions the P10.2 agent had staged (Q3, Q4, Q5, Q6, Q11 rows, all `close`);
  their rows and the triage update land in the P10.2 commit. P10.8's row and tick follow
  with it.
- P10.2 applied (`5c83da1`): 39 rows, fix 26, decide 0, defer 5, close 8, fix-golden 0. Closed
  Q3, Q4, Q5, Q6, Q11 (files deleted, inside `743b3bf`); candidate features
  `docs/features/letters-nib-follows-writing-line.md` and
  `docs/features/ink-tip-hold-stroke-ends.md`, `docs/README.md` lists `features/`.
  Q10 widened: 125 non-`Sheet` uses of "sheet" (maps 88 in 34 files, ink and letters
  14 in 7, tests 20 in 14, glossary 3); P10.9 estimated about 410 lines, not split, with
  a stop-and-split rule past 600. New later row
  `maps-tests-sheet-identifiers-name-the-map` (`sheet_card` and four test names), slice
  to be cut under "Later issues". P10.5b not run (both members closed); P10.6 drops rung
  order; P10.11 empty unless a fix slice's G-self moves a row. P10.8 row done, ticked.
- P10.3c second commit landed (`3951cba`), Q7 (C): `pyntpot.ink.wash.wash` added to
  `edge-darkening`'s `Implemented in:` line, `Source:` line in `wash`. Red:
  `test_every_site_cites_its_key` named `edge-darkening: pyntpot.ink.wash.wash`; green
  after. Baseline `{"commit": "489f3a6...", "dirty": false}`; AST-neutral 1 file; prek
  exit 0; not-golden 172 s; tolerance 312 s; G-self 300 s (17 passed, byte-identical).
  P10.3c ticked. All four release blockers (D8, Verification 1, D24 twice over) cleared.
- Mutation run attempt 2 failed the same way: shard 0 died during the 43rd mutant of the
  pattern (after 42: 38 killed, 4 survived), "The runner has received a shutdown signal",
  exit 143, at 4 min 40 s. Deterministic, so real (a second failure is real). Working
  hypothesis: one `simplify` mutant exhausts the runner's memory; mutmut caps time per
  mutant, not memory. A capped local reproduction is running; the finding is filed under
  "Later issues" once the mutant is named.
- P10.3d landed (`57d9548`), Q1 (2): `CONTRIBUTING.md` "Commits" now says an agent session's
  commit ends with its session's attribution trailers; the plan's "P3 and P4" slice rule,
  P9 preamble and P10 "Commit messages" rule say the same. Check: the `rg` printed seven
  lines before, three after (P0's record line and the two Q1 lines), as the plan states.
  prek exit 0; not-golden 117 s; tolerance 364 s.
- Paused at the maintainer's request (`952ab03`). Two in-flight agents stopped before
  hand-off, nothing from them kept: the P10.4b implementer (worktree discarded, no edits
  landed) and the capped mutant reproduction (no findings file written). No worktrees,
  no uncommitted changes.

## Resume point

- Done: P10.0, P10.1, P10.2, P10.3a, P10.3b, P10.3c, P10.3d, P10.4a, P10.8. Every
  release blocker is cleared (D8, Verification 1, D24).
- Part 1 left, in order: P10.4b (rename `edt` to `chamfer_distance`, delete
  `point_to_segment`; restart from scratch), then P10.5a (outline route, delete `_radii`),
  then P10.9 (docs and terms, with the widened sheet/map pass; stop and split into
  P10.9a/b past 600 lines). Then open the `p10-triage` PR (not opened yet; the maintainer
  was asked whether to open it now or when part 1 is complete).
- Open finding to file under "Later issues": the Mutation workflow on `main` dies
  deterministically during the 43rd mutant of `pyntpot.ink.polyline.x_simplify*`
  (run 37689849941, both attempts, exit 143, runner shutdown). Next step: name that
  mutant and reproduce it locally under a hard memory cap (`prlimit --as=4G`, `timeout`),
  then propose a memory limit around `mutmut run` in `mutation.yml`. The `tasks.md:124`
  row stays not done until a run completes.
- Untriaged later row: `maps-tests-sheet-identifiers-name-the-map` (slice not cut).
- After part 1: P11, then P10.R (tag 0.0.1, tag only, after the maintainer confirms no
  pending PyPI trusted publisher), then P8, then part 2, P7, P9.
- Resumed 2026-10-08 at `253dfc3`: P10.4b restarted from scratch; the capped mutant reproduction restarted.
- P10.4b landed (`90c3812`): `ink.noise.edt` renamed `chamfer_distance` across 8 `src`
  files, 6 test files and `references.md`; `ink.polyline.point_to_segment` deleted. Check
  grep for both names prints nothing. Baseline `{"commit": "253dfc3...", "dirty": false}`;
  prek exit 0; not-golden 111 s (1041 passed, 1 skipped); tolerance 364 s; G-self 400 s
  (18 passed, byte-identical); `test_reference_keys` 7 passed.
- P10.5a landed (`0484a72`): `draw_plate` builds `NibGroups` with
  `replace(style.face, label_route=hand.route)`; `letters.trace._radii` deleted. Red:
  `test_an_outline_route_is_written_with_the_finer_nib` failed on the plate difference
  (bbox (0, 9, 115, 76)); green after. Vulture at 60 no longer lists `_radii`. Baseline
  `{"commit": "033db9c...", "dirty": false}`; prek exit 0; not-golden 112 s (1042 passed,
  1 skipped); tolerance 393 s; G-self 403 s (18 passed, byte-identical).
- Mutation failure root-caused (capped local reproduction at `1bae755`, 49 min):
  `pyntpot.ink.polyline.x_simplify__mutmut_31` (`best, bi = -1.0, lo` to `+1.0`) loops
  for ever when every point lies within 1.0 of the chord, growing the stack about
  90 to 100 MB/s; mutmut 3.8 caps CPU time only. "42 tested" was the count of finished
  mutants with four running at once, so 31 was the one still running. Under
  `prlimit --as=3500000000` the mutant gets `MemoryError` at 31 s and scores killed
  (exact step text checked locally, 321 s). Filed as
  `docs/issues/mutation-runaway-mutant-kills-the-runner.md`, row added, fix cut as
  P10.12 (part 1). The later row `maps-tests-sheet-identifiers-name-the-map` cut as
  P10.13 (part 1, after P10.9). Both slices written under "Later issues", no plan review
  (each one small, owner files and check named).
- P10.12 landed (`457e6ad`): the workflow's "Mutation run" step runs
  `prlimit --as=3500000000 -- uv run mutmut run`; ADR 0012 gains the cap and how a capped
  runaway scores, plus a History line; new
  `tests/mutation/test_workflow.py::test_every_mutmut_run_is_under_an_address_space_cap`,
  red first, green after. Gate: prek exit 0; not-golden 127 s (1043 passed, 1 skipped);
  tolerance 392 s (18 passed). Mutation workflow dispatched on `p10-triage`
  (`mode: pattern`, `pyntpot.ink.polyline.x_simplify*`, 204 queued); P10.12 and the
  `tasks.md:124` row are done when that run completes with a score.
