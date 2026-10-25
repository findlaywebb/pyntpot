"""Explanation figures: how the hand writes a name and how the nib lays ink, a stage at a time.

`docs/explanation/the-hand-and-the-nib.md` follows one name, "Keswick", along one line,
then follows one pen stroke. Each call paints one figure, selected by `figure=`, from the
same paper seed, so what changes from one figure to the next is the stage and nothing
else.

The name, in the order the essay builds it:

- `line`: the line the name is set along, drawn with the narrow nib.
- `centreline`: the hand's marks, stroked by a nib that is one width the whole way round
  (`NibStyle.label_pen_thin` of 0).
- `broad`: the same marks with the nib as it is by default, held at an angle, so a mark
  thickens across the nib and thins along it.
- `turned`: the same marks with the nib held at the other slant (`label_pen_angle_deg`).
- `ground`: the name written on a dark wash with no backing wash (`Setting.wash` false).
- `backing`: the same name with the backing wash lifted under it.

The ink, a stroke at a time:

- `set-down`: one long pen stroke, with the blot the nib leaves where it is set down.
- `runs-dry`: the same stroke with the nib's reservoir on (`BrushStyle.pen_starve`): it
  thins and lightens as it runs down and comes back at the reload.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `rgb`, `composite`, `brush_from_id`, `stamp`,
`ink_density` and `save_image`; from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`,
`Setting`, `NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`. It introduces none.

Run it with `uv run python examples/nib_stages.py out/ --figure broad`; it writes
`out/nib-broad.png`. `--size` sets the image's width in pixels, 360 by default.
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
    "broad",
    "turned",
    "ground",
    "backing",
    "set-down",
    "runs-dry",
)
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
#: The nib's two slants, in degrees from the page's horizontal, y down.
DEFAULT_ANGLE, TURNED_ANGLE = -38.0, 38.0


def _line(w: float, h: float) -> tuple[tuple[float, float], ...]:
    """A gentle sine across the middle of the figure, in display pixels at the design width."""
    x = np.linspace(0.1 * w, 0.9 * w, 60)
    y = 0.52 * h + 0.045 * h * np.sin(2 * np.pi * (x - 0.1 * w) / (0.8 * w))
    return tuple((float(px), float(py)) for px, py in zip(x, y, strict=True))


def _ground(sheet: Sheet, w: int, h: int) -> np.ndarray:
    """The density of a dark wash across the middle band of the figure."""
    cover = np.zeros((h, w), np.float32)
    cover[int(0.2 * h) : int(0.82 * h), int(0.06 * w) : int(0.94 * w)] = 1.0
    return wash(cover, sheet, 1.0, 0.2)


def _name(figure: str, canvas: Canvas, sheet: Sheet, paper: np.ndarray, unit: float) -> np.ndarray:
    """Paint the figure's name over the paper, over a dark wash for the last two figures."""
    h = canvas.h
    on_ground = figure in {"ground", "backing"}
    ground = _ground(sheet, canvas.w, h) if on_ground else np.zeros((h, canvas.w), np.float32)
    if on_ground:
        wood = rgb(PIGMENTS["wood"])
        paper = composite([(ground, wood), (ground, wood)], paper, PaperStyle())
    if figure == "line":
        return _stroke(paper, sheet, canvas, [_line(canvas.w, h)], BrushStyle(), 1.6)
    angle = TURNED_ANGLE if figure == "turned" else DEFAULT_ANGLE
    thin = 0.0 if figure == "centreline" else NibStyle().label_pen_thin
    nib = NibStyle(label_size_px=TYPE_PX, label_pen_angle_deg=angle, label_pen_thin=thin)
    nib = replace(nib, label_pen_width_px=4.6, label_ink="#241c14", label_wash_spread=0.5)
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


def main(out_dir: Path, figure: str = "broad", size: int = DESIGN_W) -> Path:
    """Paint one figure, write it into `out_dir` as `nib-<figure>.png` and return that path.

    Args:
        out_dir: The directory the image is written into.
        figure: The figure, one of `FIGURES`.
        size: The image's width in pixels; its height is five ninths of that.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
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
    path = out_dir / f"nib-{figure}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint one nib figure and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="broad", help="the figure to paint")
    parser.add_argument("--size", type=int, default=DESIGN_W, help="the image's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
