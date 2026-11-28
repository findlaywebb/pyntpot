# 008a plan review

Reviewer: fresh-context plan reviewer. Checked on `b999946` (branch `work-008a`), with 008 and
009 merged. I measured the numbers below by running `journal_geometry` against every packaged
and example theme, and by timing one themed card paint. I wrote no coordinates outside the
Lynmouth box: this file is scanned by `test_coordinates.py` too.

## Verdict: BLOCK

The idea is sound: a synthetic fixture inside a real box, a committed generator, one example
script, a mean-RGB golden over every theme, and docs images through the existing registry.
**The single most important change is the card frame.** The card is not the fetch box. The
painter frames it from the track (`card_geometry.py:26-43`), growing the track's box by
1.55 x the fitted ribbon, padding it by 9 % and widening it to an aspect of at least 1.12.
For the plan's 2.4 x 3.0 km track that card is **6.2 x 5.55 km**. It is wider than the
Lynmouth box (5.58 km east to west) and well outside the plan's 4.0 x 4.6 km fetch box and
its 3 km feature square. The 800 m margins in P0 item 4 make this worse. The card would
paint bare paper down both sides. The coast would stop short of the card edge, so
`sea_from_coast` would drop it and paint no sea. At 600 px the lanes would not be painted at
all. Eight more findings would make an agent fail a gate or guess, each with a fix below.

## Answers to the questions in the brief

1. **Does P0 item 4 (800 m margins) keep the whole painted card inside the Lynmouth box? No.**
   The arithmetic for the fetch box is right: track plus 800 m is 4.0 x 4.6 km, inside the
   box. But nothing is painted from the fetch box. `build_basemap` clips every layer to
   `geometry["card"]` (`layers.py:285-287`), and `journal_geometry` sizes that card from the
   track alone (`card_geometry.py:66-75`). Measured with `Style()` at 600 px for a 2.4 x 3.0 km
   track centred on (51.225, -3.84): the card is 6,217 x 5,551 m. That is about 300 m past the
   Lynmouth box's west and east edges, and 1.1 km past the fetch box on each side. Yr Wyddfa's
   theme (`card_pad_frac: 0.14`) frames 6,743 x 6,021 m. The frame the plan assumes, "a 3 km
   square", is less than half the card's width. See finding 1.
2. **Payload tags the real loaders read.** I verified each one. The full table is in finding 5.
   - Sea: none as a tag. The painted sea is built from `natural=coastline` ways in the
     **features** payload (`cover.py:174-198`, `sea.py`).
   - Lake with island: a `natural=water` relation with `outer` and `inner` members
     (`osm_elements.py:315-320`, `polygon_rings` `:140-153`).
   - River split: two `waterway=river` ways that share the same `name`. A river is always kept
     (`osm_elements.py:276-281`).
   - Stream: `waterway=stream`. It is kept only if the track interacts with it under the
     default `rivers="key"`, and it is dropped as a stub if it ends on nothing
     (`basemap_strokes.py:291-295`).
   - Major road: `highway` in `primary|secondary|trunk|motorway` (`overpass.py:59`).
   - Minor road: `MINOR_ROADS` (`overpass.py:61`). It is kept only if the track interacts with
     it under the default `roads="key"` (`osm_elements.py:251-258`).
   - Cover, in the **land cover** payload (`cover.py:46-87`): `landuse=meadow`, `natural=heath`,
     `landuse=residential` (built), `natural=bare_rock`. Wood is `landuse=forest` or
     `natural=wood` in the **features** payload (`cover.py:150-166`).
   - Settlement: a `place=village|town|hamlet` node (`picks_settlements.py:22,143`).
   - Landmark: a node whose `classify` class is offered, such as `man_made=lighthouse`
     (`overpass.py:74-85`).
3. **Sea from a coastline.** `coastline_chains` cuts each `natural=coastline` way at the
   **card** edge, joins the pieces and drops chains of 300 m or less (`cover.py:35,174-198`).
   `sea_from_coast` keeps an open chain only if both ends lie on the card edge, and a closed
   ring is an island. Land is on the left of the way's direction, and a wrong winding is
   repaired by probes (`sea.py:1-19`). So the coast way must run **past every theme's card
   edge**, and the offshore island must be a closed ring longer than 300 m.
   `VectorLayers.sea` is a different sea: it is traced from the elevation grid at 0 m
   (`relief_layers.py:183`, `contours.py:195-225`). With the plan's 20 m floor it is empty.
