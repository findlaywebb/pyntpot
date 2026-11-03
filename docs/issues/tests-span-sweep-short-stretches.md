# The sweep's 10-cap stretches are too short to read above scale 2.0

GitHub issue: [#143](https://github.com/findlaywebb/pyntpot/issues/143)

Area: tests (fixture tools).

The span curve scale sweep (`tests/fixtures/span_sweep_score.py` and
`tests/fixtures/sweep_span_scale.py`, spec 004) reads stretches 16 caps long. It also
reports two secondary lengths, 10 and 24 caps, which never decide anything.

Spec 004 argues that a stretch needs at least five resampled segments for its turning to
mean anything. The resampling step is the reading scale, so a 10-cap stretch read above
scale 2.0 has fewer than five. The 10-cap table is therefore cut off at 2.0, and its rows
near 2.0 rest on very few segments.

Possible fix: drop the 10-cap length, or tie the window length to the reading scale
(e.g. at least five scale steps) so every row has the same number of segments.
