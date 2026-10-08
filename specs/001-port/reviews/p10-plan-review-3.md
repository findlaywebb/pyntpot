# P10 plan review 3

## Scope

I reviewed `specs/001-port/plan.md` at `p10-triage` HEAD (`2cf55a9`):

- the P10 section (6024 to 7574);
- the order and ADR edits in P7 (5805 to 5827), P8 (5829 to 5845), P9 (5866 to 5871) and P11 (7575 to 7657);
- the ADR numbers table (513 to 538);
- `specs/001-port/tasks.md`.

I read them against round 2 (`reviews/p10-plan-review-2.md`), the diff `6506569..HEAD`, the run log, and the code. All checks were read-only, and I ran no golden test. I did not re-open the settled order: P10.0 to P10.2, part 1, P11, P10.R (0.0.1), P8, part 2, P7 (0.1.0), P9, with later fixes as 0.1.x.

## What I checked

**The overlap claim between P10 and P11.** An AST scan of `src/pyntpot` at HEAD finds exactly 58 underscore names that another module imports:

| Area | Count | Defining modules |
| --- | --- | --- |
| `ink` | 6 | `ink.tip` |
| `letters` | 6 | `letters.skeleton` and `letters.trace._centrelines` |
| other `maps` | 12 | |
| `maps.lettering` | 34 | |

- **No overlap.** I compared the 58 against P11's 20 promoted names by module and name. None of P11's defining modules (`ink.brush`, `ink.brush_style`, `ink.pad`, `ink.style`, `ink.pigment`, `ink.sheet`, `ink.io`, `letters.setting`, `letters.style`, `letters.nib`, `maps.cache`, `maps.providers.*`) defines one of the 58. So dropping an underscore cannot collide with a promoted name in the same module.
- **No new docstring failures.** All 58 already have docstrings, so ruff `D1xx` raises nothing new once the underscore goes.
- **Conclusion.** The claim holds.

**P10.5a against the widened surface.**

- The change is confined to `maps.lettering.pipeline.draw_plate`. P11 does not promote `draw_plate`, and P10.5a does not touch the logic of `letters/nib.py` (`nib.py:117-120`).
- `NibGroups` becomes public in P11, but P10.5a only calls it.
- So the part-1 classification survives P11.

**The ADR numbers.**

- The table (528 to 530), line 46, P9 (5868 to 5870), P10 (6377 to 6383), P11 (7617 to 7623) and `tasks.md` all agree: 0024 is P10.5b's, 0025 is P10.11's, and 0026 is P11.1's.
- `docs/decisions` holds 0001 to 0012 plus `README.md`. The README is not an index, so no file needs updating per ADR.
- No test checks that the numbers are contiguous.

**P10.3d's check.** It now names its seven lines by role, not by line number, so the merge did not make it stale. `rg` still prints exactly seven lines: `CONTRIBUTING.md:50`, and `plan.md` lines 139, 490, 5852, 5853, 6591 and 6592.

**Shared-file rows added in round 2.**

- `tests/support/lettering.py:39` says "card pixels".
- `osm.py` holds both `_open_rivers` (71) and `_osm_layers` (142).
- P10.9's owner files cover the test file that the pixel grep names.

**The release mechanics.**

- `CHANGELOG.md` holds `## [Unreleased]` and nothing else.
- P10.R's branch, tag, record commit, refused-push fallback and trusted-publisher confirmation each have exactly one prescribed path (7417 to 7475).
- The four-PR rule (6168 to 6184) matches them.

## Round 2 findings

