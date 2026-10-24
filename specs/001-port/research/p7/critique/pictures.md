# Picture critique: the non-map showcase images

Reviewer's group: `docs/images/painting-with-python/*`, `docs/images/curves/*`,
`docs/images/word.webp`, `docs/images/tutorials/*` and `docs/images/gallery/*` (route maps
excluded), `docs/images/how-to/own-shapes.webp`. Every image was viewed at 1:1 and zoomed
with nearest-neighbour crops; the lettering was re-rendered at 1x, 2x and 3x to find the
cause of the pixelation and of the "Keswick" kink. Diagnostic renders and crops are in
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/critique/diag/`
and `.../critique/pics/` (the scripts in `.../critique/scripts/`).

## Part 1. Findings that cut across the whole group

### 1.1 Lettering pixelation: the cause is the canvas, not (mainly) the skeleton grid

The maintainer's guess was "double the grid density". There are two grids, and the one
that matters most is not the one the guess points at.

- **The render grid (the main cause).** `examples/lettering.py`, `composition.py`,
  `word.py`, `how_to_own_shapes.py` all paint with `Canvas(0, 0, W, H, W, H)` and
  `NibSurface(canvas, 1.0, ...)`, i.e. one render pixel per display pixel, at the final
  published width (360, 480). A 36 px setting has an x-height of about 15 px and a nib
  about 1.5 px wide, so every stroke edge is one antialiased pixel and every counter
  (the A, the e, the b) is two or three pixels: they fill and the letters go blobby. The
  maps do not have this problem because `CardStyle.supersample = 2`.
  - Evidence: `diag/amb-scales.png` renders "Ambleside" with `Canvas(0,0,W,H,k*W,k*H)` and
    `NibSurface(canvas, k, ...)` at k = 1 (as published), 2 and 3, each Lanczos-reduced to
    360 px, plus k = 3 reduced to 720 px. k = 1 is visibly soft and blotchy; k = 2 is
    crisp; k = 3 to 720 is what the image should be.
  - **Fix (examples only, no `src/` change):** paint every lettered example at
    `SUPERSAMPLE = 3` (render canvas 3x, `NibSurface.scale = 3`, `Sheet` grain scaled by 3)
    and Lanczos-reduce. Cost is about 9x pixels on a tiny canvas, negligible.
- **The display grid (the second cause).** The docs are read on GitHub, which shows an
  image at its natural size. A 360 px image on a 2x (Retina) screen is upscaled 2x by the
  browser: every image in the tutorial rung set looks soft or stair-stepped on a laptop.
  - **Fix:** publish at twice the CSS width (720 for the 360 rungs, 960 for composition,
    1280 for the curves) and show with `<img src=... width="360">` in the Markdown. The
    `page` budget is 250 KB and these files are currently 3 to 60 KB, so there is room.
  - Raise the lossy quality too: `tutorials/paper.webp` is 3.1 KB, `wash.webp` 4.1 KB,
    `composition.webp` 8.9 KB. At that size WebP smears the grain and the lettering in
    `composition.webp` is lossy (the letters' edges ring). Paint lettered figures as
    `webp-lossless` (composition, word, own-shapes, derwentwater) or quality 90+.
- **The skeleton grid (`letters/skeleton.py`, `RASTER_EM = 128`).** This is the grid the
  "double the density" idea would touch. Doubling it to 256 helps a little at large sizes
  (the wordmark at 104 px, the hero) but does not fix the pixelation above; what it does
  touch is the next finding.

### 1.2 The "Keswick" kink: three separate causes, all real

Rendered at 3x with the mark centrelines overlaid in blue (`diag/c_sine.png`,
`diag/c_flat.png`, `diag/c_flatK.png`):

1. **Glyph skeleton artefacts (library, `letters/trace.py`).** The K's arms do not meet its
   stem: the Zhang-Suen medial axis forks at the junction and a short horizontal bridge
   runs from the stem to where the arms meet, so at 1x the K reads as "h" plus a "t"
   crossbar. That is the kink the maintainer saw. The same machinery splits the e into
   three or four near-concentric loops (`_flanks`, `FLANK_MIN 0.40`), doubles the stems of
   m and n ("Ammbleside" at 3x), splits the d into "cl" and draws the o of "pyntpot" as a
   double ring. The chains are also raw pixel staircases (`(c + 0.5, r + 0.5)` per pixel,
   no smoothing), so every diagonal wobbles at the nib's scale.
   - **Fix (src/, letters):** smooth each chain before it leaves `centrelines` (Chaikin
     twice, or a Gaussian of sigma 1.5 raster px along arc length, ends pinned); collapse
     a junction whose branches meet within one stroke width to a single node (it removes
     the K bridge); raise `FLANK_MIN` so a flank is split only when it is really two
     strokes (try 0.7) or skip flanks for glyphs under 48 px. `RASTER_EM` 256 alongside.
   - **Better long-term fix:** stop thinning a filled handwriting face. Patrick Hand is a
     marker face whose outline thins badly at junctions. A single-line (stroke) font has
     the pen path as its data and nothing to thin: the Hershey script faces, or an OFL
     single-line face (Relief SingleLine is OFL). The `outline` route at 3x
     (`diag/c_outline.png`) is clean but hollow, so it is not the answer for small names.
2. **The baseline wave is too tight for the word (example).** `composition._line` is one
   full sine period over 160 px with amplitude 12.8 px: the tangent swings through about
   ±27 degrees inside a seven-letter word. Each glyph is rotated rigidly to the tangent at
   its own centre (`Hand._along`), so neighbours meet at a visible angle at the trough.
   - **Fix:** half a period or less across the word, amplitude 0.015 H, or set the word on
     a gentle arc. A rule of thumb for a lettered path: tangent change across the whole
     word under 15 degrees.
3. **The name is not centred on its path (example).** `Setting` with a `path` only writes
   from the start (`align` must be `start`). Keswick is 101 px on a 166 px path, so it
   occupies the first 60 percent of the wave, sits left of the disc's centre and lands
   exactly on the trough. Ambleside (131 px on 180 px) is likewise left of centre.
   - **Fix (example):** measure with `hand.measure(name, size)` and trim the path to that
     arc length centred on the sheet. Worth a library helper later
     (`Setting(..., align="middle")` along a path), which is a public-API change and so an
     ADR.

### 1.3 The palette is a map legend, not a paintbox

Every non-map image takes its colour from `PIGMENTS`, whose entries are pale land-use
tints (`farmland #dfe0b0`, `water #9ec4de`, `heath #e0cda2`, `rim #c2ad91`), with
transparencies between 0.04 and 0.30. They were tuned so roads and labels read on top of
them. Used as the only colours of a picture, they give every piece the same washed-out
pastel with a black pen line on it: no darks, no warm/cool contrast, no granulating blues
or burnt earths. That is most of why the curves, the gasket and Derwentwater feel like
coloured-in diagrams. The fern escapes because its stem and dabs build depth.

