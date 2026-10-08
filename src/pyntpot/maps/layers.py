"""Assembling the basemap: every layer one track's cached payloads can give.

Key names: `build_basemap`, which reads the cached feature, land cover and elevation
payloads and returns the typed `Basemap` the painter reads; `basemap`, the vector
layers as plain data, with the roads, rivers and landmark candidates already chosen by
the track's interaction with them; `BasemapInputs`, what one track's basemap is
assembled from; `scale_for`, how much coarser than a run's map a box this big is drawn.

Everything is in the card's own metre space, the one `track_projection` puts a track
in: x east, y north, origin at the south-west corner of the track's bounding box. A box
is generalised by thresholds stated for a reference span and scaled up from it.

It does not fetch anything, paint, or letter: with nothing cached for a box it returns
`None` (`build_basemap` does so whenever the feature payload is missing), the signal to
draw the bare track. Invariants: the same payloads and style
always give the same basemap; the roads and watercourses of `build_basemap` are the ones
the vector map draws, decided by the same interaction rules.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from pyntpot.ink.polyline import Pt, simplify
from pyntpot.maps.basemap import Basemap, ElevationPatch, Layers
from pyntpot.maps.basemap_strokes import (
    Frame,
    line_of,
    rivers_from_paths,
    roads_from_paths,
)
from pyntpot.maps.candidates.landmarks import pick_landmarks, rank_landmarks
from pyntpot.maps.card import Card
from pyntpot.maps.card_geometry import journal_geometry
from pyntpot.maps.cover import (
    COVER_ORDER,
    coastline_chains,
    cover_rings,
    sea_from_coast,
    wood_rings,
)
from pyntpot.maps.osm import _osm_layers
from pyntpot.maps.projection import track_projection
from pyntpot.maps.relief_layers import _relief_layers
from pyntpot.maps.rings import clip_ring
from pyntpot.maps.style_groups import BasemapStyle
from pyntpot.maps.svg_path import parse_path
from pyntpot.maps.track_index import TrackIndex, _densify

if TYPE_CHECKING:
    from pathlib import Path

    from pyntpot.maps.cache import Cache
    from pyntpot.maps.projection import Projection
    from pyntpot.maps.style import Style
    from pyntpot.maps.track import Track

Clip = tuple[float, float, float, float]

#: The box a run makes. Every generalisation threshold below is stated for this
#: span and scaled up from it, so a ride over four times the ground is drawn at
#: four times the tolerance rather than at a run's detail shrunk to fit.
REFERENCE_SPAN_M = 4000.0
MAX_SCALE = 4.0

#: The widest a keep test reaches from the track, in metres, whatever the scale.
INTERACTION_CAP_M = 200.0

#: The track is simplified to this tolerance, in metres, before the card is fitted to it.
CARD_TRACK_EPS_M = 3.0

#: The track index is simplified to this tolerance, in metres, then densified to this step.
INDEX_EPS_M = 6.0
INDEX_STEP_M = 15.0

#: The least simplification tolerance a card's lines get, in metres.
MIN_EPS_M = 2.0

#: How much of a pixel the card's lines are simplified to.
EPS_PIXELS = 1.1

#: A lake ring needs more points than this to be drawn.
LAKE_POINTS_OVER = 3

#: Ground kept around the track when drawing, before the box's scale is applied.
DEFAULT_CLIP_MARGIN_M = 900.0


@dataclass(frozen=True)
class BasemapInputs:
    """What one track's basemap is assembled from.

    Attributes:
        key: The track's cache key, naming the cache files.
        track: The recorded track.
        cache: Where the cached payloads live.
        places: User-supplied places of interest, each with a `name`, `lat` and `lng`.
    """

    key: str
    track: Track
    cache: Cache
    places: list[dict[str, Any]]


def scale_for(span_m: float) -> float:
    """How much coarser than a run's map a box this big should be drawn."""
    return min(max(span_m / REFERENCE_SPAN_M, 1.0), MAX_SCALE)


