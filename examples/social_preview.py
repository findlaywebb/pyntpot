"""The social preview: a full-width crop of the Ambleside card with the wordmark lettered on it.

GitHub shows a repository's social preview at 1280 by 640 pixels, and wants it under 1 MB.
This script paints that sheet. It paints the Ambleside card at the sheet's width
(`place_card.py`, in its showcase theme, with the curated callouts), crops the sheet's
height from it, lays a soft, ragged patch of the cream paper over the crop where the map is
quietest, and letters "pyntpot" there with the hand, over a plain line of its own, the nib
plate painted at twice its size and brought down with Lanczos. The map is painted by running
`place_card.py`, so the preview is never a copy that can drift from it.

It takes the keywords a fixture script takes, `track`, `cache_dir`, `features` and
`elevation`, and the `theme` and `place` that `place_card.py` takes, and writes
`social-preview.png` into the directory it is given. The docs image pipeline encodes that as
the JPEG the repository settings take. Every seed is fixed. It paints the Ambleside card
only, and fetches nothing the cache already holds.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate` and `save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`,
`Setting`, `NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`. It introduces none.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/social_preview.py route.gpx cache/ out/ you@example.org --place ambleside --theme examples/themes/ambleside.toml
"""

import argparse
import logging
import runpy
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from pyntpot.ink import BrushStyle, Canvas, PaperStyle, Sheet, paper_plate, save_image
from pyntpot.letters import (
    FaceStyle,
    Hand,
    HandStyle,
    NibGroups,
    NibStyle,
    NibSurface,
    Setting,
    nib_plate,
)
from pyntpot.maps import OpenTopoData, OverpassFeatures

log = logging.getLogger(__name__)

#: The sheet's width and height, in pixels: GitHub's social preview size.
W, H = 1280, 640
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The seed of the paper, the patch, the hand and the dither the file is written with.
SEED = 11
#: How many rows down the painted card the crop starts, as a fraction of the rows it leaves out.
CROP_AT = 0.42
#: The wordmark's type size and the width the hand sets it across, in multiples of the size.
NAME_PX, NAME_WIDTH = 188.0, 2.75
#: Where the wordmark's centre sits on the sheet, as fractions of the width and height.
NAME_AT = (0.47, 0.6)
#: The patch of paper behind the wordmark: its half width and half height in pixels, and how
#: opaque it is at its middle.
PATCH_HALF = (340.0, 120.0)
PATCH_OPACITY = 0.74
#: How many times larger the nib plate is painted than the sheet, before it is downsized.
NIB_SCALE = 2
_HERE = Path(__file__).resolve().parent


def _patch_mask() -> np.ndarray:
    """Return the patch's opacity over the sheet: a ragged ellipse of paper, soft at its edge."""
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    cx, cy = NAME_AT[0] * W, NAME_AT[1] * H
    angle = np.arctan2((yy - cy) / PATCH_HALF[1], (xx - cx) / PATCH_HALF[0])
    wobble = np.zeros_like(angle)
    for k in range(2, 9):
        wobble += rng.normal(0, 0.05 / k**0.6) * np.cos(k * angle + rng.uniform(0, 6.28))
    radius = np.hypot((xx - cx) / PATCH_HALF[0], (yy - cy) / PATCH_HALF[1])
    inside = np.clip((1.0 + wobble - radius) / 0.22, 0, 1)
    soft = Image.fromarray((inside * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
    return np.asarray(soft, np.float32)[..., None] / 255 * PATCH_OPACITY


def _wordmark(out_dir: Path) -> np.ndarray:
    """Letter "pyntpot" with the hand on a transparent sheet and return it as RGBA floats."""
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    span = NAME_WIDTH * NAME_PX
    x = np.linspace(NAME_AT[0] * W - 0.5 * span, NAME_AT[0] * W + 0.5 * span, 40)
    y = NAME_AT[1] * H + 0.3 * NAME_PX - 0.05 * H * (x - x[0]) / span
    line = tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))
    marks = hand.write(Setting("pyntpot", NAME_PX, path=line), hand.generator(SEED))
    big = Canvas(0, 0, NIB_SCALE * W, NIB_SCALE * H, NIB_SCALE * W, NIB_SCALE * H)
    dark = np.zeros((NIB_SCALE * H, NIB_SCALE * W), np.float32)
    surface = NibSurface(big, NIB_SCALE, dark, GRAN_PX * NIB_SCALE)
    groups = NibGroups(
        NibStyle(label_pen_width_px=1.5), face, hand_style, BrushStyle(), PaperStyle()
    )
    plate = nib_plate(marks, surface, groups, out_dir / "wordmark-plate.webp")
    if plate is None:
        raise RuntimeError("the hand wrote no marks")
    with Image.open(plate) as opened:
        small = opened.convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    return np.asarray(small, np.float32) / 255


def _sheet(card: Image.Image, work: Path) -> np.ndarray:
    """Return the sheet: the card's crop, the paper patch and the lettered wordmark, as floats."""
    fitted = card.convert("RGB").resize(
        (W, round(card.height * W / card.width)), Image.Resampling.LANCZOS
    )
    top = round((fitted.height - H) * CROP_AT)
    crop = fitted.crop((0, top, W, top + H))
    sheet = np.asarray(crop, np.float32) / 255
    paper = paper_plate(Sheet(H, W, GRAN_PX, SEED), Canvas(0, 0, W, H, W, H), PaperStyle(), W)
    mask = _patch_mask()
    sheet = sheet * (1 - mask) + paper * mask
    word = _wordmark(work)
    alpha = word[..., 3:]
    return sheet * (1 - alpha) + word[..., :3] * alpha


def main(  # noqa: PLR0913 (the script contract fixes these keywords)
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
    theme: str | None = None,
    place: str | None = None,
) -> Path:
    """Paint the preview: a crop of the Ambleside card with the wordmark on it, and return its path.

    Args:
        out_dir: Where `social-preview.png` is written; created when missing.
        track: The GPX file of the Ambleside route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.
        theme: A TOML theme file for the card, as `place_card.py` takes it.
        place: The place's fixture name, for the card's curated callouts, as `place_card.py` takes it.

    Returns:
        The path of the saved preview, `out_dir / "social-preview.png"`.
    """
    with tempfile.TemporaryDirectory() as tmp:
        card_path = runpy.run_path(str(_HERE / "place_card.py"))["main"](
            Path(tmp) / "card",
            track=track,
            cache_dir=cache_dir,
            features=features,
            elevation=elevation,
            theme=theme,
            place=place,
            size=W,
        )
        with Image.open(card_path) as card:
            sheet = _sheet(card, Path(tmp))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "social-preview.png"
    save_image(sheet, path, seed=SEED)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint the social preview.")
    parser.add_argument("track", type=Path, help="the GPX file of the Ambleside route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where social-preview.png is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as an email"
    )
    parser.add_argument(
        "--theme", help="a TOML theme file, relative to the repository's top directory"
    )
    parser.add_argument("--place", help="the name of the place's fixture")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
        theme=args.theme,
        place=args.place,
    )
