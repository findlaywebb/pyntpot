"""The tip: the bristle fields a stamp samples across and along a stroke.

Key names: `_tip_band`, bandlimiting the tip's weights; `_tip_drift`, each bristle's drift
phase; `_unfold`, scaling a drift back until the tip stops crossing itself; `_fbm1`, fractal
noise along a stroke with no period; `_spread`, carrying a per-bristle field onto the
sampled tip; `_smooth_path`, rounding a path's corners to the brush's width.

It stamps nothing and builds no brush. Every random draw takes the generator it is handed,
so the order the caller draws in is the pattern.

Invariants: no field here has a period; the smoothed path keeps its two ends.
"""

import numpy as np

from pyntpot.ink.brush import Brush
from pyntpot.ink.noise import F32

#: Fewest samples across a tip that can be smoothed.
_MIN_TIP = 3
#: Fewest samples across a tip that has a neighbour to cross.
_MIN_PAIR = 2


def _tip_band(w: np.ndarray, sigma: float) -> np.ndarray:
    """Bandlimit one stamp's weights across the tip.

    A treatment names its bristle count once, so a tip is the same number of
    logical bristles whether the mark is 3 render pixels wide or 17. On a
    narrow mark that puts most of the tip's structure past what the plate can
    carry, and what lands is an alias of it: hard-edged rails at about the
    plate's Nyquist, running the whole length of the stroke because the tip's
    weights do not change along it. Smoothing across the tip is the honest fix
    and not a blur of the mark: the deposit positions are untouched, so the
    mark keeps its width and its edge, and only the detail no pixel could have
    shown is graded away.

    Three box passes, which is a Gaussian to the eye, with the ends held by
    edge padding so the outermost bristles are not pulled inward.

    Args:
        w: The weights, `(samples along the stroke, samples across the tip)`.
        sigma: The smoothing, in samples across the tip.

    Returns:
        The smoothed weights, or `w` itself when the tip is already narrower
        than the smoothing would be.
    """
    r = round(sigma * 0.95)
    if r < 1 or w.shape[1] < _MIN_TIP:
        return w
    r = min(r, (w.shape[1] - 1) // 2)
    if r < 1:
        return w
    out = w
    for _ in range(3):
        pad = np.pad(out, ((0, 0), (r, r)), mode="edge")
        cs = np.cumsum(pad, axis=1, dtype=F32)
        cs = np.concatenate([np.zeros((len(out), 1), F32), cs], axis=1)
        out = (cs[:, 2 * r + 1 :] - cs[:, : out.shape[1]]) / F32(2 * r + 1)
    return out.astype(F32)


def _tip_drift(m: int, b: Brush, rng: np.random.Generator) -> np.ndarray:
    """Each bristle's sideways drift, as a quadrature pair per bristle.

    A bristle wanders sideways as the stroke goes on, and every bristle used to
    be given its own phase, drawn independently of the one beside it. On a
    narrow mark that is not a brush: the drift is wider than the gap between
    two bristles, so neighbours cross each other, the tip collapses into a few
    coincident filaments with bare paper between them, and the gaps run the
    whole length of the stroke because the phases do not change along it.

    Smoothing the drift across the tip is what makes it a tip again. The pair
    is renormalised afterwards, so each bristle still drifts by exactly the
    brush's own amplitude and only the phase is shared.

    Args:
        m: Logical bristles across the tip.
        b: The brush, for how much of the tip a drift is shared over.
        rng: The generator the phases are drawn from.

    Returns:
        `(2, m)`, the cosine and sine of each bristle's drift phase.
    """
    q = rng.normal(size=(2, m)).astype(F32)
    q = _tip_band(q, b.coherence * m)
    return q / np.maximum(np.hypot(q[0], q[1]), F32(1e-6))


def _unfold(
    off: np.ndarray, base: np.ndarray, jitter: np.ndarray, keep: float = 0.25
) -> np.ndarray:
    """Scale a drift back until the tip stops crossing itself.

    Even a shared drift can close the gap between two bristles where the tip
    is at its narrowest, and a closed gap is a filament with a hole beside it.
    The whole stroke's drift is scaled by one number rather than clipped per
    sample, so the mark keeps its wander and only loses the amplitude that
    would have folded it.

    Args:
        off: The offsets across the tip, `(samples, tip)`.
        base: The same without the drift.
        jitter: The drift alone.
        keep: The share of the nominal bristle spacing that has to survive.

    Returns:
        The offsets, with the drift scaled back if it had to be.
    """
    if off.shape[1] < _MIN_PAIR:
        return off
    dbase = np.diff(base, axis=1)
    djit = np.diff(jitter, axis=1)
    close = djit < 0
    if not close.any():
        return off
    room = (dbase * F32(1.0 - keep))[close] / -djit[close]
    k = float(room.min())
    if k >= 1.0:
        return off
    return base + jitter * F32(k)


def _fbm1(
    t: np.ndarray, cell: float, b: Brush, rng: np.random.Generator, rows: int = 1
) -> np.ndarray:
    """Fractal noise along a stroke, with no period in it, in about -1 to 1.

    The wanders in a stroke were sines, so a long mark repeated itself at 2 pi
    times whatever cell each one was given. This is the same feature size drawn
    from a lattice instead: the values are random, the interpolation is smooth,
    and there is nothing for the eye to lock onto. `rows` independent copies
    come out of one call, which is how each bristle gets its own drift without
    a Python loop over the tip.

    The output is normalised to a sine's own spread, so swapping one for the
    other changes what repeats and not how hard the brush is worked.

    Source: `value-noise` in docs/explanation/references.md.
    Source: `fbm` in docs/explanation/references.md.

    Args:
        t: Arc length along the stroke, in render pixels.
        cell: The coarsest lattice spacing, in the same units.
        b: The brush, for the octave count and the lacunarity.
        rng: The generator the lattice is drawn from.
        rows: How many independent fields to draw.

    Returns:
        The field, `(len(t), rows)`.
    """
    out = np.zeros((len(t), rows), F32)
    span = max(float(t[-1] - t[0]), 1.0)
    amp, total = 1.0, 0.0
    for i in range(b.org_oct):
        c = max(cell / (b.org_lac**i), 1.5)
        n = int(span / c) + 3
        g = rng.random((n, rows)).astype(F32) * F32(2.0) - F32(1.0)
        u = (t - t[0]) / c
        i0 = np.clip(np.floor(u).astype(np.int32), 0, n - 2)
        f = (u - i0).astype(F32)
        f = (f * f * (3 - 2 * f))[:, None]
        out += F32(amp) * (g[i0] + (g[i0 + 1] - g[i0]) * f)
        total += amp
        amp *= 0.5
    out /= F32(max(total, 1e-6))
    # A sine's standard deviation is 0.707, and the caller's amplitudes were
    # tuned against one. The floor keeps a short stroke, whose own spread is not
    # yet the field's, from being amplified into a swing it never had.
    sd = float(out.std())
    return np.clip(out * F32(0.707 / max(sd, 0.30)), -1.6, 1.6)


def _spread(vals: np.ndarray, u_log: np.ndarray, u: np.ndarray) -> np.ndarray:
    """Resample a per-logical-bristle field across the sampled tip.

    The tip is a handful of logical bristles, then sampled across at sub-pixel
    spacing. A field drawn per logical bristle has to be carried over to that
    sampling the same way the bristle weights are, or the drift would step from
    one bristle to the next instead of running continuously across the mark.

    Args:
        vals: The field, `(samples, logical bristles)`.
        u_log: The logical bristles' positions across the tip, ascending.
        u: The sampled positions across the tip.

    Returns:
        The field at `(samples, len(u))`.
    """
    idx = np.clip(np.searchsorted(u_log, u) - 1, 0, len(u_log) - 2)
    span = u_log[idx + 1] - u_log[idx]
    f = ((u - u_log[idx]) / np.where(span == 0, 1.0, span)).astype(F32)
    return vals[:, idx] * (1.0 - f) + vals[:, idx + 1] * f


def _smooth_path(
    x: np.ndarray, y: np.ndarray, radius: float, step: float
) -> tuple[np.ndarray, np.ndarray]:
    """Round a polyline's corners to a brush's own width.

    A generalised track turns 82 degrees at the 95th percentile of its
    vertices. A tip stamped straight through a corner like that folds over
    itself: the normal swings through the turn in a couple of samples, the far
    side of the tip runs backwards, and what lands is a bead. No brush draws a
    corner tighter than it is wide, so the path is smoothed to that radius
    before anything is stamped along it.

    Two box passes, which is a quadratic kernel: enough to take the cusp off
    without pulling a long straight off its line. The ends are held by edge
    padding, so a mark still starts and finishes where the way does.

    Args:
        x: Column coordinate per sample, in render pixels.
        y: Row coordinate per sample.
        radius: The corner radius, in render pixels.
        step: The spacing of the samples, in render pixels.

    Returns:
        The smoothed coordinates.
    """
    r = int(min(max(round(radius / max(step, 1e-3)), 1), max(len(x) // 3, 1)))
    for _ in range(2):
        for arr in (x, y):
            pad = np.pad(arr, (r, r), mode="edge")
            cs = np.cumsum(np.concatenate([[F32(0)], pad]), dtype=F32)
            arr[:] = (cs[2 * r + 1 :] - cs[: len(arr)]) / F32(2 * r + 1)
    return x, y
