"""The glow primitive: a lift of the colour beneath a line toward the paper.

Key function: `glow`, with a hard spread and a soft blur and no colour of its own. It is a
plain function of the RGB beneath it and a float mask, in RGB and not by Kubelka-Munk, and it
draws no random number. It does not draw the line itself.

Invariants: the lift is floored at 0, so no pixel gets darker for any input; where the mask is
at or above the threshold the output equals `rgb` bit for bit; strength 0 returns `rgb` itself; every other result is a new float32 array clipped to 0 to 1.
"""

import numpy as np

from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_types import Glow
from pyntpot.ink.noise import F32, blur, chamfer_distance


def glow(
    rgb: np.ndarray,
    mask: np.ndarray,
    effect: Glow,
    *,
    threshold: float = LINE_THRESHOLD,
    paper: np.ndarray | None = None,
) -> np.ndarray:
    """Lift the colour beneath a line toward the paper, never darkening it.

    The core is the pixels within `effect.spread_px` of the mask at `threshold`; the weight
    is `effect.strength` times the core blurred by `effect.blur_px`, and the result is
    `rgb + a * max(paper - rgb, 0)`. The weight is 0 wherever the mask is at or above
    `threshold`, so the glow lifts only the halo and never washes out the line itself.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        effect: The glow.
        threshold: The mask value at which a pixel counts as the line; defaults to
            `LINE_THRESHOLD` (0.3).
        paper: `None` for wash space, where the paper is 1, or the `(h, w, 3)` paper plate.

    Returns:
        `rgb` itself at strength 0, otherwise a new float32 array clipped to 0 to 1.

    Raises:
        ValueError: When `threshold` is not above 0.
    """
    check_threshold(threshold)
    if effect.strength == 0:
        return rgb
    line = mask >= threshold
    core = chamfer_distance(line) <= effect.spread_px
    weight = effect.strength * np.clip(blur(core.astype(F32), effect.blur_px), 0.0, 1.0)
    weight = np.where(line, F32(0.0), weight)
    ground = F32(1.0) if paper is None else paper
    out = rgb + weight[..., None] * np.maximum(ground - rgb, 0.0)
    return np.clip(out, 0.0, 1.0).astype(F32, copy=False)
