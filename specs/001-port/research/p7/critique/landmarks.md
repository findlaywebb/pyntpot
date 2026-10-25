# Landmarks worth lettering on the showcase route maps

Scratch research, 2026-10-24. Coordinates appear only in this file and in the scratch
scripts beside it; none go into the repository. Names and ids were checked against the
recorded fixture payloads (`tests/fixtures/<dir>/overpass-*.json`) and, for anything the
payloads do not hold, live OpenStreetMap through the Overpass mirror at maps.mail.ru
(dumps in `osm/`). Welsh labels for Y Fenni items come from Wikidata's `cy` labels where
OSM has no `name:cy`.

Distances are to the fixture track (nearest segment, metres, element centroid; a lake's
centroid can sit well off a route that runs along its shore). Oxford's distances are to
the current fixture loop, not the planned one; Ambleside has no fixture yet, so its
distances are to a rough sketch of the Loughrigg circuit and are approximate.

"Payload?" says whether the recorded feature payload holds the element as a landmark
candidate. When it does not, a curated callout must carry its own coordinates (see 2a).

Scripts: `scripts/cands.py` (the library's own ranked candidates per fixture, output in
`cands.json`), `scripts/find.py` (search a fixture by name with distance),
`scripts/dist.py`, `scripts/sim.py` (the ranking change of 2b, simulated),
`scripts/curated.py` (the 2a example, run end to end; output `y-fenni-curated.png`).

---

## 1. Shortlists

### Keswick and Derwentwater (`keswick`)

Route: the Moot Hall, Lake Road, the shore to Friar's Crag, Crow Park and Hope Park, the
Derwent footbridge, Portinscale, back by Main Street.

| Letter as | Why | OSM element and key tags | Off route | Payload? |
|---|---|---|---|---|
| Moot Hall | The 1813 market-place hall in the middle of Main Street, the town's emblem and now its information centre; the start of the route | way 23450175: `building=civic`, `name=Moot Hall`, `wikidata=Q17540508`, `wikipedia=en:Moot Hall, Keswick` | 5 m | No (`building=civic` is not in the query) |
| Friar's Crag | The promontory Ruskin called one of the finest views in Europe; NT; the Ruskin Monument stands on it | node 686809517: `tourism=viewpoint`, `wikidata=Q85762143`. Ruskin Monument node 686809526 (`historic=monument`, `wikidata=Q26612523`, 12 m): letter one, not both | 17 m | Yes |
| Theatre by the Lake | The town's well-loved repertory theatre on the lake shore | way 91894071: `amenity=theatre`, `building=civic`, `wikidata=Q7777470` | 16 m | Yes |
| Crow Park | The National Trust lakeside meadow with the classic view down Derwentwater to Borrowdale | way 309452603: `landuse=recreation_ground`, `operator=National Trust` (in the land cover payload only) | 1 m | No |
| Derwent Pencil Museum | Keswick's pencil industry, built on Borrowdale graphite; a real local institution | way 277905445: `tourism=museum`, `wikidata=Q5193935` | 60 m | Yes |
| Derwent Island | The wooded island off the boat landings with its Georgian house (NT) | relation 9220684: `tourism=attraction`, `name=Derwent Island and House`, `alt_name=Derwent Isle and House`, NT | 243 m | Yes (as a `sight`) |
| St John's Church | The Victorian sandstone spire that marks Keswick from the lake; Hugh Walpole's grave | way 138364323: `amenity=place_of_worship`, `building=church`, `wikidata=Q17540800` | 140 m | Yes |

Reserves: Castlehead viewpoint (node 2682064793 viewpoint, node 883702081 peak; 535 m),
Walla Crag (node 5480592821, 1.6 km), Latrigg (node 29951936, 1.8 km), Keswick Launch
(node 8963886201 `amenity=boat_rental`, 39 m).

Do not letter: **The Retro Zone** (node 13064480020: `tourism=museum`, `museum=history`,
`fee=yes`, no `wikidata`, a retro games and toys shop-museum on Main Street). Also
"Keswick Town Hall" (way 167711096, `amenity=townhall`) is a different building about
100 m west of the Moot Hall; letter the Moot Hall instead.

### The Quiraing, Trotternish (`trotternish`)

