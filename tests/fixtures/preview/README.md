# Preview fixture

A synthetic route and the provider payloads cached for it, made by
`tests/fixtures/make_preview.py`. Nothing here is recorded from OpenStreetMap: the track and
every element are made up, so none of it is ODbL data. The names are real names of the
Lynmouth area (Lynmouth, Lynton, East Lyn River, West Lyn River, Countisbury, Watersmeet,
Foreland Point) standing at made-up places, by design. Features with no real name there carry
no name tag. The card's credits read "© OpenStreetMap contributors" over this
data and "elevation: NASA SRTM" over the synthetic grid, because each is its provider's credit.

Regenerate with `PYTHONPATH=tests uv run python -m fixtures.make_preview OUT_DIR`; the fixture
test runs it into a temporary directory and compares every file byte for byte.

## Files

| File | What it is |
|---|---|
| `track.gpx` | 291 points every 20 m or less, no times or elevations. |
| `overpass-3fa415870ecbe1a8.json` | The feature payload: coast, water, roads, woods, places and landmarks. |
| `landcover-3fa415870ecbe1a8.json` | The land cover payload: the gravel bar and the cover patches. |
| `elevation-3fa415870ecbe1a8.json` | An 80 by 80 grid over the features fetch box: sea at 0 m, land on a 20 m floor, one hill. |

Each payload is named `<kind>-<key>.json`, where the key is the fetch cache key of this track
with the shipped Overpass and OpenTopoData providers and the default `FetchMargins`, so a
cache over a copy of this directory finds every payload and fetches nothing.

## Frame

The track's box is 1.5 km east to west by 1.6 km north to south, centred inside the Lynmouth
box. The features fetch box (the track's box and 1500 m) is about 4.5 by 4.6 km and lies inside
the Lynmouth box; it holds every theme's card. Every element lies inside it, rounded inward by
a metre, and the land cover is written only inside it too (the land cover payload has no box
field). Every coordinate in the payloads, the elevation grid and the GPX lies inside the
Lynmouth box. The coast, the major road, the river, the stream and the minor road run to the
fetch box's edge, so each crosses every theme's card edge. Every feature listed below lies
within 350 m of the track's box, so it is inside the smallest card.

## Features and what each tests

| Feature | Payload | Tags | Name | What it tests |
|---|---|---|---|---|
| Coast | features | way `natural=coastline`, east to west, sea to the north | none | the sea, the shore and the coast's ink |
| Offshore island | features | closed anticlockwise way `natural=coastline` | none | land inside the sea |
| Lake with an island | features | relation `natural=water`, one `outer` and one `inner` | none | water with dry land in it |
| River | features | two ways `waterway=river` that part and rejoin | East Lyn River | a river that splits round a bar |
| Gravel bar | land cover | way `natural=shingle` | none | sand between the two channels |
| Stream | features | way `waterway=stream`, ending on the river | West Lyn River | a minor water joining a river |
| Major road | features | way `highway=primary` | none | a road over the river, the stream and the minor road |
| Minor road | features | way `highway=unclassified` | none | a lane the route runs along and crosses the river |
| Woods | features | ways `natural=wood`: one large, one 50 m square | none | wood, and a wood below `min_patch_px` |
| Meadow, heath, built-up, rock | land cover | `landuse=meadow`, `natural=heath`, `landuse=residential`, `natural=bare_rock` | none | each class, with 50 m squares of meadow and heath beside larger patches |
| Lynmouth, Lynton, Countisbury | features | nodes `place=village`, `place=town`, `place=hamlet` | as given | settlements near the route |
| Foreland Point, Watersmeet | features | nodes `man_made=lighthouse`, `tourism=attraction` | as given | named landmarks |
| Hill | elevation | a Gaussian 300 m high on the floor | none | relief |

## The route

It starts at Lynton's side, runs down to the minor road and along it to the river, walks up
the East Lyn River's bank beside the gravel bar and back down, then runs out east along the
road and back, and ends south of the stream. It crosses the East Lyn River twice and the West
Lyn River once. It keeps at least 300 m from the coast. It doubles back beside the minor road
(out to the east and back, within 20 m of the road) and beside the river (up the bank and
back, within 40 m of the channel).

The riverside stretch, the walk up the bank and back down it, is track points 115
to 188 (counting from 0). A journal note lies on one of them.
