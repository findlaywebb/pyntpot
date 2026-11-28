# 010 plan review

Reviewer: fresh-context plan reviewer. Measured on `d764a881` (branch `work-010`, main
`f6c8302a` plus the spec commit), ty 0.0.97.

## Verdict: BLOCK

The approach is sound. Making `Sheet` keyword-only rather than flipping it to positional
`(w, h)` is the right call (D2). Splitting E-a into 010 and 010a, with the sweep as 010b,
is right too. ty can act as the completeness proof for the Python callers. The output
hashes plus the golden suite are the right pixel proof.

What blocks it is the S2 codemod. As written, it breaks the plan's own new tests. Its D7
simplification also leaves 14 example files red on ruff, with 14 docstrings stale. Neither
problem is prescribed for. One self-test that no slice owns goes red, and one caller form
the rewrite rule does not cover is left to the agent.

**The most important change:** spell out exactly what the codemod may and may not touch.
It never rewrites a keyword argument that is already there. It never rewrites a call
inside a `pytest.raises(TypeError)` block. It has one rule for a starred call. After it,
`ruff check --fix --select F401` runs and the "Public names" docstring lines are edited,
and the spec's "nothing else changes" clause is amended to allow those two.

## What I verified and found sound

- **Call counts.** My own AST count reproduces every cell of S2's table exactly: `Sheet`
  2/44/54, `wash` 5/23/36, `brush_from_id` 4/61/27, 256 in all. The only call made
  through an attribute is `pyntpot.Sheet(64, 64, 8.0)` (`tests/unit/test_public_api.py:173`).
  No target call nests inside another, so rewriting the last call first is safe. No
  existing target call carries a `# ty: ignore`. Every name the codemod targets is
  imported from `pyntpot*`; no alias or sibling module re-exports one.
- **ty as the completeness proof.** I checked with ty 0.0.97, `all = "error"`. A
  positional call to a `kw_only=True` dataclass is flagged (`too-many-positional-arguments`
  plus `missing-argument`). So are a starred `*tuple[int, ...]` or `*ndarray.shape`
  call, a positional density to `wash(..., *, body, pool)`, a leftover `base=` keyword
  (`unknown-argument`) and a `partial(wash, 1, 2, 0.5, 0.3)`. `[tool.ty.src]` includes
  `src`, `tests` and `examples` with no excludes (`pyproject.toml`).
- **Ruff.** B008 does refuse `style=BrushStyle()`: `BrushStyle` is
  `@dataclass(frozen=True, kw_only=True)` (`ink/brush_style.py:18`) but is not in
  `extend-immutable-calls`. `max-args = 6` holds for all four signatures. The repo is
  `ruff format` clean (811 files), so `ruff format .` reflows only the rewritten calls.
- **Public surface.** `typing.Self` is in `ALLOWED` (`tests/architecture/_public_surface.py:68`),
  so `Canvas.pixels(...) -> Self` passes `test_public_signatures.py`.
  `test_field_docs.py` / `_field_rule.py:81` does check that `Attributes:` follows field
  order. No test pins `inspect.signature` of these names. Neither `__init__.py` docstring
  quotes a signature, so S2's ownership of them changes nothing; that is harmless.
- **Markdown coverage.** Outside `docs/decisions`, `docs/features` and `specs`, exactly
  eight non-Python files call the three functions. They are the eight S2 lists. The only
  backticked prose signature that `test_docs_signatures.py` checks is
  `how-the-wash-works.md:33`. `docs/decisions/` is excluded from the site (`mkdocs.yml:13-20`),
  so ADR 0068's quote can stay. Every `python` block on a tutorial page must be a
  verbatim quote of its script (`test_tutorial_quotes.py`), so the scripts' migration
  forces the tutorial blocks to follow.
- **Pixel proof.** `IMAGES` has 91 entries, one for each of the 91 files under
  `docs/images/`: 35 stems, 19 fixture entries, 90 WebP and 1 JPEG. The one example with
  calls that is not registered, `line_effect_scenes.py`, is imported by the registered
  `line_effect_grids.py`.
- **Line budget.** `brush.py` 355, `nib.py` 357, `washing.py` 316, `sheet.py` 199 and
  `paper.py` 90 all have room. `grid_hashes.py` is 104 lines, not 113, which changes
  nothing.
