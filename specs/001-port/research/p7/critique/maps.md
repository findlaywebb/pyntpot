# Map images: art-direction critique

Group: every map image (hero, five place cards, four map styles, tutorial and gallery route
maps, route-ink how-to, social preview), with the Lynmouth golden `tests/golden/lynmouth/map.png`
as the reference. Crops are in
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/critique/crops-maps/`.

## The diagnosis in one paragraph

I agree with the maintainer on every map point, and the causes can be traced to specific
settings. Three things together keep the cards from looking iconic. (1) **Framing.** The
painted land is a torn "ribbon" only about 0.4 to 1.25 km round the route (`ribbon_min_m` /
`ribbon_max_m`, `ribbon_mult = 1.0`), but the card is framed as if the ribbon were 1.55 times
wider (`card_grow_mult = 1.55`). So every card is a small sticker of land floating on a lot of
bare cream paper, with orange roads and blue rivers running off it onto nothing. Lynmouth works
because the sea runs to the edge (`sea_to_edge`) and the land fills most of the frame. (2)
**The route ink.** `#c22050` with `glow_opacity = 0.8`, `glow_px = 2.5` and a cream casing
(`route_inks.ride.effect`) is a screen magenta with a halo, which is the digital look. The sepia
style (`#8a3418`, no glow) already shows that an earthy red reads as painted. (3) **No terrain.**
`hillshade_mode = "off"`. The painter ignores hillshade, contours and hachures entirely: they
reach only the basemap/candidate export, never the painted plates. The only relief on a card is
`cover.relief`, whose density is hard-coded at most 0.30 to 0.40 in
`src/pyntpot/maps/painter/paper.py::relief_density` and laid in a pale `#c9bda4` at
transparency 0.3. Yr Wyddfa and the Quiraing therefore look as flat as Oxford.

## Per image

### `docs/images/hero.webp` (Keswick, 1200 px, README hero). Score 2/5
- **Works:** the paper, the torn ribbon edge and the soft wash of Derwentwater; the Greta and
  Derwent as fat blue brush strokes have real presence; the lettering is legible at this size.
- **Does not work:**
  - Land covers about 35% of the card. The left third is bare paper with two orphaned river
    strokes, and the bottom right holds only a lone A-road. Nothing tells the eye where to look.
  - The route is a tangle, not an icon. It has three spurs. The out-and-back down to Friar's
    Crag is drawn as two parallel lines a few pixels apart, which looks like a rendering fault.
  - The magenta has a pale halo.
  - The landmark choice is weak: "The Retro Zone" (OSM `tourism=museum`, a retro games shop
    and museum on Main Street) is lettered with a leader as if it were the town's landmark.
    "Lake Road Chapel" is minor too. The fixture holds Moot Hall, Friar's Crag, the Pencil
    Museum, St Kentigern's and Castlehead, and summit names (Skiddaw, Latrigg) are in reach.
  - The "7" in "A5271" reads as "?".
- **Earns its place?** No. It is the first image a visitor sees and shows the library's weakest
  framing. The maintainer wants Ambleside, and I agree a new place is the right call. Keswick is
  also used five more times on the page (tutorial, gallery, how-to, styles, social), so the hero
  should not repeat it.
- **Fixes:**
  1. New fixture: Ambleside with the head of Windermere, Rydal Water and Loughrigg. The route
     should be one clean closed loop, for example Ambleside, Rydal, Loughrigg Terrace, back by
     Loughrigg Tarn. Build it with `tests/fixtures/make_track.py --ways` (needs a network
     session). Avoid out-and-back spurs: a closed loop is what makes Lynmouth read as an icon.
  2. Fill the frame: `ribbon.ribbon_mult = 1.5` (the frame already allows for 1.55),
     `ribbon_max_m` about 2500, and consider `card_pad_frac` 0.05. The aim is land touching or
     nearly touching three edges, with paper as a margin rather than a void.
  3. Maroon route (see the top-10).
  4. Name the landmarks: `basemap.pick_landmarks = [...]` in a per-place theme, the way
     `examples/themes/y-fenni.toml` does it.
  5. Relief on (needs src, see the top-10). Fell country is the point of an Ambleside hero.

### `docs/images/places/keswick.webp` (720). Score 2/5
Same composition as the hero at 720 px, with the same issues. The extra "B5289" label sits
alone on blank paper. The "Greta" label is drawn twice (fine) but one copy sits in pale ink
over the dark river, where it is barely legible. The cramped junction near "The Retro Zone"
has five brown lanes, the route and two leaders crossing in about 40 px. **Fix:**
`pick_landmarks = ["Moot Hall", "Friar's Crag", "St Kentigern's Church"]` (check the exact OSM
names), widen the ribbon as above, and trim the Friar's Crag spur from the route or make it a
loop.