- **Fix (src/, ink; ADR):** add an artist's palette beside the map palette, with real
  pigment names, a mass-tone hex, a `TRANSPARENCY` and a granulation flag: ultramarine,
  cerulean, indigo, Payne's grey, burnt sienna, raw sienna, yellow ochre, quinacridone
  rose, perylene maroon (this is also the maroon the route wants), sap green, Hooker's
  green. Until then, the examples can pass hex colours directly through `rgb()`.
- Paint with value range: a pale first wash, a mid glaze and a small accent at three
  times the density. None of the current non-map pieces has a passage darker than mid
  value except the black ink.

### 1.4 The paper edge reads as a photo vignette

On every image the "worn border" is a uniform 8 to 12 px grey blur hugging all four edges
(`pics/z_corner.png`), the look of a lens vignette or a drop shadow, not a worn or deckled
sheet. The foxing blotches are soft grey smudges about 20 px across (top right of
own-shapes, bottom of the rose and Lissajous) and read as dirt on a scanner glass rather
than foxing, which is small sharp rust-brown specks.

- **Fix (style values first, `src/` if needed):** warmer edge tint (raw sienna, not
  grey), half the width, broken by the grain noise so it is uneven; foxing as 1 to 4 px
  specks in a burnt-sienna tint, clustered, at a lower count. For the painting-with-Python
  pieces, consider no edge at all and a plain deckle so the art, not the frame, is the
  subject.

