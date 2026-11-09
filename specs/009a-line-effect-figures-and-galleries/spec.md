# 009a: Line effect figures, the galleries, one route colour and pigments that carry their transparency

GitHub issues: [#159](https://github.com/findlaywebb/pyntpot/issues/159),
[#69](https://github.com/findlaywebb/pyntpot/issues/69),
[#70](https://github.com/findlaywebb/pyntpot/issues/70),
[#67](https://github.com/findlaywebb/pyntpot/issues/67),
[#104](https://github.com/findlaywebb/pyntpot/issues/104),
[#105](https://github.com/findlaywebb/pyntpot/issues/105),
[#106](https://github.com/findlaywebb/pyntpot/issues/106).

Branch: `claude/quirky-hypatia-z2pii3-stacked`, stacked on PR 1's branch
`claude/quirky-hypatia-z2pii3` (`specs/009-line-effects-and-registry/`). Decision record:
ADR 0070 rules 17 and 18 and the figures and docs side of rules 8 to 14; a new ADR records
this PR's golden regeneration and the one public name rule 17 needs. Evidence:
`specs/009-line-effects-and-registry/research.md` ("#159: one route colour in one place",
"The labelled grid helper and the galleries"). Breaking: the title carries `!`.

## Problem

PR 1 gives the engine a pigment registry, a `Colour` type, palettes, the casing, glow,
shadow and pen casing primitives and a `line_effects:` theme table, all off and none of
them shown. Three defects and gaps remain. A fed route colour leaves the "start" and
"finish" labels pink, because `with_route_ink` feeds only `route_ink.colour`. A pigment's
transparency still lives apart from it, in `paper.pigment_transparency`. And the docs show
neither every brush id, nor every pigment and how pairs mix, nor what any line effect or
several important settings do.

## Acceptance criteria

### One route colour (#159, ADR 0070 rule 18)

- [ ] `Style.with_route_ink(colour=c)` sets `route_ink.colour` and `nib.label_route_ink`
      to `c` in lower case; with no colour fed, both are the theme's. A fed width alone
      still moves only `digest()`.
- [ ] A Hypothesis property over `#rrggbb` (either case), from `Style()` and every packaged
      theme: every route-coloured resolution equals the fed colour
      (`route_ink.colour` and the nib's resolved `route` ink).
- [ ] A structural test walks every `Colour`-typed field of every style group (ADR 0070
      rule 4). For each field whose default equals `RouteInkStyle().colour`, a fed colour
      sets it.
- [ ] One pixel test: after `with_route_ink(colour=VIOLET)`, `letter` writes a nib plate
      that is not byte-equal to the default's, and the "start" marker label's opaque
      pixels average within 12 of `VIOLET` per channel.
- [ ] A fed colour moves `lettering_digest()`, pinned as a literal; at the default no
      digest moves.
- [ ] `docs/how-to/change-the-route-ink.md` says the markers follow a fed colour, that a
      fed colour overrides a theme's own marker shade, and that the first `letter` after
      a new colour strokes the nib plate again (about 4.5 s).
      `docs/issues/maps-route-ink-leaves-marker-labels-pink.md` is deleted.

### A pigment carries its own transparency (D7, ADR 0070 rule 17)

- [ ] `PaperStyle.pigment_transparency` is gone. A theme that sets
      `paper.pigment_transparency` fails at load, and the located error names
      `cover.pigments.<class>.transparency`.
- [ ] Each `cover.pigments` entry is a pigment reference: a `#rrggbb`, a registry name or
      an alias. It may instead be a table `{pigment: <ref>, transparency: <0 to 1>}`. At
      load the transparency is resolved: the entry's own, else the named pigment's own,
      else, for a bare `#rrggbb`, the transparency of the built-in pigment the role bound
      by default, else `paper.km_transparency`.
- [ ] A bare hex keeps its role's default transparency: a theme that rebinds a role by
      `#rrggbb` and sets no transparency paints with the transparency the role had
      before, not `paper.km_transparency`.
- [ ] A role entry replaces the base theme's binding as a whole. It is never merged key
      by key.
- [ ] Every bundled and example theme is migrated, so that every role keeps the colour
      and transparency it painted with before. Every base plate of every theme is
      byte-identical before and after. The `default`, `pen-and-ink`, `sepia` and
      `winter` map-styles images, the place cards, the hero and the social preview do
      not move.
- [ ] `BASE_DIGEST`, `DIGEST`, every theme's `DIGESTS` entry, `GOLDEN_HASH` and the
      Lynmouth `plates.json` hash are re-pinned to measured literals. `LETTERING_DIGEST`
      does not move. Both copies of `theme.schema.json` are regenerated.

### Galleries (#69, #70)

- [ ] `examples/brush_gallery.py` paints every brush id, one figure per prefix group:
      `riv-str-lan` (24 ids), `maj` (40) and `trk` (48), 112 in all.
      - Rows are the eight treatments, each lettered with its number and kind.
      - Columns are the prefix's ink colour columns.
      - Each cell holds one S-stroke at 4 px and one at 12 px, with the id lettered
        beneath.
      - A docs test fails if an id of `BRUSH_COLOURS` by `BRUSH_TREATMENTS` is missing.
- [ ] `examples/pigment_gallery.py` paints every registry pigment, all on `paper_plate`
      paper, glazed by Kubelka-Munk at each pigment's own transparency.
      - `roles` has 15 rows and `painters` has 10. Each row holds:
        - the name, lettered;
        - washes at strengths 0.3, 0.6 and 0.9;
        - a 0.9 strip across a grey-brown ink bar, so a stain and a veil differ;
        - the transparency and the Colour Index code, lettered.
      - `glazes` shows six painter's pairs as columns. The rows are: multiplied, A glazed
        over B, and B glazed over A.
      - `palettes` shows every bundled palette: a row of its aliases, each swatch
        lettered with the alias and the pigment it names.
      - A docs test fails if a registry pigment or a bundled palette is missing.
- [ ] `docs/reference/brush-gallery.md` and `docs/reference/pigment-gallery.md` show the
      figures. They repeat every lettered value as real text in a table, which a docs
      test checks against the code. Both pages are linked from `brushes.md` and
      `pigments.md` and are in the nav.

### Line effects shown and documented (#104, #105, #106, ADR 0070 rules 8 to 14)

- [ ] Effect parameter sweeps on free strokes, each cell's value lettered, all through the
      `examples/labelled_grid.py` helper of #170:
      - casing width by colour;
      - glow spread by blur;
      - shadow offset by blur;
      - pen casing gap by ink width.
      Each sweep's zero cell equals the plain stroke, byte for byte.
- [ ] On the Ambleside fixture:
      - a how-to result card with `road_major` cased and the route haloed, from a new
        `examples/themes/ambleside-cased.yaml`;
      - a figure of the route under each preset: none, `cased`, `halo` and `lifted`.
- [ ] Two explanation figures:
      - a cream casing and a glow over a dark wood wash, glazed and on RGB;
      - casings drawn per stroke against casings drawn as a group, at a junction and at
        a road crossing a river.
- [ ] Diataxis pages, in British English, with captions of the form "Painted by
      `examples/<stem>.py`":
      - `docs/how-to/case-light-or-shadow-a-line.md`;
      - `docs/reference/line-effects.md`, which lists the classes, the fields with their
        units, the preset expansions, the draw order and which digest each effect moves
        and at what cost;
      - `docs/explanation/line-effects.md`, which explains why an effect works on RGB
        and is not a glaze, and why route effects appear only in `compose`'s output and
        never on the consumer's SVG page.
      A docs test pins the reference tables to the code.
- [ ] A Painting with Python page, `docs/tutorials/painting-with-python/cased-strokes.md`,
      with `examples/cased_stroke.py`. Using only the public `ink` effect primitives on a
      free stroke, it casts a casing, a glow and a shadow.
- [ ] The packaged `bold` theme cases `road_major` with the `cased` preset. Its
      map-styles image and mean are re-pinned. No other bundled theme adopts an effect.

### Setting grids (#67)

- [ ] `examples/setting_grids.py` paints three sweeps:
      - `pool`: the wash's edge pooling;
      - `granulation`: the granulation size;
      - `dryness`: a brush's dryness by its load.
- [ ] `examples/relief_grid.py` paints `cover.relief_strength` at 0.5, 1, 1.5 and 2 on an
      Ambleside crop.
- [ ] Each sweep is shown under the paragraph that describes its setting. Glaze order is
      the pigment gallery's `glazes`. Wash body and nib angle and width are the existing
      tutorial and nib grids.

### Images, budgets, notes

- [ ] Every new image is registered in `tests/support/docs_images.py` under three new
      slices: `009a-galleries` (500,000 B), `009a-line-effects` (600,000 B) and
      `009a-setting-grids` (250,000 B). The directory stays within 7,000,000 B.
- [ ] The goldens are regenerated once, as the last task. The moved pins and images are
      exactly those in `plan.md`'s table, recorded in the new ADR and in the PR body
      with ADR 0052's review images.
- [ ] The notes for #104, #105, #106, #159, #67, #69 and #70 are deleted, along with any
      registry note PR 1 left (#71, #72, #170). Every note that linked to one now points
      at the page that replaced it.
- [ ] The PR says `Closes #159, #69, #70, #67, #104, #105, #106`.

## Changelog

```
feat(maps)!: a cover class binds a pigment that carries its own transparency; paper.pigment_transparency is gone
fix(maps): a fed route colour also letters the start and finish markers
feat(maps): the bold theme cases its main roads
docs(docs): galleries of every brush id and every pigment, with glaze pairs and Colour Index codes
docs(docs): how-to, reference, explanation and a Painting with Python page for casings, glows and shadows
docs(docs): setting grids for wash pooling, granulation, dryness and relief strength
```

## Out of scope

- Bridges from OSM `bridge` and `layer` tags (#209) and water-lining (#210).
- Effects on lettering or leaders (ADR 0070 rule 14).
- Tinting the markers at compose, or `label_route_ink = None` meaning the route's colour
  (rejected by ADR 0070).
- A nib plate cache entry per route colour.
- A command-line route colour option.
- The public `letters` round trip of #165.
- Any change to the effect primitives' maths or to PR 1's five grids.
- Effects in `pen-and-ink`, `sepia` or `winter`.
