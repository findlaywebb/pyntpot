# A leader's pin ring can close into a dot

GitHub issue: [#130](https://github.com/findlaywebb/pyntpot/issues/130)

`pin` in `maps/lettering_furniture.py` draws the ring a leader points at with a radius of
`max(size * 0.14, 2.2)` display pixels: 2.8 px at the shipped 20 px type size. The nib
strokes it with the `pin` role's weight (`MARK_WEIGHT["pin"]` in `letters/nib.py`, 1.5 times
the 0.85 px leader width), a 1.275 px pen, so the hole inside the ink is only about 2.2 px
across, and the organic brush's bristle jitter is wide enough to fill it.

Measured as `TestCounters` in `tests/unit/letters/test_nib.py` measures a counter (the mean
alpha inside half the ring's radius, at a render scale of 2), stroked alone with the default
theme over 400 seeds: 21% of pins have a core above 0.4 and the worst reads 0.67, a filled
dot. With the pin brush's jitter at 0 none close (worst 0.34), so it is the jitter that
closes it, but the mean core is still 0.26 without it: the ring is too small for its pen.

On main the Lynmouth "Lynton and Exmoor Museum" pin is open by luck (core 0.382). Any change
that reshuffles the label generator can close it: on `fix/43-skeleton-tails` it reads 0.750.

The ring's radius is set from the type size alone and never from the pen it is drawn with,
so nothing keeps a hole a pen width or two across.
