# P10 plan review 2

## Scope

I reviewed `specs/001-port/plan.md`, section `### P10. Triage and address the
port's issues`, at `6506569` (lines 6020 to 7454). I also reviewed the P7, P8 and P9
order edits (5804 to 5867), the ADR table (513 to 533), and `specs/001-port/tasks.md`.
I read them against round 1 (`reviews/p10-plan-review-1.md`), the run log, and the
code. Line numbers are those at `6506569`.

The branch has since moved on to `4649245`:

- It merged `main`'s P11 sketch (`39f67bd`), which adds 78 lines after P10.11 and two
  lines in P7. Lines after 5822 are therefore 2 higher at HEAD.
- The P10 section itself is unchanged.
- The newest run-log entry queues a P11 order note "for the next plan-fix round".

P10.1 will run against the branch head, not against `6506569`, so that merge is in
scope where it changes P10's order (B2).

## What I checked

All checks were read-only. I ran no golden test.

**P10.3d's check.** `rg -n -U -i "no\s+(co-authorship\s+)?trailers" CONTRIBUTING.md specs/001-port/plan.md` prints exactly the seven lines the slice names: `CONTRIBUTING.md:50`, and `plan.md` lines 139, 490, 5848, 5849, 6519 and 6520.

**P10.5a.** Through the public API it cannot move a pixel:

- `letter` calls `draw_plate(plates, placed, spans, strands, style)` with no `route` (`lettering/pipeline.py:118`).
- `Hand.route = route or face.label_route` (`letters/hand.py:59`), so `replace(style.face, label_route=hand.route) == style.face` on that path.
- `draw_plate` is not exported (`maps/__init__.py`).
- The new test is red today, because the narrowing applies to `role == "glyph"` (`nib.py:117-120`).

**P10.3a.** It cannot move P8's hash:

- `compose` calls `draw_attribution` only `if attribution:` (`maps/pipeline.py:166`).
- P8's verification render passes `attribution=False` (plan 5839-5841).

**The version is pinned nowhere else.** `0.1.0` appears only in `pyproject.toml:3` and in `uv.lock:732`.

- `__version__` and the two User-Agent strings read the installed metadata.
- No cache key uses the version.
- `test_public_api.py:43` checks only that the major part is a digit.

**The release mechanics.**

- `CHANGELOG.md` holds only `## [Unreleased]`.
- `uv lock --check` exists in uv 0.11.32.
- `publish.yml` matches the plan: tags `v*`, `environment: pypi`, `id-token: write`, `uv build`, `pypa/gh-action-pypi-publish@release/v1`. It creates no GitHub release.
- The repository is public (`gh api repos/findlaywebb/pyntpot`), so the `git+https` dependency line works without credentials.
- No tag exists.

**ADRs.** `docs/decisions` holds 0001 to 0012. No test checks that the numbers are contiguous, so writing 0024 or 0025 before 0013 to 0023 is harmless.

**Counts that re-checked.**

| Claim | Result |
| --- | --- |
| `edt` sites | 8 `src` files and 6 test modules |
| `point_to_segment` | only its definition and its docstring mention |
| Non-canonical terms | 10 grep lines |
| "card pixel" | 60 `src` lines in 22 files, and 7 test lines |
| "rule seven" | 3 lines |
| Q10 "sheet" in scope | 52 non-`Sheet` lines in 15 files, and the allowed list is exactly the `placement_names.py:172` `log.info` line plus the `ink.sheet` import |
| `docs/` and "card pixel" | Neither "card pixel" (Q2 (1)) nor "display pixel" (Q2 (2)) appears outside `issues/` and `decisions/`, so the P10.9 check can pass |
| `tests/unit/ink/test_deposit.py` | does not exist yet |
| The route constants | `RouteInk.casing` reads `CASING_COLOURS` (`style_groups.py:288`) |
| `pyntpot.ink.tip._fbm1` | cited in `references.md` lines 66 and 72, and imported by `ink/stamp.py:24` |

## Round 1 findings

