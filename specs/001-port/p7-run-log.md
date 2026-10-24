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

## P7.11 landed (2026-10-24)

ADRs 0013 to 0021 by a slice agent in a worktree (commit cherry-picked). Pointers: 0013
(to 0002, 0010), 0016 (to 0004, adds the attribution switch), 0017 (to 0004), 0019 (to
0007, 0026, 0027), 0020 (to 0005). Full: 0014, 0015, 0018, 0021. `docs/decisions/README.md`
gains an index of 0001 to 0030. G-here green in the worktree. Noticed: ADR 0007's stale
`_port` sentence, filed as `docs/issues/docs-adr-0007-stale-port-wording.md`. The ADR
titles keep the house "—" in their headings; `docs/decisions` is outside the dash gate.

## P7.12 landed (2026-10-24)

`ci.yml` gains `workflow_dispatch` and a `docs` job (lychee `v2.9.0` offline, `uv build`,
`twine check --strict`); weekly advisory `links.yml`; `lychee.toml`; twine 7.0.0 in
`dev`. Local: lychee 0.24.2 parses the config (every current README and docs link is
remote, so offline excludes all 42); a scratch file with a broken relative link is
reported as an error, so the offline check does catch broken local links. `twine check
--strict` passes on the wheel and sdist. G-here green. `include_fragments` left out
(lychee 0.24.2 rejects the value). Open: the done line's green run on GitHub;
`workflow_dispatch` only dispatches from the default branch, so it is met by the draft
PR's run instead.
