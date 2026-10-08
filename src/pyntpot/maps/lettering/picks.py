"""What the map names: the landmarks, the user's own places, the ground and the route's markers.

Key names: `journal_picks` and `journal_heuristic`, the landmarks to letter; `ground_labels`,
the settlements and rivers a card is entitled to; `home_places` and `home_labels`, the
user's own places; `route_markers`, where the track set off and finished.

The settlement, river and road picks live in `picks_settlements`, `picks_rivers` and
`picks_roads`, and the named lines they read in `picks_lines`. It does not place or draw a
name.

Invariants: the ground is picked by rule and the annotations only add to it; the markers are
the track and carry the route's ink.
"""

import math
from typing import Any

from pyntpot.ink.polyline import Pt
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.annotations import Annotations
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import TIER_MARKER, TIER_PLACE, Box, Label, Measure
from pyntpot.maps.lettering.picks_lines import NamedLines
from pyntpot.maps.lettering.picks_rivers import pick_rivers
from pyntpot.maps.lettering.picks_settlements import MERGE_M, pick_settlements
from pyntpot.maps.style import Style


def journal_picks(picks: Annotations | None, basemap: Basemap, cap: int) -> list[dict[str, Any]]:
    """The annotations' landmarks, each with a position, in their order.

    A landmark with its own latitude and longitude is placed there. One that is
    only a name, or has no position, is looked up by name in the basemap's
    candidates and dropped when none matches. The list stops once a landmark
    with its own fields brings it to `cap`; a name-only landmark is never
    counted against `cap`.
    """
    wanted = list(getattr(picks, "landmarks", None) or [])
    if not wanted:
        return []
    by_name = {c["name"]: c for c in basemap.candidates}
    out: list[dict[str, Any]] = []
    for entry in wanted:
        if isinstance(entry, str):
            found = by_name.get(entry)
            if not found:
                continue
            out.append(
                {
                    "name": entry,
                    "kind": found.get("class", ""),
                    "why": "",
                    "x": found["x"],
                    "y": found["y"],
                }
            )
            continue
        name = getattr(entry, "name", "")
        lat, lng = getattr(entry, "lat", None), getattr(entry, "lng", None)
        item = {
            "name": name,
            "kind": getattr(entry, "kind", "") or "",
            "why": getattr(entry, "why", "") or "",
        }
        if lat is None or lng is None:
            found = by_name.get(name)
            if not found:
                continue
            item["x"], item["y"] = found["x"], found["y"]
        else:
            item["lat"], item["lng"] = float(lat), float(lng)
        out.append(item)
        if len(out) >= cap:
            break
    return out


def journal_heuristic(basemap: Basemap, cap: int) -> list[dict[str, Any]]:
    """The fallback when no landmark lands: the leading `cap` candidates.

    The candidates come in the basemap's order, most notable first.
    """
    out = []
    for c in basemap.candidates:
        out.append(
            {
                "name": c["name"],
                "kind": c.get("class", ""),
                "why": f"nearest named feature, {c.get('distance_m')} m off the route",
                "x": c["x"],
                "y": c["y"],
            }
        )
        if len(out) >= cap:
            break
    return out


def home_places(basemap: Basemap, card: Card) -> list[Label]:
    """The user's own places marked `kind: settlement`, as settlement labels.

    Such an entry is lettered like any other settlement, which is what
    "Swell, a village" wants and what a house marker would say wrongly. Every
    other entry, and one whose position falls outside the card, is left out.
    """
    out: list[Label] = []
    for place in basemap.places:
        if place.get("kind") != "settlement":
            continue
        x, y = card.xy(place["x"], place["y"])
        if not (0 < x < card.w and 0 < y < card.h):
            continue
        out.append(
            Label(
                name=place.get("n", ""),
                kind="settlement",
                why=place.get("note", ""),
                px=x,
                py=y,
                tier=TIER_PLACE,
                size=DEFAULT_LINE_PX * 1.15,
            )
        )
    return out


