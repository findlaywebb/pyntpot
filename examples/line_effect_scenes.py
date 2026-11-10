"""The scenes of the line effect sweeps: the wash and the stroke every cell of a figure shares.

Split from `line_effect_grids.py` so that script keeps the sweeps' layout and effects. Four
scenes, one for each figure the sweeps paint, each a `Scene`: a wash in wash space (where the
paper is 1), the stroke's density, and the stroke's ink as RGB.

- `casing`: a `MAJ2-b` road, 6 pixels wide, over a farmland and wood wash.
- `glow`: an `RIV1-a` river, 4 pixels wide, over a dark wood wash.
- `shadow`: a solid `#c22050` line, 4 pixels wide, over farmland.
- `pen-casing`: a solid 1.5 pixel `#3a2c20` line over a Payne's grey tint.

`scene(figure, w, h)` returns the scene of a cell `w` by `h` pixels, painted once and cached.
`Scene` is a frozen record of three arrays.

It paints no effect, letters nothing and writes no file: the effect is the sweep script's. The
arrays are shared between callers, who must not change them. It holds the seed, the granulation
size and the pen tint's strength the sweeps share.

Public names it uses: from `pyntpot.ink`, `Colour`, `pigment`, `PigmentLayer`, `Sheet`,
`PaperStyle`, `BrushStyle`, `brush_from_id`, `stamp`, `ink_density`, `wash`, `composite` and
`rgb`. It introduces none.
"""

from dataclasses import dataclass
from functools import cache

import numpy as np

from pyntpot.ink import (
    BrushStyle,
    Colour,
    PaperStyle,
    PigmentLayer,
    Sheet,
    brush_from_id,
    composite,
    ink_density,
    pigment,
    rgb,
    stamp,
    wash,
)

#: The seed of the paper's noise, the washes, the bristles, the hand and the dither of the file.
SEED = 7
#: The size of the paper's granulation and of the washes' mottle, in pixels.
GRAN_PX = 8.0
#: The pen line's ink, the solid line's ink and the pen tint's strength.
PEN_INK, SOLID_INK, TINT = Colour("#3a2c20"), Colour("#c22050"), 0.3


def _curve(w: int, h: int) -> np.ndarray:
    """An S-shaped line across a cell of `w` by `h` pixels."""
    t = np.linspace(0.0, 1.0, 70)
    return np.column_stack([10 + t * (w - 20), h / 2 + 0.16 * h * np.sin(2 * np.pi * t)])


def _solid(points: np.ndarray, width_px: float, shape: tuple[int, int]) -> np.ndarray:
    """A solid line's density: 1 inside `width_px` of the polyline, soft across one pixel."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    start, step = points[:-1], np.diff(points, axis=0)
    px, py = xx[..., None] - start[:, 0], yy[..., None] - start[:, 1]
    along = np.clip((px * step[:, 0] + py * step[:, 1]) / (step**2).sum(axis=1), 0.0, 1.0)
    dist = np.hypot(px - along * step[:, 0], py - along * step[:, 1]).min(axis=-1)
    return np.clip(width_px / 2 + 0.5 - dist, 0.0, 1.0).astype(np.float32)


def _brushed(brush_id: str, width_px: float, sheet: Sheet) -> tuple[np.ndarray, np.ndarray]:
    """A brush id's stroke along the curve: its density and its ink as RGB."""
    brush, ink = brush_from_id(brush_id, width_px, 1.0, BrushStyle())
    acc = np.zeros((sheet.h, sheet.w), np.float32)
    stamp(acc, _curve(sheet.w, sheet.h), brush, np.random.default_rng(SEED))
    return ink_density(acc, brush, sheet), rgb(ink)


def _washed(sheet: Sheet, *layers: tuple[str, float, float, float]) -> np.ndarray:
    """The wash in wash space, where the paper is 1.

    Each layer is `(pigment name, left edge, right edge, body)`, the edges as shares of the width.
    """
    stack: list[PigmentLayer] = []
    xx = np.arange(sheet.w, dtype=np.float32)[None, :] / sheet.w
    for name, lo, hi, body in layers:
        cover = np.broadcast_to(((xx >= lo) & (xx <= hi)).astype(np.float32), (sheet.h, sheet.w))
        pig = pigment(name)
        km = PaperStyle().km_transparency if pig.transparency is None else pig.transparency
        stack.append((wash(cover, sheet, body, 0.0), rgb(pig.colour), km))
    return composite(stack, np.ones((sheet.h, sheet.w, 3), np.float32), PaperStyle())


@dataclass(frozen=True)
class Scene:
    """What every cell of a figure shares: the wash, and the stroke's density and ink."""

    wash: np.ndarray
    density: np.ndarray
    ink: np.ndarray


@cache
def scene(figure: str, w: int, h: int) -> Scene:
    """The wash and the stroke of a figure's cell of `w` by `h` pixels, painted once.

    Callers must not change the arrays.
    """
    sheet = Sheet(h, w, GRAN_PX, SEED)
    if figure == "casing":
        base = _washed(
            sheet, ("farmland", 0.0, 0.6, 0.8), ("wood", 0.4, 1.0, 0.9), ("wood", 0.5, 1.0, 0.9)
        )
        return Scene(base, *_brushed("MAJ2-b", 6.0, sheet))
    if figure == "glow":
        return Scene(
            _washed(sheet, *[("wood", 0.0, 1.0, 0.9)] * 3), *_brushed("RIV1-a", 4.0, sheet)
        )
    if figure == "shadow":
        base = _washed(sheet, ("farmland", 0.0, 1.0, 0.8))
        return Scene(base, _solid(_curve(w, h), 4.0, (h, w)), rgb(SOLID_INK))
    base = _washed(sheet, ("paynes_grey", 0.0, 1.0, TINT))
    return Scene(base, _solid(_curve(w, h), 1.5, (h, w)), rgb(PEN_INK))
