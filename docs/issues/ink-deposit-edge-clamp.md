# Ink stamped off the plate piles up on its edge pixels

`pyntpot.ink.deposit.deposit` splats each sample bilinearly into the
accumulator, and clamps each of the four corner indices into the grid with
`np.clip(..., 0, w - 1)` and `np.clip(..., 0, h - 1)`. A sample that lies off
the accumulator is not dropped: both of its corners on that axis clamp to the
same edge pixel, so its full weight lands on the plate's outermost row or
column. A stroke that runs past the edge of the plate, or whose bristle drift
or wobble carries it past, therefore lays a line of ink along the border.

P6 recorded the behaviour in the docstring ("A sample off the accumulator
lands on its nearest edge pixel") and does not change it: the docs pass
changes no executable line, and whether any current plate is affected depends
on how close the callers' paths come to the edge, which needs a pixel check.

To show it: make `acc = np.zeros((8, 8), np.float32)`, call
`deposit(acc, None, (np.array([[-5.0]]), np.array([[3.0]])), np.ones((1, 1), np.float32), None, None)`
and read `acc[3, 0]`, which is 1.0.

Possible fix: mask out the corners that fall outside the grid (weight zero)
rather than clamping them, in all three accumulators alike; then run G-self to
see whether any golden plate moves, and take a golden decision if one does.
