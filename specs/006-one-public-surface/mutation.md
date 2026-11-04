# 006 mutation run (S10)

Local, advisory (ADR 0012), on the functions whose behaviour this branch changed
(plan.md "S10 — Mutation testing"). mutmut 3.8.0, run from `HEAD` `702c1b4` (round 1)
and re-run from each new `HEAD` after the survivors' tests were committed.

## Run list

The rule, run as a throwaway script in the scratchpad:
`uv run python tests/mutation/scope.py --base origin/main --out "$patterns"` listed 51
touched `ink`/`letters` functions. Their bodies were compared with `origin/main` as a
normalised AST (docstring dropped, `ast.unparse`, the old text with `Pt` → `Point`,
`Anchor` → `Align`, `pyntpot.ink.wash` → `pyntpot.ink.washing`, `pyntpot.ink.stamp` →
`pyntpot.ink.stamping`, old paths through the module renames). Two differ:
`pyntpot.ink.bloom.x_bloom*` and `pyntpot.ink.washing.x_wash*`, which are the table's two
`ink` rows; no `letters` function differs (the generated keyword-only `__init__`s have no
source to mutate). The run list is the table: two `ink` patterns and the seven `maps`
patterns. `PaintJob.flow` is not run (a `@property`, which mutmut does not mutate; plan.md
gives the reason).

## Scores

| Function | Pattern | Generated | Killed | Equivalent |
| --- | --- | --- | --- | --- |
| `ink.washing.wash` | `pyntpot.ink.washing.x_wash*` | 203 | 195 | 8 |
| `ink.bloom.bloom` | `pyntpot.ink.bloom.x_bloom__mutmut_*` | 202 | 193 | 9 |
| `maps.lettering.picks_roads.named_roads` | `…picks_roads.x_named_roads*` | 84 | 83 | 1 |
| `maps.lettering.picks_roads._road_pieces` | `…picks_roads.x__road_pieces*` | 69 | 64 | 5 |
| `maps.lettering.picks_roads.pick_roads` | `…picks_roads.x_pick_roads*` | 91 | 87 | 4 |
| `maps.lettering.picks_lines.named_lines` | `…picks_lines.x_named_lines*` | 135 | 132 | 3 |
| `maps.lettering.pipeline._ground` | `…pipeline.x__ground*` | 37 | 35 | 2 |
| `maps.projection.track_projection` | `…projection.x_track_projection*` | 52 | 51 | 1 |
| `maps.painter.job.PaintJob.bloom` | `…job.xǁPaintJobǁbloom*` | 53 | 53 | 0 |

No function had `no tests`. Round 1 left 55 `ink` and 109 `maps` survivors; every one is
now killed or listed below.

## Equivalent mutants

### `ink.washing.wash`

- `x_wash__mutmut_54`, `x_wash__mutmut_64` (`np.clip(a - blur(a, o.rim_px), 0.0, None)`
  and `…, 0.0, 2.0)`): `a` is in 0 to 1 and `blur(a)` is non-negative and includes the
  pixel's own weight, so `a - blur(a)` never exceeds 1 and the upper clip never acts.
- `x_wash__mutmut_67` (`peak >= _RIM_PEAK`): `peak` is a float32 value and `1e-5` is not
  representable in float32, so `peak == 1e-5` never holds and `>=` is `>`.
- `x_wash__mutmut_145` (`bloom(dens, a, None, o.blooms)`): `bloom` never reads its
  `sheet` argument.
- `x_wash__mutmut_156` (`blur(dens, 2.6)`): `blur` takes the radius
  `max(1, round(sigma * 0.95))`, and 1.6 and 2.6 both give 2.
- `x_wash__mutmut_166` (`np.clip(m * 2.0, None, 1)`): `sheet.wet` is fbm normalised to 0
  to 1, so `m * 2.0` is never below 0.
- `x_wash__mutmut_178`, `x_wash__mutmut_187` (`np.clip(m * 2.0 - 1.0, 0, None)` and
  `…, 0, 2)`): `sheet.wet` is at most 1, so `m * 2.0 - 1.0` is never above 1.

### `ink.bloom.bloom`

- `x_bloom__mutmut_36` (`astype(None)`): NumPy reads a `None` dtype as float64, the type
  it replaces.
- `x_bloom__mutmut_107` (`y1 + y0 < _MIN_BOX`): it differs only when a box is under 5 rows
  with `y0 > 0`; a clipped box keeps `span + 1` rows, so that needs a span of 3, so a
  radius under 0.75 px, so a plate at most 3 px on one side; `y0 > 0` needs over 3 rows,
  so that side is the width, and the column test skips the bloom anyway.
- `x_bloom__mutmut_109` (`x1 + x0 < _MIN_BOX`): the same argument with rows and columns
  swapped.
- `x_bloom__mutmut_111` (`break` for `continue`): whether a box is skipped depends only on
  the plate's size: a plate under 5 px on a side skips every bloom, and one 5 px or more on
  both sides skips none (its span is at least 4, so a clipped box keeps 5 rows), so
  stopping at the first skip lays the same.
