"""Each example theme paints the Keswick card, and each card has the pinned size and mean colour."""

import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from pyntpot.maps import OpenTopoData, OverpassFeatures

from support import REPO_ROOT
from support.examples import run_example

pytestmark = pytest.mark.golden

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-tests@example.invalid"

#: The card's size in pixels, width then height, which no theme changes.
CARD_SIZE = (1800, 1607)

#: Each theme's mean red, green and blue over the whole card, pinned from a paint.
MEAN_RGB: dict[str, tuple[float, float, float]] = {
    "pen-and-ink": (223.9, 219.6, 209.1),
    "sepia": (176.5, 154.1, 112.8),
    "bold": (215.4, 216.6, 195.8),
    "winter": (205.5, 211.6, 217.0),
}

#: How far a channel's mean may move between operating systems, out of 255.
MEAN_TOLERANCE = 1.5


@pytest.mark.parametrize("theme", list(MEAN_RGB), ids=list(MEAN_RGB))
def test_the_theme_paints_the_keswick_card(tmp_path: Path, theme: str) -> None:
    """From the fixture's cache alone, the theme paints a card of the pinned size and mean colour."""
    cache = tmp_path / "cache"
    shutil.copytree(REPO_ROOT / "tests" / "fixtures" / "keswick", cache)

    written = run_example(
        "map_styles",
        tmp_path / "out",
        figure=theme,
        track=cache / "track.gpx",
        cache_dir=cache,
        features=OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0),
        elevation=OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0),
    )

    with Image.open(written) as card:
        assert card.mode == "RGB"
        assert card.size == CARD_SIZE
        mean = np.asarray(card).reshape(-1, 3).mean(axis=0)
    assert mean == pytest.approx(MEAN_RGB[theme], abs=MEAN_TOLERANCE)
