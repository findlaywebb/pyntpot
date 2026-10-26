"""Painting with Python: nine ferns from slightly perturbed Barnsley maps, one species in one grid.

`examples/fern.py` paints one fern from Barnsley's four affine maps. Move the numbers of the
maps a little and the fern moves a little: a frond map turned a few degrees more curls
further, one scaled a per cent smaller makes a shorter, lacier plant, a leaflet map with its
matrix nudged leans its leaflets over. This script runs that loop nine times, each time
with a seed of its own. `perturbed` returns the four maps for one seed: the stem map is
kept (it only draws the stem), the frond map is turned by `-1` to `6` degrees and scaled by
a few per cent, and the two leaflet maps have every entry of their matrices moved by up to
5 per cent. Because the maps change, so does the fern's extent, so `_fit` measures each
fern's points and fits them into its cell.

Each fern is painted the way the single fern is: the points are counted into a grid the size
of the cell, the count becomes a coverage mask and the mask becomes a `wash`, the frond in
`wood` and the leaflets in `scrub`, glazed by Kubelka-Munk; a sharper count of every point draws
the veins and the stem; and a few dabs of a wet brush finish it. Each fern is painted in its
own cell at the cell's size, with its points and dabs in proportion to the cell's area,
never at the grid's size and downsized, and the paper is laid once under all nine.

It does not choose between ferns, vary the pigments or draw anything but the nine ferns.

Public names it uses, all from `pyntpot.ink`: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`,
`wash`, `PIGMENTS`, `TRANSPARENCY`, `rgb`, `PigmentLayer`, `composite`, `brush_from_id`,
`BrushStyle`, `stamp`, `ink_density` and `save_image`.

Run it with `uv run python examples/fern_family.py out/`; it writes `out/fern-family.png`. It
takes `size`, the grid's width in pixels (its height is four thirds of that), and `seed`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from pyntpot.ink import (
    PIGMENTS,
    TRANSPARENCY,
    BrushStyle,
    Canvas,
    PaperStyle,
    PigmentLayer,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    paper_plate,
    rgb,
    save_image,
    stamp,
    wash,
)

logger = logging.getLogger(__name__)

#: Barnsley's four maps, one row each: `a, b, c, d, e, f` in `x' = a x + b y + e`,
#: `y' = c x + d y + f`. In order: the stem, the frond, the left leaflet, the right leaflet.
MAPS = np.array(
    [
        [0.00, 0.00, 0.00, 0.16, 0.0, 0.00],
        [0.85, 0.04, -0.04, 0.85, 0.0, 1.60],
        [0.20, -0.26, 0.23, 0.22, 0.0, 1.60],
        [-0.15, 0.28, 0.26, 0.24, 0.0, 0.44],
    ]
)
#: The odds of choosing each map.
PROBABILITIES = (0.01, 0.85, 0.07, 0.07)
#: The index of the first leaflet map; the maps before it are the stem and the frond.
LEFT_LEAFLET = 2
#: The points and the dabs of one fern on the single fern's 600 by 800 canvas, which the
#: points and dabs of a cell are scaled down from by area.
FULL_POINTS, FULL_DABS, FULL_AREA = 200_000, 400, 600 * 800
#: A family is this many ferns across and this many down.
ACROSS, DOWN = 3, 3
#: The share of a cell a fern's width and its height may fill.
FIT_WIDTH, FIT_HEIGHT = 0.8, 0.8
#: The margin of paper round the grid, as a share of its width.
MARGIN = 0.05
#: The size of the paper's granulation noise, in pixels, at the single fern's width.
GRAN_PX = 8.0
#: The default seed, and the default width of the grid in pixels.
SEED = 7
SIZE = 900


def perturbed(maps: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Return the four maps moved a few per cent: the frond turned and scaled, the leaflets' matrices nudged."""
    out = maps.copy()
    theta = np.radians(rng.uniform(-1.0, 6.0))
    scale = rng.uniform(0.835, 0.865)
    out[1, :4] = scale * np.array([np.cos(theta), np.sin(theta), -np.sin(theta), np.cos(theta)])
    out[1, 5] = maps[1, 5] * rng.uniform(0.94, 1.06)
    for k in (2, 3):
        out[k, :4] = maps[k, :4] * rng.uniform(0.94, 1.06, 4)
    return out


def fern_points(maps: np.ndarray, n: int, rng: np.random.Generator) -> np.ndarray:
    """Iterate `maps` `n` times; return an `(n, 3)` array of x, y and the map last chosen."""
    choices = rng.choice(4, size=n, p=PROBABILITIES)
    out = np.empty((n, 3))
    x = y = 0.0
    for i, k in enumerate(choices.tolist()):
        a, b, c, d, e, f = maps[k]
        x, y = a * x + b * y + e, c * x + d * y + f
        out[i] = x, y, k
    return out


