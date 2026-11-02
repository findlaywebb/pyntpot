# 004 — plan

## Approach

Layer: `maps` (lettering) only, and one constant in it. No boundary or public-API change,
so no ADR. `SPAN_CURVE_SCALE_CAPS` is a module constant, not exported from
`pyntpot.maps.__init__`.

The work is a measurement tool under `tests/fixtures/` plus a constant set from its output.
`tests/fixtures/` is where the repo keeps the scripts that read or build the fixtures
(`make_track.py`, `trim_fixture.py`, `record_fixture.py`). Each is run as
`uv run python tests/fixtures/<name>.py ...`, imported by its tests as
`fixtures.<name>` (pytest `pythonpath = ["tests"]`), logs through `logging`, takes its
config as arguments and never reads the environment. The sweep tool follows the same
convention. It is not under `src/`, so it is outside the package boundary contract, but it
imports only `pyntpot` (public `pyntpot.maps` names, plus the lettering modules it
measures, `span_sides` private helpers included, as the unit tests already do) and the
standard library. It does not import `httpx`. Nothing is fetched: the providers get
`budget=0` and a dead endpoint, as `tests/golden/test_places.py` does.

Order (the commit history must show the rule first):

1. Commit `spec.md`, `plan.md`, `tasks.md`. The plan-reviewer passes the plan.
2. Test-first: the generator and scorer tests, red; then the tool, green.
3. Run the sweep once and write `sweep.md`.
4. Apply the decision rule (spec, "The decision rule"). Set or keep the constant, and
   rewrite its comment.
5. Pin behaviour if the value moved. Review span tests and goldens.
6. Delete the note. Gates. Commit and push.

## The tool: `tests/fixtures/sweep_span_scale.py`

Pure functions first, CLI last; at most 400 lines (split along generator/scorer vs CLI if
it grows past it, never trimmed).

Imports: the standard library; `pyntpot.maps` (`Cache`, `FetchMargins`, `OpenTopoData`,
`OverpassFeatures`, `Style`, `Track`, `fetch`); `pyntpot.maps.cache` (`MARGIN_M`,
`LANDCOVER_MARGIN_M`); `pyntpot.maps.strands` (`separate_strands`, `strand_gap_px`);
`pyntpot.ink.polyline` (`Pt`, `length`); `pyntpot.maps.lettering.label` (`Span`);
`pyntpot.maps.lettering.span_line` (`SPAN_OFFSET_CAPS`);
`pyntpot.maps.lettering.span_sides` (`_convex_side`, `bend_strength`). No `httpx`.

- `SCALES = [i / 10 for i in range(6, 26)]`, `SECONDARY = {10.0: max scale 2.0,
  24.0: max scale 2.5}`, `CLEARLY_BETTER_RATIO = 1.25`, `MULTIPLE_TOL = 1e-9`.
- `stretches(route_px, cap_px, length_caps, step_caps) -> list[tuple[int, int]]`: the
  spec's sliding stretches as `(i0, i1)` index pairs.
- `coverage(mark, sub) -> float`: feet of the mark's first and last points on `sub` by
  segment (arc-length position = cumulative length to the segment plus `t` along it),
  **signed** `(s_last - s_first) / length(sub)`; may be negative; 0.0 for a mark under
  two points or a zero-length `sub`.
- `decisive(a: float, b: float) -> int`: the two sides' coverages (`a` for side +1, `b`
  for side -1); returns +1 or -1 for the better side when `hi > CLEARLY_BETTER_RATIO * lo`,
  else 0. `lo = 0, hi > 0` is decisive; both 0 is not.
