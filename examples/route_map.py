"""Rung 8 of the tutorial: a route map, the engine's first application.

The earlier rungs paint with the primitives directly; this one runs the four map
stages over a GPX track. `Track.from_gpx` reads the route, `Cache` keeps the
provider payloads and the painted plates under one directory, `fetch` builds the
basemap from what `OverpassFeatures` (the map features and land cover) and
`OpenTopoData` (the elevation) return, `paint` lays the paper, washes and pen
plates in the `Style.default()` look, `letter` places and writes the names, and
`compose` stacks them into one card, which is saved as `map.png`.

The first run with a track fetches from the public Overpass and OpenTopoData
servers, within their usage limits; `contact` (an email address, say) is sent
with each request so that their operators can reach the caller. A later run with
the same track reads the cache and fetches nothing. The card carries the
attribution `compose` draws by default, the credit the map data's licences ask
for.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/route_map.py route.gpx cache/ out/ you@example.org

`main` takes the providers as arguments, so a caller can pass its own; it does
not annotate the route or draw places of interest.
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


def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> Path:
    """Fetch what the cache lacks for a track, paint, letter and compose it, and save the card.

    Args:
        out_dir: Where `map.png` is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The path of the saved card, `out_dir / "map.png"`.
    """
    route = Track.from_gpx(track)
    cache = Cache(cache_dir)
    style = Style.default()
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
    parser = argparse.ArgumentParser(description="Paint a route map from a GPX track.")
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
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
    )
