"""Basemap geometry for the route chart.

OSM features, an SRTM hillshade and candidate landmarks, all built from files
cached under `data/geo/`.

Everything this module emits is in the route chart's own metre space, the one
`normalise.project_route` puts a `RoutePoint` in: x east, y north, origin at the
south-west corner of the track's bounding box. The chart therefore draws a road
and the track through exactly the same transform, and a test can check the
projection without rendering anything.

Nothing here reaches the network except `fetch_activity`, which is attended use
only: the renderer reads the cache and, when there is no cache, says so and
draws the bare track.
"""

from __future__ import annotations

import json
import logging
import math
import re
import time
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pyntpot.ink.chains import join_chains, join_strokes
from pyntpot.ink.polyline import (
    clip_line,
    eased,
    length,
    simplify,
    smooth,
)

if TYPE_CHECKING:
    from pyntpot.ink.brush_style import BrushStyle
    from pyntpot.maps.basemap import Basemap, ElevationPatch, Line
    from pyntpot.maps.projection import Projection
    from pyntpot.maps.rings import Rings
    from pyntpot.maps.style_groups import BasemapStyle, CardStyle, RibbonStyle
    from pyntpot.maps.track_index import TrackIndex

log = logging.getLogger(__name__)

#: Overpass mirrors, tried in order. A public endpoint returns 504 under load
#: often enough that one URL is not a fetch strategy.
OVERPASS_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
OVERPASS_URL = OVERPASS_URLS[0]
ELEVATION_URL = "https://api.opentopodata.org/v1/srtm30m"

#: Metres of ground kept around the track's bounding box when fetching.
MARGIN_M = 1500.0
#: Samples per side of the SRTM grid. 80 x 80 over a 5 km box is a 60 m post,
#: which is finer than SRTM's own 30 m only in the sense that the interpolation
#: is smooth: it is the grid a hillshade reads well at, not new information.
ELEV_N = 80

#: Roads that are drawn whatever the track did.
MAJOR_ROADS = ("motorway", "trunk", "primary", "secondary")
#: Roads that are drawn only where the track interacted with them.
MINOR_ROADS = ("tertiary", "unclassified", "residential", "track", "service")

Pt = tuple[float, float]


# --------------------------------------------------------------------------- bounding box


def bounding_box(
    lat: list[float], lng: list[float], margin_m: float = MARGIN_M
) -> tuple[float, float, float, float]:
    """South, west, north, east degrees around a track, grown by `margin_m`."""
    mid = (min(lat) + max(lat)) / 2
    dlat = margin_m / 110540.0
    dlng = margin_m / (111320.0 * math.cos(math.radians(mid)))
    return (min(lat) - dlat, min(lng) - dlng, max(lat) + dlat, max(lng) + dlng)


# --------------------------------------------------------------------------- geometry


# --------------------------------------------------------------------------- proximity


#: The share of a watercourse's own length OSM has to tag as underground before
#: none of it is drawn. Half: a river passing under a bridge or a short culvert
#: is an open river, and a river that is mostly in a pipe is a sewer.
BURIED_FRAC = 0.5


# --------------------------------------------------------------------------- osm


def _geom(entry: dict[str, Any], proj: Projection) -> list[Pt]:
    """Project one Overpass `geometry` array into metres."""
    return [proj(g["lat"], g["lon"]) for g in entry.get("geometry") or [] if g]


def _polygon_rings(entry: dict[str, Any], proj: Projection) -> Rings:
    """Outer and inner rings of one way or relation, in metres."""
    if entry.get("type") == "way":
        pts = _geom(entry, proj)
        return ([pts], []) if len(pts) > 3 else ([], [])
    outer, inner = [], []
    for member in entry.get("members") or []:
        pts = _geom(member, proj)
        if len(pts) < 2:
            continue
        (inner if member.get("role") == "inner" else outer).append(pts)
    return (
        [c for c in join_chains(outer, tol=1.0) if len(c) > 3],
        [c for c in join_chains(inner, tol=1.0) if len(c) > 3],
    )


# --------------------------------------------------------------------------- relief


# --------------------------------------------------------------------------- fetch

OVERPASS_QUERY = """[out:json][timeout:240];
(
  way["highway"~"^({roads})$"]({box});
  way["landuse"="forest"]({box});
  way["natural"="wood"]({box});
  relation["landuse"="forest"]({box});
  relation["natural"="wood"]({box});
  way["boundary"~"^(national_park|protected_area)$"]({box});
  relation["boundary"~"^(national_park|protected_area)$"]({box});
  way["waterway"~"^(river|stream)$"]({box});
  way["natural"~"^(water|coastline|bay)$"]({box});
  relation["natural"="water"]({box});
  node["tourism"~"^({tourism})$"]({box});
  way["tourism"~"^({tourism})$"]["name"]({box});
  relation["tourism"~"^({tourism})$"]["name"]({box});
  node["historic"]({box});
  way["historic"]({box});
  node["man_made"~"^({manmade})$"]({box});
  way["man_made"~"^({manmade})$"]["name"]({box});
  way["building"~"^({buildings})$"]["name"]({box});
  node["amenity"~"^({amenities})$"]["name"]({box});
  way["amenity"~"^({amenities})$"]["name"]({box});
  way["leisure"~"^({leisure})$"]["name"]({box});
  relation["leisure"~"^({leisure})$"]["name"]({box});
  relation["amenity"~"^({amenities})$"]["name"]({box});
  relation["building"~"^({buildings})$"]["name"]({box});
  way["bridge"]["name"]({box});
  node["natural"~"^(peak|arch|cave_entrance)$"]({box});
  node["place"~"^(city|town|village|hamlet|suburb)$"]({box});
);
out geom;"""


GPX_POINT = re.compile(r'lat="([-\d.]+)"\s+lon="([-\d.]+)"')


def read_gpx(path: Path) -> tuple[list[float], list[float]]:
    """Latitudes and longitudes from a GPX track.

    The GPX is the source for where a session went; this is the same read the
    snapshot does.

    Args:
        path: The cached `route.gpx`.

    Returns:
        Latitudes and longitudes in recorded order.
    """
    rows = GPX_POINT.findall(path.read_text())
    return ([float(a) for a, _ in rows], [float(b) for _, b in rows])


def overpass_path(key: str, cache_dir: Path) -> Path:
    """Where the OSM payload for one activity is cached."""
    return cache_dir / f"overpass-{key}.json"


def elevation_path(key: str, cache_dir: Path) -> Path:
    """Where the SRTM grid for one activity is cached."""
    return cache_dir / f"elevation-{key}.json"


def _get(
    url: str,
    params: dict[str, str] | None = None,
    data: dict[str, str] | None = None,
    timeout: float = 240.0,
) -> str:
    """One HTTP call, imported late so the renderer never needs the client."""
    import httpx

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        if data is not None:
            response = client.post(url, data=data)
        else:
            response = client.get(url, params=params)
        response.raise_for_status()
        return response.text


