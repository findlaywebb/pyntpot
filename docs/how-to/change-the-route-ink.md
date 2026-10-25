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
   a pink `#c22050`, 5.4 pixels wide.

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
   INFO:pyntpot.maps.pipeline:plates in cache/plates/f0a137ce97afcb43 are current, nothing repainted
   INFO:__main__:wrote out/route_ink.png
   ```

   No plate is painted from the route ink. `paint` reads its width only to space the
   strands of a doubled-back route, and `compose` draws it over the plates.

## Result

![The Ambleside route map card with the route drawn in deep violet, a little heavier than the default pink.](../images/how-to/route-ink.webp)

Painted by `examples/how_to_route_ink.py`, which changes only the route's ink from
`examples/route_map.py`. Run it the same way, with your track, a cache directory, an output
directory and a contact:

```bash
uv run python examples/how_to_route_ink.py route.gpx cache/ out/ https://example.org/your-project
```

Pick a colour that stands apart from the washes under it. A maroon or a violet reads
against the greens and the blue of the water; a blue route would be lost among the rivers.

## Try the treatments and the colours

The colour is one thing the ink holds; the treatment is another. The theme's `[route_inks.ride]`
table sets a `style`, and the route is drawn either as a plain `solid` line or as a `pen`
stroke, tinted from a plate the pen painted. A pen reads as hand-inked, and which brush
it uses decides how: a wet brush lays an even line and a dry one breaks up along its length.

![Twelve small copies of the Ambleside card in three rows of four. The columns are the route in maroon, in the default pink, in indigo and in burnt sienna. The top row draws the route as a plain solid line, the middle row as a wet pen line and the bottom row as a dry pen line that thins and breaks.](../images/how-to/route-ink-grid.webp)

*Painted by `examples/how_to_route_ink.py`, `figure="grid"`, in `examples/themes/ambleside.toml`. The rows are a solid line, a wet pen (brush `MAJ1-e`) and a dry pen (brush `MAJ3-e`). The columns are the maroon `#7b2335`, the default pink `#c22050`, indigo and burnt sienna, the last two from `PAINTERS_PIGMENTS`.*

A `for` loop paints it. The pen's brush is part of what `paint` draws, so the plates are
painted once for each brush, each set in its own directory, and the twelve cells are twelve
`compose` calls over them. The colour changes with `with_route_ink` and the treatment by
replacing the ride ink's `style`:

<!-- from examples/how_to_route_ink.py -->
```python
    for treatment, brush in ROWS:
        row = _row_style(small, treatment, brush)
        plates = paint(basemap, row, key_dir / brush)
        cells.append(
            [
                compose(
                    plates,
                    unlettered,
                    basemap,
                    row.with_route_ink(colour=colour),
                    attribution=False,
                )
                for colour in COLOURS
            ]
        )
```

A dotted route is not in the grid: `compose` draws a `dotted` treatment as a solid line today.

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
