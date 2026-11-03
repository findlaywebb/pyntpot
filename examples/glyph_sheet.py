"""The glyph sheet: every printable ASCII glyph of the face, written by the hand, for the reference page.

The top block writes each glyph alone in its own cell at `GLYPH_PX`, sixteen cells a row:
the capitals, the small letters, the digits and the 32 ASCII symbols the face ships. The
bottom block writes the same characters again as running lines at `SMALL_PX`, the size a
map label is read at, where a glyph's terminal tails and the bridges inside it matter
most. Each glyph is written with the default face, hand, nib and ink, on the default
paper with no foxing, so a change to how a glyph is traced shows plainly on the sheet.

It covers printable ASCII only: the face's Latin-1 and Latin Extended-A letters are not
drawn. The space is not drawn either, since it has no ink.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate` and `save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`,
`Setting`, `Mark`, `NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`.

Run it with `uv run python examples/glyph_sheet.py out/`; it writes `out/glyph_sheet.png`.
Every seed is fixed, so one run writes the same file.
"""

import argparse
import logging
import string
import tempfile
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

#: The rows of the cell block, in order: capitals, small letters, digits and symbols.
ROWS: tuple[str, ...] = (
    string.ascii_uppercase[:16],
    string.ascii_uppercase[16:],
    string.ascii_lowercase[:16],
    string.ascii_lowercase[16:],
    string.digits,
    string.punctuation[:16],
    string.punctuation[16:],
)
#: The running lines of the small block, one per family.
LINES: tuple[str, ...] = (
    string.ascii_uppercase,
    string.ascii_lowercase,
    string.digits + " " + string.punctuation,
)
#: The cells across one row of the cell block.
COLUMNS = 16
#: The sheet's width, its margin, and one cell's height, in pixels.
W, MARGIN, CELL_H = 720, 20, 50
#: The size each glyph is written at in its cell, and the size of the running lines.
GLYPH_PX, SMALL_PX = 32.0, 14.0
#: How far apart the running lines sit, and the gap above them, in pixels.
SMALL_LEADING, SMALL_GAP = 22, 22
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The seed of the paper, the hand and the dither the file is written with.
SEED = 11
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2
STEM = "glyph_sheet"


def _settings(h: int) -> list[Setting]:
    """Return every setting on the sheet: one a glyph in the cell block, one a running line."""
    cell_w = (W - 2 * MARGIN) / COLUMNS
    settings = [
        Setting(
            ch,
            GLYPH_PX,
            anchor=(MARGIN + (c + 0.5) * cell_w, MARGIN + (r + 0.75) * CELL_H),
            align="middle",
            wash=False,
        )
        for r, row in enumerate(ROWS)
        for c, ch in enumerate(row)
    ]
    top = h - MARGIN - (len(LINES) - 1) * SMALL_LEADING
    settings += [
        Setting(line, SMALL_PX, anchor=(MARGIN, top + i * SMALL_LEADING), wash=False)
        for i, line in enumerate(LINES)
    ]
    return settings


def main(out_dir: Path) -> Path:
    """Write every glyph on the paper and return the path of `glyph_sheet.png` in `out_dir`.

    Args:
        out_dir: The directory the image is written into.

    Returns:
        The path of the image, `glyph_sheet.png`.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    h = 2 * MARGIN + len(ROWS) * CELL_H + SMALL_GAP + (len(LINES) - 1) * SMALL_LEADING
    sheet = Sheet(h, W, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, W, h, W, h), PaperStyle(paper_foxing=0.0), W)

    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    rng = hand.generator(SEED)
    marks: list[Mark] = [mark for s in _settings(h) for mark in hand.write(s, rng)]

    big = Canvas(0, 0, W * NIB_SCALE, h * NIB_SCALE, W * NIB_SCALE, h * NIB_SCALE)
    dark = np.zeros((h * NIB_SCALE, W * NIB_SCALE), np.float32)
    surface = NibSurface(big, NIB_SCALE, dark, GRAN_PX * NIB_SCALE)
    groups = NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())
    with tempfile.TemporaryDirectory() as scratch:
        written = nib_plate(marks, surface, groups, Path(scratch) / "plate.webp")
        if written is None:
            raise RuntimeError("the hand wrote no marks")
        with Image.open(written) as plate:
            small = plate.convert("RGBA").resize((W, h), Image.Resampling.LANCZOS)
    rgba = np.asarray(small, np.float32) / 255
    alpha = rgba[..., 3:]
    out = paper * (1 - alpha) + rgba[..., :3] * alpha

    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write every glyph of the hand and save a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
