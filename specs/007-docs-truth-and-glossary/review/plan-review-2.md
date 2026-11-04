Verdict: BLOCK

# 007 plan review 2

Reviewed `plan.md`, `spec.md` and `tasks.md` at `529753f` against the worktree, the locked
docs group, and 006's plan. 006's plan changed while this review ran: its fix round 2 was
committed as `a7d664d` (`/home/user/pyntpot`, branch `feat/006-one-public-surface`). This
review reads that commit, not the `c936970` or `943cb32` copies the 007 plan was reconciled
against.

All five round-1 blockers are fixed, and the prototypes reproduce. The 12 adopted
should-fixes add no scope beyond the spec. The blocking problem is new and comes from
outside: 006's S9 now sweeps retired words in `tests/**`, so it edits the lines 007's S5
edits, and S8 assumes 006 left lines that 006 now changes. Two smaller defects came in with
the fix round, both in S8 step 2.

## Round-1 blockers: verified

1. **Index order and `Next:`. Fixed.** I prototyped the test as written: exact
   `NavEntry.sections`, plus each direct subsection's index, first occurrence only. Today:
   Tutorials and Reference pass. Painting with Python fails (Vector drawing comes before
   Pictures). How-to fails (nav order differs from the index). Explanation passes. These are
   exactly the plan's claims (plan.md:157-161). S0's new How-to order equals
   `how-to/index.md`'s order. The gallery's headings, after S3 moves "Map from the command
   line", are a subsequence of the post-S0 nav.
2. **Marker. Fixed.** With "nearest preceding non-blank line" and indented fences dedented,
   all 39 marked tutorial blocks are verbatim. Exactly two python blocks are unmarked, both
   on `pictures.md` (lines 28 and 46). The `pictures.md` fix (`scene.inside`, `scene.sheet`,
   8-space indent) matches `examples/derwentwater.py:189-190`.
3. **CLI synopsis. Fixed.** At `COLUMNS=80` the `map` usage wraps to three lines; at 200 it
   is one line. Collapsing gives the same string either way, and it equals the plan's
   prescribed synopsis lines (plan.md:535-536).
4. **Say instead. Fixed.** Every "Say instead" ends in a term: nib plate, landmark, map,
   track, trace.
5. **#162 numbers. Fixed.** Re-prototyped over every caption on every site page. Only both
   clauses of `gallery.md:221` fail (`[-38, 0, 90]`, `[0.5, 0.85]`). The corrected caption
   passes against `ANGLES` and `THINS`.

Other claims the plan relies on, re-checked:

- **Build time.** Strict build in a scratch copy, with `abbr`, `snippets` `auto_append`,
  `content.tooltips`, `validation: anchors: warn` and a blank-line-separated abbreviations
  file of the plan's forms: 2.10 s before, 3.0-3.2 s after. The build is clean. The maps
  API page renders 54 `<abbr>`, and none is inside `<code>`.
- **S2.** The from-claim check finds exactly the 8 claims of #163. All 69 dotted paths
  resolve. The style-field comparator as specified matches 206 of 206 rows. The only
  quoted-choice Type cell is `paper_edge`.
- **S3.** The figure and theme check fails exactly on `docs/index.md` (hero) and
  `data-policy.md`. The four missing gallery images are confirmed. S4's new first-map
  caption passes S3's rule.
- **S7 commands.** There are 7 `pyntpot` lines, 2 of them the `cli.md` usage lines that
  must be skipped, and 18 example commands. All pass.
- **S8 step 6.** The swap list covers every S1 cell whose object ADR 0068 exports. No S1
  cell names an object that is already exported under another path.
- **Follow-ups.** None of 006's seven follow-up notes duplicates 007's out-of-scope
  filings.

## Blockers

### 1. 006's S9 now edits the test lines S5 edits; the overlap table and S8 are stale

- **Evidence.** In 006 `a7d664d`, plan.md:948-975, S9 owns `tests/**/*.py` docstrings,
  comments, test names and locals that carry a retired word. It lists these lines:
  - `tests/golden/test_places.py:45, 51, 89, 188`;
  - `tests/support/docs_images.py:351` (the `_place_card` docstring);
  - `tests/unit/maps/test_example_themes.py:53, 67` (the test renamed to
    `test_the_label_cap_is_the_landmark_count`), `68`, `70` and `73` (the local `callouts`
    becomes `landmarks`);
  - `tests/architecture/test_reference_pages.py:168`;
  - every test line 007's S8 step 9 lists (`test_draw_plate.py:1,48`,
    `test_placement_water.py:89,90,93`, `test_cache.py:206`,
    `test_pipeline_letter_compose.py:102`, `test_route_ink.py:27`).

  006 leaves only the two `"callouts"` key strings, because `examples/` is outside its
  scope.
- **The 007 plan says otherwise.**
  - plan.md:93 and :725-728 say 006 has no edit in `test_example_themes.py`.
  - plan.md:96-99 lists `tests/golden/test_places.py` and `tests/support/docs_images.py`
    as "007's alone".
  - S5 (plan.md:735-742) edits the comments, docstrings and `_place_card` docstring on the
    same lines.
  - S8 step 1 (plan.md:890-894) says any conflict other than `GLOSSARY.md` means stop.
  - S8 step 2 rewrites `:168`, which 006 has already rewritten.
  - S8 step 9 (plan.md:1017-1025) expects a red on test lines 006 has already fixed.
- **Result.** The S8 rebase conflicts in `test_example_themes.py`, where both sides change
  line 70. It probably also conflicts in `docs_images.py:351` and in the `test_places.py`
  comments, so S8 halts. S8 step 9's red-first step has nothing to go red, and an agent
  will hunt for a failure that should not exist.
