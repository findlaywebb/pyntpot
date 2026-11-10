# 009a follow-up: the casing figures repainted at 2x, a union and a reserve shown (PR 2)

PR: findlaywebb/pyntpot#213, branch `claude/quirky-hypatia-z2pii3-stacked`, stacked on #211. The
engine change is `specs/009-line-effects-and-registry/followup-casing.md` (PR 1), merged into this
branch first. Decisions 24 to 27 are binding. This PR changes figures, docs and pinned images
only: no `src` file.

## Problem

- PR 1 anti-aliases casings and pen casings, so every figure that lays one paints differently.
- PR 1 adds `Reserve` and `casing_unions`, which no page shows.
- The line effect sweeps and the essay figures are painted at scale 1 and shown 600 to 720 px
  wide, so on a 2x screen each stair is two device pixels.

## Decisions taken here

1. **Every line effect figure painted by a script at scale 1 is painted at 2x and
   Lanczos-reduced to its present width:**
   - the four sweeps of `examples/line_effect_grids.py` (casing, glow, shadow, pen casing) and
     the new reserve sweep;
   - `cased_stroke.py`;
   - both figures of `line_effect_reasons.py`.

   How:
   - every `*_px`, stroke width and `GRAN_PX` is doubled on a grid twice the size;
   - the paper and every cell are composited at 2x;
   - the result is reduced once and then lettered at 1x;
   - a "2 px" label still means 2 display pixels.

   Glow and shadow sweeps move too. Decision 27 names the sweeps without exception, and one
   scale per script keeps a label meaning one thing; per-figure scales were rejected. The
   Ambleside card, the presets figure and bold are already painted at `supersample: 2` and
   change only through PR 1's casing. The setting grids (`setting_grids.py`) are left alone.
2. **The reserve** gets one new image, `how-to/reserve-sweep.webp`, on the how-to page:
   - the `MAJ2-b` road of the casing sweep over the same wash;
   - reserve width across (0, 1, 2, 3 and 5 px), pool down (0 and 0.3);
   - lossy, 720 px, slice `009a-line-effects`.

   The Painting with Python page gets two new cells in `cased-stroke` ("reserved" and
   "reserved, pooled"), a new cell rather than a second image. Its grid goes from 2 × 2 to
   3 × 2, keeping 600 px.
3. **The union** gets a third cell in `explanation/line-effects-draw-order`: "casings as a
   union", after "each stroke cased" and "casings first". In "casings first", the second road's
   ring shows through the first road's glaze at the fork; in the union cell it does not. This is
   a new cell, not a new image.
4. **No budget is raised.**
   - The `009a-line-effects` share is 600,000 bytes; its nine images weigh 318,500 now.
   - The estimate after is at most 430,000, with 2x painting adding up to 25% and the reserve
     sweep about 25,000.
   - The lossless pen casing sweep (87,256 bytes) stays far under the 250,000-byte page kind
     budget.
   - If a share or kind test fails, the figure loses cells; the budget never moves.
5. **No bundled theme or preset adopts a reserve or a union.** Bold keeps its cream casing
   (decision 26).

## Figures

| Image (each with its master under `tests/golden/docs/`) | Script and figure | What changes |
| --- | --- | --- |
| `how-to/casing-sweep.webp` | `line_effect_grids.py`, `casing` | anti-aliased ring; 2x |
| `how-to/glow-sweep.webp` | `line_effect_grids.py`, `glow` | 2x |
| `how-to/shadow-sweep.webp` | `line_effect_grids.py`, `shadow` | 2x |
| `painting-with-python/pen-casing-sweep.webp` | `line_effect_grids.py`, `pen-casing` | continuous edge lines; 2x |
| `how-to/reserve-sweep.webp` (added) | `line_effect_grids.py`, `reserve` | new |
| `painting-with-python/cased-stroke.webp` | `cased_stroke.py` | anti-aliased casing; two reserve cells; 3 × 2; 2x |
| `explanation/line-effects-draw-order.webp` | `line_effect_reasons.py`, `draw-order` | anti-aliased; third cell "casings as a union"; 2x |
| `explanation/line-effects-glaze-or-rgb.webp` | `line_effect_reasons.py`, `glaze-or-rgb` | casing column anti-aliased; 2x |
| `how-to/line-effects.webp` | `how_to_line_effects.py`, `card` | the cased `road_major` |
| `how-to/line-effects-presets.webp` | `how_to_line_effects.py`, `presets` | the cased cell |
| `map-styles/bold.webp` | the bold map style | the cased route; `MEAN_RGB["bold"]` re-pinned |

## Docs

