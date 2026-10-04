"""Placed labels and spans as marks: the settings the hand writes and the furniture beside them.

Key names: `marks`, which turns the placed labels and spans of a card into the
marks the nib plate strokes; `label_marks` and `span_marks`, one label's and one
span's; `open_hand`, which opens the style's hand; `box_size`, the hand's width
and height with the room the placer reserves around a name.

A `Label` or a `Span` is a map type and the hand knows neither. Here a label is
translated into a `Setting` (its ink from its kind, tier and intent, its slant
and tracking from its kind, the line it sits on from its window or its feature's
line) and written by `Hand.write`; then the furniture a label is entitled to, a
pin and a leader, a house, an underline, and a span's own line and ticks, is
drawn here as marks and wandered with `Hand.stroke` from the same generator, in
the order the face's glyphs left it, so the card's pixels do not move.

It places nothing: the window a placer chose stays on the label, and a name the
placer never saw is set along the best window of its feature's line only as a
fallback. It reads no style but the face and the seed, and it does not stroke
the marks into a plate.

Invariants: one generator a label and one a span, seeded from what names it (the
name and the anchor, or the name, the start index and `span`); a name set along a
line is never upside down; a span never takes a leader.
"""

import logging
import zlib
from collections.abc import Sequence

import numpy as np

from pyntpot.ink.polyline import Pt
from pyntpot.letters.hand import Hand
from pyntpot.letters.setting import DEFAULT_LINE_PX, Mark, Setting
from pyntpot.maps.lettering.label import NO_LEADER, SPAN_EFFORT, TIER_SPAN, Label, Span
from pyntpot.maps.lettering.placement_lift import _offset_line, lift_baseline
from pyntpot.maps.lettering_furniture import leader, pin, underline
from pyntpot.maps.lettering_window import baseline
from pyntpot.maps.style import Style

log = logging.getLogger(__name__)

#: Which ink a kind is written in. The ground is the map's own dark, the water
#: is the water, and the track is the route's colour. Everything else in the
#: hierarchy follows from that one rule.
KIND_INK = {"river": "water", "marker": "route"}

#: Extra letter spacing a kind is set with, in em units. Water is set wide
#: because that is how a printed map has always said "this is a river" without
#: changing the size, and a road is set slightly wide for the same reason.
KIND_TRACKING = {"river": 0.24, "road": 0.10, "settlement": 0.05}

#: How far a kind leans. Water is italic by convention.
KIND_SLANT = {"river": 0.22}

#: How far an effort span's name leans, whatever its kind.
SPAN_EFFORT_SLANT = 0.16

#: Which ink a span's intent is written in: purple for a remark, green for
#: something that went as it should, red for something that went wrong, gold
#: for a best effort. Kept darker than the pigments a watercolour would give,
#: because these are written at a 14 px cap height on a granulated cream ground
#: and a pale one does not read.
SPAN_INTENT_INK = {
    "note": "#5b3f8c",
    "good": "#2f6b3d",
    "warning": "#a3282d",
    "celebration": "#9a7212",
}

#: The user's own place, as a small house in card pixels with y down. The page
#: drew this in vector and the card drew nothing, which is the one place the two
#: outputs disagreed; it is drawn here now, once, in the map's own ink, so both
#: of them get the same pixels and both reserve the same room for it.
HOME_GLYPH = [(-7.0, 1.5), (0.0, -6.5), (7.0, 1.5), (7.0, 8.0), (-7.0, 8.0), (-7.0, 1.5)]


def open_hand(style: Style, route: str | None = None) -> Hand | None:
    """The style's hand, or None when this machine cannot open its face.

    A machine without the vendored file letters nothing rather than failing
    to draw a map.

    Args:
        style: The style whose face and hand are opened.
        route: `centreline` or `outline`; the style's when not given.
    """
    try:
        return Hand(style.face, style.hand, route)
    except OSError as exc:
        log.info("no face to letter with: %s", exc)
        return None


def box_size(hand: Hand, text: str, size: float) -> tuple[float, float]:
    """A name's width and height with the room the placer reserves: half an em more."""
    width, height = hand.measure(text, size)
    return width + size * 0.5, height


def marks(hand: Hand, placed: Sequence[Label], spans: Sequence[Span]) -> list[Mark]:
    """Everything on the label layer, as strokes in card pixels.

    Args:
        hand: The hand that writes and wanders every mark.
        placed: The placed labels, in the order they claimed their boxes.
        spans: The placed spans, whose lines and ticks are drawn too.

    Returns:
        The marks, spans first, in the order they are laid down.
    """
    out: list[Mark] = []
    for span in spans:
        out.extend(span_marks(hand, span))
    for lb in placed:
        out.extend(label_marks(hand, lb))
    return out


