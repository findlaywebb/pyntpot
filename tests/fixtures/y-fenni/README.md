# Y Fenni (Abergavenny) fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

The food-tour route. A loop of about 2.2 km
(2.21 km, 120 points) in Y Fenni from the castle: Lower Castle Street, Monk Street and Cross Street
past Angel Bakery, Market Street, Lion Street to Bean & Bread, Nevill Street to Rate of Rise, back
to Market Street for Shepherd's Ice Cream, Frogmore Street to Tŷ Melin and a little beyond, Cibi
Walk and Castle Street back to the castle.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL as the
payloads are (see Licences).

It is built by `tests/fixtures/make_track.py` under the D16 statement: invented along public
OpenStreetMap ways, resampled every 20 m, no time, elevation or activity type, no home and no
personal route; ODbL as a derivative of OpenStreetMap. Fetched 2026-10-25 from the mirror and with the
contact string named under Source. Its box, rounded outward to 0.01, is 51.82, -3.03, 51.83, -3.01,
inside the box in the table below.

Checks the build passed (distance from the track to the OpenStreetMap node, limit 40 m each):
Angel Bakery `12633622904` (10 m); Bean & Bread `9060360117` (7 m); Rate of Rise Coffee Roastery
`12553434518` (8 m); Shepherd's Ice Cream, a node of way 727692762, `6819447139` (4 m); the Tŷ Melin
point `5560350617` (9 m); length 2 to 4 km (2.21 km).

### Tŷ Melin's point

Tŷ Melin Bakery is not mapped in OpenStreetMap under its own name. Its public address is
**54 Frogmore Street, Abergavenny NP7 5AH**, as the bakery's own site (`tymelinbakery.com`, "Our
Sites") lists it. OpenStreetMap holds that address as node **5560350617** (version 6, edited
2026-08-21; `shop=vacant`, `old_name=Field Day Flowers`, `addr:housenumber=54`,
`addr:street=Frogmore Street`, `addr:postcode=NP7 5AH`), which lies inside the building way
**1362830302** (version 1, `building=yes`) on Frogmore Street. The slice places Tŷ Melin's point
on that node: 51.8238632, -3.0202249 (latitude, longitude). The maintainer confirms or moves it;
this README is the only place it is recorded, and the docs' custom label for Tŷ Melin takes it from here.

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-31d229011257f9fa.json` | OSM features for the feature box, from Overpass. |
| `landcover-31d229011257f9fa.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-31d229011257f9fa.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

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
| Track points lie inside (rounded outward to 0.01) | 51.81 | -3.03 | 51.83 | -3.01 |
| Features and elevation (track plus 1500 m) | 51.807169 | -3.043161 | 51.838759 | -2.995442 |
| Land cover (track plus 2600 m) | 51.797218 | -3.059148 | 51.848710 | -2.979455 |

Fetched at the library's default margins (1,500 m for the features and elevation, 2,600 m for land cover); the card box lies inside the features box.

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

```
27275923:1375286508:426149,27275930:426149:14111379273,27275930:14111379273:1375286511,23398808,23398921,31145719:253333895:14105543309,1550835725:14105543309:14105543314,1550835725:14105543314:14105543309,31145719:14105543309:253333966,23398928:253333966:3728192129,368980616,398334877:4011003962:14105543354,1550835736:14105543354:3728192016,368980604,368980615,27275928:3728192003:299402803,27275927:299402803:301381290,27448959,727711261,27448958:301381294:301381288,27275928:301381288:253332790,23398921:253332790:14106446221,23398921:14106446221:253332790,27275928:253332790:299402803,23398804:299402803:253332737,22952082,34039911,614770648,1046554109,123270584:31069948:945925117,1046554110,123270585,123270582,1418837333,34039938:1375281446:1375281452,1550012131:1375281452:14097767148,1550012126,1550012129:14097767144:14097767138,727728433:14097767138:6819741714,727731877,727731878,22952082:247295593:253332737,23398804,27275927:299402803:301381276,27275926:301381276:299402797,27275925:299402797:8420564766,368980610:8420564766:6293773641,672093740:6293773641:6293773640,672093740,368980610:6293773641:8420564766,27275925:8420564766:299402786,27275923:299402786:1375286508
```

| Way | Version | `highway` | `ref` | `name` |
| --- | --- | --- | --- | --- |
| 27275923 | 3 | unclassified | - | Lower Castle Street |
| 27275930 | 14 | trunk | A40 | Monk Street |
| 23398808 | 11 | unclassified | - | Cross Street |
| 23398921 | 10 | unclassified | - | Market Street |
| 31145719 | 12 | unclassified | - | Lion Street |
| 1550835725 | 1 | footway | - | The Courtyard |
| 23398928 | 11 | unclassified | - | Lion Street |
| 368980616 | 5 | service | - | - |
| 398334877 | 4 | service | - | - |
| 1550835736 | 2 | footway | - | - |
| 368980604 | 8 | steps | - | - |
| 368980615 | 3 | footway | - | - |
| 27275928 | 10 | pedestrian | - | High Street |
| 27275927 | 12 | pedestrian | - | Nevill Street |
| 27448959 | 5 | service | - | St. John's Lane |
| 727711261 | 2 | pedestrian | - | St. John's Lane |
| 27448958 | 4 | pedestrian | - | St John's Street |
| 23398804 | 9 | pedestrian | - | Frogmore Street |
| 22952082 | 12 | pedestrian | - | Frogmore Street |
| 34039911 | 9 | pedestrian | - | Frogmore Street |
| 614770648 | 5 | unclassified | - | Frogmore Street |
| 1046554109 | 3 | unclassified | - | Frogmore Street |
| 123270584 | 8 | trunk | A40 | Frogmore Street |
| 1046554110 | 3 | trunk | A40 | Park Road |
| 123270585 | 7 | trunk | A40 | Park Road |
| 123270582 | 8 | trunk | A40 | Penyfal Road |
| 1418837333 | 2 | trunk | A40 | - |
| 34039938 | 10 | trunk | A40 | - |
| 1550012131 | 1 | footway | - | - |
| 1550012126 | 1 | footway | - | - |
| 1550012129 | 2 | footway | - | - |
| 727728433 | 6 | footway | - | Cibi Walk |
| 727731877 | 2 | footway | - | Cibi Walk |
| 727731878 | 3 | footway | - | Cibi Walk |
| 27275926 | 6 | unclassified | - | - |
| 27275925 | 10 | unclassified | - | Castle Street |
| 368980610 | 4 | service | - | - |
| 672093740 | 2 | service | - | - |

## Size

The payloads are committed trimmed (`tests/fixtures/trim_fixture.py`: minified, only the fields
and tags the code reads). The budget is 6,000,000 bytes on disk for the directory,
enforced by `tests/architecture/test_coordinates.py`.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-31d229011257f9fa.json` | 43,796 | 7,881 |
| `landcover-31d229011257f9fa.json` | 492,997 | 97,660 |
| `overpass-31d229011257f9fa.json` | 1,619,950 | 321,275 |
| `track.gpx` | 5,865 | 1,014 |
| **Total, README excluded** | **2,162,608** | **427,830** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
