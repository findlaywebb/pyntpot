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
- 12:43 Plan review 1: BLOCK (4 blocking, 8 should-fix, 9 nits; `reviews/p6-plan-review-1.md`).
  Blocking: AST-neutral check rejects an added docstring; the Args/Returns rule would add
  about 2,300 boilerplate lines and push five files over 400; the reference format has no
  line for a design input and its "not verified" check can never fail; design inputs with
  no DOI or URL have no lookup route. Orchestrator decision for the fix agent: Args/Returns
  sections only on the top-level public API and only where they say something the
  signature and summary do not; everything else fixes accuracy and shape only.
- 12:50 Maintainer agreed the Args/Returns rule: type hints carry most of what those
  sections would say, and more documentation is not better documentation.
- 12:56 Plan fixes for review 1 landed (`278982d`), all 21 findings resolved. AST-neutral
  check proven on a scratch clone: added docstring exits 0, `- a` to `- (a + 0)` exits 1.
  Fix-agent additions kept: a fourth status `named-only` for a closed list of design
  inputs with no title or identifier; `value-noise` canonical source is Lewis 1989;
  `wcag-contrast` dropped from the inventory (no code computes contrast); the
  `shallow-water` site corrected to `pyntpot.ink.shallow_water.shallow_water`.
  Args/Returns under the agreed rule: at most 73 lines, under 30 expected, no file within
  150 lines of 400. Plan review 2 running.
- 13:11 Plan review 2: BLOCK (2 blocking, 4 should-fix, 8 nits; `reviews/p6-plan-review-2.md`);
  all 21 round-1 findings confirmed resolved. Blocking: `not-verified` can never clear for
  two design inputs (Postman's Knock behind a Cloudflare 403; the p5-watercolor README names
  no title or author); the jargon gate's "0 to rewrite" is unreachable because the detector
  flags code identifiers P6 may not rename. Orchestrator decisions for the fix agent: an
  archived snapshot (web.archive.org) is a check route; a repository is checked by
  `git ls-remote` plus its README describing the technique; a final logged status
  `unreachable` is allowed on design-input lines only (never on a canonical-source line)
  after every route fails, and the report lists each one; the jargon gate covers docstring
  and comment lines only, each finding rewritten or logged as kept with its reason.
