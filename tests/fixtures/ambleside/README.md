# Ambleside fixture

A synthetic track for the Loughrigg circuit and the provider payloads cached for it. Used by
the golden place cards (`tests/golden/test_places.py`).

## The track

A loop of about 9.0 km from Ambleside in the Lake District: from near Bridge House by Church
Street and Vicarage Road to Rothay Park and Miller Bridge, along Under Loughrigg Road, up
Loughrigg Fell to Loughrigg Terrace above Grasmere, east past Rydal Cave, along Rydal Water's
south shore to Pelter Bridge, and back by the A591 beside the Rothay to Ambleside. The start and
end lie about 140 m from the Bridge House node (`Old Bridge House Fudge Shop`, node 4231682907)
on Compston Road: the whole circuit through the Terrace is 9.3 km from the node itself, and the
route is held to 9 km by starting on the route, not at the building.

The track is invented along public OpenStreetMap ways chosen by id and joined and
resampled every 20 m by `tests/fixtures/make_track.py`. It is not traced from a
recorded activity, marks no home and no personal route, and carries no time,
elevation or activity type (D16). It is 9.00 km long, 460 points.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
(see Licences).

## Checks

`make_track.py` required, and the build passed, these distances from the track to OpenStreetMap
nodes: start and end `4231682907` within 200 m (139 m); via `1359605680`, Miller Bridge (the
footbridge way 38457618, first node), within 25 m (5 m); via `454661074`, Pelter Bridge (the bridge way
38457628, which OpenStreetMap leaves unnamed; first node), within 25 m (0 m); via `254328272`, Rydal Cave, within 150 m (14 m);
length 5 to 9 km (9.00 km).

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-f0a137ce97afcb43.json` | OSM features for the feature box, from Overpass. |
| `landcover-f0a137ce97afcb43.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-f0a137ce97afcb43.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

Each payload is named `<kind>-<key>.json`, where the key is the fetch cache key of
this track with the shipped Overpass and OpenTopoData (`srtm30m`) providers, so a
cache over a copy of this directory finds every payload and fetches nothing.

## Source

- **Ways**: fetched from the Overpass mirror
  `https://maps.mail.ru/osm/tools/overpass/api/interpreter` (the usual `overpass-api.de` resets
  connections from the recording environment) by `make_track.py`; ids and versions below.
- **OSM features and land cover**: the same mirror, two queries; the shipped provider's id is
  `overpass` whatever its endpoint, so the payloads carry the default key. The land cover query
  was refused twice with 504 and answered on the third try.
- **Elevation**: SRTM 30 m (`srtm30m` dataset) via the OpenTopoData public API at
  `https://api.opentopodata.org/v1/srtm30m`. 64 calls of 100 points.
- **Contact string sent**: `https://github.com/findlaywebb/pyntpot`.
- **Fetched**: 2026-10-25.

## Bounding boxes

South, west, north, east, in degrees.

| Box | South | West | North | East |
|---|---|---|---|---|
| Track points lie inside (rounded outward to 0.01) | 54.43 | -3.02 | 54.45 | -2.96 |
| Features and elevation (track plus 1500 m) | 54.417448 | -3.038709 | 54.459354 | -2.940005 |
| Land cover (track plus 2600 m) | 54.407497 | -3.055700 | 54.469305 | -2.923014 |

Fetched at the library's default margins (1,500 m for the features and elevation, 2,600 m for land cover); the card box lies inside the features box.

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction), found with `--list-ways`:

```
1368434936:12673539838:1156324008,4719035:1156324008:30051170,4879680,38457621,38457622,38457618,975261433,121445172,680899020:1359605663:1359605678,121445180:1359605678:31579697,4881504:31579697:31579682,1208585841:31579682:11198259391,466068805:11198259391:454661027,4881502:454661027:2411245870,1134494029:2411245870:8285836541,4881501:8285836541:31579655,4907579:31579655:8280462649,144924219:8280462649:289772289,517567956:289772289:33226326,198847615:33226326:1195294079,144924220:1195294079:1584043841,890934337,345761505:8280542885:8280577503,890938535,198986638:8280577525:690990,4702697:690990:690974,23484647:690974:8280623852,890943390:8280623852:8280623821,700797484:8280623821:8280623905,890943391,890943390:8280623915:8280623900,4232442:8280623900:30050200,293562904:30050200:30050155,4905695,94465208:30050163:7899271873,892597276:7899271873:8296049877,94465208:8296049877:30050174,23484647:30050174:254328269,82604265:254328269:961388592,239724888:961388592:30050179,94465208:30050179:32029912,4907411:32029912:32029939,1134494005,4907414,4907415,4907416,38457628,76912617,699383858,699383860,43617759,43617758,202714126,177584747,100012781,1207896507,100012766,965445197,1443802073,27205368,4600159,239880513,239880514,4600162:232034:232033,561321009:232033:5412735136,561321008:5412735136:1359823030,4879677:1359823030:30051177,1513570087:30051177:4231551418,1513570229:4231551418:1156324008,1368434936
```

