"""Which named roads a card numbers, set along their own tarmac.

Key names: `pick_roads`, the labels for the roads the track was on; `named_roads`, the
labels for the roads the caller names; `road_ref`, the number to letter out of OSM's
`ref`; `road_min_px`, the shortest run a number may be set along.

It does not pick settlements or rivers, and it does not place a name.

Invariants: a numbered road is one road whatever its pieces are called; a road the
track was never on is lettered only when the caller names it.
"""

import logging
import math
from typing import Any

from pyntpot.ink.chains import joined
from pyntpot.ink.polyline import Point, length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import TIER_ROAD, Label
from pyntpot.maps.lettering.label_sizing import feature_px
from pyntpot.maps.lettering.picks_lines import NamedLines

log = logging.getLogger(__name__)

#: How long a named road has to run inside the card before its number is worth
#: setting along it, as a multiple of the type size the number is written at.
#: Stated against the type because the question is whether the road is longer
#: than its own name: a road number is five characters and about two and a half
#: type sizes wide, so this is a run about two and a half times the name, which
#: is enough for the number to read as a name along the tarmac rather than as a
#: tag on the end of it.
ROAD_MIN_CAPS = 6.4


def road_min_px(size: float) -> float:
    """The shortest run of road a number may be set along, in display pixels."""
    return size * ROAD_MIN_CAPS


ROAD_MAX = 2
#: How near the route a road has to run, in display pixels, to be one the track was on.
ROAD_ON_ROUTE_PX = 40.0


