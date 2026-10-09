"""Rung 5 of the tutorial: how two pigments combine where they overlap.

Two washes, `farmland` and `wood`, are laid as overlapping discs. Each is a
`PigmentLayer`: its density, its colour from `PIGMENTS`, and its `TRANSPARENCY`, what
the pigment shows over black as a share of what it shows over white. `composite` stacks
the layers over the paper the way the `PaperStyle` asks: with `km_glazing=False` it
multiplies them, and with `km_glazing=True` it glazes them by Kubelka-Munk, which reads
each layer's transparency. The two results are written side by side, multiply on the
left and glazing on the right.

Public names it introduces: `PigmentLayer`, `TRANSPARENCY` and `PaperStyle`'s
`km_glazing`, beside the earlier rungs' `Sheet`, `Canvas`, `paper_plate`, `wash`,
`PIGMENTS`, `rgb`, `composite` and `save_image`, all from `pyntpot.ink`.

Run it with `uv run python examples/pigments.py out/`; it writes `out/pigments.png`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
    PIGMENTS,
    TRANSPARENCY,
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

#: One panel's width and height, in pixels; the image is two panels wide.
W, H = 360, 240
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11


def _disc(centre_x: float) -> np.ndarray:
    """A disc mask on one panel, centred at `centre_x` across and halfway down."""
    yy, xx = np.mgrid[0:H, 0:W]
    return ((xx - centre_x) ** 2 + (yy - H / 2) ** 2 <= (0.3 * min(W, H)) ** 2).astype(np.float32)


def main(out_dir: Path) -> Path:
    """Composite two overlapping washes both ways, write `pigments.png` into `out_dir` and return its path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    layers: list[PigmentLayer] = [
        (wash(_disc(centre_x), sheet, 0.6, 0.3), rgb(PIGMENTS[key]), TRANSPARENCY[key])
        for key, centre_x in (("farmland", 0.38 * W), ("wood", 0.62 * W))
    ]
    multiplied = composite(layers, paper, PaperStyle(km_glazing=False))
    glazed = composite(layers, paper, PaperStyle(km_glazing=True))

    out = np.concatenate([multiplied, glazed], axis=1)
    path = out_dir / "pigments.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Composite two pigments and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