def span_marks(hand: Hand, span: Span) -> list[Mark]:
    """A span's own line and its two end ticks: one gesture with its name.

    The name is not drawn here. It went through the placer with every other
    name and comes back in the placed labels, which is what stops a span from
    claiming paper nothing else knows about.
    """
    out: list[Mark] = []
    ink = SPAN_INTENT_INK.get(span.intent or "note", SPAN_INTENT_INK["note"])
    size = span.label.size if span.label else DEFAULT_LINE_PX
    rng = hand.generator(_crc(span.name, span.i0, "span"))
    if span.line:
        out.append(
            Mark(
                pts=hand.stroke(span.line, rng, 0.4),
                role="span",
                ink=ink,
                size=size,
                pen=float(rng.normal(0.0, 0.06)),
            )
        )
    for tick in span.ticks:
        out.append(Mark(pts=hand.stroke(tick, rng, 0.25), role="tick", ink=ink, size=size))
    return out


def label_marks(hand: Hand, lb: Label) -> list[Mark]:
    """One name, and whatever furniture its kind is entitled to.

    `lb.lift` is which side of its own baseline a curved name sits on: above it
    for a river or a road, outboard of the route for a span.
    """
    rng = hand.generator(_crc(lb.name, round(lb.px, 1), round(lb.py, 1)))
    track = KIND_TRACKING.get(lb.kind, 0.0)
    width = max(hand.measure(line, lb.size, track)[0] for line in lb.text_lines)
    base = baseline(lb, width) if len(lb.text_lines) == 1 else None
    out = hand.write(_setting(lb, base, track), rng)
    ink = _ink(lb)
    if base is None:
        out.extend(_furniture(hand, lb, rng, ink))
    if lb.kind == "home":
        pts = hand.stroke([(lb.px + x, lb.py + y) for x, y in HOME_GLYPH], rng, 0.35)
        out.append(Mark(pts=pts, role="span", ink=ink, size=lb.size))
    if base is None and lb.kind == "settlement" and lb.size >= DEFAULT_LINE_PX:
        pts = underline(hand, lb, width, rng)
        out.append(Mark(pts=pts, role="underline", ink=ink, size=lb.size))
    return out


def _crc(*parts: object) -> int:
    """What names one instance, as the number its generator is seeded with."""
    return zlib.crc32("|".join(str(p) for p in parts).encode())


def _ink(lb: Label) -> str:
    """Which ink a label is written in: one of the three tokens, or a colour.

    A span is the one thing on the sheet whose colour is a judgement rather
    than a category, and the judgement is the payload's `intent`, resolved here
    from `SPAN_INTENT_INK`. A name on the water is written in the water's own
    ink, the colour of the thing it is now written on.
    """
    if lb.tier == TIER_SPAN:
        return SPAN_INTENT_INK.get(lb.intent or "note", SPAN_INTENT_INK["note"])
    if lb.in_water:
        return "in_water"
    return KIND_INK.get(lb.kind, "map")


def _setting(lb: Label, base: list[Pt] | None, track: float) -> Setting:
    """The label as the hand is asked to write it: along its lifted line, or flat."""
    slant = KIND_SLANT.get(lb.kind, 0.0)
    if lb.tier == TIER_SPAN and lb.kind in SPAN_EFFORT:
        slant = SPAN_EFFORT_SLANT
    ink = _ink(lb)
    wash = not lb.in_water
    if base:
        walk = tuple(_offset_line(base, lift_baseline(lb, lb.lift)))
        return Setting(lb.name, lb.size, path=walk, slant=slant, tracking=track, ink=ink, wash=wash)
    return Setting(
        lb.name,
        lb.size,
        anchor=(lb.tx, lb.ty),
        align=lb.anchor,
        slant=slant,
        tracking=track,
        ink=ink,
        lines=tuple(lb.text_lines),
        wash=wash,
    )


def _furniture(hand: Hand, lb: Label, rng: np.random.Generator, ink: str) -> list[Mark]:
    """The pin and the leader a pinned name takes; a span and a kind that is its place take none.

    A span never takes a leader. Its name sits in clear paper beside its own
    bracket, and a connector between two marks a reader can already see belong
    together is one more line on a card that has enough.
    """
    ends = lb.leader
    if not ends or lb.kind in NO_LEADER or lb.tier == TIER_SPAN:
        return []
    ring = Mark(pts=pin(hand, lb, rng), role="pin", ink=ink, size=lb.size)
    line = Mark(pts=leader(hand, ends, rng), role="leader", ink=ink, size=lb.size)
    return [ring, line]
