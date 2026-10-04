"""What the map letters, where each name sits, and how wide it is.

One module owns the label layer, so the page and the standalone card put a
name in the same place: `charts.journal_map` and the map's lettering stage both
resolve their picks here and both call `place`. Nothing here draws. A caller takes the
placed `Label`s and the placed `Span`s and strokes them with whatever machinery
it has, vector on the page or a brush on a plate.

Three things are worth knowing before changing anything in here.

**The measure is the caller's, and it is required.** Every box on the sheet is
sized by the `measure` a caller passes to `place`, `place_spans` and
`home_labels`; there is no default. The map letters with the hand's own
`Hand.measure`, so the boxes the placer defends are the widths the letterforms
really take.

**A span is not a pin.** A climb has an extent, and the extent is thrown away
the moment it becomes a latitude and a longitude. `Span` carries the extent
through to a line drawn beside the route, offset by an iso-distance contour
rather than by a normal, because a normal offset self-intersects on exactly the
hairpins a climb is made of.

**The ground is drawn in the map's ink; the session is drawn in the route's
ink.** Settlements, rivers, roads, climbs and landmarks are the ground. Effort
spans and route markers are the session. Every other rule in here follows from
that one.
"""

from __future__ import annotations

import logging
import math
import re
from typing import TYPE_CHECKING, Any

from pyntpot.ink.chains import joined
from pyntpot.ink.polyline import (
    cumulative_length,
    length,
    simplify,
)
from pyntpot.ink.sheet import Canvas
from pyntpot.letters import nib
from pyntpot.letters.setting import DEFAULT_LINE_PX
from pyntpot.letters.style import NibGroups

if TYPE_CHECKING:
    from pyntpot.maps.basemap import Basemap, Line
    from pyntpot.maps.lettering.label import Box, Label, Measure, Span
    from pyntpot.maps.plates import Plates
    from pyntpot.maps.style import Style

log = logging.getLogger(__name__)

Pt = tuple[float, float]
#: The named lines a label may be set along, by kind: `roads` and `rivers`
#: (one entry a named line), `coast` and `crossings` (bare point lists), in
#: card metres. `named_lines` builds it from a basemap.
NamedLines = dict[str, list[Any]]


#: How much water a name needs under it before it is written on the water, as a
#: multiple of its own type size. Two and a bit: the letters occupy about one
#: type size of band, so this leaves better than half a size of water either
#: side of them. Measured against the width the river is *typically* drawn at
#: rather than its widest point, because a name set on the water may be set
#: anywhere along it.
IN_WATER_CAPS = 2.2


# --------------------------------------------------------------------------- picks