| ID | Resolved | Note |
| --- | --- | --- |
| B1 parallel marks against the table | yes | Part 1 is now a strict chain where files are shared (P10.4a/P10.3c, then P10.4b, P10.5a, P10.9). Part 2 runs P10.5b then P10.7. The `test_spans.py` line 64 edit happens once, in P10.9. The `;` legend is stale (nit 2). |
| B2 P9 against P10, and ADR numbers | yes | "P10 against P9 and P7" (6349). ADR numbers are fixed at 0024 and 0025 in the table (528-529) and in P9 (5863-5867). Line 46 is stale (nit 1). |
| B3 "P8's list" | yes | "P8's hand-off" (6316-6340) names the writer, location, format, re-triage and the no-list case. The no-list case has a new contradiction (S2). |
| S1 Q12 | yes | Always asked, as a conditional (6649-6657, 6218-6221). |
| S2 Q1 framing | yes | The answer is itself the instruction. The `CLAUDE.md` line is under Maintainer actions (6692-6694). |
| S3 Q7 (C) | yes | Recommended. P10.3c's leave-alone carves out `edge-darkening`'s `Implemented in:` line. |
| S4 Q8 evidence, `CONSUMER_ONLY` | yes | D6 and D21 are in Q8. `CONSUMER_ONLY` and its pin are in P10.7's leave-alone, and the slice says "one sentence". |
| S5 P10.9 scope and check | yes | Scoped to the issue. The counts and the allowed list are verified above. |
| S6 P10.3d check | yes | Mechanical. The seven lines are verified. |
| S7 slices that need no answer start after P10.1 | yes | 6300-6303, plus the interim trailer rule (6155-6161). |
| S8 README badge | yes | Q13. |
| S9 P10.10 and ADRs | partly | `docs/decisions/**` is now in the leave-alone. The second half, dropping `references.md` from P10.10a, rested on a false premise of round 1 ("no entry cites an `ink.tip` name"), and it now breaks P10.10a (B1). |
| S10 who runs P10.1, P10.2 and P10.R | yes | 6117-6119. |
| N1 `SpanSurroundings.dark` | yes | |
| N2 100 columns | yes | |
| N3 place names | yes | Watersmeet, Malham Cove, Dovedale, Cat Bells, Exe and Tay. |
| N4 `ink-reservoir` duplicate | yes | Differently from round 1's suggestion, but the duplicate is gone. |
| N5 0.28 named | yes | |
| N6 P10.4a coverage | yes | |
| N7 areas defined | yes | |
| N8 "includes" | yes | |
| N9 trailer count commit | yes | |
| N10 two `place_spans` calls | yes | |
| N11 which commit ticks | yes | |

## Fresh review

### Verdict: BLOCK

The approach is sound, and the maintainer's order is applied consistently in P7, P8,
P9, P10, the ADR table and `tasks.md` as of `6506569`. The part 1 and part 2
classification is right: no part-1 slice can change the P8 render's PNG hash. Two
blockers remain:

- One is a regression from round 1's fix round.
- The other is the P11 merge, which leaves P10.R and P8 ordered before a phase that
  must precede them.

The single most important change is to **put P11 between part 1 and P10.R everywhere
the order is stated**, and to fix the branch and PR mechanics that follow from that.

## Blocking

**B1. P10.10a cannot pass its own gate under Q9 (a): renaming `_fbm1` breaks `references.md`, which it may not edit.**
Plan 7385-7389 (owner files) and the `references.md` row at 6370.

- **What fails.** P10.10a's six `ink` names are those `ink/stamp.py:24` imports from `ink.tip`: `_fbm1`, `_smooth_path`, `_spread`, `_tip_band`, `_tip_drift` and `_unfold`.
- `references.md` cites `pyntpot.ink.tip._fbm1` in two `Implemented in:` lines: `value-noise` (line 66) and `fbm` (line 72).
- `test_every_site_cites_its_key` fails with "Implemented in: paths that resolve to no site" once the name moves (`test_reference_keys.py:132-136`).
- P10.10's owner list says `references.md` is "(P10.10c only ...)". So the P10.10a implementer either edits outside its ownership or stops.
- **Fix.**
  - Owner files: `docs/explanation/references.md` for P10.10a (the `value-noise` and `fbm` lines, for `ink.tip._fbm1`) and P10.10c (the three `compose` sites).
  - Add P10.10a to the shared-file table's `references.md` row, between P10.4b and P10.10c.
  - Add to P10.10's body: "every `Implemented in:` path naming a renamed name moves in the same commit; `test_reference_keys.py` is the check".

**B2. After the P11 merge, P10 still tags 0.0.1 and starts P8 straight after part 1; P11 requires both to wait for it.**
At HEAD:

- plan.md P11 "Order" says "P8 should still start after P11", and P11 runs after P10.1 and before P7.1.
- `tasks.md` P11 says "P8 starts after it".
- The run log's last entry says "the order becomes P10.0 to P10.2, part 1, P11, P10.R, P8, part 2, P7, P9".

**Where P10 contradicts this.**

