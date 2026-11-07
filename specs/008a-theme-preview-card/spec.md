# 008a — Theme preview card

GitHub issue: [#79](https://github.com/findlaywebb/pyntpot/issues/79) (a preview card for
map styles; note `docs/features/maps-theme-preview-card.md`).

Branch: its own, cut from `main` after feature 008 merges. Decision record: an amendment
to ADR 0032 (one new fixture directory and its box), written as ADR 0070 in this spec's
first slice. Depends on 008: named themes, YAML themes, `Style.named`.

## Problem

A theme is judged on real place cards, and each holds only what its place has: Ambleside
has no coast, Oxford no relief, Skye no dense streets. The interactions a theme gets
wrong (a name on a dark wash, a road over a river, a route doubling back beside a stream,
an island in a lake) are scattered across places or missing, so a theme can look right on
one card and break on another.

## Acceptance criteria

- [ ] A hand-built fixture `tests/fixtures/preview/` holds an Overpass payload, a land
      cover payload, an elevation grid and a track, written by a committed generator
      `tests/fixtures/make_preview.py` (deterministic: running it twice gives identical
      bytes), with a `README.md` saying what each feature tests.
- [ ] Every coordinate lies inside the Lynmouth box (51.19, -3.88, 51.26, -3.80);
      `tests/architecture/test_coordinates.py` has a `preview` entry with that box and a
      budget of 600,000 bytes, and passes.
- [ ] The fixture holds, laid out to meet each other: a coast with sea and an offshore
      island; a lake with an island; a river that splits round a gravel bar and a stream
      joining it; major and minor roads crossing the water and each other; wood, meadow,
      heath, built-up and rock, including patches below `min_patch_px` at 900 px; a hill
      with relief; a route that doubles back beside a road and beside the river; a
      settlement, a named landmark, a journal note and the credit.
- [ ] Every name on it is a real place or feature of the Lynmouth area (Lynmouth, Lynton,
      East Lyn River, West Lyn River, Countisbury, Watersmeet, Foreland Point); features
      with no real name there carry no name tag.
- [ ] `examples/theme_preview.py` takes `--theme` (a name or a `.yaml` path, the 008
      rule) and an output path, paints the card at 600 px from the fixture offline, in
      under 15 seconds on four cores.
- [ ] `tests/golden/test_theme_preview.py` paints every packaged theme and every example
      theme on it (golden-marked), pins each image's mean RGB within 1.5 like
      `test_map_styles.py`, and pins the label names placed.
- [ ] Five docs images `docs/images/preview/<name>.webp` (default, pen-and-ink, sepia,
      bold, winter) are registered and shown on the theme how-to's "Four packaged themes"
      section and the gallery.
- [ ] `docs/features/maps-theme-preview-card.md` is deleted; the PR says `Closes #79`.

## Changelog

```
feat(maps): a theme preview card that holds every feature and the awkward meetings between them
```

## Out of scope

- Painting the preview in `pyntpot` itself (a command): #68, session G.
- A preview per example place theme in the docs: the place cards already show them.
