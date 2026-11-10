"""Lay one line class's effect stack on an image: the bridge from a theme's pixels to an array's.

Key function: `lay_stack`, which runs a stack's effects in order through the `ink` primitives
(`casing`, `reserve`, `glow`, `shadow`), each effect passed whole. A stack's widths are in display pixels,
so each `*_px` field is multiplied by the render scale first (`dataclasses.replace`), and the
primitive then reads array pixels. A shadow takes the hillshade's light, `relief.DEFAULT_SUN`,
so a shadow falls the way the relief is lit.

Does not draw a line, build a mask or pick the paper: the caller supplies the mask and the
paper plate, or `None` for wash space. It draws no random number. A primitive takes its
`LINE_THRESHOLD` default; none is passed here.

Invariants: a stack with no effects returns `rgb` itself; the colour beneath is float32.
"""

from dataclasses import replace

import numpy as np

from pyntpot.ink import Casing, Glow, Reserve, Shadow, casing, glow, reserve, shadow
from pyntpot.ink.effect_types import EFFECT_RANGES
from pyntpot.maps.line_effects import EffectStack
from pyntpot.maps.relief import DEFAULT_SUN

#: The fields of an effect that are in pixels, and so scale with the array.
_PX_FIELDS = tuple(name for name in EFFECT_RANGES if name.endswith("_px"))


def _scaled(
    effect: Casing | Glow | Shadow | Reserve, scale: float
) -> Casing | Glow | Shadow | Reserve:
    """The effect with each of its `*_px` fields multiplied by `scale`."""
    fields = {name: getattr(effect, name) * scale for name in _PX_FIELDS if hasattr(effect, name)}
    return replace(effect, **fields)


def lay_stack(
    rgb: np.ndarray,
    mask: np.ndarray,
    stack: EffectStack,
    *,
    scale: float,
    paper: np.ndarray | None,
) -> np.ndarray:
    """Lay a stack's effects in order round the line `mask` marks.

    Args:
        rgb: The colour beneath, float32 `(h, w, 3)`, 0 to 1.
        mask: The line's density, float `(h, w)`.
        stack: The effects, widths in display pixels.
        scale: Array pixels per display pixel.
        paper: `None` for wash space, or the `(h, w, 3)` paper plate.

    Returns:
        `rgb` itself for an empty stack, otherwise the colour with every effect laid.
    """
    out = rgb
    for effect in stack.effects:
        scaled = _scaled(effect, scale)
        if isinstance(scaled, Casing):
            out = casing(out, mask, scaled, paper=paper)
        elif isinstance(scaled, Reserve):
            out = reserve(out, mask, scaled, paper=paper)
        elif isinstance(scaled, Glow):
            out = glow(out, mask, scaled, paper=paper)
        else:
            out = shadow(out, mask, scaled, azimuth_deg=DEFAULT_SUN.azimuth)
    return out
