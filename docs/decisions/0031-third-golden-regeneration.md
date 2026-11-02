# 0031 — Third golden regeneration: the East Lyn label

Status: accepted

## Context

The golden Lynmouth card lettered the East Lyn twice: once flat, reading "East Lyn", and
once along the water, reading "East Lp". Two defects, one per symptom.

- **The window was shorter than the written name.** The placer measured a name without its
  kind's tracking (`pipeline.py` passed `partial(lettering_marks.box_size, hand)`, and
  `box_size` called `hand.measure` with none), so `placement.py` cut a window of the untracked
  width times 1.02. The hand then wrote the name with `KIND_TRACKING` (0.24 em for a river,
  0.10 em for a road). For "East Lyn" at 18 px the window was 65.0 px and the written name
  85.0 px; the glyph centres of "y" and "n" fell past the walk's end, `Hand._along` clamped
  both to the end point, and the "y" descender over the "n" read as "p". Every curved river
  and road name was affected.
- **A river's repeat fell back to flat paper.** The water runs 652 px, so the river takes
  `MAJOR_RIVER_LABELS` (two). Every window on the water that passed the shape test lay within
  the repeat guard of the first name, so `place_along` returned nothing, and `_place` set the
  repeat on the cheapest flat paper about 70 px from the first name, although the placer's
  docstring says a name that repeats another's place is dropped.

Both fixes move the labels plate and the card past `MAX_DIFFERING_FRACTION`, so they land in
a golden regeneration with its own ADR, run as ADR 0025's was. With both fixes "B3234" is set
flat beside Lynton: its correctly sized window now costs more than the flat seat. The
maintainer saw before and after crops of fixes A and B together, including "B3234" set flat
beside Lynton, and accepted them: "Fix looks good, make it slice 1" (2026-10-23).

## Decision

One regeneration window of two fix steps and the regeneration. Each step is painted on the
Lynmouth fixture and compared with the previous step's output on the same machine, under
gate options that say what it may move, and the goldens are regenerated once at the end.

- The tolerance bound in `tests/golden/test_parity.py` (`MAX_DIFFERING_FRACTION = 0.005`,
  `MAX_CHANNEL_DELTA = 2`) is not changed.
- The hash input does not change: every step requires the manifest hash equal.
- `paper.webp`, `wash.webp` and `pen.webp` are required byte-identical at every step: the
  label plate is written beside the plates and moves neither the paper, the wash nor the pen.
- Step 1 exceeds the per-step bound on labels-centreline and map, and is committed as the
  maintainer-accepted exception; step 2 stays within the bound on map and exceeds it on
  labels-centreline, which is the same accepted drift (the repeat's flat "East Lyn" leaves
  the label plate). The maintainer accepted both steps together.

### Steps

| Step | Commit | Expected | Gate options |
|---|---|---|---|
| 0 | `a804fe3` | baseline, made on the window's starting commit (`"dirty": false`) | none |
| 1 | `20dab4c` `Measure a curved name's window with its kind's tracking` | paper, wash and pen byte-identical to step 0; labels-centreline and map past the bound; the hash equal; `labels.txt` equal | `--require-identical paper.webp wash.webp pen.webp --require-hash equal --require-labels-equal` |
| 2 | `af44f73` `Drop a river's repeat that finds no water` | paper, wash and pen byte-identical to step 1; the hash equal; `labels.txt` loses exactly one line, `East Lyn` | `--require-identical paper.webp wash.webp pen.webp --require-hash equal` |
| 3 | `Regenerate the goldens for the East Lyn label` | every output byte-identical to step 2 | `--require-identical all --require-hash equal` |

Outcome of each step's gate compare, against the previous step (differing fraction per
output, past the channel bound):

| Step | paper | wash | pen | labels-centreline | map | Hash | `labels.txt` |
|---|---|---|---|---|---|---|---|
| 1 | 0 (identical) | 0 (identical) | 0 (identical) | 0.058434 | 0.016597 | `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, equal | equal |
| 2 | 0 (identical) | 0 (identical) | 0 (identical) | 0.015885 | 0.002907 | `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, equal | one line deleted: `East Lyn` |