| ID | Resolved | Note |
| --- | --- | --- |
| B1 P10.10a and `references.md` | yes | Owner files (7497 to 7501), the shared-file row (6442), and the "moves in the same commit" rule with `test_reference_keys.py` as the check (7502 to 7505). |
| B2 P11 in the order | yes | Every place where the order is stated now has P11 (numbered list 6276 to 6294, diagram 6319, legend 6326 to 6331, predecessors 6340 to 6341, P8 5831 to 5833, P9 5866, P10.R 7419 to 7426, and the `tasks.md` P8, P10 and P10.R lines). P11 starts after part 1 has merged, so no part-1 slice and no P11 slice ever hold the same file. The mechanics are prescribed: four PRs, `release-0.0.1`, and `p10-fixes` from the tag. |
| S1 rule against P10.3a | yes | 6306 to 6311. |
| S2 `CASING_COLOURS` | yes | It follows `casing` in the P8 hand-off (6361 to 6368), the no-list fallback (6370 to 6375), Q8, the fill-in table and P10.7. The brief carries no separate yes or no for it. |
| S3 pending trusted publisher | yes | The false inference is gone. The confirmation now covers a pending publisher or the reviewer on the `pypi` environment (Q14, Maintainer actions, P10.R). The tag without the `v` was weighed and rejected with a reason. The quote is attributed to `spec.md:43`. |
| S4 Q3 and Q4 evidence | yes | |
| S5 P10.R bookkeeping | yes | The tick moves to the tag record on `p10-fixes`. The branch source is given. The refused push becomes a Maintainer action. |
| N1 to N9 | yes | All nine are applied: line 46, the legend, the three table rows, `arc` in P10.6's owner files, `-I` in both greps, the vulture line for `casing`, `smooth_path` in Q6 and P10.11, the hook that rewrites `src/` stopping the slice, and the `as_dict` seed row as `defer`. |

All 16 findings are resolved.

## Fresh review

### Verdict: PASS (with carried items)

**The approach.** It is sound and now consistent end to end.

- **The part 1 and part 2 split.** The rule is correct and applied without exception. Every part-1 slice either leaves P8's `attribution=False` render alone or sits outside `src/`.
- **The P11 interaction.** P11 is placed strictly between the part-1 merge and P10.R, which removes every possible collision between a P10 slice and a P11 slice. The rename and promotion sets really are disjoint. The two runtime rules (P11.0 re-measures; P10.10 checks its fresh names against P11's) cover the case where P11's list drifts.
- **The release mechanics.** Each step has one prescribed path, and the step that cannot be undone (the tag push) has a gate that rests on a correct premise.

Nothing that remains would make a slice fail or do the wrong thing. Each item below can be carried in a slice brief or a small plan touch-up.

**The single most important thing to change.** Part 2 now starts from a `main` that P11 has reshaped. Each part-2 brief has its facts re-checked at that commit before it is dispatched (S1).

## Blocking

None.

## Should-fix (carry in the briefs or a small plan touch-up)

**S1. Part 2's facts were measured before P11, and nothing re-checks them at part 2's starting commit** (6034 to 6039, 6191 to 6195, 6290 to 6293).

- **The problem.**
  - Every fact a slice relies on was re-checked at `dd19592`. That covers the counts ("10 lines before", "about 45" vulture lines, the 58-name scan, the "32 underscore names tests import", the sizes 32, 30, 60 and 231) and the importer lists.
  - Part 2 now branches from a `main` that holds P11. P11 adds docstrings and `__all__` lists, may rename `rgb`, `plate` and `to_img` "every importer repointed", may add helpers, and may promote an underscore name under P10.10's rule (which shrinks P10.10's list).
  - The rule for the whole phase has a slice run its checks before and after, but no rule says what an implementer does when the "before" output differs from the brief. Phase P10 has no generic "stop and report on a before-check mismatch".
- **What happens.** An agent either proceeds on a stale count or improvises.
- **Fix (one bullet under "Branch and PR", item 3).** Before dispatching the first part-2 slice, the orchestrating session re-runs at `p10-fixes`'s base:
  - every part-2 slice's before-checks;
  - the P10.10 AST scan;
  - `uv run vulture --min-confidence 60 src`.

  It then updates each brief's counts and names (for example, a name P11 renamed, or a P10.10 name P11 already promoted), and records the deltas in the run log. A delta that changes what a slice *changes*, as opposed to a count, goes back for a plan fix and a reviewer pass. Separately, add to the rules for the whole phase: "a before-check whose output differs from the brief stops the slice and is reported".

