# The tutorials could run as written and lead on to the rest of the docs

GitHub issue: [#172](https://github.com/findlaywebb/pyntpot/issues/172)

**What exists today.**

- **Painting with Python has no program to type.** Its five pages run a finished script
  with one `uv run` line, then quote pieces of it (24 blocks marked `<!-- from examples/... -->`
  across `curves.md`, `symmetry.md` and `fractals.md`) with the imports, constants and
  helpers left out, so a copied block fails with a `NameError`. `vector-drawing.md` shows
  no Python at all.
- **The order disagrees.** `mkdocs.yml` puts Vector drawing before Pictures; the series
  index lists Pictures first, and `pictures.md` is the only page with a "next" link, which
  points back to Vector drawing.
- **The tutorials lead nowhere else.** None of the nine pages under `docs/tutorials/` links
  a how-to, a reference page or an explanation page. Both "Where next" sections point only
  at other tutorials or at `examples/`.
- **The first map is not the hero.** The README hero and the docs landing image are painted
  by `examples/place_card.py` with the hand-tuned `examples/themes/ambleside-hero.toml` and
  the callouts in `examples/places.toml`. `first-map.md` runs `route_map.py` with the
  default theme and no annotations, gets a visibly weaker card, and never mentions the
  themes, `place_card.py` or callouts.
- **The gallery is not checked.** `tests/architecture/test_docs_images.py` checks the
  registry against the pages, not that `docs/gallery.md` shows every image. Four
  registered images are missing from it today: `reference/glyph-sheet.webp` and the three
  vector-drawing stages `svg-flat`, `svg-washes` and `svg-ink`.
- **A wrong pointer.** The "Where next" of `docs/tutorials/paint-a-watercolour.md` says
  the first map is a route round Keswick; `first-map.md` paints Ambleside.
- **`docs/explanation/performance.md` is a maintainer log**: benchmark files, spec numbers
  and gate timings, filed beside the pages that explain how the painting works.

**What the feature would add.** Each Painting with Python page opens with one short,
complete program the reader types and runs, then builds on it, with a link to the full
script. One order in the nav and the index, and a "Next" line on every page. Each tutorial
ends by pointing at the how-tos, reference and explanation pages it leans on. A last
first-map section that reaches the hero's look. An architecture test that every
non-site registry image appears in the gallery. `performance.md` moved to a maintainer
page out of the explanation section.

**Possible shape.** One docs-only pass, no code change, in the same session as the glossary
work (session A in `specs/005-feature-scoping/sessions.md`). The first-map section is
simpler once themes are named in the package (`maps-named-themes.md`, #77); until then it
passes `--style examples/themes/ambleside.toml`. The runnable programs are shorter once
blank paper and lettering each take one call (`ink-blank-paper-by-size.md`,
`letters-lettering-over-an-image.md`), so they can start as they are and shrink later.

**Related.** `docs-examples-review.md` (#63), `docs-glossary-in-place.md` (#65),
`maps-named-themes.md` (#77), `docs-missing-how-tos.md`.
