# Performance

These are measurements, not targets. pyntpot measures speed and does not optimise it
yet: a number here says where the time goes today, and nothing promises it stays or
must fall.

## What is benchmarked

Benchmarks live in `tests/benchmarks`. Each times one callable on inputs built outside
the timer from seeded generators, and asserts nothing. A plain `pytest` run calls each
once, untimed, as a smoke test (`--benchmark-disable` is in `addopts`).

- `test_ink.py`: the engine at 512 by 512. The sheet's noise fields, the chamfer
  distance, stamping a brush along a 2000 point path (a dry track and a wet river
  brush, and the starved directional brush), one pigment's wash (plain, and inside a
  wet area), and compositing four washes by multiply and by Kubelka-Munk glazing.
  These are the loops every painted plate runs.
- `test_letters.py`: the hand writing a long name along a line, and a two-row block
  from an anchor, each warm; and a fresh hand tracing every glyph from the face by
  the centreline and the outline route. Cold and warm are kept apart because tracing
  is paid once per glyph.
- `test_maps.py`: one benchmark per pipeline stage over the offline Lynmouth fixture
  (`fetch`, `paint`, `letter`, `compose`), so a slowdown names its stage. `paint`
  writes into a fresh directory each round, because `paint` skips work when the
  directory already holds current plates.

Every maps benchmark paints at `DISPLAY_PX = 450` (a module constant in
`test_maps.py`), below the default card of 900, to keep the smoke run under its
60 second budget. 450 was the first size of the ladder 450, 300, 200 and fit, so the
ladder went no further.

## Local baselines

`uv run pytest -m benchmark --benchmark-enable`, on commit `e50c7f9` plus this change,
2026-10-07, Python 3.13.16, numpy 2.5.2, Intel Xeon Processor @ 2.80GHz (4 cores,
otherwise idle). "Smoke" is the untimed call, from `--durations`, without fixture
setup. The module fixtures (the basemap, the painted plates, the lettering) cost about
6.4 s once and are charged to the first test that uses them.

| Benchmark | Source | Median (ms) | Rounds | Smoke (s) |
| --- | --- | --- | --- | --- |
| `test_ink.py::test_stamp_a_2000_point_path` | plan | 16.44 | 60 | 0.02 |
| `test_ink.py::test_building_a_sheet` | PR #6 | 78.27 | 13 | 0.08 |
| `test_ink.py::test_the_distance_transform` | PR #6 | 15.32 | 51 | 0.02 |
| `test_ink.py::test_stamping_a_long_stroke[dry-track]` | PR #6 | 11.97 | 81 | 0.01 |
| `test_ink.py::test_stamping_a_long_stroke[wet-river]` | PR #6 | 15.08 | 65 | 0.02 |
| `test_ink.py::test_stamping_a_starved_directional_brush` | PR #6 | 33.07 | 29 | 0.04 |
| `test_ink.py::test_laying_a_wash` | PR #6 | 41.32 | 23 | 0.05 |
| `test_ink.py::test_laying_a_wet_wash` | PR #6 | 61.98 | 19 | 0.06 |
| `test_ink.py::test_compositing_a_stack[multiply]` | PR #6 | 13.48 | 45 | 0.19 |
| `test_ink.py::test_compositing_a_stack[kubelka-munk]` | PR #6 | 69.48 | 15 | 0.30 |
| `test_letters.py::test_writing_a_name_with_a_fresh_hand[centreline]` | PR #6 | 11.22 | 93 | 0.01 |
| `test_letters.py::test_writing_a_name_with_a_fresh_hand[outline]` | PR #6 | 5.74 | 84 | 0.01 |
| `test_letters.py::test_writing_a_name_along_a_line` | PR #6 | 11.76 | 89 | 0.01 |
| `test_letters.py::test_writing_a_flat_block` | PR #6 | 7.76 | 136 | 0.01 |
| `test_maps.py::test_fetch` (stage fetch) | PR #6 | 381.00 | 5 | 0.37 |
| `test_maps.py::test_paint` (stage paint) | plan, PR #6 | 5251.30 | 5 | 5.00 |
| `test_maps.py::test_letter` (stage letter) | PR #6 | 174.89 | 5 | 2.55 |
| `test_maps.py::test_compose` (stage compose) | plan, PR #6 | 580.06 | 5 | 0.72 |

The three plan benchmarks `test_sheet_construction`, `test_edt` and `test_wash` were removed
on 2026-10-07 as duplicates of the PR #6 ones, which ends their CodSpeed history.

The smoke run, `uv run pytest -m benchmark`, takes about 19 s wall in total at
`DISPLAY_PX = 450` (18.7 to 20.2 s over three runs on 2026-10-08, re-measured after the
three duplicates were removed; 17.8 s before).

## CodSpeed

CI times the same benchmarks with CodSpeed in simulation mode (`--codspeed`). That
mode counts instructions, so its numbers are not wall time and do not compare with the
medians above. The dashboard is `https://codspeed.io/findlaywebb/pyntpot`.