Route: the Bealach Ollasgairte car park, the lower path north under the Quiraing to Fir
Bhreugach, back along the escarpment top.

| Letter as | Why | OSM element and key tags | Off route | Payload? |
|---|---|---|---|---|
| The Needle | The 37 m leaning pinnacle the path squeezes past; the Quiraing's signature | node 1501733166: `natural=peak`, `ele=445` | 94 m | Yes |
| The Prison | The castle-like rock mass opposite the Needle | node 1501855005: `natural=peak`, `ele=365` | 46 m | Yes |
| The Table | The hidden flat grassy summit inside the slip, said to have hosted shinty games | node 1501855011: `place=locality` | 74 m | No (`place=locality` not queried) |
| Meall na Suiramach | The summit above the Quiraing (543 m, a Marilyn), crossed on the top path | node 634382574: `natural=peak`, `ele=543`, `marilyn=yes` | 321 m | Yes |
| Fir Bhreugach | The turning point at the north end | node 9936601967: `natural=peak`, `ele=328` (OSM note: may be up to 40 m out) | 63 m | Yes |
| Cnoc a' Mheirlich | "The Shark Fin", the fin of rock above the road at the start | way 293217471: `natural=cliff`, `name:en=The Shark Fin`, `height=266` | 187 m | No |
| Quiraing Vista | The viewpoint at the bealach looking north along the landslip | node 3442223637: `tourism=viewpoint` | 31 m | Yes |

Reserves: Loch Leum na Luirginn (way 98777864, lake, `wikidata=Q20620331`, about 700 m),
Leac nan Fionn (node 9932918561, 373 m). The automatic picks today (the Prison, Quiraing
South Pinnacle, Fir Bhreugach) are three rocks of the same kind; the Needle and the Table
are what people come for. Skye names are Gaelic as OSM holds them (the Welsh rule does not
apply).

### Pen-y-Pass, Crib Goch, Yr Wyddfa, Llanberis (`yr-wyddfa`)

| Letter as | Why | OSM element and key tags | Off route | Payload? |
|---|---|---|---|---|
| Yr Wyddfa | The summit of Wales, 1085 m | node 8755297244: `natural=peak`, `name=Yr Wyddfa`, `name:cy=Yr Wyddfa`, `wikidata=Q217142` | 8 m | Yes |
| Crib Goch | The knife-edge "red ridge", the route's crux | node 3686236093: `natural=peak`, `ele=923`, `wikidata=Q3002568` | 10 m | Yes |
| Garnedd Ugain | Second summit of Wales (Crib y Ddysgl), 1065 m | node 340239820: `natural=peak`, `alt_name=Crib y Ddysgl`, `wikidata=Q3098405` | 1 m | Yes |
| Bwlch Glas | The col where the ridge route joins the Llanberis Path, marked by the standing stone | node 1535113731: `natural=saddle`, `name=Bwlch Glâs`, `ele=998`; marker stone node 8874818018 | 0 m | No (saddles not queried) |
| Hafod Eryri | The granite summit building (2009) | way 68433335: `amenity=cafe`, `name=Hafod Eryri Summit Visitor Centre`, `alt_name=Hafod Eryri` | 40 m | No (`amenity=cafe` not queried) |
| Glaslyn | The deep blue copper-mine lake under the summit, seen from Crib Goch | way 95392960: `natural=water`, `water=lake`, `name:cy=Glaslyn`, `wikidata=Q3405748` | 556 m | No (a lake, not a landmark candidate) |
| Llyn Llydaw | The big lake below, with the Miners' Track causeway | relation 20670530: `natural=water`, `name:cy=Llyn Llydaw`, `wikidata=Q3086201` | 727 m | No |
| Castell Dolbadarn | Llywelyn's round tower above Llyn Padarn at the walk's foot | way 886457626: `historic=castle`, `ruins=yes`, `name:cy=Castell Dolbadarn`, `heritage=2` (Cadw), `wikidata=Q2078555` | 947 m | Yes (as a tier 2 `monument`) |

Reserves: Bwlch Coch (node 2772604796 saddle, 2 m), Rhaeadr Llanberis viewpoint over the
Ceunant Mawr falls (node 11809624393, 532 m), Clogwyn station (way 111686299, 89 m).
Pen-y-Pass itself has no named feature in the payload beyond the car park; the start
marker already says it.

