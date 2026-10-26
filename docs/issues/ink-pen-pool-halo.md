# A pen over 2 pixels wide leaves a grey halo round its ink

GitHub issue: [#39](https://github.com/findlaywebb/pyntpot/issues/39)

`pool` in `ink/deposit.py` leaves a blot where a stroke starts. Its Gaussian's radius is
`max(width * pool_radius_frac, 1.2)` pixels (`BrushStyle.pen_pool_radius_frac`, 0.5 by
default) and its height `pen_pool_gain` (1.9). The radius grows with the pen, so a pen
wider than about 2 pixels pools a soft blot that reaches past the stroke it belongs to. A
word lettered with such a pen, where every glyph stroke starts with a blot, looks as if it
had a grey drop shadow 3 to 8 pixels wide below and round it. The P7.V13 round-2 critique
measured the mean darkening in a ring 3 to 8 pixels from the ink of the same word: 0.0083
at a 2.6 px pen with the defaults, 0.0008 at 1.5 px, and 0.0 at 2.6 px with
`pen_pool_gain=0` or `pen_pool_radius_frac=0.1`. The nib's backing wash plays no part: the
result is the same with the wash off.

The docs examples work round it with `BrushStyle(pen_pool_radius_frac=0.15)` wherever a
pen of 2 px or more letters a word (`examples/tutorial_grids.py`, `composition.py`,
`word.py`, `how_to_own_shapes.py`, `nib_stages.py`). The maps' route pens are wider still
and may show the same halo.

To show it: letter one word at 56 px with `NibStyle(label_pen_width_px=2.6)` and the
default `BrushStyle`, then again with `pen_pool_radius_frac=0.15`, and compare the paper
in the ring round the ink.

Possible fix: cap the pool radius in absolute pixels, so that a wide pen's blot stays about
as large as a narrow one's, or clip the pool to a dilation of the stroke's own cover. Every
pen and nib stroke moves, so the lettered goldens and docs images need a regeneration
window of their own with an ADR.

Found by the P7.V13 round-2 picture and reference critiques (2026-10-25).
