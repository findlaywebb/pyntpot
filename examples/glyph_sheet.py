"""The glyph sheet: every printable ASCII glyph of the face, written by the hand, for the reference page.

The top block writes each glyph alone in its own cell at `GLYPH_PX`, sixteen cells a row:
the capitals, the small letters, the digits and the 32 ASCII symbols the face ships. The
bottom block writes the same characters again as running lines at `SMALL_PX`, the size a
map label is read at, where a glyph's terminal tails and the bridges inside it matter
most. Each glyph is written with the default face, hand, nib and ink, on the default
paper with no foxing, so a change to how a glyph is traced shows plainly on the sheet.

Isolation. Every cell is its own render: its own hand generator, seeded by `glyph_seed`
from the character alone, and its own nib plate, the size of the cell. Every running line
is likewise its own render, seeded by `line_seed` from its place on the sheet. The cells
and lines are then laid side by side on one paper. So a change to how one glyph is drawn
moves only that glyph's cell and the running lines that hold it; no other pixel on the
sheet moves. A glyph that reaches past its cell is cut at the cell's edge, never drawn
into its neighbour.

It covers printable ASCII only: the face's Latin-1 and Latin Extended-A letters are not
drawn. The space is not drawn either, since it has no ink.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate` and `save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`,
`Setting`, `NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`.

Run it with `uv run python examples/glyph_sheet.py out/`; it writes `out/glyph_sheet.png`.
Every seed is fixed, so one run writes the same file.
"""

import argparse
import logging
import string
import tempfile
from collections.abc import Mapping
from pathlib import Path

import numpy as np
from PIL import Image

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
#: The sheet's width, its margin, and one cell's width and height, in pixels.
W, MARGIN, CELL_W, CELL_H = 720, 20, 42, 50
#: Where the cell block starts across the sheet: centred, so both side margins match.
CELLS_LEFT = (W - COLUMNS * CELL_W) // 2
#: The size each glyph is written at in its cell, and the size of the running lines.
GLYPH_PX, SMALL_PX = 32.0, 14.0
#: How far apart the running lines sit, and the gap above them, in pixels. Each line's
#: render is one leading tall, its baseline `LINE_BASELINE` pixels down from its top.
SMALL_LEADING, SMALL_GAP, LINE_BASELINE = 26, 22, 19
#: The sheet's height, in pixels.
H = 2 * MARGIN + len(ROWS) * CELL_H + SMALL_GAP + (len(LINES) - 1) * SMALL_LEADING
#: The top of the first running line's render, in pixels.
LINES_TOP = H - MARGIN - (len(LINES) - 1) * SMALL_LEADING - LINE_BASELINE
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 5.0
#: The sheet's base seed: the paper's and the dither's, and mixed into every render's.
SEED = 11
#: The key a running line's seed is mixed from, past every Unicode code point, so a line's
#: seed is never a character's.
LINE_KEY = 0x110000
#: How many times its size each render is painted before it is brought down.
NIB_SCALE = 2
STEM = "glyph_sheet"

#: A box on the sheet: left, top, right and bottom, in pixels, the right and bottom excluded.
Box = tuple[int, int, int, int]


def _mixed(key: int) -> int:
    """Return a seed mixed from the sheet's base seed and `key`, the same on every platform."""
    return int(np.random.SeedSequence((SEED, key)).generate_state(1)[0])


def glyph_seed(ch: str) -> int:
    """Return the seed a glyph's cell is written with, from its code point and `SEED` alone."""
    return _mixed(ord(ch))


def line_seed(index: int) -> int:
    """Return the seed the running line at `index` in `LINES` is written with."""
    return _mixed(LINE_KEY + index)


def cell_box(ch: str) -> Box:
    """Return the box of the cell `ch` is written in.

    Raises:
        ValueError: When `ch` has no cell on the sheet.
    """
    for r, row in enumerate(ROWS):
        c = row.find(ch)
        if len(ch) == 1 and c >= 0:
            x0, y0 = CELLS_LEFT + c * CELL_W, MARGIN + r * CELL_H
            return x0, y0, x0 + CELL_W, y0 + CELL_H
    raise ValueError(f"no cell on the sheet for {ch!r}")


