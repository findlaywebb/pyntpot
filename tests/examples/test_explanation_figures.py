"""The explanation essays' figure scripts each write one image per figure, and each stage differs from the one before."""

import numpy as np
import pytest
from PIL import Image

from support.examples import run_example

#: Each script's figures, in the order the essay builds them.
FIGURES: dict[str, tuple[str, ...]] = {
    "wash_stages": ("mask", "body", "rim", "grain", "overlap", "glaze"),
    "nib_stages": (
        "line",
        "centreline",
        "broad",
        "turned",
        "ground",
        "backing",
        "set-down",
        "runs-dry",
    ),
}

#: The width the tests paint at, in pixels, so each paint stays fast.
SMALL = 144

_CASES = [
    (stem, figure, FIGURES[stem][i - 1] if i else None)
    for stem in FIGURES
    for i, figure in enumerate(FIGURES[stem])
]
_IDS = [f"{stem}-{figure}" for stem, figure, _before in _CASES]


def _pixels(stem: str, figure: str, out_dir) -> np.ndarray:
    """Paint one figure at the small size and return its pixels."""
    path = run_example(stem, out_dir, figure=figure, size=SMALL)
    with Image.open(path) as image:
        assert image.mode == "RGB"
        return np.asarray(image, np.int16)


@pytest.mark.parametrize(("stem", "figure", "before"), _CASES, ids=_IDS)
def test_the_figure_is_one_image_that_differs_from_the_stage_before(stem, figure, before, tmp_path):
    """Each figure is the only file its call writes, it has some range of tone, and it is not the previous stage's picture."""
    here = tmp_path / "here"
    pixels = _pixels(stem, figure, here)
    assert len(list(here.iterdir())) == 1
    assert pixels.shape[1] == SMALL
    assert pixels.max() - pixels.min() > 8
    if before is not None:
        earlier = _pixels(stem, before, tmp_path / "before")
        assert earlier.shape == pixels.shape
        assert np.abs(earlier - pixels).max() > 4


@pytest.mark.parametrize("stem", list(FIGURES), ids=list(FIGURES))
def test_an_unknown_figure_is_refused(stem, tmp_path):
    """A figure name the essay does not build is a ValueError, not a blank image."""
    with pytest.raises(ValueError, match="no such figure"):
        run_example(stem, tmp_path, figure="nonesuch", size=SMALL)