Step 2's `diff` of `labels.txt` against step 1's:

```
4d3
< East Lyn
```

Step 3 compared with the step-2 output was byte-identical for every output (the regenerated
`labels-centreline.webp` and `map.png` equal step 2's).

### Step 1

`KIND_TRACKING` moves from `maps/lettering_marks.py` to `maps/lettering/label.py`
(`placement` cannot import `lettering_marks`, which imports `lettering_window`, which imports
`placement`); `lettering_marks` imports it from there. `label.py` gains
`MeasureTracked = Callable[[str, float, float], tuple[float, float]]`. `box_size` becomes
`box_size(hand, text, size, tracking=0.0)`. `place` and `_place` take a keyword-only
`measure_tracked` and measure the along-window width with the label's kind's tracking; the
flat candidates keep `measure_fn`. `pipeline.py` passes
`measure_tracked=partial(lettering_marks.box_size, hand)`. Two tests were written red first:
`test_a_curved_name_is_given_a_window_as_long_as_the_hand_writes_it` and
`test_every_glyph_of_a_placed_name_sits_inside_its_window`.

### Step 2

In `_place`, a river label that repeats a name already set along its water and finds no
window on that water is dropped; a river's first name keeps its flat fallback. A test was
written red first:
`test_a_rivers_second_name_with_no_water_left_is_dropped_not_set_flat`.
`test_a_rivers_two_names_are_kept_apart_along_the_water_not_across_the_map` stays green, and
`PINNED_LABELS` in `tests/unit/maps/test_pipeline_letter_compose.py` loses the second
"East Lyn" (nine names).

### Hashes

- Manifest hash of the old goldens and after every step: `340a7f6e260ee1e2-e5a5f1b4b3ca2177`.
- Manifest hash of the regenerated goldens: `340a7f6e260ee1e2-e5a5f1b4b3ca2177`, unchanged:
  the fix moves label pixels, not the geometry or style the hash covers. `GOLDEN_HASH` in
  `tests/unit/maps/test_pipeline_fetch_paint.py` is unchanged.

### Regeneration

`tests/golden/make_golden.py` painted the Lynmouth fixture into `tests/golden/lynmouth/` in
place, on the step-2 commit `af44f73`. Only `labels-centreline.webp` and `map.png` changed;
`paper.webp`, `wash.webp`, `pen.webp` and `plates.json` are untouched (`plates.json` came out
identical but for the final newline the end-of-file hook adds, so the committed file stands).
The byte-exact golden run (`uv run pytest -m golden`) and G-here then passed.

Final compare, a fresh paint against the regenerated goldens (the gate,
`--require-identical all --require-hash equal`, exit 0): every output identical, differing
fraction 0.000000, hash `340a7f6e260ee1e2-e5a5f1b4b3ca2177` on both sides.

Cumulative drift, regenerated goldens against the old ones: paper 0, wash 0, pen 0,
labels-centreline 0.067173, map 0.017122; hash unchanged.

What moved and why: curved river and road names are cut to the length the hand writes them
(the "y" and "n" of "East Lyn" no longer pile onto one point), the second "East Lyn", which
had no water left, is no longer set on flat paper, and "B3234" is set flat beside Lynton.

## Consequences

- The goldens record the corrected windows. G-self and the byte-exact golden run hold from
  the regeneration on.
- The pinned label names are nine: the second "East Lyn" is gone.
- Flat boxes for kinds with tracking (settlements, roads, a river's flat first name) are still
  reserved without it, so they understate the drawn width; this is filed in
  `docs/issues/maps-lettering-flat-boxes-without-tracking.md`, not fixed here.
- A further regeneration needs its own ADR.

The machine the steps were measured on and the goldens were regenerated on: the agent's
Linux container, Python 3.13, with the parity stack at its pins. G-here runs the goldens
byte-exact there; every other platform uses the tolerance gate.
