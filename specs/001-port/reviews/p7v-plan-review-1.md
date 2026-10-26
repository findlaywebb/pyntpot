# P7.V plan review 1

## Scope

I reviewed "#### P7.V. Revision round 1" in `specs/001-port/plan.md` on `p7-docs-release`
as it stands at `ef20569`. That includes the two amendments made while I was reviewing:
`c113fd6` (P7.V1b fetch margins, Skye at 6 km, Yr Wyddfa wider, route B decided) and
`ef20569` (P7.V7b, the paper edge and foxing restyle, and decision 13). I read it against:

- the rest of P7's conventions (the slice format, G-here, the script contract, the
  shared-file rules);
- `p7-research.md` sections 10 to 10.3;
- the five critique reports under `research/p7/critique/`;
- ADRs 0006, 0025, 0031 to 0033 and 0035;
- the source at this commit. There is no `src/` change since `60e4335`, so the plan's
  "at `60e4335`" citations hold or fail as they stand.

I made no edit beyond this file. I ran one scratch measurement (below), under the
session scratchpad.

## What I checked and found true

- **Code facts that hold:**
  - `Cache.ensure` is at `cache.py:210`, with `MARGIN_M` 1500 and `LANDCOVER_MARGIN_M`
    2600; `fetch` is at `pipeline.py:61` and takes no margin.
  - `rings_path(found.lakes)` is at `osm.py:178`, and `fill_cov` is nonzero
    (`ink/raster.py:128`).
  - `_place_flat` is at `placement_flat.py:136-184`, and `ROAD_CROSS_COST` is 90.
  - `RASTER_EM` is 128 (`skeleton.py:30`) and `FLANK_MIN` 0.40 (`trace.py:50`).
  - `pool` cuts at `span = int(r * 2)` (`deposit.py:168`).
  - `MINOR_ROADS` (`providers/overpass.py`) is exactly the five classes P7.V8 names.
  - Relief density is `clip(0.30 * (1 - shade), 0, 0.40)` (`painter/paper.py:47`).
  - `paper_plate` (`ink/paper.py:41-54`) has the worn decay `max(w * 0.012, 8)`, the
    vignette `w * 0.34` at 0.05, and foxing `noise(120, 2)` thresholded at 0.80 at 0.09.
- **The curated entry needs no new code.** `Annotations.landmarks` already takes a
  `Landmark` with its own `lat` and `lng` (`annotations.py`, `picks.journal_picks`), so
  Tŷ Melin needs no `src/` change.
- **P7.V6 does not reach the fern.** The fern dabs with `RIV1-a`, treatment row 1, pool
  0.0, and no `riv` override (`brush.py`, `brush_style.py:95-101`). `stamp` never calls
  `pool` for it.
- **The trim saves what the plan expects.** I ran the trim as P7.V1 specifies it in a
  scratch script: no `nodes` or `bounds`, tags cut to the grep's keys plus `name*`,
  minified.

  | Payload | Raw | Trimmed | Trimmed and simplified at 15 m |
  | --- | --- | --- | --- |
  | Oxford features | 4.50 MB | 2.18 MB (0.49) | not run |
  | Oxford land cover | 4.28 MB | 2.27 MB (0.53) | not run |
  | Yr Wyddfa features | 4.12 MB | 2.45 MB (0.59) | 0.52 MB (0.13) |
  | Yr Wyddfa land cover | 6.39 MB | 3.53 MB (0.55) | 0.83 MB (0.13) |

  At 0.13 of raw, a Skye payload near the causes report's whole-island counts fits the
  10 MB budget. The size risk is lower than it looked.
- **Decisions honoured:**
  - Keswick is no longer a map.
  - Tŷ Melin is hand-placed.
  - No town hall.
  - Route B.
  - The SVG steps.
  - The tutorial rhythm (with S10).
  - `default.toml` keeps its settings.

  Two exceptions are B1 (the fern) and S6 (the default look).

