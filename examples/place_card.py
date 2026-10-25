"""A focus place's route map: the card the README, the gallery and the social preview show.

The card is the one `examples/route_map.py` paints, with two options. `theme` names a TOML
theme file by its path relative to the repository's top directory, read with
`Style.from_toml`; without it the card takes `Style.default()`. `size` is the card's
display width in pixels, 900 unless you say otherwise: the script copies the style with
that `card.display_px` and paints the card at it, so the pixel grid, and with it the
hand's lettering, is set for that width. The track, the cache and the providers are the
ones `route_map.py` takes, and the four stages are the same.

`margin_m` and `landcover_margin_m` are the fetch margins the place's cache was recorded
with, in metres (the library's defaults when absent), for a place recorded wider; `place` names
the place's fixture.

The README's hero is the Keswick card at 1200 pixels. The five place cards of the gallery,
Keswick, the Quiraing on Trotternish, Yr Wyddfa, Oxford and Y Fenni, are painted at 720.
Y Fenni takes `examples/themes/y-fenni.toml`, which letters the Welsh name where
OpenStreetMap carries one.

Run it with a track, a cache directory, an output directory and a contact::

    uv run python examples/place_card.py route.gpx cache/ out/ you@example.org

The card is saved as `map.png`. It does not annotate the route or fetch anything the
cache already holds.
"""

import argparse
import logging
from dataclasses import replace
from pathlib import Path

from pyntpot.maps import (
    Cache,
    FetchMargins,
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

#: The repository's top directory, which a theme path is relative to.
REPO_ROOT = Path(__file__).resolve().parent.parent


def main(  # noqa: PLR0913 (the script contract fixes these keywords)
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
    theme: str | None = None,
    size: int = 900,
    margin_m: float | None = None,
    landcover_margin_m: float | None = None,
    place: str | None = None,
) -> Path:
    """Paint a place's route map at a display width, in a theme if one is named, and save the card.

    Args:
        out_dir: Where `map.png` is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache: provider payloads, and the plates painted from them.
        features: The map feature and land cover provider.
        elevation: The elevation provider.
        theme: A TOML theme file, as a path relative to the repository's top directory;
            `Style.default()` when absent.
        size: The card's display width in pixels.
        margin_m: How far beyond the track's box the features and elevation are fetched, in
            metres; the library's default when absent.
        landcover_margin_m: The same for land cover; the larger of its default and
            `margin_m` when absent. Both must match what the cache was recorded with, as they are part of its key.
        place: The name of the place's fixture, kept for the caller; the card does not read it.

    Returns:
        The path of the saved card, `out_dir / "map.png"`.
    """
    base = Style.from_toml(REPO_ROOT / theme) if theme else Style.default()
    style = base.model_copy(update={"card": replace(base.card, display_px=size)})
    route = Track.from_gpx(track)
    defaults = FetchMargins()
    features_m = defaults.features_m if margin_m is None else margin_m
    landcover_m = (
        max(defaults.landcover_m, features_m) if landcover_margin_m is None else landcover_margin_m
    )
    cache = Cache(cache_dir, FetchMargins(features_m, landcover_m))
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
    parser = argparse.ArgumentParser(description="Paint a place's route map.")
    parser.add_argument("track", type=Path, help="the GPX file of the route")
    parser.add_argument("cache_dir", type=Path, help="the fetch cache directory")
    parser.add_argument("out_dir", type=Path, help="where map.png is written")
    parser.add_argument(
        "contact", help="how the public servers' operators can reach you, such as an email"
    )
    parser.add_argument(
        "--theme", help="a TOML theme file, relative to the repository's top directory"
    )
    parser.add_argument("--size", type=int, default=900, help="the card's display width in pixels")
    parser.add_argument("--margin-m", type=float, help="feature and elevation margin, metres")
    parser.add_argument("--landcover-margin-m", type=float, help="land cover margin, metres")
    parser.add_argument("--place", help="the name of the place's fixture")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    main(
        args.out_dir,
        track=args.track,
        cache_dir=args.cache_dir,
        features=OverpassFeatures(args.contact),
        elevation=OpenTopoData(args.contact),
        theme=args.theme,
        size=args.size,
        margin_m=args.margin_m,
        landcover_margin_m=args.landcover_margin_m,
        place=args.place,
    )
