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
- 16:15 Plan review 4: not PASS (2 blocking, 5 should-fix, 4 nits;
  `reviews/p6-plan-review-4.md`); all round-3 findings resolved, both fix-agent rejections
  upheld. Blocking: the widened blocked-page rule also catches live non-DOI pages whose
  recorded title is a paraphrase (Stadia, ICA, Adventures in Mapping), sending ICA to
  `unreachable`; the P6.3-write brief lacks the canonical-source rule and candidate table.
  Orchestrator decision: the author-name clause applies to DOI publisher pages only, and
  P6.2's table pins match words per non-DOI page; all should-fix and nits go into the plan
  now; review 5 confirms only this round's changes.
- 16:35 Plan fixes for review 4 landed (`da8c7ce`), all 11 findings resolved. Author-name
  clause on DOI publisher pages only; non-DOI pages match on words pinned from live
  fetches (Curtis PDF, Hobbs, Stamen, Stadia, ICA, Adventures in Mapping, Urban Sketching,
  osmanyy all 200; Postman's Knock 403, words from the record and the maintainer check).
  Briefs carry the candidate table, canonical-source rule and gate definitions; an entry
  without exactly one `Implemented in:` fails. Plan review 5 (this round only) running.
- 16:50 Plan review 5: PASS (`reviews/p6-plan-review-5.md`). Two should-fix carried into
  slice briefs rather than another round: P6.4's `entries` matches only `` ## `<key>` ``
  headings and the test literal names the closing section; P6.3-write adds a `grep -c`
  check for `nib`'s "Nearest published work:" prefix. P6.0 ticked. Plan review took
  5 rounds, 12:29 to 16:50.
- 15:02 P6.1 references inventory (`specs/001-port/p6-inventory.md`), from `5299ab1`;
  started 14:34. No `src/` or `tests/` change.
  - G-here baseline on the clean `5299ab1`, per stage: `uv sync` 0 s; prek 8 s, **red**:
    `ruff-format` reformats the two Python blocks in `plan.md` (`ast_neutral.py`,
    `doc_lines.py`), every other hook passes, reformat reverted; `pytest -m "not golden"`
    158 s (1036 passed, 1 skipped, 17 deselected); `pytest -m golden --golden-tolerance`
    294 s (17 passed); `pytest -m golden` byte-exact 291 s (17 passed). `uv run prek` cannot
    spawn here (prek not in the venv), so the hooks ran as `uvx prek run --all-files`
    (prek 0.5.5). choice: log the red hook, file it, carry on | rule: no stop points; fix
    now or file (`plan.md` is not an owner file) | inputs: prek output, `git diff`.
  - Tally at `5299ab1`: 132 lines, 479 matches (as at `f6698e4`); `wet.?area` 12 matches in
    `ink/wash.py`, `ink/style.py`, `ink/shallow_water.py`, none adds a site.
  - Rows: 23, the seed's 23. Dropped: none (every seed site's body read and confirmed).
    Added rows: none. Sites added to seed rows, each choice: add site | rule: site rule |
    inputs: the body:
    - `multiply-compositing` + `pyntpot.ink.pigment.composite` (its multiply branch
      multiplies the plate over the backing) and `pyntpot.maps.compose._plates`
      (`ImageChops.multiply`, a library call it chooses and applies).
    - `lanczos` + `pyntpot.maps.compose._plates`, `_route`, `_paste_labels` (each resizes
      with `Image.Resampling.LANCZOS`; library-call clause).
    - `value-noise` + `pyntpot.ink.noise._value_noise_at` (the lattice at given
      coordinates) and `pyntpot.ink.tip._fbm1` (the same lattice built inline per octave).
    - `granulation` + `pyntpot.ink.wash.wash` (scales the density by `Sheet.pits`).
  - Not sites (callers, prose, settings, and the private parts `stamp.stamp` and
    `relief_strokes.hachures` compose): listed in the inventory's prose. choice: not a site
    | rule: site rule (a caller that only passes arguments is not a site) | inputs: bodies.
  - Decided terms, each `considered, excluded: elementary`: haversine
    (`maps/candidates/climbs.py`, `places.py`); bilinear (`ink/brush_style.py`,
    `deposit.py`, `pad.py`, `stamp.py`, `wash.py`, `maps/plates.py`, `relief.py`,
    `relief_strokes.py`); even-odd (`letters/skeleton.py`, `maps/rings.py`); scanline fill
    (`ink/raster.py`, `letters/skeleton.py`, `maps/masks.py`); flood fill (no hit); dither
    (`ink/io.py`, `maps/painter/job.py`, `painter/plates.py`, `painter/wood.py`,
    `maps/style_groups.py`); supersampling (`ink/brush_style.py`, `pad.py`, `raster.py`,
    `maps/card_geometry.py`, `style.py`, `style_groups.py`); dilation and erosion
    (`ink/noise.py`, `maps/masks.py`, `painter/cover.py`, `painter/ribbon.py`);
    `smoothstep`, linear interpolation, a clamp, a mitre limit. WCAG contrast: not a row
    (no luminance or ratio computed), closing section as `named-only`.
  - Unlisted techniques met, filed and not added (choice: file | rule: tally, technique
    in neither the seed nor the decided table | inputs: bodies, `design-sources.md`):
    pigment separation (`ink.wash.separated`), the per-bristle ink reservoir
    (`ink.deposit.spend`), the blurred-mask rim (`ink.wash.wash`'s no-flow branch).
  - Issues filed (6): `edt-is-a-chamfer-distance.md`,
    `unlisted-technique-pigment-separation.md`, `unlisted-technique-ink-reservoir.md`,
    `unlisted-technique-blurred-mask-rim.md`, `plan-code-blocks-fail-ruff-format.md`,
    `prek-not-in-the-environment.md`. Fixed: 0.
  - G-here after the change, per stage: `uv sync` 0 s; `uvx prek` 4 s, red only on the same
    `plan.md` reformat (reverted; none of this slice's files touched by any hook);
    `pytest -m "not golden"` 165 s (1036 passed, 1 skipped); `--golden-tolerance` 297 s
    (17 passed); byte-exact `pytest -m golden` 299 s (17 passed).
    `git diff --stat -- src tests` empty.
