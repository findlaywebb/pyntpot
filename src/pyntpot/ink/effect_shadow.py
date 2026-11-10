"""The shadow primitive: the line's mask offset away from the light and laid as a darken.

Key functions: `shadow` and `shadow_offset`, the whole-pixel shift the shadow falls by. It is a
plain function of the RGB beneath it and a float mask, in RGB and not by Kubelka-Munk, and it
draws no random number. The light's direction is the caller's `azimuth_deg`, not a field of
`Shadow`. It does not draw the line itself.

Invariants: where the mask is at or above the threshold the output equals `rgb` bit for bit;
the output is never lighter than `rgb`; the result is a new float32 array clipped to 0 to 1.
"""

import math

import numpy as np

from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_types import Shadow
from pyntpot.ink.noise import F32, blur


def shadow_offset(offset_px: float, azimuth_deg: float) -> tuple[int, int]:
    """The whole-pixel shift `(dx, dy)` of a shadow, in image columns and rows.

    The shadow falls away from the light, along bearing `b = azimuth_deg + 180`, with
    `dx = round(offset_px * sin b)` and `dy = round(-offset_px * cos b)`; Python's `round`
    takes half to even.

    Args:
        offset_px: How far the shadow falls, in pixels.
        azimuth_deg: The light's azimuth in degrees clockwise from north.

    Returns:
        The column shift (right is positive) and row shift (down is positive).
    """
    bearing = math.radians(azimuth_deg + 180.0)
    return round(offset_px * math.sin(bearing)), round(-offset_px * math.cos(bearing))


def _shifted(mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
    """`mask` moved by `(dx, dy)` with zero fill; never a wrap."""
    h, w = mask.shape
    out = np.zeros((h, w), F32)
    if abs(dx) >= w or abs(dy) >= h:
        return out
    out[max(dy, 0) : h + min(dy, 0), max(dx, 0) : w + min(dx, 0)] = mask[
        max(-dy, 0) : h + min(-dy, 0), max(-dx, 0) : w + min(-dx, 0)
    ]
    return out


def shadow(
    rgb: np.ndarray,
    mask: np.ndarray,
    effect: Shadow,
    *,
    azimuth_deg: float,
    threshold: float = LINE_THRESHOLD,
) -> np.ndarray:
    """Darken the colour beneath the line's offset, blurred mask, except under the line.

    The mask is shifted by `shadow_offset`, blurred by `effect.blur_px`, and the weight is
    `effect.strength` times that, times `1 - clip(mask / threshold, 0, 1)`, so it is 0 wherever
    the mask is at or above `threshold`. The result is `rgb * (1 - a * (1 - colour))` where the
    weight is above 0, and `rgb` elsewhere.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        effect: The shadow; its colour enters as `effect.colour.rgb`.
        azimuth_deg: The light's azimuth in degrees clockwise from north.
        threshold: The mask value at which a pixel counts as the line; defaults to
            `LINE_THRESHOLD` (0.3).

    Returns:
        A new float32 array clipped to 0 to 1.

    Raises:
        ValueError: When `threshold` is not above 0.
    """
    check_threshold(threshold)
    dx, dy = shadow_offset(effect.offset_px, azimuth_deg)
    soft = np.clip(blur(_shifted(mask, dx, dy), effect.blur_px), 0.0, 1.0)
    weight = effect.strength * soft * (1.0 - np.clip(mask / threshold, 0.0, 1.0))
    dark = rgb * (1.0 - weight[..., None] * (1.0 - effect.colour.rgb))
    return np.clip(np.where(weight[..., None] > 0, dark, rgb), 0.0, 1.0).astype(F32, copy=False)
