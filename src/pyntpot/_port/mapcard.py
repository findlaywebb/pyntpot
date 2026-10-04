"""The painted route map on its own, as one PNG.

The session page draws this map as an SVG with the plates inlined and the
route, the pins and the names set in vector on top. That page is the right
answer when the map sits beside the numbers; it is the wrong answer when all
that is wanted is the picture. This module composes the same plates into a
single raster card instead, so the map can be handed straight over.

Nothing here paints and nothing here fetches: it takes the basemap and the
plates the painter made from it. The route is the basemap's own track, and the
label placement comes from `labels`, which the page uses too, so the card and
the page put a name in the same place. The places, candidates and named lines a
label is set by are read from the basemap, never from the plates' manifest.
"""

from __future__ import annotations

import logging
import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageChops, ImageDraw

from pyntpot._port import labels as lb_mod
from pyntpot._port import paint
from pyntpot._port.card import STRAND_GAP_WIDTHS, separate_strands
from pyntpot._port.labels import (
    Label,
    Span,
    draw_plate,
    ground_labels,
    home_labels,
    journal_heuristic,
    journal_picks,
    pick_roads,
    place,
    resolve_spans,
    road_lines,
    route_markers,
)
from pyntpot.ink.polyline import cumulative_m

if TYPE_CHECKING:
    from pyntpot.maps.basemap import Basemap
    from pyntpot.maps.card import Card
    from pyntpot.maps.plates import Plates
    from pyntpot.maps.style import Style

log = logging.getLogger(__name__)

#: What the route is drawn at, in card pixels per card pixel, before it is
#: reduced back. 4 is where a diagonal stops showing its steps at the
#: magnification the card is read at; higher costs the square of it
#: in memory for a mark that is already smooth.
ROUTE_SS = 4


def sport_from_gpx(path: Path, default: str = "Ride") -> str:
    """The sport recorded in the track's GPX type, so the ink matches it."""
    found = re.search(r"<type>([^<]+)</type>", path.read_text()[:4000])
    return found.group(1).strip() if found else default


def _rgb(colour: str) -> tuple[int, int, int]:
    """One `#rrggbb` string as a tuple."""
    s = colour.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def _plates(plates: Plates) -> Image.Image:
    """The card itself: the wash multiplied over the paper, as the painter composed it."""
    paths = plates.paths
    paper = Image.open(paths["paper"]).convert("RGB")
    wash = Image.open(paths["wash"]).convert("RGB")
    if wash.size != paper.size:
        wash = wash.resize(paper.size, Image.LANCZOS)
    return ImageChops.multiply(paper, wash)


def _route(
    card_img: Image.Image,
    plates: Plates,
    route_px: list[tuple[float, float]],
    ink: Any,
    k: float,
) -> None:
    """The route, in the sport's own ink, drawn onto the card in place.

    The painter's pen plate is white carrying alpha so the page can tint it, so
    the same plate is tinted here. A style with no pen plate draws the line.
    """
    colour = _rgb(ink.colour)
    name = plates.manifest.files.get("pen")
    if name and ink.style == "pen":
        pen = Image.open(plates.directory / name).convert("RGBA")
        if pen.size != card_img.size:
            pen = pen.resize(card_img.size, Image.LANCZOS)
        card_img.paste(Image.new("RGB", card_img.size, colour), (0, 0), pen.getchannel("A"))
        return
    # Drawn on a grid `ROUTE_SS` times finer and reduced back, because Pillow's
    # line is hard: at one pixel per pixel a route that runs at any angle but
    # the two right ones comes back as a staircase, and the staircase is the
    # coarsest mark on a card whose every other stroke is painted.
    ss = ROUTE_SS
    big = Image.new("L", (card_img.width * ss, card_img.height * ss), 0)
    ImageDraw.Draw(big).line(
        [(x * k * ss, y * k * ss) for x, y in route_px],
        fill=255,
        width=max(int(round(ink.px * k * ss)), 1),
        joint="curve",
    )
    mask = big.resize(card_img.size, Image.LANCZOS)
    card_img.paste(Image.new("RGB", card_img.size, colour), (0, 0), mask)


