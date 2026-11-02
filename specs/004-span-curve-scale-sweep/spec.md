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
budget 0, each fixture's own theme (`examples/themes/<box>.toml`) and recorded margins, then
`card.xy` on `basemap.track` and `pyntpot.maps.strands.separate_strands(...,
strand_gap_px(style))`. The margins are those of `tests/golden/test_places.py`: Skye
18000 m features and 18000 m land cover; Ambleside and Y Fenni the defaults,
`pyntpot.maps.cache.MARGIN_M` and `LANDCOVER_MARGIN_M`. That gives the `route_px` the
lettering places spans against. No athlete track, activity id or coordinate from one is read
or written. Nothing is fetched. No coordinate is logged or written to any output.

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
  heights (same 2-cap step), to show whether the answer depends on the length chosen. At 10
  caps the five-segment argument holds only up to a scale of 2.0 (10 / 2.0 = 5), so the
  10-cap table stops at 2.0; the 24-cap table runs the full range.

## The scoring rule

For each stretch `Span(i0, i1)`, `_convex_side(span, route_px, cap_px)` gives the outside
`o` (+1, -1 or 0) and the mark each side draws. These are the marks `place_spans` draws for
rung 0: offset `cap_px * SPAN_OFFSET_CAPS`, clearance `cap_px * SPAN_CLEAR_CAPS`.

`span_line` ends in `clear_of`, which returns a line clear of the route or an empty list.
So a drawn mark is never "not clear": a mark is either drawn or empty. And when one side's
mark is empty, `_convex_side` returns the drawn side as the outside, so scoring such a
stretch would score the outside right by construction. Hence each stretch falls into
exactly one **case**, checked in this order:

| case | when | scored? |
|---|---|---|
| `no-outside` | `o = 0` | no; counted |
| `empty-mark` | either side's mark has fewer than two points: the vote can only go to the drawn side | no; counted |
| `reversed-feet` | either side's coverage is negative (below) | no; counted |
| `even` | coverages within the ratio below | no; counted |
| `decisive` | one coverage more than 1.25 times the other | yes |

**Coverage** is how much of the stretch a drawn mark spans. Drop a foot from the mark's
first point and from its last point onto the stretch (segments, not vertices), and take
each foot's arc-length position along the stretch. Coverage is `(s_last − s_first)`
divided by the stretch's arc length: **signed**, not absolute. A negative value means the
feet came back in the wrong order, which happens where a narrow bend puts the nearest
segment on the far limb; the foot is then ambiguous, so the stretch is the
`reversed-feet` case and is excluded. Coverage is lowered when `clear_of`'s
`_longest_clear` cuts the mark back to its longest clear run, which trims the ends. Folds
cut out on the inside of a bend (`_drop_folds`, `_forward_only`) keep the ends and do not
lower it. Raw mark length is **not** the metric: an offset line is longer on the outside
of a bend by geometry alone (about `2 · offset · turn`), so a length comparison would score
the outside right by construction. The foot of each end cancels that bulge.

**Decisive** is the coverage ratio and nothing else: with `hi` and `lo` the two sides'
coverages, the stretch is decisive exactly when `hi > 1.25 * lo`. So `lo = 0` with
`hi > 0` is decisive, and both 0 is not. 1.25 is a quarter better, the same "clearly
better" ratio `spans.SPAN_SIDE_SWAP_MARGIN` uses to move a mark; it is a literal here so
that tuning that constant later does not move this rule. The **better** mark is the one
with the higher coverage. The **outside is right** when `o` is the better side. The ground
truth is this measured quality, never judgement by eye.

The free-paper side and its darkness margin are not part of the score. The scale only
decides whether, and how strongly, the bend votes (`bend_strength > 0`). The question the
sweep asks is whether the side the vote pushes towards is the better mark. The free-paper
rule as it ships (signed as `span_line` draws, `freer_side`) is unchanged and unread here.

## The sweep

On the current code: offset 1.2 caps, the shipped `_convex_side`, `bend_strength`,
`span_line` and free-paper sign. For each scale `k` in `[i / 10 for i in range(6, 26)]`
(0.6 to 2.5 caps, 20 values, 1.5 among them), a stretch is **voted** when
`bend_strength(route_px[i0 : i1 + 1], cap_px * k) > 0`. Per scale, the output is:

| column | meaning |
|---|---|
| scale | `k`, in cap heights |
| voted | stretches the bend votes on |
| empty-mark | voted stretches excluded because a side drew no mark |
| reversed-feet | voted stretches excluded for ambiguous feet |
| decisive | voted, decisive stretches: `n` |
| right | of those, how many the outside is right on |
| % right | `100 · right / n`, to one decimal; blank when `n = 0` |

The table goes in `specs/004-span-curve-scale-sweep/sweep.md`, with the per-fixture count
of stretches in each case and the secondary-length tables.

## The decision rule

