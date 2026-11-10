# Mutation testing: spec 009 (S8)

Scope: `uv run python tests/mutation/scope.py --base dfc3747 --out "$patterns"`, run with
`mutmut run --max-children 2` under `prlimit --as=3500000000`. 34 changed `ink` and `letters`
functions, 543 mutants.

- **Base.** `dfc3747` is the merge base with `main`. `origin/main` has moved on since and
  changes `ink` and `letters` functions of its own (`polyline`, `trace`, `hand`, ...);
  `--base origin/main` pulled 86 functions into scope, 52 of them not this branch's. The
  merge base is the right diff.
- **Moved, not changed.** The functions of `ink/compositing.py` (moved from `ink/pigment.py`
  unchanged) are not in the scope list, so they are not run.
- **Harness.** mutmut 3.8 reads `item._nodeid`, which pytest 9.2 renamed `nodeid`, so stats
  collection fails with the repo's pins. The run used a `sitecustomize.py` outside the repo
  that aliases `Node._nodeid`; nothing in the repo changed.

## Result

| | mutants |
| --- | --- |
| Total | 543 |
| Killed by the existing suite | 474 |
| Survived the existing suite | 69 |
| Killed by new tests | 38 |
| Equivalent | 31 |

No survivor revealed a bug in `src`.

## Killed (new tests)

In `tests/unit/ink/test_effect_edges.py`:

- `casing`, `glow`: a mask exactly at the threshold; the soft step's width (2.5 and 2.25);
  the final clip, with a colour beneath of -0.5 and 1.5.
- `pen_casing`: the final clip; float32 dtype of both returned arrays, on and off; the reserve
  being exactly the paper.
- `shadow_offset`: pinned shifts at five bearings (the `+ 181` mutant).
- `_shifted`: float32 dtype, and zero-filled shifts of whole columns and rows.
- `shadow`: the darken toward its colour (pinned value), a mask of 5 taken as 1, a negative
  mask counting as no line, the final clip.
- `nearest`: one suggestion from several close names; `channels`: a stray non-`#` prefix
  refused.

In `tests/unit/ink/test_pigment_entry.py`: `_entry` keeps name, colour, transparency and
colour index. Its mutants survived because `ROLE_PIGMENTS` is built at import, before any
mutant is active, so only a direct call reaches them.

## Equivalent

- `copy=True`, `copy=None` or no `copy` on a final `astype(F32, ...)` (`glow` 39, 41, 50;
  `casing` 32, 34, 43; `pen_casing` 32, 34, 43; `shadow` 48, 50, 67): `np.clip` already
  returns a fresh float32 array, so the copy flag changes cost, not the result.
- `glow` 20: `core.astype(None)` makes float64, which `blur` casts back to float32 first.
- `glow` 11, 12, 22: the clip of a blurred 0/1 field; a normalised box blur stays in 0 to 1
  to within an ulp, which the strength and the final clip absorb.
- `pen_casing` 22: the paper `F32(2.0)` is clipped back to 1 by the final clip.
- `nearest` 9: dropping `cutoff=0.6` leaves difflib's default, which is 0.6.
- `shadow_offset` 3: `azimuth_deg - 180` differs from `+ 180` by a full turn.
- `_shifted` 9, 11: `>=` to `>` at a shift of exactly the size gives an empty slice, so
  the same zeros. `_shifted` 23, 34, 47, 60: `min(d, 1)` for `min(d, 0)` only lengthens a
  slice end past the array, which numpy clamps.
- `shadow` 9: a lower clip of the blurred mask; a negative weight is not above 0, so `rgb`
  is kept either way. `shadow` 33, 39: the upper clip of `mask / threshold`; above 1 the
  factor `1 - x` is negative, so the weight is not above 0 either way.
- `shadow` 63: `weight >= 0` for `> 0`; at weight 0, `dark` is `rgb * 1.0`, which is `rgb`.
- `brush_from_id` 5: `"XXXX".join` over a generator of at most one suggestion has no
  separator to show. `brush_from_id` 16: `rpartition` for `partition` on a known id, which
  has exactly one `-`.

## Re-run: casing and glow leave the line's own pixels untouched

`casing` and `glow` were re-run alone (`pyntpot.ink.effect_casing*`, `pyntpot.ink.effect_glow*`)
after both gained a zero weight where the mask is at or above the threshold. The mutants of the
new `np.where` lines were all killed by the "never changes a pixel under the line's core"
properties and the updated unit cases. The ten survivors are the equivalents already listed
above under their new numbers: `glow` 12, 13, 23 (clip of the blurred 0/1 field), 21 (`astype(None)`),
49, 51, 60 and `casing` 41, 43, 52 (the `copy` flag on the final `astype`). `pen_casing` is
unchanged: it alters the wash beneath the pen line, not the line, so it is exempt from the rule.

