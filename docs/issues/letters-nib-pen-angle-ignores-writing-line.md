# The nib's angle is fixed to the page, not to the writing line

`pyntpot.letters.nib._pen_profile` takes each segment's direction as
`arctan2(dy, dx)` in render pixels and compares it with
`radians(NibStyle.label_pen_angle_deg) + mark.pen`. Both angles are measured
from the page's horizontal (y down). Before this audit the comment on
`pyntpot.letters.style.NibStyle.label_pen_angle_deg` and the `angle` argument
of `_pen_profile` said the angle was "anticlockwise from the writing line".

For a flat block the writing line is the page's horizontal, so the two
readings agree up to the sign. For a setting along a path
(`pyntpot.letters.hand.Hand._along`) each glyph is turned onto the path's
tangent, but the nib is not: a name written down a steep road has its thick
and thin strokes in the page's places, not the letter's. A pen held by a hand
turns with the line it writes along, which is the more plausible intent of
the old text.

P6 does not fix it because the fix changes code and would move pixels in the
lettering goldens. The comment and docstring now say what the code does.

How to show it: write one word with `Hand.write` along a horizontal path and
along the same path turned 90 degrees, stroke both with `nib.plate`, and
compare the stroke widths of the same glyph.

Possible fix: carry the glyph's tangent angle on each `Mark` written along a
path (or fold it into `Mark.pen`) and add it to the nib angle in `_items`;
regenerate the goldens under a golden decision.
