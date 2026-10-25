"""The watercolour tutorial's variation grids: each rung's idea, changed in a `for` loop.

Every rung of `docs/tutorials/paint-a-watercolour.md` ends with a grid. A grid is the rung's
picture painted again for each value of the thing the rung taught, so a number you read about
is also a difference you can see. Each call paints one grid, selected by `figure=`, 720 pixels
wide, and the labels on it are lettered by the hand, nib plate painted at twice its size and
brought down with Lanczos.

The grids, in the order of the rungs:

- `paper`: `paper_tooth` 0.04, 0.085 and 0.16 across, `paper_edge` `"classic"` and `"warm"`
  down; every cell is its own piece of paper.
- `wash`: the wash body 0.3, 0.6 and 0.9 across, two `sheet_seed`s down.
- `brush`: four brushes across, each stroked at 3, 6 and 12 pixels down.
- `pigments`: four painter's pigment pairs, multiplied above and glazed by Kubelka-Munk below.
- `nib`: the nib's angle across and `label_pen_thin` down, "Keswick" written in each cell.
- `lettering`: "Keswick" written by nine hand seeds, three by three.
- `composition`: three hand seeds across, the name's backing wash off and on down.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `BrushStyle`,
`paper_plate`, `wash`, `PIGMENTS`, `PAINTERS_PIGMENTS`, `PAINTERS_TRANSPARENCY`, `rgb`,
`composite`, `brush_from_id`, `stamp`, `ink_density`, `PigmentLayer` and `save_image`; from
`pyntpot.letters`, `FaceStyle`, `HandStyle`, `Hand`, `Setting`, `Mark`, `NibSurface`,
`NibStyle`, `NibGroups` and `nib_plate`. It introduces none.

Run it with `uv run python examples/tutorial_grids.py out/ --figure nib`; it writes
`out/grid-nib.png`.
"""

import argparse
import logging
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    PAINTERS_TRANSPARENCY,
    PIGMENTS,
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

#: The grids, in the order of the rungs.
FIGURES: tuple[str, ...] = ("paper", "wash", "brush", "pigments", "nib", "lettering", "composition")
#: Every grid's width in pixels, and the gap between cells and the margin round them.
W, GAP, PAD = 720, 14, 14
#: The seed of the paper's noise, the hand and the dither the file is written with.
SEED = 7
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 6.0
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2
#: The size of a grid's labels, in pixels, and the ink they are lettered in.
LABEL_PX, LABEL_INK = 21.0, "#4a3a2a"
#: The name the lettered grids write.
NAME = "Keswick"

Box = tuple[int, int, int, int]


def _layout(cols: int, rows: int, cell_h: int, left: int, top: int) -> tuple[list[list[Box]], int]:
    """Return the cells of a grid, a list for each row, each cell `(x, y, w, h)`, and the grid's height."""
    cell_w = (W - left - PAD - GAP * (cols - 1)) // cols
    boxes = [
        [(left + c * (cell_w + GAP), top + r * (cell_h + GAP), cell_w, cell_h) for c in range(cols)]
        for r in range(rows)
    ]
    return boxes, top + rows * cell_h + (rows - 1) * GAP + PAD


def _paper(w: int, h: int, style: PaperStyle | None = None, seed: int = SEED) -> np.ndarray:
    """Paint a piece of paper `w` by `h` pixels."""
    sheet = Sheet(h, w, GRAN_PX, seed)
    return paper_plate(sheet, Canvas(0, 0, w, h, w, h), style or PaperStyle(paper_foxing=0.0), w)


def _desk(h: int) -> np.ndarray:
    """Paint the darker paper the cells of a tiled grid lie on."""
    return _paper(W, h, PaperStyle(paper_hex="#d4c8ac", paper_worn=0.0, paper_foxing=0.0), 3)


def _disc(w: int, h: int, cx: float, cy: float, radius: float) -> np.ndarray:
    """Return a disc mask `w` by `h` pixels, centred at (`cx`, `cy`)."""
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2).astype(np.float32)