## Casing follow-up

Scope: `uv run python tests/mutation/scope.py --base 46ee0d9b`, run with
`mutmut run --max-children 3` under `prlimit --as=3500000000` and the same out-of-repo
`sitecustomize.py`. 15 changed or added `ink` functions: `blend_casing`, `casing`, `pen_casing`,
`reserve`, `pool_band`, `lay_reserve`, `casing_union`, `_check_members`, `contour_distance`,
`_crossings`, `_shifted`, `_slices`, `ring_coverage`, `check_effect_numbers` and
`Reserve.__post_init__`. 778 mutants.

| | mutants |
| --- | --- |
| Total | 778 |
| Killed by the existing suite (one a timeout) | 680 |
| Survived the existing suite | 98 |
| Killed by new tests | 37 |
| Equivalent | 61 |

No survivor revealed a bug in `src`. `_shifted`, `check_effect_numbers` and
`Reserve.__post_init__` had no survivor.

### Killed (new tests)

- `tests/unit/ink/test_contour_distance_exact.py`: the interpolated crossing on a ramp
  (`_crossings` 45); a core pixel seeding its diagonal neighbours (`_crossings` 58); a float64
  mask read as float32 (`contour_distance` 3, 5); the far edge of the search reach and the
  `radius + 2` cap on a dot (`contour_distance` 45, 51, 58, 62, 66, 69).
- `tests/unit/ink/test_effect_reserve_parts.py`: `pool_band` at nine excesses (all 11 mutants);
  `lay_reserve` at half coverage, out-of-range colours and a pool's depth on two grounds (16, 25,
  26, 31, 49, 58, 76); a mask exactly at the threshold in `reserve` (5).
- `tests/unit/ink/test_effect_union_edges.py`: each refusal's full message (`_check_members`
  3, 13, 18, 23, 28); a bar exactly at the threshold under a casing and a reserve union
  (`casing_union` 17); a pooled one-member reserve union equal to `reserve` (`casing_union` 41).
- `tests/unit/ink/test_pen_casing_exact.py`: two pixels pinned bit for bit, so the float32
  blend is told from a float64 one (`pen_casing` 75).

### Equivalent

- `copy=True`, `copy=None` or no `copy` on a final `astype(F32, ...)` of a fresh array
  (`blend_casing` 8, 10, 19; `pen_casing` 84, 86, 95; `contour_distance` 116, 118, 130;
  `ring_coverage` 28, 30, 32; `lay_reserve` 21, 23, 32, 69, 71, 79): the flag changes cost, not
  the result.
- Radius one larger than needed (`casing` 18, `pen_casing` 17, `reserve` 15, `casing_union` 40,
  42, 43): the ring and the pool read distances only up to the old radius plus 1.5, where
  `contour_distance` is already exact.
- `_slices` 1, 2: an offset of 0 takes the other branch, whose slices are the same full range.
  `_slices` 7, 11: `slice(n)` is `slice(None, n)`.
- `_crossings` 4, 7, 49 and `contour_distance` 24: float64 for float32 intermediates of float32
  values, cast back to float32 on return with a single rounding.
- `_crossings` 37, 38, 47 and `contour_distance` 32, 33, 38, 39: a clip bound that never binds,
  because a crossing lies within 1 of its pixel.
- `_crossings` 52, `contour_distance` 119 and `casing_union` 107, `reserve` 36: `None` makes a
  NaN or a false condition, which is never selected, never exceeds 0, or leaves the same pixels.
- `_crossings` 71: `<=` for `<` ties only equal-magnitude candidates of the same sign.
- `contour_distance` 52, 59: the extra offset lies outside the reach circle and is skipped.
  72, 74: `>` for `>=` at an offset of exactly the size gives an empty slice.
- `contour_distance` 64, 65 (skipping one axis step): the opposite-side core seed two pixels away
  reaches the same contour point; the results differ by one float32 ulp.
- `contour_distance` 127, 128, 129: the final `where` only sets `big` where the value is
  already `big`, since no distance exceeds it.
- `pen_casing` 19: at a mask exactly at the threshold, `d` is at most 0, so the reserve is 1 and
  the band 0 either way.
- `lay_reserve` 33 (`pool >= 0`): a pool of 0 raises to the power 1, which libm's `pow`
  returns to within one ulp.
- `lay_reserve` 45: at `out == ground` the pooled value is the ground, the same. 46: a ground of
  0 has no `out` below it. 55, 56, 65, 66: the filler outside `deepen` is discarded by the final
  `where`.
