# Performance

These are measurements, not targets: a number here says where the time goes today, and
nothing promises it stays or must fall. The painter was profiled and made faster once,
without moving a pixel (`specs/003-painter-hot-paths/`), and the test gates run in
parallel (`specs/002-parallel-gates/`); both are recorded below.

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

`uv run pytest -m benchmark --benchmark-enable`, medians in milliseconds, on `main` at
`5904c44` and on the change that made the painter faster, 2026-10-27, Python 3.13.17, numpy
2.5.2, an Intel Xeon with AVX-512 (4 cores, otherwise idle). The lettering benchmarks run
no code that change touched: their spread between runs (about 30 %) is noise, and their
instruction counts did not move.

| Benchmark | Before (ms) | After (ms) | Rounds after |
| --- | --- | --- | --- |
| `test_ink.py::test_stamp_a_2000_point_path` | 17.19 | 11.58 | 61 |
| `test_ink.py::test_building_a_sheet` | 137.39 | 46.50 | 25 |
| `test_ink.py::test_the_distance_transform` | 12.13 | 11.02 | 60 |
| `test_ink.py::test_stamping_a_long_stroke[dry-track]` | 12.56 | 10.06 | 91 |
| `test_ink.py::test_stamping_a_long_stroke[wet-river]` | 15.09 | 12.57 | 80 |
| `test_ink.py::test_stamping_a_starved_directional_brush` | 28.60 | 16.75 | 53 |
| `test_ink.py::test_laying_a_wash` | 47.01 | 41.15 | 20 |
| `test_ink.py::test_laying_a_wet_wash` | 75.08 | 72.62 | 18 |
| `test_ink.py::test_compositing_a_stack[multiply]` | 12.59 | 10.76 | 76 |
| `test_ink.py::test_compositing_a_stack[kubelka-munk]` | 66.17 | 27.69 | 34 |
| `test_letters.py::test_writing_a_name_with_a_fresh_hand[centreline]` | 4.52 | 3.77 | 12 |
| `test_letters.py::test_writing_a_name_with_a_fresh_hand[outline]` | 4.50 | 4.10 | 144 |
| `test_letters.py::test_writing_a_name_along_a_line` | 4.22 | 4.76 | 191 |
| `test_letters.py::test_writing_a_flat_block` | 3.29 | 3.12 | 273 |
| `test_maps.py::test_fetch` (stage fetch) | 260.17 | 242.72 | 5 |
| `test_maps.py::test_paint` (stage paint) | 4597.70 | 2573.23 | 5 |
| `test_maps.py::test_letter` (stage letter) | 109.35 | 86.88 | 5 |
| `test_maps.py::test_compose` (stage compose) | 371.82 | 338.96 | 5 |

The smoke run, `uv run pytest -m benchmark`, took 61 s before and 42 s after, wall, at
`DISPLAY_PX = 450`.

## A full map paint

The same machine, one process each, wall time and peak resident memory:

| Paint | Before | After |
| --- | --- | --- |
| Lynmouth, default style (`tests/support/golden.py::paint_fixture`) | 55.9 s, 1688 MB | 22.3 s, 926 MB |
| Skye card, its theme (`tests/golden/test_places.py`) | 102.0 s, 1981 MB | 59.1 s, 1153 MB |

Before, `cProfile` put the Lynmouth paint's time in `ink_density` (10.7 s over 8 calls,
nearly all of it on ink pad pixels that held no ink: 2.5 % were laid), the box blur's
strided `cumsum` (8.8 s), lossless WebP encoding (4.3 s), Kubelka-Munk glazing over
unpainted pixels (3.7 s), value noise (3.3 s) and per-edge ring filling (2.7 s). The
change works out ink and glaze only where they were laid, sums large planes by contiguous
row adds, interpolates noise once per lattice row, fills a ring's edges in one pass,
deposits through flat indices, grows the paper to the ink grid once per grid, and writes
opaque lossless plates at a lower encoder effort (ADR 0043). Every pixel is the same,
bit for bit, as is every random draw. After, no single function costs more than 1.5 s:
the largest are Pillow's resizes, `wash` itself and the label plate's nib.

The golden suite, `uv run pytest -m golden --golden-tolerance -n auto --dist loadgroup` on
this machine: 9 min 15 s before, 3 min 34 s after. The exact run (the local gate) took
4 min 40 s after.

## The gates on CI

Job wall time on GitHub's runners, serial on `main` at `8b5253e` and with xdist after
`specs/002-parallel-gates/` (#89):

| Job | Serial | Parallel |
| --- | --- | --- |
| `checks` (3.13) | 3 min 9 s | 1 min 56 s |
| `checks` (3.14) | 2 min 43 s | 1 min 39 s |
| `golden` (ubuntu-latest, 4 workers) | 19 min 38 s | 8 min 5 s |
| `golden` (macos-15, 2 workers) | 25 min 15 s | 16 min 34 s |

After the painter change (`specs/003-painter-hot-paths/`, #93), on the same runners:

| Job | Parallel, before the painter change | After it |
| --- | --- | --- |
| `checks` (3.13) | 1 min 56 s | 1 min 46 s |
| `checks` (3.14) | 1 min 39 s | 59 s |
| `golden` (ubuntu-latest, 4 workers) | 8 min 5 s | 3 min 10 s |
| `golden` (macos-15, 2 workers) | 16 min 34 s | 6 min 27 s |

CodSpeed on #93: `paint` 41.1 s to 24.8 s (simulation), seven benchmarks faster and none
slower.

A golden worker peaked near 3 GB before the painter change, so the macOS runner (3 cores,
7 GB) runs two workers; #91 asks whether three now fit.

## CodSpeed

CI times the same benchmarks with CodSpeed in simulation mode (`--codspeed`). That
mode counts instructions, so its numbers are not wall time and do not compare with the
medians above. The dashboard is `https://codspeed.io/findlaywebb/pyntpot`.

The three plan benchmarks `test_sheet_construction`, `test_edt` and `test_wash` were removed
on 2026-10-07 as duplicates of the PR #6 ones, which ends their CodSpeed history; the
dashboard lists them as skipped until they are archived there.
