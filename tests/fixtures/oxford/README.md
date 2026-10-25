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

## The new track (`track.new.gpx`)

`track.new.gpx` is the colleges-and-bridges route that replaces `track.gpx` when the payloads are
re-recorded for it; until then the payloads above belong to `track.gpx`. A loop of about 4.0 km
(4.04 km, 209 points) in central Oxford: Carfax, the High Street to Catte Street, north past the
Radcliffe Camera, New College Lane and Queen's Lane back to the High Street, east over Magdalen
Bridge and back, Rose Lane into Christ Church Meadow, the Meadow Walk and the Broad Walk, then by the
Meadow Buildings and the War Memorial Garden footways and Rose Place to St Aldate's and Carfax.
OpenStreetMap tags no public way through Christ Church itself (every way inside the college is
`access=private` or `access=no`), so the route does not enter it.

It is built the same way and under the same D16 statement as `track.gpx`: invented along public
OpenStreetMap ways, resampled every 20 m, no time, elevation or activity type, no home and no
personal route; ODbL as a derivative of OpenStreetMap. Fetched 2026-10-25 from the same mirror,
with the same contact string.

Checks the build passed: via `2513320485` (a node of the Radcliffe Camera building, way 4884600)
within 60 m (20 m); via `12943776076` (the middle node of the Magdalen Bridge deck, way
39380970) within 15 m (0 m); length 3 to 5 km (4.04 km). The track's box, rounded outward to
0.01, is the one in the table below.

New-track ways, joined in this order by `make_track.py --ways`:

```
2988061,1160879772,1160879673:306285529:12154048739,4885405:12154048739:314214911,1675893:314214911:11704190636,244336012:11704190636:2516658024,244336012:2516658024:11704190636,1675893:11704190636:314214911,8078920:314214911:410775005,895264517:410775005:603439,1516686699,1516686700,1304105423,8078923,4713440,126369414,8126433:2361414052:603412,1304105131:603412:9044228867,977420095:9044228867:1260262210,27895984:1260262210:306285523,8125931:306285523:213429,2987960,651722051,394438023,39380970,39380970:330348966:471843078,394438023:471843078:3974478264,651722051:3974478264:455559821,2987960:455559821:441094,2987976,3171321:1642952912:603590,2988126:603590:603571,95826215:603571:1109077577,95826215:1109077577:603571,8125937,24449151:603564:8866091817,958210081:8866091817:603563,958210082:603563:257571181,60860890:257571181:1376685998,931474937:1376685998:8635843274,931474936:8635843274:761862897,60860877:761862897:603562,1408666578:603562:301734774,1408666570:301734774:12945437353,1411611627:12945437353:12139650317,1311480310,1079519510:262805367:9895595687,2988082:9895595687:213435
```

| Way | Version | `highway` | `ref` | `name` |
| --- | --- | --- | --- | --- |
| 2988061 | 61 | tertiary | A420 | High Street |
| 1160879772 | 7 | tertiary | A420 | High Street |
| 1160879673 | 11 | tertiary | A420 | High Street |
| 4885405 | 18 | cycleway | - | Catte Street |
| 1675893 | 20 | pedestrian | - | Radcliffe Square |
| 244336012 | 12 | footway | - | - |
| 8078920 | 25 | pedestrian | - | Catte Street |
| 895264517 | 4 | residential | - | Catte Street |
| 1516686699 | 1 | residential | - | New College Lane |
| 1516686700 | 1 | residential | - | New College Lane |
| 1304105423 | 4 | residential | - | New College Lane |
| 8078923 | 35 | residential | - | New College Lane |
| 4713440 | 18 | residential | - | Queen's Lane |
| 126369414 | 13 | residential | - | Queen's Lane |
| 8126433 | 28 | residential | - | Queen's Lane |
| 1304105131 | 4 | residential | - | Queen's Lane |
| 977420095 | 10 | tertiary | A420 | High Street |
| 27895984 | 34 | tertiary | A420 | High Street |
| 8125931 | 35 | tertiary | A420 | High Street |
| 2987960 | 46 | tertiary | A420 | High Street |
| 651722051 | 12 | tertiary | A420 | High Street |
| 394438023 | 12 | tertiary | A420 | High Street |
| 39380970 | 41 | tertiary | A420 | High Street |
| 2987976 | 18 | residential | - | Rose Lane |
| 3171321 | 18 | footway | - | Christ Church Meadow Walk |
| 2988126 | 11 | footway | - | - |
| 95826215 | 4 | footway | - | - |
| 8125937 | 16 | footway | - | New Walk |
| 24449151 | 12 | footway | - | Broad Walk |
| 958210081 | 8 | steps | - | Broad Walk |
| 958210082 | 4 | footway | - | Broad Walk |
| 60860890 | 6 | footway | - | - |
| 931474937 | 8 | steps | - | - |
| 931474936 | 6 | footway | - | - |
| 60860877 | 5 | footway | - | - |
| 1408666578 | 1 | footway | - | - |
| 1408666570 | 2 | footway | - | - |
| 1411611627 | 3 | footway | - | - |
| 1311480310 | 1 | footway | - | - |
| 1079519510 | 9 | tertiary | A420 | St Aldate's |
| 2988082 | 61 | tertiary | A420 | St Aldate's |

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
