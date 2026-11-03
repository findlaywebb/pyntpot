# The gallery caption under the nib-angles figure describes a different figure

GitHub issue: [#162](https://github.com/findlaywebb/pyntpot/issues/162)

Area: docs (gallery).

In `docs/gallery.md`, "The hand and the nib" section, the caption under
`images/explanation/nib-angles.webp` reads: "Painted by `examples/nib_stages.py` (seed 7,
figure angles, size 840). The name is Ambleside. The labels read -38, 0 and 90 across, and
0.5 and 0.85 down."

`examples/nib_stages.py` paints something else. `_angles_grid` writes `NAME`, which is
`"Keswick"`, in a grid of `ANGLES = (-38.0, 0.0, 38.0, 90.0)` across and
`THINS = (0.0, 0.52, 0.85)` down: twelve cells, three rows of four. The labels it letters
are formatted with `:g`, so they read -38, 0, 38 and 90 across, and 0, 0.52 and 0.85 down.

The alt text just above the caption is right ("The word Keswick written twelve times in
three rows of four"), as is the same image's alt text in
`docs/explanation/the-hand-and-the-nib.md`. The wrong caption is a copy of the one under
`images/tutorials/grid-nib.webp` (`examples/tutorial_grids.py`, figure nib), which does
letter Ambleside at three angles and two thinnings.

Possible fix: correct the caption to "The name is Keswick. The labels read -38, 0, 38 and
90 across, and 0, 0.52 and 0.85 down." To stop it drifting again, have the caption name
the script's constants (`ANGLES`, `THINS`) rather than restate their values.
