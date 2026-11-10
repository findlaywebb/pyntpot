"""The reserve primitive: the paper laid back in a ring round a line, with an optional pool.

Key function: `reserve`. A reserve is masking fluid: the pigment beneath a ring round the line
is lifted to the paper, and an optional pool darkens the pixels just outside the ring where
pigment gathered at the resist's edge. It is a plain function of the RGB beneath it, a float
mask and a `Reserve`, in RGB and not by Kubelka-Munk, and it draws no random number. It knows
nothing of maps, does not draw the line, and never darkens bare paper.

Invariants: the ring is anti-aliased and measured from the line's edge; where its coverage is 1
the output is the paper bit for bit; where the mask is at or above the threshold the output
equals `rgb` bit for bit; the pool deepens only where its band is above 0 and only ever
darkens, so a pool never lightens and never touches a pixel already at the paper; width 0 or a
mask nowhere at the threshold returns `rgb` itself.

`pool_band` and `lay_reserve` are not exported; the casing union shares them so a union of
one class agrees with `reserve` bit for bit.
"""

import numpy as np

from pyntpot.ink.effect_distance import contour_distance, ring_coverage
from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_types import Reserve
from pyntpot.ink.noise import F32


def pool_band(excess: np.ndarray) -> np.ndarray:
    """The pool's weight from `excess = d - width_px`: a tent on the ring's outer edge.

    Args:
        excess: The distance beyond the ring's outer edge, float32, subtracted once by the
            caller.

    Returns:
        `clip(1.5 - excess, 0, 1) - clip(0.5 - excess, 0, 1)`: 0 up to half a pixel inside the
        ring's outer edge, rising to 1 at half a pixel past it, and falling back to 0 at 1.5
        pixels past it.
    """
    return np.clip(F32(1.5) - excess, 0.0, 1.0) - np.clip(F32(0.5) - excess, 0.0, 1.0)


def lay_reserve(
    rgb: np.ndarray,
    coverage: np.ndarray,
    band: np.ndarray,
    pool: float,
    ground: np.ndarray | np.floating,
) -> np.ndarray:
    """Lay the paper over `rgb` by `coverage`, then deepen it by the pool where `band` is above 0.

    Where the coverage is 1 the result is `ground` exactly, and where it is 0 it is `rgb`
    exactly. The pool takes `minimum(out, ground * (out / ground) ** (1 + pool * band))` only
    where `band > 0`, the pixel is below the ground and the ground is above 0, so it never
    lightens and leaves the rest bit for bit.
    """
    ground_all = np.broadcast_to(ground, rgb.shape)
    c = coverage[..., None]
    out = np.where(c >= 1.0, ground_all, rgb + c * (ground_all - rgb))
    out = np.clip(out, 0.0, 1.0).astype(F32, copy=False)
    if pool > 0:
        b = np.broadcast_to(band[..., None], rgb.shape)
        deepen = (b > 0) & (out < ground_all) & (ground_all > 0)
        if deepen.any():
            safe = np.where(deepen, ground_all, F32(1.0))
            ratio = np.where(deepen, out, F32(1.0)) / safe
            deeper = (safe * ratio ** (F32(1.0) + F32(pool) * b)).astype(F32, copy=False)
            out = np.where(deepen, np.minimum(out, deeper), out)
    return out


def reserve(
    rgb: np.ndarray,
    mask: np.ndarray,
    effect: Reserve,
    *,
    threshold: float = LINE_THRESHOLD,
    paper: np.ndarray | None = None,
) -> np.ndarray:
    """Lay the paper back in a ring round the line, lifting every pigment beneath it.

    With `w = effect.width_px` and `c` the coverage of the ring `[0, w]` beyond the line's edge,
    anti-aliased, the output is `c * paper + (1 - c) * rgb`, so it is the paper exactly where
    `c` is 1. When `pool > 0`, a pixel darker than the paper just outside the ring is deepened
    toward a pooled edge, never lightened, and bare paper stays bare. The coverage is 0
    wherever the mask is at or above `threshold`, so the line itself is never altered.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        effect: The reserve.
        threshold: The mask value at which a pixel counts as the line; defaults to
            `LINE_THRESHOLD` (0.3).
        paper: `None` for wash space, where the paper is 1, or the `(h, w, 3)` paper plate.

    Returns:
        `rgb` itself when nothing is reserved, otherwise a new float32 array clipped to 0 to 1.

    Raises:
        ValueError: When `threshold` is not above 0.
    """
    check_threshold(threshold)
    if effect.width_px == 0:
        return rgb
    core = mask >= threshold
    if not core.any():
        return rgb
    d = contour_distance(mask, threshold=threshold, radius=effect.width_px + 2)
    coverage = np.where(core, F32(0.0), ring_coverage(d, effect.width_px))
    band = np.where(core, F32(0.0), pool_band(d - F32(effect.width_px)))
    ground = F32(1.0) if paper is None else paper
    return lay_reserve(rgb, coverage, band, effect.pool, ground)
