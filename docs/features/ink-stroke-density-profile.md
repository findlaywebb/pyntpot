# A stroke could change its density and colour along its length

GitHub issue: [#171](https://github.com/findlaywebb/pyntpot/issues/171)

**What exists today.** `stamp` (`pyntpot.ink.stamp`) takes `wprof`, a width multiplier
sampled evenly from a stroke's start to its end, and nothing else that varies along the
stroke. `ink_density` turns the whole accumulator into one density, and a `PigmentLayer`
(`ink/pigment.py`) is one density with one pigment and at most one transparency. So a stroke that fades or changes colour has to
be cut up. The spirograph in `examples/curves.py` (`_paint_spirograph`) does this: it splits
the path into 16 pieces with `np.array_split`, extends each by two points so the pieces
meet (`min(idx[-1] + 3, len(points))`), stamps each into its own accumulator, scales each
piece's density by `1.0 - 0.45 * t` and gives each its own colour from `_mixed`. The 16
layers overlap where the pieces meet, and each piece draws its own bristle phase from the
generator. `docs/tutorials/painting-with-python/curves.md` quotes the whole function and
presents it as technique.

**What the feature would add.** A density profile along one stroke, sampled the same way
as `wprof`, so a stroke can run drier or paler towards its end in one `stamp` call. A
second, larger step is a colour along the stroke: either a profile of pigment mix that
`ink_density` hands on, or a way for one stroke to feed two pigment layers with
complementary densities, so a blend from one pigment to another needs no cutting. The
spirograph then becomes one stroke and loses its magic numbers.

**Possible shape.** A `dprof` keyword on `stamp`, beside `wprof`, multiplying what each
stamp adds to the accumulator; no change for a caller that leaves it out, so no golden
moves. The colour half needs the pigment registry first and probably an ADR, since
`PigmentLayer` holds one pigment today. Rewrite `_paint_spirograph` and its page on top;
that re-pins `curves/spirograph.webp` on purpose. Until then, the page could say plainly
that the cutting is a workaround.

**Related.** `ink-one-pigment-registry.md` (#72) for the blending half;
`docs-examples-review.md` (#63).