### Central Oxford (`oxford`, planned route)

Planned: Carfax, the High, out and back over Magdalen Bridge, Queen's Lane, by the
Radcliffe Camera, through Christ Church on the return. Distances are to today's loop.

| Letter as | Why | OSM element and key tags | Off route now | Payload? |
|---|---|---|---|---|
| Carfax Tower | The 13th century tower of St Martin's at the city's crossroads; start and finish | way 311139684: `man_made=tower`, `building=church`, `official_name=St Martin's Tower`, `height=23` | 38 m | Yes |
| St Mary the Virgin | The University Church on the High, Grade I, spire over Radcliffe Square | way 60903337: `amenity=place_of_worship`, `alt_name=The University Church`, `listed_status=Grade I`, `wikidata=Q581986` | 28 m | Yes |
| Magdalen Tower | The bell tower where the choir sings at dawn on May Morning | way 77881357: `man_made=tower`, `wikidata=Q6729839` | 21 m | Yes |
| Magdalen Bridge | The 1770s bridge over the Cherwell, the out-and-back turn | way 1154991954: `man_made=bridge`, `bridge:structure=arch`, `wikidata=Q5573206` | 7 m | Yes |
| The Queen's College | Hawksmoor's front on the High; Queen's Lane runs along it | way 23679234: `amenity=university`, `learning=oxford_college`, `wikidata=Q73094` | 63 m (on the new route) | Yes |
| Bridge of Sighs | Hertford College's skyway over New College Lane, which Queen's Lane leads into | way 62333303: `bridge=yes`, `bridge:structure=humpback`, `building=university` | 216 m (on or beside the new route) | Yes |
| Radcliffe Camera | Gibbs's domed library, the image of Oxford | way 4884600: `amenity=library`, `building=university`, `loc_name=Rad Cam` | 109 m (on the new route) | Yes |
| Christ Church | The college and cathedral, entered under Tom Tower on the return | relation 15595647: `amenity=university`, `learning=oxford_college`, `tourism=attraction`; Tom Tower way 146574165 (`man_made=tower`, `height=24`, 1 m) | 4 m | Yes |

Reserves: Botanic Garden (relation 16470745, `heritage=2`, 51 m), Bodleian Library
(relation 62123, 180 m), St Edmund Hall (way 112466246, 64 m, on Queen's Lane).
Avoid: Oxford Illusion Museum (way 957951010: `tourism=museum`, no `wikidata`), which
ranks fourth automatically today.

### Y Fenni (`y-fenni`)

Route: the castle, Castle Meadows by the Wysg to the Llan-ffwyst bridge, back by Merthyr
Road and the High Street.

| Letter as | Why | OSM element and key tags | Off route | Payload? |
|---|---|---|---|---|
| Castell y Fenni | The Norman castle the town grew round; the 1175 massacre; keep holds the town museum | way 368980598: `historic=castle`, `building=ruins`, `name=Castell Y Fenni`; park way 368980592 (`wikidata=Q4667087`, `cy` label "Castell y Fenni"); museum node 12543673348 (`tourism=museum`, `wikidata=Q4667090`, "Amgueddfa Y Fenni") is inside: do not letter both | 15 to 17 m | Yes (but as a tier 2 `monument`, so chapels outrank it) |
| Priordy y Fenni | St Mary's Priory Church, Grade I, with the carved Jesse figure and the Herbert tombs; the Tithe Barn beside it | way 449666074: `amenity=place_of_worship`, `name=St Marys`, `wikidata=Q7245494` (`cy` label "Priordy y Fenni") | 120 m | Yes |
| Angel Bakery | The maintainer's pick: the much-loved bakery of the Angel, by the High Street | node 12633622904: `shop=bakery`, `name=Angel Bakery` (the Angel hotel, node 12633589283, `wikidata=Q24182520`, is next door) | 10 m | No (shops are not queried) |
| Tŷ Melin | The maintainer's pick: the Tŷ Melin bakery | **Not in OSM.** No element named like "Melin" in Y Fenni (only "Melin Uchaf", way 705718907, a house west of the town). Needs a location from the maintainer, or mapping in OSM first; never guess one | n/a | No |
| Town Hall | The Victorian town hall and market hall with its green copper spire; houses the Borough Theatre | way 368980602: `amenity=marketplace`, `name=Abergavenny Market`, `wikidata=Q29482486` (en label "Town Hall", Grade II; no Welsh label recorded); Borough Theatre node 2429925412 (`amenity=theatre`, `wikidata=Q4946329`, 18 m) is inside: letter one | 39 m | No (marketplace not queried); the theatre is |
| Pont y Fenni | The Usk Bridge, Grade II*, the medieval-rooted bridge the route crosses to Llan-ffwyst | way 22951980: `bridge=yes`, `highway=primary`, `ref=A4143`, unnamed, `wikidata=Q17743153` (`cy` label "Pont y Fenni") | 0 m | No (unnamed bridges not queried) |
| Gerddi Linda Vista | Victorian terraced gardens over the river | way 704261160: `leisure=park`, `name:cy=Gerddi Linda Vista`, `wikidata=Q117085801` | 60 m | No |

Reserves: Castle Meadows (way 1493545197, on route), the chapels the card letters today
(Methodist way 720027484, United Reformed way 720027485; both listed, `wikidata` set).
Off the card's box: Ysgyryd Fawr (node 291437459, 5.2 km), Mynydd Pen y Fâl (node
244018898, 5.1 km), the Blorenge (node 582796015, 2.8 km). They would make the hero if the
card took in more ground. A Welsh label for the Town Hall needs the maintainer's
confirmation; I found none recorded.