def _letter(
    img: np.ndarray,
    settings: Sequence[Setting],
    nib: NibStyle,
    seed: int = SEED,
    ground: np.ndarray | None = None,
) -> np.ndarray:
    """Letter the settings over `img` with the nib and return the result.

    The nib plate is painted at `NIB_SCALE` times the size of `img`, then brought down to it
    with Lanczos, and laid over `img` by its alpha. `ground` is how dark the paint is under
    each pixel of `img`, as the nib's backing wash reads it; none means bare paper.

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
    surface = NibSurface(canvas, NIB_SCALE, dark, GRAN_PX * NIB_SCALE)
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


def _labels(
    img: np.ndarray,
    boxes: list[list[Box]],
    columns: Sequence[object],
    rows: Sequence[object],
) -> np.ndarray:
    """Letter a name over each column and beside each row of a grid."""
    top, left = boxes[0][0][1], boxes[0][0][0]
    settings = [
        Setting(
            _name(text),
            LABEL_PX,
            anchor=(x + w / 2, top - 12),
            align="middle",
            wash=False,
        )
        for text, (x, _, w, _) in zip(columns, boxes[0], strict=True)
    ]
    settings += [
        Setting(
            _name(text),
            LABEL_PX,
            anchor=(left - 12, row[0][1] + row[0][3] / 2 + 7),
            align="end",
            wash=False,
        )
        for text, row in zip(rows, boxes, strict=True)
    ]
    return _letter(img, settings, NibStyle(label_ink=LABEL_INK, label_pen_width_px=1.5))


def _paper_grid() -> np.ndarray:
    """Paint `paper_tooth` across and `paper_edge` down, each cell its own piece of paper."""
    teeth = (0.04, 0.085, 0.16)
    edges: tuple[Literal["classic", "warm"], ...] = ("classic", "warm")
    boxes, h = _layout(len(teeth), len(edges), 150, 92, 46)
    out = _desk(h)
    for r, edge in enumerate(edges):
        for c, tooth in enumerate(teeth):
            x, y, w, ch = boxes[r][c]
            style = PaperStyle(paper_tooth=tooth, paper_edge=edge)
            out[y : y + ch, x : x + w] = _paper(w, ch, style, 11)
    return _labels(out, boxes, teeth, edges)


def _wash_grid() -> np.ndarray:
    """Paint the wash body across and two `sheet_seed`s down, each cell its own piece of paper."""
    bodies, seeds = (0.3, 0.6, 0.9), (11, 23)
    boxes, h = _layout(len(bodies), len(seeds), 150, 92, 46)
    out = _desk(h)
    for r, seed in enumerate(seeds):
        for c, body in enumerate(bodies):
            x, y, w, ch = boxes[r][c]
            sheet = Sheet(ch, w, GRAN_PX, seed)
            paper = paper_plate(sheet, Canvas(0, 0, w, ch, w, ch), PaperStyle(sheet_seed=seed), w)
            density = wash(_disc(w, ch, w / 2, ch / 2, 0.36 * ch), sheet, body, 0.5)
            out[y : y + ch, x : x + w] = composite(
                [(density, rgb(PIGMENTS["water"]))], paper, PaperStyle()
            )
    return _labels(out, boxes, bodies, [f"seed {seed}" for seed in seeds])


def _brush_grid() -> np.ndarray:
    """Paint four brushes across, each at three widths down, on one sheet of paper."""
    brushes, widths = ("RIV1-a", "MAJ3-b", "TRK4-d", "MAJ7-e"), (3.0, 6.0, 12.0)
    boxes, h = _layout(len(brushes), len(widths), 80, 92, 46)
    sheet = Sheet(h, W, GRAN_PX, SEED)
    out = paper_plate(sheet, Canvas(0, 0, W, h, W, h), PaperStyle(paper_foxing=0.0), W)
    t = np.linspace(0.0, 1.0, 120)
    for r, width in enumerate(widths):
        for c, brush_id in enumerate(brushes):
            x, y, w, ch = boxes[r][c]
            brush, ink_hex = brush_from_id(brush_id, width, 1.0, BrushStyle())
            acc = np.zeros((h, W), np.float32)
            wave = y + ch / 2 + 0.26 * ch * np.sin(2 * np.pi * t)
            stamp(
                acc,
                np.column_stack([x + 12 + t * (w - 24), wave]),
                brush,
                np.random.default_rng(SEED),
            )
            out = composite([(ink_density(acc, brush, sheet), rgb(ink_hex))], out, PaperStyle())
    return _labels(out, boxes, brushes, [f"{width:g} px" for width in widths])


def _pigment_grid() -> np.ndarray:
    """Paint four pigment pairs across, multiplied above and glazed by Kubelka-Munk below."""
    pairs = (
        ("cerulean", "yellow_ochre"),
        ("quinacridone_rose", "cerulean"),
        ("yellow_ochre", "quinacridone_rose"),
        ("burnt_sienna", "cerulean"),
    )
    boxes, h = _layout(len(pairs), 2, 150, 92, 46)
    sheet = Sheet(h, W, GRAN_PX, SEED)
    out = paper_plate(sheet, Canvas(0, 0, W, h, W, h), PaperStyle(paper_foxing=0.0), W)
    for r, glazed in enumerate((False, True)):
        for c, pair in enumerate(pairs):
            x, y, w, ch = boxes[r][c]
            layers: list[PigmentLayer] = [
                (
                    wash(_disc(W, h, x + w * cx, y + ch / 2, 0.36 * ch), sheet, 0.7, 0.4),
                    rgb(PAINTERS_PIGMENTS[key]),
                    PAINTERS_TRANSPARENCY[key],
                )
                for key, cx in zip(pair, (0.36, 0.64), strict=True)
            ]
            out = composite(layers, out, PaperStyle(km_glazing=glazed))
    return _labels(out, boxes, range(1, len(pairs) + 1), ["multiply", "glazed"])


def _nib_grid() -> np.ndarray:
    """Letter a name with the nib at four angles across and three `label_pen_thin`s down."""
    angles, thins = (-38, 0, 38, 90), (0.0, 0.52, 0.85)
    boxes, h = _layout(len(angles), len(thins), 92, 92, 46)
    out = _paper(W, h)
    for r, thin in enumerate(thins):
        for c, angle in enumerate(angles):
            x, y, w, ch = boxes[r][c]
            nib = NibStyle(label_pen_angle_deg=angle, label_pen_thin=thin, label_pen_width_px=3.6)
            setting = Setting(NAME, 42.0, anchor=(w / 2, 0.68 * ch), align="middle", wash=False)
            out[y : y + ch, x : x + w] = _letter(out[y : y + ch, x : x + w], [setting], nib)
    return _labels(out, boxes, angles, thins)


def _lettering_grid() -> np.ndarray:
    """Letter a name nine times, once for each of nine hand seeds, three by three."""
    boxes, h = _layout(3, 3, 96, PAD, PAD)
    out = _paper(W, h)
    for r, row in enumerate(boxes):
        for c, (x, y, w, ch) in enumerate(row):
            setting = Setting(NAME, 56.0, anchor=(w / 2, 0.7 * ch), align="middle", wash=False)
            nib = NibStyle(label_pen_width_px=2.6)
            seed = 3 * r + c + 1
            out[y : y + ch, x : x + w] = _letter(out[y : y + ch, x : x + w], [setting], nib, seed)
    return out


def _composition_cell(w: int, h: int, seed: int, *, backing: bool) -> np.ndarray:
    """Paint a wash, a wet stroke and the name over them in one cell, and return the cell."""
    sheet = Sheet(h, w, GRAN_PX, SEED)
    paper = paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)
    density = wash(_disc(w, h, w / 2, h / 2, 0.36 * h), sheet, 0.9, 0.3)
    brush, stroke_hex = brush_from_id("RIV1-a", 4.0, 1.0, BrushStyle())
    acc = np.zeros((h, w), np.float32)
    x = np.linspace(0.08 * w, 0.92 * w, 160)
    wave = h / 2 + 0.2 * h * np.sin(2 * np.pi * x / w)
    stamp(acc, np.column_stack([x, wave]), brush, np.random.default_rng(SEED))
    stroke = ink_density(acc, brush, sheet)
    painted = composite(
        [(density, rgb(PIGMENTS["water"])), (stroke, rgb(stroke_hex))], paper, PaperStyle()
    )
    setting = Setting(NAME, 30.0, anchor=(w / 2, 0.58 * h), align="middle", wash=backing)
    nib = NibStyle(label_pen_width_px=2.0, label_wash_alpha=0.8, label_wash_spread=0.6)
    return _letter(painted, [setting], nib, seed, ground=np.maximum(density, stroke))


def _composition_grid() -> np.ndarray:
    """Paint the composition for three hand seeds across, the name's backing wash off and on down."""
    seeds, backings = (1, 2, 3), (False, True)
    boxes, h = _layout(len(seeds), len(backings), 150, 92, 46)
    out = _desk(h)
    for r, backing in enumerate(backings):
        for c, seed in enumerate(seeds):
            x, y, w, ch = boxes[r][c]
            out[y : y + ch, x : x + w] = _composition_cell(w, ch, seed, backing=backing)
    return _labels(out, boxes, [f"seed {seed}" for seed in seeds], ["off", "on"])


_PAINTERS = {
    "paper": _paper_grid,
    "wash": _wash_grid,
    "brush": _brush_grid,
    "pigments": _pigment_grid,
    "nib": _nib_grid,
    "lettering": _lettering_grid,
    "composition": _composition_grid,
}


def main(out_dir: Path, figure: str = "nib") -> Path:
    """Paint one grid, write it into `out_dir` as `grid-<figure>.png` and return that path.

    Args:
        out_dir: The directory the image is written into.
        figure: The grid, one of `FIGURES`.

    Returns:
        The path of the image.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in _PAINTERS:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out = _PAINTERS[figure]()
    path = out_dir / f"grid-{figure}.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint one tutorial grid and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="nib", help="the grid to paint")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure)
