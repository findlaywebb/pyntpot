"""How-to: paint a picture from your own outline and your own path.

A hand-drawn outline of a fell, a list of (x, y) points you could have read from anywhere,
is rasterised into a coverage mask with Pillow's `ImageDraw`. `wash` lays the mask as a
wash on the paper in the `water` pigment, a pen nib (`brush_from_id`, `stamp`,
`ink_density`) strokes the outline's edge as a line, and the hand sets "Skiddaw" along a
path of your own (a `Setting` with a `path`), which `nib_plate` strokes onto a plate laid
over the painting by its alpha.

Public names it uses, all met in the tutorial: from `pyntpot.ink`, `Sheet`, `Canvas`,
`PaperStyle`, `BrushStyle`, `PIGMENTS`, `brush_from_id`, `composite`, `ink_density`,
`paper_plate`, `rgb`, `save_image`, `stamp` and `wash`; from `pyntpot.letters`, `FaceStyle`,
`Hand`, `HandStyle`, `Mark`, `NibGroups`, `NibStyle`, `NibSurface`, `Setting` and
`nib_plate`. What is new is where the shapes come from: the mask is rasterised from a
polygon and the line and the lettering path are your own points.

It writes two files into the directory it is given: the nib plate,
`own_shapes-plate.webp`, and the finished image, `own_shapes.png`. Every seed is fixed.

Run it with:

    uv run python examples/how_to_own_shapes.py out/
"""

import argparse
import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

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
SEED = 5
NAME = "Skiddaw"
STEM = "own_shapes"

#: A fell's skyline, left to right, as (x, y) points on the canvas. Yours can come from anywhere.
SKYLINE: tuple[tuple[float, float], ...] = (
    (40, 250),
    (95, 205),
    (140, 215),
    (205, 120),
    (245, 105),
    (285, 140),
    (330, 170),
    (375, 150),
    (440, 250),
)


def _smoothed(points: tuple[tuple[float, float], ...], rounds: int = 3) -> np.ndarray:
    """Return the points with each corner cut `rounds` times, ends kept, so the line curves."""
    line = np.array(points, np.float64)
    for _ in range(rounds):
        near, far = 0.75 * line[:-1] + 0.25 * line[1:], 0.25 * line[:-1] + 0.75 * line[1:]
        line = np.vstack([line[:1], np.column_stack([near, far]).reshape(-1, 2), line[-1:]])
    return line


def _outline_mask(skyline: np.ndarray) -> np.ndarray:
    """Return the skyline closed along the bottom and filled, as a 0 to 1 coverage mask."""
    image = Image.new("L", (W, H), 0)
    corners = [(float(x), float(y)) for x, y in skyline]
    ImageDraw.Draw(image).polygon([*corners, (corners[-1][0], 275), (corners[0][0], 275)], fill=255)
    return np.asarray(image, np.float32) / 255


def _lettering_path() -> tuple[tuple[float, float], ...]:
    """Return a gentle rise below the fell, in display pixels, for the name to follow."""
    x = np.linspace(130, 350, 50)
    y = 302 - 10 * np.sin(np.pi * (x - 130) / 220)
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def main(out_dir: Path) -> Path:
    """Wash a hand-drawn fell, ink its skyline, letter its name, and return the image's path.

    Args:
        out_dir: The directory the nib plate and the finished image are written into.

    Returns:
        The path of the finished image, `own_shapes.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    skyline = _smoothed(SKYLINE)
    density = wash(_outline_mask(skyline), sheet, 0.6, 0.3)

    brush, ink_hex = brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())
    acc = np.zeros((H, W), np.float32)
    stamp(acc, skyline, brush, np.random.default_rng(SEED))
    line_density = ink_density(acc, brush, sheet)
    painted = composite(
        [(density, rgb(PIGMENTS["water"])), (line_density, rgb(ink_hex))], paper, PaperStyle()
    )

    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    marks: list[Mark] = hand.write(
        Setting(NAME, 38.0, path=_lettering_path()), hand.generator(SEED)
    )
    surface = NibSurface(canvas, 1.0, np.zeros((H, W), np.float32), GRAN_PX)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    plate_path = nib_plate(marks, surface, groups, out_dir / f"{STEM}-plate.webp")
    if plate_path is None:
        raise RuntimeError("the hand wrote no marks")
    rgba = np.asarray(Image.open(plate_path).convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    out = painted * (1 - alpha) + rgba[..., :3] * alpha

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
