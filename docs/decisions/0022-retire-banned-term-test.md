# 0022 — Retire the banned-term test

Status: accepted

Supersedes the enforcement clause of D16 for the post-port tree. Amends ADR 0002's list
of scans.

## Context

D16 asked for a banned-term test, a manual pass and a history scan while the port carried
upstream data. The term list lived outside the repository, so public CI always skipped the
test, and only the maintainer's machine ran it. The port is published, and the maintainer
decided on 2026-10-04 to retire the test once it was.

Its last run, on 2026-10-26, failed only on names in the focus-place fixtures and their
docs, which are OpenStreetMap data, and on wording in `specs/001-port/`. The maintainer
accepted the fixture names and had the specs reworded.

## Decision

- Delete `tests/architecture/test_no_personal_content.py` and the `personal_terms_file`
  pytest option.
- D16's rule is unchanged: tests, examples and docs use public data only.
- The D10 coordinate allowlist (`tests/architecture/test_coordinates.py`) stays as the
  standing automated check.

## Consequences

- A contribution is not scanned for terms; review against D16 and the coordinate test
  cover it.
- The architecture tests no longer report a skip.
- ADR 0002's list of scans names the banned-term scan; from this ADR on, that scan no
  longer runs.
