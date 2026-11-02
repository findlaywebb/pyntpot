# 004 — plan review

## Round 1: BLOCK

1. [BLOCKING] Case 1 is circular. span_line ends in clear_of, which returns a clear line or [] (span_clear.py:174–223), so "broken" means "empty"; 0 non-empty broken marks found. _convex_side (span_sides.py:247–248) returns the only drawn side when the other is empty, so every case-1 stretch has o = the unbroken side (asserted on all 37). Inflates % right and n at every scale; refused is always 0 and the refusal branch in curved_side can never run. Fix: amend spec before any sweep; exclude stretches where either mark is empty from n and % right, report as own count; decisive = coverage ratio only; drop refused; T3 "one broken, one not is decisive" becomes "is excluded".
2. [BLOCKING] The rule cannot reach a decision. ~5,560 px of route over 224 px windows ≈ 25 independent stretches; after fix 1, 37 coverage-decisive before the voting filter, so n ≥ 30 likely unreachable; at n = 37, n_eff ≈ 4.6 → Agresti–Coull half-width ≈ ±0.3. Fix: decide before the sweep: (a) accept likely "kept", pre-write the comment form, state #54 closes on it; or (b) justify another floor from pool counts. Either way prescribe the 1.5 n = 0 / < 30 case.
3. [SHOULD-FIX] Coverage is not biased towards the outside (endpoint feet cancel the offset bulge), but the spec says inside folds lower coverage; they don't (_drop_folds, _forward_only keep ends; only _longest_clear trims; deciles 0.15/0.57/0.71, CLEAR_KEEP_FRAC = 0.34). 3 cases had feet reversed on narrow bends, hidden by abs(). Fix: signed s_last − s_first; negative → exclude and count; replace T2's "a mark running backwards still covers its absolute span".
4. [SHOULD-FIX] T3 calls _decisive, not in the API list: declare decisive(a: MarkQuality, b: MarkQuality) -> int with hi > 1.25 * lo. Verdict needs a field for exclusion reason/case. decide(..., overlap=step/length) is not a valid default: pass length_caps and step_caps.
5. [SHOULD-FIX] Scales [i / 10 for i in range(6, 26)]; ties on round(pct, 1); multiple-of-offset check with tolerance (1.8/1.2 = 1.5000000000000002; 1.5 * SPAN_OFFSET_CAPS = 1.7999999999999998); no test asserts == 1.8.
6. [SHOULD-FIX] "Existing gates cover the tool" is partly false: 400-line budget and print/environ AST tests scan src only (_ast_checks.PACKAGES). Covering tests/: ruff T20, ruff TID banned-api, ruff D, coordinate gate, no-mock gate. Vulture is src only. Correct the claim; add wc -l check to tasks.md.
7. [SHOULD-FIX] fixture_route needs pyntpot.maps.strands (separate_strands, strand_gap_px) and pyntpot.maps.cache (MARGIN_M, LANDCOVER_MARGIN_M); name them. Skye uses 18000/18000 m, Ambleside and Y Fenni defaults.
8. [CONSIDER] T3's 120° arc at r = 60 likely gives both marks full coverage; under fix 1 an empty inside mark is excluded. Use radii below offset + clearance (~16.8 + 7 = 23.8 px at cap 14) so the inside mark is cut back but drawn.
9. [CONSIDER] The broken-outside refusal in curved_side can never run, so its docstring claim doesn't hold; belongs in a docs/issues note + issue with the SPAN_CURVE_* follow-up, not this diff. The secondary 10-cap length at scales above 2.0 breaks the spec's "at least five segments" argument; note or cap.
Passed: tracks are public-OSM-only (make_track.py from way ids; Skye --step-m 100); tests/fixtures/ placement fits (pythonpath = ["tests"], CI runs not golden); Agresti–Coull formula correct; T1 counts 43 and 18 check out. Totals from probe: 176 stretches (Ambleside 40, Skye 93, Y Fenni 43); 37 exactly one broken, 16 both broken, 37 coverage-decisive.

### Response to round 1

The user chose option (a) of finding 2: fix the plan, run the small sweep, expect to keep
1.5, and close #54 on that outcome. Findings 1 to 8 are addressed in `spec.md`, `plan.md`
and `tasks.md`. Finding 9 is listed as out-of-scope follow-ups in `spec.md`; the
coordinator files the notes and issues.

## Round 2: BLOCK