- **010a's needs.** 010a needs `Canvas.pixels` and a keyword `Sheet`, and S1 and S2
  provide both. The section heading 010a appends to, "The sweep onto the new calls
  (010b)", matches what 010a's plan names. No file on the 010a list (`tests/support/golden.py`,
  `maps/attribution.py`, `cli.py`) calls any of the three functions.

## Findings

### 1. [BLOCKING] The codemod rewrites the plan's own red tests, so the negative tests stop testing anything

- **Plan:** S2, "Tests first (they fail before the flip)", then "How (mechanical,
  scripted)" run over all of `tests`. Also S1's `brush_from_id` test.
- **What goes wrong:**
  - S2's new negative cases are written first. They are `Sheet(240, 360, 8.0, 11)`,
    `wash(cover, sheet, 0.6, 0.3)` and `brush_from_id("MAJ6-e", 3.0, 2.0)` under
    `pytest.raises(TypeError)`, each with `# ty: ignore[...]`.
  - The codemod then runs over `tests/` and rewrites them into valid calls:
    `Sheet(w=360, h=240, gran_px=8.0, seed=11)` and `brush_from_id("MAJ6-e", 3.0, scale=2.0)`.
  - Each test then fails with "DID NOT RAISE". Its kept ignore comment becomes
    `unused-ignore-comment`, which I checked: ty reports "Unused `ty: ignore` directive"
    as an error under `all = "error"`.
  - S1's test compares `brush_from_id("MAJ6-e", 3.0)` with
    `brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())`. S2's drop rule turns the right side
    into `brush_from_id("MAJ6-e", 3.0)`. The test becomes `x == x`, and the spec's
    `style=None` means `BrushStyle()` criterion is no longer proven.
- **Fix:** add these three rules to the codemod section.
  1. The codemod rewrites only positional arguments. It never adds, drops or reorders a
     keyword argument that is already present, so an existing `scale=1.0` or
     `style=BrushStyle()` keyword stays.
  2. It skips any call lexically inside a `with pytest.raises(TypeError)` body. Or,
     simpler: S2 runs the codemod first and writes the three negative tests afterwards,
     in the same commit. Pick one and say which.
  3. S1's equality test writes its explicit side by keyword:
     `brush_from_id("MAJ6-e", 3.0, scale=1.0, style=BrushStyle())`. That is legal in S1,
     where the parameters are still positional-or-keyword, and rule 1 preserves it.

  Update `tasks.md`'s S1 and S2 lines to match.

### 2. [BLOCKING] D7 drops the only use of `BrushStyle` in 14 example files: ruff fails, and 14 docstrings go stale

- **Plan:** D7, and S2's "drop `style=` when `st` is a bare `BrushStyle()`". The spec says
  "Only the call's spelling changes ... Nothing else in those files changes". S2 also says
  "every changed line is a call's argument list or its reflow, nothing else".
- **Evidence (AST, every `Name` use counted):** after the drop, `BrushStyle` is imported
  and never used in these 14 files:
  - `examples/brush_gallery.py`, `brush_sheet.py`, `brush_stroke.py`, `cased_stroke.py`,
    `curves.py`, `fern.py`, `fern_family.py`, `kaleidoscope.py`
  - `examples/line_effect_reasons.py`, `line_effect_scenes.py`, `nib_line.py`,
    `site_theme.py`, `svg_drawing.py`, `tutorial_grids.py`

  That is F401, so `ruff check .` goes red. The module docstring of every one of the 14
  also names `BrushStyle`. For example, `brush_stroke.py:10` reads "Public names it
  introduces: `BrushStyle`, `brush_from_id`, ..." and `nib_line.py:9` reads "Public names
  it uses: `BrushStyle`, ...". After the drop those claims are false, and module
  docstrings are the agent contract. The plan forbids both edits.
- **Fix:** keep D7, which the spec requires, and prescribe what follows from it:
  1. After the codemod and `ruff format`, run
     `uv run ruff check --fix --select F401 src tests examples`. Read the diff: it removes
     only the `BrushStyle` name from these 14 import lists.
  2. In those 14 docstrings, remove `BrushStyle` from the "Public names it uses /
     introduces" sentence, and fix `brush_stroke.py:3-5`'s "with the `BrushStyle`
     defaults" wording so it stays true.
  3. Re-copy any tutorial block that quotes one of those lines.
  4. Amend the spec's "Callers" criterion and S2's "nothing else" sentence so they allow
     exactly two more kinds of change: removing an import the drop left unused, and
     removing that name from the module docstring's name list.

  The alternative is to narrow D7 to `scale` only, which has no import fallout, and leave
  `style=BrushStyle()` to 010b. Whichever you choose, write it down. Do not leave the
  agent to find out at the ruff gate.

