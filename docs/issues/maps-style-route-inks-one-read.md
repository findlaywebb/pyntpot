# The style holds four named route inks and reads one

The theme's `route_inks` table and `pyntpot.maps.style_groups.RouteInks` hold four
named route inks, each named for something a track records, while `Style.route_ink()`
reads one of them and nothing reads the other three. `RouteInk`'s and `RouteInks`'
docstrings, and the module docstring of `maps/style_groups.py`, describe the group the
same way, one ink per kind of track. pyntpot has no notion of what a track records: a
caller that draws routes in different inks keeps its own table and feeds the colour and
width through `Style.with_route_ink`. The names are left as they are because renaming
the group or its fields moves the pinned `digest()` literal (`DIGEST` in
`tests/unit/maps/test_style.py`) and every theme's `route_inks` tables, which is a change
to the theme format and the style digests and so needs its own ADR. Found while
promoting the route ink (ADR 0027).

To show it: `grep -n '^\[route_inks\.[a-z]*\]' src/pyntpot/maps/themes/default.toml`
prints four tables, and `grep -rn "route_inks\." src --include=*.py` prints the one
field `route_ink()` reads, in `maps/style.py`, and no other.

Possible fix: in a new ADR, reduce the group to the one ink `route_ink()` reads, named
for what it is (the route ink), with the theme's table, the strict-key checks and the
group tests changed to match, and re-pin `DIGEST` once, with G-self proving no pixel
moved; or keep the four inks and name them neutrally if a theme is meant to carry more
than one. Rewrite `style_groups.py`'s docstrings in the same change.
