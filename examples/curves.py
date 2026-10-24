"""Curves drawn with the pen: a rose, a Lissajous figure and a spirograph.

Each figure is a parametric curve: a pair of formulas, `x(t)` and `y(t)`, that give a
point on the paper for every value of the number `t`. Step `t` in small increments, join
the points, and the curve appears.

- The rose is `r = cos(k t)`, a radius that swells and shrinks as the angle turns. With
  `k = 5` it has five petals.
- The Lissajous figure is `x = sin(a t + d)`, `y = sin(b t)`: two swings at right angles
  to each other, three across for every two down here, so it crosses itself in a knot.
- The spirograph is the hypotrochoid of a small wheel of radius `r` rolling inside a ring
  of radius `R`, with the pen at distance `d` from the wheel's centre:
  `x = (R - r) cos t + d cos((R - r) t / r)`, `y = (R - r) sin t - d sin((R - r) t / r)`.
  With `R = 9`, `r = 4` and `d = 6` the pen returns home after four turns and has made
  nine loops.

Every curve is scaled to the same radius, so a clear margin of bare paper is left round
the figure. A light wash of one pigment is laid under the curve first, over the shape the
curve encloses (the polygon of its points, filled where its winding is odd), then the pen
draws the line over it: `stamp` sets a narrow nib's bristles along the points, `ink_density`
turns them into ink on the paper's tooth, and `composite` lays wash and ink over the paper.

Public names it uses: `PIGMENTS`, `BrushStyle`, `Canvas`, `PaperStyle`, `Sheet`,
`brush_from_id`, `composite`, `ink_density`, `paper_plate`, `rgb`, `save_image`, `stamp`
and `wash`, all from `pyntpot.ink`; it introduces none beyond the nib line's and the
wash's. Pillow's `ImageDraw` only fills the polygon that becomes the wash's coverage.

It takes `figure=` (`rose`, `lissajous` or `spirograph`) and `size=`, the width and height
of the square image in pixels. Every seed is fixed, so one run writes the same file.

Run it with `uv run python examples/curves.py out/ --figure rose`; it writes
`out/curves-rose.png`.
"""

import argparse
import logging
from collections.abc import Callable
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pyntpot.ink import (
    PIGMENTS,
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
    wash,
)

logger = logging.getLogger(__name__)

#: The default width and height of the square image, in pixels.
SIZE = 640
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 3.0
#: The seed of the paper's noise, the nib and the dither the file is written with.
SEED = 5
#: How far the curve reaches from the centre, as a fraction of the image; the rest is margin.
REACH = 0.38
#: How many points a curve is sampled at.
STEPS = 4000


def rose(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the rose `r = cos(5 t)` over `t` from 0 to pi, which closes after half a turn."""
    r = np.cos(5 * t)
    return r * np.cos(t), r * np.sin(t)


def lissajous(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the Lissajous figure with three swings across for two down."""
    return np.sin(3 * t + np.pi / 2), np.sin(2 * t)


def spirograph(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the hypotrochoid with ring 9, wheel 4 and pen distance 6 over four turns."""
    ring, wheel, pen = 9.0, 4.0, 6.0
    k = (ring - wheel) / wheel
    return (ring - wheel) * np.cos(t) + pen * np.cos(k * t), (ring - wheel) * np.sin(
        t
    ) - pen * np.sin(k * t)


#: Each figure: its formulas, the range of `t`, the wash pigment and the nib's width at 640 px.
FIGURES: dict[
    str, tuple[Callable[[np.ndarray], tuple[np.ndarray, np.ndarray]], float, str, float]
] = {
    "rose": (rose, np.pi, "heath", 2.6),
    "lissajous": (lissajous, 2 * np.pi, "water", 2.4),
    "spirograph": (spirograph, 8 * np.pi, "wood", 2.0),
}


def _points(figure: str, size: int) -> np.ndarray:
    """Return the figure's points in pixels, centred, scaled to `REACH` of the image."""
    formula, t_end, _pigment, _width = FIGURES[figure]
    x, y = formula(np.linspace(0.0, t_end, STEPS))
    scale = REACH * size / max(np.abs(x).max(), np.abs(y).max())
    return np.column_stack([size / 2 + scale * x, size / 2 + scale * y])


def _cover(points: np.ndarray, size: int) -> np.ndarray:
    """Return a 0 to 1 mask of the polygon the points make, filled where it winds an odd number of times."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).polygon([(float(px), float(py)) for px, py in points], fill=255)
    return np.asarray(mask, np.float32) / 255


def main(out_dir: Path, figure: str = "rose", size: int = SIZE) -> Path:
    """Draw one curve with the pen over a light wash and write `curves-<figure>.png` into `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: Which curve to draw: `rose`, `lissajous` or `spirograph`.
        size: The width and height of the square image, in pixels.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of the three curves.
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {sorted(FIGURES)}, not {figure!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    _formula, _t_end, pigment, nib_px = FIGURES[figure]

    sheet = Sheet(size, size, GRAN_PX, SEED)
    canvas = Canvas(0, 0, size, size, size, size)
    paper = paper_plate(sheet, canvas, PaperStyle(), size)

    points = _points(figure, size)
    under = wash(_cover(points, size), sheet, 0.45, 0.35)
    paper = composite([(under, rgb(PIGMENTS[pigment]))], paper, PaperStyle())

    brush, ink_hex = brush_from_id("MAJ6-e", nib_px * size / SIZE + 1.0, 1.0, BrushStyle())
    acc = np.zeros((size, size), np.float32)
    stamp(acc, points, brush, np.random.default_rng(SEED))
    density = ink_density(acc, brush, sheet)

    out = composite([(density, rgb(ink_hex))], paper, PaperStyle())
    path = out_dir / f"curves-{figure}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument(
        "--figure", choices=sorted(FIGURES), default="rose", help="which curve to draw"
    )
    parser.add_argument(
        "--size", type=int, default=SIZE, help="the image's width and height in pixels"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, figure=args.figure, size=args.size)