- `x_bloom__mutmut_119`, `x_bloom__mutmut_122`, `x_bloom__mutmut_127`,
  `x_bloom__mutmut_130` (the box offsets' `dtype=F32` set to `None` or dropped): the
  offsets become int64, which promotes the warped distance to float64 before it is stored
  back into the float32 density; the plate differs only in float32 rounding (at most
  1.2e-6 on the pinned plates), which only a machine-bound bit-exact pin could see.
- `x_bloom__mutmut_173` (`d <= r`): `r` scales a uniform draw and `d` carries fbm noise,
  both continuous, so `d == r` exactly does not occur on any plate a test can build.

### `maps`

- `pick_roads` `x_pick_roads__mutmut_5`, `named_roads` `x_named_roads__mutmut_12`,
  `_road_pieces` `x__road_pieces__mutmut_52`, `_ground` `x__ground__mutmut_4` and
  `x__ground__mutmut_29` (the basemap passed on as `None`): the basemap reaches only
  `feature_px(basemap, "road", …)`, which reads the basemap for a river alone; a road's
  width is its class default.
- `_road_pieces` `x__road_pieces__mutmut_53`, `x__road_pieces__mutmut_58`,
  `x__road_pieces__mutmut_59` (`feature_px`'s kind `None`, `"XXroadXX"`, `"ROAD"`):
  `feature_px` tests the kind only against `"river"`, so any other kind is a road.
- `_road_pieces` `x__road_pieces__mutmut_51` (`widths.get(key, 1.0)`): every road width is
  at least 3.4 × 1.35 = 4.59 px, so `max(1.0, width)` is the width.
- `pick_roads` `x_pick_roads__mutmut_88`, `x_pick_roads__mutmut_90`,
  `x_pick_roads__mutmut_91` (`widths.get(key, None)`, `widths.get(key)`,
  `widths.get(key, 1.0)`): `_road_pieces` sets `pieces[key]` and `widths[key]` together,
  so every picked key is in `widths` and the default is never read.
- `named_lines` `x_named_lines__mutmut_12`, `x_named_lines__mutmut_14` (`… or True`,
  `len(line) >= 1`): a line of one point or none then reaches `simplify`, which returns a
  line of under 3 points unchanged, so `len(kept) > 1` still drops it.
- `named_lines` `x_named_lines__mutmut_21` (`len(kept) >= 1`): only lines of two or more
  points reach `simplify`, which always keeps both ends, so `kept` never has one point.
- `track_projection` `x_track_projection__mutmut_31` (`raw[0][1] - route[0][0]`): the
  base projection is referenced on the first point, so `raw[0]` is exactly `(0.0, 0.0)`
  and `raw[0][1]` is `raw[0][0]`.

## Tests added

- `tests/unit/ink/test_wash_density.py` (new): the wash's density pinned per option
  (plain, flow, pits, wet), clipped to 0 to 1, zeros of the cover's shape for no cover, and
  a bleed at the blur floor bit for bit unbled.
- `tests/unit/ink/test_bloom.py`: float64 alpha at exactly 0.6 seats no bloom; a core that
  holds no wash lays no ridge.
- `tests/unit/maps/lettering/test_picks_roads.py`: `TestPickRoads` (label fields, medium
  roads, every fourth track point, exactly 40 px, exactly `road_min_px`, a skipped road
  does not stop the picker, the longest piece, the score, no name and no number) and four
  `TestNamedRoads` tests (label fields and widest width, a name on several roads, a short
  road with its exact log line, a one-point road).
- `tests/unit/maps/lettering/test_named_lines.py` (new; split out of `test_picks_roads.py`,
  which the four classes took past the 400-line budget): the numbered entry, an unnamed
  unnumbered road, a river's empty `r`, the tolerance's scale and floor.
- `tests/unit/maps/lettering/test_ground.py`: the annotations' places reach the ground.
- `tests/unit/maps/painter/test_job.py`: the `Blooms` record, the bloom seed, three no-bloom
  cases, the count's floor and cap.
- `tests/unit/maps/test_projection.py`: `TestTrackProjection` (the record's reference and
  mean latitude, unequal lengths raise, an empty route, a given route).

## Commands

`ink` (main worktree, committed config):

```bash
uv run python tests/mutation/scope.py --base origin/main --out "$patterns"
python3 "$scratch/normalise.py" "$patterns"     # the rule: bloom and wash only
prlimit --as=3500000000 -- uv run mutmut run --max-children 2 \
  "pyntpot.ink.washing.x_wash*" "pyntpot.ink.bloom.x_bloom__mutmut_*"
uv run mutmut results | grep -v 'not checked'
xargs -a "$survivors" prlimit --as=3500000000 -- uv run mutmut run --max-children 2
```

`maps` (throwaway worktree, never committed):

```bash
git worktree add --detach "$scratch/mut-maps" HEAD
# pyproject.toml there only: only_mutate = the five files of plan.md S10;
# pytest_add_cli_args_test_selection = test_picks_roads.py, test_picks.py,
# test_named_lines.py, test_ground.py, painter/test_job.py, test_projection.py,
# tests/property/test_projection.py, -m "not golden"
prlimit --as=3500000000 -- uv run mutmut run --max-children 2 \
  "pyntpot.maps.lettering.picks_roads.x_named_roads*" \
  "pyntpot.maps.lettering.picks_roads.x__road_pieces*" \
  "pyntpot.maps.lettering.picks_roads.x_pick_roads*" \
  "pyntpot.maps.lettering.picks_lines.x_named_lines*" \
  "pyntpot.maps.lettering.pipeline.x__ground*" \
  "pyntpot.maps.projection.x_track_projection*" \
  "pyntpot.maps.painter.job.xǁPaintJobǁbloom*"
git worktree remove --force "$scratch/mut-maps"   # then recreated from the new HEAD
xargs -a "$survivors" prlimit --as=3500000000 -- uv run mutmut run --max-children 3
```

Wall time: 7 to 8 minutes a full round, under 30 minutes across all rounds.
