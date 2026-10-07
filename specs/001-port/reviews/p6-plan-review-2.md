# P6 plan review 2

Reviewed: `specs/001-port/plan.md`, section `### P6. Docstrings, prose and
references` (lines 3952 to 4946), branch `p6-docs` at `c505e5b`. Read against
`reviews/p6-plan-review-1.md`, `git diff 93aee17 c505e5b -- specs/001-port/plan.md`,
`spec.md` (D24, D25, acceptance 4), `design-sources.md`, `tasks.md` and the
repository. The maintainer's Args/Returns decision of 2026-10-07 is taken as
settled and not re-opened. Probes were run on 2026-10-07: the AST-neutral
script on a scratch clone outside the repo, `refcheck.sh` on fake entries, the
seed sites resolved by file and AST, Crossref through the proxy at 2 s
spacing, and the design-sources pages and repository.

## Verdict: BLOCK

The single most important change: **give P6.3 an end state for a source
that is fetched, checked and logged, but cannot be matched.** As written,
`not-verified` is never final and the only way to clear it is a re-try under
the same rules. Two entries in `design-sources.md` fail deterministically
today, so P6.3's gate can never go green and P6.4 can never start. The
second blocker is the same kind of problem in P6.5: its jargon gate demands
"0 to rewrite", but the detector flags code identifiers that P6 is not
allowed to touch.

## Round-1 findings

All 21 are resolved in the plan text. B3 and B4 leave something behind,
reported below as new findings (S4, and blocker A).

| Finding | Status | Evidence |
|---|---|---|
| B1 AST-neutral rejects an added docstring | Resolved | I ran the script verbatim (4044-4086) on a scratch clone. These exit 0: a docstring added to nested `dx`, a module docstring edited, a docstring deleted, a comment added, a mode change. These exit 1: `- a` to `- (a + 0)`, a bare string after a docstring, an untracked file, a staged new file, a rename (R100), a deleted file, a TOML edit. |
| B2 Args/Returns boilerplate | Resolved | Rule at 4859-4870 follows the maintainer decision. The public API table matches `__all__` (one count is off, N1). The size projection is plausible: `letters/hand.py` is 229 lines and `ink/sheet.py` 117. |
| B3 Format and a vacuous check | Resolved, with a residual (S4) | One line per source, each with its own status. `refcheck.sh` fails on `not-verified`, on a `named-only` canonical line and on a status-less line, and it passes the plan's own example. |
| B4 No lookup route; closing entries | Resolved, with a residual (blocker A) | Route 3 is defined, closing-section URLs are fetched (4704-4709), and `named-only` is a closed list. |
| S1 KM route-5 citer | Resolved | Kubelka 1948 record re-fetched: ref `josa-38-5-448-R4` is as quoted. The venue-prefix rule matches "zeits f tech physik" to "zeitschrift für technische physik". |
| S2 W3C maturity and match | Resolved | 4657-4660 and 4470-4472. |
| S3 Rules vs table | Resolved | The table is authoritative (4645). Lewis 1989 re-fetched: 200, "Algorithms for solid noise synthesis", Lewis, 1989, *ACM SIGGRAPH Computer Graphics*. The `value_noise` body (`noise.py:26-46`) is a smoothstep lattice of random values, as stated. |
| S4 Non-goals on public API | Resolved | 4147-4159. |
| S5 Open inclusion rule; WCAG | Resolved | Decided-terms table at 4511-4521. WCAG dropped: no luminance or contrast computation exists (grep confirms). |
| S6 Retry end state | Resolved | 4231-4245. |
| S7 Helper signatures | Resolved | `_ast_checks` exports `PACKAGES`, `REPO_ROOT` and `_source_files`, as used by `test_docstring_conventions.py:20`. |
| S8 OpenLibrary author | Resolved | 4309-4315 and 4439-4441. |
| Nits 1-9 | Resolved | Base `92b011c` equals `git merge-base HEAD origin/main`, and `git diff 92b011c HEAD -- src tests` is empty. The dash counts (15 in `docs/decisions`, 1 in the runbook, 0 in `src`) hold with `grep -I`. |

