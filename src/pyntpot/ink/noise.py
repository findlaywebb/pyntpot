"""Noise, blur and distance fields: the raster maths every wash and mark is built on.

Key functions: `value_noise` and `fbm`, smooth and fractal noise on the pixel grid;
`fbm_aniso`, fractal noise stretched along one axis; `blur`, three box passes standing
in for a Gaussian; `edt`, a chamfer distance transform; `smoothstep`, a soft step;
`fill_holes`, the enclosed holes of a mask filled on a coarse copy. `F32` is the float
type every field is held in.

It paints nothing and reads no style. Every random field is drawn from a generator
the caller hands in, so the same seed makes the same field.

Invariants: fields are `float32` arrays; `fbm` and `fbm_aniso` are normalised to 0 to 1;
none of these functions changes an array it was given.
"""

import math

import numpy as np

F32 = np.float32

#: Below this blur width the field is returned as it is: it would not move a pixel.
_BLUR_FLOOR = 0.4


def value_noise(h: int, w: int, cell: float, rng: np.random.Generator) -> np.ndarray:
    """Smooth value noise on a grid of `cell` pixels."""
    cell = max(cell, 1.0)
    gh, gw = int(h / cell) + 3, int(w / cell) + 3
    g = rng.random((gh, gw)).astype(F32)
    ys = np.arange(h, dtype=F32) / cell
    xs = np.arange(w, dtype=F32) / cell
    y0 = np.floor(ys).astype(np.int32)
    x0 = np.floor(xs).astype(np.int32)
    fy = ys - y0
    fx = xs - x0
    fy = (fy * fy * (3 - 2 * fy))[:, None]
    fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def fbm(h: int, w: int, cell: float, octaves: int, rng: np.random.Generator) -> np.ndarray:
    """Fractal noise, normalised to 0 to 1."""
    out = np.zeros((h, w), F32)
    amp, total = 1.0, 0.0
    for i in range(octaves):
        out += amp * value_noise(h, w, cell / (2**i), rng)
        total += amp
        amp *= 0.5
    out /= total
    lo, hi = float(out.min()), float(out.max())
    return (out - lo) / max(hi - lo, 1e-6)


def _value_noise_at(
    u: np.ndarray, v: np.ndarray, cell: float, rng: np.random.Generator
) -> np.ndarray:
    """Smooth value noise sampled at arbitrary coordinates rather than a grid.

    `value_noise` walks the pixel grid, so it can only make an isotropic field.
    This takes the coordinates it is given, which is what lets a caller squash
    or rotate them first.

    Args:
        u: Column coordinate per pixel, in the same units as `cell`.
        v: Row coordinate per pixel.
        cell: The lattice spacing.
        rng: The generator the lattice is drawn from.

    Returns:
        The field, in 0 to 1, with the shape of `u`.
    """
    cell = max(cell, 1.0)
    us, vs = u / cell, v / cell
    u0f, v0f = np.floor(us), np.floor(vs)
    umin, vmin = float(u0f.min()), float(v0f.min())
    gw = int(u0f.max() - umin) + 3
    gh = int(v0f.max() - vmin) + 3
    g = rng.random((gh, gw)).astype(F32)
    ix = (u0f - umin).astype(np.int32)
    iy = (v0f - vmin).astype(np.int32)
    fx = (us - u0f).astype(F32)
    fy = (vs - v0f).astype(F32)
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = g[iy, ix]
    b = g[iy, ix + 1]
    c = g[iy + 1, ix]
    d = g[iy + 1, ix + 1]
    top = a + (b - a) * fx
    bot = c + (d - c) * fx
    return top + (bot - top) * fy


def fbm_aniso(
    shape: tuple[int, int],
    cell: float,
    octaves: int,
    rng: np.random.Generator,
    stretch: float,
    angle: float,
) -> np.ndarray:
    """Fractal noise stretched along one axis: a laid fibre, not concrete.

    Cold-press paper has a direction. Squashing one axis of the sampling
    coordinates by `stretch` before the lattice is read gives a field whose
    features are that many times longer than they are wide, all lying at the
    same sheet-wide angle.

    Args:
        shape: Rows and columns.
        cell: The coarsest lattice spacing, across the fibre.
        octaves: How many halvings to sum.
        rng: The generator the lattice is drawn from.
        stretch: How much longer than wide a fibre is.
        angle: The grain's angle in radians.

    Returns:
        The field, normalised to 0 to 1.
    """
    h, w = shape
    yy = np.arange(h, dtype=F32)[:, None]
    xx = np.arange(w, dtype=F32)[None, :]
    ca, sa = math.cos(angle), math.sin(angle)
    u = (xx * ca + yy * sa) / max(stretch, 1e-3)
    v = yy * ca - xx * sa
    out = np.zeros((h, w), F32)
    amp, total = 1.0, 0.0
    for i in range(octaves):
        out += amp * _value_noise_at(u, v, cell / (2**i), rng)
        total += amp
        amp *= 0.5
    out /= total
    lo, hi = float(out.min()), float(out.max())
    return (out - lo) / max(hi - lo, 1e-6)


