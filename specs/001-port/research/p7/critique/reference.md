# Image critique: reference sheets, explanation figures, site theme

Reviewer group: `docs/images/reference/*`, `docs/images/explanation/*`, `docs/images/site/*`
and `docs/stylesheets/pyntpot.css`, with the pages they sit on.

Checkout note: the critique checkout (`wt-crit`, at `bf0b726`) has no `docs/images/site/`, no
`docs/stylesheets/` and no `mkdocs.yml`. They exist on `release-0.1.0` / `p7-docs-site`
(commit `c73a946`, "Build the docs site"). I read them from there with `git show`. The
reference and explanation images are byte-identical on both branches.

Evidence (crops, numeric checks, prototype grids) is in
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/crit-ref/`;
the prototypes are in its `proto/` folder and were painted with the public API only.

## The short version

1. **Several figures do not show what their caption claims.** The pairs that carry the
   argument are visually identical: `wash-overlap` vs `wash-glaze` differ by 0.88/255 on
   average; `nib-centreline` vs `nib-broad` vs `nib-turned` differ by 1.3/255. A reader
   is told "the thick and thin strokes change places" and sees the same picture three times.
   Both are fixable in the example scripts alone (proven by the prototypes below).
2. **Neither reference sheet is legible enough to choose from.** No labels, cells too
   small, near-identical treatments and pastel pigments that are hard to tell apart.
   You have to count discs against a table to find `meadow`.
3. **Show, not just tell is almost absent.** Every page that names a parameter
   (body, pool, gran, transparency, nib angle, pen_thin, reservoir, ink colour, hand seed)
   shows one value of it. Grids made with a `for` loop fix this cheaply; specs below.
4. **Two library artefacts surfaced**: a square touch-down blot on nib treatments at wide
   widths (`deposit.pool` truncates its Gaussian at 2 sigma), and the centreline skeleton
   of "Keswick" drawing the final `k`'s stem as two parallel strokes and breaking the `K`.
   The second is very likely the maintainer's "kink in Keswick".
5. **Paper foxing is a recurring blemish.** `paper_foxing=0.09` puts grey thumbprints in
   the same places in every figure (same seed), including inside the "flat fill" that the
   text calls "an even tone". The site theme already turns foxing off for its paper; the
   explanation and reference figures should too.

On the maintainer's round-1 points that touch my group: agree on "show, not just tell"
(this group is where it bites hardest); agree on the "Keswick" kink and found its likely
cause; "pixelation" in lettering is not visible in these explanation figures (they are
lossless at 360 px), but the figures are so small that the modulation is lost, which is
the same complaint in another form.

---

## Reference

### `reference/pigment-swatches.webp` (600 x 360, on `reference/pigments.md`) : 2/5

What works
- Clean, calm layout; the discs have a soft, faintly mottled wash body and sit on the
  house paper, so it looks like a painter's test card rather than a CSS swatch.
- The order matches the table, and the caption says so.

What does not
- **Unlabelled.** To find `rock` you count to disc 7. A reference sheet must carry its keys
  on the image (hand-lettered with the library's own `letters`, which is also a showcase).
- **Indistinguishable neighbours.** `meadow`, `pale`, `scrub`; `rock`, `built`, `works`;
  `relief` and `rim` read as the same pale tint at 72 px. These are map ground colours by
  design (pastel), but the sheet lays them only once at one strength, so the differences
  that matter (hue at strength, how they stack) never appear.
- **Transparency is half the table and none of the picture.** The page explains
  `TRANSPARENCY` at length; the sheet cannot show it, because a disc on cream paper looks
  the same whether it stains or covers.
- **No wash character.** Edges are soft but uniformly blurred, with no pooled rim to speak
  of (`pool=0.3`), so the discs read slightly out of focus rather than wet.
- Foxing smudges and the dark worn border along the top edge.

Does it earn its place? Partly: it gives the gist (greens, buffs, a blue), but you cannot
pick a pigment from it.

Fixes (example script only, `examples/pigment_swatches.py`)
- Replace with the **pigment card** grid (Grid P1 below): graded strip per pigment,
  painted across a black ink bar with `km_glazing=True`, key hand-lettered beneath.
- Raise `pool` to about 0.55 so each swatch has a visible tide line.
- `PaperStyle(paper_foxing=0.0, paper_vignette=0.0, paper_worn=0.08)`.
- Widen to 960 px (the page budget, 250 kB, has room; the current file is 12 kB).

### `reference/brush-sheet.webp` (800 x 592, on `reference/brushes.md`) : 2/5

What works
- The colour rows are pleasant together: a muted, earthy ink palette that already feels
  like a sketchbook.
- Treatments 4 and 7 visibly break up, as the alt text says.

What does not
- **Strokes too thin to read the treatment.** At 4 px, treatments 1, 2, 3 look the same,
  and 5, 6, 8 look the same. The table lists six parameters per row; the eye gets "dry"
  and "not dry". My prototype at 3, 6 and 12 px (proto/brush-grid.png) shows that the
  treatments only separate at 12 px: 3 granulates, 4 breaks, 7 scratches, 5 and 8 show
  a dark core in a grey body.
- **Five of the fourteen rows repeat an ink.** `RIV-a` = `STR-a`; `MAJ-c` = `LAN-a` = `TRK-a`;
  `MAJ-a` = `TRK-b`; `MAJ-e` = `TRK-f`. Nine distinct inks fill fourteen rows, so most of the
  image is repetition and the rows that matter are hard to find.
- **No labels**: no treatment numbers across the top, no ids down the side.
- Foxing smudges sit right next to strokes (row 3 column 2, row 6 column 7) and read as
  dirty fingerprints on the sheet.
- Treatment 6 (the pen) has a soft blurred halo, so the crispest tool in the box looks the
  least crisp.

Library artefact found while prototyping (flag for `src/`)
- At 12 px, nib treatments 5 and 8 leave a **square grey block** at the touch-down
  (proto/bg-zoom.png). Cause: `pyntpot.ink.deposit.pool` builds the blot as a Gaussian
  with `span = int(r * 2)`, so the kernel is cut off at 2 sigma where it is still
  exp(-2) = 0.135 of peak, times `pool * pool_gain` (1.9): a visible box edge once the ink
  saturates. Fix: `span = math.ceil(3 * r)` (exp(-4.5) = 0.011). This will show on any
  wide nib line, including routes on the hero maps.

Does it earn its place? As a lookup it half works (colour by row); as a guide to choosing
a treatment it does not.

Fixes (example script, `examples/brush_sheet.py`)
- Split into two figures: Grid B1 (treatment x width, one ink) and Grid B2 (the nine
  distinct inks, one swatch each, labelled with their ids and prefixes).
- Hand-letter the treatment numbers 1 to 8 across the top and the ids down the side.
- `PaperStyle(paper_foxing=0.0)`.

---

## Explanation: how the wash works (six figures, 480 x 320, seed 11)

Shared observations
- The stage-by-stage idea is excellent and the shared seed is the right call: the
  difference between figures really is the stage.
- But six separate small images, each with its own worn border, read as six greeting
  cards. A single strip (or 3 x 2 grid) with hand-lettered stage names would let the eye
  compare, which is the whole point. Keep the individual files if the prose needs them
  inline, but add the strip to the gallery.
- Foxing appears at the same three spots in all six (left, centre-left inside the disc,
  right). Set `paper_foxing=0.0`.
- Water blue multiplied on cream comes out a grey-teal (about rgb 165, 185, 186), duller
  than `#9ec4de`. Fine for a map ground; flat for a showcase. A body of 0.8 to 0.9 with a
  pool of 0.8 would give a livelier disc.

