# Map images: art-direction critique, round 2 (P7.V13)

Group: every map image published under `docs/images/` on `p7-wip` after the P7.V revision
round: the hero, the social preview, the five place cards (Ambleside, Oxford, Skye, Y Fenni,
Yr Wyddfa), the gallery and tutorial route maps, the command-line how-to (Lynmouth), the
route-ink how-to and its grid, and the four map styles. Same rubric as round 1
(`../maps.md`): 5 = iconic, would sell the library; 4 = good, small faults; 3 = does its job,
visible faults; 2 = undermines the page; 1 = broken. Each was viewed at full size, with
crops in
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/crit2/`.

The brief this round answers is `p7-research.md` section 10: striking hero maps with more
landscape, a maroon route that looks painted, Oxford as a dense city on the Queen's Lane,
Radcliffe Camera and Christ Church route, Skye shown as an island, landmarks worth calling
out, and a different idea for each map.

## Scores

| Image | Round 1 | Round 2 | One line |
| --- | --- | --- | --- |
| `hero.webp` (Ambleside, showcase) | 2 (Keswick) | **4** | Fills the frame, maroon loop, fell country. Grasmere, Windermere and Loughrigg Fell unnamed. |
| `social-preview.jpg` | 2 | **3** | Full-width map with a lettered wordmark, but the cartouche blanks the south side of the loop. |
| `places/ambleside.webp` | new | **3** | The hero at 720 px; "Rydal Cave" is lettered on the lake, under the "Rydal Water" leader. |
| `places/oxford.webp` | 1 | **3** | Flood plain fixed, streets dense, right route. Christ Church Meadow is a bare-paper hole; the honey wash sits on the suburbs, not the colleges. |
| `places/skye.webp` | 2 (Trotternish) | **3** | The island reads at once and the journal notes are charming. The mainland is painted as sea; the Armadale leg is a triple line. |
| `places/y-fenni.webp` | 2 | **2** | A good food-tour idea, but the route is a knot in the middle of a terracotta town and six leaders cross it. |
| `places/yr-wyddfa.webp` | 2 | **3** | Glaslyn, Llyn Llydaw and the Llanberis lakes now in; a mountain palette. Pale label halos, "Afon Arddu" eaten by a lake. |
| `gallery/route-map.webp` | 2 | **2** | The default-theme Ambleside sticker: pink route, land on a third of the card, a near-copy of the tutorial image. |
| `tutorials/route-map.webp` | 3 | **3** | Same card at 900 px; right for the tutorial's default look, with the sticker framing still showing. |
| `how-to/command-line.webp` (Lynmouth) | 4 (golden) | **3** | Clean loop, but a chapel with a 40-character name and two more callouts jam the coast; Lynmouth itself is not lettered. |
| `how-to/route-ink.webp` | 3 | **3** | The violet change is clear; the same default card again. |
| `how-to/route-ink-grid.webp` | new | **2** | The grid the maintainer asked for, but the cells are too small, unlabelled, and multiply turns every ink black where the route runs over water. |
| `map-styles/bold.webp` | 3 | **3** | Unchanged in spirit: `#e6007a` and acid greens still read as a GIS default. |
| `map-styles/pen-and-ink.webp` | 2 | **3** | Rydal Water is now a pale grey wash rather than a blot; rivers are still the same grey-brown as roads. |
| `map-styles/sepia.webp` | 4 | **4** | Still the most cohesive style; vignette lighter. |
| `map-styles/winter.webp` | 3 | **3** | Scarlet on blue-white is strong; slate-blue wood still competes with the lake. |

**Under 3:** `places/y-fenni.webp`, `gallery/route-map.webp`, `how-to/route-ink-grid.webp`.

## What improved since round 1

- **The route is maroon and painted.** `#7b2335` with a wobbling stroke and no magenta halo,
  in every showcase theme. On the hero it reads as ink, which was the round's main ask.
- **Framing.** The showcase themes widen the ribbon (`ribbon_mult` 2.4 to 14) and the hero,
  Skye and Yr Wyddfa now carry land to three or four edges. The hero is the first map in the
  repo that looks like a picture rather than a diagram on a sticker.
- **Terrain.** `relief_strength` exists and is used: the ochre fellside on Ambleside and the
  grey-mauve rock on Yr Wyddfa read as high ground, which nothing did in round 1.
- **Oxford's water bug is gone.** The Cherwell is braided channels with land between them, the
  Thames reach is a river, and "Holywell Mill Stream" no longer prints white over paper.
  `roads = "all"` gives a real street grid.
