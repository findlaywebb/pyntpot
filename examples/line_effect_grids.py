"""The line effect sweeps: one stroke over a wash, with one effect swept across and down.

Four figures, selected by `figure=`, each painted on `paper_plate` paper and lettered in the
default hand through the sibling `labelled_grid.py`. Every cell holds the same wash and the same
stroke, so what changes from one cell to the next is the effect and nothing else.

- `casing`: a `MAJ2-b` road, 6 pixels wide, over a farmland and wood wash. The casing's width
  across (0, 1, 2, 3 and 5 pixels) and its colour down (the paper's, and Payne's grey).
- `glow`: an `RIV1-a` river, 4 pixels wide, over a dark wood wash. A cell with no glow, then the
  glow's spread across (0, 2, 4 and 6 pixels) and its blur down (0, 3 and 6 pixels).
- `shadow`: a solid `#c22050` line, 4 pixels wide, over farmland. A cell with no shadow, then the
  shadow's offset across (0, 1.5, 3 and 5 pixels) and its blur down (1 and 3 pixels). The light
  is in the north-west, so the shadow falls to the south-east.
- `pen-casing`: a 1.5 pixel ink line over a grey tint. A cell with no casing, then the reserve's
  gap across (1, 2, 3 and 4 pixels) and the ink edge lines' width down (0.75 and 1.5 pixels).

Each sweep is painted at scale 1: one array pixel is one display pixel, so a cell lettered "2 px"
shows what `width_px: 2` (or `spread_px`, `blur_px`, `offset_px`) does in a theme at scale 1. The
effects are laid in wash space, where the paper is 1, before the paper plate multiplies, so a
casing in the paper's own colour becomes the paper's cream and never a white ring.

The wash and the stroke every cell shares are painted by the sibling `line_effect_scenes.py`;
this script holds the layout, the effects and the lettering.

`paint_cell(figure, ...)` paints one cell and returns its float32 RGB `(h, w, 3)` before lettering
and encoding: the wash, the effect through its `pyntpot.ink` primitive with the stroke's density
as the mask, the stroke, then the crop of the paper plate at `at`. With `plain=True` it paints
the stroke with no primitive called (for the pen casing, the tint and the centre line). A sweep's
off cell is the plain stroke byte for byte. `stroke_density(figure)` is the stroke's mask.

The held values here are literals of this script and read no preset. Each swept axis is one
numeric tuple, so a caption's labels match the code.

Public names it uses: from `pyntpot.ink`, `Casing`, `Glow`, `Shadow`, `PenCasing`, `casing`,
`glow`, `shadow`, `pen_casing`, `pigment`, `Colour`, `Sheet`, `PaperStyle`,
`composite` and `save_image`; from `pyntpot.letters`, `Setting`; `LABELS`, `GridSpec`,
`grid_paper`, `label_grid`, `on_paper` and `sweep_grid` from `labelled_grid.py`; and `Scene`,
`scene`, `SEED` and `GRAN_PX` from `line_effect_scenes.py`. It introduces none.

Run it with `uv run python examples/line_effect_grids.py out/ --figure glow`; it writes
`out/glow-sweep.png`.
"""

import argparse
import logging
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
from labelled_grid import LABELS, Box, GridSpec, grid_paper, label_grid, on_paper, sweep_grid
from line_effect_scenes import GRAN_PX, SEED, Scene, scene

from pyntpot.ink import (
    Casing,
    Colour,
    Glow,
    PaperStyle,
    PenCasing,
    Shadow,
    Sheet,
    casing,
    composite,
    glow,
    pen_casing,
    pigment,
    save_image,
    shadow,
)
from pyntpot.letters import Setting

logger = logging.getLogger(__name__)

