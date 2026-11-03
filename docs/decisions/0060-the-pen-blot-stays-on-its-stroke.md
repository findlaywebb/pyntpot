# 0060 — The pen's set-down blot stays on its stroke: a golden regeneration

Status: accepted

## Context

A pen or nib stroke starts with a blot (`ink.deposit.pool`): a Gaussian of radius
`max(width * pen_pool_radius_frac, 1.2)` render pixels and height `pool * pen_pool_gain`,
cut at three radii, laid at the stroke's first point. The radius grows with the pen, so the
blot reaches one and a half widths from the start in every direction, behind the start and
past both sides of the line. A pen wider than about two pixels then leaves a soft grey disc
round the start of every stroke; on a lettered word, where every glyph stroke starts with a
blot, it reads as a grey drop shadow 3 to 8 pixels wide (GitHub issue #39). Measured on a
2.6 px `MAJ6-e` pen at scale 2, the blot added 0.0067 of density on average to the paper
3 to 8 pixels from the ink. The docs examples worked round it with
`BrushStyle(pen_pool_radius_frac=0.15)` wherever a pen of 2 px or more lettered a word. The
same blot is the soft round blob where the Brathay starts at the lower left of the hero card.

## Decision

- **The blot is laid only on the paper the nib covers.** `pool(acc, b, lay, pos)` multiplies
  the Gaussian by `nib_cover`, the share of each pixel the stroke's own tip passes over: each
  sample of the stroke stands for one stamp spacing along and one sample spacing across the
  tip, and is splatted bilinearly as `deposit` lays ink, then capped at 1. It reads the
  samples' positions, not their weights, so the stroke's very start, where the pressure is
  still zero, is under the nib all the same. The blot keeps its radius, height and three-radius
  cut, so it darkens the start of the line as before and lays nothing beside it.
- The fix is in the pool, not in the brush style: `pen_pool_radius_frac` and `pen_pool_gain`
  keep their meaning and defaults, and no theme changes.
- The examples' work-around goes: `examples/word.py`, `composition.py`, `how_to_own_shapes.py`,
  `nib_stages.py` and `tutorial_grids.py` letter with the default `BrushStyle()`, and the
  tutorial's quoted code follows.

Pinned by `tests/property/test_stamp.py` (at any pen width from 1 to 8 display pixels, on any
path, the blot lays no ink more than 2 px past the stroke's own ink),
`tests/unit/ink/test_stamp.py` (a 2.6 px pen adds nothing to the paper 3 to 8 px from its
ink) and `tests/unit/ink/test_deposit.py` (along its own stroke a wide blot still fades to
under 1.5% at the end of its span and stops there; beside the stroke it lays nothing).

### Mutation testing

`mutmut` over `ink.deposit.pool`, `ink.deposit.nib_cover` and `ink.stamp.stamp`: see the
results below.

MUTATION_RESULTS

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052. The tolerance bound is not changed,
no gate is loosened and the hash input does not change; the manifest hash does not move
(`340a7f6e260ee1e2-d9c56c0811177b0f`), so `GOLDEN_HASH` is not re-pinned. The smoke lock's
`pen` hash is re-pinned; its `paper` and `wash` do not move.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.000812
pen.webp: identical no, differing fraction 0.000150
labels-centreline.webp: identical no, differing fraction 0.005178
map.png: identical no, differing fraction 0.002939
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

`PINNED_LABELS`, the place pins and the map-styles means do not move. The wash plate moves
where a lane's blot sat on it. On the label plate most of the measured change is the grey
lift round the leaders' pins and the glyph starts, now gone; two thin bars near "Saint Mary"
and "Church" are fully transparent pixels whose colour channels changed, which nobody sees.

### Docs images

Every docs image and master was repainted with `make_docs_images.py`. The 48 that draw a
pooled pen or nib stroke moved (20 of their masters past the 0.005 parity fraction, all with
the change at stroke starts); the other 22 are byte-identical. The largest master fractions:

| Master | Fraction | Max delta | Master | Fraction | Max delta |
|---|---|---|---|---|---|
| `social-preview.png` | 0.019965 | 77 | `explanation/nib-hands.png` | 0.019227 | 34 |
| `reference/brush-sheet.png` | 0.018797 | 174 | `places/oxford.png` | 0.018575 | 55 |
| `places/y-fenni.png` | 0.017679 | 78 | `explanation/nib-angles.png` | 0.017652 | 32 |
| `painting-with-python/tree-family.png` | 0.011302 | 36 | `reference/pigment-swatches.png` | 0.010484 | 16 |
| `curves/kaleidoscope.png` | 0.009757 | 124 | `map-styles/bold.png` | 0.008723 | 20 |
| `hero.png` | 0.003558 | 159 | `explanation/nib-set-down.png` | 0.003164 | 135 |

Looked at side by side with `main`: on the brush sheet the 12 px pen swatches (rows 5, 6
and 8) lose the round dark disc at their start and begin as a dark touch inside the line;
the lettered words and the leaders lose the faint grey cloud round their glyph starts and
pins; on the hero the soft blue disc where the Brathay starts at the lower left is gone. The
lossy WebP docs images show change across the whole picture at one or two levels, which is
the encoder, not the paint: the masters' changes are local to the stroke starts.

## Consequences

- A pen's blot can no longer show past its own line at any width, so a wide pen letters
  with the library's defaults.
- A stroke that starts where another's ink already lies is darkened only under its own nib.
- A further regeneration needs its own ADR.
