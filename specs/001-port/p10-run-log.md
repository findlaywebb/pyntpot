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
