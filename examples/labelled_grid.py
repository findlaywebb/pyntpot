"""The labelled grid: one layout, one label step and one nib-plate round trip for the grid scripts.

The five grid scripts (`tutorial_grids.py`, `nib_stages.py`, `brush_sheet.py`,
`wash_stages.py` and `how_to_route_ink.py`) each paint cells on paper and then letter the
names of the columns and rows with the hand. This sibling holds the three parts they share,
so each script keeps only what is its own: what goes in a cell, and the names.

- `GridSpec`: a frozen description of a grid's cells. `.boxes()` returns the cells as a list
  of rows, each cell `(x, y, w, h)`; `.height` is the grid's height and `.cell_w` a cell's
  width. Every size is a design value scaled by `unit` and rounded, as the scripts did
  inline, so a grid designed at one width paints at another.
- `LabelStyle`: a frozen record of how a grid's names are lettered: the font size, the label
  nib's ink and pen width, the plate's grain and seed, and the offsets from the cells.
- `letter_over`: the one nib-plate round trip. It paints the plate at `NIB_SCALE` times the
  size of an image, brings it down with Lanczos as premultiplied `RGBa`, and lays it by its
  alpha.
- `label_grid`: letters the column names above and the row names beside a grid's boxes.
- `sweep_grid`: lays one painted cell in each box of a grid over a copy of the paper, for a
  grid that sweeps one setting across and another down.
- `grid_paper`: the `paper_plate` a grid is painted on, the whole sheet with no foxing.
- `on_paper`: a cell painted over bare white with its crop of that paper multiplied in.
- `SUPERSAMPLE`, `scaled_boxes` and `reduce`: the 2x paint. A figure painted at `SUPERSAMPLE`
  times its size lays its cells in `scaled_boxes(spec, SUPERSAMPLE)`, which is each 1x box
  with all four numbers multiplied (a `GridSpec` built at twice the width would not give
  exactly twice the boxes, because `cell_w` floors). `reduce(rgb, SUPERSAMPLE)` brings the
  finished paint down once with Lanczos, as float32 clipped to 0 to 1, and the names are
  lettered after that at 1x with the 1x boxes, so a label keeps its size.
- `LABELS`: the one `LabelStyle` the line effect, setting and gallery figures letter in.

It does not paint cells, choose names or own any literal a caption or tutorial quotes: each
script keeps its label tuples and lettered names. The names stay in the order the old scripts
lettered them, columns first and then any `extra` settings and then rows, because the hand
draws each setting from one random stream and a different order is a different hand.

Public names it uses: from `pyntpot.ink`, `Canvas`, `Colour`, `BrushStyle`, `PaperStyle`,
`Sheet` and `paper_plate`;
from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`, `NibSurface`,
`NibStyle`, `NibGroups` and `nib_plate`. It introduces none.
"""

import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import BrushStyle, Canvas, Colour, PaperStyle, Sheet, paper_plate
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

#: How many times the size of an image its nib plate is painted before it is brought down.
NIB_SCALE = 2

