# Oxford fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

A loop of about 2.7 km in central Oxford: Carfax, the High Street to Magdalen Bridge, Rose Lane into Christ Church Meadow, the Broad Walk, St Aldate's back to Carfax.

The track is invented along public OpenStreetMap ways chosen by id and joined and
resampled every 20 m by `tests/fixtures/make_track.py`. It is not traced from a
recorded activity, marks no home and no personal route, and carries no time,
elevation or activity type. It is 2.70 km long, 142 points.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
as the payloads are (see Licences).

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-60d89f40f4793100.json` | OSM features for the feature box, from Overpass. |
| `landcover-60d89f40f4793100.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-60d89f40f4793100.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

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
| Track points lie inside (rounded outward to 0.01) | 51.74 | -1.26 | 51.76 | -1.24 |
| Features and elevation (track plus 1500 m) | 51.735560 | -1.279428 | 51.766228 | -1.223186 |
| Land cover (track plus 2600 m) | 51.725609 | -1.295389 | 51.776179 | -1.207225 |

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

```
1311480318:12139650346:3738110066,469136813:3738110066:12139650329,1311480314,1311480316:12139650330:3586620082,352878924,363224931,363224932,362658701,362658702,983375994,1211636333,983375995,1154991955,1154991956,362658699:10741272805:3669237346,362658710,118282214:3159525350:9044258652,118282214:9044258652:3159525350,362658710,362658699:3669237346:10741272805,1154991956,1154991955,983375995,1211636333,983375994:3669237352:11225399025,362658708,1155000144,35815231,27895997:306285639:441089,2987976:441089:1642952912,3171321:1642952912:15185291,24449151:15185291:603564,1026364374,60860875,146574156,146574159,359895131,148100596,146574157,146574161,146574155,148100590:3645245130:12734032519,958210034:12734032519:12734032518,1375310018,1375310017,1417645551,108904119,108904118,1311480310,3171196:262805367:12139650320,1408581093:12139650320:12944859948,1311480312,1311480318:12139650332:12139650346
```

| Way | Version | `highway` | `name` |
|---|---|---|---|
| 1311480318 | 2 | footway | - |
| 469136813 | 16 | pedestrian | Carfax |
| 1311480314 | 2 | footway | - |
| 1311480316 | 3 | footway | - |
| 352878924 | 11 | footway | - |
| 363224931 | 6 | footway | - |
| 363224932 | 5 | footway | - |
| 362658701 | 5 | footway | - |
| 362658702 | 7 | footway | - |
| 983375994 | 7 | footway | - |
| 1211636333 | 3 | footway | - |
| 983375995 | 4 | footway | - |
| 1154991955 | 4 | footway | - |
| 1154991956 | 3 | footway | - |
| 362658699 | 8 | footway | - |
| 362658710 | 4 | footway | - |
| 118282214 | 9 | footway | - |
| 362658708 | 4 | footway | - |
| 1155000144 | 6 | steps | - |
| 35815231 | 8 | footway | - |
| 27895997 | 6 | service | - |
| 2987976 | 18 | residential | Rose Lane |
| 3171321 | 18 | footway | Christ Church Meadow Walk |
| 24449151 | 12 | footway | Broad Walk |
| 1026364374 | 4 | footway | - |
| 60860875 | 6 | footway | - |
| 146574156 | 5 | footway | - |
| 146574159 | 9 | footway | - |
| 359895131 | 3 | footway | - |
| 148100596 | 7 | footway | - |
| 146574157 | 4 | footway | - |
| 146574161 | 5 | footway | - |
| 146574155 | 7 | footway | - |
| 148100590 | 3 | footway | - |
| 958210034 | 6 | footway | - |
| 1375310018 | 2 | steps | - |
| 1375310017 | 3 | footway | - |
| 1417645551 | 1 | footway | - |
| 108904119 | 5 | footway | - |
| 108904118 | 4 | footway | - |
| 1311480310 | 1 | footway | - |
| 3171196 | 18 | residential | Pembroke Square |
| 1408581093 | 2 | footway | - |
| 1311480312 | 4 | footway | - |

## Size

Git stores the payloads compressed and `tests/` is not shipped in a distribution, so the
budget (1.5 MB) is measured as the gzip size of each file at the default level, summed.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-60d89f40f4793100.json` | 41,898 | 5,944 |
| `landcover-60d89f40f4793100.json` | 4,275,172 | 699,109 |
| `overpass-60d89f40f4793100.json` | 4,497,700 | 753,893 |
| `track.gpx` | 6,893 | 1,155 |
| **Total, README excluded** | **8,821,663** | **1,460,101** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
