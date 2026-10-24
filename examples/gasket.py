"""Painting with Python: an Apollonian gasket, every circle a washed disc, glazed where they overlap.

Four circles that each touch the other three are fixed by one rule, Descartes' circle
theorem. Write each circle's curvature as `k = 1 / r`, and give the container a negative
one, since the others lie inside it. Then

    (k1 + k2 + k3 + k4)^2 = 2 (k1^2 + k2^2 + k3^2 + k4^2)

and, given three circles, the fourth that touches all of them has `k4 = k1 + k2 + k3 +/-
2 sqrt(k1 k2 + k2 k3 + k3 k1)`. The two signs are the two circles that fit the gap. The
same rule works on the centres, read as complex numbers, with `k z` in place of `k`. So,
once a circle `k4` is known beside three others, the next one that fills the gap on the
other side is `2 (k1 + k2 + k3) - k4`, for the curvature and for `k z` alike. No square
root is needed again.

`gasket_circles` starts from the container (curvature -1) and three circles inside it
(curvatures 2, 3 and 6), finds the four circles that fill the first gaps, and repeats: every new circle
makes a new gap with each pair of its neighbours. It stops at recursion depth 5 and keeps
at most 300 circles, the largest first. Radii are compared rounded to nine places, ties go to
the shallower depth and then to the order found, and each circle's shade is drawn from a
generator of its own, so no platform's last-digit rounding can change which circle is kept
or what any other circle looks like.

Each circle is then a `wash` of its own, a disc a shade larger than the circle so that it
overlaps its neighbours. The washes are grouped by depth into at most six pigment layers,
and `composite` with `km_glazing=True` glazes the layers by Kubelka-Munk, so the overlap
shows both pigments.

Public names it uses, all from `pyntpot.ink`: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`,
`wash`, `PIGMENTS`, `TRANSPARENCY`, `rgb`, `composite` and `save_image`.

Run it with `uv run python examples/gasket.py out/`; it writes `out/gasket.png`. It takes
`size`, the image's width and height in pixels.
"""

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

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

#: The recursion depth, the most circles kept and the most pigment layers.
MAX_DEPTH = 5
MAX_CIRCLES = 300
MAX_LAYERS = 6
#: The pigments of the layers, from the container inwards: a restrained palette from `PIGMENTS`.
LAYER_PIGMENTS = ("wetland", "water", "wood", "heath", "scrub", "rim")
#: Circles smaller than this, in pixels, are a flat soft disc rather than a full wash.
SMALL_PX = 10.0
#: How much larger than its circle a disc is washed, so that neighbours overlap.
OVERLAP = 1.1
#: The size of the paper's granulation noise, in pixels, at the default size.
GRAN_PX = 8.0
#: The default seed and size.
SEED = 11
SIZE = 640


@dataclass(frozen=True)
class Circle:
    """One circle of the gasket: its curvature, its centre and the recursion depth it came at."""

    curvature: float
    centre: complex
    depth: int

    @property
    def radius(self) -> float:
        """The circle's radius, `1 / |k|`."""
        return 1.0 / abs(self.curvature)


def _seed_circles() -> list[Circle]:
    """The container (curvature -1) and three circles inside it, curvatures 2, 3 and 6, each touching the others."""
    return [
        Circle(-1.0, 0j, 0),
        Circle(2.0, -0.5 + 0j, 0),
        Circle(3.0, 2j / 3, 0),
        Circle(6.0, complex(-0.5, 2 / 3), 0),
    ]


def _replace(quad: list[Circle], j: int, depth: int) -> Circle:
    """The circle that takes the place of `quad[j]`: `2 (k1 + k2 + k3) - k4`, for `k` and for `k z`."""
    others = [c for i, c in enumerate(quad) if i != j]
    k = 2 * sum(c.curvature for c in others) - quad[j].curvature
    kz = 2 * sum(c.curvature * c.centre for c in others) - quad[j].curvature * quad[j].centre
    return Circle(k, complex(kz) / k, depth)


