"""The wood phase: a texture and a scatter of dabs over the wood's own mask.

Key names: `paint_wood`, which lays the wood's blotchy texture and its dabs among the
trimmed layers. Both cross fade over three printed scales, because a texture's scale
cannot be changed after it is printed; the two sliders, `wood_texture` and
`wood_dabs`, walk between them. `_crossfade` gives the weights across the scales for
one slider.

The texture and the dabs draw from the job's dither generator, the texture first, so
the dither the plates are written with afterwards continues the same sequence. A scale
whose weight is negligible, or a card with no wood, draws nothing and consumes nothing.

It does not decide where the wood is: the cover phase leaves that in the stack's
`wood_mask`.
"""

import numpy as np

from pyntpot.ink.noise import F32, blur, fbm
from pyntpot.ink.sheet import rgb
from pyntpot.maps.painter.job import PaintJob, PlateStack

#: A scale weighted below this is not painted.
_NEGLIGIBLE = 0.002


def _crossfade(value: float, n: int) -> list[float]:
    """Weights across `n` printed scales for a slider at `value` in 0 to 1.

    Each scale's weight falls off with its distance from the slider's position,
    and every weight fades towards zero as `value` falls below 0.25.
    """
    if n <= 1:
        return [max(0.0, min(1.0, value))]
    pos = max(0.0, min(1.0, value)) * (n - 1)
    gate = min(1.0, max(0.0, value) * 4.0)
    return [max(0.0, 1.0 - abs(pos - i)) * gate for i in range(n)]


def _texture(job: PaintJob, stack: PlateStack) -> None:
    """The blotchy texture, one field per printed scale, cross faded."""
    cover = job.style.cover
    rh, rw = job.shape
    blotch_px = max(job.layers.blotch_m / job.mpp, 6.0)
    for weight, (sc, strength) in zip(
        _crossfade(cover.wood_texture, len(cover.wood_tex_scales)),
        zip(cover.wood_tex_scales, cover.wood_tex_strengths, strict=True),
        strict=True,
    ):
        if weight <= _NEGLIGIBLE or not stack.wood_mask.any():
            continue
        field_n = fbm(rh, rw, blotch_px * sc, 3, job.dither_rng)
        dens = np.clip((field_n - 0.40) * 1.7, 0, 1) * stack.wood_mask * strength * weight
        stack.trimmed.append((blur(dens, 2.0), rgb(cover.pigments["wood"]), job.transp("wood")))


def _dabs(job: PaintJob, stack: PlateStack) -> None:
    """The scatter of dabs, one jittered grid per printed spacing, cross faded."""
    cover = job.style.cover
    rh, rw = job.shape
    rng = job.dither_rng
    dab_px = max(job.layers.dab_spacing_m / job.mpp, 26.0)
    for weight, (spacing, strength) in zip(
        _crossfade(cover.wood_dabs, len(cover.dab_spacings)),
        zip(cover.dab_spacings, cover.dab_strengths, strict=True),
        strict=True,
    ):
        if weight <= _NEGLIGIBLE or not stack.wood_mask.any():
            continue
        step = max(int(dab_px * spacing), 8)
        dabs = np.zeros((rh, rw), F32)
        gy, gx = np.meshgrid(
            np.arange(step // 2, rh, step), np.arange(step // 2, rw, step), indexing="ij"
        )
        jy = np.clip((gy + (rng.random(gy.shape) - 0.5) * step * 0.7).astype(np.int32), 0, rh - 1)
        jx = np.clip((gx + (rng.random(gx.shape) - 0.5) * step * 0.7).astype(np.int32), 0, rw - 1)
        keep = stack.wood_mask[jy, jx]
        if not keep.any():
            continue
        dabs[jy[keep], jx[keep]] = 1.0
        dab_r = max(step * 0.17, 4.0)
        dens = np.clip(blur(dabs, dab_r) * (dab_r**2) * 1.5, 0, 1) * stack.wood_mask
        stack.trimmed.append(
            (dens * strength * weight, rgb(cover.pigments["wood"]), job.transp("wood"))
        )


def paint_wood(job: PaintJob, stack: PlateStack) -> None:
    """Lay the wood's texture and its dabs among the trimmed layers."""
    _texture(job, stack)
    _dabs(job, stack)
