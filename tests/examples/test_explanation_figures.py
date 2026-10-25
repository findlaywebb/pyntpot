"""The explanation essays' figure scripts each write one image per figure, and each stage differs from the one before.

The grids are figures of their own: they are not compared with the stage before.
"""

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
        "angles",
        "ground",
        "backing",
        "set-down",
        "runs-dry",
        "hands",
    ),
}

#: The figures that are grids, not stages: each is its own picture, so none is compared with the one before.
GRIDS: frozenset[tuple[str, str]] = frozenset(
    {("wash_stages", "glaze"), ("nib_stages", "angles"), ("nib_stages", "hands")}
)

#: The width the tests paint at, in pixels, so each paint stays fast.
SMALL = 144


def _stage_before(stem: str, figure: str) -> str | None:
    """Return the nearest stage before `figure` in its script, or `None` for a grid or a first stage."""
    if (stem, figure) in GRIDS:
        return None
    stages = [f for f in FIGURES[stem] if (stem, f) not in GRIDS]
    index = stages.index(figure)
    return stages[index - 1] if index else None


_CASES = [
    (stem, figure, _stage_before(stem, figure)) for stem in FIGURES for figure in FIGURES[stem]
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
    """Each figure is the only file its call writes, it has some range of tone, and a stage is not the previous stage's picture."""
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
