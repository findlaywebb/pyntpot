"""The deposit: what each sample of a stroke carries, and laying it into the accumulators.

Key names: `weights`, the ink each sample deposits; `channels`, those weights for the ink, the
reservoir and the break-texture accumulators; `deposit`, the bilinear splat into them; `pool`,
the blot where a nib touches down.

It draws no random numbers and builds no path: it reads the `Lay` that `pyntpot.ink.stamp`
has laid out. It does not saturate or gate the accumulator (`pyntpot.ink.pad`).

Invariants: the reservoir and break channels exist only when the caller's `aux` carries the
matching accumulator; a brush off the reservoir sharing an accumulator with one on it reads
as full, and one off the directional break lays half its weight into the break channel.
"""

import numpy as np

from pyntpot.ink.brush import Brush
from pyntpot.ink.noise import F32
from pyntpot.ink.stroke import Lay

#: Fewest samples across a tip for the strip of tip each one stands on.
_MIN_STRIP = 2
_TAU = 6.283


def weights(lay: Lay, lane: np.ndarray, b: Brush) -> np.ndarray:
    """The ink each sample deposits.

    Ink per stamp is normalised against the sampling, so the darkness numbers
    mean the same thing whatever the step and the profile spacing are set to.
    `unit` is in there because what the accumulator holds is a thickness and
    not a count: on a grid twice as fine the same mark is spread across twice
    as many pixels of tip, and without the factor it comes out half as dark.
    """
    smp, off = lay.smp, lay.off
    norm = (b.step / 0.55) * (lay.tip.m / smp.m_hi) * b.unit
    wgt = (smp.prof[None, :] * lane * lay.ink.press[:, None] * b.darkness * norm).astype(F32)
    if b.coherence > 0 and smp.m_hi > _MIN_STRIP:
        # Each sample carries the strip of tip it actually stands on, not an
        # equal share of it. Once the bristles drift the samples are no longer
        # evenly spaced, and an equal share per sample turns every bunch into a
        # dark filament and every spread into a light one, which is the rest of
        # the streaking after the fold is gone. The strips sum to about the
        # tip's own width, so the mark carries about the ink equal shares would.
        span = np.empty_like(off)
        span[:, 1:-1] = (off[:, 2:] - off[:, :-2]) * F32(0.5)
        span[:, 0] = off[:, 1] - off[:, 0]
        span[:, -1] = off[:, -1] - off[:, -2]
        wgt = wgt * (span * F32(smp.m_hi - 1) / np.maximum(lay.ink.width[:, None], 1e-6))
    if lay.ink.spent is not None:
        # And it lightens with it, by about half as much again: what the eye
        # reads on a pen line is the width, not the black.
        wgt = (wgt * (1.0 - 0.5 * b.pen_thin * lay.ink.spent)[:, None]).astype(F32)
    return wgt


def spend(lay: Lay, wgt: np.ndarray, b: Brush) -> tuple[np.ndarray, np.ndarray]:
    """The weights after the reservoir, and what the reservoir held under them.

    Ink is spent with the distance travelled, weighted by pressure, so pressing
    harder spends it faster; each bristle falls at the same rate from its own
    starting load. `dip_px` is the reload: the seam it leaves is what makes a
    long line look drawn.

    Source: `ink-reservoir` in docs/explanation/references.md.
    """
    phase = np.mod(np.cumsum(lay.ink.press) * b.step, b.dip_px)[:, None]
    res0 = lay.smp.res0
    assert res0 is not None
    res = np.clip(
        b.res_floor + (1.0 - b.res_floor) * res0[None, :] * np.exp(-phase / b.run_px), 0.0, 1.3
    ).astype(F32)
    wgt = (wgt * (b.knee + (1.0 - b.knee) * res)).astype(F32)
    return wgt, (wgt * res).astype(F32)


