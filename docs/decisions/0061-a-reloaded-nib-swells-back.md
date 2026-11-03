# 0061 — A reloaded nib swells back: a golden regeneration

Status: accepted

## Context

With `BrushStyle.pen_starve` on (it is on in the default theme and every example theme), a
nib thins and lightens along a long run and is dipped again every `dip_px` of
pressure-weighted travel. `_width` in `ink/stamp.py` took the spent share as
`1 - exp(-(run mod dip_px) / run_px)`, and the `mod` dropped it to nothing in one stamp, so
the line went from its thinnest to its fullest between two neighbouring stamps (GitHub
issue #40). On the docs figure `explanation/nib-runs-dry.webp` the ink is 5, 4, 4, 3, 3
pixels wide along a run and then 6 at the reload. It reads as a glitch, not as a nib dipped
again, and the figure's caption ("swelling back at each reload") was not what the eye saw.
Measured on the issue's repro (a 5 px `MAJ6-e` pen, `pen_reservoir=22`, `pen_thin=1`,
`ink_dip_mult=1.4`), the line regained 92% of what its run had lost within one nib width.

## Decision

- **The refill eases.** `_nib_spent(run, b)` is the spent share at each stamp. Since the
  last dip the load falls as before, `1 - exp(-since / run_px)`; after the first dip it
  carries what the nib had spent by the dip, `1 - exp(-dip_px / run_px)`, and lets it ease
  away as `exp(-since / (REFILL_WIDTHS * width))`, with `_REFILL_WIDTHS` = 2. The spent
  share is continuous at the dip, the line swells back to full over about three nib widths,
  and it is capped at 1. Before the first dip nothing is carried, so a stroke shorter than
  one dip is unchanged.
- Only the nib (`pen_starve`) changes. A brush's reservoir (`ink_starve`, `deposit.spend`)
  keeps its hard seam at the dip, which is what makes a long brushed line look drawn.
- No style field is added: the refill length is a property of a nib, stated in its own
  widths.

Pinned by `tests/unit/ink/test_stamp.py` (`TestTheReload`), on the issue's repro: the line
regains under 60% of what its run lost within one nib width (it regains 42%); no nib width
loses a quarter of what a run loses, and the line keeps 40% of its peak; and the dry nib's
line is nowhere darker than the same nib's never running down. The existing test that a long
line comes back to its full width somewhere past the first dip still holds.

### Mutation testing

Run on `ink.stamp._width` and `ink.stamp._nib_spent`: 93 mutants, 77 killed by the first
run; the tests above then killed 5 of the 9 `_nib_spent` survivors (a growing exponent, a
spent share at the dip over 1, the carried share divided rather than multiplied). Left:

- `_nib_spent` 16 (`exp(-dip_px * run_px)`: the share spent at the dip read as 1 rather than
  0.75 on the repro). Not equivalent, and not killed: the extra drop is from a quarter of the
  nib's width to none, and a nib at no width still lays its core, so neither the column ink
  nor the line's width tells them apart. 24 (the refill length floored at 1 px rather than
  1e-6): only a pen under half a pixel wide reaches the floor. 32 (`run > dip_px` for
  `>=`): differs only on a stamp exactly at the dip. 43 (the cap at 2 rather than 1): the
  spent and carried shares never sum past the share at the dip, so the cap never binds.
- `_width` 9, 10, 25 (a width profile of one or two samples, or one starting a pixel in):
  the profile lines this branch does not touch; no nib profile has under three samples and a
  one-pixel shift of its start is below what a test of the mark resolves. 27, 29, 39 (a
  float64 array where float32 was): precision only. 47 (`spent` not handed on, so the
  weights do not lighten with it): the line still thins, and its lightening is not measured
  apart from its thinning by any test.

## Golden regeneration

Process as ADR 0036, with the review images of ADR 0052, on top of ADR 0059's images (main
at `4fed836`). The tolerance bound is not changed, no gate is loosened and the hash input
does not change.

### Lynmouth compare, against the committed goldens

```
paper.webp: identical yes, differing fraction 0.000000
wash.webp: identical yes, differing fraction 0.000000
pen.webp: identical yes, differing fraction 0.000000
labels-centreline.webp: identical no, differing fraction 0.000000
map.png: identical no, differing fraction 0.000000
manifest hash: 340a7f6e260ee1e2-d9c56c0811177b0f here, 340a7f6e260ee1e2-d9c56c0811177b0f in the goldens
```

No Lynmouth map stroke is long enough to reach a dip (the default reservoir is 420 nib
widths and the dip 3.2 of those), so the pen plate is byte-identical. The label plate and the
map move by at most one level in a few pixels, where a long leader or glyph stroke reaches a
dip. `GOLDEN_HASH`, `PINNED_LABELS`, the place pins, the map-styles means and the smoke lock
do not move.

### Docs images

Every docs image and master was repainted with `make_docs_images.py`. Two masters moved:

| Master | Fraction | Max delta |
|---|---|---|
| `explanation/nib-runs-dry.png` | 0.010401 | 109 |
| `places/y-fenni.png` | 0.000000 | 1 |

and three docs images (`explanation/nib-runs-dry.webp` 0.008528, `places/y-fenni.webp`
0.021756 and `places/oxford.webp` 0.005826, both of the last two at most 12 levels, the
lossy encoder spreading a one-level change). Looked at side by side with `main`: on
`nib-runs-dry` the thick step where the line jumped back to full width at each reload is now
a swell over a few nib widths; on the place cards nothing a reader would see moved.

## Consequences

- A nib that runs dry swells back at the reload instead of stepping, so the docs figure now
  shows what its caption says.
- Every pen-drawn map stroke long enough to reach a dip moves near the dip; shorter strokes
  do not.
- A further regeneration needs its own ADR.
