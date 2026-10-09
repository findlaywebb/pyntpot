"""Rung 6 of the tutorial: a name written by hand with a nib, laid over the paper.

The hand sets "Grasmere" along a gentle sine across the middle of a 360 by 240 sheet, the
nib strokes its marks onto one RGBA plate, and the plate is laid over the cream paper the
normal way, by its alpha.

Public names it introduces: from `pyntpot.letters`, `FaceStyle` and `HandStyle` (the
face and the hand's style), `Hand` (which writes a `Setting` as a list of `Mark`),
`NibSurface`, `NibStyle` and `NibGroups` (what the nib writes on and the style groups it
reads) and `nib_plate` (the marks stroked onto an RGBA plate and written). From
`pyntpot.ink` it uses `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`, `paper_plate` and
`save_image`, met in earlier rungs.

It writes two files into the directory it is given: the nib plate,
`lettering-plate.webp`, and the finished image, `lettering.png`. Every seed is fixed, so
one run writes the same files. The setting takes its default ink.

Run it with:

    uv run python examples/lettering.py out/
"""

import argparse
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import BrushStyle, Canvas, PaperStyle, Sheet, paper_plate, save_image
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

W, H = 360, 240
GRAN_PX = 3.0
SEED = 7
NAME = "Grasmere"
STEM = "lettering"


def _line() -> tuple[tuple[float, float], ...]:
    """Return a gentle sine across the middle third of the canvas, in display pixels."""
    x = np.linspace(W / 3, 2 * W / 3, 40)
    y = H / 2 + 0.04 * H * np.sin(2 * np.pi * (x - W / 3) / (W / 3))
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def main(out_dir: Path) -> Path:
    """Write a hand-lettered name over the paper and return the finished image's path.

    Args:
        out_dir: The directory the nib plate and the finished image are written into.

    Returns:
        The path of the finished image, `lettering.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    marks: list[Mark] = hand.write(Setting(NAME, 36.0, path=_line()), hand.generator(SEED))

    surface = NibSurface(canvas, 1.0, np.zeros((H, W), np.float32), GRAN_PX)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")

    rgba = np.asarray(Image.open(plate_path).convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    out = paper * (1 - alpha) + rgba[..., :3] * alpha

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
