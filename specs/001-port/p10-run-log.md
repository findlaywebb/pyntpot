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
- Maintainer on phase order (2026-10-07): "maybe we split these into multiparty so we do
  most of p10 now, 0.0.1+ as the release, then p8, then the rest of p10, then the p7
  docs, then the 0.1.0, then p9". Also: "0.1.0 can be candidate release and then 0.1.x
  can be fixes". Adopted the split: P10 part 1 (release blockers and every fix no
  upstream render can reach), tag 0.0.1, P8 against 0.0.1, P10 part 2 (fixes an upstream
  render may reach, private-name renames, golden group), P7 docs and 0.1.0, then P9.
  Plan-fix round 1 dispatched with this order and the review-1 findings.
- Plan fixes for review 1 landed (`6506569`), all 24 findings resolved and the phase
  order applied. Fix-agent choices kept: rule-seven test text moves to P10.9 (part 1, so
  `test_spans.py` line 64 is edited once); P10.R sets `version = "0.0.1"` plus `uv lock`
  and a CHANGELOG entry, and P7.4 sets 0.1.0; a `v*` tag runs `publish.yml`, and
  `pyntpot` is not on PyPI, so Q14 asks tag-only (recommended) or PyPI; ADRs 0024 and
  0025 fixed for P10.5b and P10.11. Plan review 2 running.
- Merged `main` (`1bae755`, the P11 sketch: widen the public API) into `p10-triage`;
  conflicts in the P7 order lines and the P10/P11 task lists kept both sides. Notes from
  the P7/P11 session, for the next plan-fix round: (1) P10 must claim its ADR numbers
  explicitly (it does: 0024 for P10.5b, 0025 for P10.11), so P11 takes the next free
  above those; (2) a P10 rename of a name P11 makes public is simpler before P11. P11's
  "Order": after P10.1, before P7.1, and P8 starts after it, so 0.0.1 (P10.R) comes
  after P11 and the order becomes P10.0 to P10.2, part 1, P11, P10.R, P8, part 2, P7, P9.
- Plan review 2: BLOCK (2 blocking, 5 should-fix, 9 nits; `reviews/p10-plan-review-2.md`);
  23 of 24 round-1 findings confirmed resolved, S9 partly. Blocking: P10.10a renames
  `ink.tip._fbm1`, which `references.md` cites, without owning `references.md`; P11 is
  not yet in P10's order. Plan-fix round 2 dispatched with the review-2 findings and the
  P11 integration (order part 1, P11, P10.R, P8, part 2; ADR claim; renames P11 touches
  move before P11).