### 1.5 The pen is a plotter in the curve pieces

`brush_from_id("MAJ6-e", ...)` (pen row 6) draws a constant-width black line. The nib's
broad-pen thick and thin is computed only inside `nib_plate` for lettering; the curve,
kaleidoscope, nib-line and own-shapes scripts call `stamp` with no `wprof`, so their lines
are monoline. At 640 px they look like vector output with a paper texture behind them.
`stamp` already takes `wprof`, a width multiplier along the stroke, so swelling and
tapering lines need no library change.

## Part 2. Image by image

### word.webp (README wordmark, 480 x 270): 2/5

- Works: the idea (name lettered over two glazed discs, a blue and a green, overlap
  glazing visible) is right for a wordmark.
- Does not: the lettering is the weakest in the set yet it is the first thing a visitor
  sees. The o of "pot" is a double ring (flank split), the final t has a crossbar that
  overshoots like an f, letter heights wander more than a hand would, and edges are lossy
  and soft. The green disc sits in the lower right corner as if it slipped; the
  composition has no point of rest. 480 px at 1x on a Retina README is upscaled.
- Fixes: paint at `SUPERSAMPLE = 3`, publish at 960 and show at 480; write the word with a
  broad nib angle so thick and thin shows; fix the skeleton (1.2); place the green disc so
  its centre sits on the line through the word's x-height, overlapping the blue by about a
  third, or replace the discs with one rich ultramarine wash with a granulating edge and a
  small sienna accent. Encode lossless. Consider a deliberate tight seed choice: render
  seeds 1 to 30 and pick the best word.

### tutorials/paper.webp and gallery/paper.webp (360 x 240): 2.5/5

- Works: the grain is fine and even; it shows what the text says exists.
- Does not: the grey vignette and the grey smudge "foxing" (1.4). At 3.1 KB lossy the
  grain is smeared. It is the first image of the tutorial and it reads as a blurry grey
  rectangle.
- Fixes: 1.4 values; publish at 720 lossless or quality 92; a raking-light crop beside it
  (a 3x zoom of a corner) would actually show the grain the text talks about.

### tutorials/wash.webp and gallery/wash.webp (360 x 240): 3.5/5

- Works: soft disc with a just-visible darker rim and granulation; honest.
- Does not: a perfect circle in `water` blue is pale and digital in silhouette; the rim
  darkening is too faint to "show" at 1x; the disc is off-centre right for no reason.
- Fixes: a wobbly hand-drawn mask (perturb the radius with 2 to 3 low-frequency sines,
  seeded) so the edge is a painted edge; deeper pigment (ultramarine) so the rim and
  granulation read; centre it. Optional: a "for loop" strip of four washes at rising
  density, which is the show-not-tell the maintainer asked for.

### tutorials/brush-stroke.webp and gallery/brush-stroke.webp (360 x 240): 3.5/5

- Works: the clearest teaching image in the set. The dry olive stroke breaking into
  flecks is exactly the hand-made quality the library is for.
- Does not: the blue wet stroke is a constant-width tube with rounded caps, which reads
  as vector; both strokes start hard at the left with no entry.
- Fixes: pass `wprof` (for example `0.35 + 0.65 * sin(pi * t) ** 0.7`) so the wet stroke
  swells and lifts; use row 1 for wet and row 4 for dry as now, but give the wet stroke a
  heavier `load` so it pools at its end. A three-by-three for-loop grid of treatments
  (rows 1 to 8) would show the range in one glance.

### tutorials/pigments.webp (720 x 240) and gallery/pigments.webp (480 x 160): 1.5/5

- Does not earn its place. The page says the overlap "is not the same green in the two
  panels". Measured: the lens is RGB (177, 184, 124) multiplied against (173, 182, 117)
  glazed, a difference of 4, 2 and 8 levels. Nobody can see it. `farmland` (transparency
  0.10) and `wood` (0.05) are both near-transparent, so Kubelka-Munk and multiply agree.