## Findings

### Blocker

**B1. Two slices break decision 3: the fern image is to stay byte-identical.**

- **P7.V7b.** It rewrites `ink/paper.paper_plate` with "every golden expected to move".
  `examples/fern.py:131-133` calls `paper_plate(sheet, canvas, PaperStyle(km_glazing=True,
  paper_foxing=0.03), w)`, so the fern's border and foxing change, and its pin moves.
- **P7.V11.** It doubles every registry entry's published width. The fern paints at
  `SIZE = 600` (`fern.py:78`) and is published at 600 (`docs_images.py:213`).
  `make_docs_images.py` never enlarges, so 1200 px means a repaint at `size=1200`. Grain,
  dab size and point density all scale, so it is a different image.
- **Decisions in tension:** decision 13 (restyle the paper in the library) and the
  maintainer's "the fern is the favourite image: keep it unchanged" (10, 10.1 item 4)
  cannot both hold as written. The plan has to choose; it should not leave the choice to
  the slice.
- **Fix, either:**
  - **(a)** `PaperStyle` gains one field, for example `paper_edge: Literal["grey",
    "warm"] = "grey"` (the old look). The new edge and specks sit behind `"warm"`.
    `default.toml` and every example except `fern.py` set `"warm"`. Name those scripts
    in P7.V7b's owners. Or
  - **(b)** put the question to the maintainer: "the fern's paper border and foxing
    change; its drawing does not".

  In both cases P7.V11 excludes `painting-with-python/fern.webp` by name. Its entry keeps
  width 600.

**B2. The fetch margins cannot show "the whole island", and the extra ground is clipped
anyway.**

- **The frame clips to the card.** The card is the track's bounds grown by the ribbon
  (at most `ribbon_max_m` 1250 times `card_grow_mult`) plus `card_pad_frac` of the longer
  side (`card_geometry._card_box`). `build_basemap` clips every layer to that card box
  (`layers.py:286-298`). Ground fetched beyond the card is never painted. P7.V1b says
  "the card frame is unchanged by the margins".
- **The planned loop stops short of the island's edges.** It runs Portree, Staffin, Uig,
  Dunvegan, Carbost, Glen Brittle and Sligachan, which puts its east edge at about
  Sligachan and Portree and its south edge at Glen Brittle. Six kilometres past that does
  not reach Broadford, Kyleakin or Sleat in the east and south, or Neist Point in the
  west. P7.V9a's claim that "the Sleat shores" are in the payload is false.
- **The cap does not help.** Even the 20 km cap leaves Kyleakin out, and a symmetric
  20 km margin fetches the Outer Hebrides' southern tip and Rùm instead.
- **Fix:**
  - **Make the route span the island.** Add the A87 from Sligachan through Broadford to
    Kyleakin, or the A851 to Armadale, and the B884 to Neist Point. Then size the margin
    to the card box.
  - **State the invariant: the card box lies inside the fetched box.** P7.V10's
    `card_pad_frac` and `card_grow_mult` must not outgrow the margin, and
    `test_places.py` asserts it for Skye and Yr Wyddfa.
  - **Correct the "Sleat" sentence.**
  - CONSIDER (C1) is the more durable form of the invariant.

**B3. Nothing that reads a fixture can find a non-default margin's payloads.**

- **Every consumer rebuilds the key with the default margin:**
  - `cli.py:76`;
  - `examples/place_card.py:77`, `map_styles.py:79`, `route_map.py:69` and
    `how_to_route_ink.py:70`;
  - `tests/support/golden.py:53`;
  - `test_places.py:138`, which asserts `cache.key(track, features, elevation) ==
    place.key`.

  Every `fetch` call takes the default too.
- **What follows:** after P7.V9a re-records `yr-wyddfa/` at 3000/4000 m, its files sit
  under a new key. `place_card.py` asks for the default key, so `Cache.ensure` calls the
  providers at `127.0.0.1:9`, and the call fails with `FetchError`. That reddens
  `places/yr-wyddfa.webp` and the Yr Wyddfa case of `test_places.py`. Skye has the same
  problem.