#: The figures, in the order the how-to and the tutorial show them.
FIGURES: tuple[str, ...] = ("casing", "glow", "shadow", "pen-casing")
#: The casing's widths across, in pixels, and the colours down: the paper's and Payne's grey.
WIDTHS_PX: tuple[float, ...] = (0.0, 1.0, 2.0, 3.0, 5.0)
PAPER_WHITE = Colour("#ffffff")
CASING_COLOURS: tuple[tuple[str, Colour], ...] = (
    ("paper", PAPER_WHITE),
    ("paynes_grey", pigment("paynes_grey").colour),
)
#: The glow's spread across and its blur down, in pixels.
SPREADS_PX: tuple[float, ...] = (0.0, 2.0, 4.0, 6.0)
GLOW_BLURS_PX: tuple[float, ...] = (0.0, 3.0, 6.0)
#: The shadow's offset across and its blur down, in pixels.
OFFSETS_PX: tuple[float, ...] = (0.0, 1.5, 3.0, 5.0)
SHADOW_BLURS_PX: tuple[float, ...] = (1.0, 3.0)
#: The pen casing's gap across and its ink edge lines' width down, in pixels.
GAPS_PX: tuple[float, ...] = (1.0, 2.0, 3.0, 4.0)
EDGES_PX: tuple[float, ...] = (0.75, 1.5)
#: The names of the edge lines' widths, down.
EDGE_NAMES: tuple[str, ...] = ("thin", "thick")

#: The light's azimuth in degrees clockwise from north: north-west, so shadows fall south-east.
AZIMUTH_DEG = 315.0
#: How strongly the glow lifts and the shadow darkens.
GLOW_STRENGTH, SHADOW_STRENGTH = 0.8, 0.4
#: Each figure's image width, cell height and the room left of its grid, in pixels.
WIDTH_PX = {"casing": 720, "glow": 720, "shadow": 720, "pen-casing": 600}
CELL_H = {"casing": 70, "glow": 62, "shadow": 62, "pen-casing": 62}
LEFT, TOP, GAP, PAD_RIGHT, PAD_BOTTOM = 150, 44, 12, 14, 16


@dataclass(frozen=True)
class Layout:
    """What a figure letters and paints: a dict of settings for each cell, and the names."""

    cells: list[list[dict[str, Any]]]
    columns: list[str]
    rows: list[str]
    corner: str


def _px(values: tuple[float, ...]) -> list[str]:
    """Return each value lettered with its unit."""
    return [f"{value:g} px" for value in values]


def layout(figure: str) -> Layout:
    """Return the cells' settings and the names of a figure's columns and rows.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    if figure == "casing":
        cells = [[{"width_px": w, "colour": c} for w in WIDTHS_PX] for _, c in CASING_COLOURS]
        return Layout(cells, _px(WIDTHS_PX), [name for name, _ in CASING_COLOURS], "width")
    if figure == "glow":
        cells = [[{}, *({"spread_px": s, "blur_px": b} for s in SPREADS_PX)] for b in GLOW_BLURS_PX]
        rows = [f"blur {name}" for name in _px(GLOW_BLURS_PX)]
        return Layout(cells, ["none", *_px(SPREADS_PX)], rows, "spread")
    if figure == "shadow":
        cells = [
            [{}, *({"offset_px": o, "blur_px": b} for o in OFFSETS_PX)] for b in SHADOW_BLURS_PX
        ]
        rows = [f"blur {name}" for name in _px(SHADOW_BLURS_PX)]
        return Layout(cells, ["none", *_px(OFFSETS_PX)], rows, "offset")
    cells = [[{}, *({"width_px": g, "edge_px": e} for g in GAPS_PX)] for e in EDGES_PX]
    rows = [f"{n} {px}" for n, px in zip(EDGE_NAMES, _px(EDGES_PX), strict=True)]
    return Layout(cells, ["none", *_px(GAPS_PX)], rows, "gap")


def _check(figure: str) -> None:
    """Raise `ValueError` for a figure the sweeps do not have."""
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")


@cache
def _spec(figure: str) -> GridSpec:
    """The figure's grid of cells."""
    made = layout(figure)
    return GridSpec(
        WIDTH_PX[figure],
        len(made.columns),
        len(made.rows),
        CELL_H[figure],
        LEFT,
        TOP,
        GAP,
        PAD_RIGHT,
        PAD_BOTTOM,
    )


@cache
def _paper(figure: str) -> np.ndarray:
    """The paper plate of the whole figure; a cell paints over its own crop of it."""
    return grid_paper(Sheet(_spec(figure).height, WIDTH_PX[figure], GRAN_PX, SEED))


def _scene(figure: str) -> Scene:
    """The scene of a figure's cell, which `line_effect_scenes.py` paints once."""
    return scene(figure, _spec(figure).cell_w, CELL_H[figure])


