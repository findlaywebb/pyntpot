# 0025 — Second golden regeneration: the finer ink grid laid centre to centre

Status: proposed

## Context

`InkPad.lay` mapped a polyline onto the pad's finer grid as `line * ink_ss` in all three of
its `stamp` calls (the profiles path, the unjoined path and the chained path). That aligns
the two grids at their corners, but plate pixel `i` covers fine pixels `i * ink_ss` to
`i * ink_ss + ink_ss - 1` and is centred on fine pixel `i * ink_ss + (ink_ss - 1) / 2`. So
every mark painted at `ink_ss` above 1 sat `(1 - 1 / ink_ss) / 2` of a plate pixel up and
left of where the plate's own grid lays it: a third of a pixel at the default theme's
`ink_ss` of 3.

The fix moves every plate a pad paints, so it moves the goldens and needs a regeneration.
ADR 0006 made its window the port's only regeneration; this ADR is the second, for this
one fix. The maintainer widened the golden-group rule for this row and, shown before,
after and difference (x8) comparisons of the fix, accepted the drift: "Accept it -
identical to human eye" (2026-10-21).

## Decision

One regeneration window of one fix step and the regeneration, run as ADR 0006's was: the
step is painted on the Lynmouth fixture and compared with the output of the window's
starting commit on the same machine, under gate options that say what it may move, and
the goldens are regenerated once at the end.

- The tolerance bound in `tests/golden/test_parity.py` (`MAX_DIFFERING_FRACTION = 0.005`,
  `MAX_CHANNEL_DELTA = 2`) is not changed.
- The hash input does not change: the step requires the manifest hash equal.
- Step 1 exceeds the per-step bound on wash, pen, labels-centreline and map, and is
  committed as the one maintainer-accepted exception, as ADR 0006's step 3 was, because
  its drift is explained: the whole ink layer moves a third of a pixel down and right, and
  paper, which no pad paints, is byte-identical.

### Steps

| Step | Commit | Expected | Gate options |
|---|---|---|---|
| 0 | `79a95ad` | baseline, made on the window's starting commit (`"dirty": false`) | none |
| 1 | `Lay the finer ink grid centre to centre with the plate` | `paper.webp` byte-identical to step 0; wash, pen, labels-centreline and map past the bound at the accepted figures; the hash equal; `labels.txt` equal | `--require-identical paper.webp --max-fraction 0.005 --require-hash equal --require-labels-equal` |
| 2 | `Regenerate the goldens once more for the half-pixel fix` | every output byte-identical to step 1 | `--require-identical all --require-hash equal` |

Outcome of step 1's gate compare, against step 0 (differing fraction per output, past the
channel bound):

| Step | paper | wash | pen | labels-centreline | map | Hash | `labels.txt` |
|---|---|---|---|---|---|---|---|
| 1 | 0 (identical) | 0.053400 | 0.007298 | 0.038954 | 0.060095 | `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, equal | equal |

### Step 1

Step 1 adds `InkPad._on_grid`, which lays a render-pixel polyline on the pad's grid pixel
centre on pixel centre (`line * ink_ss + (ink_ss - 1) / 2` when `ink_ss` is above 1), and
the three `stamp` calls pass it. At `ink_ss` 1 nothing changes. A new test,
`test_a_finer_grid_lays_the_mark_where_the_plate_grid_does`, pins the density-weighted
mean row of a level stroke at `ink_ss` 2 and 3 to within 0.1 px of the `ink_ss` 1 mark;
before the fix it sat 0.28 px up at `ink_ss` 2.

Step 1 compare, against step 0 (the gate; exit 1, its four `gate violated` lines the
accepted exception):

```
paper.webp against step-0: identical yes, differing fraction 0.000000
wash.webp against step-0: identical no, differing fraction 0.053400
pen.webp against step-0: identical no, differing fraction 0.007298
labels-centreline.webp against step-0: identical no, differing fraction 0.038954
map.png against step-0: identical no, differing fraction 0.060095
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, 340a7f6e260ee1e2-e5a5f1b4b3ca2177 in step-0
gate violated: wash.webp differing fraction 0.053400 over 0.005
gate violated: pen.webp differing fraction 0.007298 over 0.005
gate violated: labels-centreline.webp differing fraction 0.038954 over 0.005
gate violated: map.png differing fraction 0.060095 over 0.005
```

Step 1 compare, against the committed goldens (cumulative record):

```
paper.webp against tests/golden/lynmouth: identical yes, differing fraction 0.000000
wash.webp against tests/golden/lynmouth: identical no, differing fraction 0.053400
pen.webp against tests/golden/lynmouth: identical no, differing fraction 0.007298
labels-centreline.webp against tests/golden/lynmouth: identical no, differing fraction 0.038954
map.png against tests/golden/lynmouth: identical no, differing fraction 0.060095
manifest hash: 340a7f6e260ee1e2-e5a5f1b4b3ca2177 here, 340a7f6e260ee1e2-e5a5f1b4b3ca2177 in tests/golden/lynmouth
```

**The figures the maintainer was shown.** The comparison the maintainer accepted gave map
0.0601, wash 0.0534, labels-centreline 0.0344 and pen 0.0005, from a script that read
the RGB channels only. `make_golden.py --compare`, the window's compare tool, counts alpha
too for the RGBA outputs, which is why pen and labels-centreline differ; the images are
the same. The gate figures are `make_golden.py`'s: map 0.060095, wash 0.053400,
labels-centreline 0.038954, pen 0.007298, paper 0.

**Two tests move with the fix.**

- `tests/unit/ink/test_pad.py::test_a_finer_grid_converges_on_the_mark_the_brush_describes`
  compared `ink_ss` 1, 2 and 3 with an `ink_ss` 6 reference. Before the fix the reference
  sat 5/12 px off the `ink_ss` 1 mark but only 1/6 px off the `ink_ss` 2 mark, so the
  error at 1 carried more grid offset than the error at 2, and the first doubling looked
  better than it is. With every grid on the reference's centres, err(2)/err(1) is 0.793 to
  0.815 over a sweep of eight generator seeds, three sheet seeds and four geometries
  (0.695 to 0.750 before), and err(3)/err(2) is 0.910 to 1.037, so the error stops at the
  bristle texture's floor after the first doubling. The test keeps its `gap` assertions,
  bounds the first doubling at 0.85 (was 0.8), drops `err[1] > err[2]`, and asserts
  `err[2] < err[0] * 0.9`.
- `tests/unit/maps/painter/test_smoke.py::SMOKE_SHA`: the `pen` and `wash` hashes of the
  smoke plate move, since the pad paints both; `paper` does not.

## Consequences

- The goldens record the corrected grid. G-self and the byte-exact golden run hold from
  the regeneration on.
- The maintainer's exact run on their machine is the follow-up check, as ADR 0006 says;
  exact parity is per platform and tolerance mode is the cross-platform gate.
- A further regeneration needs its own ADR.

The machine step 1 was measured on: the agent's Linux container,
`Linux vm 6.18.44-fc-v140 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux`,
Python 3.13.16, numpy 2.5.2, Pillow 13.0.0, fonttools 4.63.0.