### Ambleside, the Loughrigg circuit (planned hero, no fixture yet)

Assumed circuit: Bridge House, Rothay Park, Miller Bridge, Loughrigg Fell, Loughrigg
Terrace, Rydal Cave, Rydal Water, Pelter Bridge, back under Loughrigg.

| Letter as | Why | OSM element and key tags | Off route (approx.) |
|---|---|---|---|
| Bridge House | The tiny 17th century house on a bridge over Stock Beck, Ambleside's emblem (NT) | way 389884072: `tourism=attraction`, `operator=National Trust`, `wikidata=Q17530674` | 0 m |
| St Mary's Church | Gilbert Scott's spire, the landmark of the town; the rushbearing | way 202713691: `amenity=place_of_worship`, `wikidata=Q17543708` | 125 m |
| Miller Bridge | The old packhorse-style crossing of the Rothay onto Loughrigg | way 38457618: `bridge=yes`, `highway=footway`, `wikidata=Q26537368` | 0 m |
| Loughrigg Fell | The summit, 335 m, with its views to Windermere and the Langdales | node 1779620834: `natural=peak`, `ele=335.1`, `wikidata=Q6686237` | 0 m |
| Loughrigg Terrace | The famous terrace path above Grasmere | way 293562902: `highway=bridleway`, `bridge=yes`, `name=Loughrigg Terrace` | 0 m |
| Rydal Cave | The great slate quarry cavern with stepping stones | node 254328272: `historic=mine`, `tourism=attraction`, `mineral=slate` | 0 m |
| Rydal Water | The small lake Wordsworth walked daily | relation 402811: `natural=water`, `wikidata=Q1544320` | shore beside the route (centroid 400 m) |
| Pelter Bridge | The humpback bridge into Rydal at the circuit's turn | way 699383861: `man_made=bridge`, `bridge:structure=humpback`, `wikidata=Q26538017` | 0 m |

Reserves: Rydal Mount (way 157007659, Wordsworth's home 1813 to 1850, `wikidata=Q782981`;
OSM notes it closed as of September 2026, about 420 m), Dora's Field (way 157007646, NT,
about 270 m), the Armitt Museum (way 239880517, `wikidata=Q688663`, about 120 m),
Zeffirellis (way 846685465, `amenity=cinema`, `wikidata=Q38518607`, about 100 m, a
much-loved local institution), Grasmere (relation 350299) and Loughrigg Tarn (way
4569100). Galava Roman Fort (way 43060432) and Stock Ghyll Force (node 1377739489) are
about 1 km and 0.8 km off.

---

## 2. How the library chooses landmarks, and how to change it

### What happens today

