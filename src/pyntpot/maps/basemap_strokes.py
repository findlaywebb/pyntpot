"""The road and river strokes of a basemap, chained and drawn as someone would.

Key names: `roads_from_paths` and `rivers_from_paths`, which turn the vector map's
road and river path strings into the typed `Road` and `River` strokes the painter
reads; `drawn`, which simplifies a line and rounds its corners; `line_of`, a point list
as the basemap carries it; `Frame`, the clip box, tolerance and sizes the strokes are
stated against.

A street is one stroke: OSM hands it over cut at every junction, so the pieces of one
road (or one watercourse, by name) are chained back together before the brush is set
down. It does not fetch features, keep or drop roads by interaction, or paint. Invariants:
a road stroke shorter than the brush that would draw it is dropped; a river is drawn at
the width it measures at each point where mapped water gives one, and at its class
floor elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyntpot.ink.chains import join_strokes
from pyntpot.ink.polyline import Pt, clip_line, eased, length, simplify, smooth
from pyntpot.maps.basemap import Line, River, Road
from pyntpot.maps.rivers import CHANNEL_EASE_SAMPLES, channel, major_rivers, painted_width_px
from pyntpot.maps.svg_path import parse_path

if TYPE_CHECKING:
    from pyntpot.ink.brush_style import BrushStyle

#: The median sample of a width profile is the one at this share of its length.
MIDDLE = 2

#: The least a chain is joined across, in metres.
MIN_JOIN_M = 1.0

#: Brush width, in pixels, a band falls back to when the style names none.
FALLBACK_BRUSH_PX = 2.0

#: Painted width, in pixels, of a watercourse class the card has no curve for.
FALLBACK_WET_PX = 2.2

#: Tolerance share a river line is simplified at, against a road's.
RIVER_EPS_SHARE = 0.6

#: The brush each road band is painted with.
BAND_BRUSH = {"major": "road_major", "minor": "lane", "path": "track"}

#: The highway values that are paths for the brush's sake.
PATH_HIGHWAYS = ("track", "path", "footway", "bridleway")


@dataclass(frozen=True)
class Frame:
    """What the strokes are stated against.

    Attributes:
        clip: The card box in metres; pieces are cut to it.
        eps: Simplification tolerance in metres, the card's pixel size or more.
        geometry: The card geometry, for the display metres per pixel and the river floors.
        brush: The brush widths a stroke's floor is stated in.
    """

    clip: tuple[float, float, float, float]
    eps: float
    geometry: dict[str, Any]
    brush: BrushStyle


def line_of(points: list[Pt]) -> Line:
    """A polyline as the basemap carries it: float pairs at full precision."""
    return tuple((float(x), float(y)) for x, y in points)


def drawn(piece: list[Pt], tol: float) -> Line:
    """Simplify, then Chaikin: a line someone drew, not a line surveyed."""
    return line_of(smooth(simplify(piece, tol), passes=2))


def _band(row: dict[str, Any]) -> str:
    """Which brush paints a road row."""
    if row["c"] == "major":
        return "major"
    if row["k"] in PATH_HIGHWAYS:
        return "path"
    return "minor"


def roads_from_paths(rows: list[dict[str, Any]], frame: Frame) -> list[Road]:
    """The road strokes of the vector map's road rows.

    Three brushes' worth of road: the A and B roads, the lanes, and the tracks
    the session actually used, which get the scratchy dry brush.

    A street is one stroke. OSM hands it over cut at every junction, and
    painting each cut as its own stroke gave every one of them a set-down blot
    and a taper at both ends: `join_strokes` chains the pieces of one road
    back together first, so the brush is set down where the street starts and
    lifted where it ends.

    Args:
        rows: The road rows, each with its class, highway, name, number and path.
        frame: The clip box, tolerance and sizes.

    Returns:
        One stroke per chained road, in the order the roads first appear.
    """
    pieces: dict[tuple[Any, ...], list[list[Pt]]] = {}
    meta: dict[tuple[Any, ...], dict[str, Any]] = {}
    for r in rows:
        band = _band(r)
        # What counts as one road: its band, and the name or number it is known
        # by. Unnamed pieces of a band are one group and chain on their ends
        # alone, which is the right answer for a pavement network that has no
        # names to gather by.
        road_key = (band, r["n"], r.get("r", ""))
        meta.setdefault(
            road_key, {"c": r["c"], "b": band, "k": r["k"], "n": r["n"], "r": r.get("r", "")}
        )
        for seg in parse_path(r["d"]):
            pieces.setdefault(road_key, []).extend(
                c for c in clip_line(seg, frame.clip) if len(c) > 1
            )
    # And a stroke shorter than the brush that would draw it is a dab, not a
    # road. What is left after the chaining is mostly a slip lane or a link at a
    # junction that the chain could not take because it took the carriageway
    # instead: a hundred of them can be under one display pixel long, and each
    # still pays for a set-down blot the size of the brush.
    roads = []
    for road_key, lines in pieces.items():
        band = road_key[0]
        width = frame.brush.brush_width_px.get(BAND_BRUSH[band], FALLBACK_BRUSH_PX)
        floor = width * frame.geometry["mpp_display"]
        info = meta[road_key]
        for chain in join_strokes(lines, tol=max(frame.eps, MIN_JOIN_M)):
            if length(chain) < floor:
                continue
            roads.append(
                Road(
                    line=drawn(chain, frame.eps),
                    cls=info["c"],
                    band=info["b"],
                    highway=info["k"],
                    name=info["n"],
                    ref=info["r"],
                )
            )
    return roads


def _river(
    chain: list[Pt], cls: str, name: str, lakes: list[list[Pt]], frame: Frame, *, measured: bool
) -> River:
    """One watercourse chain as a stroke.

    Where the watercourse has mapped water to measure, it is re-centred in its own
    channel and drawn at the width it measures at each point rather than at one width
    throughout.
    """
    floor = frame.geometry["wet_px"].get(cls, FALLBACK_WET_PX)
    width, name_width, profile = floor, floor, ()
    if measured:
        chain, along = channel(chain, lakes)
        widths = [painted_width_px(floor, w or 0.0, frame.geometry["mpp_display"]) for w in along]
        widths = eased(widths, CHANNEL_EASE_SAMPLES)
        widest = max(widths)
        width = round(widest, 2)
        # And the width it is *typically* drawn at, which is the one a
        # name has to fit inside: `w` is the widest point and says how
        # far a name lifted clear of the water has to be lifted, but a
        # name set on the water could be set anywhere along it.
        name_width = round(sorted(widths)[len(widths) // MIDDLE], 2)
        profile = tuple(round(v / widest, 3) for v in widths)
    return River(
        line=drawn(chain, frame.eps * RIVER_EPS_SHARE),
        cls=cls,
        name=name,
        width_px=width,
        name_width_px=name_width,
        profile=profile,
    )


def rivers_from_paths(
    rows: list[dict[str, Any]], lakes: list[list[Pt]], frame: Frame
) -> list[River]:
    """The river strokes of the vector map's river rows.

    The pieces of each watercourse are gathered by name so it is measured and
    classed as one river rather than as the dozen ways OSM cut it into, and chained
    before it is measured or drawn, exactly as a road's are, so the width runs
    continuously along the river rather than restarting at every way OSM cut it at.

    Args:
        rows: The river rows, each with its class, name and path.
        lakes: The inland water rings the widths are measured against.
        frame: The clip box, tolerance and sizes.

    Returns:
        One stroke per chained watercourse, in the order the names first appear.
    """
    pieces_by: dict[str, list[list[Pt]]] = {}
    for r in rows:
        for seg in parse_path(r["d"]):
            pieces_by.setdefault(r["n"], []).extend(
                c for c in clip_line(seg, frame.clip) if len(c) > 1
            )
    major, widths = major_rivers(pieces_by, lakes, frame.brush.major_river_rel_frac)
    classed = {
        r["n"]: (("major" if r["n"] in major else "medium") if r["c"] == "river" else "minor")
        for r in rows
    }
    return [
        _river(chain, classed.get(name, "minor"), name, lakes, frame, measured=name in widths)
        for name, lines in pieces_by.items()
        for chain in join_strokes(lines, tol=max(frame.eps, MIN_JOIN_M))
    ]
