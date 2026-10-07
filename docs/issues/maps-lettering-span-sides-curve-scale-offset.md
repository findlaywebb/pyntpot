# The bend is read at 1.5 cap heights, tuned against an offset that is now 1.2

`pyntpot.maps.lettering.span_sides.SPAN_CURVE_SCALE_CAPS` is 1.5. Its comment
argued that "the right spacing is the offset the bracket will be drawn at,
1.7 cap heights" and that 1.5 "is under the offset". The offset is
`pyntpot.maps.lettering.span_line.SPAN_OFFSET_CAPS`, 1.2, so 1.5 is now over
it, and the sweep the comment quotes (89% right at 1.5 caps, 79% at 2) was
measured against the older offset.

P6 rewrote the comment to name `SPAN_OFFSET_CAPS` and dropped the 1.7 figure;
it changed no value. Whether 1.5 is still the best reading scale needs the
sweep re-run over the cached rides, which is not a docs task.

Possible fix: re-run the reading-scale sweep at the current offset and set
`SPAN_CURVE_SCALE_CAPS` from it, or derive it from `SPAN_OFFSET_CAPS`, then
review the span goldens.
