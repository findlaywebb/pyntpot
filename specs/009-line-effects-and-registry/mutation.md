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
