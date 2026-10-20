# The ink pad's finer grid sits a fraction of a pixel off the plate's

Area: `ink`.

`pyntpot.ink.pad.InkPad.lay` maps a polyline onto the finer grid as
`line * ss`. That aligns the two grids at their corners, not at their pixel
centres: plate pixel `i` covers fine pixels `i * ss` to `i * ss + ss - 1`,
whose centre is at `i * ss + (ss - 1) / 2`, while the line's point `i` lands
on fine pixel `i * ss`. After `read` reduces the density back, every mark
painted with `ink_ss` above 1 sits `(1 - 1 / ss) / 2` of a plate pixel up and
to the left of where the same mark sits at `ink_ss` 1: a third of a pixel at
the default theme's `ink_ss = 3`.

Found while measuring a replacement for
`tests/unit/ink/test_pad.py::test_a_finer_grid_converges_on_the_mark_the_brush_describes`:
the shift is about 13% of the pixel error between `ink_ss` 1 and a finer-grid
reference. The shift differs with `ink_ss` (none at 1, five twelfths of a pixel
at the test's reference of 6), so it adds to the error the test measures
rather than cancelling out of it.

To show it: on a `Sheet(40, 300, gran_px=9.0, seed=11)`, paint a horizontal
`MAJ6-e` route stroke (width 3.0) at `y = 20.0` through `InkPad` with
`BrushStyle(ink_ss=1)` and with `BrushStyle(ink_ss=3)`, rng seed 91, and take
the density-weighted mean row of each `read`: 20.21 at `ink_ss` 1 and 19.88 at
`ink_ss` 3, a third of a pixel up. Adding `(ss - 1) / (2 * ss)` to the polyline
before `lay` (what the fix would do inside `lay`) gives 20.22.

Possible fix: offset the scaled line by `(ss - 1) / 2` fine pixels in `lay`, in
all three of its stamp calls. The default theme paints every pad at
`ink_ss = 3`, so the fix moves pixels on every golden plate and needs a golden
regeneration under its own decision.
