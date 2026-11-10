"""The setting grids: one picture painted at a range of one setting, for the pages that explain it.

Three figures, selected by `figure=`, each painted on `paper_plate` paper and lettered in the
default hand through the sibling `labelled_grid.py`. Every cell of a figure is the same picture
painted with the same seeds, so what changes from one cell to the next is the swept setting and
nothing else. `relief_grid.py` holds the fourth grid, which needs the Ambleside fixture.

- `pool`: one ultramarine disc, `wash(..., pool=)` swept across (0, 0.25, 0.6 and 1.2 of extra
  density at the edge, on a body of 0.4) and the sheet's seed down (11 and 29), on a slow mottle (`gran_px` 60).
  The pool is the pigment that gathers just inside the edge when a wash dries.
- `granulation`: the same disc with `pool` 0.25, the sheet's `gran_px` swept across (3, 6, 12
  and 24 pixels) and its `fibre` down (0, the smooth sheet, 0.35, cold press, which is
  `PaperStyle.paper_fibre_mix`'s default, and 1, a tooth that is all fibre).
- `dryness`: a `MAJ2-c` stroke 12 pixels wide, an S across the cell, with the treatment's `dry`
  swept across (0.1, 0.4, 0.7 and 0.9) and its `load` down (0.5, 3 and 8: the load is the extra
  ink where the brush is set down, and it only shows as a blot at the start of the stroke). The settings are
  `BrushStyle.brush_overrides["major"]`, and `brush_from_id` reads them with `override="major"`;
  every other treatment value is the sheet's row 2. Without `override=` the id's prefix is
  looked up, `maj`, and the setting would do nothing.

Each figure is painted at scale 1, so a cell lettered with a value shows what that value does at
one array pixel to one display pixel. The held values are literals of this script and read no
theme. `paint_cell(figure, row, col)` paints one cell and returns its float32 RGB `(h, w, 3)`
before lettering and encoding.

Public names it uses: from `pyntpot.ink`, `Sheet`, `PaperStyle`, `BrushStyle`, `wash`,
`pigment`, `rgb`, `composite`, `brush_from_id`, `stamp`, `ink_density` and `save_image`; from
`pyntpot.letters`, `Setting`; and `LABELS`, `GridSpec`, `grid_paper`, `label_grid`, `on_paper`
and `sweep_grid` from `labelled_grid.py`. It introduces none.

Run it with `uv run python examples/setting_grids.py out/ --figure pool`; it writes
`out/pool-sweep.png`.
"""

import argparse
import logging
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
from labelled_grid import LABELS, Box, GridSpec, grid_paper, label_grid, on_paper, sweep_grid

from pyntpot.ink import (
    BrushStyle,
    PaperStyle,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    pigment,
    rgb,
    save_image,
    stamp,
    wash,
)
from pyntpot.letters import Setting

logger = logging.getLogger(__name__)

#: The figures, in the order the pages show them.
FIGURES: tuple[str, ...] = ("pool", "granulation", "dryness")
#: The pool across the first figure, as the extra density at the edge, and the seeds down it.
POOLS: tuple[float, ...] = (0.0, 0.25, 0.6, 1.2)
POOL_SEEDS: tuple[int, ...] = (11, 29)
#: The granulation's cell across, in pixels, and the fibre down: smooth, cold press and the
#: whole tooth laid as fibre (the fibre's weight runs from 0 to 1).
GRAN_PXS: tuple[float, ...] = (3.0, 6.0, 12.0, 24.0)
FIBRES: tuple[float, ...] = (0.0, 0.35, 1.0)
FIBRE_NAMES: tuple[str, ...] = ("smooth", "cold press", "all fibre")
#: The dryness across, and the load down. The sheet's rows keep load between 0.4 and 1.6, where
#: it barely shows, so the sweep goes on to 8, where the set-down blot reads.
DRYNESS: tuple[float, ...] = (0.1, 0.4, 0.7, 0.9)
LOADS: tuple[float, ...] = (0.5, 3.0, 8.0)
#: The brush every dryness cell strokes, its width in pixels, and the key of its overrides.
BRUSH_ID, STROKE_PX, OVERRIDE = "MAJ2-c", 12.0, "major"

#: The seed of the paper, the bristles, the dither of the file and the held washes.
SEED = 11
#: The size of the paper's granulation noise under every figure, in pixels.
PAPER_GRAN_PX = 8.0
#: The wash disc's body density, the slow mottle's size and the granulation figure's pool.
BODY, SLOW_GRAN_PX, GRAN_POOL = 0.4, 60.0, 0.25
#: The image width, the room left of the cells and above them, the gap and the margins, in pixels.
WIDTH_PX, TOP, GAP, PAD_RIGHT, PAD_BOTTOM = 720, 44, 12, 14, 16
#: The room left of each figure's cells, for its row names.
LEFT = {"pool": 120, "granulation": 190, "dryness": 120}
#: Each figure's cell height in pixels.
CELL_H = {"pool": 120, "granulation": 120, "dryness": 76}