4. **Can the cache key be computed as described?** Yes, mechanically. `Cache(dir,
   margins).key(track, OverpassFeatures("t"), OpenTopoData("t"))` works, because the provider
   ids are constants (`overpass.py:192`, `opentopodata.py:91`) and do not depend on the
   contact or the endpoint. But the plan contradicts itself: P1 step 2 says "with the
   library's default margins", and P0 item 4 says 800 m. With 800 m, the key carries
   `landcover_margin_m` (`cache.py:146-147`). And the key must come from the track **as read
   back from the written GPX**, which is rounded (`cache.py:139-141` rounds the box to six
   places). See finding 6.
5. **Will the docs registration and the captions test accept the plan's entries?** Not as
   written.
   - The runner passes `features=` and `elevation=` to every fixture script
     (`make_docs_images.py:45-52`), so the P0 item 6 signature raises `TypeError` (finding 2).
   - `docs_images.py` needs three edits, not two (finding 8).
   - The plan's sample caption has no backticks, so `_PAINTED_BY` (`test_captions.py:23`) does
     not see it as a caption at all.
6. **Golden pattern and mean-RGB pinning.** Copying `test_map_styles.py` is right: copy the
   fixture to `tmp_path`, use budget-0 providers, pin mean RGB as literals within 1.5. Three
   parts are wrong:
   - A 600 px card is a **1200 px** PNG, because `CARD_SIZE` is `(1800, 1281)` at 900
     (`test_map_styles.py:22`).
   - The script's `main` returns only a path, so the test cannot read the placed labels.
   - Parametrizing over `Style.themes()` instead of the pinned dict's keys makes a new theme a
     `KeyError`, not a clear failure.

   See findings 7 and 9.
7. **Under-specified.** These are left for the agent to guess:
   - the track's shape and size
   - where each feature lies
   - tags, names and element ids
   - the `min_patch_px` threshold (the default is 0, so the test is vacuous)
   - the "doubles back" predicate (vacuous as written)
   - the journal note's point
   - the docs entries' width, kind, encoding and options
   - where the `default` image goes in a section that has no subsection for it

## Findings

### 1. [BLOCKING] The card frame is not the fetch box: the planned card leaves the box, outruns its data, loses its sea and drops its lanes

