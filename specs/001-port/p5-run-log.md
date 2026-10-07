# P5 run log

Orchestrated run (orchestrator-mode). Branch `p5-quality`; one PR to `main`.

User instructions (2026-10-07 01:25 BST):

- Implement P5.1, P5.2, P5.3a and P5.4, open the PR, confirm it passes.
- 01:40 BST: no stop points. Every slice makes its own choice by a stated
  rule (mutation scope, sharding, which benchmarks stay, display size) and
  records it with its numbers in this log.
- After P5.4 and a green PR: a final HTML report stating every timing and
  every choice, published as an artifact.
- Resume trigger at 05:00 BST (`trig_01SinKcqKPbmg6iqfFi66Rto`).

## Log

- 01:25 P5.0 plan committed (`d1eb2c3`, `c123091`); plan-reviewer running.
- 01:50 Plan review 1: BLOCK (3 blocking, 8 should-fix, 3 nits). Notable:
  mutmut breaks with `tests/` selection (architecture tests scan `mutants/`);
  ink+letters is 8310 mutants, about 4.5 to 9 h unsharded on 4 cores.
  Orchestrator decisions sent to the fix agent: nightly sharded from the start
  (N = ceil(hours / 3.5), at least 2; maps joins scope if N stays at most 8);
  benchmarks kept, smoke budget 60 s with display ladder 450, 300, 200;
  coverage measured on 3.13 and 3.14, lower figure gates.
- 01:38 Container restart lost the first plan-fix agent; re-dispatched from
  the committed plan.
- 01:47 Plan fixes for review 1 landed (`f4df084`). Two fix-agent additions
  kept: per-module patterns `x_*` and `xǁ*` (a package `__init__` name prefixes
  its submodules), and `shard.py` refusing an empty shard. Plan review 2 running.
- 01:58 Plan review 2: BLOCK on one item (step-3 timing measurement double
  counts across runs), plus should-fixes on the CI run script, scope.py edge
  cases, survivor filtering and a P5.3b re-shard rule. All 14 round-1 findings
  confirmed resolved. Fix agent dispatched.
- 02:20 Plan review 3: PASS. Two P5.3a items carried into the P5.3a brief
  rather than another plan round: guard an empty patterns file at the top of
  the PR run script; compute sample counts and scores from `.meta` exit codes
  (`mutmut.stats.status_by_exit_code`), not before/after stats. P5.0 ticked.
- 02:15 P5.1 property tests: 28 tests in 7 files, default profile (100 examples
  each, no `max_examples` cut). Suite time 10.4 s (budget 30 s). Slowest:
  hand same-seed 1.53 s, stamp same-seed 1.04 s, stamp path-unchanged 0.75 s,
  pigment no-layers 0.47 s, blur constant-field 0.46 s; the rest under 0.45 s.
  Passed also under `--hypothesis-seed` 11, 12, 13 and `CI=true` with
  `--randomly-seed` 1 and 2. No findings filed: every property held.
