"""The brush sheet: every brush id, stroked once, for the reference page.

`brush_from_id` reads a brush id such as `MAJ2-a`: a three-letter prefix, a treatment
row `1` to `8`, a hyphen and an ink colour column. `stamp` lays one stroke of each brush
along a short line and `ink_density` turns the accumulator into ink density on the
paper's tooth. The sheet has one row for each prefix and colour column and one column for
each treatment row, so a row reads left to right from row 1 to row 8. Strokes of one ink
are combined before the ink is composited over the paper.

`BRUSH_IDS` lists the ids as a literal tuple, in sheet order, because the brush tables are
private to `pyntpot.ink`; `tests/architecture/test_reference_pages.py` checks it against
those tables.

Public names it uses: `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`, `BrushStyle`,
`brush_from_id`, `stamp`, `ink_density`, `rgb`, `composite` and `save_image`, all from
`pyntpot.ink`.

Run it with `uv run python examples/brush_sheet.py out/`; it writes `out/brush_sheet.png`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
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
)

logger = logging.getLogger(__name__)

#: Every brush id, one row of eight treatments per prefix and colour column.
# fmt: off
BRUSH_IDS: tuple[str, ...] = (
    "RIV1-a", "RIV2-a", "RIV3-a", "RIV4-a", "RIV5-a", "RIV6-a", "RIV7-a", "RIV8-a",
    "STR1-a", "STR2-a", "STR3-a", "STR4-a", "STR5-a", "STR6-a", "STR7-a", "STR8-a",
    "MAJ1-a", "MAJ2-a", "MAJ3-a", "MAJ4-a", "MAJ5-a", "MAJ6-a", "MAJ7-a", "MAJ8-a",
    "MAJ1-b", "MAJ2-b", "MAJ3-b", "MAJ4-b", "MAJ5-b", "MAJ6-b", "MAJ7-b", "MAJ8-b",
    "MAJ1-c", "MAJ2-c", "MAJ3-c", "MAJ4-c", "MAJ5-c", "MAJ6-c", "MAJ7-c", "MAJ8-c",
    "MAJ1-d", "MAJ2-d", "MAJ3-d", "MAJ4-d", "MAJ5-d", "MAJ6-d", "MAJ7-d", "MAJ8-d",
    "MAJ1-e", "MAJ2-e", "MAJ3-e", "MAJ4-e", "MAJ5-e", "MAJ6-e", "MAJ7-e", "MAJ8-e",
    "LAN1-a", "LAN2-a", "LAN3-a", "LAN4-a", "LAN5-a", "LAN6-a", "LAN7-a", "LAN8-a",
    "TRK1-a", "TRK2-a", "TRK3-a", "TRK4-a", "TRK5-a", "TRK6-a", "TRK7-a", "TRK8-a",
    "TRK1-b", "TRK2-b", "TRK3-b", "TRK4-b", "TRK5-b", "TRK6-b", "TRK7-b", "TRK8-b",
    "TRK1-c", "TRK2-c", "TRK3-c", "TRK4-c", "TRK5-c", "TRK6-c", "TRK7-c", "TRK8-c",
    "TRK1-d", "TRK2-d", "TRK3-d", "TRK4-d", "TRK5-d", "TRK6-d", "TRK7-d", "TRK8-d",
    "TRK1-e", "TRK2-e", "TRK3-e", "TRK4-e", "TRK5-e", "TRK6-e", "TRK7-e", "TRK8-e",
    "TRK1-f", "TRK2-f", "TRK3-f", "TRK4-f", "TRK5-f", "TRK6-f", "TRK7-f", "TRK8-f",
)
# fmt: on

#: The treatment rows on one sheet row, and so the cells across.
COLUMNS = 8
#: One cell's width and height, and the sheet's margin, in pixels.
CELL_W, CELL_H, MARGIN = 96, 40, 16
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise, the bristles and the dither the file is written with.
SEED = 11
#: The width every brush is stroked at, in pixels.
STROKE_PX = 4.0


def _cell_line(row: int, column: int) -> np.ndarray:
    """A gentle S-shaped line across one cell of the sheet."""
    x0 = MARGIN + column * CELL_W + 8
    y0 = MARGIN + row * CELL_H + CELL_H / 2
    x = np.linspace(x0, x0 + CELL_W - 20, 60)
    return np.column_stack([x, y0 + 5.0 * np.sin(2 * np.pi * (x - x0) / (CELL_W - 20))])


def main(out_dir: Path) -> Path:
    """Stroke every brush id on the paper, write `brush_sheet.png` into `out_dir` and return its path."""
    rows = len(BRUSH_IDS) // COLUMNS
    w, h = 2 * MARGIN + COLUMNS * CELL_W, 2 * MARGIN + rows * CELL_H
    sheet = Sheet(h, w, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(), w)

    by_ink: dict[str, np.ndarray] = {}
    for index, brush_id in enumerate(BRUSH_IDS):
        brush, ink_hex = brush_from_id(brush_id, STROKE_PX, 1.0, BrushStyle())
        acc = np.zeros((h, w), np.float32)
        line = _cell_line(*divmod(index, COLUMNS))
        stamp(acc, line, brush, np.random.default_rng(SEED + index))
        density = ink_density(acc, brush, sheet)
        by_ink[ink_hex] = np.maximum(by_ink.get(ink_hex, 0.0), density)

    out = composite([(density, rgb(ink)) for ink, density in by_ink.items()], paper, PaperStyle())
    path = out_dir / "brush_sheet.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stroke every brush id and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
