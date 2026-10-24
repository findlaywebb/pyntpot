# Keswick fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

A loop of about 6.7 km: the Moot Hall, Lake Road, the shore path to Friar's Crag and back along it to the boat landings, through Crow Park and Hope Park to the Derwent footbridge, the Cumbria Way to Portinscale, and back to the Moot Hall by the Cumbria Way and Main Street.

The track is invented along public OpenStreetMap ways chosen by id and joined and
resampled every 20 m by `tests/fixtures/make_track.py`. It is not traced from a
recorded activity, marks no home and no personal route, and carries no time,
elevation or activity type. It is 6.74 km long, 346 points.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
as the payloads are (see Licences).

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-f2f4692b66d96eb9.json` | OSM features for the feature box, from Overpass. |
| `landcover-f2f4692b66d96eb9.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-f2f4692b66d96eb9.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

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
| Track points lie inside (rounded outward to 0.01) | 54.59 | -3.17 | 54.61 | -3.13 |
| Features and elevation (track plus 1500 m) | 54.576502 | -3.184494 | 54.619929 | -3.113259 |
| Land cover (track plus 2600 m) | 54.566551 | -3.201551 | 54.629880 | -3.096202 |

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

```
23450171:12966536443:9400488539,23450174:9400488539:2823462693,23450172,54531666,389567253,34695611,34695645:403822939:403822942,660878199,34695645:6187403859:253851421,1419366572,277704484,1269535823,59468303,29230018,1397495358,1396228809,54531652,54531651,59468312,59468312,54531651,54531652,1396228809,1397495358,29230018,59468303:321505335:403824845,1184478773:403824845:7798344351,968877481,132515654:1457573242:1421004639,109169988,1396181062,1396181060,1396181057,38622454:371336715:6898489492,736825569:6898489492:9692050851,1396181071:9692050851:9692050842,1396181070,1396181073,1396181072,131587819:6506616126:1751144816,163416876,163416873:1751144827:6506616140,693052110:6506616140:8958859871,968362043,987718697,109170034:2125439133:9134694047,988252919:9134694047:9134694066,988252920,1549102479,1549102480:14089860796:2823462672,26822326:2823462672:294227286,454536555,183372099,104682222,1412319632,70077686,101743019,26822427,138365044,138365043,26822434,1117166263,1412272863:294231072:12978509353,1412315533,999590515:12978509352:9132229082,232699357:9132229082:684250507,54254416:684250507:684250524,54254417:684250524:684250549,54254423:684250549:684250625,101743021,454908721,1050979427:929281907:9657868983,1050979430:9657868983:9657868967,1050979431,454908724,660876485,454919575:6187385538:14089836474,1549107979,1549107978,1549107977,1549107976:14089836468:14076951557,1549102478,1547716684,1549107984,1549107983:14089836485:14089909703,1549107994,1549107995,1549107985,1549107986,988526634:10901005024:14100680319,1550308415,1550308414,1549751371,1548829239,1548829240,1548829241,1548829244,1411121712,1411098597,201966206,23450174:2821759066:2821759016,1545841562,23450174:5540222483:9400488540,23450171:9400488540:12966536443
```

