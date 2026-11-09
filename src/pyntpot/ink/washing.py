"""One wash: the density a coverage mask becomes, and how it is split and modulated.

Key functions: `wash`, one pigment's density from a coverage mask, with an edge pooled
by a rim or a flow term, bleeding into a shared wet area and optionally bloomed
(`ink.bloom`); `flow_edge`, the rim as an outward flow decaying inward;
`separated`, one wash as one pigment or the two it is mixed from; `fluid_modulate`, a
stack of washes modulated by one coarse shallow-water pass (`ink.shallow_water`).

It reads the style group it is handed (`WashStyle`) and nothing else, and it writes no file.

Invariants: every `WashOptions` field from `wet` on is inert when it is not given, so a
caller that sets none of them gets no bleed, flow rim, pit granulation or blooms;
`fluid_modulate` changes the densities in place and returns the same layers.
"""

from dataclasses import dataclass

import numpy as np
from PIL import Image

from pyntpot.ink.bloom import Blooms, bloom
from pyntpot.ink.compositing import PigmentLayer
from pyntpot.ink.noise import F32, blur, chamfer_distance
from pyntpot.ink.shallow_water import shallow_water
from pyntpot.ink.sheet import Sheet, rgb
from pyntpot.ink.style import WashStyle

#: Alpha above this counts as inside the wash.
_INSIDE = 0.5
#: A wash smaller than this many pixels has no rim.
_MIN_AREA = 4
#: A rim whose peak is below this is left unscaled.
_RIM_PEAK = 1e-5
#: A bleed narrower than this many pixels is not made.
_BLEED_FLOOR = 0.4
#: A heavy field with less pigment than this is not separated.
_NO_PIGMENT = 1e-9
#: A coarse cell wetter than this is wet.
_WET_FLOOR = 0.05


@dataclass(frozen=True, kw_only=True)
class Flow:
    """The settings that take the rim from `flow_edge`, named as its parameters are.

    Attributes:
        exp: How fast the width grows with area.
        ref_frac: The reference area, as a share of the canvas.
        frac: The decay length, as a share of the rim's width.
    """

    exp: float
    ref_frac: float
    frac: float


def flow_edge(
    a: np.ndarray, sheet: Sheet, rim_px: float, exp: float, ref_frac: float, frac: float = 0.38
) -> np.ndarray:
    """Edge darkening as an outward flow term, decaying inward from the edge.

    Mask minus blur is symmetric about the geometric edge and one width
    everywhere. Real edge darkening is pigment carried out by evaporation at a
    pinned contact line, so it sits inside the wet boundary and is wider on a
    large wash than on a small one. Coarse noise then breaks it up, because a
    contact line does not pin evenly.

    Source: `edge-darkening` in docs/explanation/references.md.

    Args:
        a: The wash's own alpha, in 0 to 1.
        sheet: The paper's noise fields.
        rim_px: The rim's width at the reference area.
        exp: How fast the width grows with area.
        ref_frac: The reference area, as a share of the canvas.
        frac: The decay length as a share of `rim_px`.

    Returns:
        The rim, in 0 to 1.
    """
    inside = a > _INSIDE
    area = float(inside.sum())
    if area < _MIN_AREA:
        return np.zeros_like(a)
    ref = max(a.size * ref_frac, 1.0)
    width = max(rim_px * frac * (area / ref) ** exp, 0.8)
    d = chamfer_distance(~inside)
    rim = np.exp(-d / F32(width)) * a * (0.6 + 0.8 * sheet.coarse)
    return np.clip(rim, 0.0, 1.0)


@dataclass(frozen=True, kw_only=True, eq=False)
class WashOptions:
    """How one wash looks: its edge, its body, the wet area it shares and its extras.

    Every field from `wet` on is inert when it is not given.

    Attributes:
        wobble: Coarse noise on the edge, in mask units.
        dry: Fine noise on the edge, in mask units.
        rim_px: Width of the pooled edge, in render pixels.
        gran: Granulation, as a share of the body density.
        uneven: Slow variation across the wash.
        tooth: How much the paper's tooth lightens it.
        wet: The shared wet-area field, when there is one. Inside it this wash bleeds into whatever
            is beside it and gives up most of its rim, because a class boundary under water is not
            an edge.
        bleed_px: How far the bleed carries, in render pixels.
        bleed_mix: How much of the bleed is taken at the centre of a wet area.
        rim_drop: How much of the rim the wet area removes.
        gran_gamma: Above 0, granulation follows the paper's own pits at this gamma rather than the
            unrelated `sheet.gran` field.
        flow: To take the rim from `flow_edge` instead.
        blooms: To lay backruns.
    """

    wobble: float = 3.6
    dry: float = 1.8
    rim_px: float = 7.0
    gran: float = 0.26
    uneven: float = 0.22
    tooth: float = 0.34
    wet: np.ndarray | None = None
    bleed_px: float = 5.0
    bleed_mix: float = 0.55
    rim_drop: float = 0.7
    gran_gamma: float = 0.0
    flow: Flow | None = None
    blooms: Blooms | None = None


