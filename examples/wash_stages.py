"""Explanation figures: one wash built a stage at a time, every stage from one seed.

`docs/explanation/how-the-wash-works.md` follows a single disc of water-blue wash from a
flat fill to two glazed washes. Each call paints one stage, selected by `figure=`, so the
essay can set the stages side by side; the paper's seed is the same in all of them, so
what changes from one figure to the next is the stage and nothing else.

The figures, in the order the essay builds them:

- `mask`: the coverage mask laid as a flat density, the fill a wash is not.
- `body`: `wash` with no pooled edge. The edge breaks up on the paper's noise, the tone
  drifts and the paper's tooth lightens it; the grain is a slow mottle.
- `rim`: the same wash with a pooled edge (`pool`), pigment gathered just inside the edge.
- `grain`: the same wash on a sheet with a fine grain (`gran_px`), the pigment granulating.
- `overlap`: a second wash, farmland, laid over the first and multiplied with it.
- `glaze`: the same two washes glazed by Kubelka-Munk in place of multiply.

Public names it uses: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`, `wash`, `PIGMENTS`,
`TRANSPARENCY`, `PigmentLayer`, `rgb`, `composite` and `save_image`, all from
`pyntpot.ink`; it introduces none. It does not reach the wash options that give backruns,
a bleed into a shared wet area, a flow rim or a granulation that follows the paper's pits,
because `pyntpot.ink` does not export them.

Run it with `uv run python examples/wash_stages.py out/ --figure rim`; it writes
`out/wash-rim.png`. `--size` sets the image's width in pixels, 360 by default.
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

#: The figures, in the order the essay builds them.
FIGURES: tuple[str, ...] = ("mask", "body", "rim", "grain", "overlap", "glaze")
#: The width the figures are designed at, in pixels; the height is two thirds of it.
DESIGN_W = 360
#: The grain's cell, in pixels at the design width: a slow mottle, then a fine grain.
SLOW_GRAN_PX, FINE_GRAN_PX = 60.0, 6.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11
#: The body density of each wash and the extra the pooled edge adds.
BODY, POOL = 0.8, 0.55


def _disc(w: int, h: int, centre_x: float) -> np.ndarray:
    """A coverage mask: a disc halfway down, `centre_x` of the way across."""
    yy, xx = np.mgrid[0:h, 0:w]
    reach = 0.34 * min(w, h)
    return ((xx - centre_x * w) ** 2 + (yy - h / 2) ** 2 <= reach**2).astype(np.float32)


def main(out_dir: Path, figure: str = "rim", size: int = DESIGN_W) -> Path:
    """Paint one stage of the wash, write it into `out_dir` as `wash-<figure>.png` and return that path.

    Args:
        out_dir: The directory the image is written into.
        figure: The stage, one of `FIGURES`.
        size: The image's width in pixels; its height is two thirds of that.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    w, h = size, size * 2 // 3
    unit = size / DESIGN_W
    gran = (FINE_GRAN_PX if figure in {"grain", "overlap", "glaze"} else SLOW_GRAN_PX) * unit
    sheet = Sheet(h, w, gran, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(), w)
    pool = POOL if figure != "body" else 0.0

    blue = _disc(w, h, 0.5 if figure in {"mask", "body", "rim", "grain"} else 0.4)
    density = blue * BODY if figure == "mask" else wash(blue, sheet, BODY, pool)
    layers: list[PigmentLayer] = [(density, rgb(PIGMENTS["water"]), TRANSPARENCY["water"])]
    if figure in {"overlap", "glaze"}:
        green = wash(_disc(w, h, 0.62), sheet, BODY, POOL)
        layers.append((green, rgb(PIGMENTS["farmland"]), TRANSPARENCY["farmland"]))

    out = composite(layers, paper, PaperStyle(km_glazing=figure == "glaze"))
    path = out_dir / f"wash-{figure}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint one stage of a wash and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="rim", help="the stage to paint")
    parser.add_argument("--size", type=int, default=DESIGN_W, help="the image's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