def ground_labels(
    basemap: Basemap,
    lines: NamedLines,
    card: Card,
    route_px: list[Pt],
    picks: Annotations | None = None,
) -> list[Label]:
    """The names the ground is entitled to, whatever the annotations asked for.

    Settlements come from the basemap's candidates and watercourses from its
    named lines. Choosing them is a rule, not a judgement, so it runs by
    default and the annotations only ever add to it.

    Three tiers own the answer, in this order: the rule, the user's own places
    for a standing exception, and the annotations' places for this track.

    Args:
        basemap: The basemap, for its places and candidates.
        lines: The named lines, for the watercourses.
        card: The card, for the projection and its size.
        route_px: The track in display pixels.
        picks: The annotations, whose `places` name this track's exceptions;
            none adds nothing.

    Returns:
        The user's places, then the settlements, then the rivers, in the
        order they claim their boxes.
    """
    mine = home_places(basemap, card)
    always = [p.get("n", "") for p in basemap.places if p.get("always")] + [lb.name for lb in mine]
    wanted = list(picks.places) if picks else []
    # The user writes "Swell" and OSM has Upper and Lower; the entry
    # carries its own position and it is authoritative, so a group within about
    # a merge's distance of it is the same place and is not lettered twice.
    near = MERGE_M * card.scale
    settled = [
        lb
        for lb in pick_settlements(basemap, card, route_px, always=always, wanted=wanted)
        if all(
            lb.name.casefold() != own.name.casefold()
            and math.dist((lb.px, lb.py), (own.px, own.py)) > near
            for own in mine
        )
    ]
    return mine + settled + pick_rivers(basemap, lines, card, route_px)


def route_markers(route_px: list[Pt], size: float = DEFAULT_LINE_PX * 0.65) -> list[Label]:
    """Where the track set off and where it finished, in the route's own ink.

    The ground is drawn in the map's ink and the track in the route's, and
    these two are the track: they are facts about the ride, not about the
    place. A loop puts them on top of each other, so it gets one mark.
    """
    if len(route_px) < MIN_ROUTE_POINTS:
        return []
    start, end = route_px[0], route_px[-1]
    if math.dist(start, end) < LOOP_CLOSE_PX:
        return [
            Label(
                name="start",
                kind="marker",
                why="where the session began",
                px=start[0],
                py=start[1],
                tier=TIER_MARKER,
                size=size,
            )
        ]
    return [
        Label(
            name="start",
            kind="marker",
            why="where the session began",
            px=start[0],
            py=start[1],
            tier=TIER_MARKER,
            size=size,
        ),
        Label(
            name="finish",
            kind="marker",
            why="where the session ended",
            px=end[0],
            py=end[1],
            tier=TIER_MARKER,
            size=size,
        ),
    ]


#: The fewest points a route needs for a start and a finish.
MIN_ROUTE_POINTS = 2
#: How near its start the route ends, in display pixels, for the two marks to be one.
LOOP_CLOSE_PX = 30.0
#: How far below its house a user's own place has its name written.
HOME_NAME_DROP = 25.0


def home_labels(
    basemap: Basemap, card: Card, style: Style, measure_fn: Measure
) -> tuple[list[Label], list[Box]]:
    """The user's houses, already placed, and the room they need.

    A house (a place with `sym: house`) is not placed by the placer: it is
    where it is, and its name goes under it. So it comes back placed, with the
    box it occupies, and the box goes into the placer's `taken` list so nothing
    else is written across it.

    Args:
        basemap: The basemap, for its places.
        card: The card, for the projection and its size.
        style: The style, for the type size and whether to draw at all.
        measure_fn: How wide a name is.

    Returns:
        The labels, and the boxes they have already claimed.
    """
    if not style.lettering.home_glyph:
        return [], []
    size = style.nib.label_size_px * 0.85
    out: list[Label] = []
    boxes: list[Box] = []
    for place in basemap.places:
        if place.get("sym") != "house":
            continue
        x, y = card.xy(place["x"], place["y"])
        name = str(place.get("n") or "home")
        wide = max(measure_fn(name, size)[0], 26.0)
        box = (x - wide / 2, y - 10, x + wide / 2, y + 28)
        out.append(
            Label(
                name=name,
                kind="home",
                why="the rider's own place",
                px=x,
                py=y,
                tier=TIER_PLACE,
                size=size,
                box=box,
                tx=x,
                ty=y + HOME_NAME_DROP,
                anchor="middle",
            )
        )
        boxes.append(box)
    return out, boxes
