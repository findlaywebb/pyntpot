# P6 plan review 4

Reviewed: `specs/001-port/plan.md`, section `### P6. Docstrings, prose and
references` (lines 3952 to 5646), branch `p6-docs` at `6c1e380`. Read against
`reviews/p6-plan-review-3.md`, `git diff f6698e4 6c1e380 -- specs/001-port/plan.md
specs/001-port/tasks.md`, `spec.md`, `design-sources.md`, `p6-run-log.md` and
the repository.

These decisions are settled and are not re-opened here: the run-log decisions
at 13:05, 14:05 (including the `maintainer-checked` precedence), 14:40, 15:10
and 15:45, and the total length of the section.

Probes were run on 2026-10-07 in a scratch directory outside the repo:

- `refcheck.sh`, `doc_lines.py` and `ast_neutral.py`, extracted verbatim from
  the plan with the two-space indent stripped. All three parse.
- `refcheck.sh` on a generated `references.md` with all 23 entries at their
  pinned counts. It was run against the real run log and against modified
  copies of it.
- The five P6.5 file-list commands, run under bash.
- The match-table greps, and the P6.1 tally, run in the main checkout.
- The seven design-record web pages, the Chaikin DOI and The Postman's Knock,
  fetched through the proxy 2 s apart, with bodies folded as in *match*.
- `uv run pytest -m golden --golden-tolerance` alone, timed and with its peak
  memory measured.

## Verdict: SOUND-WITH-FIXES (2 blocking, both small)

The most important change: **the "blocked page" rule that was widened for the
Elsevier stubs also catches live web pages whose design-record title is a
paraphrase.**

- One of those pages, the ICA Wainwright page, then fails *match* on two
  fields.
- It would be published as `unreachable`, even though it answered 200 and is
  plainly the work.

All round-3 findings are resolved. The two parts of fix A that the fix agent
rejected were rightly rejected.

## Round-3 findings

| Finding | Status | Evidence |
|---|---|---|
| A: the wet-area bleed is missing, and two greps were false | Resolved | See the detail below the table. |
| A3: the "besides the six" count, rejected by the fix agent | **Rejection right** | Of the 23 rows, 13 get lines from the table, and 6 are the "not recorded" rows (`lanczos`, `zhang-suen`, `marching-squares`, `chamfer-distance`, `fbm`, `value-noise`). That leaves exactly `catmull-rom`, `hachures`, `nib` and `label-placement`. `wet-area-bleed` takes its lines from the table, so it never joins the no-line list. The count stays four. |
| A3: "Luft's route 3 is unchanged", rejected by the fix agent | **Rejection right** | `design-sources.md` gives Luft, Deussen no year. Route 3's selection rule needs the year to match (4674-4678), so route 3 would always fail for Luft. Luft is now the canonical source, with its DOI fixed (4353-4364). Its design-input line is the fixed "canonical source above", which carries no status. So no route applies to the design input. The expected route-3 list (4350-4352, 5063-5065) correctly drops Luft. |
| B: Elsevier 200 stubs | Resolved, but see new B1 | See the detail below the table. |
| S1: P6.5a-e can run in parallel | Resolved | See "Parallel P6.5a-e worktrees" below. |
| S2: the `maintainer-checked` bound | Resolved | See "`refcheck.sh` against the real run log" below. |
| S3: `doc_lines.py` | Resolved | It refuses an absolute FILE (exit 1) and an empty list (exit 1). The `letters` group gives `doc_lines: 8 files`, 8 header lines, and `git status` stays clean. The gate counts header lines, not the exit status. |
| S4: `Note:` lines written from memory | Resolved, with a caveat (S4 below) | 5087-5099. |
| S5: what each brief carries | Resolved in form, with gaps (B2, S3) | 4261-4275. |
| Consider: split P6.3 into two sub-agents | Adopted | 5040-5049. |
| Nits 1-3 | Resolved | Nit 1: 4985-4987. Nit 2: 5549-5555. Nit 3: 5221-5228. My probes confirm nit 3: `- Design Input:` and an indented bullet both fail. |