### `docs/images/places/oxford.webp` (720). Score 1/5
- **Biggest fault: the "flood plain".** A dark, bleeding blue mass covers the Cherwell from
  Magdalen Bridge north, spills off the ribbon onto bare paper and runs up to the top edge. This
  is a **src bug, not data**. `src/pyntpot/maps/osm_elements.py::_area` keeps only the outer
  rings of a `natural=water` area (`outer, _ = _area_rings(...)`) and throws away the inner
  rings. The Cherwell's riverbank multipolygon (relation 1046961 in the Oxford fixture) has 8
  outer and 14 inner members. The inners are the islands and meadows between the Cherwell's
  channels, so dropping them fills the whole braided reach as solid water. Relation 1083245 (5
  outer, 8 inner) and 36896 (12 outer, 5 inner, the Thames/Isis reach south of Christ Church
  Meadow) are hit the same way. That probably explains the "odd Isis" too. Wood keeps its holes
  (`found.wood_holes`), and lakes need the same. A knock-on effect: the wide fake water makes
  the lettering class "Holywell Mill Stream" as `in_water` (`picks_rivers.py`, `IN_WATER_CAPS`),
  so it is lettered in near-white `label_in_water_ink` across paper and land, where it is
  illegible. The water is also not trimmed to the ribbon.
- **Thin city:** `basemap.roads = "key"` draws only major roads plus the ones the route touches.
  In a city that leaves about ten strokes and no street grid. Also, `lane` is 1.8 px against
  `road_major` 3.6 px.
- **Route:** the small square inside Christ Church (Tom Quad) reads as a glitch at this scale.
  The maintainer's route (Queen's Lane, Radcliffe Camera, out and back over Magdalen Bridge,
  back through Christ Church) needs a new `track.gpx` from `make_track.py`. Radcliffe Camera,
  Queen's Lane, Magdalen Bridge, Sheldonian, Bodleian and Carfax are all in the fixture.
- **Labels:** "Christ Church" placed beside "start", and a crowded "Tom Tower" leader.
  Missing: the Radcliffe Camera, the Isis/Thames and the High.
