"""The pigment gallery: every pigment as three washes, how pairs glaze, and the bundled palettes.

Four figures, selected by `figure=`, each painted on `paper_plate` paper and lettered in the
default hand through the sibling `labelled_grid.py`.

- `roles`: the fifteen pigments a map names by role (`PIGMENTS`), one row each, in registry
  order. The canonical name is lettered at the left, as typed in a theme. Three washes of the
  pigment sit across, at `STRENGTHS` 0.3, 0.6 and 0.9, each glazed by Kubelka-Munk at the
  pigment's own transparency. The right margin letters that transparency, then the Colour Index
  code, left blank where the registry records none.
- `painters`: the same, for the ten tube pigments (`PAINTERS_PIGMENTS`).
- `glazes`: six `GLAZE_PAIRS` across, each lettered on two lines, first the pigment laid under
  or over and then the other. Three rows of two overlapping discs: multiplied, the first over
  the second, and the second over the first. The discs are painted watercolour on the figure's
  own sheet, granulated, and each pair is chosen so the overlap of A over B is a measurably
  different colour from B over A, because glazing is not commutative.
- `palettes`: one block for each bundled palette (`Palette.names()`). Each alias is a 0.6 wash
  glazed at its pigment's transparency, with the alias above it and the pigment it names below.
  A palette alias bound to a bare hex has no transparency of its own, so it glazes at
  `PaperStyle.km_transparency` and is lettered with its hex.

Transparency is shown the one way in every figure: as washes at three strengths beside the
lettered value. There is no ink bar. `wash_rows` returns the painted `roles` or `painters`
figure before lettering, with each wash's box, so a test can measure the washes themselves.
`palette_swatches` lists the palettes figure's swatches.

It paints no map and reads no theme file; the palettes are read through `Palette.named`.

Public names it uses: from `pyntpot.ink`, `Sheet`, `Canvas`, `PaperStyle`, `Colour`,
`PIGMENT_REGISTRY`, `PIGMENTS`, `PAINTERS_PIGMENTS`, `PigmentLayer`, `paper_plate`, `wash`,
`rgb`, `composite` and `save_image`; from `pyntpot.letters`, `Setting` and
`NibStyle`; from `pyntpot.maps`, `Palette`; and `GridSpec`, `LabelStyle`, `label_grid` and
`letter_over` from `labelled_grid.py`. It introduces none.

Run it with `uv run python examples/pigment_gallery.py out/ --figure glazes`; it writes
`out/pigment-gallery-glazes.png`. `--size` sets the width in pixels, 720 by default.
"""

import argparse
import dataclasses
import logging
from pathlib import Path
from typing import NamedTuple

import numpy as np
from labelled_grid import Box, GridSpec, LabelStyle, label_grid, letter_over

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    PIGMENT_REGISTRY,
    PIGMENTS,
    Canvas,
    Colour,
    PaperStyle,
    PigmentLayer,
    Sheet,
    composite,
    paper_plate,
    rgb,
    save_image,
    wash,
)
from pyntpot.letters import NibStyle, Setting
from pyntpot.maps import Palette

logger = logging.getLogger(__name__)

