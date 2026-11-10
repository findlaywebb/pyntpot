"""How-to: the relief at four strengths, one close window of the Ambleside card in each.

`CoverStyle.relief_strength` multiplies the shaded relief's density, and the ceiling it is held
to, so 1 is the style's own relief, 0 is none, and above 1 is a heavier hill. This script paints
the Ambleside fixture four times with the default style, once at each of 0, 2, 4 and 8, and shows the same close window of each card, on the slope of
Loughrigg Fell, side by side. The relief is part of what `paint` draws, so each strength paints its own plates, each in its own directory of the cache, and
nothing else changes from one cell to the next: the route, the washes and the paper are the same.
Each cell is the card composed with no lettering and no attribution, so the hill is what is seen;
the strengths are lettered over the cells, in the hand.

Public names it uses: from `pyntpot.maps`, `Cache`, `Lettering`, `OpenTopoData`,
`OverpassFeatures`, `Style`, `Track`, `compose`, `fetch` and `paint`; from `pyntpot.ink`,
`Canvas`, `Colour`, `PaperStyle`, `Sheet`, `paper_plate` and `save_image`; `GridSpec`, `LabelStyle`
and `label_grid` from the sibling `labelled_grid.py`. It introduces none. It writes
`out_dir / "relief_strength.png"`.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/relief_grid.py route.gpx cache/ out/ https://example.org/your-project
"""

import argparse
import dataclasses
import logging
from pathlib import Path

import numpy as np
from labelled_grid import GridSpec, LabelStyle, label_grid
from PIL import Image

from pyntpot.ink import Canvas, Colour, PaperStyle, Sheet, paper_plate, save_image
from pyntpot.maps import (
    Cache,
    Lettering,
    OpenTopoData,
    OverpassFeatures,
    Style,
    Track,
    compose,
    fetch,
    paint,
)

log = logging.getLogger(__name__)

#: The strengths across: no relief, then three heavier than the default's own. The window sits on
#: Loughrigg Fell's slope, where each step darkens the hill by at least 3 CIE76 ΔE on average; the
#: strength has no upper limit, and the relief saturates a little above 8.
STRENGTHS: tuple[float, ...] = (0.0, 2.0, 4.0, 8.0)
#: The grid's width in pixels, the room left of the cells, above them, round them and between them.
GRID_W, LEFT, TOP, PAD, GAP = 720, 12, 44, 12, 12
#: How many times a cell's width the card is painted across, and where the close window's top left
#: corner is, as shares of the card's width and height. The window is `1 / ZOOM` of the card across.
ZOOM, WINDOW_AT = 2, (0.28, 0.26)
#: The hand's seed.
SEED = 7
#: How the names are lettered.
LABELS = LabelStyle(px=21.0, ink=Colour("#4a3a2a"), pen_px=1.5, gran_px=12.0, seed=SEED, col_dy=12)


def _style(strength: float, cell_w: int) -> Style:
    """The default style at card size, cropped to the loop, with the relief at `strength`."""
    base = Style()
    return base.model_copy(
        update={
            "card": dataclasses.replace(base.card, display_px=cell_w * ZOOM),
            "cover": dataclasses.replace(base.cover, relief_strength=strength),
        }
    )


def _window(card: Image.Image) -> Image.Image:
    """The close window of a composed card that its cell shows: the same box in every cell."""
    width, height = card.size
    left, top = round(WINDOW_AT[0] * width), round(WINDOW_AT[1] * height)
    return card.crop((left, top, left + round(width / ZOOM), top + round(height / ZOOM)))


def paint_cells(
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
    cell_w: int,
) -> list[Image.Image]:
    """The close window of the card painted at each of `STRENGTHS`, in order, `cell_w * ZOOM` wide."""
    route, cache = Track.from_gpx(track), Cache(cache_dir)
    styles = [_style(s, cell_w) for s in STRENGTHS]
    basemap = fetch(route, cache, features, elevation, styles[0])
    key_dir = cache.plates_dir(cache.key(route, features, elevation))
    unlettered = Lettering((), (), None)
    cells: list[Image.Image] = []
    for strength, style in zip(STRENGTHS, styles, strict=True):
        plates = paint(basemap, style, key_dir / f"relief-{strength:g}")
        cells.append(_window(compose(plates, unlettered, basemap, style, attribution=False)))
    return cells


def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> Path:
    """Paint the card at each relief strength, crop one window of each and save the grid.

    Args:
        out_dir: Where the picture is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The path of the saved picture, `out_dir / "relief_strength.png"`.
    """
    cell_w = (GRID_W - LEFT - PAD - GAP * (len(STRENGTHS) - 1)) // len(STRENGTHS)
    cells = paint_cells(
        track=track, cache_dir=cache_dir, features=features, elevation=elevation, cell_w=cell_w
    )
    cell_h = round(cells[0].height * cell_w / cells[0].width)
    spec = GridSpec(GRID_W, len(STRENGTHS), 1, cell_h, LEFT, TOP, GAP, PAD, PAD)
    boxes = spec.boxes()
    sheet = Sheet(spec.height, GRID_W, 6.0, SEED)
    canvas = Canvas(0, 0, GRID_W, spec.height, GRID_W, spec.height)
    grid = paper_plate(sheet, canvas, PaperStyle(paper_foxing=0.0), GRID_W)
    for (x, y, _, _), cell in zip(boxes[0], cells, strict=True):
        resized = cell.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        grid[y : y + cell_h, x : x + cell_w] = np.asarray(resized, np.float32) / 255
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "relief_strength.png"
    save_image(label_grid(grid, boxes, STRENGTHS, [""], LABELS), path, seed=SEED)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint the relief at four strengths.")
    parser.add_argument("track", type=Path, help="the GPX file of the route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where the picture is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as a project URL"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
    )
