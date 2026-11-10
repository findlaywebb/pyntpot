"""The two pictures behind the line effects essay: why an effect is not a glaze, and the draw order.

Two figures, selected by `figure=`, each painted on `paper_plate` paper at `SUPERSAMPLE` times
its size, brought down once with Lanczos, and lettered in the default hand at 1x through the
sibling `labelled_grid.py`. Every pixel number below is a display value, doubled where it is
painted.

- `glaze-or-rgb`: a two by two grid over one dark wood wash, the casing and the glow across and
  the way each is laid down. The top row lays the effect as a glaze: the ring the effect would
  cover, as the density of a cream pigment, composited by multiplying. The bottom row lays it as
  RGB, through the `casing` and `glow` primitives. A multiplied cream cannot lighten the wood,
  so the glazed rings barely show and the RGB ones do.
- `draw-order`: three cells, each a road that forks into two over a river. In "each stroke
  cased" every road is cased and then drawn, in turn, so the second road's casing cuts across
  the first road's line at the fork. In "casings first" both casings are laid, and then both
  roads, so the fork reads as one road, but the second road's ring still lies under the first
  road's glaze and shows through it. In "casings as a union" one casing is laid round the union
  of the two roads' footprints (the mask is the larger of the two densities), so there is one
  outline round the fork and no ring inside a road. All three cells lay the river first and plain.

The layers go down in one order everywhere: the wash in wash space, where the paper is 1, then
the effect with the stroke's density as its mask, then the stroke, and last the multiplication by
the `paper_plate` crop. The held values are literals of this script and read no preset. The
casings are white, so they are the paper's own colour.

`paint_cell(figure, ...)` paints one cell at the doubled size and returns its float32 RGB
`(h, w, 3)` before reduction, lettering and encoding, with `at` the cell's corner on the doubled
paper; `layout(figure)` returns the cells' settings and the names.

Public names it uses: from `pyntpot.ink`, `Casing`, `Glow`, `casing`, `glow`, `pigment`, `Colour`,
`PigmentLayer`, `Sheet`, `PaperStyle`, `BrushStyle`, `brush_from_id`, `stamp`, `ink_density`,
`wash`, `composite`, `rgb` and `save_image`; and `LABELS`, `SUPERSAMPLE`, `GridSpec`, `grid_paper`,
`label_grid`, `on_paper`, `reduce`, `scaled_boxes` and `sweep_grid` from `labelled_grid.py`. It introduces none.

Run it with `uv run python examples/line_effect_reasons.py out/ --figure draw-order`; it writes
`out/line-effects-draw-order.png`.
"""

import argparse
import logging
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
from labelled_grid import (
    LABELS,
    SUPERSAMPLE,
    GridSpec,
    grid_paper,
    label_grid,
    on_paper,
    reduce,
    scaled_boxes,
    sweep_grid,
)

from pyntpot.ink import (
    BrushStyle,
    Casing,
    Colour,
    Glow,
    PaperStyle,
    PigmentLayer,
    Sheet,
    brush_from_id,
    casing,
    composite,
    glow,
    ink_density,
    pigment,
    rgb,
    save_image,
    stamp,
    wash,
)

logger = logging.getLogger(__name__)

#: The figures, in the order the essay shows them.
FIGURES: tuple[str, ...] = ("glaze-or-rgb", "draw-order")
#: The names of the glaze-or-rgb grid: the effects across and the ways of laying them down.
EFFECTS: tuple[str, ...] = ("casing", "glow")
WAYS: tuple[str, ...] = ("glaze", "RGB")
#: The names of the draw-order cells.
ORDERS: tuple[str, ...] = ("each stroke cased", "casings first", "casings as a union")

#: The casing's colour is the paper's, and the cream the glazed rings are laid in is near it.
PAPER_WHITE, CREAM = Colour("#ffffff"), Colour("#f3e9d2")
#: The casing's width and the glow's spread, blur and strength, in pixels, and how strongly each lifts.
CASING_PX, GLOW_SPREAD_PX, GLOW_BLUR_PX, GLOW_STRENGTH = 4.0, 4.0, 5.0, 0.9
#: The draw-order casing's width in pixels.
ORDER_CASING_PX = 4.5
#: The seed of the paper's noise, the washes, the bristles, the hand and the dither of the file.
SEED = 7
#: The size of the paper's granulation and of the washes' mottle, in pixels.
GRAN_PX = 8.0
#: Each figure's width, cell height and the room left of its grid and above it, in pixels.
WIDTH_PX = 720
CELL_H = {"glaze-or-rgb": 96, "draw-order": 200}
LEFT = {"glaze-or-rgb": 100, "draw-order": 14}
TOP, GAP, PAD_RIGHT, PAD_BOTTOM = 44, 12, 14, 16


