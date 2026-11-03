# An organic brush's drift shifts a short stroke sideways
GitHub issue: [#125](https://github.com/findlaywebb/pyntpot/issues/125)

On an organic brush with coherence, `_organic_fields` in `ink/stamp.py` smooths each
bristle's lattice drift across the tip (`tip_band`) and rescales the result back to the
spread it had before. The rescale was taken about zero, so it multiplies the part every
bristle shares as well as the part they differ by. On a stroke shorter than one drift cell
the field is nearly constant along the stroke, so the shared part is mostly a constant, and
the rescale turns it into a sideways shift of the whole stroke along its normal: up to about
three times the drift's own reach (a 5 by 7 px ring moved 3.3 px off its path at seed
worst-case, against a 1.1 px jitter).

On a closed glyph or ring that changes its radius. A 20 px "o" at scale 2 has its counter
60% inked at worst across 400 label seeds, and a pin ring can fill once another change
reshuffles the generator's draws.

The fix rescales only the spread about the stroke's own mean, which smoothing across the
tip leaves where it was.
