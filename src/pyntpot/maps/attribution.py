"""The data attribution a composed map carries: the text, and the hand that writes it.

Key names: `attribution_text`, which joins the short line of each `Credit` into the
one line drawn on the map; `draw_attribution`, which writes that line in the
style's hand at the bottom right of a card; `attribution_size`, the type size for a
card width; `ATTRIBUTION_SIZE_PX`, `ATTRIBUTION_REFERENCE_PX`, `ATTRIBUTION_MIN_SIZE_PX`
and `ATTRIBUTION_MARGIN_PX`, the pinned sizes, all in display pixels.

The credit is a licence obligation, so it is sized to be read where the card is
published: the type is `ATTRIBUTION_SIZE_PX` on a card `ATTRIBUTION_REFERENCE_PX`
wide, grows with the card's display width and is never under
`ATTRIBUTION_MIN_SIZE_PX`; the caller gives the render scale (render pixels per
display pixel) so the size and the margin survive the downsizing of a supersampled
card. The line is stroked through the same hand, nib and ink engine as the map's
names, on a plate the size of the text block, stroked at no less than two render pixels
per display pixel (`plate_scale`) and shrunk with Lanczos, and pasted with its alpha. A line wider than
`ATTRIBUTION_WIDE_FRACTION` of the card is broken into two right-aligned lines at the
" · " that joins the credits (the dot is the break); it is never shrunk under the
floor. It does not choose the credits (the basemap carries them), it does not break a
line that has no separator, and it draws nothing, logging why, when there is no hand
to write with or the hand strokes nothing.

Invariants: the text keeps the credits' order; only the block's pixels change; the same
text and style write the same pixels.
"""

import logging
import math
import tempfile
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from pyntpot.ink.sheet import Canvas
from pyntpot.letters import nib
from pyntpot.letters.hand import Hand
from pyntpot.maps import lettering_marks
from pyntpot.maps.credit import Credit
from pyntpot.maps.lettering.label import Label
from pyntpot.maps.plates import dark_array
from pyntpot.maps.style import Style

log = logging.getLogger(__name__)

#: The type size of the attribution line on a card `ATTRIBUTION_REFERENCE_PX` wide, in
#: display pixels. 13 puts the x-height near 6 px on the 720 px published card, which
#: reads at 100 percent; the 11 px it replaces landed near 5 after the supersample
#: was shrunk away.
ATTRIBUTION_SIZE_PX = 13.0

#: The display width the size is pinned at; wider cards scale it up in proportion.
ATTRIBUTION_REFERENCE_PX = 720.0

#: The smallest type size, in display pixels, whatever the card's width.
ATTRIBUTION_MIN_SIZE_PX = 12.0

#: How far the attribution block sits from the card's bottom and right edges, in display pixels.
ATTRIBUTION_MARGIN_PX = 10.0

#: The widest share of the card a line may take before it is broken at the separator.
ATTRIBUTION_WIDE_FRACTION = 0.7

#: The credits' separator, where a wide line breaks.
SEPARATOR = " · "

#: The line spacing, in type sizes.
_LEAD = 1.3

#: Room inside the block around the text, in display pixels, so no stroke is clipped.
_PAD_PX = 4.0

#: The paper's granulation cell on the attribution plate, in display pixels.
_GRAN_PX = 6.0

#: Render pixels per display pixel the plate is stroked at, at least: a card already
#: painted at this scale or finer needs no extra supersampling of its own.
_CRISP_SCALE = 2.0


def plate_scale(scale: float) -> int:
    """The factor the plate is stroked at and shrunk from, for a card at `scale` render px per display px."""
    return max(1, math.ceil(_CRISP_SCALE / scale))


def attribution_size(display_width: float) -> float:
    """The type size, in display pixels, for a card of this display width."""
    return max(
        ATTRIBUTION_MIN_SIZE_PX, ATTRIBUTION_SIZE_PX * display_width / ATTRIBUTION_REFERENCE_PX
    )


def attribution_text(owed: Sequence[Credit]) -> str:
    """Join the credits' short lines, in the order given, into the line drawn on the map."""
    return " · ".join(credit.short for credit in owed)


def _lines(hand: Hand, text: str, size: float, limit: float) -> list[str]:
    """The text as one line, or two broken at the separator nearest its middle when wider than `limit`."""
    if lettering_marks.box_size(hand, text, size)[0] <= limit or SEPARATOR not in text:
        return [text]
    parts = text.split(SEPARATOR)
    half = len(text) / 2
    best = min(
        range(1, len(parts)),
        key=lambda i: abs(len(SEPARATOR.join(parts[:i])) - half),
    )
    return [SEPARATOR.join(parts[:best]), SEPARATOR.join(parts[best:])]


def draw_attribution(image: Image.Image, text: str, style: Style, scale: float = 1.0) -> None:
    """Write the attribution at the bottom right of a card, in place.

    Args:
        image: The card; its pixels under the text block change, no others.
        text: The line to write; nothing is drawn for an empty line.
        style: The style whose hand, nib and ink write it.
        scale: Render pixels per display pixel of the card; the type size and margin are
            in display pixels and are multiplied by it.
    """
    if not text:
        return
    hand = lettering_marks.open_hand(style)
    if hand is None:
        log.info("no hand to write the attribution with, none is drawn")
        return
    size = attribution_size(image.width / scale) * scale
    pad = _PAD_PX * scale
    lines = _lines(hand, text, size, image.width * ATTRIBUTION_WIDE_FRACTION - 2 * pad)
    sizes = [lettering_marks.box_size(hand, line, size) for line in lines]
    width = max(w for w, _h in sizes)
    lead = size * _LEAD
    block = (
        math.ceil(width + 2 * pad),
        math.ceil(pad + size + lead * (len(lines) - 1) + size * 0.5 + pad),
    )
    marks = []
    for i, (line, (line_w, _h)) in enumerate(zip(lines, sizes, strict=True)):
        x = pad + width - line_w
        y = pad + size + lead * i
        marks += lettering_marks.label_marks(
            hand, Label(name=line, kind="landmark", px=x, py=y, tx=x, ty=y, size=size)
        )
    factor = plate_scale(scale)
    big = (block[0] * factor, block[1] * factor)
    with tempfile.TemporaryDirectory() as work:
        surface = nib.NibSurface(
            Canvas(0.0, 0.0, float(big[0]), float(big[1]), big[0], big[1]),
            float(factor),
            dark_array(None, big[1], big[0]),
            _GRAN_PX * scale * factor,
        )
        groups = nib.NibGroups(style.nib, style.face, style.hand, style.brush, style.paper)
        path = nib.nib_plate(marks, surface, groups, Path(work) / "attribution.webp")
        if path is None:
            log.info("the attribution drew nothing")
            return
        with Image.open(path) as opened:
            plate = opened.convert("RGBa").resize(block, Image.Resampling.LANCZOS).convert("RGBA")
    margin = ATTRIBUTION_MARGIN_PX * scale
    left = round(image.width - margin - plate.width)
    top = round(image.height - margin - plate.height)
    image.paste(plate, (left, top), plate.getchannel("A"))
