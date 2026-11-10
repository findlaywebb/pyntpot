"""Case, light and shadow one stroke, with the `pyntpot.ink` primitives alone.

One brush stroke runs across a wash of farmland and wood, painted six times, three across and two
down: plain, then cased, then lit by a glow, then shadowed, then with a reserve of bare paper round
it, and last with that reserve pooled. No map, theme or style is involved. A line effect is a
function of the colours beneath a line and the line's mask, so it works on any stroke you can draw.

Each cell lays its layers in one order: the wash, in wash space where the paper is 1; then the
effect, with the stroke's density as its mask; then the stroke over it; and last the paper plate's
crop, multiplied in. The effect goes down before the stroke, because casing, glow and reserve leave
the line's own pixels alone and a stroke laid over them keeps its colour. The casing is white, which
in wash space is the paper's own colour. A reserve lays the paper itself back and lifts the wash
beneath it, so where it is whole the cell is the bare paper plate; its pool gathers a faint edge
just outside the ring. The light is in the north-west, azimuth 315 degrees, so the shadow falls to
the south-east.

The figure is painted at `SUPERSAMPLE` times its size, every pixel number doubled, and brought down
once with Lanczos before the names are lettered at 1x, so a ring a few pixels wide has no stair
steps. The numbers below are display pixels; `paint_cell(name, at)` paints one cell at the doubled
size and returns its float32 RGB `(h, w, 3)`, before reduction, lettering and encoding, with `at`
the cell's corner on the doubled paper. The held values are literals of this script and read no
preset.

Public names it uses: from `pyntpot.ink`, `Casing`, `Glow`, `Reserve`, `Shadow`, `casing`, `glow`,
`reserve`, `shadow`, `pigment`, `Colour`, `PigmentLayer`, `Sheet`, `PaperStyle`, `BrushStyle`,
`brush_from_id`, `stamp`, `ink_density`, `wash`, `composite`, `rgb` and `save_image`; from
`pyntpot.letters`, `Setting`; and `LABELS`, `SUPERSAMPLE`, `GridSpec`, `grid_paper`, `label_grid`,
`reduce`, `scaled_boxes` and `sweep_grid` from `labelled_grid.py`. It introduces none.

Run it with `uv run python examples/cased_stroke.py out/`; it writes `out/cased_stroke.png`.
"""

import argparse
import logging
from functools import cache
from pathlib import Path

import numpy as np
from labelled_grid import (
    LABELS,
    SUPERSAMPLE,
    Box,
    GridSpec,
    grid_paper,
    label_grid,
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
    Reserve,
    Shadow,
    Sheet,
    brush_from_id,
    casing,
    composite,
    glow,
    ink_density,
    pigment,
    reserve,
    rgb,
    save_image,
    shadow,
    stamp,
    wash,
)
from pyntpot.letters import Setting

logger = logging.getLogger(__name__)

#: The six cells, three across and two down, named for the effect each lays under the stroke.
CELLS: tuple[str, ...] = ("plain", "cased", "glow", "shadow", "reserved", "reserved, pooled")
#: How many cells sit across.
ACROSS = 3
#: The casing's width in pixels, white so that it is the paper's colour.
CASING_PX, CASING_COLOUR = 2.5, Colour("#ffffff")
#: The glow's spread and blur in pixels, and how strongly it lifts.
GLOW_SPREAD_PX, GLOW_BLUR_PX, GLOW_STRENGTH = 3.0, 4.0, 0.8
#: The shadow's offset and blur in pixels, how strongly it darkens, its colour and the light's azimuth.
SHADOW_OFFSET_PX, SHADOW_BLUR_PX, SHADOW_STRENGTH = 4.0, 2.0, 0.7
SHADOW_COLOUR, AZIMUTH_DEG = pigment("paynes_grey").colour, 315.0
#: The reserve's width in pixels, and the pool of the pooled cell (the other cell has none).
RESERVE_PX, RESERVE_POOL = 3.0, 0.3
#: The brush of the stroke and its width in pixels.
BRUSH_ID, STROKE_PX = "MAJ2-b", 6.0
#: The seed of the paper's noise, the washes, the bristles, the hand and the dither of the file.
SEED = 7
#: The size of the paper's granulation and of the washes' mottle, in pixels.
GRAN_PX = 8.0
#: The image's width, a cell's height and the room round the cells, in pixels.
WIDTH_PX, CELL_H = 600, 100
LEFT, TOP, GAP, PAD_RIGHT, PAD_BOTTOM = 14, 44, 34, 14, 16

SPEC = GridSpec(
    WIDTH_PX, ACROSS, len(CELLS) // ACROSS, CELL_H, LEFT, TOP, GAP, PAD_RIGHT, PAD_BOTTOM
)


@cache
def _paper() -> np.ndarray:
    """The paper plate of the whole image at `SUPERSAMPLE` times its size, cropped by each cell."""
    big = SUPERSAMPLE
    return grid_paper(Sheet(SPEC.height * big, WIDTH_PX * big, GRAN_PX * big, SEED))


