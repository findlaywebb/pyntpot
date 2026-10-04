"""Fixture providers that answer from the Lynmouth payloads instead of the network.

`FixtureFeatures` and `FixtureElevation` implement the `Features` and `Elevation`
protocols with the shipped providers' ids and credits, so a cache key computed for the
real providers finds the fixture files. They ignore the box and sample count they are
asked for and always return the fixture payloads. Each records the name of every method
called on it in `calls`, so a test can count fetches.
"""

from pyntpot.maps.credit import Credit
from pyntpot.maps.providers.base import ElevationGrid
from pyntpot.maps.track import BoundingBox

from support.paths import FIXTURE_DIR, KEY

#: The shipped Overpass provider's credit, written out here.
OSM_CREDIT = Credit(
    "© OpenStreetMap contributors",
    "https://www.openstreetmap.org/copyright",
    "© OpenStreetMap contributors (openstreetmap.org/copyright)",
)

#: The shipped OpenTopoData provider's credit for its default dataset, written out here.
SRTM_CREDIT = Credit(
    "Elevation: NASA SRTM via OpenTopoData",
    "https://www.opentopodata.org/",
    "elevation: NASA SRTM",
)


class FixtureFeatures:
    """The Lynmouth feature and land cover payloads, under the Overpass provider's id."""

    id = "overpass"
    credit = OSM_CREDIT

    def __init__(self) -> None:
        """Start with no calls recorded."""
        self.calls: list[str] = []

    def features(self, box: BoundingBox) -> str:
        """Return the fixture's feature payload, whatever the box."""
        del box
        self.calls.append("features")
        return (FIXTURE_DIR / f"overpass-{KEY}.json").read_text()

    def landcover(self, box: BoundingBox) -> str:
        """Return the fixture's land cover payload, whatever the box."""
        del box
        self.calls.append("landcover")
        return (FIXTURE_DIR / f"landcover-{KEY}.json").read_text()


class FixtureElevation:
    """The Lynmouth elevation grid, under the OpenTopoData SRTM provider's id."""

    id = "opentopodata-srtm30m"
    credit = SRTM_CREDIT

    def __init__(self) -> None:
        """Start with no calls recorded."""
        self.calls: list[str] = []

    def grid(self, box: BoundingBox, n: int) -> ElevationGrid:
        """Return the fixture's elevation grid, whatever the box and sample count."""
        del box, n
        self.calls.append("grid")
        return ElevationGrid.from_json((FIXTURE_DIR / f"elevation-{KEY}.json").read_text())