## Verified, no action

- **Seed sites.** All 26 dotted paths resolve by file and AST at `c505e5b`,
  at the stated lines, and every one already has a docstring. The
  `shallow-water` correction is right: `ink.wash` line 330 calls
  `ink.shallow_water.shallow_water`.
- **Three sites spot-checked by reading the body:**
  - `value_noise` is lattice value noise.
  - `_reduce` applies `Image.Resampling.LANCZOS`. `maps/compose.py` has
    four more LANCZOS calls. P6.1's "any function whose own body the tally
    places a seed term in" reaches them; the site rule decides.
  - `Sheet.pits` is a method with Args and Returns, so the citation goes
    before `Args:`.
- **Crossref, 2 s spacing, all 200, no 429:**
  - Lewis 1989: as above.
  - Kubelka 1948: 8 references, R4 as quoted.
  - Baxter, Lin route 3: top hit `10.1109/pccga.2004.1348363`, `issued`
    `[[null]]`. The container-title year 2004 matches, so the selection rule
    picks it.
- **Docstring consumers.** Nothing in `src/` reads `__doc__`. The CLI's
  argparse `description` is a literal. `Style.digest` hashes dataclass
  fields, not schemas. `src/` has no directive comments (`noqa`,
  `type: ignore`, `pragma`). A docstring or comment edit cannot reach a
  pixel, a digest or a gate.
- **Citation line.** 66 characters at most (`midpoint-displacement`), well
  under ruff's 100. "Source" is not a pydocstyle Google section name.
- **Coordinate gate.** It does not trip on DOIs (`38.000448` is preceded by
  `.`, which the lookbehind excludes).

## [BLOCKING]

### A. `not-verified` has no end state, and two design-sources entries fail deterministically (4387-4389, 4442-4443, 4665-4672, 4241-4243, 4929-4932)

The plan makes `not-verified` "never final". The only route to clear it is
"a fresh re-try of only those entries under the pacing rule" (4671, 4931),
and the canonical-source replacement rule (4647-4649) applies only to
`Canonical source` lines. A source that fails for a reason a re-try cannot
change therefore keeps P6.3 red forever. "P6.4 does not start while P6.3's
gate is red" (4672). Two such sources exist today:

1. **The Postman's Knock** (`https://thepostmansknock.com/illustrated-wedding-maps/`,
   a closing-section entry). The fetch returned `403`, `server: cloudflare`,
   `cf-mitigated: challenge`, `<title>Just a moment...`. A HEAD retry got the
   same answer. A 403 is not in the 429/5xx/reset retry set. Routes 2 to 6
   don't apply: no DOI, no ISBN, no repository, no citing work. It is not on
   the `named-only` list, because it has a URL. A Wayback lookup
   (`archive.org/wayback/available`) answered 429 twice, so that is not a
   dependable fallback either.
2. **axelinternet/p5-watercolor** (route 5). `git clone --depth 1` works.
   - The README's title is "Watercolor canvas" and it names no author.
   - There is no licence file.
   - `package.json` names the *boilerplate's* author, Michael Kontogiannis,
     which would mislead.
   Route 5 needs "its README names the title and author" (4443). Both fields
   fail, and *match* says "a mismatch in two or more means the source is not
   the one meant" (4473). The result is `not-verified`, every time.

This also contradicts the design record. `design-sources.md` lines 4-7 say:
"an entry that cannot be verified is recorded there as 'cited in design, not
verified'". The maintainer constraint is that "unrecoverable design inputs
cite the canonical source and are marked so". Both expect a marked end state
for a design input. The plan offers none, so the agent must either break the
gate or improvise a status, and both break "no stop points".

**Fix:**

- Add a fifth status, for example `checked-unmatched`. It is allowed only on
  `Design input` and `Read during design` lines, never on `Canonical
  source`, and only when:
  - every applicable route was tried and logged, and
  - the failure is deterministic: a challenge or 403/404 page, or a body
    that fails *match*. Never a 429, 5xx or reset.
