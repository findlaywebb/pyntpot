"""Docs image pins: each committed image and master is what its registered script paints now.

Exact mode pins the lossy docs file and the lossless master. With `--golden-tolerance`
only the master is compared: lossy re-encoding amplifies sub-LSB float noise past the
parity bound, so the docs file is checked on CI by the architecture test (ADR 0033).
"""

from pathlib import Path

import numpy as np
import pytest
from golden.make_docs_images import paint_entry
from PIL import Image

from support import REPO_ROOT
from support.docs_images import IMAGES, IMAGES_DIR, MASTERS_DIR, DocsImage, master_path
from support.golden import MAX_CHANNEL_DELTA, MAX_DIFFERING_FRACTION, differing_fraction

pytestmark = pytest.mark.golden


def _decoded(path: Path) -> np.ndarray:
    """Decode an image file to an array."""
    with Image.open(path) as img:
        return np.asarray(img.convert("RGB"))


def _fresh(tmp_path: Path, relative: Path | str, content: bytes) -> Path:
    """Write a fresh paint into the `fresh` tree at its repository path, and return it."""
    path = tmp_path / "fresh" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


@pytest.mark.parametrize("entry", IMAGES, ids=[entry.image for entry in IMAGES])
def test_each_image_matches_a_fresh_paint(
    tmp_path: Path, golden_tolerance: bool, entry: DocsImage
) -> None:
    """The committed master equals the fresh master within the bound; exactly, so does the docs image."""
    # The `fresh` tree holds, at the repository paths, only what this mode gates, so CI's
    # failure step (`diff_images.py`) diffs failures and never an ungated lossy docs file.
    data, master = paint_entry(entry, tmp_path / "work")
    fresh_master = _fresh(tmp_path, Path(MASTERS_DIR) / master_path(entry.image), master)
    committed_master = REPO_ROOT / MASTERS_DIR / master_path(entry.image)

    if not golden_tolerance:
        fresh_docs = _fresh(tmp_path, Path(IMAGES_DIR) / entry.image, data)
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
