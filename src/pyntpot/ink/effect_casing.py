"""The casing primitive: a ring of colour laid over the paper round a line.

Key function: `casing`. It is a plain function of the RGB beneath it, a float mask and a
`Casing`, in RGB and not by Kubelka-Munk, and it draws no random number. It knows nothing of
maps and does not draw the line itself.

Invariants: width 0, strength 0 or a mask nowhere at the threshold returns `rgb` itself; where
the mask is at or above the threshold the output equals `rgb` bit for bit; every other result is
a new float32 array clipped to 0 to 1.
"""

import numpy as np

from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_types import Casing
from pyntpot.ink.noise import F32, chamfer_distance, smoothstep


def casing(
    rgb: np.ndarray,
    mask: np.ndarray,
    effect: Casing,
    *,
    threshold: float = LINE_THRESHOLD,
    paper: np.ndarray | None = None,
) -> np.ndarray:
    """Blend a ring round the line toward its colour laid over the paper.

    With `w = effect.width_px`, the weight is `effect.strength` times a soft step of
    `w - d`, where `d` is the chamfer distance to the pixels of `mask` at `threshold`, and
    the result is `rgb + a * (colour * paper - rgb)`, so a white casing is the paper. The
    weight is 0 wherever the mask is at or above `threshold`, so the casing paints only
    outside the line and never shows through it.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        effect: The casing; its colour enters as `effect.colour.rgb`.
        threshold: The mask value at which a pixel counts as the line; defaults to
            `LINE_THRESHOLD` (0.3).
        paper: `None` for wash space, where the paper is 1, or the `(h, w, 3)` paper plate.

    Returns:
        `rgb` itself when nothing is cast, otherwise a new float32 array clipped to 0 to 1.

    Raises:
        ValueError: When `threshold` is not above 0.
    """
    check_threshold(threshold)
    if effect.width_px == 0 or effect.strength == 0:
        return rgb
    core = mask >= threshold
    if not core.any():
        return rgb
    weight = effect.strength * smoothstep(effect.width_px - chamfer_distance(core), 1.0)
    weight = np.where(core, F32(0.0), weight)
    ground = F32(1.0) if paper is None else paper
    target = effect.colour.rgb * ground
    out = rgb + weight[..., None] * (target - rgb)
    return np.clip(out, 0.0, 1.0).astype(F32, copy=False)
