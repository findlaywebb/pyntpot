"""The pen casing primitive: a reserve of bare paper between two ink edge lines.

Key function: `pen_casing`. In pen-and-ink a casing is a reserve, so it knocks the wash beneath
a line out to the paper and returns the density of the two edge lines for the caller to ink. It
draws no random number, does not ink the edges itself and is not wired into any line.

Invariants: it alters only the wash, never an inked line, which the caller draws over the
reserve; width 0 returns `(rgb, zeros)` with `rgb` itself; inside the reserve the result is the
paper exactly; the edge band lies outside the reserve. The reserve and the band are
anti-aliased, with fractional values at the edges, and measured from the line's edge.
"""

import numpy as np

from pyntpot.ink.effect_distance import contour_distance
from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_types import PenCasing
from pyntpot.ink.noise import F32


def pen_casing(
    rgb: np.ndarray,
    mask: np.ndarray,
    effect: PenCasing,
    *,
    threshold: float = LINE_THRESHOLD,
    paper: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Knock the wash to the paper inside the reserve and return the edge lines' density.

    With `d` the signed distance from the line's edge, the contour of `mask` at `threshold`,
    the reserve's coverage `r` is 1 on the line and `clip(width_px + 0.5 - d, 0, 1)` outside
    it, and the edge lines' density is `clip(width_px + edge_px + 0.5 - d, 0, 1) - r` outside
    the line and 0 on it. The width is measured from the line's edge. The output is
    `r * paper + (1 - r) * rgb`, so it is the paper exactly wherever `r` is 1.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        effect: The pen casing.
        threshold: The mask value at which a pixel counts as the line; defaults to
            `LINE_THRESHOLD` (0.3).
        paper: `None` for wash space, where the paper is 1, or the `(h, w, 3)` paper plate.

    Returns:
        The colour with the reserve knocked out, and the edge lines' density as float32
        `(h, w)`, from 0 to 1, with `r + density` at most 1.

    Raises:
        ValueError: When `threshold` is not above 0.
    """
    check_threshold(threshold)
    if effect.width_px == 0:
        return rgb, np.zeros(mask.shape, F32)
    d = contour_distance(mask, threshold=threshold, radius=effect.width_px + effect.edge_px + 1)
    core = mask >= threshold
    reserve = np.where(core, F32(1.0), np.clip(F32(effect.width_px) + F32(0.5) - d, 0.0, 1.0))
    outer = np.clip(F32(effect.width_px + effect.edge_px) + F32(0.5) - d, 0.0, 1.0)
    band = np.where(core, F32(0.0), outer - reserve).astype(F32)
    ground = F32(1.0) if paper is None else paper
    r = reserve.astype(F32)[..., None]
    out = r * ground + (F32(1.0) - r) * rgb
    return np.clip(out, 0.0, 1.0).astype(F32, copy=False), band