- 13:24 Maintainer checked the two design inputs that the proxy cannot fetch (screenshots,
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
- 13:28 Plan fixes for review 2 landed (`3cb46e6`), all 14 findings resolved. Archive and
  repository routes added; statuses `unreachable` and `maintainer-checked` barred from
  canonical-source lines; `maintainer-checked` passes only when the URL is in this log.
  Repository year rule: last-commit year, written "(2018, last commit, approximate)".
  Jargon gate fed docstring and comment text only by a `doc_lines.py` (ast + tokenize):
  findings across `src/` drop from 36 to 18. MoXi DOI kept as `10.1145/1186822.1073221`
  (SIGGRAPH 2005 Papers; `10.1145/1073204.1073221` is the TOG 24(3) record of the same
  paper). Probes: Postman's Knock 403, Wayback API 429 through full backoff, direct
  snapshot resets; p5-watercolor `ls-remote` exit 0, raw README 200. P6 section now
  about 1,300 lines. Plan review 3 running.
- 13:29 Maintainer: about 1,300 lines of P6 plan is fine for the orchestrator to follow
  and hand out as sub-steps to parallel sub-agents. Reviewer 3 told to judge single
  slices only, and whether P6.5a-e can run in parallel worktrees.
- 13:38 Plan review 3: BLOCK (2 blocking, 5 should-fix, 1 consider, 3 nits;
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
- 13:59 Plan fixes for review 3 landed (`b6e5dd5`), all 11 findings resolved. New row
  `wet-area-bleed` (canonical: Luft and Deussen 2006, `10.1145/1124728.1124732`; sites
  `ink.wash.wash` and `maps.painter.cover.wet_field`; Curtis as design input). Blocked-page
  rule widened: a 200 page also counts as blocked when its body lacks every author's family
  name (Elsevier's stub carries the title inside a script). Probes: Chaikin, Catmull-Rom,
  Borgefors each 200 stub, then Crossref 200 and a match: `verified-via-index`. P6.3 split
  into fetch and write sub-agents; P6.5a-e parallel in worktrees. `maintainer-checked`
  bound to marker lines; the two 13:24 checks carry them. Plan review 4 running.
- 14:17 Plan review 4: not PASS (2 blocking, 5 should-fix, 4 nits;
  `reviews/p6-plan-review-4.md`); all round-3 findings resolved, both fix-agent rejections
  upheld. Blocking: the widened blocked-page rule also catches live non-DOI pages whose
  recorded title is a paraphrase (Stadia, ICA, Adventures in Mapping), sending ICA to
  `unreachable`; the P6.3-write brief lacks the canonical-source rule and candidate table.
  Orchestrator decision: the author-name clause applies to DOI publisher pages only, and
  P6.2's table pins match words per non-DOI page; all should-fix and nits go into the plan
  now; review 5 confirms only this round's changes.
- 14:28 Plan fixes for review 4 landed (`da8c7ce`), all 11 findings resolved. Author-name
  clause on DOI publisher pages only; non-DOI pages match on words pinned from live
  fetches (Curtis PDF, Hobbs, Stamen, Stadia, ICA, Adventures in Mapping, Urban Sketching,
  osmanyy all 200; Postman's Knock 403, words from the record and the maintainer check).
  Briefs carry the candidate table, canonical-source rule and gate definitions; an entry
  without exactly one `Implemented in:` fails. Plan review 5 (this round only) running.
- 14:33 Plan review 5: PASS (`reviews/p6-plan-review-5.md`). Two should-fix carried into
  slice briefs rather than another round: P6.4's `entries` matches only `` ## `<key>` ``
  headings and the test literal names the closing section; P6.3-write adds a `grep -c`
  check for `nib`'s "Nearest published work:" prefix. P6.0 ticked. Plan review took
  5 rounds, 12:29 to 14:33 (2 h 4 min).
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
- 15:05 Orchestrator correction: the entries from 12:43 to 14:33 were first stamped with
  estimated times (12:52 to 16:50), not read from a clock. They are now restamped from
  their commit times (BST). The 13:24 entry's own text and the plan reviewers' briefs
  quoted the old stamps (14:05, 15:10, 15:45); they mean 13:24, 13:38 and 13:59. From here
  every entry's time is read from `date` when it is written.
- 15:03 P6.1 verified and ticked (`b2f56c5`). The red `ruff-format` hook was P6.0's: the
  plan's two script blocks were unformatted, so `ruff format --check .` (a CI step) failed.
  Fixed in `14286ba` (formatting only: `ast.dump` identical for `ast_neutral.py` and
  `doc_lines.py`; the plan's "14:05" references now 13:24); the issue file is removed.
  Orchestrator check: format and lint clean. P6.2 dispatched.
- 15:18 P6.2 match the design sources to the inventory, from `7c5d482`; started 15:03,
  wall time 15 min (G-here 13 min of it). No `src/` or `tests/` change. Owner files:
  `p6-inventory.md` (design-input column), `spec.md` (open question moved to "Resolved
  questions"), this log. Every `design-sources.md` entry is in the match table (33
  bullets); none outside it.
  - Matches, each `rule: match table | inputs: design-sources.md`:
    - choice: Curtis et al. 1997 -> `edge-darkening`, `backruns`, `granulation`,
      `shallow-water` (the canonical source above); `kubelka-munk`, `wet-area-bleed`
      (own `Design input` line, grail URL)
    - choice: Van Laerhoven, Van Reeth 2005 -> `kubelka-munk`
    - choice: Bousseau et al. 2006 -> `edge-darkening`
    - choice: Luft, Deussen -> `wet-area-bleed` (the canonical source above)
    - choice: Chu, Tai 2005 (MoXi) -> `bristle-brush`
    - choice: Baxter, Lin 2004 -> `bristle-brush`
    - choice: Kubelka, Munk 1931 -> `kubelka-munk` (the canonical source above)
    - choice: Deegan et al. -> `backruns` (`named-only` `deegan-coffee-ring`)
    - choice: 2019 arXiv drying study -> `backruns` (`named-only` `arxiv-watercolour-drying`)
    - choice: Lee, wet-on-wet -> `shallow-water` (`named-only` `lee-wet-on-wet`)
    - choice: WetBrush -> `shallow-water` (`named-only` `wetbrush`)
    - choice: Tyler Hobbs 2017 -> `midpoint-displacement`
    - choice: axelinternet, p5-watercolor -> `midpoint-displacement` (status
      `maintainer-checked`)
    - choice: Horn 1981 -> `hillshade` (the canonical source above)
    - choice: Douglas, Peucker 1973 -> `douglas-peucker`; Chaikin 1974 -> `chaikin` (each
      the canonical source above)
    - choice: Lanczos resampling (named) -> `lanczos` (not recorded)
    - choice: Zhang, Suen 1984 (named in the code) -> `zhang-suen` (not recorded)
    - choice: Marching squares (named in the code) -> `marching-squares` (not recorded)
    - choice: Euclidean distance transform; fBm and value noise (named in the code) ->
      `chamfer-distance`, `fbm`, `value-noise` (not recorded)
    - choice: Stamen, *Watercolor process* -> `multiply-compositing`, `box-blur`,
      `edge-darkening`
    - choice: osmanyy.com, *Risograph CSS* -> `multiply-compositing`
    - choice: Stadia Maps, ICA MapCarte 95/365, Adventures in Mapping 2024, Urban
      Sketching World, The Postman's Knock -> closing
    - choice: OSM via Overpass; OSM tagging; OpenTopoData SRTM; Open-Elevation; Patrick
      Hand; Caveat; SVG filter effects; CSS mix-blend-mode; WCAG AA; walk-guide maps;
      researcher search terms; MapTiler and Stadia notes -> closing (`named-only`)
  - Rows with no table line, each choice: `original design reading not recorded; the
    canonical source stands in.` | rule: P6.2 match rule (row the table gives no line) |
    inputs: match table, inventory: `catmull-rom`, `hachures`, `nib`, `label-placement`;
    with the six "not recorded" rows above, 10 rows carry that line. P6.1 added no row,
    so no `design-input-for-<key>.md` issue.
  - Design inputs per row: `kubelka-munk` 3, `multiply-compositing` 2, `zhang-suen` 1,
    `douglas-peucker` 1, `chaikin` 1, `catmull-rom` 1, `marching-squares` 1, `lanczos` 1,
    `value-noise` 1, `fbm` 1, `chamfer-distance` 1, `box-blur` 1, `hillshade` 1,
    `hachures` 1, `midpoint-displacement` 2, `edge-darkening` 3, `backruns` 3,
    `granulation` 1, `shallow-water` 3, `wet-area-bleed` 2, `bristle-brush` 2, `nib` 1,
    `label-placement` 1 (equal to `refcheck.sh`'s `inputs` list).
  - Closing section, 17 lines in `design-sources.md` order: Stadia Maps, "Stamen
    Watercolor" (to fetch); ICA, "MapCarte 95/365: Pictorial Guide to the Lakeland Fells
    by Alfred Wainwright, 1955-1966" (to fetch); Adventures in Mapping, "Tolkien Style
    Maps in a GIS: part 3, Water" (to fetch); Urban Sketching World, "Urban Sketching
    Examples: Line and Wash" (to fetch); The Postman's Knock, "Illustrated Wedding Maps"
    (`maintainer-checked`); `named-only`: `osm-overpass`, `osm-tagging`,
    `opentopodata-srtm`, `open-elevation`, `patrick-hand`, `caveat`, `svg-filter-effects`,
    `css-mix-blend-mode`, `wcag-aa-contrast`, `walk-guide-maps`,
    `researcher-search-terms`, `maptiler-stadia-notes`. By status: 12 `named-only`, 1
    `maintainer-checked`, 4 assigned by P6.3's fetch.
  - Corrections, pinned citation fields that differ from `design-sources.md` (rule:
    match table, pinned page words; inputs: P6.2's table): Hobbs title "A Guide to
    Simulating Watercolor Paint with Generative Art" (case), author Hobbs, T.; Stamen
    title "Watercolor Process", author Watson, Z. (Stamen Design), year 2012 added;
    Stadia title "Stamen Watercolor" (record: "Stamen Watercolor style docs"), (n.d.);
    ICA title "MapCarte 95/365: Pictorial Guide to the Lakeland Fells by Alfred
    Wainwright, 1955-1966" (record: "A Pictorial Guide ..., Alfred Wainwright, 1955 to
    1966"), author "ICA Commission on Map Design" (record: "ICA Map Design Commission");
    Adventures in Mapping title "Tolkien Style Maps in a GIS: part 3, Water" and author
    Nelson, J. added; Urban Sketching title "Urban Sketching Examples: Line and Wash"
    (record: "Line and wash"), (n.d.); Postman's Knock title "Illustrated Wedding Maps"
    (case), author Bugbee, L., 2014 added; osmanyy title "Risograph.css" (record:
    "Risograph CSS"), author Osman, year 2025 added.
  - Greps behind the table, re-run at `7c5d482`, every count as pinned (no
    `match-table-evidence.md`):
    - `grep -rniIE 'wet.?area' src`: 11 lines, `ink/wash.py` 4, 142, 159, 164, 199, 309;
      `ink/shallow_water.py` 44, 66; `ink/style.py` 109, 115, 119.
      `sed -n '218,219p;228,230p' src/pyntpot/ink/wash.py`:
      `rim = rim * (1.0 - o.wet * o.rim_drop)` and
      `dens = dens * (1.0 - m_wet) + blur(dens, o.bleed_px) * m_wet`.
      `grep -n 'wet_map\|def wet_field' src/pyntpot/maps/painter/cover.py`: 32, 95, 104.
    - `grep -rliIE 'blob' src | wc -l`: 16 (15 `.py` and `maps/themes/default.toml`);
      `grep -rniIE 'blob' src | wc -l`: 48.
    - `grep -rnE '\bstarve\b|run_px|dip_px|pen_starve' src/pyntpot/ink/brush.py`: first
      four lines `starve` 191, `run_px` 192, `dip_px` 194, `pen_starve` 202.
    - `grep -rniIE 'luminance' src`: 2 lines, `ink/io.py:54`, `maps/painter/plates.py:42`.
  - Issues filed: 0. Fixed: 0. No case outside a rule.
  - G-here after the change, per stage: `uv sync` 0 s; `uv run prek` cannot spawn (as at
    P6.1, `prek-not-in-the-environment`), so `uvx prek run --all-files` 4 s, green, no
    file touched; `pytest -m "not golden"` 161 s (1036 passed, 1 skipped, 17
    deselected); `--golden-tolerance` 294 s (17 passed); byte-exact `pytest -m golden`
    304 s (17 passed). `git diff --stat -- src tests` empty.
- 15:19 P6.2 verified and ticked (`bef4d29`). P6.3-fetch dispatched.
- 15:30 P6.3-fetch (steps 1 to 3), from `bef4d29`; started 15:19. No repository file
  changed except this log. `$SLICE` =
  `/tmp/claude-0/-home-user-pyntpot/81b07070-1ea4-5527-9ae2-48b727070240/scratchpad/p6.3/`;
  bodies under `$SLICE/refs/` (`<key>-<n>.{html,json,pdf,md,txt}`, headers beside each as
  `.hdr`), every attempt in `$SLICE/attempts.tsv`. Requests 15:20:55 to 15:28:44 BST, wall
  time 7 min 49 s (whole slice 15:19 to 15:30, 11 min). 73 requests (72 `curl`, 1
  `git ls-remote`), 5 answered 429 (all the Wayback availability API), 8 connection
  resets (OpenLibrary 3, Wayback snapshot 5). Pacing: one request at least 2 s after the
  last, never two at once; backoff 5, 10, 20, 40 s on 429, 5xx or reset.
  `grep -cE '^ *- maintainer-checked: https?://'` on this log printed `2` before the run.
  - choice: fetch a work once when several keys cite it (Curtis 1997 canonical for
    `edge-darkening`, `backruns`, `granulation`, `shallow-water`; Strassmann 1986 for
    `bristle-brush` and `nib`; the Curtis PDF for `kubelka-munk` and `wet-area-bleed`;
    Stamen for `multiply-compositing`, `box-blur`, `edge-darkening`), log one source line
    and one evidence row per key, each naming the shared saved body | rule: step 1 (one
    line per source); pacing rule | inputs: candidate table, P6.2 match table.
  - choice: a canonical source given only as a DOI is checked against the identity the
    plan's tool facts give it (author family names and year; title where the design
    record or tool facts give one), and its citation fields are the Crossref record's,
    case kept as the record gives it | rule: Source line (fields the record gives);
    *Match* | inputs: tool facts, Crossref records.
  - choice: IEEE `doi.org` answers 202 with an empty body after redirects, counted as
    blocked | rule: route 2 (a page is blocked when its status is not 200) | inputs:
    `box-blur-1.html`, `hillshade-1.html`, `bristle-brush-6.html` (0 bytes each).
  - choice: no route 7 for any source but The Postman's Knock: every other own page
    either verified at route 1 or was a DOI publisher page that route 2 verified, and
    p5-watercolor verified at route 5 | rule: route 7 (only when routes 2 to 6 did not
    verify) | inputs: the bodies below.
  - choice: the 16 `named-only` works and the fixed `the canonical source above.` (9
    lines) and `not recorded` (10 lines) design inputs are not fetched | rule: step 1;
    fixed design-input lines | inputs: P6.2 match table.
  - kubelka-munk | Kubelka, Munk 1931 (canonical) | none (no DOI, URL, title or ISBN;
    route 6 through Kubelka 1948) | n/a | route 6 | first author Kubelka, year 1931,
    volume 12, first page 593, venue "Zeits. f. tech. Physik" by abbreviation of
    "Zeitschrift für technische Physik" | venue taken from the citing reference; title,
    initials and last page in no record | 0
    - attempt | https://doi.org/10.1364/JOSA.38.000448 | 200 at https://opg.optica.org/josa/abstract.cfm?uri=josa-38-5-448 (`kubelka-munk-1.html`, 200,727 bytes; folded title 10, `kubelka` 19, `1948` 14)
    - attempt | https://api.crossref.org/works/10.1364%2FJOSA.38.000448 | 200 (`kubelka-munk-2.json`: "New Contributions to the Optics of Intensely Light-Scattering Materials Part I", Kubelka, Paul, 1948, *Journal of the Optical Society of America* 38(5), 448; 8 references, R4 `{"first-page":"593","volume":"12","author":"Kubelka","year":"1931","journal-title":"Zeits. f. tech. Physik"}`)
    - evidence | kubelka-munk | Canonical source | Kubelka; Munk (1931). *Zeitschrift für technische Physik* 12, 593. | none | verified-via-index | cited in the reference list of Kubelka 1948, https://doi.org/10.1364/JOSA.38.000448, whose Optica page 200 shows its title, author and year, by first author, year, journal, volume and first page; second author from the design record; title, initials and last page in no fetched record, so not cited | 2026-10-07
  - kubelka-munk | Curtis et al. 1997, grail PDF (design input) | https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf | 200 | route 1 | PDF words `computer generated watercolor` 4, `curtis` 1, `anderson` 1, `seims` 1, `fleischer` 1 (as `fleischery`), `salesin` 4 (`pdftotext` to `kubelka-munk-3.txt`); `1997` 0 | year from the design record, not shown on the page | 0
    - attempt | https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf | 200 (`kubelka-munk-3.pdf`)
    - evidence | kubelka-munk | Design input | Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997, year from the design record, not shown on the page). Computer-Generated Watercolor. | https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf | verified | PDF 200, title and every author in the text | 2026-10-07
  - kubelka-munk | Van Laerhoven, Van Reeth 2005 (design input) | https://api.crossref.org/works?query.bibliographic=Van+Laerhoven+Van+Reeth+Real-time+simulation+of+watery+paint&rows=5&... | 200 | route 3, then route 2 | first hit `10.1002/cav.95`: title folds equal, year 2005, authors Van Laerhoven, Van Reeth | title U+2010 in "Real‐time" written as ASCII hyphen (dash rule); venue, volume, issue, pages and initials added from the record | 0
    - attempt | https://api.crossref.org/works?query.bibliographic=Van+Laerhoven+Van+Reeth+Real-time+simulation+of+watery+paint&rows=5&select=DOI,title,subtitle,issued,author,container-title,event | 200 (`kubelka-munk-4.json`; five hits: 10.1002/cav.95 "Real‐time simulation of watery paint" 2005; 10.1145/1187112.1187187 "Real-time simulation of thin paint media" 2005; 10.1109/cgi.2004.1309281 "Real-time watercolor painting on a distributed paper model" null; 10.1007/s00371-007-0144-5 "From dust till drawn" 2007; 10.1002/cav.406 "Paint‐on‐glass animation ..." 2011)
    - attempt | https://doi.org/10.1002/cav.95 | 403 at https://onlinelibrary.wiley.com/doi/10.1002/cav.95, `<title>Just a moment...`, `cf-mitigated: challenge` (`kubelka-munk-5.html`)
    - attempt | https://api.crossref.org/works/10.1002%2Fcav.95 | 200 (`kubelka-munk-6.json`)
    - evidence | kubelka-munk | Design input | Van Laerhoven, T.; Van Reeth, F. (2005). Real-time simulation of watery paint. *Computer Animation and Virtual Worlds* 16(3-4), 429-439. | https://doi.org/10.1002/cav.95 | verified-via-index | Crossref record by bibliographic search, publisher page 403 challenge | 2026-10-07
  - multiply-compositing | W3C Compositing and Blending Level 1 (canonical) | https://www.w3.org/TR/compositing-1/ | 200 | route 1 (standard) | `<title>` "Compositing and Blending Level 1"; `<p id="w3c-state">` "W3C Candidate Recommendation Draft", `<time class="dt-updated" datetime="2024-03-21">21 March 2024` | none | 0
    - attempt | https://www.w3.org/TR/compositing-1/ | 200 (`multiply-compositing-1.html`)
    - evidence | multiply-compositing | Canonical source | W3C (2024). Compositing and Blending Level 1. W3C Candidate Recommendation Draft, 21 March 2024. | https://www.w3.org/TR/compositing-1/ | verified | page 200, title and w3c-state W3C Candidate Recommendation Draft, updated 2024-03-21 | 2026-10-07
  - multiply-compositing | Stamen, *Watercolor process* (design input) | https://stamen.com/watercolor-process-3dd5135861fe/ | 200 | route 1 | `watercolor process` 28, `zach watson` 2, `stamen` 270; `<title>` "Watercolor Process | Stamen"; `article:published_time` 2012-03-26 | pinned title, author and year as P6.2 logged | 0
    - attempt | https://stamen.com/watercolor-process-3dd5135861fe/ | 200 (`multiply-compositing-2.html`)
    - evidence | multiply-compositing | Design input | Watson, Z. (Stamen Design) (2012). Watercolor Process. | https://stamen.com/watercolor-process-3dd5135861fe/ | verified | page 200 with its pinned words, published 2012-03-26 | 2026-10-07
  - multiply-compositing | osmanyy.com, *Risograph CSS* (design input) | https://osmanyy.com/projects/risograph-css/ | 200 | route 1 | `risograph css` 22, `osman` 25, `2025` 9; `<title>` "Risograph.css — Osman&#39;s Workshop"; `article:published_time` 2025-07-03 | pinned title, author and year as P6.2 logged | 0
    - attempt | https://osmanyy.com/projects/risograph-css/ | 200 (`multiply-compositing-3.html`)
    - evidence | multiply-compositing | Design input | Osman (osmanyy.com) (2025). Risograph.css. | https://osmanyy.com/projects/risograph-css/ | verified | page 200 with its pinned words, published 2025-07-03 | 2026-10-07
  - zhang-suen | `10.1145/357994.358023` (canonical) | https://doi.org/10.1145/357994.358023 | 403 | route 2 | title, authors Zhang, Suen, year 1984 | none | 0
    - attempt | https://doi.org/10.1145/357994.358023 | 403 at https://dl.acm.org/doi/10.1145/357994.358023, `<title>Just a moment...`, `cf-mitigated: challenge` (`zhang-suen-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F357994.358023 | 200 (`zhang-suen-2.json`)
    - evidence | zhang-suen | Canonical source | Zhang, T. Y.; Suen, C. Y. (1984). A fast parallel algorithm for thinning digital patterns. *Communications of the ACM* 27(3), 236-239. | https://doi.org/10.1145/357994.358023 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - douglas-peucker | `10.3138/FM57-6770-U75U-7727` (canonical) | https://doi.org/10.3138/FM57-6770-U75U-7727 | 403 | route 2 | authors Douglas, Peucker, year 1973 | the design record's "Line simplification" is a description, not a title; title and venue from the record (record's capitals kept) | 0
    - attempt | https://doi.org/10.3138/FM57-6770-U75U-7727 | 403 at https://utppublishing.com/doi/10.3138/FM57-6770-U75U-7727, `cf-mitigated: challenge` (`douglas-peucker-1.html`)
    - attempt | https://api.crossref.org/works/10.3138%2FFM57-6770-U75U-7727 | 200 (`douglas-peucker-2.json`)
    - evidence | douglas-peucker | Canonical source | DOUGLAS, D. H.; PEUCKER, T. K. (1973). ALGORITHMS FOR THE REDUCTION OF THE NUMBER OF POINTS REQUIRED TO REPRESENT A DIGITIZED LINE OR ITS CARICATURE. *Cartographica* 10(2), 112-122. | https://doi.org/10.3138/FM57-6770-U75U-7727 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - chaikin | `10.1016/0146-664X(74)90028-8` (canonical) | https://doi.org/10.1016/0146-664X(74)90028-8 | 200 stub | route 2 | title, author Chaikin, year 1974 | none | 0
    - attempt | https://doi.org/10.1016/0146-664X%2874%2990028-8 | 200 at https://linkinghub.elsevier.com/retrieve/pii/0146664X74900288, `<title>Redirecting`, 2,655 bytes, folded title 1, `chaikin` 0, so blocked (`chaikin-1.html`)
    - attempt | https://api.crossref.org/works/10.1016%2F0146-664X%2874%2990028-8 | 200 (`chaikin-2.json`)
    - evidence | chaikin | Canonical source | Chaikin, G. M. (1974). An algorithm for high-speed curve generation. *Computer Graphics and Image Processing* 3(4), 346-349. | https://doi.org/10.1016/0146-664X(74)90028-8 | verified-via-index | Crossref record, publisher page 200 stub without authors | 2026-10-07
  - catmull-rom | `10.1016/B978-0-12-079050-0.50020-5` (canonical) | https://doi.org/10.1016/B978-0-12-079050-0.50020-5 | 200 stub | route 2 | title, authors Catmull, Rom, year 1974 | none (record title in capitals, kept) | 0
    - attempt | https://doi.org/10.1016/B978-0-12-079050-0.50020-5 | 200 at https://linkinghub.elsevier.com/retrieve/pii/B9780120790500500205, `<title>Redirecting`, 2,666 bytes, folded title 1, `catmull` 0, `rom` 0, so blocked (`catmull-rom-1.html`)
    - attempt | https://api.crossref.org/works/10.1016%2FB978-0-12-079050-0.50020-5 | 200 (`catmull-rom-2.json`; `book-chapter`, no volume or issue)
    - evidence | catmull-rom | Canonical source | Catmull, E.; Rom, R. (1974). A CLASS OF LOCAL INTERPOLATING SPLINES. *Computer Aided Geometric Design*, 317-326. | https://doi.org/10.1016/B978-0-12-079050-0.50020-5 | verified-via-index | Crossref record, publisher page 200 stub without authors | 2026-10-07
  - marching-squares | `10.1145/37402.37422` (canonical, the 2-D case) | https://doi.org/10.1145/37402.37422 | 403 | route 2 | authors Lorensen, Cline, year 1987 | none | 0
    - attempt | https://doi.org/10.1145/37402.37422 | 403 at https://dl.acm.org/doi/10.1145/37402.37422, `cf-mitigated: challenge` (`marching-squares-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F37402.37422 | 200 (`marching-squares-2.json`)
    - evidence | marching-squares | Canonical source | Lorensen, W. E.; Cline, H. E. (1987). Marching cubes: A high resolution 3D surface construction algorithm. *ACM SIGGRAPH Computer Graphics* 21(4), 163-169. | https://doi.org/10.1145/37402.37422 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - lanczos | `10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2` (canonical) | https://doi.org/10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2 | 403 | route 2 | author Duchon, year 1979 | none | 0
    - attempt | https://doi.org/10.1175/1520-0450%281979%29018%3C1016%3ALFIOAT%3E2.0.CO%3B2 | 403 at https://journals.ametsoc.org:443/view/journals/apme/18/8/1520-0450_1979_018_1016_lfioat_2_0_co_2.xml, "ERROR: The request could not be satisfied" (`lanczos-1.html`)
    - attempt | https://api.crossref.org/works/10.1175%2F1520-0450%281979%29018%3C1016%3ALFIOAT%3E2.0.CO%3B2 | 200 (`lanczos-2.json`)
    - evidence | lanczos | Canonical source | Duchon, C. E. (1979). Lanczos Filtering in One and Two Dimensions. *Journal of Applied Meteorology* 18(8), 1016-1022. | https://doi.org/10.1175/1520-0450(1979)018<1016:LFIOAT>2.0.CO;2 | verified-via-index | Crossref record, publisher page 403 | 2026-10-07
  - value-noise | `10.1145/74334.74360` (canonical) | https://doi.org/10.1145/74334.74360 | 403 | route 2 | title "Algorithms for solid noise synthesis", author Lewis, year 1989 | none | 0
    - attempt | https://doi.org/10.1145/74334.74360 | 403 at https://dl.acm.org/doi/10.1145/74334.74360, `cf-mitigated: challenge` (`value-noise-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F74334.74360 | 200 (`value-noise-2.json`)
    - evidence | value-noise | Canonical source | Lewis, J. P. (1989). Algorithms for solid noise synthesis. *ACM SIGGRAPH Computer Graphics* 23(3), 263-270. | https://doi.org/10.1145/74334.74360 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - fbm | `10.1137/1010093` (canonical) | https://doi.org/10.1137/1010093 | 403 | route 2 | authors Mandelbrot, Van Ness, year 1968 | none | 0
    - attempt | https://doi.org/10.1137/1010093 | 403 at https://epubs.siam.org/doi/10.1137/1010093, `cf-mitigated: challenge` (`fbm-1.html`)
    - attempt | https://api.crossref.org/works/10.1137%2F1010093 | 200 (`fbm-2.json`)
    - evidence | fbm | Canonical source | Mandelbrot, B. B.; Van Ness, J. W. (1968). Fractional Brownian Motions, Fractional Noises and Applications. *SIAM Review* 10(4), 422-437. | https://doi.org/10.1137/1010093 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - chamfer-distance | `10.1016/S0734-189X(86)80047-0` (canonical) | https://doi.org/10.1016/S0734-189X(86)80047-0 | 200 stub | route 2 | title, author Borgefors, year 1986 | none | 0
    - attempt | https://doi.org/10.1016/S0734-189X%2886%2980047-0 | 200 at https://linkinghub.elsevier.com/retrieve/pii/S0734189X86800470, `<title>Redirecting`, 2,657 bytes, folded title 1, `borgefors` 0, so blocked (`chamfer-distance-1.html`)
    - attempt | https://api.crossref.org/works/10.1016%2FS0734-189X%2886%2980047-0 | 200 (`chamfer-distance-2.json`)
    - evidence | chamfer-distance | Canonical source | Borgefors, G. (1986). Distance transformations in digital images. *Computer Vision, Graphics, and Image Processing* 34(3), 344-371. | https://doi.org/10.1016/S0734-189X(86)80047-0 | verified-via-index | Crossref record, publisher page 200 stub without authors | 2026-10-07
  - box-blur | `10.1109/TPAMI.1986.4767776` (canonical) | https://doi.org/10.1109/TPAMI.1986.4767776 | 202 | route 2 | author Wells, year 1986 | none | 0
    - attempt | https://doi.org/10.1109/TPAMI.1986.4767776 | 202 at https://ieeexplore.ieee.org/document/4767776/, empty body (`box-blur-1.html`)
    - attempt | https://api.crossref.org/works/10.1109%2FTPAMI.1986.4767776 | 200 (`box-blur-2.json`)
    - evidence | box-blur | Canonical source | Wells, W. M. (1986). Efficient Synthesis of Gaussian Filters by Cascaded Uniform Filters. *IEEE Transactions on Pattern Analysis and Machine Intelligence* PAMI-8(2), 234-239. | https://doi.org/10.1109/TPAMI.1986.4767776 | verified-via-index | Crossref record, publisher page 202 with an empty body | 2026-10-07
  - box-blur | Stamen, *Watercolor process* (design input) | https://stamen.com/watercolor-process-3dd5135861fe/ | 200 | route 1 | as for `multiply-compositing` (shared body `multiply-compositing-2.html`) | as P6.2 logged | 0
    - attempt | https://stamen.com/watercolor-process-3dd5135861fe/ | 200 (shared, `multiply-compositing-2.html`)
    - evidence | box-blur | Design input | Watson, Z. (Stamen Design) (2012). Watercolor Process. | https://stamen.com/watercolor-process-3dd5135861fe/ | verified | page 200 with its pinned words, published 2012-03-26 | 2026-10-07
  - hillshade | `10.1109/PROC.1981.11918` (canonical) | https://doi.org/10.1109/PROC.1981.11918 | 202 | route 2 | title "Hill shading and the reflectance map" (equal to the design record's), author Horn, year 1981 | none | 0
    - attempt | https://doi.org/10.1109/PROC.1981.11918 | 202 at https://ieeexplore.ieee.org/document/1456186/, empty body (`hillshade-1.html`)
    - attempt | https://api.crossref.org/works/10.1109%2FPROC.1981.11918 | 200 (`hillshade-2.json`)
    - evidence | hillshade | Canonical source | Horn, B. K. P. (1981). Hill shading and the reflectance map. *Proceedings of the IEEE* 69(1), 14-47. | https://doi.org/10.1109/PROC.1981.11918 | verified-via-index | Crossref record, publisher page 202 with an empty body | 2026-10-07
  - hachures | Imhof, ISBN 9781589480261 (canonical) | https://openlibrary.org/isbn/9781589480261.json | 200 | route 4 | title "Cartographic Relief Presentation", author Eduard Imhof, published "June 1, 2007", publisher ESRI Press | none | 1 (reset, then 200 after 5 s); author fetch 2 (reset, reset, then 200)
    - attempt | https://openlibrary.org/isbn/9781589480261.json | curl: (35) Recv failure: Connection reset by peer
    - attempt | https://openlibrary.org/isbn/9781589480261.json | 200 at https://openlibrary.org/books/OL8832465M.json (`hachures-1.json`; `authors` `/authors/OL1273097A`, `by_statement` null)
    - attempt | https://openlibrary.org/authors/OL1273097A.json | curl: (35) Recv failure: Connection reset by peer
    - attempt | https://openlibrary.org/authors/OL1273097A.json | curl: (35) Recv failure: Connection reset by peer
    - attempt | https://openlibrary.org/authors/OL1273097A.json | 200 (`hachures-2.json`, `.name` "Eduard Imhof")
    - evidence | hachures | Canonical source | Imhof, E. (2007). Cartographic Relief Presentation. ESRI Press. ISBN 9781589480261. | none | verified-via-index | OpenLibrary ISBN record 9781589480261 and author record OL1273097A | 2026-10-07
  - midpoint-displacement | `10.1145/358523.358553` (canonical) | https://doi.org/10.1145/358523.358553 | 403 | route 2 | authors Fournier, Fussell, Carpenter, year 1982 | none | 0
    - attempt | https://doi.org/10.1145/358523.358553 | 403 at https://dl.acm.org/doi/10.1145/358523.358553, `cf-mitigated: challenge` (`midpoint-displacement-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F358523.358553 | 200 (`midpoint-displacement-2.json`)
    - evidence | midpoint-displacement | Canonical source | Fournier, A.; Fussell, D.; Carpenter, L. (1982). Computer rendering of stochastic models. *Communications of the ACM* 25(6), 371-384. | https://doi.org/10.1145/358523.358553 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - midpoint-displacement | Tyler Hobbs 2017 (design input) | https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art | 200 | route 1 | `a guide to simulating watercolor paint with generative art` 7, `tyler hobbs` 26, `2017` 6 | pinned title case and author as P6.2 logged | 0
    - attempt | https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art | 200 (`midpoint-displacement-3.html`)
    - evidence | midpoint-displacement | Design input | Hobbs, T. (2017). A Guide to Simulating Watercolor Paint with Generative Art. | https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art | verified | page 200 with its pinned words, 2017 in the body | 2026-10-07
  - midpoint-displacement | axelinternet, p5-watercolor (design input; marker line, precedence) | https://github.com/axelinternet/p5-watercolor | 403 | route 5 | owner and name equal the entry's author and title; `git ls-remote` exit 0; README `hobbs` 2, `watercolor` 3 | none | 0
    - attempt | https://github.com/axelinternet/p5-watercolor | 403, "GitHub access to this repository is not enabled for this session" (`midpoint-displacement-4.html`)
    - attempt | git ls-remote https://github.com/axelinternet/p5-watercolor | exit 0, `HEAD` and `refs/heads/master` a3e995a, `refs/pull/1/head`, `refs/pull/1/merge` (`midpoint-displacement-5.txt`)
    - attempt | https://raw.githubusercontent.com/axelinternet/p5-watercolor/HEAD/README.md | 200, heading "# Watercolor canvas", "p5 implementation of [Typer Hobbs generative watercolor simulation](http://www.tylerlhobbs.com/writings/watercolor)." (`midpoint-displacement-6.md`)
    - evidence | midpoint-displacement | Design input | Hultman, A. (axelinternet) (2018, last commit, approximate). p5-watercolor. | https://github.com/axelinternet/p5-watercolor | maintainer-checked | maintainer-checked: run log 2026-10-07, owner axelinternet (Axel Hultman), About and README p5 implementation of Tyler Hobbs generative watercolor simulation, last commit about 2018; own page 403; route 5 matched, git ls-remote exit 0 at a3e995a and raw README 200, "p5 implementation of Typer Hobbs generative watercolor simulation" | 2026-10-07
  - edge-darkening, backruns, granulation, shallow-water | `10.1145/258734.258896` (canonical; one fetch, four keys) | https://doi.org/10.1145/258734.258896 | 403 | route 2 | title "Computer-generated watercolor", authors Curtis, Anderson, Seims, Fleischer, Salesin, year 1997 | record title case "Computer-generated watercolor"; venue the record's container title | 0
    - attempt | https://doi.org/10.1145/258734.258896 | 403 at http://portal.acm.org/citation.cfm?doid=258734.258896, `<title>Attention Required! | Cloudflare` (`edge-darkening-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F258734.258896 | 200 (`edge-darkening-2.json`; container "Proceedings of the 24th annual conference on Computer graphics and interactive techniques  - SIGGRAPH '97", two spaces before the hyphen in the record; 0 references)
    - evidence | edge-darkening | Canonical source | Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. | https://doi.org/10.1145/258734.258896 | verified-via-index | Crossref record, publisher page 403 Cloudflare block | 2026-10-07
    - evidence | backruns | Canonical source | Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. | https://doi.org/10.1145/258734.258896 | verified-via-index | Crossref record, publisher page 403 Cloudflare block | 2026-10-07
    - evidence | granulation | Canonical source | Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. | https://doi.org/10.1145/258734.258896 | verified-via-index | Crossref record, publisher page 403 Cloudflare block | 2026-10-07
    - evidence | shallow-water | Canonical source | Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997). Computer-generated watercolor. *Proceedings of the 24th annual conference on Computer graphics and interactive techniques - SIGGRAPH '97*, 421-430. | https://doi.org/10.1145/258734.258896 | verified-via-index | Crossref record, publisher page 403 Cloudflare block | 2026-10-07
  - edge-darkening | Bousseau et al. 2006 (design input) | https://api.crossref.org/works?query.bibliographic=Bousseau+Interactive+watercolor+rendering+with+temporal+coherence+and+abstraction&rows=5&... | 200 | route 3, then route 2 | first hit `10.1145/1124728.1124751`: title folds equal, year 2006, author Bousseau | "et al." expanded to the record's Kaplan, Thollot, Sillion; venue and pages from the record; the design record's "NPAR 2006" agrees with event "NPAR06" | 0
    - attempt | https://api.crossref.org/works?query.bibliographic=Bousseau+Interactive+watercolor+rendering+with+temporal+coherence+and+abstraction&rows=5&select=DOI,title,subtitle,issued,author,container-title,event | 200 (`edge-darkening-3.json`; five hits: 10.1145/1124728.1124751 the title 2006; 10.1145/987657.987661 "Interactive rendering of suggestive contours with temporal coherence" 2004; 10.1201/b10627-8 "Utilizing Temporal Coherence" 2005; 10.1145/340916.340919 "Interactive dynamic abstraction" 2000; 10.32657/10220/47356 "Real-time watercolor rendering of 3D objects and animation with enhanced control" null)
    - attempt | https://doi.org/10.1145/1124728.1124751 | 403 at https://dl.acm.org/doi/10.1145/1124728.1124751, `cf-mitigated: challenge` (`edge-darkening-4.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F1124728.1124751 | 200 (`edge-darkening-5.json`)
    - evidence | edge-darkening | Design input | Bousseau, A.; Kaplan, M.; Thollot, J.; Sillion, F. X. (2006). Interactive watercolor rendering with temporal coherence and abstraction. *Proceedings of the 4th international symposium on Non-photorealistic animation and rendering*, 141-149. | https://doi.org/10.1145/1124728.1124751 | verified-via-index | Crossref record by bibliographic search, publisher page 403 challenge | 2026-10-07
  - edge-darkening | Stamen, *Watercolor process* (design input) | https://stamen.com/watercolor-process-3dd5135861fe/ | 200 | route 1 | as for `multiply-compositing` (shared body `multiply-compositing-2.html`) | as P6.2 logged | 0
    - attempt | https://stamen.com/watercolor-process-3dd5135861fe/ | 200 (shared, `multiply-compositing-2.html`)
    - evidence | edge-darkening | Design input | Watson, Z. (Stamen Design) (2012). Watercolor Process. | https://stamen.com/watercolor-process-3dd5135861fe/ | verified | page 200 with its pinned words, published 2012-03-26 | 2026-10-07
  - wet-area-bleed | `10.1145/1124728.1124732` (canonical, DOI fixed by the plan) | https://doi.org/10.1145/1124728.1124732 | 403 | route 2 | title begins with the design record's "Real-time watercolor illustrations of plants", authors Luft, Deussen; year 2006 | record title "... of plants using a blurred depth test"; year 2006 added (the design record gives none) | 0
    - attempt | https://doi.org/10.1145/1124728.1124732 | 403 at https://dl.acm.org/doi/10.1145/1124728.1124732, `cf-mitigated: challenge` (`wet-area-bleed-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F1124728.1124732 | 200 (`wet-area-bleed-2.json`; event "NPAR06: The 4th International Symposium on Non-Photorealistic Animation")
    - evidence | wet-area-bleed | Canonical source | Luft, T.; Deussen, O. (2006). Real-time watercolor illustrations of plants using a blurred depth test. *Proceedings of the 4th international symposium on Non-photorealistic animation and rendering*, 11-20. | https://doi.org/10.1145/1124728.1124732 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - wet-area-bleed | Curtis et al. 1997, grail PDF (design input) | https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf | 200 | route 1 | as for `kubelka-munk` (shared body `kubelka-munk-3.pdf`) | year from the design record, not shown on the page | 0
    - attempt | https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf | 200 (shared, `kubelka-munk-3.pdf`)
    - evidence | wet-area-bleed | Design input | Curtis, C. J.; Anderson, S. E.; Seims, J. E.; Fleischer, K. W.; Salesin, D. H. (1997, year from the design record, not shown on the page). Computer-Generated Watercolor. | https://grail.cs.washington.edu/projects/watercolor/paper_small.pdf | verified | PDF 200, title and every author in the text | 2026-10-07
  - bristle-brush, nib | `10.1145/15886.15911` (canonical; one fetch, two keys) | https://doi.org/10.1145/15886.15911 | 403 | route 2 | author Strassmann, year 1986 | none | 0
    - attempt | https://doi.org/10.1145/15886.15911 | 403 at https://dl.acm.org/doi/10.1145/15886.15911, `cf-mitigated: challenge` (`bristle-brush-1.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F15886.15911 | 200 (`bristle-brush-2.json`)
    - evidence | bristle-brush | Canonical source | Strassmann, S. (1986). Hairy brushes. *ACM SIGGRAPH Computer Graphics* 20(4), 225-232. | https://doi.org/10.1145/15886.15911 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
    - evidence | nib | Canonical source | Nearest published work: Strassmann, S. (1986). Hairy brushes. *ACM SIGGRAPH Computer Graphics* 20(4), 225-232. | https://doi.org/10.1145/15886.15911 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - bristle-brush | Chu, Tai 2005, MoXi (design input; DOI fixed by the plan) | https://doi.org/10.1145/1186822.1073221 | 403 | route 2 | title "MoXi" plus subtitle "real-time ink dispersion in absorbent paper" folds equal to the design record's, authors Chu, Tai, year 2005 | venue "ACM SIGGRAPH 2005 Papers" and pages from the record | 0
    - attempt | https://doi.org/10.1145/1186822.1073221 | 403 at https://dl.acm.org/doi/10.1145/1186822.1073221, `cf-mitigated: challenge` (`bristle-brush-3.html`)
    - attempt | https://api.crossref.org/works/10.1145%2F1186822.1073221 | 200 (`bristle-brush-4.json`; event "SIGGRAPH05: Special Interest Group on Computer Graphics and Interactive Techniques Conference")
    - evidence | bristle-brush | Design input | Chu, N. S.-H.; Tai, C.-L. (2005). MoXi: real-time ink dispersion in absorbent paper. *ACM SIGGRAPH 2005 Papers*, 504-511. | https://doi.org/10.1145/1186822.1073221 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - bristle-brush | Baxter, Lin 2004 (design input) | https://api.crossref.org/works?query.bibliographic=Baxter+Lin+A+versatile+interactive+3D+brush+model&rows=5&... | 200 | route 3, then route 2 | first hit `10.1109/pccga.2004.1348363`: title folds equal; `issued` null, year 2004 from the container title "PG 2004"; authors Baxter, Lin | year 2004 from the container title; venue and pages from the record | 0
    - attempt | https://api.crossref.org/works?query.bibliographic=Baxter+Lin+A+versatile+interactive+3D+brush+model&rows=5&select=DOI,title,subtitle,issued,author,container-title,event | 200 (`bristle-brush-5.json`; five hits: 10.1109/pccga.2004.1348363 the title, issued null; 10.1145/383259.383313 "DAB" 2001; 10.1145/1198555.1198618 "DAB" 2005; 10.1145/1186223.1186227 "A viscous paint model for interactive applications" 2004; 10.58837/chula.the.2012.932 "3D-Model rendering in Chinese brush style" null)
    - attempt | https://doi.org/10.1109/pccga.2004.1348363 | 202 at https://ieeexplore.ieee.org/document/1348363/, empty body (`bristle-brush-6.html`)
    - attempt | https://api.crossref.org/works/10.1109%2Fpccga.2004.1348363 | 200 (`bristle-brush-7.json`)
    - evidence | bristle-brush | Design input | Baxter, W. V.; Lin, M. C. (2004). A versatile interactive 3D brush model. *12th Pacific Conference on Computer Graphics and Applications, 2004. PG 2004. Proceedings.*, 316-325. | https://doi.org/10.1109/pccga.2004.1348363 | verified-via-index | Crossref record by bibliographic search, issued null, year from the container title PG 2004, publisher page 202 with an empty body | 2026-10-07
  - label-placement | `10.1559/152304075784313304` (canonical) | https://doi.org/10.1559/152304075784313304 | 403 | route 2 | author Imhof, year 1975 | none | 0
    - attempt | https://doi.org/10.1559/152304075784313304 | 403 at https://www.tandfonline.com/doi/full/10.1559/152304075784313304, `cf-mitigated: challenge` (`label-placement-1.html`)
    - attempt | https://api.crossref.org/works/10.1559%2F152304075784313304 | 200 (`label-placement-2.json`)
    - evidence | label-placement | Canonical source | Imhof, E. (1975). Positioning Names on Maps. *The American Cartographer* 2(2), 128-144. | https://doi.org/10.1559/152304075784313304 | verified-via-index | Crossref record, publisher page 403 challenge | 2026-10-07
  - closing | Stadia Maps, Stamen Watercolor docs | https://docs.stadiamaps.com/map-styles/stamen-watercolor/ | 200 | route 1 | `stamen watercolor` 43, `stadia maps` 22; `<title>` "Stamen Watercolor - Stadia Maps Documentation"; no published date | pinned title and (n.d.) as P6.2 logged | 0
    - attempt | https://docs.stadiamaps.com/map-styles/stamen-watercolor/ | 200 (`closing-1.html`)
    - evidence | closing | Read during design | Stadia Maps (n.d.). Stamen Watercolor. | https://docs.stadiamaps.com/map-styles/stamen-watercolor/ | verified | page 200 with its pinned words | 2026-10-07
  - closing | ICA MapCarte 95/365, Wainwright | https://mapdesign.icaci.org/2014/04/mapcarte-95365-pictorial-guide-to-the-lakeland-fells-by-alfred-wainwright-1955-1966/ | 200 | route 1 | `mapcarte 95 365` 4, `pictorial guide to the lakeland fells` 17, `wainwright` 32, `commission on map design` 6, `2014` 49 | pinned title and author as P6.2 logged | 0
    - attempt | https://mapdesign.icaci.org/2014/04/mapcarte-95365-pictorial-guide-to-the-lakeland-fells-by-alfred-wainwright-1955-1966/ | 200 (`closing-2.html`)
    - evidence | closing | Read during design | ICA Commission on Map Design (2014). MapCarte 95/365: Pictorial Guide to the Lakeland Fells by Alfred Wainwright, 1955-1966. | https://mapdesign.icaci.org/2014/04/mapcarte-95365-pictorial-guide-to-the-lakeland-fells-by-alfred-wainwright-1955-1966/ | verified | page 200 with its pinned words, 2014 in the body | 2026-10-07
  - closing | Adventures in Mapping 2024 | https://adventuresinmapping.com/2024/02/14/7595/ | 200 | route 1 | `adventures in mapping` 7, `tolkien style maps in a gis part 3 water` 5, `john nelson` 7, `2024` 29; `article:published_time` 2024-02-14 | pinned title and author as P6.2 logged | 0
    - attempt | https://adventuresinmapping.com/2024/02/14/7595/ | 200 (`closing-3.html`)
    - evidence | closing | Read during design | Nelson, J. (Adventures in Mapping) (2024). Tolkien Style Maps in a GIS: part 3, Water. | https://adventuresinmapping.com/2024/02/14/7595/ | verified | page 200 with its pinned words, published 2024-02-14 | 2026-10-07
  - closing | Urban Sketching World, *Line and wash* | https://urbansketchingworld.com/line-and-wash/ | 200 | route 1 | `line and wash` 35, `urban sketching world` 3; no `article:published_time` | pinned title and (n.d.) as P6.2 logged | 0
    - attempt | https://urbansketchingworld.com/line-and-wash/ | 200 (`closing-4.html`)
    - evidence | closing | Read during design | Urban Sketching World (n.d.). Urban Sketching Examples: Line and Wash. | https://urbansketchingworld.com/line-and-wash/ | verified | page 200 with its pinned words | 2026-10-07
  - closing | The Postman's Knock, *Illustrated wedding maps* (marker line, precedence) | https://thepostmansknock.com/illustrated-wedding-maps/ | 403 | none (routes 1 and 7 failed; routes 2 to 6 do not apply) | none from a route; fields from the 13:24 marker entry | none | Wayback API 4 retries, exhausted; snapshot 4 retries, exhausted
    - attempt | https://thepostmansknock.com/illustrated-wedding-maps/ | 403, `<title>Just a moment...`, `cf-mitigated: challenge` (`closing-5.html`)
    - attempt | https://archive.org/wayback/available?url=thepostmansknock.com/illustrated-wedding-maps/ | 429, and 429 after each wait of 5, 10, 20 and 40 s (`closing-6.json`), exhausted
    - attempt | https://web.archive.org/web/20261007id_/https://thepostmansknock.com/illustrated-wedding-maps/ | curl: (35) Recv failure: Connection reset by peer, and the same after each wait of 5, 10, 20 and 40 s, exhausted
    - evidence | closing | Read during design | Bugbee, L. (2014). Illustrated Wedding Maps. | https://thepostmansknock.com/illustrated-wedding-maps/ | maintainer-checked | maintainer-checked: run log 2026-10-07, Illustrated Wedding Maps, Lindsey Bugbee, 13 March 2014, title, author and year match, process section paywalled; own page 403 challenge; Wayback API 429 after backoff 5, 10, 20, 40 s; snapshot 20261007 connection reset after backoff 5, 10, 20, 40 s | 2026-10-07
  - Not fetched, written as their exact lines: the 16 `named-only` works (`deegan-coffee-ring`,
    `arxiv-watercolour-drying`, `lee-wet-on-wet`, `wetbrush`, `osm-overpass`,
    `osm-tagging`, `opentopodata-srtm`, `open-elevation`, `patrick-hand`, `caveat`,
    `svg-filter-effects`, `css-mix-blend-mode`, `wcag-aa-contrast`, `walk-guide-maps`,
    `researcher-search-terms`, `maptiler-stadia-notes`); 9 `the canonical source above.`
    lines; 10 `not recorded` lines.
  - Final status by source line: 23 canonical lines, 1 `verified` (W3C) and 22
    `verified-via-index` (route 2: 20; route 4: `hachures`; route 6: `kubelka-munk`); 12
    fetched design-input lines, 7 `verified`, 4 `verified-via-index`, 1
    `maintainer-checked`; 5 fetched closing lines, 4 `verified`, 1 `maintainer-checked`;
    16 `named-only`. `unreachable` 0, `not-verified` 0. No candidate replaced; no
    mismatch in any field.
  - Corrections to design-sources entries (each from a record or pinned page): Van
    Laerhoven, Van Reeth title U+2010 written as ASCII hyphen (dash rule; the only
    U+2010 to U+2015 character in any copied field) and venue added; Bousseau "et al."
    expanded to Kaplan, Thollot, Sillion; Luft, Deussen title extended by "using a blurred
    depth test" and year 2006 added; MoXi venue "ACM SIGGRAPH 2005 Papers"; Baxter, Lin
    year from the container title (issued null); Curtis 1997 record title case
    "Computer-generated watercolor" on the canonical lines (the PDF design-input lines
    keep the pinned "Computer-Generated Watercolor"); Douglas, Peucker and Chaikin given
    their record titles (the design record has descriptions); Kubelka, Munk venue from
    Kubelka 1948's reference; the page-title and author corrections P6.2 logged (Hobbs,
    Stamen, Stadia, ICA, Adventures in Mapping, Urban Sketching, The Postman's Knock,
    osmanyy) hold on the live pages.
  - Step 3 (re-try `not-verified` and `unreachable` entries): none exist, so no retry
    rows. choice: no step-3 re-try | rule: step 3 (only `not-verified` and `unreachable`
    entries) | inputs: the evidence rows above. The Postman's Knock is
    `maintainer-checked` by precedence; its archive route stays failed and is quoted.
  - Issues filed: 0. Fixed: 0. No case outside a rule.
- 15:50 P6.3-write (step 4, mechanical checks, gate), from `bef4d29` plus P6.3-fetch's
  log entry; started 15:31, wall time 19 min (G-here 12 min of it). No `src/` or `tests/`
  change. Owner files: `docs/explanation/references.md` (new, 182 lines, 23 entries plus
  the closing section), `docs/README.md` (`explanation/` subfolder line), `GLOSSARY.md`
  (`reference` row), this log. The `write-docs` skill was read (reference mode).
  - choice: `$SCRIPTS` (`$SCRATCH/p6-scripts/`) did not exist, so P6.3-write wrote
    `ast_neutral.py`, `refcheck.sh` and `doc_lines.py` there verbatim from the plan's three
    blocks, two-space indentation stripped, and `SHA256SUMS` (`ast_neutral.py`
    611a5ddf..., `refcheck.sh` cd899deb..., `doc_lines.py` cb06ad2e...);
    `sha256sum -c` OK for all three | rule: Shared scripts | inputs: plan blocks, brief.
  - choice: each source line written from the last (here the only) evidence row of its
    source, 40 rows (23 canonical, 12 design input, 5 closing), by a generator script in
    `$SLICE/write/gen.py`, never a fetch; line = label, citation fields, URL (omitted when
    the row says `none`), `[<status>: <how-checked>; <date>]`; for the two
    `maintainer-checked` rows the how-checked text already begins with the status, so it
    is not doubled | rule: step 4; Source line; maintainer-checked | inputs: evidence rows.
  - choice: design-input slots per entry in `design-sources.md` order as the inventory's
    design-input column lists them (fixed lines and `named-only` lines in place) |
    rule: reference format; P6.2 match table | inputs: `p6-inventory.md`.
  - choice: entry headings use the inventory's Technique column text, `Implemented in:`
    its Sites without line hints | rule: Key; Implemented in | inputs: `p6-inventory.md`.
  - choice: `nib`'s canonical line begins `- Canonical source: Nearest published work:
    Strassmann, S. (1986).` | rule: step 4, canonical-source rule 5 | inputs: evidence row.
  - `Note:` lines, 5, each basis (a), each a code fact read from the site's body:
    - `marching-squares` (a, the 2-D case, rule 3): `contours.marching_squares` traces one
      level's polylines through square grid cells, crossings interpolated linearly.
    - `lanczos` (a): applied through Pillow, `Image.Resampling.LANCZOS` at
      `ink/pad.py:128` and `maps/compose.py:48,69,84,98`.
    - `chamfer-distance` (a): weights 1 and 1.41421356 in `ink.noise.edt`, a sweep down
      the rows and one back up.
    - `hillshade` (a): slope and aspect from `numpy.gradient` (`maps.relief._shade`).
    - `nib` (a, rule 5): laid through `ink.pad.InkPad`; own parts are the broad-nib width
      (`letters.nib._pen_profile`, `(1 - thin) + thin * abs(sin(theta - angle))`), the
      optional backing wash, and normal (not multiply) compositing of the ink layers.
    - choice: no (b) note (P6.1 added no row) and no (c) note (no departure taken from a
      saved body) | rule: step 4 `Note:` lines | inputs: inventory, evidence rows.
  - Corrections in P6.3-write: none (no U+2010 to U+2015 character in the file; the one
    dash correction is P6.3-fetch's, already in its evidence row). `strip_emdashes.py
    --check`: `would replace 0, 0 remaining`.
  - Mechanical checks, outputs:
    - keys: `diff` empty, exit 0; 23 keys, none repeated.
    - design-sources URLs: no `missing` line.
    - `refcheck.sh`: exit 0, printing only:
      `MAINTAINER-CHECKED 104: - Design input: Hultman, A. (axelinternet) (2018, last commit, approximate). p5-watercolor. https://github.com/axelinternet/p5-watercolor [...]`
      and `MAINTAINER-CHECKED 170: - Read during design: Bugbee, L. (2014). Illustrated Wedding Maps. https://thepostmansknock.com/illustrated-wedding-maps/ [...]`.
      No `UNREACHABLE` line.
    - one canonical line per entry: prints nothing.
    - `grep -c '^- Canonical source: Nearest published work:'
      docs/explanation/references.md`: `1` (expected 1, the `nib` line).
  - Entries by status: canonical 1 `verified`, 22 `verified-via-index`; design input 7
    `verified`, 4 `verified-via-index`, 1 `maintainer-checked`, 4 `named-only`, 19 fixed;
    closing 4 `verified`, 1 `maintainer-checked`, 12 `named-only`. `not-verified` 0,
    `unreachable` 0. No row sent back to P6.3-fetch.
  - Not done, out of the brief's owner files: the inventory's status column
    (`p6-inventory.md`, listed in the slice's owner files) stays empty.
  - Issues filed: 0. Fixed: 0. No case outside a rule.
  - G-here, per stage: `uv sync` 1 s; `uv run prek` cannot spawn (as at P6.1 and P6.2),
    so `uvx prek run --all-files` 4 s, green, no file touched; `pytest -m "not golden"`
    156 s (1036 passed, 1 skipped, 17 deselected); `--golden-tolerance` 281 s (17
    passed); byte-exact `pytest -m golden` 283 s (17 passed).
- 15:51 P6.3-write, follow-up at the orchestrator's request (the inventory was left out of
  the first brief): the inventory's status column filled.
  - choice: each row's status cell is its canonical source's status from that key's
    `Canonical source` evidence row, backticked; 22 `verified-via-index`, 1 `verified`
    (`multiply-compositing`) | rule: P6.3 owner files (status column); P6.1 (sixth column
    for P6.3's statuses) | inputs: evidence rows, orchestrator brief.
  - Re-run: key diff empty, exit 0, 23 keys; `refcheck.sh` exit 0, only the two
    `MAINTAINER-CHECKED` lines (104, 170). Issues filed: 0.
- 15:50 P6.3 verified and ticked (`7130b60`, `19eb6db`): 23 entries, 22 canonical sources `verified-via-index` and 1 `verified`; no `unreachable` or `not-verified`. P6.4 dispatched.
- 16:12 P6.4 cite each key in its docstring, and gate it. Start 15:51, end 16:12 BST
  (wall 21 min). Starting commit `5124b5e`; `$SLICE` is `$SCRATCH/p6.4/`; shared scripts
  `sha256sum -c SHA256SUMS`: all three OK.
  - G-self baseline: `$MG "$SLICE/before"` 59 s, `{"commit": "5124b5eb8feec00fcb8e4114599739b28e837ca8", "dirty": false}`.
    A first baseline was taken with the new test file already untracked in the tree and
    read `"dirty": true`; it was discarded and remade with the file moved out (invalid
    baseline rule).
  - Red, before any citation line: `tests/architecture/test_reference_keys.py` 1 failed,
    5 passed; `FAILED test_every_site_cites_its_key`, `AssertionError: sites that do not
    cite their entry's key: ['kubelka-munk: pyntpot.ink.pigment.km_rt', ...]`, all 36
    site-key pairs of the 23 entries, and no `Implemented in:` path unresolved (none was
    wrong, so `references.md` is unchanged).
  - Green, after: 6 passed.
  - Citation lines: 36 in 19 files, 83 lines added and 7 replaced (each one-line docstring
    made multi-line). Lines added per file: `ink/noise.py` +16, `ink/pigment.py` +9,
    `maps/compose.py` +8, `ink/wash.py` +7, `ink/polyline.py` +6, `ink/tip.py` +3,
    `maps/relief.py` +3, and +2 each in `ink/curves.py`, `ink/pad.py`, `ink/raster.py`,
    `ink/shallow_water.py`, `ink/sheet.py`, `ink/stamp.py`, `letters/nib.py`,
    `letters/skeleton.py`, `maps/contours.py`, `maps/lettering/placement.py`,
    `maps/painter/cover.py`, `maps/relief_strokes.py`. Nearest 400: `ink/polyline.py` 361,
    `ink/wash.py` 361 (the plan's 360 plus the second key on `wash.wash`),
    `maps/lettering/placement.py` 350. New test file 240 lines.
  - choice: a site with two keys (`maps.compose._plates`, `ink.tip._fbm1`,
    `ink.wash.wash`) carries the two lines adjacent, as one last paragraph, in
    `references.md` entry order | rule: Citation line in a docstring ("a site that
    implements two techniques carries two lines"); line budget item 1 | inputs:
    `references.md`, the three docstrings.
  - choice: prek run as `uvx prek run --all-files` | rule: as P6.1 to P6.3, filed in
    `docs/issues/prek-not-in-the-environment.md` | inputs: `uv run prek` failing to spawn.
  - AST-neutral: `python3 -I "$SCRIPTS/ast_neutral.py" 5124b5e` printed
    `AST-neutral: 19 files`, exit 0.
  - G-here, per stage: `uv sync` 0 s; `uvx prek run --all-files` 5 s, green (a first run
    caught two ty `unsound` diagnostics in the new test, fixed in the test); `pytest -m
    "not golden"` 162 s (1042 passed, 1 skipped, 17 deselected), re-run after the ty fix
    161 s, exit 0; `--golden-tolerance` 294 s (17 passed); byte-exact `pytest -m golden`
    284 s (17 passed). G-self `--golden-dir="$SLICE/before"` 288 s (17 passed).
  - Issues filed: 0. Fixed: 0. No case outside a rule.
- 16:13 P6.4 verified and ticked (`5ff3c03`): 36 citation lines in 19 files, architecture
  tests green (orchestrator rerun). `ink/wash.py` reached 361 lines against the plan's
  predicted 360 (two keys on `wash`); under 400, no action. P6.5 dispatch: shared scripts
  at `/tmp/claude-0/-home-user-pyntpot/81b07070-1ea4-5527-9ae2-48b727070240/scratchpad/p6-scripts` (SHA256SUMS OK); five detached worktrees at `5ff3c03` under
  `/tmp/claude-0/-home-user-pyntpot/81b07070-1ea4-5527-9ae2-48b727070240/scratchpad/wt/p6.5{a..e}`; `$SLICE` = `/tmp/claude-0/-home-user-pyntpot/81b07070-1ea4-5527-9ae2-48b727070240/scratchpad/p6.5<x>/`. P6.5a-e dispatched in parallel.
- 16:50 P6.5a ink docstrings and comments. Start 16:15, end 16:50 BST. Starting commit `5ff3c03`; `sha256sum -c` all OK; files 19 (expected 19). Public API done 16:23.
  Docstrings changed, public: `Sheet` module (invariant names the fibre settings), `Canvas.px`, `Sheet.pits` (Returns: in 0 to 1), `Sheet.noise`, `composite` (Returns), `wash`; private and other names in all 16 modified files; added 4 nested-helper docstrings (`polyline.clip_line.inside`, `wash.fluid_modulate.down`, `shallow_water.dx`, `shallow_water.dy`). Sections added: `Canvas.px` Args/Returns ((n, 2) shape, x from the west edge, y down from the north edge); `Sheet.noise` Args (`cell` in pixels, `octaves` as halvings; each call advances the shared generator). Comments changed 17 (phase numbers removed, tense fixed where a live sine path read as past, `PAPER` comment, a dangling `# --- ribbon` marker removed).
  - choice: prek as `uvx prek run --all-files` | rule: as P6.1-P6.4, prek-not-in-the-environment | inputs: spawn failure.
  - choice: measurement prose in `#:` field comments kept; only tense that contradicts live code fixed | rule: behaviour wins; house rules beat the skills | inputs: brush_style.py, style.py.
  - kept: precise term | src/pyntpot/ink/chains.py:176 | surface | OSM's road surface tag
  - kept: precise term | src/pyntpot/ink/pigment.py:45 | surface | the paper surface, as ink/sheet.py uses it
  - kept: precise term | src/pyntpot/ink/sheet.py:8 | surface | the paper surface painting is done on
  - Reworded: style.py:209 "surface". Fixed 41, filed 2: ink-tip-smooth-path-ends, ink-deposit-edge-clamp. brush.py stays 391; no line-budget issue.
  - Gates (measured under parallel load (5 slices running)): ast-neutral 16 files; uv sync 0 s; uvx prek 8 s; not-golden 171 s; tolerance 314 s; exact 258 s (re-run after the agent's own 10-minute background limit cut the first); G-self baseline 78 s, compare 272 s; doc_lines 19/19/19, 3 findings, all kept.
  - Glossary changes proposed: none.
- 17:04 P6.5a landed by the orchestrator (measured alone): partition clean; patch applied on `9eed861`; ast-neutral 0 s; uv sync 0 s; uvx prek 4 s; not-golden 156 s (................................... [100%]); tolerance 299 s; exact 288 s; doc_lines 19/19 headers, 3 findings, 3 kept lines; glossary changes applied 0, deferred 0.
- P6.5b letters: start 16:15, end 16:42 BST. File list 8 (table 8). Lines 1726 -> 1730. Public API done 16:20.
  Docstrings changed 19 (public 1, other 18), added 0, sections added 0, comments changed 8. Fixed 27, filed 6.
  Gates (measured under parallel load (5 slices running)): ast-neutral 8 files; uv sync 0 s; uvx prek 5 s; not-golden 163 s; tolerance 308 s; exact 320 s; G-self baseline 72 s, compare 282 s; doc_lines 8/8/8, 5 findings, all kept.
  choice: Hand Args stay on class docstring | rule: Args rule (existing correct section stays) | inputs: hand.py
  choice: no summary-length rewrites | rule: house rules beat the skills (line-length 100) | inputs: pyproject.toml
  choice: docstrings skill not applied to # comments; comments got accuracy and prose passes only | rule: house rules beat the skills (skill excludes # comments) | inputs: docstrings SKILL.md
  choice: history narration in private docstrings (_flank, _dots, _extend, OutlineFont.measure) rewritten as present-tense fact or removed | rule: house rules beat the skills (skill Process) | inputs: trace.py, font.py
  choice: card pixels vs display pixels left as is, filed | rule: fix now or file (no glossary term picks one) | inputs: GLOSSARY.md card and mark rows
  choice: pen angle, outline width, route ink, glyph advance texts rewritten to the code and filed | rule: behaviour wins | inputs: nib.py, style.py, font.py, lettering/pipeline.py, the face's hmtx
  choice: uvx prek in place of uv run prek | rule: no stop points (as at P6.1) | inputs: prek-not-in-the-environment.md
  kept: precise term | src/pyntpot/letters/nib.py:16 | surface | the `surface` parameter (NibSurface)
  kept: precise term | src/pyntpot/letters/nib.py:21 | surface | the `surface` argument of plate
  kept: precise term | src/pyntpot/letters/nib.py:176 | surface | the `surface` parameter of _sheet
  kept: precise term | src/pyntpot/letters/nib.py:206 | surface | Args entry naming the `surface` parameter
  kept: precise term | src/pyntpot/letters/nib.py:284 | surface | Args entry naming the `surface` parameter
  Glossary changes proposed: none. Issues filed: letters-nib-outline-width-reads-face-route, letters-nib-pen-angle-ignores-writing-line, letters-trace-radii-unused, letters-card-pixels-and-display-pixels, letters-font-missing-glyph-advance, letters-style-label-route-ink-not-filled.
- 17:17 P6.5b landed by the orchestrator (measured alone): partition clean; patch applied on `55fdf43`; ast-neutral 0 s; uv sync 0 s; uvx prek 5 s; not-golden 155 s (................................... [100%]); tolerance 302 s; exact 287 s; doc_lines 8/8 headers, 5 findings, 5 kept lines; glossary changes applied 0, deferred 0.
- 16:44 P6.5c maps facade, data and furniture. Start 16:15, end 16:44 BST. Start 5ff3c03; files 32 (plan 32); SHA256SUMS OK. Public API done 16:22.
  Docstrings and comments: diff +110/-113 over 23 files; sections added 2 (`Track.from_gpx` Raises ValueError: time not ISO 8601 with a zone, fewer than two points, or a latitude outside [-90, 90]; `Style.from_toml` Raises tomllib.TOMLDecodeError).
  - choice: prek as `uvx prek run --all-files` | rule: as P6.1 to P6.4, docs/issues/prek-not-in-the-environment.md | inputs: `uv run prek` failed to spawn.
  - choice: Raises on Track.from_gpx and Style.from_toml only | rule: Args rule (a condition for a raise) | inputs: the 21 public methods.
  - choice: summary mood left mixed | rule: Args rule (accuracy and layout only) | inputs: style.py, plates.py.
  - choice: landmark_export non-goal paragraph deleted | rule: house rules beat the skills (not public; the module keeps it) | inputs: export.py.
  - choice: hillshade_mode text fixed, not filed | rule: behaviour wins (the theme is also "off") | inputs: default.toml.
  - Fixed: 1 detector finding (`landmark_classes.py:143`, "first class") plus the accuracy fixes; filed 2 (maps-style-groups-labels-switch-is-read-by-the-attribution-only, maps-style-groups-route-constants-have-no-reader). kept: none.
  - Gates (measured under parallel load (5 slices running)): ast-neutral 23 files 1 s; uv sync 0 s; uvx prek 5 s; not-golden 171 s; tolerance 304 s; exact 313 s; G-self baseline 67 s, compare 280 s; doc_lines 32/32/32, 0 findings.
  - Glossary changes proposed: none. Noted for P6.6: the `backdrop` and `terms` cells say "darkness grid" where the term is "dark grid".
- 17:29 P6.5c landed by the orchestrator (measured alone): partition clean; patch applied on `bd4e55d`; ast-neutral 0 s; uv sync 0 s; uvx prek 4 s; not-golden 157 s (................................... [100%]); tolerance 298 s; exact 282 s; doc_lines 32/32 headers, 0 findings, 1 kept lines; glossary changes applied 0, deferred 0.
- 16:44 P6.5d maps geometry and painter. Start 16:15, end 16:44 BST. Start `5ff3c03`; SHA256SUMS OK; files 28 (expected 28). Public API done 16:21 (none in group).
  Docstrings changed 48 private in 25 files (accuracy: `paper_plate` grid, `COVER_ORDER` decides overlaps, `build_basemap` returns None without features, `TrackIndex` bucket scan, painter phase shapes, a missing exploration page, `_derived`, `stroke_d`, `sea_from_coast`, `shade_bands`, `separate_strands`, `_waterway`, `_open_rivers`, `declutter`); history narration removed in `rivers`, `osm_elements`, `job`, `plates`, `pen`; added 4 nested-helper docstrings; `strands` module docstring gained key names, non-goals, invariants; sections added 0 (4 private Returns/Args corrected); comments changed 11. Net +23 lines; largest file `layers.py` 331.
  - Detector before: 2 findings (generalise.py:1, :128 `intricate`), both reworded. After: 0. kept: none.
  - choice: prek as `uvx prek` | rule: as P6.1 to P6.4, prek-not-in-the-environment | inputs: spawn failure.
  - choice: "activity"/"session" -> "track", "route metres" -> "card metres", "darkness grid" -> "dark grid" | rule: one name a concept (GLOSSARY track, card) | inputs: GLOSSARY.md, track_projection.
  - choice: "SRTM grid"/"elevation grid" -> "elevation patch" in painter | rule: glossary | inputs: Layers.elevation type.
  - choice: issue files tunnel=no and private cross-module imports | rule: behaviour wins; fix now or file | inputs: osm_elements._waterway, imports. Filed: maps-osm-elements-tunnel-no, maps-track-index-private-names-imported.
  - Gates (measured under parallel load (5 slices running)): ast-neutral 26 files; uv sync 0 s; uvx prek 6 s; not-golden 167 s; tolerance 309 s; exact 309 s; G-self baseline 72 s, compare 266 s; doc_lines 28/28/28, 0 findings.
  - Glossary changes proposed: none. Noticed outside the group: "activity" and "label agent" remain in `candidates/export`, `lettering/label`, `lettering/picks`.
- 17:41 P6.5d landed by the orchestrator (measured alone): partition clean; patch applied on `2a78886`; ast-neutral 0 s; uv sync 0 s; uvx prek 5 s; not-golden 153 s (................................... [100%]); tolerance 291 s; exact 288 s; doc_lines 28/28 headers, 0 findings, 1 kept lines; glossary changes applied 0, deferred 0.
- 16:50 P6.5e maps lettering docstrings and comments. Start 16:15, end 16:50 BST; files 21 (table 21); public API done 16:23. Times measured under parallel load (5 slices running).
  Docstrings changed: 2 public (`letter`, `pipeline` module), about 60 other in 19 files; added 1 (nested `picks_lines.named_lines.kept_lines`); sections added 0; comments changed about 30 (stale names `schema.Span`, `_bracket`, `journal_layers`; "rule seven" -> "the route rule"; payload/agent wording -> annotations; wrong facts: "a third" where the value is 0.25, offset 1.7 where it is 1.2, EDGE_PX direction, `_freer_side` and the side convention, rung order, "nearest" where the order is by notability, `journal_picks` cap).
  - Baseline 72 s, clean. AST-neutral: 19 files. G-here: sync 0 s; uvx prek 12 s; not-golden 214 s (1042 passed, 1 skipped); tolerance 283 s; exact 272 s; G-self 284 s (17 passed each).
  - Detector: 5 findings before, 0 after; no kept: lines.
  - choice: prek via uvx | rule: P6.4 precedent, docs/issues/prek-not-in-the-environment.md | inputs: spawn failure.
  - choice: text about earlier code versions rewritten as present facts; why-measurements kept | rule: house rules beat the skills (docstrings rubric, Process) | inputs: each docstring and its code.
  - choice: "sheet" homonym filed, not reworded | rule: fix now or file | inputs: GLOSSARY.md sheet row, 48 uses.
  - Fixed ~45, filed 7: label-as-dict-unused, picks-journal-picks-cap, sheet-homonym, span-sides-curve-scale-offset, span-sides-freer-side-sign (reproduced with a script), spans-place-spans-rung-order, spans-rule-seven-in-tests.
  - Glossary changes proposed: none.
- 17:54 P6.5e landed by the orchestrator (measured alone): partition clean; patch applied on `f52eb8b`; ast-neutral 0 s; uv sync 0 s; uvx prek 5 s; not-golden 156 s (................................... [100%]); tolerance 292 s; exact 288 s; doc_lines 21/21 headers, 0 findings, 1 kept lines; glossary changes applied 0, deferred 0.
