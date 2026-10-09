"""Rung 4 of the tutorial: a pen nib's line, drawn as a spiral.

A nib is a brush too: row 6 of the brush sheet is a pen, so `brush_from_id("MAJ6-e",
...)` gives a narrow nib that sets ink down where it touches and nowhere else. The
sequence is the brush stroke's: `stamp` the line into an accumulator, `ink_density` it
on the paper's tooth, and `composite` it over the paper in the ink colour the brush came
with.

Public names it uses: `BrushStyle`, `brush_from_id`, `stamp`, `ink_density`, `Sheet`,
`Canvas`, `PaperStyle`, `paper_plate`, `rgb`, `composite` and `save_image`, all from
`pyntpot.ink`; it introduces none beyond the brush stroke's.

Run it with `uv run python examples/nib_line.py out/`; it writes `out/nib_line.png`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
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
)

logger = logging.getLogger(__name__)

#: The image's width and height, in pixels.
W, H = 360, 240
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise, the nib and the dither the file is written with.
SEED = 11
#: How many turns the spiral makes.
TURNS = 3


def main(out_dir: Path) -> Path:
    """Draw a spiral with a pen nib, write `nib_line.png` into `out_dir` and return its path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    theta = np.linspace(0.0, TURNS * 2 * np.pi, 600)
    radius = 0.42 * min(W, H) * (0.1 + 0.9 * theta / theta[-1])
    line = np.column_stack([W / 2 + radius * np.cos(theta), H / 2 + radius * np.sin(theta)])

    brush, ink_hex = brush_from_id("MAJ6-e", 3.0, 1.0, BrushStyle())
    acc = np.zeros((H, W), np.float32)
    stamp(acc, line, brush, np.random.default_rng(SEED))
    density = ink_density(acc, brush, sheet)

    out = composite([(density, rgb(ink_hex))], paper, PaperStyle())
    path = out_dir / "nib_line.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw a spiral with a pen nib and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