- **A collision in the key:** `Cache.key` hashes `margin_m` only (`cache.py:113-120`).
  Two recordings that differ only in the land cover margin would share a key and a file.
- **Fix:**
  - **The key.** `Cache.key(track, features, elevation, margin_m=MARGIN_M,
    landcover_margin_m=LANDCOVER_MARGIN_M)` adds `"landcover_margin_m"` to the canonical
    JSON only when it is not the default. That is the same omit-at-default rule as the
    digests, so the default key is byte-identical; pin it.
  - **`place_card.py`** takes `margin_m` and `landcover_margin_m` options, passed to both
    `fetch` and `cache.key`. The registry entries for Skye and Yr Wyddfa carry them.
  - **`test_places.py`'s `Place`** gains the two fields and passes them.
  - **The CLI.** `cli.py:76` passes its `--margin-m` through.
  - **Ownership.** P7.V1b owns the key change and `cli.py`. P7.V9a owns `place_card.py`'s
    options, the registry entries and `test_places.py`.

**B4. P7.V1 strips the keys P7.V5 ranks on, and P7.V5's fallback re-records Lynmouth.**

- **The keys are absent from `src/`.** `grep -rhoE` finds none of `wikidata`,
  `wikipedia`, `heritage`, `listed_status`, `shop`, `brand` or `brand:wikidata` under
  `src/pyntpot/maps`.
- **Lynmouth holds three of them.** Its payload has `wikidata` 24 times, `wikipedia` 11
  and `shop` 2. P7.V1 will drop all of them from every fixture.
- **What follows:** P7.V5 then "re-runs `record_fixture.py` for the affected place". For
  Lynmouth that fetches today's OSM, so every Lynmouth golden moves for reasons other
  than the fix. For the focus places it means a second network round.
- **Fix:** P7.V1's `KEPT_TAG_KEYS` is the grep's result plus those seven keys, named in
  the brief. Delete P7.V5's re-record branch. Also add `--include='*.py'` to the grep:
  it currently walks `__pycache__`.

**B5. Golden, docs-pin and test ownership has gaps at P7.V9a and P7.V10.**

- **P7.V9a's moved images.** It re-records `oxford/`, `y-fenni/` and `yr-wyddfa/`. Those
  fixtures paint `places/{oxford,y-fenni,yr-wyddfa}.webp` and their masters
  (`docs_images.py:317-347`), so all three pins move. P7.V9a owns neither the images,
  the masters nor the registry.
- **P7.V10's new themes.** P7.V10 adds four themes. `test_example_themes.py` pins
  `THEME_NAMES` and asserts that the directory holds exactly those themes (`:10`,
  `:28-33`), so it goes red. That file is not an owner.
- **P7.V10's Y Fenni change.** P7.V10 also extends `y-fenni.toml`, which moves
  `places/y-fenni.webp`.
- **Labels and pins across the engine chain.** The shared-file row gives
  `test_places.py`'s labels to P7.V5 and P7.V10 only. P7.V2 (the Cherwell), P7.V3 (label
  positions and drops), P7.V7 and P7.V7b can each move labels or pins, and none of them
  lists `test_places.py`.
- **Fix:**
  - P7.V9a and P7.V10 each own the docs images and masters they move, regenerated with
    `make_docs_images.py` for the named entries.
  - P7.V10 owns `test_example_themes.py`.
  - Every engine slice from P7.V2 to P7.V7b lists `test_places.py` (expected labels,
    rewritten from a run and recorded) as a possible owner. Widen the shared-file row to
    match.

**B6. P7.V7 names the wrong mechanism and the wrong owner files.**

- **Where the pen route is painted:** at paint time, by
  `painter/pen.py:paint_route_pen`, along `job.layers.route` (`pen.py:117`).
  `compose.route` only tints that plate (`compose.py:69-75`).
