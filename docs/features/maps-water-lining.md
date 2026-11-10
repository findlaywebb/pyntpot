# Water could be lined along its shores

GitHub issue: [#210](https://github.com/findlaywebb/pyntpot/issues/210)

**What exists today.** Water is a filled shape with a coast line: lakes, rivers and the
sea are washed flat and edged once. Nothing echoes the shore into the water.

**What the feature would add.** Water-lining, the hand cartography convention of
parallel lines that follow a shoreline out into the water, each fainter and further
apart than the last, so the water seems to ripple away from the land. It is common in
Swiss and Imhof-school maps and in old engraved charts. Candidates to try: the shore of
Llyn Padarn and Llyn Peris at Llanberis, Windermere, or the coast at Lynmouth.

**Why.** It gives water a hand-drawn texture that a flat wash cannot, and it suits a
library whose point is the look of pen and wash.

**Approach sketch.**

- Build the lines from the distance field the glow primitive already computes
  (`chamfer_distance` in `src/pyntpot/ink/noise.py:233`, ADR 0070): the distance of each
  water pixel from the shore. A water-line is an iso-contour of that field.
- Spacing and count fall off with distance: the first line close to the shore, each
  next one further out, the gaps growing and the line weight and opacity falling, and
  the series stopping after a theme-set count or distance.
- The contours are traced and drawn as strokes with a brush id, so they take the same
  wobble and generalisation as other lines. Open ends where a river narrows are tapered,
  not cut.
- Theme fields for count, first spacing, growth ratio and brush; default count 0 so no
  pinned image moves.
- The distance field lives in `ink`, the contour tracing and the theme in `maps`, so the
  boundary rule holds.

**Dependencies.** The glow primitive and its distance field (spec 009, [ADR 0070](../decisions/0070-line-effects-and-one-pigment-registry.md)). The brush
registry from the same spec for the line's brush.

**Open questions.**

- One field for all water, or per water body, so two lakes do not line into each other?
- Rivers: lined only once wider than a threshold, or never?
- Does it stop at the map edge or fade before it?
- Cost: one more `chamfer_distance` on the full plane plus tracing; spec 009 research,
  section 3, has the per-plane figures.