#: The figures, in the order the reference page shows them.
FIGURES: tuple[str, ...] = ("roles", "painters", "glazes", "palettes")
#: The width every figure is designed at, in pixels.
DESIGN_W = 720
#: The seed of the paper's noise, the hand and the dither the file is written with.
SEED = 7
#: The size of the paper's granulation noise, in pixels at the design width.
GRAN_PX = 40.0
#: The strengths of the three washes of a pigment, across.
STRENGTHS: tuple[float, ...] = (0.3, 0.6, 0.9)
#: The pooled-edge share of a wash.
POOL = 0.25
#: The six pairs the glaze figure lays, each the pigment named first and the one named second.
GLAZE_PAIRS: tuple[tuple[str, str], ...] = (
    ("cerulean", "yellow_ochre"),
    ("cerulean", "burnt_sienna"),
    ("ultramarine", "yellow_ochre"),
    ("yellow_ochre", "indigo"),
    ("yellow_ochre", "perylene_maroon"),
    ("cerulean", "quinacridone_rose"),
)
#: The glaze figure's rows, down.
GLAZE_ROWS: tuple[str, ...] = ("multiply", "A over B", "B over A")
#: The strength of the glaze figure's discs and of the palettes figure's swatches.
DISC_STRENGTH, SWATCH_STRENGTH = 0.8, 0.6
#: How every figure's names are lettered: one hand, at the design width.
LABELS = LabelStyle(px=21.0, ink=Colour("#4a3a2a"), pen_px=1.5, gran_px=12.0, seed=7, col_dy=12)
#: The size of the smaller lettering, and the palettes figure's pigment names, at the design width.
SMALL_PX = 14.0
#: Palettes are laid this many swatches to a line.
PALETTE_COLUMNS = 5


class WashRows(NamedTuple):
    """The painted `roles` or `painters` figure before it is lettered.

    Attributes:
        image: The float32 RGB figure, `(h, w, 3)`.
        boxes: The three washes of each row, as `(x, y, w, h)`, a list for each pigment.
        names: The pigments, one for each row, in registry order.
    """

    image: np.ndarray
    boxes: list[list[Box]]
    names: tuple[str, ...]


def _scaled(style: LabelStyle, unit: float, px: float | None = None) -> LabelStyle:
    """Return `style` scaled by `unit`, at `px` (design pixels) if given."""
    return dataclasses.replace(
        style,
        px=(style.px if px is None else px) * unit,
        pen_px=style.pen_px * unit,
        gran_px=style.gran_px * unit,
        col_dy=style.col_dy * unit,
        row_dx=style.row_dx * unit,
        row_dy=style.row_dy * unit,
    )


def _paper(sheet: Sheet, w: int, h: int) -> np.ndarray:
    """The `paper_plate` the figure is painted on."""
    return paper_plate(sheet, Canvas(0, 0, w, h, w, h), PaperStyle(paper_foxing=0.0), w)


def _mask(w: int, h: int, boxes: list[Box]) -> np.ndarray:
    """A coverage mask, 1 inside each of the boxes."""
    mask = np.zeros((h, w), np.float32)
    for x, y, bw, bh in boxes:
        mask[y : y + bh, x : x + bw] = 1.0
    return mask


def _disc(w: int, h: int, cx: float, cy: float, radius: float) -> np.ndarray:
    """A coverage mask of a disc centred at (`cx`, `cy`)."""
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx - cx) ** 2 + (yy - cy) ** 2 <= radius**2).astype(np.float32)


def _layer(density: np.ndarray, name: str) -> PigmentLayer:
    """The glaze layer of a registry pigment: its density, colour and own transparency."""
    found = PIGMENT_REGISTRY.get(name)
    if found.transparency is None:
        return (density, rgb(found.colour))
    return (density, rgb(found.colour), found.transparency)


def _names(figure: str) -> tuple[str, ...]:
    """The pigments a wash figure paints, in registry order."""
    return tuple(PIGMENTS if figure == "roles" else PAINTERS_PIGMENTS)


def wash_rows(figure: str, size: int = DESIGN_W) -> WashRows:
    """Paint the `roles` or `painters` figure's washes on paper, before any lettering.

    Args:
        figure: `roles` or `painters`.
        size: The width in pixels.

    Returns:
        The painted figure, the boxes of the washes and the pigments, one for each row.

    Raises:
        ValueError: When `figure` is not a wash figure.
    """
    if figure not in {"roles", "painters"}:
        raise ValueError(f"no such wash figure {figure!r}; the wash figures are roles, painters")
    names = _names(figure)
    unit = size / DESIGN_W
    spec = GridSpec(size, len(STRENGTHS), len(names), 26, 215, 40, 8, 160, 14, unit)
    boxes, w, h = spec.boxes(), size, spec.height
    sheet = Sheet(h, w, GRAN_PX * unit, SEED)
    out = _paper(sheet, w, h)
    for column, strength in enumerate(STRENGTHS):
        density = wash(_mask(w, h, [row[column] for row in boxes]), sheet, strength, POOL)
        for name, row in zip(names, boxes, strict=True):
            x, y, bw, bh = row[column]
            crop = (slice(y, y + bh), slice(x, x + bw))
            out[crop] = composite(
                [_layer(density[crop], name)], out[crop], PaperStyle(km_glazing=True)
            )
    return WashRows(out, boxes, names)