1. `OverpassFeatures` asks for a fixed tag vocabulary (`FEATURE_QUERY` in
   `src/pyntpot/maps/providers/overpass.py`): tourism, historic, a few man_made and
   building values, `amenity` in place_of_worship/theatre/arts_centre/university/townhall/
   courthouse/casino, named bridges, peaks. No `shop`, no `amenity=cafe` or
   `marketplace`, no `building=civic`, no saddles, no `place=locality`, no unnamed bridges.
2. `osm_elements.sort_element` turns each named element into a candidate row with
   `classify(tags)` (`candidates/landmark_classes.py`) and keeps only
   `LANDMARK_TAG_KEYS` of its tags (no `wikidata`, `heritage`, `listed_status` or `shop`).
3. `build_basemap` (`layers.py`) sets `Basemap.candidates` from `rank_landmarks`, which
   sorts by `landmark_rank`: `(tier, distance / reach)`. The tier comes from the class
   (`LANDMARK_REACH_M`). Nothing in the key says how notable a thing is beyond its class.
4. `letter(plates, basemap, annotations, style)` (`lettering/pipeline.py::_anchored`):
   with no annotations, or none that resolves, `journal_heuristic` letters the first
   `style.lettering.label_max` (3) of `basemap.candidates`. Note that it does **not** use
   `pick_landmarks` (which applies `LANDMARK_CLASSES` and the reach filter); that result
   goes only to `vector_layers`. So the card's automatic picks are simply the top three of
   the rank order.

### Why the shop won on Keswick

The Retro Zone is tagged `tourism=museum`. `TOURISM_DESTINATIONS` (zoo, museum,
aquarium, theme_park) puts every `tourism=museum` in class `attraction`, tier 1 with a
450 m reach: the same tier as a summit, a spire or a zoo. It sits 8 m off Main Street, so
its comfort ratio (8 / 450 = 0.018) beats nearly everything. Today's top three are Lake
Road Chapel (9/700), The Retro Zone (8/450), Derwent Bridge (7/250). The Moot Hall never
had a chance: its building (`building=civic`) is not in the query, and the only rows
named for it are a blue plaque (class `plaque`, tier 3) and "Keswick Town Hall", a
different building. The same flaw puts the Oxford Illusion Museum fourth in Oxford.

### 2(a) Curated callouts through the public API, today

Use `Annotations.landmarks`, passed to `letter`, not `fetch(places=...)`:

- `fetch(..., places=[...])` entries are user places. A default entry (`kind` marker) is
  projected into `Basemap.places` but is **never lettered or drawn**; only
  `kind: "settlement"` entries are lettered (as settlements), `symbol: "house"` entries
  draw the home glyph, and `always_label` only forces a settlement candidate of the same
  name. The coordinate key is `lng`; an entry keyed `lon` is silently dropped. So
  `places` is the wrong tool for landmarks.
- `Annotations(landmarks=...)` takes `Landmark(name, kind, why, lat, lng)` entries or bare
  strings. With `lat` and `lng` the label is anchored there, so it works for things the
  payload lacks (the Moot Hall, Hafod Eryri, the Angel Bakery, Pont y Fenni). A bare
  string must match a candidate's lettered name exactly (after the style's `name_tags`)
  among the first 80 ranked candidates, or it is silently skipped.
- **Curated landmarks replace the automatic picks; they do not add to them.** The
  heuristic runs only when no annotation landmark resolves. Settlements, rivers, road
  numbers and the start/finish markers are still lettered by rule.
- At most `style.lettering.label_max` (default 3) are taken, in the caller's order, and
  the placer may still drop one it cannot fit, so put the most important first and raise
  `label_max` to letter more.
- `Landmark` is not re-exported from `pyntpot.maps`; a docs script can stay on the
  exported surface with `Annotations.model_validate`.

Example for the Y Fenni fixture (run end to end in `scripts/curated.py`; it lettered the
castle, the bakery, the town hall, the bridge and the theatre, and the placer dropped the
priory for space at six):

