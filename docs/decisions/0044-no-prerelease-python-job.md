# 0044 — No pre-release Python job (amends D4)

Status: accepted

## Context

D4 (`specs/001-port/spec.md`) set the Python floor at 3.13, the CI matrix at 3.13 and 3.14,
and added a 3.15 pre-release job allowed to fail. That job installed its test plugins
unpinned, to catch breakage from the newest releases early.

From 2026-10-27 it failed on every run, on `main` too, for a reason outside pyntpot: the
newest pytest dropped the private `Node._nodeid`, which pytest-benchmark reads, so every
benchmark errored in set-up while every test passed (#94). Being allowed to fail, it blocked
nothing, but it showed red on every pull request and each one needed a note saying why.

## Decision

Maintainer decision, 2026-11-02: the `prerelease` job is removed from `.github/workflows/ci.yml`.
CI runs the supported versions only, 3.13 and 3.14. Python 3.15 support is added once 3.15 is
released, by adding it to the `checks` matrix and fixing whatever it needs then. The floor
and the matrix of D4 are otherwise unchanged.

## Consequences

- A breaking change in a Python or plugin pre-release is found when 3.15 is added, not
  before it.
- Pull requests no longer carry a red check that is not theirs.
- #94 is closed as not planned, with its note `docs/issues/tests-prerelease-pytest-benchmark.md`.