**S2. After P11, "public" means `__all__`, and P10.10 does not say its renamed names stay out of it** (7477 to 7536, and Q9 at 6692 to 6705).

- **The ambiguity.**
  - P10.10's title and its row say "public names for what another module imports". Q9 (a) says such a name "is public".
  - When P10.10 runs, P11 will have pinned an `__all__` for each layer package in `tests/unit/test_public_api.py`. ADR 0007's Consequences, which P11's 0026 amends, require a new ADR for "a new public name".
- **The risk.** An agent reading "make public" against that surface may:
  - add the renamed names to `pyntpot.ink.__all__` and the others;
  - extend `test_public_api.py`;
  - or stop to write an ADR.
- **What prevents it today.** P10.10's leave-alone lists none of those files.
- **Fix.** Add to P10.10's leave-alone:
  - `src/pyntpot/{ink,letters,maps}/__init__.py` and every `__all__`;
  - `tests/unit/test_public_api.py`;
  - P11's import test for the example scripts.

  Then add one sentence: "a renamed name is module-level, not public API (ADR 0007 as amended by 0026: only names in an `__all__` are public); it joins no `__all__` or package docstring and needs no ADR". P10.2 runs before P11.0, so Q9's evidence could also say this in one clause, so that the maintainer answers knowing it. That is optional.

**S3. "Later issues" does not route issues found in P11, or fixes cut after the `p10-fixes` PR has merged** (6253 to 6268, 6181).

- **P11 is not covered.** Issues are routed if found "in P10's own slices or in P7 to P9". P11 now runs inside P10's span, and is not listed. A defect P11 surfaces has no stated home: a P10 row, or P11's own record.
- **The second gap.** A slice cut after the `p10-triage` PR has merged "joins part 2 whatever it reaches (part 2 still lands before P7.4)". But "Both part-2 PRs merge before P7.1 starts". So a `fix` row found during P7.1 to P7.3 joins a part 2 that has already merged, and it has no branch or PR.
- **Fix.**
  - Add P11 to the list ("in P10's own slices, in P11, or in P7 to P9").
  - Add: "a slice cut after the `p10-fixes` PR has merged lands on its own branch `p10-late-<id>` from `main`, through its own PR, before P7.4".

## Nits

1. **`tasks.md` P9 order line.** It reads "after P7.4, P8 and P10 (both parts)", while plan P9 (5866) now adds P11. P11 is implied, because P7.4 follows P11, but make the two match.
2. **"P10 against P11", first bullet (6401 to 6403).** "The orchestrating session stops and puts it to the maintainer as a later `decide` row" contradicts "Later issues" ("a new `decide` row after P10.2 does not open a second stop"). Say whose stop it is. For example: "P11.0 leaves the name out of its list, and the row stands `defer` until answered". Or: "P11.0 stops; this is P11's stop, not P10's".
3. **P11.0's brief.** P11's own "Order" paragraph states only the other side of the rule ("a part-2 slice that would rename or delete a name P11 has made public needs its own ADR and stops"). The P11.0 planner learns the "promote under P10.10's name" rule only by following a cross-reference into P10. Copy that bullet into P11's sketch, or require P11.0's brief to carry it.
4. **P10.R's `CHANGELOG.md`.** It assumes `## [Unreleased]` is empty. If P11, or anything after it, adds entries there, then under Keep a Changelog they belong under `## [0.0.1]`. Add: "entries already under Unreleased move into the 0.0.1 section".

## Counts

- 0 blocking.
- 3 should-fix:
  - S1: re-check part 2's facts after P11.
  - S2: P10.10's renamed names stay out of `__all__` and need no ADR.
  - S3: "Later issues" routes issues found in P11, and fixes cut after `p10-fixes` merges.
- 4 nits.

Verdict: PASS
