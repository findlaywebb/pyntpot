"""How-to: case a road and lift the route with a line effect in a theme file.

Two figures, picked by `figure`, both painted on the Ambleside fixture.

- `"card"`, the default, is the card in `examples/themes/ambleside-cased.yaml`: the Ambleside
  look, with its main road cased and its route lifted by a shadow. Both are effect presets named
  under `line_effects:` in the theme, so the script paints nothing special: it loads the theme
  and runs `fetch`, `paint`, `letter` and `compose`.
- `"presets"` is four small cards cropped to the loop, two across and two down: the route with no effect,
  then with the `cased`, `halo` and `lifted` presets. The route's effects are laid at compose,
  so the plates are painted once and composed four times. Each cell's style comes from a theme
  file the script writes in a temporary directory, holding `extends: <ambleside.yaml>` and
  `line_effects: {route: <preset>}`, and read with `Style.from_yaml`; the no-effect cell is
  `ambleside.yaml` itself. The cells carry no place names, as `how_to_route_ink.py`'s grid does.

It does not set an effect's numbers: a preset's values are the package's, and a theme that wants
other numbers writes the stack out in `line_effects:`. It writes `out_dir / "line_effects.png"`
(`out_dir / "line_effects_presets.png"` for the presets).

Public names it uses: from `pyntpot.maps`, `Cache`, `Lettering`, `OpenTopoData`,
`OverpassFeatures`, `Style`, `Track`, `compose`, `fetch`, `letter` and `paint`; from
`pyntpot.ink`, `Canvas`, `Colour`, `PaperStyle`, `Sheet`, `paper_plate` and `save_image`; from
`pyntpot.letters`, `Setting`;
`GridSpec`, `LabelStyle` and `label_grid` from the sibling `labelled_grid.py`. It introduces none.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/how_to_line_effects.py route.gpx cache/ out/ https://example.org/your-project
"""

import argparse
import dataclasses
import logging
import tempfile
from pathlib import Path

import numpy as np
from labelled_grid import GridSpec, LabelStyle, label_grid
from PIL import Image

from pyntpot.ink import Canvas, Colour, PaperStyle, Sheet, paper_plate, save_image
from pyntpot.letters import Setting
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
FIGURES: tuple[str, ...] = ("card", "presets")
#: The example themes' directory.
THEMES_DIR = Path(__file__).resolve().parent / "themes"
#: The theme the card is painted in, and the one the presets extend.
CARD_THEME = THEMES_DIR / "ambleside-cased.yaml"
BASE_THEME = THEMES_DIR / "ambleside.yaml"
#: The cells across the presets figure, named for the route's effect: none, then each preset.
CELLS: tuple[str, ...] = ("none", "cased", "halo", "lifted")
#: How many cells sit across the presets figure.
ACROSS = 2
#: The presets figure's width in pixels, the room left of the cells, above them, round them and
#: between them (a row's gap holds the names of the row below).
#: The cells sit two across and two down.
GRID_W, LEFT, TOP, PAD, GAP = 720, 12, 44, 12, 34
#: How many times a cell's size its card is painted before it is brought down with Lanczos.
PAINT_SCALE = 2
#: How much of the route's width a cell draws; the cell is small, so the route is a little heavier.
CELL_ROUTE_SCALE = 1.5
#: The ribbon fields that crop a cell to the loop, as `how_to_route_ink.py` crops its grid.
CROP: dict[str, float] = {
    "ribbon_k": 4.0,
    "ribbon_c": 60.0,
    "ribbon_min_m": 260.0,
    "card_grow_mult": 0.9,
}
#: The size of the names on the figure, in pixels, the ink they are lettered in and the hand's seed.
LABEL_PX, LABEL_INK, SEED = 21.0, Colour("#4a3a2a"), 7
#: How many times its size the nib plate is painted before it is brought down.
NIB_SCALE = 2
#: How the names are lettered.
LABELS = LabelStyle(
    px=LABEL_PX, ink=LABEL_INK, pen_px=1.5, gran_px=6.0 * NIB_SCALE, seed=SEED, col_dy=12
)