def _paste_labels(card_img: Image.Image, plate: Path) -> None:
    """The label plate, over the painting, at the card's own size.

    The card and the page now draw the same pixels, because they are the same
    pixels: one RGBA plate, stroked through the ink engine, embedded by the
    page and pasted here. What this replaces is a serif face with a hard cream
    halo, shrunk until it fitted boxes that had been sized for a cursive.
    """
    ink = Image.open(plate).convert("RGBA")
    if ink.size != card_img.size:
        ink = ink.resize(card_img.size, Image.LANCZOS)
    card_img.paste(ink, (0, 0), ink.getchannel("A"))


def pinned_card(basemap: Basemap) -> Card:
    """The basemap's card, offset so its track's first point lands on the painter's route."""
    first, start = basemap.layers.route[0], basemap.track[0]
    return replace(basemap.card, offset=(first[0] - start[0], first[1] - start[1]))


def route_pixels(basemap: Basemap, style: Style) -> list[tuple[float, float]]:
    """The drawn route in display pixels: the basemap's track, its strands pulled apart.

    The track is placed through the pinned card, then separated where it runs
    back over itself by the gap the route ink leaves between strands.
    """
    card = pinned_card(basemap)
    ink = style.route_ink()
    return separate_strands([card.xy(x, y) for x, y in basemap.track], ink.px * STRAND_GAP_WIDTHS)


def letter_card(
    basemap: Basemap, plates: Plates, style: Style, picks: Any | None
) -> tuple[list[Label], list[Span], Path | None]:
    """Place the card's names and spans and stroke them into a label plate.

    Args:
        basemap: The basemap the plates were painted from, for the places, the
            candidates, the named lines and the projection.
        plates: The painted plates, beside which the label plate is written.
        style: The style: its flat painter style letters the card.
        picks: A payload's `map` block, naming the landmarks to letter. Without
            one the nearest named features are lettered instead.

    Returns:
        The placed labels in placement order, the placed spans, and the label
        plate, or None when there is no hand or nothing to draw.
    """
    pstyle = style.paint_style()
    manifest = plates.manifest
    card = pinned_card(basemap)
    route_px = route_pixels(basemap, style)
    lines = lb_mod.named_lines(basemap, pstyle.label_geom_tol_px)

    hand = lb_mod.hand(pstyle)
    home, taken = home_labels(basemap, card, pstyle, hand.measure if hand else None)
    ground = (
        ground_labels(basemap, lines, card, route_px, picks)
        + pick_roads(basemap, lines, card, route_px)
        + route_markers(route_px)
        if pstyle.label_ground
        else []
    )
    wanted = journal_picks(picks, basemap, pstyle.label_max) if picks else []
    if not wanted:
        wanted = journal_heuristic(basemap, pstyle.label_max)
    anchored = []
    for lb in wanted:
        if "x" in lb:
            x, y = card.xy(lb["x"], lb["y"])
        else:
            x, y = card.xy(*basemap.projection(lb["lat"], lb["lng"]))
        if 0 < x < card.w and 0 < y < card.h:
            anchored.append(
                Label(
                    name=lb["name"],
                    kind=lb.get("kind", ""),
                    why=lb.get("why", ""),
                    px=x,
                    py=y,
                    size=pstyle.label_size_px,
                )
            )
    # A bare track carries no clock, so a span stated in seconds cannot be
    # resolved here and says so; one stated in kilometres or in indices can.
    spans = resolve_spans(picks, [], cumulative_m(route_px, card.scale))
    placed = home + place(
        ground + anchored,
        spans,
        card,
        route_px,
        {"w": manifest.dark.w, "h": manifest.dark.h, "v": manifest.dark.values},
        taken,
        hand.measure if hand else None,
        road_lines(lines, card),
    )
    plate = draw_plate(plates, placed, spans, route_px, pstyle) if hand else None
    return placed, spans, plate