def _box1(a: np.ndarray, r: int, axis: int) -> np.ndarray:
    """One box blur pass along one axis."""
    if r < 1:
        return a
    a = np.moveaxis(a, axis, -1)
    n = a.shape[-1]
    pad = np.pad(a, [(0, 0)] * (a.ndim - 1) + [(r + 1, r)], mode="edge")
    cs = np.cumsum(pad, axis=-1, dtype=F32)
    out = (cs[..., 2 * r + 1 :] - cs[..., :n]) / F32(2 * r + 1)
    return np.moveaxis(out, -1, axis)


def blur(a: np.ndarray, sigma: float) -> np.ndarray:
    """Three box passes, which is a Gaussian to the eye and much cheaper."""
    if sigma <= _BLUR_FLOOR:
        return a.astype(F32, copy=False)
    r = max(1, round(sigma * 0.95))
    out = a.astype(F32, copy=True)
    for _ in range(3):
        out = _box1(out, r, 1)
        out = _box1(out, r, 0)
    return out


def edt(mask: np.ndarray) -> np.ndarray:
    """Chamfer distance in pixels to the nearest True cell."""
    inf = F32(1e6)
    d = np.where(mask, F32(0), inf).astype(F32)
    if not mask.any():
        return d
    h, w = d.shape
    idx = np.arange(w, dtype=F32)
    dd, one = F32(1.41421356), F32(1.0)
    for r in range(h):
        row = d[r].copy()
        if r:
            p = d[r - 1]
            np.minimum(row, p + one, out=row)
            np.minimum(row[:-1], p[1:] + dd, out=row[:-1])
            np.minimum(row[1:], p[:-1] + dd, out=row[1:])
        np.minimum(row, np.minimum.accumulate(row - idx) + idx, out=row)
        d[r] = row
    for r in range(h - 1, -1, -1):
        row = d[r].copy()
        if r < h - 1:
            p = d[r + 1]
            np.minimum(row, p + one, out=row)
            np.minimum(row[:-1], p[1:] + dd, out=row[:-1])
            np.minimum(row[1:], p[:-1] + dd, out=row[1:])
        rev = row[::-1].copy()
        np.minimum(rev, np.minimum.accumulate(rev - idx) + idx, out=rev)
        d[r] = rev[::-1]
    return d


def smoothstep(x: np.ndarray, w: float) -> np.ndarray:
    """A soft step of width `w` about zero."""
    t = np.clip(x / w + 0.5, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def fill_holes(mask: np.ndarray, step: int = 6) -> np.ndarray:
    """Fill anything the outside cannot reach: the inside of a loop is land.

    Done on a coarse copy, because the flood is a propagation and the answer is
    a shape, not a pixel.

    Args:
        mask: The dilated track.
        step: Coarsening factor for the flood.

    Returns:
        The mask with its enclosed holes filled.
    """
    small = mask[::step, ::step]
    free = ~small
    reach = np.zeros_like(free)
    reach[0, :] |= free[0, :]
    reach[-1, :] |= free[-1, :]
    reach[:, 0] |= free[:, 0]
    reach[:, -1] |= free[:, -1]
    for i in range(4000):
        grown = reach.copy()
        grown[1:, :] |= reach[:-1, :]
        grown[:-1, :] |= reach[1:, :]
        grown[:, 1:] |= reach[:, :-1]
        grown[:, :-1] |= reach[:, 1:]
        grown &= free
        if i % 20 == 0 and np.array_equal(grown, reach):
            break
        if not grown.sum() > reach.sum():
            reach = grown
            break
        reach = grown
    holes = free & ~reach
    if not holes.any():
        return mask
    big = np.repeat(np.repeat(holes, step, 0), step, 1)[: mask.shape[0], : mask.shape[1]]
    if big.shape != mask.shape:
        pad = np.zeros_like(mask)
        pad[: big.shape[0], : big.shape[1]] = big
        big = pad
    return mask | big