### 3. [BLOCKING] `tests/docs/test_docs_signatures.py:76-77` goes red, and no slice owns it

- **Evidence:** the extractor's self-test uses
  ``("`wash(cover, sheet, base, pool, options)` here.", False)`` as its "full" case.
  After the rename, `wash`'s parameters are `[cover, sheet, body, pool, options]`. The
  quoted `base` no longer matches, so the case is flagged and the test fails. These are
  string literals: the codemod does not reach them and ty cannot see them. The file is
  in no slice's Owns list and not in "Files to touch".
- **Fix:** S2 owns `tests/docs/test_docs_signatures.py`. Change `base` to `body` in the
  two literals on lines 76 and 77, and add the file to "Files to touch" and the S2 row of
  the partition.

### 4. [BLOCKING] Four starred `Sheet` calls fall outside the codemod's rule

- **Evidence:**
  - `tests/unit/maps/painter/test_paper.py:23` and `:38`: `Sheet(*job.shape, gran_px=6.0, seed=3)`
  - `tests/unit/maps/painter/test_water.py:32`: `Sheet(*cov.shape, gran_px=8.0, seed=5)`
  - `examples/line_effect_grids.py:201`: `Sheet(*size, GRAN_PX * SUPERSAMPLE, SEED)`,
    where `size` is `(height, width)` (`:200`)

  The rule `Sheet(a, b, c, d, ...)` → `Sheet(w=b, h=a, ...)` does not say what to do with
  a starred argument. ty flags all four, but the agent has to invent the form, and a swap
  in `line_effect_grids` would transpose a registered docs figure.
- **Fix:** prescribe the form. A starred first argument `*s` becomes
  `w=s[1], h=s[0]`, and any further positional arguments map as usual. So
  `Sheet(w=job.shape[1], h=job.shape[0], gran_px=6.0, seed=3)` and
  `Sheet(w=size[1], h=size[0], gran_px=GRAN_PX * SUPERSAMPLE, seed=SEED)`. No new local
  variables. The codemod refuses, loudly, any other starred or `**` form; there is none
  today.

### 5. [SHOULD-FIX] The S2 wash test points at a pin that does not exist, and the test plan contradicts S2 on `Sheet` pins

- **Evidence:**
  - S2 says `wash(cover, sheet, body=0.6, pool=0.3)` "equals the file's existing pinned
    density" in `test_wash.py`. That file has no pinned density. The pins are `PINNED` in
    `tests/unit/ink/test_wash_density.py:15-24`, at body 0.52 and pool 0.20, and the
    codemod already rewrites `test_each_option_lays_the_pinned_density` (`:41`) into
    keyword form. An agent looking for the pin may instead invent one by running the code
    under test, which breaks the golden rule.
  - The Test plan row for `Sheet` says "pinned field hashes". S2 says the values are "not
    pinned here".
- **Fix:**
  - Drop the S2 keyword-equals-pin assertion and say that `test_wash_density.py`'s
    `PINNED`, rewritten by the codemod, is the proof. Keep only the `TypeError` case in
    `test_wash.py`.
  - Change the Test plan row to "positional `TypeError`; shape `(h, w)`; keyword order
    irrelevant; values proven by the existing pins (`test_paper.py`'s classic plate,
    `test_wash_density.PINNED`) and S4".

### 6. [SHOULD-FIX] `check --stem` cannot do what S4 asks of it

- **Evidence:** `check` (`grid_hashes.py:74-90`) logs every recorded image missing from
  the measured set as an error. S4 says to find a failure "with the hash tool's `--stem`
  on the failing entry", against the full 91-entry JSON. Every entry outside the
  narrowed stem would then report "recorded but no longer ...", and the run exits 1.
- **Fix:** prescribe the semantics. With `--stem`, `record` writes only the selected
  entries. `check` compares only the selected entries and ignores recorded entries of
  other stems, but still errors on a selected stem's entry that is missing from the JSON.
  An unknown `--stem` value is an argparse error. Add a short self-test for the
  narrowing; `tests/golden/test_*.py` is the precedent for helper tests. Also say whether
  S0's tool change and the recorded JSON are one commit or two: "committed alone" is
  ambiguous.

