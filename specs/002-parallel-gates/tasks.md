# 002 — tasks

- [x] Measure the serial baseline: local fast, local golden, CI `checks`, CI golden (spec).
- [x] Profile one Lynmouth paint; record the hot paths in `specs/003-painter-hot-paths/spec.md`.
- [ ] Plan passes the plan-reviewer gate.
- [ ] Comment on #81 with the branch name.
- [ ] `pytest-xdist` in the dev group, `uv lock`, `--dist loadgroup` in `addopts`.
- [ ] `xdist_group` marks on the six module-paint golden modules.
- [ ] Local checks from the plan's test plan: fast `-n auto` under three seeds, coverage
      gates, golden exact `-n auto` with peak memory, grouped modules on one worker each,
      benchmark smoke, mutmut clean run, prek.
- [ ] `ci.yml` (`checks -n auto`, prerelease install) and `golden.yml` (`-n auto`, macOS
      workers per the memory measurement).
- [ ] `CONTRIBUTING.md`, `CLAUDE.md`, `docs/features/tests-fast-gates.md`.
- [ ] Fresh-context diff review against the plan; triage.
- [ ] PR (title `ci(tests): run the test and golden gates in parallel`), CI green on both
      runners, times recorded in the PR body.
