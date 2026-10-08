"""The map's third stage: letter painted plates with names and spans.

Key names: `letter`, which picks what a map names, anchors it on the card,
resolves the caller's span requests onto the route, places every name and span
measured by the hand, and strokes them into a label plate beside the plates;
`Lettering`, what it hands back: the placed labels, the placed spans and the
label plate's path.

Everything route-shaped that `letter` reads is `Plates.strands`, the route as
it is drawn: the ground names, the road numbers and the route markers are
picked against it, the names are placed clear of it, the plate is stroked
beside it, and a span is resolved on its arc length. A span request resolves
by point index, by kilometre along the strands, and by seconds from the start
when the basemap carries the track's times; one stated in seconds over a
basemap without times does not land and is left out. When there are no
annotations, or none of their landmarks lands, the basemap's leading
candidates are lettered instead.

It does not paint the base plates and it does not compose the card. It reads
no configuration from the environment. When there is no hand to letter with
(the style turns lettering off, or the face cannot be opened) it places
nothing and writes no plate.

Invariants: every name is measured with the hand, never with a flat
per-character width; `Lettering.labels` is in placement order, the user's own
places first; `plate_path` is `None` exactly when nothing was stroked, and
otherwise names a file inside `Plates.directory`.
"""

import json
import logging
from dataclasses import dataclass, replace
from functools import partial
from pathlib import Path

from pyntpot.ink.polyline import Pt, cumulative_length
from pyntpot.ink.sheet import Canvas
from pyntpot.letters import nib
from pyntpot.letters.style import NibGroups
from pyntpot.maps import lettering_marks
from pyntpot.maps.annotations import Annotations
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.cache import Cache
from pyntpot.maps.lettering.label import Label, Span
from pyntpot.maps.lettering.picks import (
    ground_labels,
    home_labels,
    journal_heuristic,
    journal_picks,
    route_markers,
)
from pyntpot.maps.lettering.picks_lines import NamedLines, named_lines, road_lines
from pyntpot.maps.lettering.picks_roads import pick_roads
from pyntpot.maps.lettering.placement import place
from pyntpot.maps.lettering.placement_costs import Backdrop
from pyntpot.maps.lettering.spans import resolve_spans
from pyntpot.maps.plates import Plates, dark_array
from pyntpot.maps.style import Style

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Lettering:
    """What a map is lettered with, and the plate it was stroked into.

    Attributes:
        labels: The placed labels, in placement order.
        spans: The placed spans, each resolved from a span request onto the
            route.
        plate_path: The label plate, or `None` when nothing was stroked.
    """

    labels: tuple[Label, ...]
    spans: tuple[Span, ...]
    plate_path: Path | None


def letter(
    plates: Plates, basemap: Basemap, annotations: Annotations | None, style: Style
) -> Lettering:
    """Place a map's names and spans and stroke them into a label plate.

    Args:
        plates: The painted plates: their strands are the route lettered
            against, their darkness keeps names on light ground, and the label
            plate is written beside them.
        basemap: The basemap the plates were painted from, for the places, the
            candidates, the named lines, the projection and the track's times.
        annotations: The caller's landmarks, places and span requests, or
            `None` to letter the basemap's leading candidates.
        style: The style the card is lettered in.

    Returns:
        The placed labels and spans and the label plate; empty, with no plate,
        when there is no hand to letter with.
    """
    hand = lettering_marks.open_hand(style) if style.lettering.labels else None
    if hand is None:
        log.info("no hand to letter %s with, nothing is lettered", plates.directory)
        return Lettering((), (), None)
    measure = partial(lettering_marks.box_size, hand)
    card = basemap.card
    strands = list(plates.strands)
    lines = named_lines(basemap, style.lettering.label_geom_tol_px)
    home, taken = home_labels(basemap, card, style, measure)
    ground = _ground(basemap, lines, strands, annotations, style)
    anchored = _anchored(basemap, annotations, style)
    spans = _spans(plates, basemap, annotations, strands)
    dark = plates.manifest.dark
    backdrop = Backdrop(
        card,
        strands,
        {"w": dark.w, "h": dark.h, "v": dark.values},
        road_lines(lines, card),
    )
    placed = home + place(ground + anchored, spans, backdrop, taken, measure)
    plate = draw_plate(plates, placed, spans, strands, style)
    return Lettering(tuple(placed), tuple(spans), plate)


