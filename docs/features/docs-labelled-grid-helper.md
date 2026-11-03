# The docs scripts could share one labelled-grid helper

GitHub issue: [#170](https://github.com/findlaywebb/pyntpot/issues/170)

**What exists today.** Five scripts in `examples/` paint a labelled grid, the same picture
at a few values with the values lettered over the columns and beside the rows, and each
writes its own layout and its own labels:

- `tutorial_grids.py`: `_layout` and `_labels`, for the seven tutorial grids;
- `nib_stages.py`: `_cells` and `_letter`, for the `angles` and `hands` grids;
- `brush_sheet.py`: `_grid` and `_letter`;
- `wash_stages.py`: `_glaze_grid` and `_letter`;
- `how_to_route_ink.py`: `_grid` and `_lettered`.

The lettering half is the same nib-plate round trip each time (a `Hand`, a `NibSurface` at
`NIB_SCALE`, `nib_plate` into a temporary file, a Lanczos downsize, an alpha blend), copied
almost line for line; `pigment_swatches.py` and `how_to_own_shapes.py` carry two more
copies. The label offsets (`-12`, `-14`, `+7` display pixels) are bare numbers in each.

**What the feature would add.** One helper that takes a painter (a function from a cell's
size and its values to an image), the values across and down, and the label ink, and
returns the lettered grid. Each script then says only what it varies. The grids of
`docs-variable-effect-grids.md` (#67), the brush id gallery (#69) and the pigment gallery
(#70) are all this helper with a different painter, so it should land before them.

**Possible shape.** Where the helper lives is the first decision. The scripts are loaded by
`runpy.run_path` (`tests/support/examples.py`), which does not put `examples/` on the
import path, so a sibling module needs that runner and `make_docs_images.py` to add it. The
lettering half could instead be the public call of `letters-lettering-over-an-image.md`,
leaving only the layout in `examples/`. Moving
the five grids onto it must keep their docs image pins exact; a pin that moves is a bug in
the helper, not a new picture.

**Related.** `docs-variable-effect-grids.md` (#67), `docs-brush-id-gallery.md` (#69),
`docs-pigment-gallery.md` (#70), `letters-lettering-over-an-image.md`,
`docs-examples-review.md` (#63).