- Fixes: pick a pair that disagrees: a covering pigment over a staining one and the
  reverse (for example `relief` 0.30 over `water` 0.04, both orders), or the artist's
  ultramarine under burnt sienna, which glazes to a granulating grey but multiplies to
  mud. Label each panel by hand ("multiply", "glazed") so the reader knows which is which.
  Better still, the for-loop grid: rows are pigment pairs, columns are the two modes.

### tutorials/nib-line.webp (360 x 240) and gallery/nib-line.webp (320 x 213): 3/5

- Works: a clean spiral, good dark ink, sensible framing.
- Does not: the caption promises a line "slightly uneven where the ink meets the grain";
  at 1x it is a uniform monoline. It does not show what a nib is (thick and thin with the
  direction of travel), which is the point of the rung.
- Fixes: compute a broad-nib `wprof` from the tangent angle against a nib angle of -38
  degrees (the `NibStyle.label_pen_angle_deg` default), so the spiral thickens on its
  downstrokes; publish at 720 lossless and show at 360; or a side-by-side of "pen held
  flat" and "pen at 38 degrees".

### tutorials/lettering.webp and gallery/lettering.webp (360 x 240): 2.5/5

- Works: legible, lively, the per-glyph jitter reads as a hand.
- Does not: blobby at 1x (1.1): the A is a filled blob, m has a doubled stem, d reads as
  "cl" (1.2). The name sits left of centre (1.2.3). A single word floating on blank paper
  is a lot of empty space for a page image.
- Fixes: supersample 3 and publish at 2x; centre the path; once the skeleton is fixed,
  re-pick the seed by rendering 20 and choosing; consider a small underline or a
  for-loop strip of the same name with five seeds, which shows the hand varying and is
  the strongest argument the page could make.

### tutorials/composition.webp and gallery/composition.webp (480 x 320): 2/5

- Works: the three ingredients are present and the glazing of stroke over wash shows.
- Does not: the name is crowded into the brush stroke (the stroke runs through "ck"),
  sits left of centre on the trough of a too-tight wave, and has the K kink (1.2). The
  blue stroke is a constant tube and the same blue family as the wash, so the picture is
  one note. Lossy at 8.9 KB softens the letters. As the payoff image of the tutorial it
  should be a small picture, and it is a diagram.
- Fixes: put the name above the stroke on a gentle arc, centred; give the stroke a
  `wprof` and a different pigment from the wash (sienna or sap green under the blue
  disc); make the wash a hand-shaped tarn rather than a disc; supersample 3; lossless or
  quality 92 at 960 shown at 480. It could become a tiny landscape: a pale sky wash, a
  fell stroke and "Keswick" in the foreground, which previews the maps.

### curves/rose.webp (640 x 640): 2.5/5

- Works: clean geometry, gentle fill, good margin.
- Does not: a monoline pen at constant width (1.5); the five petals' outlines converge on
  a solid black knot at the centre (`pics/z_rose.png`); the `heath` tan fill is flat and
  nearly paper-coloured, so the flower reads as a line drawing coloured with a highlighter.
- Fixes: this is the piece that most wants the brush. Split the curve at the origin into
  five petal loops and stamp each with a row-1 or row-2 brush, `wprof = sin(pi*t)**0.6`,
  so each petal is a single swelling stroke that tapers to nothing at the centre (no
  knot). Wash each petal individually in quinacridone rose or perylene maroon at a
  per-petal random density in [0.35, 0.6], with the rim darkening on, so petals differ.
  Drop the black ink or use a sepia at half density.

### curves/lissajous.webp (640 x 640): 3/5

- Works: the alternating fill (enclosed loops washed, crossings left white) is a good
  idea and makes the figure read; the best balanced of the three curves.
- Does not: constant black monoline; one flat pale blue; the knot at the centre crossing
  is heavy; nearly touches the margin top and bottom while the paper smudge sits in the
  empty bottom right.
- Fixes: keep the pen here (it is a technical figure) but give it a nib angle `wprof`, so
  the long diagonals go thin and the verticals thick; wash alternate loops in two
  pigments (cerulean and ultramarine) so the crossing pattern becomes a chequer;
  REACH 0.34.