def fetch_overpass(box: tuple[float, float, float, float], path: Path) -> int:
    """Fetch OSM features for one bounding box into the cache.

    Args:
        box: (south, west, north, east) in degrees.
        path: Cache file to write.

    Returns:
        Bytes written.
    """
    query = OVERPASS_QUERY.format(
        box=",".join(f"{value:f}" for value in box),
        roads="|".join(MAJOR_ROADS + MINOR_ROADS),
        tourism="|".join(TOURISM_LANDMARKS),
        manmade="|".join(MANMADE_LANDMARKS),
        buildings="|".join(BUILDING_LANDMARKS),
        amenities="|".join(AMENITY_LANDMARKS),
        leisure="|".join(LEISURE_LANDMARKS),
    )
    text = ""
    for attempt in range(3):
        for url in OVERPASS_URLS:
            try:
                text = _get(url, data={"data": query})
                json.loads(text)
            except Exception as exc:  # a mirror under load is not a failed fetch
                log.info("overpass %s attempt %d: %s", url, attempt + 1, exc)
                text = ""
                time.sleep(4.0)
                continue
            break
        if text:
            break
    if not text:
        raise RuntimeError("every Overpass mirror refused the query")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.stat().st_size


def fetch_elevation(
    box: tuple[float, float, float, float],
    path: Path,
    n: int = ELEV_N,
    chunk: int = 100,
    pause: float = 1.1,
) -> int:
    """Fetch an n by n SRTM grid for one bounding box into the cache.

    Args:
        box: (south, west, north, east) in degrees.
        path: Cache file to write.
        n: Samples per side.
        chunk: Points per request; the public endpoint takes 100.
        pause: Seconds between requests, to stay inside the endpoint's rate.

    Returns:
        Bytes written.
    """
    south, west, north, east = box
    lats = [south + (north - south) * i / (n - 1) for i in range(n)]
    lons = [west + (east - west) * j / (n - 1) for j in range(n)]
    points = [(la, lo) for la in lats for lo in lons]
    values: list[float] = []
    for start in range(0, len(points), chunk):
        batch = points[start : start + chunk]
        locations = "|".join(f"{a:.6f},{b:.6f}" for a, b in batch)
        payload = json.loads(_get(ELEVATION_URL, params={"locations": locations}))
        if payload.get("status") != "OK":
            raise RuntimeError(f"elevation endpoint said {payload.get('status')!r}")
        values.extend(
            0.0 if r["elevation"] is None else float(r["elevation"]) for r in payload["results"]
        )
        log.info("elevation %d/%d", len(values), len(points))
        time.sleep(pause)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"n": n, "bbox": list(box), "lats": lats, "lons": lons, "elev": values})
    )
    return path.stat().st_size


def fetch_activity(
    key: str,
    lat: list[float],
    lng: list[float],
    cache_dir: Path,
    force: bool = False,
    margin_m: float = MARGIN_M,
    n: int = ELEV_N,
    land_cover: bool = True,
) -> dict[str, Any]:
    """Fill the cache for one activity. Attended use only.

    Three payloads: the OSM features and the SRTM grid the vector map draws,
    and the land cover classes the painted map needs. The land cover is fetched
    over a wider box, because the painted card is grown by a ribbon radius
    before it is drawn.

    Args:
        key: The activity, naming the cache files.
        lat: Track latitudes.
        lng: Track longitudes.
        cache_dir: Where the payloads live.
        force: Refetch even when a cache file is already there.
        margin_m: Ground kept around the track's bounding box.
        n: Samples per side of the elevation grid.
        land_cover: Fetch the land cover classes too.

    Returns:
        What was written, by name, with byte counts.
    """
    box = bounding_box(lat, lng, margin_m)
    out: dict[str, Any] = {"box": [round(v, 6) for v in box]}
    osm = overpass_path(key, cache_dir)
    if force or not osm.exists():
        out["overpass"] = fetch_overpass(box, osm)
    else:
        out["overpass"] = f"cached, {osm.stat().st_size} bytes"
    elev = elevation_path(key, cache_dir)
    if force or not elev.exists():
        out["elevation"] = fetch_elevation(box, elev, n=n)
    else:
        out["elevation"] = f"cached, {elev.stat().st_size} bytes"
    if land_cover:
        cover = landcover_path(key, cache_dir)
        if force or not cover.exists():
            wide = bounding_box(lat, lng, LANDCOVER_MARGIN_M)
            out["landcover_box"] = [round(v, 6) for v in wide]
            out["landcover"] = fetch_landcover(wide, cover)
        else:
            out["landcover"] = f"cached, {cover.stat().st_size} bytes"
    return out


# --------------------------------------------------------------------------- landmarks

#: The `tourism` values worth a place on a map, and the `man_made`, `building`,
#: `amenity` and `leisure` ones. These are what the box actually asks OSM for,
#: so widening the map's vocabulary is one edit here and not two.
#:
#: A query for monuments, artworks and history alone asks for nothing a person
#: would actually navigate by. It leaves the sheet naming a drinking fountain
#: and a statue while the zoo, the terraces along a ring road and every bridge
#: over the canal are never offered at all: the picks read as what
#: OpenStreetMap calls a monument rather than as what someone moving through
#: the place would pick out.
TOURISM_LANDMARKS = (
    "attraction",
    "viewpoint",
    "artwork",
    "museum",
    "zoo",
    "aquarium",
    "gallery",
    "theme_park",
)
MANMADE_LANDMARKS = (
    "lighthouse",
    "obelisk",
    "tower",
    "monument",
    "bridge",
    "water_tower",
    "chimney",
    "windmill",
    "pier",
    "mast",
)
BUILDING_LANDMARKS = (
    "cathedral",
    "church",
    "chapel",
    "mosque",
    "synagogue",
    "temple",
    "castle",
    "palace",
    "stadium",
    "train_station",
    "university",
    "hospital",
    "museum",
    "tower",
)
AMENITY_LANDMARKS = (
    "place_of_worship",
    "theatre",
    "arts_centre",
    "university",
    "townhall",
    "courthouse",
    "casino",
)
LEISURE_LANDMARKS = ("stadium", "sports_centre", "marina")

#: The tags a candidate carries forward, so the label agent can see what a thing
#: is and `landmark_reach` can see how tall it stands.
LANDMARK_TAG_KEYS = (
    "tourism",
    "historic",
    "natural",
    "place",
    "man_made",
    "building",
    "amenity",
    "leisure",
    "bridge",
    "height",
    "building:levels",
    "artwork_type",
    "artist_name",
    "ele",
    "start_date",
    "memorial",
)

# --------------------------------------------------------------------------- assembly

#: The box a run makes. Every generalisation threshold below is stated for this
#: span and scaled up from it, so a ride over four times the ground is drawn at
#: four times the tolerance rather than at a run's detail shrunk to fit.
REFERENCE_SPAN_M = 4000.0
MAX_SCALE = 4.0


def scale_for(span_m: float) -> float:
    """How much coarser than a run's map a box this big should be drawn."""
    return min(max(span_m / REFERENCE_SPAN_M, 1.0), MAX_SCALE)


