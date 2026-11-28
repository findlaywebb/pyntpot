# 010a — Lettering over an image in one call, and the basemap's key

Revision 2 (after `review-plan.md`): the premultiply claim is limited to a resize that
changes the size; `nib_plate` writes `nib_rgba`'s arrays exactly only with `plate_lossless`
on; the round-trip check bans `nib_plate` and `Image.open` in the attribution; the `fix`
line has a test; ADR 0073 skips 0072, which spec 008a holds.

GitHub issues: [#165](https://github.com/findlaywebb/pyntpot/issues/165) (lettering over an
image in one call) and [#167](https://github.com/findlaywebb/pyntpot/issues/167) (fetch
hands back what paint needs). This PR closes both.

Decision record: ADR 0073 (`docs/decisions/0073-boilerplate-free-calls.md`), rules 5 to
11, written and accepted in `specs/010-blank-paper-and-keyword-arguments/` (PR 1 of E-a).
This PR stacks on 010: `letter_over` builds its plate with `Canvas.pixels` and a keyword
`Sheet`.

## Problem

**Lettering over an image (#165).** `nib_plate(marks, surface, groups, path)` only writes a
file. To letter a painted array, a caller builds a `Canvas` and a zero darkness array at
twice the size and a `NibSurface`, builds `NibGroups` from five style objects (it has no
defaults), writes the plate, reopens it with Pillow, shrinks it with Lanczos, divides by
255 and blends. Measured on `f6c8302`: `examples/` holds nine copies of that round trip
(`composition`, `derwentwater`, `glyph_sheet`, `how_to_own_shapes`, `labelled_grid`,
`lettering`, `nib_stages`, `social_preview`, `word`), the private
`labelled_grid.letter_over` serving the grid and gallery scripts, and `NIB_SCALE = 2` is
defined in 12 scripts. The library does it too: `maps/attribution.py` writes the
attribution plate into a temporary directory and reopens it. (The note's 14 copies in 13
scripts were counted before spec 009 folded five grid scripts into `labelled_grid.py`. Its
"drift" between scripts that convert through `"RGBa"` and those that do not is no drift in
pixels: Pillow premultiplies an RGBA image inside a `resize` that changes the size, so
at the examples' 2x shrink the two give the same pixels, measured. At the same size Pillow
copies without premultiplying, which is why the shared shrink premultiplies explicitly.)

**The basemap's key (#167).** `fetch` gets the cache key from `cache.ensure` and drops it,
so every caller rebuilds it, passing the providers a second time:
`paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))`. Measured:
8 sites in 6 example scripts (`route_map`, `place_card`, `map_styles`, `relief_grid`,
`how_to_route_ink` twice, `how_to_line_effects` twice), 3 docs pages, the command line and
`tests/support/golden.py`. `candidate_export(track, cache, key)` and
`vector_layers(track, cache, key, style)` take the same key.

## Acceptance criteria

### The in-memory nib plate and `letter_over` (#165)

- [ ] `pyntpot.letters` exports `nib_rgba(marks, surface, groups)`, returning the nib
      plate's straight colour `(h, w, 3)` and alpha `(h, w)`, floats in 0 to 1 at the
      surface's size (float32 for a float32 darkness, measured), uncast, exactly as
      `nib_plate` composes them, or `None` when there is nothing to draw (no marks, or no mark of two
      points). With `plate_lossless` on (the default), `nib_plate` writes exactly these
      arrays: the file it writes decodes to the 8-bit form of `nib_rgba`'s alpha
      everywhere and of its colour wherever the alpha is above 0. With it off, the colour
      is written lossy, as today.
- [ ] `pyntpot.letters` exports `letter_over(image, marks, groups=None, *, gran_px,
      scale=2, dark=None)`, which returns `image` with the marks lettered on it (ADR 0073
      rule 6), as a new array, leaving `image` unchanged:
  - for a painted image and marks, it equals bit for bit the round trip the examples
    write today (a surface of `scale` times the size, `nib_plate` to a file, Pillow
    Lanczos to the image size, `/ 255`, `image * (1 - a) + colour * a`), with a zero
    darkness and with a darkness ramp brought up bilinearly as `labelled_grid.py` does;
  - `groups=None` gives the same result as `NibGroups()`;
  - with nothing to draw it returns an array equal to `image`, not `image` itself;
  - a pixel far from every mark (where the shrunk alpha is 0) is exactly the image's,
    at `scale=2` and at `scale=1` (a shrink to the same size);
  - an `image` that is not `(h, w, 3)`, a `dark` that is not `(h, w)`, or a `scale`
    under 1 raises `ValueError`.
- [ ] `NibGroups()` equals `NibGroups(NibStyle(), FaceStyle(), HandStyle(), BrushStyle(),
      PaperStyle())`, `NibGroups(nib=n)` keeps the other four at their defaults, and
      positional construction still works.
- [ ] `maps/attribution.py` strokes the attribution with `nib_rgba` and writes no file:
      it calls neither `nib_plate` nor `Image.open` and imports no `tempfile`, and no
      module in `letters` imports `tempfile` (architecture test). The shrink both use
      lives once, in `ink` (private), shared with `save_rgba`'s 8-bit conversion. It
      premultiplies explicitly, so a shrink to the same size, as the attribution makes on
      a card supersampled 2x or more, is bit-identical to today (a pinned test).
- [ ] A style whose `paper.plate_lossless` is off draws the same attribution bytes as
      the default style (the `fix` line; `tests/unit/maps/test_attribution.py`).

### The basemap's key (#167)

- [ ] `Basemap` has a required keyword-only field `key`, last, documented in
      `Attributes:`: `fetch(track, cache, features, elevation, style).key ==
      cache.key(track, features, elevation)`. A `Basemap` built without `key` raises
      `TypeError`. `basemap.canonical()`, and so `Cache.base_key` and every plate hash, does
      not read it: two basemaps that differ only in `key` have the same canonical text.
- [ ] The command line and `tests/support/golden.py` paint into
      `cache.plates_dir(basemap.key)` and no longer call `cache.key`. `fetch`'s,
      `paint`'s, `candidate_export`'s and `vector_layers`' signatures are unchanged.
- [ ] `basemap.py`'s module docstring states the new invariant (it carries the key the
      cache gave it and computes none) in place of "It carries no cache key".

