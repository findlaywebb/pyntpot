# Lettering costs about twice main's since names keep off the water

GitHub issue: [#115](https://github.com/findlaywebb/pyntpot/issues/115)

Area: maps (lettering, performance).

PR #112 taught the placer to keep flat names off lakes and water strokes
(`pyntpot.maps.lettering.placement_water`) and let a river's flat name sit beside any of
12 points along its own course. Both add work to every candidate seat, and `letter` got
slower:

| Measure (Lynmouth benchmark, `test_letter`) | main | PR #112 |
|---|---|---|
| CodSpeed simulation | 1 s | 2.1 s |
| callgrind, `letter` alone, plate already stroked | 3.68 G | 4.73 G (1.29x) |
| Wall time on one machine | 1.56 s | 1.40 s (noise) |

The first version was 25x slower in wall time and 5.6x by CodSpeed. Two changes in
PR #112 brought it down to these figures:

- a summed-area table of the pixels where water could lie, built once per card, so a dry
  box is priced in constant time;
- an early exit in `placement_flat._seat_cost`, which abandons a seat once it can no
  longer win.

Neither moves a seat.

What remains:

- The river course anchors add flat candidates, and each candidate pays
  `off_own_feature` distance sums and `near_route` calls.
- Boxes that do touch water still run the full stroke test (331 of them on the
  benchmark).

Measured 2026-11-03 with valgrind callgrind against main at b2f688e.

Possible fix:

- Add a river's course anchors only when its usual seats all fail, or cap them at a few.
  This moves seats, so the goldens need regenerating under an ADR.
- Or vectorise the per-candidate distance sums.

Overlaps with #113, which reworks how seats are found and priced.