def wash(
    cover: np.ndarray,
    sheet: Sheet,
    base: float,
    pool: float,
    options: WashOptions | None = None,
) -> np.ndarray:
    """One pigment's density from a coverage mask.

    The edge is the blurred mask thresholded against two noise scales, which is
    cheaper than a signed distance field and, at this resolution, the same
    picture. Pooling is the mask minus its own blur, or `flow_edge` when
    `WashOptions.flow` is given, so pigment sits just inside the edge instead
    of fading out of it.

    Everything from `WashOptions.wet` on is inert when it is not given.

    Source: `granulation` in docs/explanation/references.md.
    Source: `wet-area-bleed` in docs/explanation/references.md.
    Source: `edge-darkening` in docs/explanation/references.md.

    Args:
        cover: Coverage in 0 to 1.
        sheet: The paper's noise fields.
        base: Density of the flat body of the wash.
        pool: Extra density where the pigment pools at the edge.
        options: The wash's edge, body, wet area and extras; the defaults when
            it is not given.

    Returns:
        Density in 0 to 1.
    """
    o = options or WashOptions()
    if not cover.any():
        return np.zeros_like(cover)
    soft = blur(cover, 2.4)
    edge = (o.wobble * (sheet.coarse - 0.5) + o.dry * (sheet.fine - 0.5)) * 0.06
    a = np.clip((soft - 0.5 + edge) * 3.2 + 0.5, 0.0, 1.0)
    if o.flow is not None:
        rim = flow_edge(a, sheet, o.rim_px, o.flow.exp, o.flow.ref_frac, o.flow.frac)
    else:
        rim = np.clip(a - blur(a, o.rim_px), 0.0, 1.0)
    peak = float(rim.max())
    if peak > _RIM_PEAK:
        rim = rim / peak
    if o.wet is not None:
        rim = rim * (1.0 - o.wet * o.rim_drop)
    dens = a * base + rim * pool
    dens *= 1.0 + o.uneven * (sheet.wet - 0.5) * 2.0
    if o.gran_gamma > 0:
        pits = sheet.pits(o.gran_gamma)
        dens *= 1.0 + o.gran * (pits - float(pits.mean())) * 2.4
    else:
        dens *= 1.0 + o.gran * np.clip((sheet.gran - 0.5) * 2.4, -0.7, 1.0)
    dens *= 1.0 - o.tooth * (sheet.paper - 0.5)
    if o.wet is not None and o.bleed_px > _BLEED_FLOOR:
        m_wet = o.wet * o.bleed_mix
        dens = dens * (1.0 - m_wet) + blur(dens, o.bleed_px) * m_wet
    if o.blooms is not None:
        bloom(dens, a, sheet, o.blooms)
    b1 = blur(dens, 1.6)
    b2 = blur(dens, 4.4)
    m = sheet.wet
    lo = np.clip(m * 2.0, 0, 1)
    hi = np.clip(m * 2.0 - 1.0, 0, 1)
    return np.clip(dens * (1 - lo) + b1 * (lo - hi) + b2 * hi, 0.0, 1.0)