### curves/spirograph.webp (640 x 640): 3/5

- Works: an attractive star; the overlapping washes darken nicely where petals cross.
- Does not: monoline; a small bare "hole" at the centre is drawn as a tight dark knot of
  lines; nine identical petals in one sage green are static.
- Fixes: brush instead of pen: a single long brush stroke along the whole hypotrochoid
  with `press` variation and a slowly falling `load`, so the line visibly runs drier
  towards its end (that is a property only a painted spirograph has, and it is the
  library's selling point). Graded pigment along the curve (cerulean to sap green by
  arc length, as layered washes).

### curves/kaleidoscope.webp (640 x 640): 3.5/5

- Works: the strongest of the curve pieces; reads as stained glass; blue, green and tan
  balance; symmetry is the right teaching image for its page.
- Does not: the inner blue petals and the green ones behind them are crowded, and the
  hexagram at the centre is a tiny dark clot; the thin rays crossing the ring look
  vector-precise; everything is the same line weight.
- Fixes: drop the inner green petal layer or halve its reach; replace the clot with a
  single washed disc in a strong accent (perylene maroon); outline in two weights (heavy
  for the ring and petals, light for the rays) via `wprof`; deepen the blue to cerulean
  with granulation; a radial graded background wash inside the ring would make it glow.

### painting-with-python/fern.webp (600 x 800): 4.5/5, keep unchanged

- Works: the best image in the docs. A recognisable Barnsley fern that looks pressed and
  painted: two greens, a thin inked stem, the dabbed texture of the fronds, generous
  paper. The maintainer is right.
- Minor and not to be acted on (the fern stays as it is): the pale "holes" between
  pinnae read a little like bites, and the two lowest pale pinnae are a different green
  from the rest, which some will read as a choice and some as an error.
- Leverage it: the fern is the model for a "family" image (Part 3): the same IFS with its
  four maps perturbed a few percent per seed gives a sheet of distinct ferns.

### painting-with-python/gasket.webp (640 x 640): 1.5/5, replace

- Does not: the four largest discs take two thirds of the circle and are flat pale
  pastels, so the eye sees five balloons, not a fractal. The defining property of an
  Apollonian gasket (circles that only touch, with ever smaller circles in the gaps) is
  destroyed by `OVERLAP = 1.1`: discs overlap into lenses and the gaps, where the fractal
  lives, are filled by the container's `wetland` wash. Depth 5 with `MAX_CIRCLES = 300`
  stops long before self-similarity is visible. The deepest circles fall in the `rim`
  layer and the sub-`SMALL_PX` ones are flat discs at 1.3x density, which is why they
  read as brown beads or dirt. Overall mean colour is a muddy grey-green.
- Could it be saved? Partly: `OVERLAP = 0.94` so bare paper separates every pair; no
  container wash; depth 9 to 10 with `MAX_CIRCLES = 4000` and circles below 3 px dropped;
  colour by depth in one family (largest pale cerulean, smaller deeper, smallest
  indigo), or by integer curvature modulo 3 in three pigments; ink each circle with a
  fine nib so the tangencies read; a less symmetric seed such as curvatures
  (-6, 11, 14, 15). That would make an honest diagram of a gasket. It would still be a
  diagram: nested circles are a mathematician's fractal and do not exercise a brush.
- **Replace with a recursive tree** (deterministic recursion, so the page still contrasts
  "an IFS (the fern) and recursion (the tree)"). `branch(p, angle, length, depth)` with
  two or three children, child angle spread 20 to 35 degrees perturbed per seed, length
  ratio 0.68 to 0.78 perturbed, a little gravitational droop. Paint each branch with a
  brush whose width follows depth (`wprof` from parent width to child width, so joints are
  continuous), trunk in burnt umber at row 1 or 2, twigs at the deepest levels in the pen
  (row 6) at low density: the brush-to-pen hand-off is exactly what this library does
  that others do not. Optional canopy: at the leaf tips, seeded dabs of sap green and
  raw sienna (autumn) with `km_glazing`, as the fern does. It paints beautifully in
  watercolour, it is nature (it sits next to the fern), and it gives a family for free
  (Part 3). A winter hawthorn or a wind-bent Lakeland oak are good named targets.
