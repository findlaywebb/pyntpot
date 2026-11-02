"""How-to: paint the route map with the route in another colour, width and treatment.

The card is the one `examples/route_map.py` paints, with changes to the route's ink only.
`Style.default()` gives the theme's look (or the theme file you name with `theme`);
`Style.with_route_ink` returns a copy whose route is inked in the colour and width you feed.
Only the route's ink changes, so the paper, the washes and the pen plates are the ones a plain
run painted: `paint` finds them current in the cache and repaints nothing, and `compose` draws
the route in the new ink.

`figure` picks the picture. `"violet"`, the default, is the card with the route in a deep violet
`#6a2c91` at 6.5 display pixels. `"grid"` is six small cards painted by a `for` loop: two pens down
(a wet pen, brush `MAJ1-e`; a dry pen, brush `MAJ3-e`) by three colours across (maroon, indigo and
burnt sienna). Each card is cropped to the loop, the route is drawn in the normal blend so that it
keeps its colour over water, and the rows and the columns are named in the hand. The pen's brush is
part of what `paint` draws, so the grid paints its plates twice, once per brush, each in its own
directory, and the six cells are six composes over them. The cells carry no names of places: the
hand's sizes are set in display pixels and would swamp a cell 200 pixels wide.

Public names it uses: from `pyntpot.maps`, `Cache`, `Lettering`, `OpenTopoData`,
`OverpassFeatures`, `Style`, `Track`, `compose`, `fetch`, `letter` and `paint`; from
`pyntpot.ink`, `PAINTERS_PIGMENTS`, `BrushStyle`, `Canvas`, `PaperStyle`, `Sheet`, `paper_plate`
and `save_image`; from `pyntpot.letters`, `FaceStyle`, `Hand`, `HandStyle`, `Mark`, `NibGroups`,
`NibStyle`, `NibSurface`, `Setting` and `nib_plate`; it introduces none beyond
`Style.with_route_ink`. It writes `out_dir / "route_ink.png"` (`out_dir / "route_ink_grid.png"` for the grid).

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/how_to_route_ink.py route.gpx cache/ out/ https://example.org/your-project

`main` takes the providers as arguments, as `route_map.py` does; it does not annotate the
route.
"""

import argparse
import dataclasses
import logging
import tempfile
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from PIL import Image

