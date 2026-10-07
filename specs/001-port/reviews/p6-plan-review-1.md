# P6 plan review 1

Reviewed: `specs/001-port/plan.md`, section `### P6. Docstrings, prose and
references` (lines 3952 to 4620), branch `p6-docs` at `73878bb`. HEAD is now
`c4c1533` ("Log P6.0", run log only). Read against `spec.md` (D24, D25,
acceptance 4), `design-sources.md`, `tasks.md` P6, the maintainer constraints
of 2026-10-07, and the repository. Reviewer ran read-only commands and paced
curl probes through the proxy (2026-10-07).

## Verdict: BLOCK

The single most important change: **fix the AST-neutral check so that adding
a docstring passes, and replace the blanket Args/Returns mandate with the
skill's "where it adds information" rule plus a bounded mechanical floor.**
As written, the gate rejects work the plan requires, and the shape rule turns
an accuracy audit into about 2,300 lines of boilerplate that overflows five
files.

### What holds (verified, no action)

- All 26 seed dotted paths resolve to the stated `def`/`class` at the stated
  line at `73878bb`. Every seed site already has a docstring.
- The measurement table matches exactly: modules, lines, defs, public defs and
  docstring lines per subpackage. Comment-line counts differ slightly
  (tokenizer count: ink 467 vs 433), which doesn't matter.
- The nine undocumented defs are as stated: 4 in `ink`, 4 in `maps` top level,
  1 in `maps/lettering`. All nine are nested helpers (`inside`, `dx`, `dy`,
  `down`, `interp`, `key`, `traced`, `kept_lines`, `chunk`).
- The P6.5c/P6.5d split covers every `maps/*.py` exactly once (4,461 and
  4,574 lines, as stated).
- Nothing in `src/` or `tests/` reads `__doc__` or `inspect.getdoc`. There is
  no `use_attribute_docstrings`, and there are no bare string statements
  besides docstrings.
- Dash counts are as stated: none in `src/`, 15 in `docs/decisions/`, 1 in
  the runbook.
- These all hold: `edt` weights 1 and `1.41421356`, `_shade` uses
  `np.gradient`, Crossref 200 for Duchon (percent-encoded), Borgefors, Imhof
  1975, Perlin 1985 and Strassmann 1986, grail PDF 200, WCAG 2.2 200.

## [BLOCKING]

### B1. The AST-neutral check rejects an added docstring, but the plan requires adding nine (lines 4009-4016 vs 4556)

`blanked()` sets an existing docstring's value to `""`. It leaves the `Expr`
node in the body. Adding a docstring to a function that had none therefore
adds an `Expr` node, and the dumps differ. I ran the plan's function verbatim:

```
add docstring neutral? False
delete docstring neutral? False
```

P6.5 says "Add the missing docstrings (nine at P6.0 across the tree)" (4556),
and the rule at 3997-3998 says a non-zero exit means "revert that hunk, never
commit it". An agent following both literally either drops required work or
edits the gate to get green. Either way the slice is wrong. **Fix:** remove
the leading docstring statement instead of blanking it:

```python
if isinstance(node, DOC_OWNERS) and node.body and _is_doc(node.body[0]):
    node.body = node.body[1:]
```

With that change, add, edit and delete are all neutral. Deletion is still
guarded: ruff `D` catches a missing public docstring, and
`test_reference_keys.py` catches a lost citation. While there, also fail on
untracked new files under `src/`. `git diff --name-only BASE` does not list
them: add `git ls-files --others --exclude-standard src`.

### B2. The shape rule mandates Args/Returns everywhere: an accuracy audit becomes ~2,300 lines of boilerplate and overflows five files (lines 4549-4556)

The rule at 4552-4555 requires "`Args:` for every parameter of a public
function and of a private one with three or more parameters; `Returns:`
unless it returns `None`". Measured with an AST script at `73878bb`:

- 398 functions fall under the Args rule, and 246 of them have no `Args:`.
- 365 functions with a non-`None` return annotation have no `Returns:`.
  The Returns clause has no public/private qualifier, so it reaches nested
  helpers such as `dx` and `inside`.
- 296 of 572 functions have one-line docstrings today. That is the repo's
  house shape.
- Filling the gaps adds an estimated 2,280 lines: ink ~470, letters ~200,
  maps top ~670, lettering ~530, candidates ~170, painter ~170,
  providers ~80.
