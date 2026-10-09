"""Rung 2 of the tutorial: one wash of watercolour laid over the paper.

A wash starts from a coverage mask, here a disc drawn in numpy. `wash` turns the mask
into pigment density on the paper's noise: a flat body, and extra pigment pooled just
inside the edge. `composite` lays that density over the paper in a pigment's colour:
`PIGMENTS` holds each pigment's `#rrggbb` hex, and `rgb` turns it into the float triple
`composite` reads. `PaperStyle` says how the layers combine; its defaults multiply them.

Public names it introduces: `wash`, `PIGMENTS`, `rgb` and `composite`, beside the
paper rung's `Sheet`, `Canvas`, `PaperStyle`, `paper_plate` and `save_image`, all from
`pyntpot.ink`.

Run it with `uv run python examples/wash.py out/`; it writes `out/wash.png`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
    PIGMENTS,
    Canvas,
    PaperStyle,
    Sheet,
    composite,
    paper_plate,
    rgb,
    save_image,
    wash,
)

logger = logging.getLogger(__name__)

#: The image's width and height, in pixels.
W, H = 360, 240
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11


def main(out_dir: Path) -> Path:
    """Lay a disc of water over the paper, write it into `out_dir` as `wash.png` and return that path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    yy, xx = np.mgrid[0:H, 0:W]
    disc = ((xx - W / 2) ** 2 + (yy - H / 2) ** 2 <= (0.3 * min(W, H)) ** 2).astype(np.float32)
    density = wash(disc, sheet, 0.6, 0.3)

    out = composite([(density, rgb(PIGMENTS["water"]))], paper, PaperStyle())
    path = out_dir / "wash.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lay one wash over the paper and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
