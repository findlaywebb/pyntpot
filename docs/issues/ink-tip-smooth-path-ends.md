# Corner smoothing pulls a stroke's ends in along its path

`pyntpot.ink.tip._smooth_path` rounds a path's corners with two box passes
over the resampled coordinates, edge-padded. Its docstring said the ends were
"held by edge padding, so a mark still starts and finishes where the way
does", and the `pyntpot.ink.tip` module docstring listed "the smoothed path
keeps its two ends" as an invariant. The code does not do that: edge padding
averages each end with its inner neighbours, so on a straight end the first
and last samples move inward along the path. On a 50-sample straight line at
0.4 px spacing with the default smoothing for a 4.8 px brush (radius 3.36 px)
the start moves from 0.0 to 1.41 px and the end from 19.6 to 18.19 px, about
four tenths of the radius at each end. It also smooths `x` and `y` in place.

P6 corrected both docstrings to say what the code does. It does not change
the code: the docs pass changes no executable line, and a fix moves pixels in
every plate painted with `stroke_smooth` on.

To show it: build `x = np.arange(50, dtype=np.float32) * 0.4` and
`y = np.zeros(50, np.float32)`, then call `_smooth_path(x, y, 3.36, 0.4)` and
compare the first and last `x` with 0.0 and 19.6.

Possible fix: after smoothing, put the first and last samples back where they
were (or blend the first and last `r` samples back towards the raw path), so
a mark starts and finishes on the way's own ends. That needs a golden
decision for themes with `stroke_smooth` on, and a property test that the
ends are unmoved.
