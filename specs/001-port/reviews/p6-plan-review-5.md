# P6 plan review 5

Reviewed: the changes to `specs/001-port/plan.md` from `9474c49` to HEAD
(`4f01559`, branch `p6-docs`), against `reviews/p6-plan-review-4.md`. Scope
was this round's changes only. The run-log decisions and the section's
length were not re-opened.

Probes were run on 2026-10-07 in the session scratchpad, outside the repo:

- **Live pages.** Seven design-record web pages were fetched through the
  proxy with `curl -sSL`, 2 s apart: Stadia, ICA, Adventures in Mapping,
  osmanyy, Stamen, Urban Sketching World and Hobbs. The Curtis grail PDF was
  also fetched and run through `pdftotext`. Each body was `html.unescape`d
  and folded as *match* says (NFKC, lowercase, non-alphanumeric to space,
  whitespace collapsed). Each pinned word was then counted as a substring.
- **`refcheck.sh`.** It was extracted verbatim from the plan; it parses. It
  was run against the real run log on three generated samples:
  - all 23 entries at their pinned counts, with `nib`'s canonical line
    carrying the `Nearest published work:` prefix and a `Note:` on
    `lanczos`;
  - the same sample plus a fake entry, `` ## `fake-entry` Fake technique ``,
    with a canonical line, the fixed `not recorded` line and no
    `Implemented in:`;
  - the same sample with `nib`'s `Implemented in:` line removed.
- **The cited code.** The `-I` greps and the line references in the changed
  text were checked in `src/`.
- **Gate commands.** The "Gate commands" paragraph (plan 535-565) was
  checked against every slice that runs a gate.

## Verdict: PASS (SOUND)

No finding blocks. All 11 round-4 findings are resolved. The two
should-fix items below are small, and both can go straight into a brief.

## Round-4 findings

| Finding | Status | Evidence |
|---|---|---|
| B1: the widened "blocked" rule catches paraphrased web pages | **Resolved** | See "B1 in detail" below the table. |
| B2: the P6.3-write brief lacks rule 5 | **Resolved** | See "B2 in detail" below the table. |
| S1: the `-I` greps | Resolved | See "S1 in detail" below the table. |
| S2: `fluid_modulate` | Resolved | 4889 decides it as not a site. The 4848-4854 text names 309. Checked in `ink/wash.py`: line 293 is `def fluid_modulate`, 309 is its `wet:` argument, and 330 calls `shallow_water` on the downsampled grid. The percentile gain is at about 339. |
| S3: briefs name blocks they do not carry | Resolved | See "S3 in detail" below the table. |
| S4: notes about papers nobody fetched | Resolved | Both notes now state code facts only. `chamfer-distance` (5119): `noise.py:176` holds `F32(1.41421356), F32(1.0)` inside `edt` (168). `hillshade` (step 4): `relief.py:136` holds `np.gradient` inside `_shade` (128). A pinned note states the code fact only, unless a body saved under `$SLICE/refs/` shows the paper's claim. |
| S5: an entry with no `Implemented in:` line passes every gate | **Resolved** | See "S5 in detail" below the table. |
| Nit 1 | Resolved | 4618-4624 is in the past tense ("already in the run log ... No one waits"). The marker grep prints `2` at HEAD. |
| Nit 2 | Resolved | 5531-5536: the base is P6.4 or `Log P6.5 dispatch`, and landing starts only after all five hand-offs. |
| Nit 3 | Resolved | 4155-4159: the `line-budget-` form is accepted, and the landing check accepts both forms. |
| Nit 4 | Resolved | The source-line rule says no `]` in how-checked text, and to write "issued null". The evidence row repeats it. |

**B1 in detail.**

- **The DOI-only clause.** The title-and-author clause is now confined to a
  DOI's publisher page (4683-4690). The tool fact (4396-4400), route 7
  (4727-4730) and `verified-via-index` (4568-4571) all agree with it.
- **How a web page matches.** A design-record web page is now matched only
  by its pinned words (4672-4675, 4755-4774), and it has no fields to
  mismatch. So ICA can no longer fall through to `unreachable`.
- **Live re-run.** Every pinned word is present on every live page:

| Page | Words found (folded, as substrings) |
|---|---|
| Stadia | `stamen watercolor` 43, `stadia maps` 22 |
| ICA | `mapcarte 95 365` 4, `pictorial guide to the lakeland fells` 17, `wainwright` 32, `commission on map design` 6 |
| Adventures in Mapping | `adventures in mapping` 7, `tolkien style maps in a gis part 3 water` 5, `john nelson` 7 |
| osmanyy | `risograph css` 22, `osman` 25 |
| Stamen | `watercolor process` 28, `zach watson` 2, `stamen` 270 |
| Urban Sketching World | `line and wash` 35, `urban sketching world` 3 |
| Hobbs | full title 7, `tyler hobbs` 26 |
| Curtis PDF | title 4, `curtis`, `anderson`, `seims` 1 each, `fleischer` 1 (through `fleischery`), `salesin` 4, `1997` 0 |