def _wash_figure(figure: str, size: int) -> np.ndarray:
    """The lettered `roles` or `painters` figure."""
    unit = size / DESIGN_W
    painted = wash_rows(figure, size)
    margin = painted.boxes[0][-1][0] + painted.boxes[0][-1][2] + round(18 * unit)
    small = _scaled(LABELS, unit, SMALL_PX)
    top = painted.boxes[0][0][1] - small.col_dy
    notes = [Setting("transp.", small.px, anchor=(margin, top), wash=False)]
    if figure == "painters":
        notes.append(Setting("CI", small.px, anchor=(margin + 66 * unit, top), wash=False))
    for name, row in zip(painted.names, painted.boxes, strict=True):
        found = PIGMENT_REGISTRY.get(name)
        baseline = row[0][1] + row[0][3] / 2 + 7 * unit
        notes.append(
            Setting(f"{found.transparency:.2f}", 21.0 * unit, anchor=(margin, baseline), wash=False)
        )
        if found.colour_index is not None:
            notes.append(
                Setting(
                    found.colour_index,
                    21.0 * unit,
                    anchor=(margin + 66 * unit, baseline),
                    wash=False,
                )
            )
    return label_grid(
        painted.image, painted.boxes, STRENGTHS, painted.names, _scaled(LABELS, unit), extra=notes
    )


def _glaze_figure(size: int) -> np.ndarray:
    """The lettered glaze figure: six pairs across, multiply, A over B and B over A down.

    Every disc is painted once on the figure's own sheet, as the tutorial's glaze grid does, and
    the three rows composite the same two washes of a pair three ways.
    """
    unit = size / DESIGN_W
    spec = GridSpec(size, len(GLAZE_PAIRS), len(GLAZE_ROWS), 76, 84, 70, 8, 8, 12, unit)
    boxes, w, h = spec.boxes(), size, spec.height
    sheet = Sheet(h, w, GRAN_PX * unit, SEED)
    out = _paper(sheet, w, h)
    radius = min(0.33 * spec.cell_w, 0.46 * round(76 * unit))
    centres = [
        [(x + bw * cx, y + bh / 2) for row in boxes for x, y, bw, bh in row] for cx in (0.35, 0.65)
    ]
    washes = [
        wash(
            np.maximum.reduce([_disc(w, h, cx, cy, radius) for cx, cy in centres[side]]),
            sheet,
            DISC_STRENGTH,
            POOL,
        )
        for side in (0, 1)
    ]
    for r, row in enumerate(boxes):
        for (x, y, bw, bh), (first, second) in zip(row, GLAZE_PAIRS, strict=True):
            crop = (slice(y, y + bh), slice(x, x + bw))
            layers = [_layer(washes[0][crop], first), _layer(washes[1][crop], second)]
            order = layers[::-1] if GLAZE_ROWS[r] == "B over A" else layers
            out[crop] = composite(
                order, out[crop], PaperStyle(km_glazing=GLAZE_ROWS[r] != "multiply")
            )
    small = _scaled(LABELS, unit, SMALL_PX)
    firsts = [
        Setting(
            first,
            small.px,
            anchor=(x + bw / 2, boxes[0][0][1] - small.col_dy - 18 * unit),
            align="middle",
            wash=False,
        )
        for (x, _, bw, _), (first, _) in zip(boxes[0], GLAZE_PAIRS, strict=True)
    ]
    seconds = [second for _, second in GLAZE_PAIRS]
    return label_grid(out, boxes, seconds, GLAZE_ROWS, small, extra=firsts)


