# 004 — Span curve scale sweep

GitHub issue: [#54](https://github.com/findlaywebb/pyntpot/issues/54)
(note: `docs/issues/maps-lettering-span-sides-curve-scale-offset.md`).

## Problem

`span_sides.SPAN_CURVE_SCALE_CAPS = 1.5` is the spacing, in cap heights, at which a span's
stretch is resampled before `bend_strength` reads its turning. It gates and weighs the
bend's vote in `curved_side`. Its comment cites a sweep (89% right at 1.5 caps, 79% at 2)
over "187 stretches from the four cached tracks". That sweep left no script, no record of
how stretches were chosen, no scoring rule and no labels, and it ran against an older mark
(offset 1.7 caps, the old free-paper sign, an iso-contour bracket since replaced). The
mark is now drawn at `span_line.SPAN_OFFSET_CAPS = 1.2`. So 1.5 is untested against the
code that ships. This spec does not try to reproduce 89% or 79%.

This spec fixes the stretch generator, the scoring rule, the sweep and the decision rule
**before any sweep is run**, so the history shows the rule came first.

## Data

Public data only. The routes are the committed synthetic tracks `tests/fixtures/<box>/track.gpx`
of three fixture boxes, Ambleside, Skye and Y Fenni. Each one is OpenStreetMap ways joined by
`tests/fixtures/make_track.py` (see each fixture's `README.md`). They are projected exactly as
the golden place cards project them: `fetch` from a copy of the fixture with request
budget 0, each fixture's own theme and recorded margins as in `tests/golden/test_places.py`,
then `card.xy` on `basemap.track` and `separate_strands(..., strand_gap_px(style))`. That
gives the `route_px` the lettering places spans against. No athlete track, activity id or
coordinate from one is read or written. Nothing is fetched. No coordinate is logged or
written to any output.

`cap_px` is 14.0, the value `placement.place` passes to `place_spans` (its default).

## The stretch generator

Sliding stretches along each fixture's `route_px`, measured by arc length in display
pixels:

- **Length: 16 cap heights** (224 px). The coarsest scale swept, 2.5 caps, must still leave
  the stretch at least five resampled segments (16 / 2.5 = 6.4), or `route_turn` measures
  almost nothing. The routes are 1327 px (Ambleside), 1424 px (Y Fenni) and 2813 px (Skye)
  long in display pixels. So a stretch is about a sixth, a sixth and a twelfth of its
  route: a part of the route, as a span is, and not most of it.
- **Step: 2 cap heights** (28 px). A bend is then seen at eight phases inside a stretch
  rather than at one. Consecutive stretches overlap by seven eighths, so they are not
  independent. The decision rule below counts that.
- A stretch runs from the first route index at or past arc length `s` to the first index at
  or past `s + 16 caps`, for `s = 0, step, 2·step, ...` while `s + 16 caps` is no more than the
  route's length. A stretch with fewer than three points is skipped.
- Secondary, reported but never used to choose: the same sweep at lengths 10 and 24 cap
  heights (same 2-cap step), to show whether the answer depends on the length chosen.

## The scoring rule

For each stretch `Span(i0, i1)`, `_convex_side(span, route_px, cap_px)` gives the outside
`o` (+1, -1 or 0) and the mark each side draws. These are the marks `place_spans` draws for
rung 0: offset `cap_px * SPAN_OFFSET_CAPS`, clearance `cap_px * SPAN_CLEAR_CAPS`. A stretch
with `o = 0` has no outside and is not scored.

Each side's mark gets two measured qualities:

- **broken**: `_mark_broken(mark, route_px, cap_px * SPAN_CLEAR_CAPS)`. The mark is empty
  or not clear of the route.
- **coverage**: how much of the stretch the mark spans. Drop a foot from the mark's first
  point and from its last point onto the stretch (segments, not vertices). Coverage is the
  arc length along the stretch between the two feet, divided by the stretch's arc length,
  between 0 and 1. A mark cut back by the clearance pass, or folded out on the inside of a
  bend, covers less of its stretch. Raw mark length is **not** the metric. An offset line
  is longer on the outside of a bend by geometry alone (about `2 · offset · turn`), so a
  length comparison would score the outside right by construction.

A stretch is **decisive** when the two marks differ in a measured quality:

1. exactly one side's mark is broken; or
2. neither is broken and one side's coverage is more than **1.25 times** the other's. That
   is a quarter better, the same "clearly better" ratio `spans.SPAN_SIDE_SWAP_MARGIN` uses
   to move a mark. It is stated here as a literal so that tuning that constant later does
   not move this rule.

Both broken, or coverages within the ratio, is not decisive. The **better** mark is the
unbroken one in case 1 and the higher-coverage one in case 2. The **outside is right**
when `o` is the better side. The ground truth is these measured qualities, never
judgement by eye.

The free-paper side and its darkness margin are not part of the score. The scale only
decides whether, and how strongly, the bend votes (`bend_strength > 0`). The question the
sweep asks is whether the side the vote pushes towards is the better mark. The free-paper
rule as it ships (signed as `span_line` draws, `freer_side`) is unchanged and unread here.

## The sweep

On the current code: offset 1.2 caps, the shipped `_convex_side`, `bend_strength`,
`span_line` and free-paper sign. For each scale `k` from 0.6 to 2.5 caps in steps of 0.1
(20 values, 1.5 among them), a stretch is **voted** when
`bend_strength(route_px[i0 : i1 + 1], cap_px * k) > 0`. Per scale, the output is:

| column | meaning |
|---|---|
| scale | `k`, in cap heights |
| voted | stretches the bend votes on |
| decisive | voted, decisive stretches with an outside: `n` |
| right | of those, how many the outside is right on |
| % right | `100 · right / n`, to one decimal |
| refused | of the wrong ones, how many `curved_side`'s broken-outside refusal already stops (the outside is broken and the other side is not) |

The table goes in `specs/004-span-curve-scale-sweep/sweep.md`, with the per-fixture
stretch counts and the secondary-length tables.

## The decision rule

1. A scale is eligible when its `n` at the 16-cap length is at least 30.
2. The best scale is the eligible one with the highest % right. A tie (equal to 0.1
   percentage points) goes to the larger `n`, which is the more decisive evidence, and
   then to the smaller scale.
3. **Can the sweep tell the scales apart?** Stretches overlap, so the effective count is
   `n_eff = n · step / length = n / 8`. Take the Agresti–Coull 95% interval of the best
   scale's share right on `n_eff` (`p̃ = (p · n_eff + 2) / (n_eff + 4)`, half-width
   `1.96 · sqrt(p̃ (1 − p̃) / (n_eff + 4))`). The value changes only when 1.5's % right
   lies below that interval's lower bound. Otherwise, or when no scale is eligible,
   1.5 stays. The numbers that decided it are recorded in `sweep.md` and reported. A
   choice is not forced.
4. When the value changes and the best scale is `m · SPAN_OFFSET_CAPS` for `m` a multiple
   of 0.5 (0.6, 1.2, 1.8, 2.4), the constant is written as that product, not a bare
   literal.

## Acceptance criteria

- [ ] This spec, with the generator, scoring rule, sweep and decision rule, is committed
      before the sweep runs.
- [ ] The sweep tool lives under `tests/fixtures/`. It obeys the boundary, logs and never
      prints, reads no environment, and writes no coordinate. Its stretch generator and
      scorer have unit tests on small, deterministic, real objects (no mocks).
- [ ] `sweep.md` holds the full table (all 20 scales), the per-fixture counts, the
      secondary lengths and the decision-rule arithmetic.
- [ ] `SPAN_CURVE_SCALE_CAPS` is set from the result by the decision rule, or kept at 1.5
      with the reason. Its comment states the scoring rule as a capability fact (what was
      measured on which public tracks, and the share right), with no spec number and no
      89%/79% figures.
- [ ] If the value changes, a test pins a behaviour the new scale has and the old did not,
      when one exists that is meaningful (not a restatement of the literal).
- [ ] The span tests in `tests/unit/maps/lettering/` and every golden are reviewed. No
      golden card carries a span today, so none is expected to move. Any that does is
      regenerated only by the documented process, with the diff explained.
- [ ] `docs/issues/maps-lettering-span-sides-curve-scale-offset.md` is deleted, and no file
      outside `specs/001-port/` (history) refers to it.
- [ ] Gates green: `uv run pytest -n auto --dist loadgroup`, `uv run ruff check .`,
      `uv run ruff format --check .`, `uv run ty check`, `uv run lint-imports`,
      `prek run --all-files`.

## Out of scope

- `SPAN_CURVE_MIN_TURN_DEG`, `SPAN_CURVE_FULL_TURN_DEG`, `SPAN_CURVE_MIN_COHERENCE` and
  `SPAN_CURVE_WEIGHT`. Their comments cite the same unrecorded sweep. That is a follow-up
  for the backlog (a new note and issue), not this diff. Only the words that would dangle
  once the scale comment is rewritten ("the same 187 stretches") are touched.
- The other fixture boxes (Lynmouth, Oxford, Yr Wyddfa) and any new recording.
- Any change to `_convex_side`, `bend_strength`, `span_line` or the free-paper rule.
- River name clipping (#53) and cover fill (#45).
