"""The shipped `Features` provider: OpenStreetMap data from the public Overpass API.

Key type: `OverpassFeatures`, which posts the feature query and the land cover query
for a bounding box to an Overpass endpoint and returns the JSON text unparsed. The
query templates and the tag lists they are formatted with live here as module
constants.

The provider keeps to Overpass's published usage limits by default: one request at a
time per instance, a pause of `BACKOFF_S` seconds after a 429 before the next endpoint,
at most `budget` queries per instance (100 by default, the published daily regular
use), and a `[maxsize:N]` header bounding every response at `MAXSIZE_BYTES`. A
contact string is required and travels in the User-Agent, so an operator can reach
the caller.

It does not parse, validate or cache the payloads, retry an endpoint it has already
tried, or share a budget between instances: two instances have two budgets.

Invariants: the query templates are byte-equal to the painter's own; the size bound is
spliced in at request time by replacing the leading `[out:json]`, so the templates
themselves never change. The budget is checked before any request, so a refused
query makes none.
"""

import logging
import threading
import time
from collections.abc import Callable
from importlib.metadata import version

import httpx

from pyntpot.maps.credit import Credit
from pyntpot.maps.providers.base import ProviderBudgetExceededError, ProviderError
from pyntpot.maps.track import BoundingBox

log = logging.getLogger(__name__)

#: Public Overpass endpoints, tried in order.
DEFAULT_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)

#: The largest response any query may ask the server for, in bytes (64 MiB).
MAXSIZE_BYTES = 67_108_864

#: Seconds to wait after a 429 before trying the next endpoint.
BACKOFF_S = 30.0

#: Seconds the client waits for the feature query, matching its `[timeout:N]`.
FEATURE_TIMEOUT_S = 240.0

#: Seconds the client waits for the land cover query, matching its `[timeout:N]`.
LANDCOVER_TIMEOUT_S = 300.0

#: Roads that are drawn whatever the track did.
MAJOR_ROADS = ("motorway", "trunk", "primary", "secondary")
#: Roads that are drawn only where the track interacted with them.
MINOR_ROADS = ("tertiary", "unclassified", "residential", "track", "service")

#: Tag values the feature query asks for as landmark candidates, by key.
TOURISM_LANDMARKS = (
    "attraction",
    "viewpoint",
    "artwork",
    "museum",
    "zoo",
    "aquarium",
    "gallery",
    "theme_park",
)
MANMADE_LANDMARKS = (
    "lighthouse",
    "obelisk",
    "tower",
    "monument",
    "bridge",
    "water_tower",
    "chimney",
    "windmill",
    "pier",
    "mast",
)
BUILDING_LANDMARKS = (
    "cathedral",
    "church",
    "chapel",
    "mosque",
    "synagogue",
    "temple",
    "castle",
    "palace",
    "stadium",
    "train_station",
    "university",
    "hospital",
    "museum",
    "tower",
)
AMENITY_LANDMARKS = (
    "place_of_worship",
    "theatre",
    "arts_centre",
    "university",
    "townhall",
    "courthouse",
    "casino",
)
LEISURE_LANDMARKS = ("stadium", "sports_centre", "marina")

#: The feature query: roads, woods, protected areas, water, landmarks and places.
FEATURE_QUERY = """[out:json][timeout:240];
(
  way["highway"~"^({roads})$"]({box});
  way["landuse"="forest"]({box});
  way["natural"="wood"]({box});
  relation["landuse"="forest"]({box});
  relation["natural"="wood"]({box});
  way["boundary"~"^(national_park|protected_area)$"]({box});
  relation["boundary"~"^(national_park|protected_area)$"]({box});
  way["waterway"~"^(river|stream)$"]({box});
  way["natural"~"^(water|coastline|bay)$"]({box});
  relation["natural"="water"]({box});
  node["tourism"~"^({tourism})$"]({box});
  way["tourism"~"^({tourism})$"]["name"]({box});
  relation["tourism"~"^({tourism})$"]["name"]({box});
  node["historic"]({box});
  way["historic"]({box});
  node["man_made"~"^({manmade})$"]({box});
  way["man_made"~"^({manmade})$"]["name"]({box});
  way["building"~"^({buildings})$"]["name"]({box});
  node["amenity"~"^({amenities})$"]["name"]({box});
  way["amenity"~"^({amenities})$"]["name"]({box});
  way["leisure"~"^({leisure})$"]["name"]({box});
  relation["leisure"~"^({leisure})$"]["name"]({box});
  relation["amenity"~"^({amenities})$"]["name"]({box});
  relation["building"~"^({buildings})$"]["name"]({box});
  way["bridge"]["name"]({box});
  node["natural"~"^(peak|arch|cave_entrance)$"]({box});
  node["place"~"^(city|town|village|hamlet|suburb)$"]({box});
);
out geom;"""

#: The land cover classes the land cover query asks for, by key.
LANDCOVER_LANDUSE = (
    "farmland|meadow|grass|orchard|vineyard|allotments|"
    "village_green|recreation_ground|cemetery|residential|"
    "industrial|commercial|retail|quarry|farmyard|"
    "greenhouse_horticulture"
)
LANDCOVER_NATURAL = "grassland|heath|moor|scrub|wetland|bare_rock|beach|sand|shingle|cliff|scree"
LANDCOVER_LEISURE = "park|golf_course|nature_reserve|pitch|garden"