- The how-checked text states what was fetched and what failed, an issue
  file is filed, and `refcheck.sh` accepts it on those labels only.
- The row's canonical line (always verified) then carries the technique.
  That is what the maintainer constraint already asks for.
- Separately, give route 5 a match a repository can pass. The URL's
  owner/name equals the entry's author and title, `git ls-remote` succeeds,
  and the README names the technique or its upstream ("p5 implementation of
  [Tyler] Hobbs generative watercolor simulation"). Then p5-watercolor
  verifies instead of needing the new status.

### B. The P6.5 jargon gate cannot pass: the detector flags code identifiers (4888-4891, 4876-4878, 4320-4323)

The P6.5 gate requires `detect_ai_jargon.py <group files>` to report "0 to
rewrite". I ran it over every `src/**/*.py` at `c505e5b`: 36 findings, 50
flagged lines. Many sit on executable lines that P6 may not change, because
the AST-neutral check forbids renames:

- `letters/nib.py`, 17 lines, among them 173, 175, 179, 190, 212, 227, 273,
  289-291, 299 and 333. These are the `surface` parameter and the
  `surface.canvas` attribute reads.
- `maps/attribution.py:80` and `:87`.
- `maps/lettering/pipeline.py:228` and `:235`, `surface = nib.NibSurface(`.

So P6.5b, P6.5c and P6.5e can never meet their gate. The tool's own output
also says: "Each one is a claim to check, not an order: if the flagged word
is the precise one, keep it and say so". Here "surface" is the precise word
for the paper surface in `ink/sheet.py:8` and `ink/pigment.py:45`. The plan's
evidence for the tool ("0 findings at P6.0 on `ink/wash.py`, `README.md` and
`docs/explanation/performance.md`") sampled three clean files.

**Fix:** gate on docstring and comment lines only. Every finding on such a
line is either rewritten or logged as `kept: precise term | <reason>`, and
code-line findings are logged as `out of scope: identifier`. The check is
"no unlogged finding", not "0 to rewrite". Say the same for "swappable"
findings: the current gate ignores them, while 4877 says fix each finding.

## [SHOULD-FIX]

### S1. The P6.2 match rule is semantic, and several entries will be matched differently by two sessions (4603-4623)

The plan pinned the canonical candidates (4645, review-1 S3) but left the
design-input matches to "its right-hand note names that row's technique or
effect". Against `design-sources.md`, these entries match ambiguously:

| Entry | Ambiguity |
|---|---|
| Van Laerhoven | "Kubelka-Munk compositing in place of multiply": `kubelka-munk` only, or also `multiply-compositing`? |
| Stamen | "mask, blur, noise, texture and multiply recipe; paper grain; rim darkening via blurred mask": anywhere from 1 to 6 rows (`multiply-compositing`, `box-blur`, `fbm`/`value-noise`, `granulation`, `edge-darkening`) |
| Bousseau | "distance term": `edge-darkening` only, or also `chamfer-distance`? |
| MoXi | "ink starvation; brush reservoir": `bristle-brush` or `nib`? |
| Luft, Deussen | "shared wet-area map": no row clearly fits. The hand-off "expects none" unmatched, yet it is not on the no-technique list. |
| Wainwright | "hatching moire warning": `hachures` or none? |
| Postman's Knock | "bleed the edge": `edge-darkening` or none? |
| p5-watercolor | "implementation reference for the Hobbs method": names no technique literally |

These choices end up in the published `references.md`. **Fix:** decide them
in the plan as a table (entry to rows), the way the candidates were decided.
P6.2 then applies the table and logs it.

### S2. The URL rule contradicts the example and the URL-completeness check for Curtis (4363-4366, 4349, 4737, 4423)

- The source-line rule says the URL is `https://doi.org/<DOI>` "where a DOI
  exists". Curtis has one (`10.1145/258734.258896`, in the candidate table).
- Followed literally, every Curtis line carries the DOI. Then
  `https://grail.cs.washington.edu/.../paper_small.pdf` appears nowhere, and
  the URL check at 4737 prints `missing`.
- The format example (4349) uses the grail URL instead.

Route 1 also says "the DOI or URL" without saying which to try first. So the
same work gets `verified` (PDF) or `verified-via-index` (ACM 403, then
Crossref) depending on the session. **Fix:** "a design input's URL is the
one `design-sources.md` gives; a canonical line's URL is `doi.org` when a
DOI exists; route 1 tries the line's own URL".

### S3. Route 3 picks a different MoXi DOI from the one in the tool facts (4275-4278, 4431-4438, 4702-4703)

MoXi has no DOI or URL in `design-sources.md`, so route 3 applies. The
step-1 "expected" list omits it, though. I ran the search, and the first
hit passing title plus year is `10.1145/1186822.1073221` (*ACM SIGGRAPH 2005
Papers*). The tool facts name `10.1145/1073204.1073221` (*ACM Transactions on
Graphics*), which is third. A session that reads the tool facts uses one; a
session that follows route 3 uses the other. **Fix:** "a design input whose
DOI is listed in the tool facts uses that DOI (routes 1 and 2); route 3
applies only to the rest", and add MoXi to that list.

### S4. `named-only` is not bounded by the mechanical check (4376-4386, 4725, 4747-4749)

`refcheck.sh` accepts `[named-only: ...]` on any `Design input` or `Read
during design` line. I tested
`- Design input: Van Laerhoven (2005). Real-time. [named-only: lazy; ...]`
and it passes. The plan says "a `named-only` line with no item there is a
failure of the check", but nothing mechanical enforces that; it is a log
pairing done by hand. That makes `named-only` a way to skip a fetch
unnoticed, which goes against "every reference is fetched". **Fix:** give
each closed-list item a fixed citation string, and make `refcheck.sh`
accept `named-only` only on lines whose citation is one of those strings.

## Nits

1. **Method count.** The public classes have 20 public methods plus
   `Hand.__init__`, which makes 21, not "21, plus `Hand.__init__`" (4001,
   4004). The 15 that lack a section are listed correctly.
2. **The date is not enforced.** The status regex (4723) does not require
   the `; YYYY-MM-DD` that the source-line format requires (4363). Append
   `; [0-9]{4}-[0-9]{2}-[0-9]{2}\]$`.
3. **HTML entities.** *Match* on a web body (4467-4470) does not say to
   decode them first. Two fetched bodies carry `Osman&#39;s` and
   `&#8211;`. Decode with `html.unescape` before folding.
4. **One design-sources bullet can hold two works.** Deegan with the arXiv
   study, Lee with WetBrush, Douglas-Peucker with Chaikin. "One
   `Design input:` line per matched entry" (4338) and the closed list,
   which names them separately (4379-4381), disagree on one line or two.
5. **Fields not from any record.** The Kubelka-Munk citation's last page
   (601) and title come from no fetched record. The how-checked text
   discloses the title and the second author but not the page range (4348,
   4677). D24 says "never from memory": either mark it, or cite `593` only.
6. **Scratch scripts in fresh sessions.** `$SCRATCH` does not survive a
   session, yet P6.6 step 3 reruns "the P6.3 mechanical checks", which need
   `refcheck.sh`. Say that every consuming session writes `ast_neutral.py`
   and `refcheck.sh` verbatim from the plan block, indentation stripped.
7. **Inventory columns.** P6.3 adds a status column to `p6-inventory.md`
   (4641) that P6.1's column spec does not reserve (4581). The key grep
   (4733) takes any backticked first cell in the file, so a second table
   there would pollute it. Say "one table only".
8. **Dashes outside titles.** The dash rule (4165-4170) covers titles
   only. Crossref container titles and page ranges can carry U+2013 too.
   Apply the rule to every copied field.

## Counts

2 blocking, 4 should-fix, 8 nits.