- **Landmarks are chosen.** `examples/places.toml` callouts: Bridge House and Rydal Cave;
  Radcliffe Camera, the Bridge of Sighs, Magdalen Bridge and Christ Church; the Horseshoe's
  tops and lakes; the Y Fenni food tour including the hand-placed Tŷ Melin. "The Retro Zone"
  and the chapels are gone (except on Lynmouth, below).
- **One idea per map** is visible: a fell loop, a college city walk, an island road trip with
  journal notes, a food tour, a mountain traverse.
- **Out-and-back drawn once.** Oxford's Magdalen Bridge leg is a single stroke, not two
  parallel lines.
- **Keswick is retired** and the social preview is a full-width map with the wordmark on it.

## Per image

### `hero.webp` (1200 px, showcase Ambleside). 4/5
- **Works:** land fills about 90% of the frame; Rydal Water and Grasmere are big, soft washes;
  the loop is one clean figure; ochre fell against green wood gives a landscape; "Ambleside"
  underlined is a good anchor.
- **Faults:**
  1. Grasmere (the large lake top left), the head of Windermere (bottom right) and Loughrigg
     Fell are not lettered, though the default-theme card names Loughrigg Fell. The fell the
     route circles is the subject. *Cause:* theme data (`places.toml` callouts; the showcase
     theme has `pick_landmarks = []` and the callouts crowd out the heuristic picks). *Fix:* add
     Grasmere, Windermere and Loughrigg Fell to `[ambleside].callouts`.
  2. Short brown hair-like stubs stick out of the route between Rydal and Ambleside (minor
     roads clipped to the route corridor). *Cause:* library, `minor_road_classes` drawn as
     clipped fragments. *Fix:* drop minor-road pieces shorter than about 20 px after clipping.
  3. Short blue dashes of stream (south of Loughrigg Terrace, west of Rydal Cave) stop dead
     mid-land. *Cause:* same clipping. *Fix:* same length floor for waterways, or fade ends.
  4. A pale rectangle sits behind "Loughrigg Terrace" where the label backing knocks back the
     wash; visible as a box at full size. *Cause:* library, nib backing shape. *Fix:* feather
     the backing mask, or follow the glyph outlines rather than the label box.
  5. A faint blue smear on the land left of Grasmere (a pond or wetland painted very pale)
     reads as a stain. Minor.
  6. "start" is a small pink word in a field; there is no start mark on the line. Minor.

### `social-preview.jpg` (1280x640). 3/5
- **Works:** the map runs edge to edge, the wordmark is lettered in the hand, the colours carry
  at thumbnail size.
- **Faults:** the cartouche is a cream blur band that washes out the south leg of the loop, so
  at link-card size the route reads as an open arc, not a loop. The map's own labels are too
  small to read at 300 to 600 px and add noise. *Fix (example script):* move the crop so the
  loop sits right of centre and the wordmark goes over the open fell or Grasmere side, where
  no route runs; omit labels other than "Ambleside" in this crop.

### `places/ambleside.webp` (720). 3/5
The hero recomposed for 720. "Rydal Cave" is placed inside Rydal Water, and the "Rydal Water"
leader runs down through the "v" of "Cave", so the lake looks named "Rydal Cave". "Bridge
House" has a long leader crossing the start. *Cause:* library placer (the lake polygon is
allowed as label ground for a non-water name; leaders are not checked against other labels).
*Fix:* forbid a land callout on a water polygon, and reject a leader that crosses another
label's box; failing that, drop Rydal Cave at 720.

### `places/oxford.webp` (720, Oxford theme). 3/5
- **Works:** a city at last: dense lanes, honey terraces, green quads, a properly braided
  Cherwell, and the route goes up to the Bridge of Sighs, along Queen's Lane, out to Magdalen
  Bridge once and round by Christ Church as asked.