- `Verdict` (frozen dataclass): `case: str` (one of `no-outside`, `empty-mark`,
  `reversed-feet`, `even`, `decisive`, checked in the spec's order), `outside: int`,
  `better: int` (0 unless `case == "decisive"`), with a `right` property.
- `judge(span, route_px, cap_px) -> Verdict`: `_convex_side` for the outside and the two
  marks, then the spec's cases. `_mark_broken` is not used: a drawn mark is always clear.
- `ScaleRow` (frozen dataclass: `scale, voted, empty_mark, reversed_feet, decisive,
  right`) with a `percent_right` property (`None` when `decisive == 0`), and
  `sweep(cases, cap_px, scales) -> list[ScaleRow]`, where a case is
  `(sub, verdict)` with `sub = route_px[i0 : i1 + 1]`. The verdict is computed once per
  stretch (it does not depend on the scale). Only `bend_strength` is re-run per scale.
- `Decision` (frozen dataclass: `scale`, `changed`, `reason`, `n_current`, `best`,
  `lower`, `upper`, `multiple`) and
  `decide(rows, length_caps, step_caps, current=1.5, n_min=30) -> Decision`: the spec's
  decision rule. Ties on `round(percent_right, 1)`. `n_eff = n * step_caps / length_caps`.
  `multiple` is `m` when `abs(scale / SPAN_OFFSET_CAPS - m) < MULTIPLE_TOL` for `m` a
  multiple of 0.5, else `None`.
- `FIXTURES`: `(directory, theme, FetchMargins)` for the three boxes, from
  `tests/golden/test_places.py`: Skye `FetchMargins(18000.0, 18000.0)`, Ambleside and
  Y Fenni `FetchMargins(MARGIN_M, LANDCOVER_MARGIN_M)`; themes
  `examples/themes/<box>.toml`.
- `fixture_route(directory, theme, margins) -> list[Pt]`: copies the fixture to a
  `tempfile.TemporaryDirectory`, then `fetch` (providers at `http://127.0.0.1:9`,
  `budget=0`), `card.xy`, `separate_strands(route, strand_gap_px(style))`.
- `main(argv)`: `--out PATH` (the `sweep.md` to write), `--cap-px` (default 14.0). Writes
  the markdown tables to `--out`. Logs a one-line summary per scale and the decision.
  `if __name__ == "__main__": main()`.

No coordinate appears in the tool, its tests or its output. Only counts, scales and
shares are written.

## Files to touch

- `specs/004-span-curve-scale-sweep/spec.md`, `plan.md`, `tasks.md` (new); `sweep.md`
  (new, the tool's output, committed as written); `review.md` (new, the plan-review rounds,
  as `specs/003-*/review.md` does).
- `tests/fixtures/sweep_span_scale.py` (new): the tool.
- `tests/fixtures/test_sweep_span_scale.py` (new): its tests.
- `src/pyntpot/maps/lettering/span_sides.py`: `SPAN_CURVE_SCALE_CAPS` value (expected:
  kept) and its comment, rewritten in the spec's pre-written form ("The comment,
  pre-written"), the blanks filled from `sweep.md`. No spec number, no 89%/79%, no
  "the four cached tracks" in that comment. In `SPAN_CURVE_WEIGHT`'s comment, "Over the
  same 187 stretches" becomes "Over 187 stretches from the four cached tracks", so its own
  claim stands once the scale comment no longer introduces the 187. That is the only edit
  outside the scale constant.
- `tests/unit/maps/lettering/test_span_sides.py`: one pinned behaviour test, only if the
  value moves and a meaningful one exists (Test plan, T6).
- `docs/issues/maps-lettering-span-sides-curve-scale-offset.md`: deleted.

## Files to leave alone

- `span_sides.py` logic (`bend_strength`, `_convex_side`, `_mark_broken`, `curved_side`,
  `freer_side`) and the other `SPAN_CURVE_*` constants. Tempting, because their comments
  cite the same lost sweep. They are a separate question with a separate rule; out of scope
  per the spec. Report as a follow-up.
- `span_line.py` (`SPAN_OFFSET_CAPS`), `span_clear.py`, `spans.py`
  (`SPAN_SIDE_SWAP_MARGIN`). The scorer copies the 1.25 ratio as a literal on purpose, so
  tuning the constant later does not move the rule.
- `specs/001-port/p10-triage.md`, `specs/001-port/plan.md`: they record history (the
  deferral). They are not current references to a live note, so they are not rewritten.
- `tests/golden/**`, `examples/places.toml`: no golden card carries a span. Regenerate
  only if a golden test goes red (it should not).
- `maps/lettering/placement_along.py`, `picks_rivers.py` and anything river-name
  related (#53). Cover and land-cover code (#45).
- `tests/fixtures/<box>/*`: read, never written; the tool copies to a temp directory.

## Test plan

No mocks; real `Span`s, real polylines built in the test, `support.lettering.arc` for
bends. One docstring line per test; `parametrize` with `ids=`. Function-scoped fixtures
only.

- **T1 generator** (`TestStretches`): a straight route of 101 points 1 px apart with
  `cap_px=1`, length 16, step 2 gives the pinned pairs `(0, 16), (2, 18), ...,
  (84, 100)`: 43 stretches. A route shorter than one length gives none. The step and the
  length are in cap heights: at `cap_px=2` the same route gives 18 stretches, pinned. A
  route with uneven spacing starts each stretch at the first index at or past `s`.
- **T2 coverage**: a mark that runs the length of a straight stretch at an offset has
  coverage 1.0; one over its middle half has 0.5; a mark drawn backwards (last point
  before the first along the stretch) has coverage -0.5, negative; a one-point mark has
  0.0.
- **T3 judge and decisive**:
  - `decisive(0.8, 0.64)` is 0 (ratio exactly 1.25; 0.64 * 1.25 is 0.8 in floating
    point, checked) and `decisive(0.8, 0.63)` is +1; `decisive(0.0, 0.5)` is -1;
    `decisive(0.0, 0.0)` is 0;
  - a bend `arc(120.0, r=R)` with `R` below offset plus clearance (16.8 + 7 = 23.8 px at
    `cap_px=14`), so the inside mark is cut back but still drawn: case `decisive` and the
    outside right. `R` (about 20) and the turn are chosen by measuring under the shipped
    `span_line` and pinned; if no such arc gives a drawn inside mark, the test pins the
    `empty-mark` case on it instead and a hand-built `Verdict` covers `right`;
  - a stretch where one side draws nothing (a route doubling back tight enough that one
    side is empty, found by measuring): case `empty-mark`, excluded;
  - a straight stretch: case `no-outside`, `outside == 0`.
- **T4 sweep and decide** on constructed `ScaleRow`s (pure data, pinned literals): `n` at
  1.5 of 0 and of 29 keeps 1.5 with no comparison; the tie-breaks on `round(pct, 1)`
  (larger `n`, then smaller scale); the eligibility floor (`n < 30` skipped); keeping 1.5
  when it lies inside the best's interval; changing when it lies below, with the pinned
  bounds; `multiple` is 1.5 for the scale `SCALES[12]` (which is `1.8` as computed) and
  `None` for `SCALES[11]` (1.7), compared with `pytest.approx`, never `== 1.8`. `sweep` on
  two hand-made cases (a hard bend voted at every scale, a straight never voted) gives the
  pinned counts.
- **T5 real fixture, golden-marked** (`@pytest.mark.golden`, since it runs `fetch`): the Y
  Fenni route (the cheapest fetch, about 0.2 s) gives a pinned stretch count at 16/2 caps.
  The literal is read from the first run and pinned. A change in projection or strands
  then shows up here.
- **T6 chosen value** (only if it moves): a stretch whose `bend_strength` at
  `cap_px * SPAN_CURVE_SCALE_CAPS` differs in kind (zero against positive) from the old
  1.5, and `curved_side` moves or keeps the side accordingly. If no such stretch is
  meaningful, no test is added and `tasks.md` says why. Expected not to apply (1.5 kept).
- **Existing tests**: `test_span_sides.py`, `test_spans.py` and `test_lettering_marks.py`
  run unchanged. If one goes red under a new value, that is the behaviour change. It is
  reviewed against the sweep, and the test is updated only if the old expectation was
  pinned to the old scale's behaviour, with the reason in the commit.
- **Goldens**: `uv run pytest -m golden` exact locally before and after. Expected
  unchanged (no spans).
- **Gates over `tests/`**: what does cover the tool is ruff `T20` (no print), ruff `TID`
  banned-api, ruff `D` (docstrings), the coordinate gate and the no-mock gate. The
  400-line budget and the print/environ AST tests scan `src` only
  (`tests/architecture/_ast_checks.PACKAGES`), and vulture is `src` only, so the tool's
  line count is checked by hand (`wc -l`, a task) and its no-environ rule by review.

## Verification

- The sweep is run once, after the spec commit, with
  `uv run python tests/fixtures/sweep_span_scale.py --out specs/004-span-curve-scale-sweep/sweep.md`.
  `sweep.md` is committed as the tool wrote it, then annotated below a rule line with
  the decision.
- Gates: `uv run pytest -n auto --dist loadgroup`, `uv run ruff check .`,
  `uv run ruff format --check .`, `uv run ty check`, `uv run lint-imports`,
  `prek run --all-files`.

## Delegation

Small enough for one context. Dispatched: the plan-reviewer gate (fresh context) and a
fresh-context diff review against this plan before the PR. The sweep tool, the
measurement and the constant stay in the main context: the decision has to be made by
whoever read the table.

## File-ownership partition

One owner for every file above. Parallel agents are on #53 (river path-name clipping in
`maps/lettering` placement code) and #45 (cover fill). This plan touches neither area.
`span_sides.py` and `test_span_sides.py` are this branch's alone.

## Decisions

- **Coverage, not length**, is the quality metric (spec, "The scoring rule"). Length
  favours the outside by geometry and would make the sweep circular.
- **Empty marks excluded, not scored** (review round 1, finding 1): `span_line` returns a
  clear mark or none, and `_convex_side` names the drawn side as the outside when the
  other is empty, so scoring those stretches would score the outside right by
  construction. They are counted in their own column.
- **Signed coverage** (finding 3): reversed feet are ambiguous, excluded and counted,
  rather than hidden by `abs()`.
- **Expected outcome: 1.5 kept** (finding 2, the user's option (a)): about 25
  independent stretches cannot separate scales a tenth of a cap apart. The comment form
  is pre-written in the spec and #54 closes on it.
- **Effective count n/8**: overlapping stretches are not independent. The decision rule
  discounts them rather than reporting a false precision.
- **Three boxes, existing tracks**: the data rule names Ambleside, Skye and Y Fenni. Their
  committed tracks are OSM ways, so they are usable, and nothing new is fetched.