#: The land cover query: the ground between the feature query's woods, water and roads.
LANDCOVER_QUERY = """[out:json][timeout:300];
(
  way["landuse"~"^({landuse})$"]({box});
  relation["landuse"~"^({landuse})$"]({box});
  way["natural"~"^({natural})$"]({box});
  relation["natural"~"^({natural})$"]({box});
  way["leisure"~"^({leisure})$"]({box});
  relation["leisure"~"^({leisure})$"]({box});
);
out geom;"""


def _box_text(box: BoundingBox) -> str:
    """Return the box as Overpass reads it: south, west, north, east, six decimals."""
    return ",".join(f"{value:f}" for value in box)


def _with_maxsize(query: str) -> str:
    """Return the query with the response size bound spliced after `[out:json]`."""
    return query.replace("[out:json]", f"[out:json][maxsize:{MAXSIZE_BYTES}]", 1)


class OverpassFeatures:
    """OpenStreetMap features and land cover from Overpass, within its usage limits.

    Attributes:
        id: The stable name the fetch cache keys on.
        credit: The OpenStreetMap attribution the data is owed.
        endpoints: The Overpass interpreter URLs, tried in order.
        user_agent: The User-Agent sent with every request, carrying the contact.
    """

    id = "overpass"
    credit = Credit(
        "© OpenStreetMap contributors",
        "https://www.openstreetmap.org/copyright",
        "© OpenStreetMap contributors (openstreetmap.org/copyright)",
    )

    def __init__(
        self,
        contact: str,
        endpoints: tuple[str, ...] = DEFAULT_ENDPOINTS,
        *,
        budget: int = 100,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        """Make a provider; no request is sent until a query is asked for.

        Args:
            contact: How an Overpass operator can reach the caller, such as an email.
            endpoints: Overpass interpreter URLs, tried in order.
            budget: The most queries this instance will send.
            client: The HTTP client to send with; the caller keeps ownership. When
                `None`, each query opens and closes its own client.
            sleep: Waits a number of seconds; the back-off after a 429 calls it.

        Raises:
            ValueError: When `contact` is empty or `endpoints` is empty.
        """
        if not contact.strip():
            raise ValueError("Overpass needs a contact string, such as an email address")
        if not endpoints:
            raise ValueError("Overpass needs at least one endpoint")
        self.endpoints = endpoints
        self.user_agent = f"pyntpot/{version('pyntpot')} ({contact})"
        self._budget = budget
        self._queries = 0
        self._client = client
        self._sleep = sleep
        self._lock = threading.Lock()

    def features(self, box: BoundingBox) -> str:
        """Return the feature query's Overpass JSON for the box.

        Raises:
            ProviderBudgetExceededError: When this instance has spent its budget.
            ProviderError: When every endpoint failed.
        """
        query = FEATURE_QUERY.format(
            box=_box_text(box),
            roads="|".join(MAJOR_ROADS + MINOR_ROADS),
            tourism="|".join(TOURISM_LANDMARKS),
            manmade="|".join(MANMADE_LANDMARKS),
            buildings="|".join(BUILDING_LANDMARKS),
            amenities="|".join(AMENITY_LANDMARKS),
            leisure="|".join(LEISURE_LANDMARKS),
        )
        return self._query(query, FEATURE_TIMEOUT_S)

    def landcover(self, box: BoundingBox) -> str:
        """Return the land cover query's Overpass JSON for the box.

        Raises:
            ProviderBudgetExceededError: When this instance has spent its budget.
            ProviderError: When every endpoint failed.
        """
        query = LANDCOVER_QUERY.format(
            box=_box_text(box),
            landuse=LANDCOVER_LANDUSE,
            natural=LANDCOVER_NATURAL,
            leisure=LANDCOVER_LEISURE,
        )
        return self._query(query, LANDCOVER_TIMEOUT_S)

    def _query(self, query: str, timeout: float) -> str:
        """Spend one query of the budget, then send it, one at a time per instance."""
        with self._lock:
            if self._queries >= self._budget:
                raise ProviderBudgetExceededError(
                    f"Overpass budget of {self._budget} queries spent on this provider"
                )
            self._queries += 1
            if self._client is not None:
                return self._send(self._client, _with_maxsize(query), timeout)
            with httpx.Client(follow_redirects=True) as client:
                return self._send(client, _with_maxsize(query), timeout)

    def _send(self, client: httpx.Client, query: str, timeout: float) -> str:
        """Post the query to each endpoint in turn and return the first success.

        Raises:
            ProviderError: From the last `httpx.HTTPError` when every endpoint failed.
        """
        last: httpx.HTTPError | None = None
        for url in self.endpoints:
            try:
                response = client.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": self.user_agent},
                    timeout=timeout,
                )
                response.raise_for_status()
            except httpx.HTTPError as exc:
                log.info("overpass %s refused the query: %s", url, exc)
                last = exc
                too_many = isinstance(exc, httpx.HTTPStatusError) and (
                    exc.response.status_code == httpx.codes.TOO_MANY_REQUESTS
                )
                if too_many:
                    self._sleep(BACKOFF_S)
                continue
            return response.text
        raise ProviderError("every Overpass endpoint refused the query") from last