- 02:18 P5.1 verified by the orchestrator (977 passed, lint and types clean) and ticked. CodSpeed onboarding PR is #6 (branch `codspeed/setup-benchmarks`, opened 02:15); P5.4 reconciles it.
- 02:31 P5.2 coverage baseline (ADR 0011), `CI=true`, `-m "not golden and not benchmark"`,
  branch, two runs per interpreter, identical within each. 3.13: ink+letters 95.49,
  maps 92.87, whole package 93.69. 3.14: ink+letters 95.38, maps 92.77, whole
  package 93.59. Rule: T = 95 (3.14 figure rounded down), T_maps = 92 (3.14, same).
  Bite check: `--fail-under=96` on ink+letters exited 2 ("total of 95 is less than
  fail-under=96"); maps `--fail-under=94` exited 2. Note: `maps --fail-under=93`
  exits 0 at default precision (92.87 displays as 93); with `--precision=2` it exits 2.
  Gates at T and T_maps exit 0.
- 02:55 P5.2 landed (`33b3950`); T = 95, T_maps = 92 from 3.14. Orchestrator found the gate rounded to whole percent; fix `f506f44` gates at two decimals (maps at 93 now exits 2). P5.2 ticked.
- 05:45 P5.3a mutation testing (ADR 0012 proposed). Machine idle, 4 cores; times BST.
  - Step 1 (02:58 to 03:21): the plan's `[tool.mutmut]` table as written fails here.
    With mutmut's default `process_isolation = "fork"`, `uv run mutmut run
    "pyntpot.ink.polyline*"` passed stats, then "Failed to run clean test":
    Hypothesis `FailedHealthCheck` (`differing_executors`) on
    `tests/property/test_polyline.py::TestSimplify::test_simplifying_twice_changes_nothing`.
    mutmut runs pytest twice in its own process and forks mutants from it, so each
    property-test class gets a second instance; every mutant forked after that would be
    "killed" by the health check. Fix, in the owned `[tool.mutmut]` table:
    `process_isolation = "forkserver"` (each pytest call in a fresh process). Re-run from
    a clean `mutants/`: stats, clean run and forced-fail check pass, mutants test
    (interrupted after 182 of 715 polyline mutants). `mutants/src/pyntpot/ink/polyline.py`
    defines `x_simplify__mutmut_1`; method keys read `pyntpot.ink.sheet.xǁCanvasǁpx__mutmut_1`;
    name format as the tool facts, no script change. The 14 `Hand` unit tests pass inside
    `mutants/` against the trampolined `letters/hand.py`; the font was copied, so no
    `also_copy`.
  - Finding: `tests/unit/maps/test_cli.py::TestMap::test_a_full_cache_makes_no_request`
    takes 72 s and reaches most `ink.polyline` functions, so every surviving mutant there
    pays it. A looping mutant runs to mutmut's wall bound, `(estimated + 1) * 15` s,
    about 20 minutes for such a function. Under `forkserver`, mutmut 3.8 records every
    mutant's duration as 0.0.
  - Step 2 (03:24 to 03:53), PR path on a scratch commit editing `simplify` line 67
    (`best, bi = -1.0, lo` to `bi, best = lo, -1.0`), from a clean `mutants/`, steps run
    as CI does (`bash -eo pipefail`). `scope.py --base HEAD~1` wrote one pattern,
    `pyntpot.ink.polyline.x_simplify*`. Run step: exit 0, 1570 s, `tested=true`.
    `export-cicd-stats`: killed 57, survived 12, timeout 1, segfault 2, no_tests 0,
    total 8310. `results` filtered to the 72 tested (12 survived, 2 segfault, 1 timeout
    listed). `score.py`: "mutation score 0.8056, min_score 0.0000", exit 0. The two
    segfaults are exit -9: mutant 31 (`best = +1.0`) loops while its stack grows and is
    killed; mutmut 3.8 classes SIGKILL as segfault, which counts against the score.
    Scratch commit dropped; `src` clean. Correction 1 checked: `scope.py --base HEAD`
    wrote an empty file, the run step logged "no changed functions in the mutation
    scope", wrote `tested=false` and exited 0.
  - Step 3 (03:55 to 05:40), `only_mutate` temporarily all three, counts from `.meta`
    exit codes via `mutmut.stats.status_by_exit_code` (correction 2). `O` = 379 s (cold,
    one mutant; generation 26 s). `M`: ink 6151, letters 2159, maps 17099.

    | Sample | Wall (s) | Tested | Score |
    | --- | --- | --- | --- |
    | `pyntpot.ink.polyline*` | 1200, exit 124 | 179 (46 no tests, 99 killed, 33 survived, 1 timeout) | 0.5587 |
    | `pyntpot.ink.polyline.x_deform_line*` (narrowing 1, 130 mutants) | 651 | 130 (98 killed, 32 survived) | 0.7538 |
    | `pyntpot.letters.hand*` | 1200, exit 124 | 76 (57 killed, 19 survived) | 0.7500 |
    | `pyntpot.letters.hand.xǁHandǁ_flat*` (narrowing 1, 95 mutants) | 516 | 95 (72 killed, 23 survived) | 0.7579 |
    | `pyntpot.maps.rings*` | 574 | 98 (79 killed, 19 survived) | 0.8061 |
    | `pyntpot.maps.painter.cover*` | 1200, exit 124 | 173 (119 killed, 54 survived) | 0.6879 |
    | `pyntpot.maps.painter.cover.x__class_washes*` (narrowing 1, 69 mutants) | 612 | 69 (45 killed, 24 survived) | 0.6522 |

    Each narrowing took the module's function with the most mutants, and each narrowed
    run finished, so no second narrowing. The `x__class_washes` mutants had all been
    tested by the timed-out `cover` run; the narrowed run re-tested all 69 (mutmut
    re-runs every mutant a pattern names, and its printed results agree: 45 killed,
    24 survived), so the after-run `.meta` codes are that run's.

    | Subpackage | M | s (s/mutant) | H (h) |
    | --- | --- | --- | --- |
    | ink | 6151 | 5.01 (651 / 130) | 8.56 |
    | letters | 2159 | 5.43 (516 / 95) | 3.26 |
    | maps | 17099 | 7.10 (1186 / 167) | 33.73 |

    `N_core` = max(2, ceil(11.81 / 3.5)) = 4. `N_all` = max(2, ceil(45.55 / 3.5)) = 14.
    `N_all` > 8, so the scope stays `ink` and `letters` and `N` = 4; `maps` is out on
    `H_maps` 33.73 h and `N_all` 14. `only_mutate` restored to ink and letters,
    `shards = 4`. `shard.py --index 0` wrote 12 patterns (6 modules); `--matrix-out`
    appended `indices=[0, 1, 2, 3]`. The 21 in-scope modules with mutants (4942 lines)
    split 1296, 1240, 1198 and 1208 lines; the 6 modules left out
    (`ink/__init__`, `brush_style`, `stroke`, `ink/style`, `letters/__init__`,
    `letters/style`) have 0 mutants by mutmut's own generator. `mutants/` removed.
  - Action pins from `git ls-remote --tags`: `upload-artifact@v7.0.1`,
    `download-artifact@v8.0.1`.
- 06:03 P5.3a landed (`bfb7af9`) and verified by the orchestrator (lint, types, mutation-script tests, workflow YAML parse). Scope ink+letters, 4 shards; maps out at about 34 h. Deviation accepted: `process_isolation = "forkserver"` (Hypothesis health check under mutmut's in-process reruns). P5.3a ticked.
- P5.4 benchmarks and the CodSpeed workflow. Machine idle, 4 cores, Xeon @ 2.80GHz, Python 3.13.16, numpy 2.5.2.
  - Reconcile: onboarding PR #6 (`codspeed/setup-benchmarks`, 17 benchmarks over ink, letters and maps, a workflow, a README badge, and a `--benchmark-disable` on ci.yml's `Tests` step). Read, never pushed to. Adopted: the workflow's `workflow_dispatch` trigger and its comment, and `id-token: write` (already in the plan's spec); no token input or runner choice (OIDC, `ubuntu-latest`). Superseded here, so PR #6 can be closed: `--benchmark-disable` is in `addopts` and ci.yml's `Tests` step already deselects benchmarks. Not adopted (outside this slice's owner files): the README badge. All 17 PR benchmarks kept, rewritten to the repo's rules (module `pytestmark`, no asserts, no mocks, seeded inputs, `brush, _ = ...`, one `benchmark` call each); none left out. Nothing breaks a repo rule.
  - The PR's 4 maps benchmarks became `test_fetch`, `test_paint`, `test_letter`, `test_compose` (the plan's `test_paint` and `test_compose` are the PR's painting and composing under the plan's inputs: `class_style(display_px=DISPLAY_PX)`, fresh directory per round, attribution on). The PR's 4 letters benchmarks went to a third file, `test_letters.py`, since the plan names only `test_ink.py` and `test_maps.py` and the letters layer is its own. The PR's ink benchmarks sit beside the plan's 4 in `test_ink.py`; where they overlap (sheet, edt, stamp, wash) both are kept, with different inputs, and the PR's wash shares the plan's seed-3 sheet.
  - Smoke budget (60 s): `uv run pytest -m benchmark` at `DISPLAY_PX = 450` took 17.8 s wall (21 passed). Under 60 s at the first rung, so no 300 or 200 step and no benchmark dropped. Final `DISPLAY_PX` = 450.
  - Timings (median under `--benchmark-enable`, smoke = untimed call; fixtures about 6.4 s once, charged to `test_letter`'s setup):

    | Benchmark | Source | Median (ms) | Rounds | Smoke (s) |
    | --- | --- | --- | --- | --- |
    | `test_ink.py::test_sheet_construction` | plan | 95.18 | 10 | 0.08 |
    | `test_ink.py::test_edt` | plan | 14.79 | 65 | 0.02 |
    | `test_ink.py::test_stamp_a_2000_point_path` | plan | 16.44 | 60 | 0.02 |
    | `test_ink.py::test_wash` | plan | 44.49 | 24 | 0.04 |
    | `test_ink.py::test_building_a_sheet` | PR #6 | 78.27 | 13 | 0.08 |
    | `test_ink.py::test_the_distance_transform` | PR #6 | 15.32 | 51 | 0.02 |
    | `test_ink.py::test_stamping_a_long_stroke[dry-track]` | PR #6 | 11.97 | 81 | 0.01 |
    | `test_ink.py::test_stamping_a_long_stroke[wet-river]` | PR #6 | 15.08 | 65 | 0.02 |
    | `test_ink.py::test_stamping_a_starved_directional_brush` | PR #6 | 33.07 | 29 | 0.04 |
    | `test_ink.py::test_laying_a_wash` | PR #6 | 41.32 | 23 | 0.05 |
    | `test_ink.py::test_laying_a_wet_wash` | PR #6 | 61.98 | 19 | 0.06 |
    | `test_ink.py::test_compositing_a_stack[multiply]` | PR #6 | 13.48 | 45 | 0.19 |
    | `test_ink.py::test_compositing_a_stack[kubelka-munk]` | PR #6 | 69.48 | 15 | 0.30 |
    | `test_letters.py::test_writing_a_name_with_a_fresh_hand[centreline]` | PR #6 | 11.22 | 93 | 0.01 |
    | `test_letters.py::test_writing_a_name_with_a_fresh_hand[outline]` | PR #6 | 5.74 | 84 | 0.01 |
    | `test_letters.py::test_writing_a_name_along_a_line` | PR #6 | 11.76 | 89 | 0.01 |
    | `test_letters.py::test_writing_a_flat_block` | PR #6 | 7.76 | 136 | 0.01 |
    | `test_maps.py::test_fetch` (stage fetch) | PR #6 | 381.00 | 5 | 0.37 |
    | `test_maps.py::test_paint` (stage paint) | plan, PR #6 | 5251.30 | 5 | 5.00 |
    | `test_maps.py::test_letter` (stage letter) | PR #6 | 174.89 | 5 | 2.55 |
    | `test_maps.py::test_compose` (stage compose) | plan, PR #6 | 580.06 | 5 | 0.72 |

  - `--benchmark-enable` run of all 21: 72.1 s. `--codspeed` run locally: 105.9 s wall, 21 benchmarked.
  - First CodSpeed job time on the PR: not yet known (needs the PR); no follow-up commit yet.
  - Action pins from `git ls-remote --tags`: `CodSpeedHQ/action@v5.4.0` (checkout `v7.0.1` and setup-uv `v10.2.0` equal ci.yml's).
- 06:19 P5.4 landed (`668311b`) and verified (lint, types, YAML, smoke 18.1 s). 21 benchmarks (4 plan, 17 from PR #6), maps at display_px 450. P5.4 ticked. Opening the PR; diff review against the plan runs alongside CI.
- 06:28 PR #7 opened. Diff review: nothing blocking; one should-fix (stamp specks never reached 2 px) and two nits fixed in `92b6a6b`, verified with two fresh seeds. prerelease (3.15) segfaults on main too; diagnosis pending.
- 06:33 CI on `caeeaba`: checks 3.13/3.14, golden ubuntu/macos, mutation green. prerelease red: CPython 3.15.0b2 + numpy 2.5.2 segfault on `import numpy.random`, same on main; commented on PR #7 with a proposed uv bump (0.11.32, resolves b4), kept out of P5. CodSpeed detected 21 benchmarks.
