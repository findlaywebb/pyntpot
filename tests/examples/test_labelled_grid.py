"""The labelled-grid helper lays out and letters the five grid scripts exactly as each did inline.

The box literals below were recorded from the scripts' own layout code (`tutorial_grids._layout`,
`nib_stages._cells` and the layouts inline in `brush_sheet`, `wash_stages` and `how_to_route_ink`)
before the helper replaced them, so a drift in the rounding fails here, not in a golden image.
"""

import numpy as np
import pytest

from pyntpot.ink import Colour
from pyntpot.letters import NibStyle, Setting

from support.examples import load_example


@pytest.fixture(scope="module")
def helper():
    """The helper script's namespace, loaded once."""
    return load_example("labelled_grid", "example_labelled_grid")


def _regular(
    left: int, top: int, cell_w: int, cell_h: int, gap: int, cols: int, rows: int
) -> list[list[tuple[int, int, int, int]]]:
    """Return the boxes of a regular grid, the way every old layout spaced its cells."""
    return [
        [(left + c * (cell_w + gap), top + r * (cell_h + gap), cell_w, cell_h) for c in range(cols)]
        for r in range(rows)
    ]


#: (id, GridSpec keywords, the boxes and height the old layout code gave).
LAYOUTS = [
    pytest.param(
        {"width": 720, "cols": 3, "rows": 2, "cell_h": 150, "left": 92, "top": 46},
        _regular(92, 46, 195, 150, 14, 3, 2),
        374,
        id="tutorial-paper",
    ),
    pytest.param(
        {"width": 720, "cols": 3, "rows": 3, "cell_h": 96, "left": 14, "top": 14},
        _regular(14, 14, 221, 96, 14, 3, 3),
        344,
        id="tutorial-lettering",
    ),
    pytest.param(
        {
            "width": 900,
            "cols": 4,
            "rows": 3,
            "cell_h": 108,
            "left": 110,
            "top": 54,
            "gap": 12,
            "pad_right": 12,
            "pad_bottom": 12,
            "unit": 1.0,
        },
        _regular(110, 54, 185, 108, 12, 4, 3),
        414,
        id="nib-angles-design-size",
    ),
    pytest.param(
        {
            "width": 360,
            "cols": 4,
            "rows": 3,
            "cell_h": 108,
            "left": 110,
            "top": 54,
            "gap": 12,
            "pad_right": 12,
            "pad_bottom": 12,
            "unit": 0.4,
        },
        [
            [(44, 22, 74, 43), (123, 22, 74, 43), (202, 22, 74, 43), (281, 22, 74, 43)],
            [(44, 70, 74, 43), (123, 70, 74, 43), (202, 70, 74, 43), (281, 70, 74, 43)],
            [(44, 118, 74, 43), (123, 118, 74, 43), (202, 118, 74, 43), (281, 118, 74, 43)],
        ],
        166,
        id="nib-angles-scaled",
    ),
    pytest.param(
        {
            "width": 360,
            "cols": 3,
            "rows": 3,
            "cell_h": 104,
            "left": 12,
            "top": 12,
            "gap": 12,
            "pad_right": 12,
            "pad_bottom": 12,
            "unit": 0.4,
        },
        [
            [(5, 5, 113, 42), (123, 5, 113, 42), (241, 5, 113, 42)],
            [(5, 52, 113, 42), (123, 52, 113, 42), (241, 52, 113, 42)],
            [(5, 99, 113, 42), (123, 99, 113, 42), (241, 99, 113, 42)],
        ],
        146,
        id="nib-hands-scaled",
    ),
    pytest.param(
        {
            "width": 960,
            "cols": 8,
            "rows": 3,
            "cell_h": 84,
            "left": 74,
            "top": 44,
            "gap": 8,
            "pad_right": 16,
            "pad_bottom": 42,
        },
        _regular(74, 44, 101, 84, 8, 8, 3),
        354,
        id="brush-grid",
    ),
    pytest.param(
        {
            "width": 360,
            "cols": 4,
            "rows": 2,
            "cell_h": 136.0,
            "left": 110,
            "top": 52,
            "gap": 12,
            "pad_right": 12,
            "pad_bottom": 14,
            "unit": 0.45,
        },
        [
            [(50, 23, 72, 61), (127, 23, 72, 61), (204, 23, 72, 61), (281, 23, 72, 61)],
            [(50, 89, 72, 61), (127, 89, 72, 61), (204, 89, 72, 61), (281, 89, 72, 61)],
        ],
        156,
        id="wash-glaze-360",
    ),
    pytest.param(
        {
            "width": 500,
            "cols": 4,
            "rows": 2,
            "cell_h": 136.0,
            "left": 110,
            "top": 52,
            "gap": 12,
            "pad_right": 12,
            "pad_bottom": 14,
            "unit": 0.625,
        },
        [
            [(69, 32, 99, 85), (176, 32, 99, 85), (283, 32, 99, 85), (390, 32, 99, 85)],
            [(69, 125, 99, 85), (176, 125, 99, 85), (283, 125, 99, 85), (390, 125, 99, 85)],
        ],
        219,
        id="wash-glaze-500",
    ),
    pytest.param(
        {
            "width": 720,
            "cols": 3,
            "rows": 2,
            "cell_h": 100,
            "left": 104,
            "top": 44,
            "gap": 10,
            "pad_right": 12,
            "pad_bottom": 12,
        },
        _regular(104, 44, 194, 100, 10, 3, 2),
        266,
        id="route-ink",
    ),
]


