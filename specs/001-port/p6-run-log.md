# P6 run log

Orchestrated run (orchestrator-mode). Branch `p6-docs`; one PR to `main`.

User instructions (2026-10-07 12:14 BST):

- Run P6 the way P5 was run (`p5-run-log.md`), orchestrator mode.
- First expand P6 in `plan.md` into slices; plan-reviewer must PASS before any code.
- No stop points: every choice follows a rule in the plan and is logged here.
- P6.2: where a design-input source cannot be recovered, cite the canonical source
  and mark it so. Fetch and check every reference.
- Branch `p6-docs`, one PR. Drive it to green CI, then publish an HTML report of
  timings, choices and findings.
- Do not merge until the maintainer says.

## Log

- 12:14 Branch `p6-docs` from `main` at `92b011c`. P6.0 (fatten P6) dispatched.
- 12:29 P6.0 plan committed (`73878bb`), 14 min planner. Slices P6.0, P6.1 inventory,
  P6.2 match design sources, P6.3 fetch, check and write `references.md`, P6.4 key test
  plus `Source:` lines, P6.5a-e docstring and src prose pass per group (ink; letters;
  maps facade/data/furniture; maps geometry/painter; maps lettering; at most 5,000 lines
  each), P6.6 docs prose pass and phase gate. Tool facts: doi.org to ACM gives 403
  (Cloudflare), Crossref API 200 with matching metadata (429 on bursts: pause and retry),
  github.com 403 but `git ls-remote` works, OpenLibrary works on retry. Plan review 1
  running.
