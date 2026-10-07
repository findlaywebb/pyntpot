"""Which settlements a card names: ranked, merged into places and spaced apart.

Key names: `settlements`, the candidate places merged by stem; `pick_settlements`, the
labels the sheet carries and `settlement_budget`, how many a card this wide holds.

It does not pick rivers, roads or landmarks, and it does not place a name.

Invariants: a settlement is never chosen by raw distance; a forced name spends no slot.
"""

import math
from typing import Any

from pyntpot.ink.polyline import Pt, length
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.card import Card
from pyntpot.maps.lettering.label import TIER_SETTLEMENT, Label
from pyntpot.maps.lettering.placement_names import _stem

#: What a settlement is worth before the route is taken into account.
SETTLEMENT_RANK = {"city": 4.0, "town": 3.0, "village": 2.0, "suburb": 1.5, "hamlet": 1.0}
#: How near two members of a pair have to be to be the same place, in metres.
MERGE_M = 1500.0
#: Past this a settlement is not part of this ride.
SETTLEMENT_MAX_OFF_M = 1500.0
#: Under this a settlement is not worth a name: a run through empty country gets
#: one label or none rather than three hamlets.
SETTLEMENT_FLOOR = 3.0
#: How far apart two settlement names have to be on the sheet, in display pixels
#: of a 900 px card, so two villages a kilometre apart never both letter. Scaled
#: with the card, because the constraint is the sheet and not the ground.
SETTLEMENT_SEPARATION_PX = 120.0
#: How near an end of the route a settlement has to be to have been where the
#: session set off from or finished, as a fraction of the route's own length.
#: Stated against the ride rather than in metres because on a loop through empty
#: country the one settlement for miles is nearest to both ends and has earned
#: nothing by it.
SETTLEMENT_ENDPOINT_FRAC = 0.05


def settlements(basemap: Basemap) -> list[dict[str, Any]]:
    """Every settlement among the basemap's candidates, merged into places.

    The candidates already carry them: the feature layers collect every named
    thing, so a place node is among the candidates whether or not it is a
    landmark. Nothing here is fetched and nothing is repainted.
    """
    found: list[dict[str, Any]] = []
    for c in basemap.candidates:
        if c.get("class") != "place":
            continue
        kind = str((c.get("tags") or {}).get("place", ""))
        if kind not in SETTLEMENT_RANK:
            continue
        found.append(
            {
                "name": c["name"],
                "kind": kind,
                "x": c["x"],
                "y": c["y"],
                "off_route_m": float(c.get("distance_m") or 0.0),
            }
        )
    groups: list[dict[str, Any]] = []
    for entry in sorted(found, key=lambda e: e["off_route_m"]):
        stem = _stem(entry["name"])
        for group in groups:
            if group["stem"] != stem:
                continue
            if math.dist((group["x"], group["y"]), (entry["x"], entry["y"])) > MERGE_M:
                continue
            # Positioned on the member nearest the route, which is the one the
            # route actually runs through.
            group["kind"] = max(group["kind"], entry["kind"], key=lambda k: SETTLEMENT_RANK[k])
            break
        else:
            groups.append({**entry, "name": stem, "stem": stem})
    return groups


def settlement_budget(display_px: float) -> int:
    """How many settlements a card this wide carries.

    The constraint is card area, not ground area: a bigger box means more
    settlements competing for the same slots, not more slots.
    """
    return max(2, min(round(3 * display_px / 900.0), 5))


def pick_settlements(
    basemap: Basemap,
    card: Card,
    route_px: list[Pt],
    always: list[str] | None = None,
    wanted: list[str] | None = None,
    budget: int | None = None,
) -> list[Label]:
    """Which settlements the sheet names, by rank and by route relationship.

    Never by raw distance order: a distance sort exhausts itself inside one
    town's wall plaques. Settlements draw from their own pool and their own
    budget and never compete with the landmarks for a slot.

    Args:
        basemap: The basemap, for its candidates.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        always: Names the user's own file says to letter whenever the box
            holds them, which do not spend a slot.
        wanted: Names the annotations' `places` ask for, likewise.
        budget: How many to letter; from the card's width when not given.

    Returns:
        One `Label` a settlement, highest score first, anchored in card pixels.
    """
    always_set = {str(n).casefold() for n in (always or [])}
    wanted_set = {str(n).casefold() for n in (wanted or [])}
    budget = budget if budget is not None else settlement_budget(card.w)
    ends = [route_px[0], route_px[-1]] if route_px else []
    reach = length(route_px) * SETTLEMENT_ENDPOINT_FRAC
    found = settlements(basemap)
    scored: list[tuple[float, bool, dict[str, Any], Pt]] = []
    for entry in found:
        if entry["off_route_m"] > SETTLEMENT_MAX_OFF_M:
            continue
        at = card.xy(entry["x"], entry["y"])
        forced = entry["name"].casefold() in always_set or entry["name"].casefold() in wanted_set
        endpoint = bool(ends) and _nearest_to_ends(entry, found, card, ends, reach)
        score = (
            1.6 * SETTLEMENT_RANK[entry["kind"]]
            + 2.0 * max(0.0, 1.0 - entry["off_route_m"] / 800.0)
            + (1.5 if endpoint else 0.0)
            + (100.0 if forced else 0.0)
        )
        scored.append((score, forced, entry, at))
    scored.sort(key=lambda s: -s[0])
    out: list[Label] = []
    spent = 0
    for score, forced, entry, (x, y) in scored:
        if not (0 < x < card.w and 0 < y < card.h):
            continue
        if not forced and (score < SETTLEMENT_FLOOR or spent >= budget):
            continue
        apart = SETTLEMENT_SEPARATION_PX * card.w / 900.0
        if any(math.dist((x, y), (lb.px, lb.py)) < apart for lb in out):
            continue
        town = entry["kind"] in ("city", "town")
        out.append(
            Label(
                name=entry["name"],
                kind="settlement",
                why=f"{entry['kind']}, {entry['off_route_m']:.0f} m off the route",
                px=x,
                py=y,
                tier=TIER_SETTLEMENT,
                size=DEFAULT_LINE_PX * (1.15 if town else 0.85),
            )
        )
        if not forced:
            spent += 1
    return out


def _nearest_to_ends(
    entry: dict[str, Any], found: list[dict[str, Any]], card: Card, ends: list[Pt], reach: float
) -> bool:
    """True when this is the settlement the route set off from or finished in.

    Nearest is not enough on its own: on a loop through empty country the only
    settlement for miles is nearest to both ends and has earned nothing.
    """
    here = card.xy(entry["x"], entry["y"])
    for end in ends:
        mine = math.dist(here, end)
        if mine > reach:
            continue
        if all(math.dist(card.xy(o["x"], o["y"]), end) >= mine for o in found):
            return True
    return False
