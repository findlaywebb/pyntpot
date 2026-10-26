# Skye fixture

A synthetic track for a one-way tour of the Isle of Skye on public roads, and the provider
payloads cached for it, recorded with wider fetch margins. Used by the golden place cards
(`tests/golden/test_places.py`).

## The track

A one-way tour of 282.98 km on the A87, A851, A863, B8009, B884, A850 and A855 and the Glen
Brittle road, from the Kyleakin roundabout at the Skye Bridge end: the A87 to Broadford; a spur on
the A851 to Armadale and back; the A87 to Sligachan; the A863 and the B8009 to the Glen Brittle
road, a spur to the Fairy Pools car park and back; the B8009 on to Carbost and back to the A863;
the A863 to Dunvegan; a spur on the B884 and Waterstein Road to Neist Point and back; the A863, the
A850 and the A87 to Uig; the A855 round by Staffin and the Storr to Portree. The spurs are
out-and-back legs.

`tests/fixtures/make_track.py --step-m 100` builds the track from OpenStreetMap ways,
joined and resampled every 100 m. It is 282.98 km long, 2,853 points.

The track is a derivative of OpenStreetMap data, so `track.gpx` is licensed under the ODbL
(see Licences).

## Checks

`make_track.py` required, and the build passed, these distances from the track to OpenStreetMap
nodes (distance, then limit):

| Place | Node | Metres | Limit |
|---|---|---|---|
| Kyleakin | 13061972609 (`Welcome to Kyleakin`) | 93 | 300 |
| Broadford | 282090795 | 0 | 300 |
| Armadale | 4173438090 (`Armadale Ferry Terminal`) | 72 | 200 |
| Sligachan | 413289874 | 29 | 400 |
| Fairy Pools car park | 2920914335 (a node of way 288535229) | 3 | 100 |
| Carbost | 494147722 (`Talisker Distillery`) | 34 | 300 |
| Dunvegan | 267259178 | 0 | 500 |
| Neist Point | 3533914185 (a node of the car park, way 346948970) | 1 | 200 |
| Uig | 754453622 (`Uig Post Office`) | 12 | 300 |
| Staffin | 999855962 (`Staffin Post Office`) | 58 | 300 |
| Portree | 46628151 | 61 | 400 |

Length 240 to 320 km: 282.98 km. The Uig ferry terminal (node 2172200513) is 416 m from the
route: the A87 passes above the pier road, so Uig is checked at its post office.

## Files

| File | What it is |
|---|---|
| `track.gpx` | The generated track. |
| `overpass-ada01f635902a1fd.json` | OSM features for the feature box, from Overpass. |
| `landcover-ada01f635902a1fd.json` | OSM land cover for the wider land cover box, from Overpass. |
| `elevation-ada01f635902a1fd.json` | 80 by 80 SRTM grid over the feature box, from OpenTopoData. |

Each payload is named `<kind>-<key>.json`, where the key is the fetch cache key of this track
with the shipped providers and the margins of 18,000 m below, so a cache over a copy of this
directory built with those margins finds every payload and fetches nothing.

## Source

- **Ways**: fetched from the Overpass mirror
  `https://maps.mail.ru/osm/tools/overpass/api/interpreter` (the usual `overpass-api.de` resets
  connections from the recording environment) by `make_track.py`; ids and versions below.
- **OSM features and land cover**: the same mirror, two queries over the margin boxes below. The
  recorder trimmed them (`trim_fixture.py`: minified, only the fields and tags the code reads), then
  they were simplified at 25 m (`--simplify-m 25`, a quarter of a display pixel at the card's 106.4
  metres per pixel) and scale-aware drops were applied: `--drop-minor-roads` (the minor road and
  footpath classes; the pen paints them only below 8 display metres per pixel) and `--min-area-m2
  11326` (closed ways and multipolygons under one display pixel squared, except water, coast,
  places and named areas). Skye alone is simplified and dropped (ADR 0032).
- **Elevation**: SRTM 30 m (`srtm30m` dataset) via the OpenTopoData public API at
  `https://api.opentopodata.org/v1/srtm30m`. 64 calls of 100 points.
- **Contact string sent**: `https://github.com/findlaywebb/pyntpot`.
- **Fetched**: 2026-10-25.