### `wash-mask.webp` : 3/5
Does its job: hard edge, even tone. But a foxing smudge shows through the disc, so the
"flat fill" is not quite flat and the reader may think the mask has texture. Fix:
foxing off.

### `wash-body.webp` : 3/5
The soft, wavering edge and the drift are clearly visible against the mask. Good.

### `wash-rim.webp` : 2/5
The claim is "a darker band of blue just inside the edge, so the disc looks outlined".
Measured: the edge band is 173 (red channel) against 178 in `body`, a real but small
change, while the drifted centre is 153, darker than the rim. So the eye reads "darker
middle, slightly darker edge", not "outlined". Fix: raise `POOL` from 0.55 to about 1.0
and lower the body to 0.6 for this figure, or pick a seed whose drift is lighter in the
middle. Grid W1 below makes this argument better than any single figure.

### `wash-grain.webp` : 3/5
The grain is visible. Two problems: at 6 px it looks like a uniform digital speckle more
than settled pigment; and the edge band is no longer distinguishable (edge 162 vs centre
158), though the alt text says "the edge band is still there". Fix: show grain at 3, 6, 12
and 24 px in a strip (Grid W2); correct the alt text, or raise the pool so it survives.

### `wash-overlap.webp` : 3/5 (on its own)
Clear: two discs, dull green crossing. Fine.

