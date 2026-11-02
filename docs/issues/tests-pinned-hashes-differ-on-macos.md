# Three pinned-hash tests fail on macOS arm64

GitHub issue: [#86](https://github.com/findlaywebb/pyntpot/issues/86)

Area: tests (`ink`, `maps`).

On macOS 26.6 (arm64, Python 3.13.6, numpy 2.5.2), `uv run pytest -m "not golden"` fails three
tests that compare a plate's sha256 with a pinned literal. CI on `ubuntu-latest` passes them,
and they fail the same way on a clean checkout of `main` at `51aae1f`.

- `tests/unit/ink/test_paper.py::TestClassicEdge::test_the_classic_plate_is_the_pinned_one`
  fails with and without `--golden-tolerance`.
- `tests/unit/maps/painter/test_smoke.py::test_the_flags_off_still_paint_the_plates_that_were_approved`
  and `::test_the_wash_flags_off_still_paint_the_plates_that_were_approved` fail exact (the
  `wash` hash differs, `paper` too in the first) and pass with `--golden-tolerance`.

So the local gate in `CLAUDE.md` is red on a Mac before any change is made, and a
contributor cannot tell these failures from their own.
