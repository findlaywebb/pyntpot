"""The pigment card: every pigment key, laid as a graded strip across a bar of ink, for the reference page.

Each key of `PIGMENTS` gets one cell, in the order `PIGMENTS` holds them, five to a row. A cell is
a strip of the pigment's wash that deepens from left to right, laid across a crisp, narrow bar of mid grey-brown ink that shows bare beyond the strip's two
ends, and glazed by Kubelka-Munk, with the key lettered beneath it. Over the paper a pigment
shows its colour; over the ink bar it shows its transparency: a staining pigment lets the bar
through, and a covering one veils it. `wash` turns each strip's mask into a density, `rgb` turns the pigment's
hex into a colour, and `composite` stacks the bar and the strips over the paper with
`PaperStyle(km_glazing=True)`. The hand letters each key at twice its size and the plate is
brought down with Lanczos.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate`, `PIGMENTS`, `TRANSPARENCY`, `wash`, `rgb`, `composite`, `PigmentLayer` and
`save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`,
`NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`.

Run it with `uv run python examples/pigment_swatches.py out/`; it writes
`out/pigment_swatches.png`.
"""

import argparse
import logging
import tempfile
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

#: Cells across a row.
COLUMNS = 5
#: One cell's width and height, in pixels.
CELL_W, CELL_H = 192, 124
#: The strip's width and height, and the ink bar's height across its middle, in pixels.
STRIP_W, STRIP_H, BAR_H = 164, 64, 10
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 6.0
#: The seed of the paper's noise, the hand and the dither the file is written with.
SEED = 11
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2
#: The size and the ink of a key's lettering, in pixels.
KEY_PX, KEY_INK = 21.0, "#3a2c20"
#: The ink bar's colour: a mid grey-brown, where a covering veil reads as a lightening and a stain as a tint.
BAR_HEX = "#6a625a"


def _letter(img: np.ndarray, settings: list[Setting]) -> np.ndarray:
    """Letter the settings over `img` with the nib, plate painted at `NIB_SCALE` times and brought down.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    h, w = img.shape[:2]
    big = Canvas(0, 0, w * NIB_SCALE, h * NIB_SCALE, w * NIB_SCALE, h * NIB_SCALE)
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    rng = hand.generator(SEED)
    marks: list[Mark] = [mark for s in settings for mark in hand.write(s, rng)]
    surface = NibSurface(
        big, NIB_SCALE, np.zeros((h * NIB_SCALE, w * NIB_SCALE), np.float32), GRAN_PX * NIB_SCALE
    )
    groups = NibGroups(
        NibStyle(label_ink=KEY_INK, label_pen_width_px=1.5),
        face,
        hand_style,
        BrushStyle(),
        PaperStyle(),
    )
    with tempfile.TemporaryDirectory() as scratch:
        written = nib_plate(marks, surface, groups, Path(scratch) / "plate.webp")
        if written is None:
            raise RuntimeError("the hand wrote no marks")
        with Image.open(written) as plate:
            small = plate.convert("RGBa").resize((w, h), Image.Resampling.LANCZOS)
            rgba = np.asarray(small.convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    return img * (1 - alpha) + rgba[..., :3] * alpha


def _cell_origin(index: int) -> tuple[int, int]:
    """The strip's top-left corner in the index'th cell of the card."""
    row, column = divmod(index, COLUMNS)
    return column * CELL_W + (CELL_W - STRIP_W) // 2, row * CELL_H + 12


def _mask(w: int, h: int, x: int, y: int, strip_h: int, inset: int = 0) -> np.ndarray:
    """A rectangle mask `w` by `h` pixels: the strip's `strip_h` rows from (`x`, `y`)."""
    mask = np.zeros((h, w), np.float32)
    mask[y : y + strip_h, x + inset : x + STRIP_W - inset] = 1.0
    return mask


def main(out_dir: Path) -> Path:
    """Lay every pigment as a graded strip over an ink bar, write `pigment_swatches.png` into `out_dir` and return its path."""
    rows = -(-len(PIGMENTS) // COLUMNS)
    w, h = COLUMNS * CELL_W, rows * CELL_H
    sheet = Sheet(h, w, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)

    bar = np.zeros((h, w), np.float32)
    layers: list[PigmentLayer] = []
    ramp = np.linspace(0.2, 1.0, STRIP_W, dtype=np.float32)
    for index, (key, hex_colour) in enumerate(PIGMENTS.items()):
        x, y = _cell_origin(index)
        bar += _mask(w, h, x, y + (STRIP_H - BAR_H) // 2, BAR_H, inset=-8)
        density = wash(_mask(w, h, x, y, STRIP_H), sheet, 1.0, 0.3)
        density[:, x : x + STRIP_W] *= ramp
        layers.append((density, rgb(hex_colour), TRANSPARENCY[key]))
    ink: PigmentLayer = (np.clip(bar, 0.0, 1.0), rgb(BAR_HEX))
    out = composite([ink, *layers], paper, PaperStyle(km_glazing=True))

    keys = [
        Setting(
            key,
            KEY_PX,
            anchor=(_cell_origin(i)[0] + STRIP_W / 2, _cell_origin(i)[1] + STRIP_H + 28),
            align="middle",
            wash=False,
        )
        for i, key in enumerate(PIGMENTS)
    ]
    path = out_dir / "pigment_swatches.png"
    save_image(_letter(out, keys), path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lay every pigment as a strip over an ink bar and write a PNG."
    )
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