- **Fixes:**
  1. src: keep inner rings for `natural=water` and subtract them, as wood does.
  2. An Oxford theme (copy `y-fenni.toml`'s pattern) with `roads = "all"`,
     `brush_width_px.lane = 2.4`, `pick_landmarks = ["Radcliffe Camera", "Magdalen Tower",
     "Tom Tower", "Sheldonian Theatre"]` and `pick_roads = ["High Street", "Queen's Lane"]`.
  3. A new route as above.
  4. A building wash: `cover.pigments.built` is `#ddd3c3`, almost paper. For a city, a warm
     Cotswold-stone ochre such as `#d9c08f` at transparency about 0.18 would make the colleges
     read as a solid honey-coloured core.

### `docs/images/places/trotternish.webp` (720). Score 2/5
- **Works:** the hand lettering of the Gaelic names; Fir Bhreugach is a good pick.
- **Does not work:**
  - The Quiraing is one of the most dramatic escarpments in Britain, and the card shows a pale
    grey-cream oval with no relief, almost no land cover and no Trotternish ridge.
  - The route is out and back on two nearly parallel lines, which again looks like a fault
    rather than a walk.
  - The ribbon covers about 20% of the card; the rest is one road and a river.
  - "Brogaig" is lettered in water ink because it is OSM's "River Brogaig" with the "River"
    dropped. That reads as a settlement in the wrong ink, so letter the full name or drop it.
  - The Needle and Meall na Suiramach are in the fixture but not lettered.
- **Fixes:** relief (src); a route loop over Meall na Suiramach (the classic Quiraing circuit)
  rather than out and back; `pick_landmarks = ["The Needle", "The Prison", "Meall na
  Suiramach"]`; widen the ribbon. Heath and rock pigments need to show on moorland: if OSM has
  no cover there, the pale base (`pale_base 0.5`, `pale` `#d5e0b4`) is all there is, so lift
  `pale` towards a moorland ochre-green such as `#cdbf8e`.

### `docs/images/places/yr-wyddfa.webp` (720). Score 2/5
- **Works:** the route's stroke wobbles nicely along Crib Goch. The names Garnedd Ugain, Yr
  Wyddfa and Crib Goch are right. The diagonal composition is the best of the five places.
- **Does not work:**
  - No mountain. The highest point in Wales, and the ground is a flat sage wash.
  - Glaslyn and Llyn Llydaw, the defining lakes of the Horseshoe, are in the fixture
    (`Glaslyn` way, `Llyn Llydaw` relation) but appear only as three tiny pale spots, because
    the lakes are trimmed to the narrow ribbon. Llyn Padarn and Llyn Peris by Llanberis are
    missing entirely.
  - "fon Arddu" is clipped at the left edge: the label has run off the card ("Afon Arddu").
    That is a placement bug (src, lettering window).
  - The summit has no mark heavier than the leader dot.
  - "Nant Peris" and its leader sit in empty paper.
- **Fixes:** widen the ribbon so the cwm and its lakes are inside (`ribbon_mult` 1.5,
  `ribbon_max_m` 2500); relief (src); a darker rock/relief pigment for mountains (`relief`
  `#8e8577` and `rock` `#b9b1a3` in a "mountain" theme); keep labels inside the card (src).

### `docs/images/places/y-fenni.webp` (720, Welsh theme). Score 2/5
- **Works:** Afon Wysg is lettered twice along the water, well spaced. The theme shows off
  `name_tags`.
- **Does not work:**
  - The route is a small scribble inside the town, smaller than the road network around it.
    The orange roads dominate the card.
  - The landmarks are three chapels and a theatre (United Reformed Church, Methodist Church,
    Borough Theatre), while the castle and St Mary's Priory are in the fixture and the Blorenge
    and Ysgyryd Fawr are in summit reach.
  - "Gavenny River" is the English name on a card that claims Welsh, because OSM carries no
    `name:cy` there. That is a data gap, so either accept it or `pick_` around it.
- **Fixes:** a route round Castle Meadows and the castle, out along the Usk; `pick_landmarks =
  ["Abergavenny Castle", "St Mary's Priory", "Blorenge", "Ysgyryd Fawr"]`; quieter roads
  (`roads = "major"` in this theme, or a paler road ink); widen the ribbon.

### `docs/images/map-styles/bold.webp`. Score 3/5
It does what the page claims (saturated, thick magenta). As a picture it is garish: the
`#e6007a` 8 px route and the acid greens look like a GIS default, not paint. It is useful as a
contrast, but call it "bold" rather than make it look loud. **Fix:** keep the high saturation
but make the route a deep cadmium red, `#b0201c` at 7 px, so it still looks pigment-based.

### `docs/images/map-styles/pen-and-ink.webp`. Score 2/5
The best idea in the set, but it under-delivers. Derwentwater vanishes into a mid-grey blot
that reads as a stain. The wood "ink stipple" the theme comment promises is not visible at
720 px. The Greta label sits on top of a road. The rivers are the same grey as the roads, so
the water reads as a road. **Fix:** water as a light hatch, or a clearly darker `label_water_ink`
river stroke. Raise the stipple density (`cover.wood_dabs` / `dab_strengths`), and give the
roads a thinner pen than the rivers (`river_mult` 0.5 is already set, so the roads need
`brush_width_px` lowered). It might be the most striking style of all if the lake read as water.

### `docs/images/map-styles/sepia.webp`. Score 4/5
The most cohesive map in the whole group. The foxing, the vignette and the brown washes hang
together, and the route `#8a3418` is the closest thing to the maroon the maintainer asked for.
**Evidence for the maroon change:** it reads as ink, not screen. Small issues: the "Greta"
labels are low contrast on the dark river, and the vignette is heavy at the corners.

### `docs/images/map-styles/winter.webp`. Score 3/5
It reads clearly as "winter". The scarlet route `#c8321e` on blue-white is the strongest
figure-ground contrast in the set. Derwentwater and the wood washes in grey-blue merge, so the
lake loses its shape. **Fix:** make the wood a warmer grey-green, such as `#8f9a92`, so the lake
stays the coolest thing on the card.

### `docs/images/tutorials/route-map.webp` (900). Score 3/5
This is the payoff image of the main tutorial, and it does show every layer the tutorial
builds (washes, rivers, roads, lettering, route). Same framing and route problems as the hero.
Keswick is fine here, as the place the tutorial teaches with. **Fix:** inherit the default-theme
changes (maroon, wider ribbon). There is no need for a new place.

### `docs/images/gallery/route-map.webp` (720). Score 2/5 in context
It is byte-different from `places/keswick.webp` but visually the same card. The gallery page
then shows Keswick at 720 in near-identical form four or five times (command line, route map,
places, route ink, styles). **Fix:** reuse one file, or have the command-line how-to show a
different place (Lynmouth, which is already a golden and the best composed map in the repo).

### `docs/images/how-to/route-ink.webp`. Score 3/5
The violet change is clear, but one image cannot show what "change the ink" means. The
maintainer asked for a grid made by a `for` loop. **Fix:** a 2x2 or 3x1 grid of the same crop
round Keswick in maroon `#7a1f2b`, sepia `#8a3418`, violet `#5b2a86` and black `#15110d`, each
lettered with its hex in the hand. It would also show the user that the route plate is tinted
at compose time, without a repaint.

### `docs/images/social-preview.jpg` (1280x640). Score 2/5
The left half is the Keswick card, cut off at its left edge. The right half is a large blank
area holding a "pyntpot" wordmark over two overlapping wash circles. At the 300 to 600 px sizes
a link card is shown, the route is a thin pink scribble, and the attribution sits stranded in
the centre bottom. **Fix:** a tight crop of the best map (the new Ambleside hero or Lynmouth)
across the full width, with the wordmark lettered on the map as a title cartouche. Or put the
fern beside the map, since it is the maintainer's favourite image.

### `tests/golden/lynmouth/map.png` (reference). Score 4/5
Why it works:
- The sea runs to the edge, giving a solid, dark top band.
- The land fills about 65% of the frame.
- One clean closed loop, read in an instant.
- The East Lyn's deep blue against the green valley.
- "Lynton" lettered big and underlined.

Its flaws are a cluster of four labels jammed along the coast ("Lyn Valley Art and Craft
Centre" is the same shop-as-landmark mistake) and the same glowing magenta. Use it as the
template the other cards should move towards.

## Ranked top 10 fixes (biggest visual payoff first)

1. **Maroon route, no glow** (default theme): every `route_inks.*.colour` and
   `nib.label_route_ink` set to a perylene-maroon such as `#7a1f2b`; `route_inks.ride.effect`
   with `glow_opacity = 0`, `glow_px = 0`, `casing_px = 0`; px about 4.6. One TOML edit
   repaints every map.
2. **Fill the frame:** `ribbon.ribbon_mult = 1.5` (the framing already assumes 1.55) and
   `ribbon_max_m` about 2500, so land fills about 65% of each card as in Lynmouth. This also
   brings Glaslyn and Llyn Llydaw onto the Yr Wyddfa card.
3. **src bug: keep inner rings of water areas** (`osm_elements.py::_area`). This fixes the
   Oxford "flood plain" (Cherwell relation 1046961, 14 inners dropped), the Isis reach, and the
   white "Holywell Mill Stream" label.
4. **New Ambleside hero** on a single closed loop (new fixture with `make_track.py`), with
   Windermere, Rydal and Loughrigg in frame.
5. **Visible relief (src):** expose a relief strength (today hard-coded at 0.30/0.40 in
   `painter/paper.py`), and/or paint hachures or contour pen lines on the plate; `hillshade_mode`
   currently never reaches the painted card. Use a darker `relief` pigment (`#8e8577`) for
   mountain cards.
6. **Landmarks chosen, not scraped:** a per-place `pick_landmarks` (Keswick: Moot Hall, Friar's
   Crag; Oxford: Radcliffe Camera, Magdalen Tower; Y Fenni: castle, priory, Blorenge;
   Trotternish: The Needle). Also review `landmarks = "all"` in `default.toml`, which bypasses
   `LANDMARK_CLASSES` (the dataclass default is `heuristic`).
7. **Oxford theme:** `roads = "all"`, a wider `lane` brush (2.4 px), a honey `built` wash
   (`#d9c08f`), and the maintainer's Queen's Lane / Radcliffe Camera / Christ Church route.
8. **Routes as loops, not out-and-backs:** the doubled parallel lines on Keswick (Friar's Crag)
   and Trotternish look like rendering faults. Re-route, or draw a retraced section once.
9. **A route-ink grid** on the how-to page (a `for` loop over four inks), and stop reusing the
   same Keswick card on five gallery entries; give the command-line how-to Lynmouth instead.
10. **Lettering fixes (src):** "Afon Arddu" clipped at the card edge on Yr Wyddfa; the "7" in
    "A5271" reads as "?"; leaders crowding the junction at Keswick. Also the social preview
    rebuilt as a full-width map crop with the wordmark as a cartouche.