### 7. [SHOULD-FIX] The ADR index and the ADR number are not prescribed

- **Evidence:**
  - `docs/decisions/README.md` gives every ADR a row, and amended ADRs carry an
    "amended by" note (row 0069). The plan never names this file, so the agent may skip
    the row and the notes on 0007, 0026, 0027 and 0068, and no test catches it.
  - The last ADR on main and on every remote branch is 0071. The plan uses 0073 without
    saying why it skips 0072.
- **Fix:**
  - Start owns `docs/decisions/README.md`: add the 0073 row, "Boilerplate-free calls
    (amends 0007, 0026, 0027 and 0068)", and an "amended by 0073: ..." clause on each of
    those four rows.
  - Either state what holds 0072 or use 0072. If you change the number, update both
    specs and 010a's plan.

### 8. [SHOULD-FIX] The ADR's "supersedes 0007's documented `Sheet(h, w, ...)`" quotes text 0007 does not contain

- **Evidence:** 0007 lists the engine names and documents no `Sheet` signature
  (`docs/decisions/0007-*.md:18-19`). What binds the signatures is 0026, "Members"
  (`0026-widen-the-public-api.md:73-82`): "the names in `__all__` and their documented
  signatures", which covers the docstrings. An agent told to supersede a sentence that
  is not there will make one up.