def _fit(points: np.ndarray, w: int, h: int) -> np.ndarray:
    """Return `points` as pixels in a `(h, w)` cell: the fern centred, its foot low, y up the page."""
    lo, hi = points[:, :2].min(axis=0), points[:, :2].max(axis=0)
    k = min(FIT_WIDTH * w / (hi[0] - lo[0]), FIT_HEIGHT * h / (hi[1] - lo[1]))
    col = w / 2 + k * (points[:, 0] - (lo[0] + hi[0]) / 2)
    row = h * (0.5 + FIT_HEIGHT / 2) - k * (points[:, 1] - lo[1])
    return np.column_stack([col, row, points[:, 2]])


def _count(pixels: np.ndarray, w: int, h: int) -> np.ndarray:
    """Count the points, already in pixels, into a `(h, w)` grid."""
    grid, _, _ = np.histogram2d(pixels[:, 1], pixels[:, 0], bins=(h, w), range=((0, h), (0, w)))
    return grid.astype(np.float32)


def _cover(grid: np.ndarray, k: float) -> np.ndarray:
    """A coverage mask in 0 to 1: a pixel saturates once it is well covered."""
    return (1.0 - np.exp(-k * grid)).astype(np.float32)


def _thicken(cover: np.ndarray, px: int) -> np.ndarray:
    """Grow a mask by `px` pixels each way, so a wash, which rounds off fine detail, still reads it."""
    image = Image.fromarray(cover, mode="F").filter(ImageFilter.MaxFilter(2 * px + 1))
    return np.asarray(image, dtype=np.float32)


def _dabs(frond: np.ndarray, w: int, h: int, sheet: Sheet, rng: np.random.Generator) -> np.ndarray:
    """Dab a wet brush at sampled points of the frond, each a short stroke leaning up the frond."""
    scale = w / 600
    brush, _ = brush_from_id("RIV1-a", 2.0 * scale, 1.0, BrushStyle())
    count = min(round(FULL_DABS * w * h / FULL_AREA), len(frond))
    acc = np.zeros((h, w), np.float32)
    for x, y, _ in frond[rng.choice(len(frond), size=count, replace=False)]:
        lean = rng.normal(-0.5, 0.35)
        tip = (x + 8 * scale * np.sin(lean), y - 8 * scale * np.cos(lean))
        stamp(acc, np.array([(x, y), tip]), brush, rng)
    return ink_density(acc, brush, sheet)


def paint_fern(cell: tuple[int, int], sheet: Sheet, seed: int) -> list[np.ndarray]:
    """Paint one perturbed fern in a `(height, width)` cell; return its leaflet, frond, vein and dab densities."""
    h, w = cell
    rng = np.random.default_rng(seed)
    maps = perturbed(MAPS, rng)
    n = max(round(FULL_POINTS * w * h / FULL_AREA), 2_000)
    pixels = _fit(fern_points(maps, n, rng), w, h)
    frond = pixels[pixels[:, 2] < LEFT_LEAFLET]
    leaflets = pixels[pixels[:, 2] >= LEFT_LEAFLET]
    detail = _cover(_count(pixels, w, h), 0.25)
    return [
        wash(_thicken(_cover(_count(leaflets, w, h), 1.0), 1), sheet, 0.55, 0.25),
        wash(_thicken(_cover(_count(frond, w, h), 1.0), 1), sheet, 0.75, 0.3),
        0.55 * detail * (0.7 + 0.6 * sheet.gran),
        0.5 * _dabs(frond, w, h, sheet, rng),
    ]


def main(out_dir: Path, size: int = SIZE, seed: int = SEED) -> Path:
    """Paint nine perturbed ferns on one sheet, write `fern-family.png` into `out_dir` and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = size, size * 4 // 3
    style = PaperStyle(km_glazing=True, paper_foxing=0.03)
    paper = paper_plate(Sheet(h, w, GRAN_PX * size / 600, seed), Canvas(0, 0, w, h, w, h), style, w)
    pad = round(MARGIN * w)
    cw, ch = (w - 2 * pad) // ACROSS, (h - 2 * pad) // DOWN
    densities = [np.zeros((h, w), np.float32) for _ in range(4)]
    for i in range(ACROSS * DOWN):
        row, col = divmod(i, ACROSS)
        window = (
            slice(pad + row * ch, pad + (row + 1) * ch),
            slice(pad + col * cw, pad + (col + 1) * cw),
        )
        sheet = Sheet(ch, cw, GRAN_PX * cw / 600, seed + i)
        for target, density in zip(densities, paint_fern((ch, cw), sheet, seed + i), strict=True):
            target[window] = density
    pigments = ("scrub", "wood", "wood", "wood")
    layers: list[PigmentLayer] = [
        (density, rgb(PIGMENTS[key]), TRANSPARENCY[key])
        for density, key in zip(densities, pigments, strict=True)
    ]
    path = out_dir / "fern-family.png"
    save_image(composite(layers, paper, style), path, seed=seed)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Paint nine perturbed Barnsley ferns and write a PNG."
    )
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--size", type=int, default=SIZE, help="the grid's width in pixels")
    parser.add_argument(
        "--seed", type=int, default=SEED, help="the seed of the points and the paper"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.size, args.seed)