The expected outcome, stated before the sweep: **1.5 is kept.** The probe in the plan
review counted 176 stretches over the three fixtures and 37 coverage-decisive ones before
the voting filter. At about 25 independent stretches the data cannot separate scales a
tenth of a cap apart. #54 closes on that recorded result.

1. If `n` at 1.5 is 0 or below 30, 1.5 is kept, its `n` is recorded, and no comparison is
   made.
2. Otherwise a scale is eligible when its `n` is at least 30. The best scale is the
   eligible one with the highest `round(% right, 1)`. A tie goes to the larger `n`, then to
   the smaller scale.
3. Stretches overlap, so the effective count is
   `n_eff = n · step_caps / length_caps = n / 8`. Take the Agresti–Coull 95% interval of the
   best scale's share right on `n_eff`: `p̃ = (p · n_eff + 2) / (n_eff + 4)`, half-width
   `1.96 · sqrt(p̃ (1 − p̃) / (n_eff + 4))`. The value changes only when 1.5's share right
   lies below that interval's lower bound. Otherwise 1.5 stays. The numbers that decided it
   are recorded in `sweep.md`. A choice is not forced.
4. When the value changes and the best scale is `m · SPAN_OFFSET_CAPS` for `m` a multiple
   of 0.5 (within 1e-9, since `1.8 / 1.2` is not exactly 1.5 in floating point), the
   constant is written as that product, not a bare literal.

### The comment, pre-written

When 1.5 is kept (the expected case), `SPAN_CURVE_SCALE_CAPS`'s comment keeps its
argument for reading near the offset and replaces the old sweep with this form, the
blanks filled from `sweep.md`:

> Measured on the Ambleside, Skye and Y Fenni fixture tracks, in stretches 16 cap heights
> long taken every 2, with the mark drawn at `SPAN_OFFSET_CAPS`: of the stretches where
> both sides draw a mark and one covers more than a quarter more of its stretch than the
> other, the outside is the better mark on `R` of `N` (`P`%) read at 1.5. Scales from
> 0.6 to 2.5 could not be told apart on that data, so 1.5 stands.

When `N` is below 30, the last sentence becomes "`N` stretches are too few to compare
scales, so 1.5 stands." If the rule changes the value, the comment states the same
measurement at the new scale and the interval that separated it from 1.5.

## Acceptance criteria

- [ ] This spec, with the generator, scoring rule, sweep and decision rule, is committed
      before any stretch is scored at any scale.
- [ ] The sweep tool lives under `tests/fixtures/`. It imports only `pyntpot` and the
      standard library, logs and never prints, reads no environment, and writes no
      coordinate. Its stretch generator and scorer have unit tests on small, deterministic,
      real objects (no mocks). The tool and its test are each at most 400 lines.
- [ ] `sweep.md` holds the full table (all 20 scales), the per-fixture case counts, the
      secondary lengths and the decision-rule arithmetic.
- [ ] `SPAN_CURVE_SCALE_CAPS` is set by the decision rule (expected: kept at 1.5). Its
      comment takes the pre-written form as a capability fact, with no spec number and no
      89%/79% figures.
- [ ] If the value changes, a test pins a behaviour the new scale has and the old did not,
      when a meaningful one exists (not a restatement of the literal).
- [ ] The span tests in `tests/unit/maps/lettering/` and every golden are reviewed. No
      golden card carries a span today, so none is expected to move. Any that does is
      regenerated only by the documented process, with the diff explained.
- [ ] `docs/issues/maps-lettering-span-sides-curve-scale-offset.md` is deleted, and no file
      outside `specs/001-port/` (history) refers to it. #54 closes with the PR.
- [ ] Gates green: `uv run pytest -n auto --dist loadgroup`, `uv run ruff check .`,
      `uv run ruff format --check .`, `uv run ty check`, `uv run lint-imports`,
      `prek run --all-files`.

## Out of scope

Follow-ups, filed separately as notes and issues by the coordinator, not in this diff:

- `curved_side`'s broken-outside refusal can never run: `span_line` returns a clear mark or
  none, and `_convex_side` already returns the drawn side when one is empty. Its docstring's
  claim that the refusal turns the term from roughly even into clearly worth having does
  not hold.
- `SPAN_CURVE_MIN_TURN_DEG`, `SPAN_CURVE_FULL_TURN_DEG`, `SPAN_CURVE_MIN_COHERENCE` and
  `SPAN_CURVE_WEIGHT` cite the same unrecorded sweep. Only the words that would dangle once
  the scale comment is rewritten ("the same 187 stretches") are touched here.
- The 10-cap secondary length above a scale of 2.0 (capped here; see the generator).

Also out:

- The other fixture boxes (Lynmouth, Oxford, Yr Wyddfa) and any new recording.
- Any change to `_convex_side`, `bend_strength`, `span_line` or the free-paper rule.
- River name clipping (#53) and cover fill (#45).
