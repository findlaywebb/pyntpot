# The how-to guides could cover the common map tasks

GitHub issue: [#173](https://github.com/findlaywebb/pyntpot/issues/173)

**What exists today.** `docs/how-to/` holds eight guides and an index: writing a theme, the
command line, working offline, crediting the data, changing the route ink, lettering your
own landmarks, painting your own shapes and self-hosting the providers. The review of them
(`specs/005-feature-scoping/review/03-how-to.md`, "Missing how-tos") lists 16 tasks a user
plausibly has with no guide. The ones most often wanted:

1. **Change the card's size or resolution.** Needs `model_copy` with `dataclasses.replace`
   on `card.display_px` and `supersample`; `pyntpot map` has no `--size`.
2. **Mark a stretch of the route** (a climb, a stop, a bad section) through
   `Annotations.spans`, by track index, kilometre or seconds. `SpanRequest` is not exported
   from `pyntpot.maps`, so a user cannot build one through the public API.
3. **Pin journal notes to the map.** `JournalNote` is public and the Skye card uses notes,
   but no guide gives the limits (6 notes of 60 characters).
4. **Map a planned route or a track that is not GPX.** `Track(lat=..., lng=...)` already
   takes a list of points; the command-line guide only says to export the recorded track.
5. **Choose names from the candidate export.** `candidate_export`, pick, then
   `Annotations.landmarks`. A landmark placed at coordinates is a `Landmark`, which is not
   exported either.
6. **Add relief or turn it off**: `[basemap] hillshade_mode` and `contour_interval`.
7. **Use another font for the lettering**: `[face] label_face` takes a `.ttf` path.
8. **Handle fetch failures in a script**: `FetchError` and `ProviderBudgetExceededError` are
   exported, but the guides quote them only as command-line output to read.

The other eight: letter a settlement or pick roads, draw your own map from
`vector_layers`, fetch a wider area (`--margin-m`), get another variation through the
seeds, letter a title on your own picture, map many tracks sharing one cache, change a
wash colour in your own painting, and use the plates on disk in another tool.

**What the feature would add.** A guide for each of the eight above, grouped in the how-to
index by task, each with a command-line path first where `pyntpot map` can do it and Python
second.

**Possible shape.** Write the ones that need no library change first (3, 4, 6, 7, 8).
Guides 2 and 5 wait on `SpanRequest` and `Landmark` becoming public
(`maps-public-signature-types.md`). Guide 1 is one line once `pyntpot map`
takes `--size` (`cli-wider-commands.md`, #68), and shorter in Python once a theme can
override one field (`maps-themes-as-overrides.md`, #80). Picking roads per card (as
opposed to `[basemap] pick_roads` in a theme) waits on `Annotations.roads`, which is accepted and then ignored today
(`docs/issues/maps-annotations-roads-ignored.md`).

**Related.** `maps-public-signature-types.md`, `cli-wider-commands.md` (#68),
`maps-themes-as-overrides.md` (#80), `docs-tutorials-lead-on.md`.
