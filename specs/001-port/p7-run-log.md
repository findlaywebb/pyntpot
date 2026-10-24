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

## P7.1 landed on `p7-golden`, PR #27 held (2026-10-24)

Commits `20dab4c` (fix A), `af44f73` (fix B), `3902526` (regeneration, ADR 0031, the
flat-box issue). Steps against the previous step, manifest hash
`340a7f6e260ee1e2-e5a5f1b4b3ca2177` throughout: step 1 paper, wash, pen identical,
labels-centreline 0.058434, map 0.016597, labels equal; step 2 identical on those three,
labels-centreline 0.015885, map 0.002907, `labels.txt` diff exactly `< East Lyn`; step 3
all identical. Cumulative against the old goldens: labels-centreline 0.067173, map
0.017122. Three tests added in `test_placement.py` (now 389 lines); `placement.py` 380
lines. Deviations: the red tests were written against the new signature, so they were
red by import or `TypeError` before the fix and by `2 == 1` for fix B, not by the 65.0
against 85.0 figures; two golden-comparing tests in the non-golden suite are red between
commits 1 and 3, as in ADR 0025's window; `make_golden` dropped `plates.json`'s trailing
newline and the committed file was restored. The new card was looked at: one "East Lyn"
along the water, "B3234" flat beside Lynton. `p7-golden` merged into `p7-docs-release`;
the resolved issue file deleted here.

## P7.2 landed (2026-10-24)

Commit cherry-picked from its worktree, no conflict with P7.1. CONTRIBUTING gains
"Writing docs" and the Welsh-named, focus-first place list (Dee and Severn kept English,
with the reason); CLAUDE.md's place line; README's "Develop" section becomes a pointer;
`docs/README.md` points to `docs/index.md` in plain text. Six test files take the Welsh
names; Trefynwy and Machynlleth keep the old lengths and no pin moved. The dash-gate
command could not be written into CONTRIBUTING (it matches its own dashes), so it is a
prose instruction there. G-here green in the worktree (1119 passed, 1 skipped; golden 22
passed under tolerance).

## P7.3 budget re-based (2026-10-24, orchestrating session)

P7.3 stopped at its budget: Keswick's payloads are 6.6 MB raw (overpass 2.8 MB, land
cover 3.8 MB) against 4 MB. The raw budget measured the wrong thing. Git stores blobs
zlib-compressed and `tests/` is in neither the sdist nor the wheel, so what a fixture
costs the repo is its compressed size: Lynmouth's payloads gzip to about 0.56 MB (raw
3.6 MB) and Keswick's to about 1.05 MB (raw 6.6 MB). The orchestrating session re-based
the budget on gzip-compressed size: 1.5 MB per fixture, 2.5 MB for `yr-wyddfa/`, still a
stop when passed, with raw and compressed sizes recorded per fixture. Payloads stay
byte-for-byte as recorded. For the maintainer to confirm or overrule in the morning;
overruling means trimming the fetch margins, a change to the cache key and so a code
decision, not a fixture one.
