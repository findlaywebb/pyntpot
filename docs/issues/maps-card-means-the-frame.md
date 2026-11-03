# Some docstrings in maps still call the picture a card

GitHub issue: [#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD)

Area: maps (docstrings).

`GLOSSARY.md` defines the card as the coordinate frame of one map (a box in card metres
and the display and render pixel grids it maps to), not the picture: the picture is the
map. Feature 006's docstring sweep changes the lines feature 007's spec lists (its C1 to C8
and M1 to M4); other docstrings under `src/pyntpot/maps/` still use card for the
painted picture. Two examples:

- `maps/style_groups.py`, `RouteInk`: "How the route is drawn on the card".
- `maps/style_groups.py`, the `blend` field's comment: "`"normal"` lays the ink over
  the card". The style-fields reference page now says "over the map".

Most "on the card" uses (a point on the card edge, every name on the card) mean the frame
and are right.

Possible fix: read every "card" in `src/` docstrings and comments against the glossary,
and say map where the picture is meant. Identifiers (`CardStyle`, `card_pad_frac`) and
manifest keys do not change.
