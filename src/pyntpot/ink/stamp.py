"""The stamp: one stroke's bristles laid into an ink accumulator.

Key name: `stamp`, which walks a path in render pixels, draws a tip of logical bristles from
the generator, and deposits every bristle's ink bilinearly into the accumulator. It is split
into named steps, each a stage of a stroke: the path (`_trace`), the pressure and width along
it (`_pressure`, `_width`), the wander (`_wobble`), the tip (`_draw_tip`, `_sample_tip`),
where each bristle lands (`_offsets`) and what each carries (`_lanes`). What the weights are
and how they are deposited is `pyntpot.ink.deposit`.

It does not turn an accumulator into density (`pyntpot.ink.pad`) and builds no brush
(`pyntpot.ink.brush`).

Invariants: the generator is drawn from in a fixed order (phase, pressure lattice, wander
lattice, the tip; the lattices only for an organic brush), so one seed gives one stroke; a
path shorter than 2.5 pixels stamps nothing.
"""

import numpy as np

from pyntpot.ink.brush import Brush
from pyntpot.ink.deposit import channels, deposit, pool, weights
from pyntpot.ink.noise import F32
from pyntpot.ink.stroke import Lay, Mark, Sampled, Tip, Trace
from pyntpot.ink.tip import _fbm1, _smooth_path, _spread, _tip_band, _tip_drift, _unfold

#: Shortest path, in render pixels, that is worth a stamp.
_MIN_PATH_PX = 2.5
#: Most samples across a tip.
_MAX_TIP_SAMPLES = 512
#: Fewest points on a path.
_MIN_POINTS = 2
#: Normals shorter than this are left unscaled.
_MIN_NORMAL = 1e-5
_TAU = 6.283


def _trace(pts: np.ndarray, b: Brush) -> Trace | None:
    """Resample a path evenly and take its normals, or None when it is too short."""
    if len(pts) < _MIN_POINTS:
        return None
    d = np.diff(pts, axis=0)
    seg = np.hypot(d[:, 0], d[:, 1])
    total = float(seg.sum())
    if total < _MIN_PATH_PX:
        return None
    cum = np.concatenate([[0.0], np.cumsum(seg)])
    n = max(int(total / b.step) + 2, 3)
    t = np.linspace(0.0, total, n).astype(F32)
    x = np.interp(t, cum, pts[:, 0]).astype(F32)
    y = np.interp(t, cum, pts[:, 1]).astype(F32)
    if b.smooth > 0:
        # Before the tangent, because the fold at a cusp is in the normal.
        x, y = _smooth_path(x, y, b.smooth, total / max(n - 1, 1))
    tx = np.gradient(x)
    ty = np.gradient(y)
    ln = np.hypot(tx, ty)
    ln[ln < _MIN_NORMAL] = 1.0
    nx, ny = (-ty / ln).astype(F32), (tx / ln).astype(F32)
    return Trace(x, y, nx, ny, t, total)


def _pressure(tr: Trace, b: Brush, ph: float, rng: np.random.Generator) -> np.ndarray:
    """Pressure along the stroke: slow variation, set down loaded, lifted to a point."""
    t = tr.t
    if b.organic:
        # The sine pressure comes back every 2 pi press cells; the lattice does not.
        press = 1.0 + b.press * _fbm1(t, _TAU * b.press_cell * b.org_mult, b, rng)[:, 0]
    else:
        press = 1.0 + b.press * (
            np.sin(ph + t / b.press_cell) * 0.6 + np.sin(ph * 1.7 + t / (b.press_cell * 0.36)) * 0.4
        )
    # Set down loaded, lift to a point. Both ends taper by pressure, never by
    # opacity, and the lift is capped at a third of the stroke's own length.
    lift_px = max(min(b.lift, tr.total * 0.34), 1.0)
    ends = np.clip(np.minimum(t, tr.total - t) / lift_px, 0.0, 1.0) ** 0.7
    # The set-down is a nib touching the paper: a lot of ink in the first few
    # stamps, gone within about a width of travel, not a swelling.
    load_px = b.load_px if b.load_px > 0 else max(b.width * 0.85, 2.0)
    return press * ends * (1.0 + b.load * np.exp(-t / load_px))


def _width(tr: Trace, b: Brush, press: np.ndarray, wprof: np.ndarray | None) -> Mark:
    """The mark's width along the stroke, from pressure, a width profile and a nib's run."""
    width = b.width * (0.62 + 0.38 * press)
    if wprof is not None and len(wprof) > 1:
        width = width * np.interp(
            tr.t, np.linspace(0.0, tr.total, len(wprof)), np.asarray(wprof, F32)
        )
    spent = None
    if b.pen_starve:
        # A nib does not break, it runs down: the line thins over a long run and
        # comes back full at the reload. The thinning is put on the width rather
        # than on the pressure because a pen's ink is saturated long before the
        # accumulator is, so darkness alone would not show.
        spent = 1.0 - np.exp(-np.mod(np.cumsum(press) * b.step, b.dip_px) / b.run_px)
        nib = (1.0 - b.pen_thin * spent).astype(F32)
        width = width * nib
    return Mark(press, width, spent)


