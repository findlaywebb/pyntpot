"""The road and river strokes of a basemap, chained and drawn as someone would.

Key names: `roads_from_paths` and `rivers_from_paths`, which turn the vector map's
road and river path strings into the typed `Road` and `River` strokes the painter
reads; `drawn`, which simplifies a line and rounds its corners; `line_of`, a point list
as the basemap carries it; `Frame`, the clip box, tolerance and sizes the strokes are
stated against.

A street is one stroke: OSM hands it over cut at every junction, so the pieces of one
road (or one watercourse, by name) are chained back together before the brush is set
down. It does not fetch features, keep or drop roads by interaction, or paint. Invariants:
a road stroke shorter than the brush that would draw it is dropped; a lane, path or stream
stroke shorter than `STUB_FLOOR_PX` display pixels is dropped unless both its ends meet
another stroke (`stubs`); a river is drawn at the width it measures at each point where
mapped water gives one, and at its class floor elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyntpot.ink.chains import join_strokes
from pyntpot.ink.cut import cut_line
from pyntpot.ink.polyline import Pt, clip_line, eased, foot_on, length, simplify, smooth
from pyntpot.maps.basemap import Line, River, Road
from pyntpot.maps.rivers import CHANNEL_EASE_SAMPLES, channel, major_rivers, painted_width_px
from pyntpot.maps.svg_path import parse_path

if TYPE_CHECKING:
    from pyntpot.ink.brush_style import BrushStyle

#: The median sample of a width profile is at index `len(widths) // MIDDLE`.
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

#: The road bands and the watercourse class a short loose piece is dropped from. The
#: major roads and the rivers are left whole: a gap in either would show.
STUB_BANDS = ("minor", "path")
STUB_CLASS = "minor"

#: A lane, path or stream stroke shorter than this, in display pixels, with an end that
#: meets nothing, is a stub: a hair sticking out of the route where the track met the
#: end of a driveway, or a dash of brook that starts and stops on the land. Twenty
#: pixels is a couple of letters of a name; less than that says nothing about where
#: the road or the water goes.
STUB_FLOOR_PX = 20.0

#: How near, in display pixels, a stroke's end has to come to another stroke to meet it.
MEET_PX = 1.5


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


def stubs(
    lines: list[list[Pt]], short: list[bool], ground: list[list[Pt]], meet: float
) -> set[int]:
    """The short lines with an end that meets no other line: the strokes not to draw.

    A short piece between two others is a link in the network, a street joining two
    streets or a beck joining a lake to a river, and is kept; a short piece with an end
    on nothing is a stub.

    Args:
        lines: The strokes, in metres.
        short: Whether each stroke is short enough to be a stub.
        ground: Further lines an end may meet, such as the lake shores, in metres; none empty.
        meet: How near an end has to come to another line to meet it, in metres.

    Returns:
        The indices of the short strokes that have a loose end.
    """
    others = [(i, line, _box(line, meet)) for i, line in enumerate([*lines, *ground])]

    def met(end: Pt, own: int) -> bool:
        x, y = end
        return any(
            i != own
            and box[0] <= x <= box[2]
            and box[1] <= y <= box[3]
            and foot_on(end, line)[0] <= meet
            for i, line, box in others
        )

    return {
        i for i, line in enumerate(lines) if short[i] and not (met(line[0], i) and met(line[-1], i))
    }


def _box(line: list[Pt], grow: float) -> tuple[float, float, float, float]:
    """A line's bounding box grown by `grow` on every side."""
    xs = [p[0] for p in line]
    ys = [p[1] for p in line]
    return (min(xs) - grow, min(ys) - grow, max(xs) + grow, max(ys) + grow)


def _band(row: dict[str, Any]) -> str:
    """Which brush paints a road row."""
    if row["c"] == "major":
        return "major"
    if row["k"] in PATH_HIGHWAYS:
        return "path"
    return "minor"


def roads_from_paths(rows: list[dict[str, Any]], frame: Frame) -> list[Road]:
    """The road strokes of the vector map's road rows.

    Three bands of road, each with its own brush: the major roads, the lanes,
    and the paths (tracks, paths, footways and bridleways).

    A street is one stroke. OSM hands it over cut at every junction, and
    painting each cut as its own stroke would give each one a set-down blot
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
    # instead: many are under one display pixel long, and each would still pay
    # for a set-down blot the size of the brush.
    mpp = frame.geometry["mpp_display"]
    chains: list[tuple[list[Pt], dict[str, Any]]] = []
    for road_key, lines in pieces.items():
        band = road_key[0]
        width = frame.brush.brush_width_px.get(BAND_BRUSH[band], FALLBACK_BRUSH_PX)
        floor = width * mpp
        chains += [
            (chain, meta[road_key])
            for chain in join_strokes(lines, tol=max(frame.eps, MIN_JOIN_M))
            if length(chain) >= floor
        ]
    # And a lane or path that is short and ends on nothing is a stub: the end of a
    # driveway the track touched, drawn as a hair off the route.
    short = [i["b"] in STUB_BANDS and length(c) < STUB_FLOOR_PX * mpp for c, i in chains]
    dropped = stubs([c for c, _ in chains], short, [], MEET_PX * mpp)
    return [
        Road(
            line=drawn(chain, frame.eps),
            cls=info["c"],
            band=info["b"],
            highway=info["k"],
            name=info["n"],
            ref=info["r"],
        )
        for i, (chain, info) in enumerate(chains)
        if i not in dropped
    ]


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
        # name has to fit inside: `width` is the widest point and says how
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
            # Cut where it crosses the card's edge, so a river that comes in from
            # beyond the card starts on the edge, where the stamp knows it was not
            # set down on this paper, rather than at its first point inside.
            pieces_by.setdefault(r["n"], []).extend(cut_line(seg, frame.clip))
    major, widths = major_rivers(pieces_by, lakes, frame.brush.major_river_rel_frac)
    classed = {
        r["n"]: (("major" if r["n"] in major else "medium") if r["c"] == "river" else "minor")
        for r in rows
    }
    chains = [
        (chain, name, classed.get(name, "minor"))
        for name, lines in pieces_by.items()
        for chain in join_strokes(lines, tol=max(frame.eps, MIN_JOIN_M))
    ]
    # A stream that is short and ends on nothing, not on other water, is a dash on
    # the land: drawn, it reads as water that stops dead.
    mpp = frame.geometry["mpp_display"]
    short = [c == STUB_CLASS and length(chain) < STUB_FLOOR_PX * mpp for chain, _, c in chains]
    shores = [[*ring, ring[0]] for ring in lakes if len(ring) > 1]
    dropped = stubs([chain for chain, _, _ in chains], short, shores, MEET_PX * mpp)
    return [
        _river(chain, cls, name, lakes, frame, measured=name in widths)
        for i, (chain, name, cls) in enumerate(chains)
        if i not in dropped
    ]
