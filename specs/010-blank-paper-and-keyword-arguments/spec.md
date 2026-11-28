# 010 — Blank paper by size, and keyword arguments for the ink engine

Revision 2 (after `review-plan.md`): the callers criterion names the two edits D7 forces;
the docs criterion names an AST check over fenced blocks; the ADR criterion names the
index; ADR 0073 skips 0072, which spec 008a holds.

GitHub issue: [#166](https://github.com/findlaywebb/pyntpot/issues/166) (blank paper set
up from a size alone). This PR closes it.

Decision record: ADR 0073 (`docs/decisions/0073-boilerplate-free-calls.md`), which covers
all three API changes of scoping group E-a (`specs/005-feature-scoping/sessions.md`,
"E. Kill the boilerplate"): this PR lands its N2 rules; the stacked
`specs/010a-lettering-over-an-image-and-the-basemap-key/` lands its N1 and N3 rules
(#165, #167), as ADR 0070 rule 17 landed in 009a.

## Problem

Painting on blank paper with `pyntpot.ink` repeats the same numbers in three calls, and
two of the engine's calls take numbers a reader cannot guess, by position. Measured on
`f6c8302`:

- `Sheet(h, w, gran_px, seed)` takes height first, while `Canvas(x0, y0, x1, y1, w, h)` and
  Pillow take width first. All 54 `Sheet` calls in `examples/` (33 files) and 41 of the 44
  in `tests/` pass the size by position, so a copied call with the two swapped transposes a
  non-square image in silence.
- Outside `maps` a canvas's box means nothing: `examples/` builds one 43 times in 25 files,
  42 of them as `Canvas(0, 0, w, h, w, h)`, and the watercolour tutorial quotes 12 more.
- `paper_plate(sheet, canvas, style, display_px)` reads only the canvas's `w` and `h`, then
  takes `display_px`, which is the canvas width again in its 35 calls in `examples/`.
- `wash(cover, sheet, base, pool, options=None)` takes its two densities by position: all
  36 calls in `examples/` (20 files) do, 24 of them as two bare literals
  (`wash(disc, sheet, 0.6, 0.3)`). The glossary calls the first density the body
  (`GLOSSARY.md`, "body"), and the parameter is `base`.
- `brush_from_id(brush_id, width_display_px, scale, style, override=None)` has no
  defaults: 25 of its 27 calls in `examples/` (19 files) pass `scale` 1.0, 20 pass a bare
  `BrushStyle()`, 19 pass both.

(The note's figures, 47 canvases, 30 washes and 22 brush calls, were measured before
specs 008 and 009 added scripts; these supersede them.)

## Acceptance criteria

### The API (ADR 0073, N2 rules)

- [ ] `Sheet` is a keyword-only dataclass whose first two fields are `w` then `h`:
      `Sheet(w=360, h=240, gran_px=8.0, seed=11)`. A positional call raises `TypeError`.
      Its other fields, defaults, `Attributes:` entries (reordered to field order) and the
      five noise fields it draws are unchanged: for the same size, grain, seed and fibre,
      every field is bit-identical to today's.
- [ ] `Canvas.pixels(*, w, h)` returns the canvas whose box is its own pixel grid:
      `Canvas(0.0, 0.0, float(w), float(h), w, h)`, so its `scale` is exactly 1 and `px` maps
      `(x, y)` to `(x, h - y)` (no scaling, north up). A width or height under 1 raises `ValueError`. `Canvas`'s constructor is
      unchanged.
- [ ] `paper_plate(sheet, canvas, style, display_px=None)`: with `display_px` left out,
      the grid is measured against `canvas.w`, and the paper is bit-identical to passing
      `canvas.w` (a grid-on and a grid-off case). Passing `display_px` still works.
- [ ] `wash(cover, sheet, *, body, pool, options=None)`: `base` is renamed `body`, and
      `body`, `pool` and `options` are keyword-only. A positional density raises
      `TypeError`. The density for given values is bit-identical to today's.
- [ ] `brush_from_id(brush_id, width_display_px, *, scale=1.0, style=None,
      override=None)`: `style=None` means `BrushStyle()`. `brush_from_id(id, w)` returns a
      brush and ink equal to `brush_from_id(id, w, scale=1.0, style=BrushStyle())`. A
      positional `scale` raises `TypeError`.
- [ ] Each signature above is what `pyntpot.ink` and the top-level façade (`Sheet`,
      `Canvas` and `wash` are in `pyntpot.__all__`) export, and the reference renders it.
      No public name is added to or removed from any `__all__`.

### The callers move with the signatures

- [ ] Every caller of `Sheet`, `wash` and `brush_from_id` in `src/`, `tests/`,
      `examples/`, `README.md` and `docs/` uses the new form. Only the call's spelling
      changes, positional arguments only: an existing keyword argument is never touched.
      A `brush_from_id` call drops a positional `scale` that is the literal 1 or 1.0 and a
      positional `style` that is a bare `BrushStyle()`, because those are now the defaults.
      Beyond the calls, exactly these change: a `BrushStyle` import that the drop left
      unused (14 example files) and that name in the same files' module-docstring list of
      the names they use, the tutorial blocks quoting those lines, one test docstring
      (`tests/unit/test_public_api.py:172`), the extractor self-test literals in
      `tests/docs/test_docs_signatures.py`, and a `brush_from_id` case added to
      `tests/architecture/test_benchmark_inputs.py`. Nothing else in those files changes
      (`Canvas.pixels` and the `display_px` default are adopted by 010b, not here).
- [ ] Every tutorial block stays a verbatim quote of its script
      (`tests/docs/test_tutorial_quotes.py`), the README's quick start stays a quote of
      `examples/wash.py` (`tests/docs/test_readme.py`), and every quoted signature in prose
      lists every parameter (`tests/docs/test_docs_signatures.py`):
      `docs/explanation/how-the-wash-works.md` reads `wash(cover, sheet, body, pool,
      options)` and `docs/reference/brushes.md`'s example is in the keyword form.
- [ ] No fenced code block in `README.md` or a `docs/` page (outside `decisions/` and
      `features/`) calls `Sheet` with a positional argument, or `wash` or `brush_from_id`
      with more than two: the AST check over fenced blocks in `plan.md`, "Running the
      gates", reports nothing.

### Pixels do not move

- [ ] The sha256 of every file each registered docs image's script writes, and of its RGB
      pixels, recorded on the branch base, is unchanged
      (`tests/golden/output_hashes.py check`, 96 entries (91 recorded on 38179789, the five 008a preview images on e89eff3e)).
- [ ] The golden suite passes with no regeneration: no file under `docs/images/`,
      `tests/golden/docs/` or `tests/golden/lynmouth/` changes, and no pinned literal
      (`GOLDEN_HASH`, `DIGEST`, `BASE_DIGEST`, `LETTERING_DIGEST`, the theme digests, any
      unit or property pin) changes.

### Records

- [ ] ADR 0073 is written and accepted. It amends ADR 0007 (`Sheet` and `wash` are its
      façade names), 0026 (its member rule binds documented signatures; `brush_from_id`;
      `NibGroups`), 0068 (`wash`'s "keeps the signature" sentence; `Basemap`'s
      construction) and 0027 (where a caller gets the key), quoting only sentences those
      ADRs contain. It states that rules 5 to 11 land in 010a, which may amend them.
      `docs/decisions/README.md` has its row and an "amended by 0073" clause on each of the
      four amended rows. (0072 is skipped: spec 008a holds it and lands first.)
- [ ] `GLOSSARY.md`'s "body" row reads "`wash`'s `body`" and the glossary page and
      tooltips are regenerated.
- [ ] `docs/features/ink-blank-paper-by-size.md` is deleted and every link to it
      repointed; the sweep it described (examples and the tutorial onto `Canvas.pixels`
      and the `display_px` default) is added to `docs/features/docs-examples-review.md`
      (#63) as the 010b work. The two mentions in
      `docs/features/docs-tutorial-opening-programs.md` name #166 and ADR 0073 instead,
      and `git grep ink-blank-paper-by-size -- ':!specs' ':!docs/decisions'` is empty. The
      PR body says `Closes #166`.
- [ ] Mutation testing has run by `plan.md`'s S5 rule: `Canvas.pixels` and `paper_plate`
      in full, `wash` and `brush_from_id` against their recorded equivalents, and the
      spelling-only `letters` functions shown spelling-only. Each survivor is killed or
      named as equivalent, with its reason (`mutation.md`, PR description), or, past the
      150-line bound, filed as an issue.
- [ ] No file under `src/` is over 400 lines; no mocking; logging only. Gates green:
      `uv run pytest -n auto --dist loadgroup`, `uv run ruff check .`, `uv run ty check`,
      `uv run lint-imports`, `prek run --all-files`, and the golden suite.

## Changelog

PR title (breaking: every positional `Sheet`, `wash` and `brush_from_id` call fails):

```
feat(ink)!: take the sheet's size, the wash's densities and the brush scale by keyword
```

Under "Changelog" in the PR description:

```
feat(ink)!: Sheet takes every field by keyword, width first: Sheet(w=, h=, gran_px=, seed=); a positional call raises TypeError
feat(ink)!: wash takes body, pool and options by keyword, and its base density is renamed body: wash(cover, sheet, body=, pool=)
feat(ink)!: brush_from_id takes scale, style and override by keyword; scale defaults to 1.0 and style to BrushStyle()
feat(ink): Canvas.pixels(w=, h=), a canvas that is only its pixel grid
feat(ink): paper_plate's display_px defaults to the canvas width
```

## Out of scope

- **N1 and N3** (#165 lettering over an image, #167 the basemap's key): the stacked
  `specs/010a-lettering-over-an-image-and-the-basemap-key/`. It builds on this PR
  (`letter_over` builds its plate with `Canvas.pixels` and a keyword `Sheet`).
- **The sweep (010b, scoping group E-b).** Moving `examples/`, the tutorials, the how-to
  guides and the README onto the additive calls (`Canvas.pixels` for the 42
  `Canvas(0, 0, w, h, w, h)`, dropping the 35 `display_px` arguments), onto 010a's
  `letter_over` and `basemap.key`, and N11 (#174, housekeeping). Sizing: this PR's forced
  migration is already about 256 call sites in about 70 files; a sweep on top would put
  the diff past one reviewable pass, and a sweep moves no pixel (every new call is
  bit-identical), so nothing is gained by doing it in the same regeneration window.
- `Canvas`'s own constructor (positional, already width first; `maps` builds three).
- `NibSurface`, `composite`'s arguments, `PaperStyle` as a default of `paper_plate`.
- A one-call blank-paper helper (`Sheet` plus `Canvas.pixels` plus `paper_plate` is
  three short calls, each already public; a fourth name for the same thing is refused).
