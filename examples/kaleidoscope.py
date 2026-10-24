"""A kaleidoscope: one small motif, washed and inked, repeated by mirror and rotation.

The motif is drawn once, in a wedge of the paper at the right of the centre: a petal, a
leaf, a disc, a diamond, a corner of the centre and a spoke, each a list of points given as a radius (a fraction of
the figure's reach) and an angle in degrees. Two moves repeat it:

- the mirror turns a point at angle `a` into one at `-a`, so the motif meets its own
  reflection along the horizontal line through the centre;
- the rotation turns a point through 60 degrees, six times round, so the pair repeats
  with six-fold symmetry. Mirror and rotation together make twelve copies of every shape.

The shapes are the wash: each pigment's twelve copies are filled into one coverage mask
with Pillow's `ImageDraw.polygon`, and `wash` turns the mask into pigment density on the
paper's noise. Where two pigments overlap, `composite` glazes one over the other. The
lines are the ink: the twelve copies of each polyline are stamped with a narrow nib, the
way `nib_line.py` draws its spiral.

The figure keeps a clear margin of bare paper all round: its outer ring reaches 40% of
the image's width from the centre.

Public names it uses: `PIGMENTS`, `BrushStyle`, `Canvas`, `PaperStyle`, `PigmentLayer`,
`Sheet`, `brush_from_id`, `composite`, `ink_density`, `paper_plate`, `rgb`, `save_image`, `stamp`
and `wash`, all from `pyntpot.ink`; it introduces none beyond the curves script's.

It takes `size=`, the width and height of the square image in pixels. Every seed is
fixed, so one run writes the same file.

Run it with `uv run python examples/kaleidoscope.py out/`; it writes
`out/kaleidoscope.png`.
"""

import argparse
import logging
import math
from itertools import pairwise
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from pyntpot.ink import (
    PIGMENTS,
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

#: The default width and height of the square image, in pixels.
SIZE = 640
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 3.0
#: The seed of the paper's noise, the nib and the dither the file is written with.
SEED = 9
#: How far the outer ring reaches from the centre, as a fraction of the image.
REACH = 0.40
#: How many times the motif is turned round the centre.
FOLD = 6

#: One point of the motif: a radius from 0 to 1 and an angle in degrees.
Polar = tuple[float, float]


def _petal(r0: float, r1: float, angle: float, half_width: float) -> list[Polar]:
    """Return the outline of a leaf from radius `r0` to `r1`, centred on `angle` degrees."""
    u = np.linspace(0.0, 1.0, 24)
    spread = half_width * np.sin(np.pi * u) ** 0.8
    out = [(r0 + (r1 - r0) * float(a), angle + float(s)) for a, s in zip(u, spread, strict=True)]
    back = [
        (r0 + (r1 - r0) * float(a), angle - float(s))
        for a, s in zip(u[::-1], spread[::-1], strict=True)
    ]
    return out + back


def _disc(r: float, angle: float, radius: float) -> list[Polar]:
    """Return a circle of `radius` (in the figure's units) centred at `r` and `angle` degrees."""
    cx, cy = r * math.cos(math.radians(angle)), r * math.sin(math.radians(angle))
    ring = [
        (cx + radius * math.cos(a), cy + radius * math.sin(a))
        for a in np.linspace(0, 2 * np.pi, 40)
    ]
    return [(math.hypot(x, y), math.degrees(math.atan2(y, x))) for x, y in ring]


#: The shapes washed, by pigment: a water petal, a wetland leaf, a wood diamond and heath shapes.
SHAPES: dict[str, list[list[Polar]]] = {
    "water": [_petal(0.12, 0.58, 14.0, 11.0)],
    "wetland": [_petal(0.20, 0.56, 30.0, 4.5)],
    "wood": [[(0.60, 30.0), (0.78, 21.0), (0.94, 30.0), (0.78, 39.0)]],
    "heath": [_disc(0.76, 0.0, 0.07), [(0.11, 30.0), (0.11, 90.0), (0.11, 150.0)]],
}

#: The lines inked: the shapes' outlines and the spokes between the petals.
LINES: list[list[Polar]] = [
    *(shape + shape[:1] for shapes in SHAPES.values() for shape in shapes),
    [(0.11, 0.0), (0.69, 0.0)],
    [(0.85, 0.0), (0.97, 0.0)],
]


def _to_xy(shape: list[Polar], turn: int, size: int, *, mirror: bool) -> np.ndarray:
    """Return a shape's points in pixels, mirrored about the horizontal axis or not, turned `turn` times."""
    angles = np.radians([(-a if mirror else a) + turn * 360.0 / FOLD for _r, a in shape])
    radii = np.array([r for r, _a in shape]) * REACH * size
    return np.column_stack([size / 2 + radii * np.cos(angles), size / 2 + radii * np.sin(angles)])


def _copies(shape: list[Polar], size: int) -> list[np.ndarray]:
    """Return the twelve copies of a shape: the mirror pair, turned six times round."""
    return [
        _to_xy(shape, turn, size, mirror=mirror) for mirror in (False, True) for turn in range(FOLD)
    ]


def _cover(shapes: list[list[Polar]], size: int) -> np.ndarray:
    """Return a 0 to 1 mask of every copy of every shape in `shapes`."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    for shape in shapes:
        for points in _copies(shape, size):
            draw.polygon([(float(x), float(y)) for x, y in points], fill=255)
    return np.asarray(mask, np.float32) / 255


def _dense(points: np.ndarray, step: float) -> np.ndarray:
    """Return the polyline resampled so no two neighbours are more than `step` pixels apart."""
    out = [points[:1]]
    for a, b in pairwise(points):
        n = max(1, math.ceil(float(np.hypot(*(b - a))) / step))
        out.append(a + (b - a) * (np.arange(1, n + 1)[:, None] / n))
    return np.concatenate(out)


def main(out_dir: Path, size: int = SIZE) -> Path:
    """Paint the washed and inked motif, repeated by mirror and rotation, into `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        size: The width and height of the square image, in pixels.

    Returns:
        The path of the image, `kaleidoscope.png`.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Sheet(size, size, GRAN_PX, SEED)
    canvas = Canvas(0, 0, size, size, size, size)
    paper = paper_plate(sheet, canvas, PaperStyle(), size)

    washes: list[PigmentLayer] = [
        (wash(_cover(shapes, size), sheet, 0.55, 0.35), rgb(PIGMENTS[pigment]))
        for pigment, shapes in SHAPES.items()
    ]
    paper = composite(washes, paper, PaperStyle())

    brush, ink_hex = brush_from_id("MAJ6-e", 2.0 * size / SIZE + 1.0, 1.0, BrushStyle())
    acc = np.zeros((size, size), np.float32)
    rng = np.random.default_rng(SEED)
    ring = _to_xy([(1.0, a) for a in np.linspace(0.0, 360.0, 361)], 0, size, mirror=False)
    for points in [ring, *(copy for line in LINES for copy in _copies(line, size))]:
        stamp(acc, _dense(points, 1.0), brush, rng)
    density = ink_density(acc, brush, sheet)

    out = composite([(density, rgb(ink_hex))], paper, PaperStyle())
    path = out_dir / "kaleidoscope.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument(
        "--size", type=int, default=SIZE, help="the image's width and height in pixels"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, size=args.size)
