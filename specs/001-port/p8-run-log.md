# P8 run log

Orchestrating session's log for P8 (migrate the upstream training-analysis repo onto
`pyntpot` v0.0.1). Plan branch `p8-plan`, cut from `p10-fixes` at `75e2000` ("Record the
v0.0.1 tag"). All P8 code changes land upstream; this repo carries only the plan, this
log and the hand-off. No personal detail (activity ids, dates or names of sessions,
routes, athlete data) is recorded here; the reference activity is named "the reference
activity" and identified upstream only.

- 2026-10-09. Start. Read plan.md "### P8", the P10 hand-off bullet, "### P3 and P4: how
  to run a slice"; `p10-run-log.md` (tail), `p11-run-log.md`, ADRs 0007 and 0026 (via a
  digest agent). Tag `v0.0.1` present; `p10-fixes` pushed with "Record the v0.0.1 tag".
- Upstream at `e62657f` (clean). Map code is `analysis/report/` (geo, paint, labels,
  mapcard, outlinefont, style, charts), about 21.5k lines; tests `tests/test_paint.py`,
  `test_geo.py`, `test_report.py`. No CI, no type gate, `requires-python >=3.12`.
- Reference render, old code at upstream `e62657f`: first attempt blocked, no hash.
  `geo fetch` failed with "every Overpass mirror refused the query" (`geo.py:1439`); the
  main instance reset the connection through the proxy, mirrors returned 500 and 504. The
  elevation source returned 200. Old code has no attribution text or flag (static grep,
  `__main__.py:361-373`). Retrying; no upstream edit until a hash is recorded.
- P8 fattened (`23803fb`, plan +861 lines, `tasks.md` one line per slice). Slices: P8.1
  (Python 3.13, dependency), P8.2 (reference-hash test), P8.Q (maintainer stop for the hash
  and gap rows); group 1 P8.3a, P8.3b, P8.6; group 2 P8.4, P8.5a, P8.5b; P8.7 (delete the
  engine), phase gate, P8.H (hand-off); P8.8 conditional. Writer foresees three `decide`
  gap rows (candidate export, vector basemap, route ink by sport) and expects the hash to
  miss (ADR 0006 step 3 moved `map.png`). The reference must be rendered with `--sport
  Ride`; the retry agent was told. Plan-reviewer round 1 started.
- Reference render recorded, old code at upstream `e62657f`, clean tree, no code or env
  change; the fetch succeeded on spaced retries (main Overpass instance still resets TLS;
  a mirror answered once its 500s cleared). 1800x1529 PNG, sha256 with `--sport Ride` (the
  comparable reference) `745936193e2b6a7af4d43063424974311234200f07ab441328c5de224b9475a7`;
  default sport `89a9a24dd86a323c60e00746e652f7ee161f5242ab7730f622a4d9ebe9e5facb`.
  Deterministic: Ride render repeated after deleting the plates, same PNG and plates.
  Detail (commands, cache hashes, versions) kept upstream in git-ignored
  `data/p8-reference/reference.md`. Upstream's own retry is 3 rounds of 4 s
  (`geo.py:1425-1436`); short for a busy mirror, not a P8 matter.