def break_texture(lay: Lay, wgt: np.ndarray, b: Brush) -> np.ndarray:
    """The break texture, in the stroke's own frame.

    It runs `dir_elong` times longer along the mark than across it, so a dry
    brush leaves scratches running with the line rather than blotches sitting
    on it. Clipped rather than scaled, so the texture keeps its flats: the
    splat averages it once and the gate would otherwise read a grey mush.
    """
    dir_ph = lay.tip.dir_ph
    assert dir_ph is not None
    kx = F32(_TAU / max(b.dir_cell * b.dir_elong, 1.0))
    ky = F32(_TAU / max(b.dir_cell, 1.0))
    sl = lay.tr.t[:, None] * kx
    ul = lay.off * ky
    tex_d = (
        0.50 * np.sin(sl + ul * 0.85 + dir_ph[0])
        + 0.30 * np.sin(sl * 2.3 - ul * 1.7 + dir_ph[1])
        + 0.20 * np.sin(sl * 0.55 + ul * 0.4 + dir_ph[2])
    )
    return (wgt * np.clip(0.5 + 0.85 * tex_d, 0.0, 1.0)).astype(F32)


def channels(
    lay: Lay, wgt: np.ndarray, aux: dict[str, np.ndarray] | None, b: Brush
) -> tuple[np.ndarray, np.ndarray | None, np.ndarray | None]:
    """The ink, the reservoir and the break texture, as the weights each deposits.

    Returns:
        The ink's weights, and those for the `res` and `tooth` accumulators,
        each None when the brush has no such accumulator to fill.
    """
    wgt_r = wgt_t = None
    if aux is not None and "res" in aux and not b.starve:
        # A brush sharing an accumulator with one that is on the reservoir but
        # not on it itself reads as full, never as empty.
        wgt_r = wgt
    if aux is not None and "tooth" in aux and not b.dir_dry:
        wgt_t = (wgt * F32(0.5)).astype(F32)
    if b.starve and aux is not None:
        wgt, wgt_r = spend(lay, wgt, b)
    if b.dir_dry and aux is not None:
        wgt_t = break_texture(lay, wgt, b)
    return wgt, wgt_r, wgt_t


def deposit(
    acc: np.ndarray,
    aux: dict[str, np.ndarray] | None,
    pos: tuple[np.ndarray, np.ndarray],
    wgt: np.ndarray,
    wgt_r: np.ndarray | None,
    wgt_t: np.ndarray | None,
) -> None:
    """Deposit the weights bilinearly.

    Rounding to the nearest pixel instead would put steps and stair-edges in
    the mark. A sample off the accumulator lands on its nearest edge pixel.
    """
    h, w = acc.shape
    px, py = pos
    fx0 = np.floor(px)
    fy0 = np.floor(py)
    ax = (px - fx0).astype(F32)
    ay = (py - fy0).astype(F32)
    ix0 = fx0.astype(np.int32)
    iy0 = fy0.astype(np.int32)
    for dy in (0, 1):
        wy = ay if dy else (1.0 - ay)
        iy = np.clip(iy0 + dy, 0, h - 1)
        for dx in (0, 1):
            wx = ax if dx else (1.0 - ax)
            ix = np.clip(ix0 + dx, 0, w - 1)
            at = (iy.ravel(), ix.ravel())
            np.add.at(acc, at, (wgt * wx * wy).ravel())
            if aux is not None and wgt_r is not None:
                np.add.at(aux["res"], at, (wgt_r * wx * wy).ravel())
            if aux is not None and wgt_t is not None:
                np.add.at(aux["tooth"], at, (wgt_t * wx * wy).ravel())


def pool(acc: np.ndarray, b: Brush, x: float, y: float) -> None:
    """Leave a blot where the stroke starts.

    Tighter and denser than a swelling, so it reads as the first touch rather
    than a bulge in the line.
    """
    h, w = acc.shape
    r = max(b.width * b.pool_radius_frac, 1.2)
    span = int(r * 2)
    yy, xx = np.ogrid[-span : span + 1, -span : span + 1]
    blob = np.exp(-(xx * xx + yy * yy) / (2 * r * r)).astype(F32) * b.pool * b.pool_gain
    cy, cx = round(y), round(x)
    y0, y1 = max(cy - span, 0), min(cy + span + 1, h)
    x0, x1 = max(cx - span, 0), min(cx + span + 1, w)
    if y1 > y0 and x1 > x0:
        acc[y0:y1, x0:x1] += blob[y0 - cy + span : y1 - cy + span, x0 - cx + span : x1 - cx + span]
