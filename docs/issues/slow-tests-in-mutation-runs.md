# Slow end-to-end tests dominate mutation run time

mutmut runs, for each mutant, every test that covers the mutated function.
A few whole-pipeline unit tests reach deep into `ink`, so mutants in small
helpers pay for a full map render. The slowest found so far is
`tests/unit/maps/test_cli.py::TestMap::test_a_full_cache_makes_no_request`
at 72 s; it reaches most of `ink.polyline`.

Evidence (P5.3a, recorded in `specs/001-port/p5-run-log.md` and ADR 0012):
one changed line in `simplify` gave 72 mutants and took 26 minutes, and the
measured cost was about 5 s per mutant in `ink` and `letters` and 7 s in
`maps`, so a full run over `ink` and `letters` is about 12 hours of runner
time. That cost is why mutation testing is manual and advisory.

Possible fix: keep end-to-end tests out of mutation runs, so each mutant is
judged by the unit and property tests written for it. Either mark the slow
pipeline tests (for example `@pytest.mark.pipeline`) and add
`-m "not golden and not pipeline"` to `pytest_add_cli_args_test_selection`
in `[tool.mutmut]`, or narrow that selection to the test directories that
mirror the mutated packages. Then re-measure seconds per mutant on the same
samples and record the result in ADR 0012. Mutants that only a pipeline test
killed will show as survivors; that is the point, since they mark code the
focused tests do not check.
