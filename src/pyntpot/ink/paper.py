"""The paper plate: the cream paper painted from the sheet alone.

Key name: `paper_plate`, cream rag, a worn border, a vignette, a little
foxing, and a grid when the style asks for one.

It writes nothing to disk and lays no pigment; the caller composites over
it and writes it.

Invariants: the paper is an `(h, w, 3)` array in 0 to 1, the canvas's
size; it draws two fields from the sheet's own generator (`Sheet.noise`),
so on one sheet it depends on what was drawn before it, and it draws from
no other generator.
"""

import numpy as np

from pyntpot.ink.noise import F32
from pyntpot.ink.sheet import Canvas, Sheet, rgb
from pyntpot.ink.style import PaperStyle


def paper_plate(sheet: Sheet, canvas: Canvas, style: PaperStyle, display_px: int) -> np.ndarray:
    """Paint the paper: cream rag, a worn border, a vignette, a little foxing, a grid if asked.

    Args:
        sheet: The paper's noise fields, of the canvas's size; two more
            fields are drawn from its generator.
        canvas: The raster painted on; only its `w` and `h` are read.
        style: The paper's colour, tooth, wear, vignette, foxing and grid.
        display_px: The width, in pixels, the style's `grid_spacing_px` is
            measured against; the canvas width is the usual value, and gives
            a line every `grid_spacing_px` canvas pixels. Read only when the
            style asks for a grid.

    Returns:
        An `(h, w, 3)` float array in 0 to 1.

    It lays no pigment and writes nothing. On one sheet the result depends
    on how many fields were drawn from the sheet's generator before it.
    """
    h, w = canvas.h, canvas.w
    base = rgb(style.paper_hex)
    img = np.repeat(base[None, None, :], h, 0).repeat(w, 1).copy()
    img *= (1.0 + style.paper_tooth * (sheet.paper - 0.5))[..., None]
    yy = np.minimum(np.arange(h)[:, None], h - 1 - np.arange(h)[:, None])
    xx = np.minimum(np.arange(w)[None, :], w - 1 - np.arange(w)[None, :])
    edge_px = np.minimum(yy, xx).astype(F32)
    worn = np.exp(-edge_px / F32(max(w * 0.012, 8.0)))
    worn = worn * (0.55 + 0.9 * sheet.noise(26.0, 2))
    img *= (1.0 - style.paper_worn * np.clip(worn, 0, 1))[..., None]
    vign = np.exp(-edge_px / F32(w * 0.34))
    img *= (1.0 - style.paper_vignette * vign)[..., None]
    fox = np.clip((sheet.noise(120.0, 2) - 0.80) * 5.0, 0, 1)
    img *= (1.0 - style.paper_foxing * fox)[..., None]
    if style.grid:
        step = max(style.grid_spacing_px * canvas.w / max(display_px, 1), 4.0)
        rows = (np.arange(h) % step < 1.0)[:, None]
        cols = (np.arange(w) % step < 1.0)[None, :]
        line = np.clip(rows * 1.0 + cols * 0.55, 0, 1).astype(F32)
        img *= (1.0 - style.grid_opacity * 0.30 * line)[..., None]
    return np.clip(img, 0, 1)
