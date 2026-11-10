# Wide casings are slow: contour_distance costs the square of its radius
GitHub issue: [#214](https://github.com/findlaywebb/pyntpot/issues/214)

Area: ink (performance). Label: `performance`, `area: ink`.

`contour_distance` (`src/pyntpot/ink/effect_distance.py`) is one direct search over a disc of
pixel offsets, so its cost grows with the square of the radius its caller passes. Measured on a
1800 x 1281 array:

| Radius | Time |
| --- | --- |
| 3 | 0.28 s |
| 8 | 0.74 s |
| 16 | 2.24 s |
| 33 | 8.81 s |

No figure or theme asks for a radius past 12 (a casing or reserve of 11 px), so nothing is slow
today. A casing of 30 px or more on a full-size plate is. A faster form would have to keep the
0.4 px accuracy the property in `tests/property/test_contour_distance.py` claims for wide rings,
which a separable or chamfer bound does not; an exact Euclidean transform of the seeds is the
likely route.
