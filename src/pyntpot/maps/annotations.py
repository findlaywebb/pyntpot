"""What a caller asks a map to letter: landmarks, places and spans.

Key types: `Annotations`, the caller's whole request; `Landmark`, one named
thing to letter, at its own coordinates or looked up among the basemap's
candidates; `SpanRequest`, one stretch of the route to mark, stated by point
index, by kilometre or by seconds from the start.

It does not place, resolve or draw anything: the lettering stage reads these
values and decides where each lands. A span request is not a placed span: it
says which stretch is meant, and the lettering resolves it onto the route and
places it. `Annotations.roads` is accepted and not read: no road is lettered by
a caller's name, the roads lettered are the ones the lettering picks itself.

Invariants: every value here is immutable and rejects unknown fields; a span
request states exactly one start and exactly one end.
"""

from typing import Self

import pydantic


class Landmark(pydantic.BaseModel, frozen=True, extra="forbid"):
    """One named thing to letter.

    Attributes:
        name: The name lettered, and the name looked up among the basemap's
            candidates when no coordinates are given.
        kind: What sort of thing it is, which chooses how it is lettered.
        why: Why it is lettered, carried with the placed label.
        lat: Its latitude in degrees, or `None` to look it up by name.
        lng: Its longitude in degrees, or `None` to look it up by name.
    """

    name: str
    kind: str = ""
    why: str = ""
    lat: float | None = None
    lng: float | None = None


class SpanRequest(pydantic.BaseModel, frozen=True, extra="forbid"):
    """One stretch of the route a caller asks to have marked.

    Each end is stated once, in one of three ways: a point index into the
    track, a distance along the route in kilometres, or seconds from the start
    (which resolves only when the basemap carries the track's times).

    Attributes:
        name: The name lettered beside the stretch.
        kind: What sort of stretch it is, such as `climb` or `descent`.
        why: Why it is marked, carried with the placed span.
        intent: What it says about the stretch, which chooses its ink.
        from_i: The start as a point index.
        from_km: The start in kilometres along the route.
        from_s: The start in seconds from the first point.
        to_i: The end as a point index.
        to_km: The end in kilometres along the route.
        to_s: The end in seconds from the first point.
    """

    name: str
    kind: str = "climb"
    why: str = ""
    intent: str = "note"
    from_i: int | None = None
    from_km: float | None = None
    from_s: float | None = None
    to_i: int | None = None
    to_km: float | None = None
    to_s: float | None = None

    @pydantic.model_validator(mode="after")
    def _one_start_one_end(self) -> Self:
        """Require exactly one `from_*` and exactly one `to_*` value."""
        for end in ("from", "to"):
            stated = [
                unit for unit in ("i", "km", "s") if getattr(self, f"{end}_{unit}") is not None
            ]
            if len(stated) != 1:
                raise ValueError(f"a span needs exactly one {end}_* value, got {len(stated)}")
        return self


class Annotations(pydantic.BaseModel, frozen=True, extra="forbid"):
    """What a caller asks a map to letter.

    Attributes:
        landmarks: The landmarks to letter, in the caller's order of
            preference. A bare string is a name looked up among the basemap's
            candidates.
        places: Names of settlements the lettering should always letter.
        roads: Accepted and not read: road names are never taken from a
            caller.
        spans: The stretches of the route to mark, best first.
    """

    landmarks: tuple[Landmark | str, ...] = ()
    places: tuple[str, ...] = ()
    roads: tuple[str, ...] = ()
    spans: tuple[SpanRequest, ...] = ()
