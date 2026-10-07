"""The land-cover phase: one label per pixel, one wet field, and a wash for each class.

Key names: `paint_cover`, which labels the ground, finds the wood, and lays one wash
per class (or the single pale wash when cover is off) among the trimmed layers; and
`wet_field`, the one wet map over the union of the cover.

The land is labelled with one class per pixel, so two land pigments cannot stack. The
outlines are deformed in metres before anything is rasterised, because deforming is
polygon work rather than pixel work; the surveyed coast and the lakes are already filled
and are not touched by it. Inside the wet field the classes are wet at the same time, so
they bleed into each other and no boundary between two of them carries its own rim; the
outer silhouette of the land sits outside it and keeps the edge it should have.

It does not paint the wood's texture or dabs, the relief or the sea. Each wash draws its
blooms from the job's shared generator, in class order.
"""

import numpy as np

from pyntpot.ink.noise import F32, edt, smoothstep
from pyntpot.ink.pigment import Layer
from pyntpot.ink.raster import Deform, deform_rings, fill_cov
from pyntpot.ink.sheet import rgb
from pyntpot.ink.style import WashStyle
from pyntpot.ink.wash import WashOptions, separated, wash
from pyntpot.maps.painter.job import INSIDE, PaintJob, PlateStack, drawable

#: A wet field's reach is never narrower than this many pixels.
_WET_BACK_FLOOR = 4.0


def wet_field(label: np.ndarray, style: WashStyle, rim_cov: float) -> np.ndarray | None:
    """One wet field over the union of the cover, or `None` when there is nothing to wet.

    Inside it the classes are wet at the same time. When `wet_close_px` is set, the
    union is closed over gaps that wide first: the classes do not abut, they meet
    along hairlines of unmapped ground a pixel or two wide, so the union taken as it
    stands is cut through by dry lines exactly where two washes meet, and no bleed
    width can reach a seam. Closing is a dilate and an erode by the same distance, so
    the land's outer silhouette comes back where it was.

    Source: `wet-area-bleed` in docs/explanation/references.md.

    Args:
        label: One class index per pixel, 0 where there is no cover.
        style: The wash style, for the bleed and the closing distance.
        rim_cov: The pooled rim of a cover wash, in pixels.

    Returns:
        The wet field in 0 to 1, or `None` when bleeding is off or no land is labelled.
    """
    if not (style.wet_bleed and label.any()):
        return None
    back = max(rim_cov * style.wet_bleed_edge_mult, _WET_BACK_FLOOR)
    dry = label == 0
    if style.wet_close_px > 0:
        gap = F32(style.wet_close_px)
        dry = ~(edt(~(edt(label > 0) <= gap)) > gap)
    return smoothstep(edt(dry) - F32(back), back)


def _deform(job: PaintJob) -> Deform | None:
    """The cover outlines' deformation, in metres, or `None` when the silhouette is not deformed."""
    wash_style = job.style.wash
    if not wash_style.silhouette_deform:
        return None
    floor_m, mult = wash_style.silhouette_deform_max_m
    return (
        job.deform_rng,
        wash_style.silhouette_deform_amount,
        int(wash_style.silhouette_deform_depth),
        wash_style.silhouette_deform_decay,
        max(floor_m, mult * job.mpp),
        wash_style.silhouette_deform_min_px * job.mpp,
    )


def cover_order(job: PaintJob) -> list[str]:
    """The cover classes the basemap carries, in painting order."""
    layers = job.layers
    return [c for c in layers.cover_order if c in layers.cover]


def _label(job: PaintJob, stack: PlateStack, order: list[str]) -> None:
    """One class index per pixel, with the water cut out so no pigment lies on it."""
    deform = _deform(job)
    for i, cls in enumerate(order, 1):
        rings = drawable(job.layers.cover[cls])
        if rings:
            stack.label[fill_cov(deform_rings(rings, deform), job.canvas) > INSIDE] = i
    stack.label[stack.water] = 0


def _class_washes(job: PaintJob, stack: PlateStack, order: list[str]) -> list[Layer]:
    """One separated wash per labelled class, wet together across the cover."""
    style = job.style
    wet_map = wet_field(stack.label, style.wash, job.rim_cov)
    layers: list[Layer] = []
    for i, cls in enumerate(order, 1):
        base, pool = style.cover.cover_cfg.get(cls, (0.5, 0.2))
        cov = (stack.label == i).astype(F32)
        if not cov.any():
            continue
        options = WashOptions(
            rim_px=job.rim_cov,
            wet=wet_map,
            bleed_px=style.wash.wet_bleed_px,
            bleed_mix=style.wash.wet_bleed_mix,
            rim_drop=style.wash.wet_rim_drop,
            gran_gamma=job.gran_gamma,
            flow=job.flow,
            blooms=job.bloom(cov),
        )
        layers.extend(
            separated(
                wash(cov, job.sheet, base, pool, options),
                cls,
                rgb(style.cover.pigments[cls]),
                job.transp(cls),
                job.sheet,
                style.wash,
            )
        )
    return layers


def _pale_wash(job: PaintJob, stack: PlateStack) -> Layer:
    """The single pale wash over everything that is not sea, drawn when cover is off."""
    cover = job.style.cover
    pale = 1.0 - np.maximum(stack.sea_cov, 0.0)
    options = WashOptions(
        rim_px=max(6.0, 120.0 / job.mpp),
        gran_gamma=job.gran_gamma,
        flow=job.flow,
        blooms=job.bloom(pale),
    )
    return (
        wash(pale, job.sheet, cover.pale_base, cover.pale_pool, options),
        rgb(cover.pigments["pale"]),
        job.transp("pale"),
    )


def paint_cover(job: PaintJob, stack: PlateStack) -> None:
    """Label the ground, find the wood, and wash each class among the trimmed layers."""
    if not job.style.cover.land_cover:
        stack.trimmed.append(_pale_wash(job, stack))
        return
    order = cover_order(job)
    _label(job, stack, order)
    stack.trimmed.extend(_class_washes(job, stack, order))
    if "wood" in order:
        stack.wood_mask = stack.label == order.index("wood") + 1
