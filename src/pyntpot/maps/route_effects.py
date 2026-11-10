"""The route's effects at compose: its stack laid round the route on the card.

Key function: `lay`, which takes the card as 8-bit RGB, the route's mask and the paper plate, lays
the route's `EffectStack` (via `effect_pass.lay_stack`) and returns the card as 8-bit RGB. The
mask is the pen plate's alpha, taken at `LINE_THRESHOLD`, or the solid line's reduced mask; it is
one mask for the whole route, so a stretch that is retraced is one line and not two.

Does not draw the route itself, read the pen plate from disk or touch the SVG page, which does not
draw route effects. It draws no random number. An empty stack returns the card unchanged.
"""

import numpy as np
from PIL import Image

from pyntpot.ink.effect_mask import LINE_THRESHOLD
from pyntpot.ink.noise import F32
from pyntpot.maps.effect_pass import lay_stack
from pyntpot.maps.line_effects import EffectStack


def pen_mask(alpha: Image.Image) -> np.ndarray:
    """The route mask of a pen plate's alpha: 1 where it is at `LINE_THRESHOLD`, else 0."""
    density = np.asarray(alpha, F32) / F32(255.0)
    return (density >= LINE_THRESHOLD).astype(F32)


def solid_mask(reduced: Image.Image) -> np.ndarray:
    """The route mask of the solid line's reduced `L` image, as a 0 to 1 density."""
    return np.asarray(reduced, F32) / F32(255.0)


def lay(
    card: Image.Image,
    mask: np.ndarray,
    stack: EffectStack,
    *,
    scale: float,
    paper: Image.Image,
) -> Image.Image:
    """The card with `stack` laid round the route `mask` marks, as a new 8-bit RGB image.

    Args:
        card: The card, RGB.
        mask: The route's density, a float array of the card's shape.
        stack: The route's effects, widths in display pixels.
        scale: Card pixels per display pixel.
        paper: The paper plate, at the card's size.

    Returns:
        The card with the effects laid, rounded back to 8 bits.
    """
    if not stack.effects:
        return card
    rgb = np.asarray(card.convert("RGB"), F32) / F32(255.0)
    plate = np.asarray(paper.convert("RGB"), F32) / F32(255.0)
    laid = lay_stack(rgb, mask, stack, scale=scale, paper=plate)
    return Image.fromarray(np.rint(laid * F32(255.0)).astype(np.uint8), "RGB")