@cache
def _scene() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """The wash, the stroke's density and its ink as RGB, at `SUPERSAMPLE` times a cell's size.

    Callers must not change them.
    """
    big = SUPERSAMPLE
    w, h = SPEC.cell_w * big, CELL_H * big
    sheet = Sheet(h, w, GRAN_PX * big, SEED)
    xx = np.arange(w, dtype=np.float32)[None, :] / w
    stack: list[PigmentLayer] = []
    for name, lo, hi in (("farmland", 0.0, 0.6), ("wood", 0.4, 1.0), ("wood", 0.5, 1.0)):
        cover = np.broadcast_to(((xx >= lo) & (xx <= hi)).astype(np.float32), (h, w))
        pig = pigment(name)
        km = PaperStyle().km_transparency if pig.transparency is None else pig.transparency
        stack.append((wash(cover, sheet, 0.8, 0.0), rgb(pig.colour), km))
    ground = composite(stack, np.ones((h, w, 3), np.float32), PaperStyle())

    t = np.linspace(0.0, 1.0, 70)
    line = np.column_stack(
        [10 * big + t * (w - 20 * big), h / 2 + 0.16 * h * np.sin(2 * np.pi * t)]
    )
    brush, ink = brush_from_id(BRUSH_ID, STROKE_PX * big, 1.0, BrushStyle())
    acc = np.zeros((h, w), np.float32)
    stamp(acc, line, brush, np.random.default_rng(SEED))
    return ground, ink_density(acc, brush, sheet), rgb(ink)


def paint_cell(name: str, at: tuple[int, int] = (0, 0)) -> np.ndarray:
    """Paint one cell at `SUPERSAMPLE` times its size and return its float32 RGB `(h, w, 3)`.

    The wash, then the effect `name` through its primitive with the stroke's density as the mask,
    then the stroke, then the paper plate's crop at `at` multiplied in. Every pixel number is
    the display value times `SUPERSAMPLE`.

    Args:
        name: One of `CELLS`; `"plain"` lays no effect.
        at: The cell's top left corner on the doubled image, which picks the paper's crop.

    Returns:
        The cell as float32 RGB, in 0 to 1.

    Raises:
        ValueError: When `name` is not one of `CELLS`.
    """
    if name not in CELLS:
        raise ValueError(f"no such cell {name!r}; the cells are {', '.join(CELLS)}")
    ground, density, ink = _scene()
    px = SUPERSAMPLE
    under = ground
    if name == "cased":
        ring = Casing(width_px=CASING_PX * px, colour=CASING_COLOUR, strength=1.0)
        under = casing(ground, density, ring, paper=None)
    elif name == "glow":
        spread, blur = GLOW_SPREAD_PX * px, GLOW_BLUR_PX * px
        lift = Glow(spread_px=spread, blur_px=blur, strength=GLOW_STRENGTH)
        under = glow(ground, density, lift, paper=None)
    elif name == "shadow":
        cast = Shadow(
            offset_px=SHADOW_OFFSET_PX * px,
            blur_px=SHADOW_BLUR_PX * px,
            strength=SHADOW_STRENGTH,
            colour=SHADOW_COLOUR,
        )
        under = shadow(ground, density, cast, azimuth_deg=AZIMUTH_DEG)
    elif name in ("reserved", "reserved, pooled"):
        pool = RESERVE_POOL if name == "reserved, pooled" else 0.0
        bare = Reserve(width_px=RESERVE_PX * px, pool=pool)
        under = reserve(ground, density, bare, paper=None)
    laid = composite([(density, ink)], under, PaperStyle())
    x, y = at
    crop = _paper()[y : y + laid.shape[0], x : x + laid.shape[1]]
    return np.clip(laid * crop, 0.0, 1.0).astype(np.float32)


def _later(boxes: list[list[Box]]) -> list[Setting]:
    """The names of the rows after the first, each in the gap above its cell."""
    flat = [box for row in boxes for box in row]
    return [
        Setting(name, LABELS.px, anchor=(x + w / 2, y - LABELS.col_dy), align="middle", wash=False)
        for name, (x, y, w, _) in zip(CELLS[ACROSS:], flat[ACROSS:], strict=True)
    ]


def main(out_dir: Path) -> Path:
    """Paint the six cells and return the path of `cased_stroke.png` in `out_dir`."""
    boxes = SPEC.boxes()
    big = sweep_grid(
        _paper(),
        scaled_boxes(SPEC, SUPERSAMPLE),
        lambda r, c, box: paint_cell(CELLS[r * ACROSS + c], (box[0], box[1])),
    )
    img = reduce(big, SUPERSAMPLE)
    # `label_grid` names the first row above its cells; the second row's names sit in the gap
    # above it.
    labelled = label_grid(
        img, boxes, CELLS[:ACROSS], ("",) * len(boxes), LABELS, extra=_later(boxes)
    )
    path = out_dir / "cased_stroke.png"
    save_image(labelled, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Case, light and shadow one stroke and write a PNG."
    )
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