- Five files would go over 400: `ink/polyline.py` (355, +~111),
  `maps/lettering/placement.py` (348, +~60), `maps/lettering/span_line.py`
  (385, +~53), `maps/lettering/spans.py` (373, +~32) and `ink/brush.py`
  (391, +~15).

Why this blocks:

1. **It conflicts with the skill the slice must read.** `docstrings/SKILL.md`
   says "Trivial/obvious function → one-line summary only. Don't manufacture
   empty `Args:`/`Returns:` sections" and "an edit must improve accuracy or
   information, not just taste". `conventions.md:43-45` and the rubric's
   *Filler* row say the same. "House rules beat the skills" (4066) covers
   CLAUDE.md only, and CLAUDE.md mandates no Args sections. The agent gets
   two contradictory instructions with no precedence rule between them.
2. **It makes line-budget outcomes arbitrary.** Rule (3) at 4062-4063 lands
   line-adding fixes "while the file stays at or under 400". In the five
   files above, whatever comes first in public-API order uses up the
   headroom. Boilerplate Args sections on early public names will push a
   real accuracy fix on a later private name into a `line-budget-*` issue.
   Accuracy should never lose to padding.
3. **It is scope creep.** D25 asks for an audit. It does not ask for a
   convention migration.

This is the decision that will age worst: a tree of templated `Args:` blocks
restating type-hinted parameters, which every later edit then has to keep in
sync.

**Fix:**

- Adopt the skill's rule: Args/Returns/Raises where they add information.
- Give a mechanical floor so no session re-decides it: "names in any
  `__all__`, and any function whose parameter meaning is not evident from
  name plus annotation".
- Exempt nested functions explicitly.
- Add a priority for the line budget: accuracy fixes land before shape
  fixes, by a two-pass order within a file.

### B3. The reference format is incomplete, and the "no unchecked canonical" check cannot fail (lines 4186-4219, 4221-4251, 4458)

- **No format for a recovered design input.** The template shows only the
  not-recorded variant of `Design input:` (4196). Most entries will carry a
  recovered input (Curtis for five keys, Hobbs plus p5-watercolor, Stamen,
  osmanyy, Horn, Douglas-Peucker, Chaikin, Chu-Tai, Baxter-Lin, Van
  Laerhoven, Bousseau, Luft-Deussen). The plan does not say:
  - whether each input gets a full citation and its URL. The P6.3 URL check
    effectively requires the URL.
  - how several inputs are listed.
  - how to write "the design input is the canonical source"
    (Douglas-Peucker, Chaikin and Horn are in `design-sources.md` as read
    sources).
