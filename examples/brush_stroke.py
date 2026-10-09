"""Rung 3 of the tutorial: two brush strokes, one wet and one dry.

A brush comes from a cell of the brush sheet: `brush_from_id` reads an id such as
`RIV1-a` (a wet river brush) or `TRK4-d` (a dry track brush) with the `BrushStyle`
defaults, and returns the brush and its ink colour as hex. `stamp` lays one stroke's
bristles along a path into an accumulator, and `ink_density` turns that accumulator into
ink density on the paper's tooth. Each stroke is composited over the paper in the
colour its brush came with.

Public names it introduces: `BrushStyle`, `brush_from_id`, `stamp` and `ink_density`,
beside the earlier rungs' `Sheet`, `Canvas`, `PaperStyle`, `paper_plate`, `rgb`,
`composite` and `save_image`, all from `pyntpot.ink`.

Run it with `uv run python examples/brush_stroke.py out/`; it writes
`out/brush_stroke.png`.
"""

import argparse
import logging
from pathlib import Path

import numpy as np

from pyntpot.ink import (
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
)

logger = logging.getLogger(__name__)

#: The image's width and height, in pixels.
W, H = 360, 240
#: The size of the paper's granulation noise, in pixels.
GRAN_PX = 8.0
#: The seed of the paper's noise, the bristles and the dither the file is written with.
SEED = 11


def _stroke(
    brush_id: str, width_px: float, line: np.ndarray, sheet: Sheet
) -> tuple[np.ndarray, str]:
    """Stamp one stroke of a brush sheet cell along a line; return its density and ink hex."""
    brush, ink_hex = brush_from_id(brush_id, width_px, 1.0, BrushStyle())
    acc = np.zeros((H, W), np.float32)
    stamp(acc, line, brush, np.random.default_rng(SEED))
    return ink_density(acc, brush, sheet), ink_hex


def main(out_dir: Path) -> Path:
    """Paint a wet and a dry stroke on the paper, write `brush_stroke.png` into `out_dir` and return its path."""
    sheet = Sheet(H, W, GRAN_PX, SEED)
    canvas = Canvas(0, 0, W, H, W, H)
    paper = paper_plate(sheet, canvas, PaperStyle(), W)

    x = np.linspace(0.1 * W, 0.9 * W, 200)
    wet_line = np.column_stack([x, H / 2 + 0.12 * H * np.sin(2 * np.pi * x / W)])
    dry_line = np.column_stack([x, 0.78 * H + 0.08 * H * np.sin(2 * np.pi * x / W + np.pi)])
    wet, wet_hex = _stroke("RIV1-a", 6.0, wet_line, sheet)
    dry, dry_hex = _stroke("TRK4-d", 4.0, dry_line, sheet)

    out = composite([(wet, rgb(wet_hex)), (dry, rgb(dry_hex))], paper, PaperStyle())
    path = out_dir / "brush_stroke.png"
    save_image(out, path, seed=SEED)
    logger.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint two brush strokes and write a PNG.")
    parser.add_argument("out_dir", type=Path, help="the directory the PNG is written into")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(args.out_dir)
