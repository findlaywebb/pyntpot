"""Explanation figures: how the hand writes a name and how the nib lays ink, a stage at a time.

`docs/explanation/the-hand-and-the-nib.md` follows one name, "Keswick", along one line,
then follows one pen stroke. Each call paints one figure, selected by `figure=`, from the
same paper seed, so what changes from one figure to the next is the stage and nothing
else.

The name, in the order the essay builds it:

- `line`: the line the name is set along, drawn with the narrow nib.
- `centreline`: the hand's marks, stroked by a nib that is one width the whole way round
  (`NibStyle.label_pen_thin` of 0).
- `angles`: a grid, not a stage: the same name written with the nib held at four angles
  (`label_pen_angle_deg`) across and thinned by three amounts (`label_pen_thin`) down, so a
  mark thickens across the nib and thins along it, and the thick and thin strokes change places
  as the nib turns. The first row is one width the whole way round.
- `ground`: the name written on a dark, irregular wash with no backing wash (`Setting.wash`
  false).
- `backing`: the same name with the backing wash lifted under it.
- `hands`: a grid: the same name written by nine hand seeds, three by three.

The ink, a stroke at a time:

- `set-down`: one long pen stroke, with the blot the nib leaves where it is set down.
- `runs-dry`: the same stroke with the nib's reservoir on (`BrushStyle.pen_starve`): it
  thins and lightens as it runs down and comes back at the reload.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate`, `wash`, `PAINTERS_PIGMENTS`, `rgb`, `composite`, `brush_from_id`, `stamp`,
`ink_density` and `save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`,
`Setting`, `NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`. It introduces none.

Run it with `uv run python examples/nib_stages.py out/ --figure angles`; it writes
`out/nib-angles.png`. `--size` sets the image's width in pixels, 360 by default; the two
grids, `angles` and `hands`, are designed at 900 and scale with it.
"""

import argparse
import logging
import tempfile
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
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

#: The figures, in the order the essay builds them.
FIGURES: tuple[str, ...] = (
    "line",
    "centreline",
    "angles",
    "ground",
    "backing",
    "set-down",
    "runs-dry",
    "hands",
)
#: The grids, `angles` and `hands`: the width they are designed at, in pixels.
GRID_W = 900
#: The nib's angles across the `angles` grid, and the thinnings down it.
ANGLES, THINS = (-38.0, 0.0, 38.0, 90.0), (0.0, 0.52, 0.85)
#: How many times its size a grid's nib plate is painted before it is brought down.
NIB_SCALE = 2
#: The width the figures are designed at, in pixels; the height is five ninths of it.
DESIGN_W = 360
#: How many times larger the nib plate is painted than the figure, before it is downsized.
NIB_SCALE = 2
#: The size of the paper's granulation noise, in pixels at the design width.
GRAN_PX = 3.0
#: The seed of the paper's noise, the hand, the nib and the dither the file is written with.
SEED = 7
#: The name the hand writes, and its type size in display pixels at the design width.
NAME, TYPE_PX = "Keswick", 84.0
#: The nib's default slant, in degrees from the page's horizontal, y down.
DEFAULT_ANGLE = -38.0


def _line(w: float, h: float) -> tuple[tuple[float, float], ...]:
    """A gentle sine across the middle of the figure, in display pixels at the design width."""
    x = np.linspace(0.1 * w, 0.9 * w, 60)
    y = 0.52 * h + 0.045 * h * np.sin(2 * np.pi * (x - 0.1 * w) / (0.8 * w))
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def _ground(sheet: Sheet, w: int, h: int) -> np.ndarray:
    """The density of a dark, irregular wash of sap green under the middle of the figure, pooled at its edge."""
    yy, xx = np.mgrid[0:h, 0:w]
    dx, dy = (xx - 0.5 * w) / (0.43 * w), (yy - 0.52 * h) / (0.4 * h)
    angle = np.arctan2(dy, dx)
    reach = (
        1.0
        + 0.1 * np.sin(3 * angle + 1.0)
        + 0.06 * np.sin(5 * angle + 2.3)
        + 0.04 * np.sin(8 * angle)
    )
    cover = (np.hypot(dx, dy) <= reach).astype(np.float32)
    return wash(cover, sheet, 1.0, 0.6)


