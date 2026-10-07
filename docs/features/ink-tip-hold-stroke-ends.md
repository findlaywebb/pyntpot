# A smoothed stroke could keep the way's own ends

**What exists today.** `pyntpot.ink.tip._smooth_path` rounds a path's corners
with two box passes over the resampled coordinates, edge-padded. Edge padding
averages each end with its inner neighbours, so on a straight end the first and
last samples move inward along the path, by about four tenths of the smoothing
radius at each end. On a 50-sample straight line at 0.4 px spacing, with the
default smoothing for a 4.8 px brush (`stroke_smooth_mult` 0.7, radius 3.36 px),
the start moves from 0.0 to 1.41 px and the end from 19.6 to 18.19 px. The
smoothing runs for every stroke of a brush with `stroke_smooth` on, which the
default theme sets, so every pen and label stroke on the golden card passes
through it, and the goldens (`pen.webp`, `labels-centreline.webp`, `map.png`)
pin the drawn-in ends. The docstrings of `_smooth_path` and of `pyntpot.ink.tip`
say what the code does.

**What the feature would add.** A style switch, off by default, that puts a
smoothed stroke's ends back on the way's own ends, so a mark starts and
finishes where the way does while its corners stay rounded. With the switch off
the current look is kept, and the goldens do not move.

**Why it is not a defect.** The drawn-in ends are the shipped look, and the
goldens record it. An earlier docstring said the ends were held ("a mark still
starts and finishes where the way does"); the maintainer kept the current look
and asked for the held ends as an option.

**Possible shape.** A `BrushStyle` field beside `stroke_smooth` and
`stroke_smooth_mult` holds the switch. With it on, after smoothing, the first
and last samples go back to where they were, or the first and last `r` samples
are blended back towards the raw path so the end does not kink. A property test
pins that with the switch on a smoothed path keeps its two ends, and a unit pin
gives the case above: ends 0.0 and 19.6 with the switch on, 1.41 and 18.19 with
it off.
