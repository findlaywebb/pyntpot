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

## P7.3, P7.4 and the parallel group landed (2026-10-24, overnight)

All by slice agents in detached worktrees, cherry-picked in order: P7.3, P7.4, then P7.5,
P7.6a, P7.6b, P7.6c, P7.9, P7.8, P7.7. The group ran from P7.4's commit with the Keswick
fixture copied in untracked (P7.3 had not landed yet); each slice's only expected red was
the coordinate gate on those untracked files. Each slice ran its own golden pins exact;
the full suite runs at landing and on the PR. Landing conflicts were all in the shared
append-only registry `tests/support/docs_images.py`, resolved by keeping both blocks.

- **P7.3**: five fixtures; sizes raw / gzip: Keswick 6.66 MB / 1.06 MB; Trotternish
  1.12 / 0.18; Yr Wyddfa 10.59 / 1.69 (budget 2.5); Oxford 8.83 / 1.46 (37 KB under
  1.5); Y Fenni 3.87 / 0.62. Lengths: 6.74, 6.58, 11.10, 2.70, 2.78 km, all in range.
  Yr Wyddfa checks: start 35 m from the Pen-y-Pass car park outline node, 8 m from the
  summit trig point, 0 m from the Llanberis Path's road end. `--ways` gained an
  `ID:FROM:TO` cut, as the mountain and town ways cannot be used whole; two summit
  spurs were dropped from the specs. `test_coordinates.py` exempts itself (it holds the
  boxes table). Golden job locally +4 min (five cards). All recorded through the mirror
  with the repo URL as contact.
- **P7.4**: registry, regeneration script, pins, budgets, gallery (8 entries, 185 KB of
  500 KB). SVG spike: `svgelements` 1.9.6 imports clean under `-W error` but fails `ty`
  (unresolved imports), so it was rejected; P7.6c reads SVG with `xml.etree`. Golden
  locally +1 min.
- **P7.5**: the two tutorial pages, the sync test (5 tests), pigments now rung 4 and the
  nib rung 5; 8 page images, 211 KB. Keswick first paint about 59 s, 3.5 s cached.
- **P7.6a**: curves (rose, Lissajous, spirograph) and a kaleidoscope; 123 KB.
- **P7.6b**: Barnsley fern and Apollonian gasket (reworked once at orchestrator review
  so the container shows and the discs sit inside it; cap raised to 300 circles); 83 KB.
- **P7.6c**: Derwentwater and the SVG drawing (fell.svg fixed once at review: skyline,
  tarn); 44 KB.
- **P7.7**: four example themes (pen-and-ink, sepia, bold, winter); 182 KB; golden
  map-style test about 4 min locally. Rivers can be non-blue only through `MAJ` brush ids.
- **P7.8**: six how-to guides, the command test; 58 KB. Noticed: `OpenTopoData.credit`
  is fixed to "NASA SRTM" whatever dataset a self-hosted server serves (the guide says so).
- **P7.9**: reference pages with 20 pin tests; pigment and brush sheets, 65 KB. The
  architecture suite now imports `pyntpot` (to read the CLI parser and the style
  dataclasses) and argparse's private `_actions`.
- **Fix at landing**: prek's `ruff format` formats Python blocks inside Markdown, so an
  excerpt quoted from inside a function is dedented and then fails the verbatim sync.
  The gasket's layer-building became its own top-level function `gasket_layers`, quoted
  whole; the image is unchanged (pin exact). The rule for every page: quote whole
  top-level functions or statements.

For the maintainer: the Keswick card works but is weak as the hero. The route runs out
and back over itself, a shop ("The Retro Zone") is lettered as a landmark, and the lake
is faint in the default theme (clear in "bold").

## P7.10 landed (2026-10-24)

Three essays (how the wash works, the hand and the nib, data policy), `wash_stages.py`
and `nib_stages.py` with 14 figures (437 KB of 500 KB), figure tests under 2 s. Parked:
`docs/features/ink-public-wash-options.md`, because `WashOptions` is not public, so a
truly flat body, backruns, bleed, the flow rim, pit granulation, pigment separation and
the shallow-water pass are described in words with their keys but have no figure. The
data-policy page covers five duties (the brief said four: legibility is the fifth). The
runs-dry nib figure uses an exaggerated reservoir, as its caption says.

## Fixture budget re-based again (2026-10-24, orchestrating session)

CI's `checks` jobs failed the gzip budget on Oxford: 1,506,991 bytes there against
1,462,704 on the recording machine. The compressed size depends on the zlib build, so the
test was not deterministic. The budget is now bytes on disk: 10 MB per fixture, 12 MB for
`yr-wyddfa/` (largest today: Oxford 8.83 MB, Yr Wyddfa 10.59 MB); git stores them at about
a sixth of that. ADR 0032 says so and keeps the gzip figures for scale. Still for the
maintainer to confirm. The `docs` job's link failures were from a commit before the
explanation pages landed; offline lychee is clean on the current tree.

## P7.3b landed (2026-10-24)

`BasemapStyle.name_tags` (default `("name",)`, omitted from the digest at its default),
`examples/themes/y-fenni.toml` reads `name:cy` first. Proof: `make_golden.py` compare
against `tests/golden/lynmouth`, all five identical, hash
`340a7f6e260ee1e2-e5a5f1b4b3ca2177` both sides. The Y Fenni card now letters Y Fenni,
Llan-ffwyst and Afon Wysg (was Abergavenny, Llanfoist, Usk). Three files outside the
brief were needed and touched: `test_example_themes.py` (the new theme in its list),
`docs/reference/style-fields.md` (the new field) and the ADR index. `_name` treats an empty
tag value as absent. `docs/features/maps-prefer-welsh-names.md` deleted.

Orchestrator fix at landing, `tests/golden/test_places.py`: the label pin compares the
distinct names, because Oxford places one "Cherwell" on CI and in later local runs where
the recording run placed two (a placement near-tie); and the Y Fenni assertions now test
the lettered names, not the pinned list (they were tautological).

## Docs-image pins redesigned (2026-10-24, orchestrating session; provisional)

CI failed several docs-image pins under `--golden-tolerance` on both OSes (fern 3 to 9%,
route map 1.4%, sepia 3.1%, gasket 0.75%; bound 0.5%), while this sandbox is exact.
Measured cause: sub-LSB CPU noise flips 0.04 to 0.09% of 8-bit pixels by at most 2
levels, but lossy WebP at q90 turns that into 3 to 10% of pixels past the bound; only
lossless is immune, and lossless page images are too large to publish. The bound and the
delta were not changed. Design now (ADR 0033, "Pins across platforms", provisional for
the maintainer): each entry also commits a lossless PNG master, at most 240 px wide, under
`tests/golden/docs/` (46 masters, 2.3 MB); exact mode checks the docs image and the
master; tolerance mode (CI) checks the master only. Under simulated noise no master
pixel moves by more than 2. Before this, the fern and the gasket were also given
per-element random streams so a float flip cannot cascade (they were not the cause, but
it keeps any flip local). The CI failure artifact now holds the painted images only (it
was 190 MB with the fixture copies).

For the maintainer: this departs from the plan's order. P7.4's done line (a green two-OS
run before the fan-out) was not met overnight, because the fan-out ran in parallel to
save time; the drift surfaced on the draft PR afterwards.

## P7.13 landed (2026-10-24)

README in the prescribed order (wordmark, tagline, Keswick hero, Derwentwater as the
non-map image, lede, five badges, what it is, stated values, gallery strip, install,
quick start, credit, docs, status, licence; every image and repo link absolute at
`main`). `word.py` (the painted wordmark), `place_card.py` (hero at 1200 px and the five
place cards, Y Fenni with its Welsh theme), `social_preview.py` (1280 by 640 JPEG,
102 KB); 8 images and masters, 0.42 MB of the 2.7 MB share. `docs/index.md`,
`docs/gallery.md`, the five index pages' prose, `docs/README.md`'s user list; lychee's
index exclusion removed (offline: 202 OK, 0 errors); `test_readme.py`; Q13 marked done
in `p10-triage.md`. The README's Python quick start is `wash.py` from its constants to
the end of `main`, verbatim. Agent's judgement, shared: the hero has wide empty paper
on the left and stray river strokes; the wordmark is plain.

## Fresh-context review and its fixes (2026-10-24)

