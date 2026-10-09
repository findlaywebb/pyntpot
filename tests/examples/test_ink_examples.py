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
