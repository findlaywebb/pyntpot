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
