"""Curves: a rose and a spirograph drawn with the brush, and a Lissajous figure with the pen.

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
the figure. A light wash is laid under each curve first, over the shape the curve encloses
(the polygon of its points, filled where its winding is odd), then the line goes over it.

The Lissajous figure is a technical figure and keeps the narrow pen: `stamp` sets a nib's
bristles along the points, `ink_density` turns them into ink on the paper's tooth, and
`composite` lays wash and ink over the paper. The rose and the spirograph are painted with
the brush, because a brush has a stroke's weight. The rose is cut where it crosses the
centre into five petals; each petal is one stroke of a wet brush (`stamp`'s `wprof` swells it
from nothing at the centre to full width and back to nothing, so there is no knot at the
centre), over a wash of its own in `quinacridone_rose` at a density of its own. The
spirograph is one long stroke in three pigments laid end to end, `ultramarine`, `cerulean`
and `sap_green`, over a pale `cerulean` wash; `wprof` thins it and the density falls along it,
so the line runs drier as the brush empties.

Public names it uses: `PIGMENTS`, `PAINTERS_PIGMENTS`, `PAINTERS_TRANSPARENCY`, `BrushStyle`,
`Canvas`, `PaperStyle`, `Sheet`, `brush_from_id`, `composite`, `ink_density`, `paper_plate`,
`rgb`, `save_image`, `stamp` and `wash`, all from `pyntpot.ink`. Pillow's `ImageDraw` only fills
the polygon that becomes the wash's coverage.

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
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
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
SEED = 5
#: How far the curve reaches from the centre, as a fraction of the image; the rest is margin.
REACH = 0.38
#: How many points a curve is sampled at.
STEPS = 4000


def rose(t: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return the rose `r = cos(5 a)` over `t` from 0 to pi, from one crossing of the centre to the last, tip up.

    The angle `a` is `t` turned by a tenth of a half turn, so that `t = 0` is a crossing of the centre; five petals
    follow, each ending at the centre.
    """
    a = t + np.pi / 10
    r = np.cos(5 * a)
    return r * np.sin(a), -r * np.cos(a)


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


#: Each figure: its formulas, the range of `t`, and the wash pigment and the nib's width at 640 px
#: that the penned figure uses; the brushed figures choose their painter's pigments themselves.
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


def _petal(points: np.ndarray, index: int) -> np.ndarray:
    """Return the points of the rose's `index`th petal: one fifth of the curve, from the centre round and back."""
    each = (len(points) - 1) // 5
    return points[index * each : (index + 1) * each + 1]


def _taper(count: int, floor: float, power: float) -> np.ndarray:
    """Return a width profile of `count` samples that swells from `floor` to 1 and back, a petal's stroke."""
    return np.maximum(np.sin(np.linspace(0.0, np.pi, count)) ** power, floor)


def _stack(layers: list[tuple[np.ndarray, str]]) -> list[PigmentLayer]:
    """Return density layers, each with its painter's pigment (a key of `PAINTERS_PIGMENTS`) and transparency."""
    return [
        (density, rgb(PAINTERS_PIGMENTS[key]), PAINTERS_TRANSPARENCY[key])
        for density, key in layers
    ]


def _paint_rose(
    points: np.ndarray, sheet: Sheet, size: int, rng: np.random.Generator
) -> list[PigmentLayer]:
    """Return the rose's layers: a wash for each petal, then one brush stroke round each."""
    wet, _ = brush_from_id("RIV2-a", 14.0 * size / SIZE, 1.0, BrushStyle())
    petals = np.zeros((size, size), np.float32)
    strokes = np.zeros((size, size), np.float32)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    for i in range(5):
        petal = _petal(points, i)
        drift = rng.normal(0.0, 0.006 * size, 2)
        body = wash(_cover(petal + drift, size), sheet, rng.uniform(0.3, 0.5), 0.45)
        reach = np.hypot(*(petal - size / 2).T).max()
        deepen = 1.45 - 0.9 * np.hypot(xx - size / 2, yy - size / 2) / reach
        body = np.clip(body * deepen, 0.0, 1.0)
        petals = np.maximum(petals, body)
        stamp(strokes, petal, wet, rng, wprof=_taper(24, 0.05, 0.6) * rng.uniform(0.75, 1.1))
    return _stack(
        [
            (petals, "quinacridone_rose"),
            (0.55 * ink_density(strokes, wet, sheet), "perylene_maroon"),
        ]
    )


def _paint_spirograph(
    points: np.ndarray, sheet: Sheet, size: int, rng: np.random.Generator
) -> list[PigmentLayer]:
    """Return the spirograph's layers: a pale wash, then one long stroke in three pigments that runs drier."""
    layers = [(wash(_cover(points, size), sheet, 0.3, 0.3), "cerulean")]
    thirds = np.array_split(np.arange(len(points)), 3)
    for i, (idx, key) in enumerate(
        zip(thirds, ("ultramarine", "cerulean", "sap_green"), strict=True)
    ):
        stop = min(idx[-1] + 2, len(points))
        part = points[idx[0] : stop]
        brush, _ = brush_from_id(
            ("RIV2-a", "TRK3-a", "TRK4-a")[i], 6.0 * size / SIZE, 1.0, BrushStyle()
        )
        acc = np.zeros((size, size), np.float32)
        fade = np.linspace(1.0 - i / 3, 1.0 - (i + 1) / 3, 24)
        stamp(acc, part, brush, rng, wprof=0.45 + 0.55 * fade)
        layers.append((ink_density(acc, brush, sheet) * (0.55 + 0.45 * fade.mean()), key))
    return _stack(layers)


def main(out_dir: Path, figure: str = "rose", size: int = SIZE) -> Path:
    """Draw one curve over a light wash and write `curves-<figure>.png` into `out_dir`.

    The rose and the spirograph are painted with the brush and the Lissajous figure is penned.

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
    points = _points(figure, size)
    rng = np.random.default_rng(SEED)
    if figure == "lissajous":
        style = PaperStyle()
        paper = paper_plate(sheet, canvas, style, size)
        under = wash(_cover(points, size), sheet, 0.45, 0.35)
        paper = composite([(under, rgb(PIGMENTS[pigment]))], paper, style)
        brush, ink_hex = brush_from_id("MAJ6-e", nib_px * size / SIZE + 1.0, 1.0, BrushStyle())
        acc = np.zeros((size, size), np.float32)
        stamp(acc, points, brush, rng)
        out = composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], paper, style)
    else:
        style = PaperStyle(km_glazing=True, paper_foxing=0.03)
        paper = paper_plate(sheet, canvas, style, size)
        paint = _paint_rose if figure == "rose" else _paint_spirograph
        out = composite(paint(points, sheet, size, rng), paper, style)
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
