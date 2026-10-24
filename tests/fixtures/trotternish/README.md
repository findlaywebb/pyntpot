# Trotternish (the Quiraing) fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

A loop of about 6.6 km on the Quiraing, Trotternish, Skye: from the car park at the Bealach Ollasgairte on the Staffin to Uig road, north along the lower path under the Quiraing to Fir Bhreugach, returning south along the escarpment top path to the car park.

The track is invented along public OpenStreetMap ways chosen by id and joined and
resampled every 20 m by `tests/fixtures/make_track.py`. It is not traced from a
recorded activity, marks no home and no personal route, and carries no time,
elevation or activity type. It is 6.58 km long, 338 points.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
as the payloads are (see Licences).

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-70696067aa04a7f8.json` | OSM features for the feature box, from Overpass. |
| `landcover-70696067aa04a7f8.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-70696067aa04a7f8.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

Each payload is named `<kind>-<key>.json`, where the key is the fetch cache key of
this track with the shipped Overpass and OpenTopoData (`srtm30m`) providers, so a
cache over a copy of this directory finds every payload and fetches nothing.

## Source

- **OSM features and land cover**: OpenStreetMap via the Overpass mirror
  `https://maps.mail.ru/osm/tools/overpass/api/interpreter` (the usual
  `overpass-api.de` resets connections from the recording environment). Two queries.
  The shipped provider's id is `overpass` whatever its endpoint, so the payloads carry
  the default key.
- **Ways**: fetched from the same mirror by `make_track.py`; ids and versions below.
- **Elevation**: SRTM 30 m (`srtm30m` dataset) via the OpenTopoData public API at
  `https://api.opentopodata.org/v1/srtm30m`. 64 calls of 100 points.
- **Contact string sent**: `https://github.com/findlaywebb/pyntpot`.
- **Fetched**: 2026-10-24.

## Bounding boxes

South, west, north, east, in degrees.

| Box | South | West | North | East |
|---|---|---|---|---|
| Track points lie inside (rounded outward to 0.01) | 57.62 | -6.30 | 57.66 | -6.27 |
| Features and elevation (track plus 1500 m) | 57.614688 | -6.316856 | 57.664973 | -6.245425 |
| Land cover (track plus 2600 m) | 57.604737 | -6.335318 | 57.674924 | -6.226963 |

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

```
313986734:8796460505:272010961,1161568389,1083622445:10803422850:2891826524,1161568388,1163885800,1163885799,1177247409,1177247408,1163885798,204004136,1083622446,1082698097,1082698097,1177247403,1177247402,35900238:419629084:419629114,260547987:419629114:2660493920,1084427269,1084427268:9937306709:3070364221,35900238:3070364221:12596196864,1360684257,35900238:419629155:419627556,1161568388,1083622445:2891826524:10803422850,1161568389,313986734:272010961:8796460505
```

| Way | Version | `highway` | `name` |
|---|---|---|---|
| 313986734 | 15 | tertiary | Quiraing Road |
| 1161568389 | 2 | footway | - |
| 1083622445 | 3 | footway | - |
| 1161568388 | 3 | path | - |
| 1163885800 | 2 | path | - |
| 1163885799 | 2 | path | - |
| 1177247409 | 1 | path | - |
| 1177247408 | 1 | path | - |
| 1163885798 | 1 | path | - |
| 204004136 | 19 | path | - |
| 1083622446 | 5 | path | - |
| 1082698097 | 1 | path | - |
| 1177247403 | 1 | path | - |
| 1177247402 | 1 | path | - |
| 35900238 | 11 | path | - |
| 260547987 | 2 | path | - |
| 1084427269 | 3 | path | - |
| 1084427268 | 3 | path | - |
| 1360684257 | 2 | path | - |

## Size

Git stores the payloads compressed and `tests/` is not shipped in a distribution, so the
budget (1.5 MB) is measured as the gzip size of each file at the default level, summed.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-70696067aa04a7f8.json` | 47,163 | 10,621 |
| `landcover-70696067aa04a7f8.json` | 447,623 | 69,494 |
| `overpass-70696067aa04a7f8.json` | 602,617 | 99,868 |
| `track.gpx` | 16,110 | 2,561 |
| **Total, README excluded** | **1,113,513** | **182,544** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
