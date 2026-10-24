# Write a theme

A theme is a TOML file that holds one style: a table for each style group, which together
say how the map is painted, lettered and composed. This guide copies the default theme,
changes a group and loads the result, then shows four themes that do it differently. It
assumes you have painted a first map from the [tutorial](../tutorials/index.md).

The package ships one theme, and `Style.default()` loads it. Every other look is a file
you write and load yourself. Choosing a theme by name, from Python or from the command
line, is [a feature the package does not have yet](https://github.com/findlaywebb/pyntpot/blob/main/docs/features/maps-named-themes.md).

## Steps

1. Copy the default theme. It lives inside the package, so read it with `importlib.resources`:

    ```python
    from importlib import resources
    from pathlib import Path

    default = resources.files("pyntpot.maps") / "themes" / "default.toml"
    Path("my-theme.toml").write_text(default.read_text())
    ```

    The copy is a full theme: every group is there, because `Style.from_toml` needs every
    group and rejects a key that a group does not have.

2. Change a group. Open `my-theme.toml` and edit the values inside one table. To paint on
    darker, yellower paper, change the paper's colour in the `[paper]` table:

    ```toml
    [paper]
    paper_hex = "#e6cf9f"
    ```

    The route's colour is in the `[route_inks.ride]` table, and the colours of the washes
    are in `[cover.pigments]`. Colours are `#rrggbb` strings.

3. Load it, and paint with it in place of `Style.default()`:

    ```python
    from pathlib import Path

    from pyntpot.maps import Style

    style = Style.from_toml(Path("my-theme.toml"))
    ```

    Pass `style` to `fetch`, `paint`, `letter` and `compose`, as
    [`examples/route_map.py`](https://github.com/findlaywebb/pyntpot/blob/main/examples/route_map.py) does with the default. Plates
    painted in another style are painted again, so a change to the theme is always seen.

## Four example themes

The themes in [`examples/themes/`](https://github.com/findlaywebb/pyntpot/tree/main/examples/themes/) are each a copy of the default
with a few groups changed. [`examples/map_styles.py`](https://github.com/findlaywebb/pyntpot/blob/main/examples/map_styles.py) paints
the Keswick route in one of them. Read the files beside the pictures to see how little
changes between looks.

### Pen and ink

![A route map of Keswick in near-black ink on pale paper, with grey roads and rivers and a black route.](../images/map-styles/pen-and-ink.webp)

Painted by `examples/map_styles.py` with `figure="pen-and-ink"`.

The colour washes are off: `land_cover` is false in `[cover]`, so the land takes one pale
grey tint. The `[brush.brushes]` table picks grey and black ink for the roads and rivers,
`[brush]` thins the rivers, and `[route_inks.ride]` lays the route in black with a cream
casing so that it still stands out.

### Sepia

![A route map of Keswick in faded browns on yellowed, foxed paper with a dark vignette.](../images/map-styles/sepia.webp)

Painted by `examples/map_styles.py` with `figure="sepia"`.

The `[paper]` table yellows the paper and raises the wear, the foxing and the vignette.
Every pigment in `[cover.pigments]` is a faded brown or ochre, and the brush ids in
`[brush.brushes]` ink the rivers and roads in browns.

### Bold

![A route map of Keswick in saturated greens, oranges and blues, with a thick magenta route.](../images/map-styles/bold.webp)

Painted by `examples/map_styles.py` with `figure="bold"`.

The pigments in `[cover.pigments]` are saturated, and `[paper.pigment_transparency]`
makes them denser. `river_mult` widens the rivers, `[nib]` letters larger and heavier, and
`[route_inks.ride]` lays a wide magenta route with a cream casing.

### Winter

![A route map of Keswick in cool greys and blues on pale blue-white paper, with a scarlet route.](../images/map-styles/winter.webp)

Painted by `examples/map_styles.py` with `figure="winter"`.

The paper is a pale blue-white without foxing, the pigments are greys and blues, and the
roads are inked in grey. The route is the one warm colour on the card.

## When it goes wrong

- **`pydantic.ValidationError` with `Field required`, naming a group such as `hand`.** The
  theme lacks a table. Start from a copy of the default theme and keep every table, even
  one you do not change.
- **`Extra inputs are not permitted`, naming a table such as `nibs`.** A table name is
  misspelt, so the real table is also reported missing. Compare it with the default theme.
- **`[paper] has unknown keys ['paper_colour']`.** A key is not one of the group's
  fields. Keys are checked at every level, so a misspelt colour name inside
  `[cover.pigments]` is reported the same way.
- **`Input should be a valid number`, naming a field such as `paper.paper_tooth`.** The
  value has the wrong type. The message names the table and the key.
- **`tomllib.TOMLDecodeError`.** The file is not TOML. The message gives the line and column.
- **`ValueError: invalid literal for int() with base 16` when you paint.** A colour is not
  a `#rrggbb` string. Loading does not check colours, so the error comes from `paint`,
  not from `Style.from_toml`. Colour names such as `"cream"` and short forms such as
  `"#fff"` fail the same way.
- **`ValueError: no such brush 'MAJ9-a'` when you paint.** A brush id in `[brush.brushes]`
  names a row or a colour that the brush sheet lacks. Loading does not check brush ids
  either. Use ids the default theme uses, or ones from the brush sheet.