@dataclass(frozen=True)
class Layout:
    """What a figure letters: the names of its columns and rows, and the corner's."""

    columns: list[str]
    rows: list[str]
    corner: str


def _check(figure: str) -> None:
    """Raise `ValueError` for a figure the grids do not have."""
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")


def layout(figure: str) -> Layout:
    """Return the names of a figure's columns and rows.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    if figure == "pool":
        return Layout([f"{p:g}" for p in POOLS], [f"seed {s}" for s in POOL_SEEDS], "pool")
    if figure == "granulation":
        columns = [f"{g:g} px" for g in GRAN_PXS]
        rows = [f"{f:g} {name}" for f, name in zip(FIBRES, FIBRE_NAMES, strict=True)]
        return Layout(columns, rows, "grain")
    return Layout([f"{d:g}" for d in DRYNESS], [f"load {ld:g}" for ld in LOADS], "dry")


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
    """The paper plate of the whole figure; a cell paints over its own crop of it."""
    return grid_paper(Sheet(_spec(figure).height, WIDTH_PX, PAPER_GRAN_PX, SEED))


def _disc(w: int, h: int) -> np.ndarray:
    """A coverage mask: a disc in the middle of a cell, most of its height."""
    yy, xx = np.mgrid[0:h, 0:w]
    radius = 0.38 * h
    return (((xx - w / 2) ** 2 + (yy - h / 2) ** 2) <= radius**2).astype(np.float32)


def _washed(under: np.ndarray, sheet: Sheet, pool: float) -> np.ndarray:
    """The ultramarine disc over `under`, washed on `sheet` with `pool` at its edge."""
    h, w = under.shape[:2]
    blue = pigment("ultramarine")
    transparency = PaperStyle().km_transparency if blue.transparency is None else blue.transparency
    density = wash(_disc(w, h), sheet, BODY, pool)
    return composite([(density, rgb(blue.colour), transparency)], under, PaperStyle())


def _stroke(under: np.ndarray, dry: float, load: float) -> np.ndarray:
    """A `MAJ2-c` S-stroke over `under`, its dryness and load read through `override="major"`."""
    h, w = under.shape[:2]
    major = {**BrushStyle().brush_overrides[OVERRIDE], "dry": dry, "load": load}
    style = BrushStyle(brush_overrides={OVERRIDE: major})
    brush, ink = brush_from_id(BRUSH_ID, STROKE_PX, 1.0, style, override=OVERRIDE)
    sheet = Sheet(h, w, PAPER_GRAN_PX, SEED)
    t = np.linspace(0.0, 1.0, 80)
    line = np.column_stack([10 + t * (w - 20), h / 2 + 0.2 * h * np.sin(2 * np.pi * t)])
    acc = np.zeros((h, w), np.float32)
    stamp(acc, line, brush, np.random.default_rng(SEED))
    return composite([(ink_density(acc, brush, sheet), rgb(ink))], under, PaperStyle())


def paint_cell(figure: str, row: int, col: int, *, at: tuple[int, int] = (0, 0)) -> np.ndarray:
    """Paint one cell of a figure and return its float32 RGB `(h, w, 3)`.

    The picture is painted over bare white, then the crop of the paper plate at `at` is
    multiplied in, as the paper is laid over a wash.

    Args:
        figure: One of `FIGURES`.
        row: The row, counted from the top.
        col: The column, counted from the left.
        at: The cell's top left corner on the figure, which picks the paper's crop.

    Returns:
        The cell as float32 RGB, in 0 to 1.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    w, h = _spec(figure).cell_w, CELL_H[figure]
    white = np.ones((h, w, 3), np.float32)
    if figure == "pool":
        sheet = Sheet(h, w, SLOW_GRAN_PX, POOL_SEEDS[row])
        laid = _washed(white, sheet, POOLS[col])
    elif figure == "granulation":
        sheet = Sheet(h, w, GRAN_PXS[col], SEED, fibre=FIBRES[row])
        laid = _washed(white, sheet, GRAN_POOL)
    else:
        laid = _stroke(white, DRYNESS[col], LOADS[row])
    return on_paper(laid, _paper(figure), at)


def main(out_dir: Path, figure: str = "pool") -> Path:
    """Paint one grid and return the path of its PNG in `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: One of `FIGURES`.

    Returns:
        The path of the image, `<figure>-sweep.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    made, boxes = layout(figure), _spec(figure).boxes()

    def paint(row: int, col: int, box: Box) -> np.ndarray:
        """Paint the cell of a row and column at its box."""
        return paint_cell(figure, row, col, at=(box[0], box[1]))

    img = sweep_grid(_paper(figure), boxes, paint)
    corner = Setting(
        made.corner,
        LABELS.px,
        anchor=(boxes[0][0][0] - LABELS.row_dx, boxes[0][0][1] - LABELS.col_dy),
        align="end",
        wash=False,
    )
    labelled = label_grid(img, boxes, made.columns, made.rows, LABELS, extra=[corner])
    path = out_dir / f"{figure}-sweep.png"
    save_image(labelled, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a setting grid and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="pool", help="the grid")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure)
