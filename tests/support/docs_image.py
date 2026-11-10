"""One docs image's description and where its files live: `DocsImage` and the paths it is kept at.

Key types: `DocsImage`, one committed image and the script run that paints it; `Kind`,
`Encoding` and `Option`, its field types; `IMAGES_DIR` and `MASTERS_DIR`, where the images
and their lossless masters live, relative to the repo root; `MASTER_WIDTH`, the widest a
master is; `master_path`, an image's master path.

It holds no entry and no budget: `tests/support/docs_images.py` holds the registry and the
budgets, and `tests/support/docs_images_009a.py` holds one slice's block of entries. It
paints, encodes and reads nothing.
"""

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Literal

#: Where the committed images live, relative to the repo root.
IMAGES_DIR = "docs/images"

#: Where the lossless reference masters live, relative to the repo root.
MASTERS_DIR = "tests/golden/docs"

#: The widest a reference master is; a narrower entry keeps its own width.
MASTER_WIDTH = 240

Kind = Literal["thumbnail", "page", "hero", "preview"]
Encoding = Literal["webp-lossless", "webp-lossy", "jpeg"]
Option = tuple[str, str | int | float]


@dataclass(frozen=True)
class DocsImage:
    """One committed image: where it lives and which script run paints it.

    Attributes:
        image: The file's path under `docs/images/`.
        stem: The script in `examples/`, without `.py`.
        options: Keyword arguments for the script's `main`, as name and value pairs.
        fixture: The directory under `tests/fixtures/` the script reads, or `None`.
        width: The width the image is downsized to, never enlarged.
        kind: Which size budget the file keeps to.
        encoding: How the file is written.
        slice: The plan slice that registered it, a key of `SLICE_SHARE_BYTES`.
        quality: The lossy encoders' quality, or `None` for the encoding's own default.
    """

    image: str
    stem: str
    options: tuple[Option, ...]
    fixture: str | None
    width: int
    kind: Kind
    encoding: Encoding
    slice: str
    quality: int | None = None


def master_path(image: str) -> str:
    """Return a docs image's reference master path under `MASTERS_DIR`: its path with `.png`."""
    return str(PurePosixPath(image).with_suffix(".png"))
