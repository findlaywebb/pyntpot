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
- P10.9 landed (`75ef5b9`), one slice, 491 changed lines in 80 files: 11 non-canonical sites,
  the OpenTopoData bullet resolved ("per instance", ADR 0004; Open questions now none),
  rule seven in 3 test docstrings, "display pixels" everywhere ("card pixel" grep empty;
  `display pixels` and `render pixels` glossary rows), and the widened sheet/map pass
  (non-`Sheet` "sheet" 391 lines to 262 kept, all the class, its fields, the brush sheet
  or one log string; `map` glossary row). A follow-up pass reworded every "map" in `ink`
  and `letters` prose (29 hits to 8 kept: the `maps` package named as a caller or
  importer, and the ink key `"map"`, a runtime value). Gates: AST-neutral 58 files;
  prek exit 0; not-golden exit 0; G-self exit 0 (18 passed, byte-identical) against
  `{"commit": "fd2c2cd...", "dirty": false}`. New later row `letters-map-ink-key`
  (issue filed): the `"map"` ink key in `letters`, `defer` to part 2 after P8's
  upstream-read record, since `Mark` may carry it to an upstream reader.
- Mutation run on `p10-triage` (https://github.com/findlaywebb/pyntpot/actions/runs/37771476343,
  head `457e6ad`): success, 4 min 11 s for the mutation step, 5 min in all. Score job:
  "counts: killed 60, timeout 0, survived 12, suspicious 0, no_tests 0, segfault 0",
  "mutation score 0.8333 (advisory)": all 72 mutants of the pattern tested, `_31` among
  the killed. Far faster than P5's 26 min because P10.8 marked the 61 s CLI test golden,
  so it left the mutation selection. P10.12 done and ticked; the `tasks.md:124` row
  done.
- P10.13 landed (`5d23e17`): `tests/support/lettering.py::sheet_card` renamed `map_card` (28
  uses repointed) and four tests renamed "sheet" to "map". The row's check grep is
  corrected (the seed missed `runs_across_the_sheet`) and prints nothing. Collected tests
  1062 before and after (`-p no:randomly`, summed per file). prek exit 0; not-golden
  125 s (1043 passed, 1 skipped); tolerance 417 s (18 passed). Part 1 is complete.
- Part-1 review (S3): three slice commits carry a message other than the one the plan
  gives, and the pushed history is left as it is. P10.3d `57d9548`: plan
  `State one rule for commit trailers`, actual `State one commit trailer rule`. P10.4a
  `a16c6bc`: plan `Delete the three duplicate ink benchmarks`, actual
  `Delete the duplicate benchmarks`. P10.8 `743b3bf`: plan
  `Mark the full-fixture CLI test golden`, actual `Mark the slow CLI test golden`.
- Part 1 diff review (fresh context, against the plan): 0 blocking, 3 should-fix,
  11 nits; logic changed only in the 11 files the plan intends, P10.9 docstring-only,
  ruff, ty, lint-imports and the architecture tests green. Fixes landed in one commit:
  the `letters-map-ink-key` issue corrected (the key resolves to `NibStyle.label_ink`;
  suggested name "label"), the `tasks.md:124` row done on the PR branch with a dispatch
  on `main` after the merge, the three differing commit messages recorded above, and
  nits N1 to N6, N8, N9 (benchmark smoke re-measured: 18.7 to 20.2 s) and N11; N7 and N10
  left (cosmetic; already recorded). Gates: prek exit 0; AST-neutral 4 files; not-golden
  121 s (1043 passed, 1 skipped). Part 1 ready for its PR, held for the maintainer's go.