def pick_roads(
    basemap: Basemap,
    lines: NamedLines,
    card: Card,
    route_px: list[Point],
    budget: int = ROAD_MAX,
) -> list[Label]:
    """Which named roads the map numbers, set along their own tarmac.

    A road number is the quietest thing on the map and one of the most useful:
    it is how someone on the track works out where a climb actually was. A road is lettered
    by its number where OSM has one, and by its name only where it has none:
    "A591" places a climb, "Keswick Road" eats a corner and says nothing at
    26 m a pixel. Only the roads the track was on, and only where there is
    enough of one inside the card to write on.

    **A numbered road is one road, whatever OSM calls each mile of it.** A
    street name changes at every parish: the A82 crosses a card as Glencoe,
    then Ballachulish, then New Road, then Kinlochleven Road, none of them a
    third of the shortest run a name can be set on. So where a road has a
    number the number is what its pieces are gathered by, and the name is only
    the fallback for a road that has none. Only major and medium roads are
    numbered.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the roads.
        card: The card, for the projection and its size.
        route_px: The track in display pixels.
        budget: How many to letter.

    Returns:
        One `Label` a road, best first, carrying the tarmac as its baseline.
    """
    thin = route_px[::4] or route_px
    pieces, widths, _osm_names = _road_pieces(
        basemap, lines.get("roads") or [], card, frozenset({"major", "medium"})
    )
    size = DEFAULT_LINE_PX * 0.7
    shortest = road_min_px(size)
    best: dict[str, tuple[float, list[Point]]] = {}
    for key, parts in pieces.items():
        line = max(joined(parts), key=length)
        if length(line) < shortest:
            continue
        near = min(min(math.dist(p, q) for q in thin) for p in line[::2])
        if near > ROAD_ON_ROUTE_PX:  # a road the track was never on is not this map's
            continue
        best[key] = (length(line) - near, line)
    out: list[Label] = []
    for key, (_score, line) in sorted(best.items(), key=lambda kv: -kv[1][0])[:budget]:
        mid = line[len(line) // 2]
        out.append(
            Label(
                name=key,
                kind="road",
                why="road the track was on",
                px=mid[0],
                py=mid[1],
                tier=TIER_ROAD,
                size=size,
                baseline=line,
                feature_px=widths.get(key, 0.0),
            )
        )
    return out


def named_roads(
    basemap: Basemap, lines: NamedLines, card: Card, names: tuple[str, ...]
) -> list[Label]:
    """The roads the caller names, each set along its own tarmac, in the caller's order.

    A name matches a road by its number or by any OSM name its pieces carry, ignoring
    case, over every road class the basemap draws, named or numbered. A label is
    lettered by the road's number when it has one, its name otherwise, even when the
    match was by name: "Lynbridge Road" letters "B3234". A road matched twice (named
    twice, or by number and by name) is lettered once, where it was first named; a name
    carried by several roads letters each of them. There is no budget and no test of
    how near the track a road runs.

    A named road's label sits on its longest run over its named and numbered pieces
    together, so naming a road the card would pick anyway can move where its number
    sits. A road whose run is shorter than `road_min_px` is not lettered and is logged
    at INFO: it is drawn, and whether its number fits depends on the card's size. A
    road all of whose pieces fall under two points, once simplified or on the card's
    pixel grid, counts as not drawn.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the roads and the numbered pieces.
        card: The card, for the projection and its size.
        names: The road numbers or names the caller listed.

    Returns:
        One `Label` a matched road long enough to letter, in the order listed.

    Raises:
        ValueError: A listed name matches no road the map draws; every such name is
            given.
    """
    entries = (lines.get("roads") or []) + (lines.get("numbered") or [])
    pieces, widths, osm_names = _road_pieces(basemap, entries, card, None)
    size = DEFAULT_LINE_PX * 0.7
    shortest = road_min_px(size)
    seen: set[str] = set()
    unmatched: list[str] = []
    out: list[Label] = []
    for name in names:
        wanted = name.casefold()
        keys = [k for k in pieces if k.casefold() == wanted or wanted in osm_names[k]]
        if not keys:
            unmatched.append(name)
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            line = max(joined(pieces[key]), key=length)
            if length(line) < shortest:
                log.info("road %s is too short on this card to letter", key)
                continue
            mid = line[len(line) // 2]
            out.append(
                Label(
                    name=key,
                    kind="road",
                    why="road the caller named",
                    px=mid[0],
                    py=mid[1],
                    tier=TIER_ROAD,
                    size=size,
                    baseline=line,
                    feature_px=widths[key],
                )
            )
    if unmatched:
        joined_names = ", ".join(repr(n) for n in unmatched)
        raise ValueError(f"no road the map draws is numbered or named {joined_names}")
    return out


def _road_pieces(
    basemap: Basemap,
    entries: list[dict[str, Any]],
    card: Card,
    classes: frozenset[str] | None,
) -> tuple[dict[str, list[list[Point]]], dict[str, float], dict[str, set[str]]]:
    """The roads' pieces in display pixels, gathered by number, or by name where there is none.

    Args:
        basemap: The basemap, for the width each class was painted at.
        entries: Road entries of the named lines.
        card: The card, for the projection.
        classes: The road classes kept, or `None` to keep every class.

    Returns:
        `(pieces, widths, osm_names)`, each keyed by the road's number or name in
        first appearance: the pieces of two or more points, the widest painted width,
        and the casefolded OSM names its pieces carry. Every key of `osm_names` is a
        key of `pieces` and `widths`.
    """
    pieces: dict[str, list[list[Point]]] = {}
    widths: dict[str, float] = {}
    osm_names: dict[str, set[str]] = {}
    for entry in entries:
        name = str(entry.get("n") or "")
        key = road_ref(entry.get("r")) or name
        if not key or (classes is not None and entry.get("c") not in classes):
            continue
        line = [card.xy(x, y) for x, y in entry.get("d") or []]
        if len(line) > 1:
            pieces.setdefault(key, []).append(line)
            widths[key] = max(
                widths.get(key, 0.0), feature_px(basemap, "road", str(entry.get("c")))
            )
            known = osm_names.setdefault(key, set())
            if name:
                known.add(name.casefold())
    return pieces, widths, osm_names


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
