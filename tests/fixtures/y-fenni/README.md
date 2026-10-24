# Y Fenni (Abergavenny) fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

A loop of about 2.8 km in Y Fenni (Abergavenny, Monmouthshire): the castle, Castle Meadows by the Wysg (the Usk) to the Llanfoist bridge, back along Merthyr Road and the High Street to the castle.

The track is invented along public OpenStreetMap ways chosen by id and joined and
resampled every 20 m by `tests/fixtures/make_track.py`. It is not traced from a
recorded activity, marks no home and no personal route, and carries no time,
elevation or activity type. It is 2.78 km long, 145 points.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
as the payloads are (see Licences).

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-e634bd2f1a4ded97.json` | OSM features for the feature box, from Overpass. |
| `landcover-e634bd2f1a4ded97.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-e634bd2f1a4ded97.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

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
| Track points lie inside (rounded outward to 0.01) | 51.81 | -3.03 | 51.83 | -3.01 |
| Features and elevation (track plus 1500 m) | 51.804254 | -3.051128 | 51.835697 | -2.995427 |
| Land cover (track plus 2600 m) | 51.794303 | -3.067114 | 51.845648 | -2.979441 |

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

```
720029321:6758034991:6758034986,942243909,942243907,942243908,368980625,27275924,27275925,1046554108:299402797:1448480389,131629662:1448480389:1975835949,186835043,186835038,131629655:1975835935:1448480399,131629665,1046554107,186831568,53027185:671630726:671630711,131696825,1046554106:671630967:671630970,53027193,1340598890,22951981:12400668351:247294262,22951980,1046554103,128218854,54580143:1417439837:1417439838,54580143:1417439838:1417439779,54580144:1417439779:247294272,23649768,23649755:256217216:577241405,23649748,727577456,128218854,1046554103,22951980,22951981,397610318,22951983:247294275:247294279,22951984:247294279:410825705,31145803,1046554108,27275926,27448957:301381276:301381284,27448958,27275928:301381288:253332790,23398808,27275930:1375286511:426149,27275923,27275924,368980625,942243908,942243907,942243909,720029321:6758034986:6758034991
```

| Way | Version | `highway` | `name` |
|---|---|---|---|
| 720029321 | 3 | path | - |
| 942243909 | 2 | service | - |
| 942243907 | 2 | service | - |
| 942243908 | 1 | service | - |
| 368980625 | 4 | service | - |
| 27275924 | 6 | unclassified | - |
| 27275925 | 10 | unclassified | Castle Street |
| 1046554108 | 6 | unclassified | Tudor Street |
| 131629662 | 4 | service | - |
| 186835043 | 3 | footway | - |
| 186835038 | 2 | footway | - |
| 131629655 | 5 | service | - |
| 131629665 | 3 | service | - |
| 1046554107 | 3 | service | - |
| 186831568 | 1 | footway | - |
| 53027185 | 9 | footway | - |
| 131696825 | 7 | footway | - |
| 1046554106 | 6 | cycleway | - |
| 53027193 | 7 | steps | - |
| 1340598890 | 2 | footway | - |
| 22951981 | 11 | primary | - |
| 22951980 | 16 | primary | - |
| 1046554103 | 5 | primary | - |
| 128218854 | 9 | primary | - |
| 54580143 | 6 | cycleway | - |
| 54580144 | 10 | trunk_link | - |
| 23649768 | 11 | trunk_link | - |
| 23649755 | 11 | primary | - |
| 23649748 | 9 | primary | - |
| 727577456 | 2 | primary | - |
| 397610318 | 9 | primary | - |
| 22951983 | 9 | primary | - |
| 22951984 | 19 | secondary | Merthyr Road |
| 31145803 | 14 | unclassified | Tudor Street |
| 27275926 | 6 | unclassified | - |
| 27448957 | 9 | unclassified | St John's Street |
| 27448958 | 4 | pedestrian | St John's Street |
| 27275928 | 10 | pedestrian | High Street |
| 23398808 | 11 | unclassified | Cross Street |
| 27275930 | 14 | trunk | Monk Street |
| 27275923 | 3 | unclassified | Lower Castle Street |

## Size

Git stores the payloads compressed and `tests/` is not shipped in a distribution, so the
budget (1.5 MB) is measured as the gzip size of each file at the default level, summed.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-e634bd2f1a4ded97.json` | 43,650 | 8,358 |
| `landcover-e634bd2f1a4ded97.json` | 1,027,435 | 168,863 |
| `overpass-e634bd2f1a4ded97.json` | 2,788,708 | 438,177 |
| `track.gpx` | 7,035 | 1,180 |
| **Total, README excluded** | **3,866,828** | **616,578** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
