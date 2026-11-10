"""The brush gallery: every brush id stroked at 4 and at 12 pixels, a figure for each prefix group.

Three figures, selected by `figure=`, each painted on `paper_plate` paper and lettered in the
default hand through the sibling `labelled_grid.py`.

- `riv-str-lan`: `RIV`, `STR` and `LAN`. `RIV` and `STR` are one brush in one ink, so they share
  one column, lettered "RIV = STR", and each of its cells is lettered with both ids
  (`RIV1-a = STR1-a`) over one painted stroke. `LAN` is the second column. 16 cells, 24 ids.
- `maj`: `MAJ`, its five ink columns `a` to `e`.
- `trk`: `TRK`, its six ink columns `a` to `f`.

Each figure's rows are the eight treatments, lettered with their number and kind ("1 wet" to
"8 light nib"); its columns are ink colours. Each cell holds an S-shaped stroke 4 pixels wide
above one 12 pixels wide, because dryness reads only when a stroke is wide, and its id is
lettered beneath. The nib treatments (5, 6 and 8) are built through the same `brush_from_id`.
Strokes of one ink are combined before one composite, as `brush_sheet.py` does.

`PREFIX_COLUMNS` lists the colour columns of each prefix as a literal, because the brush tables
are private to `pyntpot.ink`; `tests/docs/test_reference_pages.py` pins it to those tables.
`cell_ids` and `figure_ids` say which ids a figure paints.

Public names it uses: from `pyntpot.ink`, `Sheet`, `PaperStyle`, `BrushStyle`, `brush_from_id`,
`stamp`, `ink_density`, `rgb`, `composite` and `save_image`; from `pyntpot.letters`, `Setting`;
and `LABELS`, `GridSpec`, `LabelStyle`, `grid_paper` and `label_grid` from `labelled_grid.py`.
It introduces none.

Run it with `uv run python examples/brush_gallery.py out/ --figure maj`; it writes
`out/brush-gallery-maj.png`. `--size` sets the width in pixels, 720 by default.
"""

import argparse
import dataclasses
import logging
from pathlib import Path

import numpy as np
from labelled_grid import LABELS, GridSpec, LabelStyle, grid_paper, label_grid

from pyntpot.ink import (
    BrushStyle,
    PaperStyle,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    rgb,
    save_image,
    stamp,
)
from pyntpot.letters import Setting

logger = logging.getLogger(__name__)

#: The figures, in the order the reference page shows them.
FIGURES: tuple[str, ...] = ("riv-str-lan", "maj", "trk")
#: The colour columns of each brush prefix, as letters.
PREFIX_COLUMNS: dict[str, str] = {
    "RIV": "a",
    "STR": "a",
    "MAJ": "abcde",
    "LAN": "a",
    "TRK": "abcdef",
}
#: The kind of each treatment row, 1 to 8.
KINDS: tuple[str, ...] = ("wet", "soft", "gritty", "dry", "nib", "pen", "driest", "light nib")
#: The two stroke widths of a cell, in display pixels: the narrow stroke above, the wide below.
WIDTHS_PX: tuple[float, ...] = (4.0, 12.0)
#: The width the figures are designed at, in pixels.
DESIGN_W = 720
#: The size of the paper's granulation noise, in pixels at the design width.
GRAN_PX = 8.0
#: The seed of the paper's noise, the bristles, the hand and the dither the file is written with.
SEED = 7
#: A cell's height, the gap round it (the id is lettered in the gap below), the room left of the
#: grid and above it, and the margin to its right, in pixels at the design width.
CELL_H, GAP, LEFT, TOP, PAD_RIGHT = 50, 26, 128, 44, 14
#: The size of the ids lettered under the cells, in pixels at the design width.
ID_PX = 14.0


def _columns(figure: str) -> tuple[tuple[str, ...], ...]:
    """The figure's columns, each the prefix-and-column keys (`RIV-a`) that share its one stroke."""
    if figure == "riv-str-lan":
        shared = zip(PREFIX_COLUMNS["RIV"], PREFIX_COLUMNS["STR"], strict=True)
        return (
            *((f"RIV-{a}", f"STR-{b}") for a, b in shared),
            *((f"LAN-{letter}",) for letter in PREFIX_COLUMNS["LAN"]),
        )
    prefix = figure.upper()
    return tuple((f"{prefix}-{letter}",) for letter in PREFIX_COLUMNS[prefix])


