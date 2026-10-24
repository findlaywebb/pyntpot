"""The curves and symmetry scripts run offline and each writes one image of the size asked for."""

import numpy as np
import pytest
from PIL import Image

from support.examples import run_example

#: The small side, in pixels, every test paints at.
SMALL = 120

#: Each script and the options that choose one of its figures.
CASES: dict[str, tuple[str, dict[str, object]]] = {
    "rose": ("curves", {"figure": "rose"}),
    "lissajous": ("curves", {"figure": "lissajous"}),
    "spirograph": ("curves", {"figure": "spirograph"}),
    "kaleidoscope": ("kaleidoscope", {}),
}


@pytest.mark.parametrize("case", list(CASES), ids=list(CASES))
def test_main_writes_one_image_that_is_not_flat(case, tmp_path):
    """`main` writes exactly one PNG of the given small size and it is not one flat colour."""
    stem, options = CASES[case]
    path = run_example(stem, tmp_path, size=SMALL, **options)
    assert list(tmp_path.iterdir()) == [path]
    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.size == (SMALL, SMALL)
        pixels = np.asarray(image.convert("RGB"))
    low, high = pixels.min(axis=(0, 1)), pixels.max(axis=(0, 1))
    assert (low != high).any(), (low, high)


def test_an_unknown_figure_is_refused(tmp_path):
    """`curves` raises `ValueError` for a figure it does not draw."""
    with pytest.raises(ValueError, match="figure"):
        run_example("curves", tmp_path, size=SMALL, figure="cardioid")