def _name(figure: str, canvas: Canvas, sheet: Sheet, paper: np.ndarray, unit: float) -> np.ndarray:
    """Paint the figure's name over the paper, over a dark wash for the last two figures."""
    h = canvas.h
    on_ground = figure in {"ground", "backing"}
    ground = _ground(sheet, canvas.w, h) if on_ground else np.zeros((h, canvas.w), np.float32)
    if on_ground:
        paper = composite([(ground, rgb(PAINTERS_PIGMENTS["sap_green"]))], paper, PaperStyle())
    if figure == "line":
        return _stroke(paper, sheet, canvas, [_line(canvas.w, h)], BrushStyle(), 1.6)
    thin = 0.0 if figure == "centreline" else NibStyle().label_pen_thin
    nib = NibStyle(label_size_px=TYPE_PX, label_pen_angle_deg=DEFAULT_ANGLE, label_pen_thin=thin)
    nib = replace(nib, label_pen_width_px=4.6, label_ink="#241c14", label_wash_spread=0.35)
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    setting = Setting(NAME, TYPE_PX, path=_line(canvas.w / unit, h / unit), wash=figure != "ground")
    marks = hand.write(setting, hand.generator(SEED))
    big = Canvas(
        0, 0, NIB_SCALE * canvas.w, NIB_SCALE * canvas.h, NIB_SCALE * canvas.w, NIB_SCALE * canvas.h
    )
    dark2 = np.repeat(np.repeat(ground, NIB_SCALE, axis=0), NIB_SCALE, axis=1)
    surface = NibSurface(big, NIB_SCALE * unit, dark2, GRAN_PX * NIB_SCALE * unit)
    groups = NibGroups(nib, face, hand_style, BrushStyle(), PaperStyle())
    return _lay_plate(marks, surface, groups, paper)


def _lay_plate(
    marks: Sequence[Mark], surface: NibSurface, groups: NibGroups, paper: np.ndarray
) -> np.ndarray:
    """Stroke the marks onto one RGBA plate and lay it over the paper by its alpha."""
    with tempfile.TemporaryDirectory() as scratch:
        written = nib_plate(marks, surface, groups, Path(scratch) / "plate.webp")
        if written is None:
            raise RuntimeError("the hand wrote no marks")
        with Image.open(written) as plate:
            size = (surface.canvas.w // NIB_SCALE, surface.canvas.h // NIB_SCALE)
            small = plate.convert("RGBA").resize(size, Image.Resampling.LANCZOS)
    rgba = np.asarray(small, np.float32) / 255
    alpha = rgba[..., 3:]
    return paper * (1 - alpha) + rgba[..., :3] * alpha


def _stroke(
    paper: np.ndarray,
    sheet: Sheet,
    canvas: Canvas,
    lines: list[tuple[tuple[float, float], ...]],
    style: BrushStyle,
    width_px: float,
) -> np.ndarray:
    """Stamp each line with the pen nib, read the ink back on the paper and lay it over `paper`."""
    unit = canvas.w / DESIGN_W
    brush, ink_hex = brush_from_id("MAJ6-e", width_px, unit, style)
    acc = np.zeros((canvas.h, canvas.w), np.float32)
    rng = np.random.default_rng(SEED)
    for line in lines:
        stamp(acc, np.asarray(line, np.float64) * unit, brush, rng)
    return composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], paper, PaperStyle())


def _pen_line(w: float, h: float) -> tuple[tuple[float, float], ...]:
    """A long wavy line for the pen stroke, in display pixels at the design width."""
    x = np.linspace(0.08 * w, 0.92 * w, 400)
    y = 0.5 * h + 0.2 * h * np.sin(2 * np.pi * 2 * (x - 0.08 * w) / (0.84 * w))
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def _letter(img: np.ndarray, settings: list[Setting], nib: NibStyle, seed: int) -> np.ndarray:
    """Letter the settings over `img`, the plate painted at `NIB_SCALE` times and brought down with Lanczos.

    Raises:
        RuntimeError: When the hand wrote no marks, so there is no plate to lay.
    """
    h, w = img.shape[:2]
    big = Canvas(0, 0, w * NIB_SCALE, h * NIB_SCALE, w * NIB_SCALE, h * NIB_SCALE)
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    rng = hand.generator(seed)
    marks: list[Mark] = [mark for s in settings for mark in hand.write(s, rng)]
    dark = np.zeros((h * NIB_SCALE, w * NIB_SCALE), np.float32)
    surface = NibSurface(big, NIB_SCALE, dark, GRAN_PX * NIB_SCALE * w / GRID_W)
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


