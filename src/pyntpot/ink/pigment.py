"""Pigments and compositing: the colours a wash transmits and how a stack of layers is laid.

Key names: `PIGMENTS`, what a full-strength wash of each pigment transmits; `TRANSPARENCY`,
what each shows over black as a share of what it shows over white; `PigmentLayer`, one layer of
the stack; `multiply_plate`, the stack as transmission; `km_rt` and `km_plate`, Kubelka-Munk
glazing; `composite`, the stack over a backing the way `PaperStyle` asks.

It paints no wash and writes no file.

Invariants: multiply ignores a layer's transparency; a layer with no density, or an all-zero
one, is skipped; the result is clipped to 0 to 1.
"""

import numpy as np

from pyntpot.ink.noise import F32
from pyntpot.ink.style import PaperStyle

#: Multiply colours: what a full-strength wash of each pigment transmits. The
#: inks are darker than the washes, because a mark is not a wash.
PIGMENTS = {
    "farmland": "#dfe0b0",
    "meadow": "#cfdfae",
    "orchard": "#d5dda2",
    "scrub": "#c9d5a4",
    "heath": "#e0cda2",
    "sand": "#ecdfbe",
    "rock": "#dcd6c6",
    "wetland": "#bfd2cd",
    "built": "#ddd3c3",
    "works": "#d2cbc0",
    "wood": "#a8c286",
    "pale": "#d5e0b4",
    "water": "#9ec4de",
    "relief": "#c9bda4",
    "rim": "#c2ad91",
}


#: What each pigment shows over black, as a share of what it shows over white.
#: This is the one number Kubelka-Munk glazing needs beyond the hex, and it is
#: where a pigment is recorded as staining or covering: near 0 is a transparent
#: glaze that lets the layer under it through, near 1 is a covering body colour.
#: The wood green and the water blue stain; the relief grey and the built greys
#: sit on the surface. Anything not named here takes `km_transparency`.
TRANSPARENCY = {
    "farmland": 0.10,
    "meadow": 0.09,
    "orchard": 0.09,
    "scrub": 0.08,
    "heath": 0.14,
    "sand": 0.16,
    "rock": 0.22,
    "wetland": 0.08,
    "built": 0.26,
    "works": 0.28,
    "wood": 0.05,
    "pale": 0.12,
    "water": 0.04,
    "relief": 0.30,
    "rim": 0.18,
}


#: One layer of the pigment stack: its density, its pigment over white, and,
#: where the caller knows it, what that pigment shows over black as a share of
#: that. Only Kubelka-Munk glazing reads the third; multiply ignores it.
PigmentLayer = tuple[np.ndarray | None, np.ndarray] | tuple[np.ndarray | None, np.ndarray, float]

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
    x = np.clip(dens, 0.0, 1.0).astype(F32)[..., None]
    bsx = np.clip((b * s).astype(F32)[None, None, :] * x, 0.0, 40.0)
    sh, ch = np.sinh(bsx), np.cosh(bsx)
    af = a.astype(F32)[None, None, :]
    bf = b.astype(F32)[None, None, :]
    c = np.maximum(af * sh + bf * ch, F32(1e-9))
    return sh / c, bf / c


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
    out = base.astype(F32, copy=True)
    for layer in layers:
        dens, pig = layer[0], layer[1]
        if dens is None or not dens.any():
            continue
        t = float(layer[2]) if len(layer) == _WITH_TRANSPARENCY else transparency
        r, tr = km_rt(dens, pig, t)
        out = r + tr * tr * out / np.maximum(1.0 - r * out, 1e-6)
    return np.clip(out, 0.0, 1.0)


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