- **One `Checked:` line, several sources.** Status is assigned "one per
  source" (4221), but an entry has one `Checked:` line (4198). Curtis via the
  publisher PDF, KM via route 6 and Van Laerhoven via Crossref cannot all be
  expressed on it. The maintainer constraint ("every reference is actually
  fetched and checked ... and the check logged") needs per-source status in
  the deliverable, not only in the log.
- **The verification is vacuous.** The check is
  `! grep -n 'Canonical source:.*not verified'`. Status is written on the
  `Checked:` line, never on `Canonical source:`, so this grep passes whatever
  P6.3 does. The same check is rerun as phase-gate step 3 (4606).

**Fix:** pin one line per source with its own status, for example

```
- Canonical source: <citation>. <url> [<status>]
- Design input: <citation>. <url> [<status>]
```

or a `Checked:` sub-bullet per source. Then make the check structural: every
`Canonical source:` line ends in one of statuses 1 to 5, or in the rule-6
marker. Also show an example entry with two design inputs.

### B4. Design inputs without an identifier have no lookup route, and it is unstated whether the no-technique entries are fetched (lines 4437-4447, 4201-4203)

P6.3 must "fetch every canonical and design-input source". About seven design
inputs in `design-sources.md` have no DOI or URL in either document:

- Van Laerhoven and Van Reeth 2005
- Bousseau et al. 2006
- Luft and Deussen
- Baxter and Lin 2004
- Deegan et al.
- the 2019 arXiv study
- Lee / WetBrush

The tool facts call OpenAlex search unreliable, and offer nothing in its
place. P6.2 says "does not search for more records". The agent will
improvise a discovery method and a hit-selection rule, which breaks "every
choice follows a written rule".

The route exists. I verified that Crossref
`GET /works?query.bibliographic=<title author>&rows=2` returns the right
work as the top hit for three of them:

- `10.1002/cav.95` (Van Laerhoven)
- `10.1145/1124728.1124751` (Bousseau)
- `10.1145/1124728.1124732` (Luft-Deussen; its subtitle "using a blurred
  depth test" is handled by the subtitle clause)

The second hits are near-misses by the same authors ("Real-time simulation
of thin paint media", 2005). That is why the selection rule must be "first
hit that passes *match*, else the next, max N, else route 6".

Separately, the closing section lists no-technique entries "with its status"
(4202). That implies a check, yet step 1 fetches only canonical and design
inputs. Say whether the about ten URLs there (Stadia, Wainwright, Adventures
in Mapping, Urban Sketching, Postman's Knock, the Stamen tiles notes) are
fetched and matched. The maintainer constraint says every reference is.
Also say what status a no-URL, no-title entry gets (the font, the providers,
"Named only").

## [SHOULD-FIX]

### S1. Route 5 for `kubelka-munk` has no working path (lines 4235-4238, 4416)

The plan's example citer is Curtis 1997, and it doesn't work:

- The Crossref record for `10.1145/258734.258896` has 0 references.
- Its PDF (fetched, `pdftotext`) cites Kubelka 1954 [21], Haase-Meyer [14]
  and Kortum [20]. It does not cite Kubelka and Munk 1931.
- Haase-Meyer 1992 (`10.1145/146443.146452`, 28 refs) doesn't cite it
  either.
- Kubelka 1948 (`10.1364/JOSA.38.000448`) does cite it. That Crossref
  reference reads
  `{"first-page":"593","volume":"12","author":"Kubelka","year":"1931","journal-title":"Zeits. f. tech. Physik"}`:
  first author only, and no title.

So the *match* rule (all author family names, year, title) fails, and the
library's central technique drops to rule 6, which replaces its canonical
line. **Fix:**

- Name Kubelka 1948 as the route-5 citer.
- Define a title-less reference match: first author, year, venue, volume
  and first page.
- State the expected entry text when the match is partial.

### S2. Rule 4 says "current Recommendation", but Compositing Level 1 is a Candidate Recommendation Draft (lines 4399-4401, 4417)

`https://www.w3.org/TR/compositing-1/` answers 200 and labels itself
"Candidate Recommendation Draft". WCAG 2.2 is a Recommendation
(12 December 2024). Read literally, rule 4 fails for `multiply-compositing`
and sends the agent to rules 5 and 6. Reword it to "the standards body's
current published version".

*Match* is also undefined for a standard with editors and no authors. Say
the entry's author is the body (`W3C`) and the match is title plus status
date.

### S3. The canonical-source rules contradict the candidate table (lines 4387-4410 vs 4411-4435)

- Rule 1 ("the eponym's paper") points Lanczos at Lanczos's own work, not
  Duchon 1979.
- Rule 2 ("first peer-reviewed description of the algorithm the code's body
  carries out") does not point to Borgefors 1986 for a two-pass (1, √2)
  chamfer. That is Rosenfeld-Pfaltz 1966 or Montanari 1968; Borgefors
  analyses weights and recommends 3-4.
- Rule 2 does not point to Perlin 1985 for `value_noise` either. Its body is
  a smoothstep-interpolated lattice of random values (`noise.py:26-46`),
  not gradient noise.
- "Applied in order until one verifies" invites the agent to re-litigate
  every row.

Either state that the table is authoritative and the rules apply only to
rows P6.1 adds and to candidates that fail to verify, or correct the
candidates. "First" is also not mechanically checkable; drop it.

### S4. "House rules beat the skills" misstates CLAUDE.md (lines 4066-4072)

CLAUDE.md says "**Module and public-API** docstrings are the agent contract:
purpose, key types, what it does *not* do, invariants". The plan confines
non-goals to module docstrings. That permits the skill's *Narrative* rule
(delete "what the code does not do") on public classes and functions.

Public API docstrings carry designed-gap text today. Example:
`maps/annotations.py` `Annotations`, "roads: Accepted and not read: road
names are never taken from a ...". **Fix:** non-goals and invariants stay in
module docstrings and in the docstrings of every name in any `__all__`.

### S5. The inclusion rule is open-ended, and the `wcag-contrast` seed row violates it (lines 4272-4293, 4327)

- **Rule (a) has no closed decision set.** It admits "a term of art with a
  published originating description". `src/` also names haversine (5 hits),
  bilinear (13), even-odd (4), scanline (6), flood fill (2), dither (15),
  supersampling (12), dilation (4) and erosion (2). None is on the grep and
  none is decided. Inventory size will vary by session.
- **The grep is not a filter.** It returns 826 hits in 87 of 108 files, and
  "read each hit's function body" amounts to reading the whole tree.
- **`wcag-contrast` fails rule (b).** Its site is `none`, and rule (b)
  needs "a code site implements it". "P6.1 checks the default theme's inks"
  has no outcome rule: keep or drop, and what if the inks fail 3:1?

**Fix:** list each of the terms above with a decided in/out. Make the grep
plus that list the complete search. Decide `wcag-contrast` here: either drop
it to the no-technique section, or add a clause (c) for value choices with
its check spelled out.

### S6. The Crossref retry policy has no end state, so a 429 can downgrade a status (lines 4132-4135)

Crossref answers with `x-rate-limit-limit: 5`, `x-rate-limit-interval: 1s`,
`x-concurrency-limit: 1` and `x-api-pool: public-single`. Even so, I got a
429 on the **fifth** call at 1.2 s spacing; the plan reports the 15th with
no pause. Retrying after 5 s worked. Add: after the 5/10/20 s retries, wait
60 s and repeat; never assign a status route on a 429, 5xx or reset; log
every retry.

### S7. The P6.4 helper signatures are underspecified (lines 4484-4491)

- `cited_keys(tree)` cannot return qualified names "under `pyntpot`" from an
  AST alone. Pin `cited_keys(module: str, tree: ast.Module)` and state which
  nodes it walks: top-level defs, classes and their methods; nested defs are
  excluded.
- Sibling architecture tests import `REPO_ROOT`, `PACKAGES` and
  `_source_files` from `._ast_checks`. Prescribe that rather than
  `support.REPO_ROOT`, or the new test diverges from the pattern.
- `pyntpot.ink.stamp` and `pyntpot.ink.wash` are both modules and, through
  `ink/__init__.py`, functions. File-based resolution (as written) is right;
  say so explicitly so the agent does not resolve by import.

### S8. Route 3 cannot match an author from the ISBN record alone (lines 4167-4170, 4232)

`openlibrary.org/isbn/9781589480261.json` gives
`"authors":[{"key":"/authors/OL1273097A"}]` and `by_statement: null`. The
*match* rule needs the family name. Add a second fetch,
`https://openlibrary.org<key>.json`, and match on `.name`.

## Nits

1. **A citation costs 2-3 lines, not one.** Rule (1) at 4058 says one line.
   A citation is 2 lines in a multi-line docstring (blank plus line) and 3
   when a one-liner becomes multi-line. Headroom is ample: the fullest site
   file is `ink/polyline.py` at 355 with three sites. `ink/brush.py` is not
   a site.
2. **The drift clause contradicts rule (1).** The clause at 4502-4505
   ("files it") would leave `test_every_site_cites_its_key` red. Delete it,
   since rule (1) says it always lands.
3. **The phase-gate base is ambiguous.** "<P6.0 commit>" (4601) becomes
   ambiguous once review rounds add commits. Name `92b011c`, the branch
   point. Local `main` is stale (`1c9aaa5` vs `origin/main` `92b011c`), so
   `git merge-base main HEAD` would be wrong.
4. **Commit rules disagree with practice.** "No trailers" (4091) contradicts
   the attribution trailers the session already writes (`c4c1533`).
   Orchestrator log commits such as "Log P6.0" fall outside "one commit per
   slice". State both.
5. **`GLOSSARY.md` has no `Today` column** (4543); it holds dotted names in
   the Meaning cell.
6. **The phase-gate dash grep reads binary files.** Step 5 (4610) greps
   `src/pyntpot`, which holds the binary font. Add `-I`; binary matches
   already occur, for example `tests/golden/lynmouth/map.png`.
7. **Titles copied from Crossref can carry dashes.** They can include U+2010
   or U+2013; the Van Laerhoven record has "Real‐time". Say whether titles
   are written with ASCII hyphens, which conflicts with "quoted titles keep
   their spelling", or verbatim, which may trip the dash gate for en-dashes.
8. **Issue file shape.** The existing files are prose with a title and
   "Possible fix", not the five named parts given at 4052-4053. Either
   reference them as they are or prescribe a template.
9. **`cited by <key>` is ambiguous.** It means the key of the entry whose
   checked source carries the reference (for example `edge-darkening` for
   Curtis). Say so.

## Counts

4 blocking, 8 should-fix, 9 nits.
