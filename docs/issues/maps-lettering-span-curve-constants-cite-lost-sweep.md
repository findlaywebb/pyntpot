# Four bend constants still cite a sweep nobody can rerun

GitHub issue: [#142](https://github.com/findlaywebb/pyntpot/issues/142)

Area: maps (lettering).

Four constants in `pyntpot.maps.lettering.span_sides` justify their values with a sweep
"over the four cached tracks" (187 stretches):

- `SPAN_CURVE_MIN_TURN_DEG` (35): "25 degrees moves 33 stretches for 24 better and 8
  worse, 35 moves 32 for 24 and 7".
- `SPAN_CURVE_FULL_TURN_DEG` (75).
- `SPAN_CURVE_MIN_COHERENCE` (0.62).
- `SPAN_CURVE_WEIGHT` (0.08): "picked by measuring the margins".

The four tracks are upstream reference rides. The repository does not hold them, and no
upstream data may cross into it (spec 001, D16). The sweep left no script, no stretch
selection, no scoring rule and no labels. It ran at the old 1.7-cap bracket offset,
before the free-paper sign fix, with a bracket since replaced.

#54 found the same for `SPAN_CURVE_SCALE_CAPS`. Spec 004 re-measured it on the
Ambleside, Skye and Y Fenni fixture tracks with a scoring rule written down first. Only
4 stretches were decisive at 1.5, too few to compare scales.

Possible fix:

- Reword the four comments so they no longer state the lost figures as current evidence.
- Re-measure them with spec 004's tool (`tests/fixtures/span_sweep_score.py`) once there
  are enough fixture tracks with span requests to decide anything.