def gasket_circles(depth: int) -> list[Circle]:
    """The four seed circles and every circle found by `depth` rounds of Descartes, at most `MAX_CIRCLES`."""
    seeds = _seed_circles()
    found = list(seeds)
    frontier: list[tuple[list[Circle], int]] = [(seeds, -1)]
    for level in range(1, depth + 1):
        grown: list[tuple[list[Circle], int]] = []
        for quad, skip in frontier:
            for j in range(4):
                if j == skip:
                    continue
                new = _replace(quad, j, level)
                found.append(new)
                grown.append(([*quad[:j], new, *quad[j + 1 :]], j))
        frontier = grown
    order = sorted(range(len(found)), key=lambda i: (-round(found[i].radius, 9), found[i].depth, i))
    return [found[i] for i in order[:MAX_CIRCLES]]


def _disc(circle: Circle, size: int, centre_px: float, scale_px: float) -> np.ndarray:
    """A soft-edged disc mask on a `size` square canvas for one circle, a shade larger than it and kept inside the container."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = centre_px + scale_px * circle.centre.real
    cy = centre_px - scale_px * circle.centre.imag
    r = scale_px * circle.radius * (1.0 if circle.curvature < 0 else OVERLAP)
    disc = np.clip(r - np.hypot(xx - cx, yy - cy) + 0.5, 0.0, 1.0)
    inside = np.clip(scale_px - np.hypot(xx - centre_px, yy - centre_px) + 0.5, 0.0, 1.0)
    return disc * inside


def _ring(size: int, centre_px: float, scale_px: float, sheet: Sheet, seed: int) -> np.ndarray:
    """The container's edge as one thin brush stroke round it, as ink density."""
    brush, _ = brush_from_id("LAN1-a", 2.4 * size / SIZE, 1.0, BrushStyle())
    angle = np.linspace(0.0, 2.0 * np.pi, 720)
    path = np.column_stack(
        [centre_px + scale_px * np.cos(angle), centre_px + scale_px * np.sin(angle)]
    )
    acc = np.zeros((size, size), np.float32)
    stamp(acc, path, brush, np.random.default_rng([seed, MAX_CIRCLES]))
    return ink_density(acc, brush, sheet)


def gasket_layers(size: int, sheet: Sheet, seed: int) -> list[PigmentLayer]:
    """Wash every circle of the gasket and group the washes into pigment layers."""
    centre_px, scale_px = size / 2, 0.40 * size
    layers = [np.zeros((size, size), np.float32) for _ in range(MAX_LAYERS)]
    for rank, circle in enumerate(gasket_circles(MAX_DEPTH)):
        layer = 0 if circle.curvature < 0 else 1 + min(circle.depth, MAX_LAYERS - 2)
        shade = np.random.default_rng([seed, rank]).uniform(0.2, 0.45)
        base = 0.3 if circle.curvature < 0 else shade + 0.5 * circle.depth / MAX_DEPTH
        disc = _disc(circle, size, centre_px, scale_px)
        small = scale_px * circle.radius < SMALL_PX
        body = disc * base * 1.3 if small else wash(disc, sheet, base, 0.55)
        layers[layer] = np.maximum(layers[layer], body)
    layers[MAX_LAYERS - 1] = np.maximum(
        layers[MAX_LAYERS - 1], 0.9 * _ring(size, centre_px, scale_px, sheet, seed)
    )
    stack: list[PigmentLayer] = [
        (density, rgb(PIGMENTS[key]), TRANSPARENCY[key])
        for density, key in zip(layers, LAYER_PIGMENTS, strict=True)
    ]
    return stack


def main(out_dir: Path, size: int = SIZE, seed: int = SEED) -> Path:
    """Wash and glaze the gasket, write `gasket.png` into `out_dir` and return its path."""
    sheet = Sheet(size, size, GRAN_PX * size / SIZE, seed)
    canvas = Canvas(0, 0, size, size, size, size)
    style = PaperStyle(km_glazing=True, paper_foxing=0.03)
    paper = paper_plate(sheet, canvas, style, size)

    stack = gasket_layers(size, sheet, seed)
    path = out_dir / "gasket.png"
    save_image(composite(stack, paper, style), path, seed=seed)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint an Apollonian gasket and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument(
        "--size", type=int, default=SIZE, help="the image's width and height in pixels"
    )
    parser.add_argument(
        "--seed", type=int, default=SEED, help="the seed of the paper and the washes"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.size, args.seed)