- Second choice: **a cow parsley umbel** (umbels of umbels, two or three levels): fine
  pen stems radiating from a point, each ending in a cluster of tiny white flowers that
  are *reserved* (left as paper) against a loose blue-grey background wash. Negative
  painting is a real watercolour technique and would be new in the docs.
- Avoid: Mandelbrot and Julia sets, dragon and Hilbert curves, Sierpinski triangles; all
  read as computer art however they are painted.

### painting-with-python/derwentwater.webp (720 x 480): 3/5

- Works: real ambition: recession by layered hill washes, a reflected lake with horizontal
  streaks, an island, a lettered title. The cool far hills and the warm sky band are the
  right idea. The title lettering is the best lettering in the group (flat setting, larger
  size).
- Does not: the middle and near hills are a coarse speckle of granulation that reads as
  camouflage print or a JPEG of a hedge, not as a wash; there is no soft edge anywhere;
  the shoreline is a ruler-straight dark band across the full width; the island is a
  flat blob of the same speckle floating on that line; values are all mid-light, so
  there is no focal point. The lake reflects nothing of the hills' shapes clearly.
- Fixes: halve the granulation amplitude on the near hills and wet-blend (blur the mask
  edges by 6 to 10 px) the far ones so aerial perspective is soft-far, crisp-near; break
  the shoreline with a perturbed bank and let the reflection be the hills' silhouettes
  inverted and streaked, not a band; give the island a darker accent (sap green plus a
  touch of indigo) and a pale reflection; one dark passage (the near fell's shadow side in
  indigo) to anchor the value range; sky as a graded wet-in-wet wash from cerulean at the
  top to the warm band. Supersample 3 for the title; check "Derwentwater" for the w
  artefact at 3x.

### painting-with-python/svg-drawing.webp (720 x 480): 2.5/5

- Works: shows the SVG route (filled paths washed, strokes inked) and has charm: birds,
  sun, two trees.
- Does not: transparent glazing makes the far fell show through the main fell as a dark
  green band across its middle, so the near hill looks like glass; the `skyline` stroke
  only covers the left half of the main fell's outline (it ends at x = 470 of 600 in the
  SVG) and starts at (150, 300), inside the left bank, so the black line visibly runs
  down into the field; the wall (two parallel pen lines plus ticks) reads as a railway or
  a fence, not a dry-stone wall; the tarn the caption describes as "on the fell" is a
  small blue smear at the fell's foot; the sun is near the paper colour.
- Fixes, mostly in `examples/drawings/fell.svg`: subtract each nearer fill from the ones
  behind it (paint around, as a painter would), or give the near fell a covering pigment;
  extend the skyline path to the full outline and start it at the fell's foot on the
  bank's top edge; draw the wall as a row of small irregular stones (short pen arcs) on
  one line; move the tarn up onto the fell's shoulder (around y = 200) as the caption
  promises, or fix the caption; sun in raw sienna at higher density.

### how-to/own-shapes.webp (480 x 320): 2.5/5

- Works: does what the how-to says (your own mask, a wash, a pen skyline, a lettered
  name) in a few lines.
- Does not: the wash ends in a ruler-straight bottom edge, so the fell is a bar chart;
  black monoline skyline; "Skiddaw" is small, left of centre and straddles the wash's
  bottom edge (half the word on wash, half on paper); a grey smudge of foxing top right.
  Lettering pixelation as 1.1.
- Fixes: fade the wash out at the bottom (multiply the mask by a vertical ramp over the
  lowest 15 percent) or end it on a perturbed line; skyline with a nib `wprof`; set the
  name centred under the fell on clean paper, 44 px, supersampled; seed with no foxing
  in the sky; Skiddaw's real profile (the long south-west ridge and Little Man) would make
  it recognisable to Lakeland readers.

## Part 3. Procedural nature pieces: families from small perturbations

The maintainer wants procedural generation that yields a varied family. The strongest
format for the docs is a grid painted by a `for seed in range(n)` loop, which is also the
"show, not tell" ask. Each idea lists what is perturbed and why it paints well.