- **Titles and dates.** Each `<title>` matches the pinned citation title.
  ICA's hyphen in "1955-1966" is ASCII in the source. The
  `article:published_time` values are 2012-03-26 (Stamen), 2024-02-14
  (Adventures in Mapping) and 2025-07-03 (osmanyy), as pinned. ICA has no
  such meta tag, and its 2014 comes from the design record, which gives
  2014.
- **The Postman's Knock.** Its pinned author and year (Bugbee, 2014) come
  from the run log's 14:05 marker entry, so nothing in them is from memory.

**B2 in detail.**

- P6.3-write's brief row (4279) now carries the candidate table and the
  canonical-source rule.
- The evidence row requires the prefix for `nib` (5150-5152).
- Step 4 fixes `nib`'s canonical line text, and says a `nib` line without
  the prefix is a defect.
- `refcheck.sh` accepts the prefixed line (probe: the good sample exits 0).

**S1 in detail.**

- The match-table greps now use `-I` (4994, 5002-5007, 5011).
- At HEAD, with `__pycache__` present under `src/`, they give 11, 16, 48
  and 2, as pinned.
- The P6.1 tally needs no `-I`, because it already restricts the search
  with `--include=*.py`.

**S3 in detail.**

- **What a brief copies.** The "Gate commands" definition (4266-4272)
  copies the paragraph at 535, with `$MG` written in full, the G-here
  bullet and, where a row says so, the G-self bullet. `$SCRATCH/before` is
  read as `$SLICE/before`.
- **Every gate-running slice carries it:**
  - P6.1, P6.2 and P6.3-write: G-here.
  - P6.4, P6.5a-e and P6.6: G-here and G-self.
- **P6.3-fetch.** Its row correctly has none, because it runs no gate
  (5139-5140: "the slice's gate and commit are one, after P6.3-write").
- **P6.1's row** now carries the candidate table.

**S5 in detail.**

- **`refcheck.sh`.** It now counts `Implemented in:` lines (exactly 1) and
  `Note:` lines (at most 1) for each entry. The probes:
  - the good sample exits 0 and prints exactly the two `MAINTAINER-CHECKED`
    lines (p5-watercolor and The Postman's Knock);
  - the fake entry exits 1 with `FAIL Implemented in fake-entry: 0 lines,
    want 1`;
  - removing `nib`'s line exits 1 with `FAIL Implemented in nib: 0 lines,
    want 1`.
- **The P6.4 test.** It adds `entries_without_sites`, and a literal-text
  test for it (5437-5450).

## New defects in the changed text

None would make a slice fail or produce a wrong result. Two small gaps
follow.

## [SHOULD-FIX]

- **S1 (brief, P6.4; 5412-5414): "a heading" in `entries` is wider than an
  entry heading.**
  - **What the plan says.** "A heading with no `Implemented in:` line maps
    to `[]`, never drops out."
  - **How it fails.** Read literally, this includes
    `## Read during design, no technique here`. That heading has no
    `Implemented in:` line by design. If an implementer keys every `## `
    heading, `test_every_entry_lists_a_site` goes red on the real file.
  - **Why it does not block.** The red test would surface it at P6.4, so it
    costs a cycle, not a wrong result.
  - **Fix.** Say "an entry heading (`` ## `<key>` <technique> ``, the Key
    regex); the closing heading is not an entry". Put the closing section
    in the literal for `test_entries_without_sites_names_an_entry_with_no_site`,
    so the test proves the closing heading is excluded.
- **S2 (brief, P6.3-write): the `Nearest published work:` prefix is
  required but never checked mechanically.**
  - **What the plan has.** Step 4 calls a `nib` line without it "a defect",
    but neither `refcheck.sh` nor the other mechanical checks look for it.
    P6.6 gate step 3 re-runs only those checks, so a dropped prefix would
    pass both gates.
  - **Fix.** Add one line to the mechanical checks:
    `grep -cE '^- Canonical source: Nearest published work: ' docs/explanation/references.md`
    equals 1, plus the number of rows P6.1 added under rule 5, as logged.

## Counts

- 0 blocking.
- 2 should-fix, both brief-level.
- All 11 round-4 findings are resolved.
