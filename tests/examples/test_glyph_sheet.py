"""The glyph sheet writes each glyph on its own, so a change to one glyph moves only its cell."""

import runpy

import numpy as np
import pytest

from pyntpot.letters import NibStyle

from support.examples import EXAMPLES_DIR

#: The seed of the capital A's cell, from `SeedSequence((11, 65))`.
PINNED_A_SEED = 2338548601


@pytest.fixture(scope="module")
def glyph_sheet():
    """The glyph sheet script's namespace, loaded once without its main block."""
    return runpy.run_path(str(EXAMPLES_DIR / "glyph_sheet.py"), run_name="example_glyph_sheet")


@pytest.fixture(scope="module")
def painted(glyph_sheet):
    """The sheet painted with the default nib for every glyph, an immutable array."""
    sheet = glyph_sheet["paint"]()
    sheet.flags.writeable = False
    return sheet


def _moved_outside(before: np.ndarray, after: np.ndarray, boxes) -> tuple[bool, list[bool]]:
    """Return whether any pixel moved outside `boxes`, and whether each box moved."""
    moved = (before != after).any(axis=-1)
    inside = np.zeros_like(moved)
    for x0, y0, x1, y1 in boxes:
        inside[y0:y1, x0:x1] = True
    return bool((moved & ~inside).any()), [
        bool(moved[y0:y1, x0:x1].any()) for x0, y0, x1, y1 in boxes
    ]


def test_the_sheet_is_deterministic(glyph_sheet, painted):
    """Two paints of the sheet are the same array, pixel for pixel."""
    np.testing.assert_array_equal(glyph_sheet["paint"](), painted)


@pytest.mark.parametrize(
    ("ch", "line"),
    [("Q", 0), ("&", 2)],
    ids=["capital-Q", "ampersand"],
)
def test_a_glyph_written_with_another_nib_moves_only_its_cell_and_its_line(
    glyph_sheet, painted, ch, line
):
    """A wider nib for one glyph moves its cell and the running line holding it, and nothing else."""
    after = glyph_sheet["paint"]({ch: NibStyle(label_pen_width_px=2.4)})
    boxes = [glyph_sheet["cell_box"](ch), glyph_sheet["line_box"](line)]
    outside, each = _moved_outside(painted, after, boxes)
    assert not outside
    assert each == [True, True]


def test_every_cell_and_line_has_a_seed_of_its_own(glyph_sheet):
    """No two cells or running lines share a seed, so no two renders draw the same stream."""
    cells = [glyph_sheet["glyph_seed"](ch) for ch in "".join(glyph_sheet["ROWS"])]
    lines = [glyph_sheet["line_seed"](i) for i in range(len(glyph_sheet["LINES"]))]
    assert len(set(cells + lines)) == len(cells) + len(lines)


def test_a_glyph_seed_is_pinned_to_its_character(glyph_sheet):
    """A glyph's seed comes from its code point and the base seed alone, pinned here."""
    assert glyph_sheet["glyph_seed"]("A") == PINNED_A_SEED
