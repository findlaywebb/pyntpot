# The order land cover paints in could be set by the theme

GitHub issue: [#147](https://github.com/findlaywebb/pyntpot/issues/147)

**What exists today.** The order in which land-cover classes paint is a constant,
`COVER_ORDER` in `maps/cover.py`, and `maps/layers.py` reads it directly
(`cover_order=tuple(c for c in COVER_ORDER if c in cover)`). A later class replaces an
earlier one where they overlap, so a plate carries one class per pixel. A theme can
recolour a class (`[cover.cover_cfg]` in `maps/themes/default.toml`, `CoverStyle.cover_cfg`
in `maps/style_groups.py`) but cannot reorder the classes or say which of them share a wash.

**Why it came up.** Oxford. PR #122 (fixes #44) gives education land
(`landuse=education`, `amenity=university`, `amenity=college`) a pigment. Painted as plain
`built` it would sit above the greens and cover the college quads and meadows, which are
the green heart of the card. The maintainer chose "quads on top": education land is its
own `campus` class, painted in `built`'s pigment but below the greens (meadow, grass,
park), so a quad stays green, while ordinary town `built` still paints over greens. That is
one fixed answer; another theme, or another city, may want the other one.

**The mechanism on the experiment branch** (`origin/exp/oxford-quads`, commit 8ce7c0e):

- `src/pyntpot/maps/cover.py:79-81` tags the three education keys `campus`.
- `src/pyntpot/maps/cover.py:91-104` puts `campus` first in `COVER_ORDER`, below `meadow`.
- `src/pyntpot/maps/cover.py:109` declares `PAINTED_AS = {"campus": "built"}`: a class
  labelled at its own place in the order but washed as another, in that class's pigment and
  as one wash with it.
- `src/pyntpot/maps/painter/cover.py:105-120` (`_washed`) turns the order and `PAINTED_AS`
  into the label indices each wash covers; `_class_washes` (line 123) then builds one wash
  per washed class with `np.isin(stack.label, indices)`.

Both the order and `PAINTED_AS` are module constants, so changing either means editing the
package.

**Two levels of ambition.**

1. *A toggle.* One theme option, for example `[cover] campus_under_greens = true`, that
   chooses whether greens paint over campus land (the Oxford answer) or campus land paints
   over greens (the plain town answer). It moves `campus` within the order and nothing else.
   Small, and it settles the case in hand.
2. *A layering system.* A theme declares the paint order of the cover classes, and which
   classes merge into one wash (what `PAINTED_AS` does now), so the order and the merging
   are data, not constants. The package order becomes the default theme's value. This also
   opens cases the toggle cannot reach, such as a heath that sits above woods in a moorland
   theme, or `works` merged into `built` in a calmer palette (related to #46, which asks for
   a way to merge cover classes).

**Open questions.**

- Where the order lives in the theme TOML: a list under `[cover]` (`order = [...]`) beside
  `cover_cfg`, and a table (`painted_as = { campus = "built" }`). Whether a theme may omit
  a class and so drop it, or must name every class.
- Its interaction with `maps/style_groups.py`: `CoverStyle` would gain the fields, and the
  loader would need to validate that every class in `COVER_TAGS` appears exactly once, that
  `painted_as` targets exist, and that no chain loops. `from_toml` currently needs every
  group present, so this also meets #80 (themes as overrides) and #77 (named themes): an
  override theme should be able to change just the order, and a shipped theme should be
  able to carry its own.
- The boundary: `COVER_TAGS` (tag to class) stays in `maps/cover.py`; only order and
  merging move to the theme. `layers.py` and the painter would read them from the style,
  not import the constant.
- How a golden test covers it: a pinned literal for the resolved wash list on a small
  synthetic cover (quad inside campus inside town), once per setting, plus one Oxford-style
  card painted both ways as a golden pair. The default theme's golden must not move when the
  default order is unchanged.
- Whether the order must stay one total order, or whether pairwise rules ("greens over
  campus") are easier for a theme author to read and harder to get inconsistent.

**Why it is not a defect.** With #122 the shipped answer is "quads on top" for every
theme; nothing is wrong, the choice is just not the theme's to make.

**Related.** #44 and PR #122 (education land gets a pigment class); #80 (a theme declares
only what it changes); #77 (themes chosen by name); #46 (cover patches cannot be merged by
a theme).
