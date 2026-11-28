# 010 — tasks

Slices and files are in `plan.md`. Order: Start, S0, S1, S2, S3, S4, S5, S6, all serial.

## Start

- [ ] Comment the branch name and spec `010` on #166.
- [ ] ADR 0073 written from `plan.md`, "ADR 0073 contents" (rules 1 to 11; 5 to 11 land
      in 010a), amending 0007, 0026, 0027 and 0068.
- [ ] The plan-reviewer passes the plan.

## S0: Baseline hashes

- [ ] `git mv tests/golden/grid_hashes.py tests/golden/output_hashes.py`; every registered
      stem by default, `--stem` repeatable; `git grep grid_hashes -- ':!specs'` empty.
- [ ] On the untouched base: `record specs/010-blank-paper-and-keyword-arguments/output-hashes.json`,
      committed alone, run time in the message.
- [ ] `check` passes; slice gate green.

## S1: The additive half

- [ ] Red: `Canvas.pixels` (equal, scale 1, identity, refuses 0); `paper_plate` default
      (grid on and off, differs at half width); `brush_from_id` defaults.
- [ ] `Canvas.pixels`, `display_px=None`, `scale=1.0, style=None`; slice gate green.

## S2: The flip and the forced migration (one commit)

- [ ] Red: positional `Sheet`, `wash` and `brush_from_id` raise `TypeError`; keyword
      order of `Sheet` does not matter; `wash(..., body=, pool=)` equals the pin.
- [ ] `Sheet` `kw_only`, `w` before `h`, `Attributes:` reordered; `wash(*, body, pool,
      options)`; `brush_from_id(*, scale, style, override)`.
- [ ] Scratch codemod over `src`, `tests`, `examples` (spelling only; drop literal `1.0`
      scale and bare `BrushStyle()` style); `ruff format`; diff read line by line.
- [ ] Markdown by hand: README, the four tutorial pages re-quoted, the how-to, the
      explanation's prose signature, the brushes reference example.
- [ ] `uv run ty check` green; docs grep empty; slice gate and coverage gate green.

## S3: Records

- [ ] Glossary "body" row; regenerated.
- [ ] `docs/features/ink-blank-paper-by-size.md` deleted, links repointed to ADR 0073;
      the 010b sweep section added to `docs/features/docs-examples-review.md`.
- [ ] Slice gate, strict docs build, dash check.

## S4: The pixel proof

- [ ] `output_hashes.py check` against S0: 91 entries unchanged.
- [ ] Golden suite green with no regeneration; `git status --porcelain docs/images tests/golden` empty.

## S5: Mutation testing

- [ ] `scope.py` patterns run; survivors killed or named in `mutation.md`.

## S6: Final review and PR

- [ ] Fresh-context diff review against the plan; elegance pass; findings triaged.
- [ ] PR: title `feat(ink)!: take the sheet's size, the wash's densities and the brush scale by keyword`,
      the five Changelog lines, `Closes #166`, mutation equivalents, "Golden and docs
      images: none moved" with the S4 evidence.