### `wash-glaze.webp` : 1/5
**The figure does not show its claim.** The text says the glazed crossing is "cleaner and
lighter"; measured crossing colour is (144.7, 165.7, 138.1) multiplied vs (145.8, 166.8,
139.2) glazed, one level apart; mean difference over the whole image 0.88/255. Cause: both
pigments are stains (water 0.04, farmland 0.10), and Kubelka-Munk with near-zero
transparency is very close to multiply. The figure accidentally proves that glazing
stains changes nothing.

Fix (example only, no `src/` change): make the second disc a covering pigment. The
`PigmentLayer` tuple carries its own transparency, so the script can pass a third value.
Prototype `proto/glaze-grid.png` (Grid W3) lays a blue stain under a red at transparency
0.04, 0.2, 0.5, 0.9, multiply on the top row and Kubelka-Munk below: the KM row goes from
"same as multiply" to "red covers the blue" and the multiply row stays identical, which
also illustrates the page's sentence "multiply ignores it". This is the strongest
single image in my prototypes.

## Explanation: the hand and the nib (eight figures, 360 x 200, seed 7)

Shared observations
- 360 px is too small for the subject. The name is about 40 px tall and the pen 4.6 px
  wide; the effects being explained live in one or two pixels.
- Every figure has the worn, embossed border and a foxing patch bottom right.
- The ink has a soft grey halo round every stroke, which reads as a drop shadow rather
  than wicking. I checked: it is not the backing wash (setting `wash=False` gives a
  byte-identical image), so it is the ink's edge bleed. Worth a look at the bleed radius
  relative to pen width (`src/`, letters or ink), or at the intermediate plate the
  example writes as WebP.

### `nib-line.webp` : 2/5
A thin line on empty paper. It carries one sentence. Better: draw the line faintly (a
pencil-grey guide) under the name in every following figure, and drop this one, so the
reader sees the name sitting on its path.

### `nib-centreline.webp` : 3/5
The point (even width reads as plotted) lands. But at 3x (proto/cl-big.png) the
skeleton is visibly wrong: **the final `k`'s stem is two parallel strokes**, and the `K`'s
stem is broken where the arms meet, with a heavy blob at the junction. Thinning a wide
stem gives two near-parallel chains that the spur pruning keeps. This is almost certainly
the maintainer's "kink". It needs a `src/pyntpot/letters` fix (merge or drop near-parallel
chains closer than about a pen width; or prune loops as well as spurs), not a figure fix.

### `nib-broad.webp` : 2/5 and `nib-turned.webp` : 1/5
**Not distinguishable from the centreline figure or from each other** (mean difference
1.3/255; ink pixel counts 3696, 3232, 3349). The argument of the section, thick across
and thin along, then swapped, is invisible. Prototype `proto/nib-grid.png` shows that at
a 9 px pen and `label_pen_thin` 0.85 the angle becomes readable; at the default 0.52 it
stays subtle even at 3x. Fix: Grid N1 (angle x thin). For the single figures, paint at
720 px, pen 8 to 10 px, `label_pen_thin=0.8`, and say in the caption that the thinning is
exaggerated, as the reservoir caption already does.

### `nib-ground.webp` : 2/5
The "dark wash" is a hard-edged rectangle of saturated green (wood glazed twice): it looks
like a sticky note, the least painterly image in the group. Fix: paint the ground as an
irregular wash (a hill silhouette, or a blob from blurred noise thresholded) with a pool,
so the figure looks like a corner of a map. `wood` once at body 1.0 with `pool=0.6` should
be dark enough.

### `nib-backing.webp` : 3/5
The effect is clear: the name pops. The lifted patch is a large flat pale band across the
top that reaches the edge of the rectangle, so it reads as a smear more than as paint
lifted with a damp brush. A tighter `label_wash_spread` (0.3) and the irregular ground
above would help.

### `nib-set-down.webp` : 3/5
A good long stroke, but the blot is a 3 px dot. Paint at double width, or add an inset
crop at 4x of the touch-down.