def separated(
    dens: np.ndarray,
    key: str,
    pig: np.ndarray,
    transparency: float,
    sheet: Sheet,
    style: WashStyle,
) -> list[PigmentLayer]:
    """One wash as one pigment, or as the two it is really mixed from.

    A tube green is a staining green with a heavier blue-black in it, and the
    two come apart as the wash dries: the heavy one drops into the paper's
    hollows and the light one floats over the tooth. Curtis' pigment
    separation, taken as one extra layer rather than a second solver. The total
    density stays the wash's own, because the heavy field is scaled to sum to
    its share of the wash and that share is taken out of the light one: the flag
    redistributes a wash, it does not add to it.

    The pair only reads as two pigments through `km_glazing`. Under multiply
    the layers still stack, but the two hues average where they overlap, which
    is what glazing keeps apart.

    Source: `pigment-separation` in docs/explanation/references.md.

    Args:
        dens: The wash's density.
        key: The land class, which is what decides whether it separates.
        pig: The pigment over white.
        transparency: What that pigment shows over black, as a share.
        sheet: The paper's noise fields, for the pits the heavy one settles in.
        style: The wash group: whether the pigment separates, and how.

    Returns:
        One layer, or the light one and then the heavy one over it.
    """
    hex2 = style.separation_pigments.get(key) if style.pigment_separation else None
    if hex2 is None or hex2 == "":
        return [(dens, pig, transparency)]
    share = float(np.clip(style.separation_share, 0.0, 0.9))
    heavy = dens * sheet.pits(style.separation_gamma)
    # Scaled against this wash's own pigment rather than against the sheet's
    # mean tooth, so the heavy pigment is exactly the share of the wash it is
    # said to be wherever the wash happens to lie. The pits say where it goes,
    # not how much of it there is.
    total = float(heavy.sum())
    if total < _NO_PIGMENT:
        return [(dens, pig, transparency)]
    heavy = heavy * F32(share * float(dens.sum()) / total)
    return [
        (dens * F32(1.0 - share), pig, transparency),
        (np.clip(heavy, 0.0, 1.0), rgb(hex2), float(style.separation_transparency)),
    ]


def fluid_modulate(
    layers: list[PigmentLayer], wet: np.ndarray, sheet: Sheet, style: WashStyle
) -> list[PigmentLayer]:
    """Modulate a stack of washes by one coarse shallow-water pass.

    The rule this holds to is that the pass modulates the painter and never
    becomes it: the water is run on a grid `fluid_grid` times coarser than the
    plate each way, against the densities the painter has already laid, and
    what comes back multiplies them. A pass that produced nothing leaves the
    plate it was given.

    The densities are modulated in place, so a plate carrying fourteen layers
    needs no second copy of every one.

    Args:
        layers: The washes to modulate. Their densities are changed in place.
        wet: The wet area at plate resolution, in 0 to 1.
        sheet: The paper's noise fields.
        style: The wash group: the fluid pass's grid, steps, amount and seed.

    Returns:
        The same layers, for a caller that would rather read it that way.
    """
    q = max(int(style.fluid_grid), 1)
    h, w = wet.shape
    qh, qw = max(h // q, 8), max(w // q, 8)

    def down(a: np.ndarray) -> np.ndarray:
        """Average `a` over `q` by `q` cells onto the coarse grid."""
        return a[: qh * q, : qw * q].reshape(qh, q, qw, q).mean(axis=(1, 3), dtype=F32)

    wet_q = down(wet)
    if not (wet_q > _WET_FLOOR).any():
        return layers
    total = np.zeros((h, w), F32)
    for layer in layers:
        if layer[0] is not None:
            total += layer[0]
    dep = shallow_water(
        wet_q,
        np.clip(down(total), 0.0, 1.0),
        down(sheet.paper),
        style,
    )
    # Read against its own middle and its own spread inside the wash, not
    # against its maximum: a deposit field piles up hard in a few cells, and
    # scaling by the largest of them would leave every other cell untouched.
    seen = dep[wet_q > _WET_FLOOR]
    lo, mid, hi = (float(v) for v in np.percentile(seen, [10, 50, 90]))
    gain_q = 1.0 + style.fluid_amount * np.clip((dep - mid) / max(hi - lo, 1e-6), -1.5, 1.5)
    # The whole gain is built on the coarse grid, the fade out to dry paper
    # included, and brought back up bilinearly in one step. Anything done at
    # plate resolution here costs more than the pass that earned it: a single
    # blur over 1800 by 1529 is a fifth of the solver.
    gain_q = gain_q * wet_q + (1.0 - wet_q)
    gain = np.asarray(
        Image.fromarray(gain_q.astype(F32), "F").resize((w, h), Image.Resampling.BILINEAR), F32
    )
    for layer in layers:
        if layer[0] is not None:
            np.multiply(layer[0], gain, out=layer[0])
            np.clip(layer[0], 0.0, 1.0, out=layer[0])
    return layers
