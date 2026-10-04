"""A small painting job to run the painter's phases against, built from real objects."""

import dataclasses
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pyntpot.maps.basemap import Basemap, Layers, Line
from pyntpot.maps.card import Card
from pyntpot.maps.painter.job import PaintJob
from pyntpot.maps.projection import track_projection
from pyntpot.maps.style import Style

#: The card: 320 by 240 metres painted at 160 by 120 pixels, two metres a pixel.
CARD = Card(
    box=(0.0, 0.0, 320.0, 240.0), display=(80, 60), render=(160, 120), mpp=2.0, mpp_display=4.0
)


def square(x0: float, y0: float, x1: float, y1: float) -> Line:
    """One closed rectangular ring, in card metres."""
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0))


def tiny_style(
    *, wash: Mapping[str, Any] | None = None, cover: Mapping[str, Any] | None = None
) -> Style:
    """The packaged style with some wash and cover fields moved."""
    base = Style.default()
    return base.model_copy(
        update={
            "wash": dataclasses.replace(base.wash, **(wash or {})),
            "cover": dataclasses.replace(base.cover, **(cover or {})),
        }
    )


def tiny_job(out_dir: Path, style: Style | None = None, **layers: Any) -> PaintJob:
    """A job over `CARD` whose layers hold nothing but what is passed in."""
    projection = track_projection([51.2250, 51.2255], [-3.8400, -3.8395])[0]
    held: dict[str, Any] = {
        "route": ((10.0, 10.0), (300.0, 200.0)),
        "cover": {},
        "cover_order": (),
        "lakes": (),
        "sea": (),
        "coastline": (),
        "roads": (),
        "rivers": (),
        "elevation": None,
        "ribbon_m": 120,
        "wet_px": {},
        "minor_roads": False,
        "blotch_m": 40.0,
        "dab_spacing_m": 30.0,
        "gran_m": 12.0,
    }
    held.update(layers)
    basemap = Basemap(
        projection=projection,
        card=CARD,
        layers=Layers(**held),
        bounds=CARD.box,
        span_m=320,
        ribbon_fitted_m=120,
        track=held["route"],
    )
    return PaintJob.begin(basemap, style or Style.default(), out_dir)
