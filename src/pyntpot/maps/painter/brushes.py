"""A plate's brushes, and how dark each land-cover class washes.

Key names: `plate_brushes`, which builds every line class's brush for one plate, sized
against the plate's own display pixel, and `COVER_CFG`, how dark a wash of each
land-cover class goes and how hard its edge pools, the painter's default for
`CoverStyle.cover_cfg`.

It builds brushes and lays no ink; the brush-sheet tables and `brush_from_id` live in
`pyntpot.ink.brush`. A class with no measured width takes the river importance
curve's own default.
"""

from pyntpot.ink.brush import Brush, brush_from_id
from pyntpot.ink.brush_style import BrushStyle

#: How dark a wash of each class goes, and how hard its edge pools.
COVER_CFG = {
    "farmland": (0.52, 0.20),
    "meadow": (0.55, 0.22),
    "orchard": (0.55, 0.24),
    "scrub": (0.58, 0.26),
    "heath": (0.60, 0.26),
    "sand": (0.50, 0.22),
    "rock": (0.52, 0.26),
    "wetland": (0.60, 0.28),
    "built": (0.55, 0.20),
    "works": (0.58, 0.22),
    "wood": (0.72, 0.30),
}


def plate_brushes(
    style: BrushStyle, scale: float, wet_px: dict[str, float]
) -> dict[str, tuple[Brush, str]]:
    """Every class's brush for one plate, sized against its own display pixel.

    Args:
        style: The brush style.
        scale: Render pixels per display pixel.
        wet_px: Painted width in display pixels per watercourse class, from the
            river importance curve.

    Returns:
        Brush and ink colour by class key.
    """
    mult = style.river_mult
    widths = {
        "major": wet_px.get("major", 8.4) * mult,
        "medium": wet_px.get("medium", 5.5) * mult,
        "minor": wet_px.get("minor", 2.2) * mult,
        "coast": wet_px.get("medium", 5.5) * mult * style.coast_width_frac,
        "road_major": style.brush_width_px["road_major"],
        "lane": style.brush_width_px["lane"],
        "track": style.brush_width_px["track"],
    }
    return {
        key: brush_from_id(style.brushes[key], widths[key], scale, style, key) for key in widths
    }
