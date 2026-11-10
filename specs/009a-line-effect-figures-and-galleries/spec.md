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
      that is not byte-equal to the default's. On that plate's RGBA, the pixels with alpha
      at least 0.9 inside the box of the "start" marker label (from `Lettering.labels`)
      have a mean RGB nearer `VIOLET` than `#c22050` by Euclidean distance.
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
- [ ] `CoverStyle.pigments` maps each cover class to a `pyntpot.maps.CoverPigment`, a
      `NamedTuple` of a `Colour` and a transparency (a float, or `None`).
- [ ] Each `cover.pigments` entry is a pigment reference: a `#rrggbb`, a registry name or
      an alias. It may instead be a table `{pigment: <ref>, transparency: <0 to 1>}`. At
      load one rule resolves the transparency of every form: the entry's own, else the
      resolved pigment's own (a derived `{base: x}` pigment that sets none takes its
      base's; an alias resolves to the `Pigment` it binds, a hex alias to a pigment-less
      one), else the transparency of the cover class's built-in pigment. So a bare
      hex, an alias to a hex (a `.gpl` palette alias included), `{pigment: "#rrggbb"}`
      with no transparency and a theme pigment with none all take the cover class's
      built-in transparency, and a test covers each form. A theme or palette alias
      resolves as PR 1's `resolve_pigment` resolves it.
- [ ] A `CoverPigment` has one written form: a ref, or `{pigment: "#rrggbb",
      transparency: t}`, never a list. The theme dump, the schema `default`, the
      `style-fields.md` Default cells and the checker all use it.
- [ ] An error in the table form is located at its own key and line:
      `cover.pigments.<class>.pigment`, `.transparency`, or an unknown inner key with
      the nearest of `pigment` and `transparency` suggested. `transparency` is a number
      from 0 to 1; a `bool` or a string is refused.
- [ ] `paper.km_transparency` applies only to a `CoverPigment(colour, None)` built in
      Python, or a Python-built key outside the 15 cover classes (whose built-in
      transparency is `None`); no theme can produce either. A `str` value built in Python
      takes the cover class's built-in transparency, as a theme's bare hex does.
- [ ] A cover class's entry replaces the base theme's whole. It is never merged key by
      key, so an `extends` child that rebinds a class by bare hex takes the class's
      built-in transparency, not its parent's. A test pins this, and the theme how-to and
      ADR 0070 rule 17 say it.
- [ ] Every bundled and example theme is migrated, so that every cover class keeps the
      colour and transparency it painted with before. Every base plate of every theme is
      byte-identical before and after. The `pen-and-ink`, `sepia` and `winter`
      map-styles images, the place cards, the hero and the social preview do not move.
- [ ] `BASE_DIGEST`, `DIGEST`, every theme's `DIGESTS` entry, `GOLDEN_HASH` and the
      Lynmouth `plates.json` hash are re-pinned to measured literals. `LETTERING_DIGEST`
      does not move. Both copies of `theme.schema.json` are regenerated.

### Galleries (#69, #70)

- [ ] `examples/brush_gallery.py` paints every brush id, one figure per prefix group:
      `riv-str-lan` (24 ids), `maj` (40) and `trk` (48), 112 in all.
      - Rows are the eight treatments, each lettered with its number and kind.
      - Columns are the prefix's ink colour columns. `RIV` and `STR` are one brush (one
        colour, no override), so they share a column lettered "RIV = STR", and the page
        table lists both ids.
      - Each cell holds one S-stroke at 4 px and one at 12 px, with the id lettered
        beneath.
      - A docs test fails if an id of `BRUSH_COLOURS` by `BRUSH_TREATMENTS` is missing.
- [ ] `examples/pigment_gallery.py` paints every registry pigment, all on `paper_plate`
      paper, glazed by Kubelka-Munk at each pigment's own transparency.
      - `roles` has 15 rows and `painters` has 10. Each row holds:
        - the name, lettered;
        - washes at strengths 0.3, 0.6 and 0.9;
        - the pigment's transparency shown the same way in both figures: its three washes
          carry it, each glazed at the pigment's own transparency, beside the lettered
          value. There is no ink bar (the old card's grey bar, spread 0.13, read as a stray
          line, and the painter's pigments span transparency 0.04 to 0.24, too narrow for
          any bar to show a visible spread);
        - the transparency and the Colour Index code, lettered.
      - `glazes` shows six painter's pairs as columns. The rows are: multiplied, A glazed
        over B, and B glazed over A.
      - `palettes` shows every bundled palette: a row of its aliases, each swatch
        lettered with the alias and the pigment it names (a hex alias with its hex), read
        from `Palette.pigments`.
      - A docs test fails if a registry pigment or a bundled palette is missing.
