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
- Plan-reviewer round 1: BLOCK, seven findings (hash gates unreachable at v0.0.1; page
  track source vs `paint` cache key; `drawn` over a bare track; `paint --display` changing
  the base digest; unnamed offline test factory; `geo candidates` under G1 (b); four wrong
  check-first counts). Upstream facts sampled otherwise correct; no personal detail in the
  diff. Reviewer rendered the reference inputs through v0.0.1's public API: sha256
  `0dfffcca...`, differing fraction 0.104 (paper identical, wash 0.105, pen 0.004).
  Treated as a reference-hash mismatch: an independent agent is verifying like-for-like
  inputs and the cause before the maintainer is asked. Plan fixes held until then.
- Hash mismatch verified (independent agent, fresh venv, v0.0.1 from git): like-for-like
  inputs (same payloads, GPX track, port-default style, ride ink, no landmark picks,
  `attribution=False`); sha256 `0dfffccab9be726492f14f9ded582ed385ec81838e8ba120dcf20bb9cde26619`.
  Bisected: `020c3ff` and `3e49f61` render the old reference exactly; `637573c` (ADR 0006
  step 3: full-precision geometry, card pin removed) renders the v0.0.1 hash byte for byte,
  nothing later moves a pixel. Wash 0.105 is shared-generator amplification of sub-pixel
  moves (deferred `shared-generators`); pen 0.004 is the unrounded route. No public setting
  restores rounding; rounding the public `Basemap` to 0.1 m and re-applying the pin offset
  before `paint` reproduces `745936...a7` exactly. Run stopped for the maintainer.
- P8.Q (asked early, after the review measured the mismatch). Maintainer on the hash:
  "Accept ADR 0006, re-pin": the migrated render's reference is the v0.0.1 hash
  `0dfffcca...6619`; the old `745936...a7` stays recorded with the bisection as the
  explained difference. Shown old-vs-new comparisons first (wash granulation and edge
  tone differ; geometry matches). On the gaps: G1 "Explain more"; G2 "I think we just
  need a new promotion layer that it quickest to do now"; G3 "again - something to
  promote now".
- Maintainer on the comparison crops: "For the wash differences - this seems to be due to
  the random seeding. Stylistically they are the same". Matches the bisection: shared
  generators amplify the sub-pixel geometry moves (`shared-generators`, deferred).
- Maintainer: G1 "Yes, promote all three"; pin "Pin v0.0.2": one pyntpot promotion slice
  (G1 public `landmark_export` over a public `Basemap`, G2 a public vector-layer value, G3
  a route-ink sport selection), one ADR, its own branch and PR held for the maintainer's
  merge, then tag `v0.0.2`; P8 depends on `@v0.0.2`. Plan to be refixed (review round 1
  findings plus these answers) by a fresh agent and reviewed again.
- Maintainer on G3: "the pyntpot code should of course be generic - not sport map
  oriented. So it just needs methods to feed in the colour". G3 becomes a caller-supplied
  route ink (no sport concept in pyntpot; upstream keeps its own sport-to-colour table);
  the same generic test applies to G1 and G2. Plan agent told.
- Plan refixed by a fresh agent (`a9b1fb2`): promotion group P8.P1
  (ADR 0027), P8.P2a-c in parallel (G1 `candidate_export`, G2 `vector_layers` /
  `VectorLayers`, G3 `Style.with_route_ink(colour, width_px)`), P8.P3 (0.0.2, PR held,
  tag); gates pinned to `0dfffcca`; P8.Q recorded, P8.8 deleted; round-1 findings 1-7
  and the non-blocking items addressed. A fourth row foreseen,
  `maps-style-route-inks-name-sports` (defer). Plan-reviewer round 2 started.
- Maintainer's standing instructions for this run (2026-10-09), verbatim: "Stop and ask
  me: before merging any PR, in either repo; if the reference hash does not match." Also:
  "Any gap in pyntpot's public surface is filed in pyntpot's p10-triage.md, not patched
  around in upstream." And: "for pyntpot repo, no personal details should leak into it".
- Plan-reviewer round 2: BLOCK, two findings (`vector_layers` takes 9 args against ruff
  `max-args = 6`; ADR 0027 wording names "sport" twice). Round-1 findings fixed in
  substance; about 40 facts spot-checked; no personal detail; bare `dict` return judged
  acceptable. Thirteen non-blocking items. Fresh agent fixing; round 3 to follow.
