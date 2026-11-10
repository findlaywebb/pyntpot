"""The wash plate with line effects: the basemap's ink laid class by class, each with its stack.

Key function: `lay_wash`, which composites the sea and the pooled rim over the ground, lays the
water group's effect stacks in class order, glazes the water layer, lays the road group's stacks,
then glazes the road layers. All of a group's effects go beneath all of its ink, so a casing or a
reserve sits under every line of the group and never over a neighbouring class's line.

A casing union (`basemap.casing_unions`) lays one ring round its members' masks together: at the
ring's place in the stack of the union's first member in class order that has a mask, while every
other member's ring step is skipped. Glows and shadows stay per class.

Used only when the style sets a basemap line effect; with none, the wash plate keeps its single
`composite` call. The paper is wash space (`paper=None`), where white is the paper. It draws no
random number, so the dither generator is untouched, and it paints no ink itself: the layers and
the per-class masks come from `pen.pen_groups`.

Invariants: with every stack empty the result equals the single composite of the same layers in
Kubelka-Munk glazing, and within float rounding in multiply glazing.
"""

import numpy as np

from pyntpot.ink.compositing import PigmentLayer, composite
from pyntpot.ink.noise import F32
from pyntpot.maps.effect_pass import RingPairs, lay_stack
from pyntpot.maps.line_effects import ROAD_GROUP, WATER_GROUP, ring_effect
from pyntpot.maps.painter.job import PaintJob
from pyntpot.maps.painter.pen import PenGroup, PenGroups


def _union_rings(job: PaintJob, classes: tuple[str, ...], group: PenGroup) -> dict[str, RingPairs]:
    """For each union in this group, its carrier class mapped to every member's mask and ring.

    The carrier is the union's first member in class order that has a mask; its pairs are those
    members that have a mask and a ring effect, in class order.
    """
    rings: dict[str, RingPairs] = {}
    for union in job.style.basemap.casing_unions:
        members = [cls for cls in classes if cls in union and cls in group.masks]
        pairs = tuple(
            (group.masks[cls], effect)
            for cls in members
            if (effect := ring_effect(job.style.basemap.line_effects.get(cls))) is not None
        )
        if pairs:
            rings[members[0]] = pairs
    return rings


def _lay_group(
    job: PaintJob, rgb: np.ndarray, classes: tuple[str, ...], group: PenGroup
) -> np.ndarray:
    """The group's stacks laid in class order, then its ink glazed over them."""
    rings = _union_rings(job, classes, group)
    united = {cls for union in job.style.basemap.casing_unions for cls in union}
    for cls in classes:
        stack = job.style.basemap.line_effects.get(cls)
        mask = group.masks.get(cls)
        if stack is not None and mask is not None:
            ring = rings.get(cls, () if cls in united else None)
            rgb = lay_stack(rgb, mask, stack, scale=job.scale, paper=None, ring=ring)
    if not group.layers:
        return rgb
    return composite(group.layers, rgb.astype(F32, copy=False), job.style.paper)


def lay_wash(
    job: PaintJob, ground: np.ndarray, under: list[PigmentLayer], groups: PenGroups
) -> np.ndarray:
    """The wash plate: `under` over `ground`, then each group's effects and ink.

    Args:
        job: The job, whose style holds the stacks, the paper and `km_glazing`.
        ground: The ribbon's ground, `(h, w, 3)`.
        under: The sea and rim layers laid first.
        groups: `pen.pen_groups(job)`.

    Returns:
        The wash plate, the shape of `ground`.
    """
    rgb = composite(under, ground, job.style.paper) if under else ground
    rgb = _lay_group(job, rgb, WATER_GROUP, groups.water)
    return _lay_group(job, rgb, ROAD_GROUP, groups.road)
