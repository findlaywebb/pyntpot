# Case, light or shadow a line

Make a line read against what it crosses: a casing round a road, a glow round a river, or a
shadow that falls from a route. Each is a line effect, set in a theme per line class.

![The Ambleside map with its main road cased in the paper's colour, so it stands clear of the wash, and its maroon route lifted off the page by a soft shadow to the south-east.](../images/how-to/line-effects.webp)

*Painted by `examples/how_to_line_effects.py` (figure card, theme `examples/themes/ambleside-cased.yaml`). The main road is cased and the route is lifted, both by name.*

![One brown road crossing farmland and wood, cased in the paper's colour and in Payne's grey at five widths.](../images/how-to/casing-sweep.webp)

*Painted by `examples/line_effect_grids.py` (figure casing). The labels read 0, 1, 2, 3 and 5 across, and paper and paynes_grey down. Each width is in pixels at scale 1.*

**Before you start:** you need a theme file. [Write a theme](write-a-theme.md) shows how to
make one and describes the `line_effects:` key in its "Line effects" section. A width, spread,
blur or offset in a theme is in display pixels, from 0 to 16, so the sweeps below, painted at
scale 1, show what the same number does in a theme at scale 1.

## Case a line

A casing is a ring of one colour round a line. A casing in the paper's colour cuts a road out of
a busy wash; one in a dark pigment outlines it. Casing width 0 draws nothing, and 2 or 3 pixels
reads as a ring without becoming a border. The sweep above shows both colours.

## Lift a line with a glow

A glow lifts the colours round a line toward the paper. It never darkens, and it has no colour of
its own, so it suits a river through dark woodland. A spread sets how far the hard core reaches
and a blur how softly it falls away.

![One river over dark wood, with no glow and then a glow at four spreads and three blurs.](../images/how-to/glow-sweep.webp)

*Painted by `examples/line_effect_grids.py` (figure glow). The labels read 0, 2, 4 and 6 across, and 0, 3 and 6 down. The first column has no glow. The spreads and the blurs are in pixels.*

## Cast a shadow

A shadow darkens the colours beside a line, on the side away from the light, which is the
north-west, so it falls to the south-east. It never darkens the line itself. An offset moves it
away from the line, and a blur softens its edge.

![One crimson line over farmland, with no shadow and then a shadow at four offsets and two blurs.](../images/how-to/shadow-sweep.webp)

*Painted by `examples/line_effect_grids.py` (figure shadow). The labels read 0, 1.5, 3 and 5 across, and 1 and 3 down. The first column has no shadow. The offsets and the blurs are in pixels.*

## Use a preset

You do not have to write the numbers. The package ships three effect presets, `cased`, `halo` and `lifted`, and a line class takes one by name. This is the whole of `examples/themes/ambleside-cased.yaml`, the theme the picture at the top is painted in:

```yaml
extends: ambleside.yaml

line_effects:
  road_major: cased
  route: lifted
```

`road_major` is the main road, which the casing cuts out of the farmland and wood it crosses, and `route` is the route, which the shadow lifts off the page. The four cells below show the route's three presets next to none, all cropped to the same close window on the loop, where the route crosses a river and runs beside a road, and all painted from one set of plates, because a route effect is laid at compose and repaints nothing.

![One close window on the Ambleside loop four times, two across and two down, where the route crosses a river beside a road: the route plain, then with a ring of paper round it, then with a soft pale margin, then with a soft shadow to its south-east.](../images/how-to/line-effects-presets.webp)

*Painted by `examples/how_to_line_effects.py` (figure presets, theme `examples/themes/ambleside.yaml`). The names are none, cased, halo and lifted; each cell but the first reads a theme file that extends `ambleside.yaml` and sets `line_effects: {route: <name>}`.*

A preset suits a line the way its effect does. `cased` separates a road from busy colour, `halo` lifts a river or a route out of dark woodland, and `lifted` sets a route on the page. To use other numbers, write the stack out under the class, or name a preset of your own in `effect_presets:`, both described in [Write a theme](write-a-theme.md). A class on a basemap line repaints the base plates when it changes, and the route does not: see which digest each class moves in [Line effects](../reference/line-effects.md).