### Pixels do not move

- [ ] The output hashes of all 91 registered docs image entries
      (`tests/golden/output_hashes.py check`, recorded on this branch's base, which is 010
      merged) are unchanged, the map cards with their attribution among them.
- [ ] The golden suite passes with no regeneration; nothing under `docs/images/`,
      `tests/golden/docs/` or `tests/golden/lynmouth/` changes, and no pinned literal moves.

### Records

- [ ] `docs/reference/letters.md` gains `::: pyntpot.letters.letter_over` and
      `::: pyntpot.letters.nib_rgba`; `tests/unit/test_public_api.py` pins the two names;
      the `letters` package docstring names them.
- [ ] `GLOSSARY.md`'s "nib plate" row names `pyntpot.letters.nib_rgba` and
      `pyntpot.letters.letter_over` in its code column, and its "basemap" row says it
      carries its cache key; the glossary is regenerated.
- [ ] `docs/features/letters-lettering-over-an-image.md` and
      `docs/features/maps-fetch-hands-back-the-plates-dir.md` are deleted and their links
      repointed; the sweep of their copies (the nine round trips, the 8 key lines and the
      docs pages) is added to `docs/features/docs-examples-review.md` (#63) under 010b.
      The PR body says `Closes #165` and `Closes #167`.
- [ ] Mutation testing has run on the changed `ink` and `letters` functions (`plan.md`,
      S6); each survivor is killed or named as equivalent (`mutation.md`, PR description).
- [ ] No file under `src/` is over 400 lines; no mocking; logging only. Gates green:
      `uv run pytest -n auto --dist loadgroup`, `uv run ruff check .`, `uv run ty check`,
      `uv run lint-imports`, `prek run --all-files`, and the golden suite.

## Changelog

PR title (no `!`: the two new calls and the `NibGroups` defaults are additive; the one
breaking line, for a `Basemap` built by hand, is under Changelog):

```
feat(letters): letter over an image in one call, with an in-memory nib plate
```

Under "Changelog" in the PR description:

```
feat(letters): nib_rgba, the nib plate's colour and alpha as arrays, which nib_plate writes
feat(letters): NibGroups defaults every group to the default look
feat(maps)!: Basemap carries its cache key (Basemap.key), so paint, candidate_export and vector_layers take basemap.key; a Basemap built by hand passes key=
fix(maps): the attribution is lettered in memory, so a style with lossy plates no longer passes it through a lossy file
```

## Out of scope

- **The sweep (010b, scoping group E-b):** the nine nib round trips and
  `labelled_grid.letter_over` onto `pyntpot.letters.letter_over`; the 8 key lines in 6
  example scripts and the docs pages `docs/tutorials/first-map.md`,
  `docs/how-to/change-the-route-ink.md`, `docs/how-to/self-host-providers.md` and
  `docs/how-to/work-offline-and-reuse-the-cache.md` onto `basemap.key`; the tutorial
  (`paint-a-watercolour.md`) and `docs/how-to/paint-your-own-shapes.md` teaching
  `letter_over`; `tests/examples/test_letters_examples.py`'s pin on `<stem>-plate.webp`,
  which the sweep retires; 010's `Canvas.pixels` and `display_px` sweep; N11 (#174).
  Sizing: this PR is the design-heavy half of E-a (a new `letters` call with a
  bit-identity argument, a module split, a record field); the sweep is about 25 files of
  deletions and tutorial prose, a review on its own, and moves no pixel, so splitting it
  costs no extra regeneration.
- `NibSurface`'s shape (its `dark` gets no default): `letter_over` builds the surface for
  the common case, so the positional reorder a default would force buys nothing.
- A float resize of the nib plate (ADR 0073 rule 8).
- Lettering `Setting`s directly (`letter_over` takes marks; a caller writes them with its
  own `Hand` and seed).
- A `Fetched` value, and a one-call `render` for the CLI and the examples (#68).
- The lettering stage's own nib plate in the fetch cache (`maps/lettering/pipeline.py`
  still writes it with `nib_plate`).