1. [BLOCKING] Coverage favours the inside by construction; the spec's "The foot of each end cancels that bulge" is false. shape_curve simplifies the stretch into chords, so the offset line's end sits on the end chord's normal, not the route's normal, tilted by half the chord angle. Outside: the end lands back inside the stretch, coverage < 1. Inside: lands past the stretch end and clamps to exactly 1.0. Isolated arcs (cap 14), clear of everything: outside 0.958 vs inside 1.0 at r=60; 0.82 vs 1.0 at r=20; 0.42–0.80 vs 1.0 at r≤16 (decisive with inside "better"). Fixtures with span_line(..., clear_px=0.0): 8 stretches decisive on geometry alone; of 35 coverage-decisive, 7 stop being decisive once geometry is normalised. Mirror image of the length bias; would push down P%. Fix (amend spec before any scoring): per side, coverage = drawn-mark coverage ÷ coverage of the same side drawn with clear_px=0.0 (with 0.0, clear_of returns the line untouched since seg_gap < 0 is never true). This "kept share" isolates the _longest_clear cut-back. If unclipped coverage ≤ 0 → reversed-feet. Reword the comment's "covers more than a quarter more of its stretch" to "keeps more than a quarter more of its own mark once cleared of the route". Record the correction of round-1 finding 3 in review.md.
2. [BLOCKING] T3's arc test fails as written. At r≈20 the arc is even (0.827 vs 1.0, ratio 1.21); at r≤16 decisive with the outside wrong. The fallback only handles an empty inside mark. Under fix 1 an isolated arc has no cut-back on either side, so it will be even. Fix: build the decisive case from a real cut-back: arc(90, r=100) plus a later strand of the same route passing within clearance of one side's mark near its end, so _longest_clear trims that side. Strand inside: decisive, outside right. Strand outside: decisive, outside wrong. Measure and pin the exact strand; drop the hand-built Verdict fallback. Add an isolated tight arc pinned as even under the normalised metric (regression test for 1).
3. [SHOULD-FIX] The pre-written comment doesn't say which old sentences go. Two survivors would contradict the result: "The single most important number here, and the one the outside-of-the-bend rule lives or dies on." and "Read coarser, the measure answers a different question and stops predicting anything." Fix: keep span_sides.py lines 97–98 up to "cap height" and lines 101–105 through "a bend that squeezes it"; delete both sentences above and everything from "Over 187 stretches" to "the argument". Add "N overlapping stretches, about N/8 independent". Prescribe the N = 0 wording. The rest of the form is a capability fact with no spec/roadmap number: good.
4. [CONSIDER] Decisive pool before voting is 35 under the round-2 case order: Ambleside 4, Skye 27, Y Fenni 4. Rule 1's "below 30" case is likely. Add one line in sweep.md that the result is mostly Skye.
Checks out: case order sound (both empty → _convex_side 0 → no-outside); clearance doesn't move the outside on all 35 decisive stretches; mouth-mark stretches negligible (1 decisive); float claims hold (0.64*1.25 == 0.8; 0.8 > 1.25*0.63; 15/10 == 1.5; 1.8/1.2 within 1e-9); decide() fully prescribed; rest of round 1 fine.
Reviewer probe scripts (reusable for geometry, not scoring): /tmp/claude-0/-home-user-pyntpot/816196dd-1fce-5506-ae3e-fb503729b021/scratchpad/probe/ (probe2.py case counts, arc.py arc search, probe3.py clearance-off asymmetry).

### Correction to round 1, finding 3

Round 1 found coverage not biased towards the outside, because the feet of the two ends
cancel the offset bulge. Round 2 shows that is false the other way: coverage is biased
towards the inside, since `shape_curve`'s chords tilt the offset line's ends. Round 1's
other points under finding 3 stand (folds keep the ends; `_longest_clear` is what trims
them; signed coverage). The bias is corrected by the kept share in round 2's fix 1.

### Response to round 2

All four findings are taken as given:

1. `spec.md`'s scoring rule now measures the **kept share**: each side's drawn coverage
   divided by the coverage of the same side drawn with `clear_px=0.0`. Unclipped coverage
   ≤ 0, or drawn coverage < 0, is `reversed-feet`. "The foot of each end cancels that
   bulge" is gone, replaced by the measured inside bias. The comment form says "keeps
   more than a quarter more of its own mark once cleared of the route".