def _ground(
    basemap: Basemap,
    lines: NamedLines,
    strands: list[Pt],
    annotations: Annotations | None,
    style: Style,
) -> list[Label]:
    """The settlements, rivers, road numbers and route markers, when the style letters the ground."""
    if not style.lettering.label_ground:
        return []
    card = basemap.card
    return (
        ground_labels(basemap, lines, card, strands, annotations)
        + pick_roads(basemap, lines, card, strands)
        + route_markers(strands)
    )


def _anchored(basemap: Basemap, annotations: Annotations | None, style: Style) -> list[Label]:
    """The landmarks to letter, the caller's or the leading candidates, anchored on the card."""
    cap = style.lettering.label_max
    wanted = journal_picks(annotations, basemap, cap) if annotations is not None else []
    if not wanted:
        wanted = journal_heuristic(basemap, cap)
    card = basemap.card
    anchored: list[Label] = []
    for entry in wanted:
        if "x" in entry:
            x, y = card.xy(entry["x"], entry["y"])
        else:
            x, y = card.xy(*basemap.projection(entry["lat"], entry["lng"]))
        if 0 < x < card.w and 0 < y < card.h:
            anchored.append(
                Label(
                    name=entry["name"],
                    kind=entry.get("kind", ""),
                    why=entry.get("why", ""),
                    px=x,
                    py=y,
                    size=style.nib.label_size_px,
                )
            )
    return anchored


def _spans(
    plates: Plates, basemap: Basemap, annotations: Annotations | None, strands: list[Pt]
) -> list[Span]:
    """The caller's span requests resolved onto the strands' arc length and the track's times."""
    times = list(basemap.track_time) if basemap.track_time is not None else []
    return resolve_spans(annotations, times, cumulative_length(strands, plates.card.scale))


def draw_plate(
    plates: Plates,
    placed: list[Label],
    spans: list[Span],
    route_px: list[Pt],
    style: Style,
    route: str | None = None,
) -> Path | None:
    """Stroke the placed names and spans into an RGBA plate beside the plates.

    The lettering is raster because the ink is: `stamp` deposits into a numpy
    accumulator gated on the paper's own height, and there is no path out of
    that to vector. So the label layer is a fourth plate, and the page and the
    card both draw the same pixels instead of each approximating them.

    It is cached on `Cache.lettering_key`, kept in a JSON sidecar beside the
    plate: the marks to be stroked, the base plates' hash and the style's
    lettering digest, so a moved name, pin, leader or span line, a repaint of
    the base plates or another hand all change it. A plate on disk whose key
    does not match is stroked again, never reused, so yesterday's names are
    never lettered over today's map.

    Args:
        plates: The painted plates, beside which the label plate is written.
        placed: The placed labels.
        spans: The placed spans.
        route_px: The track in display pixels.
        style: The style the card is lettered in; its brush style makes the
            lettering's brushes and ink pads.
        route: `centreline` or `outline`; the style's when not given.

    Returns:
        The path to the plate, or None when there is nothing to draw or no
        hand to draw it with.
    """
    if not placed and not spans:
        return None
    hand = lettering_marks.open_hand(style, route)
    if hand is None:
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
    face = replace(style.face, label_route=hand.route)
    written = nib.plate(
        marks, surface, NibGroups(style.nib, face, style.hand, style.brush, style.paper), path
    )
    if written is not None:
        side.write_text(json.dumps({"key": key, "face": hand.font.name, "route": hand.route}))
    return written
