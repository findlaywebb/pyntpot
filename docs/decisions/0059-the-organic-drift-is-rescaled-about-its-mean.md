# 0059 — The organic drift is rescaled about its own mean: a golden regeneration

Status: accepted

## Context

On an organic brush with coherence, `ink.stamp._organic_fields` draws each logical
bristle's sideways drift as its own lattice field, smooths the fields across the tip
(`tip_band`) so neighbours drift together rather than crossing, and rescales the result back
to the spread it had before smoothing (GitHub issue #125). The rescale was taken about zero:
`jit_log * was / std`. It multiplied the part every bristle shares as well as the part they
differ by.

On a long stroke that shared part averages out along the stroke and does no harm. On a
stroke shorter than one drift cell (about 195 render pixels at a brush unit of 1 and the
default organic multiplier) the field is nearly constant along it, so the shared part is
mostly a constant, and the rescale turned it into a sideways shift of the whole stroke
along its normal. Measured on a 5 by 7 pixel ring with the major-road brush, the worst of
300 seeds moved 3.34 pixels off its path, three times the brush's 1.1 pixel jitter. On a
closed glyph or ring that changes its radius: a 20 pixel "o" at scale 2 had the middle of
its counter 0.61 inked at worst across 400 label seeds, and a pin ring can fill once another
change reshuffles the generator's draws (the skeleton change of issue #43 does on Lynmouth).
The same fault was found and fixed on the parked branch of issue #61; this is that fix alone,
on `main`.

## Decision

- **Only the spread about the stroke's own mean is rescaled.** `_organic_fields` takes the
  smoothed field's mean and rescales `jit_log - mean` to the old spread, then adds the mean
  back: `mean + (jit_log - mean) * was / std`. Smoothing across the tip leaves that mean
  where the field put it, so the stroke keeps the drift it was drawn with and is not pushed
  sideways; the spread, which is what the rescale is for, is restored exactly as before.
- Not changed: the generator's draw order (no draw is added or removed), the lattice cells,
  `tip_band`, the coherence of any brush, and the sine drift of a brush that is not organic.

Pinned by `tests/unit/ink/test_stamp_drift.py`: a short ring's ink stays within 1.6 times the
jitter of its path over 300 seeds (3.34 px before the fix, bound 1.76); the shared drift keeps
the field's spread and its mean (a mean shift of 2.27 before, bound 0.25) and still leans
the way the field did; neighbouring bristles drift more alike once the drift is shared; and
the break along the stroke is the next lattice field at its own cell. `TestCounters` in
`tests/unit/letters/test_nib.py` holds a 20 px "o" open over 400 label seeds (0.61 inked
before, bound 0.4).

## Golden regeneration

Process as ADR 0036. The tolerance bound is not changed, no gate is loosened and the hash
input does not change; the manifest hash does not move (`340a7f6e260ee1e2-d9c56c0811177b0f`).

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical no, differing fraction 0.012353
pen.webp: identical no, differing fraction 0.003246
labels-centreline.webp: identical no, differing fraction 0.014783
map.png: identical no, differing fraction 0.018953
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

The paper does not move: it paints no organic stroke. The wash, pen and lettering move
wherever an organic brush lays a stroke. `PINNED_LABELS` is unchanged: every name keeps its
seat, and only the strokes that write it and the roads and rivers are redrawn. The goldens
were regenerated in place with `make_golden.py` and compared with the paint they came from
(`--require-identical all --require-hash equal`): every output byte-identical.
`GOLDEN_HASH` is not re-pinned.

### Docs images

Every docs image and master was repainted with `make_docs_images.py`. The 18 that paint an
organic stroke moved, and only they; every other entry is byte-identical. Master differing
fractions against `main`'s masters:

| Image | Master | Image | Master |
|---|---|---|---|
| `places/oxford.webp` | 0.104926 | `places/y-fenni.webp` | 0.080880 |
| `places/skye.webp` | 0.074416 | `painting-with-python/tree-family.webp` | 0.065052 |
| `how-to/route-ink-grid.webp` | 0.062377 | `painting-with-python/tree.webp` | 0.058854 |
| `gallery/route-map.webp` | 0.051974 | `places/ambleside.webp` | 0.051974 |
| `map-styles/bold.webp` | 0.042958 | `tutorials/route-map.webp` | 0.041423 |
| `how-to/route-ink.webp` | 0.040789 | `map-styles/winter.webp` | 0.039474 |
| `map-styles/pen-and-ink.webp` | 0.037500 | `map-styles/sepia.webp` | 0.031262 |
| `places/yr-wyddfa.webp` | 0.028544 | `how-to/command-line.webp` | 0.021972 |
| `social-preview.jpg` | 0.012431 | `hero.webp` | 0.010916 |

Looked at side by side with `main`: no name, pin or leader moves. The changes are the
texture of organic strokes: roads, rivers and lettering are drawn with a different edge
wander along their whole length, so the differing fraction is high on every card, but no
stroke is visibly wider, thinner or displaced. Short closed strokes (the pin rings by
Lynton, the bowls of small letters) sit on their path as drawn.

## Consequences

- A short organic stroke drifts as its bristles' fields say, and is never shifted
  sideways as a whole by the rescale; a small counter or pin ring stays open.
- The drift's spread across the tip is unchanged, so long strokes look as before.
- A further regeneration needs its own ADR.