def journal_picks(picks: Any, basemap: Basemap, cap: int) -> list[dict[str, Any]]:
    """The payload's landmarks, each with a position, in the payload's order.

    A pick states its own latitude and longitude, which is what the label agent
    is asked for. A pick that is only a name is looked up in the candidates the
    box offered, so an older payload still labels its map.
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
    """The fallback when the payload named none: the nearest named things."""
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


def named_lines(basemap: Basemap, tol_px: float) -> NamedLines:
    """The lines a name can be set along, simplified, in the card's own metres.

    The named centrelines and the coastline, at a tolerance that is generous
    because a baseline is read at a glance and never measured.

    Args:
        basemap: The basemap, for its roads, watercourses and coastline.
        tol_px: Simplification tolerance in display pixels.

    Returns:
        `{"roads": [...], "rivers": [...], "coast": [...], "crossings": [...]}`:
        each road and river entry a name, a class, a road number where OSM has
        one, the painted widths and a polyline `d`; each coast and crossing
        entry a bare polyline.
    """
    layers = basemap.layers
    tol = max(tol_px * float(basemap.card.mpp_display), 1.0)

    def kept_lines(line: Line) -> list[list[list[float]]]:
        out = []
        for piece in [list(line)] if len(line) > 1 else []:
            kept = simplify(piece, tol)
            if len(kept) > 1:
                out.append([[x, y] for x, y in kept])
        return out

    named: dict[str, list[dict[str, Any]]] = {
        "roads": [
            {"n": r.name, "c": r.cls, "r": r.ref, "w": 0.0, "wn": 0.0, "line": r.line}
            for r in layers.roads
        ],
        "rivers": [
            {
                "n": r.name,
                "c": r.cls,
                "r": "",
                "w": r.width_px,
                "wn": r.name_width_px,
                "line": r.line,
            }
            for r in layers.rivers
        ],
    }
    geom: NamedLines = {"roads": [], "rivers": [], "coast": [], "crossings": []}
    for key in ("roads", "rivers"):
        for entry in named[key]:
            for line in kept_lines(entry["line"]):
                if entry["n"]:
                    # `w` is the width this watercourse was actually painted at,
                    # which is its own where one could be measured and the class
                    # floor where it could not. A name clears the ink it is set
                    # beside, so it has to be the ink that was laid down and not
                    # what the class would have laid down.
                    geom[key].append(
                        {
                            "n": entry["n"],
                            "c": entry["c"],
                            "r": entry["r"],
                            "w": entry["w"],
                            "wn": entry["wn"],
                            "d": line,
                        }
                    )
                else:
                    # An unnamed lane can carry no name of its own, so a label
                    # could be laid across one for nothing. It is kept, without
                    # a name, purely so the crossing cost can see it.
                    geom["crossings"].append(line)
    for coast in layers.coastline:
        geom["coast"].extend(kept_lines(coast))
    return geom


def road_lines(lines: NamedLines, card: Any) -> list[list[Pt]]:
    """Everything on the card a name should not be laid across, in card pixels.

    The named roads, the unnamed lanes, and the watercourses. All three are
    marks on the paper and a name written over any of them is harder to read;
    the named roads were the only ones charged, so a label could sit on an
    unnamed lane for nothing and "Swell" could sit on its own river. The
    lanes have no name and cannot carry one, so they are kept in `crossings`
    purely for this.
    """
    out: list[list[Pt]] = []
    geom = lines
    for key in ("roads", "rivers"):
        for entry in geom.get(key) or []:
            line = [card.xy(x, y) for x, y in entry.get("d") or []]
            if len(line) > 1:
                out.append(line)
    for raw in geom.get("crossings") or []:
        line = [card.xy(x, y) for x, y in raw]
        if len(line) > 1:
            out.append(line)
    return out


# --------------------------------------------------------------------------- spans


#: When a mark fails as a mark. Two things only: nothing was drawn, or what was
#: drawn comes nearer the route than the clearance it was given. Neither is a
#: matter of taste. What used to be here as well - that a mark must not close
#: on itself, and that it must hold the offset the ladder reserved to within a
#: quarter - is withdrawn: a mark may be drawn round a doubled-back stretch,
#: which encloses it, and its distance from the route is allowed to vary.


# --------------------------------------------------------------------------- settlements

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
    """Every settlement the painted box holds, merged into places.

    The candidates already carry them: `journal_layers` asks for every named
    thing, so a place node is in the basemap whether or not it is a landmark.
    Nothing here is fetched and nothing is repainted.
    """
    from pyntpot.maps.lettering.placement_names import _stem

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
    card: Any,
    route_px: list[Pt],
    always: list[str] | None = None,
    wanted: list[str] | None = None,
    budget: int | None = None,
) -> list[Label]:
    """Which settlements the sheet names, by rank and by route relationship.

    Never by raw distance order: a distance sort exhausts itself inside one
    town's wall plaques, which is the fault the "a place name is not a landmark"
    rule was written to stop. Settlements draw from their own pool and their own
    budget and never compete with the landmarks for a slot.

    Args:
        basemap: The basemap, for its candidates.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        always: Names the user's own file says to letter whenever the box
            holds them, which do not spend a slot.
        wanted: Names this session's payload asked for, likewise.
        budget: How many to letter; from the card's width when not given.

    Returns:
        One `Label` a settlement, highest score first, anchored in card pixels.
    """
    from pyntpot.maps.lettering.label import TIER_SETTLEMENT, Label

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
    entry: dict[str, Any], found: list[dict[str, Any]], card: Any, ends: list[Pt], reach: float
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


# --------------------------------------------------------------------------- rivers

#: How many watercourses a sheet names. The major one always, and the best
#: medium only when it is worth having beside it. Never a brook.
RIVER_MAX = 2
RIVER_REL_FLOOR = 0.2

#: How much water a river has to have on the sheet before it is lettered twice,
#: as a share of the card's longer side. The reason for the second name is that
#: a river crossing the whole sheet is read in pieces; a river clipping a corner
#: is read in one, and the second name has nowhere to go but away from its own
#: water. With a single major watercourse on the sheet and only 295 px of
#: water on a 900 px sheet, it would take both allowances and write the second
#: one in open paper past the end of the river. The allowance is earned by the
#: run, not by the rank.
MAJOR_RIVER_TWICE_FRAC = 0.55


def pick_rivers(
    basemap: Basemap,
    lines: NamedLines,
    card: Any,
    route_px: list[Pt],
    budget: int = RIVER_MAX,
) -> list[Label]:
    """Which watercourses the sheet names, by run inside the card and proximity.

    The painting classes answer "how wide is the brush" and are computed from
    run length alone, which cannot separate two tributaries of the same length.
    What separates them on a ride is the route: the one it crossed is the one
    worth naming.

    Args:
        basemap: The basemap, for the width each class was painted at.
        lines: The named lines, for the watercourses.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        budget: How many to letter.

    Returns:
        One `Label` a river, best first, anchored on its own water and carrying
        the water as its baseline.
    """
    from pyntpot.maps.lettering.label import TIER_RIVER, Label, feature_px
    from pyntpot.maps.lettering.placement_names import MAJOR_RIVER_LABELS
    from pyntpot.maps.lettering.placement_window import _on_line

    geom = lines.get("rivers") or []
    thin = route_px[::3] or route_px
    typical: dict[str, float] = {}
    scored: list[tuple[float, str, list[Pt]]] = []
    widths: dict[str, float] = {}
    for entry in geom:
        name = str(entry.get("n") or "")
        if not name or entry.get("c") == "minor":
            continue
        line = [card.xy(x, y) for x, y in entry.get("d") or []]
        if len(line) < 2:
            continue
        run_m = length(line) / max(card.scale, 1e-9)
        near_m = min(min(math.dist(p, q) for q in thin) for p in line[::2]) / max(card.scale, 1e-9)
        score = run_m / 1000.0 * min(max(1.0 - near_m / 500.0, 0.2), 1.0)
        widths[name] = max(
            widths.get(name, 0.0),
            feature_px(basemap, "river", str(entry.get("c")), float(entry.get("w") or 0.0)),
        )
        # The width the river is typically drawn at, which is what decides
        # whether its own name fits in it.
        typical[name] = max(
            typical.get(name, 0.0),
            feature_px(basemap, "river", str(entry.get("c")), float(entry.get("wn") or 0.0)),
        )
        scored.append((score, name, line))
    # One river arrives as a dozen ways, and taking the longest of them threw
    # most of the water away: a name may go anywhere along its own watercourse,
    # and that freedom is only real if the whole watercourse is one line. The
    # pieces are chained end to end first, exactly as a road's are.
    pieces: dict[str, list[list[Pt]]] = {}
    totals: dict[str, float] = {}
    for score, name, line in scored:
        pieces.setdefault(name, []).append(line)
        totals[name] = totals.get(name, 0.0) + score
    merged: dict[str, tuple[float, list[Pt]]] = {
        name: (totals[name], max(joined(parts), key=length)) for name, parts in pieces.items()
    }
    order = sorted(merged.items(), key=lambda kv: -kv[1][0])
    out: list[Label] = []
    for rank, (name, (score, line)) in enumerate(order[:budget]):
        if out and score < RIVER_REL_FLOOR * order[0][1][0]:
            break
        # The major river is the first, and it is the only one lettered twice.
        # The two are anchored at the third and at the two-thirds point of the
        # water so the placer starts them in different halves; each is then free
        # to move anywhere along the whole line from there, and the repeat guard
        # in `place` keeps them from converging on the same window.
        run = length(line)
        twice = run >= MAJOR_RIVER_TWICE_FRAC * max(card.w, card.h)
        times = MAJOR_RIVER_LABELS if rank == 0 and twice else 1
        for n in range(times):
            at = (n + 1) / (times + 1)
            anchor = _on_line(line, cumulative_length(line), run * at)[0]
            size = DEFAULT_LINE_PX * 0.9
            out.append(
                Label(
                    name=river_name(name),
                    kind="river",
                    why=name,
                    px=anchor[0],
                    py=anchor[1],
                    tier=TIER_RIVER,
                    size=size,
                    baseline=line,
                    in_water=typical.get(name, 0.0) >= size * IN_WATER_CAPS,
                    feature_px=widths.get(name, 0.0),
                )
            )
    return out


def river_name(name: str) -> str:
    """ "River Eden" as "Eden": the water it is written on says the rest."""
    return re.sub(r"^River\s+", "", str(name)).strip() or str(name)


# --------------------------------------------------------------------------- the ground


def home_places(basemap: Basemap, card: Any) -> list[Label]:
    """The user's own places, as labels, for the ones with no glyph of their own.

    An entry with a symbol is drawn by the caller as it always was, glyph and
    name together, and is not returned here. An entry marked
    `kind: settlement` has no glyph and is lettered like any other settlement,
    which is what "Swell, a village" wants and what a house
    marker would say wrongly.
    """
    from pyntpot.maps.lettering.label import TIER_PLACE, Label

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
    card: Any,
    route_px: list[Pt],
    picks: Any | None = None,
) -> list[Label]:
    """The names the ground is entitled to, whatever the payload asked for.

    Settlements and watercourses are already in the data and have simply never
    been lettered: the settlements sit in the basemap's candidates and the
    watercourses in its named lines. Choosing them is a rule, not a judgement,
    so it runs by default and the payload only ever adds to it.

    Three tiers own the answer, in this order: the rule, the user's own file
    for a standing exception, and `map.places` in the payload for this session.

    Args:
        basemap: The basemap, for its places and candidates.
        lines: The named lines, for the watercourses.
        card: The card, for the projection and its size.
        route_px: The track in card pixels.
        picks: The payload's `map` block, whose `places` name this session's
            exceptions. That hook has existed and done nothing since it was
            written; this is what reads it.

    Returns:
        The user's places, then the settlements, then the rivers, in the
        order they claim their boxes.
    """
    mine = home_places(basemap, card)
    always = [p.get("n", "") for p in basemap.places if p.get("always")] + [lb.name for lb in mine]
    wanted = list(getattr(picks, "places", None) or [])
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


# --------------------------------------------------------------------------- roads

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


def pick_roads(
    basemap: Basemap,
    lines: NamedLines,
    card: Any,
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
    from pyntpot.maps.lettering.label import TIER_ROAD, Label, feature_px

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
        if near > 40.0:  # a road the session was never on is not this map's
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


def road_ref(raw: Any) -> str:
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


def route_markers(route_px: list[Pt], size: float = DEFAULT_LINE_PX * 0.65) -> list[Label]:
    """Where the session set off and where it finished, in the route's own ink.

    The ground is drawn in the map's ink and the session in the route's, and
    these two are the session: they are facts about the ride, not about the
    place. A loop puts them on top of each other, so it gets one mark.
    """
    from pyntpot.maps.lettering.label import TIER_MARKER, Label

    if len(route_px) < 2:
        return []
    start, end = route_px[0], route_px[-1]
    if math.dist(start, end) < 30.0:
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


# --------------------------------------------------------------------------- home

#: How far below its house a user's own place has its name written.
HOME_NAME_DROP = 25.0


def home_labels(
    basemap: Basemap, card: Any, style: Style, measure_fn: Measure
) -> tuple[list[Label], list[Box]]:
    """The user's marked places, already placed, and the room they need.

    A house is not placed by the placer: it is where it is, and its name goes
    under it. So it comes back placed, with the box it occupies, and the box
    goes into the placer's `taken` list so nothing else is written across it.

    Args:
        basemap: The basemap, for its places.
        card: The card, for the projection and its size.
        style: The style, for the type size and whether to draw at all.
        measure_fn: How wide a name is.

    Returns:
        The labels, and the boxes they have already claimed.
    """
    from pyntpot.maps.lettering.label import TIER_PLACE, Label

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
        out.append(
            Label(
                name=name,
                kind="home",
                why="the rider's own place",
                px=x,
                py=y,
                tier=TIER_PLACE,
                size=size,
                box=(x - wide / 2, y - 10, x + wide / 2, y + 28),
                tx=x,
                ty=y + HOME_NAME_DROP,
                anchor="middle",
            )
        )
        boxes.append(out[-1].box)
    return out, boxes


# --------------------------------------------------------------------------- the plate


def draw_plate(
    plates: Plates,
    placed: list[Label],
    spans: list[Span],
    route_px: list[Pt],
    style: Style,
    route: str | None = None,
) -> Any:
    """Stroke the placed names into an RGBA plate beside the other plates.

    The lettering is raster because the ink is: `stamp` deposits into a numpy
    accumulator gated on the paper's own height, and there is no path out of
    that to vector. So the label layer is a fourth plate, and the page and the
    card both draw the same pixels instead of each approximating them.

    It is cached on `Cache.lettering_key`: the marks to be stroked, the base
    plates' hash and the style's lettering digest, so a moved name, pin, leader
    or span line, a repaint of the base plates or another hand all change it. A
    plate whose key does not match is not drawn at all rather than lettering
    yesterday's names over today's map.

    Args:
        plates: The painted plates, beside which the label plate is written.
        placed: The placed labels.
        spans: The placed spans.
        route_px: The track in card pixels.
        style: The style the card is lettered in; its brush style makes the
            lettering's brushes and ink pads.
        route: `centreline` or `outline`; the style's when not given.

    Returns:
        The path to the plate, or None when there is nothing to draw or no
        engine to draw it with.
    """
    import json

    if not placed and not spans:
        return None
    from pyntpot.letters.hand import Hand
    from pyntpot.maps import lettering_marks
    from pyntpot.maps.cache import Cache
    from pyntpot.maps.plates import dark_array

    try:
        hand = Hand(style.face, style.hand, route)
    except (ImportError, OSError) as exc:  # no fonttools, or no face on disk
        log.info("no face to letter with: %s", exc)
        return None
    root = plates.directory
    stem = f"labels-{hand.route}"
    path, side = root / f"{stem}.webp", root / f"{stem}.json"
    marks = lettering_marks.marks(hand, placed, spans)
    if not marks:
        return None
    key = Cache.lettering_key(marks, plates.hash, style)
    if path.exists() and side.exists():
        try:
            if json.loads(side.read_text()).get("key") == key:
                return path
        except (OSError, ValueError):  # a half-written key is not a crash
            pass
    card = plates.card
    rw, rh = card.render
    surface = nib.NibSurface(
        Canvas(*card.box, rw, rh),
        card.render_scale,
        dark_array(plates.manifest.dark, rh, rw),
        plates.manifest.gran_px,
    )
    written = nib.plate(
        marks, surface, NibGroups(style.nib, style.face, style.hand, style.brush, style.paper), path
    )
    if written is not None:
        side.write_text(json.dumps({"key": key, "face": hand.font.name, "route": hand.route}))
    return written
