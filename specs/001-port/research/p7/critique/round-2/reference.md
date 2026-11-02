# Image critique, round 2: reference sheets and explanation figures (P7.V13)

Scope: `docs/images/reference/*` and `docs/images/explanation/*` on `p7-wip` (last image commit
`00b1744`), each read at full size and against the caption and alt text that cite it
(`docs/reference/pigments.md`, `docs/reference/brushes.md`,
`docs/explanation/how-the-wash-works.md`, `docs/explanation/the-hand-and-the-nib.md`,
`docs/gallery.md`). Same rubric as round 1 (`../reference.md`): 1 = does not show its claim,
3 = shows it but with a visible fault, 5 = a figure you would choose to show. The site theme
is out of scope this round.

Evidence (PNG copies, crops, contact sheets) is in
`/tmp/claude-0/-home-user-pyntpot/b5f3e52e-44b7-5bec-868e-9b1bf82d5242/scratchpad/crit2/`.

## Scores

| Figure | R1 | R2 | Change |
| --- | --- | --- | --- |
| `reference/pigment-swatches` (pigment card) | 2 | 3 | labelled, graded, KM over a bar; bar too heavy, veil faint |
| `reference/brush-sheet` (treatment x width) | 2 | 4 | replaced by the grid; readable at 12 px, labelled, square blot gone |
| `explanation/wash-mask` | 3 | 4 | foxing gone: the fill is flat (centre 168 ± 1) |
| `explanation/wash-body` | 3 | 3 | unchanged in substance; cleaner paper |
| `explanation/wash-rim` | 2 | 3 | a real rim now (edge ring 161 vs interior 175); centre still as dark |
| `explanation/wash-grain` | 3 | 3 | edge band survives (163 vs 171), so the alt text is now true |
| `explanation/wash-overlap` | 3 | 3 | unchanged |
| `explanation/wash-glaze` (glaze grid) | 1 | 4 | replaced by the multiply/KM x transparency grid: the claim now shows at a glance |
| `explanation/nib-line` | 2 | 2 | unchanged |
| `explanation/nib-centreline` | 3 | 4 | the double `k` stem and broken `K` are gone; even stroke reads |
| `explanation/nib-hands` (new) | n/a | 4 | nine seeds, variation visible |
| `explanation/nib-angles` (new, replaces broad/turned at 2 and 1) | 2 / 1 | 3 | angle now changes the picture; thinned strokes are ragged, halo heavy |
| `explanation/nib-ground` | 2 | 3 | irregular patch instead of a sticky note; flat and the claimed edge band is absent |
| `explanation/nib-backing` | 3 | 3 | the lift is a rectangle |
| `explanation/nib-set-down` | 3 | 3 | unchanged; blot still a few pixels |
| `explanation/nib-runs-dry` | 2 | 2 | reload still a hard step |

Mean 3.2 (round 1, same figures where comparable: 2.4).

**Under 3:** `nib-line` (2), `nib-runs-dry` (2). Both unchanged from round 1.

## What improved across the group

- **Foxing is off** in every figure; no more repeated thumbprints, including inside the flat fill.
- **The warm paper** sits well under the washes and the brown ink; figures read as one set.
- **Both reference sheets are labelled** in the library's own hand: keys under the pigments,
  treatment numbers, widths and kinds on the brush grid.
- **The three arguments that were invisible are now visible**: glazing vs multiply
  (wash-glaze), nib angle x thinning (nib-angles), the hand's variation (nib-hands).
- **Two library defects fixed**: the square touch-down blot (nib treatments at 12 px now
  leave a round blot) and the centreline skeleton of "Keswick" (single `k` stem, whole `K`).

---

## Reference

### `reference/pigment-swatches.webp` (960 x 372): 3/5

Caption: graded strips across a black band, KM-glazed; "the staining pigments let the black show
through at their deep end; the covering greys and browns veil it".

Works
- Every key is lettered under its strip; you can find `rock` without counting.
- The strips deepen left to right (e.g. `relief` above the bar 226 to 150), so each pigment shows
  more than one strength and neighbours like `meadow`/`pale`/`scrub` now separate at the deep end.
- The covering pigments do veil the bar a little: bar under `works`, `built`, `relief` goes from
  about 36 at the pale end to 61 at the deep end; under `water`/`wetland`/`wood` it stays 22 to 31.

