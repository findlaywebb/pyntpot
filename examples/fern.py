"""Painting with Python: a Barnsley fern, iterated from four affine maps and washed in two greens.

A point starts at the origin. Again and again one of four affine maps, each `x, y -> (a x +
b y + e, c x + d y + f)`, is chosen at random and applied, and the point is kept. The maps
and the odds of choosing each are Barnsley's: 1 per cent flatten the point onto the stem,
85 per cent carry it up the frond, and 7 per cent each throw it onto the left and the
right leaflet. Which map was last chosen is kept with every point.

The points are counted into a grid the size of the canvas. The count becomes a coverage
mask (`1 - exp(-k n)`, so a pixel stops getting darker once it is well covered), and the
mask becomes a `wash`. The frond, the points that last took the 85 per cent map, is laid in
`wood`; the leaflets, the points of the two 7 per cent maps, are laid in `scrub`, and both
are glazed by Kubelka-Munk, so where leaflet meets frond the greens stay green. A second,
sharper count of all the points is laid over the washes in `wood` to draw the veins and
the stem. At most 400 sampled points then get a brush dab: `stamp` lays a short stroke of a
wet brush, and `ink_density` turns it into a darker green.

Public names it uses, all from `pyntpot.ink`: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`,
`wash`, `PIGMENTS`, `TRANSPARENCY`, `rgb`, `composite`, `brush_from_id`, `BrushStyle`, `stamp`,
`ink_density` and `save_image`.

Run it with `uv run python examples/fern.py out/`; it writes `out/fern.png`. It takes
`size`, the image's width in pixels (its height is four thirds of that), and `seed`.
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
#: The index of the first leaflet map; the maps before it are the stem and the frond.
LEFT_LEAFLET = 2
#: The odds of choosing each map.
PROBABILITIES = (0.01, 0.85, 0.07, 0.07)
#: The most points iterated, and the most that get a brush dab.
MAX_POINTS = 200_000
MAX_DABS = 400
#: The canvas's extent in fern units, with a margin: the fern runs from -2.18 to 2.66 across
#: and from 0 to 10 up.
X_MIN, X_MAX, Y_MAX = -2.7, 3.2, 10.4
#: The size of the paper's granulation noise, in pixels, at the default width.
GRAN_PX = 8.0
#: The default seed, and the default width of the image in pixels.
SEED = 7
SIZE = 600


def fern_points(n: int, seed: int) -> np.ndarray:
    """Iterate the four maps `n` times; return an `(n, 3)` array of x, y and the map last chosen."""
    rng = np.random.default_rng(seed)
    choices = rng.choice(4, size=min(n, MAX_POINTS), p=PROBABILITIES)
    out = np.empty((len(choices), 3))
    x = y = 0.0
    for i, k in enumerate(choices.tolist()):
        a, b, c, d, e, f = MAPS[k]
        x, y = a * x + b * y + e, c * x + d * y + f
        out[i] = x, y, k
    return out


def _count(points: np.ndarray, w: int, h: int) -> np.ndarray:
    """Count the points into a `(h, w)` grid, y up the page, fern fitted to the canvas."""
    col = (points[:, 0] - X_MIN) / (X_MAX - X_MIN) * w
    row = (1.0 - points[:, 1] / Y_MAX) * h
    grid, _, _ = np.histogram2d(row, col, bins=(h, w), range=((0, h), (0, w)))
    return grid.astype(np.float32)


def _cover(grid: np.ndarray, k: float) -> np.ndarray:
    """A coverage mask in 0 to 1: a pixel saturates once it is well covered."""
    return (1.0 - np.exp(-k * grid)).astype(np.float32)


def _thicken(cover: np.ndarray, px: int) -> np.ndarray:
    """Grow a mask by `px` pixels each way, so a wash, which rounds off fine detail, still reads it."""
    image = Image.fromarray(cover, mode="F").filter(ImageFilter.MaxFilter(2 * px + 1))
    return np.asarray(image, dtype=np.float32)


def _dabs(points: np.ndarray, w: int, h: int, scale: float, sheet: Sheet, seed: int) -> np.ndarray:
    """Dab a wet brush at up to `MAX_DABS` sampled points, each a short stroke leaning up the frond."""
    rng = np.random.default_rng(seed)
    brush, _ = brush_from_id("RIV1-a", 2.0 * scale, 1.0, BrushStyle())
    pick = points[rng.choice(len(points), size=min(MAX_DABS, len(points)), replace=False)]
    acc = np.zeros((h, w), np.float32)
    for x, y, _ in pick:
        px = (x - X_MIN) / (X_MAX - X_MIN) * w
        py = (1.0 - y / Y_MAX) * h
        lean = rng.normal(-0.5, 0.35)
        tip = (px + 8 * scale * np.sin(lean), py - 8 * scale * np.cos(lean))
        stamp(acc, np.array([(px, py), tip]), brush, rng)
    return ink_density(acc, brush, sheet)


def main(out_dir: Path, size: int = SIZE, seed: int = SEED) -> Path:
    """Iterate the fern, wash it in two greens, write `fern.png` into `out_dir` and return its path."""
    w, h = size, size * 4 // 3
    scale = size / SIZE
    sheet = Sheet(h, w, GRAN_PX * scale, seed)
    canvas = Canvas(0, 0, w, h, w, h)
    style = PaperStyle(km_glazing=True, paper_foxing=0.03)
    paper = paper_plate(sheet, canvas, style, w)

    points = fern_points(MAX_POINTS, seed)
    frond = points[points[:, 2] < LEFT_LEAFLET]
    leaflets = points[points[:, 2] >= LEFT_LEAFLET]
    layers: list[PigmentLayer] = [
        (
            wash(_thicken(_cover(_count(leaflets, w, h), 1.0), 1), sheet, 0.55, 0.25),
            rgb(PIGMENTS["scrub"]),
            TRANSPARENCY["scrub"],
        ),
        (
            wash(_thicken(_cover(_count(frond, w, h), 1.0), 1), sheet, 0.75, 0.3),
            rgb(PIGMENTS["wood"]),
            TRANSPARENCY["wood"],
        ),
    ]
    detail = _cover(_count(points, w, h), 0.25)
    layers.append(
        (0.55 * detail * (0.7 + 0.6 * sheet.gran), rgb(PIGMENTS["wood"]), TRANSPARENCY["wood"])
    )
    dabs = _dabs(frond, w, h, scale, sheet, seed)
    layers.append((0.5 * dabs, rgb(PIGMENTS["wood"]), TRANSPARENCY["wood"]))
    out = composite(layers, paper, style)
    path = out_dir / "fern.png"
    save_image(out, path, seed=seed)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a Barnsley fern and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--size", type=int, default=SIZE, help="the image's width in pixels")
    parser.add_argument(
        "--seed", type=int, default=SEED, help="the seed of the points and the paper"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.size, args.seed)
