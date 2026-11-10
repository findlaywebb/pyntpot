"""The casing union: one ring round the union of several lines' footprints.

Key function: `casing_union`, private to `ink` and reached by `maps` by module path. Given
`(mask, effect)` pairs, all `Casing` or all `Reserve`, it lays one ring whose coverage is the
maximum of the members' own, each at its own width, and which is never laid inside any member's
footprint, so one class's ring cannot show through another class's line. It does not draw the
lines, knows no line class, and draws no random number.

Invariants: the output equals `rgb` bit for bit wherever any member's mask is at or above the
threshold; members of width 0 add no ring; a union of one member equals that member's own
`casing` or `reserve` bit for bit; members all of width 0, or no mask at the threshold, return
`rgb` itself.
"""

from collections.abc import Sequence

import numpy as np

from pyntpot.ink.effect_casing import blend_casing
from pyntpot.ink.effect_distance import contour_distance, ring_coverage
from pyntpot.ink.effect_mask import LINE_THRESHOLD, check_threshold
from pyntpot.ink.effect_reserve import lay_reserve, pool_band
from pyntpot.ink.effect_types import Casing, Reserve
from pyntpot.ink.noise import F32

type Member = tuple[np.ndarray, Casing] | tuple[np.ndarray, Reserve]


def _check_members(members: Sequence[Member]) -> None:
    """Refuse an empty union, mixed kinds, or members whose shared fields differ."""
    if not members:
        raise ValueError("a casing union needs at least one member")
    effects = [effect for _, effect in members]
    first = effects[0]
    if any(type(e) is not type(first) for e in effects):
        raise ValueError("a casing union takes all casings or all reserves: the kind differs")
    if isinstance(first, Casing):
        if any(e.colour != first.colour for e in effects if isinstance(e, Casing)):
            raise ValueError("casings in one union must share a colour")
        if any(e.strength != first.strength for e in effects if isinstance(e, Casing)):
            raise ValueError("casings in one union must share a strength")
    elif any(e.pool != first.pool for e in effects if isinstance(e, Reserve)):
        raise ValueError("reserves in one union must share a pool")


def casing_union(
    rgb: np.ndarray,
    members: Sequence[Member],
    *,
    threshold: float = LINE_THRESHOLD,
    paper: np.ndarray | None = None,
) -> np.ndarray:
    """Lay one casing or reserve round the union of several lines, outside every footprint.

    The ring's coverage is the maximum of the members' `ring_coverage`, each at its own width,
    and its weight is 0 wherever any member's mask is at or above `threshold`. A casing union
    blends as `casing` does, with its members' one colour and strength. A reserve union lays the
    paper as `reserve` does, its pool band taken from the least `d - width_px` over the members.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        members: `(mask, effect)` pairs, the effects all `Casing` or all `Reserve`.
        threshold: The mask value at which a pixel counts as a line; defaults to
            `LINE_THRESHOLD` (0.3).
        paper: `None` for wash space, where the paper is 1, or the `(h, w, 3)` paper plate.

    Returns:
        `rgb` itself when nothing is cast, otherwise a new float32 array clipped to 0 to 1.

    Raises:
        ValueError: When `threshold` is not above 0, `members` is empty, the kinds are mixed,
            casings differ in colour or strength, or reserves differ in pool.
    """
    check_threshold(threshold)
    _check_members(members)
    first = members[0][1]
    if isinstance(first, Casing) and first.strength == 0:
        return rgb
    core = np.zeros(rgb.shape[:2], bool)
    for mask, _ in members:
        core |= mask >= threshold
    live = [(m, e) for m, e in members if e.width_px > 0]
    if not live or not core.any():
        return rgb
    coverage = np.zeros(rgb.shape[:2], F32)
    excess = np.full(rgb.shape[:2], np.inf, F32)
    for mask, effect in live:
        radius = effect.width_px + (1 if isinstance(effect, Casing) else 2)
        d = contour_distance(mask, threshold=threshold, radius=radius)
        coverage = np.maximum(coverage, ring_coverage(d, effect.width_px))
        excess = np.minimum(excess, d - F32(effect.width_px))
    ground = F32(1.0) if paper is None else paper
    if isinstance(first, Casing):
        weight = first.strength * coverage
        return blend_casing(rgb, np.where(core, F32(0.0), weight), first, ground)
    assert isinstance(first, Reserve)
    coverage = np.where(core, F32(0.0), coverage)
    band = np.where(core, F32(0.0), pool_band(excess))
    return lay_reserve(rgb, coverage, band, first.pool, ground)
