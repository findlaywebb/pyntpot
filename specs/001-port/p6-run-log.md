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
- 12:52 Plan review 1: BLOCK (4 blocking, 8 should-fix, 9 nits; `reviews/p6-plan-review-1.md`).
  Blocking: AST-neutral check rejects an added docstring; the Args/Returns rule would add
  about 2,300 boilerplate lines and push five files over 400; the reference format has no
  line for a design input and its "not verified" check can never fail; design inputs with
  no DOI or URL have no lookup route. Orchestrator decision for the fix agent: Args/Returns
  sections only on the top-level public API and only where they say something the
  signature and summary do not; everything else fixes accuracy and shape only.
- 13:05 Maintainer agreed the Args/Returns rule: type hints carry most of what those
  sections would say, and more documentation is not better documentation.
- 13:20 Plan fixes for review 1 landed (`278982d`), all 21 findings resolved. AST-neutral
  check proven on a scratch clone: added docstring exits 0, `- a` to `- (a + 0)` exits 1.
  Fix-agent additions kept: a fourth status `named-only` for a closed list of design
  inputs with no title or identifier; `value-noise` canonical source is Lewis 1989;
  `wcag-contrast` dropped from the inventory (no code computes contrast); the
  `shallow-water` site corrected to `pyntpot.ink.shallow_water.shallow_water`.
  Args/Returns under the agreed rule: at most 73 lines, under 30 expected, no file within
  150 lines of 400. Plan review 2 running.
- 13:48 Plan review 2: BLOCK (2 blocking, 4 should-fix, 8 nits; `reviews/p6-plan-review-2.md`);
  all 21 round-1 findings confirmed resolved. Blocking: `not-verified` can never clear for
  two design inputs (Postman's Knock behind a Cloudflare 403; the p5-watercolor README names
  no title or author); the jargon gate's "0 to rewrite" is unreachable because the detector
  flags code identifiers P6 may not rename. Orchestrator decisions for the fix agent: an
  archived snapshot (web.archive.org) is a check route; a repository is checked by
  `git ls-remote` plus its README describing the technique; a final logged status
  `unreachable` is allowed on design-input lines only (never on a canonical-source line)
  after every route fails, and the report lists each one; the jargon gate covers docstring
  and comment lines only, each finding rewritten or logged as kept with its reason.
- 14:05 Maintainer checked the two design inputs that the proxy cannot fetch (screenshots,
  2026-10-07). Plan fix agent told to add a `maintainer-checked` route (design-input lines
  only, never canonical-source lines).
  - axelinternet, p5-watercolor (https://github.com/axelinternet/p5-watercolor): owner
    `axelinternet` (Axel Hultman), About "p5 implementation of Tyler Hobbs generative
    watercolor simulation", README heading "Watercolor canvas" linking Hobbs's guide;
    last commit about 8 years ago (about 2018); contributors axelinternet, mkontogiannis.
    Matches the entry: implementation of the Hobbs method.
  - maintainer-checked: https://github.com/axelinternet/p5-watercolor | 2026-10-07 | owner axelinternet (Axel Hultman); About and README: p5 implementation of Tyler Hobbs generative watercolor simulation; last commit about 2018
  - The Postman's Knock, *Illustrated Wedding Maps*
    (https://thepostmansknock.com/illustrated-wedding-maps/): author Lindsey Bugbee,
    13 March 2014. Title, author and year match. The process section is behind a paywall
    (TPK Premium), so the extent idiom (trim to a blob, bleed the edge) is not visible on
    the page: metadata matched, technique not confirmed from the text.
  - maintainer-checked: https://thepostmansknock.com/illustrated-wedding-maps/ | 2026-10-07 | Illustrated Wedding Maps, Lindsey Bugbee, 13 March 2014; process section paywalled, technique not confirmed
- 14:30 Plan fixes for review 2 landed (`3cb46e6`), all 14 findings resolved. Archive and
  repository routes added; statuses `unreachable` and `maintainer-checked` barred from
  canonical-source lines; `maintainer-checked` passes only when the URL is in this log.
  Repository year rule: last-commit year, written "(2018, last commit, approximate)".
  Jargon gate fed docstring and comment text only by a `doc_lines.py` (ast + tokenize):
  findings across `src/` drop from 36 to 18. MoXi DOI kept as `10.1145/1186822.1073221`
  (SIGGRAPH 2005 Papers; `10.1145/1073204.1073221` is the TOG 24(3) record of the same
  paper). Probes: Postman's Knock 403, Wayback API 429 through full backoff, direct
  snapshot resets; p5-watercolor `ls-remote` exit 0, raw README 200. P6 section now
  about 1,300 lines. Plan review 3 running.
- 14:40 Maintainer: about 1,300 lines of P6 plan is fine for the orchestrator to follow
  and hand out as sub-steps to parallel sub-agents. Reviewer 3 told to judge single
  slices only, and whether P6.5a-e can run in parallel worktrees.
- 15:10 Plan review 3: BLOCK (2 blocking, 5 should-fix, 1 consider, 3 nits;
  `reviews/p6-plan-review-3.md`); all 14 round-2 findings confirmed resolved. Blocking:
  the match table wrongly says no code implements a wet-area bleed (`pyntpot.ink.wash.wash`
  does, lines 218-230) and that `blob` occurs only in `letters/`; Elsevier answers 200
  with a "Redirecting" stub for Chaikin, Catmull-Rom and Borgefors, so route 2 never
  falls through and those lines stay `not-verified`. Orchestrator decisions: add the
  wet-area-bleed seed row (Luft and Deussen as design input); a publisher page whose body
  does not contain the title counts as blocked and falls through to the index routes;
  P6.5a-e run in parallel worktrees (no hard-coded paths, own scratch dir each, glossary
  changes and run-log entries handed back to the orchestrator, who applies them);
  `maintainer-checked` is bound to log lines carrying an explicit marker, not to any
  URL in the log. S4 and S5 go into the plan too.
- 15:45 Plan fixes for review 3 landed (`b6e5dd5`), all 11 findings resolved. New row
  `wet-area-bleed` (canonical: Luft and Deussen 2006, `10.1145/1124728.1124732`; sites
  `ink.wash.wash` and `maps.painter.cover.wet_field`; Curtis as design input). Blocked-page
  rule widened: a 200 page also counts as blocked when its body lacks every author's family
  name (Elsevier's stub carries the title inside a script). Probes: Chaikin, Catmull-Rom,
  Borgefors each 200 stub, then Crossref 200 and a match: `verified-via-index`. P6.3 split
  into fetch and write sub-agents; P6.5a-e parallel in worktrees. `maintainer-checked`
  bound to marker lines; the two 14:05 checks carry them. Plan review 4 running.
