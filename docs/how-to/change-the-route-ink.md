# Change the route ink

You want the route on your map in another colour or width, and nothing else changed. You
do not need a whole theme for that: `Style.with_route_ink` hands you a copy of a style with
the route's ink replaced.

You need the tutorial's first map behind you ([First map](../tutorials/first-map.md)) and a
script that paints a card with `fetch`, `paint`, `letter` and `compose`, such as
`examples/route_map.py`. The command line has no option for the route ink; set it from a
script, or in a theme ([Write a theme](write-a-theme.md)).

## Steps

1. Build the style as before, then ask it for a copy with your ink. The colour is `#`
   followed by six hexadecimal digits, and the width is in display pixels:

   ```python
   style = Style.default().with_route_ink(colour="#6a2c91", width_px=6.5)
   ```

   Either argument may be left out to keep the theme's value. The default theme's route is
   a crimson `#c22050`, 5.4 pixels wide.

2. Pass that one `style` to every stage, where the script passed `Style.default()`:

   ```python
   basemap = fetch(route, cache, features, elevation, style)
   plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
   lettering = letter(plates, basemap, None, style)
   card = compose(plates, lettering, basemap, style)
   ```

   `Style` is frozen, so `with_route_ink` never changes the style you call it on. It returns
   a new one, and the stages must be given that one.

3. Run the script. If you had already painted the card in the old ink, the paper, the
   washes, the pen plates and the label plate are still current in the cache, so
   `paint` logs that it repainted nothing and the run takes seconds:

   ```text
   plates in cache/plates/f2f4692b66d96eb9 are current, nothing repainted
   wrote out/route_ink.png
   ```

   The route ink is not part of what the plates are painted from. Only `compose` reads
   it, when it draws the route over them.

## Result

![The Keswick route map card with the route drawn in deep violet, a little heavier than the default crimson.](../images/how-to/route-ink.webp)

Painted by `examples/how_to_route_ink.py`, which changes only the route's ink from
`examples/route_map.py`. Run it the same way, with your track, a cache directory, an output
directory and a contact:

```bash
uv run python examples/how_to_route_ink.py route.gpx cache/ out/ https://example.org/your-project
```

Pick a colour that stands apart from the washes under it. A crimson or a violet reads
against the greens and the blue of the water; a blue route would be lost among the rivers.

## When it goes wrong

- `ValueError: route colour 'red' is not a # and six hexadecimal digits`: `with_route_ink`
  takes `#rrggbb` only. Colour names and the short `#abc` form are refused. Upper-case
  digits are fine; they are stored in lower case.
- `ValueError: route width 0 px is not a finite number above zero`: The width must be a
  number above zero that is not infinite and not `nan`. A `bool` is refused too.
- The route did not change colour: you passed the original `Style.default()` to `compose`
  and not the copy `with_route_ink` returned. Name the copy and pass it to every stage.
- The width changed nothing you can see: the style's route ink is a `pen` treatment, which
  tints the painted pen plate, and that plate's stroke width is the `route` group's
  `route_pen_width_px`. The width you feed then only sets how far apart the strands of a
  doubled-back route are drawn. The default theme's route is `solid`, so its width is the
  line's width.
- The picture repainted everything: you changed something besides the ink, such as a group
  of your theme. Only the route ink leaves the plates current.
