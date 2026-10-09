"""Writing plates: the dither that hides banding and the WebP encoders.

Key functions: `to_img`, an RGB image with a little dither; `save_webp`, one RGB plate;
`save_image`, a painted RGB array written to any image file Pillow knows, WebP lossless;
`save_alpha`, a white plate carrying alpha for one the page tints itself; `save_rgba`, a
plate carrying its own colour and alpha. Each `save_` function writes the file, creating its
directory, and returns its size in bytes.

It does not decide what is painted or, except in `save_image`, which always writes WebP
lossless, whether to write lossless: the caller passes the setting it read from its style.

Invariants: lossless writes the exact pixels that were composed; a plate's alpha is stored
as 8 bits, rounded to nearest.
"""

from pathlib import Path

import numpy as np
from PIL import Image


def to_img(arr: np.ndarray, rng: np.random.Generator) -> Image.Image:
    """An RGB image with a little dither, so a flat wash has no banding."""
    d = (rng.random(arr.shape, dtype=np.float32) - rng.random(arr.shape, dtype=np.float32)) * 0.5
    return Image.fromarray(np.clip(arr * 255.0 + 0.5 + d, 0, 255).astype(np.uint8), "RGB")


def save_webp(img: Image.Image, path: Path, quality: int = 74, *, lossless: bool = False) -> int:
    """Write one WebP plate and return its size in bytes.

    Args:
        img: The plate.
        path: Where to write it.
        quality: The lossy encoder's quality, used only when `lossless` is off.
        lossless: Write the exact pixels the painter composed. This is what the
            ink wants: the lossy encoder works in 4 by 4 blocks on a half
            resolution chroma plane, which is wider than most of the marks on
            the plate, so it replaces a stroke's ramp with two flats and a step
            and takes the paper's grain with it.

    Returns:
        The file's size in bytes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if lossless:
        img.save(path, format="WEBP", lossless=True, method=5)
    else:
        img.save(path, format="WEBP", quality=quality, method=5)
    return path.stat().st_size


def save_image(image: np.ndarray, path: Path, *, seed: int = 0) -> int:
    """Write a painted RGB array to an image file and return its size in bytes.

    It dithers as `to_img` does, with a generator seeded from `seed`, so one
    array and seed write one file. The format follows the suffix: `.webp` is
    written lossless, every other suffix by Pillow's encoder for it, `.png`
    the usual.

    Args:
        image: The painted array, `(h, w, 3)` floats in 0 to 1, as `composite`
            and `paper_plate` return.
        path: Where to write it; its directory is created.
        seed: Seeds the dither's generator.

    Returns:
        The file's size in bytes.

    Raises:
        ValueError: When Pillow knows no format for the suffix.

    It writes no alpha (that is `save_rgba`) and does not decide what is
    painted.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    img = to_img(image, np.random.default_rng(seed))
    if path.suffix.lower() == ".webp":
        return save_webp(img, path, lossless=True)
    img.save(path)
    return path.stat().st_size


def save_alpha(alpha: np.ndarray, path: Path, quality: int = 82, *, lossless: bool = False) -> int:
    """Write a white plate carrying alpha, for one the page tints itself.

    White rather than black, because an SVG mask reads luminance times alpha by
    default: a black plate would mask everything out whichever way it is read.

    WebP already stores the alpha channel losslessly, so this plate was never
    the one the encoder was hurting; `lossless` covers the flat white beside it
    and costs nothing, the file coming out slightly smaller than the lossy one.

    Args:
        alpha: The plate's alpha, in 0 to 1.
        path: Where to write it.
        quality: The lossy encoder's quality for the colour channels, used only
            when `lossless` is off.
        lossless: Write the exact pixels.

    Returns:
        The file's size in bytes.
    """
    h, w = alpha.shape
    rgba = np.full((h, w, 4), 255, np.uint8)
    rgba[..., 3] = np.clip(alpha * 255 + 0.5, 0, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(rgba, "RGBA")
    if lossless:
        img.save(path, format="WEBP", lossless=True, method=4)
    else:
        img.save(path, format="WEBP", quality=quality, method=4)
    return path.stat().st_size


def save_rgba(
    rgb: np.ndarray, alpha: np.ndarray, path: Path, quality: int = 88, *, lossless: bool = True
) -> int:
    """Write a plate carrying its own colour and its own alpha.

    The label plate is composited normally rather than multiplied, so it needs
    both: multiply can only darken, and a backing wash in the paper's own colour
    has to be able to lighten.

    Lossless by default, and for the same reason the base plates are: the lossy
    encoder transforms in 4 by 4 blocks on a half resolution chroma plane, and
    a thinned glyph stroke is between one and three pixels wide. It is the
    worst case the encoder has, not a marginal one, and a name is the thing on
    the card a reader looks at closest.

    Args:
        rgb: The colour, `(h, w, 3)` in 0 to 1.
        alpha: The coverage, `(h, w)` in 0 to 1.
        path: Where to write.
        quality: The lossy encoder's quality, used only when `lossless` is off.
        lossless: Write the exact pixels that were composed.

    Returns:
        The file's size in bytes.
    """
    h, w = alpha.shape
    out = np.empty((h, w, 4), np.uint8)
    out[..., :3] = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(alpha * 255.0 + 0.5, 0, 255).astype(np.uint8)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(out, "RGBA")
    if lossless:
        img.save(path, format="WEBP", lossless=True, method=4)
    else:
        img.save(path, format="WEBP", quality=quality, method=4)
    return path.stat().st_size