- **Fix.**
  - **S5.** Change only the two key strings: `"callouts"` to `"landmarks"` at
    `tests/golden/test_places.py:194` and `tests/unit/maps/test_example_themes.py:70`. Do
    not touch their comments, docstrings, test name or local. Drop
    `tests/support/docs_images.py` from S5's owned files (006 writes the same "curated
    landmarks"). Update S5's Done line and the "Files to touch" list to match.
  - **Overlap table.** Add rows for all three files: 006's S9 owns the wording, and 007
    changes only the key string.
  - **S8 step 1.** Name the expected conflict at `test_example_themes.py:70` and give its
    resolution: `landmarks = tomllib.load(handle)[name].get("landmarks", [])`. Any hunk in
    `test_places.py` resolves to 006's wording with 007's key.
  - **S8 step 2.** Drop the `:168` docstring edit and keep the function rename.
  - **S8 step 9.** The extension to `tests/` and `src/` should pass on arrival. A red is a
    line 006's S9 missed: fix it here if it is under `tests/`, and report it to 006 if it
    is under `src/`.
  - **Pin the 006 commit.** State that the plan was reconciled against `a7d664d`. 006's plan
    is still moving, so S8 re-runs the overlap check against the merged diff, as the Risks
    section already says.

### 2. S8 step 2's done criterion requires editing an accepted ADR

- **Evidence.** S8 step 2 (plan.md:921-923) is done when
  `grep -rnE "architecture/test_(…|docs_images|…)"` outside `specs/` and `docs/issues/`
  finds nothing, and it says to "repoint any docstring or note that names them".
  `docs/decisions/0033-docs-images-and-examples.md:21` names
  `tests/architecture/test_docs_images.py`, but "Files to leave alone" says
  `docs/decisions/**` gets no ADR changes (plan.md:1098). The grep also hits
  `tests/support/docs_images.py:40`, which is not in S8's owned files.
- **Result.** The two instructions contradict each other. The agent either edits ADR 0033
  or cannot meet its done criterion.
- **Fix.** Exclude `docs/decisions/` from the grep. Add `tests/support/docs_images.py`
  (the module docstring, line 40) to S8's owned files.

### 3. S8 step 2 deletes a helper that another test still calls, and its replacement misses prose commands

- **Evidence.** S8 step 2 deletes `_tutorial_pages`. It is also called by
  `test_every_run_command_names_an_existing_script` (`tests/architecture/test_tutorials.py:93-103`),
  which stays.
- **Result.** As written, ruff reports F821 and the moved file fails.
- **The obvious replacement does not cover everything.** The natural move is to delete that
  test too, as subsumed by S7's example-command test, but S7 reads fenced blocks only.
  `curves.md` (`uv run python examples/curves.py out/ --figure rose`) and `symmetry.md`
  (`uv run python examples/kaleidoscope.py out/`) give their commands as inline code in
  prose, so nothing would check them. That misses the spec's "every option of a
  `uv run python examples/<script>.py` command … (test, generic over pages)".
- **Fix.** S8 step 2 also deletes `test_every_run_command_names_an_existing_script`. S7's
  `test_docs_commands.py` reads two sources:
  - the fenced blocks;
  - every backticked inline span in `prose()` that starts `pyntpot ` or
    `uv run python examples/`.

## Suggestions

1. **Caption sentence end.** "Up to its full stop" (plan.md:569) must not split on a
   decimal point. A naive `.` truncates the corrected nib caption at `0.` of `0.52` and
   silently skips the `down` clause (prototyped: 1 clause checked instead of 2). Define
   the end as a `.` followed by whitespace, `*` or end of line. Also say that the caption
   paragraph runs past the closing `*`: `brushes.md:7` and `gallery.md:183` put "The
   labels read" outside the italics.
2. **Carry the old commands test's guards into S7.** S8 deletes `test_how_to_commands.py`,
   so S7's test needs what it had:
   - inline-string extractor tests: a continued line, an indented fence, a misspelt option
     rejected, and an output line in a `text` block;
   - a non-vacuity assertion (`map-from-the-command-line.md` yields a command).

   Also prescribe the usage-line skip as the regex `^pyntpot (map )?\[` rather than "by
   that shape". S7 deliberately reads `text` blocks, which the old test treated as
   output.
3. **`resolve_dotted` and the shadowed names.** At the base, `resolve_dotted` resolves
   `pyntpot.ink.wash`, `pyntpot.maps.compose` and `pyntpot.maps.vector_layers` to the
   shadowing modules (#164), not to the functions (plan.md:248-249 says the opposite).
   This is harmless: they resolve, and S8 step 6 skips modules. But correct the sentence,
   and pin the behaviour with a helper test, so that nobody "fixes" `resolve_dotted` to
   prefer attributes.
4. **The landmarks how-to.** S5's "leave … the import sentence of
   `letter-your-own-landmarks.md` to S8" (plan.md:729-731) points at nothing. The file
   has no import sentence; line 36 is the code line S5 rewrites, and S8 step 7 adds the
   sentence. Reword it to: S5 adds no sentence about importing `Landmark`.
5. **"Meaning holds no dotted code path"** (plan.md:252) conflicts with the spec's exact
   Meanings, which contain `Style.route_ink`, `Style.with_route_ink`,
   `PaperStyle.km_glazing`, `PaperStyle.paper_foxing` and `Setting.wash`. Say instead "no
   module path (`pyntpot.…`, `ink.x.Y`); attribute references stay".