## Bounding boxes

South, west, north, east, in degrees.

| Box | South | West | North | East |
|---|---|---|---|---|
| Track points lie inside (rounded outward to 0.01) | 57.06 | -6.78 | 57.69 | -5.74 |
| `--box` for the `ref=` items | 57.00 | -6.85 | 57.72 | -5.746 |
| Features and elevation (track plus 18000 m) | 56.901273 | -7.078788 | 57.847557 | -5.445012 |
| Land cover (track plus 18000 m) | 56.901273 | -7.078788 | 57.847557 | -5.445012 |

Fetched with margins of 18,000 m for the features and elevation and for land cover: the smallest whole kilometre covering the card box's largest overhang beyond the track's box (16,871 m, to the west, from the aspect floor), plus 1 km of headroom. The card box lies inside the features box (`test_places.py` asserts it).

Overpass returns full geometry for every way and relation touching a box, so the two
Overpass payloads hold coordinates well outside these boxes.

The `--box` east edge, -5.746, sits just west of the Kyleakin roundabout, the Skye Bridge end,
so the bridge and the mainland A87 beyond it are outside the box.

## Ways

Joined in this order by `make_track.py --box 57.00,-6.85,57.72,-5.746 --step-m 100 --ways`.
A `ref=REF:FROM:TO` item takes every highway way carrying that `ref` in the box, chained
end to end and cut at the two node ids. Three refs chain cleanly: `A851`, `A863` and `B884`.
The others did not, and are listed by way id (`ID` whole, `ID:FROM:TO` the part between two
node ids): `A87` forks at ways 37677537, 417693320 and 1083622389; `B8009` forks at ways
40622715, 294894878 and 417681235; `A850` and `A855` are not one line (the chain finds gaps
over 5 m). The Glen Brittle road and the last stretch of the road to Neist Point carry no `ref`,
so they are listed by id too.

