# The route ink's style key overloads Style

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

Area: maps (style).

`RouteInk.style` in `maps/style_groups.py` (a theme's `[route_ink] style`) says how the
route is drawn: `"pen"` tints the painted pen plate, any other value (every theme says
`"solid"`) draws the line. `Style` is also the whole map style, and "style group",
"style field" and "route ink style" are all glossary phrases. A reader of
`style.route_ink.style` meets the word twice with two meanings.

Possible fix: rename the key to say what it chooses (for example `mode` or `drawn_as`),
with an ADR, since themes carry it; a theme with the old key would need a clear error or a
read-time alias.
