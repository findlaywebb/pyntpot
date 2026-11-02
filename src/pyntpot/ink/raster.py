"""Rasterising outlines: coverage of filled rings, stroked lines and deformed outlines.

Key functions: `fill_cov`, the coverage of a set of rings, supersampled and averaged
down; `stroke_mask`, a binary mask of polylines at a fixed width; `deform_ring` and
`deform_rings`, Hobbs' recursive midpoint displacement of closed outlines, with `Deform`
the settings tuple one class's outlines are deformed by.

It reads no style and writes no file. Geometry arrives in the canvas's metres and leaves
as pixels or as deformed metres.

Invariants: `fill_cov` returns `float32` in 0 to 1 at the canvas's own size; `deform_rings`
with no settings returns the rings it was given, unchanged.
"""

from typing import Any

import numpy as np
import numpy.typing as npt

from pyntpot.ink.noise import F32, chamfer_distance
from pyntpot.ink.polyline import Pt
from pyntpot.ink.sheet import Canvas

#: A ring needs three points to enclose anything, and a ring array is `(n, 2)`.
_MIN_RING = 3
_POINT_DIMS = 2
#: Deformation stops doubling a ring that has grown past this many points.
_MAX_RING_POINTS = 24000


def _crossings(xs: np.ndarray, ys: np.ndarray, hs: int, ws: int) -> tuple[np.ndarray, np.ndarray]:
    """Every scanline crossing of one ring's edges, as flat accumulator cells and windings.

    The accumulator is `(hs, ws + 2)`: the rows, and the columns plus two of margin.
    Each edge runs from a point to the next, the last back to the first, and is
    taken upward, with its winding negated when it ran downward; a level edge
    crosses no row. Per edge the arithmetic is the scalar form's, element for
    element, so the crossings land on the same cells.
    """
    x1, y1 = np.roll(xs, -1), np.roll(ys, -1)
    down = y1 < ys
    lo_x, lo_y = np.where(down, x1, xs), np.where(down, y1, ys)
    hi_x, hi_y = np.where(down, xs, x1), np.where(down, ys, y1)
    # Clipped at both ends before the cast, so a ring far off the canvas cannot
    # overflow it; an edge left with no rows is skipped either way.
    r0 = np.clip(np.ceil(lo_y - 0.5), 0, hs).astype(np.intp)
    r1 = np.clip(np.ceil(hi_y - 0.5), 0, hs).astype(np.intp)
    rows = np.where((ys != y1) & (r1 > r0), r1 - r0, 0)
    e = np.repeat(np.arange(len(rows)), rows)
    rr = np.arange(len(e)) - (np.cumsum(rows) - rows)[e] + r0[e]
    xx = lo_x[e] + (rr + 0.5 - lo_y[e]) * (hi_x - lo_x)[e] / (hi_y - lo_y)[e]
    cc = np.clip(np.ceil(xx - 0.5).astype(np.int32), 0, ws + 1)
    return rr * (ws + 2) + cc, np.where(down, -1, 1).astype(np.int16)[e]


#: What one class's outlines are deformed by: the generator, the first round's
#: variance as a share of a segment, the rounds, what each round hands its
#: children, the ceiling on one displacement and the segment length to stop at,
#: both in the rings' own metres.
Deform = tuple[np.random.Generator, float, int, float, float, float]