Faults
- **The veil is too faint to read as the lesson.** 25 vs 61 out of 255 is "black vs very dark
  grey". Cause: the most covering pigment in the table is 0.30, and KM at 0.3 over a near-black
  ink only lifts it slightly. Fix (example only): shorten the bar so a bare stretch of black
  shows beyond each strip's deep end as the reference (now only 6 px, `inset=-6`); or lay a
  mid-grey bar (`BAR_HEX` about `#6a625a`) where a covering veil reads as a lightening and a
  stain as a tint.
- **The bar dominates.** A soft-edged black sausage over a third of each strip's height (22 of
  64 px) draws the eye before the pigment does, and it is blurred (`wash(..., 1.0, 0.0)` on a
  hard mask), so it looks out of focus. Fix: `BAR_H` about 10, and draw the bar with a pen
  treatment (`MAJ6-*`) or a crisp mask rather than a wash.
- A 1 px dark vertical line at the left edge of every strip (the wash's pooled edge on a hard
  rectangle, kept by the ramp). Minor; inset the ramp start or round the mask corners.
- Lettering: "farmland" sets as "far mLand" (a gap after `r`, an `l` that reads as a capital).
  Hand spacing/glyph choice in `letters`, not the figure; worth a backlog note.

### `reference/brush-sheet.webp` (960 x 354): 4/5

Caption: one ink, eight treatments at 3, 6, 12 px; wet ones stay whole, dry ones break up,
nibs blot at touch-down. All three claims are visible.

Works
- 3 (gritty), 4 (dry), 7 (driest) separate clearly at 12 px and 4 and 7 at every width;
  the width rows make the case the caption makes ("a stroke 4 pixels wide hides what a
  treatment does").
- The touch-down blot on 5, 6 and 8 is round and soft now; no square.
- Labels across, down and beneath are legible and in the house hand.

Faults
- **The pen (6) and nibs (5, 8) are the softest strokes on the sheet.** At 12 px their edges
  and blot are blurred, so the crispest tools look the least crisp (round-1 point, still there).
  Cause: the ink edge bleed is a fixed radius, too large relative to a firm nib. Smallest fix
  is in `src/` (scale nib bleed down with `Dry`/`Gap` near zero); in the figure, nothing.
- "fine nib" (8) is as wide as "nib" (5) because width comes from the row; the word misleads.
  Fix: letter it "nib, light" or similar, or say in the caption that the width is set by row.
- The nine distinct inks (round-1 grid B2) are not shown anywhere; the ink table on the page
  has no picture. Not a fault of this figure; a gap on the page.

---

## Explanation: how the wash works

### `wash-mask.webp`: 4/5
Flat and hard-edged as claimed; centre 168 ± 1, edge 170. Foxing gone. Nothing to fix.

### `wash-body.webp`: 3/5
Soft, wavering edge and the drift both read. The drift puts a darker patch right of centre
(159 vs 175 at the edge), which then competes with the rim in the next figure.

### `wash-rim.webp`: 3/5
Claim: "a darker band of blue just inside the edge, so the disc looks outlined". It does now:
the ring at 0.90 r is 161 against 175 just inside it. But the drifted centre (159) is as dark
as the rim, so the eye still reads "dark middle and dark edge". Fix (example): lower the body
for this figure (about 0.6) or move the drift seed so the centre is lighter; or add the round-1
body x pool grid (W1), which is still missing.

### `wash-grain.webp`: 3/5
The edge band is there (edge 163 vs mid 171), so the alt text now holds. At 6 px the grain
still reads as a fine digital speckle more than settled pigment; the grain-size strip (W2) was
not added.

### `wash-overlap.webp`: 3/5
Clear and correct; unchanged. Its role is now the set-up for the glaze grid, which the prose
handles well ("Two stains do not show the difference").

### `wash-glaze.webp` (800 x 350): 4/5
Claim: multiply row identical across, glazed row lightening and warming until the overlap is
sienna alone at 0.9. Exactly what the image shows, at a glance. The best figure in the group.

Fault
- The discs are very soft-edged and have no wash character (no rim, no grain), so they read as
  blurred vector circles next to the stage figures above them. Fix (example): give the two
  layers `pool` about 0.5 and a smaller blur, so they look painted like the rest of the page.
- Ultramarine and burnt sienna at full strength are louder than every other figure on the
  page; acceptable for a teaching figure.

## Explanation: the hand and the nib

### `nib-line.webp`: 2/5 (under 3)
Unchanged: a thin line on empty paper carrying one sentence. Fix as round 1: draw this line
as a faint pencil guide under the name in `nib-centreline` (and the ground/backing figures)
and drop the separate figure, or keep it but at the width of the grids.

### `nib-centreline.webp`: 4/5
Even width, reads as plotted, as claimed. The skeleton fault is fixed: the final `k` has one
stem and the `K` is whole. Still 360 px, so on the page it is small.

New fault across the page: this figure (and ground/backing) letter with a thin pen, while
`nib-hands` and `nib-angles` use a pen about three times as heavy. The reader is told the
grids are "the centreline's even stroke again" and sees what looks like another face. Fix:
paint the stage figures with the grids' pen (or the grids with the stage pen at a larger
size) so the name is recognisably the same object down the page.