```
33236135:267413651:377057551,43999759:377057551:35528025,43999756:35528025:559469464,40976026:559469464:35528022,43999841:35528022:559470582,43999840:559470582:559470581,33237002:559470581:3829673801,209343373:3829673801:2195659884,209343372:2195659884:2195659864,33236999:2195659864:35528014,314151780:35528014:3201981852,314151771:3201981852:3201981851,185194215:3201981851:1957526056,185194214:1957526056:1957526057,417953357:1957526057:32018141,ref=A851:32018141:11066779915,ref=A851:11066779915:32018141,865939957:32018141:441751092,1100723923:441751092:10073965326,1100723924:10073965326:32018135,44448070:32018135:576015026,209346236:576015026:2195683742,209346235:2195683742:2195683658,1230313177:2195683658:32018117,37677539:32018117:8796477515,950194129:8796477515:32018107,417693320:32018107:9930421650,1083622389:9930421650:441751032,37677537:441751032:441751028,1160529129:441751028:441695023,1162265457:441695023:10809195866,1162265458:10809195866:10809195867,1162265456:10809195867:441750980,223002379:441750980:2319498099,314151779:2319498099:3201983482,314151777:3201983482:32018075,43999900:32018075:559471330,43999901:559471330:32018051,250221920:32018051:32017995,1465393490:32017995:13440373724,250221915:13440373724:999918395,49917810:999918395:461726639,314151772:461726639:3201983497,314151774:3201983497:461726597,314151781:461726597:3201983479,314151775:3201983479:32017968,1052386060:32017968:9671598544,1052386061:9671598544:9671598612,35557177:9671598612:416648816,35557197:416648816:416648922,417681232:416648922:32016413,1083622413:32016413:3201819419,1083622413:3201819419:32016413,ref=A863:32016413:13435921422,1464876401,22725913:2394064078:494147743,40682126,40682125,44204086,230983876,286471680,286471681,230983877,286471506,286471507:2901499823:299209977,286471510:299209977:2901499841,286471509:2901499841:388580076,301686157:388580076:10756157721,1156624898:10756157721:10756157722,1156624897:10756157722:3057802084,301686156:3057802084:243761753,301686151:243761753:762197253,301686152:762197253:388580062,288534668:388580062:388581927,169271340,288534670,941060104:2920904882:1804371684,941060104:1804371684:2920904882,288534670:2920904882:2920904884,169271340:2920904884:388581927,288534668:388581927:388580062,301686152,301686151,301686156,1156624897,1156624898,301686157,286471509,286471510,286471507:299209977:2394064009,230983878,301688708,301688707,294894872:243762105:2985264264,1529403269:2985264264:13352258170,40682122:13352258170:388582545,1475511877:388582545:12330664911,1475511877:12330664911:388582545,40682122,1529403269,294894872,301688707:243762105:3057835621,301688708:3057835621:388580080,230983878:388580080:2394064009,286471507:2394064009:2901499823,286471506:2901499823:243761931,230983877:243761931:2394064068,286471681:2394064068:2901499273,286471680:2901499273:2901499272,230983876:2901499272:2394064019,44204086:2394064019:561457876,40682125:561457876:243761915,40682126:243761915:494147743,22725913:494147743:35414422,ref=A863:35414422:1290144972,ref=A863:1290144972:2521002334,ref=B884:2521002334:243762624,418133022:243762624:243762622,34495876:243762622:3533914294,346948971,346948971:3533914295:3533914294,34495876:3533914294:243762622,418133022,ref=B884:243762624:2521002334,ref=A863:2521002334:35350711,169157767,236399181,236399180,389431628,389431629,236399179,419874075,292965499,292965488,417907754,292965494,417907752,292965500,406494827,406494828,254402913,254402912,417902947,417902946,245211093,245211088,240313356,240313357,245211092,245211085,245211083,245211094,248294246:1993009000:2550971023,248294245:2550971023:2550971231,60495160:2550971231:754336009,60495161:754336009:754336047,60615578:754336047:758133786,60615577:758133786:758133781,386840095:758133781:3901963542,60495649:3901963542:754367958,60495648:754367958:754367964,60495654:754367964:754368135,60495655:754368135:754387307,60495657:754387307:754387332,60495656:754387332:32016077,60495458:32016077:36147055,313986733:36147055:2333709900,313986732:2333709900:3200253414,315513033:3200253414:3216247988,232684458:3216247988:32016065,315513032:32016065:3216247987,671288252:3216247987:1780188424,671288252:1780188424:3216247987,315513032,232684458,315513033,313986732,313986733,60615540:36147055:754475060,60615539:754475060:546947481,60499732:546947481:36147041,5183446:36147041:14024409681,1540291919:14024409681:755704864,1540291918:755704864:36146972,387732836:36146972:3909794305,387796761:3909794305:3910292156,387796760:3910292156:3910292168,387732835:3910292168:36146944,5183513,86254015:36147529:9941464340,1084960825:9941464340:1001198683,86254014:1001198683:1001198684,686796000:1001198684:6437834602,686795999:6437834602:2333688876,1083622448:2333688876:1001175020,1083918464:1001175020:35451181,1083622447:35451181:35451161,86252218:35451161:1001141148,290940202:1001141148:35451108,364974942:35451108:1001141190,364974951:1001141190:35451104,86251721:35451104:1001131291,314096598:1001131291:3201362624,314096597:3201362624:35451088,86154310:35451088:35451083,1553820493:35451083:14136667108,290940197:14136667108:1000035598,290940191:1000035598:1000035578,319907880:1000035578:3263953783,319907879:3263953783:3263953782,290940243:3263953782:1000035506,290940205:1000035506:35451019,936925212:35451019:14157227404,1556537580:14157227404:14157227405,1556537579:14157227405:8681235748,936925213:8681235748:8681235749,295647647:8681235749:14157529956,1556567066:14157529956:14157529957,1556567065:14157529957:35450958,1083622431:35450958:67452654,1083622432:67452654:35450943,936925214:35450943:2993819881,295647649:2993819881:35450926,86154271:35450926:35450920,86154261:35450920:1000035367,86154260:1000035367:35450913,377555279:35450913:35450905,377922983:35450905:35450896,86154255:35450896:1000035234,86154253:1000035234:35450870,169157768,377922985,377555272,205301525,205301526,679915339,1557579721,377922984,236398153,25862281:35450818:34580464,1529268428:34580464:470536344,25862279:470536344:34580460,25862277:34580460:34580454,328880512:34580454:470536220,25862275:470536220:34580452,95224477:34580452:13395139814
```

