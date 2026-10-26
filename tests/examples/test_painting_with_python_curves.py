"""The curves and symmetry scripts run offline and each writes one image of the size asked for."""

import runpy

import numpy as np
import pytest
from PIL import Image

from support.examples import EXAMPLES_DIR, run_example

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


def test_each_rose_petal_starts_and_ends_at_the_centre():
    """The rose is cut into five petals, and each is one loop from the centre round and back to it."""
    ns = runpy.run_path(str(EXAMPLES_DIR / "curves.py"), run_name="example_curves")
    size = 600
    points = ns["_points"]("rose", size)
    centre = np.array([size / 2, size / 2])
    for index in range(5):
        petal = ns["_petal"](points, index)
        assert np.hypot(*(petal[0] - centre)) < 0.01 * size
        assert np.hypot(*(petal[-1] - centre)) < 0.01 * size
        assert np.hypot(*(petal - centre).T).max() > 0.3 * size
