# P7 plan review 3

## Scope

I reviewed `specs/001-port/plan.md` on `p7-docs-release` at `0b2c8b1`, the revision after
round 2. The parts I read:

- the section "### P7. Docs and first release";
- the ADR numbers table (rows 0024 and 0031 to 0035) and the paragraph under it;
- the P7 section of `specs/001-port/tasks.md`;
- rounds 1 and 2, `reviews/p7-plan-review-1.md` and `reviews/p7-plan-review-2.md`.

Settled, and not reopened here: every maintainer choice settled in rounds 1 and 2, all
five routes and the focus places, Keswick as the hero and tutorial fixture, and the
Y Fenni card lettering "Y Fenni" through a style setting with the default unchanged.

I made no edits beyond this file. I ran three things:

- the plan's dash gate (exit 1, so it passes today);
- a relative-link scan of `README.md` and `docs/**/*.md` (41 files, no broken link, so
  P7.12's offline lychee starts green);
- a scratch script that added a defaulted `name_tags` field to `BasemapStyle`, applied the
  plan's omit-at-default rule, and hashed the default style's basemap group.

## What I checked

**The P7.3b digest rule holds byte for byte.**

- `_group_digest` (`style.py:217`) hashes `json.dumps(asdict(group), sort_keys=True,
  default=str)`. If the default-valued key is dropped from that dict, the JSON text is
  the same as today's.
- The scratch run gave the basemap group digest `52ecda2b5685fa55` both before and after,
  and `base_digest()` stayed `e5a5f1b4b3ca2177`.
- `Cache.base_key` (`cache.py:181`) is `sha256(basemap.canonical())` plus `-` plus
  `base_digest()`. `Basemap.canonical` (`basemap.py:198`) is the card and `asdict` of the
  layers, with no style options in it. Under the default tags the layers' names are
  unchanged, so `plates.json`'s `340a7f6e260ee1e2-e5a5f1b4b3ca2177` holds.
- Every file that pins one of the three digests keeps it: `test_style.py:73-75`,
  `test_pipeline_fetch_paint.py`, `plates.json`, and ADRs 0005, 0006 and 0025.

**Where the names are read.**

- Every OSM name the card letters goes through `osm_elements`. Settlements and landmarks
  take `"n"` from `_candidate` and then `rank_landmarks` into `Basemap.candidates`, which
  `picks.py` and `picks_settlements.py` read. Roads, rivers and the coast take their `n`
  from the same module.
- `layers.py:154` reads `place.get("name")`, but those are the caller's places, not OSM
  data. Leaving `layers.py` alone is right.
- `candidates/places.py` and `roads.py` are reached only from `candidate_export`
  (`maps/__init__.py:16`).
- The feature query ends in `out geom`, so all tags come back, `name:cy` among them.

**The style tests.**

- `test_style_groups.py` has the `BasemapStyle` row of `PINNED` (`:204-232`) and
  `BASEMAP_DEFAULTS` (`:261-289`), which is checked field by field, by value and by type.
  `("name",)` is a `tuple`, so the type check passes.
- `SOURCED` does not include `BasemapStyle`, so no provenance digest moves.
- `test_basemap_is_the_effective_options` builds `BasemapStyle()` on both sides, so it
  stays green.

**The gallery table against the rungs' real sizes.**

- `test_ink_examples.py` and `test_letters_examples.py` pin these sizes: paper, wash,
  brush_stroke, nib_line and lettering at 360 by 240, pigments at 720 by 240, and
  composition at 480 by 320. `route_map` writes the 900 px card.
- No width in the table is larger than its source, so nothing is enlarged.
- Scaled from round 2's measurements, the estimates are:
  - nib_line, lossless at 320 px: about 47 KB;
  - lettering, lossless at 360 px: 53 KB;
  - the map, lossy at 720 px: 49 KB on Lynmouth;
  - the lossy rungs: under 10 KB.
- All are under the 60 KB thumbnail budget. Keswick may be denser than Lynmouth, and
  the stop rule ("lossy already, so a smaller width") covers that.

**The script contract against the code.**

- `route_map.main(out_dir, *, track: Path, cache_dir, features, elevation)` matches the
  contract.
- `test_route_map_example.py` copies the fixture and builds both providers at
  `127.0.0.1:9` with `budget=0`, as the contract says.
- `run_example` passes `**options` through. The existing rungs take `main(out_dir)`
  only, and their gallery entries carry no options, so the call works.

**G-here.** P7 now cites the plan-wide G-here at `plan.md:558-559`, under "P3 and P4: how
to run a slice" (`:350`). P7.R's `publish.yml` writes its gate commands out and runs the
goldens only under `--golden-tolerance`.

## Round-2 findings

| Finding | Status | Why |
| --- | --- | --- |
| B1 P7.3b group and digests | Resolved | The field is in `BasemapStyle` and reaches every read site through `scope.options`. The `DIGEST_OMITS_AT_DEFAULT` rule is in `style.py`, ADR 0035 amends 0005, the owners are added, the candidate export is scoped out, and `test_osm_elements.py` is marked new. I verified the digest claim by running it. One owner is missing (S1 below). |
| B2 script contract | Resolved | `track` is the GPX `Path`, and `theme: str \| None` is added. `place_card.py` paints the Y Fenni card with the theme. `test_places.py` calls `fetch`, `paint` and `letter` directly. |
| S1 README link rule | Resolved | Only images and links into the repo must be absolute repo URLs. Badges and links to other sites are allowed. |
| S2 G-here and publish | Resolved | It cites the plan-wide gate. `publish.yml`'s commands are written out, with tolerance-only goldens. |
| S3 P7.11 and P7.12 sharing files | Resolved | Both are sequenced before P7.3. There is a shared-files row for `pyproject.toml`, `uv.lock` and `ci.yml` with the re-lock rule. P7.12 adds `workflow_dispatch`. The predecessor lines lag the diagram (m1). |
| S4 budgets and encodings | Resolved | There is a per-entry gallery table, an over-budget stop rule, lossy swatch sheets, and the brush ids as a literal tuple checked against the private tables. |
| S5 budget remedy | Resolved | An over-budget fixture stops and reports, and if Keswick parks the slices after it stop. |
| S6 route tooling | Resolved | `--list-ways`, `--start-node`, `--via-node`, `--end-node` and `--length-km` are added, and the box goes on the command line only. One wrinkle is in m6. |
| S7 existing `place` callers | Resolved | They pass `lambda name, size, tracking: flat_measure(name, size)`. |
| S8 | Resolved | It was folded into B2. |
| S9 group bound | Resolved | The bound sentence is under the shared-files table. P7.8 to P7.10 have gates and done lines, and P7.10 has a test-first. P7.7 still has no done line (m5). |
| S10 one image per call | Resolved | `main` returns one path, and the other files a script writes are ignored. |
| m1 to m6 | Resolved | These are the step-3 `git status` check, the one-box pairing, the D26 and river readings, `docs/README.md` linking no missing page, the four files, and the split target `test_placement_windows.py`. |

## Findings

No blocker. Each item below is a local fix the implementing slice can make without a
decision. Where a choice exists, I name the default to take.

### Should fix (fold into the slice)

**S1. P7.3b: a seventh test file pins `BasemapStyle`'s fields and is not an owner.**

- **The test:** `tests/unit/maps/candidates/test_export.py:88-120`
  (`test_the_candidate_basemap_is_the_old_candidate_options`) asserts that
  `dataclasses.asdict(CANDIDATE_BASEMAP)` equals a literal dict of all 27 fields.
  `CANDIDATE_BASEMAP` is `replace(BasemapStyle(), ...)` (`candidates/export.py:39`).
- **What follows:** adding `name_tags` turns it red.
- **Fix:** add the file to P7.3b's owners, with the entry `"name_tags": ("name",)` written
  by hand. The export's semantics do not change, because it runs `osm_elements` under the
  default tags.

**S2. P7.13's hero at 1200 px contradicts "downsizes to `width` and never enlarges".**

- **The conflict:** the revision made the hero "the Keswick card at 1200 px". The card's
  display width is `CardStyle.display_px`, 900 in the default theme
  (`test_style.py:37`). `make_docs_images.py` never enlarges, and the contract gives a map
  script no way to set the card's size.
- **What follows:** the agent either registers a 1200 px entry it cannot produce, or
  invents an option ad hoc.
- **Fix:** `place_card.py` takes `size: int = 900`, applied as
  `style.model_copy(update={"card": replace(style.card, display_px=size)})`, and the hero
  entry passes `size=1200`. This is the same `size=` the contract already gives non-golden
  tests. The other choice is to make the hero 900 px.

**S3. The shares sum to 7.1 MB against a 7 MB total.**

- **The sum:** 0.5 + 0.5 + 3 × 0.4 + 0.6 + 0.3 + 0.5 + 0.5 + 2.8 + 0.2 = 7.1.
- **What follows:** every slice can pass its own share while the total test fails.
- **Fix:** make the total 7.1 MB, or P7.13's share 2.7 MB.

**S4. "A tag name is a token (ADR 0026)" misreads 0026.**

- **What 0026 says:** "an OSM tag key or value ... is data, not a token". Its member rule
  also makes a member of a class in no `__all__` free to change, and `BasemapStyle` is in
  no `__all__`; only `Style` is.
- **What follows:** ADR 0035 would assert a public commitment that contradicts 0026.
- **Fix:** replace the sentence with "the tag names are OSM data (ADR 0026); the field is
  documented as a theme key".

### Minor (notes for the implementer)

- **m1. The predecessor lines lag the order diagram.** P7.3 says "Predecessor: P7.2" and
  P7.4 says "P7.3". The diagram and `tasks.md` run P7.2, P7.11, P7.12, P7.3, P7.3b, then
  P7.4. Follow the diagram.
- **m2. The P7.0 line and the ADR table.**
  - The P7.0 line says "0031 to 0034 added"; 0035 was added too.
  - Row 0035 lacks "(amends 0005)", which rows 0032 to 0034 carry for their amendments.
- **m3. `default.toml` and `name_tags`.** Adding `name_tags = ["name"]` to the `[basemap]`
  table is harmless, because a default value is omitted from the digest, and
  `test_cli.py`'s text replace is unaffected. It also keeps `default.toml` a full theme,
  which P7.7's themes and `y-fenni.toml` are copied from. Prefer adding it over the
  owner entry's "unchanged".
- **m4. Check that the town is lettered at all.** Before P7.3b pins "Y Fenni", check
  that P7.3's recorded Y Fenni label list holds "Abergavenny". If the default lettering
  does not letter the town, stop and report rather than tune the lettering.
- **m5. P7.7 has no "Done:" line and no test-first.** Take "the theme-load test red
  before the themes exist" as its test-first, and "Done: both new tests green" as its
  done line.
- **m6. The Pen-y-Pass car park may be mapped as a way, not a node.** If so,
  `--start-node` takes a node of its outline. The 150 m tolerance covers that.
- **m7. `placement.py`'s line budget.** The file is 351 lines before P7.1's two fixes.
  If it passes 400, split it along responsibility lines, as with `test_placement.py`.

## Verdict

**PASS.** Both round-2 blockers and all ten should-fix items are resolved, and the new
repo facts hold. In particular, the default-omitting digest keeps `BASE_DIGEST`, the
manifest hash and every golden byte-identical, which I verified by running it. Fold
S1 to S4 into P7.3b, P7.4 and P7.13 as they run. None of them needs a maintainer
decision.
