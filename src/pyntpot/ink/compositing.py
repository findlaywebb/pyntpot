"""Compositing: how a stack of pigment layers is laid.

Key names: `PigmentLayer`, one layer of the stack; `multiply_plate`, the stack as transmission;
`km_rt` and `km_plate`, Kubelka-Munk glazing; `composite`, the stack over a backing the way
`PaperStyle` asks.

It paints no wash and writes no file.

Invariants: multiply ignores a layer's transparency; a layer with no density, or an all-zero
one, is skipped; the result is clipped to 0 to 1.
"""

import numpy as np

from pyntpot.ink.noise import F32
from pyntpot.ink.style import PaperStyle

PigmentLayer = tuple[np.ndarray | None, np.ndarray] | tuple[np.ndarray | None, np.ndarray, float]
"""One layer of the pigment stack: its density, its pigment over white, and, where the caller knows
it, what that pigment shows over black as a share of that. Only Kubelka-Munk glazing reads the
third; multiply ignores it."""

#: How many members a layer has when it names its own transparency.
_WITH_TRANSPARENCY = 3


def multiply_plate(layers: list[PigmentLayer], h: int, w: int) -> np.ndarray:
    """Stack densities into one white-backed multiply plate.

    Source: `multiply-compositing` in docs/explanation/references.md.
    """
    out = np.ones((h, w, 3), F32)
    for layer in layers:
        dens, pig = layer[0], layer[1]
        if dens is None or not dens.any():
            continue
        out *= 1.0 - dens[..., None] * (1.0 - pig)
    return np.clip(out, 0.0, 1.0)


def km_rt(dens: np.ndarray, pig: np.ndarray, transparency: float) -> tuple[np.ndarray, np.ndarray]:
    """One wash's reflectance and transmittance, per Kubelka-Munk.

    The pigment hex the painter already carries is Rw, what a unit wash of it
    shows over white. The one number this needs beyond that is Rb, what the
    same wash shows over black, which is what says whether the pigment stains
    or covers. K and S follow from the pair, and the painter's own density is
    the layer's thickness.

    The step that is easy to miss is deriving S from Rw and Rb rather than
    picking it: without it the round trip does not return Rw and every wash
    goes black.

    Source: `kubelka-munk` in docs/explanation/references.md.

    Args:
        dens: Layer thickness, the wash's density in 0 to 1.
        pig: The pigment over white, three channels in 0 to 1.
        transparency: Rb over Rw. Near 0 the pigment is a transparent glaze
            that lets the layer under it through; near 1 it covers.

    Returns:
        Reflectance and transmittance, each `dens.shape + (3,)`.
    """
    rw = np.clip(pig, 1e-3, 0.999).astype(np.float64)
    rb = np.clip(rw * float(np.clip(transparency, 1e-3, 0.95)), 1e-4, rw - 1e-4)
    a = 0.5 * (rw + (rb - rw + 1.0) / rb)
    b = np.sqrt(np.maximum(a * a - 1.0, 1e-9))
    z = (b * b - (a - rw) * (a - 1.0)) / (b * (1.0 - rw))
    s = (1.0 / b) * 0.5 * np.log((z + 1.0) / (z - 1.0))
    # a, b and S are three numbers a channel; only the thickness is a plate, so
    # the hyperbolics run in float32 and the plate stays half the size.
    x = np.clip(dens, 0.0, 1.0).astype(F32, copy=False)[..., None]
    bsx = (b * s).astype(F32) * x
    np.clip(bsx, 0.0, 40.0, out=bsx)
    sh, ch = np.sinh(bsx), np.cosh(bsx)
    bf = b.astype(F32)
    c = a.astype(F32) * sh
    c += np.multiply(bf, ch, out=ch)
    np.maximum(c, F32(1e-9), out=c)
    np.divide(sh, c, out=sh)
    return sh, np.divide(bf, c, out=c)


def km_plate(
    layers: list[PigmentLayer], base: np.ndarray, transparency: float = 0.06
) -> np.ndarray:
    """Glaze the layers optically over a backing, bottom layer first.

    Multiply is transmission with no scattering, so two washes crossing lose
    their chroma and go grey. Kubelka-Munk keeps the scattering, so a green
    over a blue is still green over blue where they meet.

    Source: `kubelka-munk` in docs/explanation/references.md.

    Args:
        layers: Density, pigment, and optionally the pigment's transparency.
        base: What the stack is laid over, `(h, w, 3)`.
        transparency: The default, for a layer that does not name one.

    Returns:
        The glazed plate, in 0 to 1.
    """
    out = base.astype(F32, order="C", copy=True)
    pixels = out.reshape(-1, 3)
    for layer in layers:
        dens, pig = layer[0], layer[1]
        if dens is None:
            continue
        if dens.shape != out.shape[:-1]:
            raise ValueError(f"a layer of shape {dens.shape} on a base of {out.shape}")
        # A pixel with no density is left exactly as it was (r is 0, tr is 1),
        # so only the painted pixels are glazed.
        painted = np.flatnonzero(dens)
        if painted.size == 0:
            continue
        t = float(layer[2]) if len(layer) == _WITH_TRANSPARENCY else transparency
        r, tr = km_rt(dens.ravel()[painted], pig, t)
        under = pixels[painted]
        glazed = np.multiply(tr, tr, out=tr)
        glazed *= under
        np.multiply(r, under, out=under)
        np.subtract(1.0, under, out=under)
        np.maximum(under, 1e-6, out=under)
        glazed /= under
        glazed += r
        pixels[painted] = glazed
    return np.clip(out, 0.0, 1.0, out=out)


def composite(layers: list[PigmentLayer], base: np.ndarray, style: PaperStyle) -> np.ndarray:
    """Stack one set of layers over a backing, the way the style asks.

    Source: `multiply-compositing` in docs/explanation/references.md.

    Args:
        layers: Density, pigment, and optionally a transparency.
        base: What the stack is laid over, `(h, w, 3)`.
        style: The paper group, for `km_glazing` and `km_transparency`.

    Returns:
        The composited plate, the shape of `base`, clipped to 0 to 1.
    """
    if style.km_glazing:
        return km_plate(layers, base, style.km_transparency)
    h, w = base.shape[:2]
    return np.clip(base * multiply_plate(layers, h, w), 0.0, 1.0)
