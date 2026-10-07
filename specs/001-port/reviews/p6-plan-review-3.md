# P6 plan review 3

Reviewed: `specs/001-port/plan.md`, section `### P6. Docstrings, prose and
references` (lines 3952 to 5263), branch `p6-docs`. The plan is at `6d5f27f`;
HEAD is `f3fd835`, which only appends the maintainer's 14:40 note to the run
log. Read against `reviews/p6-plan-review-2.md`,
`git diff 31c1d26 6d5f27f -- specs/001-port/plan.md`, `spec.md`,
`design-sources.md`, `p6-run-log.md` and the repository.

These maintainer decisions are settled and not re-opened:

- Args/Returns sections only where they add information.
- `maintainer-checked` for p5-watercolor and The Postman's Knock (14:05).
- The total length of the section is fine (14:40). Following the 14:40 note,
  only single slices are judged, along with whether P6.5a to P6.5e can run in
  parallel.

Probes were run on 2026-10-07, in a scratch directory outside the repo:

- `doc_lines.py` and `refcheck.sh`, extracted verbatim from the plan with the
  two-space indent stripped.
- `doc_lines.py` on a scratch clone, with absolute paths.
- `doi.org` through the proxy for nine candidate DOIs, 2 s apart.
- Greps of `src/` for every factual claim in the P6.2 match table.

## Verdict: BLOCK

The most important change: **the P6.2 match table is authoritative, and one
of its rows rests on a false grep.**

- The table sends Luft, Deussen to the closing section because "no code site
  holds a wet-area map shared between washes (`grep -rniE 'wet.?area' src`
  finds none)".
- That grep finds three hits. `pyntpot.ink.wash.wash` implements exactly
  that technique.
- So the inventory is missing a technique under its own inclusion rule (b).
  As written, P6 would publish a `references.md` that says a design input
  informed no technique, when the code implements it, and would leave that
  technique uncited, against D24.

The second blocker is that route 2 cannot be reached for three Elsevier
canonical sources. That gives a permanent red gate, which breaks "no stop
points".

Both fixes are small and mechanical.

## Round-2 findings

All 14 are resolved in the plan text.

| Finding | Status | Evidence |
|---|---|---|
| A `not-verified` has no end state | Resolved | Two new statuses: `unreachable` (4468-4480) and `maintainer-checked` (4481-4495). Both are final, and both are barred from `Canonical source` lines by `refcheck.sh`: my probes give exit 1 for each on a canonical line. The archive route is route 7. Route 5 now matches a repository by owner and name, plus `ls-remote` and README words. Tracing p5-watercolor through it: the README "p5 implementation of [Typer Hobbs generative watercolor simulation]" folds to text that contains `hobbs` and `watercolor`, so it matches. |
| B The jargon gate is unreachable | Resolved | `doc_lines.py` (5139-5170) reproduces the claim exactly. Over the 108 files of `src/` it reports 18 findings, 5 of them in `letters/nib.py`. The `surface` identifier lines are gone. A scan for non-docstring bare string statements finds none, so the extractor misses no prose of that kind. The gate is now "no finding without an outcome" (5196-5199). |
| S1 The match is semantic | Resolved in form | The table is at 4759-4794 and covers every `design-sources.md` entry (checked bullet by bullet). Between them, its lines and the fixed lines cover all 22 seed rows. **One row's premise is false: blocker A.** |
| S2 URL rule and the Curtis URL | Resolved | 4438-4447. |
| S3 MoXi DOI | Resolved | `10.1145/1186822.1073221` is fixed, with the reason (4295-4308). Routes 1 and 2 use it (4886-4888), and route 3 does not apply. Tool facts and step 1 now agree. |
| S4 `named-only` is unbounded | Resolved | The 16-key closed list has exact citations and needs each key exactly once (4918-4961). Probes, each exit 1 as claimed: the round-2 fake (`lazy`); a real key under the wrong label (`osm-overpass` as `Design input`); `named-only` on a canonical line. |
| Nits 1-8 | Resolved | Method count (4003); date regex (4941); `html.unescape` (4594); two works give two lines (4404-4407); Kubelka-Munk last page not cited (4416, 4860); scripts rewritten every session (4099-4104); one table only (4724-4727); the dash rule covers every copied field (4173-4181). |

## [BLOCKING]

### A. The match table's Luft, Deussen row (4764) is based on a false grep, and the inventory lacks the shared wet-area bleed (4636-4646, 4691-4714, 4761)

`grep -rniE 'wet.?area' src` at HEAD gives these hits:

- `ink/wash.py:4`: "bleeding into a shared wet area".
- `:142`: "the wet area it shares".
- `:159`: "#: The shared wet-area map, when there is one. Inside it this wash
  bleeds into whatever is beside it and gives up most of its rim".

The body carries it out at `ink/wash.py:218-230`:

- `rim = rim * (1.0 - o.wet * o.rim_drop)`
- `dens = dens * (1.0 - m_wet) + blur(dens, o.bleed_px) * m_wet`

That is Luft and Deussen's "shared wet-area map so adjacent washes bleed",
word for word. Curtis's note also names the "wet-area mask".

Under inclusion rule (b), this technique must enter the inventory:
`design-sources.md` names it, and a code site implements it. It is not in
the seed, though. The tally regex (4665) has no `wet` term, so P6.1 will
never meet it. Even if P6.1 did, line 4669-4671 tells it to file an issue and
not add the row. Executed as written:

- P6.2 applies a table whose "Why" cell a reader can disprove with the grep
  it quotes. A careful agent either stops or logs a false justification.
- P6.3 publishes Luft, Deussen under "Read during design, no technique here".
- One implemented technique cites nothing, against D24.

The same table has a second false evidence string. The Postman's Knock row
(4785) says "`blob` occurs only in `letters/`". It also occurs in `ink/`
(`deposit.py`, `chains.py`, `brush_style.py`) and in many `maps/` modules
(`generalise.py`, `masks.py`, `osm.py`, `layers.py`, `style_groups.py`). That
row's conclusion still holds: those are wood and park generalisation blobs,
and no code trims the extent. Only the evidence is wrong.

**Fix:**

1. Add a seed row, for example `wet-area-bleed` | "bleed inside a shared
   wet-area map" | `pyntpot.ink.wash.wash`. Its candidate canonical source is
   Luft, Deussen 2006 (`10.1145/1124728.1124732`, rule 2), unless the
   maintainer prefers Curtis's wet-area mask; decide it in the plan.
2. Move Luft, Deussen to that row: as "the canonical source above" if it is
   the canonical, else as its own `Design input` line. Add `wet-area-bleed`
   to Curtis's row as a `Design input` line with the grail URL.
3. Update the "besides the six" count (4797-4799) and the route-3 expectation
   (4889-4890). Luft's route-3 lookup is unchanged.
4. Correct the Postman's Knock evidence: blobs exist in `maps/` for woods and
   parks, and none trims the extent.
5. Before the next review, re-run every grep the match table quotes and paste
   the outputs into the run log.

### B. Route 2 cannot be reached for three Elsevier canonical sources (4541-4545, 4579-4580, 4452-4457)

Route 2 applies only when "the publisher page is not 200 or is a challenge
page". Probed through the proxy, `curl -sSL https://doi.org/<DOI>` gives:

| DOI | Result |
|---|---|
| `10.1016/0146-664X(74)90028-8` (Chaikin) | **200** at `linkinghub.elsevier.com`, `<title>Redirecting`, a meta-refresh page with no title or author |
| `10.1016/B978-0-12-079050-0.50020-5` (Catmull, Rom) | **200** `Redirecting` |
| `10.1016/S0734-189X(86)80047-0` (Borgefors) | **200** `Redirecting` |
| UTP, SIAM, Taylor and Francis, Wiley | 403 Cloudflare challenge (route 2 applies) |
| AMS (Duchon) | 403 CloudFront |
| IEEE (Wells, Horn) | 202 with an empty body (route 2 applies: not 200) |

For the three Elsevier sources, followed literally:

1. Route 1 fails *match*.
2. Route 2's precondition is false: the page is 200, and a meta-refresh page
   is not the Cloudflare "challenge page" the tool facts define.
3. Routes 3 to 6 do not apply.
4. Route 7 fires only on "not 200, a challenge page, or a 404".
5. Route 8 gives `not-verified`.

Then the canonical-source rule finds no replacement, because rule 1 makes
the eponym's paper the only answer. A re-try gives the same result every
time. So P6.3's gate stays red forever, and P6.4 never starts. The status
definition of `verified-via-index` ("own page is blocked or absent") is
looser than route 2's precondition, so the plan disagrees with itself here as
well.

**Fix:** "Route 2 applies to any source with a DOI whose route 1 did not
match, whatever the status", and route 7 likewise "to any source with a URL
whose route 1 did not match". Add the Elsevier 200 `Redirecting` page to the
tool facts.

## [SHOULD-FIX]

### S1. P6.5a to P6.5e are forced into sequence without a real dependency (4202-4211)

I checked whether they can run as parallel sub-agents in separate worktrees.

