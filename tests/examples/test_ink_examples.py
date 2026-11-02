"""The ink rungs' scripts run offline and each writes its image."""

import numpy as np
import pytest
from PIL import Image

from support.examples import run_example

#: Each ink rung's finished image, width by height in pixels.
SIZES: dict[str, tuple[int, int]] = {
    "paper": (360, 240),
    "wash": (360, 240),
    "brush_stroke": (360, 240),
    "nib_line": (360, 240),
    "pigments": (720, 240),
}


@pytest.mark.parametrize("stem", list(SIZES), ids=list(SIZES))
def test_the_script_writes_an_image(stem, tmp_path):
    """The script writes one PNG of the rung's size that is not one flat colour."""
    path = run_example(stem, tmp_path)
    assert path.is_file()
    assert list(tmp_path.iterdir()) == [path]
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == SIZES[stem]
        pixels = np.asarray(image)
    low, high = pixels.min(axis=(0, 1)), pixels.max(axis=(0, 1))
    assert (low != high).all(), (low, high)


#: The tutorial grids, one per rung, each painted 720 pixels wide.
GRIDS: tuple[str, ...] = (
    "paper",
    "wash",
    "brush",
    "pigments",
    "nib",
    "lettering",
    "composition",
)


@pytest.mark.parametrize("figure", GRIDS, ids=GRIDS)
def test_a_tutorial_grid_is_one_image_at_its_published_width(figure, tmp_path):
    """Each tutorial grid writes one PNG, 720 pixels wide, that is not one flat colour."""
    path = run_example("tutorial_grids", tmp_path, figure=figure)
    assert list(tmp_path.iterdir()) == [path]
    with Image.open(path) as image:
        assert image.mode == "RGB"
        assert image.width == 720
        pixels = np.asarray(image)
    assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()


def test_an_unknown_tutorial_grid_is_refused(tmp_path):
    """A grid name the tutorial does not have is a ValueError, not a blank image."""
    with pytest.raises(ValueError, match="no such figure"):
        run_example("tutorial_grids", tmp_path, figure="nonesuch")


@pytest.mark.parametrize(
    ("stem", "options", "width"),
    [
        ("pigment_swatches", {}, 960),
        ("brush_sheet", {"figure": "grid"}, 960),
        ("brush_sheet", {"figure": "sheet"}, 800),
    ],
    ids=["pigment-card", "brush-grid", "brush-sheet"],
)
def test_a_reference_sheet_is_one_image_of_its_width(stem, options, width, tmp_path):
    """Each reference sheet writes one PNG of its width that is not one flat colour."""
    path = run_example(stem, tmp_path, **options)
    assert list(tmp_path.iterdir()) == [path]
    with Image.open(path) as image:
        assert image.width == width
        pixels = np.asarray(image.convert("RGB"))
    assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()
