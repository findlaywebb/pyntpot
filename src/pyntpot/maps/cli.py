"""The `pyntpot` command: `pyntpot map` turns a GPX track into a painted map PNG.

Key names: `main`, the entry point `pyntpot` runs; `build_parser`, the argparse
parser it reads.

`pyntpot map TRACK.gpx -o OUT.png --cache DIR --contact STR [--style FILE]
[--no-attribution]` reads the track, fills the cache directory for any payload it
lacks from Overpass and OpenTopoData (identified by `--contact`), paints the plates
into the cache's plates directory for the track's key, letters the card with no
annotations and composes the PNG. A cache that already holds the payloads sends no
request.

It uses the standard library's `argparse` only, takes every path and the contact as
arguments, and reads nothing from the environment. Logging is configured inside
`main` and nowhere else; it writes the progress to standard error. It does not
take annotations, places or provider options.

Invariants: `main` returns 0 on success; a missing required argument exits with
status 2, as `argparse` does.
"""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from pyntpot.maps import pipeline
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering import letter
from pyntpot.maps.providers.opentopodata import OpenTopoData
from pyntpot.maps.providers.overpass import OverpassFeatures
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

log = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Return the parser for the `pyntpot` command and its `map` subcommand."""
    parser = argparse.ArgumentParser(prog="pyntpot", description="Hand-drawn watercolour maps.")
    commands = parser.add_subparsers(dest="command", required=True)
    route = commands.add_parser("map", help="paint a GPX track as a map PNG")
    route.add_argument("track", type=Path, help="the GPX file to map")
    route.add_argument("-o", "--output", type=Path, required=True, help="the PNG to write")
    route.add_argument("--cache", type=Path, required=True, help="the cache directory")
    route.add_argument(
        "--contact",
        required=True,
        help="how the data providers' operators can reach you, such as an email address",
    )
    route.add_argument("--style", type=Path, help="a TOML theme; the default theme when absent")
    route.add_argument(
        "--no-attribution", action="store_true", help="leave the data attribution off the map"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the `pyntpot` command.

    Args:
        argv: The arguments after the program name; `sys.argv[1:]` when `None`.

    Returns:
        The exit status: 0 on success. Bad arguments exit with status 2 through
        `argparse`.
    """
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    track = Track.from_gpx(args.track)
    style = Style.from_toml(args.style) if args.style else Style.default()
    cache = Cache(args.cache)
    features = OverpassFeatures(args.contact)
    elevation = OpenTopoData(args.contact)
    basemap = pipeline.fetch(track, cache, features, elevation, style)
    plates = pipeline.paint(basemap, style, cache.plates_dir(cache.key(track, features, elevation)))
    lettering = letter(plates, basemap, None, style)
    image = pipeline.compose(plates, lettering, basemap, style, attribution=not args.no_attribution)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
    log.info("wrote %s", args.output)
    return 0
