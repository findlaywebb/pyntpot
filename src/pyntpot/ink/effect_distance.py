"""The signed sub-pixel distance from a line's edge, and the ring coverage built on it.

Key names: `contour_distance`, the Euclidean distance in pixels from each pixel centre to the
line's contour (the mask at its threshold), and `ring_coverage`, the box-filtered coverage of a
ring beyond that contour. Both are private to `ink`: the casing, the pen casing and the reserve
call them, and a caller of `ink` never needs a distance field.

It is pure numpy, draws no random number and has no scipy. It does not blur, threshold or
dilate a mask for a caller, and it does not measure inside the line.

Invariants: the distance is at most 0 wherever `mask >= threshold` and at least 0 elsewhere,
bit for bit; outside the line it is within 0.4 px of the exact distance for a threshold from
0.2 to 0.5, wherever the nearest contour point lies on the array; a mask with no pixel at the
threshold gives `radius + 2` everywhere, and an all-line mask gives 0 everywhere.
"""

import numpy as np

from pyntpot.ink.noise import F32

#: The four neighbours a seed's contour crossing is looked for toward, as (row, column) steps.
_NEIGHBOURS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _shifted(plane: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """`plane` read at each pixel's neighbour `(dy, dx)` away, the edge repeated."""
    h, w = plane.shape
    padded = np.pad(plane, 1, mode="edge")
    return padded[1 + dy : 1 + dy + h, 1 + dx : 1 + dx + w]


def _crossings(mask: np.ndarray, core: np.ndarray, tau: np.floating) -> np.ndarray:
    """Each pixel's signed offset to the contour along its nearest crossing, or inf.

    Where a pixel and a 4-neighbour lie on opposite sides of the threshold, the contour is put
    where the mask, linearly interpolated between the two, equals the threshold. The offset is
    that distance from the pixel, negative inside the line and positive outside, within 1.
    """
    best = np.full(mask.shape, np.inf, F32)
    for dy, dx in _NEIGHBOURS:
        other = _shifted(mask, dy, dx)
        across = _shifted(core, dy, dx) != core
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            frac = np.clip(np.abs((tau - mask) / (other - mask)), 0.0, 1.0)
        cand = np.where(across, np.where(core, -frac, frac), np.inf).astype(F32)
        best = np.where(np.abs(cand) < np.abs(best), cand, best)
    return best


def _slices(offset: int, size: int) -> tuple[slice, slice]:
    """The (source, destination) slices that move a plane by `offset` along one axis."""
    if offset >= 0:
        return slice(offset, None), slice(None, size - offset)
    return slice(None, size + offset), slice(-offset, None)


def contour_distance(mask: np.ndarray, *, threshold: float, radius: float) -> np.ndarray:
    """The signed distance in pixels from each pixel centre to the line's contour.

    The contour is where the mask crosses `threshold`, placed by linear interpolation between
    neighbouring pixels, and the distance to it is the minimum over every pixel within
    `radius + 2` of that pixel of the pixel's offset plus the straight-line step between them.
    The cost grows with the square of `radius`.

    Args:
        mask: The line's density, float `(h, w)`; read as float32.
        threshold: The mask value at which a pixel counts as the line.
        radius: The farthest outside distance the caller reads; the result is accurate for
            outside distances up to it, and capped at `radius + 2` beyond.

    Returns:
        A float32 array of the mask's shape. Outside the line (`mask < threshold`) it is the
        distance, from 0 to `radius + 2`. Inside (`mask >= threshold`) only the sign is
        claimed: the value is 0 or negative. A mask with no pixel at `threshold` gives
        `radius + 2` everywhere; a mask with no pixel below it gives 0 everywhere.
    """
    m = np.asarray(mask, F32)
    core = m >= threshold
    h, w = m.shape
    big = F32(radius + 2)
    crossing = _crossings(m, core, F32(threshold))
    seeded = np.isfinite(crossing)
    start = np.where(seeded, np.clip(crossing, -1.0, 1.0), big).astype(F32)
    best = start.copy()
    reach = int(np.ceil(radius)) + 1
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            if (
                (dy, dx) == (0, 0)
                or dy * dy + dx * dx > reach * reach
                or abs(dy) >= h
                or abs(dx) >= w
            ):
                continue
            (sy, ty), (sx, tx) = _slices(dy, h), _slices(dx, w)
            step = F32(np.hypot(dy, dx))
            np.minimum(best[ty, tx], start[sy, sx] + step, out=best[ty, tx])
    best = np.where(core, np.minimum(best, 0.0), np.maximum(best, 0.0))
    return np.where(~core & ~seeded & (best >= big), big, best).astype(F32, copy=False)


def ring_coverage(distance: np.ndarray, width_px: float) -> np.ndarray:
    """The box-filtered coverage of the ring `[0, width_px]` beyond the contour.

    Args:
        distance: A `contour_distance` result.
        width_px: The ring's width, from the line's edge, at least 0.

    Returns:
        `clip(width_px + 0.5 - d, 0, 1) * clip(d + 0.5, 0, 1)`: 1 where the pixel lies wholly
        in the ring, 0 where it lies wholly outside, and the covered fraction between.
    """
    outer = np.clip(F32(width_px) + F32(0.5) - distance, 0.0, 1.0)
    inner = np.clip(distance + F32(0.5), 0.0, 1.0)
    return (outer * inner).astype(F32, copy=False)