- **Faults:**
  1. **Christ Church Meadow is bare paper.** The biggest shape inside the loop is an unpainted
     cream hole. *Cause:* most likely land cover: the meadow's landuse/leisure class has no
     pigment in this theme, or it is a multipolygon that loses its fill. *Fix:* check the
     meadow's tags in the fixture; map them to `grass` or `meadow` in the theme. If the area is
     present but unfilled, it is a src bug of the same family as round 1's water rings.
  2. **The honey is on the suburbs, not the colleges.** Jericho, St Clement's and Iffley Road
     are solid `#e3b867`; the historic core is pale cream with green. The city's heart reads
     emptier than its edges. *Cause:* the built wash keys on `landuse=residential` and
     buildings; colleges are `amenity=university/college` areas. *Fix:* add those classes to
     `built` in the Oxford theme (or a `college` class at a deeper honey).
  3. "Cherwell" (upper copy) loses its "C" under the river stroke. *Cause:* library placer
     (along-water label overlapping its own river's stroke). *Fix:* offset along-water labels
     clear of the stroke width.
  4. "Magdalen Bridge" is lettered over three roads; a pale grey bar marks the bridge under the
     route end. *Fix:* the placer's road penalty is too weak in `roads = "all"` cities; raise
     it there.
  5. Streets and rivers run off the land onto bare paper at the top left, left and right.
     *Fix:* clip roads to the land wash in the city theme, or `ribbon_mult` up so the wash
     reaches the card edge.
  6. "start" floats in a block, away from the line.

### `places/skye.webp` (720, Skye theme). 3/5
- **Works:** the island is unmistakable, coast outlined in a darker blue, Raasay and the small
  isles alongside; the four journal notes are the most charming lettering on the site.
- **Faults:**
  1. **The mainland is painted as sea.** Everything east of the Kyle is the same blue as the
     water, with dark-blue rivers and brown roads drawn across it, so the Skye Bridge seems to
     land in the sea. *Cause:* library or fixture: the sea is filled outside the coast rings,
     and the mainland coastline is clipped open at the fetch box, so the mainland is treated
     as water. *Fix:* close open coastline pieces against the box edge before filling (the
     usual coastline-to-polygon step), or fill only polygons on the water side of the
     coastline.
  2. **The Armadale leg is drawn three times** as parallel strokes with a road showing between
     them; the Dunvegan spur is doubled too. Round 1's "parallel lines look like a fault"
     returns. *Fix:* draw a retraced section once (dedupe segments within a few px), or end
     the day at Armadale and start the next from the bridge.
  3. "Snizort" and "Sligachan" are pale blue water-ink names on land and partly covered by the
     route. *Fix:* use the land ink for these, or drop them.
  4. The Dunvegan note's leader cuts through "Coral". *Fix:* same leader-crosses-label rule as
     Ambleside.
  5. The Cuillin and Portree are not named, and the island's interior has no relief worth the
     name for the most mountainous part of Skye. *Fix:* callouts for the Cuillin and Portree;
     relief is set but too faint at this scale.

### `places/y-fenni.webp` (720, Welsh theme). 2/5
- **Works:** the idea (a food tour), the hand-placed Tŷ Melin, Castell y Fenni in Welsh, Afon
  Wysg along the water.
- **Faults:**
  1. The route is a small knot in the centre, overlapping itself, and six callouts stacked on
     the left send leaders across it and each other. It reads as a tangle, not a tour.
     *Cause:* the framing is the whole town while the tour covers a few streets. *Fix:* frame on
     the tour: much smaller `ribbon_mult` or a fixed card box round the centre, so the route
     fills half the card; then the callouts can sit beside their shops with short leaders.
  2. The terracotta built wash covers most of the card and the maroon route has little contrast
     on it. *Fix:* in this theme a paler built wash (or the honey of Oxford) so maroon stands out.
  3. "Y Fenni" is struck through by a leader and overlapped by "Gavenny River" and "B4233".
  4. "Llan-ffoyst" is lettered on bare paper with a road through it; streets run off the land.
- **Flag:** below 3. The tour needs its own framing before the labels can work.

### `places/yr-wyddfa.webp` (720, mountain theme). 3/5
- **Works:** Glaslyn and Llyn Llydaw are in and named; Llyn Peris and Padarn appear by
  Llanberis; the route is a clean traverse up Crib Goch, over Garnedd Ugain and down; the
  grey-mauve rock reads as mountain.
- **Faults:**
  1. Pale halos (lozenges) behind "Glaslyn", "Llyn Llydaw", "Crib Goch" and "A4086" are visible
     against the dark rock wash. *Cause:* library label backing. *Fix:* as on the hero.
  2. "Afon Arddu" has its "Ar" covered by a lake blob painted over the label. *Cause:* library
     placer ignores small water polygons. *Fix:* include lakes in the label obstacle set.
  3. The palette is muddy: grey-violet blotches without a sense of slope; the summit is not the
     visual peak. *Fix:* relief strength up and the darkest tone on the north-facing cwm walls.
  4. Roads and a river on bare paper at the bottom left and top right corners.

### `gallery/route-map.webp` (720, default theme). 2/5
Default Ambleside: pink `#c22050`, land on about a third of the card, roads and rivers running
onto paper. It is fine as the default look, but in the gallery it sits beside the showcase
cards and looks like a draft of them, and it is the same card as the tutorial image. *Fix:* in
the gallery use the showcase hero crop (or Lynmouth), and let the tutorial alone show the
default look. **Flag:** below 3.

### `tutorials/route-map.webp` (900, default theme). 3/5
Right image for the tutorial (it shows what the default theme gives). Landmarks are now good
(Loughrigg Fell, Pelter Bridge, St Mary's). The sticker framing of round 1's fault 1 is
unchanged in the default theme, as decided. No change needed beyond the gallery fix above.

### `how-to/command-line.webp` (720, Lynmouth, default theme). 3/5
A clean loop and the sea along the top. But the three callouts jammed on the coast are the
weakest choices on the site: "Living Waters Lynton United Reformed Church" (40 characters,
a chapel), "Saint Mary the Virgin" and "Lynton and Exmoor Museum", with converging leaders.
Lynmouth is not lettered at all. *Cause:* default `landmarks = "all"` heuristic. *Fix:* name
cap (drop names over about 25 characters) and rank churches below landmarks; letter Lynmouth.
The golden was 4 because the sea ran to the edge; this card has paper margins on three sides.

### `how-to/route-ink.webp` (720). 3/5
Does its job: violet on the default card. Fourth near-identical default Ambleside card on the
site (gallery, tutorial, route ink, four styles).

### `how-to/route-ink-grid.webp` (720x384, 4x3). 2/5
- **Works:** it exists, it is made by the `for` loop, it uses the showcase card.
- **Faults:**
  1. Cells are 180x128 px and the route is about 1 px; maroon, indigo and sienna are hard to
     tell apart, and the wet and dry rows look the same.
  2. **Multiply blackens the route over water.** The route's east side, which runs beside the
     Rothay, is near black in every column, including the pink. *Cause:* `blend = "multiply"`
     on the route effect, composited over dark river and wash. The same darkening is milder on
     the hero. *Fix:* `blend = "normal"` at opacity about 0.9 for the route, or multiply only
     over paper.
  3. No lettering: the reader cannot map columns to inks or rows to pens without the caption.
  4. Every cell crops the loop at the left.
- **Fix:** crop each cell to the loop at 2x scale; 3 inks by 2 pens (drop solid, it is the
  plain case) at about 240x180; letter each column's hex and each row's pen in the hand.
- **Flag:** below 3.

### `map-styles/bold.webp`. 3/5
Unchanged from round 1. The magenta and acid greens still look digital beside the new maroon.
Round 1's fix (a cadmium red route, `#b0201c` at 7 px) was not taken.

### `map-styles/pen-and-ink.webp`. 3/5 (up from 2)
Rydal Water is now a pale grey wash and reads as water; the black route is strong. Rivers are
still the same grey-brown as roads, so the Brathay and Rothay look like lanes, and no wood
stipple is visible. *Fix:* rivers in a blue-black or a doubled line; the stipple density
round 1 suggested.

### `map-styles/sepia.webp`. 4/5
Cohesive and handsome. "Rothay" is low contrast on the dark wash.

### `map-styles/winter.webp`. 3/5
Strong figure-ground. The slate-blue wood patches are the same tone as Rydal Water, so the lake
still loses its shape. Round 1's warmer grey-green wood (`#8f9a92`) was not taken.

## Remaining faults across the set, by payoff

1. **Leaders and labels collide** (Ambleside 720, Skye, Y Fenni, Oxford, Lynmouth). Library:
   reject a leader that crosses another label or the route near its anchor; forbid land names
   on water polygons; keep along-water labels off their own stroke.
2. **Multiply route blend** turns the ink black over water (grid, slightly on the hero).
   Theme: `blend = "normal"` or opacity, or a library rule to multiply only over light ground.
3. **Skye's mainland painted as sea.** Library or fixture: close clipped coastline at the box.
4. **Retraced routes drawn as parallel lines** (Skye Armadale and Dunvegan). Library: dedupe
   retraced segments, as the Oxford out-and-back already shows.
5. **Y Fenni framing.** Theme: frame on the tour, not the town.
6. **Oxford's meadow hole and honey on the wrong ground.** Theme (pigment classes), or src if
   the meadow's area is dropped.
7. **Label backing boxes visible** on dark washes (hero, Yr Wyddfa). Library: feather or
   glyph-shaped backing.
8. **Clipped stubs** of minor roads and streams (hero). Library: minimum length after clipping.
9. **Missing names that matter:** Grasmere, Windermere, Loughrigg Fell on the hero; the Cuillin
   and Portree on Skye; Lynmouth on its own card. Data: `places.toml`.
10. **The default card repeats** (gallery, tutorial, route ink, four styles). Docs: gallery
    takes the hero or Lynmouth.
