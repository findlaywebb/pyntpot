"""One route map in four themes: the map is not limited to the default look.

`Style.default()` paints the shipped look, but a style is only data. A theme is a TOML
file with one table per style group, and `Style.from_toml` reads it. This script paints
the same route, over the same cached payloads, in one of four example themes kept in
`examples/themes/`: `pen-and-ink` (no colour washes, ink on paper), `sepia` (faded warm
browns on yellowed paper), `bold` (saturated pigments and a strong route ink) and
`winter` (cool greys and blues on pale paper). Each is a copy of the default theme with
a few groups changed: the paper's colour, the pigments, the inks of the lettering and
the route, and whether the cover and relief are painted at all.

`figure` names the theme. The track, the cache and the providers are the ones
`route_map.py` takes, and the paint is the same four stages; only the style differs.
The cache keeps one set of painted plates per track, stamped with the style's hash, so
a run with a different theme repaints the plates and leaves the fetched payloads alone.

Run it with a theme name, a track, a cache directory, an output directory and a contact::

    uv run python examples/map_styles.py winter route.gpx cache/ out/ you@example.org

The card is saved as `map.png`. It does not change what is drawn, only how: the roads,
the rivers and the names are the default theme's choices in every theme.
"""

import argparse
import logging
from pathlib import Path

from pyntpot.maps import (
    Cache,
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

#: The example themes, by the stem of their file in `themes/` beside this script.
FIGURES: tuple[str, ...] = ("pen-and-ink", "sepia", "bold", "winter")
THEMES_DIR = Path(__file__).resolve().parent / "themes"


def main(
    out_dir: Path,
    *,
    figure: str,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> Path:
    """Paint the route map in one example theme and save the card.

    Args:
        out_dir: Where `map.png` is written; created when missing.
        figure: The theme, one of `FIGURES`.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The path of the saved card, `out_dir / "map.png"`.

    Raises:
        ValueError: When `figure` is not one of `FIGURES`.
    """
    if figure not in FIGURES:
        raise ValueError(f"figure must be one of {FIGURES}, not {figure!r}")
    style = Style.from_toml(THEMES_DIR / f"{figure}.toml")
    route = Track.from_gpx(track)
    cache = Cache(cache_dir)
    basemap = fetch(route, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
    lettering = letter(plates, basemap, None, style)
    card = compose(plates, lettering, basemap, style)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "map.png"
    card.save(path)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a route map in an example theme.")
    parser.add_argument("figure", choices=FIGURES, help="the example theme")
    parser.add_argument("track", type=Path, help="the GPX file of the route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where map.png is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as an email"
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        figure=args.figure,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
    )
