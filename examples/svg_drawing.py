"""Painting with Python: a small SVG drawing, flat, then washed, then inked, then painted.

pyntpot does not read SVG. This script reads its own drawing, `drawings/fell.svg`, with
`xml.etree.ElementTree` and a path subset it states: the absolute commands `M`, `L`, `C`
and `Z`, with a cubic Bezier flattened to `CURVE_SEGMENTS` straight segments. Any other
command raises `ValueError`, so a drawing outside the subset fails loudly rather than
painting half of itself.

It takes `figure=` and paints one of four pictures of the same drawing, so a page can show
what each step adds:

- `flat` draws every shape in its own SVG colour with Pillow, on white, the way a browser
  would show the file. No pyntpot painting is in it.
- `washes` lays only the filled shapes as washes on paper. Each `fill` picks the nearest
  pigment of `PIGMENTS` and `PAINTERS_PIGMENTS`. A shape is painted around the shapes in
  front of it, as a painter leaves paper for the nearer hill, so a far fell does not show
  through a near one.
- `ink` lays only the stroked paths on paper. A path's `class` names a pen (`pen`, `track`
  or `beck`), its `stroke-width` sets the brush's width, and `stamp` lays the brush along
  the flattened points. Each `stroke` colour picks the nearest pigment too.
- `painting`, the default, is the washes and then the inks, on paper.

Paths are painted in the order the file lists them, so the file is the back to front order
of the picture.

Public names: nothing new. From `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS`,
`PAINTERS_TRANSPARENCY`, `rgb`, `composite`, `BrushStyle`, `brush_from_id`, `stamp`,
`ink_density` and `save_image`.

It writes one file: `svg_drawing.png` for `painting`, `svg_drawing-<figure>.png` for the
others. Every seed is fixed, so one run writes the same file. `size` is the picture's width
in pixels; its height is two thirds of that, and the drawing is fitted inside the sheet
with a margin of bare paper.

Run it with:

    uv run python examples/svg_drawing.py out/ --figure washes
"""

import argparse
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
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

STEM = "svg_drawing"
SEED = 5
#: The pictures `figure=` selects, from the plain drawing to the finished painting.
FIGURES = ("flat", "washes", "ink", "painting")
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
#: How much a wash's body and its pooled edge are laid, the same for every shape.
WASH_BODY, WASH_POOL = 0.85, 0.35
#: How far a shape's wash runs under the shape in front of it, as a share of the width, so
#: two neighbouring washes meet in a wet edge and not a gap of bare paper.
TUCK = 1 / 360
#: The supersampling of the flat drawing, which has no paper to hide hard edges in.
FLAT_SUPERSAMPLE = 3

_SVG = "{http://www.w3.org/2000/svg}"
_TOKEN = re.compile(r"[A-Za-z]|-?\d+(?:\.\d+)?")
#: How many numbers each supported command takes.
_ARITY = {"M": 2, "L": 2, "C": 6, "Z": 0}
#: Every pigment a colour in the drawing can name, and what each shows over black.
_COLOURS = {**PIGMENTS, **PAINTERS_PIGMENTS}
_TRANSPARENCY = {**TRANSPARENCY, **PAINTERS_TRANSPARENCY}

#: A flattened subpath: its points in drawing units, and whether it was closed.
Loop = tuple[np.ndarray, bool]


@dataclass(frozen=True)
class Shape:
    """One `<path>` of the drawing: where it runs and how it is coloured.

    Attributes:
        loops: The flattened subpaths, in drawing units.
        fill: The `fill` colour as `#rrggbb`, or `none`.
        stroke: The `stroke` colour as `#rrggbb`, or `none`.
        width: The `stroke-width`, in drawing units.
        pen: The `class`, naming the pen that inks it.
    """

    loops: list[Loop]
    fill: str
    stroke: str
    width: float
    pen: str


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


def read_drawing(path: Path) -> tuple[tuple[float, float], list[Shape]]:
    """Return the drawing's `viewBox` width and height, and its shapes back to front."""
    root = ET.parse(path).getroot()
    _, _, view_w, view_h = (float(v) for v in root.attrib["viewBox"].split())
    shapes = [
        Shape(
            parse_path(element.attrib["d"]),
            element.get("fill", "none"),
            element.get("stroke", "none"),
            float(element.get("stroke-width", "1")),
            element.get("class", "pen"),
        )
        for element in root.iter(f"{_SVG}path")
    ]
    return (view_w, view_h), shapes


def _nearest(colour: str) -> str:
    """Return the pigment, among `PIGMENTS` and `PAINTERS_PIGMENTS`, closest to a `#rrggbb` colour."""
    target = rgb(colour)
    return min(_COLOURS, key=lambda key: float(np.abs(rgb(_COLOURS[key]) - target).sum()))