| Location (at `6506569`) | What it says |
| --- | --- |
| Numbered order (6259-6270) | omits P11 |
| Diagram (6284-6295) | omits P11 |
| P10.R's predecessor (7323-7326) | "every part-1 slice", with no P11 |
| P10.R's commit | "the last commit on `p10-triage`" |
| P8's order paragraph (5828-5832) | omits P11 |
| `tasks.md` P10 and P8 order lines | omit P11 |

An orchestrator following P10 tags `v0.0.1` before P11 exists. P8 then migrates
against a surface without P11's names, which defeats P11's stated reason for the order.

**Why the mechanics break as well.**

- P10.R's version commit cannot be the last commit of the `p10-triage` PR if P11 must land on `main` between part 1 and the tag.
- P11 shares files with part 1 if it starts early (it only has to start after P10.1):
  - `GLOSSARY.md` is P10.9's.
  - The module docstrings of promoted names are also edited by part 1 or P10.10; for example `letters/nib.py` is edited by P10.4b and P10.9.
  - `plan.md`: P11.0 adds an ADR-table row, and P10.3d edits the "P3 and P4" slice rule a few lines above it.

**Fix.** Apply the recorded order in every place listed above.

- **The order.** P10.0 to P10.2, part 1 (landed), P11 (all slices), P10.R, P8, part 2, P7, P9.
- **P11's start.** It starts after part 1 has landed, so no part-1 slice and no P11 slice ever hold the same file. Otherwise list the shared files in the table.
- **P10.R's mechanics.** Prescribe one. For example:
  - the `p10-triage` PR merges part 1 without the version commit;
  - P11 lands through its own PR;
  - P10.R's version commit then goes on a short `release-0.0.1` branch through its own PR;
  - the tag goes on the `main` commit that holds it.
- **The PR count.** Update the "Branch and PR" rule (6162-6169) to match.

## Should-fix

**S1. The rule that splits the parts contradicts P10.3a's placement** (6260-6263 against 6272-6282).

- **The conflict.** The rule says "a slice is in part 2 if it changes a branch that an upstream call of the public API can take and that can change a rendered PNG". `compose(..., attribution=True)` under a style with `labels=False` is such a branch, so by the rule P10.3a is part 2. Yet the list puts every release blocker in part 1.
- **Why it matters.** P10.3a is safe for P8 only because P8's hash render passes `attribution=False`, and the plan never says so. A "Later issues" slice classified "by the rule that splits them" (6249-6250) gets no guidance when it is a release blocker.
- **Fix.** Add one sentence to the rule: "A release blocker is part 1 if it cannot change P8's verification render (`compose(..., attribution=False)` on the upstream's activity). P10.3a qualifies because `compose` calls `draw_attribution` only when `attribution` is true. A release blocker that could change that render goes to part 2 and still lands before P7.4."

**S2. The route-constant rules delete `CASING_COLOURS` while keeping `RouteInk.casing`, which reads it** (6330-6340, 6603-6611, against 7197-7198).

- **The no-list fallback.** It says "the four constants ... (`ROUTE_INK`, `ROUTE_EFFECT_OFF`, `ROUTE_SHADOW`, `CASING_COLOURS`) are deleted, and `RouteInk.casing` ... becomes `defer`". That breaks `casing` (`style_groups.py:288`, `return CASING_COLOURS.get(named, named)`).
- **The likely case.** The per-name rule ("delete if the list does not name it") does the same when the record names `casing`. The record cannot name the private `CASING_COLOURS` without a D21 breach. So the orchestrator writes "`CASING_COLOURS`: yes" into the brief.
- **The result.** P10.7's body then says "`CASING_COLOURS` stays whenever `casing` does". The brief contradicts the slice, and `ty` goes red if the brief wins.
- **Fix.** In "P8's hand-off", the fallback and Q8, say: "`CASING_COLOURS` follows `RouteInk.casing`: kept, deferred or deleted with it. The three other constants are decided per name." In the fallback, "the four constants" becomes "`ROUTE_INK`, `ROUTE_EFFECT_OFF` and `ROUTE_SHADOW`".

**S3. Q14 and P10.R infer "no trusted publisher exists" from "not on PyPI". That inference is false, and the step it guards cannot be undone** (6672-6679, 7354-7362).

- **Why it is false.** A *pending* trusted publisher can be registered for a project name that does not exist yet. That is exactly what reading (2) tells the maintainer to do.
- **The risk.** If one was ever registered for `pyntpot` / `publish.yml` / `pypi`, pushing `v0.0.1` under Q14 (1) publishes 0.0.1 and claims the name, against the maintainer's answer.
- **What gates it.** Only the maintainer's tag confirmation, and the plan primes that confirmation with the false premise.
- **Fix.**
  - Replace "so no trusted publisher exists yet" with "whether a pending trusted publisher is registered could not be checked from this session".
  - Under Q14 (1), the P10.R confirmation asks: "confirm no pending trusted publisher for `pyntpot` is registered on PyPI (or that the `pypi` environment requires your approval)".
  - Alternatively, weigh a tag that `publish.yml` ignores, such as `0.0.1` without the `v`. D11 asks only for "a git tag". That removes both the failed Publish run and the risk.
