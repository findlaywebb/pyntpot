"""The map's stages around the lettering: fetch a basemap, paint its plates, compose the card.

Key names: `fetch`, which fills a `Cache` for a `Track` through the providers it
is handed and builds the track's `Basemap` from the cached payloads; `paint`,
which paints a basemap's plates into a directory, or hands back the plates
already there when their manifest carries the current hash; `compose`, which
lays the painted plates, the route and the label plate into one raster card;
`FetchError`, raised when the cached features are gone once the fetch has run.
The stage between `paint` and `compose` is `maps.lettering.letter`.

`fetch` takes the style, because the card, the ribbon and the watercourse widths
are fitted to it. `paint` uses the basemap's card and layers as given: a basemap
fetched with one style and painted with another paints the first style's card,
in the second style's pigments. `paint` places the basemap's track on the card
for the plates it returns, both as recorded and pulled apart into strands where
the route runs back over itself, the line the route is drawn along.

`compose` draws the route along `Plates.strands` in the style's route ink and
pastes the label plate over it when the lettering has one; with no label plate
the card is handed over bare. Unless its `attribution` flag is off it then
writes the basemap's credits at the bottom right (`maps.attribution`).

It does not letter a card, and it reaches no network except through
the providers it is handed. It reads no configuration from the environment and
resolves no path against the working directory: the cache and the plates
directory are always arguments.

Invariants: `fetch` calls a provider only for a payload missing from the cache;
`paint` writes nothing when the plates in its directory carry the hash of the
basemap and the style's base groups, and every plate they name is on disk; the
returned `Plates.route_px` and `Plates.strands` each have one point per point
of `Basemap.track`.
"""

import dataclasses
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from PIL import Image

from pyntpot._port import card as strand_card
from pyntpot._port import mapcard
from pyntpot.maps.attribution import attribution_text, draw_attribution
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.layers import BasemapInputs, build_basemap
from pyntpot.maps.lettering import Lettering
from pyntpot.maps.painter.plates import paint_plates
from pyntpot.maps.plates import Plates
from pyntpot.maps.providers.base import Elevation, Features
from pyntpot.maps.style import Style
from pyntpot.maps.track import Track

log = logging.getLogger(__name__)


class FetchError(RuntimeError):
    """The cached features for a track were missing once the fetch had run."""


def fetch(
    track: Track,
    cache: Cache,
    features: Features,
    elevation: Elevation,
    style: Style,
    places: Sequence[Mapping[str, Any]] = (),
) -> Basemap:
    """Fetch whatever the cache lacks for a track and build its basemap.

    Args:
        track: The route to map.
        cache: Where the provider payloads are cached.
        features: The feature and land cover provider.
        elevation: The elevation provider.
        style: The style; its painter fields fit the card, the ribbon and the
            watercourse widths, and its basemap group says what is drawn.
        places: Places of interest to mark, each with a `name`, `lat` and
            `lng`; one without both coordinates, or off the card, is dropped.

    Returns:
        The basemap, carrying the track's times and both providers' credits.

    Raises:
        FetchError: When the features payload is missing after the fetch, as
            when the cache directory was changed underneath it.
    """
    key = cache.ensure(track, features, elevation)
    inputs = BasemapInputs(key, track, cache, [dict(place) for place in places])
    basemap = build_basemap(inputs, style)
    if basemap is None:
        raise FetchError(f"no cached features for key {key}: {cache.features_path(key)} is missing")
    return dataclasses.replace(
        basemap,
        track_time=track.time,
        credits=(features.credit, elevation.credit),
    )


def paint(basemap: Basemap, style: Style, out_dir: Path) -> Plates:
    """Paint a basemap's plates into a directory, unless the plates there are current.

    The basemap's card and layers are painted as given; only the style's
    pigments, brushes and paper come from `style`.

    Args:
        basemap: The basemap to paint.
        style: The style: its painter fields paint, its base digest goes into
            the hash, and its route ink sets the gap between strands.
        out_dir: Where the plates and their manifest are written; created when
            missing.

    Returns:
        The plates, freshly painted or already current, with the track placed
        on the card as `route_px` and pulled apart into `strands`.
    """
    plates = _current(out_dir, Cache.base_key(basemap, style))
    if plates is None:
        plates = paint_plates(basemap, style, out_dir)
    else:
        log.info("plates in %s are current, nothing repainted", out_dir)
    card = basemap.card
    route_px = tuple(card.xy(x, y) for x, y in basemap.track)
    gap_px = style.route_ink().px * strand_card.STRAND_GAP_WIDTHS
    strands = tuple(strand_card.separate_strands(list(route_px), gap_px))
    return dataclasses.replace(plates, route_px=route_px, strands=strands)


def compose(
    plates: Plates,
    lettering: Lettering,
    basemap: Basemap,
    style: Style,
    *,
    attribution: bool = True,
) -> Image.Image:
    """Compose painted, lettered plates into one raster card.

    The wash is multiplied over the paper, the route is drawn along
    `plates.strands` in the style's route ink (tinting the pen plate when the
    ink is a pen), the label plate is pasted over both when there is one, and
    the attribution is written last.

    Args:
        plates: The painted plates, with their strands set.
        lettering: The lettering; its label plate, when set, is pasted last.
        basemap: The basemap the plates were painted from, whose credits are
            owed on the card.
        style: The style whose route ink draws the route.
        attribution: Whether to write the basemap's credits at the bottom
            right; `False` leaves the card as the plates and lettering made it.

    Returns:
        The card, at the size of the paper plate.
    """
    card = mapcard._plates(plates)
    k = card.width / max(plates.card.display[0], 1)
    mapcard._route(card, plates, list(plates.strands), style.route_ink(), k)
    if lettering.plate_path is None:
        log.info("no label plate for %s, the card has no lettering", plates.directory)
    else:
        mapcard._paste_labels(card, lettering.plate_path)
    if attribution:
        draw_attribution(card, attribution_text(basemap.credits), style)
    return card


def _current(out_dir: Path, want: str) -> Plates | None:
    """Return the plates in `out_dir` when they carry hash `want` and are all on disk."""
    plates = Cache.load_plates(out_dir)
    return plates if plates is not None and plates.hash == want else None
