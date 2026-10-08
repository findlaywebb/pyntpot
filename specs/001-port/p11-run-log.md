# P11 run log

Orchestrating session's log for P11 (widen the public API for primitive-first tutorials),
then P10.R (tag 0.0.1). Branch `p11-public-api`, cut from `main` at `ff752f6` (PR #9, P10
part 1, merged).

- 2026-10-08. Start. Read plan.md "### P11", "P10 against P11", "#### P10.R", "### P3 and
  P4: how to run a slice"; `p10-run-log.md` (tail) and `p10-triage.md`.
- Mutation run on `main` after the part-1 merge: run 37854572820 at `ff752f6`, success,
  "counts: killed 59, timeout 1, survived 12, suspicious 0, no_tests 0, segfault 0",
  "mutation score 0.8333 (advisory)". Recorded in `p10-run-log.md`; the `tasks.md:124` row
  in `p10-triage.md` marked fully done.
- AST-neutral script extracted verbatim from plan.md P6 "AST-neutral check" to
  `$SCRATCH/p11-scripts/ast_neutral.py`, with `SHA256SUMS` beside it; at `ff752f6` it prints
  "AST-neutral: 0 files".
- G-self baseline on the clean starting commit, before any edit:
  `PYTHONPATH=tests uv run python tests/golden/make_golden.py "$SCRATCH/before"`:
  `{"commit": "ff752f6ff122e12b29edc8a6f6b117056529d202", "dirty": false}`, 1 min 36 s.
- P11.0 dispatched to a plan author in a detached worktree at `ff752f6`. Maintainer
  (2026-10-08): "Optimise plan and implementation for sub agent parallelisation"; relayed to
  the author: parallel lines with disjoint owner files, a rule per shared file, per-slice
  G-self baselines in each worktree, and an order diagram.
- Maintainer (2026-10-08): "File clashes can be manned with working trees and conflicts
  resolved when merging". Relayed to the P11.0 author: parallel slices may share files,
  each in its own worktree; the orchestrating session resolves conflicts at each merge, by
  a merge rule per shared file the plan states, then re-runs G-here on the merged branch and
  G-self against the slice's own baseline. No slice relies on another parallel slice's
  unlanded edits, and a rename repoints all of its importers in the same slice.
- P11.0 draft from the plan author, in the worktree at `ff752f6` (uncommitted): plan.md
  +796/-74, tasks.md. Slices: P11.1 foundation (ADR 0026, the pins for each layer's
  `__all__`, the examples harness); parallel group 1: P11.2a (`ink` marks and pigment,
  `Layer` to `PigmentLayer`), P11.2b (`paper_plate` moved to `ink/paper.py`, new helper
  `save_image`), P11.3 (`letters`, `plate` to `nib_plate`), P11.4 (`maps` cache and
  providers); parallel group 2: P11.5a, P11.5b and P11.5c (the example scripts), then a phase
  gate. 21 names promoted, none of them top-level. No name left out; no `decide` row.
  Plan-reviewer, round 1, dispatched.
- Plan review 1: BLOCK, 1 blocker, 6 majors, 11 minors. B1: G-here never lints new
  untracked files (prek passes tracked files only). M1: `maps/painter/plates.py` shared by
  P11.2a and P11.2b with no merge rule. M2: unnamed owner files, and docstrings not
  prescribed. M3: `paper_plate` promoted with a thin contract. M4: the lettering and
  composition steps are not prescribed. M5: the route-map test is network-free only when it
  passes. M6: promoting `Setting` and `Mark` makes the deferred `"map"` ink key public.
  Checks that held: importer counts, names and signatures, the 58 P10.10 pairs, ty and
  `_SCANNED` with `examples`, G-self across the `paper_plate` move, coverage headroom
  (ink and letters 96.08, maps 93.30). Fix round 1 dispatched to a fresh agent.
- Fix round 1 (a fresh agent): all 18 findings addressed, none kept against the review.
  B1: P11's G-here runs `ruff format --check .` and `ruff check .` before prek. M1: a merge
  rule for `plates.py`. M2 and M3: "Docstrings, decided"; `paper_plate`'s `plate` parameter
  becomes `canvas`. M4: seven exact steps for lettering and composition. M5: the
  route-map test asserts the cache key and its entries first, with providers at `budget=0`
  and loopback endpoints. M6: option (a); ADR 0026 records the `"map"` key as public, and
  renaming it needs its own ADR and a maintainer stop (`p10-triage.md` row updated). Plan
  review 2 dispatched to a fresh reviewer, told that P11.0 is the branch's first plan
  commit, not its first commit.
- Plan review 2: BLOCK, 0 blockers, 2 majors, 5 minors; of round 1's 18 findings, 16 are
  resolved and 2 partly. Re-run probes held: ruff on an untracked example; route-map cache
  key `f173b2f7a20bb9d4`, and with `budget=0` providers the full map paints with no request
  (99 s); every `paper_plate` caller passes the canvas positionally; the seven-step
  lettering sequence passes ty and ruff and runs in under 2 s. N1: P11.2b's test imports
  `PaperStyle` from `pyntpot.ink`, which only P11.2a exports, so P11.2b is red in its own
  worktree. N2: ADR 0026's "one such token" is false, and its membership rule leaves
  unclear whether classes reached only through attributes are public, which collides with
  the deferred P10 rows (`RouteInk.effect`/`casing`, `Label.as_dict`). The reviewer
  removed a stray worktree it had made at `/home/user/r2sim` (confirmed gone). Fix round 2
  dispatched to a fresh agent.
- Fix round 2 (a fresh agent). N1: P11.2b's test imports from the defining modules; every
  parallel slice now imports promoted names from their defining modules (the sweep found
  no other miss). N2(a): ADR 0026 lists every token that crosses the surface, measured at
  `ff752f6` (4 ink keys or a `#rrggbb` colour, 6 `Mark.role` roles, 2 `label_route` values,
  3 `Setting.align` edges, 112 brush sheet ids and 6 override keys, 15 pigment keys,
  `OpenTopoData`'s `dataset`). N2(b): ADR 0007 does not make classes reached through an
  attribute public, so the rule is "public = names in a public module's `__all__`";
  `RouteInk` and `Label` are not public, and the deferred P10 rows need no ADR. Minors
  fixed. Plan review 3 dispatched to a fresh reviewer.
