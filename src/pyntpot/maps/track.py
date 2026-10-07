"""A recorded route as plain data: where it went, and optionally how high and when.

Key types: `Track`, an immutable run of latitudes and longitudes with optional
elevations and times, and `BoundingBox`, the south, west, north, east degrees
around it.

`Track.from_gpx` reads only `trkpt` elements, matched by local name whatever
their namespace. Elevation and time are kept only when every point has them; time is
seconds from the first point and never reads the clock. A track has no sport
field. It does not fetch, simplify or draw anything, and it imports nothing
from the package: the margin arithmetic is its own copy.

Invariants: `lat`, `lng` and any `ele` or `time` have equal lengths, a track has
at least two points, and every latitude lies in [-90, 90].
"""

import math
import xml.etree.ElementTree as ET
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, Self

import pydantic

MIN_TRACK_POINTS = 2
MAX_LATITUDE_DEGREES = 90.0


class BoundingBox(NamedTuple):
    """South, west, north, east degrees."""

    south: float
    west: float
    north: float
    east: float


class Track(pydantic.BaseModel, frozen=True):
    """A recorded route.

    Attributes:
        lat: Latitudes in degrees, in recorded order.
        lng: Longitudes in degrees, one per latitude.
        ele: Elevations in metres, one per point, or `None`.
        time: Seconds from the first point, one per point, or `None`.
    """

    lat: tuple[float, ...]
    lng: tuple[float, ...]
    ele: tuple[float, ...] | None = None
    time: tuple[float, ...] | None = None

    @pydantic.model_validator(mode="after")
    def _check_shape(self) -> Self:
        """Require equal lengths, two points or more, and latitudes on the globe."""
        count = len(self.lat)
        if len(self.lng) != count:
            raise ValueError("lat and lng must have equal lengths")
        for name in ("ele", "time"):
            series = getattr(self, name)
            if series is not None and len(series) != count:
                raise ValueError(f"{name} must have one value per point")
        if count < MIN_TRACK_POINTS:
            raise ValueError("a track needs at least two points")
        if any(not -MAX_LATITUDE_DEGREES <= value <= MAX_LATITUDE_DEGREES for value in self.lat):
            raise ValueError("latitudes must lie in [-90, 90]")
        return self

    @classmethod
    def from_gpx(cls, path: Path) -> Self:
        """Read a GPX file's `trkpt` elements.

        Args:
            path: A GPX 1.0 or 1.1 file.

        Returns:
            The track; `ele` and `time` are set only when every point has them.

        Raises:
            ValueError: When a point's time is not an ISO 8601 time with a zone,
                or the points do not make a track: fewer than two, or a
                latitude outside [-90, 90].
        """
        root = ET.parse(path).getroot()
        points = [el for el in root.iter() if _local(el.tag) == "trkpt"]
        lat = tuple(float(el.attrib["lat"]) for el in points)
        lng = tuple(float(el.attrib["lon"]) for el in points)
        ele = _child_values(points, "ele", float)
        stamps = _child_values(points, "time", _parse_time)
        time = None if stamps is None else tuple(s - stamps[0] for s in stamps)
        return cls(lat=lat, lng=lng, ele=ele, time=time)

    def bounding_box(self, margin_m: float) -> BoundingBox:
        """The track's extent grown by `margin_m` metres on every side."""
        mid = (min(self.lat) + max(self.lat)) / 2
        dlat = margin_m / 110540.0
        dlng = margin_m / (111320.0 * math.cos(math.radians(mid)))
        return BoundingBox(
            min(self.lat) - dlat,
            min(self.lng) - dlng,
            max(self.lat) + dlat,
            max(self.lng) + dlng,
        )


def _local(tag: str) -> str:
    """Return an element tag without its namespace."""
    return tag.rpartition("}")[2]


def _parse_time(text: str) -> float:
    """Return an aware ISO 8601 time as seconds since the epoch."""
    moment = datetime.fromisoformat(text.strip())
    if moment.tzinfo is None:
        raise ValueError(f"GPX time {text!r} has no time zone")
    return moment.timestamp()


def _child_values(
    points: list[ET.Element], name: str, convert: Callable[[str], float]
) -> tuple[float, ...] | None:
    """Return one converted child value per point, or `None` unless every point has one."""
    values: list[float] = []
    for point in points:
        child = next((c for c in point if _local(c.tag) == name), None)
        if child is None or child.text is None:
            return None
        values.append(convert(child.text))
    return tuple(values)