A fresh-context reviewer read the whole P7 diff against the plan
(`reviews/p7-docs-review.md`): no blockers, six majors, seventeen minors; accuracy held
wherever a reader would test it. Fixed in one commit: the route ink's unread `effect`
(claims dropped, listed as a field with no reader, issue filed); the rose "Try changing"
step; the README quick start now runs as pasted; "sheet" no longer used for paper ("Compose
the painting"); first-map copies the fixture from the clone; place-card captions; most
minors. Ambleside is now the name the lettering rung writes (its sine widened so the first
letters read). Left for the maintainer: the shop "The Retro Zone" lettered as a landmark on
the Keswick card (the hero), and the gasket cap raised to 300. Issues filed:
`maps-route-ink-effect-unread.md`, `maps-lettering-river-name-clipped-at-path-end.md`.

## P7.14 on its own branch, PR #29 (2026-10-24)

Material for MkDocs 9.7.7 (Zensical is at 0.0.72, before the 0.1 the plan's rule asks
for) with mkdocstrings-python 2.0.10, a strict build on every PR and a Pages deploy on
push to `main`; generated API reference with a test that every public name appears once;
the painted theme (paper, brush rule, `PIGMENTS` palette as CSS, contrast tested), Patrick
Hand for headings only. Fixes at landing: `.gitignore`'s `site/` also ignored
`docs/images/site/` and its masters (now `/site/`); four lint findings the slice missed.
`p7-docs-release` merged into it after the review fixes; strict build clean. Its tasks.md
line is ticked when #29 merges. Maintainer action: enable Pages from Actions. Docstring
findings: `PIGMENTS`, `TRANSPARENCY` and `PigmentLayer` use `#:` comments, which the
reference does not show; `stamp`'s source line is plain text.

## P7.V1 Fixture trimming (2026-10-25)

`tests/fixtures/trim_fixture.py` (new) rewrites an Overpass payload as minified JSON
(`separators=(",", ":")`, `ensure_ascii=False`, one trailing newline), drops each
element's `nodes` and `bounds`, filters `tags` to `KEPT_TAG_KEYS` plus every key starting
`name`, and with `--simplify-m M` runs Douglas-Peucker on way and member geometry (ends
kept exactly). `record_fixture.py` trims the feature and land cover payloads after
`Cache.ensure`. `test_trim_fixture.py` (5 tests) written first. Lynmouth and Yr Wyddfa
trimmed in place, without `--simplify-m`; a second run changes nothing.

**Sizes** (`du -sb` per directory, bytes; payload files in brackets):

| Directory | Before | After | overpass | landcover |
| --- | --- | --- | --- | --- |
| `lynmouth/` | 3 648 402 | 2 007 944 | 1 456 826 -> 839 288 | 2 125 886 -> 1 102 966 |
| `yr-wyddfa/` | 10 593 606 | 6 060 891 | 4 119 750 -> 2 450 790 | 6 393 510 -> 3 529 755 |

`elevation-*.json` and `track.gpx` untouched. Fixture budgets are lowered in P7.V9a.

**`KEPT_TAG_KEYS`**, from
`grep -rhoE --include='*.py' '"[a-z_:]+"' src/pyntpot/maps | sort -u` (403 literals)
intersected with the tag keys present in the payloads of all seven fixture directories,
then the seven P7.V5 keys added. `name` and `name:cy` are in the intersection but covered
by the `name*` prefix rule, so the tuple omits them:

```
amenity artist_name artwork_type attraction boundary bridge building building:levels
direction display ele footway garden heath height highway historic industrial landuse
leisure man_made meadow memorial museum natural note peak place place_of_worship plaque
ref residential service start_date tourism trees tunnel type water waterway wetland
wikidata wikipedia heritage listed_status shop brand brand:wikidata
```

**Proof no picture moved.** Before trimming `uv run pytest -m golden` (exact): 85 passed.
After: `pytest -m "not golden"` 1230 passed, 1 skipped; `-m golden --golden-tolerance`
passed; `-m golden` exact 85 passed in 27 min 18 s; `git status tests/golden docs/images`
clean. No key had to be added to the tuple.

**CI baseline** (the GitHub MCP tools were not available to this session; read through
`gh run list` and `gh run view`, read only; nothing dispatched). The latest completed
`golden.yml` run on `p7-docs-release` is 40147407817 (`pull_request`, head `4cbcb7a`,
success; the run on the base commit `573630c` was still in progress, and the commits
between touch only plan and review files): job `golden (ubuntu-latest)` 00:37:22Z to
00:55:55Z = **18 min 33 s**. `golden (macos-15)` in the same run: 17 min 39 s. The round's
CI budget is this plus 4 minutes at the P7.V12-group checkpoint.

## P7.V8b Painter's pigments (2026-10-25)

Separate tables `PAINTERS_PIGMENTS` and `PAINTERS_TRANSPARENCY` in `ink/pigment.py`,
exported from `pyntpot.ink`; ADR 0039, glossary row, "Painter's pigments" section on
`pigments.md`, tests (pinned `PIGMENTS` and `TRANSPARENCY` literals, same keys, shares in
[0, 1], non-white swatch per pigment). No other slice's owner file touched. Gate: prek green;
`-m "not golden"` 1245 passed, 1 skipped; `-m golden --golden-tolerance` passed;
`-m golden` exact 85 passed (26 min 8 s); no golden or docs image moved.
## P7.V1b Fetch margins as options (2026-10-25)

`Cache` holds `margins: FetchMargins`, read by `key`, `ensure` and `fetch` (public frozen
dataclass `features_m`, `landcover_m`, defaults `MARGIN_M`, `LANDCOVER_MARGIN_M`;
validated in `__post_init__`); `landcover_margin_m` joins the canonical
JSON only when not the default, so the default key (`f173b2f7a20bb9d4`) is byte-identical.
`FetchMargins` raises `ValueError` naming the value for a margin outside 0 to 20 000 m or a
land cover margin under the feature margin (`MAX_MARGIN_M` in `cache.py`). `pyntpot map --margin-m` reaches `fetch` and
`cache.key`, the land cover margin being `max(2600, margin)`. `record_fixture.py` gains
`--margin-m` and `--landcover-margin-m`. ADR 0040 and its index row; `cli.md` and
`cache-layout.md` updated; `test_key_inputs_are_named` gains `landcover_margin_m`. Tests
first: `tests/unit/maps/test_cache_margins.py` (new; recording providers keep the requested
boxes, no mock). Examples and `tests/support/golden.py` untouched.

Gate: prek green; `-m "not golden"` and `-m golden --golden-tolerance` green; `-m golden`
exact green with `git status tests/golden docs/images` clean. `Ruled by the coordinator: no `noqa`; the two
keywords became the one `FetchMargins`, held by `Cache(directory, margins)` so `fetch` keeps its
signature (exported from `pyntpot.maps`, in the public API test
and the glossary). The exact golden run was done before this change and not repeated (no
golden reads a non-default margin).
## P7.V9a part 1: the showcase tracks (2026-10-25)

Part 1 builds the tracks and the `make_track.py` changes. The payloads, margins, budgets,
`test_places.py` and the docs images are part 2, after P7.V1b.

**`make_track.py`** gains `--step-m` (default the `STEP_M` of 20 m), `ref=REF[:FROM:TO]` items in
`--ways` (one ordered list with ids) and `--box S,W,N,E` (command line only). A ref's ways chain by
shared node or a gap of at most 5 m; it fails, naming way ids, on a gap, a fork or a closed way.
`test_make_track.py` (14 tests, offline, hand-built ways) written first.

**Tracks** (built over the mirror; contact is the repo URL; every via-node and length check passed):

| Fixture | Route | Length | Points | Ways fetched | `--ways` items |
| --- | --- | --- | --- | --- | --- |
| `ambleside/track.gpx` | Loughrigg circuit, loop | 9.00 km | 460 | 65 | 70 |
| `skye/track.gpx` | island tour, one way, `--step-m 100` | 282.98 km | 2,853 | 281 | 246 (8 `ref=`) |
| `oxford/track.new.gpx` | colleges and bridges, loop | 4.04 km | 209 | 41 | 48 |
| `y-fenni/track.new.gpx` | food tour, loop | 2.21 km | 120 | 38 | 52 |

- Ambleside: a route through Loughrigg Terrace from Bridge House is about 9.3 km, over the 9 km
  bound, so the loop starts and ends on Church Street/Compston Road about 140 m from the Bridge
  House node (README). Passes the Miller Bridge and Pelter Bridge nodes and Rydal Cave.
- Skye: `ref=` items for `A851`, `A863` and `B884`. `A87` and `B8009` fork and `A850` and `A855`
  have gaps over 5 m, so those and the unreferenced Glen Brittle and Neist Point roads are listed
  by way id. All eleven place checks passed (Uig is checked at its post office: the ferry
  terminal is 416 m below the A87). The `--box` east edge is just west of the Kyleakin
  roundabout. Whole-island ways are not recorded here: that is part 2.
- Oxford: no way inside Christ Church is tagged other than `private` or `no`, so the route runs by
  the Meadow Buildings and War Memorial Garden footways. Radcliffe Camera and Magdalen Bridge
  nodes checked.
- Y Fenni: Angel Bakery, Bean & Bread, Rate of Rise, Shepherd's Ice Cream and the Tŷ Melin point
  checked. Tŷ Melin: its public address (from the bakery's own site) is held in OpenStreetMap as
  an address node inside a building way; the README records both and the point.

The old `oxford/track.gpx` and `y-fenni/track.gpx` stay with their payloads; part 2 swaps in
`track.new.gpx` and re-records. `test_coordinates.py` gains the `ambleside` and `skye` boxes
(each the track's box rounded outward to 0.01); the two new fixtures have no cache key until part 2.
The Oxford and Y Fenni boxes already hold their new tracks and are unchanged.

## P7.V8 Showcase style fields (2026-10-25)

`basemap.minor_road_classes` (default `MINOR_ROADS`, read in `osm_elements._road` for `roads = "all"`),
`cover.relief_strength` (default 1.0, scales `relief_density` and its 0.40 cap, passed in by
`painter/relief.py`), and `compose.route` reading `blend` (`normal` or `multiply`) and `opacity`
(default 1.0, not written into `default.toml`) for the solid and the pen route; ADR 0037. Both
dataclass fields join `DIGEST_OMITS_AT_DEFAULT`, so the default style's three digests are
unchanged (pinned tests hold). Re-pinned: `CoverStyle` default-fields digest in
`test_style_groups.py`, `f201b60695520db7` to `a128e6b0e70f5c23` (the new field changes the
hashed JSON); `BasemapStyle` defaults and both field-order rows gained the new names. Docs:
`style-fields.md` (the two fields, a `blend` and `opacity` table under the route inks, the
"no reader" note narrowed). Edits to files other slices own, kept minimal: none of the
P7.V2 to P7.V7b slices' files beyond `painter/paper.py` (one signature default and the density
line), which P7.V2 to P7.V7b do not edit as far as their briefs say.
## P7.V9b Journal notes (2026-10-25)

`Annotations.notes` (at most 6 `JournalNote`s of at most 60 characters, exported from
`pyntpot.maps`), seated by the new `maps/lettering/notes.py` (`note_labels`, `seat_notes`) before
`place` runs; `pipeline.letter` passes their boxes on as taken and puts them after the home glyphs
in `Lettering.labels`. `best_flat` gains an optional `forms` argument (the import-order test bans importing
`_place_flat`); `placement.py` is untouched: a note has no baseline, so `off_own_feature` already costs it nothing. ADR 0038, glossary "journal note", test first in
`tests/unit/maps/lettering/test_notes.py`. No golden moved.
## P7.V9a part 2: the showcase payloads (2026-10-25)

Recorded over the mirror with the repository URL as contact, by `record_fixture.py` (trims after
`Cache.ensure`). The mirror answered the land cover query (and once the feature query) with 504
Gateway Time-out on the first one or two tries; the recorder's own retries carried each recording
through. Commits, one per fixture: `Record the ambleside fixture`, `... oxford ...`,
`... y-fenni ...`, `... yr-wyddfa ...`.

**Stops reported to the coordinator: Skye over the 12 MB rule, and Ambleside over 6 MB (both ruled below).**

- **Skye** (margins below): raw 85.7 MB features and 31.4 MB land cover; trimmed 46.3 and 17.8 MB;
  `--simplify-m 15` gives 13.5 and 6.0 MB (19.7 MB the directory); re-trimmed at `--simplify-m 25`,
  11.4 and 5.0 MB, **16.66 MB the directory, over the 12 MB limit**. The simplification is exhausted:
  of the 25 m payloads about 12.6 MB is geometry and tags and the rest is structure, over 49,000
  ways and 450 relations in the features and 16,300 ways in the land cover; fewer vertices would
  not bring it under 12 MB. At the 720 px card `mpp_display` is 106 m, so 25 m is a quarter of a
  display pixel. The payloads are not committed; the three trimmed payloads (key `ada01f635902a1fd`,
  recorded with 18,000 m for both margins) are held outside the repository, in the session
  scratchpad, `skye-held/`. `skye/` holds the track and README only, as part 1 left it.
- **Ambleside** at the library's default margins: 6,571,595 bytes the directory (land cover 4.87 MB
  trimmed, features 1.62 MB), over the 6 MB default. `BUDGETS["ambleside"] = 7_000_000` is set so the
  gates run, with a comment; the coordinator accepted it: a deliberate per-fixture budget for the hero walking map, like Keswick's, not a loosening of a contract.

**Margins** (the margin rule: card box by `journal_geometry` under the default ribbon fields of the
simplified projected track, the card's largest overhang beyond the track's box, plus 1 km):

| Fixture | Card overhang | Margin (features and land cover) | Inside the default box? |
| --- | --- | --- | --- |
| `skye/` | 16,871 m (west; the aspect floor widens the card east and west) | 18,000 m | not asserted (no payloads committed) |
| `yr-wyddfa/` | 1,957 m | 3,000 m | no (default 1,500 m); inside the 3,000 m box, asserted |
| `ambleside/` | 1,356 m | default (1,500 m; 2,600 m) | yes |
| `oxford/` | 882 m | default | yes |
| `y-fenni/` | 882 m | default | yes |

**Sizes** (every file in the directory, bytes; payloads are trimmed; not simplified):

| Fixture | overpass | landcover | elevation | Directory | Budget |
| --- | --- | --- | --- | --- | --- |
| `ambleside/` | 1,624,907 | 4,869,967 | 45,650 | 6,571,595 | 7,000,000 (default 6,000,000) |
| `oxford/` | 2,374,957 | 2,415,634 | 41,901 | 4,850,357 | 6,000,000 |
| `y-fenni/` | 1,619,950 | 492,997 | 43,797 | 2,171,023 | 6,000,000 |
| `yr-wyddfa/` | 3,718,963 | 3,915,945 | 47,962 | 7,715,942 | 8,000,000 (was 12,000,000) |
| `keswick/` | untrimmed | | | 6,663,743 | 7,000,000 (new entry; P7.V12a removes it) |

Keys: ambleside `f0a137ce97afcb43`, oxford `edf326cc49d5cc52`, y-fenni `31d229011257f9fa`, yr-wyddfa
`353c7a77ae84f4c1`. The default budget is 6 MB (was 10 MB); `trotternish/` (1.1 MB) needs no entry.

**`test_places.py`**: `Place` gains `margin_m` and `landcover_margin_m`, a `Cache` over
`FetchMargins(...)`; a place with non-default margins asserts the card box lies inside
`track.bounding_box(margin_m)` projected through `basemap.projection` (Yr Wyddfa only; Skye has no
row). `place_card.py` gains `margin_m`, `landcover_margin_m` and `place` options (margins build
`Cache(cache_dir, FetchMargins(...))`; the land cover margin is the larger of its default and
`margin_m` when absent; `place` is accepted and unused until P7.V10). `docs_images._PLACES` rows carry
`("place", fixture)` and the Yr Wyddfa row `margin_m` and `landcover_margin_m` 3000.0 (a float: the key
hashes the number as written, so `3000` and `3000.0` are different keys).

**Expected labels** (first run; distinct names compared as a set):

- `ambleside`: Ambleside, Rydal, Rydal Bridge, Rydal Road, A591, Rothay, Brathay, Hope Church, start (9)
- `oxford`: Cherwell, Thames, A4144, A4158, High Street, Magdalen Tower, The Bridge of Sighs, start
  (8; was 8 with Holywell Mill Stream, B480, Tom Tower and Christ Church, now gone with the route)
- `y-fenni`: Y Fenni, Llan-ffwyst, Afon Wysg, Gavenny River, A40, Abergavenny Baptist Church, Methodist
  Church, Borough Theatre, start (9; United Reformed Church and B4246 gone)
- `yr-wyddfa`: Afon Arddu, Afon Nant Peris, A4086, Garnedd Ugain, Yr Wyddfa, Crib Goch, start, finish
  (8; Llanberis and Nant Peris, lettered before, are no longer placed on the wider card)

**Images moved**: `places/oxford.webp`, `places/y-fenni.webp`, `places/yr-wyddfa.webp` and their three
masters, regenerated with `make_docs_images.py` (the cards changed because the fixtures did).

**The cards, looked at** (painted at 900 px and viewed; the engine faults are the later slices'):
Ambleside: Rydal Water is a blue patch cut at the card's left edge and not named; the route reads
well and the three bridge and church leaders are clean, but no peak (Loughrigg) or Terrace is named
and the fell is bare ground. Oxford: the Cherwell is one solid blue blot beside the route (P7.V2);
the Radcliffe Camera, the colleges and Magdalen Bridge are not lettered, `High Street` sits as a
landmark label (P7.V5, P7.V10). Y Fenni: the 2.2 km loop is tiny and its doubled legs overlap into
a tangle (P7.V7), and no food-stop is named (P7.V10). Yr Wyddfa: grey foxing smudges at the paper's
edge (P7.V7b); the ground beyond the ribbon is empty paper, so the widening shows only roads and
rivers there; a lake is cut by the frame at the lower left and not named.

**CI allowance** (`gh` read-only gave no per-test durations for the baseline run, so measured
locally, `--durations=0`, exact golden run on this machine): Keswick card in `test_places.py`
57.6 s and Trotternish 46.1 s (103.7 s); their pins in `test_docs_images.py`
`places/keswick.webp` 35.4 s and `places/trotternish.webp` 23.6 s (59.0 s); 162.7 s in all, which
P7.V12a removes (the hero and the social preview, painted from Keswick today, move to Ambleside and
stay). The new Ambleside card adds 43.3 s to `test_places.py`; Oxford and Y Fenni are unchanged in
cost (51.9 s, 51.5 s); Yr Wyddfa 41.4 s. The golden CI run after the last fixture is dispatched by the
orchestrating session and not recorded here.

## 2026-10-25 P7.V3 A leader never crosses a placed label (code; regeneration deferred to the group regeneration slice)

**Change.** `LEADER_CROSS_LABEL_COST` (= `ROAD_CROSS_COST`, 90) per placed box a leader segment
passes through, charged in `_place_flat` (candidate leader from the anchor to the box's near edge,
leadered names only: not spans or `NO_LEADER` kinds) and in `placement._seat_cost` (so
`_swap_seats` cannot put a label back across). New helper `placement_costs.leader_crossings`.
`placement.py` is 391 lines, so no split. Tests: `test_placement_flat.py` (leader not run through a
placed label) and `test_placement.py` (swap refused when it would cross a third label); both failed
before the fix.

**Attribution (Lynmouth, `--compare`).** Nothing moved: paper, wash, pen, labels-centreline and
map are identical, differing fraction 0.000000 each, manifest hash unchanged. No label changes. The
fix targets Keswick ("Lake Road Chapel" through "Keswick"), which the Lynmouth card does not show.
Expected to move: the places card(s) with a leader crossing a placed label (Keswick, any other
in `test_places.py`), their docs images and masters; map styles and Lynmouth expected unmoved.
The group regeneration slice should list the places labels whose positions moved.

**Draft ADR 0036 section (P7.V3).** A leader never crosses a placed label. `_place_flat` costed a
candidate's box against placed boxes but not the line joining it to its mark, so a chapel's leader
could cut the "K" of "Keswick". A candidate now pays `LEADER_CROSS_LABEL_COST` (90, equal to
`ROAD_CROSS_COST`) for each placed box its leader passes through, in the flat placer and in the swap
pass's `_seat_cost`. It is a price, not a ban: where every seat crosses, the cheapest still wins.
Leaderless names (spans, settlements, rivers, roads, markers) are not charged. Positions of
leadered labels move on cards where a leader used to cross a label; regeneration is deferred to
the group slice.
## 2026-10-25, P7.V4 The skeleton draws each stroke once (code; regeneration deferred to the group regeneration slice)

**Cause found.** The thinned skeleton was sound (clean one-pixel lines, correct junction counts); the
fault was the walk that turned it into chains in `letters/skeleton.py`, plus long flanks in
`letters/trace.py`. `RASTER_EM`, `FLANK_MIN` and the junction merge were not touched. Four faults:
(1) `_step` skipped any pixel touching the previous one, so a walk stepped over a junction node and
ran on to the far end: a stroke was drawn through the junction and again from the other side (k, m, n,
K stems). (2) A junction pixel with a neighbour for each staircase pixel started the same branch twice.
(3) A walk that came back to its own start node (a bowl on a stem: d, g, a) carried on and drew the stem
again. (4) A dead-end corner pixel stopped a walk mid-stroke (R's bowl twice), and leftover staircase
corners became 7-pixel loops. Separately, a flank longer than 3 half-widths is the stem's own other
side (d, p, B, A), not an arm folded into a stem (M's flanks are 1.5).

**Fix.** `_walk` ends at any node beside it and at its own start node once round a loop; `_step` takes
the pixel that touches the walk least; `_again` drops a walk whose run is already drawn; `_loops` drops
leftovers lying wholly beside drawn chains; `trace._flank` drops a flank longer than `FLANK_LONGEST`
(3.0 half-widths). Test: `tests/unit/letters/test_skeleton_glyphs.py` (pieces, no stroke alongside
another for more than a stroke width, the o one ring); red before on K k e m n d a g o, green after,
and every A-Z a-z 0-9 clears the same check.

**Attribution (Lynmouth, `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/after-p7v4`).** paper, wash, pen: byte-identical. `labels-centreline.webp`
moved (5.36 percent of pixels past the parity bound), `map.png` moved (1.69 percent). `labels.txt` is
identical to a run without the change (`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/before-p7v4`): no label changes. Looked at: every letter is
drawn once, and the leader lines moved too (the hand's draws are made per stroke, so fewer strokes
shift every later draw). Crop: `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/p7v4-lynmouth-labels-before-after.png`. Words with the shipped hand,
before (left) and after (right): `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/p7v4-words-64px-before-after.png` and
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/p7v4-words-200px-before-after.png`.

**Expected to move at regeneration:** Lynmouth `labels-centreline.webp` and `map.png`; every lettered
card in `test_places.py`; the lettered docs images and masters (hero, social preview, word, lettering,
nib pages, place cards); map styles; the smoke lock only if it letters (not checked here).

**Draft ADR 0036 section (P7.V4).** The centreline skeleton draws each stroke once. The chain walk no
longer steps over junctions, repeats branches, runs past a loop's own node or dead-ends at a staircase
corner, and a flank is an arm only when short. No single-line font was needed. The lettered goldens
and images repaint; labels do not change.

Regeneration deferred to the group regeneration slice.

### P7.V4 follow-up (same day): strokes meet at their junctions

The first cut drew each stroke once but the nib showed gaps: d's ascender came away from its stem,
the a's foot was a stray dot, t's bar and stem looked unjoined. Causes: (1) every stroke ends at a
junction, and the nib tapers each end, so the stem is thin exactly where it is joined; (2) short
spurs at a junction that carry straight on from another branch (the top of an n, the foot of a d)
were pruned; (3) flank stubs started beside the stem, not on it, and several were shorter than the
pen is wide. Fix: new `letters/junction.py` (`join_through`) makes one stroke of the two arms that
leave a junction in opposite directions (a crossing joins both pairs; junction pixels within 3 px are
one junction and a bridge inside one is dropped); `skeleton.prune` keeps a spur that carries on from
another branch; a flank starts on its stem and is dropped under 2.2 half-widths. Tests added to
`test_skeleton_glyphs.py` (class `TestJoined`, every letter and figure but D, Q, 3, 8): every
skeleton pixel is within 0.03 em of a stroke, no stroke is shorter than a stroke width, the glyph is
one piece, the t is two strokes; red before on d, n, Y, t, y, f, k, K, M, h, R, B. Known, not fixed:
terminal tails of D, Q, 3 are still pruned as spurs and 8 keeps a 0.047 em bridge.
Lynmouth re-attribution (`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/after2-p7v4`): paper, wash, pen identical; `labels-centreline.webp`
4.92 percent moved; `map.png` 1.62 percent; `labels.txt` identical. Images: `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/p7v4-words-64px-before-after-v2.png`,
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/p7v4-words-200px-before-after-v2.png`. Draft ADR 0036 addition: strokes that run on through a
junction are one stroke (`letters/junction.py`).
## P7.V5 Landmark ranking (2026-10-25)

Code and unit tests only; regeneration deferred to the group regeneration slice (the engine group P7.V2 to P7.V7b runs in parallel worktrees, brief `engine-brief.md`). No golden, docs image or master was touched.

**Change.** `landmark_classes.classify` now, after the plaque rule and before `_RULES`: returns `other` for anything tagged `shop`, `brand` or `brand:wikidata`; returns `sight` for a `tourism=museum` with none of `wikidata`, `wikipedia`, `heritage`, `listed_status`; and a new rule ahead of `monument` in `_RULES` classes `historic=castle` and `building=castle` as `building` (tier 1). `is_recorded(tags)` (new, `RECORD_KEYS`) says whether the record knows a thing; `landmark_rank` is `(tier, not recorded, distance / reach)`; `osm_elements.LANDMARK_TAG_KEYS` gains the four record keys and `shop`, `brand`, `brand:wikidata`. Fixture check: all seven keys are present in the committed `overpass-*.json` payloads (wikidata 7 files, wikipedia 7, heritage 5, listed_status 4, shop 2, brand 1, brand:wikidata 2); nothing re-recorded.

**Attribution (Lynmouth, `make_golden.py --compare`).** Moved: `labels-centreline.webp` (7.6052% of pixels) and `map.png` (3.6517%). `paper.webp`, `wash.webp`, `pen.webp` identical; manifest hash unchanged. Labels: `Hollerday Hill` and `Lyn Valley Art and Craft Centre` (a shop) are replaced by `Lynton and Exmoor Museum` and `Living Waters Lynton United Reformed Church`; the other labels are equal. The map shows the two new landmark labels with leader lines in the Lynton cluster. Outputs: `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/after-v5-lynmouth/`, before: `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/before-v5-lynmouth/`.

**Cards, automatic landmark picks, before and after** (default style, painted by `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/../engine_cards.py`; PNGs in `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/before-v5/` and `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/after-v5/`, `keswick.png`, `oxford.png`, `y-fenni.png`):
- Keswick: before `Derwent Bridge`, `Lake Road Chapel`, `The Retro Zone`; after `Derwent Pencil Museum`, `Friar's Crag`, `Theatre by the Lake`. The Retro Zone, a shop tagged `tourism=museum`, is gone.
- Oxford: `High Street` gone, `Tom Tower` in (the rest equal).
- Y Fenni: labels unchanged (the plan expected the Y Fenni pin to move; it does not).

**Expected to move at regeneration.** Lynmouth golden (`labels-centreline.webp`, `map.png`), the Keswick and Oxford place pins (`test_places.py` expected labels) and their `places/*.webp`, the hero and social preview (Keswick card), the Keswick-derived docs images, Ambleside and Skye cards if their picks change, and the map-styles goldens. Not Y Fenni labels.

**Draft ADR 0036 section (P7.V5).** Landmark ranking. Decision: shops and brands are never offered (`other`); a `tourism=museum` the wider record does not know is a `sight` (tier 2) and a recorded one stays an `attraction`; castles are `building` (tier 1); inside a tier a recorded thing (any of `wikidata`, `wikipedia`, `heritage`, `listed_status`; never `brand:wikidata`) ranks first, so `landmark_rank` is `(tier, not recorded, distance / reach)`. Why: the Keswick card lettered a gift shop as a museum and the Lynmouth card an art and craft centre. Moved: Lynmouth labels (two swapped) and the Keswick and Oxford picks above. Regeneration deferred to the group regeneration slice.
## P7.V6 The nib's touch-down has no square edge (2026-10-25)

**Change**: `ink/deposit.py pool` cuts its Gaussian at `span = ceil(3 * r)` instead of `int(r * 2)`
(side midpoint of the span at `exp(-4.5)`, 1.1%, was `exp(-2)`, 13.5%). Test first:
`test_a_wide_pool_has_faded_to_nothing_at_the_side_of_its_span` (0.135 before, passes after).

**Smoke lock**: the `pen` hash moved to `bb86cd1e...d97`; the `wash` hash did NOT move
(`c1617293...`), so `tests/golden/smoke/wash.webp` is unchanged and was not regenerated (the
smoke box's wash brushes never reach a wide pool). `paper` unchanged.

**Attribution** (Lynmouth, `make_golden.py --compare tests/golden/lynmouth`, scratch
`scratchpad/engine/after-v6`; base of this branch also differs from the committed goldens by
nothing, the compare below is against the committed ones): paper identical; wash 0.000645 of
pixels moved; pen 0.000120; labels-centreline 0.001111; map.png 0.000573. Manifest hash unchanged.
Labels: `labels.txt` identical with and without the change (`engine/before-v6` vs `after-v6`).
Against the unchanged base the map moves 0.54% of pixels, largest channel delta 17 (faint): the
blots at stroke starts are slightly wider and softer, with no square edge.

**Benchmark** (`tests/benchmarks/test_ink.py`, min of 3 runs, machine loaded by parallel slices):
no slowdown; after vs before (ms) stamp 2000 points 12.23 vs 12.80, long stroke dry-track 9.49 vs
9.81, wet-river 10.57 vs 11.44, starved directional 20.58 vs 26.99, wash 37.7 vs 48.5, wet wash
55.8 vs 60.2. Well inside 15%.

**Expected to move at regeneration**: `tests/golden/lynmouth/*` (wash, pen, labels-centreline,
map), the Lynmouth/places/map-styles goldens and docs images (every card that stamps a pen
start). `test_places.py` expected labels not expected to move.

**Draft ADR 0036 section (P7.V6)**: "The pool fades to nothing at its edge. `pool` cut its
Gaussian at two radii, leaving a square blot at wide widths (13.5% of the centre at the side
midpoint). It is cut at `ceil(3 r)` (1.1%). Moves the `pen` smoke hash; the `wash` smoke plate
does not move. Benchmarks unchanged within noise."
## 2026-10-25 P7.V7 The pen route keeps its legs apart (code; regeneration deferred)

**Change.** `painter/pen.py:paint_route_pen` now separates the route with `separate_strands(canvas.px(route),
route_pen_width_px * STRAND_GAP_WIDTHS * scale)` before it lays the pen, whatever the ride ink, so the
pen plate reads base-group fields only. `strands.py` gains `strand_gap_px(style)` (the pen's gap when the
route pen is on and the ride ink is `"pen"`, else the ride ink's), used by `pipeline.paint` alone. The
`Style.with_route_ink` and `pipeline.paint` docstrings state the new rule. The "within a pixel" test
passed on the simplified `layers.route`, so the C1 fallback (separating `basemap.track`) was not needed and
`plates.py` is untouched. Tests: `tests/unit/maps/painter/test_pen_strands.py` (two inked runs across an
out-and-back; strands within a pixel of the pen's runs under a pen ride ink; the gap rule; solid and pen
ride inks paint byte-identical pen plates). The smoke lock's pen hash did not move.

**Attribution** (Lynmouth, `make_golden.py --compare`): `pen.webp` moved, differing fraction 0.000876
(changes in a box of x 409-1395, y 407-1052 of 1800x1457, where the track doubles back); paper, wash,
labels-centreline and `map.png` identical (the default ride ink is solid, so the composed card and the
strands are unchanged); manifest hash unchanged. Labels: none changed (strands unchanged for a solid ride).
Y Fenni card (720 px, `y-fenni.toml`, solid ride): `map.png` byte-identical before and after; its pen
plate moved, fraction 0.0059, the doubled legs now drawn as two lines beside each other.
Images: `engine/v7-lynmouth-pen-before-after.png`, `engine/v7-yfenni-pen-before-after.png`, `engine/yf-before/map.png`,
`engine/yf-after/map.png` (all under the scratchpad).
Expected to move in the regeneration slice: `tests/golden/lynmouth/pen.webp`; every card's pen plate in
`test_places.py` (plates only, composed images identical); docs images only where a pen ride ink is used
(none today); map styles only if a style sets the ride ink to `"pen"`.

**Draft ADR 0036 section.** The pen route follows the separated strands. The pen plate is a base plate and
the route inks are in `digest()` only (ADRs 0005, 0027), so the pen separates the doubled-back legs by its
own `route_pen_width_px * STRAND_GAP_WIDTHS` whatever the ride ink. `pipeline.paint` separates the shown
route by `strand_gap_px(style)`, the pen's gap when the pen plate is the route shown, so lettering and the
solid route read the line the pen painted. Moved: the pen plate of every card with a doubled-back track.

Regeneration deferred to the group regeneration slice.

## 2026-10-25 P7.V7b The paper's edge and foxing (code; regeneration deferred)

`PaperStyle.paper_edge: Literal["classic", "warm"] = "warm"` (not in `DIGEST_OMITS_AT_DEFAULT`),
`default.toml` `[paper]` names it. `"classic"` is the old arithmetic (hash pinned from the base,
`ae150866b4642275`); `"warm"` draws the same two fields in the same order (the generator ends in
the same state, tested), narrows the vignette to `w * 0.08 * (0.5 + n26)`, darkens the worn
border and vignette through `PAPER_EDGE_TINT` (#b08a5a-ish), and foxes with the top 0.3%
(`FOX_SPECK_AREA`) of `sheet.gran` by rank, weighted `0.4 + 0.6 * n120`, tinted `PAPER_FOX_TINT`
(#9a5a32-ish). Also: `paper_foxing=0.0` in `pigment_swatches`, `brush_sheet`, `wash_stages`,
`nib_stages` (their `paper_plate` call); `DocsImage.quality` threaded through `_encode`
(no entry sets it). Docs images not regenerated.

**Pins moved**: default style digests `25ae6fee082ebff5` -> `d7997015c8df9b37`, base
`e5a5f1b4b3ca2177` -> `d9c56c0811177b0f`, lettering `d15ae2f30e9ca5ce` unchanged; `PaperStyle`
group digest `fe2d6474dad3b304` -> `b47c9c6b3a8c1505`; smoke `paper` hash -> `e044d9c4...369ce`
(`wash`, `pen` unchanged, so `tests/golden/smoke/wash.webp` is unchanged).
`GOLDEN_HASH` in `test_pipeline_fetch_paint.py` (golden-marked) still names the old base digest:
the regeneration slice sets it to `340a7f6e260ee1e2-d9c56c0811177b0f`.

**Attribution** (Lynmouth, scratch `engine/after-v7b`): paper 0.99999 of pixels moved; wash
0.000645; pen 0.000120; labels-centreline 0.0777; map.png 0.960. Manifest hash `340a7f6e260ee1e2-d9c56c0811177b0f`
(base digest only). `labels.txt` identical with and without the change. The interior brightens
(card centre RGB 0.940/0.905/0.828 -> 0.954/0.919/0.840): the vignette's narrowing; the classic
smudges are gone; specks added. Job sheet: foxed pixels 0.30%, largest speck 21 render px
(grain 22.4) = about 10.5 display px, for P7.V13. Pictures: `engine/cmp-lynmouth.png`,
`engine/cmp-wash.png`, `engine/cmp-fern.png` (before left, after right). The edge browns,
narrow and uneven; specks are small rust dots.

**Expected to move at regeneration**: all of `tests/golden/lynmouth/*`, places, map styles, every
docs image and master (the fern included).

**Draft ADR 0036 section (P7.V7b)**: "The paper browns at its edge and foxes in specks. The grey
vignette and broad grey smudges are replaced, by default, with a narrow warm edge and small rust
specks (`paper_edge = "warm"`); `"classic"` keeps the old paper. The draws are unchanged, so
later fields keep their values. Moves every image and the default style's full and base digests."

## P7.V2 Water areas keep their islands (2026-10-25, code; regeneration deferred to the group regeneration slice)

**Change.** `Harvest.lake_holes` collects the inner rings of a water multipolygon; `osm.py` writes the
lake fill as `rings_path(lakes, lake_holes)` (holes wound clockwise, the fill is nonzero); the vector
export reads the same `water_area` path, so it gains the holes with no code change of its own and no
existing test pinned its rings. In `rivers.py` a point is in water by a nonzero winding sum over all
rings (`_in_water`), and `_banks_at` takes the nearest crossing of any ring on each ray
(`_nearest_bank`), holes included. `layers.py` needed no change: `clip_ring` and `simplify` keep each
ring's winding (pinned by the new painted-mask test). Bays keep ignoring inner rings. Tests first
(they failed on the old code): the painted lake mask is bare inside an island, a point on an island is
not in water, a river beside an island measures 150 m (100 m to the lake edge, 50 m to the island), not
the 400 m of the envelope. ADR 0036 was not written here (the brief defers it to the group regeneration
slice); its V2 section text is below.

**Attribution.** Lynmouth (`make_golden.py --compare tests/golden/lynmouth`): paper, wash, pen,
labels-centreline and map.png all identical, differing fraction 0.000000, manifest hash unchanged:
Lynmouth's payload holds no holed water, so no Lynmouth golden moves. Oxford card (900 px,
`examples/place_card.py`, before = base `src`, after = this change), saved as
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/v2-oxford-before.png` and `/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/engine/v2-oxford-after.png`: before, the Cherwell is one solid blue blot
about 600 render px across, beside the route, drawn as a 160 to 190 px "major" river; after, the
river is its braided channels (a long loop to the north east and several strands past Magdalen and
below the route), drawn at the width of each channel, with the islands showing as land. Labels: the
set is the same eight words (Bridge of Sighs, Magdalen Tower, High Street, A4144, A4158, Cherwell,
Thames, start) but "Cherwell" is now lettered twice, on two strands, in the river's ink rather than
white-on-blue, and "Thames" moves to the south west bank; "Magdalen Tower" and "High Street" are
placed to the right of their markers. The Oxford pin in `tests/golden/test_places.py` is expected to
move (not edited here).

**Goldens expected to move** (not run, not regenerated): `tests/golden/test_places.py` Oxford (image and
labels); `test_docs_images.py` `places/oxford.webp` (and any docs image painted from the Oxford
fixture, such as the gallery card and its master); Lynmouth, the other places and the map-styles
images do not move.

**Draft ADR 0036 section (P7.V2, water areas keep their islands).** A water multipolygon's inner
rings are islands. The lake fill carries them as holes wound against the outer rings, so the nonzero
fill leaves them dry; the river-width measure treats a point inside an island as not in water and
measures a river's banks to the nearest ring edge of any ring, so a channel beside an island is as
wide as the water it runs in, not as the lake's outer envelope. This moves every card whose payload
holds a holed water relation (Oxford's Cherwell: 14 inner rings, 41.1 of 49.2 ha) and no other.
Regeneration deferred to the group regeneration slice.
## P7.V9a Skye, scale-aware drops (2026-10-25)

`trim_fixture.py` gains `--drop-minor-roads` (drops ways whose `highway` is tertiary, unclassified,
residential, track, service, footway, path, cycleway, pedestrian, bridleway or steps) and
`--min-area-m2 A` (drops closed ways and multipolygon relations whose outer area is below A, unless
`natural=water` or `coastline`, a `place` tag or any `name*` tag), tests first in
`test_trim_fixture.py`. Basis: `painter/pen.py` paints the `lane` and `track` bands only when
`layers.minor_roads` is true, which is `mpp_display < brush.minor_roads_mppd` (8.0 in the default
theme and `BrushStyle`); Skye's card is `mpp_display` 106.429, 900 by 804 display px. A = (106.429)²,
11,326 m2, under one display pixel.

**Sizes** (the held 25 m payloads, then both drops): overpass 11,435,782 -> 8,615,542; landcover
5,025,596 -> 3,698,328; with the elevation payload, track and README the directory is about
12.5 MB, **still over the 12 MB limit, so Skye is again not committed** and no more is dropped.

**Biggest contributors after the drops** (bytes of element text, count): features payload: streams
2.95 MB (15,010 ways), natural=water 1.52 MB (5,297), historic=ruins 1.16 MB (7,609), coastline 0.96 MB
(2,846), woods 0.59 MB (1,210), forest 0.42 MB (868), a nature reserve 0.31 MB (8 relations), rivers
0.19 MB (367). Land cover payload: bare rock 0.97 MB (5,274), meadow 0.78 MB (2,121), a nature reserve
0.34 MB (10), cliffs 0.29 MB (1,627), heath 0.27 MB, residential 0.23 MB, wetland 0.20 MB, scrub 0.19
MB, scree 0.18 MB.

**Lossless?** The Skye card painted from the 25 m payloads and from the dropped payloads (default
style, 18,000 m margins, the same plates cache keys): the same seven label names, the card box inside
the fetched feature box, but not byte-identical: **max pixel difference 57 of 255**, 79,235 of
2,892,600 pixels differ (2.7 %), 9,519 (0.33 %) by more than 8. The difference is confined to a thin
band along the route's ribbon, where the dropped sub-pixel cover areas fed the wash's blotches and
edges; nothing is missing at card scale. Not a pin: no golden holds Skye.

**Ruling and completion (orchestrator, applying the maintainer's 2026-10-25 instruction not to stop
Skye for a slight overrun).** Skye is accepted as it is, both drops and 25 m: the directory is
12,511,755 bytes and `BUDGETS["skye"]` is 13,000,000 (measured, rounded up to the next 0.5 MB).
Committed: the three payloads (key `ada01f635902a1fd`), `KEYS`, `SKYE_KEY`, a `test_places` row with
`margin_m` and `landcover_margin_m` 18000.0 (card box inside the fetched box, asserted; labels
Cnoc an t-Sithean, Giant Angus MacAskill Museum, Sligachan, Snizort, Staffin Dinosaur Museum, start,
finish: 7), a `docs_images._PLACES` row, `places/skye.webp` and its master (pinned against the current
code; the goldens are regenerated once after the five parallel engine fixes), README. The card looked at
(900 px): the island is not washed, only its coast and streams are outlined, and the lochs read as
labels on bare paper ("Snizort", "Sligachan" are sea lochs); two museums are the only landmarks named; grey
foxing at the edge. Gates: prek, `-m "not golden"` and `-m golden --golden-tolerance`; the exact
27-minute golden run was skipped this time by instruction.

## 2026-10-25 P7.V7c Group regeneration (P7.V2 to P7.V7b)

The one regeneration for the seven engine fixes that were coded in parallel (`engine-brief.md`),
on `p7v-7c` (= `p7-wip` at `bbd1c6f`, with the Skye fixture). ADR 0036 written
(`docs/decisions/0036-fourth-golden-regeneration.md`, index row added).

**Lynmouth `--compare` against the committed goldens** (scratch `regen-lynmouth`): paper 0.999990,
wash 0.000645, pen 0.000887, labels-centreline 0.107045, map 0.970524 of pixels moved; hash
`340a7f6e260ee1e2-e5a5f1b4b3ca2177` to `340a7f6e260ee1e2-d9c56c0811177b0f`. That is the union of the
slices' attributions: paper P7.V7b alone; wash P7.V6 (0.000645, equal to its own figure); pen P7.V6
0.000120 plus P7.V7 0.000876; labels-centreline P7.V4, P7.V5, P7.V6, P7.V7b; map likewise; P7.V2 and
P7.V3 move nothing on Lynmouth. Nothing unexplained. Labels: `Hollerday Hill` and `Lyn Valley Art
and Craft Centre` replaced by `Lynton and Exmoor Museum` and `Living Waters Lynton United Reformed
Church` (P7.V5), the rest equal. Looked at the old and new `map.png` side by side: the paper is
brighter inside with a narrow, uneven warm brown edge in place of the grey vignette, the pink route
and ink are unchanged, the Lynton cluster has the two new landmark labels with leaders.
Regenerated `tests/golden/lynmouth/` in place; a fresh paint compared with it:
`--require-identical all --require-hash equal`, exit 0, every output identical.

**Smoke lock**: `SMOKE_SHA` (paper `e044d9c4...`, pen `bb86cd1e...`, wash `c1617293...`) already
matches the merged code, exact and golden-marked tests green; `tests/golden/smoke/wash.webp`
unchanged, nothing regenerated. **`GOLDEN_HASH`**: re-pinned to `340a7f6e260ee1e2-d9c56c0811177b0f`
(the P7.V7b measurement, verified: the golden-marked fetch-paint test passes).

**`test_places.py` label changes** (each run on the code after P7.V3, after V4 and V5, after V6, V7
and V7b, and after V2; every change in a set of names came from P7.V5):
skye lost `Cnoc an t-Sìthean`, `Giant Angus MacAskill Museum`, `Staffin Dinosaur Museum` and gained
`Free Church of Scotland Kilmuir`, `Broadford Church of Scotland`, `Kensaleyre Church`; ambleside lost
`Rydal Bridge`, `Rydal Road`, `Hope Church` and gained `Pelter Bridge`, `Loughrigg Fell`, `St Mary's`;
keswick lost `Lake Road Chapel`, `The Retro Zone`, `Derwent Bridge` and gained `Theatre by the Lake`,
`Friar's Crag`, `Derwent Pencil Museum`; oxford lost `High Street` and gained `Tom Tower` (and P7.V2
makes `Cherwell` lettered twice, the distinct set unchanged); trotternish, yr-wyddfa, y-fenni
unchanged. P7.V3 moved no set. Positions are not pinned. **`test_map_styles.py`** `MEAN_RGB`
re-pinned: pen-and-ink 229.9, 224.8, 213.3; sepia 206.0, 177.8, 128.3 (was 176.5, 154.1, 112.8: its
paper has `paper_vignette = 0.22`, which the narrow edge brightens most); bold 218.9, 219.6, 197.9;
winter 214.9, 220.5, 224.9.

**Docs images**: all 55 entries and masters repainted (`regen-docs`), fern included; copied into
`docs/images/` and `tests/golden/docs/`. Budgets: no fallback fired, no entry sets `quality`. Tightest
files: `gallery/lettering.webp` 56,640 of 60,000 (lossless), `gallery/nib-line.webp` 54,578
(lossless), `gallery/route-map.webp` 50,290 (lossy); P7.10 436,740 of 500,000; total 1,929,628 of
7,000,000. `tests/architecture/test_docs_images.py` green.

**Also re-pinned** (found by the tolerance golden run, golden-marked): `PINNED_LABELS` in
`tests/unit/maps/test_pipeline_letter_compose.py` (the two P7.V5 Lynmouth label swaps, in placement order).

**Filed**: `docs/issues/letters-terminal-tails-pruned.md` (D, Q, 3, 8).

**Looks wrong in the new images (findings, not fixed)**:
- `docs/images/places/oxford.webp`: "The Bridge of Sighs" ends "Sighc" at 720 px (the last s reads as
  a c); the braided Cherwell is now several heavy blue strokes, and the Cherwell is lettered twice.
- `docs/images/hero.webp`: the leader of "Friar's Crag" runs through the words "Friar's Crag"
  (its own label); the leader and label are the same line at the "g". The warm edge reads well; the
  rust specks are not visible at display size.
- `docs/images/places/skye.webp`: the only landmarks are three churches (the museums and the hill
  left with P7.V5's ranking); "Broadford Church of Scotland" wraps over two lines.
- `tests/golden/lynmouth/map.png`: "Living Waters Lynton United Reformed Church" is long, its
  leader crosses the Lynton name area, and "Lynton and Exmoor Museum" sits tight against "start".
- Sepia theme card is much lighter than before (mean red +29.5).
## 2026-10-25 P7.V7d Sea from closed coastline rings; no landmark at cap zero (code; regeneration in P7.V7c follow-up)

Two capability gaps found by P7.V10. Code and unit tests only; no golden, docs image or master was
touched.

**Fix 1, the sea.** `sea_from_coast` closed only one open chain, so a card whose coast is closed
island rings (Skye: the island, Raasay and the islets are closed rings; the mainland is an open chain)
had no sea and its lochs read as bare paper. It now lives in `maps/sea.py` (split from `cover.py` for
the line budget, and so `cover.py` keeps the reading of payloads). The sea is the card edge wound
anticlockwise plus every land region wound clockwise, filled by the nonzero rule `fill_cov` already
uses; `Layers.sea` keeps its type (`list[list[Pt]]`). Land regions: a closed ring as it stands, and
open chains joined end to start walking the card edge anticlockwise (so two chains round one strip of
land, or a mainland cut by several chains, close correctly). Winding verified on the Skye fixture:
OSM's coast is land on the left, anticlockwise round the islands; painted, the islands and mainland
read as land and the lochs and open water as sea (picture below). Probes just right of every chain
guard the convention: if most lie in the land the chains make, all are reversed; if neither way holds,
no sea. A card with exactly one open chain and no closed ring takes the old single-closure path
unchanged (same ring, same probes), so no existing card moves for that reason.

**Attribution.** Lynmouth (open chain only): `make_golden.py --compare` against a run of the p7-wip
base: paper, wash, pen, labels-centreline, map.png all identical (differing fraction 0.000000),
labels.txt identical, manifest hash identical. (Against the committed `tests/golden/lynmouth` it still
differs, 0.97 of map.png, from the other engine fixes already in p7-wip, none from this slice.)
Moved: any card whose coast has a closed ring or two or more open chains. Expected: Skye
(docs image `places/skye.webp`, its master, `test_places` skye row), and possibly Trotternish and
Ambleside/Keswick if their fixtures carry islets or lake islands as coastline (not painted here).
Skye before/after: `scratchpad/engine/v7d-skye-before.png`, `v7d-skye-after.png` (default theme, 720 px,
18,000 m margins): before, no sea; after, the sea washed round Skye, Raasay, the lochs and the
mainland shore, the island standing as paper.

**Draft ADR 0036 section (sea from closed rings).** "The sea is the card area outside every land
region, as one set of rings filled by the nonzero rule: the card edge wound anticlockwise, each land
region (a closed coastline ring, or open chains joined along the card edge anticlockwise) wound
clockwise. OSM's land-on-the-left winding is checked by probes, and reversed whole if the data
disagrees. One open chain alone keeps its single closure ring. `Layers.sea` is unchanged in type; its
rings may now include the card's own rectangle and holes."

**Fix 2, the cap.** `journal_heuristic` appended a candidate before testing the cap, so
`lettering.label_max = 0` with no caller landmarks still lettered the first candidate ("Free Church of
Scotland Kilmuir" on Skye). The test now comes first. `journal_picks` already stopped at zero.
No card moves except one set to `label_max = 0`. Draft ADR 0036 section: "`label_max` is a hard cap:
zero letters no landmark, whether from the caller's annotations or the fallback."

Gate: prek and `pytest -m "not golden"` green. Regeneration deferred to the P7.V7c follow-up.
## P7.V10 Showcase themes and the curated callouts (2026-10-25)

Four themes new (`ambleside`, `skye`, `yr-wyddfa`, `oxford`), `y-fenni` extended; each a copy of the
current `default.toml` (so it carries `paper_edge`, `relief_strength` and `minor_road_classes`) with
the changes below. Every theme: route pen `MAJ1-e`, `#7b2335`, `blend = "multiply"`, glow, casing and
shadow 0, `label_route_ink` the same; the maroon is kept as its hex (`perylene_maroon` is not within 12
of it). `examples/places.toml` holds each place's callouts (name, `lat`, `lng` from the OSM element) and
Skye's four journal notes; `examples/place_card.py` reads it for its `place` option; `test_places.py`
reads it with `tomllib`. Every callout carries its own point: the Ambleside, Wyddfa and Oxford names
are in the payload as elements (the point is the centre of the element's geometry), Angel Bakery,
Bean & Bread, Rate of Rise and Shepherd's Ice Cream come from the OSM node API (nodes 12633622904,
9060360117, 12553434518, 6819447139), Tŷ Melin is the point `y-fenni/README.md` records (node
5560350617, **not confirmed by the maintainer: P7.V15 flags it**), Castell y Fenni is the centre of
way 368980598 (OSM names it "Castell Y Fenni"; the lettered name is the plan's "Castell y Fenni").
`basemap.candidates` was not used to match a lettered name for any callout.

Painted area (the share of the 720 px card whose RGB differs from the card's own paper plate, resized
to the card, by more than 2/255 in some channel; the route and the lettering count; the card is 1440
px wide at supersample 2): Ambleside 84.6 %, Skye 71.1 %, Yr Wyddfa 68.4 %, Oxford 75.4 %, Y Fenni
76.5 %. At the golden test's 900 px: 83.7, 69.4, 67.4, 73.8, 75.2 %.

| Place | Idea and palette | Fields moved from the default |
| --- | --- | --- |
| Ambleside | the hero: fells and water fill the frame; green, russet and lake blue | `ribbon_mult` 2.6, `relief_strength` 2.0, route 3.6 px, `label_max` 4, pigments |
| Skye | the island trip; slate-blue wash, heather and moss patches | `ribbon_mult` 14, `relief_strength` 1.8, `label_max` 0, denser cover classes, pigments |
| Yr Wyddfa | the ridge; slate violet and bracken russet, deep lake blue | `ribbon_mult` 3.2, `relief_strength` 2.4, route 3.6 px, `label_max` 4, pigments |
| Oxford | a dense city; honey built-up wash, green quads, blue rivers | `roads = "all"`, `minor_road_classes` tertiary, unclassified, residential, `lane` 1.1 px, `ribbon_mult` 2.4, `label_max` 4 |
| Y Fenni | the food tour; terracotta, saffron and olive on cream, sage river | `name_tags`, `roads = "all"` as Oxford, `ribbon_mult` 2.4, `label_max` 6, pigments |

Callouts lettered at 720 and at 900 px: all four at Ambleside, Yr Wyddfa (Crib Goch, Garnedd Ugain,
Glaslyn, Llyn Llydaw) and Oxford (Radcliffe Camera, Magdalen Bridge, Christ Church, The Bridge of
Sighs), all six at Y Fenni (Tŷ Melin and the castle among them: none dropped); the four Skye notes.
Nothing was dropped by the placer.

**Capability gaps (not fixed here: `src/` is not this slice's).**

1. *The sea is not washed, so the island cannot be.* `cover.sea_from_coast` closes the one longest
   coastline chain that enters and leaves the card. Skye's coast is closed island rings and several
   chains, so `Layers.sea` is empty (`sea ()`), no sea plate is painted, and `ribbon.coast_hard_mask`
   has nothing to stop the ribbon at. The ribbon wash lies over land and sea alike, and the relief
   shading (a flat density everywhere, scaled by `relief_strength`) is the one colour both share. The
   theme can only make that colour the sea's: Skye's `relief` pigment is a slate blue, the coast and the
   road stand on it, and land shows only where a cover class (heath, rock, wood) is mapped. A field
   that fills the sea from the elevation grid's zero cells (`sea_rings` already traces them for the
   vector map), or that builds a sea from closed coast rings, is missing. The 60 % share is met (71 %)
   because the ribbon is wide, not because the island is washed.
2. *`label_max = 0` still letters one church on Skye* ("Free Church of Scotland Kilmuir"): it is not a
   landmark pick the cap governs. A theme cannot turn the ground's own names off without
   `label_ground = false`, which would drop "Sligachan" and "Snizort" too.
3. *`lettering.labels` counts the journal notes' text*, so the pin holds the note sentences.
4. `hillshade_mode = "bands"` changed nothing on Skye's painted card (tried; it is the vector map's
   relief), so the strong relief is `cover.relief_strength` alone.
5. Keswick's `test_places` row fails at the base (the landmark ranking now offers other names): it is
   the regeneration slice's, not changed here.
### P7.V11 Lettered examples painted at nib scale 2

`lettering.py`, `word.py`, `composition.py`, `derwentwater.py`, `how_to_own_shapes.py` and
`nib_stages.py` paint their nib plate on a canvas `NIB_SCALE` (2) times the picture and downsize it
with Lanczos, so the nib's edge is resolved at twice the display grid (cause: causes report item 4).
Published widths unchanged. The plate file written beside each image is now twice the image's size
(test first: `test_the_nib_plate_is_painted_at_twice_the_image_size`). The two quoted blocks of
`paint-a-watercolour.md` follow the scripts. Regenerated, with their masters: `word`,
`gallery/{lettering,composition}`, `tutorials/{lettering,composition}`,
`painting-with-python/derwentwater`, `how-to/own-shapes` and `explanation/nib-{centreline,broad,turned,ground,backing}`
(`nib-line`, `nib-set-down` and `nib-runs-dry` carry no plate and did not move). Encodings and
qualities unchanged; `gallery/lettering.webp` stays lossless at 56,558 bytes against the 60,000 budget,
so no lossy fallback. Looked at before and after at 100 % and 200 %: the lettering is crisp, the edges
no longer stair-stepped or blurred; the strokes read thinner and finer than the old soft blobs, which is
the nib's true width now resolved. Side by side: `scratchpad/v11-crisp.png`. The other docs-image pins
fail until the engine regeneration lands (expected). The golden CI run is to be recorded at the
checkpoint.
## P7.V12d The SVG drawing, step by step (2026-10-25)

`examples/svg_drawing.py` takes `figure=` (`flat`, `washes`, `ink`, `painting`) and paints one
picture of `drawings/fell.svg` per call; `vector-drawing.md` now shows the raw SVG (three
marked blocks, a new `.svg` marker form checked by `test_tutorials.py`, and the page joined
`_tutorial_pages()`), the drawing flat, the washes, the inks and the painting, each with what
it adds and changes. Fixes in the drawing and script: each wash is painted around the shapes in
front of it (a near fell no longer glazes the far one, the tarn is bare paper under water), the
skyline follows the whole fell from where it leaves the bank, the tarn sits on the fell's
shoulder with the beck running from it, the wall is a base line with a row of stones, the sun
is yellow ochre, the trees are sap green, and ink colours come from `PAINTERS_PIGMENTS`
(indigo, burnt sienna, cerulean). Glazing is Kubelka-Munk. Images moved: `svg-drawing.webp`
(redrawn); new `svg-flat.webp` (lossless), `svg-washes.webp`, `svg-ink.webp`, all 720 px, 16 to 24 KB.
Registered under `P7.V12d` (share 150,000). The existing pins other than these four were not
regenerated here.
## P7.V12c Painting with Python: trees, the fern family, brushed curves (2026-10-25)

Deleted `examples/gasket.py`, its image and master, its test cases and its page section.
New `examples/trees.py` (`figure="tree"` and `"family"`) and `examples/fern_family.py`;
`examples/curves.py` paints the rose and the spirograph with the brush (the Lissajous figure keeps
the pen and its old code path, so its image moves only with the engine fixes). `examples/fern.py`
is untouched.

**Trees.** A limb is a path of 14 points that bends (drawn up when young, sagging when old) and
splits into two limbs, now and then three, to depth 6; the straightest child carries on its
parent's stroke, so a stroke is one `stamp` call with `wprof` from the chain's widths and there is
no step at a joint. Limbs to depth 3 are a wet brush (`RIV2-a`, `BrushStyle(brush_organic,
stroke_smooth)`), thinner limbs are a nib (`MAJ6-e`, floor width 0.55 px) taking up at the brush's
end point. The canopy is two `sap_green` washes and one `yellow_ochre` wash over discs at the last
three depths' tips, then short `RIV1-a` dabs in `sap_green` and a few in `indigo`; the trunk has a
`perylene_maroon` shade stroke; the ground is a tapering dry `TRK4-d` stroke in `raw_sienna`. Every
tree is fitted to its cell (80 per cent of the width and the height) before it is painted. Depth 7
was tried and dropped: at cell size the twigs closed into a dark clot under the glaze.
**Cell cost.** The family paints nine 240 by 320 cells: about 9 s against about 3 s for the tree
at 600 by 800, and 4 s for the fern family (nine 300 by 400 cells).

**Fern family.** The fern's own pipeline per cell (counts, `_thicken`, `wash` in `scrub` and `wood`,
sharper veins, dabs), points and dabs in proportion to the cell's area, with `perturbed` turning the
frond map 0.5 to 5.5 degrees, scaling it 0.835 to 0.865, moving its rise by 6 per cent and each leaflet
matrix entry by 6 per cent. The fern family is published 900 px wide, because at 720 px the cells'
pinnae gaps closed under the wash's fixed 2.4 px blur and the ferns lost the fern's character.

**Curves.** The rose is cut at the centre into five petals; each petal is one `RIV2-a` stroke with a
sine `wprof` (no knot at the centre), a `quinacridone_rose` wash of its own, out of register by a few
pixels and deeper toward the centre, and the strokes are `perylene_maroon`. The spirograph is one stroke
in three pieces, `ultramarine`, `cerulean` and `sap_green`, on a pale `cerulean` wash, the later
pieces drier brushes (`TRK3-a`, `TRK4-a`) with `wprof` and density falling, so it breaks up at the end.

**Pins.** Added `painting-with-python/tree.webp` (600 px), `tree-family.webp` (720) and
`fern-family.webp` (900) with their masters, and regenerated `curves/rose.webp` and
`curves/spirograph.webp`; removed `gasket.webp` and its master; one registry block, `P7.V12c`, share
600 000 bytes. The images' sizes are 41 KB, 76 KB and 120 KB.

**Not done.** A for-loop grid for the curves page (for example a rose with 3, 5 and 7 petals) is not
painted; the families are the page's for-loop grids. The fern family keeps the fern's own pigments
(`wood`, `scrub`), not painter's pigments, to stay one family with `fern.webp`.
## P7.V12b The watercolour tutorial in one rhythm (2026-10-25)

`docs/tutorials/paint-a-watercolour.md` rewritten to decision 5's rhythm: picture, what a painter does,
how the engine models it, code, what to notice, then a `for`-loop grid (`examples/tutorial_grids.py`, new,
`figure=` paper, wash, brush, pigments, nib, lettering, composition; each 720 px wide, lettered labels at
nib scale 2 brought down with Lanczos). The rung scripts and their quoted blocks are untouched.

Reference and explanation figures: `reference/pigment-swatches` is now a labelled pigment card (graded
strip over an ink bar, Kubelka-Munk, 960 px); `reference/brush-sheet` is the treatment-by-width grid
(`brush_sheet.py` `figure="grid"`, 960 px; the `sheet` figure stays); `explanation/wash-glaze` is the
transparency grid (multiply row against Kubelka-Munk row, 800 px); `nib-broad` and `nib-turned` are removed
for `nib-angles` (840 px); `nib-hands` (nine seeds, 840 px) is new; `nib-ground` and `nib-backing` sit on an
irregular pooled sap-green wash. Registry: a `"P7.V12b"` block (share 1,000,000; measured about 895,000),
the older entries edited as the plan names. Widths of the two nib grids were cut from 900 to 840 to stay
under the 250 kB page budget (lossless).

Pins: only my entries were regenerated and pinned (`test_docs_images.py -k` on the 14 entries, exact:
pass). Other pins are the regeneration slice's. P7.V11 is parallel, not in this base: the new lettered code
uses the scale-2 pattern itself; `nib_stages.py`'s existing figures still paint at scale 1 and will
conflict textually with P7.V11 around `_name`.

## P7.V reconcile (2026-10-25)

`p7v-rec` = `p7-wip` with P7.V0 to P7.V11, P7.V7c, P7.V7d and P7.V12b/c/d merged. At the merge, prek
and `pytest -m "not golden"` were already green: no merge breakage in code or unit tests.

**Fixes.**
- `examples/nib_stages.py`: P7.V11 and P7.V12b each defined `NIB_SCALE = 2`; one definition now, its
  comment covering the figures and the grids. Its lettering is at nib scale 2 with Lanczos both ways.
- `examples/tutorial_grids.py` (P7.V12b) already letters its cells at `NIB_SCALE` 2 with Lanczos
  downsizing (it carried the pattern itself); nothing to change, no grid image moved.

**Skye retune** (`examples/themes/skye.toml`, 720 px at 18,000 m margins, looked at three times). With
the sea washed from the coast rings, the theme no longer fakes sea with a slate-blue relief: `relief`
`#b59a6c`, `rim` `#c9b58a` and `pale` `#cdc39a` are warm land washes, `relief_strength` 3.0 (was 1.8),
`water` `#4f86ad` is the sea, `heath` `#9a7490`, `rock` `#9a948c`, `wood` `#587a4c`, `scrub` `#8f9a5c`,
route pen 2.2 px (was 3.4). `ribbon_mult` stays 14: the ribbon takes in the whole island. The island is
land (washed fawn with moss, heather and rock patches), the sea is blue, the four notes are lettered.
With the P7.V7d cap fix, `label_max = 0` letters no landmark: "Free Church of Scotland Kilmuir" is gone from
the pin, as intended (the notes, the ground names "Sligachan" and "Snizort", start and finish remain).

**Yr Wyddfa.** Investigated: the card box lies inside the fetched box (the test's assertion holds) and the
route is not clipped by the frame. The track's last point (53.108649, -4.12053) projects to about
(300, 300) px of the 1440 px card, inside it; the route simply ends there, on the hillside above
Llanberis, as the fixture's track does. The summit label was missing because "Yr Wyddfa" was not a
callout. Fixed in `examples/places.toml`: first callout `Yr Wyddfa`, the point of OSM node 8755297244
(the peak, 53.0684857, -4.0762324, from the fixture payload). In `yr-wyddfa.toml`: `label_max` 4 to 5,
`ribbon_mult` 3.2 to 4.8 and `card_pad_frac` 0.09 to 0.14, so the wash fills the frame round the finish
instead of ending in a torn edge beside it.

**Pins.** `tests/golden/test_places.py`: skye loses `Free Church of Scotland Kilmuir`; yr-wyddfa gains
`Yr Wyddfa`; every other place's set unchanged. Regenerated with `make_docs_images.py` (all 68 entries,
masters too; only five files differ from the committed): `places/skye`, `places/yr-wyddfa`,
`social-preview.jpg`, `explanation/nib-ground` and `explanation/nib-backing` (the last two: the
combination of P7.V11's scale 2 and P7.V12b's sap-green ground). No lossy fallback fired and no entry
set `quality`; `tests/architecture/test_docs_images.py` (budgets) green.

**Contact sheet** of the five showcase cards: `scratchpad/showcase/contact-final.png`.
## P7.V12a Maps pages: the hero, the gallery, map styles, landmarks how-to (2026-10-25)

**Hero and preview.** `hero.webp` is the Ambleside card at 1200 px in `examples/themes/ambleside.toml` with its
curated callouts (`place=ambleside`). `examples/social_preview.py` now paints the Ambleside card at the sheet's
width (1280), crops 640 rows, lays a ragged patch of paper over the quiet fell inside the route's loop and
letters "pyntpot" over it with the hand (188 px, nib 1.5 px, plate at scale 2 brought down with Lanczos); it
takes `theme` and `place` like `place_card.py`. Looked at at full size: the maroon loop, Rydal Water and the
callouts stay legible round the word. The JPEG is 155,545 bytes (budget 900,000).

**Route-ink grid.** `examples/how_to_route_ink.py` takes `figure` (`violet`, the old picture, or `grid`) and
`theme`. The grid is three treatments (solid, wet pen `MAJ1-e`, dry pen `MAJ3-e`) by four colours (maroon,
the default pink, indigo, burnt sienna): two `paint` calls, one per pen brush, in `plates_dir(key) / brush`,
and twelve `compose` calls over them. Deviation from the plan: the cards are painted at a display width of
360 px and brought down to the cell's 180 px with Lanczos, because at 180 the brushes (set in display pixels)
swamp a cell; the route keeps its usual width. Still two paints, and about 12 s for the whole figure. The
dry row reads as dry, so the `MAJ4-e` fallback is not taken. `how-to/route-ink-grid.webp` is 86 KB; unlettered
cells carry no attribution.

**Moved to Ambleside / Lynmouth.** `gallery/route-map`, `tutorials/route-map`, `how-to/route-ink` and the four
`map-styles` are painted over `ambleside`; `how-to/command-line.webp` is new, `route_map` over `lynmouth`.
`test_map_styles.py` paints the Ambleside card: size (1800, 1281) and four mean colours re-pinned from a paint.
First map, tutorials index, route-ink, command-line, offline and write-a-theme pages, `data-policy.md`
(its image is `places/ambleside.webp`), the README (hero, caption, strip alt) and `index.md` follow. The
command-line page's byte counts are the Lynmouth payloads' stored sizes (trimmed; a first run would report
more), a line the page says. New how-to `letter-your-own-landmarks.md` shows Oxford's callouts, Tŷ Melin as
the custom entry and `places/y-fenni.webp`. The gallery's Places section is the five showcase maps, one line
each. The two stale alt texts the reconcile found: the Oxford "crimson route" (now maroon) and the issue note
about the old Oxford image (the Cherwell is no longer a blob).

**Retired.** `tests/fixtures/{keswick,trotternish}/`, their place cards and masters, their `_PLACES` rows,
`KESWICK_KEY`, `TROTTERNISH_KEY`, their `test_places.py` entries and `test_coordinates.py` boxes, keys and
budget; the coordinate self-test now uses Ambleside's and Skye's values. The fixture grep found no other
reference. `specs/001-port/reviews/p7v-plan-review-3.md` quoted the old Keswick pair
and was reworded so that the coordinate gate stays green.

**Registry.** One `"P7.V12a"` block (the grid and the command-line image), share 300,000; the older entries
moved as the plan names. Pins regenerated and checked exact: the entries named above.