8 of the items are `ref=` items. The ways below are every way the build fetched
(each `ref=` item's whole ref in the box, and each listed id), with the version
fetched.

| Way | Version | `highway` | `ref` | `name` |
| --- | --- | --- | --- | --- |
| 33236135 | 11 | trunk | A87 | - |
| 43999759 | 18 | trunk | A87 | - |
| 43999756 | 12 | trunk | A87 | - |
| 40976026 | 16 | trunk | A87 | - |
| 43999841 | 10 | trunk | A87 | - |
| 43999840 | 12 | trunk | A87 | - |
| 33237002 | 21 | trunk | A87 | - |
| 209343373 | 8 | trunk | A87 | - |
| 209343372 | 7 | trunk | A87 | - |
| 33236999 | 26 | trunk | A87 | - |
| 314151780 | 13 | trunk | A87 | - |
| 314151771 | 6 | trunk | A87 | - |
| 185194215 | 11 | trunk | A87 | - |
| 185194214 | 7 | trunk | A87 | - |
| 417953357 | 6 | trunk | A87 | - |
| 865939957 | 6 | trunk | A87 | - |
| 1100723923 | 2 | trunk | A87 | - |
| 1100723924 | 2 | trunk | A87 | - |
| 44448070 | 19 | trunk | A87 | - |
| 209346236 | 17 | trunk | A87 | - |
| 209346235 | 9 | trunk | A87 | - |
| 1230313177 | 1 | trunk | A87 | - |
| 37677539 | 36 | trunk | A87 | - |
| 950194129 | 3 | trunk | A87 | - |
| 417693320 | 5 | trunk | A87 | - |
| 1083622389 | 2 | trunk | A87 | - |
| 37677537 | 12 | trunk | A87 | - |
| 1160529129 | 4 | trunk | A87 | - |
| 1162265457 | 1 | trunk | A87 | - |
| 1162265458 | 2 | trunk | A87 | - |
| 1162265456 | 2 | trunk | A87 | - |
| 223002379 | 11 | trunk | A87 | - |
| 314151779 | 8 | trunk | A87 | - |
| 314151777 | 5 | trunk | A87 | - |
| 43999900 | 21 | trunk | A87 | - |
| 43999901 | 9 | trunk | A87 | - |
| 250221920 | 10 | trunk | A87 | - |
| 1465393490 | 1 | trunk | A87 | - |
| 250221915 | 4 | trunk | A87 | - |
| 49917810 | 18 | trunk | A87 | - |
| 314151772 | 3 | trunk | A87 | - |
| 314151774 | 5 | trunk | A87 | - |
| 314151781 | 3 | trunk | A87 | - |
| 314151775 | 6 | trunk | A87 | - |
| 1052386060 | 2 | trunk | A87 | - |
| 1052386061 | 3 | trunk | A87 | - |
| 35557177 | 39 | trunk | A87 | - |
| 35557197 | 17 | trunk | A87 | - |
| 417681232 | 3 | trunk | A87 | - |
| 1083622413 | 1 | trunk | A87 | - |
| 1464876401 | 1 | secondary | - | - |
| 22725913 | 22 | secondary | B8009 | - |
| 40682126 | 3 | secondary | B8009 | - |
| 40682125 | 4 | secondary | B8009 | - |
| 44204086 | 9 | secondary | B8009 | - |
| 230983876 | 12 | secondary | B8009 | - |
| 286471680 | 8 | secondary | B8009 | - |
| 286471681 | 4 | secondary | B8009 | - |
| 230983877 | 6 | secondary | B8009 | - |
| 286471506 | 6 | secondary | B8009 | - |
| 286471507 | 4 | secondary | B8009 | - |
| 286471510 | 11 | tertiary | - | - |
| 286471509 | 10 | tertiary | - | - |
| 301686157 | 7 | tertiary | - | - |
| 1156624898 | 1 | tertiary | - | - |
| 1156624897 | 2 | tertiary | - | - |
| 301686156 | 8 | tertiary | - | - |
| 301686151 | 6 | tertiary | - | - |
| 301686152 | 7 | tertiary | - | - |
| 288534668 | 8 | tertiary | - | - |
| 169271340 | 6 | service | - | - |
| 288534670 | 2 | service | - | - |
| 941060104 | 3 | service | - | - |
| 230983878 | 5 | secondary | B8009 | - |
| 301688708 | 4 | secondary | B8009 | - |
| 301688707 | 4 | secondary | B8009 | - |
| 294894872 | 6 | secondary | B8009 | - |
| 1529403269 | 1 | secondary | B8009 | - |
| 40682122 | 13 | secondary | B8009 | - |
| 1475511877 | 1 | secondary | B8009 | - |
| 418133022 | 6 | unclassified | - | Waterstein Road |
| 34495876 | 22 | unclassified | - | Waterstein Road |
| 346948971 | 1 | service | - | - |
| 169157767 | 21 | primary | A850 | - |
| 236399181 | 10 | primary | A850 | - |
| 236399180 | 18 | primary | A850 | - |
| 389431628 | 3 | primary | A850 | - |
| 389431629 | 3 | primary | A850 | - |
| 236399179 | 17 | primary | A850 | - |
| 419874075 | 3 | primary | A850 | - |
| 292965499 | 3 | primary | A850 | - |
| 292965488 | 7 | primary | A850 | - |
| 417907754 | 4 | primary | A850 | - |
| 292965494 | 3 | primary | A850 | - |
| 417907752 | 3 | primary | A850 | - |
| 292965500 | 17 | primary | A850 | - |
| 406494827 | 10 | primary | A850 | - |
| 406494828 | 23 | primary | A850 | - |
| 254402913 | 3 | primary | A850 | - |
| 254402912 | 7 | primary | A850 | - |
| 417902947 | 5 | primary | A850 | - |
| 417902946 | 10 | primary | A850 | - |
| 245211093 | 3 | primary | A850 | - |
| 245211088 | 7 | primary | A850 | - |
| 240313356 | 6 | primary | A850 | Skeabost Bridge |
| 240313357 | 12 | primary | A850 | - |
| 245211092 | 5 | primary | A850 | - |
| 245211085 | 4 | primary | A850 | - |
| 245211083 | 5 | primary | A850 | - |
| 245211094 | 4 | primary | A850 | - |
| 248294246 | 8 | trunk | A87 | - |
| 248294245 | 5 | trunk | A87 | - |
| 60495160 | 18 | trunk | A87 | - |
| 60495161 | 10 | trunk | A87 | - |
| 60615578 | 14 | trunk | A87 | - |
| 60615577 | 4 | trunk | A87 | Romesdal Bridge |
| 386840095 | 4 | trunk | A87 | - |
| 60495649 | 18 | trunk | A87 | - |
| 60495648 | 7 | trunk | A87 | Hinnisdal Bridge |
| 60495654 | 25 | trunk | A87 | - |
| 60495655 | 16 | trunk | A87 | - |
| 60495657 | 7 | trunk | A87 | - |
| 60495656 | 7 | trunk | A87 | - |
| 60495458 | 16 | trunk | A87 | - |
| 313986733 | 7 | trunk | A87 | - |
| 313986732 | 5 | trunk | A87 | - |
| 315513033 | 4 | trunk | A87 | - |
| 232684458 | 9 | trunk | A87 | - |
| 315513032 | 5 | trunk | A87 | - |
| 671288252 | 9 | trunk | A87 | - |
| 60615540 | 12 | primary | A855 | - |
| 60615539 | 4 | primary | A855 | - |
| 60499732 | 12 | primary | A855 | - |
| 5183446 | 44 | primary | A855 | - |
| 1540291919 | 1 | primary | A855 | - |
| 1540291918 | 2 | primary | A855 | - |
| 387732836 | 3 | primary | A855 | - |
| 387796761 | 8 | primary | A855 | - |
| 387796760 | 4 | primary | A855 | - |
| 387732835 | 13 | primary | A855 | - |
| 5183513 | 15 | primary | A855 | - |
| 86254015 | 15 | primary | A855 | - |
| 1084960825 | 4 | primary | A855 | - |
| 86254014 | 4 | primary | A855 | - |
| 686796000 | 10 | primary | A855 | - |
| 686795999 | 4 | primary | A855 | - |
| 1083622448 | 6 | primary | A855 | - |
| 1083918464 | 2 | primary | A855 | - |
| 1083622447 | 6 | primary | A855 | - |
| 86252218 | 34 | primary | A855 | - |
| 290940202 | 5 | primary | A855 | - |
| 364974942 | 8 | primary | A855 | - |
| 364974951 | 5 | primary | A855 | - |
| 86251721 | 18 | primary | A855 | - |
| 314096598 | 6 | primary | A855 | - |
| 314096597 | 7 | primary | A855 | - |
| 86154310 | 16 | primary | A855 | - |
| 1553820493 | 1 | primary | A855 | - |
| 290940197 | 7 | primary | A855 | - |
| 290940191 | 4 | primary | A855 | - |
| 319907880 | 10 | primary | A855 | - |
| 319907879 | 6 | primary | A855 | - |
| 290940243 | 9 | primary | A855 | - |
| 290940205 | 9 | primary | A855 | - |
| 936925212 | 6 | primary | A855 | - |
| 1556537580 | 1 | primary | A855 | - |
| 1556537579 | 1 | primary | A855 | - |
| 936925213 | 3 | primary | A855 | - |
| 295647647 | 13 | primary | A855 | - |
| 1556567066 | 1 | primary | A855 | - |
| 1556567065 | 1 | primary | A855 | - |
| 1083622431 | 5 | primary | A855 | - |
| 1083622432 | 5 | primary | A855 | - |
| 936925214 | 7 | primary | A855 | - |
| 295647649 | 5 | primary | A855 | - |
| 86154271 | 23 | primary | A855 | - |
| 86154261 | 11 | primary | A855 | - |
| 86154260 | 11 | primary | A855 | - |
| 377555279 | 7 | primary | A855 | - |
| 377922983 | 7 | primary | A855 | - |
| 86154255 | 10 | primary | A855 | - |
| 86154253 | 10 | primary | A855 | - |
| 169157768 | 12 | primary | A855 | - |
| 377922985 | 3 | primary | A855 | - |
| 377555272 | 8 | primary | A855 | - |
| 205301525 | 5 | primary | A855 | - |
| 205301526 | 11 | primary | A855 | - |
| 679915339 | 4 | primary | A855 | - |
| 1557579721 | 1 | primary | A855 | - |
| 377922984 | 7 | primary | A855 | - |
| 236398153 | 11 | primary | A855 | Staffin Road |
| 25862281 | 13 | primary | A855 | Staffin Road |
| 1529268428 | 1 | primary | A855 | Staffin Road |
| 25862279 | 11 | primary | A855 | Mill Road |
| 25862277 | 16 | primary | A855 | Barraid Bosville |
| 328880512 | 11 | primary | A855 | Bank Street |
| 25862275 | 17 | primary | A855 | Bank Street |
| 95224477 | 18 | primary | A855 | The Green |
| 4904828 | 19 | primary | A851 | - |
| 34377979 | 17 | primary | A851 | - |
| 34377980 | 12 | primary | A851 | - |
| 34377982 | 20 | primary | A851 | - |
| 34377983 | 9 | primary | A851 | - |
| 34377985 | 19 | primary | A851 | - |
| 52104532 | 14 | primary | A851 | - |
| 52104642 | 7 | primary | A851 | Drochaid a' Mhuilinn |
| 52104643 | 9 | primary | A851 | - |
| 52105286 | 6 | primary | A851 | - |
| 52105287 | 7 | primary | A851 | - |
| 83336241 | 6 | primary | A851 | - |
| 83336243 | 14 | primary | A851 | - |
| 185194212 | 9 | primary | A851 | - |
| 203982024 | 7 | primary | A851 | - |
| 203982025 | 7 | primary | A851 | - |
| 203984843 | 8 | primary | A851 | - |
| 203984846 | 9 | primary | A851 | - |
| 221008308 | 18 | primary | A851 | - |
| 221030882 | 5 | primary | A851 | - |
| 221030885 | 10 | primary | A851 | - |
| 417954748 | 5 | primary | A851 | - |
| 1091960508 | 3 | primary | A851 | - |
| 1091960509 | 2 | primary | A851 | - |
| 1097704382 | 3 | primary | A851 | - |
| 1097704383 | 4 | primary | A851 | - |
| 1451049763 | 2 | primary | A851 | - |
| 1451049764 | 2 | primary | A851 | - |
| 1451049765 | 2 | primary | A851 | - |
| 1451053229 | 2 | primary | A851 | - |
| 1451053230 | 1 | primary | A851 | - |
| 1547448530 | 1 | primary | A851 | - |
| 116352965 | 34 | primary | A863 | - |
| 116353656 | 20 | primary | A863 | - |
| 116353658 | 8 | primary | A863 | - |
| 205421950 | 13 | primary | A863 | - |
| 205421951 | 4 | primary | A863 | - |
| 236399177 | 13 | primary | A863 | - |
| 236399178 | 13 | primary | A863 | - |
| 236399182 | 17 | primary | A863 | - |
| 236399183 | 13 | primary | A863 | - |
| 245038552 | 21 | primary | A863 | - |
| 245038553 | 6 | primary | A863 | - |
| 245072293 | 5 | primary | A863 | - |
| 245072295 | 11 | primary | A863 | - |
| 290940370 | 3 | primary | A863 | - |
| 290940380 | 6 | primary | A863 | - |
| 290940388 | 3 | primary | A863 | - |
| 290940392 | 6 | primary | A863 | - |
| 290940414 | 3 | primary | A863 | - |
| 290940421 | 5 | primary | A863 | - |
| 290940443 | 5 | primary | A863 | - |
| 290940450 | 7 | primary | A863 | - |
| 290940456 | 13 | primary | A863 | - |
| 417681225 | 21 | primary | A863 | - |
| 417907755 | 5 | primary | A863 | - |
| 418130317 | 2 | primary | A863 | - |
| 418130319 | 3 | primary | A863 | - |
| 418130320 | 3 | primary | A863 | - |
| 1083622411 | 4 | primary | A863 | - |
| 1083622412 | 3 | primary | A863 | - |
| 1464335087 | 3 | primary | A863 | - |
| 1464335088 | 1 | primary | A863 | - |
| 1474492274 | 1 | primary | A863 | - |
| 1474492276 | 1 | primary | A863 | - |
| 1484581032 | 2 | primary | A863 | - |
| 22725936 | 16 | secondary | B884 | - |
| 22725959 | 13 | secondary | B884 | - |
| 86264097 | 7 | secondary | B884 | - |
| 86264101 | 10 | secondary | B884 | - |
| 86264104 | 10 | unclassified | B884 | - |
| 241641648 | 4 | secondary | B884 | - |
| 241641675 | 10 | secondary | B884 | - |
| 241641677 | 6 | secondary | B884 | - |
| 244072933 | 8 | secondary | B884 | - |
| 244072934 | 6 | secondary | B884 | - |
| 244072935 | 31 | secondary | B884 | - |
| 244179994 | 6 | secondary | B884 | - |
| 244179995 | 6 | secondary | B884 | - |
| 1489842921 | 1 | secondary | B884 | - |
| 1489842922 | 1 | secondary | B884 | - |
| 1492785626 | 2 | secondary | B884 | - |
| 1492785627 | 2 | secondary | B884 | - |

## Size

The payloads are committed trimmed, simplified and dropped (see Source). The budget is 13,000,000 bytes on disk for the directory (the measured size rounded up to the next half megabyte, by the maintainer's ruling not to stop Skye for a slight overrun of 12 MB),
enforced by `tests/architecture/test_coordinates.py`.

| File | Bytes | Gzip bytes |
|---|---|---|
| `elevation-ada01f635902a1fd.json` | 39,274 | 6,889 |
| `landcover-ada01f635902a1fd.json` | 3,698,328 | 619,379 |
| `overpass-ada01f635902a1fd.json` | 8,615,542 | 1,537,408 |
| `track.gpx` | 134,315 | 22,521 |
| **Total, README excluded** | **12,487,459** | **2,186,197** |

## Licences and attribution

Contains OpenStreetMap data © OpenStreetMap contributors, available under the Open
Database Licence (openstreetmap.org/copyright).

`track.gpx` and the two Overpass payloads are a derivative database of OpenStreetMap and
are distributed under the ODbL.

Elevation data: NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second* [Dataset]. NASA Land Processes Distributed Active Archive Center.
https://doi.org/10.5067/MEASURES/SRTM/SRTMGL1.003
