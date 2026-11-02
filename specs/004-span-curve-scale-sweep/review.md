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
