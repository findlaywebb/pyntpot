"""The brush sheet: every brush id, stroked once, and the treatments by width, for the reference page.

Two figures, selected by `figure=`. `sheet` strokes every id; `grid` strokes one ink's eight
treatments at three widths, 3, 6 and 12 pixels, with the treatment numbers and their kinds
lettered, because a stroke four pixels wide hides what a treatment does and a twelve-pixel one
shows it.

`brush_from_id` reads a brush id such as `MAJ2-a`: a three-letter prefix, a treatment
row `1` to `8`, a hyphen and an ink colour column. `stamp` lays one stroke of each brush
along a short line and `ink_density` turns the accumulator into ink density on the
paper's tooth. The sheet has one row for each prefix and colour column and one column for
each treatment row, so a row reads left to right from row 1 to row 8. Strokes of one ink
are combined before the ink is composited over the paper.

`BRUSH_IDS` lists the ids as a literal tuple, in sheet order, because the brush tables are
private to `pyntpot.ink`; `tests/architecture/test_reference_pages.py` checks it against
those tables.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`,
`BrushStyle`, `brush_from_id`, `stamp`, `ink_density`, `rgb`, `composite` and `save_image`; for
the grid's lettering, from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`,
`NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`.

Run it with `uv run python examples/brush_sheet.py out/ --figure grid`; it writes
`out/brush_grid.png`. The `sheet` figure writes `out/brush_sheet.png`.
"""