def _derived(options: BasemapStyle, factor: float) -> dict[str, Any]:
    """The generalisation thresholds actually used, for the notes column."""
    return {
        "scale": round(factor, 2),
        "road_eps_m": round(10.0 * factor, 1),
        "wood_eps_m": round(22.0 * factor, 1),
        "river_eps_m": round(12.0 * factor, 1),
        "interaction_m": round(min(options.interaction_m * factor, 200.0), 1),
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


def basemap(
    key: str,
    lat: list[float],
    lng: list[float],
    options: BasemapStyle | None = None,
    route: list[Pt] | None = None,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
    clip_margin_m: float = 900.0,
) -> dict[str, Any] | None:
    """Assemble every basemap layer for one activity from the cache.

    Args:
        key: The activity, naming the two cache files.
        lat: Track latitudes in recorded order.
        lng: Track longitudes, same length.
        options: What to draw. The defaults are the basemap group's own.
        route: The already-projected track, when the caller has one. The
            snapshot's route is simplified before its origin is taken, so a road
            projected from scratch could sit a metre or two off the track it
            runs beside; passing the route pins the two to the same origin.
        cache_dir: Where the cached payloads live.
        places: User-supplied places of interest.
        clip_margin_m: Metres of ground kept around the track's bounding box
            when drawing, before the box's scale is applied.

    Returns:
        Layers in route metre space, or None when nothing is cached for this
        box, which is the renderer's signal to draw the bare track and say so.
    """
    from pyntpot.maps.projection import track_projection
    from pyntpot.maps.style_groups import BasemapStyle
    from pyntpot.maps.track_index import TrackIndex, _densify

    options = options or BasemapStyle()
    osm_file = overpass_path(key, cache_dir)
    elev_file = elevation_path(key, cache_dir)
    if not osm_file.exists() and not elev_file.exists():
        return None
    proj, pts = track_projection(lat, lng, route)
    xs = [x for x, _ in pts]
    ys = [y for _, y in pts]
    span = max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    factor = scale_for(span)
    derived = _derived(options, factor)
    margin = clip_margin_m * factor
    clip = (min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin)
    out: dict[str, Any] = {
        "id": key,
        "clip": [round(v, 1) for v in clip],
        "bounds": [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)],
        "span_m": round(span),
        "derived": derived,
        "sources": [],
    }
    # Simplified so the index is small, then densified so it is honest: the
    # index measures distance to a vertex, and a straight kilometre simplifies
    # to two of them, which would put a road running beside it half a field away.
    index = TrackIndex(_densify(simplify(pts, 6.0), 15.0))
    if osm_file.exists():
        out.update(_osm_layers(osm_file, proj, clip, index, options, derived))
        out["sources"].append(f"OSM via Overpass, {osm_file.stat().st_size // 1024} KB cached")
    if elev_file.exists():
        out.update(_relief_layers(elev_file, proj, clip, options, derived, index))
        out["sources"].append("SRTM 30 m via OpenTopoData")
    out["places"] = _place_marks(places, proj, clip)
    from pyntpot.maps.candidates.landmarks import pick_landmarks

    out["landmarks"] = pick_landmarks(
        out.get("landmark_candidates", []),
        mode=options.landmarks,
        radius_m=derived["landmark_radius_m"],
        cap=derived["landmark_cap"],
        picks=options.pick_landmarks,
    )
    return out


def _place_marks(
    places: list[dict[str, Any]], proj: Projection, clip: tuple[float, float, float, float]
) -> list[dict[str, Any]]:
    """Project the supplied places, keeping the ones inside the sheet."""
    xmin, ymin, xmax, ymax = clip
    out = []
    for place in places:
        if "lat" not in place or "lng" not in place:
            continue
        x, y = proj(float(place["lat"]), float(place["lng"]))
        if not (xmin <= x <= xmax and ymin <= y <= ymax):
            continue
        # `kind` and `always_label` are optional and default to what the file
        # has always meant: a glyph named by `symbol`, with the name under it,
        # chosen by the score like anything else. A `settlement` entry draws no
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


def _relief_layers(
    path: Path,
    proj: Projection,
    clip: tuple[float, float, float, float],
    options: BasemapStyle,
    derived: dict[str, Any],
    index: TrackIndex | None = None,
) -> dict[str, Any]:
    """Every relief and water layer the SRTM grid can carry."""
    from pyntpot.maps.contours import contour_lines, sea_rings
    from pyntpot.maps.relief import Terrain, hillshade_png, shade_bands
    from pyntpot.maps.relief_strokes import Field, Hatching, hachures, wave_strokes

    data = json.loads(path.read_text())
    n = data["n"]
    values = data["elev"]
    grid = [[float(v) for v in values[r * n : (r + 1) * n]] for r in range(n)]
    lats, lons = data["lats"], data["lons"]
    dx = (lons[1] - lons[0]) * proj.kx
    dy = (lats[1] - lats[0]) * proj.ky
    x0, y0 = proj(lats[0], lons[0])
    x1, y1 = proj(lats[-1], lons[-1])
    water, islands = sea_rings(grid, lats, lons, proj)
    flat = [v for row in grid for v in row]
    mode = options.hillshade_mode
    every = options.all_variants
    out: dict[str, Any] = {
        "hillshade_bands": [],
        "hillshade_raster": None,
        "hachures": [],
        "contours": [],
        "sea_waves": "",
        "sea": _sea_path(water, islands, clip, options, derived),
        "elevation": {"min": round(min(flat)), "max": round(max(flat)), "grid": n},
    }
    if every or mode == "bands":
        levels = 2 if options.generalise else max(3, min(8, options.hillshade_levels))
        out["hillshade_bands"] = shade_bands(
            Terrain(grid, lats, lons, proj, dx, dy),
            levels=levels,
            eps=derived["cell_m"] * 0.8 if options.generalise else derived["wood_eps_m"] * 0.6,
        )
    if every or mode == "raster":
        href, width, height = hillshade_png(grid, dx, dy)
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
            grid, lats, lons, proj, options.contour_interval, eps=derived["river_eps_m"] * 1.4
        )
    field = Field(grid, lats, lons, proj)
    if every or mode == "hachures":
        out["hachures"] = hachures(
            field,
            clip,
            index,
            Hatching(
                spacing_m=derived["hachure_spacing_m"],
                min_slope=options.hachure_min_slope,
                max_length_m=derived["hachure_length_m"],
            ),
        )
    if out["sea"]["d"] and (every or options.sea_style == "waves"):
        out["sea_waves"] = wave_strokes(
            field,
            clip,
            spacing_m=derived["hachure_spacing_m"] * 2.4,
            length_m=derived["hachure_length_m"] * 0.8,
        )
    return out


def _soften(line: list[Pt], eps: float, options: BasemapStyle) -> list[Pt]:
    """Simplify a line, then round its corners off.

    A road drawn from OSM nodes is a survey; two Chaikin passes make it a line
    someone drew, which is what the rest of the sheet now looks like.
    """
    out = simplify(line, eps)
    if options.generalise and options.smooth_passes:
        # Chaikin quadruples the points, so the curve is simplified again at a
        # tolerance it cannot see: the line stays round and the layer stays small.
        out = simplify(smooth(out, passes=min(2, options.smooth_passes), closed=False), eps * 0.3)
    return out