def _card(
    out_dir: Path,
    route: Track,
    cache: Cache,
    providers: tuple[OverpassFeatures, OpenTopoData],
) -> Path:
    """Paint the card in `ambleside-cased.yaml` and save it as `line_effects.png`."""
    features, elevation = providers
    style = Style.from_yaml(CARD_THEME)
    basemap = fetch(route, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
    card = compose(plates, letter(plates, basemap, None, style), basemap, style)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "line_effects.png"
    card.save(path)
    return path


def _cell_style(style: Style, cell_w: int) -> Style:
    """The style at cell size: a card `cell_w` wide at `PAINT_SCALE`, cropped to the loop."""
    small = style.model_copy(
        update={
            "card": dataclasses.replace(style.card, display_px=cell_w * PAINT_SCALE),
            "ribbon": dataclasses.replace(style.ribbon, **CROP),
        }
    )
    small = small.with_route_ink(width_px=small.route_ink.px * CELL_ROUTE_SCALE)
    return small.model_copy(
        update={
            "route": dataclasses.replace(
                small.route, route_pen_width_px=small.route.route_pen_width_px * CELL_ROUTE_SCALE
            )
        }
    )


def _styles(scratch: Path) -> list[Style]:
    """The style of each cell: `ambleside.yaml`, then one theme file written in `scratch` per preset."""
    styles = [Style.from_yaml(BASE_THEME)]
    for name in CELLS[1:]:
        theme = scratch / f"{name}.yaml"
        theme.write_text(
            f"extends: {BASE_THEME}\nline_effects:\n  route: {name}\n", encoding="utf-8"
        )
        styles.append(Style.from_yaml(theme))
    return styles


def _presets(
    out_dir: Path,
    route: Track,
    cache: Cache,
    providers: tuple[OverpassFeatures, OpenTopoData],
) -> Path:
    """Paint the cells once, compose each preset over them, name them and save `line_effects_presets.png`."""
    features, elevation = providers
    cell_w = (GRID_W - LEFT - PAD - GAP * (ACROSS - 1)) // ACROSS
    with tempfile.TemporaryDirectory() as scratch:
        styles = [_cell_style(s, cell_w) for s in _styles(Path(scratch))]
    basemap = fetch(route, cache, features, elevation, styles[0])
    plates = paint(basemap, styles[0], cache.plates_dir(cache.key(route, features, elevation)))
    unlettered = Lettering((), (), None)
    cells = [compose(plates, unlettered, basemap, s, attribution=False) for s in styles]
    cell_h = round(cells[0].height * cell_w / cells[0].width)
    spec = GridSpec(GRID_W, ACROSS, len(CELLS) // ACROSS, cell_h, LEFT, TOP, GAP, PAD, PAD)
    boxes = spec.boxes()
    sheet = Sheet(spec.height, GRID_W, 6.0, SEED)
    canvas = Canvas(0, 0, GRID_W, spec.height, GRID_W, spec.height)
    grid = paper_plate(sheet, canvas, PaperStyle(paper_foxing=0.0), GRID_W)
    flat = [box for row in boxes for box in row]
    for (x, y, _, _), cell in zip(flat, cells, strict=True):
        resized = cell.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        grid[y : y + cell_h, x : x + cell_w] = np.asarray(resized, np.float32) / 255
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "line_effects_presets.png"
    # The first row is named above its cells by `label_grid`; each later row's names sit in the gap above it.
    later = [
        Setting(
            name,
            LABELS.px,
            anchor=(x + w / 2, y - LABELS.col_dy),
            align="middle",
            wash=False,
        )
        for name, (x, y, w, _) in zip(CELLS[ACROSS:], flat[ACROSS:], strict=True)
    ]
    lettered = label_grid(grid, boxes, CELLS[:ACROSS], ("",) * len(boxes), LABELS, extra=later)
    save_image(lettered, path, seed=SEED)
    return path


def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
    figure: str = "card",
) -> Path:
    """Paint the cased card or the presets figure and save it.

    Args:
        out_dir: Where the picture is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.
        figure: The picture, one of `FIGURES`.

    Returns:
        The path of the saved picture: `out_dir / "line_effects.png"`, or
        `out_dir / "line_effects_presets.png"` for the presets.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {FIGURES}, not {figure!r}")
    route = Track.from_gpx(track)
    paint_figure = _card if figure == "card" else _presets
    path = paint_figure(out_dir, route, Cache(cache_dir), (features, elevation))
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a route map with line effects.")
    parser.add_argument("track", type=Path, help="the GPX file of the route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where the picture is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as a project URL"
    )
    parser.add_argument("--figure", choices=FIGURES, default="card", help="the picture")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
        figure=args.figure,
    )
