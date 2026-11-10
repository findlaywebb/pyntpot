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
- `glaze`: a grid, not a stage. A blue stain under a warm pigment whose transparency steps
  from 0.04 to 0.9, laid by multiply in one row and glazed by Kubelka-Munk in the other, so a
  covering pigment hides the blue only where the glaze reads its transparency.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS`,
`PAINTERS_TRANSPARENCY`, `PigmentLayer`, `rgb`, `composite` and `save_image`; for the grid's
labels, `GridSpec`, `LabelStyle` and `label_grid` from the sibling `labelled_grid.py`, which
lays out the cells and letters the names. It introduces none. It does not reach the wash options that give backruns,
a bleed into a shared wet area, a flow rim or a granulation that follows the paper's pits,
because `pyntpot.ink` does not export them.

Run it with `uv run python examples/wash_stages.py out/ --figure rim`; it writes
`out/wash-rim.png`. `--size` sets the image's width in pixels, 360 by default; the `glaze`
grid is designed at 800 and scales with it.
"""

import argparse
import logging
from pathlib import Path

import numpy as np
from labelled_grid import GridSpec, LabelStyle, label_grid

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    PIGMENTS,
    TRANSPARENCY,
    Canvas,
    Colour,
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
#: The glaze grid: its design width, the transparencies it steps through across, and its
#: cell height as a share of the width.
GRID_W, STEPS, CELL_H = 800, (0.04, 0.2, 0.5, 0.9), 0.17


def _disc(w: int, h: int, centre_x: float) -> np.ndarray:
    """A coverage mask: a disc halfway down, `centre_x` of the way across."""
    return _circle(w, h, centre_x * w, h / 2, 0.34 * min(w, h))


def _circle(w: int, h: int, cx: float, cy: float, radius: float) -> np.ndarray:
    """A coverage mask `w` by `h` pixels: a disc of `radius` pixels centred at (`cx`, `cy`)."""
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2).astype(np.float32)


def _glaze_grid(size: int) -> np.ndarray:
    """Paint a blue stain under a warm pigment at four transparencies, multiplied above and glazed below."""
    unit = size / GRID_W
    left, top, gap = round(110 * unit), round(52 * unit), round(12 * unit)
    spec = GridSpec(
        size, len(STEPS), 2, round(CELL_H * size), left, top, gap, gap, round(14 * unit)
    )
    cell_w, cell_h, h = spec.cell_w, round(CELL_H * size), spec.height
    boxes = spec.boxes()
    sheet = Sheet(h, size, SLOW_GRAN_PX * unit / 2, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, size, h, size, h), PaperStyle(paper_foxing=0.0), size)

    out = paper
    blue, warm = rgb(PAINTERS_PIGMENTS["ultramarine"]), rgb(PAINTERS_PIGMENTS["burnt_sienna"])
    cell_sheet = Sheet(cell_h, cell_w, SLOW_GRAN_PX * unit / 2, SEED)
    under = wash(
        _circle(cell_w, cell_h, 0.4 * cell_w, cell_h / 2, 0.34 * cell_h), cell_sheet, 0.8, 0.4
    )
    over = wash(
        _circle(cell_w, cell_h, 0.62 * cell_w, cell_h / 2, 0.34 * cell_h), cell_sheet, 0.9, 0.4
    )
    for row in range(2):
        for col, transparency in enumerate(STEPS):
            x0, y0 = boxes[row][col][:2]
            layers: list[PigmentLayer] = [
                (under, blue, PAINTERS_TRANSPARENCY["ultramarine"]),
                (over, warm, transparency),
            ]
            cell = out[y0 : y0 + cell_h, x0 : x0 + cell_w]
            out[y0 : y0 + cell_h, x0 : x0 + cell_w] = composite(
                layers, cell, PaperStyle(km_glazing=row == 1)
            )
    style = LabelStyle(
        px=21.0 * unit,
        ink=Colour("#3a2c20"),
        pen_px=1.5 * size / GRID_W,
        gran_px=SLOW_GRAN_PX * size / DESIGN_W,
        seed=SEED,
        col_dy=14 * unit,
        row_dx=12 * unit,
        row_dy=7 * unit,
    )
    return label_grid(out, boxes, STEPS, ("multiply", "glazed"), style)


def main(out_dir: Path, figure: str = "rim", size: int = DESIGN_W) -> Path:
    """Paint one stage of the wash, write it into `out_dir` as `wash-<figure>.png` and return that path.

    Args:
        out_dir: The directory the image is written into.
        figure: The stage, one of `FIGURES`.
        size: The image's width in pixels; its height is two thirds of that, except for
            the `glaze` grid, whose height follows its rows.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    path = out_dir / f"wash-{figure}.png"
    if figure == "glaze":
        save_image(_glaze_grid(size), path, seed=SEED)
        logger.info("wrote %s", path)
        return path
    w, h = size, size * 2 // 3
    unit = size / DESIGN_W
    gran = (FINE_GRAN_PX if figure in {"grain", "overlap"} else SLOW_GRAN_PX) * unit
    sheet = Sheet(h, w, gran, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)
    pool = POOL if figure != "body" else 0.0

    blue = _disc(w, h, 0.5 if figure in {"mask", "body", "rim", "grain"} else 0.4)
    density = blue * BODY if figure == "mask" else wash(blue, sheet, BODY, pool)
    layers: list[PigmentLayer] = [(density, rgb(PIGMENTS["water"]), TRANSPARENCY["water"])]
    if figure == "overlap":
        green = wash(_disc(w, h, 0.62), sheet, BODY, POOL)
        layers.append((green, rgb(PIGMENTS["farmland"]), TRANSPARENCY["farmland"]))

    out = composite(layers, paper, PaperStyle(km_glazing=False))
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