def palette_swatches() -> tuple[tuple[str, str, str], ...]:
    """The palettes figure's swatches, in order: the palette, the alias and the pigment it names.

    A pigment bound to a bare hex is named by its hex.
    """
    return tuple(
        (name, alias, bound.name)
        for name in Palette.names()
        for alias, bound in Palette.named(name).pigments.items()
    )


def _palettes_figure(size: int) -> np.ndarray:
    """The lettered palettes figure: a block of swatches for each bundled palette."""
    unit = size / DESIGN_W
    swatches = palette_swatches()
    placed: list[tuple[int, int, str, str, str]] = []
    row = 0
    for palette in Palette.names():
        mine = [(alias, bound) for p, alias, bound in swatches if p == palette]
        for start in range(0, len(mine), PALETTE_COLUMNS):
            placed += [
                (row, column, palette if start == 0 else "", alias, bound)
                for column, (alias, bound) in enumerate(mine[start : start + PALETTE_COLUMNS])
            ]
            row += 1
    spec = GridSpec(size, PALETTE_COLUMNS, row, 46, 100, 40, 56, 14, 34, unit)
    boxes, w, h = spec.boxes(), size, spec.height
    sheet = Sheet(h, w, GRAN_PX * unit / 2, SEED)
    out = _paper(sheet, w, h)
    chosen = [boxes[r][c] for r, c, _, _, _ in placed]
    density = wash(_mask(w, h, chosen), sheet, SWATCH_STRENGTH, POOL)
    small = _scaled(LABELS, unit, SMALL_PX)
    notes: list[Setting] = []
    for (r, _, palette, alias, bound), (x, y, bw, bh) in zip(placed, chosen, strict=True):
        crop = (slice(y, y + bh), slice(x, x + bw))
        out[crop] = composite(
            [_swatch_layer(density[crop], bound)], out[crop], PaperStyle(km_glazing=True)
        )
        centre = x + bw / 2
        notes.append(
            Setting(alias, 18 * unit, anchor=(centre, y - 8 * unit), align="middle", wash=False)
        )
        notes.append(
            Setting(
                bound, small.px, anchor=(centre, y + bh + 20 * unit), align="middle", wash=False
            )
        )
        if palette:
            notes.append(
                Setting(
                    palette,
                    LABELS.px * unit,
                    anchor=(boxes[r][0][0] - 14 * unit, y + bh / 2 + 7 * unit),
                    align="end",
                    wash=False,
                )
            )
    nib = NibStyle(label_ink=LABELS.ink, label_pen_width_px=LABELS.pen_px * unit)
    return letter_over(out, notes, nib, gran_px=LABELS.gran_px * unit, seed=LABELS.seed)


def _swatch_layer(density: np.ndarray, pigment_name: str) -> PigmentLayer:
    """The layer of a palette swatch: a registry pigment with its transparency, or a hex without."""
    if pigment_name.startswith("#"):
        return (density, rgb(pigment_name))
    return _layer(density, pigment_name)


def main(out_dir: Path, figure: str = "roles", size: int = DESIGN_W) -> Path:
    """Paint one figure and return the path of its PNG in `out_dir`.

    Args:
        out_dir: The directory the image is written into.
        figure: One of `FIGURES`.
        size: The image's width in pixels.

    Returns:
        The path of the image, `pigment-gallery-<figure>.png`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"no such figure {figure!r}; the figures are {', '.join(FIGURES)}")
    if figure == "glazes":
        image = _glaze_figure(size)
    elif figure == "palettes":
        image = _palettes_figure(size)
    else:
        image = _wash_figure(figure, size)
    path = out_dir / f"pigment-gallery-{figure}.png"
    save_image(image, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a pigment gallery figure and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    parser.add_argument("--figure", choices=FIGURES, default="roles", help="the figure to paint")
    parser.add_argument("--size", type=int, default=DESIGN_W, help="the image's width in pixels")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir, args.figure, args.size)
