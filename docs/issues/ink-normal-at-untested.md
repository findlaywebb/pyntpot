# `polyline.normal_at` has no focused test

GitHub issue: [#108](https://github.com/findlaywebb/pyntpot/issues/108)

Area: ink (tests).

`pyntpot.ink.polyline.normal_at` returns the unit left normal at a point, differencing
its neighbours and falling back to (0, 1) on a degenerate run. Its only caller is
`pyntpot.maps.rivers`, and no test in `tests/unit/ink`, `tests/unit/letters` or
`tests/property` reaches it. The `maps` tests that once covered it are outside the
mutation test selection (ADR 0012, 2026-11-02), so a mutation run on it scores all 37 of
its mutants `no tests` (measured 2026-11-02 with a one-line change to the function).

Fix: a focused test class in `tests/unit/ink/test_polyline.py` that pins the normal on a
straight run, at both ends (the clamped neighbours), and the (0, 1) fallback on repeated
points; then a mutation run on `pyntpot.ink.polyline.x_normal_at*` to kill or name each
survivor.