def _wobble(tr: Trace, b: Brush, ph: float, rng: np.random.Generator) -> Trace:
    """The path moved sideways by the line's own slow wander."""
    t = tr.t
    if b.organic:
        # The sine wander comes back every 210 render pixels at the default step,
        # which on a road drawn end to end is the thing the eye picks out first.
        wob = b.wobble * _fbm1(t, _TAU * 33.45 * b.unit * b.org_mult, b, rng)[:, 0]
    else:
        wob = b.wobble * (
            np.sin(ph * 2.3 + t / (46.0 * b.step / 0.55)) * 0.6
            + np.sin(ph * 3.1 + t / (15.0 * b.step / 0.55)) * 0.4
        )
    return Trace(tr.x + tr.nx * wob, tr.y + tr.ny * wob, tr.nx, tr.ny, t, tr.total)


def _draw_tip(t: np.ndarray, b: Brush, rng: np.random.Generator) -> Tip:
    """Draw the tip as a handful of logical bristles.

    This is the pattern, not the sampling. A real brush has two or three heavy
    tines and some fine ones, so a low-frequency profile clumps them rather
    than leaving a comb.
    """
    m = max(b.bristles, 2)
    u_log = np.linspace(-1.0, 1.0, m)
    keep = (rng.random(m) > b.gap).astype(np.float64)
    clump = 0.55 + 0.45 * np.sin(
        float(rng.random()) * _TAU + u_log * float(rng.uniform(2.2, 5.5)) * 3.14
    )
    tex = b.texture
    bw_log = (rng.random(m) * 0.55 + 0.62) * keep * ((1.0 - tex) + tex * clump)
    drift_log = _tip_drift(m, b, rng)
    fp_log = rng.random(m) * _TAU
    fq_log = rng.random(m) * 0.6 + 0.7
    # Each bristle sets off with its own load, and the fat ones carry more, so
    # the light bristles give out first as the brush runs down.
    res_log = (0.55 + 0.9 * rng.random(m)) * (0.5 + 0.5 * bw_log) if b.starve else None
    dir_ph = rng.random(3) * _TAU if b.dir_dry else None
    jit_log = along_log = None
    if b.organic:
        jit_log, along_log = _organic_fields(t, m, b, rng)
    return Tip(m, u_log, bw_log, drift_log, fp_log, fq_log, res_log, dir_ph, jit_log, along_log)


