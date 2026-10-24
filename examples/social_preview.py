"""The social preview: the Keswick card beside the wordmark, on one sheet of paper.

GitHub shows a repository's social preview at 1280 by 640 pixels, and wants it under 1 MB.
This script paints that sheet: it lays the cream paper, then the Keswick card on the left
(`place_card.py`, painted at 720 pixels and fitted to the sheet's height) and the wordmark
on the right (`word.py`, fitted to the right half), each with its edge feathered into the
paper so that neither shows as a box. Both are painted by running those two scripts, so
the preview is never a copy that can drift from them.

It takes the keywords a fixture script takes, `track`, `cache_dir`, `features` and
`elevation`, and writes `social-preview.png` into the directory it is given. The docs
image pipeline encodes that as the JPEG the repository settings take. Every seed is fixed.
It paints the Keswick card only, and fetches nothing the cache already holds.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/social_preview.py route.gpx cache/ out/ you@example.org
"""

import argparse
import logging
import runpy
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import Canvas, PaperStyle, Sheet, paper_plate, save_image
from pyntpot.maps import OpenTopoData, OverpassFeatures

log = logging.getLogger(__name__)

#: The sheet's width and height, in pixels: GitHub's social preview size.
W, H = 1280, 640
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The seed of the paper and of the dither the file is written with.
SEED = 11
#: The card's display width when it is painted, in pixels.
CARD_PX = 720
#: The margin round the card, in pixels.
MARGIN = 22
#: The wordmark's width on the sheet, in pixels.
WORD_W = 560
#: How far each picture's edge fades into the paper, in pixels.
FEATHER = 36
_HERE = Path(__file__).resolve().parent


def _feathered(img: Image.Image, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    """Return `img` fitted to `width` by `height`, as floats, with a mask fading its edges."""
    fitted = np.asarray(img.convert("RGB").resize((width, height), Image.Resampling.LANCZOS))
    ramp_x = np.clip(np.minimum(np.arange(width), np.arange(width)[::-1]) / FEATHER, 0, 1)
    ramp_y = np.clip(np.minimum(np.arange(height), np.arange(height)[::-1]) / FEATHER, 0, 1)
    mask = np.minimum(ramp_y[:, None], ramp_x[None, :])[..., None]
    return fitted.astype(np.float32) / 255, mask.astype(np.float32)


def _lay(sheet: np.ndarray, img: Image.Image, left: int, top: int, size: tuple[int, int]) -> None:
    """Lay `img`, fitted to `size`, over `sheet` at `left` and `top`, its edges feathered."""
    width, height = size
    pixels, mask = _feathered(img, width, height)
    region = sheet[top : top + height, left : left + width]
    sheet[top : top + height, left : left + width] = region * (1 - mask) + pixels * mask


def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> Path:
    """Paint the preview: the Keswick card and the wordmark on paper, and return its path.

    Args:
        out_dir: Where `social-preview.png` is written; created when missing.
        track: The GPX file of the Keswick route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The path of the saved preview, `out_dir / "social-preview.png"`.
    """
    sheet = paper_plate(Sheet(H, W, GRAN_PX, SEED), Canvas(0, 0, W, H, W, H), PaperStyle(), W)
    with tempfile.TemporaryDirectory() as tmp:
        card_path = runpy.run_path(str(_HERE / "place_card.py"))["main"](
            Path(tmp) / "card",
            track=track,
            cache_dir=cache_dir,
            features=features,
            elevation=elevation,
            size=CARD_PX,
        )
        word_path = runpy.run_path(str(_HERE / "word.py"))["main"](Path(tmp) / "word")
        with Image.open(card_path) as card, Image.open(word_path) as word:
            card_h = H - 2 * MARGIN
            card_w = round(card.width * card_h / card.height)
            _lay(sheet, card, MARGIN, MARGIN, (card_w, card_h))
            word_h = round(word.height * WORD_W / word.width)
            left = card_w + MARGIN + (W - card_w - MARGIN - WORD_W) // 2
            _lay(sheet, word, left, (H - word_h) // 2, (WORD_W, word_h))
    path = out_dir / "social-preview.png"
    save_image(sheet, path, seed=SEED)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint the social preview.")
    parser.add_argument("track", type=Path, help="the GPX file of the Keswick route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where social-preview.png is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as an email"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
    )