- Round-2 fixes (`3431466`): `vector_layers(track, cache, key, style, places=(), *,
  origin=None)` (ruff-probed); ADR 0027 wording generic; 0027 row in the ADR table; all
  non-blocking items. Gap rows renamed: `upstream-card-route-ink-by-sport` is now
  `upstream-card-route-ink-fed`, `maps-style-route-inks-name-sports` is now
  `maps-style-route-inks-one-read`. Place-name check: the one landmark named in P8 is
  already in pyntpot's Lynmouth fixture, so kept. Plan-reviewer round 3 started.
- Plan-reviewer round 3: PASS at `3431466`. Round-2 findings fixed; must-holds checked
  (hash pins, promotion, generic wording, no personal detail with the architecture tests
  green at HEAD, disjoint owners, hand-off); about 35 fresh facts correct; the promotion's
  new names probed in a scratch worktree (ty, ruff, lint-imports, architecture tests
  green, `MAPS_PUBLIC` red as the intended red step). Five non-blocking items being folded
  in before P8.P1.
- Triage rows filed on `p10-fixes` (`b17a3f9`): `upstream-candidate-export-private` fix
  P8.P2a, `upstream-vector-basemap-private` fix P8.P2b, `upstream-card-route-ink-fed` fix
  P8.P2c, `maps-style-route-inks-one-read` defer.
- `p8-promote` cut from `main` at `90c2fd6`. P8.P1 landed (`d63bf2c`): ADR 0027, 108
  lines, wording grep empty. G-here green: format 329 files, ruff clean, prek all hooks,
  not-golden 1064 passed 1 skipped, golden 19 passed (tolerance and byte-exact). Deviation:
  the title's dash follows every existing ADR title. P8.P2a, P8.P2b, P8.P2c started in
  parallel worktrees from `d63bf2c`.
- P8.P2b landed (`870d31e`), first of the group, no rebase. Baseline `{"commit":
  "d63bf2ca031614ee878c3e4d09957dcef277ba3a", "dirty": false}`. Red: "ImportError: cannot
  import name 'VectorLayers' from 'pyntpot.maps'". G-here green: format 331, ruff clean,
  prek all hooks, not-golden 1074 passed 1 skipped, golden 19 (tolerance, byte-exact);
  G-self 19 byte-identical; coverage ink+letters 96.14 (gate 95), maps 93.98 (gate 92),
  `vector_layers.py` 286 lines at 100%. Check-first figures held. No deviation.
- P8.P2a landed (implementer at `c317f8b`, baseline `{"commit":
  "d63bf2ca031614ee878c3e4d09957dcef277ba3a", "dirty": false}`; red: `test_public_api`
  `[maps]` and "ImportError: cannot import name 'candidate_export'"). Rebased onto
  `870d31e` with conflicts in CHANGELOG, GLOSSARY, `maps/__init__.py`, `test_public_api.py`,
  resolved by a fresh agent by the merge rules (union; docstring paragraph as the rule
  gives it; `__all__` RUF022 order) as `11ddd60`. Gates on the rebased commit: format,
  ruff, prek (ty, import-linter, architecture) green; not-golden no failures (1059 passed,
  1 skipped in the coverage run); golden 19 (tolerance, byte-exact), G-self 19
  byte-identical; coverage ink+letters 96.14, maps 94.02.
- P8.P2c implementer done (`de5ec3b`): red 10 failed on "'Style' object has no attribute
  'with_route_ink'"; gates green, golden 21 (two new route-ink goldens), G-self
  byte-identical, coverage 96.14 / 93.29. Rebasing onto `11ddd60`: CHANGELOG and GLOSSARY
  conflicts, a fresh agent resolving.
- P8.P2c landed: rebased by a fresh agent onto `11ddd60` as `0cd5407` (CHANGELOG and
  GLOSSARY unioned in landing order). Gates on the rebased commit green: format, ruff,
  prek 9 hooks; not-golden 1068 run, 0 failed, 1 skipped; golden 21 (tolerance, exact),
  G-self 21 byte-identical; coverage ink+letters 96.14, maps 94.03.
- P8.P3 version commit started; in parallel a fresh-context review of the promotion diff
  `90c2fd6..0cd5407`.
