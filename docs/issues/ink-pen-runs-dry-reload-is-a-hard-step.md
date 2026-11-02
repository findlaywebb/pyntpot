# A pen that runs dry jumps back to full width at each reload

GitHub issue: [#40](https://github.com/findlaywebb/pyntpot/issues/40)

With `BrushStyle.pen_starve` on, `_width` in `ink/stamp.py` thins the nib by
`1 - exp(-(cumulative pressure * step mod dip_px) / run_px)`. The `mod` resets the spent
share to zero in one stamp, so the width goes from its thinnest to its fullest between two
neighbouring stamps. On `docs/images/explanation/nib-runs-dry.webp` the ink is 5, 4, 4, 3,
3 pixels wide along a run and then 6 at the reload, and a little further on it goes 5, 6, 9,
12 within a few pixels. It reads as a glitch and not as a nib dipped again, and the figure's
caption ("swelling back at each reload") is not what the eye sees.

To show it: stroke one long line with `BrushStyle(pen_starve=True, pen_reservoir=22.0,
pen_thin=1.0, ink_dip_mult=1.4)` and a pen brush (`MAJ6-e`, 5 px), and read the stroke's
width along it: it falls and then steps up at the reload.

Possible fix: ease the refill, so that the spent share falls back over two or three nib
widths after the reload (for example by smoothing `spent` with a short moving average before
`nib` is computed, or by letting it decay as `exp(-since_dip / (2 * width))` once the dip
point is passed). The docs figure and every golden that sets `pen_starve` move, so it needs
a regeneration window of its own with an ADR.

Found by the P7.V13 round-2 reference critique (2026-10-25).