def _organic_fields(
    t: np.ndarray, m: int, b: Brush, rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """The lattice drift and break per bristle, in place of the two sines.

    The sine drift sideways is one wavelength shared by the whole tip, so the
    streaks breathe together, and the sine break's per-bristle frequencies beat
    against each other into a long repeat. Drawn per logical bristle and
    spread across the tip by the caller.
    """
    jit_log = _fbm1(t, _TAU * 62.0 * b.unit * b.org_mult, b, rng, m)
    if b.coherence > 0:
        # The same sharing as the sine's phases, and for the same reason:
        # each bristle's drift is its own field, and neighbours can be driven
        # apart far enough to cross. Rescaled to the spread it had, because
        # smoothing independent fields together flattens them and the point
        # is who drifts with whom, not how far.
        was = float(jit_log.std())
        jit_log = _tip_band(jit_log, b.coherence * m)
        jit_log = jit_log * F32(was / max(float(jit_log.std()), 1e-6))
    along_log = _fbm1(t, _TAU * 24.0 * b.unit * b.org_mult, b, rng, m)
    return jit_log, along_log


def _sample_tip(tip: Tip, b: Brush, width: np.ndarray) -> Sampled:
    """Sample the tip across at sub-pixel spacing.

    A wide brush is then a continuous edge rather than a row of separate
    lines, and no step shows. It is sampled across the tip's own width plus the
    room the drift needs: two bristles a nominal spacing apart can be driven
    twice that apart, and a sampling that only covers the nominal width leaves
    the stretched places with gaps between deposits, which is a light lane by a
    different route. The drift is only counted when it is coherent, so a tip
    with no coherence is sampled across its nominal width alone.
    """
    mean_w = float(np.mean(width))
    reach = mean_w + 4.0 * b.jitter if b.coherence > 0 else mean_w
    m_hi = int(min(max(tip.m, reach / max(b.profile_px, 0.1) + 2), _MAX_TIP_SAMPLES))
    u = np.linspace(-1.0, 1.0, m_hi).astype(F32)
    bw = np.interp(u, tip.u_log, tip.bw_log).astype(F32)
    dc = np.interp(u, tip.u_log, tip.drift_log[0]).astype(F32)
    ds = np.interp(u, tip.u_log, tip.drift_log[1]).astype(F32)
    fp = np.interp(u, tip.u_log, tip.fp_log).astype(F32)
    fq = np.interp(u, tip.u_log, tip.fq_log).astype(F32)
    res0 = np.interp(u, tip.u_log, tip.res_log).astype(F32) if tip.res_log is not None else None
    prof = ((1.0 - 0.32 * np.abs(u)) ** 1.3).astype(F32)
    if b.solid > 0:
        # A loaded pen or fine liner: a flat core the bristles sit on top of.
        prof = prof * (1.0 - b.solid) + b.solid * np.clip((1.0 - np.abs(u)) * 6.0, 0.0, 1.0)
        bw = bw * (1.0 - b.solid) + b.solid
    return Sampled(m_hi, u, bw, dc, ds, fp, fq, res0, prof, mean_w)


def _offsets(tr: Trace, ink: Mark, tip: Tip, smp: Sampled, b: Brush) -> np.ndarray:
    """Where each sample across the tip sits, sideways of the path, at every stamp."""
    if tip.jit_log is not None:
        jitter = b.jitter * _spread(tip.jit_log, tip.u_log, smp.u)
    else:
        # The sine drift, written as a quadrature pair so the phase can be
        # shared across the tip: `dc` and `ds` are the cosine and sine of one
        # bristle's phase and square to 1, so the amplitude is the brush's own
        # and the sharing decides only who drifts with whom.
        phase = (tr.t / (62.0 * b.unit)).astype(F32)
        jitter = b.jitter * (
            smp.dc[None, :] * np.sin(phase)[:, None] + smp.ds[None, :] * np.cos(phase)[:, None]
        )
    base = smp.u[None, :] * ink.width[:, None] * F32(0.5)
    off = base + jitter
    if b.coherence > 0:
        off = _unfold(off, base, jitter)
    return off


def _lanes(tr: Trace, tip: Tip, smp: Sampled, b: Brush) -> np.ndarray:
    """The tip's lanes: what the bristles weigh and where the brush is breaking.

    Each bristle carries and loses ink as it goes, and on a dry brush it lifts
    off the paper entirely for a stretch: that is where the mark breaks. This is
    everything that varies across the mark apart from its own shape.
    """
    if tip.along_log is not None:
        along = 0.5 + 0.5 * _spread(tip.along_log, tip.u_log, smp.u)
    else:
        along = 0.5 + 0.5 * np.sin(
            smp.fp[None, :] + tr.t[:, None] * smp.fq[None, :] / (24.0 * b.unit)
        )
    cut = b.dry * 0.5
    along = np.clip((along - cut) / max(1.0 - cut, 1e-3), 0.0, 1.0)
    along = (1.0 - b.texture) + b.texture * along
    lane = (smp.bw[None, :] * along).astype(F32)
    if b.band_px > 0 and smp.mean_w > 0:
        # Held to what a mark this wide can show, so the bristle weights, the
        # dropped lanes and the break texture are all bandlimited together. The
        # stroke's own length is untouched, and so are the deposit positions:
        # the mark keeps its width and its edge.
        lane = _tip_band(lane, b.band_px * b.unit * smp.m_hi / smp.mean_w)
    if b.contrast != 1.0:
        # How hard the lanes are, about the tip's own mean, so the knob moves
        # the streaking and not the mark's profile or how much ink it carries.
        mid = lane.mean(axis=1, keepdims=True)
        lane = np.maximum(mid + (lane - mid) * b.contrast, F32(0.0))
    return lane


def stamp(
    acc: np.ndarray,
    pts: np.ndarray,
    b: Brush,
    rng: np.random.Generator,
    aux: dict[str, np.ndarray] | None = None,
    wprof: np.ndarray | None = None,
) -> None:
    """Stamp one stroke's bristles into an ink accumulator.

    Source: `bristle-brush` in docs/explanation/references.md.

    Args:
        acc: The accumulator, added to in place.
        pts: The path in render pixels.
        b: The brush.
        rng: The generator the bristle pattern is drawn from.
        aux: The accumulators from `ink_aux`, added to in place alongside the
            ink. None when neither reservoir nor directional break is on.
        wprof: A width multiplier along the stroke, sampled evenly from its
            start to its end and interpolated onto the stamps. This is what a
            broad nib is: the mark thickens and thins with the angle between
            the stroke and the nib, and there is no other way to say so,
            because pressure is generated inside here and width follows it.
    """
    tr = _trace(pts, b)
    if tr is None:
        return
    ph = float(rng.random()) * _TAU
    ink = _width(tr, b, _pressure(tr, b, ph, rng), wprof)
    tr = _wobble(tr, b, ph, rng)
    tip = _draw_tip(tr.t, b, rng)
    smp = _sample_tip(tip, b, ink.width)
    lay = Lay(tr, ink, tip, smp, _offsets(tr, ink, tip, smp, b))
    wgt, wgt_r, wgt_t = channels(lay, weights(lay, _lanes(tr, tip, smp, b), b), aux, b)
    px = tr.x[:, None] + tr.nx[:, None] * lay.off
    py = tr.y[:, None] + tr.ny[:, None] * lay.off
    deposit(acc, aux, (px, py), wgt, wgt_r, wgt_t)
    if b.pool > 0:
        pool(acc, b, float(tr.x[0]), float(tr.y[0]))