def _points(loop: Loop, fit: tuple[float, float, float]) -> np.ndarray:
    """Return a loop's points on the sheet, a closed one ending where it began."""
    scale, dx, dy = fit
    points = loop[0] * scale + np.array([dx, dy])
    return np.vstack([points, points[:1]]) if loop[1] else points


def _flat(shapes: list[Shape], fit: tuple[float, float, float], h: int, w: int) -> np.ndarray:
    """Return the drawing as flat colour on white: each shape in its own SVG fill and stroke."""
    k = FLAT_SUPERSAMPLE
    image = Image.new("RGB", (w * k, h * k), "white")
    draw = ImageDraw.Draw(image)
    for shape in shapes:
        for loop in shape.loops:
            points = [(x * k, y * k) for x, y in _points(loop, fit)]
            if shape.fill != "none":
                draw.polygon(points, fill=shape.fill)
            if shape.stroke != "none":
                line = max(1, round(shape.width * fit[0] * k))
                draw.line(points, fill=shape.stroke, width=line, joint="curve")
    small = image.resize((w, h), Image.Resampling.LANCZOS)
    return np.asarray(small, np.float32) / 255


def _mask(shape: Shape, fit: tuple[float, float, float], h: int, w: int) -> Image.Image:
    """Return the shape's filled outline as a greyscale image, drawn with Pillow's polygon fill."""
    image = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(image)
    for loop in shape.loops:
        draw.polygon([tuple(p) for p in _points(loop, fit)], fill=255)
    return image


def _washes(
    shapes: list[Shape], fit: tuple[float, float, float], sheet: Sheet, h: int, w: int
) -> list[PigmentLayer]:
    """Return one wash per filled shape, each painted around the shapes in front of it."""
    filled = [shape for shape in shapes if shape.fill != "none"]
    tuck = ImageFilter.MinFilter(2 * max(1, round(w * TUCK)) + 1)
    masks = [_mask(shape, fit, h, w) for shape in filled]
    in_front = np.zeros((h, w), np.float32)
    layers: list[PigmentLayer] = []
    for shape, mask in zip(reversed(filled), reversed(masks), strict=True):
        cover = np.clip(np.asarray(mask, np.float32) / 255 - in_front, 0.0, 1.0)
        pigment = _nearest(shape.fill)
        layers.append(
            (
                wash(cover, sheet, WASH_BODY, WASH_POOL),
                rgb(_COLOURS[pigment]),
                _TRANSPARENCY[pigment],
            )
        )
        in_front = np.maximum(in_front, np.asarray(mask.filter(tuck), np.float32) / 255)
    return layers[::-1]


def _inks(
    shapes: list[Shape], fit: tuple[float, float, float], sheet: Sheet, h: int, w: int
) -> list[PigmentLayer]:
    """Return one ink layer per stroked shape, each stamped along its flattened points."""
    layers: list[PigmentLayer] = []
    rng = np.random.default_rng(SEED)
    for shape in shapes:
        if shape.stroke == "none":
            continue
        brush, _ = brush_from_id(
            PENS[shape.pen], shape.width * fit[0] * PEN_SHARE, 1.0, BrushStyle()
        )
        acc = np.zeros((h, w), np.float32)
        for loop in shape.loops:
            stamp(acc, _points(loop, fit), brush, rng)
        pigment = _nearest(shape.stroke)
        layers.append(
            (ink_density(acc, brush, sheet), rgb(_COLOURS[pigment]), _TRANSPARENCY[pigment])
        )
    return layers


def main(out_dir: Path, figure: str = "painting", size: int = 720) -> Path:
    """Paint one picture of the drawing, write it into `out_dir` and return its path.

    Args:
        out_dir: The directory the image is written into.
        figure: Which picture: `flat`, `washes`, `ink` or `painting`.
        size: The picture's width in pixels; its height is two thirds of that.

    Returns:
        The path of the finished image: `svg_drawing.png` for `painting`, else
        `svg_drawing-<figure>.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {FIGURES}, not {figure!r}")
    out_dir.mkdir(parents=True, exist_ok=True)
    w, h = size, size * 2 // 3
    (view_w, view_h), shapes = read_drawing(DRAWING)
    scale = FIT * w / view_w
    fit = (scale, (w - view_w * scale) / 2, (h - view_h * scale) / 2)

    if figure == "flat":
        out = _flat(shapes, fit, h, w)
    else:
        sheet = Sheet(h, w, max(size / 120, 2.0), SEED)
        style = PaperStyle(km_glazing=True)
        paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), style, w)
        layers = _washes(shapes, fit, sheet, h, w) if figure != "ink" else []
        layers += _inks(shapes, fit, sheet, h, w) if figure != "washes" else []
        out = composite(layers, paper, style)
    path = out_dir / (f"{STEM}.png" if figure == "painting" else f"{STEM}-{figure}.png")
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("out_dir", type=Path, help="the directory to write the image into")
    parser.add_argument("--figure", choices=FIGURES, default="painting", help="which picture")
    parser.add_argument("--size", type=int, default=720, help="the picture's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
