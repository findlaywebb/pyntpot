# Small land-cover patches speckle a card seen at thumbnail size

GitHub issue: [#46](https://github.com/findlaywebb/pyntpot/issues/46)

On the Ambleside hero card (`docs/images/hero.webp`) the woods, meadows and scrub are
painted as many small patches in contrasting greens over the tawny fell. At full size
they read as texture; at thumbnail size (about 400 px wide, as the README and gallery show
it) they read as noise, and the card looks busy. The calmer hero theme
(`examples/themes/ambleside-hero.toml`) softens the palette but cannot remove the patches:
no theme field merges or drops cover polygons below a size.

Found while calming the hero (maintainer review, 2026-10-25). Bringing the hero to 5 of 5
waits on this and on `maps-river-start-pools-into-a-blob.md`.

To show it: paint the hero from `tests/fixtures/ambleside/` in the hero theme and view it
400 px wide.

Possible fix: a cover generalisation field giving a minimum patch area in display pixels,
below which a patch merges into its largest neighbour or is dropped.
