"""The pigment sheet: every pigment key, laid as one washed disc, for the reference page.

Each key of `PIGMENTS` is laid as a small wash on the paper, in the order `PIGMENTS` holds
them, five to a row. A `wash` of a disc mask gives the density, `rgb` turns the pigment's
hex into a colour, and `composite` stacks the fifteen discs over the paper with the
`PaperStyle` defaults, so each disc is the pigment alone over white paper, multiplied.
The sheet carries no lettering; the page beside it lists the keys in the same order.

Public names it uses: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`, `PIGMENTS`, `wash`,
`rgb`, `composite` and `save_image`, all from `pyntpot.ink`.

Run it with `uv run python examples/pigment_swatches.py out/`; it writes
`out/pigment_swatches.png`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
    PIGMENTS,
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

logger = logging.getLogger(__name__)

#: Discs across a row.
COLUMNS = 5
#: One swatch cell's side, in pixels.
CELL = 120
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11


def _disc(index: int, w: int, h: int) -> np.ndarray:
    """A disc mask centred in the index'th cell of the sheet."""
    row, column = divmod(index, COLUMNS)
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = (column + 0.5) * CELL, (row + 0.5) * CELL
    return ((xx - cx) ** 2 + (yy - cy) ** 2 <= (0.36 * CELL) ** 2).astype(np.float32)


def main(out_dir: Path) -> Path:
    """Lay every pigment as a washed disc, write `pigment_swatches.png` into `out_dir` and return its path."""
    rows = -(-len(PIGMENTS) // COLUMNS)
    w, h = COLUMNS * CELL, rows * CELL
    sheet = Sheet(h, w, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(), w)

    layers: list[PigmentLayer] = [
        (wash(_disc(index, w, h), sheet, 0.8, 0.3), rgb(hex_colour))
        for index, hex_colour in enumerate(PIGMENTS.values())
    ]
    out = composite(layers, paper, PaperStyle())
    path = out_dir / "pigment_swatches.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lay every pigment as a disc and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
