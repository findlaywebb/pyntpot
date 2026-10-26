# P7.V plan review 5

## Scope

This is a narrow review of "#### P7.V. Revision round 1" in `specs/001-port/plan.md` at
`f0bc454` ("P7.V0: revise the round after plan review 4", branch `p7-wip`). It checks
the four review-4 fixes (B1, B2, S1, S2) against the diff `92d7cde..f0bc454` and the
source, and looks for any contradiction the edits brought in. It does not re-review the
round, which rounds 1 to 4 covered. I checked out nothing and wrote nothing to the repo
except this file. The measurements come from a scratchpad script
(`uv run --offline python`) that builds `Sheet`s with the library's own code.

## Review-4 findings: status

| Finding | Status |
| --- | --- |
| B1 (warm and classic equal) | **Resolved.** The test now sets `paper_vignette=0.0`, `paper_foxing=0.0` and `paper_worn=0.0`, and claims "equal everywhere (to 1e-6)". Against `paper.py:47-54`, each of the three factors is then exactly `1 - 0 * x = 1`. Under the plan's warm rule, `1 - k * (1 - tint)` with `k = 0` is also exactly 1. Warm takes the same two draws in the same order. So the only things left in either plate are the base and the tooth, which are shared, and the two plates are equal bit for bit. The test still proves what it is for. |
| B2 (speck bound) | **Resolved.** The rank threshold is now "on `sheet.gran` alone", and the `0.4 + 0.6 * n120` weight "sets each speck's strength only (never its extent)", so the mask ambiguity is gone. The bound is now `2 * gran_px` across. I re-measured it over 16 seeds (0 to 15), using each component's bounding-box extent with both 4- and 8-connectivity (the two give the same answer). On 360 by 240 at `gran_px` 3, the largest speck is 3 to 5 px (at most 1.67×) against a bound of 6. On 1800 by 1457 at 22.4, it is 21 to 42 px (at most 1.88×) against 44.8, and the job sheet's seed 11 gives 21 px. The foxed share is 0.30% on every sheet, under the 1% check. `Sheet.gran` is drawn before the fibre field (`sheet.py:103-115`), so the job sheet's `paper_fibre` cannot move the specks. scipy is not installed, so the agent writes its own component labelling. Either connectivity passes. |
| S1 (smoke lock owner) | **Resolved where it matters.** P7.V6's owners now name `test_smoke.py` (`SMOKE_SHA` pen and wash) and `tests/golden/smoke/wash.webp`. A shared-files row says "P7.V6, then P7.V7b, sequential, never two at once". P7.V7b already owned "its pinned hashes", and its "every golden … that moves" covers `tests/golden/smoke/*`. The generic "and `SMOKE_SHA`, if it moves" line was not added to the engine-slice rule (plan line 6619), but I checked that no other engine slice moves the lock. The smoke basemap has `lakes=()` (`tests/support/basemaps.py`), so P7.V2's hole and winding changes are inert there. P7.V3 to P7.V5 change lettering and landmarks, which the paper, wash and pen plates do not read. P7.V7's `separate_strands` returns its input unchanged when nothing doubles back (`strands.py:76-83`), and the smoke route `40 + 30 sin(x / 260)` rises in x. So the omission cannot redden a gate. |
| S2 ("pass" read backwards) | **Resolved.** P7.V7b and P7.V11 both say "would exceed". No "would pass" is left in the section. |

## Findings

No blocker.

**[SHOULD-FIX] tasks.md contradicts decision 3 on the fern.** This is not new this
round: `tasks.md` has said it since `92d7cde`. It is not a gate failure, but P7.V7b
owns `tasks.md` and will read the line.

- **What tasks.md says.** The P7.V7b entry (`specs/001-port/tasks.md:177`) says "the
  fern keeps `"classic"` (every image but the fern regenerated)".
- **What the plan says.** Decision 3 and P7.V7b say the fern takes the new paper,
  `examples/fern.py` is not edited, and the fern's image and master are regenerated.
- **The risk.** An agent that takes the task line literally could edit `fern.py`
  (outside its owner list) or skip the fern's regeneration. The fern's docs image would
  then disagree with the regenerated master.
- **Fix.** Reword the entry to "the fern takes the new paper (every image regenerated)".
  P7.V0 can do it, or P7.V7b when it ticks the entry.

**[CONSIDER] Add the generic `SMOKE_SHA` line anyway.** Review 4 asked for "and
`SMOKE_SHA`, if it moves" in the engine-slice rule at plan line 6619. No slice needs it
as the plan stands. It would cost one clause and would cover an engine slice whose fix
turns out to reach a plate.

## No new contradiction

The new shared-files row agrees with P7.V6's and P7.V7b's owner lists and with the
order P7.V6 → P7.V7 → P7.V7b. The equality test no longer competes with the
"within 2% a tenth in" check, which review 4 measured as passing with `paper_tooth=0`.
The speck rule's "same share of every sheet whatever its `gran_px`" agrees with the
grain-relative bound. Recording the largest speck in display pixels hands the look to
P7.V13, and leaves no unit test pinned to a width-relative number.

## Verdict

**PASS.** All four review-4 fixes are correct and complete in effect, and none breaks a
slice's gate. The one should-fix (the stale fern wording in `tasks.md`) can be absorbed
by P7.V7b.
