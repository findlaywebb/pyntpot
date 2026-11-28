"""A theme's preview card: the synthetic Lynmouth route painted in any theme, offline.

The card is made from `tests/fixtures/preview/`, a made-up route and the provider payloads
cached for it, which hold every feature a theme can get wrong and the awkward meetings between
them: a coast with an island, a river that splits round a bar, a lake with an island, roads over
water, lanes the route runs along, and small patches of every cover class. `preview` paints it
in a `Style` at `DISPLAY_PX` and returns the card and its `Lettering`; `main` reads a theme
with `Style.from_theme` (a packaged name or a .yaml file relative to the repository's top
directory) and saves the card. The card letters one curated landmark, Foreland Point, and one
journal note pinned to the riverside stretch of the route, track point `NOTE_POINT`.

Run it with a theme and an output directory::

    uv run python examples/theme_preview.py --theme default out/

The card is saved as `preview.png`. It copies the fixture into a temporary directory and
makes no request: its providers have no budget. It does not fetch, record or write anything
beside the card and the plates in the cache directory it is given.
"""

import argparse
import logging
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

from PIL import Image

from pyntpot.maps import (
    Annotations,
    Cache,
    JournalNote,
    Landmark,
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

#: The repository's top directory, which a theme path is relative to.
REPO_ROOT = Path(__file__).resolve().parent.parent

#: The preview fixture: the track and the payloads cached for it.
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "preview"

#: The card's display width in pixels.
DISPLAY_PX = 600

#: The index of the track point the journal note is pinned to, on the riverside stretch.
NOTE_POINT = 150

#: How the providers name the caller; never sent, since no request is made.
CONTACT = "pyntpot-preview@example.invalid"


def preview(
    style: Style,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
) -> tuple[Image.Image, Lettering]:
    """Paint the preview card in a style at `DISPLAY_PX`.

    Args:
        style: The style to paint in; copied with `card.display_px` set to `DISPLAY_PX`.
        track: The GPX file of the route.
        cache_dir: The fetch cache holding the fixture's payloads.
        features: The map feature and land cover provider.
        elevation: The elevation provider.

    Returns:
        The composed card and the lettering placed on it.
    """
    style = style.model_copy(update={"card": replace(style.card, display_px=DISPLAY_PX)})
    route = Track.from_gpx(track)
    cache = Cache(cache_dir)
    basemap = fetch(route, cache, features, elevation, style)
    plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
    annotations = Annotations(
        landmarks=[Landmark(name="Foreland Point")],
        notes=[
            JournalNote(
                text="High tide at Lynmouth",
                lat=route.lat[NOTE_POINT],
                lng=route.lng[NOTE_POINT],
            )
        ],
    )
    lettering = letter(plates, basemap, annotations, style)
    return compose(plates, lettering, basemap, style), lettering


def main(
    out_dir: Path,
    *,
    track: Path,
    cache_dir: Path,
    features: OverpassFeatures,
    elevation: OpenTopoData,
    theme: str = "default",
) -> Path:
    """Paint the preview card in a theme and save it.

    Args:
        out_dir: Where `preview.png` is written; created when missing.
        track: The GPX file of the route.
        cache_dir: The fetch cache holding the fixture's payloads.
        features: The map feature and land cover provider.
        elevation: The elevation provider.
        theme: A theme name or a .yaml file relative to the repository's top directory,
            read with `Style.from_theme`.

    Returns:
        The path of the saved card, `out_dir / "preview.png"`.
    """
    style = Style.from_theme(theme, relative_to=REPO_ROOT)
    card, _ = preview(
        style, track=track, cache_dir=cache_dir, features=features, elevation=elevation
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "preview.png"
    card.save(path)
    log.info("wrote %s", path)
    return path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paint a theme's preview card.")
    parser.add_argument("out_dir", type=Path, help="where preview.png is written")
    parser.add_argument(
        "--theme",
        default="default",
        help="a theme name or a .yaml file relative to the repository's top directory",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    with tempfile.TemporaryDirectory() as tmp:
        cache = Path(tmp) / "cache"
        shutil.copytree(FIXTURE, cache)
        main(
            args.out_dir,
            track=cache / "track.gpx",
            cache_dir=cache,
            features=OverpassFeatures(CONTACT, ("http://127.0.0.1:9/api/interpreter",), budget=0),
            elevation=OpenTopoData(CONTACT, "http://127.0.0.1:9", budget=0),
            theme=args.theme,
        )
