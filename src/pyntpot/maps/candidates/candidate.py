"""One ranked option a map could name for a track.

Key type: `Candidate`, a frozen record of the kind of thing (`road`, `climb`,
`place` or `landmark`), its name, its rank within its kind, where it is, and the
row the export writes for it.

`rank` is meaningful only among candidates of one kind from one call: a landmark
is ordered by tier then by how comfortably it sits inside its reach, a climb by
metres gained, a road by metres run, and a place by where the route passed it.
The kinds share no scale, so a rank is never compared across kinds.

It does not rank, fetch or project anything; the kind modules build candidates.
Invariants: `rank` counts from 1; `span` is a pair of track sample indices when
it is set; `where` is in card metres. `detail` holds the kind's row as the
export writes it, and is shared with the caller rather than copied.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from pyntpot.ink.polyline import Pt


@dataclass(frozen=True)
class Candidate:
    """One ranked annotation option.

    Attributes:
        kind: `road`, `climb`, `place` or `landmark`.
        name: What it is called; empty for a climb, which the caller names.
        rank: One-based, within its kind and its call.
        at_m: Metres along the track where it starts or is passed, or `None`.
        where: Where it is in card metres, or `None` for a road.
        span: The first and last track sample it covers, or `None`.
        detail: The kind's row, as the export writes it.
    """

    kind: str
    name: str
    rank: int
    at_m: float | None
    where: Pt | None
    span: tuple[int, int] | None
    detail: Mapping[str, Any]