- **Fix:** rule 1 should read: "a breaking change to the documented signatures of
  `Sheet` (0007's façade name), `wash` (0068's 'keeps the signature' sentence) and
  `brush_from_id` (0026's member rule)". Quote only sentences that exist.

### 9. [SHOULD-FIX] The note-link sweep collides with "Files to leave alone"

- **Evidence:** `docs/features/docs-tutorial-opening-programs.md:15` and `:21` name
  `ink-blank-paper-by-size.md`. They are backticked file names, not links, so
  `test_docs_links.py` will not flag them. S3 owns "every file `git grep -l` names", but
  "Files to leave alone" forbids every `docs/features/*` note except two.
- **Fix:** add `docs-tutorial-opening-programs.md`, at lines 15 and 21 only, to S3's
  Owns list and to the leave-alone exception. Say what replaces the name: "#166, closed
  by ADR 0073; the sweep is under `docs-examples-review.md`". Then
  `git grep ink-blank-paper-by-size -- ':!specs' ':!docs/decisions'` must be empty, and
  that is the gate.

### 10. [SHOULD-FIX] The docs grep cannot prove the spec criterion it backs

- **Evidence:** the regex
  `wash\([^)]*,[^)=]*[0-9.]+, *[0-9.]+\)` cannot cross a `)`, and it needs both densities
  to be literals. It misses forms that are in the docs today:
  - `paint-a-watercolour.md:184` and `:387`, `wash(_disc(...), sheet, body, 0.5)` and
    `..., sheet, 0.7, 0.4)`
  - `curves.md:147`, `wash(_cover(...), sheet, rng.uniform(0.3, 0.5), 0.45)`
  - `pictures.md:31`, `wash(cover, scene.sheet, crest, 0.25)`

  The tutorial pages are safe only because `test_tutorial_quotes.py` forces them to follow
  their scripts. The spec makes "the grep ... is empty" the acceptance criterion, and an
  empty grep does not mean the job is done.
- **Fix:** replace the grep with a scratch AST check (never committed) for S2 and S6. It
  extracts every fenced `python` block from `README.md` and from `docs/` outside
  `decisions/` and `features/` (`support.site_pages.fenced_blocks`), parses each block,
  wrapping an unparseable one in `def _():`, and reports any `Sheet` call with a
  positional argument, any `wash` call with more than two, and any `brush_from_id` call
  with more than two. A plain `git grep` covers prose: the inline `brush_from_id(` in
  `reference/brushes.md` and the `wash(` in `explanation/how-the-wash-works.md`. Reword
  the spec's criterion to name that check.

### 11. [SHOULD-FIX] S5's size is not bounded: four in-scope functions have never been mutation-tested

- **Evidence:**
  - `wash` (203 mutants, 8 equivalents, `specs/006-one-public-surface/mutation.md:25`) and
    `brush_from_id` (008, 009) have recorded runs.
  - `paper_plate`, `letters.nib._sheet`, `_backing_wash` and `nib_brushes` appear in no
    `specs/*/mutation.md`.
  - The plan runs every function in full and kills or names every survivor, including
    those on untouched lines. That is legitimate under CLAUDE.md, but it is unsized test
    work in a PR the plan already calls the size limit of one review (D1).
  - 006 took the opposite rule: it compared normalised ASTs and left spelling-only
    functions out of its run list. The plan makes the opposite choice without saying why.
- **Fix:**
  - State the rule and the reason.
  - Point S5 at 006's, 008's and 009's equivalent lists for `wash` and `brush_from_id`.
    The mutant numbers will have moved, so each reason is re-checked, not copied.
  - Say where survivor-killing tests go: `test_paper.py` is at 168 lines,
    `tests/unit/letters/test_nib.py` is the letters target, and neither may pass 400.
  - Add: if one function's survivors would add more than about 150 lines of tests, file
    a `docs/issues/` note and a GitHub issue for the rest instead of growing this diff.
    CLAUDE.md sends out-of-scope discoveries there.

### 12. [SHOULD-FIX] Small ambiguities the agent will execute literally

- **`paper_plate` grid off (S1):** "Same with the grid off" can be read as also asserting
  "differs at `canvas.w // 2`". That cannot hold: `display_px` is read only when the grid
  is on (`paper.py:84-85`). Say that the grid-off case asserts equality only.
- **A stale test docstring:** `tests/unit/test_public_api.py:172` says
  "`pyntpot.Sheet(64, 64, 8.0)` constructs a sheet". The codemod rewrites the call on line
  173 but not the docstring. Allow that one docstring edit by name.
- **A misleading citation:** S2 cites `tests/unit/ink/test_wash.py:40` as a target call
  that carries a `# ty: ignore`. It is a `Flow(...)` call, and no target call carries
  one. Drop the citation so the agent does not look for a kept ignore that does not
  exist.

### 13. [CONSIDER] ADR 0073 accepts rules 5 to 11 before 010a's plan has been reviewed

010a has no `review-plan.md` yet. If its review changes `letter_over`'s signature
(rule 6) or `Basemap.key` (rule 10), an accepted ADR will already state the old design.
Add one sentence to 0073: rules 5 to 11 land in 010a, which may amend them in its own PR,
and the ADR index row says so until then. This is the 0070 rule 17 precedent, made
explicit.

### 14. [CONSIDER] `style=None` gets around `test_benchmark_inputs.py`

`tests/architecture/test_benchmark_inputs.py` stops a benchmark from building
`BrushStyle` directly, because that would time whatever the default look is. After this
PR, `brush_from_id(id, w)` in a benchmark builds `BrushStyle()` internally, and the check
cannot see it. Today's benchmark calls pass `flags_off(BrushStyle)` explicitly
(`tests/benchmarks/test_ink.py:63,91,104`), so nothing breaks now. Either extend the
check to flag a `brush_from_id` call under `tests/benchmarks/` that has no `style=`, or
file it as a follow-up issue. Do not leave the gap unrecorded.

### 15. [CONSIDER] "base" lives on in `maps` vocabulary

Renaming `wash`'s `base` to `body` follows the glossary. But `maps/painter/cover.py:136`
still unpacks `base, pool = ...cover_cfg...`, and `CoverStyle.pale_base` still feeds the
body (`:174`). These are theme keys, so renaming them would be a breaking theme change and
is rightly out of scope. Say so in 0073's consequences, so the elegance pass does not
"fix" them inside this PR.

## Re-review (revision 2)

Reviewer: the same plan reviewer. Read on `e56bcce1` (rebased on `38179789`), ty 0.0.100.
The rebase changes only tooling (8 files: workflows, `pyproject.toml`, `uv.lock`). On the
new toolchain the tree is still `ruff format` clean (813 files) and `ruff check` clean, so
`ruff check --fix --select F401` can only remove imports the D7 drop leaves unused.

### Verdict: PASS

All four blocking findings are resolved, each with a concrete prescription that I
checked against the code. The revision adds no blocking contradiction. Three small items
remain. Fix them while implementing: none of them can make the end result wrong, and the
gates would catch the first one.

### The blocking findings

1. **The codemod and the negative tests: resolved.**
   - Codemod rule 1 means positional arguments only, so an existing keyword is never
     touched.
   - S2's "Order inside the slice" writes the three negative tests after the codemod,
     in the same commit. The codemod never sees them (D11).
   - S1's explicit side is `brush_from_id("MAJ6-e", 3.0, scale=1.0, style=BrushStyle())`,
     by keyword, so it survives rule 1 and keeps proving that `style=None` means
     `BrushStyle()`.
   - Watching the negative tests fail on a worktree of S1's commit is sound: there each
     positional call is still accepted, so each test fails with "DID NOT RAISE".
2. **D7's fallout: resolved.**
   - The F401 pass and the 14 named files are correct. I re-ran the AST scan: no file
     under `src/` or `tests/` loses its last `BrushStyle` use.
   - I read the `BrushStyle` mention in each of the 14 module docstrings. Thirteen
     mention it only in the "Public names" sentence. `brush_stroke.py` also has the
     `:3-5` sentence, which the plan rewords.
   - The spec's callers criterion now lists exactly what may change beyond the calls,
     and the "Reading the diff" list matches it.
3. **`test_docs_signatures.py:76-77`: resolved.** S2 owns the file, and the file is in
   "Files to touch" and in the partition.
4. **The starred `Sheet` calls: resolved.** Rule 3 gives the exact rewrite for all four
   sites, and rule 6 refuses any other starred or `**` form, loudly.

The should-fix and consider findings (5 to 15) are applied. I checked the two that carry
risk:
- **The docs call check (finding 10).** I prototyped the check as specified on this base,
  with the plain parse first and then the `def _():` wrap. It finds 30 positional target
  calls across README, the how-to and the four tutorial pages, and skips no block that
  contains a target call. So it is a real gate, not an empty grep.
- **The ADR number (finding 7).** 0072 is
  `docs/decisions/0072-preview-fixture-in-the-lynmouth-box.md` on
  `origin/claude/lucid-shannon-v36myd` (spec 008a), so skipping it is correct.

### Remaining items (none blocking)

1. **[SHOULD-FIX] `brush_from_id`'s negative test must not carry `missing-argument`.**
   - The plan says, under "Running the gates", that "a positional call to these
     signatures is `# ty: ignore[too-many-positional-arguments, missing-argument]`
     (measured)". `tasks.md` S2 prescribes those two codes for all three negative tests.
   - That holds for `Sheet` and `wash`. It does not hold for
     `brush_from_id("MAJ6-e", 3.0, 2.0)`: every keyword-only parameter there has a
     default, so ty 0.0.100 reports only `too-many-positional-arguments`. I checked it
     on a scratch file, and the two-code ignore then fails ty with
     "`unused-ignore-comment`: Unused `ty: ignore` directive: 'missing-argument'".
   - S2's own bullet hedges ("the ignore codes ty reports for it"), but the general
     sentence and the task line do not.
   - Fix: `# ty: ignore[too-many-positional-arguments]` for the `brush_from_id` case, in
     the plan sentence and in `tasks.md`.
2. **[SHOULD-FIX] S5 asks for a spelling-only proof that `brush_from_id` cannot pass.**
   - S5's "Spelling-only" bullet says to show each of the five functions is
     spelling-only by normalised `ast.dump` against the base. `brush_from_id`'s body
     gains S1's `style = BrushStyle() if style is None else style`, so its dump differs
     from `origin/main` whatever the normalisation.
   - `brush_from_id` is mutated anyway, so this does not change the outcome. But an
     agent told to "show it" will either stall or write a normaliser that hides a real
     change.
   - Fix: give the proof only for `wash`, `nib_brushes`, `_sheet` and `_backing_wash`,
     and say that `brush_from_id` has a new line and is mutated with the recorded
     equivalents as the check.
3. **[CONSIDER] The S0 self-test's import path.**
   - `grid_hashes.py:25` imports `from make_docs_images import fixture_options`, a bare
     sibling import. It resolves under pytest only because `tests/golden/` has no
     `__init__.py`, so prepend mode puts that directory on `sys.path`. Then
     `make_docs_images` is loaded twice, under two names, beside the
     `golden.make_docs_images` that `repaint.py:28` imports.
   - Switching to `from golden.make_docs_images import fixture_options`, as `repaint.py`
     does, works both from `test_output_hashes.py` and from the documented
     `PYTHONPATH=tests uv run python tests/golden/output_hashes.py ...` command.
   - S0 already owns the file, so this is a one-line change in that slice.
