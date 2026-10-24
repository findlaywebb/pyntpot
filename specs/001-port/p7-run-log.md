# P7 run log

One dated entry per slice, appended. Plan: `plan.md`, "P7. Docs and first release".

## 2026-10-23 to 24, overnight run (orchestrating session)

The maintainer asked for as much of P7 as can be done overnight, to be assessed in the
morning. Deviations from the plan's order, decided by the orchestrating session:

- PR 1 (`p7-golden`, P7.1) cannot be merged overnight, so `p7-docs-release` takes
  `p7-golden` in by a merge commit instead of `main` after PR 1 merges. When PR 1
  merges, `main` is merged into `p7-docs-release` as the plan says; the result is the
  same tree.
- P7.1's bookkeeping (this log, the `tasks.md` tick, deleting the resolved issue file)
  is done on `p7-docs-release`, where those files live, not on `p7-golden`.
- P7.2, P7.3, P7.11 and P7.12 run in parallel detached worktrees. Their owner files are
  disjoint: P7.3 touches neither `pyproject.toml`, `uv.lock` nor `ci.yml` (the reason
  the plan ran P7.11 and P7.12 first), and P7.2's one overlap with P7.1
  (`test_placement.py:53`) is resolved at the merge.
- Slices do not write this log or `tasks.md`; the orchestrating session appends their
  entries at landing.
- The providers' contact string for recording is the repo URL, not a personal address.