def _derived(options: BasemapStyle, factor: float) -> dict[str, Any]:
    """The generalisation thresholds at this box's scale, which the layer builders read."""
    return {
        "scale": round(factor, 2),
        "road_eps_m": round(10.0 * factor, 1),
        "wood_eps_m": round(22.0 * factor, 1),
        "river_eps_m": round(12.0 * factor, 1),
        "interaction_m": round(min(options.interaction_m * factor, INTERACTION_CAP_M), 1),
        "interaction_run_m": round(options.interaction_run_m * factor, 1),
        "landmark_radius_m": round(options.landmark_radius_m * factor, 1),
        "cell_m": round(options.cell_m * factor, 1),
        "blob_jitter_m": round(options.blob_jitter_m * factor, 1),
        "tree_spacing_m": round(options.tree_spacing_m * factor, 1),
        "river_width": round(min(14.0, 8.0 * factor**0.6), 1),
        "min_area_ha": round(options.min_area_ha * factor**2, 1),
        "hachure_spacing_m": round(options.hachure_spacing_m * factor, 1),
        "hachure_length_m": round(options.hachure_max_length_m * factor, 1),
        "landmark_cap": max(options.landmark_max, round(options.landmark_max * factor**0.5)),
    }


def _place_marks(
    places: list[dict[str, Any]], proj: Projection, clip: Clip
) -> list[dict[str, Any]]:
    """Project the supplied places, keeping the ones inside the map."""
    xmin, ymin, xmax, ymax = clip
    out = []
    for place in places:
        if "lat" not in place or "lng" not in place:
            continue
        x, y = proj(float(place["lat"]), float(place["lng"]))
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            continue
        # `kind` and `always_label` are optional. By default a place is a glyph
        # named by `symbol`, with the name under it, chosen by the score like
        # anything else. A `settlement` entry draws no
        # glyph, and an `always_label` one is lettered whenever the box holds it.
        kind = str(place.get("kind", "marker"))
        symbol = place.get("symbol", "" if kind == "settlement" else "pin")
        out.append(
            {
                "n": place.get("name", ""),
                "sym": symbol,
                "kind": kind,
                "always": bool(place.get("always_label", False)),
                "x": round(x, 1),
                "y": round(y, 1),
                "note": place.get("note", ""),
            }
        )
    return out


def basemap(
    inputs: BasemapInputs,
    options: BasemapStyle | None = None,
    route: list[Pt] | None = None,
    clip_margin_m: float = DEFAULT_CLIP_MARGIN_M,
) -> dict[str, Any] | None:
    """Assemble every basemap layer for one track from the cache.

    Args:
        inputs: The cache key, the track, its cache and its places.
        options: What to draw. The defaults are the basemap group's own.
        route: The already-projected track, when the caller has one. Its first
            point fixes the origin, so a caller that simplified its track before
            projecting it gets roads on the same origin as that track, not a
            metre or two off it.
        clip_margin_m: Metres of ground kept around the track's bounding box
            when drawing, before the box's scale is applied.

    Returns:
        The vector layers as plain data in card metres, or None when nothing
        is cached for this box, the signal to draw the bare track and say so.
    """
    options = options or BasemapStyle()
    osm_file = inputs.cache.features_path(inputs.key)
    elev_file = inputs.cache.elevation_path(inputs.key)
    if not osm_file.exists() and not elev_file.exists():
        return None
    proj, pts = track_projection(list(inputs.track.lat), list(inputs.track.lng), route)
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    factor = scale_for(span)
    derived = _derived(options, factor)
    margin = clip_margin_m * factor
    clip = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    out: dict[str, Any] = {
        "id": inputs.key,
        "clip": [round(v, 1) for v in clip],
        "bounds": [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)],
        "span_m": round(span),
        "derived": derived,
        "sources": [],
    }
    # Simplified so the index is small, then densified so it is honest: the
    # index measures distance to a vertex, and a straight kilometre simplifies
    # to two of them, which would put a road running beside it half a field away.
    index = TrackIndex(_densify(simplify(pts, INDEX_EPS_M), INDEX_STEP_M))
    if osm_file.exists():
        out.update(_osm_layers(osm_file, proj, clip, index, options, derived))
        out["sources"].append(f"OSM via Overpass, {osm_file.stat().st_size // 1024} KB cached")
    if elev_file.exists():
        out.update(_relief_layers(elev_file, proj, clip, options, derived, index))
        out["sources"].append("SRTM 30 m via OpenTopoData")
    out["places"] = _place_marks(inputs.places, proj, clip)
    out["landmarks"] = pick_landmarks(
        out.get("landmark_candidates", []),
        mode=options.landmarks,
        radius_m=derived["landmark_radius_m"],
        cap=derived["landmark_cap"],
        picks=options.pick_landmarks,
    )
    return out


