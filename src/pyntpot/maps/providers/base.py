"""What a feature or elevation provider promises, and the grid an elevation provider returns.

Key types: `Features`, a source of OpenStreetMap feature and land cover payloads for a
bounding box; `Elevation`, a source of elevation grids; `ElevationGrid`, an `n` by `n`
lattice of elevations over a box; `ProviderError`, raised when a provider cannot answer;
and `ProviderBudgetExceededError`, raised before the call that would pass a provider's
usage budget.

The two protocols are the package's only protocols. A provider carries a stable `id`,
which the fetch cache keys on, and the `Credit` its data is owed. This module fetches
nothing, holds no state and imports nothing from the painter: the shipped providers
and any caller's own implement the protocols elsewhere.

Invariants: `ElevationGrid.to_json` writes the same bytes as the painter's elevation
cache file (keys `n`, `bbox`, `lats`, `lons`, `elev`, default separators, no trailing
newline), and `from_json` then `to_json` reproduces such a file byte for byte.
"""

import json
from dataclasses import dataclass
from typing import Protocol, Self

from pyntpot.maps.credit import Credit
from pyntpot.maps.track import BoundingBox


class ProviderError(RuntimeError):
    """A provider could not answer: every endpoint failed or the reply was unusable."""


class ProviderBudgetExceededError(ProviderError):
    """A provider refused a call because it would pass the provider's usage budget."""


@dataclass(frozen=True)
class ElevationGrid:
    """An `n` by `n` lattice of elevations over a bounding box.

    Attributes:
        n: Samples per side.
        box: The south, west, north, east degrees the lattice spans.
        lats: The `n` sample latitudes, south to north.
        lons: The `n` sample longitudes, west to east.
        elev: The `n * n` elevations in metres, row by row from the south, each row
            west to east.
    """

    n: int
    box: BoundingBox
    lats: tuple[float, ...]
    lons: tuple[float, ...]
    elev: tuple[float, ...]

    def to_json(self) -> str:
        """Return the grid in the painter's elevation cache file format."""
        return json.dumps(
            {
                "n": self.n,
                "bbox": list(self.box),
                "lats": list(self.lats),
                "lons": list(self.lons),
                "elev": list(self.elev),
            }
        )

    @classmethod
    def from_json(cls, text: str) -> Self:
        """Read a grid from the painter's elevation cache file format.

        Raises:
            KeyError: When a key is missing.
            json.JSONDecodeError: When the text is not JSON.
        """
        data = json.loads(text)
        return cls(
            n=int(data["n"]),
            box=BoundingBox(*(float(v) for v in data["bbox"])),
            lats=tuple(float(v) for v in data["lats"]),
            lons=tuple(float(v) for v in data["lons"]),
            elev=tuple(float(v) for v in data["elev"]),
        )


class Features(Protocol):
    """A source of OpenStreetMap features and land cover for a bounding box.

    `id` names the source stably across processes, so the fetch cache can key on it.
    Payloads are Overpass JSON text, returned unparsed.
    """

    @property
    def id(self) -> str:
        """The stable name of this source."""
        ...

    @property
    def credit(self) -> Credit:
        """The attribution this source's data is owed."""
        ...

    def features(self, box: BoundingBox) -> str:
        """Return the feature query's Overpass JSON for the box."""
        ...

    def landcover(self, box: BoundingBox) -> str:
        """Return the land cover query's Overpass JSON for the box."""
        ...


class Elevation(Protocol):
    """A source of elevation grids.

    `id` names the source stably across processes, so the fetch cache can key on it.
    """

    @property
    def id(self) -> str:
        """The stable name of this source."""
        ...

    @property
    def credit(self) -> Credit:
        """The attribution this source's data is owed."""
        ...

    def grid(self, box: BoundingBox, n: int) -> ElevationGrid:
        """Return an `n` by `n` elevation grid over the box."""
        ...