- **Where the strands come from:** `pipeline.paint`, after `paint_plates`, from
  `route_inks.ride.px` (`pipeline.py:121-127`). They do not exist when the pen plate is
  drawn.
- **The default already paints a pen route.** `default.toml:254-257` has `route_pen =
  true` with `MAJ6-e`. So "only cards with `route_pen = true`" is every default card,
  Lynmouth's `pen.webp` golden included.
- **What follows:** an agent limited to `compose.py` and `strands.py` cannot make this
  fix.
- **Fix:**
  - **Owners:** `painter/pen.py`, `painter/plates.py` if the strands are passed in,
    `pipeline.py` and `strands.py`.
  - **Mechanism:** the strands are computed from the route in render pixels before the
    pen plate is laid. The gap is `route_pen_width_px` when the pen draws the route, and
    `px` otherwise.
  - **Expected moves:** Lynmouth `pen.webp` and every card's pen plate. Composed images
    move only where the ride style is `"pen"`.

**B7. P7.V8b is not additive.**

- **The swatch sheet moves.** `examples/pigment_swatches.py:57,64` lays one swatch per
  `PIGMENTS` entry, so ten new keys move `reference/pigment-swatches.webp` and its
  master.
- **The reference test fails.** `test_reference_pages.py:197-199` requires every
  `PIGMENTS` key in `pigments.md`, which is not an owner.
- **The keys mean something else.** `PIGMENTS` is keyed by map role (`farmland`, `wood`,
  `water`, `relief`, ...), and `cover.pigments` names them. Mixing "ultramarine" into it
  confuses two concepts.
- **The docs-site palette moves.** P7.14's palette CSS is written from `PIGMENTS`, so it
  moves on `p7-docs-site`.
- **A naming slip:** the transparency table is `TRANSPARENCY`; "or wherever" is not
  needed.
- **Fix:** a separate public table, `PAINTERS_PIGMENTS` with `PAINTERS_TRANSPARENCY`
  (glossary term "painter's pigment"). `PIGMENTS`, its sheet, its page and the CSS stay
  byte-identical. `pigments.md` gains a section owned by P7.V8b, and the reference test
  gains a check for the new table.

**B8. P7.V8's digest rule does not fit `effect`, and two reference pages are missing.**

- **`blend` already exists.** `route_inks.<sport>.effect.blend = "normal"` is already in
  `default.toml` (`:266`, `:281`). `effect` is a `dict[str, Any]`.
- **The omit rule cannot reach it.** `DIGEST_OMITS_AT_DEFAULT` omits dataclass fields
  only (`style.py:222-230`).
- **`opacity` would move a pinned digest.** Writing `opacity = 1.0` into `default.toml`'s
  effect tables moves `Style.digest()`, which hashes `route_inks` and is pinned.
- **Two pages are missing.** `test_reference_pages.py:104-123` requires every CLI option
  in `cli.md` (P7.V1b adds `--margin-m`) and every style field in `style-fields.md`
  (P7.V8 adds two). Neither page is owned. P7.3b's run log records exactly this miss.
- **Fix:**
  - `blend` is read from the existing key.
  - `opacity` is read as `effect.get("opacity", 1.0)` and is not written into
    `default.toml`.
  - Only `minor_road_classes` and `relief_strength` go into `DIGEST_OMITS_AT_DEFAULT`.
  - Owners: `docs/reference/style-fields.md` for P7.V8, `docs/reference/cli.md` for
    P7.V1b.

**B9. P7.V11 as written will hit its own stops, and part of it does not exist.**

- **The `<img>` tags do not exist.** The pages embed 106 images in Markdown syntax and
  one `<img>`, so "width attributes only" has nothing to edit. Each embed would become an
  HTML `<img>` with its alt text.
