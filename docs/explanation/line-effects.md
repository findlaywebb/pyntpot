# Line effects: why they work on colours, not as glazes

A line effect is a casing, a glow or a shadow laid round a line: a road that stands clear of the wash it crosses, a river that lifts out of dark woodland, a route that sits above the page. pyntpot paints everything else as glazes of pigment, so it is fair to ask why these are not glazes too. This page says why they are not, in what order they are drawn, and where they appear. For how to set one, see [Case, light or shadow a line](../how-to/case-light-or-shadow-a-line.md); for every field and value, see [Line effects](../reference/line-effects.md).

## Why a line effect is not a glaze

A wash is a pigment laid as a glaze. Glazing, or multiplying, can only keep a colour as it is or darken it, because a layer of pigment lets some light through and stops the rest. That is exactly right for a wash over a wash. It cannot make a casing. A casing in the paper's colour has to lay cream over a dark wood, and a glaze at the default transparency lets the wood show through almost whole. Multiplying cannot lighten at all, so it cannot make a glow either.

So an effect does not glaze. It is a plain function of the colours beneath it: `casing(rgb, mask, effect, *, threshold, paper)` takes the picture so far, the line's mask and a `Casing`, and blends a ring round the line toward the casing's colour as it would look laid over the paper. `glow(rgb, mask, effect, *, threshold, paper)` lifts the colours round the line toward the paper, and never darkens them. `shadow(rgb, mask, effect, *, azimuth_deg, threshold)` darkens beside the line, away from the light. Each knows nothing of maps: it takes an array, a mask and its own small value type.

![A two by two grid over one dark green wood wash. The top row lays a pale cream ring round a brown road and round a blue-green river as a glaze, and the rings barely show. The bottom row lays the same rings as RGB: a clear pale casing round the road and a soft pale glow round the river.](../images/explanation/line-effects-glaze-or-rgb.webp)

*Painted by `examples/line_effect_reasons.py` (figure glaze-or-rgb). The labels read casing and glow across, and glaze and RGB down. Each cell is the same wash and the same stroke; the top row lays the effect's ring as a cream glaze and the bottom row lays it through the `casing` and `glow` primitives.*

The departure is limited to effects. Lines and washes still glaze, and an effect is laid before the line it belongs to, so the line is still glazed over it.

### Why the line's own pixels are left alone

A casing and a glow change only the pixels outside the line: where the mask is at or above the threshold, they leave the colour as it was. This is on purpose. A line is a translucent stroke, so a casing laid under it would show through it and tint it, and a glow would wash it out. Leaving the line's own pixels untouched means the stroke keeps its colour, whatever the effect and whatever the width. A shadow likewise never darkens the line that casts it.

## Casings first: the draw order

Where two lines meet, the order the casings and the lines go down in matters. Case each road and draw it in turn, and the second road's casing is laid over the first road's line, so a pale seam cuts across the first road at the fork. Lay every casing first and then every line, and the casings all lie under all the lines: the fork reads as one road, and a road over a river reads as a crossing.

![Two cells, each a river crossed by two roads that fork. On the left, each road is cased and drawn in turn, and a pale seam cuts across the first road where the second joins it. On the right, both casings are laid first and then both roads, and the fork is one road with no seam.](../images/explanation/line-effects-draw-order.webp)

*Painted by `examples/line_effect_reasons.py` (figure draw-order). The labels read each stroke cased and casings first. Both cells lay the river first and plain; only the order of the two roads' casings differs.*

The painter follows the second order. It draws the water group, then the road group, and within a group lays the effects of every class on what lies beneath it before it lays the group's lines. The full order, class by class, is in [Line effects](../reference/line-effects.md).

## Where a route's effects appear

A basemap line's effects are laid when the base plates are painted, so changing one paints the plates again. The route's effects are laid when `compose` draws the route, above the whole base plate, from the route's mask. So a route effect repaints nothing: it costs one compose. It also means a route effect exists only in the pixels `compose` returns.

A page that draws the route itself, as an SVG laid over the card, does not get the route's effects. The SVG is not in those pixels, and `compose` never sees it. If you want a casing round a route you draw yourself, case it where you draw it, as [Cased strokes](../tutorials/painting-with-python/cased-strokes.md) does for a free stroke.

## What line effects do not do

They are not laid on lettering or its leaders, so no effect moves the lettering digest. A glow has no colour of its own. A pen casing has no theme key: it is an `ink` primitive for a picture painted in Python. Pigment separation keeps its own transparency and is not an effect.