def stroke_density(figure: str) -> np.ndarray:
    """The density of a figure's stroke, the mask its effect is laid by."""
    _check(figure)
    return _scene(figure).density


def _cased(scene: Scene, width_px: float = 0.0, colour: Colour = PAPER_WHITE) -> np.ndarray:
    """The wash with a casing of `width_px` and `colour` round the stroke."""
    effect = Casing(width_px=width_px, colour=colour, strength=1.0)
    return casing(scene.wash, scene.density, effect, paper=None)


def _glowed(scene: Scene, spread_px: float | None = None, blur_px: float = 0.0) -> np.ndarray:
    """The wash with a glow round the stroke; `None` for the spread is no glow."""
    if spread_px is None:
        return glow(scene.wash, scene.density, Glow(), paper=None)
    effect = Glow(spread_px=spread_px, blur_px=blur_px, strength=GLOW_STRENGTH)
    return glow(scene.wash, scene.density, effect, paper=None)


def _shadowed(scene: Scene, offset_px: float | None = None, blur_px: float = 0.0) -> np.ndarray:
    """The wash with a Payne's grey shadow of the stroke; `None` for the offset is no shadow."""
    if offset_px is None:
        return shadow(scene.wash, scene.density, Shadow(), azimuth_deg=AZIMUTH_DEG)
    effect = Shadow(
        offset_px=offset_px,
        blur_px=blur_px,
        strength=SHADOW_STRENGTH,
        colour=pigment("paynes_grey").colour,
    )
    return shadow(scene.wash, scene.density, effect, azimuth_deg=AZIMUTH_DEG)


def _reserved(
    scene: Scene, width_px: float | None = None, edge_px: float = 0.0
) -> tuple[np.ndarray, np.ndarray]:
    """The tint with a reserve round the stroke and the density of the ink edge lines."""
    effect = PenCasing() if width_px is None else PenCasing(width_px=width_px, edge_px=edge_px)
    return pen_casing(scene.wash, scene.density, effect, paper=None)


def paint_cell(
    figure: str,
    *,
    plain: bool = False,
    at: tuple[int, int] = (0, 0),
    **values: Any,  # noqa: ANN401 - each figure's effect takes its own numbers and colour
) -> np.ndarray:
    """Paint one cell of a figure and return its float32 RGB `(h, w, 3)`.

    The wash, then the effect through its `pyntpot.ink` primitive, then the stroke, then the
    paper plate's crop at `at` multiplied in. With no `values` the effect is the primitive's
    default, which is off; the casing's `width_px=0.0` is its off setting. `plain=True` paints
    the stroke with no primitive called.

    Args:
        figure: One of `FIGURES`.
        plain: Skip the effect altogether.
        at: The cell's top left corner on the figure, which picks the paper's crop.
        **values: The effect's settings: `width_px` and `colour` for the casing, `spread_px` and
            `blur_px` for the glow, `offset_px` and `blur_px` for the shadow, `width_px` and
            `edge_px` for the pen casing.

    Returns:
        The cell as float32 RGB, in 0 to 1.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    scene = _scene(figure)
    edges: np.ndarray | None = None
    under = scene.wash
    if not plain:
        match figure:
            case "casing":
                under = _cased(scene, **values)
            case "glow":
                under = _glowed(scene, **values)
            case "shadow":
                under = _shadowed(scene, **values)
            case _:
                under, edges = _reserved(scene, **values)
    if edges is not None and edges.any():
        under = composite([(edges, scene.ink)], under, PaperStyle())
    laid = composite([(scene.density, scene.ink)], under, PaperStyle())
    return on_paper(laid, _paper(figure), at)


def main(out_dir: Path, figure: str = "casing") -> Path:
    """Paint one sweep and return the path of its PNG in `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: One of `FIGURES`.

    Returns:
        The path of the image, `<figure>-sweep.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    _check(figure)
    made, spec = layout(figure), _spec(figure)
    boxes = spec.boxes()

    def paint(row: int, col: int, box: Box) -> np.ndarray:
        """Paint the cell of a row and column at its box."""
        return paint_cell(figure, at=(box[0], box[1]), **made.cells[row][col])

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
    parser = argparse.ArgumentParser(description="Paint a line effect sweep and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="casing", help="the sweep")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure)