@dataclass(frozen=True)
class Layout:
    """What a figure letters: the names of its columns and rows."""

    columns: tuple[str, ...]
    rows: tuple[str, ...]


@dataclass(frozen=True)
class Stroke:
    """One stroke of a cell: its density, which is the mask an effect is laid by, and its ink as RGB."""

    density: np.ndarray
    ink: np.ndarray


def layout(figure: str) -> Layout:
    """Return the names of a figure's columns and rows.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    if figure == "glaze-or-rgb":
        return Layout(EFFECTS, WAYS)
    return Layout(ORDERS, ("",))


def _check(figure: str) -> None:
    """Raise `ValueError` for a figure the essay does not have."""
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")


@cache
def _spec(figure: str) -> GridSpec:
    """The figure's grid of cells."""
    made = layout(figure)
    return GridSpec(
        WIDTH_PX,
        len(made.columns),
        len(made.rows),
        CELL_H[figure],
        LEFT[figure],
        TOP,
        GAP,
        PAD_RIGHT,
        PAD_BOTTOM,
    )


@cache
def _paper(figure: str) -> np.ndarray:
    """The paper plate of the whole figure at `SUPERSAMPLE` times its size; a cell paints over its own crop of it."""
    big = SUPERSAMPLE
    return grid_paper(Sheet(_spec(figure).height * big, WIDTH_PX * big, GRAN_PX * big, SEED))


def _line(points: tuple[tuple[float, float], ...], n: int = 80) -> np.ndarray:
    """A smooth line through three control points, a quadratic curve of `n` points."""
    (x0, y0), (x1, y1), (x2, y2) = points
    t = np.linspace(0.0, 1.0, n)[:, None]
    p0, p1, p2 = np.array([x0, y0]), np.array([x1, y1]), np.array([x2, y2])
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t**2 * p2


def _stroke(brush_id: str, width_px: float, line: np.ndarray, sheet: Sheet, seed: int) -> Stroke:
    """A brush id's stroke along `line`: its density and its ink as RGB."""
    brush, ink = brush_from_id(brush_id, width_px, 1.0, BrushStyle())
    acc = np.zeros((sheet.h, sheet.w), np.float32)
    stamp(acc, line, brush, np.random.default_rng(seed))
    return Stroke(ink_density(acc, brush, sheet), rgb(ink))


def _washed(sheet: Sheet, *layers: tuple[str, float, float]) -> np.ndarray:
    """The wash in wash space, where the paper is 1.

    Each layer is `(pigment name, left edge, body)`: the pigment covers the sheet from the edge,
    a share of the width, to the right, at that body.
    """
    stack: list[PigmentLayer] = []
    xx = np.arange(sheet.w, dtype=np.float32)[None, :] / sheet.w
    for name, lo, body in layers:
        cover = np.broadcast_to((xx >= lo).astype(np.float32), (sheet.h, sheet.w))
        pig = pigment(name)
        km = PaperStyle().km_transparency if pig.transparency is None else pig.transparency
        stack.append((wash(cover, sheet, body, 0.0), rgb(pig.colour), km))
    return composite(stack, np.ones((sheet.h, sheet.w, 3), np.float32), PaperStyle())


def _laid(stroke: Stroke, under: np.ndarray) -> np.ndarray:
    """The stroke composited over `under`."""
    return composite([(stroke.density, stroke.ink)], under, PaperStyle())


def _glaze_or_rgb(effect: str, how: str, at: tuple[int, int]) -> np.ndarray:
    """One cell of the glaze-or-rgb grid: `effect` laid under a stroke as a `how`."""
    big = SUPERSAMPLE
    w, h = _spec("glaze-or-rgb").cell_w * big, CELL_H["glaze-or-rgb"] * big
    sheet = Sheet(h, w, GRAN_PX * big, SEED)
    line = _line(((10 * big, h * 0.6), (w / 2, h * 0.2), (w - 10 * big, h * 0.6)))
    wide = effect == "casing"
    width = (6.0 if wide else 4.0) * big
    stroke = _stroke("MAJ2-b" if wide else "RIV1-a", width, line, sheet, SEED)
    ground = _washed(sheet, *[("wood", 0.0, 0.9)] * 3)
    ring = Casing(width_px=CASING_PX * big, colour=PAPER_WHITE, strength=1.0)
    lift = Glow(spread_px=GLOW_SPREAD_PX * big, blur_px=GLOW_BLUR_PX * big, strength=GLOW_STRENGTH)

    def laid_under(base: np.ndarray) -> np.ndarray:
        """`effect` laid round the stroke over `base`, by its RGB primitive."""
        if effect == "casing":
            return casing(base, stroke.density, ring, paper=None)
        return glow(base, stroke.density, lift, paper=None)

    if how == "RGB":
        under = laid_under(ground)
    else:
        weight = laid_under(np.zeros_like(ground))[..., 0]
        under = composite([(weight, rgb(CREAM))], ground, PaperStyle())
    return on_paper(_laid(stroke, under), _paper("glaze-or-rgb"), at)


