# Yr Wyddfa (Eryri) fixture

A synthetic track and the provider payloads cached for it. Used by the golden
place cards (`tests/golden/test_places.py`).

## The track

A one-way route of about 11 km over Crib Goch to the summit of Yr Wyddfa, Eryri: Pen-y-Pass, the Pyg Track to Bwlch y Moch, Crib Goch, Bwlch Coch, Crib y Ddysgl (Garnedd Ugain), Bwlch Glas, the summit, then the Llanberis Path to its foot at the public road in Llanberis. Near Bwlch Glas the descent runs close to the ascent; that is expected. The summit is reached by the path steps at its top and the track turns there; the trig point is within 8 m of the track.

The track is invented along public OpenStreetMap ways chosen by id and joined and
resampled every 20 m by `tests/fixtures/make_track.py`. It is not traced from a
recorded activity, marks no home and no personal route, and carries no time,
elevation or activity type. It is 11.10 km long, 566 points.

Checks passed when the track was built (distances to the OSM nodes): the Pen-y-Pass car park outline node 1385264838, 35 m (limit 150 m); the summit trig point node 1745517169, 8 m (limit 30 m); the node 294193247 where the Llanberis Path meets the public road, 0 m (limit 30 m). Length bound 11 to 13 km.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
as the payloads are (see Licences).

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-353c7a77ae84f4c1.json` | OSM features for the feature box, from Overpass. |
| `landcover-353c7a77ae84f4c1.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-353c7a77ae84f4c1.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

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
- **Fetched**: 2026-10-25 (re-recorded wider; first fetched 2026-10-24).

## Bounding boxes

South, west, north, east, in degrees.

| Box | South | West | North | East |
|---|---|---|---|---|
| Track points lie inside (rounded outward to 0.01) | 53.06 | -4.13 | 53.11 | -4.02 |
| Features and elevation (track plus 3000 m) | 53.041268 | -4.165402 | 53.135890 | -3.975964 |
| Land cover (track plus 3000 m) | 53.041268 | -4.165402 | 53.135890 | -3.975964 |

Fetched at 3,000 m for the features and elevation and for land cover (`--margin-m 3000
--landcover-margin-m 3000` of `record_fixture.py`), wider than the library defaults of
1,500 m and 2,600 m so the card shows the ground beside the massif as far as it reaches. The
margin is the smallest whole kilometre that covers the card box's largest overhang beyond the
track's box (1,957 m, the card box of the default ribbon fields, to the west and south) plus 1 km of
headroom for a theme. The card box lies inside the features box (`test_places.py` asserts it).
The payloads are not simplified: the walking maps keep every vertex.

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

## Ways

Joined in this order, by `make_track.py --ways` (`ID` is the whole way; `ID:FROM:TO` is the
part between two of its node ids, in that direction):

```
177289177,140115342,372419761,140115388,168426574,1111478730,168426583,531038424,26566365,1111478731,167869299,114874816,54585244,152280669,1550779486,601019698,1550779487,1339233653,601019706,601019706,1339233653,1550779487,601019698,1550779486,152280669,26819108,691073240,691073241
```

| Way | Version | `highway` | `name` |
|---|---|---|---|
| 177289177 | 7 | service | - |
| 140115342 | 8 | track | Llwybr Bwlch Moch |
| 372419761 | 7 | path | Llwybr Bwlch Moch |
| 140115388 | 11 | path | Llwybr Bwlch Moch |
| 168426574 | 5 | path | Crib Goch |
| 1111478730 | 3 | path | Crib Goch |
| 168426583 | 10 | path | Crib Goch |
| 531038424 | 3 | path | Crib Goch |
| 26566365 | 18 | path | - |
| 1111478731 | 2 | path | - |
| 167869299 | 6 | path | - |
| 114874816 | 8 | path | - |
| 54585244 | 7 | path | - |
| 152280669 | 16 | bridleway | Llanberis Path |
| 1550779486 | 2 | steps | Llanberis Path |
| 601019698 | 11 | steps | - |
| 1550779487 | 2 | footway | - |
| 1339233653 | 4 | steps | - |
| 601019706 | 7 | footway | - |
| 26819108 | 28 | bridleway | Llanberis Path |
| 691073240 | 2 | bridleway | Llanberis Path |
| 691073241 | 4 | bridleway | Llanberis Path |

## Size

The payloads are committed trimmed (`tests/fixtures/trim_fixture.py`: minified, only the fields
and tags the code reads). The budget is 8,000,000 bytes on disk for the directory,
enforced by `tests/architecture/test_coordinates.py`.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-353c7a77ae84f4c1.json` | 47,961 | 12,903 |
| `landcover-353c7a77ae84f4c1.json` | 3,915,945 | 710,560 |
| `overpass-353c7a77ae84f4c1.json` | 3,718,963 | 752,512 |
| `track.gpx` | 26,825 | 4,168 |
| **Total, README excluded** | **7,709,694** | **1,480,143** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