- **How-to (`docs/how-to/case-light-or-shadow-a-line.md`).**
  - New "Reserve the paper round a line", with the reserve sweep and a `line_effects` example
    (`road_major: {reserve: {width_px: 2, pool: 0.3}}`).
  - New "Case several classes as one", with a `casing_unions: [[road_major, lane]]` example and
    the rule that members share one colour and strength.
  - Note that a stack takes a casing or a reserve, not both.
- **Reference (`docs/reference/line-effects.md`).**
  - "Effect fields" gains a `reserve` table: `width_px` 0 to 16, display px; `pool` 0 to 1,
    default 0.
  - A new "Casing unions" table: the key, its form, the one-group rule, the agreement rule, that
    `route` never joins, the digest it moves, and `[]` to turn an inherited set off.
  - "Draw order" says where a union's ring is laid.
  - "The primitives" lists `reserve`.
  - The page shows no image (house rule).
- **Explanation (`docs/explanation/line-effects.md`).**
  - New "One ring round a junction: casing unions", with the three-cell draw-order figure. It
    explains why casings-first is enough for opaque renderers and not for glazes.
  - New "A reserve: the paper laid back", explaining masking fluid, the pool, and why a reserve
    is its own kind and not a white casing.
  - The casing paragraph says the width is measured from the line's edge.
- **Tutorial (`docs/tutorials/painting-with-python/cased-strokes.md`).**
  - Covers the 3 × 2 figure, with the reserve cells' code calling `Reserve` and `reserve`.
  - Keep any check that the page's code matches `cased_stroke.py` green.
- **`docs/how-to/write-a-theme.md`.** The "Line effects" section names `reserve` and
  `casing_unions` in one paragraph each, linking to the how-to.
- **Everywhere.**
  - Every caption reads "Painted by `examples/<stem>.py`" with the figure. Lettered text is
    repeated beside the image.
  - Alt text says what changed.
  - Use glossary terms only (reserve, casing union, pool), with no em or en dashes.

## The moved-image record

- **The baseline is PR 2's tip before this follow-up.** Relative to `main`, every figure above
  except bold is still an added image of this PR, and bold was already moved by it. So the
  review record is relative to that tip, before PR 1's follow-up merge:
  `diff_images.py --ref <PR 2 tip before T0>`.
- **`specs/009a-line-effect-figures-and-galleries/images.md`** gains a section "Follow-up:
  casings anti-aliased and painted at 2x". It holds a "Moved" table (file, differing fraction,
  extent, reason, judged at 2x) for every image and master in "Figures", and an "Added" row for
  `how-to/reserve-sweep.webp` and its master.
- **ADR 0071 is amended in place** (unmerged, as 0071 itself did to 0070):
  - a section "Follow-up: casings anti-aliased, a reserve and a union" with the same table, the
    Lynmouth compare (every image byte-identical; `plates.json` hash unchanged at
    `90193bbb26f681bf-ebe16b5246aeb21f`) and the re-pinned `MEAN_RGB["bold"]`;
  - "Added images" gains the reserve sweep;
  - the closing line becomes "Any other moved image after this ADR and its follow-up section is
    a defect in the slice that moved it."

  A new ADR would record the same regeneration of the same PR in two places.

## Acceptance criteria

- [ ] PR 1's follow-up is merged into this branch, and the not-golden gate is green before any
      figure changes.
- [ ] A scratch repaint after the merge moves exactly the images in "Figures" (less the reserve
      sweep), and their masters. Nothing else moves: Lynmouth and the other docs images are
      byte-identical.
- [ ] Each 2x figure is painted on a grid twice its 1x spec and reduced once with Lanczos to
      its registered width.
      - Its "off" cell still equals the plain stroke cell byte for byte.
      - Every value it letters is the display value.
      - `tests/examples/test_line_effect_sweeps.py` (new) pins:
        - the 2x paint's reduced size;
        - the reserve sweep's off column equals its plain cell;
        - a pool row is nowhere lighter than the zero-pool row;
        - the thin pen edge line (gap 1, edge 0.75) has edge ink in every column of its span at
          display size (at least 0.5).
- [ ] The draw-order union cell equals the "casings first" cell outside the two roads'
      footprints and rings. Inside the first road's footprint it is no lighter than it, and is
      lighter nowhere.
- [ ] The cased-stroke reserve cells: "reserved" equals the paper plate crop where the ring is
      whole; "reserved, pooled" is nowhere lighter than "reserved".
- [ ] Docs as in "Docs"; the docs tests and the strict build are green.
- [ ] The goldens are regenerated once, at the end (T6), after every figure is judged at 2x
      zoom. `images.md` and ADR 0071 hold the record. The PR body's "Golden and docs images"
      block is refreshed from `publish_diffs.py` (the orchestrator pushes it).
- [ ] No budget, share or tolerance changes. The five grid scripts' hashes are unchanged.

## Tracks and gates

