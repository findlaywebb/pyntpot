# Minor roads and streams are drawn as short stubs where the route's corridor clips them

GitHub issue: [#56](https://github.com/findlaywebb/pyntpot/issues/56)

Minor roads and streams are clipped to the route's corridor, and a piece that is only a few
pixels long after the clip is still drawn. On the Ambleside card short brown hair-like
stubs stick out of the route between Rydal and Ambleside, and short blue dashes of stream
stop dead on the land south of Loughrigg Terrace and west of Rydal Cave.

Found by the round-2 map critique (2026-10-25).

To show it: paint the Ambleside place card from `tests/fixtures/ambleside/` at 1200 pixels
and look along the route between Rydal and Ambleside.

Possible fix: drop a piece shorter than about twenty display pixels after clipping, or fade
its ends. The vector layers and docs images move, so it needs a regeneration window of its own
with an ADR.
