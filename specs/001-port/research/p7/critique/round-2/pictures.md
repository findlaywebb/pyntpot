# Picture critique, round 2: the non-map images (P7.V13)

Same group and rubric as round 1 (`../pictures.md`, scores out of 5). Viewed at 1:1 on
`p7-wip` at `1b434aa`, with nearest-neighbour crops of every lettered passage. Scratch
renders and crops are in
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/crit2/`.
Group: `painting-with-python/*`, `curves/*`, `tutorials/*` (not `route-map`), the gallery
and README thumbnails in `gallery/*` (not `route-map`), `word.webp`, `how-to/own-shapes.webp`.

What this round answers from section 10 of `p7-research.md`: for-loop grids (show, don't
tell), the fern unchanged, procedural families, the brush for curves, lettering
pixelation, the Keswick kink, the SVG shown raw and step by step, and trees in place of
the gasket.

## Scores

| Image | R1 | R2 | Change in one line |
|---|---|---|---|
| `word.webp` | 2 | 2.5 | Letters now clean (no double o); layout, lossy ringing and the slipped green disc remain |
| `tutorials/paper` (= `gallery/paper`) | 2.5 | 3 | Warm narrow edge replaces the grey vignette; still nearly blank, 3.4 KB lossy |
| `tutorials/grid-paper` | new | 3 | Classic and warm read; tooth across barely reads at 150 px cells |
| `tutorials/wash` (= `gallery/wash`) | 3.5 | 3.5 | Unchanged drawing, new paper |
| `tutorials/grid-wash` | new | 3 | Density across reads; the seed rows look almost the same |
| `tutorials/brush-stroke` (= `gallery/brush-stroke`) | 3.5 | 3.5 | Unchanged |
| `tutorials/grid-brush` | new | 4 | Best grid: four treatments by three widths, the dry breakup reads |
| `tutorials/pigments` (720) and `gallery/pigments` (480) | 1.5 | **1.5** | Unchanged: still `farmland` over `wood`, still fails its caption; also a README thumbnail |
| `tutorials/grid-pigments` | new | 4 | Real pigments, strong colour; multiply and glaze differ visibly in pairs 2 and 4 |
| `tutorials/nib-line` (= `gallery/nib-line`) | 3 | 3 | Unchanged monoline spiral |
| `tutorials/grid-nib` | new | **2.5** | A soft grey drop shadow round every word; bold blobby letters hide the angle effect |
| `tutorials/lettering` (= `gallery/lettering`) | 2.5 | 3.5 | Pixelation fixed: open A, single m stems, a real d |
| `tutorials/grid-lettering` | new | 3 | Shows the hand varying well; same drop shadow as grid-nib |
| `tutorials/composition` (= `gallery/composition`) | 2 | **2.5** | Letters crisper and the K whole; layout unchanged (name on the stroke, left, on the trough) |
| `tutorials/grid-composition` | new | 3 | Better layout than the single image; the backing wash reads as a white-out label |
| `curves/rose` | 2.5 | 3.5 | Brushed petals tapering to the centre, no knot, real rose pigment; outline too even |
| `curves/lissajous` | 3 | 3 | Unchanged |
| `curves/spirograph` | 3 | 3 | Now brushed, but crossings no longer deepen and the colour changes in three hard steps |
| `curves/kaleidoscope` | 3.5 | 3.5 | Unchanged |
| `painting-with-python/fern` | 4.5 | 4.5 | Drawing unchanged as asked; the warm paper suits it |
| `painting-with-python/fern-family` | new | 4 | Reads at once as one species, nine plants; crowded to the top edge |
| `painting-with-python/tree` (gasket's replacement) | 1.5 (gasket) | 3 | A real improvement over the gasket; limbs sit on top of the foliage and the crown is a ring of bubbles |
| `painting-with-python/tree-family` | new | 3.5 | Nine distinct trees of one kind; crowns touch the sheet edges and each other |
| `painting-with-python/derwentwater` | 3 | 3 | Title lettering now clean; the painting is unchanged |
| `painting-with-python/svg-flat` | new | 4 | Does its job: the SVG as drawn, flat on white |
| `painting-with-python/svg-washes` | new | 3.5 | Clear step; trees become flat dark dots |
| `painting-with-python/svg-ink` | new | 3 | Clear step; the wall reads as a ladder |
| `painting-with-python/svg-drawing` | 2.5 | 3.5 | The round-1 faults are fixed: no glaze-through, full skyline, tarn on the fell |
| `how-to/own-shapes` | 2.5 | **2.5** | Letters crisper; the layout faults are all still there |

`gallery/lettering`, `composition`, `paper`, `wash` and `brush-stroke` are byte-identical
to their `tutorials/` copies. `gallery/nib-line` and `gallery/pigments` are smaller
renders of the same drawings, so they take the same scores.

### Under 3

1. `tutorials/pigments.webp` and `gallery/pigments.webp`: 1.5. The second one is in the README's thumbnail row.
2. `tutorials/grid-nib.webp`: 2.5.
3. `tutorials/composition.webp` and `gallery/composition.webp`: 2.5. Also a README thumbnail.
4. `how-to/own-shapes.webp`: 2.5.
5. `word.webp`: 2.5. It is the README wordmark.

## Part 1. What improved across the group

- **Lettering pixelation is fixed.** The nib plate is now painted at scale 2 and reduced
  with Lanczos. At 5x crops, "Ambleside" has an open A, single m stems and a d that no
  longer reads as "cl". "Derwentwater", "Skiddaw" and "pyntpot" are clean and the o in
  "pyntpot" is a single ring. One spacing fault is left: a gap after the i in "Ambleside"
  ("si de") and in "Skiddaw" ("Ski ddaw"). It looks like the dot's advance; see 1.3.
- **The Keswick kink is gone at the glyph level.** In `composition`, `grid-lettering` and
  `grid-composition`, the K's arms meet its stem with no "h plus crossbar" bridge. The
  composition-level cause from round 1 (1.2.2 and 1.2.3: a tight wave and a name that is
  not centred) is still in `tutorials/composition` (Part 2).
- **Show, don't tell, landed.** Every rung has a grid. `grid-brush` and `grid-pigments`
  are the strongest teaching images in the docs. `grid-pigments` also fixes round 1's
  pigments complaint (Part 2), but the old single `pigments` image is still published
  next to it.
- **The procedural families landed.** `fern-family` and `tree-family` read as one species
  with nine members, which is what the maintainer asked for.
- **The paper.** The warm, narrow, uneven edge replaces the grey lens vignette everywhere.
  The rust specks are present but at 1x they are almost too small to see. That is
  acceptable.
- **The SVG page** now shows the raw SVG as code blocks, then flat, washes, ink and the
  finished painting. The round-1 drawing faults (glaze-through, half skyline, tarn at the
  foot) are fixed.

## Part 1b. New faults that cut across several images

### 1.1 Drop-shadow halo round wide-nib lettering (`grid-nib`, `grid-lettering`, a little in `grid-composition`)

Every word in `grid-nib` (pen width 3.6 px) and `grid-lettering` (2.6 px) has a soft grey
halo 3 to 8 px wide below and around it. At 1x it reads as a Photoshop drop shadow.
`tutorials/lettering` (1.5 px pen) does not have it.

- **Cause, reproduced** (`crit2/halo2.py`): the pen's ink pooling,
  `BrushStyle.pen_pool_radius_frac = 0.5` with `pen_pool_gain = 1.9`. The pool's blur
  radius scales with the pen width, so a pen over about 2 px spreads a blot past the
  stroke. Measured mean darkening in a ring 3 to 8 px from the ink, for the same word:
  0.0083 at 2.6 px with the defaults, 0.0008 at 1.5 px, and 0.0 at 2.6 px with
  `pen_pool_gain=0` or `pen_pool_radius_frac=0.1`. The backing wash plays no part: the
  result is the same with `label_wash=False`.
- **Smallest fix (examples):** in `tutorial_grids._letter`, pass
  `BrushStyle(pen_pool_radius_frac=0.15)`, or use pen widths of 2 px or less and a larger
  `Setting` size.
- **Library fix (backlog):** cap the pool radius in absolute pixels, or clip the pool to
  a dilation of the stroke's own cover. The maps' wider route pens may show the same
  halo, so the maps critic should check it.

### 1.2 The old single images sit beside their own grid and lose to it

`pigments`, `composition`, `wash`, `nib-line` and `brush-stroke` were not repainted. Each
is now followed on the page by a grid that does its job better. In the composition grid
the name is centred, flat and above the stroke; the single image still has it on the
stroke and on the trough. The README thumbnail row and `gallery.md` show the old
singles, so the first thing a visitor sees is the weakest version.

- **Smallest fix:** take one cell from each grid as the single image, so the single and
  its grid agree. For pigments, one glazed pair (sienna over ultramarine). For
  composition, the seed 2 "off" cell at 480. Repaint the thumbnails from those.

### 1.3 Stale alt text

- README and `gallery.md` still describe the paper as "a darker worn border and a few
  pale blotches of foxing".
- The composition alt text still says "running across it in a long wave", which is true
  but is the fault.
- The grid-nib alt text promises hairlines "in the bottom row". At 1x they show only in
  the 90 degree cell.

Fix these with the repaint.

## Part 2. Image by image (only what changed or remains)

### word.webp (480 x 270): 2.5

- Better: the letters are clean, with no doubled o and no f-like t.
- Faults left:
  - **Lossy ringing round the letters** (VP8, 9.5 KB). Cause: S7 kept `word.webp` lossy.
    Smallest fix: quality 95, as S7 already allows for any image that passes its budget.
  - **The green disc** still sits low right with its bottom 8 px from the sheet edge. No
    composition change was made this round. Smallest fix: move its centre up to the
    word's x-height line, overlapping the blue by about a third (`examples/word.py`).
  - **Ink blots at stroke starts** (the tops of n, p and t). These are the pen pool of
    1.1 at the wordmark's pen width. Same fix.
  - **The baseline bounces** more than a hand would (the y and both p's drop). Smallest
    fix: render seeds 1 to 30 and pick one.

### tutorials/paper (= gallery/paper): 3

- Better: the warm edge. It now reads as paper, not as a lens.
- Faults left:
  - The image is still almost empty, and 3.4 KB of lossy encoding smears the grain.
    Smallest fix: quality 92.
  - A 3x crop of one corner, set beside it, would show the grain and the specks the text
    talks about.

### tutorials/grid-paper (new): 3

- Works: classic against warm is obvious. The loop matches the code shown.
- Faults:
  - **Tooth across barely reads.** At 150 px cells and 1x, 0.04 and 0.085 look the same.
    Cause: the grain is fine and the cells are small. Smallest fix: zoom each cell 2x on a
    40 by 40 px region (nearest-neighbour), or add a stripe of mid wash across every cell
    so the grain shows through it, as it would under paint.
  - **The khaki "desk"** behind the cells is a dull mid-tone that flattens the warm edge.
    Smallest fix: a darker, cooler desk (slate grey) so the warm edge stands out.

### tutorials/grid-wash (new): 3

- Faults:
  - **The seed rows are nearly the same.** Only the mottle differs, which cannot be seen
    at 1x. Cause: `Sheet(..., seed)` changes only the noise. Smallest fix: make the second
    axis something visible: rim on and off, or a painter's pigment (cerulean against
    ultramarine) in place of the map's `water`.
  - **Still perfect circles in map blue**, and even 0.9 is mid-light. Smallest fix:
    `PAINTERS_PIGMENTS["ultramarine"]`, and perturb the disc radius with two
    low-frequency sines (round 1).

### tutorials/grid-brush (new): 4

- Works: the clearest show-not-tell in the docs. The dry treatments break up as they
  widen, exactly as the caption says.
- Faults:
  - **`MAJ7-e` at 6 and 12 px is a hollow ribbon**, two edges with paper between, like an
    outlined tube. Cause: a pen row stretched past its natural width. Smallest fix: cap
    the scratchy column at 6 px, or replace it with `MAJ3-e`.
  - **The column labels are brush IDs** (`RIV1-a`), which mean nothing to a reader.
    Smallest fix: label "wet", "grainy", "dry" and "scratchy", and keep the IDs in the
    code block.

### tutorials/pigments (and gallery/pigments): 1.5, under 3

- Unchanged from round 1. The two panels still differ by 2 to 8 levels and the image
  still fails its own caption ("a different green"). `grid-pigments` now makes the point
  properly.
- **Smallest fix:** retire this image and promote one column of `grid-pigments`
  (sienna over blue: multiply against glazed) as the rung's lead picture and the gallery
  and README thumbnail.

### tutorials/grid-pigments (new): 4

- Works: real pigments, strong colour, and the four pairs are well chosen. In pairs 2
  (rose over blue) and 4 (sienna over blue), multiply goes muddy-dark while glazing stays
  clean.
- Faults:
  - **The column labels are 1 to 4.** Smallest fix: letter the pairs ("blue + ochre" and
    so on). The alt text already names them.
  - **Pairs 1 and 3 barely differ** between the rows. Smallest fix: swap them for a
    covering pigment over a staining one (indigo over quinacridone rose), where the two
    models disagree most.

### tutorials/nib-line (and gallery/nib-line): 3

- Unchanged: a monoline spiral, and the caption still promises unevenness the image does
  not show.
- `grid-nib` was meant to carry the nib's thick and thin, but see below. Smallest fix:
  stamp the spiral with a nib-angle `wprof` (round 1), so this rung shows thick and thin
  on its own.

### tutorials/grid-nib (new): 2.5, under 3

- Faults:
  - **The drop-shadow halo** (1.1).
  - **The nib is too wide for a 42 px word** (3.6 px). The counters of e and the bowl of
    c fill. Across the top row the four angles look identical, because at `thin = 0` the
    nib is round. Only the 90 degree cells at 0.52 and 0.85 show hairlines, and at 0.85
    the K and the w break into dots.
- **Smallest fix:**
  - pen 2.0 px and word 56 px;
  - drop the `thin = 0` row (it is the control and teaches nothing) and use 0.5 and 0.8;
  - letter a word with more diagonals and curves than "Keswick". "Ambleside" is the
    focus place and has the bowls.
  - The pool fix from 1.1 then removes the halo.

### tutorials/lettering (= gallery/lettering): 3.5

- Better: crisp and legible, with no doubled stems. It answers the pixelation complaint.
- Faults:
  - **Still left of centre and high.** The word spans x 92 to 215 on a 360 px sheet
    (centre 153 against 180) and climbs about 10 degrees.
  - **"si de" spacing gap.**
  - Smallest fix: centre the trimmed path, as round 1 said: measure with `hand.measure`
    and centre the path on the sheet. Try other seeds for the gap.

### tutorials/grid-lettering (new): 3

- Works: nine copies, no two alike. It is the strongest argument for the hand.
- Faults:
  - The halo (1.1).
  - At 56 px with a 2.6 px pen the word is heavier than any lettering on the maps, so it
    does not preview what a reader will get.
- Smallest fix: the 1.1 pool fix, and pen 1.8 px.

### tutorials/composition (= gallery/composition): 2.5, under 3

- Better: the letters are crisp and the K is whole (no kink).
- Faults left (all of round 1's layout faults):
  - the name sits on the stroke ("Keswick" rides the wave);
  - left of centre (x 160 to 255 on 480);
  - on the trough of a one-period wave;
  - the stroke is the same blue as the disc.
- **Smallest fix:** repaint from `_composition_cell`'s layout, which already has a
  centred, flat name above the stroke. Seed 2 "off" from `grid-composition` is a better
  picture than this one. Give the stroke burnt sienna or sap green.

### tutorials/grid-composition (new): 3

- Works: the name is centred and flat, and the seeds differ legibly.
- Faults:
  - **The "on" row's backing wash reads as a white-out label** stuck behind the word.
    That is the sticker look that `nib._backing_wash`'s docstring says it avoids. Cause:
    `label_wash_alpha=0.8` and `spread=0.6`, much stronger than the defaults (0.5 and
    0.75), on a ground that is mid-light, not dark. Smallest fix: the defaults, and
    explain that the wash appears only on dark ground. Or put a darker wash under the
    name in this grid, so the reader sees why the backing exists.
  - **The stroke runs through the letters** in seeds 1 and 3. Smallest fix: lower the
    stroke by 0.1 of the cell.

### curves/rose: 3.5

- Better: five brushed petals tapering to nothing at the centre, so the round-1 black
  knot is gone. Quinacridone rose deepening toward the centre is real colour.
- Faults:
  - **The outline is an even, heavy maroon band.** Each petal reads as a sticker with a
    keyline. Cause: the petal stroke traces the whole petal outline at 0.55 density with
    a taper that peaks at the tip. Smallest fix: drop the stroke to 0.3 density, or stamp
    with a drier row (`TRK3-a`) so the outline breaks in places.
  - **The five petals are almost the same.** The per-petal density is drawn from
    [0.3, 0.5] and then multiplied by a shared radial deepen. Smallest fix: widen it to
    [0.25, 0.6] and jitter each petal's angle and length by a few per cent.

### curves/spirograph: 3

- Better: brushed, with a visible taper and a dry, broken green end.
- Faults:
  - **Crossings no longer deepen.** The fill is one `wash` of the union of the loops
    (`_cover(points)`), so overlapping petals are flat. Round 1's best quality has been
    lost. Smallest fix: wash each loop separately and glaze them.
  - **The colour changes in three hard steps** (navy, then cerulean, then green) at the
    `array_split` thirds. Smallest fix: overlap the thirds by about 5 per cent and fade
    each segment's density in and out across the overlap.
  - **The green third is visibly lighter and dotted**, unlike the others, so it looks
    like a different line rather than the same stroke running dry. Smallest fix: one
    brush for all three thirds, letting `load` fall.

### curves/lissajous: 3, and curves/kaleidoscope: 3.5

- Unchanged. Round 1's fixes still apply (a nib-angle `wprof`, two pigments in a
  chequer; the kaleidoscope's crowded inner petals and the clot at its centre). They are
  not urgent.

### painting-with-python/fern: 4.5

- The drawing is unchanged, as asked, and the warm paper suits it better than the grey
  vignette did. Nothing to do.

### painting-with-python/fern-family (new): 4

- Works: "one species, nine plants" reads at a glance. It reuses the fern's own
  painting, and some plants curl while others stand upright.
- Faults:
  - **Crowding.** The top row's tips are 12 px from the sheet's top edge, and the top
    row's stems almost meet the middle row's tips. Cause: `FIT_WIDTH, FIT_HEIGHT = 0.9,
    0.92` on cells that abut, with no sheet margin. Smallest fix: `FIT_HEIGHT` 0.8 and a
    5 per cent sheet margin.
  - **Only two forms**, curled paisley (seven) and upright (two). Smallest fix: widen the
    curl range (`theta` 0.5 to 5.5 degrees, try -1 to 6) and vary the leaflet green per
    member across two or three greens (round 1 suggested it).

### painting-with-python/tree (new, the gasket's replacement): 3

- Better: far better than the gasket. A recognisable tree, a brushed trunk that tapers by
  depth, a pen hand-off to the twigs, and painter's pigments. The structure is right.
- Faults:
  - **The limbs are painted over the foliage.** `LAYERS` puts `limbs`, `shade` and
    `twigs` after `canopy`, `canopy2` and `warm`. The result reads as a bare tree in
    front of a green cloud, not a tree in leaf. Smallest fix: move `canopy2` and `leaves`
    after `twigs` in `LAYERS`, so foliage overlaps the outer limbs and only the trunk and
    first forks read through.
  - **The crown is a ring of bubbles.** Each crown is a union of hard discs (`_crown`)
    washed with a rim, so the outline is a scalloped cartoon cloud with a dark rim on
    every lobe. Smallest fix: blur the disc mask by about 0.03 w before the wash, and
    perturb each disc's radius with noise, or lower the canopy's rim.
  - **The shade stroke is a seam.** The perylene stroke on the trunk starts hard at the
    first fork, keeps one width and ends below the trunk's rounded foot, which leaves a
    purple speck under the trunk. Cause: `_strokes(limbs[:1])` offset by `0.22 * wd`
    with no taper. Smallest fix: run it over 15 to 85 per cent of the trunk with a
    `sin(pi t) ** 0.5` taper.
  - The leaf dabs are rounded rectangles, all one size. They read as confetti. Smallest
    fix: a smaller brush and a spread of dab lengths.

### painting-with-python/tree-family (new): 3.5

- Works: nine distinct trees of one kind. Lean, spread and crown all vary.
- Faults:
  - **The crowns touch the sheet edges** (the left and right columns run to within 5 px)
    and touch each other between rows. The bottom row's ground strokes are 20 px from the
    sheet's foot. Cause: `fitted` scales the limbs to `FIT_WIDTH 0.8` but the crown discs
    reach `w * 0.075` past the tips, and the foot sits at `0.94 h`. Smallest fix: fit the
    limbs plus the crown radius, or `FIT_WIDTH, FIT_HEIGHT = 0.65, 0.72` and foot at
    `0.9 h`.
  - The tree faults above, repeated nine times.

### painting-with-python/derwentwater: 3

- The title is clean now. The painting itself is unchanged: speckle "camouflage" hills,
  a ruler-straight shoreline and a blob island. Round 1's fixes stand. It is the
  weakest picture on its page now that trees and ferns sit beside it.

### The SVG sequence: svg-flat 4, svg-washes 3.5, svg-ink 3, svg-drawing 3.5

- Works: the page now shows the raw SVG (three code blocks), then the drawing flat, then
  washes only, ink only, and the painting. The reader can see what each step adds.
  Round 1's faults are fixed in `fell.svg`.
- Faults:
  - **The wall reads as a ladder or a railway** in `svg-ink` and `svg-drawing`. The
    stone outlines are inked at `stroke-width 1.4`, as heavy as the wall line, on stones
    only about 8 px tall. Smallest fix: stroke the stones at 0.7, or wash them in a grey
    and ink only the base line.
  - **The trees become flat dark dots** in `svg-washes`: two disc washes at high density
    with no edge variation. Smallest fix: wash the crowns at about 0.6 of their current
    density, so they glaze like the fells.
  - **The scene is a rectangle cut out of the paper.** The bottom edge is straight at
    y 408, and the far fell's left edge is vertical at x 85. Smallest fix: in
    `fell.svg`, let the banks run off a ragged bottom edge, or fade the lowest band.
  - **The tarn on its beck reads as a lollipop** (a lens on a stalk). Smallest fix:
    start the beck a little below and to one side of the tarn.

### how-to/own-shapes: 2.5, under 3

- Better: "Skiddaw" is crisp.
- Faults left (all from round 1):
  - The wash's bottom edge is ruler-straight, so the fell looks like a bar chart.
  - The name sits left of centre and straddles the wash's bottom edge.
  - The skyline is a constant black monoline.
  - There is a "Ski ddaw" spacing gap.
- **Smallest fix (`examples/how_to_own_shapes.py`):**
  - multiply the mask by a vertical ramp over its lowest 15 per cent;
  - centre the name below the fell on clean paper (`align="middle"`, anchor at
    0.88 H);
  - stamp the skyline with a `wprof`.

## Part 3. Top fixes for the next round, by payoff

1. **The pen-pool halo** (1.1). Two example lines (`pen_pool_radius_frac=0.15`) clear
   `grid-nib` and `grid-lettering`. Then cap the pool in the library.
2. **Retire or repaint the old singles from their grids** (1.2): pigments, composition,
   and with them the README thumbnails. This removes two of the five images under 3.
3. **own-shapes and word layout**: the ramped wash and centred name; the disc moved and
   quality 95.
4. **Tree paint order and crown edge**: foliage after limbs, blurred crown mask, tapered
   shade. That moves the tree from 3 to 4, and the family with it.
5. **Spirograph**: per-loop washes and overlapped colour thirds, which win back the
   crossings.
6. **Family margins**: `FIT` values for the fern and tree families.
7. **grid-nib redesign**: thinner pen, larger word, drop the `thin = 0` row, and letter
   "Ambleside".