1. **A fern family** (beside the unchanged fern): the four IFS maps' coefficients each
   perturbed by about 3 to 6 percent per seed (keep the stem map fixed), plus the
   leaflet green chosen from two or three greens. Nine ferns in a 3 by 3 grid: some
   upright, some arching, some lacy. Proven code path; instantly reads as "one species,
   nine plants".
2. **A copse of trees** (the gasket's replacement, Part 2): branch angle, length ratio,
   droop and branching count perturbed; a row of five on one ground wash at receding
   scale reads as a hedge line or a copse. Brush-to-pen hand-off is a showcase.
3. **Unique snowflakes**: six-fold symmetry (it reuses the kaleidoscope page's mirror and
   rotation code) with a random dendrite grown on one twelfth: side branches at random
   positions and lengths. Painted as cerulean washes with ink edges on a blue-grey sheet,
   a 3 by 3 grid makes the "no two alike" point visibly. Links fractals to symmetry.
4. **Beck pebbles**: noise-perturbed ellipses (radius perturbed by a few low-frequency
   sines), each washed in a granulating earth (burnt sienna, raw umber, Payne's grey)
   with a pale highlight reserved and a wet shadow under it. Granulation is where the
   paper engine shines and pebbles hide no flaw. A "handful from the Greta" sheet.
5. **Seed heads by phyllotaxis**: florets at the golden angle with the angle and radius
   jittered per seed (dandelion clock, teasel, sunflower). Pen dots and seeded washes; the
   jitter is visible as character, not error.
6. **Leaves**: a midrib and veins grown by a small branching rule, the blade a perturbed
   superformula or Bezier outline; washed wet-in-wet from green to raw sienna to
   perylene maroon by seed, an autumn sheet. Strong colour, shows glazing.
7. **Fell skylines**: midpoint-displacement ridges (Derwentwater already has `_ridge`)
   with roughness and seed varied; nine small landscape thumbnails, each three washes
   deep. This connects the nature pieces back to the maps.

Painting notes for all of them: vary the pigment per member as well as the shape; leave
real paper between members; keep each member small and the sheet generous, as the fern
does.

## Part 4. Ranked top 10 fixes (biggest visual payoff first)

1. **Supersample every lettered example 3x** (`Canvas` render size and
   `NibSurface.scale` = 3, grain scaled) and Lanczos down: fixes most of the pixelation in
   lettering, composition, word, own-shapes and Derwentwater. Examples only.
2. **Publish at 2x the display width** with `<img width=...>` and raise WebP quality (or
   lossless for lettered figures); everything currently upscales on Retina screens and
   the 3 to 9 KB lossy rungs are smeared.
3. **Fix the glyph skeleton** in `letters/trace.py`: smooth chains, collapse near
   junctions (the K bridge, the "Keswick" kink), stop spurious flank splits (doubled e, m,
   o, d); `RASTER_EM` 256. Longer term, a single-line stroke font. `src/` change.
4. **Replace the gasket with a recursive tree** painted brush-to-pen with depth-tapered
   `wprof` (cow parsley umbel as second choice).
5. **Add an artist's palette** (ultramarine, burnt sienna, indigo, perylene maroon and so
   on) and paint the non-map pieces with real darks; `src/` change plus ADR, or hex
   colours in the examples meanwhile.
6. **Rebuild the pigments rung** so the two panels visibly differ (a covering pigment
   over a staining one, both orders, hand-labelled); today it fails its own caption.
7. **Brush, not pen, for the rose and spirograph**: per-petal tapered strokes via
   `stamp(..., wprof=...)`, a drying single stroke for the spirograph; nib-angle `wprof`
   for the Lissajous, nib-line and skylines.
8. **Composition and lettering layout**: centre the name on a trimmed path, gentle wave
   (under 15 degrees of tangent change), keep the name off the brush stroke.
9. **Paper edge and foxing**: warmer, narrower, broken edge; foxing as small rust specks,
   not grey smudges; it touches every image.
10. **Add a for-loop family sheet** (ferns from perturbed IFS maps, then snowflakes or
    pebbles) and fix the SVG drawing's glazing-through and half skyline.
