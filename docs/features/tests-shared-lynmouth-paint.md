# The golden run could paint Lynmouth once

GitHub issue: [#90](https://github.com/findlaywebb/pyntpot/issues/90)

**What exists today.** Six golden-marked modules each paint the whole Lynmouth fixture in a
module-scoped fixture: `tests/golden/test_parity.py`, and in `tests/unit/maps/`
`test_attribution.py`, `test_pipeline_letter_compose.py`, `lettering/test_notes.py`,
`test_route_ink.py` and `test_pipeline_fetch_paint.py`. `test_cli.py` and
`tests/examples/test_route_map_example.py` paint it again per test. A serial golden run on
2026-10-27 spent about seven minutes on these paints, most of them the same default-style
map. Under xdist each module is a group, so each paints once (`specs/002-parallel-gates/`),
but the paints still repeat across modules.

**What the feature would add.** One paint of the default-style Lynmouth map, shared by the
modules that read the same plates, so a golden run pays for it once.

**Why it is not a defect.** Every module gets the right answer; the cost is repetition.

**Possible shape.** The house rules allow a module-scoped fixture for an immutable object
and nothing wider, so a shared paint needs either a decision to allow a session-scoped,
read-only paint (an ADR: what is shared, and that no test may write to it) or the modules
merged where they read the same plates. Under xdist a session fixture is per worker, so
the modules would also share one `xdist_group`. Related: #82 asks whether the tests should
move off Lynmouth at all.
