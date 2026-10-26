# Oxford fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

The colleges-and-bridges route. A loop of about 4.0 km
(4.04 km, 209 points) in central Oxford: Carfax, the High Street to Catte Street, north past the
Radcliffe Camera, New College Lane and Queen's Lane back to the High Street, east over Magdalen
Bridge and back, Rose Lane into Christ Church Meadow, the Meadow Walk and the Broad Walk, then by the
Meadow Buildings and the War Memorial Garden footways and Rose Place to St Aldate's and Carfax.
OpenStreetMap tags no public way through Christ Church itself (every way inside the college is
`access=private` or `access=no`), so the route does not enter it.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL as the
payloads are (see Licences).

It is built by `tests/fixtures/make_track.py` under the D16 statement: invented along public
OpenStreetMap ways, resampled every 20 m, no time, elevation or activity type, no home and no
personal route; ODbL as a derivative of OpenStreetMap. Fetched 2026-10-25 from the mirror and with the
contact string named under Source.

Checks the build passed: via `2513320485` (a node of the Radcliffe Camera building, way 4884600)
within 60 m (20 m); via `12943776076` (the middle node of the Magdalen Bridge deck, way
39380970) within 15 m (0 m); length 3 to 5 km (4.04 km). The track's box, rounded outward to
0.01, is the one in the table below.

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-edf326cc49d5cc52.json` | OSM features for the feature box, from Overpass. |
| `landcover-edf326cc49d5cc52.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-edf326cc49d5cc52.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

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
- **Fetched**: 2026-10-25.

## Bounding boxes

South, west, north, east, in degrees.

| Box | South | West | North | East |
|---|---|---|---|---|
| Track points lie inside (rounded outward to 0.01) | 51.74 | -1.26 | 51.76 | -1.24 |
| Features and elevation (track plus 1500 m) | 51.730633 | -1.279390 | 51.768049 | -1.223208 |
| Land cover (track plus 2600 m) | 51.720682 | -1.295351 | 51.778000 | -1.207247 |

Fetched at the library's default margins (1,500 m for the features and elevation, 2,600 m for land cover); the card box lies inside the features box.

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

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

## Size

The payloads are committed trimmed (`tests/fixtures/trim_fixture.py`: minified, only the fields
and tags the code reads). The budget is 6,000,000 bytes on disk for the directory,
enforced by `tests/architecture/test_coordinates.py`.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-edf326cc49d5cc52.json` | 41,900 | 6,030 |
| `landcover-edf326cc49d5cc52.json` | 2,415,634 | 451,092 |
| `overpass-edf326cc49d5cc52.json` | 2,374,957 | 456,773 |
| `track.gpx` | 10,058 | 1,638 |
| **Total, README excluded** | **4,842,549** | **915,533** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