| Way | Version | `highway` | `ref` | `name` |
| --- | --- | --- | --- | --- |
| 1368434936 | 2 | service | - | - |
| 4719035 | 17 | residential | - | Vicarage Road |
| 4879680 | 11 | footway | - | - |
| 38457621 | 9 | footway | - | - |
| 38457622 | 11 | footway | - | - |
| 38457618 | 12 | footway | - | Miller Bridge |
| 975261433 | 1 | footway | - | - |
| 121445172 | 5 | unclassified | - | Under Loughrigg Road |
| 680899020 | 3 | unclassified | - | Under Loughrigg Road |
| 121445180 | 6 | unclassified | - | Under Loughrigg Road |
| 4881504 | 19 | service | - | - |
| 1208585841 | 2 | service | - | - |
| 466068805 | 8 | track | - | - |
| 4881502 | 22 | track | - | - |
| 1134494029 | 4 | track | - | - |
| 4881501 | 15 | bridleway | - | - |
| 4907579 | 22 | bridleway | - | - |
| 144924219 | 3 | path | - | - |
| 517567956 | 2 | path | - | - |
| 198847615 | 7 | footway | - | - |
| 144924220 | 4 | path | - | - |
| 890934337 | 1 | path | - | - |
| 345761505 | 7 | path | - | - |
| 890938535 | 2 | path | - | - |
| 198986638 | 5 | path | - | - |
| 4702697 | 20 | path | - | - |
| 23484647 | 12 | path | - | - |
| 890943390 | 1 | path | - | - |
| 700797484 | 4 | path | - | - |
| 890943391 | 1 | path | - | - |
| 4232442 | 17 | footway | - | - |
| 293562904 | 8 | bridleway | - | Loughrigg Terrace |
| 4905695 | 11 | path | - | - |
| 94465208 | 22 | bridleway | - | - |
| 892597276 | 1 | path | - | - |
| 82604265 | 7 | path | - | - |
| 239724888 | 1 | footway | - | - |
| 4907411 | 16 | bridleway | - | - |
| 1134494005 | 2 | service | - | - |
| 4907414 | 10 | service | - | - |
| 4907415 | 11 | unclassified | - | - |
| 4907416 | 6 | unclassified | - | - |
| 38457628 | 6 | unclassified | - | - |
| 76912617 | 2 | unclassified | - | - |
| 699383858 | 5 | trunk | A591 | - |
| 699383860 | 5 | trunk | A591 | - |
| 43617759 | 20 | trunk | A591 | Rydal Bridge |
| 43617758 | 22 | trunk | A591 | - |
| 202714126 | 13 | trunk | A591 | - |
| 177584747 | 18 | trunk | A591 | Rydal Road |
| 100012781 | 17 | trunk | A591 | Scandale Bridge |
| 1207896507 | 2 | trunk | A591 | Rydal Road |
| 100012766 | 18 | trunk | A591 | Rydal Road |
| 965445197 | 3 | trunk | A591 | Rydal Road |
| 1443802073 | 1 | trunk | A591 | Rydal Road |
| 27205368 | 32 | trunk | A591 | Rydal Road |
| 4600159 | 26 | trunk | A591 | Rydal Road |
| 239880513 | 7 | trunk | A591 | Rydal Road |
| 239880514 | 11 | trunk | A591 | Rydal Road |
| 4600162 | 16 | trunk | A591 | Compston Road |
| 561321009 | 6 | trunk | A591 | Compston Road |
| 561321008 | 6 | trunk | A591 | Compston Road |
| 4879677 | 12 | unclassified | - | Millans Park |
| 1513570087 | 2 | residential | - | Vicarage Road |
| 1513570229 | 1 | residential | - | Vicarage Road |

## Size

The payloads are committed trimmed (`tests/fixtures/trim_fixture.py`: minified, only the fields
and tags the code reads). The budget is 7,000,000 bytes on disk for the directory (the 6,000,000 bytes of the other walking maps
would not hold this one: land cover on the fells is dense), enforced by `tests/architecture/test_coordinates.py`.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-f0a137ce97afcb43.json` | 45,649 | 10,781 |
| `landcover-f0a137ce97afcb43.json` | 4,869,967 | 792,667 |
| `overpass-f0a137ce97afcb43.json` | 1,624,907 | 320,303 |
| `track.gpx` | 21,855 | 3,402 |
| **Total, README excluded** | **6,562,378** | **1,127,153** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
