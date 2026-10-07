# The longest span takes the rung nearest the route, not the outer rail

`pyntpot.maps.lettering.spans.place_spans` takes the spans longest first, and
`pyntpot.maps.lettering.spans._rung` gives the first span on a side rung 0,
the offset nearest the route; a later, shorter span that overlaps it moves
out a rung. Its docstring said the opposite: "the longest span is the outer
rail and shorter ones nest inside it". `Span.rank`'s comment ("so overlapping
spans nest rather than stack") reads the same way.

P6 rewrote the `place_spans` docstring to describe the code and changed no
code. Which order reads better on the card is a design question the goldens
cannot answer: shorter brackets outside a longer one may be the intended
look or a defect.

To show it: on an empty side, `_rung` gives `Span(i0=10, i1=90)` rung 0;
with that recorded as `(10, 90, 0)`, it gives the overlapping
`Span(i0=30, i1=50)` rung 1, further out.

Possible fix: decide which nesting is wanted. If the longest should be the
outer rail, take the spans shortest first in `place_spans` (or rank from the
outside in `_rung`) and regenerate the span goldens; otherwise nothing in the
code changes.
