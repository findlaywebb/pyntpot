Verdict: PASS

# 007 plan review 3

I reviewed `plan.md`, `spec.md` and `tasks.md` at `e8eaad7`, checking them against the
worktree and against 006's plan. The plan is reconciled against 006 at `a7d664d`. While
this review ran, 006 committed its fix round 3 as `6baba86` (`/home/user/pyntpot`). I
diffed `a7d664d..6baba86`. The changes are:

- the retired-word self-check now diffs against the slice's base;
- `test_public_api.py` gets a rebase note;
- S7 swaps its road test (Lee Road and B3223);
- S10 changes the bloom mutation pattern;
- S9 done criterion 3 reads moved rows in place.

None of these touches a file, line or ownership rule that 007 relies on. The pin to
`a7d664d` still holds, and S8 step 1 reruns the overlap check against the merged diff
anyway.

All three round-2 blockers are fixed. The fresh pass found no defect that would make an
implementer fail, move a golden, overlap 006 before S8, or loosen a contract.

## Round-2 blockers: verified

1. **006's S9 owns the test wording. Fixed.**
   - 006's S9 (`a7d664d` and `6baba86`) lists exactly the 20 retired-word hits under
     `tests/` that `git grep` finds at this base. It leaves only the two `"callouts"`
     keys: `tests/golden/test_places.py:194` and
     `tests/unit/maps/test_example_themes.py:70`.
   - S5 now changes only those two string literals (plan.md:745-783). S5 no longer owns
     `tests/support/docs_images.py`. Its done line checks one changed line in each file.
   - The overlap table has a row for each shared file (plan.md:102-105).
   - S8 step 1 names the conflict at `test_example_themes.py:70` and gives the exact
     resolution: 006's local name with 007's key. It also covers a possible
     `test_places.py` hunk. Between `:188` and `:194` there are five unchanged lines,
     so git may or may not report a hunk there, and the plan says so.
   - S8 step 2 drops the `:168` docstring edit and keeps the `label_plate` function
     rename.
   - S8 step 9 now expects green on arrival, with a non-vacuity check. A miss under
     `tests/` is fixed in S8; a miss under `src/` is reported to 006.
2. **The step-2 path grep and ADR 0033. Fixed.** I ran the grep at this base, excluding
   `specs/`, `docs/issues/` and `docs/decisions/`. It hits three lines:
   - `examples/brush_sheet.py:16`, which S8 owns;
   - `tests/support/docs_images.py:40`, which S8 now owns, on a line 006 does not touch
     (006 edits only `:351`);
   - `docs/features/docs-tutorials-lead-on.md:23`, which S7 deletes.

   ADR 0033's mention stays, as the plan says.
3. **`_tutorial_pages` has a second caller. Fixed.** S8 step 2 deletes
   `test_every_run_command_names_an_existing_script` together with the helper, after
   S7's command test is green. S7's `test_docs_commands.py` reads two sources: the
   fenced blocks, and every inline span starting `uv run python examples/`. That covers
   `curves.md:14` and `symmetry.md:12`, and a non-vacuity assertion pins both spans.
   Leaving out inline `pyntpot ` spans is right: I confirmed they are names, an error
   message and `--help`, not commands.

All five round-2 suggestions are adopted as written: the caption sentence end, the
paragraph read past the closing `*`, the extractor helper tests, the usage-line regex,
the `resolve_dotted` module-first pin, and the corrected Meaning rule.

## Fresh pass: checked and sound

- **S1 rows.** All 54 current `GLOSSARY.md` rows are kept. Each of the 26 new rows has
  its Meaning in the spec's "Canonical terms". All 57 distinct dotted names in the
  table resolve with a longest-module-prefix resolver at this base.
- **S8 step 6 at the base.** S8 step 6's exported-name rule finds no cell naming a
  private path to an object a layer exports, so it really is red only after 006. The
  swap list matches ADR 0068's export table at `6baba86`. `Label` and `Span` stay in
  `label.py` after 006's S0b split, so their private paths resolve on both sides.
- **Style groups.** The group exports at this base match S2's split: `PaperStyle` and
  `BrushStyle` from `pyntpot.ink`; `FaceStyle`, `NibStyle` and `HandStyle` from
  `pyntpot.letters`; the other eight exported nowhere.
- **S8 step 1 grep.** At the base it finds only `style-fields.md:263` and `:277`.
  `references.md` "Implemented in" paths resolve today, and 006 repoints them itself.
- **Tests 007 cannot edit before S8.** S0, S1, S2 and S4 change nothing that
  `tests/architecture/test_site.py`, `test_reference_pages.py` (glossary pointer, the
  `command` dest, the sidecar `route` key) or `test_readme.py` checks. The moved files
  appear in no allowlist, config or per-file ignore. Nothing outside the moved files
  refers to them except the docstrings S8 owns.
- **Repository links.** The repository links on site pages all resolve today, except
  the two whose notes 006 deletes. S6 removes the `ink-public-wash-options.md` link
  before 006 lands. The `maps-public-provider-protocols.md` link at
  `self-host-providers.md:9` is S8 step 7's expected red.
- **Places key rename.** No other reader of the `places.toml` key exists. No docs image
  is keyed on script text, so renaming the key moves no golden.

## Suggestions (non-blocking)

1. **Name the two retired-word lines no slice step lists.** Both files belong to a
   slice, and S7's test would catch both, but naming them saves the integrator a red:
   - `docs/reference/style-fields.md:175`, "the outline route writes with", becomes
     "outline trace" (S2);
   - `docs/explanation/the-hand-and-the-nib.md:33`, "the `outline` route draws round
     the contour", becomes "`outline` trace". S5 names only `:32`.
2. **Prescribe the block for S4's new first-map command.** Use a `console` block with
   `$ `, like the page's other commands. S7's extractor reads only
   `bash`/`console`/`shell`/`sh`/`text` blocks and inline spans. An untagged fence would
   leave the `--theme`/`--place`/`--size` check silently unrun, despite S7's claim that
   it checks this command.
3. **Fix two things in `test_tutorials.py` after S8 step 2's deletions.**
   - `EXAMPLES_DIR` stays in use (`test_the_vector_page_links_the_drawing_it_reads`), so
     drop it from the parenthetical list of names to remove; only `_COMMAND` goes.
   - Rewrite the module docstring too. It still promises the verbatim check and the
     run-command check, and module docstrings are the agent contract.
4. **Add `-I` to S8 step 1's `grep -rnE`.** As written it prints 18 "binary file
   matches" lines from `docs/images/`, which an agent may read as unexpected hits.
5. **Generate the Hypothesis property's input directly.** For S1's `anchor` property,
   build terms that always contain an ASCII letter rather than filtering `st.text()`.
   Filtering risks a `filter_too_much` health-check failure.
6. **Say how to take `GLOSSARY.md` during a rebase.** During a rebase, "ours" and
   "theirs" are swapped. Spell out "this branch's file" as
   `git checkout --theirs GLOSSARY.md` during the rebase, or merge `main` instead.