- **Also.** The quote "git tag until PyPI" is from spec D11 (`spec.md:43`), not from P8's text.

**S4. Q3's evidence no longer holds under the adopted order, which tilts the question** (6544-6548, and Q4 at 6551-6552).

- **The stale reasoning.** Reading (1) of Q3 says "an upstream label with an uncovered character would move the P8 hash". But P10.5b is now part 2, after P8, so it cannot move P8's hash. Q4 (1) leans on the same reasoning ("the goldens and the upstream hash were made with it").
- **Fix.**
  - Restate Q3 (1) as "0.28 is the ported literal (D5); under (2) an upstream label with an uncovered character renders differently from 0.1.0 on (part 2 runs after P8, so P8's hash is unaffected)".
  - In Q4 (1), drop "and the upstream hash".

**S5. P10.R's bookkeeping after the merge has no home** (7345-7348, 6162-6169, 6322).

- **Ticked before done.** P10.R ticks its `tasks.md` line in the version commit, before the maintainer has confirmed or the tag exists.
- **No branch for the record.** "The tag push is recorded in the run log, and P8 does not start until the run log records it". But by then `p10-triage` has merged, and the plan does not say on which branch that entry lands.
- **Where `p10-fixes` comes from.** The plan never says where it branches from, although the P8 hand-off record is its first commit.
- **A refused push.** No fallback is given if the proxy refuses `git push origin v0.0.1`.
- **Fix.** Combine with B2's mechanics:
  - `p10-fixes` branches from `main` at the tagged commit or later.
  - Its first bookkeeping commit records the tag (name, commit, Publish run URL and result) and ticks P10.R.
  - A refused tag push becomes a Maintainer action ("push `v0.0.1` at `<sha>`").

## Nits

1. **Line 46.** "0003 to 0023 are assigned" becomes "0003 to 0025" (and P11's number once P11.0 fixes it).
2. **6297.** The legend explains `;`, which no longer appears in the diagram. Describe `├`/`┬` branches as "may run in parallel worktrees", and `─` as a sequence.
3. **The shared-file table (6355-6375)** says "every row" but omits some shared files. The diagram already orders them, but list them:
   - `tests/unit/maps/lettering/test_draw_plate.py`: P10.5a, then P10.5b.
   - `src/pyntpot/maps/osm.py`: P10.7 (`_open_rivers` docstring), then P10.10c (`_osm_layers`).
   - `tests/support/lettering.py`: P10.9, under Q2 (line 39 says "card pixels"), then P10.6 (it confirms the docstring).
4. **P10.6 (7098-7100).** `tests/support/lettering.py::arc` is under leave-alone with "confirm it still reads true". Its docstring equates side +1 with `(-dy, dx)`, which is `route_turn`'s sign, not the drawn side P10.6 defines. If it does not read true, the slice has to come back. Move it to the owner files with "reword only if it names the drawn side; it describes `route_turn`'s sign".
5. **P10.9 rule seven (7273).** `grep -rniE "rule (seven|7)\b" src tests` also matches the `.pyc` in `__pycache__`. Use `grep -rnIiE`.
6. **P10.7 (7192).** `\.casing\b` does not match `def casing`, so the grep alone does not list the property before. Say that the vulture line is the check for `casing`.
7. **P10.11 and Q6.** Both name `_smooth_path`, which P10.10a renames under Q9 (a) before P10.11. Say that P10.11's brief uses the name after P10.10a.
8. **P10.3b.** If a hook rewrites a file under `src/`, G-self and the AST-neutral check apply. Say so, or "a hook that rewrites `src/` stops the slice" (P6 ran the hooks green, so none is expected).
9. **The `as_dict` seed row (6438)** carries three conditional outcomes, but P10.1 writes one outcome per row. Write it as Q8's row is written: `defer` ("awaiting what upstream reads") until P8's hand-off re-triages it.

## Counts

- 2 blocking:
  - B1: P10.10a renames `_fbm1`, which `references.md` cites, and may not edit `references.md`.
  - B2: P11 is missing from P10's order, so P10.R and P8 come before it, and the branch and PR mechanics are unspecified.
- 5 should-fix: S1 to S5.
- 9 nits.

Verdict: BLOCK
