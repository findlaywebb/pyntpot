# Lynmouth fixture

A synthetic track and the provider payloads cached for it. Used by the unit
tests and the golden parity test.

## Files

| File | What it is |
|---|---|
| `track.gpx` | Synthetic 8 km loop of 400 points through Lynmouth and Lynton, Devon. Generated, not recorded. No time, elevation or activity type. |
| `overpass-f173b2f7a20bb9d4.json` | OSM features for the feature box, from Overpass. |
| `landcover-f173b2f7a20bb9d4.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-f173b2f7a20bb9d4.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

Each payload is named `<kind>-<key>.json`, where the key is the fetch cache key
of this track with the shipped Overpass and OpenTopoData (`srtm30m`) providers,
so a cache over a copy of this directory finds every payload and fetches
nothing.

## Source

- **OSM features and land cover**: OpenStreetMap via the Overpass API at
  `https://overpass-api.de/api/interpreter`. Two queries.
- **Elevation**: SRTM 30 m (`srtm30m` dataset) via the OpenTopoData public API
  at `https://api.opentopodata.org/v1/srtm30m`. 64 calls of 100 points.
- **Fetched**: 2026-10-03.

## Bounding boxes

South, west, north, east, in degrees.

| Box | South | West | North | East |
|---|---|---|---|---|
| Track points lie inside | 51.19 | -3.88 | 51.26 | -3.80 |
| Features and elevation (track plus 1500 m) | 51.20 | -3.87 | 51.25 | -3.79 |
| Land cover (track plus 2600 m) | 51.19 | -3.89 | 51.26 | -3.77 |

Overpass returns full geometry for every way and relation touching a box, so
the two Overpass payloads hold coordinates well outside these boxes.

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the
Open Database Licence (openstreetmap.org/copyright).

The two Overpass payloads are a derivative database of OpenStreetMap and are
distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission
Global 1 arc second* [Dataset]. NASA Land Processes Distributed Active Archive
Center. https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
