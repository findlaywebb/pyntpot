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
basemap without times does not land and is left out. Without annotations the
nearest named features are lettered instead of the caller's landmarks.

It does not paint the base plates and it does not compose the card. It reads
no configuration from the environment. When there is no hand to letter with
(the style turns lettering off, or the face cannot be opened) it places
nothing and writes no plate.

Invariants: every name is measured with the hand, never with a flat
per-character width; `Lettering.labels` is in placement order, the user's own
places first; `plate_path` is `None` exactly when nothing was stroked, and
otherwise names a file inside `Plates.directory`.
"""

import logging
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from pyntpot._port import labels as placer
from pyntpot._port import paint as painter
from pyntpot.ink.polyline import Pt, cumulative_length
from pyntpot.maps import lettering_marks
from pyntpot.maps.annotations import Annotations
from pyntpot.maps.basemap import Basemap
from pyntpot.maps.plates import Plates
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

    labels: tuple[placer.Label, ...]
    spans: tuple[placer.Span, ...]
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
            `None` to letter the nearest named features.
        style: The style the card is lettered in.

    Returns:
        The placed labels and spans and the label plate; empty, with no plate,
        when there is no hand to letter with.
    """
    pstyle = style.paint_style()
    hand = lettering_marks.open_hand(style) if style.lettering.labels else None
    if hand is None:
        log.info("no hand to letter %s with, nothing is lettered", plates.directory)
        return Lettering((), (), None)
    measure = partial(lettering_marks.box_size, hand)
    card = basemap.card
    strands = list(plates.strands)
    lines = placer.named_lines(basemap, pstyle.label_geom_tol_px)
    home, taken = placer.home_labels(basemap, card, pstyle, measure)
    ground = _ground(basemap, lines, strands, annotations, pstyle)
    anchored = _anchored(basemap, annotations, pstyle)
    spans = _spans(plates, basemap, annotations, strands)
    dark = plates.manifest.dark
    placed = home + placer.place(
        ground + anchored,
        spans,
        card,
        strands,
        {"w": dark.w, "h": dark.h, "v": dark.values},
        taken,
        measure,
        placer.road_lines(lines, card),
    )
    plate = placer.draw_plate(plates, placed, spans, strands, pstyle, style.brush)
    return Lettering(tuple(placed), tuple(spans), plate)


def _ground(
    basemap: Basemap,
    lines: placer.NamedLines,
    strands: list[Pt],
    annotations: Annotations | None,
    pstyle: painter.PaintStyle,
) -> list[placer.Label]:
    """The settlements, rivers, road numbers and route markers, when the style letters the ground."""
    if not pstyle.label_ground:
        return []
    card = basemap.card
    return (
        placer.ground_labels(basemap, lines, card, strands, annotations)
        + placer.pick_roads(basemap, lines, card, strands)
        + placer.route_markers(strands)
    )


def _anchored(
    basemap: Basemap, annotations: Annotations | None, pstyle: painter.PaintStyle
) -> list[placer.Label]:
    """The landmarks to letter, the caller's or the nearest named, anchored on the card."""
    cap = pstyle.label_max
    wanted = placer.journal_picks(annotations, basemap, cap) if annotations is not None else []
    if not wanted:
        wanted = placer.journal_heuristic(basemap, cap)
    card = basemap.card
    anchored: list[placer.Label] = []
    for entry in wanted:
        if "x" in entry:
            x, y = card.xy(entry["x"], entry["y"])
        else:
            x, y = card.xy(*basemap.projection(entry["lat"], entry["lng"]))
        if 0 < x < card.w and 0 < y < card.h:
            anchored.append(
                placer.Label(
                    name=entry["name"],
                    kind=entry.get("kind", ""),
                    why=entry.get("why", ""),
                    px=x,
                    py=y,
                    size=pstyle.label_size_px,
                )
            )
    return anchored


def _spans(
    plates: Plates, basemap: Basemap, annotations: Annotations | None, strands: list[Pt]
) -> list[placer.Span]:
    """The caller's span requests resolved onto the strands' arc length and the track's times."""
    times = list(basemap.track_time) if basemap.track_time is not None else []
    return placer.resolve_spans(annotations, times, cumulative_length(strands, plates.card.scale))
