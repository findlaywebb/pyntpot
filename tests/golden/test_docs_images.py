"""Docs image pins: each committed image is what its registered script paints now."""

from pathlib import Path

import numpy as np
import pytest
from golden.make_docs_images import paint_entry
from golden.test_parity import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION
from PIL import Image

from support import REPO_ROOT
from support.docs_images import IMAGES, IMAGES_DIR, DocsImage
from support.golden import differing_fraction

pytestmark = pytest.mark.golden


def _decoded(path: Path) -> np.ndarray:
    """Decode an image file to an array."""
    with Image.open(path) as img:
        return np.asarray(img.convert("RGB"))


@pytest.mark.parametrize("entry", IMAGES, ids=[entry.image for entry in IMAGES])
def test_each_image_matches_a_fresh_paint(
    tmp_path: Path, golden_tolerance: bool, entry: DocsImage
) -> None:
    """The committed image, decoded, equals its script's fresh paint encoded the same way and decoded."""
    fresh = tmp_path / "fresh" / Path(entry.image).name
    fresh.parent.mkdir()
    fresh.write_bytes(paint_entry(entry, tmp_path / "work"))
    committed = REPO_ROOT / IMAGES_DIR / entry.image

    if not golden_tolerance:
        assert np.array_equal(_decoded(committed), _decoded(fresh)), f"{entry.image} differs"
        return
    fraction = differing_fraction(committed, fresh, MAX_CHANNEL_DELTA)
    assert fraction <= MAX_DIFFERING_FRACTION, f"{entry.image}: {fraction:.4%} of pixels differ"
