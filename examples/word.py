"""The wordmark: "pyntpot" lettered by the hand on a washed disc, painted with the engine.

The paint pot in the name is a pot of water-blue wash. Two discs are washed on the paper,
a blue one and a smaller green one that overlaps its right edge, and the two pigments
glaze where they meet. The hand then sets "pyntpot" along a gentle rise across the blue
disc, the nib strokes its marks onto one RGBA plate, and the plate is laid over the washed
paper by its alpha. It uses only what the earlier rungs introduced: from `pyntpot.ink`,
`Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`, `paper_plate`, `wash`, `PIGMENTS`,
`TRANSPARENCY`, `PigmentLayer`, `rgb`, `composite` and `save_image`; from `pyntpot.letters`,
`FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`, `NibSurface`, `NibStyle`, `NibGroups`
and `nib_plate`.

It writes two files into the directory it is given: the nib plate, `word-plate.webp`, and
the wordmark, `word.png`. Every seed is fixed, so one run writes the same files. It
paints no map and reads no file.

Run it with:

    uv run python examples/word.py out/
"""

import argparse
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import (
    PIGMENTS,
    TRANSPARENCY,
    BrushStyle,
    Canvas,
    PaperStyle,
    PigmentLayer,
    Sheet,
    composite,
    paper_plate,
    rgb,
    save_image,
    wash,
)
from pyntpot.letters import (
    FaceStyle,
    Hand,
    HandStyle,
    Mark,
    NibGroups,
    NibStyle,
    NibSurface,
    Setting,
    nib_plate,
)

logger = logging.getLogger(__name__)

#: The image's width and height, in pixels.
W, H = 640, 360
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The seed of the paper, the washes, the hand and the dither the file is written with.
SEED = 7
#: The hand's seed, chosen from the first thirty for a level baseline.
HAND_SEED = 11
NAME = "pyntpot"
STEM = "word"
#: How many times larger the nib plate is painted than the picture, before it is downsized.
NIB_SCALE = 2
#: The size the name is set at, in pixels.
NAME_PX = 104.0
#: How wide the name is set, in multiples of its size, as the hand writes it.
NAME_WIDTH = 2.75


def _disc(centre_x: float, centre_y: float, radius: float) -> np.ndarray:
    """Return a disc mask of the given centre and radius, in pixels."""
    yy, xx = np.mgrid[0:H, 0:W]
    return ((xx - centre_x) ** 2 + (yy - centre_y) ** 2 <= radius**2).astype(np.float32)


def _line() -> tuple[tuple[float, float], ...]:
    """Return a gentle rise across the disc, in pixels: the line the name is set along."""
    span = NAME_WIDTH * NAME_PX
    x = np.linspace(0.5 * (W - span), 0.5 * (W + span), 40)
    y = 0.6 * H - 0.045 * H * (x - x[0]) / span
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def main(out_dir: Path) -> Path:
    """Wash two discs, letter "pyntpot" over them, and return the wordmark's path.

    Args:
        out_dir: The directory the nib plate and the wordmark are written into.

    Returns:
        The path of the wordmark, `word.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    layers: list[PigmentLayer] = [
        (wash(_disc(cx, cy, r), sheet, 0.6, 0.3), rgb(PIGMENTS[key]), TRANSPARENCY[key])
        for key, cx, cy, r in (
            ("water", 0.5 * W, 0.5 * H, 0.46 * H),
            ("wood", 0.79 * W, 0.57 * H, 0.17 * H),
        )
    ]
    washed = composite(layers, paper, PaperStyle())

    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    marks: list[Mark] = hand.write(Setting(NAME, NAME_PX, path=_line()), hand.generator(HAND_SEED))

    canvas2 = Canvas(0, 0, NIB_SCALE * W, NIB_SCALE * H, NIB_SCALE * W, NIB_SCALE * H)
    dark2 = np.zeros((NIB_SCALE * H, NIB_SCALE * W), np.float32)
    surface = NibSurface(canvas2, NIB_SCALE, dark2, GRAN_PX * NIB_SCALE)
    groups = NibGroups(
        NibStyle(), face, hand_style, BrushStyle(pen_pool_radius_frac=0.15), PaperStyle()
    )
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")

    with Image.open(plate_path) as big:
        small = big.convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    rgba = np.asarray(small, np.float32) / 255
    alpha = rgba[..., 3:]
    out = washed * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path, help="the directory to write the images into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