- **Plan:** P0 item 4 (800 m margins, track at most 2.4 x 3.0 km); P1 step 2 ("features in card
  metres on a 3 km square").
- **Evidence.** Measured with `journal_geometry` on a box track, `display_px=600`:

  | Track box | Theme | Card (m) | m per display px | Lanes painted |
  | --- | --- | --- | --- | --- |
  | 2.4 x 3.0 km | default (and 9 others) | 6,217 x 5,551 | 10.36 | no |
  | 2.4 x 3.0 km | yr-wyddfa | 6,743 x 6,021 | 11.24 | no |
  | 1.5 x 1.6 km | default (and 9 others) | 3,934 x 3,512 | 6.56 | yes |
  | 1.5 x 1.6 km | y-fenni (smallest) | 2,733 x 2,440 | 4.56 | yes |
  | 1.5 x 1.6 km | yr-wyddfa (largest) | 4,267 x 3,810 | 7.11 | yes |

  - Lanes are painted only below `minor_roads_mppd = 8.0` m per display px
    (`card_geometry.py:96`, `brush_style.py:176`). At the plan's size, the spec's "minor roads"
    criterion fails on ten of the twelve themes.
  - The Lynmouth box is 5.58 km east to west, so no track of the planned size can have its
    card inside it.
  - The card's width varies 1.6x across the themes, because `y-fenni.yaml` and `yr-wyddfa.yaml`
    override `ribbon_k`, `ribbon_c`, `ribbon_min_m`, `card_grow_mult` and `card_pad_frac`. So
    "inside the card" means different ground for different themes.
  - The fetch margins only name the key and the elevation grid's box. The generator writes
    whatever it likes into the payloads.
- **Fix (prescribe exactly):**
  - **Track:** its box is 1.5 km east to west by 1.6 km north to south, each within 50 m,
    centred on (51.225, -3.84).
  - **Margins: the library's defaults** (`Cache(dir)`, `FetchMargins()`). Drop
    `PREVIEW_MARGINS` and `PREVIEW_MARGIN_M` from the plan.
    - The features fetch box, `track.bounding_box(MARGIN_M)`, is then 4.5 x 4.6 km. It lies
      inside the Lynmouth box and contains every theme's card, with at least 116 m to spare
      east to west and 395 m north to south.
    - The nominal land cover box (2,600 m) is never written anywhere: the land cover payload
      has no box field. The generator simply writes land cover only inside the features box,
      and the README says so.
    - This also makes P0 item 6's margin plumbing, and the key contradiction in finding 6,
      go away.
  - **Data region:**
    - Every element lies inside the features fetch box, rounded inward by 1 m.
    - The coast, the major road, the river and the minor road run to that box's edge, so each
      crosses every theme's card edge.
    - Every feature the spec lists lies within **350 m of the track's box**, so it is inside
      the smallest (y-fenni) card as well as the largest.
  - **Proof in `test_make_preview.py`**, non-golden: for every theme in the golden's
    `MEAN_RGB` keys, `fetch` with budget-0 providers on a copy of the fixture, then assert:
    - `basemap.card.box` lies inside the projected features fetch box. This is the
      `test_places.py:216-221` pattern.
    - The fetch box lies inside `BOXES["preview"]`.
    - `basemap.layers.minor_roads` is true for every theme but `ambleside-hero`, whose
      `minor_roads_mppd: 2.0` drops lanes by design.

### 2. [BLOCKING] The example's signature breaks the docs runner, and P0 and P2 disagree on it

- **Plan:** P0 item 6, `main(out_dir, *, track, cache_dir, theme=None)`, with the providers
  built inside. P2 step 1, `main(theme=..., out=...)`. P2 step 2, "no branching on the value".
- **Evidence:** `make_docs_images.py:45-52` and the pin test pass `track`, `cache_dir`,
  `features` and `elevation` to every fixture script. The registry contract says so too
  (`docs_images.py:15-22`). A `main` without `features` and `elevation` raises `TypeError`.
  `theme=None` forces a branch, which P2 forbids. `run_example` returns only the path
  (`support/examples.py:50-54`), so the golden test cannot read the placed labels from `main`.
- **Fix:**
  - The example exposes
    `preview(style: Style, *, track: Path, cache_dir: Path, features: OverpassFeatures,
    elevation: OpenTopoData) -> tuple[Image.Image, Lettering]`, and
    `main(out_dir: Path, *, track: Path, cache_dir: Path, features: OverpassFeatures,
    elevation: OpenTopoData, theme: str = "default") -> Path`.
  - `main` always calls `Style.from_theme(theme, relative_to=REPO_ROOT)`, copies the style
    with `card.display_px = 600` as `place_card.py` does, calls `preview`, and saves
    `out_dir / "preview.png"`.
  - The `__main__` block takes `--theme` and `out_dir`. It copies `REPO_ROOT / "tests" /
    "fixtures" / "preview"` into a `tempfile.TemporaryDirectory()` and builds both providers
    with `budget=0` at `http://127.0.0.1:9`, as `test_map_styles.py:44-45` does.
  - The annotations are module constants built in `preview`:
    - `Landmark(name="Foreland Point")`, with no coordinates. It is looked up by name among
      the candidates (`annotations.py:36-44`).
    - `JournalNote(text="High tide at Lynmouth", lat=route.lat[i], lng=route.lng[i])`, where
      `i = NOTE_POINT` is a named index constant that the generator's README records as the
      riverside stretch. No coordinate literal appears in the example.
  - The golden test calls `load_example("theme_preview", "example_theme_preview")["preview"]`.
  - `tests/architecture/test_examples.py` needs no edit: it pins only the rung scripts
    (`:18-27`).

### 3. [BLOCKING] The fixture test reads `vector_layers`, which has no land cover, a different sea and a different clip

- **Plan:** P1 step 1 says the payloads "load through `vector_layers` with `Style()` and the
  layers hold ... sea, ... each of the five cover classes, a cover patch smaller than
  `min_patch_px`".
- **Evidence:**
  - `VectorLayers` has no land cover classes at all (`vector_layer_build.py:213-236`).
  - Its `sea` is the elevation-traced sea (`relief_layers.py:183`), which the 20 m floor
    leaves empty.
  - Its clip is the track box plus 900 m times the box's scale, not the card
    (`vector_layer_build.py:16`, `layers.py:199-200`).
  - The painter's river classes are `major`, `medium` and `minor`, not `river` and `stream`
    (`basemap_strokes.py:283`).
- **Fix:** run the presence test on the painted basemap: `fetch(...)` with `Style()` on a copy,
  through budget-0 providers. Assert:
  - `layers.sea` is non-empty.
  - `layers.coastline` holds one open chain and one closed ring.
  - `layers.lakes` holds a ring with another inside it, checked with `point_in_ring` and
    opposite `signed_area` (`rings.py`).
  - `{"wood", "meadow", "heath", "built", "rock"} <= layers.cover.keys()`.
  - `layers.roads` has both `cls == "major"` and `cls == "minor"`.
  - `layers.rivers` has two chains named `East Lyn River` (the split) and one `cls == "minor"`
    stream.
  - `basemap.candidates`, or the payload, holds the settlement and `Foreland Point`.

  Run the per-theme frame checks of finding 1 in the same file.

### 4. [BLOCKING] "Smaller than `min_patch_px` at 900 px" has no threshold: the default is 0

- **Evidence:** `CoverStyle.min_patch_px` defaults to `0.0`, which keeps every patch
  (`style_groups.py:128-130,155`). The only theme that sets it is `ambleside-hero.yaml`, at
  400. It is an area in display px squared (`painter/cover.py:108`). As written the predicate
  is unsatisfiable, or vacuous, depending on how the agent reads it.
- **Fix:** name the threshold as **400 display px squared at a 900 px display width**
  (`ambleside-hero`'s value).
  - Prescribe at least two small patches, one `meadow` and one `heath`, each a 50 x 50 m
    square (2,500 m squared). That is under 400 px squared at 900 px on every theme's card:
    the smallest, y-fenni's, is 3.04 m per px at 900, and 400 px squared is 3,690 m squared
    there.
  - Each patch sits against a larger patch of another class, so the fold has a neighbour to
    take.
  - The test computes `area_m2 / mpp_display(900) ** 2 < 400` from the basemap fetched with
    `display_px=900`, not from a literal.

### 5. [BLOCKING] No element table: tags, names, ids, directions and the keep rules are left to guess

- **Evidence:**
  - Without the track interacting with them, the default style drops minor roads and streams
    (`osm_elements.py:251-258,276-281`; `interaction_m=60`, `interaction_run_m=100`,
    `style_groups.py:280-281`).
  - A stream that ends on nothing is dropped as a stub (`basemap_strokes.py:291-295`).
  - Unnamed roads and streams are keyed by `entry["id"]` (`osm_elements.py:221,269`), so a
    missing or repeated id merges ways silently.
  - Coast chains of 300 m or less are dropped (`cover.py:35`).
  - A hamlet scores under the settlement floor unless it is near the route
    (`picks_settlements.py:29,128-143`).
  - The golden label list depends on every one of these choices.
- **Fix:** put this table in the plan. The generator writes it into `README.md`, and the test
  asserts it.

  | Feature | Payload | Element and tags | Name | Placement rule |
  | --- | --- | --- | --- | --- |
  | Coast | features | way, `natural=coastline`, drawn east to west (land on its left, to the south) | none | crosses the fetch box from its west edge to its east edge, north of the track, at least 300 m off it |
  | Offshore island | features | closed way, `natural=coastline`, anticlockwise, perimeter of at least 600 m | none | wholly in the smallest card, in the sea |
  | Lake | features | relation, `natural=water`, one `outer` and one `inner` member, each with `geometry` | none | wholly in the smallest card, at least 300 m across |
  | River | features | two ways, `waterway=river`, that part and rejoin round the gravel bar, sharing end vertices | `East Lyn River` | runs from the fetch box's south edge into the sea |
  | Gravel bar | land cover | way, `natural=shingle` | none | between the two branches |
  | Stream | features | way, `waterway=stream`, last vertex identical to a river vertex | `West Lyn River` | crossed by the track once |
  | Major road | features | way, `highway=primary` | none, and no `ref` | crosses the river by a bridge-less crossing and crosses the minor road |
  | Minor road | features | way, `highway=unclassified` | none | crosses the river; the track runs along it for at least 300 m within 20 m |
  | Wood | features | way, `natural=wood` | none | one large and one 50 m patch |
  | Meadow, heath, built-up, rock | land cover | `landuse=meadow`, `natural=heath`, `landuse=residential`, `natural=bare_rock` | none | one large patch each, and the small patches of finding 4 |
  | Settlements | features | nodes, `place=village` (`Lynmouth`, at the river mouth), `place=town` (`Lynton`), `place=hamlet` (`Countisbury`) | as given | within 800 m of the track |
  | Landmarks | features | node `man_made=lighthouse` (`Foreland Point`, on the coast); node `tourism=attraction` (`Watersmeet`, at the stream's mouth) | as given | inside the smallest card |

  - Element ids run 1, 2, 3, and so on, in writing order, unique across both Overpass
    payloads.
  - Relation members carry `type`, `ref`, `role` and `geometry`, the shape of the Lynmouth
    payload.
  - If the plan's author wants a road number, `A39` is real but not in the spec's name list.
    Leave it out unless the spec is amended.

### 6. [BLOCKING] The key: two margins named, and the key must come from the read-back track

- **Evidence:** P1 step 2 says "with the library's default margins", and P0 item 4 says 800 m.
  `Cache.key` hashes the box of the `Track` it is given, rounded to six places
  (`cache.py:139-147`). If the generator keys an unrounded in-memory track and then writes the
  GPX at fixed precision, the key can differ from the one the example computes from the file.
- **Fix:** use the default margins (finding 1). The generator, in order:
  1. builds the track in metres;
  2. converts it to degrees through one fixed
     `Projection(lat0=51.225, lat_ref=51.225, lng_ref=-3.84)` with `.inverse`;
  3. writes `track.gpx` at six decimals, in the Lynmouth `track.gpx` layout, with no times;
  4. reads it back with `Track.from_gpx`;
  5. sets `key = Cache(out_dir).key(track, OverpassFeatures(CONTACT), OpenTopoData(CONTACT))`;
  6. lays the features out through the same projection;
  7. writes the elevation as `ElevationGrid(n=ELEVATION_SAMPLES,
     box=track.bounding_box(MARGIN_M), ...).to_json()`, the bytes `Cache.ensure` would write
     (`cache.py:284`, `providers/base.py:63-71`).

  `PREVIEW_KEY` in `paths.py` is the pinned literal, and the fixture test asserts it equals
  the computed key.

### 7. [BLOCKING] The golden test's size assertion is wrong, and it cannot read the labels

- **Evidence:** compose returns the render grid, display times `supersample` (2). A 600 px card
  is a 1200 x 1071 or 1072 PNG (measured `display [600, 536]`). `test_map_styles.py:22` pins
  `(1800, 1281)` for 900. "Writes a 600 px wide PNG" fails.
- **Fix:**
  - Pin `CARD_SIZE` as a literal measured once (width 1200), and the mean RGB as literals
    within 1.5.
  - Read the labels from `preview(...)`'s `Lettering` (finding 2), as a set of distinct names
    like `test_places.py:93-96`. Pin them for **every** theme, not only `default`: the spec
    says "pins the label names placed" for the themes it paints, the lettering is already
    computed, and `label_max` and `name_tags` differ by theme (`oxford.yaml` 4, `y-fenni.yaml`
    6 with `name:cy`).
  - Parametrize over `list(MEAN_RGB)` with ids. Add one **non-golden** test asserting
    `set(MEAN_RGB) == set(Style.themes()) | {example .yaml paths}`. Then a new theme fails
    loudly in the fast suite, not as a `KeyError` in the golden workflow.

### 8. [BLOCKING] `docs_images.py` needs three edits, the caption needs backticks, and the entries are unprescribed

- **Evidence:**
  - The `IMAGES_009A` precedent is three edits: the import (`docs_images.py:45`),
    `**SHARES_009A` inside `SLICE_SHARE_BYTES` (`:75`) and `IMAGES += IMAGES_009A` (`:511`).
    P3's "two lines only" leaves out the share, and
    `test_each_entry_names_a_known_slice_and_an_extension_its_encoding_writes`
    (`tests/docs/test_docs_images.py:112`) fails on it.
  - The caption regex is ``^\*Painted by `examples/(?P<stem>...)\.py` ``
    (`test_captions.py:23`). The plan's sample has no backticks, so it is not read as a
    caption.
  - The how-to's "Four packaged themes" has subsections only for `pen-and-ink`, `sepia`, `bold`
    and `winter` (`write-a-theme.md:448-500`). "Under each packaged theme" leaves `default`
    with nowhere to go.
- **Fix:**
  - The three edits above.
  - In `docs_images_008a.py`, five entries `DocsImage(f"preview/{name}.webp", "theme_preview",
    (("theme", name),), "preview", 600, "page", "webp-lossy", "008a-preview")` for `default`,
    `pen-and-ink`, `sepia`, `bold` and `winter`. Pass `theme="default"` explicitly so every
    caption names its theme.
  - Captions read ``*Painted by `examples/theme_preview.py` with `theme="sepia"`.*``.
  - In the how-to:
    - Add one paragraph and the `default` image directly under `## Four packaged themes`,
      before `### Pen and ink`.
    - Add each other preview image after that theme's existing map-styles image and caption.
    - Add one sentence to the section's opening paragraph naming
      `examples/theme_preview.py` and the preview fixture.
  - In `docs/gallery.md`, add the five images under the existing
    `### [Write a theme](how-to/write-a-theme.md)` heading, after the four map-styles images
    and before the relief-strength image.

### 9. [SHOULD-FIX] The generator's output is not tied to the committed bytes

- **Evidence:** P1 tests that two runs are identical. Nothing tests that they equal
  `tests/fixtures/preview/`, so the committed fixture can drift from its generator. P0 item 5
  copies the Lynmouth `osm3s` block, whose `copyright` states the data is from OpenStreetMap
  under the ODbL. That is false for synthetic data. Its `timestamp` is a recording time.
- **Fix:**
  - The generator takes an output directory. The test writes into `tmp_path` and asserts every
    file is byte-equal to the committed one.
  - Every float is rounded: seven decimals for coordinates, whole metres for elevation, which
    SRTM-like data needs anyway because `_NUMBER` would read a 1.25 m elevation as a
    longitude if the payloads were ever scanned.
  - Write `json.dumps(..., indent=None, separators=(",", ":"))` with a trailing newline.
  - `osm3s` is `{"timestamp_osm_base": "2026-11-28T00:00:00Z", "copyright": "Synthetic data
    made by tests/fixtures/make_preview.py; not OpenStreetMap data."}`.
  - The test also checks every latitude and longitude in all three payloads, the elevation
    `bbox`, `lats` and `lons`, and the GPX against `BOXES["preview"]`, not only the nodes.

### 10. [SHOULD-FIX] The elevation contradicts the coast

- **Evidence:** a 20 m floor everywhere puts the sea at 20 m. The relief then shades the sea,
  and the elevation-traced sea (`contours.sea_rings` at 0 m) disagrees with the painted one.
- **Fix:** elevation is 0 at every grid point on the sea side of the coast (and inside the
  island's ring: land). Elsewhere it is a 20 m floor plus a Gaussian 300 m high with a 500 m
  sigma, centred inside the smallest card on the land side, at least 400 m from the coast.
  Round to whole metres.

### 11. [SHOULD-FIX] ADR 0072 must amend more of 0032 than the box table

- **Evidence:** ADR 0032's "Fixture rules, for every fixture" says three things the preview
  breaks:
  - the track is built by `make_track.py` from OSM ways;
  - the payloads are recorded by `record_fixture.py` and licensed ODbL;
  - "the plan, this ADR and every other file carry no coordinate".

  The generator carries its centre, and the `Foreland Point` name is lettered at an invented
  position, far from the real headland (which lies east of the Lynmouth box). CLAUDE.md says
  coordinates are "never invented". Its "A card per fixture" also names `test_places.py`.
- **Fix:** ADR 0072 says, for `preview/` only:
  - the track and payloads are made up by `make_preview.py`, not built or recorded, and are
    not ODbL;
  - the generator holds its centre inside the box;
  - real names stand at made-up places by design;
  - its card test is `tests/golden/test_theme_preview.py`.

  It also states the margins (the defaults) and the 600,000-byte budget.

### 12. [SHOULD-FIX] `test_coordinates.py` needs a `KEYS` entry, which P1's owned list leaves out

- **Evidence:** payload exemption comes from `KEYS` (`test_coordinates.py:37-44,58-78`).
  Without it, all three payloads are scanned. P1 lists only "one `BOXES` and one `BUDGETS`
  entry".
- **Fix:** own the `PREVIEW_KEY` import and `"preview": PREVIEW_KEY` in `KEYS` too. The budget
  entry `"preview": 600_000` is right. Drop `PREVIEW_DIR`: `paths.py` names no per-place
  directory, and each one is `FIXTURES / <name>` (`paths.py:16-17`).

### 13. [SHOULD-FIX] The "doubles back" predicate is vacuous, and "beside" is unmeasured

- **Evidence:** "some pair of non-adjacent track points within 30 m" holds at any bend of a
  track sampled every 20 m.
- **Fix:**
  - Some two points at least 400 m apart *along* the track lie within 30 m of each other.
  - One such retraced stretch runs within 20 m of the minor road for at least 300 m.
  - Another runs within 40 m of the `East Lyn River` for at least 300 m.
  - Measure with `ink.polyline` distances in the generator's metre frame.

### 14. [SHOULD-FIX] The 15-second criterion has no check

- **Evidence:** in this environment (4 cores), one `test_map_styles.py` paint (Ambleside at
  900 px, dense land cover) took 22.9 s wall time, pytest start-up included. 600 px synthetic
  should be well under that, but the plan never measures it.
- **Fix:** P2 ends with a timed `uv run python examples/theme_preview.py --theme default out/`.
  Record the wall time in the PR body, and in the fixture README if it is over 10 s. No
  timing test.

### 15. [CONSIDER] Split the generator before it grows

The geometry, the three writers and the README writer are four responsibilities. Start with
`make_preview.py` (layout, in metres) and `preview_payloads.py` (projection and writers).
`make_track.py` is already at 451 lines, and only `src/` is budget-enforced.

### 16. [CONSIDER] Workflow steps the plan omits

- At the start, comment the branch name on #79 (CLAUDE.md "Starting").
- Avoid the retired word "callout" from the feature note in any new `.py` or example file
  (`test_retired_words.py`).
- The card's credit reads "© OpenStreetMap contributors" over synthetic data, because it is
  the provider's credit. The spec asks for the credit, so keep it, but say so in the fixture
  README.

## Re-review (revision 2)

Checked revision 2 of `plan.md` on branch `claude/lucid-shannon-v36myd`, with `main` at `3817978`.
The only change on main is a toolchain bump, and it touches none of the code cited above.

### Verdict: BLOCK

Revision 2 takes every finding as binding, and fixes findings 1 to 8 as prescribed. Two new
problems remain, and an agent cannot one-shot the plan with either of them:

- The plan has two homes for the 600 px copy of the style.
- The coast rows of finding 5's table, which the plan adopts verbatim, make the island
  impossible to place inside the smallest card. Decision 2 requires it there.

The table's flaw is mine. Both fixes are one line or one short table.

### Resolutions verified

| Finding | Status | Where in revision 2 |
| --- | --- | --- |
| 1 Card frame | resolved: 1.5 x 1.6 km track, default margins, data region, per-theme frame and lanes checks | decisions 1-2, test plan row 3 |
| 2 Example signature | resolved, except finding R1 | decision 10 |
| 3 Presence test on `fetch` | resolved | test plan row 3 |
| 4 Small patches | resolved | decision 4 |
| 5 Element table | adopted verbatim; its coast rows conflict with decision 2 (finding R2) | decision 3 |
| 6 Key from the read-back GPX | resolved | decision 7 |
| 7 Golden size, labels, theme set | resolved; the test's placement is weak (finding R3) | decision 11 |
| 8 Docs registration | resolved | decision 13 |
| 9-14, 16 | resolved | decisions 5, 6, 8, 12, 14; files list; P4 |
| 15 Generator split | resolved | decision 9 |

I checked the points the brief raises:

- **Landmark lookup by name is sound.** `journal_picks` looks a coordinate-less `Landmark` up
  in `basemap.candidates` by name (`lettering/picks.py:41,68-72`). The candidates are every
  named node inside the card (`osm_elements.py:357-360`, `candidates/landmarks.py:193-197`),
  and the cap is far above this fixture's handful of names. With `y-fenni`'s
  `name_tags: [name:cy, name]` the name still falls back to `name`.
  - One consequence to expect: once any curated landmark lands, the heuristic landmarks are
    not lettered (`lettering/pipeline.py:176-179`). `Watersmeet` will therefore not be
    lettered unless it is added to the annotations' `landmarks`. That is fine for the spec,
    which asks for "a named landmark", and the label pins will show it.
- **The elevation rule and the island agree.** Decision 5 makes the island's ring land at the
  20 m floor, and the sea 0 m. The grid spacing is about 57 m (80 samples over 4.5 km), so a
  110 m-radius island holds several land samples. The step from the sea at 0 m to the hill
  at the coast reads as a cliff, which is right for this coast.

### Findings

#### BLOCKING

**R1. The 600 px copy has two possible homes.**
- Decision 10 has `main` copy the style with `card.display_px = 600` and then call `preview`.
- Decision 11 has the golden test call `preview(...)` directly and pin `CARD_SIZE` at width
  1200.
- A test that passes `Style.from_theme(theme)` to `preview` paints at the default 900 px: an
  1800 px PNG, different labels, and different mean RGB from the docs images. The agent must
  either copy the style again in the test, which makes two sources, or notice and restructure.

*Fix:* `preview` applies the copy itself, as its first line:
`style = style.model_copy(update={"card": replace(style.card, display_px=DISPLAY_PX)})`,
with `DISPLAY_PX = 600` a module constant. `main` passes `Style.from_theme(theme,
relative_to=REPO_ROOT)` unchanged. Every caller then gets the 600 px card.

**R2. Finding 5's coast rows contradict decision 2, so the island cannot be placed.**
- In the plan's metre frame (origin at the track box's centre, x east, y north), the track
  box is x -750 to 750 and y -800 to 800.
- The smallest card, `y-fenni`, reaches y 1220. The default card reaches y 1756, and the
  largest, `yr-wyddfa`, y 1905. The fetch box reaches y 2300.
- The table says the coast runs "north of the track, at least 300 m off it". Read as a
  straight line north of the track box, that puts the coast at or above y 1100. That leaves
  at most 120 m of sea inside the smallest card.
- The island needs a perimeter of at least 600 m, so it is about 190 m across. It cannot sit
  in that strip, yet decision 2 requires every listed feature inside the smallest card.
- The agent will either break decision 2 silently, because no test checks the smallest
  card's contents, or come back.

*Fix:* prescribe where the sea lies, and test the smallest card.

- **The coast** is drawn east to west through these metre points: (2249, 450), (900, 450),
  (600, 700), (300, 1150), (-2249, 1150). The sea is north of it.
- **The island** is centred at (950, 900), radius 110 m, as an anticlockwise closed ring of
  at least 24 vertices. Its perimeter is about 690 m.
- **`Foreland Point`** is placed at (1050, 450), on the coast east of the bend.
- **The river's mouth** is on the coast segment from (600, 700) to (300, 1150).
- These positions keep every listed feature within 350 m of the track box. The island
  reaches x 1060, and the coast's west part is at y 1150.
- **The track** keeps at least 300 m from every coast vertex and segment. East of x 600 it
  therefore stays at or below y 150. It reaches the track box's north edge, y 800, west of
  x 0.

Then add to `test_make_preview.py`: run finding 3's presence assertions on
`Style.from_theme("examples/themes/y-fenni.yaml", relative_to=REPO_ROOT)`, the smallest card,
as well as on `Style()`. Skip the lane assertion, which the per-theme loop already covers.

#### SHOULD-FIX

**R3. Put the theme-set test beside `MEAN_RGB`, and the per-theme fixture checks in P1.**
- The plan puts the non-golden theme-set test in `tests/fixtures/test_make_preview.py`. That
  test must then import `MEAN_RGB` from the golden module (`golden.test_theme_preview`, a
  namespace import of a test module).
- It also gives P2 the per-theme frame and lanes checks, which prove P1's layout. If they
  fail, P2 must edit the generator, and P1 owns the generator.

*Fix:*
- The per-theme checks belong to P1. They loop over
  `(*Style.themes(), *sorted(f"examples/themes/{p.name}" for p in (REPO_ROOT / "examples" /
  "themes").glob("*.yaml")))`, so they do not depend on the golden test.
- The theme-set test belongs to P2, inside `tests/golden/test_theme_preview.py`. Put the
  `golden` mark on the paint test as a decorator, not as `pytestmark`. Leave
  `test_every_theme_has_a_pinned_mean` unmarked, computing the same expression inline, so it
  runs in the fast suite.
- `test_make_preview.py` is then P1's alone.

**R4. `NOTE_POINT` has two homes.** The example holds the literal, and the generator decides
which track point is riverside. *Fix:* `test_make_preview.py` reads `NOTE_POINT` from
`load_example("theme_preview", "example_theme_preview")`. It asserts that the read-back
track's point at that index lies within 40 m of the `East Lyn River`, and at least 300 m from
the coast. P1 creates the constant, and the example imports nothing from tests.

**R5. Round the elevation `bbox` too.** Decision 8 rounds "coordinates". The `bbox` and the
grid's `lats` and `lons` are computed from `track.bounding_box` by `cos`, so round all three
to seven decimals before `ElevationGrid(...)`. Then the committed bytes do not rest on the
last ulp of a libm.

#### CONSIDER

- If the card should letter `Watersmeet` too, list it after `Foreland Point` in the
  annotations' `landmarks` (see the landmark note above).
- In the `__main__` block, `shutil.copytree` needs a destination that does not exist yet.
  Copy to `Path(tmp) / "cache"`, as `make_docs_images.py:47` does.

## Re-review (revision 3)

This is a short confirmation pass on revision 3 (`8650ba5c`), checking only that R1 and R2
are resolved and that decisions 15 to 19 do not contradict decisions 1 to 14.

### Verdict: PASS

- **R1 is resolved.** Decision 15 puts `DISPLAY_PX = 600` and the style copy at the start of
  `preview`, and has `main` pass `Style.from_theme(...)` unchanged. Decision 10 still says
  `main` copies the style. The plan's header now states that decisions 15 to 19 override
  decisions 10 and 11 where they disagree, so there is one rule.
- **R2 is resolved.** Decision 16 takes the coast, island, `Foreland Point` and river mouth
  geometry verbatim. It replaces the coast rows' placement rules in finding 5's table. It
  runs finding 3's presence assertions on the y-fenni style as well as on `Style()`.
  - These agree with decision 2: every listed feature is within 350 m of the track box, and
    the coast runs to the fetch-box edge.
  - They agree with decision 6: the riverside and stream stretches lie south of the coast,
    and every track point is at least 300 m from it.
- **Decisions 17 to 19 introduce no new contradiction.**
  - `test_make_preview.py` is again shared, P1 then P2 (P2 adds the `NOTE_POINT` check).
    The slices are serial and each half is named, so this is acceptable.

Two editorial notes, neither blocking:
- The test plan's "Features meet each other" row still names only `Style()`. Decision 16
  adds the y-fenni style.
- Decision 10 says the fixture README records `NOTE_POINT`. The README is written in P1,
  before the example exists, so it should record the riverside stretch's index range, and
  P2 picks `NOTE_POINT` inside that range.