- Promotion diff review (fresh context, `90c2fd6..0cd5407`): fix first. API matches ADR
  0027; default digest `25ae6fee082ebff5` unchanged; no sport wording; all gates green in
  a probe worktree. Findings: (1, blocking) `with_route_ink` admits `inf` and `True`, and
  `5` vs `5.0` or colour case move `digest()`; (2) docstring overclaims width for a pen
  ink; (3) `VectorLayers` not picklable or hashable, undocumented; (4) `places`,
  read-only, `picked` and elevation-only untested; (5) no compose width test. A fresh
  agent fixing all five as one commit before P8.P3. Out of scope, noted for P10:
  `maps/layers.py:109` still says "a run's map" (pre-existing wording).
- Review fixes landed (`ad47df0`, fresh agent; baseline `{"commit":
  "0cd540795d16485b1d2f3766fc5de4122b9b1fe6", "dirty": false}`; red 3 failed: equal fed
  values' digests, bool and infinite widths). Gates green, golden 22, G-self 22
  byte-identical, coverage 96.14 / 94.04, default digest `25ae6fee082ebff5`. Trade-off
  noted for P10: the places test keeps every place inside the Lynmouth box, so the
  out-of-box drop filter is untested.
- P8.P3 version commit rebased onto the fix as `8cf499c`. Gate: `__version__` 0.0.2, lock
  check 48 packages, format 333, ruff clean, prek 9 hooks, not-golden 1093 passed 1
  skipped (personal-terms file absent here), golden 22 (tolerance, exact). `p8-promote`
  pushed; PR #12 to `main` opened and held for the maintainer.
- PR #12 CI green on `8cf499c`: checks (3.13, 3.14), golden (ubuntu, macos-15),
  prerelease, benchmarks, CodSpeed (no performance change); mergeable, clean. Held for
  the maintainer's merge; then the `v0.0.2` tag waits on the maintainer's confirmation.
- Maintainer: "Merge and tag". PR #12 squash-merged as `0e094c7` on `main` (version
  0.0.2). Annotated tag `v0.0.2` made locally on `0e094c7` ("pyntpot 0.0.2, a candidate
  for the upstream migration"); the push was refused by the proxy four times ("send-pack:
  unexpected disconnect while reading sideband packet"), as for `v0.0.1`. Branch pushes
  work. Maintainer action: push `v0.0.2` at `0e094c7`. P8.1 waits on it. `origin/main`
  merged into `p10-fixes` (a merge, not a rebase) and pushed.
- Maintainer pushed `v0.0.2`: annotated `9fe2542` on `0e094c7` (checked with
  `git ls-remote`). Upstream `origin/main` still `e62657f`, so no check-first deltas.
  Upstream branch `p8-pyntpot-migration` cut from it and pushed; P8.1 started.
- P8.1 landed upstream (`99218a1`): Python 3.13, ruff py313, dependency on `v0.0.2`,
  hatch direct references. Lock source resolves to `0e094c7`; `__version__` 0.0.2; G-up
  369 passed 9 skipped, ruff clean at py313, `--help` exits 0. Deviation: hatch metadata
  set before `uv add --raw` (it refused otherwise). Upstream draft PR #1 opened, held.
- Before P8.2: the reference record lacked the input copies "The reference, decided"
  requires before P8.1 (missed at that point; no upstream code depends on them yet). An
  agent is completing it against the old code at `e62657f`.
- Reference record completed upstream in git-ignored `data/p8-reference/`: the three
  old-named payloads, the GPX, `places.json` at `e62657f`, the analysis payload and
  `snapshot.json`, each with its sha256 in `reference.md`, plus a Preconditions section.
  Caveat: `snapshot.json` was normalised from read-only pulls holding only the fields
  `normalise` reads (no projected fitness rows, today = 2026-10-09); it feeds only the
  phase gate's page check. P8.2 started in its worktree with the record copied in.
- P8.2 landed upstream (`4c179d2`): `tests/test_map_parity.py`. Check-first: all seven
  input copies match `reference.md`; `athlete/places.json` unchanged since `e62657f`.
  G-up 370 passed 9 skipped, ruff clean, new file format-clean, `--help` 0. G-ref:
  "tests/test_map_parity.py::test_reference_render_matches_pinned_hash PASSED",
  "1 passed in 50.11s": the reference inputs through `v0.0.2`'s public API give
  `0dfffcca...6619` exactly. Deviations: the test finds the payloads by glob (no activity
  in the test) and skips unless exactly one overpass payload is present; the plan's
  docstring wording carries `# noqa: E501`.
- Group 1 started in parallel worktrees from `4c179d2`: P8.3a, P8.3b, P8.6.
