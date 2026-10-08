# Slow end-to-end tests dominate mutation run time

mutmut runs, for each mutant, every test that covers the mutated function.
A few whole-pipeline unit tests reach deep into `ink`, so mutants in small
helpers pay for a full map render.

Evidence (P5.3a, recorded in `specs/001-port/p5-run-log.md` and ADR 0012):
one changed line in `simplify` gave 72 mutants and took 26 minutes, and the
measured cost was about 5 s per mutant in `ink` and `letters` and 7 s in
`maps`, so a full run over `ink` and `letters` is about 12 hours of runner
time. That cost is why mutation testing is manual and advisory.

The slowest test found, `tests/unit/maps/test_cli.py::TestMap::test_a_full_cache_makes_no_request`
(72 s), is now marked `@pytest.mark.golden`, so the mutation selection
(`-m "not golden"`) skips it; a fast `--style` test of `pyntpot.maps.cli.main`
over a 120-pixel copy of the default theme keeps the `maps` coverage.

Open: the wider selection. Possible fix: narrow
`pytest_add_cli_args_test_selection` in `[tool.mutmut]` to the test directories
that mirror the mutated packages, or mark other slow pipeline tests, then
re-measure seconds per mutant on the same samples and record the result in
ADR 0012. Mutants that only a pipeline test killed will show as survivors; that
is the point, since they mark code the focused tests do not check.
