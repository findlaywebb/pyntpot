# 006 plan review 4

**Verdict: PASS**

The round-3 blocker is fixed, and I checked the fix against the code. The five
should-fixes and the two consider items went in correctly. The round-3 diff
(`git diff 3283e88 6baba86`, plan.md and spec.md only) adds no defect that would make a
slice fail, and it touches nothing earlier reviews passed.

Reviewed at `6baba86`. I ran the probes from the repo venv against the Lynmouth fixture.
Scratch scripts only; nothing in the tree was changed.

## Round-3 blocker: verified

**B1, the too-short example is now `Lee Road`.** I re-ran round 3's in-process check:

- I painted the fixture and patched `named_lines` to add S7's `numbered` key.
- I replaced `_ground` with the plan's version, and added `_road_pieces` and
  `named_roads` with the logic copied from S7 (`classes=None`, match by casefolded key or
  OSM name, too-short log, `named or pick_roads`).
- I called the real `letter`, which runs the real `place`, on a copied plates directory.

| `roads` | Matched key and run | Placed road labels | Plan expects |
| --- | --- | --- | --- |
| `()` | none | `['A39', 'B3234']`, all labels = `PINNED_LABELS` | same |
| `("Lee Road",)` | `Lee Road`, 70.0 px; logs `road Lee Road is too short…` | `['A39', 'B3234']`, all labels = `PINNED_LABELS` | same |
| `("B3223",)` | `B3223`, 274.2 px | `['B3223']` | same |
| `("B3234",)` | `B3234`, 358.9 px | `['B3234']` | same |
| `("Lynbridge Road",)` | `B3234`, 358.9 px | `['B3234']` | same |
| `("Lydiate Lane",)` | `Lydiate Lane`, 123.4 px | `['Lydiate Lane']` | same |

Some facts behind those rows:

- `Lee Road` is `cls='minor'` with `ref=''`, so its key is its name and the INFO line
  says `Lee Road`, as the test asserts. No numbered piece carries the OSM name "Lee
  Road", so the name matches only that one key. Nothing else gets lettered by accident.
- The new positive test is right. The fixture's B3223 has pieces `Scobhill Road`,
  `Hillsford Bridge` and one unnamed `ref=B3223` piece. With that piece joined in, `place`
  actually sets the label.
- The plan's measurements paragraph (plan.md:797-804) and the spec's acceptance line
  (spec.md:102-104) now agree with these figures.

## Round-3 should-fixes: checked for new defects

1. **The self-check pathspec runs.** `git diff <commit> -U0 -- '*.py' '*.md' ':!specs'
   ':!docs/decisions'` exits 0 and the exclusions apply. Its `$slice_base` is defined for
   both the parallel and the serial slices.
2. **The `test_ground.py` card works.** `tiny_basemap(class_style(display_px=320,
   supersample=1))` builds:
   - The card is 320×198 display px.
   - The route runs over x 91–229, y 96–102.
   - `label_ground` defaults to True.
   - A picked `A591` within 40 px of the route and longer than 89.6 px fits on the card.
     So does an `A66` more than 40 px off the route (for example y ≈ 30 or 170, up to
     320 px long). The prescription is feasible.
3. **The bloom pattern selects only `bloom`.** mutmut 3.8.0 filters mutant names with
   `fnmatch` (`mutmut/__main__.py:813`). `pyntpot.ink.bloom.x_bloom__mutmut_*` matches
   `x_bloom__mutmut_1` and not `x_bloom_radius__mutmut_1`. `ink/bloom.py` defines
   `bloom_radius`, `highest` and `bloom`, so only `bloom` is selected.
4. **S9 done criterion 3.** The criterion now names N19, C3, C8 and R6. It is consistent
   with S4, S5 and S6, which own those moves. No new defect.
5. **The Old Lake Road test.** "Beside the route, longer than `road_min_px`, route pixels
   passed to `pick_roads`" leaves the class filter as the only reason `pick_roads` skips
   the road, which matches `picks_roads.py:83`. It is feasible on `hung_card`.

Consider items:

- The docstring note on the moved label agrees with the 358.9 px against 173.4 px run
  measured above.
- The expected rebase conflict is now named under Slices.

## Regressions

None. The diff touches only S7's tests and measurements, the Approach self-check, S9
criterion 3, S10's bloom row, and the Slices note. No owned-file list, signature,
pinned name list or merge order changed.

## Suggestions (non-blocking)

- **The self-check after a rebase.** A parallel slice that runs the self-check after
  rebasing on an earlier-merged lane, diffing against S3's commit, also sees that lane's
  lines. The check is clean either way, because every lane obeys it. But "the slice's
  own commit range" (`git diff <merge-base-before-rebase>`) is the stricter reading.
  Mention it only if an orchestrator trips on it.
- **caplog in the Lee Road test.** The `letter`-level Lee Road test asserts an INFO line
  from `pyntpot.maps.lettering.picks_roads`. `caplog.set_level(logging.INFO,
  logger="pyntpot.maps.lettering.picks_roads")`, or a root-level INFO, avoids a
  logger-level surprise if any config raises that logger's level.
