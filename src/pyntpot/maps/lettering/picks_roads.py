"""Which named roads a card numbers, set along their own tarmac.

Key names: `pick_roads`, the labels for the roads the session was on; `road_ref`, the
number to letter out of OSM's `ref`; `road_min_px`, the shortest run a number may be set
along.

It does not pick settlements or rivers, and it does not place a name.

Invariants: a numbered road is one road whatever its pieces are called; a road the
session was never on is not lettered.
"""

import math

from pyntpot.ink.chains import joined
from pyntpot.ink.polyline import Pt, length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import TIER_ROAD, Label, feature_px
from pyntpot.maps.lettering.picks_lines import NamedLines

#: How long a named road has to run inside the card before its number is worth
#: setting along it, as a multiple of the type size the number is written at.
#: Stated against the type because the question is whether the road is longer
#: than its own name: a road number is five characters and about two and a half
#: type sizes wide, so this is a run about two and a half times the name, which
#: is enough for the number to read as a name along the tarmac rather than as a
#: tag on the end of it.
#:
#: It was a flat 110 display pixels, which is over three times the widest road
#: number and was that only because the card it was tuned on happened to carry
#: a 235 px run of one road, while a card whose longest run of that same
#: road is 92 px carried no number at all.
ROAD_MIN_CAPS = 6.4


def road_min_px(size: float) -> float:
    """The shortest run of road a number may be set along, in display pixels."""
    return size * ROAD_MIN_CAPS


ROAD_MAX = 2
#: How near the route a road has to run, in card pixels, to be one the session was on.
ROAD_ON_ROUTE_PX = 40.0


def pick_roads(
    basemap: Basemap,
    lines: NamedLines,
    card: Card,
    route_px: list[Pt],
    budget: int = ROAD_MAX,
) -> list[Label]:
    """Which named roads the sheet numbers, set along their own tarmac.

    A road number is the quietest thing on the map and one of the most useful:
    it is how a rider works out where a climb actually was. A road is lettered
    by its number where OSM has one, and by its name only where it has none:
    "A591" places a climb, "Keswick Road" eats a corner and says nothing at
    26 m a pixel. Only the roads the ride was on, and only where there is
    enough of one inside the card to write on.

    **A numbered road is one road, whatever OSM calls each mile of it.** The
    pieces used to be chained by their street name, and a street name changes
    at every parish: the A82 crosses a card as Glencoe, then
    Ballachulish, then New Road, then Kinlochleven Road, none of them a third of
    the shortest run a name can be set on, so that card carried no number at
    all while the same code numbered another card twice. Where a
    road has a number the number is what its pieces are gathered by, and the
    name is only the fallback for a lane that has none.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the roads.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        budget: How many to letter.

    Returns:
        One `Label` a road, best first, carrying the tarmac as its baseline.
    """
    geom = lines.get("roads") or []
    thin = route_px[::4] or route_px
    pieces: dict[str, list[list[Pt]]] = {}
    widths: dict[str, float] = {}
    for entry in geom:
        name = str(entry.get("n") or "")
        if not name or entry.get("c") not in ("major", "medium"):
            continue
        line = [card.xy(x, y) for x, y in entry.get("d") or []]
        if len(line) > 1:
            key = road_ref(entry.get("r")) or name
            pieces.setdefault(key, []).append(line)
            widths[key] = max(
                widths.get(key, 0.0), feature_px(basemap, "road", str(entry.get("c")))
            )
    size = DEFAULT_LINE_PX * 0.7
    shortest = road_min_px(size)
    best: dict[str, tuple[float, list[Pt]]] = {}
    for key, parts in pieces.items():
        line = max(joined(parts), key=length)
        if length(line) < shortest:
            continue
        near = min(min(math.dist(p, q) for q in thin) for p in line[::2])
        if near > ROAD_ON_ROUTE_PX:  # a road the session was never on is not this map's
            continue
        best[key] = (length(line) - near, line)
    out: list[Label] = []
    for key, (_score, line) in sorted(best.items(), key=lambda kv: -kv[1][0])[:budget]:
        mid = line[len(line) // 2]
        out.append(
            Label(
                name=key,
                kind="road",
                why="road the session was on",
                px=mid[0],
                py=mid[1],
                tier=TIER_ROAD,
                size=size,
                baseline=line,
                feature_px=widths.get(key, 0.0),
            )
        )
    return out


def road_ref(raw: object) -> str:
    """The road number to letter, out of whatever OSM put in `ref`.

    OSM joins concurrent numbers with a semicolon ("A5;A470") and sometimes
    pads them. A card has room for one number, so the first is taken: it is the
    one the signs lead with.

    Not every `ref` on a highway is a road number. Walking and cycling routes
    put their own code there and this box carries "NCN", "LDP" and "PW" from
    the Pennine Way and its neighbours. A road number always carries a
    digit and a route code here does not, so a ref with no digit in it is not
    treated as one.

    Args:
        raw: The `ref` tag, or None.

    Returns:
        The number to write, or "" when the road has none.
    """
    text = str(raw or "").strip().split(";")[0].strip()
    return text if any(ch.isdigit() for ch in text) else ""