**A in detail.** These parts are fixed, and I re-checked each one in `src/`:

- The new seed row is at 4848.
- Curtis's row is at 4898, and Luft's at 4901.
- The candidate row is at 5035, and the fixed line at 4622-4623.
- The tally now has a `wet.?area` term (4797).
- At HEAD, `grep -rniE 'wet.?area' src` gives 11 lines, and the tally gives
  479 matches, 12 of them `wet.?area`.
- `ink/wash.py` 218-219 is the rim drop, and 228-230 is the bleed.
- `maps/painter/cover.py:32` is `wet_field`, called at 95 and passed as
  `WashOptions(wet=wet_map)` at 104.
- The Postman's Knock evidence is corrected.

**B in detail.**

- The blocked definition is at 4662-4671, and the tool fact at 4365-4391.
- My probe: `doi.org/10.1016/0146-664X(74)90028-8` gives 200 at
  `linkinghub.elsevier.com`, `<title>Redirecting`.
- In that body, the folded title is present and `chaikin` and `1974` are
  absent. So the page is blocked and route 2 decides, as the plan says.

## [BLOCKING]

### B1. The widened "blocked" test sends paraphrased web pages to the archive, and ICA ends `unreachable` (4662-4671, 4705-4707, 4732-4736)

**What changed.** The page is now blocked when its folded body "does not
contain the work's folded title, or ... the folded family name of every
author". Route 7 applies that same definition to a non-DOI page's own URL. But
`design-sources.md` was recovered from conversations, and its titles are
paraphrases.

**What the pages give.** Fetched and folded on 2026-10-07:

| Entry | Page `<title>` | Entry title in body | Entry author in body |
|---|---|---|---|
| Stadia Maps, "Stamen Watercolor style docs" | "Stamen Watercolor - Stadia Maps Documentation" | **no** | yes |
| ICA Map Design Commission, "MapCarte 95/365: A Pictorial Guide to the Lakeland Fells, Alfred Wainwright, 1955 to 1966" | "MapCarte 95/365: Pictorial Guide to the Lakeland Fells by Alfred Wainwright, 1955-1966" | **no** | **no** ("Commission on Map Design"; the post's author is @kennethfield) |
| Adventures in Mapping, 2024 | "Tolkien Style Maps in a GIS: part 3, Water" | the entry has no title | yes |
| Hobbs, Stamen, Urban Sketching, osmanyy | | yes | yes |

**What follows, executed literally.**

- **Stadia and ICA.** Both are "blocked" at 200 and go to route 7. The
  Wayback API answered 200 for Stadia today, but returned 429 for every
  request in review 2.
- **ICA fails *match* on two fields** (title and author), whether on the live
  page or a snapshot. Two fields means "not the one meant: try the next
  candidate", and a closing line has no candidate. So route 8 writes
  `unreachable: own page 200 ...` for a live, correct page. The gate passes
  it, and the report lists it as unreachable.
- **ICA's author** could also be read as matching, through "ICA" or
  "Commission", so two sessions may diverge.
- **Stadia**, at best, ends `verified-via-index` through a snapshot whose
  how-checked text says the live page was blocked.
- **Adventures in Mapping** has no defined title test at all.
- This was latent before round 3 for ICA's two-field mismatch. The widened
  rule adds the archive detour.

**Fix** (P6.2's table and the routes; route 5's pattern already exists):

1. Apply the title and author-absence clause only to a DOI's publisher page
   (route 2). For a non-DOI own page, "blocked" stays non-200 or a challenge
   page.
2. For each design-record web page, pin in P6.2's table the folded words its
   body must contain, as route 5 does for p5-watercolor. For example:
   - Stadia: `stamen watercolor`, `stadia maps`.
   - ICA: `mapcarte 95 365`, `lakeland fells`, `wainwright`,
     `commission on map design`.
   - Adventures in Mapping: `adventures in mapping`, `2024`.
   - The other four: the entry's title and author.
3. Take the citation title from the page's `<title>`, and log it as a
   correction to the design record.

### B2. The P6.3-write brief lacks the rule-5 prefix, so `nib`'s canonical line is published as if Strassmann were its source (4272, 5000-5002, 5057-5060, 5090)

- Canonical-source rule 5 says that where no published work describes the
  technique as built, "the citation begins 'Nearest published work:'". The
  `nib` candidate row (5037) is exactly that case.
- P6.3-write writes `references.md` "from those rows ... only". Its brief
  row (4272) carries neither the canonical-source rule nor the candidate
  table.
- The evidence row's citation is "as the record gives them, corrections
  applied". Crossref's record of `10.1145/15886.15911` has no such prefix.
- Step 4 also points P6.3-write at "the weights, candidate table" (5090),
  which is a block it does not have.
- Literal execution therefore writes `- Canonical source: Strassmann, S.
  (1986). Hairy brushes. ...` for the pen nib, with no qualifier.

**Fix (one cell of the brief table):** add "P6.3's candidate table and the
canonical-source rule" to P6.3-write's row. Alternatively, have P6.3-fetch
put the prefix into the evidence row's citation fields.

## Fresh checks that passed

### `refcheck.sh` against the real run log (at `6c1e380`)

On the generated sample, with the real run log:

- Exit 0.
- It prints exactly the two `MAINTAINER-CHECKED` lines (p5-watercolor and The
  Postman's Knock).

Each of these probes exits 1:

1. **A fake fetch-logged URL.** I appended three P6.3-style lines for the
   Stamen URL (fetch, `attempt`, `evidence ... maintainer-checked`) and marked
   the Stamen design input `maintainer-checked`. Result: `FAIL` on each such
   line.
2. **A third marker line written by a slice.** Result:
   `3 maintainer-checked marker lines, want 2`.
3. **An indented, quoted marker line.**
4. **A trailing-slash variant of the marked URL.** Result:
   `0 lines, want 1`.
5. **The `https://github.com/` prefix.**
6. **A marked URL on a `Canonical source` line.**

The P6.3 dispatch precondition `grep -cE '^ *- maintainer-checked: https?://'`
prints `2`. The bound is closed, and it fails closed.

### Parallel P6.5a-e worktrees and the merge order

**The partition is exact.** The five file-list commands give 19, 8, 32, 28
and 21 files. Their union equals `git ls-files 'src/*.py'` (108 files), with
none listed twice. The three non-`.py` files under `src/` are in no group,
and `ast_neutral.py` rejects any change to them.

**No shared write path.**

- No test or `src/` code writes outside the checkout: there is no
  `Path.home`, `/tmp` or `gettempdir`.
- `.venv`, `.hypothesis`, `.pytest_cache` and `__pycache__` are per worktree
  and git-ignored.
- `$SLICE`, `$SCRATCH/wt/p6.5<x>` and `$SCRIPTS` are distinct, and none is
  inside a checkout. So `doc_lines.py`'s OUT check passes in a worktree.
- No hard-coded checkout path remains in P6.

**Landing works.**

- Each patch is cut against the P6.4 commit and touches only group files and
  module-slugged issues. The orchestrator's own GLOSSARY, run-log and
  `tasks.md` edits are not in any patch.
- So `git apply --index` onto each previous landing applies cleanly, and
  `ast_neutral.py <previous landed commit>` sees staged and working-tree
  changes.

**Load.** The container has 4 CPUs and 15 GB. One golden tolerance run took
317 s and peaked at 1.7 GB. Five concurrent runs fit in memory, and they will
be slow, as logged.

### `wet-area-bleed` sites

Both sites are correct, as checked under A above. The budget arithmetic holds:
`ink/wash.py` is 354 lines and gains 2 for each of its three sites, so 360.

## [SHOULD-FIX]

- **S1 (brief, P6.2): the `blob` count is wrong in a used checkout.**
  - In a checkout with `__pycache__`, which P6.1's own G-here creates,
    `grep -rliE 'blob' src | wc -l` gives **29**, not 16, because `-l` lists
    the matching `.pyc` files.
  - P6.2 would then file a false `docs/issues/match-table-evidence.md`.
  - Use `grep -rliIE`, which gives 16. The `-n` counts (48 and 2) are not
    affected, because binary-match notices go to stderr.
- **S2 (brief, P6.1): `fluid_modulate` is not pinned.**
  - `pyntpot.ink.wash.fluid_modulate` (`wash.py:309`, a `wet.?area` hit and a
    `shallow` hit) runs the shallow-water pass and multiplies the densities.
  - The plan pins `paint_fluid` as not a site, but says nothing of
    `fluid_modulate`, so the site rule leaves it as a judgement call.
  - Decide it in the plan, as a site or not a site of `shallow-water`, and
    name 309 in the `wet.?area` expectation at 4803-4807.
- **S3 (brief): briefs name blocks they do not carry.**
  - P6.1 must fill "the candidate canonical source from P6.3's table" (4858),
    which its row (4269) lacks.
  - Every slice that runs G-here or G-self needs those definitions and `$MG`,
    at plan lines 536-565, outside P6. No row lists them.
- **S4 (brief, P6.3-write): two pinned notes make claims about papers nobody
  fetched.**
  - The `chamfer-distance` note says the weights are "not her recommended
    3-4". The `hillshade` note says "not Horn's eight-neighbour weights".
  - Both papers were checked only from Crossref metadata (an Elsevier stub
    and an IEEE 202). These are the from-memory claims that S4 removed
    everywhere else.
  - State only the code fact, unless a saved body shows the paper's claim.
    The code facts are `noise.py:176` (weights 1 and 1.41421356) and
    `relief.py:136` (`np.gradient`).
- **S5 (brief, P6.3-write/P6.4): an entry with no `Implemented in:` line
  passes every gate.**
  - Probe: removing `nib`'s `Implemented in:` line still gives refcheck
    exit 0.
  - P6.4's two tests then pass vacuously for that key.
  - Extend the fourth mechanical check to "exactly one `Implemented in:`, at
    most one `Note:`", or have `test_reference_keys.py` fail on an entry with
    no path.

## Nits (4)

1. **4608-4611: the marker-line sentence is out of date.**
   - "The maintainer rewrites those two entries as marker lines before P6.3
     is dispatched" is already done.
   - The lines were added in `6c1e380`, by the orchestrator, from the 14:05
     check. So "only the maintainer writes a marker line" does not describe
     what happened.
   - Put it in the past tense, so an orchestrator does not wait for the
     maintainer.
2. **5401-5402: the landing base and timing are unclear.**
   - "P6.5a on the P6.4 commit" contradicts the optional
     `Log P6.5 dispatch` commit.
   - The landing G-here is "measured alone" only if landing starts after all
     five hand-offs. Say that it does.
3. **4154-4158: the slug rule contradicts its example.** The rule says every
   slug begins with the module path, but its own example,
   `line-budget-ink-brush.md`, does not. Say that the landing check accepts
   the `line-budget-` prefix.
4. **5180: a `]` in how-checked text fails `refcheck.sh`.** The status regex
   uses `[^]]+`, so how-checked text quoting Baxter's `issued` `[[null]]`
   fails. Tell P6.3-write not to put a `]` in how-checked text.

## Counts

- 2 blocking, both new. B1 is a regression from the round-3 fix B; B2 is a
  brief gap.
- 5 should-fix, all of which can go straight into a slice brief.
- 4 nits.
- All round-3 findings are resolved, and both rejections by the fix agent are
  correct.
