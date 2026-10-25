"""How-to: paint the route map with the route in another colour, width and treatment.

The card is the one `examples/route_map.py` paints, with changes to the route's ink only.
`Style.default()` gives the theme's look (or the theme file you name with `theme`);
`Style.with_route_ink` returns a copy whose route is inked in the colour and width you feed.
Only the route's ink changes, so the paper, the washes and the pen plates are the ones a plain
run painted: `paint` finds them current in the cache and repaints nothing, and `compose` draws
the route in the new ink.

`figure` picks the picture. `"violet"`, the default, is the card with the route in a deep violet
`#6a2c91` at 6.5 display pixels. `"grid"` is twelve small cards painted by a `for` loop: three
treatments down (a solid line; a wet pen, brush `MAJ1-e`; a dry pen, brush `MAJ3-e`) by four
colours across (maroon, the default pink, indigo and burnt sienna). The pen's brush is part of
what `paint` draws, so the grid paints its plates twice, once per brush, each in its own
directory, and the twelve cells are twelve composes over them. The cells are unlettered: the
hand's sizes are set in display pixels and would swamp a cell 180 pixels wide.

Public names it uses: from `pyntpot.maps`, `Cache`, `Lettering`, `OpenTopoData`,
`OverpassFeatures`, `Style`, `Track`, `compose`, `fetch`, `letter` and `paint`; from
`pyntpot.ink`, `PAINTERS_PIGMENTS`; it introduces none beyond `Style.with_route_ink`. It
writes `out_dir / "route_ink.png"` (`out_dir / "route_ink_grid.png"` for the grid).

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/how_to_route_ink.py route.gpx cache/ out/ https://example.org/your-project

`main` takes the providers as arguments, as `route_map.py` does; it does not annotate the
route.
"""

import argparse
import dataclasses
import logging
from pathlib import Path

from PIL import Image

from pyntpot.ink import PAINTERS_PIGMENTS
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
#: A grid cell's width in pixels as shown: four cells make the grid's 720 pixels.
CELL_PX = 180
#: The width a cell's card is painted at, in display pixels, before it is brought down to `CELL_PX`:
#: the brushes' widths are set in display pixels, so a card painted at 180 would be all brush.
PAINT_PX = 360
#: How much of the route's width a cell draws, kept at the card's usual width so that the route reads at 180 pixels.
CELL_ROUTE_SCALE = 1.0
#: The grid's pens, one row each after the solid one: a wet brush and a dry one.
WET_BRUSH, DRY_BRUSH = "MAJ1-e", "MAJ3-e"
#: The grid's colours across: the maroon, the default pink, indigo and burnt sienna.
COLOURS: tuple[str, ...] = (
    "#7b2335",
    "#c22050",
    PAINTERS_PIGMENTS["indigo"],
    PAINTERS_PIGMENTS["burnt_sienna"],
)
#: The grid's rows: the treatment, then the pen brush its plates are painted with.
ROWS: tuple[tuple[str, str], ...] = (("solid", WET_BRUSH), ("pen", WET_BRUSH), ("pen", DRY_BRUSH))


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


def _row_style(small: Style, treatment: str, brush: str) -> Style:
    """The style of one row: the card at cell size with the row's treatment and pen brush."""
    ride = dataclasses.replace(small.route_inks.ride, style=treatment)
    return small.model_copy(
        update={
            "route": dataclasses.replace(small.route, route_pen_brush=brush),
            "route_inks": dataclasses.replace(small.route_inks, ride=ride),
        }
    )


def _grid(
    out_dir: Path,
    route: Track,
    cache: Cache,
    providers: tuple[OverpassFeatures, OpenTopoData],
    theme: str | None,
) -> Path:
    """Paint the twelve cells, three treatments by four colours, and save `route_ink_grid.png`."""
    features, elevation = providers
    base = _base(theme)
    small = base.model_copy(update={"card": dataclasses.replace(base.card, display_px=PAINT_PX)})
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
    for treatment, brush in ROWS:
        row = _row_style(small, treatment, brush)
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
                for colour in COLOURS
            ]
        )
    cell_h = round(cells[0][0].height * CELL_PX / cells[0][0].width)
    cell_w = CELL_PX
    grid = Image.new("RGB", (cell_w * len(COLOURS), cell_h * len(ROWS)))
    for r, row_cells in enumerate(cells):
        for c, cell in enumerate(row_cells):
            grid.paste(
                cell.resize((cell_w, cell_h), Image.Resampling.LANCZOS), (c * cell_w, r * cell_h)
            )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "route_ink_grid.png"
    grid.save(path)
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
