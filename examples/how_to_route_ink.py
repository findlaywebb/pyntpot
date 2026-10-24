"""How-to: paint the route map with the route in another colour and width.

The card is the one `examples/route_map.py` paints, with one change. `Style.default()`
gives the theme's look; `Style.with_route_ink` returns a copy of it whose route is inked in
the colour and width you feed, here a deep violet `#6a2c91` at 6.5 display pixels in place
of the theme's crimson at 5.4. Only the route's ink changes, so the paper, the washes and
the pen plates are the ones a plain run painted: `paint` finds them current in the cache
and repaints nothing, and `compose` draws the route in the new ink.

Public names it uses: from `pyntpot.maps`, `Cache`, `OpenTopoData`, `OverpassFeatures`,
`Style`, `Track`, `compose`, `fetch`, `letter` and `paint`; it introduces none beyond
`Style.with_route_ink`. It writes `out_dir / "route_ink.png"`.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/how_to_route_ink.py route.gpx cache/ out/ https://example.org/your-project

`main` takes the providers as arguments, as `route_map.py` does; it does not annotate the
route.
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

#: The route's colour, a `#` and six hexadecimal digits.
ROUTE_COLOUR = "#6a2c91"
#: The route's width, in display pixels.
ROUTE_WIDTH_PX = 6.5


def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> Path:
    """Paint a track's card with the route in `ROUTE_COLOUR` and save it as `route_ink.png`.

    Args:
        out_dir: Where `route_ink.png` is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The path of the saved card, `out_dir / "route_ink.png"`.
    """
    route = Track.from_gpx(track)
    cache = Cache(cache_dir)
    style = Style.default().with_route_ink(colour=ROUTE_COLOUR, width_px=ROUTE_WIDTH_PX)
    basemap = fetch(route, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
    lettering = letter(plates, basemap, None, style)
    card = compose(plates, lettering, basemap, style)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "route_ink.png"
    card.save(path)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a route map with a recoloured route.")
    parser.add_argument("track", type=Path, help="the GPX file of the route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where route_ink.png is written")
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