def _sea_path(
    water: list[list[Pt]],
    islands: list[list[Pt]],
    clip: tuple[float, float, float, float],
    options: BasemapStyle,
    derived: dict[str, Any],
) -> dict[str, str]:
    """The sea as one wash, with a lighter dry-brush edge pulled in from it."""
    from pyntpot.maps.generalise import Finish, Generalisation, generalise_layer
    from pyntpot.maps.rings import clip_ring
    from pyntpot.maps.svg_path import path_d, rings_path

    cut = [clip_ring(r, clip) for r in water]
    holes = [clip_ring(r, clip) for r in islands]
    if not options.generalise:
        return {"d": rings_path(cut, holes), "inner": ""}
    layer = generalise_layer(
        [r for r in cut if len(r) > 2],
        [r for r in holes if len(r) > 2],
        clip,
        Generalisation(
            derived["cell_m"],
            options.morph_cells,
            derived["min_area_ha"],
            options.smooth_passes,
        ),
        Finish(
            jitter_m=derived["blob_jitter_m"] * 0.6,
            inset_cells=options.inset_cells,
            seed=4,
        ),
    )
    return {
        "d": "".join(path_d(r, close=True) for r in layer["outer"]),
        "inner": "".join(path_d(r, close=True) for r in layer["inner"]),
    }


def _osm_layers(
    path: Path,
    proj: Projection,
    clip: tuple[float, float, float, float],
    index: TrackIndex,
    options: BasemapStyle,
    derived: dict[str, Any],
) -> dict[str, Any]:
    """Group the cached Overpass payload into the map's layers.

    Every filled layer comes back as one path wound for `fill-rule="nonzero"`,
    so two woods that overlap fill once rather than stacking their alpha into a
    patch that reads as a third thing.

    Args:
        path: The cached Overpass payload.
        proj: The activity's projection.
        clip: (xmin, ymin, xmax, ymax) in metres; everything is cut to it.
        index: The track, for the interaction tests.
        options: What to draw.
        derived: The scale-aware thresholds from `_derived`.

    Returns:
        The vector layers, in metres.
    """
    from pyntpot.maps.candidates.landmark_classes import OFFERED_CLASSES, classify
    from pyntpot.maps.generalise import Finish, Generalisation, generalise_layer
    from pyntpot.maps.rings import clip_ring
    from pyntpot.maps.svg_path import path_d, rings_path

    payload = json.loads(path.read_text())
    within = derived["interaction_m"]
    run_m = derived["interaction_run_m"]
    road_eps = derived["road_eps_m"]
    wood_eps = derived["wood_eps_m"]
    river_eps = derived["river_eps_m"]
    xmin, ymin, xmax, ymax = clip

    wood: list[list[Pt]] = []
    wood_holes: list[list[Pt]] = []
    park: list[list[Pt]] = []
    lakes: list[list[Pt]] = []
    sea_polys: list[list[Pt]] = []
    roads: list[dict[str, Any]] = []
    # Every way of one road, and whether any of it earned the road a place.
    ways: dict[tuple[str, str], list[dict[str, Any]]] = {}
    road_keep: dict[tuple[str, str], bool] = {}
    rivers: list[dict[str, Any]] = []
    # Metres of each watercourse OSM tags as underground, against its whole run.
    under: dict[str, float] = {}
    overall: dict[str, float] = {}
    coast: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    counts: dict[str, int] = {"road_dropped": 0, "stream_dropped": 0, "wood_relations": 0}

    def area_rings(entry: dict[str, Any], eps: float) -> Rings:
        outer, inner = _polygon_rings(entry, proj)
        cut = [clip_ring(r, clip) for r in outer]
        holes = [clip_ring(r, clip) for r in inner]
        return (
            [simplify(r, eps) for r in cut if len(r) > 3],
            [simplify(r, eps) for r in holes if len(r) > 3],
        )

    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        name = tags.get("name", "")
        if entry.get("type") == "node":
            x, y = proj(entry["lat"], entry["lon"])
            if not (xmin <= x <= xmax and ymin <= y <= ymax):
                continue
            candidates.append(
                {
                    "n": name,
                    "cls": classify(tags),
                    "x": round(x, 1),
                    "y": round(y, 1),
                    "d": round(index.distance(x, y, cap_m=3000.0)),
                    "tags": {k: v for k, v in tags.items() if k in LANDMARK_TAG_KEYS},
                }
            )
            continue
        highway = tags.get("highway")
        waterway = tags.get("waterway")
        if highway:
            major = highway in MAJOR_ROADS
            ref = str(tags.get("ref") or "")
            # Kept or dropped per *road*, not per way. OSM cuts a street at
            # every junction, and the interaction test was answered separately
            # for each cut: the block that crosses the route was kept and the
            # next block along was not, so every side street came off the route
            # as a stub and the sheet read as a comb. A road the session ran
            # along or across is on the card for as long as the card holds it.
            # A way with neither a number nor a name has no road to belong to,
            # so it is still decided on its own.
            road = (ref or name or f"~{entry.get('id')}", highway)
            for piece in clip_line(_geom(entry, proj), clip):
                line = _soften(piece, road_eps, options)
                if len(line) < 2:
                    continue
                ways.setdefault(road, []).append(
                    {
                        "c": "major" if major else "minor",
                        "n": name,
                        # The road number, which is what a map calls a road:
                        # "A66" says where the route went and "Lake Road"
                        # says nothing at 26 m a pixel.
                        "r": ref,
                        "k": highway,
                        "d": path_d(line),
                    }
                )
                if road not in road_keep:
                    road_keep[road] = options.roads == "all" or major or name in options.pick_roads
                if not road_keep[road] and options.roads == "key":
                    road_keep[road] = index.interacts(piece, within, run_m)
        elif waterway in ("river", "stream"):
            buried = bool(tags.get("tunnel"))
            for piece in clip_line(_geom(entry, proj), clip):
                river = waterway == "river"
                keep = (
                    options.rivers == "all"
                    or river
                    or (options.rivers == "key" and index.interacts(piece, within, run_m))
                )
                if not keep:
                    counts["stream_dropped"] += 1
                    continue
                line = _soften(piece, river_eps, options)
                if len(line) < 2:
                    continue
                # How much of this watercourse OSM says is underground, gathered
                # by name so the question is asked of the river and not of each
                # way. A river passing under one bridge is not a buried river.
                run = length(line)
                key = name or f"~{entry.get('id')}"
                under[key] = under.get(key, 0.0) + (run if buried else 0.0)
                overall[key] = overall.get(key, 0.0) + run
                rivers.append(
                    {"c": "river" if river else "stream", "n": name, "k": key, "d": path_d(line)}
                )
        elif tags.get("natural") == "coastline":
            for piece in clip_line(_geom(entry, proj), clip):
                line = _soften(piece, river_eps * 0.6, options)
                if len(line) > 1:
                    coast.append({"n": name, "d": path_d(line)})
        elif tags.get("landuse") == "forest" or tags.get("natural") == "wood":
            outer, inner = area_rings(entry, wood_eps)
            if entry.get("type") == "relation" and outer:
                counts["wood_relations"] += 1
            wood += outer
            wood_holes += inner
        elif tags.get("boundary") in ("national_park", "protected_area"):
            outer, _ = area_rings(entry, wood_eps * 1.6)
            park += outer
        elif tags.get("natural") in ("water", "bay"):
            outer, _ = area_rings(entry, river_eps)
            target = sea_polys if tags.get("natural") == "bay" else lakes
            target += outer
        # A named area whose tags make it a landmark, at its own centre. History
        # was the only kind of way that could become one, so every named
        # building, bridge and church in the box was drawn and never offered;
        # and a relation could not become one at all, so a card could name a
        # statue and not the zoo the statue stands in. OSM holds a zoo as a
        # multipolygon, and a multipolygon is a relation.
        if name and entry.get("type") in ("way", "relation") and classify(tags) in OFFERED_CLASSES:
            rings, _holes = _polygon_rings(entry, proj)
            pts = [p for ring in rings for p in ring] if rings else _geom(entry, proj)
            if pts:
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                if xmin <= cx <= xmax and ymin <= cy <= ymax:
                    candidates.append(
                        {
                            "n": name,
                            "cls": classify(tags),
                            "x": round(cx, 1),
                            "y": round(cy, 1),
                            "d": round(index.distance(cx, cy, cap_m=3000.0)),
                            "tags": {k: v for k, v in tags.items() if k in LANDMARK_TAG_KEYS},
                        }
                    )
    for road, entries in ways.items():
        if road_keep.get(road):
            roads += entries
        else:
            counts["road_dropped"] += len(entries)
    # **A buried river is not on the ground, so it is not drawn.** OSM maps a
    # buried river as a watercourse because it still flows; it runs in a sewer
    # under a street and there is nothing to see. The test is per watercourse
    # and by length, not per way: a river that passes under one short culvert
    # out of thirteen ways stays whole, and one that is `tunnel=yes` end to end
    # goes.
    gone = {
        key for key, run in overall.items() if run > 0 and under.get(key, 0.0) / run >= BURIED_FRAC
    }
    counts["river_buried"] = sum(1 for r in rivers if r["k"] in gone)
    rivers = [{k: v for k, v in r.items() if k != "k"} for r in rivers if r["k"] not in gone]
    wood_inner, trees = "", []
    if options.generalise:
        cell = derived["cell_m"]
        layer = generalise_layer(
            wood,
            wood_holes,
            clip,
            Generalisation(
                cell,
                options.morph_cells,
                derived["min_area_ha"],
                options.smooth_passes,
            ),
            Finish(
                jitter_m=derived["blob_jitter_m"],
                inset_cells=options.inset_cells,
                seed_spacing_m=derived["tree_spacing_m"],
            ),
        )
        wood_path = "".join(path_d(r, close=True) for r in layer["outer"])
        wood_inner = "".join(path_d(r, close=True) for r in layer["inner"])
        trees = layer["seeds"]
        wood_n = len(layer["outer"])
        park_layer = generalise_layer(
            park,
            [],
            clip,
            Generalisation(
                cell * 1.5,
                options.morph_cells,
                derived["min_area_ha"] * 3,
                options.smooth_passes,
            ),
            Finish(jitter_m=derived["blob_jitter_m"], inset_cells=0, seed=9),
        )
        park_path = "".join(path_d(r, close=True) for r in park_layer["outer"])
        park_n = len(park_layer["outer"])
    else:
        wood_path, wood_n = rings_path(wood, wood_holes), len(wood)
        park_path, park_n = rings_path(park), len(park)
    return {
        "wood": {"d": wood_path, "inner": wood_inner, "n": wood_n},
        "trees": trees,
        "park": {"d": park_path, "n": park_n},
        "water_area": {"d": rings_path(lakes), "n": len(lakes)},
        "sea_osm": {"d": rings_path(sea_polys), "n": len(sea_polys)},
        "coastline": coast,
        "roads": roads,
        "rivers": rivers,
        "landmark_candidates": _dedupe(candidates),
        "counts": counts,
    }


