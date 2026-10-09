"""Rung 1 of the tutorial: the paper every other rung paints on.

A `Sheet` holds the paper's noise fields, a `Canvas` the pixel grid they are painted
on, and `paper_plate` paints the cream rag, its worn border, vignette and foxing, as a
`PaperStyle` asks. `save_image` writes the painted array to a PNG. Everything is
seeded, so one run writes the same file.

Public names it introduces: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate` and
`save_image`, all from `pyntpot.ink`.

Run it with `uv run python examples/paper.py out/`; it writes `out/paper.png`.
"""

import argparse
import logging
from pathlib import Path

from pyntpot.ink import Canvas, PaperStyle, Sheet, paper_plate, save_image

logger = logging.getLogger(__name__)

#: The image's width and height, in pixels.
W, H = 360, 240
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11


def main(out_dir: Path) -> Path:
    """Paint the paper, write it into `out_dir` as `paper.png` and return that path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)
    path = out_dir / "paper.png"
    save_image(paper, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint the paper and write it as a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
