"""An elevation provider that asks an OpenTopoData server for a lattice of heights.

Key types: `OpenTopoData`, an `Elevation` provider; `PUBLIC`, the public server's
endpoint. `grid` samples an `n` by `n` lattice evenly spaced from the box's south-west
corner to its north-east corner, asks for 100 points a call, pauses 1.1 seconds after each call and
reads a missing elevation as `0.0`.

The public server's published limits are enforced by default: 100 locations a call, one
call a second (a fixed pause through the injected `sleep`, no clock is read) and at most
`budget` calls, 1000 by default, per provider instance. The call that would pass the
budget raises `ProviderBudgetExceededError` before any request is made. A reply whose
status is not `OK`, or that is not the expected JSON, raises `ProviderError`. The
count is per instance: nothing is shared between instances or processes.

The `contact` string is required and goes into the User-Agent as
`pyntpot/<version> (<contact>)`; an empty one raises `ValueError`. The constructor makes
no request. This module imports nothing from the painter and does not cache.
"""

import json
import logging
import time
from collections.abc import Callable
from importlib.metadata import version

import httpx

from pyntpot.maps.credit import Credit
from pyntpot.maps.providers.base import (
    ElevationGrid,
    ProviderBudgetExceededError,
    ProviderError,
)
from pyntpot.maps.track import BoundingBox

log = logging.getLogger(__name__)

PUBLIC = "https://api.opentopodata.org/v1"

#: Locations the public server accepts in one call.
POINTS_PER_CALL = 100

#: Seconds to pause after each call, to stay inside one call a second.
PAUSE_S = 1.1

#: Seconds to wait for one reply.
TIMEOUT_S = 240.0


class OpenTopoData:
    """An OpenTopoData server as an `Elevation` provider.

    Attributes:
        id: `opentopodata-<dataset>`, the name the fetch cache keys on.
        credit: The attribution the elevation data is owed.
    """

    credit = Credit(
        "Elevation: NASA SRTM via OpenTopoData",
        "https://www.opentopodata.org/",
        "elevation: NASA SRTM",
    )

    def __init__(
        self,
        contact: str,
        endpoint: str = PUBLIC,
        dataset: str = "srtm30m",
        *,
        budget: int = 1000,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Set up the provider; no request is made.

        Args:
            contact: How the server's operator can reach the caller, such as an email
                address or a project URL.
            endpoint: The server's base URL, without the dataset.
            dataset: The dataset to sample.
            budget: The most calls this instance may make.
            client: The HTTP client to use, or `None` for one per call.
            sleep: Called with the pause in seconds after each call.

        Raises:
            ValueError: When `contact` is empty.
        """
        if not contact.strip():
            raise ValueError("OpenTopoData needs a contact string for its User-Agent")
        self.id = f"opentopodata-{dataset}"
        self._url = f"{endpoint.rstrip('/')}/{dataset}"
        self._headers = {"User-Agent": f"pyntpot/{version('pyntpot')} ({contact})"}
        self._budget = budget
        self._calls = 0
        self._client = client
        self._sleep = sleep

    def grid(self, box: BoundingBox, n: int) -> ElevationGrid:
        """Return an `n` by `n` elevation grid over the box.

        Raises:
            ProviderBudgetExceededError: Before the call that would pass the budget.
            ProviderError: When a call fails, answers a status other than `OK` or
                answers something unreadable.
        """
        south, west, north, east = box
        lats = tuple(south + (north - south) * i / (n - 1) for i in range(n))
        lons = tuple(west + (east - west) * j / (n - 1) for j in range(n))
        points = [(la, lo) for la in lats for lo in lons]
        values: list[float] = []
        for start in range(0, len(points), POINTS_PER_CALL):
            batch = points[start : start + POINTS_PER_CALL]
            values.extend(self._call(batch))
            log.info("elevation %d/%d", len(values), len(points))
            self._sleep(PAUSE_S)
        return ElevationGrid(n=n, box=box, lats=lats, lons=lons, elev=tuple(values))

    def _call(self, batch: list[tuple[float, float]]) -> list[float]:
        """Ask for one batch of points and return their elevations in order."""
        if self._calls >= self._budget:
            raise ProviderBudgetExceededError(
                f"{self.id} would pass its budget of {self._budget} calls"
            )
        self._calls += 1
        locations = "|".join(f"{a:.6f},{b:.6f}" for a, b in batch)
        params = {"locations": locations}
        try:
            if self._client is not None:
                response = self._client.get(self._url, params=params, headers=self._headers)
            else:
                with httpx.Client(timeout=TIMEOUT_S, follow_redirects=True) as client:
                    response = client.get(self._url, params=params, headers=self._headers)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError(f"{self.id} request failed: {exc}") from exc
        try:
            payload = json.loads(response.text)
            status = payload.get("status")
            if status != "OK":
                raise ProviderError(f"{self.id} said {status!r}")
            return [
                0.0 if r["elevation"] is None else float(r["elevation"]) for r in payload["results"]
            ]
        except (json.JSONDecodeError, AttributeError, KeyError, TypeError) as exc:
            raise ProviderError(f"{self.id} answered something unreadable") from exc
