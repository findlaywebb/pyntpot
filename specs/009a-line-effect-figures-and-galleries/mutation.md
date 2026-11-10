# Mutation testing: spec 009a (G)

Scope: `uv run python tests/mutation/scope.py --base origin/claude/quirky-hypatia-z2pii3 --out "$patterns"`,
run with `mutmut run` under `prlimit --as=3500000000`. One changed `ink` function:
`pyntpot.ink.pigment_table.role_transparencies` (its docstring and the module's no longer name
`PaperStyle.pigment_transparency`). One mutant. As the plan expected, `maps` is outside
`only_mutate`, so the maps changes are not in scope; they are covered by exact-value tests.

- **Harness.** The pytest-9 workaround of `specs/009-line-effects-and-registry/mutation.md`
  (issue #207): a `sitecustomize.py` outside the repo aliasing `Node._nodeid`; nothing in the repo
  changed. A stale `mutants/` cache from an earlier run was removed first.

## Result

| | mutants |
| --- | --- |
| Total | 1 |
| Killed by the existing suite | 0 |
| Survived the existing suite | 1 |
| Killed by a new test | 1 |
| Equivalent | 0 |

The survivor, `role_transparencies` 1 (`_transparencies(None)` for `_transparencies(ROLE_PIGMENTS)`),
survived because `TRANSPARENCY` is built at import, before any mutant is active, so only a direct
call reaches it (as `_entry` did in 009). Killed by
`tests/unit/ink/test_pigment_entry.py::test_role_transparencies_is_a_fresh_copy_of_the_role_table`.
No survivor revealed a bug in `src`.

## Casing follow-up: `nib_cover`

PR 2's one `ink` change is `pyntpot.ink.deposit.nib_cover`: its splat reads the sample positions
as float64 (`pos[0][:n].astype(np.float64)`), a line the T0 merge commit `0e04f8cb` carries.
Scope: the one pattern `pyntpot.ink.deposit.x_nib_cover*`. Against PR 1's tip before its diff
review (`scope.py --base 15466d99~1`) the scope also lists `contour_distance`, `pool_band` and
`role_transparencies`, which PR 1 and 009a mutation-tested; only `nib_cover` is PR 2's. Run with `mutmut run --max-children 2`
under `prlimit --as=3500000000`, the same out-of-repo `sitecustomize.py`, and a fresh `mutants/`.

| | mutants |
| --- | --- |
| Total | 155 |
| Killed by the existing suite | 139 |
| Survived the existing suite | 16 |
| Killed by new tests | 11 |
| Equivalent | 5 |

No survivor revealed a bug in `src`.

### Killed (new tests, `tests/unit/ink/test_nib_cover_exact.py`)

- The reach from the start to the window's far side: `nib_cover` 4, 6 (the start read from the
  second stamp), 16, 18, 24, 26 (the `+ 1` of either axis changed), by
  `test_the_reach_is_measured_from_the_start_to_the_window_s_far_side`, which counts the stamps
  read with every sample put on one pixel.
- 35 (`searchsorted` side `left`): a stamp exactly at the reach plus the tip is counted, by
  `test_a_stamp_exactly_at_the_reach_is_counted`.
- 54 (`max(..., 2)`): a stroke of two stamps, by
  `test_a_stroke_of_two_stamps_stands_for_its_whole_length`.
- 72, 76 (`<=` for `<` at `x1` and `y1`): a sample on the window's far edge is kept by the mutant,
  and its far corner falls past the splat's grid, by `test_a_sample_on_the_far_edge_lays_nothing`.
- 144 (`astype(None)` on the result): by `test_the_cover_is_float32`.

The float64 read itself had no test: removing it left the whole `ink`, `letters` and property
suite green. `test_float32_and_float64_positions_give_the_same_cover_bit_for_bit` fails without
it (positions near 2800 px differ by up to 6e-8 in the cover) and passes with it.

### Equivalent

- 42, 44: `astype(None)` for `astype(np.float64)` on the positions; `None` is float64.
- 69, 73: `>=` for `>` at `x0 - 1` and `y0 - 1`. A sample exactly there has a zero fraction, so
  its whole weight lands on the margin column or row, which the result crops.
- 143: `reshape(-2, wide)`; numpy reads any negative size as the one inferred.
