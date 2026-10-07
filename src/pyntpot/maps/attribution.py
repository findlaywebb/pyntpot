"""The data attribution a composed map carries: the text, and the hand that writes it.

Key names: `attribution_text`, which joins the short line of each `Credit` into the
one line drawn on the map; `draw_attribution`, which writes that line in the
style's hand at the bottom right of a card; `ATTRIBUTION_SIZE_PX` and
`ATTRIBUTION_MARGIN_PX`, the pinned type size and distance from the card's edges.

The line is stroked through the same hand, nib and ink engine as the map's names,
on a plate the size of the text block, and pasted with its alpha. It does not
choose the credits (the basemap carries them), it does not wrap a line wider than
the card, and it draws nothing, logging why, when there is no hand to write with
or the hand strokes nothing.

Invariants: the text keeps the credits' order; only the block's pixels change;
the same text and style write the same pixels.
"""

import logging
import math
import tempfile
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from pyntpot.ink.sheet import Canvas
from pyntpot.letters import nib
from pyntpot.maps import lettering_marks
from pyntpot.maps.credit import Credit
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.plates import dark_array
from pyntpot.maps.style import Style

log = logging.getLogger(__name__)

#: The type size of the attribution line, in card pixels.
ATTRIBUTION_SIZE_PX = 11.0

#: How far the attribution block sits from the card's bottom and right edges.
ATTRIBUTION_MARGIN_PX = 8.0

#: Room inside the block around the text, so no stroke is clipped by the plate.
_PAD_PX = 4.0

#: The paper's granulation cell on the attribution plate, in pixels.
_GRAN_PX = 6.0


def attribution_text(owed: Sequence[Credit]) -> str:
    """Join the credits' short lines, in the order given, into the line drawn on the map."""
    return " · ".join(credit.short for credit in owed)


def draw_attribution(image: Image.Image, text: str, style: Style) -> None:
    """Write the attribution at the bottom right of a card, in place.

    Args:
        image: The card; its pixels under the text block change, no others.
        text: The line to write; nothing is drawn for an empty line.
        style: The style whose hand, nib and ink write it.
    """
    if not text:
        return
    hand = lettering_marks.open_hand(style)
    if hand is None:
        log.info("no hand to write the attribution with, none is drawn")
        return
    size = ATTRIBUTION_SIZE_PX
    width, height = lettering_marks.box_size(hand, text, size)
    base = _PAD_PX + size
    block = (
        math.ceil(width + 2 * _PAD_PX),
        math.ceil(base + (height - size) + size * 0.5 + _PAD_PX),
    )
    marks = lettering_marks.label_marks(
        hand,
        Label(name=text, kind="landmark", px=_PAD_PX, py=base, tx=_PAD_PX, ty=base, size=size),
    )
    with tempfile.TemporaryDirectory() as work:
        surface = nib.NibSurface(
            Canvas(0.0, 0.0, float(block[0]), float(block[1]), block[0], block[1]),
            1.0,
            dark_array(None, block[1], block[0]),
            _GRAN_PX,
        )
        groups = nib.NibGroups(style.nib, style.face, style.hand, style.brush, style.paper)
        path = nib.plate(marks, surface, groups, Path(work) / "attribution.webp")
        if path is None:
            log.info("the attribution drew nothing")
            return
        plate = Image.open(path).convert("RGBA")
        plate.load()
    left = round(image.width - ATTRIBUTION_MARGIN_PX - plate.width)
    top = round(image.height - ATTRIBUTION_MARGIN_PX - plate.height)
    image.paste(plate, (left, top), plate.getchannel("A"))
