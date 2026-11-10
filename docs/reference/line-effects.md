# Line effects

Every line class a theme can give a line effect to, the fields of each effect with their units, what the three effect presets expand to, the order the effects are drawn in, and which digest each moves. A line effect is a casing, a glow or a shadow laid round a line. For how to set one, see [Case, light or shadow a line](../how-to/case-light-or-shadow-a-line.md).

## Line classes

A theme gives an effect stack, or the name of an effect preset, to each of eight classes under the top-level `line_effects:` key. The seven basemap classes are read by the painter; `route` is read at compose.

| Class | Table | Group | Digests it moves | A change costs |
| --- | --- | --- | --- | --- |
| `major` | `basemap.line_effects` | water | `base_digest` and `digest` | the base plates are painted again |
| `medium` | `basemap.line_effects` | water | `base_digest` and `digest` | the base plates are painted again |
| `minor` | `basemap.line_effects` | water | `base_digest` and `digest` | the base plates are painted again |
| `coast` | `basemap.line_effects` | water | `base_digest` and `digest` | the base plates are painted again |
| `road_major` | `basemap.line_effects` | road | `base_digest` and `digest` | the base plates are painted again |
| `lane` | `basemap.line_effects` | road | `base_digest` and `digest` | the base plates are painted again |
| `track` | `basemap.line_effects` | road | `base_digest` and `digest` | the base plates are painted again |
| `route` | `route_ink.effects` | route | `digest` only | one compose, with no plate painted again |

Painting the base plates again took about 22 s for Lynmouth and 59 s for Skye when the effects were measured; one compose is about 0.3 s. `lettering_digest` never moves: no effect is laid on lettering or its leaders. The two tables are set only through `line_effects:`; a theme that names `basemap.line_effects` or `route_ink.effects` directly gets a located error.

## Effect fields

A theme's `_px` values are in display pixels and are scaled to the array the effect is laid on, so a width of 2 is 2 pixels at scale 1 and 4 at scale 2. A theme refuses a `_px` outside 0 to 16 and a `strength` outside 0 to 1; nothing is clipped. A stack holds at most one casing, one glow and one shadow, and a casing and a reserve are not both: each lays a ring.

| Effect | Field | Unit | Range | Default |
| --- | --- | --- | --- | --- |
| casing | `width_px` | pixels beyond the line | 0 to 16 | `0.0` |
| casing | `colour` | colour, laid over the paper | | `#ffffff` |
| casing | `strength` | blend toward the colour | 0 to 1 | `1.0` |
| glow | `spread_px` | pixels the hard core reaches | 0 to 16 | `0.0` |
| glow | `blur_px` | pixels of soft fall | 0 to 16 | `0.0` |
| glow | `strength` | lift toward the paper | 0 to 1 | `0.0` |
| shadow | `offset_px` | pixels the shadow falls | 0 to 16 | `0.0` |
| shadow | `blur_px` | pixels of soft edge | 0 to 16 | `0.0` |
| shadow | `strength` | darkness of the shadow | 0 to 1 | `0.0` |
| shadow | `colour` | colour the shadow multiplies toward | | `#3b4452` |
| reserve | `width_px` | pixels of paper laid back beyond the line | 0 to 16 | `0.0` |
| reserve | `pool` | how far pigment gathers just outside the ring | 0 to 1 | `0.0` |
| pen casing | `width_px` | pixels of bare paper beyond the line | 0 to 16 | `0.0` |
| pen casing | `edge_px` | pixels each ink edge line is wide | 0 to 16 | `0.0` |

An effect is off at a strength of 0, and a casing or a reserve also at a width of 0; a stack drops its off effects, so a stack written all off is an empty one and moves no digest. The shadow's light is the hillshade's, from the north-west (315 degrees), so a shadow falls to the south-east; it is not a field. The default shadow colour is Payne's grey. A casing's white is the paper: it is laid in wash space, so on the card it is the paper's cream.

A reserve is the paper itself laid back in a ring, every pigment under the ring lifted, where a casing is a colour laid over the wash. It has no colour and no strength. Its `pool` darkens only the pixels just outside the ring, never bare paper, and 0 leaves none. A reserve is set under a line class with `reserve:`, for example `reserve: {width_px: 2, pool: 0.3}`.

A ring is measured from the line's edge, a sub-pixel distance from the contour at the threshold, and its edge is anti-aliased on that distance, so a ring a pixel or two wide has no stair steps.

A pen casing has no theme key. It is an `ink` primitive for a pen-and-ink picture painted in Python: a reserve of bare paper between two ink lines, with the wash beneath it lifted to the paper. Pigment separation keeps its own transparency and is not an effect.

