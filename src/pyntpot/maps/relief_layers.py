"""The relief and water layers one elevation grid can carry.

Key names: `_relief_layers`, which reads a cached elevation grid and returns the
hillshade bands or raster, the contours, the hachures, the sea and its waves, in route
metres; `_sea_path`, the sea as one wash with a lighter dry-brush edge pulled in from it.

Which of the relief layers is built is the basemap style's `hillshade_mode`, and the
sea's waves follow `sea_style`; `all_variants` builds every one for comparison. It does
not fetch the grid, draw the road or wood layers, or assemble the basemap. Invariants:
every layer key is present in the result, empty when its layer was not asked for; a
sea that is empty has no waves.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pyntpot.maps.contours import contour_lines, sea_rings
from pyntpot.maps.generalise import Finish, Generalisation, generalise_layer
from pyntpot.maps.relief import Terrain, hillshade_png, shade_bands
from pyntpot.maps.relief_strokes import Field, Hatching, hachures, wave_strokes
from pyntpot.maps.rings import clip_ring
from pyntpot.maps.svg_path import path_d, rings_path

if TYPE_CHECKING:
    from pathlib import Path

    from pyntpot.ink.polyline import Pt
    from pyntpot.maps.projection import Projection
    from pyntpot.maps.style_groups import BasemapStyle
    from pyntpot.maps.track_index import TrackIndex

Clip = tuple[float, float, float, float]

#: Fewest hillshade levels asked for when the layer is not generalised, and most.
MIN_LEVELS = 3
MAX_LEVELS = 8

#: A ring needs more points than this to be a wash.
RING_POINTS_OVER = 2

#: The sea's edge wobble is this share of a wood's, and its seed is its own.
SEA_JITTER_SHARE = 0.6
SEA_SEED = 4

#: How far apart the wave strokes are, and how long, as shares of the hachure scale.
WAVE_SPACING_FACTOR = 2.4
WAVE_LENGTH_FACTOR = 0.8


def _sea_path(
    water: list[list[Pt]],
    islands: list[list[Pt]],
    clip: Clip,
    options: BasemapStyle,
    derived: dict[str, Any],
) -> dict[str, str]:
    """The sea as one wash, with a lighter dry-brush edge pulled in from it."""
    cut = [clip_ring(r, clip) for r in water]
    holes = [clip_ring(r, clip) for r in islands]
    if not options.generalise:
        return {"d": rings_path(cut, holes), "inner": ""}
    layer = generalise_layer(
        [r for r in cut if len(r) > RING_POINTS_OVER],
        [r for r in holes if len(r) > RING_POINTS_OVER],
        clip,
        Generalisation(
            derived["cell_m"],
            options.morph_cells,
            derived["min_area_ha"],
            options.smooth_passes,
        ),
        Finish(
            jitter_m=derived["blob_jitter_m"] * SEA_JITTER_SHARE,
            inset_cells=options.inset_cells,
            seed=SEA_SEED,
        ),
    )
    return {
        "d": "".join(path_d(r, close=True) for r in layer["outer"]),
        "inner": "".join(path_d(r, close=True) for r in layer["inner"]),
    }


def _shading(
    terrain: Terrain, options: BasemapStyle, derived: dict[str, Any], corners: tuple[Pt, Pt]
) -> dict[str, Any]:
    """The hillshade bands, the hillshade raster and the contours the options ask for.

    Args:
        terrain: The elevation grid with its geography.
        options: What to draw.
        derived: The scale-aware thresholds from `_derived`.
        corners: Where the grid's first and last posts fall, in route metres.

    Returns:
        `hillshade_bands`, `hillshade_raster` and `contours`.
    """
    (x0, y0), (x1, y1) = corners
    mode = options.hillshade_mode
    every = options.all_variants
    out: dict[str, Any] = {"hillshade_bands": [], "hillshade_raster": None, "contours": []}
    if every or mode == "bands":
        levels = (
            2 if options.generalise else max(MIN_LEVELS, min(MAX_LEVELS, options.hillshade_levels))
        )
        out["hillshade_bands"] = shade_bands(
            terrain,
            levels=levels,
            eps=derived["cell_m"] * 0.8 if options.generalise else derived["wood_eps_m"] * 0.6,
        )
    if every or mode == "raster":
        href, width, height = hillshade_png(terrain.grid, terrain.dx, terrain.dy)
        out["hillshade_raster"] = {
            "href": href,
            "x": round(x0, 1),
            "y": round(y0, 1),
            "w": round(x1 - x0, 1),
            "h": round(y1 - y0, 1),
            "px": width,
            "py": height,
        }
    if every or mode == "contours":
        out["contours"] = contour_lines(
            terrain.grid,
            terrain.lats,
            terrain.lons,
            terrain.proj,
            options.contour_interval,
            eps=derived["river_eps_m"] * 1.4,
        )
    return out


def _hachure_strokes(
    field: Field,
    clip: Clip,
    options: BasemapStyle,
    derived: dict[str, Any],
    index: TrackIndex | None,
) -> list[dict[str, Any]]:
    """The hachures, when the options ask for them."""
    if not (options.all_variants or options.hillshade_mode == "hachures"):
        return []
    return hachures(
        field,
        clip,
        index,
        Hatching(
            spacing_m=derived["hachure_spacing_m"],
            min_slope=options.hachure_min_slope,
            max_length_m=derived["hachure_length_m"],
        ),
    )


def _relief_layers(
    path: Path,
    proj: Projection,
    clip: Clip,
    options: BasemapStyle,
    derived: dict[str, Any],
    index: TrackIndex | None = None,
) -> dict[str, Any]:
    """Every relief and water layer the SRTM grid can carry."""
    data = json.loads(path.read_text())
    n = data["n"]
    values = data["elev"]
    grid = [[float(v) for v in values[r * n : (r + 1) * n]] for r in range(n)]
    lats, lons = data["lats"], data["lons"]
    terrain = Terrain(
        grid, lats, lons, proj, (lons[1] - lons[0]) * proj.kx, (lats[1] - lats[0]) * proj.ky
    )
    water, islands = sea_rings(grid, lats, lons, proj)
    flat = [v for row in grid for v in row]
    out: dict[str, Any] = {
        "hillshade_bands": [],
        "hillshade_raster": None,
        "hachures": [],
        "contours": [],
        "sea_waves": "",
        "sea": _sea_path(water, islands, clip, options, derived),
        "elevation": {"min": round(min(flat)), "max": round(max(flat)), "grid": n},
    }
    out.update(
        _shading(terrain, options, derived, (proj(lats[0], lons[0]), proj(lats[-1], lons[-1])))
    )
    field = Field(grid, lats, lons, proj)
    out["hachures"] = _hachure_strokes(field, clip, options, derived, index)
    if out["sea"]["d"] and (options.all_variants or options.sea_style == "waves"):
        out["sea_waves"] = wave_strokes(
            field,
            clip,
            spacing_m=derived["hachure_spacing_m"] * WAVE_SPACING_FACTOR,
            length_m=derived["hachure_length_m"] * WAVE_LENGTH_FACTOR,
        )
    return out
