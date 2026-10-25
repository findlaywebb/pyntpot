"""Explanation figures: one wash built a stage at a time, every stage from one seed.

`docs/explanation/how-the-wash-works.md` follows a single disc of water-blue wash from a
flat fill to two glazed washes. Each call paints one stage, selected by `figure=`, so the
essay can set the stages side by side; the paper's seed is the same in all of them, so
what changes from one figure to the next is the stage and nothing else.

The figures, in the order the essay builds them:

- `mask`: the coverage mask laid as a flat density, the fill a wash is not.
- `body`: `wash` with no pooled edge. The edge breaks up on the paper's noise, the tone
  drifts and the paper's tooth lightens it; the grain is a slow mottle.
- `rim`: the same wash with a pooled edge (`pool`), pigment gathered just inside the edge.
- `grain`: the same wash on a sheet with a fine grain (`gran_px`), the pigment granulating.
- `overlap`: a second wash, farmland, laid over the first and multiplied with it.
- `glaze`: a grid, not a stage. A blue stain under a warm pigment whose transparency steps
  from 0.04 to 0.9, laid by multiply in one row and glazed by Kubelka-Munk in the other, so a
  covering pigment hides the blue only where the glaze reads its transparency.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `TRANSPARENCY`, `PAINTERS_PIGMENTS`,
`PAINTERS_TRANSPARENCY`, `PigmentLayer`, `rgb`, `composite` and `save_image`; for the grid's
labels, from `pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`,
`NibSurface`, `NibStyle`, `NibGroups` and `nib_plate`. It introduces none. It does not reach the wash options that give backruns,
a bleed into a shared wet area, a flow rim or a granulation that follows the paper's pits,
because `pyntpot.ink` does not export them.

Run it with `uv run python examples/wash_stages.py out/ --figure rim`; it writes
`out/wash-rim.png`. `--size` sets the image's width in pixels, 360 by default; the `glaze`
grid is designed at 800 and scales with it.
"""

import argparse
import logging
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

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
    composite,
    paper_plate,
    rgb,
    save_image,
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
FIGURES: tuple[str, ...] = ("mask", "body", "rim", "grain", "overlap", "glaze")
#: The width the figures are designed at, in pixels; the height is two thirds of it.
DESIGN_W = 360
#: The grain's cell, in pixels at the design width: a slow mottle, then a fine grain.
SLOW_GRAN_PX, FINE_GRAN_PX = 60.0, 6.0
#: The seed of the paper's noise and of the dither the file is written with.
SEED = 11
#: The body density of each wash and the extra the pooled edge adds.
BODY, POOL = 0.8, 0.55
#: The glaze grid: its design width, the transparencies it steps through across, and its
#: cell height as a share of the width.
GRID_W, STEPS, CELL_H = 800, (0.04, 0.2, 0.5, 0.9), 0.17
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2


def _disc(w: int, h: int, centre_x: float) -> np.ndarray:
    """A coverage mask: a disc halfway down, `centre_x` of the way across."""
    return _circle(w, h, centre_x * w, h / 2, 0.34 * min(w, h))


def _circle(w: int, h: int, cx: float, cy: float, radius: float) -> np.ndarray:
    """A coverage mask `w` by `h` pixels: a disc of `radius` pixels centred at (`cx`, `cy`)."""
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2).astype(np.float32)


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
    surface = NibSurface(big, NIB_SCALE, dark, SLOW_GRAN_PX * w / DESIGN_W)
    nib = NibStyle(label_ink="#3a2c20", label_pen_width_px=1.5 * w / GRID_W)
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


def _glaze_grid(size: int) -> np.ndarray:
    """Paint a blue stain under a warm pigment at four transparencies, multiplied above and glazed below."""
    unit = size / GRID_W
    left, top, gap = round(110 * unit), round(52 * unit), round(12 * unit)
    cell_w = (size - left - gap * len(STEPS)) // len(STEPS)
    cell_h = round(CELL_H * size)
    h = top + 2 * cell_h + gap + round(14 * unit)
    sheet = Sheet(h, size, SLOW_GRAN_PX * unit / 2, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, size, h, size, h), PaperStyle(paper_foxing=0.0), size)

    out = paper
    blue, warm = rgb(PAINTERS_PIGMENTS["ultramarine"]), rgb(PAINTERS_PIGMENTS["burnt_sienna"])
    cell_sheet = Sheet(cell_h, cell_w, SLOW_GRAN_PX * unit / 2, SEED)
    under = wash(
        _circle(cell_w, cell_h, 0.4 * cell_w, cell_h / 2, 0.34 * cell_h), cell_sheet, 0.8, 0.4
    )
    over = wash(
        _circle(cell_w, cell_h, 0.62 * cell_w, cell_h / 2, 0.34 * cell_h), cell_sheet, 0.9, 0.4
    )
    for row in range(2):
        for col, transparency in enumerate(STEPS):
            x0, y0 = left + col * (cell_w + gap), top + row * (cell_h + gap)
            layers: list[PigmentLayer] = [
                (under, blue, PAINTERS_TRANSPARENCY["ultramarine"]),
                (over, warm, transparency),
            ]
            cell = out[y0 : y0 + cell_h, x0 : x0 + cell_w]
            out[y0 : y0 + cell_h, x0 : x0 + cell_w] = composite(
                layers, cell, PaperStyle(km_glazing=row == 1)
            )
    px = 21.0 * unit
    labels = [
        Setting(
            f"{t:g}",
            px,
            anchor=(left + c * (cell_w + gap) + cell_w / 2, top - 14 * unit),
            align="middle",
            wash=False,
        )
        for c, t in enumerate(STEPS)
    ]
    labels += [
        Setting(
            name,
            px,
            anchor=(left - 12 * unit, top + r * (cell_h + gap) + cell_h / 2 + 7 * unit),
            align="end",
            wash=False,
        )
        for r, name in enumerate(("multiply", "glazed"))
    ]
    return _letter(out, labels)


def main(out_dir: Path, figure: str = "rim", size: int = DESIGN_W) -> Path:
    """Paint one stage of the wash, write it into `out_dir` as `wash-<figure>.png` and return that path.

    Args:
        out_dir: The directory the image is written into.
        figure: The stage, one of `FIGURES`.
        size: The image's width in pixels; its height is two thirds of that, except for
            the `glaze` grid, whose height follows its rows.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    path = out_dir / f"wash-{figure}.png"
    if figure == "glaze":
        save_image(_glaze_grid(size), path, seed=SEED)
        logger.info("wrote %s", path)
        return path
    w, h = size, size * 2 // 3
    unit = size / DESIGN_W
    gran = (FINE_GRAN_PX if figure in {"grain", "overlap"} else SLOW_GRAN_PX) * unit
    sheet = Sheet(h, w, gran, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)
    pool = POOL if figure != "body" else 0.0

    blue = _disc(w, h, 0.5 if figure in {"mask", "body", "rim", "grain"} else 0.4)
    density = blue * BODY if figure == "mask" else wash(blue, sheet, BODY, pool)
    layers: list[PigmentLayer] = [(density, rgb(PIGMENTS["water"]), TRANSPARENCY["water"])]
    if figure == "overlap":
        green = wash(_disc(w, h, 0.62), sheet, BODY, POOL)
        layers.append((green, rgb(PIGMENTS["farmland"]), TRANSPARENCY["farmland"]))

    out = composite(layers, paper, PaperStyle())
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint one stage of a wash and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="rim", help="the stage to paint")
    parser.add_argument("--size", type=int, default=DESIGN_W, help="the image's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
