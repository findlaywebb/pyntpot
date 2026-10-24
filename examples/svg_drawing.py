"""Painting with Python: a small SVG drawing, its filled shapes washed and its strokes inked.

pyntpot does not read SVG. This script reads its own drawing, `drawings/fell.svg`, with
`xml.etree.ElementTree` and a path subset it states: the absolute commands `M`, `L`, `C`
and `Z`, with a cubic Bezier flattened to `CURVE_SEGMENTS` straight segments. Any other
command raises `ValueError`, so a drawing outside the subset fails loudly rather than
painting half of itself.

Each `<path>` is painted by what it says. A filled path becomes a mask: its flattened
outline is drawn with Pillow's `ImageDraw.polygon` onto a greyscale image, `wash` turns
that mask into pigment density, and the `fill` colour picks the nearest pigment in
`PIGMENTS`. A stroked path is inked: its `class` names a pen (`pen`, `track` or `beck`),
its `stroke-width` sets the brush's width, and `stamp` lays the brush along the flattened
point list. Paths are painted in the order the file lists them, so the file is the back
to front order of the picture.

Public names: nothing new. From `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `rgb`, `composite`, `BrushStyle`, `brush_from_id`,
`stamp`, `ink_density` and `save_image`.

It writes one file, `svg_drawing.png`. Every seed is fixed, so one run writes the same
file. `size` is the picture's width in pixels; its height is two thirds of that, and the
drawing is fitted inside the sheet with a margin of bare paper.

Run it with:

    uv run python examples/svg_drawing.py out/
"""

import argparse
import logging
import re
import xml.etree.ElementTree as ET
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

STEM = "svg_drawing"
SEED = 5
#: The drawing this script reads.
DRAWING = Path(__file__).parent / "drawings" / "fell.svg"
#: How many straight segments one cubic Bezier is flattened to.
CURVE_SEGMENTS = 12
#: The pen each `class` names: a brush sheet id.
PENS = {"pen": "MAJ6-e", "track": "TRK4-d", "beck": "RIV1-a"}
#: How much of a stroke's width the brush is given; a brush's marks spread past its nominal width.
PEN_SHARE = 0.5
#: How much of the sheet's width the drawing fills; the rest is paper.
FIT = 0.88

_SVG = "{http://www.w3.org/2000/svg}"
_TOKEN = re.compile(r"[A-Za-z]|-?\d+(?:\.\d+)?")
#: How many numbers each supported command takes.
_ARITY = {"M": 2, "L": 2, "C": 6, "Z": 0}

#: A flattened subpath: its points in drawing units, and whether it was closed.
Loop = tuple[np.ndarray, bool]


def _cubic(p0: np.ndarray, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> np.ndarray:
    """Return the `CURVE_SEGMENTS` points after `p0` of a cubic Bezier, ending on `p3`."""
    t = np.linspace(0.0, 1.0, CURVE_SEGMENTS + 1)[1:, None]
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3


def parse_path(d: str) -> list[Loop]:
    """Return a path's `d` attribute as flattened subpaths.

    Args:
        d: Path data of absolute `M`, `L`, `C` and `Z` commands.

    Returns:
        One `(points, closed)` pair per subpath, the points in the path's own units.

    Raises:
        ValueError: When the data uses a command outside `M`, `L`, `C` and `Z`, or has
            the wrong number of numbers for one.
    """
    tokens = _TOKEN.findall(d)
    loops: list[tuple[list[np.ndarray], bool]] = []
    i = 0
    while i < len(tokens):
        command = tokens[i]
        if command not in _ARITY:
            raise ValueError(f"path command {command!r} is not one of M, L, C, Z")
        count = _ARITY[command]
        values = tokens[i + 1 : i + 1 + count]
        if len(values) < count or any(v.isalpha() for v in values):
            raise ValueError(f"path command {command} needs {count} numbers")
        i += 1 + count
        xy = np.array([float(v) for v in values])
        if command == "M":
            loops.append(([xy], False))
        elif command == "L":
            loops[-1][0].append(xy)
        elif command == "C":
            start = loops[-1][0][-1]
            loops[-1][0].extend(_cubic(start, xy[0:2], xy[2:4], xy[4:6]))
        else:
            loops[-1] = (loops[-1][0], True)
    return [(np.array(points), closed) for points, closed in loops]


def _nearest_pigment(fill: str) -> str:
    """Return the `PIGMENTS` key whose colour is closest to a `#rrggbb` fill."""
    target = rgb(fill)
    return min(PIGMENTS, key=lambda key: float(np.abs(rgb(PIGMENTS[key]) - target).sum()))


def _mask(loops: list[Loop], fit: tuple[float, float, float], h: int, w: int) -> np.ndarray:
    """Return the shapes as a 0-to-1 mask, drawn with Pillow's polygon fill at `fit`."""
    scale, dx, dy = fit
    image = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(image)
    for points, _ in loops:
        draw.polygon([(x * scale + dx, y * scale + dy) for x, y in points], fill=255)
    return np.asarray(image, np.float32) / 255


def main(out_dir: Path, size: int = 720) -> Path:
    """Paint the drawing, write `svg_drawing.png` into `out_dir` and return its path.

    Args:
        out_dir: The directory the image is written into.
        size: The picture's width in pixels; its height is two thirds of that.

    Returns:
        The path of the finished image, `svg_drawing.png`.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = size, size * 2 // 3
    sheet = Sheet(h, w, max(size / 120, 2.0), SEED)
    canvas = Canvas(0, 0, w, h, w, h)
    paper = paper_plate(sheet, canvas, PaperStyle(), w)

    root = ET.parse(DRAWING).getroot()
    _, _, view_w, view_h = (float(v) for v in root.attrib["viewBox"].split())
    scale = FIT * w / view_w
    fit = (scale, (w - view_w * scale) / 2, (h - view_h * scale) / 2)

    layers = []
    inks = []
    rng = np.random.default_rng(SEED)
    for element in root.iter(f"{_SVG}path"):
        loops = parse_path(element.attrib["d"])
        fill, stroke = element.get("fill", "none"), element.get("stroke", "none")
        if fill != "none":
            cover = _mask(loops, fit, h, w)
            layers.append((wash(cover, sheet, 0.85, 0.35), rgb(PIGMENTS[_nearest_pigment(fill)])))
        if stroke != "none":
            width = float(element.get("stroke-width", "1")) * scale * PEN_SHARE
            brush, ink_hex = brush_from_id(
                PENS[element.get("class", "pen")], width, 1.0, BrushStyle()
            )
            acc = np.zeros((h, w), np.float32)
            for points, _ in loops:
                stamp(acc, points * scale + np.array(fit[1:]), brush, rng)
            inks.append((ink_density(acc, brush, sheet), rgb(ink_hex)))

    out = composite([*layers, *inks], paper, PaperStyle())
    path = out_dir / f"{STEM}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path, help="the directory to write the image into")
    parser.add_argument("--size", type=int, default=720, help="the picture's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.size)
