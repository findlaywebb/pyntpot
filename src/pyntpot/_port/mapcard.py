"""The painted route map on its own, as one PNG.

The session page draws this map as an SVG with the plates inlined and the
route, the pins and the names set in vector on top. That page is the right
answer when the map sits beside the numbers; it is the wrong answer when all
that is wanted is the picture. This module composes the same plates into a
single raster card instead, so the map can be handed straight over.

Nothing here paints and nothing here fetches: it reads
`data/geo/plates/<id>/`, which `python -m analysis.report paint` fills, and
returns None when that cache is empty. The route comes from `charts` and the
label placement from `labels`, which the page uses too, so the card and the
page put a name in the same place.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw

from pyntpot._port import labels as lb_mod
from pyntpot._port import paint
from pyntpot._port.card import STRAND_GAP_WIDTHS, separate_strands
from pyntpot._port.labels import (
    Label,
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
from pyntpot._port.style import RouteInk
from pyntpot.ink.polyline import cumulative_m

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


def _plates(manifest: dict[str, Any]) -> Image.Image:
    """The card itself: the wash multiplied over the paper, as the painter composed it."""
    root = Path(manifest["dir"])
    paper = Image.open(root / manifest["files"]["paper"]).convert("RGB")
    wash = Image.open(root / manifest["files"]["wash"]).convert("RGB")
    if wash.size != paper.size:
        wash = wash.resize(paper.size, Image.LANCZOS)
    return ImageChops.multiply(paper, wash)


def _route(
    card_img: Image.Image,
    manifest: dict[str, Any],
    route_px: list[tuple[float, float]],
    ink: Any,
    k: float,
) -> None:
    """The route, in the sport's own ink, drawn onto the card in place.

    The painter's pen plate is white carrying alpha so the page can tint it, so
    the same plate is tinted here. A style with no pen plate draws the line.
    """
    colour = _rgb(ink.colour)
    root = Path(manifest["dir"])
    name = manifest.get("files", {}).get("pen")
    if name and ink.style == "pen":
        pen = Image.open(root / name).convert("RGBA")
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


def compose(
    key: str,
    lat: list[float],
    lng: list[float],
    route_ink: RouteInk,
    pstyle: paint.PaintStyle,
    picks: Any | None,
    labels: bool,
    cache_dir: Path,
) -> Image.Image | None:
    """The painted route map for one activity, as one image.

    Args:
        key: The cache key, naming the plate cache.
        lat: Track latitudes, in recorded order.
        lng: Track longitudes, same length.
        route_ink: The route's ink for the sport.
        pstyle: The paint style the card takes.
        picks: A payload's `map` block, naming the landmarks to letter. Without
            one the nearest named features are lettered instead.
        labels: Letter the card at all. False leaves the route on the painting.
        cache_dir: Where the plates are cached.

    Returns:
        The card, or None when nothing is painted for this activity.
    """
    from pyntpot.maps.card import Card
    from pyntpot.maps.projection import track_projection

    manifest = paint.load_plates(key, cache_dir)
    if manifest is None:
        return None
    card_img = _plates(manifest)
    k = card_img.width / max(manifest["display"][0], 1)

    _proj, pts = track_projection(lat, lng)
    first = manifest.get("route0") or pts[0]
    card = Card.from_manifest(manifest, offset=(first[0] - pts[0][0], first[1] - pts[0][1]))
    ink = route_ink
    route_px = separate_strands([card.xy(x, y) for x, y in pts], ink.px * STRAND_GAP_WIDTHS)

    _route(card_img, manifest, route_px, ink, k)
    if not labels:
        return card_img

    hand = lb_mod.hand(pstyle)
    home, taken = home_labels(manifest, card, pstyle, hand.measure if hand else None)
    ground = (
        ground_labels(manifest, card, route_px, picks)
        + pick_roads(manifest, card, route_px)
        + route_markers(route_px)
        if pstyle.label_ground
        else []
    )
    wanted = journal_picks(picks, manifest, pstyle.label_max) if picks else []
    if not wanted:
        wanted = journal_heuristic(manifest, pstyle.label_max)
    anchored = []
    for lb in wanted:
        if "x" in lb:
            x, y = card.xy(lb["x"], lb["y"])
        else:
            x, y = card.xy(*_proj(lb["lat"], lb["lng"]))
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
        manifest["dark"],
        taken,
        hand.measure if hand else None,
        road_lines(manifest, card),
    )
    plate = draw_plate(manifest, placed, spans, route_px, pstyle) if hand else None
    if plate is None:
        log.info("no label plate for %s, the card is handed over bare", key)
        return card_img
    _paste_labels(card_img, plate)
    return card_img


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
