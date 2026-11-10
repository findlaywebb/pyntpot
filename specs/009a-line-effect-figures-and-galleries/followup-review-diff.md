# Casing follow-up: diff review (PR 2)

Reviewer: fresh context, sceptical staff engineer. Diff: `git diff 9ef36cc6..3173bfb5 -- examples
tests docs specs/009a-line-effect-figures-and-galleries src/pyntpot/ink/deposit.py` on
`claude/quirky-hypatia-z2pii3-stacked` (the rest comes from PR 1's merges and is reviewed there).
Against: `followup-casing.md`, `specs/009-line-effects-and-registry/followup-casing-tasks.md`
(T0 to T7), `images.md`, ADR 0071 as amended, `CLAUDE.md`, `CONTRIBUTING.md`.

**Verdict: PASS after fixes.** No BLOCKING finding. Five SHOULD-FIX findings, all fixed in this
commit. Nothing the fixes touch moves a pixel: every golden passes with no regeneration.

## Pass 1: plan compliance

Checked and fine:

- **T0 to T6 done.** The split (`line_effect_scenes.py`, with `stroke_density` left in the grid
  script as recorded), the 2x helper (`SUPERSAMPLE`, `scaled_boxes`, `reduce`, tested in
  `test_labelled_grid.py`), the five sweeps at 2x and the reserve sweep, the 3 x 2 cased stroke,
  the three-cell draw order, the reference tables and the theme how-to paragraphs. T7 is the
  orchestrator's.
- **The moved set.** `git diff --stat 9ef36cc6..HEAD -- docs/images tests/golden` is exactly the
  ten "Figures" images and their ten masters, the added reserve sweep and its master, and
  `MEAN_RGB["bold"]`. Nothing else.
- **No budget raised.** `tests/support/docs_images.py` and `SHARES_009A`'s values are untouched;
  `docs_images_009a.py` only registers the reserve sweep.
- **The record.** `images.md` and ADR 0071 list every moved image and master with fraction,
  extent and reason, the added image, the Lynmouth compare and the re-pinned `MEAN_RGB["bold"]`;
  the fractions agree between the two.
- **Public names only.** The five example scripts import only `pyntpot.ink` and `pyntpot.letters`
  top-level names.
- **Tutorial quotes and YAML.** The docs tests (quotes are exact substrings, every YAML block
  loads) and `mkdocs build --strict` pass. No em or en dash in any added human-facing line.
- **Figures against their captions.** The draw-order, cased-stroke and reserve-sweep images were
  opened at 2x and 7x nearest-neighbour: in "casings first" the second road's ring shows as a pale
  band inside the first road at the fork, and in the union cell it does not; the reserve cells are
  bare paper; the pooled edge is faint, as every caption says.

## Pass 2: quality

### BLOCKING

None.

### SHOULD-FIX (all fixed)

1. **The union was described wrongly.** The explanation said a union's mask is "the larger of
   the members' densities", and both the explanation and the reference said a picture painted in
   Python "gets the same result" from `casing` with that mask. `casing_union` takes the strongest
   of the members' own rings, each at its own width; the two agree only for members of one width,
   and even then not exactly (on the draw-order roads they differ in 105 pixels, up to 0.24, all
   where the roads meet). Fixed: the explanation states the rule and says the figure is painted
   with the larger density, which matches a one-width union apart from a few pixels where the
   lines meet; the reference says "nearly the same ring" for members of one width; the
   `line_effect_reasons.py` docstring says the same.
2. **An unrecorded, untested `src` change.** The plan says PR 2 changes no `src` file, but the T0
   merge commit `0e04f8cb` (a single-parent commit) carries a one-line `ink/deposit.py` change:
   `nib_cover` reads the positions as float64. Removing it left the whole `ink`, `letters` and
   property suite green. Fixed: `test_float32_and_float64_positions_give_the_same_cover_bit_for_bit`
   fails without it, and the change is mutation-tested and recorded in `mutation.md`.
3. **`nib_cover` survivors.** 16 of 155 mutants survived. Fixed: 11 killed by focused tests in
   `tests/unit/ink/test_nib_cover_exact.py`, 5 named equivalent in `mutation.md`. The stroke
   builder those tests share with `test_deposit.py` moved to `tests/support/lays.py`.
4. **Tests that asserted too little.**
   - `test_the_union_is_lighter_than_casings_first_nowhere` said the union is darker "inside a
     road" but asserted it anywhere. It now asserts it inside the first road's footprint.
   - `test_theme_snippets.py` summed the two pages' loaded blocks against one floor, so the line
     effects how-to's blocks could all be skipped unnoticed, and nothing checked the new YAML did
     what the prose says. It now counts each page, and a new test checks each page has a block
     giving `road_major` `Reserve(width_px=2, pool=0.3)` and one unioning `road_major` and `lane`.
5. **The judging record was inaccurate.** In `images.md` the glow verdict spoke of "rows" of
   spreads that are columns; the reserve verdict called the pool "a slightly softer margin",
   where it is a faint darker edge; the draw-order verdict left out the plan's union criterion (no
   ring through the first road); and the "Judged at 2x" column read "yes" where the plan asks for
   "pass" or the defect. Fixed, and the missing blank line before "### Added" added.

### NIT

6. Fixed. Docstring paragraphs over 100 columns in `line_effect_grids.py`,
   `line_effect_reasons.py` and `cased_stroke.py` reflowed (the lines the tutorial quotes are
   untouched).
7. Not changed. `paint_cell` takes `at` in display pixels in `line_effect_grids.py` but on the
   doubled paper in `line_effect_reasons.py` and `cased_stroke.py`. Each docstring says which, and
   the tutorial quotes `cased_stroke.py`'s crop lines, so aligning them would rewrite a quote.
8. Not changed. The wash recipe (`_washed`, the pigment's transparency fallback) and the S-curve
   are written three times across the scripts; this predates the follow-up, and `cased_stroke.py`'s
   copy is the tutorial's.
9. Not changed, and outside this follow-up. `grid_hashes.py check` reports
   `how-to/route-ink.webp` DIFFERENT, already at the pre-follow-up tip 9ef36cc6: 009a moved it on
   purpose (#159, `images.md`), and the 009 hash file was not re-recorded. The other 22 are
   identical, and the follow-up changes none of them.

## Gates after the fixes

- `uv run pytest -n 2 --dist loadgroup -m "not golden"`: pass.
- `uv run pytest -m golden -n 2 --dist loadgroup`: pass, no regeneration.
- `ruff check`, `ruff format --check`, `ty check`, `lint-imports` (3 kept),
  `mkdocs build --strict`, `prek run --all-files`: pass.
- `nib_cover` mutation re-run with the new tests: 150 killed, the 5 equivalents survive.
- Grid hash check: 22 identical, `how-to/route-ink.webp` different as at 9ef36cc6 (NIT 9).
