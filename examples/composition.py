"""Rung 7 of the tutorial: composition, a wash, a brush stroke and a name on one sheet.

On a 480 by 320 sheet of cream paper a water wash fills a disc and one wet `RIV1-a`
brush stroke runs along a sine through it; both are composited over the paper. The hand
then sets "Keswick" along a gentle sine across the middle of the sheet, the nib strokes
its marks onto one RGBA plate, and the plate is laid over the painted paper the normal
way, by its alpha.

Public names: nothing new. It puts together what earlier rungs introduced: from
`pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`, `wash`, `PIGMENTS`,
`rgb`, `BrushStyle`, `brush_from_id`, `stamp`, `ink_density`, `composite` and
`save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`,
`Mark`, `NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`.

It writes two files into the directory it is given: the nib plate,
`composition-plate.webp`, and the finished image, `composition.png`. Every seed is
fixed, so one run writes the same files. The setting takes its default ink.

Run it with:

    uv run python examples/composition.py out/
"""

import argparse
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import (
    PIGMENTS,
    BrushStyle,
    Canvas,
    PaperStyle,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    paper_plate,
    rgb,
    save_image,
    stamp,
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

W, H = 480, 320
GRAN_PX = 3.0
SEED = 7
NAME = "Keswick"
STEM = "composition"


def _line() -> tuple[tuple[float, float], ...]:
    """Return a gentle sine across the middle third of the canvas, in display pixels."""
    x = np.linspace(W / 3, 2 * W / 3, 40)
    y = H / 2 + 0.04 * H * np.sin(2 * np.pi * (x - W / 3) / (W / 3))
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def _wash_and_stroke(sheet: Sheet) -> tuple[np.ndarray, np.ndarray, str]:
    """Return a water wash's density over a disc, one wet brush stroke's density and its colour."""
    yy, xx = np.mgrid[0:H, 0:W]
    disc = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2 <= (0.3 * min(W, H)) ** 2).astype(np.float32)
    wash_density = wash(disc, sheet, 0.6, 0.3)

    brush, stroke_hex = brush_from_id("RIV1-a", 6.0, 1.0, BrushStyle())
    acc = np.zeros((H, W), np.float32)
    x = np.linspace(0.1 * W, 0.9 * W, 200)
    line = np.column_stack([x, H / 2 + 0.12 * H * np.sin(2 * np.pi * x / W)])
    stamp(acc, line, brush, np.random.default_rng(SEED))
    stroke_density = ink_density(acc, brush, sheet)
    return wash_density, stroke_density, stroke_hex


def main(out_dir: Path) -> Path:
    """Paint a wash and a stroke, write a name over them, and return the finished image's path.

    Args:
        out_dir: The directory the nib plate and the finished image are written into.

    Returns:
        The path of the finished image, `composition.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    wash_density, stroke_density, stroke_hex = _wash_and_stroke(sheet)
    paper = composite(
        [(wash_density, rgb(PIGMENTS["water"])), (stroke_density, rgb(stroke_hex))],
        paper,
        PaperStyle(),
    )

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
