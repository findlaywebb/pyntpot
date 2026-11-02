# The wash under a name shows as a pale box

GitHub issue: [#49](https://github.com/findlaywebb/pyntpot/issues/49)

`label_wash` lifts the paint under a name so it reads. Where the paint is dark (the grey-mauve
rock of the Yr Wyddfa card, the wood and fell of the Ambleside card) the lifted area shows as
a pale lozenge or rectangle behind "Glaslyn", "Llyn Llydaw", "Crib Goch", "A4086" and
"Loughrigg Terrace". The backing follows the label's box, not the glyphs, and its edge is
hard.

Found by the round-2 map critique (2026-10-25).

To show it: paint the Yr Wyddfa and Ambleside place cards at full size and look at the
names above.

Possible fix: feather the backing mask, or build it from the glyph outlines grown by a few
pixels. The lettered goldens and docs images move, so it needs a regeneration window of its
own with an ADR.