**Disjoint files: yes.** I expanded the five groups' paths (5077-5083)
against `src/pyntpot`. They partition the 108 `.py` files exactly: no
duplicate, no file missing, no path that does not exist. The c and d line
counts are as stated (4,461 and 4,574).

**The stated reasons for sequence do not hold.**

1. "Every slice appends to the run log and most to `docs/issues/`." P3
   already solved this for parallel worktree lines (631-648). Shared
   append-only files are allowed there, and the second slice to land rebases
   over the conflict. Because the implementer never commits, the
   orchestrator can also append each slice's log entry itself at landing.
2. "Bottom-up, so a `maps` docstring reads an already-corrected `ink`
   docstring." Two problems:
   - It is not a dependency. Under the behaviour-wins rule (4112) the code is
     the truth, so a `maps` docstring is checked against the `ink` code.
   - The plan does not follow it inside `maps` anyway. P6.5c (façade:
     `pipeline`, `compose`, `basemap`, `plates`) runs before P6.5d
     (geometry, painter) and P6.5e (lettering), and those are the layers the
     façade calls.

**What must change to allow parallel runs** (all small):

- **Hard-coded checkout path.** `ast_neutral.py` (4034) and `doc_lines.py`
  (5173) are run as `cd /home/user/pyntpot && ...`. In a worktree this
  checks the main checkout. Say "from the slice's worktree root".
- **Shared scratch.** If sub-agents share the orchestrator's `$SCRATCH`, the
  G-self baseline `$SCRATCH/before` (558-560), `$SCRATCH/doclines` and the
  scripts collide. Give each slice `$SCRATCH/<slice-id>/`.
- **`GLOSSARY.md`.** It is an owner file of every P6.5 slice (5099), and row
  edits next to each other conflict. Either P6.5 sessions only *propose*
  glossary corrections in the hand-off, which P6.6 (already an owner) or the
  orchestrator applies; or keep P3's append-only rule.
- **`docs/issues/` slugs.** Two groups can file the same identifier synonym
  under the same slug. Make the orchestrator de-duplicate at landing, or put
  the module in the slug.
- **Wall times.** Five concurrent G-here runs, each with byte-exact goldens,
  inflate the stage times that feed the HTML report. Log each one as
  measured under parallel load.
- **Landing.** Keep "one commit per slice, in order". The orchestrator
  rebases each slice onto the previous landed commit and re-runs G-here plus
  `ast_neutral.py` against it before committing, as P3 does.

P6.0 to P6.4 and P6.6 have real dependencies and stay sequential. P6.3 must
stay single-threaded because of the Crossref concurrency limit of 1.

### S2. The `maintainer-checked` bound is defeated by P6.3's own logging, and a missing design-input line goes undetected (4949-4951, 4881-4886, 5000-5001)

`refcheck.sh` passes `maintainer-checked` when `index(runlog, url)` finds the
URL anywhere in the run log. Probes, with the real run log plus fake lines:

- **P6.3 writes the URL itself.** Step 1 logs "URL fetched" for every source
  (4883). After P6.3 runs, every design-input URL is in the run log. I
  appended one P6.3-style fetch line for the Stamen URL; then
  `- Design input: Watson ... https://stamen.com/watercolor-process-3dd5135861fe/ [maintainer-checked: run log; 2026-10-07]`
  gives **exit 0**.
- **Prefix match.** `https://github.com/` and `https://thepostmansknock.com/`
  on `maintainer-checked` lines both give **exit 0**: substring prefixes of
  the logged URLs.

So the plan's claim that it "exits 1 ... on a design input whose URL is not
in the run log" is true on today's log and vacuous by the end of P6.3.

**Fix:** make it a closed list, like `named-only`. Hard-code the two URLs
logged at 14:05 in `refcheck.sh` and require each to appear exactly once.

**Separately:** nothing checks that every match-table line was written.
Dropping the Bousseau, Baxter or MoXi `Design input` line passes every
mechanical check, because they have no URL in `design-sources.md`. **Fix:**
pin the expected number of `Design input:` lines per key (from the match
table) and the expected number of `Read during design:` lines, and check
them.

### S3. `doc_lines.py` writes into `src/` when given absolute paths, and the gate passes vacuously on empty input (5165-5175, 5194-5200)

- **Absolute paths.** `out / f"{name}.txt"` with an absolute `name` discards
  `out`. On a scratch clone, `doc_lines.py $S/doclines2 $PWD/src/pyntpot/ink/sheet.py`
  wrote `src/pyntpot/ink/sheet.py.txt` into the tree (`git status`: `??`).
  Agents in this environment are told to use absolute paths.
- **When it is caught.** `ast_neutral.py` catches the untracked file. But in
  P6.5's gate order, `doc_lines.py` runs *after* it, so the file can reach the
  slice commit. The next catch is the phase gate's whole-branch check.