| Way | Version | `highway` | `name` |
|---|---|---|---|
| 23450171 | 18 | pedestrian | Market Square |
| 23450174 | 17 | pedestrian | Market Square |
| 23450172 | 19 | pedestrian | Lake Road |
| 54531666 | 14 | pedestrian | Lake Road |
| 389567253 | 5 | footway | - |
| 34695611 | 6 | footway | - |
| 34695645 | 10 | footway | - |
| 660878199 | 3 | footway | - |
| 1419366572 | 2 | unclassified | Lake Road |
| 277704484 | 6 | unclassified | Lake Road |
| 1269535823 | 4 | unclassified | Lake Road |
| 59468303 | 15 | unclassified | Lake Road |
| 29230018 | 24 | service | Lake Road |
| 1397495358 | 1 | service | Lake Road |
| 1396228809 | 3 | service | Lake Road |
| 54531652 | 9 | footway | - |
| 54531651 | 7 | footway | - |
| 59468312 | 6 | footway | - |
| 1184478773 | 2 | footway | - |
| 968877481 | 4 | footway | - |
| 132515654 | 11 | footway | - |
| 109169988 | 13 | unclassified | Crow Park Road |
| 1396181062 | 1 | unclassified | Crow Park Road |
| 1396181060 | 4 | unclassified | Crow Park Road |
| 1396181057 | 6 | unclassified | Crow Park Road |
| 38622454 | 15 | residential | The Headlands |
| 736825569 | 3 | service | Lakehead Court |
| 1396181071 | 2 | footway | - |
| 1396181070 | 2 | footway | - |
| 1396181073 | 3 | footway | - |
| 1396181072 | 3 | footway | - |
| 131587819 | 13 | residential | Elliot Park |
| 163416876 | 3 | service | - |
| 163416873 | 5 | service | - |
| 693052110 | 4 | footway | - |
| 968362043 | 2 | footway | - |
| 987718697 | 2 | footway | - |
| 109170034 | 12 | residential | Bridge Terrace |
| 988252919 | 17 | footway | - |
| 988252920 | 4 | footway | - |
| 1549102479 | 1 | footway | - |
| 1549102480 | 1 | footway | - |
| 26822326 | 8 | service | - |
| 454536555 | 2 | track | - |
| 183372099 | 11 | footway | - |
| 104682222 | 6 | service | - |
| 1412319632 | 1 | service | - |
| 70077686 | 11 | unclassified | - |
| 101743019 | 5 | unclassified | - |
| 26822427 | 20 | footway | - |
| 138365044 | 10 | footway | - |
| 138365043 | 9 | footway | - |
| 26822434 | 23 | unclassified | - |
| 1117166263 | 3 | unclassified | - |
| 1412272863 | 4 | unclassified | - |
| 1412315533 | 1 | footway | - |
| 999590515 | 2 | service | - |
| 232699357 | 13 | unclassified | - |
| 54254416 | 3 | residential | - |
| 54254417 | 2 | residential | - |
| 54254423 | 8 | footway | - |
| 101743021 | 4 | footway | - |
| 454908721 | 3 | footway | - |
| 1050979427 | 1 | footway | - |
| 1050979430 | 2 | footway | - |
| 1050979431 | 2 | footway | - |
| 454908724 | 5 | footway | - |
| 660876485 | 2 | footway | - |
| 454919575 | 14 | footway | - |
| 1549107979 | 1 | footway | - |
| 1549107978 | 1 | footway | - |
| 1549107977 | 1 | footway | - |
| 1549107976 | 1 | footway | - |
| 1549102478 | 1 | footway | - |
| 1547716684 | 2 | path | - |
| 1549107984 | 1 | footway | - |
| 1549107983 | 1 | footway | - |
| 1549107994 | 1 | footway | - |
| 1549107995 | 1 | footway | - |
| 1549107985 | 1 | footway | - |
| 1549107986 | 1 | footway | - |
| 988526634 | 11 | footway | - |
| 1550308415 | 1 | footway | - |
| 1550308414 | 1 | footway | - |
| 1549751371 | 3 | footway | - |
| 1548829239 | 1 | footway | - |
| 1548829240 | 1 | footway | - |
| 1548829241 | 1 | footway | - |
| 1548829244 | 1 | footway | - |
| 1411121712 | 3 | footway | - |
| 1411098597 | 2 | footway | - |
| 201966206 | 13 | pedestrian | Main Street |
| 1545841562 | 1 | pedestrian | Market Square |

## Size

Git stores the payloads compressed and `tests/` is not shipped in a distribution, so the
budget (1.5 MB) is measured as the gzip size of each file at the default level, summed.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-f2f4692b66d96eb9.json` | 43,997 | 8,106 |
| `landcover-f2f4692b66d96eb9.json` | 3,777,758 | 578,351 |
| `overpass-f2f4692b66d96eb9.json` | 2,816,505 | 463,405 |
| `track.gpx` | 16,482 | 2,537 |
| **Total** | **6,654,742** | **1,052,399** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
