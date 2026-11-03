# The outside of the bend may be no better than chance

GitHub issue: [#144](https://github.com/findlaywebb/pyntpot/issues/144)

Area: maps (lettering).

`SPAN_CURVE_SIDE` lets a bend move a span's bracket to its outside, on the grounds that
the outside of a bend has room the inside lacks. #54's sweep (spec 004,
`specs/004-span-curve-scale-sweep/sweep.md`) measured this on the Ambleside, Skye and
Y Fenni fixture tracks. A stretch is decisive when one side keeps more than a quarter
more of its own mark once cleared of the route. The outside was the better mark on:

- 0 to 33% of decisive stretches at 16 and 24 caps, at every scale with any;
- 20 to 100% at 10 caps, mostly near half.

No scale had more than 10 decisive stretches, so this proves nothing either way. It
does question whether the bend's vote helps at all.

Possible fix: gather more fixture tracks with span requests, using spec 004's tool and
scoring rule. If the outside still isn't clearly better, turn `SPAN_CURVE_SIDE` off and
record why in an ADR.
