"""The named lines a name can be set along, and the lines a name must not be laid across.

Key names: `NamedLines`, the roads, rivers, coast and crossings in card metres;
`named_lines`, which builds them from a basemap; `road_lines`, which turns them into
display-pixel lines a name is charged for crossing.

It does not choose a name or place one.

Invariants: only named roads and rivers carry a name; an unnamed lane is kept as a bare
crossing line so the cost can still see it.
"""

from typing import Any

from pyntpot.ink.polyline import Pt, simplify
from pyntpot.maps.basemap import Basemap, Line
from pyntpot.maps.card import Card

#: The lines a label may be set along or is charged for crossing, by kind:
#: `roads` and `rivers` (one entry a named line), `coast` and `crossings` (bare
#: point lists), in card metres. `named_lines` builds it from a basemap.
NamedLines = dict[str, list[Any]]


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
        """The line simplified at the tolerance, or none when too short."""
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


def road_lines(lines: NamedLines, card: Card) -> list[list[Pt]]:
    """Everything on the card a name should not be laid across, in display pixels.

    The named roads, the unnamed lanes, and the watercourses. All three are
    marks on the paper and a name written over any of them is harder to read,
    so a label pays as much for an unnamed lane or a river as for a named road.
    The lanes have no name and cannot carry one, so they are kept in
    `crossings` purely for this.
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