## Preset expansions

The package ships three effect presets. A line class takes one by name, and a theme preset of your own may not reuse these names.

| Preset | Effect | Values |
| --- | --- | --- |
| `cased` | casing | `width_px` 1.8, `strength` 0.9 |
| `halo` | glow | `spread_px` 1.5, `blur_px` 3.0, `strength` 0.85 |
| `lifted` | shadow | `offset_px` 2.5, `blur_px` 2.0, `strength` 0.45 |

A `cased` casing keeps the default colour, the paper's. A `lifted` shadow keeps Payne's grey.

## Casing unions

`casing_unions:` is a top-level theme key: a list of lists of basemap line classes. Each inner list is a union, whose rings are laid as one, so where two classes meet there is one band and no ring shows through a line. It is set in [Case, light or shadow a line](../how-to/case-light-or-shadow-a-line.md).

| Rule | What it means |
| --- | --- |
| Same group only | The members are all water classes or all road classes. |
| Members keep their width | Each member's ring is its own `width_px`; the union is the ring of the widest at each pixel. |
| Share colour and strength | Casings in one union have one `colour` and one `strength`; reserves have one `pool`. |
| One kind | A union is all casings or all reserves. |
| The route never joins | The route is cased at compose from its own mask. |
| Replaced whole | A child's list replaces its parent's, and `[]` turns an inherited set off. |
| Normalised | Members are put in class order and unions by their first member, so themes that paint one picture share a digest. |

A theme is refused, with a located error, for each of these:

| Error | Raised when |
| --- | --- |
| `is a list of lists of line classes` | `casing_unions` is no list, or a union is no list of names. |
| `names no class` | A union is empty. |
| `is not a basemap line class` | A member is no basemap class; the nearest name is offered. |
| `the route is cased at compose from its own mask and joins no union` | A union names `route`. |
| `is already in casing_unions.` | A class is in two unions, or twice in one. |
| `mixes water` | A union holds both water and road classes. |
| `has no casing or reserve` | A member has no casing or reserve in its stack, including after a child turns its stack off. |
| `a union takes one colour and strength` | Casings in a union differ in colour or strength. |
| `a union is all casings or all reserves, with one pool` | A union mixes casings and reserves, or its reserves differ in pool. |

## Draw order

1. The water group: the rings of `major`, `medium`, `minor` and `coast`, in that order, and their other effects, are laid on what lies beneath the group, then the group's lines are laid over them.
2. The road group: the rings of `road_major`, `lane` and `track`, in that order, and their other effects, are laid on what lies beneath the group, then the group's lines are laid over them.
3. The route, at compose, above the whole base plate: the stack's effects in the stack's order, then the route.

A casing union lays one ring round all its members' masks together, in the stack of its first member in class order that has a mask; the other members' ring steps are skipped. A union ring is never laid inside any member's footprint. Glows and shadows stay per class.

Within a group every casing and every reserve lies under every line, so two roads that meet read as one road, and a road that crosses a river reads as a crossing. Within a stack the effects are laid in the stack's order, each on the result of the one before.

## The primitives

The effects are five functions in `pyntpot.ink`, each taking its value type whole. A pixel whose mask is at or above `threshold` is the line. `LINE_THRESHOLD` is 0.3 and is not exported.

- `casing(rgb, mask, effect, *, threshold=LINE_THRESHOLD, paper=None)` returns the colour with a ring laid round the line.
- `glow(rgb, mask, effect, *, threshold=LINE_THRESHOLD, paper=None)` returns the colour lifted toward the paper round the line.
- `shadow(rgb, mask, effect, *, azimuth_deg, threshold=LINE_THRESHOLD)` returns the colour darkened beside the line, away from the light.
- `reserve(rgb, mask, effect, *, threshold=LINE_THRESHOLD, paper=None)` returns the colour with the paper laid back in a ring round the line, every pigment under the ring lifted, and the pool laid just outside it.
- `pen_casing(rgb, mask, effect, *, threshold=LINE_THRESHOLD, paper=None)` returns `tuple[np.ndarray, np.ndarray]`: the wash knocked back to the paper, and the density of the two edge lines.

The ring of a casing, a reserve and a pen casing is measured from the line's contour and anti-aliased on that distance. A casing union is not exported: a picture painted in Python gets the same result from `casing` by passing it the larger of the two densities.

Casing, glow and reserve leave every pixel at or above the threshold as it was, and a shadow never darkens the line that casts it. A glow never darkens.