def _check(figure: str) -> None:
    """Raise `ValueError` for a figure the gallery does not have."""
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")


def cell_ids(figure: str) -> list[list[tuple[str, ...]]]:
    """The ids of each cell of a figure: a list for each treatment row, a tuple for each column.

    A cell of the `RIV = STR` column holds both ids. Raises `ValueError` for an unknown figure.
    """
    _check(figure)
    return [
        [tuple(key.replace("-", f"{row}-") for key in column) for column in _columns(figure)]
        for row in range(1, len(KINDS) + 1)
    ]


def figure_ids(figure: str) -> tuple[str, ...]:
    """Every id a figure paints, row by row. Raises `ValueError` for an unknown figure."""
    return tuple(i for row in cell_ids(figure) for cell in row for i in cell)


def _headings(figure: str) -> list[str]:
    """The lettered heading of each column: the ink column's letter, or "RIV = STR" and "LAN"."""
    if figure == "riv-str-lan":
        return ["RIV = STR", "LAN"]
    return [key[0].split("-")[1] for key in _columns(figure)]


def _scaled(style: LabelStyle, unit: float) -> LabelStyle:
    """Return `style` scaled by `unit`."""
    return dataclasses.replace(
        style,
        px=style.px * unit,
        pen_px=style.pen_px * unit,
        gran_px=style.gran_px * unit,
        col_dy=style.col_dy * unit,
        row_dx=style.row_dx * unit,
        row_dy=style.row_dy * unit,
    )


def _stroke(x: int, y: float, w: int, amplitude: float) -> np.ndarray:
    """An S-shaped line across `w` pixels from `x`, centred on `y`."""
    t = np.linspace(0.0, 1.0, 70)
    return np.column_stack([x + 8 + t * (w - 16), y + amplitude * np.sin(2 * np.pi * t)])


def _paint(figure: str, size: int) -> tuple[np.ndarray, list[list[tuple[int, int, int, int]]]]:
    """Stroke every cell of a figure on paper, and return the image and its cells' boxes."""
    unit = size / DESIGN_W
    columns, rows = _columns(figure), len(KINDS)
    spec = GridSpec(size, len(columns), rows, CELL_H, LEFT, TOP, GAP, PAD_RIGHT, 38, unit)
    boxes, h = spec.boxes(), spec.height
    sheet = Sheet(h, size, GRAN_PX * unit, SEED)
    paper = grid_paper(sheet)
    by_ink: dict[str, np.ndarray] = {}
    index = 0
    for r, row in enumerate(cell_ids(figure)):
        for c, ids in enumerate(row):
            x, y, w, cell_h = boxes[r][c]
            for width, share in zip(WIDTHS_PX, (0.26, 0.72), strict=True):
                brush, ink = brush_from_id(ids[0], width, unit, BrushStyle())
                acc = np.zeros((h, size), np.float32)
                line = _stroke(x, y + share * cell_h, w, 0.08 * cell_h)
                stamp(acc, line, brush, np.random.default_rng(SEED + index))
                index += 1
                by_ink[ink] = np.maximum(by_ink.get(ink, 0.0), ink_density(acc, brush, sheet))
    out = composite([(d, rgb(ink)) for ink, d in by_ink.items()], paper, PaperStyle())
    return out, boxes


def main(out_dir: Path, figure: str = "riv-str-lan", size: int = DESIGN_W) -> Path:
    """Paint one figure and return the path of its PNG in `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: One of `FIGURES`.
        size: The image's width in pixels.

    Returns:
        The path of the image, `brush-gallery-<figure>.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    unit = size / DESIGN_W
    out, boxes = _paint(figure, size)
    ids = [
        Setting(
            " = ".join(cell),
            ID_PX * unit,
            anchor=(x + w / 2, y + cell_h + 19 * unit),
            align="middle",
            wash=False,
        )
        for row, cells in zip(boxes, cell_ids(figure), strict=True)
        for (x, y, w, cell_h), cell in zip(row, cells, strict=True)
    ]
    rows = [f"{n} {kind}" for n, kind in enumerate(KINDS, start=1)]
    labelled = label_grid(out, boxes, _headings(figure), rows, _scaled(LABELS, unit), extra=ids)
    path = out_dir / f"brush-gallery-{figure}.png"
    save_image(labelled, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stroke a brush gallery figure and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="riv-str-lan", help="the figure")
    parser.add_argument("--size", type=int, default=DESIGN_W, help="the image's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