import argparse
import logging
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

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
from pyntpot.letters import (
    FaceStyle,
    Hand,
    HandStyle,
    Mark,
    NibGroups,
    NibStyle,
    NibSurface,
    Setting,
    nib_plate,
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

#: The figures, the sheet of every id and the grid of one ink's treatments by width.
FIGURES: tuple[str, ...] = ("sheet", "grid")
#: The grid's width, its widths of stroke, the ink column it strokes and the treatments' kinds.
GRID_W, GRID_WIDTHS, GRID_INK = 960, (3.0, 6.0, 12.0), "MAJ{row}-c"
KINDS = ("wet", "soft", "gritty", "dry", "nib", "pen", "driest", "fine nib")
#: The grid's cell height, left margin, top margin and gap, in pixels.
GRID_CELL_H, GRID_LEFT, GRID_TOP, GRID_GAP = 84, 74, 44, 8
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2
#: The size of the grid's labels, in pixels.
LABEL_PX = 20.0


def _cell_line(row: int, column: int) -> np.ndarray:
    """A gentle S-shaped line across one cell of the sheet."""
    x0 = MARGIN + column * CELL_W + 8
    y0 = MARGIN + row * CELL_H + CELL_H / 2
    x = np.linspace(x0, x0 + CELL_W - 20, 60)
    return np.column_stack([x, y0 + 5.0 * np.sin(2 * np.pi * (x - x0) / (CELL_W - 20))])


def _sheet(out_dir: Path) -> Path:
    """Stroke every brush id on the paper, write `brush_sheet.png` into `out_dir` and return its path."""
    rows = len(BRUSH_IDS) // COLUMNS
    w, h = 2 * MARGIN + COLUMNS * CELL_W, 2 * MARGIN + rows * CELL_H
    sheet = Sheet(h, w, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)

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


def _letter(img: np.ndarray, settings: list[Setting]) -> np.ndarray:
    """Letter the settings over `img`, the plate painted at `NIB_SCALE` times and brought down with Lanczos.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    h, w = img.shape[:2]
    big = Canvas(0, 0, w * NIB_SCALE, h * NIB_SCALE, w * NIB_SCALE, h * NIB_SCALE)
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    rng = hand.generator(SEED)
    marks: list[Mark] = [mark for s in settings for mark in hand.write(s, rng)]
    dark = np.zeros((h * NIB_SCALE, w * NIB_SCALE), np.float32)
    surface = NibSurface(big, NIB_SCALE, dark, GRAN_PX * NIB_SCALE)
    nib = NibStyle(label_ink="#3a2c20", label_pen_width_px=1.5)
    groups = NibGroups(nib, face, hand_style, BrushStyle(), PaperStyle())
    with tempfile.TemporaryDirectory() as scratch:
        written = nib_plate(marks, surface, groups, Path(scratch) / "plate.webp")
        if written is None:
            raise RuntimeError("the hand wrote no marks")
        with Image.open(written) as plate:
            small = plate.convert("RGBa").resize((w, h), Image.Resampling.LANCZOS)
            rgba = np.asarray(small.convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    return img * (1 - alpha) + rgba[..., :3] * alpha


def _grid(out_dir: Path) -> Path:
    """Stroke the eight treatments of one ink at three widths, write `brush_grid.png` into `out_dir` and return its path."""
    cell_w = (GRID_W - GRID_LEFT - MARGIN - GRID_GAP * (COLUMNS - 1)) // COLUMNS
    h = GRID_TOP + len(GRID_WIDTHS) * (GRID_CELL_H + GRID_GAP) + 34
    sheet = Sheet(h, GRID_W, GRAN_PX, SEED)
    paper = paper_plate(
        sheet, Canvas(0, 0, GRID_W, h, GRID_W, h), PaperStyle(paper_foxing=0.0), GRID_W
    )

    by_ink: dict[str, np.ndarray] = {}
    for r, width in enumerate(GRID_WIDTHS):
        for c in range(COLUMNS):
            brush, ink_hex = brush_from_id(GRID_INK.format(row=c + 1), width, 1.0, BrushStyle())
            x0 = GRID_LEFT + c * (cell_w + GRID_GAP) + 8
            y0 = GRID_TOP + r * (GRID_CELL_H + GRID_GAP) + GRID_CELL_H / 2
            t = np.linspace(0.0, 1.0, 80)
            line = np.column_stack(
                [x0 + t * (cell_w - 16), y0 + 0.28 * GRID_CELL_H * np.sin(2 * np.pi * t)]
            )
            acc = np.zeros((h, GRID_W), np.float32)
            stamp(acc, line, brush, np.random.default_rng(SEED + 8 * r + c))
            by_ink[ink_hex] = np.maximum(by_ink.get(ink_hex, 0.0), ink_density(acc, brush, sheet))
    out = composite([(density, rgb(ink)) for ink, density in by_ink.items()], paper, PaperStyle())

    centres = [GRID_LEFT + c * (cell_w + GRID_GAP) + cell_w / 2 for c in range(COLUMNS)]
    labels = [
        Setting(str(c + 1), LABEL_PX, anchor=(x, GRID_TOP - 14), align="middle", wash=False)
        for c, x in enumerate(centres)
    ]
    labels += [
        Setting(KINDS[c], LABEL_PX - 3, anchor=(x, h - 12), align="middle", wash=False)
        for c, x in enumerate(centres)
    ]
    labels += [
        Setting(
            f"{width:g} px",
            LABEL_PX,
            anchor=(GRID_LEFT - 12, GRID_TOP + r * (GRID_CELL_H + GRID_GAP) + GRID_CELL_H / 2 + 7),
            align="end",
            wash=False,
        )
        for r, width in enumerate(GRID_WIDTHS)
    ]
    path = out_dir / "brush_grid.png"
    save_image(_letter(out, labels), path, seed=SEED)
    logger.info("wrote %s", path)
    return path


def main(out_dir: Path, figure: str = "sheet") -> Path:
    """Paint one figure and return the path of its PNG in `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: `sheet`, every id stroked once, or `grid`, one ink's treatments by width.

    Returns:
        The path of the image, `brush_sheet.png` or `brush_grid.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    return _sheet(out_dir) if figure == "sheet" else _grid(out_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stroke the brush ids and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="sheet", help="the figure to paint")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure)
