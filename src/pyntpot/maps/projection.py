"""The local projection that puts one track's degrees into card metres.

Key types: `Projection`, an equirectangular projection about a track: x east
and y north in metres, x scaled by the cosine of the track's mean latitude,
and the origin moved to a chosen point; and `track_projection`, which builds
the projection for one track and projects the track through it.

It does not fetch, clip or draw anything, and it knows nothing of a card's
pixel grids: the card frame converts card metres to pixels. It is a local
projection, accurate over a box a few tens of kilometres across, not a map
projection for a region.

Invariants: `inverse` undoes the projection to floating-point rounding; with
no route given, the projected track's smallest x and smallest y are both zero,
so the whole track lies in the positive quadrant.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyntpot.ink.polyline import Pt


@dataclass
class Projection:
    """The route chart's local equirectangular projection.

    x scales by the cosine of the mean latitude of the track and y grows north.
    The origin is the south-west corner of the projected track, unless
    `track_projection` was handed a route to take it from.

    Attributes:
        lat0: The latitude whose cosine scales x, in degrees.
        lat_ref: The latitude projected before the origin shift, in degrees.
        lng_ref: The longitude projected before the origin shift, in degrees.
        x0: Metres subtracted from every x, which moves the origin east.
        y0: Metres subtracted from every y, which moves the origin north.
        ky: Metres per degree of latitude.
    """

    lat0: float
    lat_ref: float
    lng_ref: float
    x0: float = 0.0
    y0: float = 0.0
    ky: float = 110540.0

    @property
    def kx(self) -> float:
        """Metres per degree of longitude at the track's mean latitude."""
        return 111320.0 * math.cos(math.radians(self.lat0))

    def __call__(self, lat: float, lng: float) -> Pt:
        """Project one coordinate into card metres."""
        return ((lng - self.lng_ref) * self.kx - self.x0, (lat - self.lat_ref) * self.ky - self.y0)

    def inverse(self, x: float, y: float) -> tuple[float, float]:
        """Latitude and longitude for a point in card metres."""
        return ((y + self.y0) / self.ky + self.lat_ref, (x + self.x0) / self.kx + self.lng_ref)


def track_projection(
    lat: list[float], lng: list[float], route: list[Pt] | None = None
) -> tuple[Projection, list[Pt]]:
    """The projection for one track, and the track projected through it.

    Args:
        lat: Latitudes in degrees, in recorded order.
        lng: Longitudes in degrees, same length.
        route: The caller's already-projected track. When it is given the origin
            is taken from its first point rather than from the bounding box, so
            both agree even if the caller simplified before taking its own.

    Returns:
        The projection, and the track in metres.
    """
    proj = Projection(lat0=sum(lat) / len(lat), lat_ref=lat[0], lng_ref=lng[0])
    raw = [proj(a, b) for a, b in zip(lat, lng, strict=True)]
    if route:
        proj.x0 = raw[0][0] - route[0][0]
        proj.y0 = raw[0][1] - route[0][1]
    else:
        proj.x0 = min(x for x, _ in raw)
        proj.y0 = min(y for _, y in raw)
    return proj, [(x - proj.x0, y - proj.y0) for x, y in raw]