- **The size budgets will fail.** A lossless lettering thumbnail is about 53 KB at
  360 px against the 60 KB `thumbnail` budget, and about four times that at 720 px.
  `docs/images/` is 1.8 MB against 7 MB, and two to four times that is at the limit.
  `KIND_BUDGET_BYTES` is a contract (ADR 0033), and the plan gives no new values.
- **The paint cost is large.** Maps would paint at 1440 px (place cards) and 2400 px
  (the hero). A Keswick card already takes about 59 s on first paint.
- **The cards are not the pixelation.** They already letter at render scale
  (`lettering/pipeline.py:237`, `card.render_scale`).
- **Three lettered scripts are missing from the owners.** `derwentwater.py:246` (the
  README's non-map image), `composition.py:117` and `how_to_own_shapes.py:138` letter at
  `NibSurface(..., 1.0, ...)`.
- **Fix:** cut P7.V11 to the cause the investigation found (causes item 4):
  - `NibSurface` scale 2 and a Lanczos downsize in every lettered example, named:
    `lettering`, `word`, `nib_stages`, `composition`, `derwentwater` and
    `how_to_own_shapes`;
  - lossless encoding for lettered figures;
  - published widths unchanged.

  If doubled widths are still wanted for line figures, list the entries, give the new
  `KIND_BUDGET_BYTES` and shares in the plan with an ADR 0033 amendment, and exclude the
  maps and the fern.

**B10. The P7.V12 group collides, and P7.V12a always stops.**

- **The gallery.** `docs/gallery.md` belongs to P7.V12a, but it shows `gasket.webp`,
  `wash-glaze`, `nib-broad`, `nib-turned`, `pigment-swatches` and `brush-sheet`
  (`gallery.md:71,129,135,163,177,181`). P7.V12b and P7.V12c delete or replace those
  images, so `test_docs_images.py`'s "every image shown is registered" check goes red in
  their worktrees.
- **The fractals index.** `docs/tutorials/painting-with-python/index.md` names the
  gasket, and no slice owns it.
- **A wrong path.** P7.V12b's `docs/tutorials/watercolour.md` does not exist; the page is
  `paint-a-watercolour.md`.
- **The README quick start.** If P7.V12b edits `wash.py`'s `main`, it breaks
  `test_readme.py`'s verbatim quick start, and the README belongs to P7.V12a.
- **The Keswick grep.** P7.V12a greps "both names" under `tests/`, `examples/` and
  `docs/` and stops on any hit outside its owners. "Keswick" is a lettering word in
  `test_hand.py`, `test_setting.py`, `property/test_hand.py`, `nib_stages.py`,
  `composition.py` and the explanation pages, so the slice always stops.
- **Files P7.V12a does not own:**
  - `tests/golden/test_map_styles.py`, which paints the Keswick card;
  - the entries that use the `keswick` fixture: the four map-styles images, the how-to
    route-ink image, the tutorial route-map rung, the gallery route-map, the hero and
    the social preview;
  - `places/keswick.webp` and `places/trotternish.webp` with their masters.

  The slice also names no replacement fixture for any of them.
- **Deferred owners.** "`docs/how-to/*.md` named in the slice" and P7.V12b's "named in
  the slice's first commit" defer ownership to parallel agents.
- **Fix:**
  - **The grep** looks for fixture references: `tests/fixtures/keswick`, `"keswick"`,
    `KESWICK_`, and the same for Trotternish.
  - **P7.V12a's owners** list those consumers, each with its new fixture: Ambleside for
    the hero, the gallery, the map styles and the social preview; Lynmouth for the
    command-line how-to.
  - **The gallery** follows the registry's rule: each P7.V12 slice owns its page's
    section of `gallery.md`.
  - **P7.V12b** owns `paint-a-watercolour.md` by its real path, and either leaves
    `wash.py`'s quoted lines alone or owns the README quick-start block.
  - **P7.V12c** owns the fractals index line.

**B11. P7.V9b's "margin band" does not exist, and its owner module is deferred.**

- **No such region.** Neither `card_geometry`, `lettering_furniture` nor the placers
  defines a margin band. The card is painted to its edges.
- **What follows:** P7.V9b must invent the region, its width and its interaction with
  the ribbon and the attribution. Its owner is "the lettering placement module ...
  named after the slice reads `lettering/`".
- **Fix:**
  - **Prescribe the band.** For example, the strip within `NOTE_BAND_FRAC` of the card
    edge (say 0.18 of the shorter side), outside the ribbon's core, never over the
    attribution box. Or drop the band: place notes through `_place_flat` as tier-0 flat
    blocks with leaders and a very high drop cost.
  - **Name the owners:** `annotations.py`, `lettering/picks.py`,
    `lettering/pipeline.py` and `lettering/placement_flat.py`.
  - **Add the gate:** `-m golden` exact with no golden moved, as P7.V8 has.

### Should fix

**S1. P7.V2: a wrong line cite, and the holes need an in-water rule.**

- **The cite.** The water branch is `osm_elements.py:283-286`; `:276-279` is the wood
  branch.
- **The holes become plain rings.** After `parse_path`, the holes are ordinary rings in
  `Layers.lakes`. `rivers._ring_at` (`rivers.py:73-78`) returns the first ring that
  contains the point. A hole ring would therefore put the island itself "in water".
- **Fix:**
  - **In water:** nonzero winding over all rings. Holes are wound clockwise by
    `rings_path`, and Sutherland-Hodgman (`rings.clip_ring`) and `simplify` keep the
    winding.
  - **Banks:** the nearest crossing of any ring on each ray.
  - **The vector layers.** `vector_layers.py:226` also takes `water_area`, so the vector
    export gains the holes. Add its test to the owners, or state that it moves.

**S2. P7.V3: the swap pass can undo the new cost.** `_seat_cost` and `_pair_cost`
(`placement.py:272-306`) re-score seats "on the same ground terms `_place_flat` scored".
Without the leader-crosses-box term there, `_swap_seats` can move a label back across.
Add `placement.py` (351 lines) to the owners and the term to `_seat_cost`.

**S3. P7.V5: two classes are unspecified.**

- **The castle.** `historic=castle` is in `MONUMENT_HISTORIC`, so it is class
  `monument`, tier 2. "Tier 1" needs a class: prescribe a `castle` rule ahead of
  `monument`, mapping to `building` (tier 1, 450 m).
- **The museum.** A `tourism=museum` is `attraction` (tier 1) through
  `TOURISM_DESTINATIONS`. Say that the unrecorded case is checked before that rule.

**S4. P7.V6's test misses the visible edge.**

- **The numbers.** Corners sit at `exp(-4)`, 1.8%. The visible square edge is the side
  midpoint, at `exp(-2)`, 13.5%. With `ceil(3r)` the side midpoint is still `exp(-4.5)`,
  1.1%.
- **Fix:** test the side midpoint below 1.5%, or make the span `ceil(3.5 * r)` (0.2%)
  and test below 1%.

**S5. P7.V7b's review cannot see what moved.**

- **Why everything moves.** `paper_plate` draws two fields from the sheet's generator,
  and later washes draw from the same one (`examples/wash.py:48-52`). `value_noise` draws
  in proportion to its lattice, so `noise(6.0, 1)` consumes far more than
  `noise(120, 2)`. Every later field in every example changes, so "away from the edge
  band, foxing only" will not hold, and the look-and-record step cannot attribute what
  moved.
- **Fix:**
  - Keep the two existing draws, in order and at the same scale.
  - Make the specks from an existing high-frequency field (`sheet.gran`), and modulate
    the edge with the existing `noise(26, 2)` field.
  - Update `paper.py`'s invariant.

**S6. Decisions 1 and 13 conflict as worded.** P7.V7b changes the default theme's look,
paper included. Reword decision 1 to "`default.toml`'s settings are unchanged; its paper
looks as decision 13 says", or follow B1(a).

**S7. ADR index and reference pages need shared-file rows.**

- **The ADR index.** `docs/decisions/README.md` is edited by P7.V1b, P7.V2, P7.V8,
  P7.V8b and P7.V9b, three of them in parallel. Rule: one row per ADR, keep both rows.
- **The reference pages.** `style-fields.md` and `pigments.md` (see B7 and B8) need rows
  too.

**S8. P7.V9a's tooling and confirmation gate are loose.**

- **The step.** `make_track.py` has a fixed `STEP_M = 20.0` (`:46`) and no option, so
  "resample at 100 m" needs `--step-m` and `make_track.py` as an owner.
- **Tŷ Melin's point.** Say where it is recorded: the fixture README, which is exempt
  from the coordinate gate.
- **The confirmation gate.** Say what P7.V10 does if the maintainer has not confirmed
  the point. Default: use it and flag it in P7.V15.
- **"One loop".** The Carbost and Glen Brittle roads are out-and-back spurs, and that is
  fine after P7.V7.

**S9. CI time is unbudgeted.**

- **The budget may already be spent.** P7's cap is 6 minutes over `a804fe3`. The run log
  already shows +4 (P7.3), +1 (P7.4) and about 4 minutes locally for map styles (P7.7).
- **The round adds more.** P7.V9a adds two cards, Skye's a large one, and P7.V11 adds
  more. P7.V11's "+4 over P7.4" is a second, conflicting budget.
- **Fix:** one budget, and a dispatched `golden.yml` run recorded after P7.V9a, P7.V7b,
  P7.V11 and P7.V12.

**S10. P7.V12b's grids do not cover every rung.** Decision 5 says every step ends with a
grid. P7.V12b lists five grids for seven rungs. Name the grid for "Stretch the paper"
and "Compose the sheet", or record that they have none.

**S11. P7.V10's callouts will be dropped in silence.**

- **The cap.** `label_max` defaults to 3 (`style_groups.py:233`), and `journal_picks`
  stops at the cap (`lettering/pipeline.py:149`). Ambleside, Yr Wyddfa and Oxford each
  have four callouts, so the fourth is dropped.
- **Missing candidates.** A name-only callout with no candidate is skipped without a
  word (`picks.journal_picks`). Lakes and Loughrigg Terrace are likely not candidates.
- **Fix:**
  - Each theme's `label_max` equals its callout count.
  - A callout carries `lat` and `lng`, inside its fixture box, wherever `landmarks.md`'s
    "Payload?" column says No.
  - Define "painted land" as a pixel whose RGB differs from the bare paper plate's by
    more than 2/255.

### Consider

- **C1. Derive the fetch margin from the frame.** `fetch` already takes `style`. When
  `margin_m=None`, the margin could be computed from `journal_geometry`: the card box's
  distance beyond the track box plus the ribbon. The explicit default stays 1500, so no
  key moves. That removes the frame-against-fetch drift behind B2, for every later theme.
- **C2. Skip work that is about to be thrown away.** P7.V1 re-trims `keswick/` and
  `trotternish/`, which P7.V12a deletes, and `oxford/` and `y-fenni/`, which P7.V9a
  re-records. Trimming only `lynmouth/` and `yr-wyddfa/` saves churn. P7.V9a still
  re-records Yr Wyddfa, but trimming it first proves byte-identity on a second large
  fixture.

## Verdict

**BLOCK.**

- **The decisions.** B1 breaks a decision the maintainer stated twice.
- **The Skye design.** B2 and B3 mean the Skye and Yr Wyddfa design cannot deliver its
  goal, and breaks consumers no slice owns.
- **The rest.** B4 to B11 are wrong mechanisms or missing owners that will turn a gate
  red, or force a stop, in a slice that cannot fix it.

Each blocker has a concrete fix above. Only B1 may need the maintainer (option b).
