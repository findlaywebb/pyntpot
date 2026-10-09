"""The lettering and composition scripts run offline and each writes its image."""

import numpy as np
import pytest
from PIL import Image

from support.examples import run_example

#: Each script's finished image size, width by height in pixels.
SIZES: dict[str, tuple[int, int]] = {
    "lettering": (360, 240),
    "composition": (480, 320),
}


@pytest.mark.parametrize("stem", list(SIZES), ids=list(SIZES))
def test_the_script_writes_an_image(stem, tmp_path):
    """The script writes one PNG of the rung's size that is not one flat colour."""
    path = run_example(stem, tmp_path)
    assert path.is_file()
    assert path.parent == tmp_path
    assert path.suffix == ".png"
    with Image.open(path) as image:
        assert image.mode == "RGB"
        assert image.size == SIZES[stem]
        pixels = np.asarray(image)
    assert (pixels.min(axis=(0, 1)) != pixels.max(axis=(0, 1))).all()


def test_the_lettering_plate_carries_alpha_only_near_the_name(tmp_path):
    """The lettering script's RGBA plate is transparent at its corners and opaque somewhere."""
    path = run_example("lettering", tmp_path)
    with Image.open(path.with_name("lettering-plate.webp")) as plate:
        alpha = np.asarray(plate.convert("RGBA"))[..., 3]
    corners = (alpha[0, 0], alpha[0, -1], alpha[-1, 0], alpha[-1, -1])
    assert all(value == 0 for value in corners)
    assert alpha.max() == 255