#: How many times its display size a 2x figure is painted before `reduce` brings it down.
SUPERSAMPLE = 2

Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class GridSpec:
    """The cells of a grid: `cols` by `rows` boxes of `cell_h` pixels, spaced by `gap`.

    `width` is the grid's width in pixels. `left` and `top` are the room before the first cell
    for the rows' and columns' names, `pad_right` and `pad_bottom` the margin after the last.
    `left`, `top`, `cell_h`, `gap`, `pad_right` and `pad_bottom` are design values: each is
    multiplied by `unit` and rounded, so `unit` 1 takes them as pixels. `trailing_gap` adds
    one more `gap` after the last column and the last row. The cell width is what is left of
    `width` shared between the columns.
    """

    width: int
    cols: int
    rows: int
    cell_h: float
    left: float
    top: float
    gap: float = 14
    pad_right: float = 14
    pad_bottom: float = 14
    unit: float = 1.0
    trailing_gap: bool = False

    def _px(self, design: float) -> int:
        """Return a design value scaled by `unit` and rounded to whole pixels."""
        return round(design * self.unit)

    @property
    def cell_w(self) -> int:
        """The width of every cell, in pixels."""
        gaps = self.cols if self.trailing_gap else self.cols - 1
        room = self.width - self._px(self.left) - self._px(self.pad_right)
        return (room - self._px(self.gap) * gaps) // self.cols

    @property
    def height(self) -> int:
        """The grid's height in pixels, to the margin below the last row."""
        gaps = self.rows if self.trailing_gap else self.rows - 1
        cells = self.rows * self._px(self.cell_h) + gaps * self._px(self.gap)
        return self._px(self.top) + cells + self._px(self.pad_bottom)

    def boxes(self) -> list[list[Box]]:
        """Return the cells, a list for each row, each cell `(x, y, w, h)`."""
        left, top, gap = self._px(self.left), self._px(self.top), self._px(self.gap)
        cell_w, cell_h = self.cell_w, self._px(self.cell_h)
        return [
            [
                (left + c * (cell_w + gap), top + r * (cell_h + gap), cell_w, cell_h)
                for c in range(self.cols)
            ]
            for r in range(self.rows)
        ]


@dataclass(frozen=True)
class LabelStyle:
    """How a grid's names are lettered.

    `px` is the font size and `ink` and `pen_px` the label nib's ink and pen width. `gran_px`
    and `seed` are the plate's grain and the hand's seed. `col_dy` is how far above the first
    row a column's name sits, `row_dx` how far left of the first column a row's name ends, and
    `row_dy` how far below a row's middle its baseline falls.
    """

    px: float
    ink: Colour
    pen_px: float
    gran_px: float
    seed: int
    col_dy: float = 14
    row_dx: float = 12
    row_dy: float = 7


#: How the line effect, setting and gallery figures letter their names: one hand, the literals
#: of the tutorial grids, with the columns' names 12 pixels above the cells.
LABELS = LabelStyle(px=21.0, ink=Colour("#4a3a2a"), pen_px=1.5, gran_px=12.0, seed=7, col_dy=12)


def letter_over(
    img: np.ndarray,
    settings: Sequence[Setting],
    nib: NibStyle,
    *,
    gran_px: float,
    seed: int,
    ground: np.ndarray | None = None,
) -> np.ndarray:
    """Letter the settings over `img` with the nib and return the result.

    The nib plate is painted at `NIB_SCALE` times the size of `img`, then brought down to it
    with Lanczos, and laid over `img` by its alpha. `gran_px` is the size of the plate's
    granulation noise at that painted size and `seed` the hand's. `ground` is how dark the paint
    is under each pixel of `img`, as the nib's backing wash reads it; none means bare paper.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    h, w = img.shape[:2]
    big_w, big_h = w * NIB_SCALE, h * NIB_SCALE
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    rng = hand.generator(seed)
    marks: list[Mark] = [mark for s in settings for mark in hand.write(s, rng)]
    dark = np.zeros((h, w), np.float32) if ground is None else ground.astype(np.float32)
    dark = np.asarray(Image.fromarray(dark).resize((big_w, big_h), Image.Resampling.BILINEAR))
    canvas = Canvas(0, 0, big_w, big_h, big_w, big_h)
    surface = NibSurface(canvas, NIB_SCALE, dark, gran_px)
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


def _name(value: object) -> str:
    """A grid label's text: a float without trailing zeros, anything else as it prints."""
    return f"{value:g}" if isinstance(value, float) else str(value)