### `nib-hands.webp` (840 x 335, new): 4/5
Nine seeds, nine visibly different copies (lean, baseline, size), as claimed. Fault: every
word sits in a soft grey halo that reads as a drop shadow (see below). The variation is
modest at a glance; a faint baseline guide per cell would make the drift visible.

### `nib-angles.webp` (840 x 386, new): 3/5
Claim: top row identical, bottom row hairlines whose position follows the angle. The top row
is identical and the 90 degree cell in the bottom row clearly thins the uprights, so the
argument is now visible (round 1: invisible).

Faults
- **The thinned strokes are ragged, not hairlines.** At 0.85 the edges become jagged and
  stair-stepped, with spikes where the width flips; it reads as damage rather than a broad nib.
  Cause: the width is modulated per stamp from the local direction of a skeleton that changes
  direction pixel to pixel, so a near-threshold stroke flickers between wide and thin. Smallest
  fix in `src/pyntpot/letters`: smooth the stroke direction (a short moving average of the
  tangent, a few stamps) before computing the nib width. The figure cannot fix this.
- **Heavy halo** round every word (also in `nib-hands`): a grey shadow offset below-right
  that looks like a drop shadow, not wicking. Round 1 traced it to the ink's edge bleed; it
  is more visible at this pen weight. Fix in `src/` (bleed radius relative to pen width), or
  `wash=False`/smaller bleed for the grid in the example if a knob exists.
- The column labels (-38, 0, 38, 90) and row labels carry no units or names; the caption
  explains them, so minor.

### `nib-ground.webp`: 3/5
Claim: irregular patch of deep sap green "with a darker band of pigment at its edge"; ink
legible but low in contrast. The irregular patch is a real improvement on the rectangle. But
the green is flat (63 to 65 across most of the patch) and the edge band is not there on the
left (straight from 220 to 65 with no dip) and barely at the bottom. Pale granulation flecks in
the lower right look like mould more than settled pigment. The `K` hangs off the left edge of
the patch onto paper. Fix (example): pool about 0.6 on the patch and body a touch under 1, and
shift the setting right so the name sits inside the patch; or correct the alt text.

### `nib-backing.webp`: 3/5
The effect is unmistakable: the name is much clearer. But the lifted patch is a rounded
rectangle the shape of the name's bounding box, with a straight top edge, so it reads as an
eraser mark. Round-1 fix (`label_wash_spread` about 0.3) not taken. Better: build the lift
mask from the dilated marks rather than their box, if that is the backing's design; otherwise
a tighter spread.

### `nib-set-down.webp`: 3/5
Unchanged: a good stroke, a blot of a few pixels at the start that you must look for. Fix as
round 1: paint at double width, or add a 4x inset of the touch-down.

### `nib-runs-dry.webp`: 2/5 (under 3)
Unchanged. Ink width per column runs 5, 4, 4, 3, 3 then jumps to 6 in one step (about x = 136),
and again 5, 6, 9, 12 within a few pixels further on: each reload is a hard step, which reads
as a glitch, not a refilled nib. The caption's "swelling back at each reload" is not what the
eye sees. Cause: the reservoir resets to full in one stamp. Fix in `src/pyntpot/ink` (or
wherever `pen_starve` lives): ease the reservoir back over two or three nib widths.

---

## Still open from round 1

- Grids W1 (body x pool) and W2 (grain size), N2 (reservoir), N4 (ink and backing), B2 (the
  nine inks), B3 (brush overrides), P2 (glaze matrix): none added.
- The wash stages are still six separate 480 px cards; a single strip would let the eye
  compare the stages.
- The 360 px nib stage figures remain small on a ~750 px column.