```python
from dataclasses import replace

from pyntpot.maps import Annotations, Cache, Style, Track, compose, fetch, letter, paint

base = Style.from_toml(REPO_ROOT / "examples/themes/y-fenni.toml")
style = base.model_copy(update={"lettering": replace(base.lettering, label_max=5)})
basemap = fetch(route, cache, features, elevation, style)
plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
callouts = Annotations.model_validate(
    {
        "landmarks": [
            {
                "name": "Castell y Fenni",
                "kind": "castle",
                "why": "the Norman castle",
                "lat": ...,
                "lng": ...,
            },
            {
                "name": "Priordy y Fenni",
                "kind": "worship",
                "why": "Grade I priory church",
                "lat": ...,
                "lng": ...,
            },
            {
                "name": "Angel Bakery",
                "kind": "bakery",
                "why": "much-loved bakery",
                "lat": ...,
                "lng": ...,
            },
            {
                "name": "Pont y Fenni",
                "kind": "bridge",
                "why": "Grade II* Usk bridge",
                "lat": ...,
                "lng": ...,
            },
            "Borough Theatre",  # a bare name: looked up among the candidates
        ]
    }
)
lettering = letter(plates, basemap, callouts, style)
card = compose(plates, lettering, basemap, style)
```

(Coordinates are elided here because they may not enter the repository; a docs script
would read them from a curated data file, or the callouts could become bare names once
the payload holds the elements, which needs the query change in 2b's follow-up.) Two
cautions from the trial render: the Town Hall and the Borough Theatre are one building, so
letter only one; and "Neuadd y Dref" in the trial was my placeholder, not a recorded name.

### 2(b) The smallest generic ranking fix (a src change)

All in `src/pyntpot/maps/candidates/landmark_classes.py`, `landmarks.py` and
`osm_elements.py`; an ADR is probably not needed (no boundary or public-API change) but
the focus-place goldens (`tests/golden/test_places.py`) and the candidate export change,
so it is a golden regeneration.

1. **Drop anything that is a shop.** In `classify`, return `other` (not offered) when the
   tags carry `shop`, `brand` or `brand:wikidata`. The query never asks for shops, but
   shops arrive through other tags (The Retro Zone is a shop that also tags
   `tourism=museum`; "Llanberis Art and Craft" is `shop=gift` on a `building=train_station`).
2. **Demote a museum the wider record does not know.** `tourism=museum` stays a tier 1
   `attraction` only when the element carries `wikidata`, `wikipedia`, `heritage` or
   `listed_status`; otherwise it is a `sight` (tier 2, 150 m). The Pencil Museum,
   Keswick Museum and Abergavenny Museum keep their place; The Retro Zone and the Oxford
   Illusion Museum fall.
3. **Rank recorded things first inside a tier.** `landmark_rank` becomes
   `(tier, not recorded, distance / reach)`, where recorded means `wikidata`, `wikipedia`,
   `heritage` or `listed_status` is set. This needs those keys added to
   `LANDMARK_TAG_KEYS` (also `shop`, so the row shows why it was dropped). Only `wikidata`
   proper counts, never `brand:wikidata`, so chains do not gain from it.
4. Optional, same spirit: class `historic=castle` with the tier 1 named buildings, not
   with tier 2 monuments, so Castell y Fenni and Castell Dolbadarn outrank chapels.

Simulated on the recorded payloads (`scripts/sim.py`), the automatic top three become:
Keswick: Theatre by the Lake, Friar's Crag, Derwent Pencil Museum (no shop); Oxford: Tom
Tower, Christ Church, Magdalen Tower (unchanged); Yr Wyddfa: unchanged; Y Fenni: the two
listed chapels, then Castell y Fenni (with point 4); Trotternish: unchanged (no peak there
has `wikidata`).

Follow-ups worth separate issues, not part of the smallest fix:

- `journal_heuristic` ignores `pick_landmarks` (class keep list and reach): the card
  letters the raw top of the rank order. Letting `letter` read the heuristic's picks would
  stop `sight`, `ruin` and `plaque` rows ever being lettered automatically.
- The Moot Hall shows the query's blind spot: a named building with `wikidata` but a
  generic `building=civic`. Asking Overpass also for named ways and nodes carrying
  `wikidata` together with `building`, `historic` or `tourism` would let the automatic
  ranking find it, at the cost of re-recording every fixture payload; check against ADR 0017
  whether the query text feeds the cache key, since a stale payload under an unchanged
  key would hide the change.
- `fetch(places=...)` documents `lat`/`lng` but a caller writing `lon` gets nothing back
  and no warning.