def line_box(index: int) -> Box:
    """Return the box of the running line at `index` in `LINES`."""
    y0 = LINES_TOP + index * SMALL_LEADING
    return MARGIN, y0, W - MARGIN, y0 + SMALL_LEADING


def _ink(
    hand: Hand, setting: Setting, seed: int, groups: NibGroups, size: tuple[int, int]
) -> np.ndarray:
    """Return one render's ink, an RGBA float array `size` (width, height) at display scale.

    The setting is written with a generator of its own from `seed`, on a nib plate of its
    own the size of the render, so nothing drawn elsewhere on the sheet reaches it.
    """
    w, h = size
    big = Canvas(0, 0, w * NIB_SCALE, h * NIB_SCALE, w * NIB_SCALE, h * NIB_SCALE)
    dark = np.zeros((h * NIB_SCALE, w * NIB_SCALE), np.float32)
    surface = NibSurface(big, NIB_SCALE, dark, GRAN_PX * NIB_SCALE)
    marks = hand.write(setting, hand.generator(seed))
    with tempfile.TemporaryDirectory() as scratch:
        written = nib_plate(marks, surface, groups, Path(scratch) / "plate.webp")
        if written is None:
            raise RuntimeError(f"the hand wrote no marks for {setting.text!r}")
        with Image.open(written) as plate:
            small = plate.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
    return np.asarray(small, np.float32) / 255


def _line_nib(line: str, nibs: Mapping[str, NibStyle], default: NibStyle) -> NibStyle:
    """Return the nib a running line is written with: its first character's in `nibs`, else `default`."""
    return next((nibs[ch] for ch in line if ch in nibs), default)


def paint(nibs: Mapping[str, NibStyle] | None = None) -> np.ndarray:
    """Paint the sheet and return it, an `(H, W, 3)` float array, before it is dithered.

    Args:
        nibs: A nib for each character to be written with other than the default nib. A
            glyph's cell is written with its own; a running line with the first of its
            characters' that is named, else the default. None names none.

    Returns:
        The painted sheet: every cell and running line, each its own render, on one paper.

    Raises:
        RuntimeError: When the hand wrote no marks for a cell or a line.
    """
    named: Mapping[str, NibStyle] = dict[str, NibStyle]() if nibs is None else nibs
    sheet = Sheet(H, W, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, W, H, W, H), PaperStyle(paper_foxing=0.0), W)
    face, hand_style, default = FaceStyle(), HandStyle(), NibStyle()
    hand = Hand(face, hand_style)

    def groups(nib: NibStyle) -> NibGroups:
        """Return the style groups a render is written with, `nib` its nib."""
        return NibGroups(nib, face, hand_style, BrushStyle(), PaperStyle())

    ink = np.zeros((H, W, 4), np.float32)
    for ch in "".join(ROWS):
        x0, y0, x1, y1 = cell_box(ch)
        setting = Setting(
            ch, GLYPH_PX, anchor=(CELL_W / 2, 0.75 * CELL_H), align="middle", wash=False
        )
        nib = groups(named.get(ch, default))
        ink[y0:y1, x0:x1] = _ink(hand, setting, glyph_seed(ch), nib, (CELL_W, CELL_H))
    for i, line in enumerate(LINES):
        x0, y0, x1, y1 = line_box(i)
        setting = Setting(line, SMALL_PX, anchor=(0.0, float(LINE_BASELINE)), wash=False)
        nib = groups(_line_nib(line, named, default))
        ink[y0:y1, x0:x1] = _ink(hand, setting, line_seed(i), nib, (x1 - x0, y1 - y0))
    alpha = ink[..., 3:]
    return paper * (1 - alpha) + ink[..., :3] * alpha


def main(out_dir: Path) -> Path:
    """Write every glyph on the paper and return the path of `glyph_sheet.png` in `out_dir`.

    Args:
        out_dir: The directory the image is written into.

    Returns:
        The path of the image, `glyph_sheet.png`.

    Raises:
        RuntimeError: When the hand wrote no marks for a cell or a line.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{STEM}.png"
    save_image(paint(), path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write every glyph of the hand and save a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
