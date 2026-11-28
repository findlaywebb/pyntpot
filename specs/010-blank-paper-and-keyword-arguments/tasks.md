# 010 — tasks

Revision 2: matches `plan.md` revision 2.

Slices and files are in `plan.md`. Order: Start, S0, S1, S2, S3, S4, S5, S6, all serial.

## Start

- [ ] Comment the branch name and spec `010` on #166.
- [x] ADR 0073 written from `plan.md`, "ADR 0073 contents" (rules 1 to 11; 5 to 11 land
      in 010a, which may amend them), amending 0007, 0026, 0027 and 0068 and quoting only
      sentences they contain; 0072 skipped (spec 008a holds it).
- [x] `docs/decisions/README.md`: the 0073 row and four "amended by 0073" clauses.
- [x] The plan-reviewer passes the plan.

## S0: Baseline hashes

- [ ] Red: `tests/golden/test_output_hashes.py` (a narrowed check ignores other stems,
      reports a missing or changed selected entry, refuses an unknown stem).
- [ ] `git mv tests/golden/grid_hashes.py tests/golden/output_hashes.py`; every registered
      stem by default, `--stem` repeatable with plan S0's semantics;
      `git grep grid_hashes -- ':!specs'` empty. Commit 1.
- [ ] On the untouched base: `record specs/010-blank-paper-and-keyword-arguments/output-hashes.json`.
      Commit 2, alone, base commit and run time in the message.
- [ ] `check` passes; slice gate green.

## S1: The additive half

- [ ] Red: `Canvas.pixels` (equal, scale 1, identity, refuses 0); `paper_plate` default
      (grid on: equal and differs at half width; grid off: equal only); `brush_from_id`
      defaults against `brush_from_id(id, w, scale=1.0, style=BrushStyle())`, written by
      keyword.
- [ ] `Canvas.pixels`, `display_px=None`, `scale=1.0, style=None`; slice gate green.

## S2: The flip and the forced migration (one commit)

- [ ] `Sheet` `kw_only`, `w` before `h`, `Attributes:` reordered; `wash(*, body, pool,
      options)`; `brush_from_id(*, scale, style, override)`.
- [ ] Scratch codemod over `src`, `tests`, `examples` by plan S2's six rules: positional
      arguments only, never an existing keyword; the starred-`Sheet` rule for the four
      named calls; loud refusal of any other starred or `**` form; drop positional literal
      `1.0` scale and bare `BrushStyle()` style. Then `ruff format`.
- [ ] `ruff check --fix --select F401 src tests examples` (only `BrushStyle` in the 14
      files); `BrushStyle` out of those 14 module docstrings and `brush_stroke.py:3-5`
      reworded; tutorial blocks re-copied.
- [ ] `test_docs_signatures.py:76-77` read `body`; `test_public_api.py:172` docstring;
      `test_benchmark_inputs.py` flags a benchmark `brush_from_id` with no `style=` (red
      first on a scratch call).
- [ ] Markdown by hand: README, the four tutorial pages re-quoted, the how-to, the
      explanation's prose signature, the brushes reference example.
- [ ] Negative tests written after the codemod (positional `Sheet`, `wash`,
      `brush_from_id` raise `TypeError`, with `ty: ignore[too-many-positional-arguments,
      missing-argument]`; `Sheet` keyword order irrelevant), seen failing on a worktree of S1.
- [ ] Diff read line by line against plan S2's list; `uv run ty check` green; docs call
      check reports nothing; slice gate and coverage gate green.

## S3: Records

- [ ] Glossary "body" row; regenerated.
- [ ] `docs/features/ink-blank-paper-by-size.md` deleted, links repointed to ADR 0073;
      `docs-tutorial-opening-programs.md:15,21` name #166 and ADR 0073; the 010b sweep
      section added to `docs/features/docs-examples-review.md`.
- [ ] Slice gate, strict docs build, dash check;
      `git grep ink-blank-paper-by-size -- ':!specs' ':!docs/decisions'` empty.

## S4: The pixel proof

- [ ] `output_hashes.py check` against S0: 91 entries unchanged.
- [ ] Golden suite green with no regeneration; `git status --porcelain docs/images tests/golden` empty.

## S5: Mutation testing

- [ ] By plan S5's rule: `Canvas.pixels` and `paper_plate` in full; the five
      spelling-only functions shown spelling-only by normalised AST (recorded);
      `wash` and `brush_from_id` mutated, survivors checked against 006, 008 and 009's
      equivalents with reasons re-checked; the three `letters` functions left out, with
      the reason.
- [ ] Survivors killed (no test file past 400) or named in `mutation.md`; past 150 lines
      for one function, the rest filed in `docs/issues/` and on GitHub.

## S6: Final review and PR

- [ ] Fresh-context diff review against the plan; elegance pass; findings triaged.
- [ ] PR: title `feat(ink)!: take the sheet's size, the wash's densities and the brush scale by keyword`,
      the five Changelog lines, `Closes #166`, mutation equivalents, "Golden and docs
      images: none moved" with the S4 evidence.
