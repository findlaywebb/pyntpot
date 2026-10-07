"""Attribution owed to a data source whose features or elevation a map draws on.

Key type: `Credit`, one source's attribution: the full text, a link to the
licence or source, and the short line drawn on the map itself.

It does not fetch, format or place anything: providers build credits and
`maps.attribution` draws the short line. A credit is immutable, compares by
value and hashes, so a set of credits holds each distinct credit once.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Credit:
    """One data source's attribution.

    Attributes:
        text: The full attribution, as the source's licence asks for it.
        url: Where the source or its licence is published.
        short: The line drawn on the map.
    """

    text: str
    url: str
    short: str
