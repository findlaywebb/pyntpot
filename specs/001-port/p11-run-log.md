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
- Plan review 3: BLOCK, 0 blockers, 1 major, 3 minors. N1 confirmed: the import sweep was
  re-run against each slice's own worktree state, and a cold import of all 106 `MODULES`
  with group 1 and the `paper_plate` move applied finds no cycle. Probes hold (tokens,
  shared values, `rgb`). R3-M1: ADR 0026 claims its token list is complete, but it misses
  the `brush_overrides` parameter keys, the `aux` keys and some class keys; the fix states
  the rule as the contract and gives the tokens as examples. Minors: `WashStyle` is an
  `ink` style; `grep -rlw` matches `.pyc` files; a sentence on ADR 0007's "free to move".
  Fix round 3 dispatched to a fresh agent.
- Fix round 3 (a fresh agent). R3-M1: ADR 0026 states the rule as the contract (any string
  a public name reads or returns as a key or enumerated value is public); the tokens are
  examples, and the missing families are added, measured at `ff752f6`: 15 override
  parameter keys, 2 `aux` keys, 7 `brushes` class keys, 3 `brush_width_px` keys, 3
  `river_curve` keys, 15 `pigment_transparency` keys. No completeness claim is left.
  R3-m1 to R3-m3 fixed (`--include=*.py` on 8 greps). Plan review 4 dispatched.
- Plan review 4: BLOCK, 0 blockers, 1 major, 0 minors. R3 findings resolved; counts re-run
  and matching; with 245 `.pyc` files present, all 12 greps print what the plan says.
  R4-M1: the widened token rule reaches theme TOML keys (so it contradicts "`RouteInk.effect`
  may be deleted freely") and OSM tags (it collides with P10.7's `tunnel=no` fix). Fix: a
  token is a string a caller passes to a public name, or an enumerated string a public name
  or field returns; field names follow the member rule; fetched provider data is not a
  token. Fix round 4 dispatched to a fresh agent.
- Fix round 4 (a fresh agent). R4-M1: the token rule is narrowed to strings a caller passes
  to a public name (as an argument, or a key or value inside one, the class keys of a style
  object the caller builds included) and enumerated strings a public name or field returns;
  field names and the TOML keys that mirror them follow the member rule; fetched provider
  data is not a token. Every family stays (pigment keys because callers subscript
  `PIGMENTS` and `TRANSPARENCY`). Deleting the `effect` tables or `Label.as_dict` and the
  `tunnel=no` fix need no ADR; renaming the `"map"` ink key does. Plan review 5 dispatched.
- Plan review 5: PASS, 0 blockers, 0 majors, 3 minors (R5-m1 `RouteInk.effect` is kept by
  P10.7 and Q8, not deleted; R5-m2 dict entries are tokens only through a field of a class
  in some `__all__`; R5-m3 "to choose a behaviour" restored, so free values such as colours
  are not tokens). All three applied by a fresh agent, and the rule text is now identical in
  its three places. Reviews: five rounds (1 blocker, 6 majors and 11 minors; then 2 majors
  and 5 minors; 1 and 3; 1 and 0; 0 and 3).
- P11.0 landed: `Fatten P11 into slices` (plan.md +1403/-76, tasks.md, `p10-triage.md`'s
  `letters-map-ink-key` row). Slices: P11.1 (sequential foundation); group 1: P11.2a,
  P11.2b, P11.3 and P11.4 in parallel; group 2: P11.5a (after 2a and 2b), P11.5b (after 2a,
  2b and 3), P11.5c (after 4).
- P11.1 landed (implementer in a detached worktree at `994b854`). Baseline
  `{"commit": "994b854aeac021952b6b53c75f4c6e2e3ff5d407", "dirty": false}`. Red step:
  "examples import a private or disallowed name: ['examples/scratch.py:1']" (line 1 only).
  Gates: `ruff format --check .` (314 files) and `ruff check .` pass; prek all-files and
  on the new files pass; not-golden 1051 passed, 1 skipped; golden in tolerance 18 passed;
  golden byte-exact 18 passed; G-self 18 passed (byte-identical). Deviations:
  `LETTERS_PUBLIC` is on one line (ruff format folds a one-item tuple); the ADR names no
  phase or slice ids; two ty fixes in the harness (`isinstance` check on `main`'s return,
  `getattr(node, "lineno", "?")`); about 340 changed lines, not 170, nearly all the
  prescribed ADR. No rebase was needed (the head had not moved), so the gates ran on the
  landed tree.