The order is T0, T1, T2, then T3 and T4 in parallel worktrees cut after T2, then T5, T6, T7.
Each file is owned by one track.

| Track | Owns |
| --- | --- |
| T0 merge and inventory | merge conflict resolutions only (expected: `style_groups.py`, `line_effects.py`, `theme_schema_tables.py`, both schema copies regenerated, `style-fields.md`, `ink.md`, `test_public_api.py`) |
| T1 split | `examples/line_effect_grids.py`, `examples/line_effect_scenes.py` (new): a pure move of the scene builders (`Scene`, `_curve`, `_solid`, `_brushed`, `_washed`, `_scene`, `stroke_density`); 386 lines leaves no room |
| T2 2x helper | `examples/labelled_grid.py` (`GridSpec.scaled(factor)`, `reduce(rgb, factor)`, `SUPERSAMPLE = 2`), `tests/examples/test_labelled_grid.py` |
| T3 sweeps | `examples/line_effect_grids.py`, `examples/line_effect_scenes.py`, `tests/support/docs_images_009a.py`, `docs/how-to/case-light-or-shadow-a-line.md`, `tests/examples/test_line_effect_sweeps.py` (new) |
| T4 essay and stroke | `examples/cased_stroke.py`, `examples/line_effect_reasons.py`, `tests/examples/test_line_effect_figures.py`, `docs/tutorials/painting-with-python/cased-strokes.md`, `docs/explanation/line-effects.md` |
| T5 reference | `docs/reference/line-effects.md`, `docs/how-to/write-a-theme.md` |
| T6 regenerate | `docs/images/**`, `tests/golden/docs/**`, `tests/golden/test_map_styles.py` (`MEAN_RGB`), `specs/009a-line-effect-figures-and-galleries/images.md`, `docs/decisions/0071-golden-regeneration-route-colour-pigment-transparency-cased-bold.md` |
| T7 close | this file's ticks, the PR body |

**Gate for T0 to T5.** The goldens are red from T0 until T6, as expected.

```bash
uv run pytest -n 2 --dist loadgroup -m "not golden" -q
uv run ruff check . && uv run ruff format --check .
uv run ty check
uv run lint-imports
PYTHONPATH=tests uv run python tests/golden/grid_hashes.py check specs/009-line-effects-and-registry/grid-hashes.json
uv run --locked --group docs mkdocs build --strict
uv run prek run --all-files
```

**T1's extra gate.** Repaint the four sweeps into scratch before and after the split; they are
byte-identical.

**T3's added image.** If a non-golden registry test needs a registered image on disk, T3 paints
and commits the added reserve sweep and its master; every moved image still waits for T6.

**T6.**

1. Repaint into scratch: `PYTHONPATH=tests uv run python tests/golden/repaint.py "$SCRATCH/t6" <every image in Figures>`.
2. Diff against the pre-follow-up tip.
3. Judge each figure (below).
4. Only then regenerate once with `make_docs_images.py`, the masters and `MEAN_RGB["bold"]`.
5. Then `uv run pytest -m golden -n 2 --dist loadgroup` with no further change, and the full
   gate.

### Judging pixelation at 2x zoom (T6, before the regeneration commit)

1. For each image in "Figures", open the scratch paint and its `diff_images.py` crop
   (`<path>.crop.png`, nearest-neighbour). Also open a whole-image 2x nearest-neighbour
   enlargement of each cell holding a casing, reserve or pen casing, written to the scratch
   directory.
2. View each with the image reader beside the research's before and after crops
   (`casing-*-before-after-4x.png`, `pen-gap*-before-after-4x.png`,
   `union-reserve-cells-2x.png`).
3. An image passes when:
   - the ring's outer edge and the pen edge lines read as continuous at 2x, with no
     two-device-pixel stairs;
   - no dotted edge line;
   - no Lanczos ringing on the paper grain or round the lettering;
   - the union cell shows no ring through the first road;
   - the reserve cells read as bare paper with, in the pooled row, a faint edge and no drawn
     outline.
4. Record "pass" or the defect per image in the "judged at 2x" column of `images.md`. A failed
   image goes back to its track; nothing regenerates until every image passes.

## Files to leave alone

- every file under `src/`
- `examples/setting_grids.py`, the galleries and the five grid scripts
- `tests/support/docs_images.py` and its budgets
- `SHARES_009A`'s values
- the Lynmouth goldens
- every theme YAML
- `BUILT_IN_PRESETS`
- ADR 0070
- `CLAUDE.md`, `CONTRIBUTING.md`

## Changelog (added under "Changelog" in #213's description)

```
docs(docs): the line effect sweeps and figures are painted at 2x, with a reserve sweep and a casing union shown
docs(docs): how to reserve the paper round a line and case several classes as one
```