def _elevation_patch(path: Path, proj: Projection) -> ElevationPatch | None:
    """The cached elevation grid placed in card metres, or None when none is cached."""
    if not path.exists():
        return None
    grid = json.loads(path.read_text())
    gx0, gy0 = proj(grid["lats"][0], grid["lons"][0])
    gx1, gy1 = proj(grid["lats"][-1], grid["lons"][-1])
    return ElevationPatch(
        n=grid["n"],
        x0=gx0,
        y0=gy0,
        x1=gx1,
        y1=gy1,
        values=tuple(round(float(v), 1) for v in grid["elev"]),
        low=round(min(grid["elev"])),
        high=round(max(grid["elev"])),
    )


def _cover(
    inputs: BasemapInputs, proj: Projection, clip: Clip, eps: float
) -> tuple[dict[str, list[list[Pt]]], list[list[Pt]], list[list[Pt]]]:
    """The land cover rings with the woods laid over them, the coast and the sea."""
    cover = cover_rings(inputs.key, proj, clip, eps, inputs.cache)
    wood = wood_rings(inputs.key, proj, clip, eps, inputs.cache)
    if wood:
        cover["wood"] = cover.get("wood", []) + wood
    coast = coastline_chains(inputs.key, proj, clip, inputs.cache)
    return cover, coast, sea_from_coast(coast, clip)


def build_basemap(
    inputs: BasemapInputs, style: Style, route: list[Pt] | None = None
) -> Basemap | None:
    """Everything the painter needs for one track, from the cache.

    The land cover, the coast and the sea come from the two cached Overpass
    payloads; the roads and the watercourses come through `basemap`, so the
    same interaction rules decide what is drawn here as on the vector map.

    Args:
        inputs: The cache key, the track, its cache and its places.
        style: The style; its card, ribbon and brush groups fit the card and
            its basemap group says what is drawn. The clip margin is the card's
            own longer side, derived here.
        route: The already-projected track, when the caller has one.

    Returns:
        The basemap in card metres, or None when the feature payload is not cached.
    """
    key, cache = inputs.key, inputs.cache
    if not cache.features_path(key).exists():
        return None
    proj, pts = track_projection(list(inputs.track.lat), list(inputs.track.lng), route)
    track = simplify(pts, CARD_TRACK_EPS_M)
    geometry = journal_geometry(track, style.card, style.ribbon, style.brush)
    x0, y0, x1, y1 = geometry["card"]
    clip = (x0, y0, x1, y1)
    eps = max(geometry["mpp"] * EPS_PIXELS, MIN_EPS_M)
    base = basemap(inputs, style.basemap, route=track, clip_margin_m=max(x1 - x0, y1 - y0))
    if base is None:
        return None
    cover, coast, sea = _cover(inputs, proj, clip, eps)
    frame = Frame(clip, eps, geometry, style.brush)
    roads = roads_from_paths(base.get("roads", []), frame)
    lakes = [
        simplify(clip_ring(r, clip), eps)
        for r in parse_path(base.get("water_area", {}).get("d", ""))
    ]
    rivers = rivers_from_paths(base.get("rivers", []), lakes, frame)
    layers = Layers(
        route=line_of(track),
        cover={k: tuple(line_of(r) for r in v) for k, v in cover.items()},
        cover_order=tuple(c for c in COVER_ORDER if c in cover),
        lakes=tuple(line_of(r) for r in lakes if len(r) > LAKE_POINTS_OVER),
        sea=tuple(line_of(r) for r in sea),
        coastline=tuple(line_of(c) for c in coast),
        roads=tuple(roads),
        rivers=tuple(rivers),
        elevation=_elevation_patch(cache.elevation_path(key), proj),
        ribbon_m=geometry["ribbon_m"],
        wet_px=geometry["wet_px"],
        minor_roads=geometry["minor_roads"],
        blotch_m=geometry["blotch_m"],
        dab_spacing_m=geometry["dab_spacing_m"],
        gran_m=geometry["gran_m"],
    )
    bx0, by0, bx1, by1 = geometry["bounds"]
    return Basemap(
        projection=proj,
        card=Card.from_manifest(geometry),
        layers=layers,
        bounds=(bx0, by0, bx1, by1),
        span_m=geometry["span_m"],
        ribbon_fitted_m=geometry["ribbon_fitted_m"],
        track=tuple(pts),
        places=tuple(base.get("places", [])),
        candidates=tuple(
            c.detail for c in rank_landmarks(base.get("landmark_candidates", []), proj)
        ),
        sources=tuple(base.get("sources", [])),
    )
