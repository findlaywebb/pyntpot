"""The pen casing primitive: a reserve of bare paper between two ink edge lines.

Key function: `pen_casing`. In pen-and-ink a casing is a reserve, so it knocks the wash beneath
a line out to the paper and returns the density of the two edge lines for the caller to ink. It
draws no random number, does not ink the edges itself and is not wired into any line.

Invariants: it alters only the wash, never an inked line, which the caller draws over the
reserve; width 0 returns `(rgb, zeros)` with `rgb` itself; inside the reserve the result is the
paper exactly; the edge band lies outside the reserve.
"""

import numpy as np

from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_types import PenCasing
from pyntpot.ink.noise import F32, chamfer_distance


def pen_casing(
    rgb: np.ndarray,
    mask: np.ndarray,
    effect: PenCasing,
    *,
    threshold: float = LINE_THRESHOLD,
    paper: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Knock the wash to the paper inside the reserve and return the edge lines' density.

    With `d` the chamfer distance to the pixels of `mask` at `threshold`, the reserve is
    `d <= effect.width_px` and the edge lines are `width_px < d <= width_px + edge_px`.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        effect: The pen casing.
        threshold: The mask value at which a pixel counts as the line; defaults to
            `LINE_THRESHOLD` (0.3).
        paper: `None` for wash space, where the paper is 1, or the `(h, w, 3)` paper plate.

    Returns:
        The colour with the reserve knocked out, and the edge lines' density as float32
        `(h, w)`, 1 on the edge band and 0 elsewhere.

    Raises:
        ValueError: When `threshold` is not above 0.
    """
    check_threshold(threshold)
    if effect.width_px == 0:
        return rgb, np.zeros(mask.shape, F32)
    dist = chamfer_distance(mask >= threshold)
    reserve = dist <= effect.width_px
    band = (~reserve) & (dist <= effect.width_px + effect.edge_px)
    ground = F32(1.0) if paper is None else paper
    out = np.where(reserve[..., None], ground, rgb)
    return np.clip(out, 0.0, 1.0).astype(F32, copy=False), band.astype(F32)