class TestGridSpec:
    """`GridSpec.boxes()` and `.height` reproduce each script's old layout, rounding included."""

    @pytest.mark.parametrize(("keywords", "boxes", "height"), LAYOUTS)
    def test_boxes_and_height_equal_the_old_layout(self, helper, keywords, boxes, height):
        """The boxes are the literals the old layout code gave, row by row, and so is the height."""
        spec = helper["GridSpec"](**keywords)
        assert spec.boxes() == boxes
        assert spec.height == height

    def test_cell_w_is_the_width_of_the_first_box(self, helper):
        """`cell_w` is the width every box has."""
        spec = helper["GridSpec"](width=720, cols=3, rows=2, cell_h=150, left=92, top=46)
        assert spec.cell_w == 195

    def test_a_trailing_gap_adds_one_gap_to_the_right_and_the_bottom(self, helper):
        """With `trailing_gap` the last column and row are each followed by a gap, as in nib_stages."""
        spec = helper["GridSpec"](
            width=900,
            cols=4,
            rows=3,
            cell_h=108,
            left=110,
            top=54,
            gap=12,
            pad_right=0,
            pad_bottom=0,
            trailing_gap=True,
        )
        assert spec.boxes() == _regular(110, 54, 185, 108, 12, 4, 3)
        assert spec.height == 414


class TestLetterOver:
    """`letter_over` is the one nib-plate round trip."""

    def test_no_marks_raises(self, helper):
        """Lettering no settings raises the RuntimeError every old `_letter` raised."""
        img = np.ones((40, 60, 3), np.float32)
        with pytest.raises(RuntimeError, match="no marks"):
            helper["letter_over"](
                img, [], NibStyle(label_ink=Colour("#241c14")), gran_px=12.0, seed=7
            )

    def test_a_name_darkens_pixels_and_leaves_the_input_alone(self, helper):
        """A lettered name changes some pixels of a copy, never the array passed in."""
        img = np.ones((60, 160, 3), np.float32)
        setting = Setting("Ambleside", 24.0, anchor=(80, 40), align="middle", wash=False)
        out = helper["letter_over"](
            img, [setting], NibStyle(label_ink=Colour("#241c14")), gran_px=12.0, seed=7
        )
        assert out.shape == img.shape
        assert (img == 1).all()
        assert (out < 1).any()


class TestLabelGrid:
    """`label_grid` letters the column names above the boxes and the row names beside them."""

    def test_labels_land_above_and_left_of_the_grid(self, helper):
        """Ink falls in the band above the first row and the band left of the first column, not inside the cells."""
        spec = helper["GridSpec"](width=400, cols=2, rows=2, cell_h=60, left=90, top=40)
        style = helper["LabelStyle"](
            px=20.0, ink=Colour("#4a3a2a"), pen_px=1.5, gran_px=12.0, seed=7
        )
        img = np.ones((spec.height, 400, 3), np.float32)
        out = helper["label_grid"](img, spec.boxes(), ["a", "b"], ["x", "y"], style)
        changed = (out != img).any(axis=-1)
        assert changed[:40, 90:].any()
        assert changed[40:, :90].any()
        for row in spec.boxes():
            for x, y, w, h in row:
                assert not changed[y : y + h, x : x + w].any()

    def test_extra_settings_are_lettered_too(self, helper):
        """A setting in `extra` is lettered with the labels."""
        spec = helper["GridSpec"](width=400, cols=2, rows=1, cell_h=60, left=90, top=40)
        style = helper["LabelStyle"](
            px=20.0, ink=Colour("#4a3a2a"), pen_px=1.5, gran_px=12.0, seed=7
        )
        img = np.ones((spec.height + 40, 400, 3), np.float32)
        foot = Setting("end", 20.0, anchor=(200, spec.height + 25), align="middle", wash=False)
        out = helper["label_grid"](img, spec.boxes(), ["a", "b"], ["x"], style, extra=[foot])
        assert (out[spec.height :] != 1).any()
