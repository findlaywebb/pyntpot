"""The card frame and every size a plate is painted at, derived from the route.

Key name: `journal_geometry`, which takes the track in metres and the card, ribbon and
brush style groups, and returns the card box, the render and display sizes, the ribbon
radius and the painted widths every layer is stated in.

Every size on the map is derived from the track's span, so a 13 km box and a 3 km box
are drawn with the same weights on screen rather than the same weights on the ground.
It does not fetch, project or clip anything and it paints nothing. Invariants: the
card's aspect lies within the ribbon group's limits; the ribbon radius is a constant
times the square root of the span plus a small-box offset, clamped, so a generous ribbon
on a small box never swells to the whole map on a big one.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyntpot.ink.brush_style import BrushStyle
    from pyntpot.ink.polyline import Pt
    from pyntpot.maps.style_groups import CardStyle, RibbonStyle

Box = tuple[float, float, float, float]


def _card_box(bounds: Box, fitted: float, ribbon: RibbonStyle) -> Box:
    """The card round a track's bounds: grown by the ribbon, padded, and kept in aspect."""
    bx0, by0, bx1, by1 = bounds
    grow = fitted * ribbon.card_grow_mult
    cx0, cy0, cx1, cy1 = bx0 - grow, by0 - grow, bx1 + grow, by1 + grow
    pad = max(
        ribbon.card_pad_frac * max(cx1 - cx0, cy1 - cy0), ribbon.card_pad_ribbon_frac * fitted
    )
    cx0, cy0, cx1, cy1 = cx0 - pad, cy0 - pad, cx1 + pad, cy1 + pad
    w, h = cx1 - cx0, cy1 - cy0
    aspect = w / h
    if aspect < ribbon.card_aspect_min:
        extra = (h * ribbon.card_aspect_min - w) / 2
        cx0, cx1 = cx0 - extra, cx1 + extra
    elif aspect > ribbon.card_aspect_max:
        extra = (w / ribbon.card_aspect_max - h) / 2
        cy0, cy1 = cy0 - extra, cy1 + extra
    return cx0, cy0, cx1, cy1


def journal_geometry(
    route: list[Pt], card: CardStyle, ribbon: RibbonStyle, brush: BrushStyle
) -> dict[str, Any]:
    """The card, its ribbon radius, and every size the plate is painted at.

    Every size on the map is derived from this, so a 13 km box and a 3 km box
    are drawn with the same weights on screen rather than the same weights on
    the ground. The ribbon is a constant times the square root of the box plus
    a small-box offset: that keeps a generous ribbon on a small box without
    swelling it to the whole map on a big one.

    Args:
        route: The track in metres.
        card: The card's display size and supersampling.
        ribbon: The ribbon's fit and the card's framing.
        brush: The widths and thresholds the sizes on the map are stated in.

    Returns:
        The card box, the render and display sizes, the ribbon radius, and the
        painted widths every layer is stated in.
    """
    xs = [p[0] for p in route]
    ys = [p[1] for p in route]
    bx0, by0, bx1, by1 = min(xs), min(ys), max(xs), max(ys)
    span = max(bx1 - bx0, by1 - by0, 1.0)
    fitted = min(
        max(ribbon.ribbon_k * math.sqrt(span) + ribbon.ribbon_c, ribbon.ribbon_min_m),
        ribbon.ribbon_max_m,
    )
    cx0, cy0, cx1, cy1 = _card_box((bx0, by0, bx1, by1), fitted, ribbon)
    w, h = cx1 - cx0, cy1 - cy0
    display_w = int(card.display_px)
    render_w = display_w * int(card.supersample)
    render_h = round(render_w * h / w)
    mpp = w / render_w
    disp = mpp * card.supersample
    return {
        "card": [round(cx0, 1), round(cy0, 1), round(cx1, 1), round(cy1, 1)],
        "bounds": [round(bx0, 1), round(by0, 1), round(bx1, 1), round(by1, 1)],
        "span_m": round(span),
        "ribbon_m": round(fitted * ribbon.ribbon_mult),
        "ribbon_fitted_m": round(fitted),
        "render": [render_w, render_h],
        "display": [display_w, round(render_h / card.supersample)],
        "mpp": round(mpp, 3),
        "mpp_display": round(disp, 3),
        "wet_px": {
            cls: round(min(max(k * (span / 1000.0) ** e, lo), hi), 2)
            for cls, (k, e, lo, hi) in brush.river_curve.items()
        },
        "minor_roads": disp < brush.minor_roads_mppd,
        "blotch_m": round(max(brush.blotch_m[0], disp * brush.blotch_m[1]), 1),
        "dab_spacing_m": round(max(brush.dab_spacing_m[0], disp * brush.dab_spacing_m[1]), 1),
        "gran_m": round(max(brush.gran_m[0], disp * brush.gran_m[1]), 1),
    }