def _dedupe(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One entry per named thing, nearest the track kept."""
    best: dict[str, dict[str, Any]] = {}
    loose: list[dict[str, Any]] = []
    for entry in sorted(candidates, key=lambda c: c["d"]):
        if not entry["n"]:
            loose.append(entry)
        elif entry["n"] not in best:
            best[entry["n"]] = entry
    return sorted(list(best.values()) + loose, key=lambda c: c["d"])


# --------------------------------------------------------------------------- hachures


# --------------------------------------------------------------------------- generalise


# --------------------------------------------------------------------------- land cover

#: The land cover classes the journal map paints. The renderer's own Overpass
#: query asks for wood, water and roads and nothing else, so the cache cannot
#: say what the ground between them is; this is the second query that can.
LANDCOVER_LANDUSE = (
    "farmland|meadow|grass|orchard|vineyard|allotments|"
    "village_green|recreation_ground|cemetery|residential|"
    "industrial|commercial|retail|quarry|farmyard|"
    "greenhouse_horticulture"
)
LANDCOVER_NATURAL = "grassland|heath|moor|scrub|wetland|bare_rock|beach|sand|shingle|cliff|scree"
LANDCOVER_LEISURE = "park|golf_course|nature_reserve|pitch|garden"

LANDCOVER_QUERY = """[out:json][timeout:300];
(
  way["landuse"~"^({landuse})$"]({box});
  relation["landuse"~"^({landuse})$"]({box});
  way["natural"~"^({natural})$"]({box});
  relation["natural"~"^({natural})$"]({box});
  way["leisure"~"^({leisure})$"]({box});
  relation["leisure"~"^({leisure})$"]({box});
);
out geom;"""

#: OSM tag to pigment class. Later in this list wins where two polygons overlap,
#: so the plate carries one class per pixel and no two land pigments can stack.
COVER_TAGS: tuple[tuple[str, str, str], ...] = (
    ("landuse", "farmland", "farmland"),
    ("landuse", "farmyard", "built"),
    ("landuse", "meadow", "meadow"),
    ("landuse", "grass", "meadow"),
    ("landuse", "village_green", "meadow"),
    ("landuse", "recreation_ground", "meadow"),
    ("leisure", "park", "meadow"),
    ("leisure", "garden", "meadow"),
    ("leisure", "pitch", "meadow"),
    ("leisure", "golf_course", "meadow"),
    ("natural", "grassland", "meadow"),
    ("landuse", "orchard", "orchard"),
    ("landuse", "vineyard", "orchard"),
    ("landuse", "allotments", "orchard"),
    ("natural", "scrub", "scrub"),
    ("leisure", "nature_reserve", "scrub"),
    ("natural", "heath", "heath"),
    ("natural", "moor", "heath"),
    ("natural", "beach", "sand"),
    ("natural", "sand", "sand"),
    ("natural", "shingle", "sand"),
    ("natural", "bare_rock", "rock"),
    ("natural", "scree", "rock"),
    ("natural", "cliff", "rock"),
    ("natural", "wetland", "wetland"),
    ("landuse", "residential", "built"),
    ("landuse", "commercial", "built"),
    ("landuse", "retail", "built"),
    ("landuse", "cemetery", "built"),
    ("landuse", "industrial", "works"),
    ("landuse", "quarry", "works"),
    ("landuse", "greenhouse_horticulture", "works"),
    ("landuse", "forest", "wood"),
    ("natural", "wood", "wood"),
)

#: Painting order, low to high. A wood drawn over farmland replaces it.
COVER_ORDER: tuple[str, ...] = (
    "farmland",
    "meadow",
    "orchard",
    "scrub",
    "heath",
    "sand",
    "rock",
    "wetland",
    "built",
    "works",
    "wood",
)

#: Ground kept around the track when fetching land cover. Wider than the
#: feature margin, because the painted card is grown by a ribbon radius first.
LANDCOVER_MARGIN_M = 2600.0


def landcover_path(key: str, cache_dir: Path) -> Path:
    """Where the land cover payload for one activity is cached."""
    return cache_dir / f"landcover-{key}.json"


def fetch_landcover(box: tuple[float, float, float, float], path: Path) -> int:
    """Fetch the land cover classes for one bounding box into the cache.

    Args:
        box: (south, west, north, east) in degrees.
        path: Cache file to write.

    Returns:
        Bytes written.

    Raises:
        RuntimeError: When every mirror refused the query.
    """
    query = LANDCOVER_QUERY.format(
        box=",".join(f"{value:f}" for value in box),
        landuse=LANDCOVER_LANDUSE,
        natural=LANDCOVER_NATURAL,
        leisure=LANDCOVER_LEISURE,
    )
    text = ""
    for attempt in range(3):
        for url in OVERPASS_URLS:
            try:
                text = _get(url, data={"data": query}, timeout=300.0)
                json.loads(text)
            except Exception as exc:  # a mirror under load is not a failed fetch
                log.info("landcover %s attempt %d: %s", url, attempt + 1, exc)
                text = ""
                time.sleep(4.0)
                continue
            break
        if text:
            break
    if not text:
        raise RuntimeError("every Overpass mirror refused the land cover query")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.stat().st_size


def cover_rings(
    key: str, proj: Projection, clip: tuple[float, float, float, float], eps: float, cache_dir: Path
) -> dict[str, list[list[Pt]]]:
    """Land cover rings by pigment class, clipped to the card and simplified.

    Args:
        key: The activity, naming the cache file.
        proj: The activity's projection.
        clip: The card, in metres.
        eps: Simplification tolerance in metres.
        cache_dir: Where the payload lives.

    Returns:
        Rings by class; empty when there is no land cover cached.
    """
    from pyntpot.maps.rings import clip_ring

    path = landcover_path(key, cache_dir)
    out: dict[str, list[list[Pt]]] = {}
    if not path.exists():
        return out
    lookup = {(key, value): cls for key, value, cls in COVER_TAGS}
    payload = json.loads(path.read_text())
    for entry in payload.get("elements", []):
        tags = entry.get("tags") or {}
        cls = None
        for tag_key in ("landuse", "natural", "leisure"):
            if tag_key in tags:
                cls = lookup.get((tag_key, tags[tag_key]), cls)
        if cls is None:
            continue
        outer, _inner = _polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > 3:
                out.setdefault(cls, []).append(simplify(cut, eps))
    return out


def wood_rings(
    key: str, proj: Projection, clip: tuple[float, float, float, float], eps: float, cache_dir: Path
) -> list[list[Pt]]:
    """Wood rings straight from the renderer's own Overpass cache."""
    from pyntpot.maps.rings import clip_ring

    path = overpass_path(key, cache_dir)
    rings: list[list[Pt]] = []
    if not path.exists():
        return rings
    for entry in json.loads(path.read_text()).get("elements", []):
        tags = entry.get("tags") or {}
        if tags.get("landuse") != "forest" and tags.get("natural") != "wood":
            continue
        outer, _ = _polygon_rings(entry, proj)
        for ring in outer:
            cut = clip_ring(ring, clip)
            if len(cut) > 3:
                rings.append(simplify(cut, eps))
    return rings


def coastline_chains(
    key: str,
    proj: Projection,
    clip: tuple[float, float, float, float],
    cache_dir: Path,
    min_length_m: float = 300.0,
) -> list[list[Pt]]:
    """Coastline ways as surveyed: clipped, joined, and never smoothed.

    The coast is the one line on the sheet a reader would notice being wrong,
    so it keeps its own vertices. Offshore rocks come back as their own
    little rings and are ink specks at plate size, so only chains of real coast
    are kept.
    """
    path = overpass_path(key, cache_dir)
    if not path.exists():
        return []
    ways: list[list[Pt]] = []
    for entry in json.loads(path.read_text()).get("elements", []):
        if (entry.get("tags") or {}).get("natural") != "coastline":
            continue
        pts = [proj(g["lat"], g["lon"]) for g in entry.get("geometry", []) if g]
        ways += [p for p in clip_line(pts, clip) if len(p) > 1]
    joined = [c for c in join_chains(ways, tol=2.0) if len(c) > 3]
    return [
        c
        for c in joined
        if sum(math.dist(c[i], c[i + 1]) for i in range(len(c) - 1)) > min_length_m
    ]


def sea_from_coast(
    chains: list[list[Pt]], clip: tuple[float, float, float, float]
) -> list[list[Pt]]:
    """Close a coastline chain around the card edge to make the sea.

    OSM draws a coastline with the land on its left, so the sea is the side the
    right-hand normal points at. Both closures round the card are built and the
    one that holds most of a set of probes just off the coast is the sea: one
    probe is not enough, because a cove puts a single right-hand normal back on
    land.

    Args:
        chains: Coastline chains in metres, already clipped to the card.
        clip: The card, in metres.

    Returns:
        One closed ring, or an empty list when no chain crosses the card.
    """
    from pyntpot.maps.rings import point_in_ring

    xmin, ymin, xmax, ymax = clip
    corners = [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)]

    def perimeter_t(p: Pt) -> float:
        """Position of a point on the card edge, 0 to 4, anticlockwise."""
        x, y = p
        if abs(y - ymin) < 1e-6:
            return (x - xmin) / max(xmax - xmin, 1e-6)
        if abs(x - xmax) < 1e-6:
            return 1 + (y - ymin) / max(ymax - ymin, 1e-6)
        if abs(y - ymax) < 1e-6:
            return 2 + (xmax - x) / max(xmax - xmin, 1e-6)
        return 3 + (ymax - y) / max(ymax - ymin, 1e-6)

    def arc(t0: float, t1: float, forward: bool) -> list[Pt]:
        """The card corners passed walking the edge from t0 to t1."""
        out: list[Pt] = []
        t = t0
        for _ in range(5):
            nxt = (math.floor(t) + 1) if forward else (math.ceil(t) - 1)
            gap = (nxt - t) % 4 if forward else (t - nxt) % 4
            want = (t1 - t) % 4 if forward else (t - t1) % 4
            if gap >= want or gap <= 1e-9:
                break
            out.append(corners[int(nxt) % 4])
            t = nxt % 4
        return out

    def length(chain: list[Pt]) -> float:
        return sum(math.dist(chain[i], chain[i + 1]) for i in range(len(chain) - 1))

    def edge_gap(p: Pt) -> float:
        return min(abs(p[0] - xmin), abs(p[0] - xmax), abs(p[1] - ymin), abs(p[1] - ymax))

    def snap(p: Pt) -> Pt:
        """Put an endpoint exactly on the card edge it was clipped against."""
        x, y = p
        gaps = [
            (abs(x - xmin), (xmin, y)),
            (abs(x - xmax), (xmax, y)),
            (abs(y - ymin), (x, ymin)),
            (abs(y - ymax), (x, ymax)),
        ]
        return min(gaps)[1]

    open_chains = [
        c for c in chains if len(c) > 3 and edge_gap(c[0]) < 30.0 and edge_gap(c[-1]) < 30.0
    ]
    open_chains = [[snap(c[0])] + c[1:-1] + [snap(c[-1])] for c in open_chains]
    if not open_chains:
        return []
    chain = max(open_chains, key=length)
    probes: list[Pt] = []
    for k in range(1, 20):
        i = max(min(len(chain) * k // 20, len(chain) - 2), 0)
        dx, dy = chain[i + 1][0] - chain[i][0], chain[i + 1][1] - chain[i][1]
        n = math.hypot(dx, dy)
        if n < 1e-6:
            continue
        probes.append((chain[i][0] + dy / n * 70.0, chain[i][1] - dx / n * 70.0))
    t0, t1 = perimeter_t(chain[-1]), perimeter_t(chain[0])
    best, best_score = None, -1
    for forward in (True, False):
        ring = chain + arc(t0, t1, forward)
        if len(ring) < 4:
            continue
        score = sum(1 for p in probes if point_in_ring(p[0], p[1], ring))
        if score > best_score:
            best, best_score = ring, score
    if best is None or best_score <= len(probes) * 0.5:
        return []
    return [best]


# --------------------------------------------------------------------------- the card


def journal_geometry(
    route: list[Pt], card: CardStyle, ribbon: RibbonStyle, brush: BrushStyle
) -> dict[str, Any]:
    """The card, its ribbon radius, and every size the plate is painted at.

    Every size on the sheet is derived from this, so a 13 km box and a 3 km box
    are drawn with the same weights on screen rather than the same weights on
    the ground. The ribbon is a constant times the square root of the box plus
    a small-box offset: that keeps a generous ribbon on a small box without
    swelling it to the whole sheet on a big one.

    Args:
        route: The track in metres.
        card: The card's display size and supersampling.
        ribbon: The ribbon's fit and the card's framing.
        brush: The widths and thresholds the sizes on the sheet are stated in.

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
    ribbon_radius = fitted * ribbon.ribbon_mult
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
    w, h = cx1 - cx0, cy1 - cy0
    display_w = int(card.display_px)
    render_w = display_w * int(card.supersample)
    render_h = int(round(render_w * h / w))
    mpp = w / render_w
    disp = mpp * card.supersample
    return {
        "card": [round(cx0, 1), round(cy0, 1), round(cx1, 1), round(cy1, 1)],
        "bounds": [round(bx0, 1), round(by0, 1), round(bx1, 1), round(by1, 1)],
        "span_m": round(span),
        "ribbon_m": round(ribbon_radius),
        "ribbon_fitted_m": round(fitted),
        "render": [render_w, render_h],
        "display": [display_w, int(round(render_h / card.supersample))],
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


def _line(points: list[Pt]) -> Line:
    """A polyline as the basemap carries it: float pairs at full precision."""
    return tuple((float(x), float(y)) for x, y in points)


def _drawn(piece: list[Pt], tol: float) -> Line:
    """Simplify, then Chaikin: a line someone drew, not a line surveyed."""
    return _line(smooth(simplify(piece, tol), passes=2))


def _elevation_patch(key: str, proj: Projection, cache_dir: Path) -> ElevationPatch | None:
    """The cached elevation grid placed in card metres, or None when none is cached."""
    from pyntpot.maps.basemap import ElevationPatch

    elev = elevation_path(key, cache_dir)
    if not elev.exists():
        return None
    grid = json.loads(elev.read_text())
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


def journal_layers(
    key: str,
    lat: list[float],
    lng: list[float],
    card_style: CardStyle,
    ribbon_style: RibbonStyle,
    brush: BrushStyle,
    route: list[Pt] | None = None,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
    basemap_style: BasemapStyle,
) -> Basemap | None:
    """Everything the painter needs for one activity, from the cache.

    The land cover, the coast and the sea come from the two cached Overpass
    payloads; the roads and the watercourses come through `basemap`, so the
    same interaction rules decide what is drawn here as on the vector map.

    Args:
        key: The activity, naming the cache files.
        lat: Track latitudes in recorded order.
        lng: Track longitudes, same length.
        card_style: The card's display size and supersampling.
        ribbon_style: The ribbon's fit and the card's framing.
        brush: The brushes and widths the card's sizes are stated in.
        route: The already-projected track, when the caller has one.
        cache_dir: Where the cached payloads live.
        places: User-supplied places of interest.
        basemap_style: What the basemap draws; the clip margin is the card's
            own longer side, derived here.

    Returns:
        The basemap in card metres, or None when nothing is cached for this box.
    """
    from pyntpot.maps.basemap import Basemap, Layers, River, Road
    from pyntpot.maps.candidates.landmarks import rank_landmarks
    from pyntpot.maps.card import Card
    from pyntpot.maps.projection import track_projection
    from pyntpot.maps.rings import clip_ring
    from pyntpot.maps.rivers import CHANNEL_EASE_SAMPLES, channel, major_rivers, painted_width_px
    from pyntpot.maps.svg_path import parse_path

    if not overpass_path(key, cache_dir).exists():
        return None
    proj, pts = track_projection(lat, lng, route)
    track = simplify(pts, 3.0)
    geometry = journal_geometry(track, card_style, ribbon_style, brush)
    clip = tuple(geometry["card"])
    eps = max(geometry["mpp"] * 1.1, 2.0)

    base = basemap(
        key,
        lat,
        lng,
        options=basemap_style,
        cache_dir=cache_dir,
        places=places,
        route=track,
        clip_margin_m=max(clip[2] - clip[0], clip[3] - clip[1]),
    )
    if base is None:
        return None

    cover = cover_rings(key, proj, clip, eps, cache_dir)
    wood = wood_rings(key, proj, clip, eps, cache_dir)
    if wood:
        cover["wood"] = cover.get("wood", []) + wood
    coast = coastline_chains(key, proj, clip, cache_dir)
    sea = sea_from_coast(coast, clip)

    # Three brushes' worth of road: the A and B roads, the lanes, and the tracks
    # the session actually used, which get the scratchy dry brush.
    #
    # A street is one stroke. OSM hands it over cut at every junction, and
    # painting each cut as its own stroke gave every one of them a set-down blot
    # and a taper at both ends: `join_strokes` chains the pieces of one road
    # back together first, so the brush is set down where the street starts and
    # lifted where it ends.
    pieces: dict[tuple[Any, ...], list[list[Pt]]] = {}
    meta: dict[tuple[Any, ...], dict[str, Any]] = {}
    for r in base.get("roads", []):
        if r["c"] == "major":
            band = "major"
        elif r["k"] in ("track", "path", "footway", "bridleway"):
            band = "path"
        else:
            band = "minor"
        # What counts as one road: its band, and the name or number it is known
        # by. Unnamed pieces of a band are one group and chain on their ends
        # alone, which is the right answer for a pavement network that has no
        # names to gather by.
        road_key = (band, r["n"], r.get("r", ""))
        meta.setdefault(
            road_key, {"c": r["c"], "b": band, "k": r["k"], "n": r["n"], "r": r.get("r", "")}
        )
        for seg in parse_path(r["d"]):
            pieces.setdefault(road_key, []).extend(c for c in clip_line(seg, clip) if len(c) > 1)
    # And a stroke shorter than the brush that would draw it is a dab, not a
    # road. What is left after the chaining is mostly a slip lane or a link at a
    # junction that the chain could not take because it took the carriageway
    # instead: a hundred of them can be under one display pixel long, and each
    # still pays for a set-down blot the size of the brush.
    band_width = {"major": "road_major", "minor": "lane", "path": "track"}
    roads = []
    for road_key, lines in pieces.items():
        band = road_key[0]
        floor = brush.brush_width_px.get(band_width[band], 2.0) * geometry["mpp_display"]
        info = meta[road_key]
        for chain in join_strokes(lines, tol=max(eps, 1.0)):
            if length(chain) < floor:
                continue
            roads.append(
                Road(
                    line=_drawn(chain, eps),
                    cls=info["c"],
                    band=info["b"],
                    highway=info["k"],
                    name=info["n"],
                    ref=info["r"],
                )
            )

    lakes = [
        simplify(clip_ring(r, clip), eps)
        for r in parse_path(base.get("water_area", {}).get("d", ""))
    ]

    # The pieces of each watercourse, gathered by name so it is measured and
    # classed as one river rather than as the dozen ways OSM cut it into.
    pieces_by: dict[str, list[list[Pt]]] = {}
    for r in base.get("rivers", []):
        for seg in parse_path(r["d"]):
            pieces_by.setdefault(r["n"], []).extend(c for c in clip_line(seg, clip) if len(c) > 1)

    major, widths = major_rivers(pieces_by, lakes, brush.major_river_rel_frac)
    classed = {
        r["n"]: (("major" if r["n"] in major else "medium") if r["c"] == "river" else "minor")
        for r in base.get("rivers", [])
    }
    rivers = []
    for name, lines in pieces_by.items():
        cls = classed.get(name, "minor")
        floor = geometry["wet_px"].get(cls, 2.2)
        # The pieces of one watercourse are chained before they are measured or
        # drawn, exactly as a road's are, so the width runs continuously along
        # the river rather than restarting at every way OSM cut it at.
        for chain in join_strokes(lines, tol=max(eps, 1.0)):
            entry: dict[str, Any] = {"c": cls, "n": name, "w": floor, "wn": floor}
            if name in widths:
                # Re-centred in its own channel, and drawn at the width it
                # measures at each point rather than at one width throughout.
                centred, along = channel(chain, lakes)
                profile = [
                    painted_width_px(floor, w or 0.0, geometry["mpp_display"]) for w in along
                ]
                profile = eased(profile, CHANNEL_EASE_SAMPLES)
                widest = max(profile)
                entry["w"] = round(widest, 2)
                # And the width it is *typically* drawn at, which is the one a
                # name has to fit inside: `w` is the widest point and says how
                # far a name lifted clear of the water has to be lifted, but a
                # name set on the water could be set anywhere along it.
                entry["wn"] = round(sorted(profile)[len(profile) // 2], 2)
                entry["wp"] = [round(v / widest, 3) for v in profile]
                chain = centred
            rivers.append(
                River(
                    line=_drawn(chain, eps * 0.6),
                    cls=entry["c"],
                    name=entry["n"],
                    width_px=entry["w"],
                    name_width_px=entry["wn"],
                    profile=tuple(entry.get("wp", ())),
                )
            )

    layers = Layers(
        route=_line(track),
        cover={k: tuple(_line(r) for r in v) for k, v in cover.items()},
        cover_order=tuple(c for c in COVER_ORDER if c in cover),
        lakes=tuple(_line(r) for r in lakes if len(r) > 3),
        sea=tuple(_line(r) for r in sea),
        coastline=tuple(_line(c) for c in coast),
        roads=tuple(roads),
        rivers=tuple(rivers),
        elevation=_elevation_patch(key, proj, cache_dir),
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


#: Metres of ground kept around the track's bounding box for the candidates.
CANDIDATE_CLIP_MARGIN_M = 2600.0


def candidate_basemap() -> BasemapStyle:
    """What `landmark_export` draws: every landmark, no relief, no generalisation."""
    from pyntpot.maps.candidates.landmark_classes import LANDMARK_CAP
    from pyntpot.maps.style_groups import BasemapStyle

    return replace(
        BasemapStyle(),
        hillshade_mode="off",
        landmarks="all",
        landmark_max=LANDMARK_CAP,
        generalise=False,
    )


def landmark_export(
    key: str,
    lat: list[float],
    lng: list[float],
    ele: list[float] | None = None,
    style: Any = None,
    route: list[Pt] | None = None,
    *,
    cache_dir: Path,
    places: list[dict[str, Any]],
) -> dict[str, Any]:
    """What the label agent reads: where the session went, and what is beside it.

    Nothing here chooses a landmark. It states what the box holds, where the
    session climbed, how hard each climb was and what the route passed on the
    way up it; which of them is worth a label, and what to call it, is the
    agent's judgement and is written back into the payload.

    Args:
        key: The activity, naming the cache files.
        lat: Track latitudes.
        lng: Track longitudes.
        ele: Track elevations, when the GPX carries them.
        style: The style, for the card the candidates are inside.
        route: The already-projected track, when the caller has one.
        cache_dir: Where the cached payloads live.
        places: User-supplied places of interest.

    Returns:
        `route` (the session's totals and the settlements it passed, in order),
        `climbs` (each grounded in that route) and `candidates`.
    """
    from pyntpot.maps.candidates.climbs import cumulative, rank_climbs
    from pyntpot.maps.candidates.landmarks import rank_landmarks
    from pyntpot.maps.candidates.places import ground_climbs, place_view, rank_places
    from pyntpot.maps.candidates.roads import named_roads
    from pyntpot.maps.projection import track_projection
    from pyntpot.maps.track import Track

    proj, pts = track_projection(lat, lng, route)
    line = tuple(pts)
    track = Track(lat=tuple(lat), lng=tuple(lng), ele=tuple(ele) if ele else None)
    dist = cumulative(lat, lng)
    found = rank_climbs(track, line)
    landmarks = []
    base = basemap(
        key,
        lat,
        lng,
        options=candidate_basemap(),
        cache_dir=cache_dir,
        places=places,
        route=simplify(pts, 3.0),
        clip_margin_m=CANDIDATE_CLIP_MARGIN_M,
    )
    if base is not None:
        landmarks = rank_landmarks(base.get("landmark_candidates", []), proj)
    settlements = []
    payload_path = overpass_path(key, cache_dir)
    if payload_path.exists():
        payload = json.loads(payload_path.read_text())
        passed = rank_places(payload, proj, track, line)
        settlements = [place_view(p.detail) for p in passed]
        found = ground_climbs(found, passed, landmarks, named_roads(payload, proj), track, line)
    return {
        "id": key,
        "points": len(lat),
        "route": {
            "total_km": round(dist[-1] / 1000, 2) if dist else 0.0,
            # Not the session's ascent: raw GPX sample-to-sample gain runs well
            # above the recorded figure, so the only climbing figure stated here
            # is the one this module actually defines.
            "sustained_ascent_m": round(sum(c.detail["gain_m"] for c in found)),
            "settlements": settlements,
        },
        "climbs": [dict(c.detail) for c in found],
        "candidates": [dict(c.detail) for c in landmarks],
    }
