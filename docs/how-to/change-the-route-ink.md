# Change the route ink

Change the route's colour or width and leave the rest of the map as it is.
`Style.with_route_ink` returns a copy of a style with a new route ink, so you do not need
a whole theme.

**Before you start:** you need a script that calls `fetch`, `paint`, `letter` and
`compose`, such as `examples/route_map.py` from the [First map](../tutorials/first-map.md)
tutorial. The command line has no route-ink option, so use a script or a
[theme](write-a-theme.md).

## Steps

1. Build the style as before, then ask it for a copy with your ink. The colour is `#`
   and six hexadecimal digits. The width is in display pixels:

   ```python
   style = Style.default().with_route_ink(colour="#6a2c91", width_px=6.5)
   ```

   Leave out either argument to keep the theme's value. The default theme's route is
   pink, `#c22050`, 5.4 pixels wide.

2. Pass that `style` to every stage, where the script passed `Style.default()`:

   ```python
   basemap = fetch(route, cache, features, elevation, style)
   plates = paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))
   lettering = letter(plates, basemap, None, style)
   card = compose(plates, lettering, basemap, style)
   ```

   `Style` is frozen, so `with_route_ink` does not change the style you call it on. The
   stages need the new one it returns.

3. Run the script. If you had already painted the card in the old ink, the plates in the
   cache are still current. `paint` logs that it repainted nothing, and the run takes
   seconds:

   ```text
   INFO:pyntpot.maps.pipeline:plates in cache/plates/f0a137ce97afcb43 are current, nothing repainted
   INFO:__main__:wrote out/route_ink.png
   ```

   No plate is painted from the route ink. `paint` reads the width only to space the
   strands of a route that doubles back, and `compose` draws the route over the plates.

## Result

![The Ambleside route map card with the route drawn in deep violet, a little heavier than the default pink.](../images/how-to/route-ink.webp)

Painted by `examples/how_to_route_ink.py`, which is `examples/route_map.py` with only the
route's ink changed. Run it with your track, a cache directory, an output directory and a
contact:

```bash
uv run python examples/how_to_route_ink.py route.gpx cache/ out/ https://example.org/your-project
```

Pick a colour that stands apart from the washes under it. Maroon and violet show up against
the greens and the blue water. A blue route would be lost among the rivers.

## Try the treatments and the colours

The ink also has a treatment. The theme's `[route_inks.ride]` table sets a `style`. The
route is drawn either as a plain `solid` line or as a `pen` stroke, tinted from a plate
the pen painted. The pen's brush changes the line: a wet brush lays a heavy, even line,
and a dry one lays a thinner, paler line.

![Six small copies of the Ambleside card, each cropped to the loop, in two rows of three. The columns are the route in maroon, indigo and burnt sienna. The top row is a wet pen line, heavy and even. The bottom row is a dry pen line, thinner and paler, and it fades in places. Rows and columns are lettered.](../images/how-to/route-ink-grid.webp)

*Painted by `examples/how_to_route_ink.py`, `figure="grid"`, in `examples/themes/ambleside.toml`. The rows are a wet pen (brush `MAJ1-e`) and a dry pen (brush `MAJ3-e`). The columns are the maroon `#7b2335`, indigo and burnt sienna, the last two from `PAINTERS_PIGMENTS`.*

A few `ribbon` fields crop each cell to the loop. The route uses the theme's `normal` blend.
A `multiply` route would darken over a river until every colour read as black. A `for` loop
paints the grid. The pen's brush is part of what `paint` draws, so the plates are painted
once for each brush, each in its own directory. The six cells are six `compose` calls over
them, and `with_route_ink` sets the colour:

<!-- from examples/how_to_route_ink.py -->
```python
    for _, brush in ROWS:
        row = _row_style(small, brush)
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
                for _, colour in COLOURS
            ]
        )
```

There is no dotted route in the grid. `compose` draws a `dotted` treatment as a solid line.

## When it goes wrong

- `ValueError: route colour 'red' is not a # and six hexadecimal digits`: `with_route_ink`
  takes `#rrggbb` only. It refuses colour names and the short `#abc` form. Upper-case
  digits are fine, and are stored in lower case.
- `ValueError: route width 0 px is not a finite number above zero`: The width must be above
  zero, and not infinite or `nan`. A `bool` is refused too.
- The route did not change colour: you passed the original `Style.default()` to a stage
  instead of the copy `with_route_ink` returned. Pass the copy to every stage.
- The width changed nothing you can see: the route ink is a `pen` treatment. It tints the
  painted pen plate, and that plate's stroke width is the `route` group's
  `route_pen_width_px`. The width you pass then only sets how far apart the strands of a
  route that doubles back are drawn. The default theme's route is `solid`, so there the
  width is the line's width.
- The picture repainted everything: you changed something besides the ink, such as a group
  of your theme. Only a change to the route ink leaves the plates current.