from pyntpot.ink import (
    PAINTERS_PIGMENTS,
    BrushStyle,
    Canvas,
    PaperStyle,
    Sheet,
    paper_plate,
    save_image,
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
from pyntpot.maps import (
    Cache,
    Lettering,
    OpenTopoData,
    OverpassFeatures,
    Style,
    Track,
    compose,
    fetch,
    letter,
    paint,
)

log = logging.getLogger(__name__)

#: The pictures `main` paints.
FIGURES: tuple[str, ...] = ("violet", "grid")
#: The repository's top directory, which a theme path is relative to.
REPO_ROOT = Path(__file__).resolve().parent.parent
#: The route's colour, a `#` and six hexadecimal digits.
ROUTE_COLOUR = "#6a2c91"
#: The route's width, in display pixels.
ROUTE_WIDTH_PX = 6.5
#: The grid's width in pixels, the room left of the cells for the rows' names, above them for the
#: columns' names, round them, and between them.
GRID_W, LEFT, TOP, PAD, GAP = 720, 104, 44, 12, 10
#: How many times a cell's size its card is painted before it is brought down with Lanczos: the
#: brushes' widths are set in display pixels, so a card painted at cell size would be all brush.
PAINT_SCALE = 2
#: How much of the route's width a cell draws; the cell is small, so the route is a little heavier.
CELL_ROUTE_SCALE = 1.5
#: The pen brushes, one row each: a wet brush and a dry one, named for the row.
ROWS: tuple[tuple[str, str], ...] = (("wet pen", "MAJ1-e"), ("dry pen", "MAJ3-e"))
#: The grid's colours across, named for the column: the maroon, indigo and burnt sienna.
COLOURS: tuple[tuple[str, str], ...] = (
    ("maroon", "#7b2335"),
    ("indigo", PAINTERS_PIGMENTS["indigo"]),
    ("burnt sienna", PAINTERS_PIGMENTS["burnt_sienna"]),
)
#: The ribbon fields that crop a cell to the loop: a small fitted ribbon and little growth round
#: the track, with the wash still wide enough to reach every edge.
CROP: dict[str, float] = {
    "ribbon_k": 4.0,
    "ribbon_c": 60.0,
    "ribbon_min_m": 260.0,
    "card_grow_mult": 0.9,
}
#: The size of the names on the grid, in pixels, the ink they are lettered in and the hand's seed.
LABEL_PX, LABEL_INK, SEED = 21.0, "#4a3a2a", 7
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2


def _base(theme: str | None) -> Style:
    """The theme file's style, relative to the repository's top directory, or `Style.default()`."""
    return Style.from_toml(REPO_ROOT / theme) if theme else Style.default()


def _violet(
    out_dir: Path,
    route: Track,
    cache: Cache,
    providers: tuple[OverpassFeatures, OpenTopoData],
    theme: str | None,
) -> Path:
    """Paint the card with the route in `ROUTE_COLOUR` and save it as `route_ink.png`."""
    features, elevation = providers
    style = _base(theme).with_route_ink(colour=ROUTE_COLOUR, width_px=ROUTE_WIDTH_PX)
    basemap = fetch(route, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
    lettering = letter(plates, basemap, None, style)
    card = compose(plates, lettering, basemap, style)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "route_ink.png"
    card.save(path)
    return path


def _row_style(small: Style, brush: str) -> Style:
    """The style of one row: the card at cell size, a wet pen with the row's brush."""
    ride = dataclasses.replace(small.route_inks.ride, style="pen")
    return small.model_copy(
        update={
            "route": dataclasses.replace(small.route, route_pen_brush=brush),
            "route_inks": dataclasses.replace(small.route_inks, ride=ride),
        }
    )


def _lettered(grid: np.ndarray, settings: Sequence[Setting]) -> np.ndarray:
    """Letter the settings over the grid with the hand and return the result.

    The nib plate is painted at `NIB_SCALE` times the grid's size, then brought down to it with
    Lanczos and laid over the grid by its alpha.
    """
    h, w = grid.shape[:2]
    big_w, big_h = w * NIB_SCALE, h * NIB_SCALE
    face, hand_style = FaceStyle(), HandStyle()
    hand = Hand(face, hand_style)
    rng = hand.generator(SEED)
    marks: list[Mark] = [mark for s in settings for mark in hand.write(s, rng)]
    canvas = Canvas(0, 0, big_w, big_h, big_w, big_h)
    surface = NibSurface(canvas, NIB_SCALE, np.zeros((big_h, big_w), np.float32), 6.0 * NIB_SCALE)
    nib = NibStyle(label_ink=LABEL_INK, label_pen_width_px=1.5)
    groups = NibGroups(nib, face, hand_style, BrushStyle(), PaperStyle())
    with tempfile.TemporaryDirectory() as scratch:
        written = nib_plate(marks, surface, groups, Path(scratch) / "plate.webp")
        if written is None:
            raise RuntimeError("the hand wrote no marks")
        with Image.open(written) as plate:
            small = plate.convert("RGBa").resize((w, h), Image.Resampling.LANCZOS)
            rgba = np.asarray(small.convert("RGBA"), np.float32) / 255
    alpha = rgba[..., 3:]
    return grid * (1 - alpha) + rgba[..., :3] * alpha


def _grid(
    out_dir: Path,
    route: Track,
    cache: Cache,
    providers: tuple[OverpassFeatures, OpenTopoData],
    theme: str | None,
) -> Path:
    """Paint the six cells, two pens by three colours, name them and save `route_ink_grid.png`."""
    features, elevation = providers
    base = _base(theme)
    cell_w = (GRID_W - LEFT - PAD - GAP * (len(COLOURS) - 1)) // len(COLOURS)
    small = base.model_copy(
        update={
            "card": dataclasses.replace(base.card, display_px=cell_w * PAINT_SCALE),
            "ribbon": dataclasses.replace(base.ribbon, **CROP),
        }
    )
    ink = small.route_ink()
    small = small.with_route_ink(width_px=ink.px * CELL_ROUTE_SCALE)
    small = small.model_copy(
        update={
            "route": dataclasses.replace(
                small.route, route_pen_width_px=small.route.route_pen_width_px * CELL_ROUTE_SCALE
            )
        }
    )
    basemap = fetch(route, cache, features, elevation, small)
    key_dir = cache.plates_dir(cache.key(route, features, elevation))
    unlettered = Lettering((), (), None)
    cells: list[list[Image.Image]] = []
    for _, brush in ROWS:
        row = _row_style(small, brush)
        plates = paint(basemap, row, key_dir / brush)
        cells.append(
            [
                compose(
                    plates,
                    unlettered,
                    basemap,
                    row.with_route_ink(colour=colour),
                    attribution=False,
                )
                for _, colour in COLOURS
            ]
        )
    cell_h = round(cells[0][0].height * cell_w / cells[0][0].width)
    grid_h = TOP + len(ROWS) * cell_h + (len(ROWS) - 1) * GAP + PAD
    sheet = Sheet(grid_h, GRID_W, 6.0, SEED)
    canvas = Canvas(0, 0, GRID_W, grid_h, GRID_W, grid_h)
    grid = paper_plate(sheet, canvas, PaperStyle(paper_foxing=0.0), GRID_W)
    settings: list[Setting] = []
    for r, row_cells in enumerate(cells):
        y = TOP + r * (cell_h + GAP)
        for c, cell in enumerate(row_cells):
            x = LEFT + c * (cell_w + GAP)
            resized = cell.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            grid[y : y + cell_h, x : x + cell_w] = np.asarray(resized, np.float32) / 255
            if r == 0:
                anchor = (x + cell_w / 2, TOP - 14)
                settings.append(
                    Setting(COLOURS[c][0], LABEL_PX, anchor=anchor, align="middle", wash=False)
                )
        anchor = (LEFT - 12, y + cell_h / 2 + 7)
        settings.append(Setting(ROWS[r][0], LABEL_PX, anchor=anchor, align="end", wash=False))
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "route_ink_grid.png"
    save_image(_lettered(grid, settings), path, seed=SEED)
    return path


def main(  # noqa: PLR0913 (the script contract fixes these keywords)
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
    figure: str = "violet",
    theme: str | None = None,
) -> Path:
    """Paint the violet card or the grid of route inks and save it.

    Args:
        out_dir: Where the picture is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.
        figure: The picture, one of `FIGURES`.
        theme: A TOML theme file, as a path relative to the repository's top directory;
            `Style.default()` when absent.

    Returns:
        The path of the saved picture: `out_dir / "route_ink.png"`, or
        `out_dir / "route_ink_grid.png"` for the grid.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {FIGURES}, not {figure!r}")
    route = Track.from_gpx(track)
    cache = Cache(cache_dir)
    paint_figure = _violet if figure == "violet" else _grid
    path = paint_figure(out_dir, route, cache, (features, elevation), theme)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a route map with a recoloured route.")
    parser.add_argument("track", type=Path, help="the GPX file of the route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where the picture is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as a project URL"
    )
    parser.add_argument("--figure", choices=FIGURES, default="violet", help="the picture")
    parser.add_argument(
        "--theme", help="a TOML theme file, relative to the repository's top directory"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
        figure=args.figure,
        theme=args.theme,
    )