2. T3 is built from a real cut-back: `arc(90, r=100)` plus a later strand of the same
   route near the inside mark's end (decisive, outside right) and near the outside mark's
   end (decisive, outside wrong), measured and pinned. The hand-built `Verdict` fallback is
   dropped. An isolated tight arc is pinned `even`.
3. The comment edit names the kept lines (97 up to "cap height", 101 to 105 through "a
   bend that squeezes it"), the two deleted sentences and the deleted tail. It adds
   "`N_all` overlapping stretches ... (about `N_all / 8` independent)" and prescribes the
   `N = 0` wording.
4. `sweep.md` gets one line on the decisive pool's split by fixture (mostly Skye).

## Round 3: PASS

1. [SHOULD-FIX, before scoring] Over-large kept share is ambiguous feet, not caught by the case list. On fixtures, side-values above 1: 1.0, 1.002, 1.008, 1.021, 1.124, 1.755; clamping to 1 flips 0 cases. The 1.755 (Skye) is ambiguous feet: unclipped mark 116 px with feet at 96 and 224 (start foot on another limb); drawn mark 77 px with feet at 0 and 224. The 1.124 is a genuine push (drawn 174 vs unclipped 178 px; end foot 199 → 224). Fix: add "or either side's kept share > 1.25" to the reversed-feet condition in the spec table and in kept_share in the plan; rename the case `ambiguous-feet`. No clearance pass can make a mark keep a quarter more than it had; pushes stayed within 1.124. Reuse the 1.25 literal, no new constant. Add a T2 case: drawn feet spanning > 1.25× the unclipped coverage → None. In the spec change "a value a little over 1 is recorded as measured" to "up to 1.25".
2. [CONSIDER] Give T3 the literals. Span over arc(90.0, r=100.0) (indices 0–59); continue the route from (200, 50) to (240, 50), then to (240, y), then west to (170, y), sampled every 2 px. Inside variant y = 72: kept +1 = 1.0, −1 = 0.502, decisive, o = +1, outside right (y = 70 also works, −1 = 0.631). Outside variant y = 40: kept +1 = 0.605, −1 = 1.0, decisive, o = +1, outside wrong (y = 37 also works, +1 = 0.683). Returning only to x = 190 leaves both even, so the strand must run back past the mark's end. o stays +1 throughout. Still pin both kept shares from your own run. Isolated arcs at r = 12, 14, 16, 20, 60 all give kept shares 1.0/1.0 → even (arc(120, r=16) confirmed).
3. [CONSIDER] Spec wording: under kept share the decisive pool before voting is 32 (7 drop out, 4 come in), not "smaller still by 7". Rule 1 (n < 30 at 1.5 after voting) remains likely.
Also confirmed: (b) drawn coverage < 0 → reversed-feet is sound (caught 1); (d) span_sides.py lines 97–111 on main match the branch and the comment prescription lines up (line 105 ends "…squeezes it. Read"). Case counts under kept share: decisive 32, even 88, reversed-feet 3, empty-mark 37, no-outside 16.
Reviewer probes: /tmp/claude-0/-home-user-pyntpot/816196dd-1fce-5506-ae3e-fb503729b021/scratchpad/probe/ (probe4.py, probe5.py, arc2.py, strand.py).

### Response to round 3

All three applied before any scoring: the case is renamed `ambiguous-feet` and also
catches a kept share above 1.25 (the 1.25 literal reused); T2 gains that case; T3 takes
the measured strand literals; the spec gives the pool of 32.

## Diff review: ready

Rule before results confirmed, scoring correct, comment matches `sweep.md`. Nits:

1. `span_sides.py`: re-wrap the `SPAN_CURVE_WEIGHT` comment to its neighbours' width.
   Done.
2. Wrap `sweep_span_scale.py` line 3 and `test_sweep_span_scale.py` line 1 under 100.
   Done.
3. `plan.md`: record the two deviations in `decide()` (the
   `abs(best.scale - current) > MULTIPLE_TOL` guard; `multiple` only filled on a change).
   Done.
4. `sweep.md`: say why `voted` exceeds the sum of the columns (no column for
   `no-outside`; at 1.5, 35 against 29). Done, in the reading, below the tool's output.
5. A `no-outside` column in `_table`. Skipped: it would need `sweep.md` regenerated.
6. `tasks.md`: trim the hedges on ticked lines; wrap the overlong line in `sweep.md`'s
   reading. Done.
7. Move `assert 0.64 * 1.25 == 0.8` into its own test with a one-line docstring. Done.