### `nib-runs-dry.webp` : 2/5
Thinning is visible, but each reload is a **hard step**: the line jumps from thin to full
in one stamp (top of the first arc, and at about 70% across), which reads as a glitch,
not as a refilled nib. A real reload swells over two or three widths. Possibly a `src/`
change (ease the reservoir back over a short ramp); otherwise an extra hand-tuned dip
just before a peak hides it. Grid N2 shows the parameters.

---

## Site theme (`release-0.1.0`): `site/paper.webp`, `site/rule.webp`, `pyntpot.css`

### `site/paper.webp` (960 x 540) : 4/5
Pleasant, quiet rag with no border or foxing: right for a page ground. `background-size:
cover` with `background-attachment: fixed` scales it 2.7x on a 2560 px screen, so the
mottle becomes blurry blobs. Paint it tileable at 512 px and use `background-repeat`
at native scale, so the tooth stays crisp at every width. Note `background-attachment:
fixed` is ignored on iOS Safari.

### `site/rule.webp` (960 x 40) : 2/5
A nearly straight, uniform blue line: at page scale it reads as a CSS border with a
wobble, not a brush stroke. It is also stretched `100% 100%` into a 0.9 rem box, so the
image is squashed about 2.8x vertically and any bristle texture goes. Its background is
247 to 254 white rather than pure white, so multiply leaves faint grey ghosts. Fixes:
use a drier, textured treatment (`RIV3-a` or `MAJ3-c` at 10 px on a 1600 x 60 canvas),
a stroke that starts with a touch-down and tapers out, `background-size: auto 100%`
(keep the aspect) with `left center`, and clip the paper to pure white before saving.
Better still, paint three or four rules with different seeds and pick one per heading
level, so headings do not all carry the identical mark.

### `pyntpot.css` : 3/5
- Good: the palette is derived from `PIGMENTS` by script; link contrasts are fine (glaze
  water on paper 6.0:1; dark-scheme link 9.4:1; accent wood 7.2:1).
- Patrick Hand headings with Material's Roboto body is a mismatch: the page reads as a
  tech site wearing a costume. A book serif for body text (Source Serif 4, Literata) would
  sit with the watercolours; keep Patrick Hand for h1/h2 only.
- The header bar is flat `glaze-water`: the one digital block on the page. Paint a header
  band (a horizontal graded water wash, 1600 x 120) and use it as the header background,
  or make the header paper-coloured with the rule beneath.
- Figures: each has its own worn border and vignette, so on the paper ground they read as
  prints with an embossed frame (fine, consistent with "sit on the page like prints").
  If that is the intent, add a faint shadow (`box-shadow: 0 1px 3px rgb(0 0 0 / .15)`);
  in the dark scheme the cream figures glow, and a 1 px paper-dark border would settle
  them.
- Figures render at natural size: the 360 px nib figures appear as postage stamps in a
  ~750 px column. Either paint them wider or add `width: 100%` for figures in the
  explanation pages.

---

## Show, not just tell: grid figures

Each is one new figure name in an existing example script (or a new example), built with
a `for` loop over the varied parameter(s), hand-lettered labels from `pyntpot.letters`
(a showcase in itself, and no digital type on a painting), foxing off. Sizes are at the
page width; all fit the 250 kB page budget as lossy WebP. Registry entries go in
`tests/support/docs_images.py` with a slice share.