def label_grid(
    img: np.ndarray,
    boxes: list[list[Box]],
    columns: Sequence[object],
    rows: Sequence[object],
    style: LabelStyle,
    *,
    extra: Sequence[Setting] = (),
) -> np.ndarray:
    """Letter a name over each column and beside each row of a grid, and any `extra` settings.

    `boxes` is a `GridSpec.boxes()` result or a script's own, a list for each row. The settings
    are lettered in the order columns, `extra`, rows.
    """
    top, left = boxes[0][0][1], boxes[0][0][0]
    settings = [
        Setting(
            _name(text),
            style.px,
            anchor=(x + w / 2, top - style.col_dy),
            align="middle",
            wash=False,
        )
        for text, (x, _, w, _) in zip(columns, boxes[0], strict=True)
    ]
    settings += extra
    settings += [
        Setting(
            _name(text),
            style.px,
            anchor=(left - style.row_dx, row[0][1] + row[0][3] / 2 + style.row_dy),
            align="end",
            wash=False,
        )
        for text, row in zip(rows, boxes, strict=True)
    ]
    nib = NibStyle(label_ink=style.ink, label_pen_width_px=style.pen_px)
    return letter_over(img, settings, nib, gran_px=style.gran_px, seed=style.seed)


def sweep_grid(
    paper: np.ndarray,
    boxes: list[list[Box]],
    paint: Callable[[int, int, Box], np.ndarray],
) -> np.ndarray:
    """Lay one painted cell in each box of a grid over a copy of `paper` and return the result.

    `paint(row, col, box)` returns the cell for that box, a float array `(h, w, 3)` of the
    box's own size, so a sweep script holds only how one cell is painted. `paper` is the whole
    image, left bare between the cells, and is not changed.

    Raises:
        ValueError: When a painted cell is not the size of its box.
    """
    out = paper.copy()
    for r, row in enumerate(boxes):
        for c, box in enumerate(row):
            x, y, w, h = box
            cell = paint(r, c, box)
            if cell.shape[:2] != (h, w):
                raise ValueError(f"cell {r},{c} is {cell.shape[:2]}, its box is {(h, w)}")
            out[y : y + h, x : x + w] = cell
    return out


def scaled_boxes(spec: GridSpec, factor: int) -> list[list[Box]]:
    """Return the cells of `spec` with every box number multiplied by `factor`.

    This is the 1x `spec.boxes()` scaled, not a `GridSpec` built at `factor` times the width,
    whose `cell_w` floors and so would not give exactly `factor` times the boxes.
    """
    return [
        [(x * factor, y * factor, w * factor, h * factor) for x, y, w, h in row]
        for row in spec.boxes()
    ]


def reduce(rgb: np.ndarray, factor: int) -> np.ndarray:
    """Return a float `(h, w, 3)` painted at `factor` times its size, brought down once with Lanczos.

    Each channel is resampled as 32-bit float, so nothing is rounded to 8 bits. The result is
    float32, clipped to 0 to 1 (Lanczos overshoots at a hard edge).

    Raises:
        ValueError: When a side of `rgb` is not a multiple of `factor`.
    """
    h, w = rgb.shape[:2]
    if h % factor or w % factor:
        raise ValueError(f"{(h, w)} is not a multiple of {factor} on both sides")
    size = (w // factor, h // factor)
    planes = [
        np.asarray(
            Image.fromarray(rgb[..., c].astype(np.float32)).resize(size, Image.Resampling.LANCZOS)
        )
        for c in range(rgb.shape[2])
    ]
    return np.clip(np.stack(planes, axis=-1), 0.0, 1.0).astype(np.float32)


def grid_paper(sheet: Sheet) -> np.ndarray:
    """Return the `paper_plate` of the whole of `sheet`, with no foxing, at one pixel to one."""
    w, h = sheet.w, sheet.h
    return paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)


def on_paper(laid: np.ndarray, paper: np.ndarray, at: tuple[int, int]) -> np.ndarray:
    """Return a cell painted over bare white with the crop of `paper` at `at` multiplied in.

    `laid` is the cell in wash space, where the paper is 1, and `at` its top left corner on
    `paper`. The result is clipped to 0 to 1 and is float32; neither input is changed.
    """
    x, y = at
    crop = paper[y : y + laid.shape[0], x : x + laid.shape[1]]
    return np.clip(laid * crop, 0.0, 1.0).astype(np.float32)