- Maintainer (2026-10-08): "Yes, good to open prs." PR #9 opened from `p10-triage` to
  `main` (https://github.com/findlaywebb/pyntpot/pull/9); subscribed to its events. Branch
  model as the plan says: each later branch (`p11-*`, `release-0.0.1`, `p10-fixes`,
  `p10-golden` if needed) is cut from `main` after the previous PR merges; none merges
  into `p10-triage`. Part 2 is its own PR.
- Mutation run on `main` after the part-1 merge (https://github.com/findlaywebb/pyntpot/actions/runs/37854572820,
  head `ff752f6`, pattern `pyntpot.ink.polyline.x_simplify*`): success, 2 min 34 s for the
  mutation step, 3 min 20 s in all. Score job: "counts: killed 59, timeout 1, survived 12,
  suspicious 0, no_tests 0, segfault 0", "mutation score 0.8333 (advisory)": all 72 mutants
  tested; one mutant timed out on `main` that was killed on the PR branch's run, and the score
  counts a timeout as detected, so the score is unchanged. The `tasks.md:124` row is fully done.
  Recorded on `p11-public-api` as its first commit.
- P10.R. P11 merged to `main` as `aa42cd8` (PR #10, squash). `release-0.0.1` cut from it:
  one commit `45bb370` (`pyproject.toml` version `0.0.1`, the `uv.lock` version line,
  the `CHANGELOG.md` 0.0.1 section); `__version__` printed `0.0.1`, `uv lock --check`
  passed, G-here green (not-golden 1064 passed, 1 skipped; golden in tolerance 19
  passed), CI 7 of 7 green. Merged as `90c2fd6` (PR #11, squash) on the maintainer's go.
- Maintainer (2026-10-09), on merging and on the tag confirmation under Q14 (1), tag only
  and no pending trusted publisher: "Good on both".
- Tag: `v0.0.1`, annotated (`0d34737`), on `90c2fd6`, message "pyntpot 0.0.1, a
  candidate for the upstream migration". The orchestrating session's push was refused by
  the proxy (five attempts, "unexpected disconnect while reading sideband packet"; branch
  pushes worked), so it became the maintainer action "push `v0.0.1` at `90c2fd6`",
  which the maintainer did.
- Publish run: https://github.com/findlaywebb/pyntpot/actions/runs/37919206681, failure as
  expected under Q14 (1): checkout, setup-uv and Build succeeded; `pypa/gh-action-pypi-publish`
  failed at trusted publishing (no publisher registered for `pyntpot`; environment
  `pypi`, ref `refs/tags/v0.0.1`). Nothing reached PyPI.
- Hand-off for P8: tag `v0.0.1` at `90c2fd6`; the upstream's dependency line is
  `pyntpot @ git+https://github.com/findlaywebb/pyntpot@v0.0.1`. P10.R ticked in
  `tasks.md`. `p10-fixes` branches from `main` at the tagged commit; part 2 waits for
  P8's hand-off ("what upstream reads").

## Part 2

- Step 3, the before-check re-run at `p10-fixes`'s head `7902589` (base `0e094c7`, v0.0.2),
  read-only agent in a detached worktree; vulture and the AST scan also re-run at
  `ff752f6` (pre-P11) for the diff. No delta changes what a slice does.
  - P10.4c, P10.6, P10.7, P10.11: every before-check as the brief states (P10.4c
    `acc[3,0]` 1.0 for both samples; P10.6 picks 3 and 1, `_freer_side` side 1 at y 283.2,
    `def as_dict` at `label.py:179`; P10.7 route constants at `style_groups.py:256, 259,
    270, 272, 288`, `tunnel=no` and `tunnel=culvert` rivers both dropped, `_waterway` at
    `osm_elements.py:228`; ADR 0025 free).
  - P10.10 AST scan: the same 58 names (ink 6, letters 6, maps 12, maps.lettering 34),
    identical at `ff752f6` and now; `vector_layers.py` imports public names only; the same
    8 clashes; no stripped name in any `__all__` (P11 and P8.P names included) or in
    `GLOSSARY.md`. Count delta: the scan finds 13 underscore names that tests import and
    no other `src` module imports where the P10.10 brief says 32; the scan is identical
    at `ff752f6`, so this is a counting-method difference, not a code change. The rule
    is unchanged; the brief keeps the rule and the slice re-counts.
  - Vulture (`--min-confidence 60 src`): 52 lines (42 at `ff752f6`). New: `ink/io.py:52
    save_image` (P11), `maps/style.py:158 with_route_ink`, 8 in `maps/vector_layers.py`
    (P8.P); `landmark_export` renamed `candidate_export` (`export.py:57`). Nothing
    vanished. Part-2 after-checks grep vulture by name, not by line count.
  - New readers of the names P10.6 and P10.7 delete: none in `src` or `tests`
    (`with_route_ink` replaces colour and px only; `_check_keys` checks dataclass fields,
    and `casing` is a property). `effect["casing_colour"]` stays in `default.toml` as
    effect data that `RouteInk.effect` keeps.
  - P8 notes, measured: "a run's map" at `maps/layers.py:7` and `:109`; the out-of-box
    place filter is `maps/layers.py:144-145` (`_place_marks`; `vector_layers` passes it
    through), and deleting it leaves `pytest -m "not golden"` green.
- Maintainer (2026-10-20) on `upstream-provider-error-private`: wrap it: `fetch` catches
  `ProviderError` and raises `FetchError` from it. A public-surface change, so it carries
  an ADR (0028, the lowest free number above 0027). Goes to a plan fix and a
  plan-reviewer pass before its slice starts.
- Plan fix for part 2 (`cc1b510`, then `51f3024`), drafted by a fresh agent and reviewed by
  fresh plan-reviewers: round 1 BLOCK (sport words missed, the new ADR not passed to the
  hooks, line-number checks, a personal route name), round 2 PASS with nits. New slices,
  each its own because the maintainer said not to widen a slice for P8's notes: P10.14
  (generic wording in docstrings and comments), P10.15 (pin the out-of-box place
  filter), P10.16 (`fetch` wraps provider errors, ADR 0028). New `defer` rows:
  `maps-provider-error-private-beyond-fetch` (`Cache.ensure` and the providers' own
  methods still raise `ProviderError`; the upstream's forced refetch calls
  `Cache.ensure` directly), `maps-lettering-session-and-rider-for-a-track` (16 lines, 5
  of them `Label.why` values the upstream reads) and `ink-pad-lay-half-pixel-shift`
  (`fix-golden` by rule 4, standing `defer`). The reviewer's "fold P10.15 into P10.7"
  was not applied, for the same instruction.
- P10.4c's first attempt stopped: the fix turned
  `test_pad.py::test_a_finer_grid_converges_on_the_mark_the_brush_describes` red. That
  test's line left the plate, so the edge clamp inflated err(1); its 0.7 bound (from the
  bulk import) fails on an on-plate line on the old code too (err(2)/err(1) 0.69 to 0.75
  across 6 geometries and 7 seed pairs). Plan fix `51f3024` (review BLOCK, then PASS):
  `test_pad.py` joins P10.4c's owners; the replacement keeps the line on a 90-high plate,
  keeps `err[0] > err[1] > err[2]`, adds a first-order ink-weight check, and bounds the
  first doubling at 0.8.
- Landed (each rebased onto the head and G-here re-run there; G-self byte-identical on
  the starting commit):
  - P10.6 `1cc2d4f`, `37e8f6d`, `4aca4ec` (one commit per member). The new test named
    "session" was renamed to say "fast span" before commit. Re-gate: not-golden 1097
    passed 1 skipped; tolerance 22 passed; exact 22 passed. Coverage 96.14 / 94.35.
  - P10.16 `c7b9e25`. Red first: `ProviderError: opentopodata-srtm30m said
    'INVALID_REQUEST'`. Re-gate: not-golden 1099 passed 1 skipped; golden 22 and 22.
    Coverage 96.14 / 94.05.
  - P10.4c `0a45f00`. Red first: `assert np.float32(1.0) == 0.0` (and `== 0.5`); the
    replacement `test_pad` test passes on base and fix. Re-gate: golden 22 and 22.
    Coverage 96.14 / 94.04.
- Render record (`compose(..., attribution=False)` on the default style, for a real
  caller; the golden fixture is unchanged by each): P10.6 changes it when annotations
  carry name-only landmarks beyond the cap, or spans (every span's side flips).
  P10.4c changes it when a stroke reaches or crosses the card's edge (the edge pixels
  get lighter). P10.7's first member changes it when a river or stream way is tagged
  `tunnel=no`. P10.16 and P10.7's second member cannot. The upstream pins `@v0.0.2`, so
  none reaches it until it bumps.
  - P10.7 `d516aab`, `f85bfe4` (one commit per member). Red first: `assert 'Exe' in
    set()`. Re-gate: golden 22 and 22. Coverage 96.14 / 94.37. Vulture now also prints
    `style_groups.py:252: unused variable 'effect'`: `RouteInk.effect` is kept as decided
    (read for style equality and by `test_style.py`), so the line stays.
  - P10.14 `a3eb905`. AST-neutral 16 files; check 1 prints only the five deferred lines.
    Re-gate: not-golden 1105 passed 1 skipped; golden 22 and 22. The personal route name
    in `placement_flat.py:83`'s comment is gone.
  - P10.15 `fdd0f86`. Red with the filter lines deleted: `assert ['Lynton', 'Countisbury']
    == ['Lynton']`; `layers.py` restored byte for byte. G-here: not-golden 1106 passed.
    `74b368d` files `tests-invented-place-name` ("Faraway" in `test_picks.py`, from the
    port) as a later `defer` row.
- Gap found at P10.10a: the `fix` row `ink-stroke-mark-shares-the-mark-term` (filed by
  P11.3, "joins P10.10a ... plan-reviewed") had no brief; step 3 had not swept open rows.
  Plan fix `609cbcd` (review BLOCK: a landed slice cannot take a member, so a new slice;
  then PASS) cut it as P10.17 and swept every open `fix` row: the README badge row moved
  to P7.1's brief (Q13 (1) put it there), and rows 63 to 65 got the Done cells P8 had
  not written (pre-squash ids, landed in `0e094c7`).
- The renames (G-self byte-identical for each; the pin
  `test_no_module_imports_another_modules_private_name` red first for each new id):
  - P10.10a `6824cfe`: 6 `ink` names. `6e903c9` files
    `docs-feature-note-cites-old-smooth-path-name` as a later `defer` row.
  - P10.10b `fa3c084`: 6 `letters` names; clash `_chains` became `skeleton_chains`.
  - P10.17 `0a16b8c`: `ink.stroke.Mark` became `StrokeProfile`; the public-reach probe
    over the seven `__all__` modules prints `[]`.
  - P10.10c `17f9939`: 12 `maps` names; clashes `compose._plates` became `painted_map`,
    `contours._pad` became `padded_grid`.
  - P10.10d `2b7116f`: 34 `maps.lettering` names; clashes `box_on_paper`, `line_tilt`,
    `line_bow`, `line_window`, `name_stem`. The AST scan prints 0 pairs; the last re-gate:
    not-golden 1110 passed 1 skipped, golden 22 and 22.
- P10.11 not run: no part-2 slice moved a golden pixel, and the one `fix-golden` row
  (`ink-pad-lay-half-pixel-shift`) stands `defer`. No `p10-golden` branch; part 2 is
  one PR. For the maintainer's hand-off: `ink-pad-lay-half-pixel-shift` (a golden
  decision), `maps-provider-error-private-beyond-fetch` and
  `maps-lettering-session-and-rider-for-a-track` (both `defer`, awaiting an answer).
- Part-2 diff review (fresh context, `7902589..761e04d`): ready; 0 blocking. Should-fix:
  the plan and triage still named the side test "session span" (now "fast span"), and
  `CHANGELOG.md` lacked the four behaviour fixes; nit: two unwrapped issue-file lines.
  All fixed in `87cbfce`. Fast checks in a scratch copy: prek green, not-golden 1110
  passed 1 skipped.
- PR #25 opened from `p10-fixes` to `main`
  (https://github.com/findlaywebb/pyntpot/pull/25); subscribed to its events. Held for
  the maintainer's go. No `p10-golden` PR: the golden group is empty.
- PR #25's CI went red at `Audit dependencies` on both Pythons, before any test step:
  new advisories against the locked `certifi` 2026.7.22 (2) and `pillow` 12.3.0 (9).
  Not this PR's: the lock has not changed since `0e094c7`, and `uv audit` fails there
  too. Lock-only bump (`uv lock --upgrade-package pillow --upgrade-package certifi`):
  certifi 2026.10.19, pillow 13.0.0. Audit clean; `uv lock --check` passes; G-here green
  (not-golden 1110 passed 1 skipped; golden 22 and 22); golden output byte-identical to
  the pre-bump baseline; coverage 96.14 / 94.41; benchmarks 18 passed.
- Maintainer (2026-10-21), on the three deferred rows in PR #25's hand-off
  (`ink-pad-lay-half-pixel-shift`, `maps-provider-error-private-beyond-fetch`,
  `maps-lettering-session-and-rider-for-a-track`): "Those three changes all make sense to
  do to me." Read as: fix the half-pixel shift under the golden-group rules; wrap
  `ProviderError` wherever a public name can leak it, as for `fetch`; reword the
  `Label.why` values as well as the prose. Each goes to a plan fix and a plan-reviewer
  pass before its slice starts.
- Maintainer (2026-10-21), on the three follow-ups: `maps-provider-error-private-beyond-fetch`:
  export `ProviderError` and `ProviderBudgetExceededError` from `pyntpot.maps`, and
  `Cache.ensure` wraps them in `FetchError` (ADR 0029). `maps-lettering-session-and-rider-for-a-track`:
  "the rider's own place" becomes "home"; the session values say "track".
  `ink-pad-lay-half-pixel-shift`: shown before, after and diff (x8) comparisons
  (differing fractions at delta > 2: map 0.0601, wash 0.0534, labels-centreline 0.0344,
  pen 0.0005; paper identical; manifest hash and labels equal), the maintainer accepted
  the drift: "Accept it - identical to human eye". It is the golden group's one
  explained exception to the 0.005 step bound, as ADR 0006's step 3 was; P10.11 runs on
  `p10-golden` after the `p10-fixes` PR merges, with ADR 0025.
- Correction to the comparison figures above: the images the maintainer accepted were made
  with the three-call fix (`line * self.ss + (self.ss - 1) / 2` at each of `lay`'s stamp
  calls). The comparison script read RGB only; the repo's `differing_fraction` counts
  alpha for RGBA outputs. Canonical fractions (`make_golden.py --compare`, delta > 2):
  map 0.060095, wash 0.053400, labels-centreline 0.038954, pen 0.007298, paper 0.
- Plan fix `563676c` (draft, review BLOCK on the consumer's name in two hand-off notes,
  a seed-dependent `err[1] > err[2]` in P10.11's `test_pad.py` change and a missing
  CHANGELOG line; then a confirmation BLOCK on the exact test docstring; then applied as
  prescribed) adds P10.18, P10.19 and P10.11's body. P10.11's `test_pad.py` change, by
  the reviewer's seed sweep: err(2)/err(1) is 0.793 to 0.815 after the half-pixel fix
  (0.695 to 0.750 before), so the first-doubling bound becomes 0.85; err(3)/err(2) is
  0.910 to 1.037, so `err[1] > err[2]` is dropped for `err[2] < err[0] * 0.9`.
- P10.18 `ec1266c`: `ProviderError` and `ProviderBudgetExceededError` exported from
  `pyntpot.maps`; `FetchError` moved to `maps/cache.py` (`pyntpot.maps.FetchError`
  unchanged); `Cache.ensure` wraps; `fetch`'s own wrap removed as unreachable; ADR 0029.
  Red first: the provider's error escaping `pytest.raises`, and the `__all__` pin. G-self
  byte-identical; not-golden 1115 passed 1 skipped; golden 22 and 22; coverage 96.14 /
  94.41.
- P10.19 `ec062f9`: the five `Label.why` values say "track" and
  "home"; 11 prose lines reworded. Red first: `('start', 'where the session began') !=
  ('start', 'where the track began')`. G-self byte-identical (`why` is never drawn);
  not-golden 1117 passed 1 skipped; golden 22 and 22. Three test lines outside the rows
  still say "session": filed as `tests-session-wording` (`defer`).
- PR #25 (`p10-fixes`) merged to `main` as `79a95ad` (squash) on the maintainer's
  standing go ("You are good to merge pr25 when it is ready"), CI 7 of 7 green on
  `76fa144`.
- P10.11, the golden group, on `p10-golden` from `79a95ad`. Step 0 baseline at `79a95ad`.
  Step 1 `693c88b` (`Lay the finer ink grid centre to centre with the plate`): red first
  `assert 19.92800499178153 == 20.207119701747484 ± 0.1`; the step compare's only
  violations were the four accepted `--max-fraction` lines (wash 0.053400, pen 0.007298,
  labels-centreline 0.038954, map 0.060095; paper identical; hash
  `340a7f6e260ee1e2-e5a5f1b4b3ca2177` equal; labels equal), committed as the
  maintainer-accepted exception. Not-golden 1118 passed 1 skipped; coverage 96.14 / 94.57.
  Backup ref `wip/p10-golden-window` pushed at `693c88b` (container restarts), deleted
  after the push. Step 2, the regeneration: four images and `plates.json` changed (paper
  byte-identical; hash unchanged; `plates.json` final newline restored by the hook);
  G-here green (not-golden 1118 passed 1 skipped; golden 22 and 22); the final compare
  byte-identical against both the new goldens and step 1; old and new `map.png` look the
  same. ADR 0025 accepted.
- PR #26 opened (`p10-golden` to `main`). CI red on `checks (3.13)`, `(3.14)` and
  `prerelease`: the two smoke tests' exact `SMOKE_SHA`, wash only. Cause: numpy's float32
  wash differs by 1 ulp between AVX-512 and non-AVX-512 paths; after the half-pixel fix one
  pixel, (90, 97), rounds one level apart. `NPY_DISABLE_CPU_FEATURES=X86_V4` reproduces CI's
  hash. One comment on the PR. Plan fix `5e174a0` (review BLOCK on the mutation run, which
  runs the same tests exact; then PASS) added P10.11 step 3 and ADR 0030.
- P10.11 step 3: the smoke lock is exact locally; under `--golden-tolerance` (CI's Tests
  steps and `[tool.mutmut]`) paper and pen stay byte-exact and wash is compared with
  `differing_fraction` against `tests/golden/smoke/wash.webp`, which a test pins to
  `SMOKE_SHA["wash"]`. Red: exact under X86_V4, 2 failed. Green: tolerance under X86_V4
  (3 passed; whole not-golden 1101 passed 1 skipped; mutmut selection 1035 passed); G-here
  green (not-golden 1119 passed 1 skipped; golden 22 and 22); coverage 96.14 / 94.57; no
  `src` or `tests/golden/lynmouth` change.