| Grid | Page | Rows | Columns | Notes |
| --- | --- | --- | --- | --- |
| **P1 Pigment card** | pigments.md | 3 | 5 (the 15 pigments in table order) | Each cell: a graded strip, body 0.2 to 0.9 left to right, painted across a horizontal black ink bar, `km_glazing=True`. Staining pigments vanish over the bar, covering ones veil it: transparency made visible. Key lettered under each strip. 960 x 540. |
| **P2 Glaze matrix** | pigments.md or how-the-wash-works.md | 6 pigments (under) | 6 pigments (over) | Pick `water`, `wood`, `meadow`, `heath`, `relief`, `built`. Each cell: two overlapping square washes, KM on. Diagonal: single pigment. Shows what map grounds do where they overlap. 720 x 720. |
| **B1 Treatment x width** | brushes.md | 3 widths (3, 6, 12 px) | 8 treatments | One ink (`MAJ*-e`). Proven readable at 12 px (proto/brush-grid.png). Number 1 to 8 across the top, "wet, wet, gritty, dry, nib, pen, scratch, nib" as a lettered word under each. 1200 x 260. |
| **B2 Ink swatches** | brushes.md | 1 | 9 distinct inks | One 10 px stroke of treatment 2 each, with the prefixes that use that ink lettered beneath (e.g. "MAJ-c LAN-a TRK-a"). Replaces the repeated rows. |
| **B3 Brush overrides** | brushes.md / style-fields.md | 3 values each | Darkness, Bristles, Gap, Dry, Texture (5 columns) | Treatment 2 at 10 px, `brush_overrides` setting one field low, default, high per row. Shows what the table's columns mean. |
| **W1 Body x pool** | how-the-wash-works.md | pool 0, 0.3, 0.6, 1.0 | body 0.3, 0.5, 0.7, 0.9 | Water discs. Keep body under 1: my prototype shows body 1.2 and 1.6 saturate to a flat, textureless disc (proto/wash-grid.png), worth a sentence on the page (and a possible `src/` soft clip). 720 x 720. |
| **W2 Grain size** | how-the-wash-works.md | 1 | `gran_px` 3, 6, 12, 24, 60 | Same disc and seed. Shows speckle to mottle. 900 x 200. |
| **W3 Glaze vs multiply** | how-the-wash-works.md (replaces overlap/glaze pair or follows it) | multiply, Kubelka-Munk | top-layer transparency 0.04, 0.2, 0.5, 0.9 | Blue stain under a warm covering red. Prototype proves it reads at a glance (proto/glaze-grid.png). 800 x 320. |
| **N1 Nib angle x thin** | the-hand-and-the-nib.md | `label_pen_thin` 0, 0.52, 0.85 | `label_pen_angle_deg` -38, 0, 38, 90 | "Keswick", pen 9 px, type about 60 px in 300 x 120 cells (my prototype at 90 px overflowed). The 0 row is identical across, which is itself the lesson. 1200 x 400. |
| **N2 Reservoir** | the-hand-and-the-nib.md | `pen_thin` 0.5, 1.0 | `pen_reservoir` 22, 44, 88 nib widths | The long wave in each cell. 900 x 300. |
| **N3 The hand's variation** | the-hand-and-the-nib.md | 3 | 3 | "Keswick" written with nine `hand.generator(seed)` values. The essay says the hand writes "a little differently each time" and shows it once; this is the cheapest, most persuasive figure on the page. 900 x 360. |
| **N4 Ink and backing** | the-hand-and-the-nib.md | backing off, on | `label_ink` in the five `MAJ` inks | Over an irregular wood wash. Shows ink choice and why the backing exists. |

Are the existing sheets legible enough to choose from? **No.** The pigment sheet has no
labels and too little difference between neighbours; the brush sheet's strokes are too
thin to tell six of the eight treatments apart, and five of its fourteen rows repeat an
ink. P1, B1 and B2 replace them.

## Ranked top 10 fixes (biggest visual payoff first)

1. Replace `wash-glaze` (and pair it with `wash-overlap`) with Grid W3, a covering pigment
   over a stain at 4 transparencies, multiply vs KM; today's pair is identical (0.88/255).
2. Grid N1 (nib angle x `label_pen_thin`, 9 px pen) to replace or follow `nib-broad` /
   `nib-turned`, which are indistinguishable from each other and the centreline figure.
3. Fix the centreline skeleton in `src/pyntpot/letters` (double `k` stem, broken `K`):
   the likely "Keswick" kink; it affects every map label, not only this page.
4. Grid N3: "Keswick" written by nine hand seeds; the essay's central claim, unshown.
5. Replace the pigment sheet with the labelled pigment card P1 (graded strip over a black
   bar, KM on).
6. Replace the brush sheet with B1 (treatment x width at 3/6/12 px) plus B2 (the nine
   distinct inks), labelled.
7. Fix the square touch-down blot in `src/pyntpot/ink/deposit.py` (`span = ceil(3r)`);
   visible on any wide nib line.
8. `paper_foxing=0.0` (and lower vignette/wear) in every reference and explanation figure:
   removes the repeated thumbprints, including the one inside the "flat fill".
9. Paint `nib-ground`/`nib-backing` on an irregular, pooled wash instead of a hard green
   rectangle; and add Grid W1 (body x pool) so the rim stage is visible.
10. Site: a textured, tapering rule kept at its aspect, a tileable paper at native scale,
    a painted header band in place of the flat blue bar, and a book serif for body text.