- [ ] `docs/reference/brush-gallery.md` and `docs/reference/pigment-gallery.md` show the
      figures. They repeat every lettered value as real text in a table, which a docs
      test checks against the code. Both pages are linked from `brushes.md` and
      `pigments.md` and are in the nav.
      The pigment gallery retires the old pigment card everywhere: its image, master and
      script are deleted, and `docs/gallery.md` and `pigments.md` show the `roles` figure.

### Line effects shown and documented (#104, #105, #106, ADR 0070 rules 8 to 14)

- [ ] Effect parameter sweeps on free strokes, each cell's value lettered, all through the
      `examples/labelled_grid.py` helper of #170:
      - casing width by colour;
      - glow spread by blur;
      - shadow offset by blur;
      - pen casing gap by ink width.
      Each sweep is painted at scale 1, so a lettered "2 px" is `width_px: 2` in a theme
      at scale 1. Every value a sweep holds is a literal in the script, never read from a
      preset. Each sweep has an off cell painted through its primitive: casing's width 0
      column, and a lettered "none" cell for glow, shadow and pen casing, each painted
      with its value type's default (`Glow()`, `Shadow()`, `PenCasing()`). The off cell equals the plain stroke (for pen casing, the
      tint and the centre ink line), painted without the primitive, as float32 arrays
      byte for byte, before lettering and encoding. Each cell lays the wash, the effect,
      the stroke, then the paper plate, in that order. The scripts import public names
      only: they pass each primitive its effect value type and leave `threshold` at its
      default, and every figure letters with one shared label style.
- [ ] The three built-in presets are tuned against the presets figure and the sweeps
      before any image naming one is painted. PR 1's preset and effect property tests
      pass with the tuned values, which the new ADR records.
- [ ] On the Ambleside fixture:
      - a how-to result card with `road_major` cased and the route haloed, from a new
        `examples/themes/ambleside-cased.yaml`;
      - a figure of the route under each preset: none, `cased`, `halo` and `lifted`,
        each cell's style loaded from a theme file the script writes, so it uses public
        names only and follows the tuned presets.
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
- [ ] The packaged `bold` theme cases its route with the `cased` preset
      (`line_effects: {route: cased}`), the route casing it declared until ADR 0046. Its
      `digest()` moves and its base and lettering digests do not. Its map-styles image
      and mean are re-pinned. No other bundled theme adopts an effect.

### Setting grids (#67)

- [ ] `examples/setting_grids.py` paints three sweeps:
      - `pool`: the wash's edge pooling;
      - `granulation`: the granulation size;
      - `dryness`: a brush's dryness by its load.
- [ ] `examples/relief_grid.py` paints `cover.relief_strength` at 0.5, 1, 1.5 and 2 on an
      Ambleside crop.
- [ ] Each sweep is shown under the paragraph that describes its setting, at the page
      and section `plan.md` names, with the fields and values it lists: `pool` by sheet
      seed, `Sheet.gran_px` by `Sheet.fibre` (smooth and cold press), treatment `dry` by
      treatment `load` (set under `brush_overrides["major"]` and read with
      `override="major"`). Glaze order is the pigment gallery's `glazes`. Wash body and nib
      angle and width are the existing tutorial and nib grids.

### Images, budgets, notes

- [ ] Every new image is registered in `tests/support/docs_images_009a.py`, which
      `tests/support/docs_images.py` folds into its registry, under three new slices: `009a-galleries` (500,000 B), `009a-line-effects` (600,000 B) and
      `009a-setting-grids` (250,000 B). The directory stays within 7,000,000 B.
- [ ] The goldens are regenerated once, as the last task. The moved pins and images are
      exactly those in `plan.md`'s table, recorded in the new ADR and in the PR body
      with ADR 0052's review images.
- [ ] The notes for #104, #105, #106, #159, #67, #69 and #70 are deleted, along with any
      registry note PR 1 left (#71, #72, #170). Every note that linked to one now points
      at the page that replaced it.
- [ ] The PR body has one `Closes #N` line per issue: `Closes #159`, `Closes #69`,
      `Closes #70`, `Closes #67`, `Closes #104`, `Closes #105` and `Closes #106`. The
      branch name is commented on each of the seven issues when work starts.

## Changelog

```
feat(maps)!: a cover class binds a pigment that carries its own transparency; paper.pigment_transparency is gone
fix(maps): a fed route colour also letters the start and finish markers
feat(maps): the bold theme cases its route
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
- A pen casing in the theme model: pen casing stays an `ink` primitive with no theme key,
  and the line effects reference page says so as a capability fact.
- Pigment separation's transparency: `wash.separation_pigments` keeps
  `wash.separation_transparency`, a designed gap the reference page states.