@cache
def _roads() -> tuple[Stroke, Stroke, Stroke, np.ndarray]:
    """The river, the first road, the second road and the wash, painted once at the doubled size.

    Callers must not change them.
    """
    big = SUPERSAMPLE
    w, h = _spec("draw-order").cell_w * big, CELL_H["draw-order"] * big
    sheet = Sheet(h, w, GRAN_PX * big, SEED)
    edge, road = 6 * big, 6.0 * big
    river = _stroke(
        "RIV1-a",
        5.0 * big,
        _line(((w * 0.62, edge), (w * 0.8, h * 0.5), (w * 0.7, h - edge))),
        sheet,
        3,
    )
    road_a = _stroke(
        "MAJ2-b",
        road,
        _line(((8 * big, h * 0.62), (w * 0.4, h * 0.45), (w - 8 * big, h * 0.4))),
        sheet,
        5,
    )
    road_b = _stroke(
        "MAJ2-b",
        road,
        _line(((w * 0.2, h - 8 * big), (w * 0.35, h * 0.65), (w * 0.55, h * 0.45))),
        sheet,
        9,
    )
    ground = _washed(sheet, ("farmland", 0.0, 0.8), ("wood", 0.55, 0.9), ("wood", 0.7, 0.9))
    return river, road_a, road_b, ground


def _draw_order(order: str, at: tuple[int, int]) -> np.ndarray:
    """One cell of the draw-order figure: a river, then two roads that fork, cased in `order`."""
    river, road_a, road_b, ground = _roads()
    ring = Casing(width_px=ORDER_CASING_PX * SUPERSAMPLE, colour=PAPER_WHITE, strength=1.0)
    under = _laid(river, ground)
    if order == "each stroke cased":
        for road in (road_a, road_b):
            under = _laid(road, casing(under, road.density, ring, paper=None))
    elif order == "casings first":
        for road in (road_a, road_b):
            under = casing(under, road.density, ring, paper=None)
        for road in (road_a, road_b):
            under = _laid(road, under)
    else:
        # The union's footprint is where either road's density is, so one ring goes round both.
        union = np.maximum(road_a.density, road_b.density)
        under = casing(under, union, ring, paper=None)
        for road in (road_a, road_b):
            under = _laid(road, under)
    return on_paper(under, _paper("draw-order"), at)


def paint_cell(figure: str, row: int, col: int, at: tuple[int, int] = (0, 0)) -> np.ndarray:
    """Paint one cell of a figure at the doubled size and return its float32 RGB `(h, w, 3)`.

    Args:
        figure: One of `FIGURES`.
        row: The cell's row.
        col: The cell's column.
        at: The cell's top left corner on the doubled figure, which picks the paper's crop.

    Returns:
        The cell as float32 RGB at `SUPERSAMPLE` times its size, in 0 to 1.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    made = layout(figure)
    if figure == "glaze-or-rgb":
        return _glaze_or_rgb(made.columns[col], made.rows[row], at)
    return _draw_order(made.columns[col], at)


def main(out_dir: Path, figure: str = "glaze-or-rgb") -> Path:
    """Paint one figure and return the path of its PNG in `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: One of `FIGURES`.

    Returns:
        The path of the image, `line-effects-<figure>.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    made, spec = layout(figure), _spec(figure)
    boxes = spec.boxes()
    big = sweep_grid(
        _paper(figure),
        scaled_boxes(spec, SUPERSAMPLE),
        lambda r, c, box: paint_cell(figure, r, c, (box[0], box[1])),
    )
    img = reduce(big, SUPERSAMPLE)
    labelled = label_grid(img, boxes, made.columns, made.rows, LABELS)
    path = out_dir / f"line-effects-{figure}.png"
    save_image(labelled, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Paint a line effects essay figure and write a PNG."
    )
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="glaze-or-rgb", help="the figure")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure)