def compose(
    basemap: Basemap, plates: Plates, style: Style, picks: Any | None, labels: bool
) -> tuple[Image.Image, list[Label]]:
    """The painted route map for one activity, as one image.

    Args:
        basemap: The basemap the plates were painted from.
        plates: The painted plates.
        style: The style: the route is drawn in its route ink and the card is
            lettered with its flat painter style.
        picks: A payload's `map` block, naming the landmarks to letter. Without
            one the nearest named features are lettered instead.
        labels: Letter the card at all. False leaves the route on the painting.

    Returns:
        The card, and the labels placed on it in placement order (none when
        `labels` is false).
    """
    card_img = _plates(plates)
    k = card_img.width / max(plates.card.display[0], 1)
    ink = style.route_ink()
    _route(card_img, plates, route_pixels(basemap, style), ink, k)
    if not labels:
        return card_img, []
    placed, _spans, plate = letter_card(basemap, plates, style, picks)
    if plate is None:
        log.info("no label plate in %s, the card is handed over bare", plates.directory)
        return card_img, placed
    _paste_labels(card_img, plate)
    return card_img, placed


#: What the alphabet sheet writes: the whole character set a place name can use,
#: then the actual strings this map draws. A letterform fault is invisible in a
#: table of glyph counts and obvious on a sheet, and the strings are there
#: because a letter is read in a word and not on its own.
ALPHABET_LINES = (
    "ABCDEFGHIJKLM",
    "NOPQRSTUVWXYZ",
    "abcdefghijklm",
    "nopqrstuvwxyz",
    "0123456789 - ' .",
    "Lynmouth  Lynmouth Bridge",
    "Watersmeet  Hollerday  Lyn",
    "A39 A399 A361 B3223",
    "the long climb out of Barbrook",
    "Cwm fjord bank glyphs vext quiz",
)

#: The sheet's own geometry in display pixels: how wide it is, how far apart the
#: lines sit, and how much paper is left round them.
ALPHABET_W = 900
ALPHABET_LEAD = 34.0
ALPHABET_MARGIN = 26.0


def alphabet_sheet(
    out: Path, pstyle: paint.PaintStyle, lines: tuple[str, ...] = ALPHABET_LINES
) -> Path:
    """Every glyph the map letters, at the size the map letters it, as a PNG.

    Written through the same hand, the same nib and the same ink engine as the
    card, so what is on the sheet is what is on the map. It exists to be looked
    at: the topology tests say an M has the parts an M should have, and this
    says whether it reads as one.

    Args:
        out: Where to write the PNG.
        pstyle: The paint style the letters take.
        lines: The lines to write.

    Returns:
        The file written.
    """
    from PIL import Image

    hand = lb_mod.hand(pstyle)
    if hand is None:
        raise RuntimeError("no hand: the face could not be opened")
    marks: list[Any] = []
    y = ALPHABET_MARGIN + pstyle.label_size_px
    for text in lines:
        marks.extend(
            hand._label_marks(
                Label(
                    name=text,
                    kind="landmark",
                    px=ALPHABET_MARGIN,
                    py=y,
                    tx=ALPHABET_MARGIN,
                    ty=y,
                    size=pstyle.label_size_px,
                    anchor="start",
                    leader=None,
                )
            )
        )
        y += ALPHABET_LEAD
    height = int(y + ALPHABET_MARGIN)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    plate = out.with_suffix(".plate.webp")
    manifest = {
        "render": [ALPHABET_W * 2, height * 2],
        "display": [ALPHABET_W, height],
        "gran_px": 6.0,
        "dir": str(out.parent),
    }
    if paint.label_plate(manifest, marks, pstyle, plate) is None:
        raise RuntimeError("the alphabet sheet drew nothing")
    ink = Image.open(plate).convert("RGBA")
    sheet = Image.new("RGBA", ink.size, (*_rgb(pstyle.paper_hex), 255))
    sheet.alpha_composite(ink)
    sheet.convert("RGB").save(out, format="PNG")
    plate.unlink()
    return out
