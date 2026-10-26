"""The raster card's drawing steps: the painted map, the route and the label plate.

The page draws the map as an SVG with the plates inlined and the route, the
pins and the names set in vector on top. These are the steps that lay the same
plates into a single raster card instead, so the picture can be handed over
alone: `painted_map` multiplies the wash over the paper, `route` draws the route on it in
the route ink, and `paste_labels` pastes the label plate over both. The
compose stage calls them in that order.

Nothing here paints, fetches, letters or places a name: it takes plates the
painter made, a route already in display pixels and a label plate already
stroked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PIL import Image, ImageChops, ImageDraw

if TYPE_CHECKING:
    from pathlib import Path

    from pyntpot.maps.plates import Plates
    from pyntpot.maps.style_groups import RouteInk

#: How many times finer than the card the route is drawn, before it is
#: reduced back. 4 is where a diagonal stops showing its steps at the
#: magnification the card is read at; higher costs the square of it
#: in memory for a mark that is already smooth.
ROUTE_SS = 4
#: The blends a route ink's effect may name.
ROUTE_BLENDS = ("normal", "multiply")


def _rgb(colour: str) -> tuple[int, int, int]:
    """One `#rrggbb` string as a tuple."""
    s = colour.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def painted_map(plates: Plates) -> Image.Image:
    """The card itself: the wash multiplied over the paper, as the painter composed it.

    Source: `multiply-compositing` in docs/explanation/references.md.
    Source: `lanczos` in docs/explanation/references.md.
    """
    paths = plates.paths
    paper = Image.open(paths["paper"]).convert("RGB")
    wash = Image.open(paths["wash"]).convert("RGB")
    if wash.size != paper.size:
        wash = wash.resize(paper.size, Image.Resampling.LANCZOS)
    return ImageChops.multiply(paper, wash)


def route(
    card_img: Image.Image,
    plates: Plates,
    route_px: list[tuple[float, float]],
    ink: RouteInk,
    k: float,
) -> None:
    """The route, in the route ink, drawn onto the card in place.

    The painter's pen plate is white carrying alpha so the page can tint it, so
    the same plate is tinted here. A style with no pen plate draws the line. The ink's
    effect keys `blend` (`"normal"` or `"multiply"`) and `opacity` (0 to 1, default 1.0)
    shape both; its other effect keys are not read.

    Source: `lanczos` in docs/explanation/references.md.
    """
    colour = _rgb(ink.colour)
    name = plates.manifest.files.get("pen")
    if name and ink.style == "pen":
        pen = Image.open(plates.directory / name).convert("RGBA")
        if pen.size != card_img.size:
            pen = pen.resize(card_img.size, Image.Resampling.LANCZOS)
        _lay(card_img, colour, pen.getchannel("A"), ink.effect)
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
        width=max(round(ink.px * k * ss), 1),
        joint="curve",
    )
    mask = big.resize(card_img.size, Image.Resampling.LANCZOS)
    _lay(card_img, colour, mask, ink.effect)


def _lay(
    card_img: Image.Image,
    colour: tuple[int, int, int],
    mask: Image.Image,
    effect: dict[str, Any],
) -> None:
    """Lay the route's colour through its mask, as the ink's `blend` and `opacity` say.

    `blend` is `"normal"` (the colour replaces the card where the mask is set) or `"multiply"`
    (the colour is multiplied into the card there, so a dark wash stays dark under it);
    `opacity` in [0, 1] scales the mask and reads 1.0 when the effect omits it.

    Raises:
        ValueError: When `blend` is neither of those or `opacity` is outside [0, 1].
    """
    blend = effect.get("blend", "normal")
    opacity = effect.get("opacity", 1.0)
    if blend not in ROUTE_BLENDS:
        raise ValueError(f"route blend {blend!r} is not one of {ROUTE_BLENDS}")
    if not 0.0 <= opacity <= 1.0:
        raise ValueError(f"route opacity {opacity!r} is not in [0, 1]")
    if opacity < 1.0:
        mask = mask.point(lambda v: round(v * opacity))
    ink = Image.new("RGB", card_img.size, colour)
    if blend == "multiply":
        ink = ImageChops.multiply(card_img, ink)
    card_img.paste(ink, (0, 0), mask)


def paste_labels(card_img: Image.Image, plate: Path) -> None:
    """The label plate, over the painting, at the card's own size.

    The card and the page draw the same pixels, because they are the same
    pixels: one RGBA plate, stroked through the ink engine, embedded by the
    page and pasted here.

    Source: `lanczos` in docs/explanation/references.md.
    """
    ink = Image.open(plate).convert("RGBA")
    if ink.size != card_img.size:
        ink = ink.resize(card_img.size, Image.Resampling.LANCZOS)
    card_img.paste(ink, (0, 0), ink.getchannel("A"))