def deform_ring(ring: npt.ArrayLike, deform: Deform) -> np.ndarray:
    """Recursive midpoint displacement of one closed outline.

    Hobbs' construction: each segment carries its own variance, is split at a
    midpoint pushed off the line by that variance times its own length, and
    hands each half a decayed and separately randomised share of it. Carrying
    the variance per segment rather than per round is the whole point. A single
    global amplitude gives an outline that wobbles at one frequency everywhere,
    which is what the blurred-mask edge already does; per-segment variance is
    what makes one stretch of a wood loose and the next stretch tight.

    Source: `midpoint-displacement` in docs/explanation/references.md.

    Args:
        ring: The outline, in the rings' own metre coordinates.
        deform: The settings, in `Deform`'s order: the generator the displacements
            are drawn from; the first round's variance, as a share of a segment's
            length; how many rounds, each doubling the point count; what each round
            hands its children, before the randomisation; the largest one
            displacement may be, in metres; and the median segment length below
            which to stop.

    Returns:
        The deformed ring, `(n, 2)`.
    """
    rng, amount, depth, decay, cap, min_seg = deform
    p = np.asarray(ring, dtype=np.float64)
    if p.ndim != _POINT_DIMS or len(p) < _MIN_RING:
        return p
    var = np.full(len(p), max(amount, 0.0))
    for _ in range(max(int(depth), 0)):
        n = len(p)
        if n > _MAX_RING_POINTS:
            break
        q = np.roll(p, -1, axis=0)
        d = q - p
        seg = np.hypot(d[:, 0], d[:, 1])
        if float(np.median(seg)) < min_seg:
            break
        ln = np.maximum(seg, 1e-9)
        off = np.clip(rng.normal(0.0, 1.0, n) * var * seg, -cap, cap)
        mid = 0.5 * (p + q)
        mid[:, 0] -= d[:, 1] / ln * off
        mid[:, 1] += d[:, 0] / ln * off
        out = np.empty((2 * n, 2))
        out[0::2] = p
        out[1::2] = mid
        p = out
        var = np.repeat(var, 2) * decay * rng.uniform(0.75, 1.25, 2 * n)
    return p


def deform_rings(rings: list[list[Pt]], deform: Deform | None) -> list[Any]:
    """Every outline of one class deformed, or the outlines unchanged.

    Args:
        rings: The class's outlines, in metres.
        deform: The settings, or None to leave them exactly as they are.

    Returns:
        The rings, deformed or the same objects.
    """
    if deform is None:
        return rings
    return [deform_ring(r, deform) for r in rings]


def fill_cov(rings: list[list[Pt]], canvas: Canvas, ss: int = 2) -> np.ndarray:
    """Coverage of a set of rings, supersampled and averaged down.

    Filled by the nonzero winding rule, so a ring wound against the one around
    it cuts a hole and two rings wound the same way fill as one.

    Raises:
        ValueError: When a ring has a coordinate that is not finite.
    """
    hs, ws = canvas.h * ss, canvas.w * ss
    acc = np.zeros((hs, ws + 2), np.int16)
    acc_flat = acc.reshape(-1, copy=False)
    for ring in rings:
        if len(ring) < _MIN_RING:
            continue
        p = canvas.px(ring) * ss
        if not np.isfinite(p).all():
            raise ValueError(f"a ring has a coordinate that is not finite: {ring[:3]}...")
        # Integer windings, so the order they are added in cannot change the sum.
        np.add.at(acc_flat, *_crossings(p[:, 0], p[:, 1], hs, ws))
    inside = (np.cumsum(acc, axis=1, dtype=np.int32)[:, :ws] != 0).view(np.uint8)
    # The supersamples counted in integers and divided once: what `mean` gives,
    # bit for bit, since a count of at most `ss * ss` is exact in float32.
    count = np.zeros((canvas.h, canvas.w), np.uint16)
    for dy in range(ss):
        for dx in range(ss):
            count += inside[dy::ss, dx::ss]
    return count.astype(F32) / F32(ss * ss)


def stroke_mask(lines: list[list[Pt]], canvas: Canvas, width_px: float) -> np.ndarray:
    """A binary mask of polylines stroked at a fixed width."""
    hits = np.zeros((canvas.h, canvas.w), bool)
    for pts in lines:
        p = canvas.px(pts)
        seg = np.hypot(np.diff(p[:, 0]), np.diff(p[:, 1]))
        total = float(seg.sum())
        if total < 1:
            continue
        cum = np.concatenate([[0.0], np.cumsum(seg)])
        t = np.linspace(0, total, max(int(total / 0.6), 2))
        ix = np.clip(np.round(np.interp(t, cum, p[:, 0])).astype(np.int32), 0, canvas.w - 1)
        iy = np.clip(np.round(np.interp(t, cum, p[:, 1])).astype(np.int32), 0, canvas.h - 1)
        hits[iy, ix] = True
    if width_px <= 1:
        return hits
    return chamfer_distance(hits) < width_px * 0.5