def _cells(
    size: int, cols: int, rows: int, cell_h: int, left: int, top: int
) -> tuple[list[tuple[int, int, int, int]], int]:
    """Return a grid's cells row by row as `(x, y, w, h)` and its height, from sizes at `GRID_W`."""
    unit, gap = size / GRID_W, round(12 * size / GRID_W)
    left, top, cell_h = round(left * unit), round(top * unit), round(cell_h * unit)
    cell_w = (size - left - gap * cols) // cols
    boxes = [
        (left + c * (cell_w + gap), top + r * (cell_h + gap), cell_w, cell_h)
        for r in range(rows)
        for c in range(cols)
    ]
    return boxes, top + rows * (cell_h + gap)


def _angles_grid(size: int) -> np.ndarray:
    """Letter the name with the nib at four angles across and three `label_pen_thin`s down, on one sheet."""
    unit = size / GRID_W
    boxes, h = _cells(size, len(ANGLES), len(THINS), 108, 110, 54)
    sheet = Sheet(h, size, GRAN_PX * unit, SEED)
    out = paper_plate(sheet, Canvas(0, 0, size, h, size, h), PaperStyle(paper_foxing=0.0), size)
    px = 22.0 * unit
    for (x, y, w, ch), (thin, angle) in zip(
        boxes, [(t, a) for t in THINS for a in ANGLES], strict=True
    ):
        nib = NibStyle(
            label_pen_angle_deg=angle,
            label_pen_thin=thin,
            label_pen_width_px=3.4 * unit,
            label_ink="#241c14",
        )
        setting = Setting(NAME, 52.0 * unit, anchor=(w / 2, 0.7 * ch), align="middle", wash=False)
        out[y : y + ch, x : x + w] = _letter(out[y : y + ch, x : x + w], [setting], nib, SEED)
    labels = [
        Setting(f"{a:g}", px, anchor=(x + w / 2, 38 * unit), align="middle", wash=False)
        for a, (x, _, w, _) in zip(ANGLES, boxes, strict=False)
    ]
    labels += [
        Setting(f"{t:g}", px, anchor=(96 * unit, y + ch / 2 + 7 * unit), align="end", wash=False)
        for t, (_, y, _, ch) in zip(THINS, boxes[:: len(ANGLES)], strict=True)
    ]
    return _letter(out, labels, NibStyle(label_ink="#3a2c20", label_pen_width_px=1.6 * unit), SEED)


def _hands_grid(size: int) -> np.ndarray:
    """Letter the name nine times, once for each of nine hand seeds, three by three."""
    unit = size / GRID_W
    boxes, h = _cells(size, 3, 3, 104, 12, 12)
    sheet = Sheet(h, size, GRAN_PX * unit, SEED)
    out = paper_plate(sheet, Canvas(0, 0, size, h, size, h), PaperStyle(paper_foxing=0.0), size)
    nib = NibStyle(label_pen_width_px=2.8 * unit, label_ink="#241c14")
    for seed, (x, y, w, ch) in enumerate(boxes, start=1):
        setting = Setting(NAME, 68.0 * unit, anchor=(w / 2, 0.7 * ch), align="middle", wash=False)
        out[y : y + ch, x : x + w] = _letter(out[y : y + ch, x : x + w], [setting], nib, seed)
    return out


def main(out_dir: Path, figure: str = "angles", size: int = DESIGN_W) -> Path:
    """Paint one figure, write it into `out_dir` as `nib-<figure>.png` and return that path.

    Args:
        out_dir: The directory the image is written into.
        figure: The figure, one of `FIGURES`.
        size: The image's width in pixels; its height is five ninths of that, except for the
            grids, `angles` and `hands`, whose height follows their rows.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    path = out_dir / f"nib-{figure}.png"
    if figure in {"angles", "hands"}:
        save_image(_angles_grid(size) if figure == "angles" else _hands_grid(size), path, seed=SEED)
        logger.info("wrote %s", path)
        return path
    w, h = size, size * 5 // 9
    unit = size / DESIGN_W
    sheet = Sheet(h, w, GRAN_PX * unit, SEED)
    canvas = Canvas(0, 0, w, h, w, h)
    paper = paper_plate(sheet, canvas, PaperStyle(paper_foxing=0.0), w)
    if figure in {"set-down", "runs-dry"}:
        style = BrushStyle(
            pen_starve=figure == "runs-dry", pen_reservoir=22.0, pen_thin=1.0, ink_dip_mult=1.4
        )
        out = _stroke(paper, sheet, canvas, [_pen_line(w / unit, h / unit)], style, 5.0)
    else:
        out = _name(figure, canvas, sheet, paper, unit)
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint one nib figure and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="angles", help="the figure to paint")
    parser.add_argument("--size", type=int, default=DESIGN_W, help="the image's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
