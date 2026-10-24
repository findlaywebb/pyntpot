"""Docs image pins: each committed image and master is what its registered script paints now.

Exact mode pins the lossy docs file and the lossless master. With `--golden-tolerance`
only the master is compared: lossy re-encoding amplifies sub-LSB float noise past the
parity bound, so the docs file is checked on CI by the architecture test (ADR 0033).
"""

from pathlib import Path

import numpy as np
import pytest
from golden.make_docs_images import paint_entry
from golden.test_parity import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION
from PIL import Image

from support import REPO_ROOT
from support.docs_images import IMAGES, IMAGES_DIR, MASTERS_DIR, DocsImage, master_path
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
    """The committed master equals the fresh master within the bound; exactly, so does the docs image."""
    fresh_docs = tmp_path / "fresh" / Path(entry.image).name
    fresh_master = tmp_path / "fresh" / Path(master_path(entry.image)).name
    fresh_docs.parent.mkdir()
    data, master = paint_entry(entry, tmp_path / "work")
    fresh_docs.write_bytes(data)
    fresh_master.write_bytes(master)
    committed_master = REPO_ROOT / MASTERS_DIR / master_path(entry.image)

    if not golden_tolerance:
        committed = REPO_ROOT / IMAGES_DIR / entry.image
        assert np.array_equal(_decoded(committed), _decoded(fresh_docs)), f"{entry.image} differs"
        assert np.array_equal(_decoded(committed_master), _decoded(fresh_master)), (
            f"{entry.image} master differs"
        )
        return
    fraction = differing_fraction(committed_master, fresh_master, MAX_CHANNEL_DELTA)
    assert fraction <= MAX_DIFFERING_FRACTION, (
        f"{entry.image} master: {fraction:.4%} of pixels differ"
    )
