# Some ink docstrings still say metres where the unit is world units

GitHub issue: [#197](https://github.com/findlaywebb/pyntpot/issues/197)

Area: ink (docstrings).

`ink` is map-agnostic and works in world units. `Canvas` in `src/pyntpot/ink/sheet.py`
now says so (feature 006), but other `ink` docstrings and comments still say "metre(s)".
`git grep -n -i "metre" -- src/pyntpot/ink` finds them:

- `src/pyntpot/ink/brush_style.py:31`, `:32`, `:38`, `:39`, `:41`, `:43`
- `src/pyntpot/ink/chains.py:46`, `:48`
- `src/pyntpot/ink/polyline.py:10`, `:191`
- `src/pyntpot/ink/raster.py:8`, `:9`, `:32`, `:64`, `:80`, `:86`, `:91`, `:129`
- `src/pyntpot/ink/style.py:161`, `:168`, `:189`, `:190`

(`kilometres` at `brush_style.py:31` is part of the same sentence as line 32.)

The fix is docstring-only wording: say "world units" for the unit. Maps may keep
"metres", since a map's world unit is the metre.

Source: `specs/006-one-public-surface/review/diff-review.md`, nice-to-have 1.