- **Empty input.** If `$SCRATCH/doclines` is empty, the detector prints a
  usage error and exits 2. "Every finding has a `kept:` line" is then
  trivially true.
- **Unspecified file list.** `<group files>` is never given as a command. The
  table's brace paths are relative to `src/pyntpot/`, while the scripts need
  repo-relative paths.

**Fix:**

- The script refuses an absolute path or a path outside `src/`
  (`Path(name).resolve().relative_to(Path.cwd() / "src")`).
- Each slice starts with `rm -rf "$SCRATCH/doclines"`.
- Give each slice a literal file-list command (for example
  `git ls-files 'src/pyntpot/ink/*.py'`). The gate checks that the number of
  `.txt` files equals the group's file count, and reads the detector's
  summary line, not its exit status (it exits 1 whenever findings exist).

### S4. `Note:` lines will be written from memory (4904-4907, 4421)

P6.3 step 3 asks for a `Note:` line "where the code departs from the
source". That needs the source's *content*, but most canonical sources are
checked from Crossref metadata only: their pages are 403, 202 or Elsevier
redirects. The plan pins these notes: Lanczos through Pillow, the chamfer
weights, hillshade central differences, the marching-squares "2-D case" and
the `nib` rule-5 note. For every other row, an agent will write claims about
a paper it has not read, and two sessions will write different ones. Those
claims end up in the published bibliography, against D24's "never from
memory".

**Fix:** a `Note:` line only on the rows the plan pins, or where the
departure is visible in a body P6.3 saved under `$SCRATCH/refs/` and quotes
in the log. Otherwise there is no `Note:` line. This narrows the plan and
does not contradict it, so it can go in the P6.3 brief.

### S5. P6.3 is at the limit of what one fresh agent can follow; say what each brief carries

Single-slice load, counting the preamble each slice needs:

| Slice | Needs | Brief size | Verdict |
|---|---|---|---|
| P6.5x | phase rules (4022-4218), the public-API table, the skills tool fact, its own body | about 400 lines | followable |
| P6.1, P6.2, P6.4, P6.6 | | under 400 lines each | followable |
| P6.3 | some phase rules (about 70 lines), the tool facts (4220-4395), the format, statuses, routes and *match* (4397-4612), the match table, its own body (4809-5008) | about 720 lines | at the limit |

P6.3 also asks for:

- 8 routes, 6 status outcomes and 2 fixed lines;
- a precedence rule, a pacing rule and a five-case canonical-source rule;
- a 50-line awk script;
- about 45 sources processed at 2 s pacing with backoff.

About 60 of P6.3's lines are evidence, not instruction: the MoXi derivation
(4296-4308), the Postman's Knock probe history (4355-4370), the p5-watercolor
probe (4336-4347) and the `refcheck.sh` proof (4987-5001). **Fix:** add one
line per slice naming the preamble blocks its brief includes, and mark the
evidence paragraphs as "for the reviewer, not the brief". The orchestrator
can do this when it composes the briefs.

## [CONSIDER]

- **Dispatch P6.3 as two sub-agents in sequence within one slice and
  commit.**
  1. Fetch and assign: needs the tool facts, routes, *match* and statuses.
     Writes one evidence row per source to the run log: fields, status and
     how-checked text.
  2. Write `references.md` from those rows and run the mechanical checks:
     needs the format, URL rule and `refcheck.sh`.

  The seam is the run log, which already holds every field. This halves the
  instruction load of the hardest slice without adding a file.

## Nits

1. **Exhausted fetch vs replacement (4250-4256 vs 4826-4828).** An exhausted
   fetch "never moves to the next candidate". The canonical-source rule
   replaces a `not-verified` candidate "for a reason other than a rate
   limit". After a 5xx or a reset, those two disagree. Say "other than an
   exhausted fetch".
2. **The `kept:` line (5181, 5197).** Say that `<file>` is the source path,
   not the detector's `$SCRATCH/doclines/...py.txt` path. Say that line
   numbers come from the final rerun: an accuracy fix added earlier in the
   file shifts them.
3. **`refcheck.sh` ignores malformed lines (4937).** Its grep only sees
   lines that begin with exactly `- Canonical source:`, `- Design input:` or
   `- Read during design:`. A `- Design Input:` line, or an indented
   `  - Design input: ... [not-verified: ...]`, is never checked: both probes
   give exit 0. Add a check that every `- ` line under a `## ` entry starts
   with one of the five labels.

## Counts

2 blocking, 5 should-fix, 1 consider, 3 nits. All 14 round-2 findings are
resolved.
