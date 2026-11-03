# 007 — Docs truth and glossary

GitHub issues: [#65](https://github.com/findlaywebb/pyntpot/issues/65) (the docs could show
a term's definition where it is used; this spec folds in the glossary gaps and drift the
feature-scoping reviews found),
[#162](https://github.com/findlaywebb/pyntpot/issues/162) (the gallery caption under the
nib-angles figure describes a different figure),
[#163](https://github.com/findlaywebb/pyntpot/issues/163) (the style-fields page names
import paths that fail, and the reference tests only check names),
[#172](https://github.com/findlaywebb/pyntpot/issues/172) (the tutorials could run as
written and lead on to the rest of the docs), and
[#TBD](https://github.com/findlaywebb/pyntpot/issues/TBD) (the wash essay says `wash`
takes nothing but a body and a pool; note `docs/issues/docs-wash-takes-options.md`).

Branch: `feat/007-docs-truth-and-glossary`. Scope source:
`specs/005-feature-scoping/sessions.md` section A.

## Problem

The docs say things the code does not, and the gates cannot tell, because the docs tests
check that names appear rather than that what the page says about them is true.

- `GLOSSARY.md` is the one source of terms, but the site shows only a link to it, about
  25 terms a reader meets have no row (tooth, glaze, granulation, rung, backing wash, ...),
  and several concepts go by two names: "nib plate" and "label plate", "landmark" and
  "callout", "track" and "route" for the recorded path, "map" and "card" for the picture,
  "trace" and "route" for centreline or outline, "treatment" for both a brush-sheet row and
  the route ink's `style`.
- `style-fields.md` claims 8 imports that fail; `cli.md`'s synopsis omits `--margin-m`;
  the gallery's nib-angles caption names the wrong word and angles; the landing page and
  the data-policy page name the wrong theme under a map; the wash essay says `wash` takes
  "nothing else" when it takes an optional `WashOptions`.
- The tutorials: the watercolour tutorial sends the reader to a route "round Keswick" (the
  first map paints Ambleside); the Painting with Python order differs between the nav and
  its index; no tutorial links a how-to, reference or explanation page; only 3 of 9
  tutorial pages have their quoted code checked; the gallery misses 4 registered images
  although it says it shows every picture; `performance.md`, a maintainer log, sits in the
  Explanation section.

## Acceptance criteria

### Glossary (#65)

- [ ] `GLOSSARY.md` stays at the repo root as plain GitHub tables, in three sections in
      this order: "Terms a reader meets" (columns Term, Meaning, In the code, Tooltip),
      "Terms a contributor meets" (Term, Meaning, In the code) and "Retired words"
      (Retired, Say instead). Every row of "Canonical terms" below is in it with the
      Meaning given there.
- [ ] Each reader row's Tooltip cell is `no` or the comma-separated forms a page
      underlines; no form is an everyday word on the test's list (map, card, route, hand,
      wash, track, ...), and no form appears twice in the glossary.
- [ ] `docs/reference/glossary.md` is generated from `GLOSSARY.md` and renders every
      reader term (no contributor term, no retired word) with an anchor `term-<slug>`; a
      test fails when it differs byte for byte from what the generator writes.
- [ ] `docs/includes/abbreviations.md` is generated from the Tooltip forms, appended to
      every site page by `pymdownx.snippets` `auto_append`, rendered by `abbr` with
      Material's `content.tooltips`; a test fails when it differs from the generator's
      output. The file is excluded from the site.
- [ ] No retired word appears in any site page, `README.md`, or any file under
      `examples/` (test, plurals and backticked words included).
- [ ] `mkdocs.yml` validates anchors (`validation: anchors: warn`), so a link to a missing
      `#term-...` or heading fails the strict build.
- [ ] The strict build passes:
      `uv run --locked --group docs mkdocs build --strict`.

### Reference truth (#163)

- [ ] Every style group's line on `style-fields.md` reads
      `` `<Dataclass>`[, from `<package>`], read as `Style.default().<group>`. ``, names the
      group's real dataclass, and names a package only when that package's `__all__`
      exports it (test).
- [ ] Every table row on `style-fields.md` is one field of its group, every field has one
      row, and each Default and Type cell equals the TOML rendering of `Style.default()`'s
      value (test; 206 rows today).
- [ ] The `cli.md` synopsis is the parser's own usage, root and every subcommand,
      whitespace aside (test).
- [ ] Every pigment row's colour and transparency, every brush treatment row's numbers and
      kind, and every brush prefix row's columns equal the code's tables (test).
- [ ] On every site page and `README.md`: every `from pyntpot... import ...` in a code
      block resolves; every prose claim `` `Name`, from `pyntpot.x` `` names a name in that
      module's `__all__`; every backticked dotted `pyntpot.*` path resolves at runtime
      (tests, generic over pages).

### Gallery and captions (#162)

- [ ] The nib-angles caption says Keswick, -38, 0, 38 and 90 across, 0, 0.52 and 0.85
      down.
- [ ] On every site page, an image followed by a `*Painted by ...*` caption: the caption
      names the registry entry's script, its `figure` and its `theme` when the entry has
      them; every number after "The labels read" is a numeric literal of that script, and
      the name after "The name is" is a string literal of it (tests). The landing-page and
      data-policy captions name their theme files.
- [ ] `docs/gallery.md` shows every registered image outside `site/` (test); the four
      missing images are added under their sections.

### Tutorials (#172)

- [ ] Every fenced `python` block on every page under `docs/tutorials/` sits under a
      `<!-- from examples/... -->` marker and is a verbatim part of that file (tests,
      covering all nine pages by glob).
- [ ] Painting with Python is in one order everywhere: Curves, Symmetry, Fractals,
      Pictures, Vector drawing, in the nav, its index and the gallery (test).
- [ ] Every nav section with an index page lists its pages there in nav order, and the
      gallery's sections follow nav order (tests; the How-to nav takes its index's order).
- [ ] Every tutorial page ends with a `Next: [...](...)` line naming the next page in nav
      order; the last tutorial page's points at the how-to index (test).
- [ ] Every tutorial page that is not an index links at least one page under `how-to/`,
      `reference/` or `explanation/` (test).
- [ ] The watercolour tutorial's "Where next" says Ambleside; references to rungs on
      Painting with Python pages name a real rung title and link its heading.
- [ ] `first-map.md` ends with a section that paints the Ambleside map in
      `examples/themes/ambleside.toml` with its landmarks, using the registered
      `images/places/ambleside.webp`. No new image is registered.
- [ ] `performance.md` lives at `docs/runbooks/performance.md`, out of the nav and the
      Explanation index; `CONTRIBUTING.md` and `docs/README.md` point at it there (test for
      the nav).

### The wash essay (#TBD)

- [ ] `how-the-wash-works.md` says `wash` takes a coverage mask, a sheet, a body, a pool
      and an optional `WashOptions`; backruns and bleed are among its fields, while pigment
      separation and the shallow-water pass are separate steps of the map painter. It no
      longer links the feature note.
- [ ] A backticked signature `name(a, b, ...)` of a public function, whose arguments are
      all parameter names of it, lists every parameter in order (test).

### Whole feature

- [ ] No pinned or golden image moves; no image is added to the registry; no example
      script's output changes (full suite with golden-marked tests green).
- [ ] The notes for #162 and #163 and the feature notes for #65 and #172 are deleted, as
      is `docs/issues/docs-wash-takes-options.md`; the PR body says `Closes #65`,
      `Closes #162`, `Closes #163`, `Closes #172` and `Closes #<wash issue>`.
- [ ] Each item under "Out of scope, filed separately" has its note and GitHub issue, or
      is folded into the existing note named there.

## Canonical terms

The glossary's new and changed rows. The Meaning column is the exact text for
`GLOSSARY.md`. "Replaces" lists the words this retires or narrows. "src changes" is what
feature 006's docstring sweep changes in `src/` (line numbers at `cb75c7b`, before 006's
module renames); identifiers, parameters, file names and manifest keys never change here.
Where src changes say "none", `src/` already agrees.

| Term | Meaning | Replaces | src changes (006) |
| --- | --- | --- | --- |
| nib plate | The lettering's own RGBA plate: marks stroked through the ink engine on the paper's colour, composited normally rather than multiplied. The lettering stage keeps it in the fetch cache as `labels-centreline.webp` or `labels-outline.webp`. | label plate | "label plate" to "nib plate", 23 times in 7 files: `ink/io.py:123` (reword: "A plate with its own alpha, such as the nib plate, is composited normally ..."); `maps/lettering_marks.py:83`; `maps/lettering/pipeline.py:5,7,73,84,98,217`; `maps/compose.py:1,7,11,125`; `maps/cache.py:7,25,228,232`; `maps/style_groups.py:245`; `maps/pipeline.py:7`, `:21` (twice), `:147`, `:152`, `:167`. |
| track | The recorded GPS path being mapped: its points, and optionally their heights and times. | route, for the recorded path | `maps/track.py:1` "A recorded route as plain data" to "A recorded GPS track as plain data"; `maps/track.py:40` "A recorded route." to "A recorded GPS track."; `maps/pipeline.py:73` "The route to map." to "The track to map." |
| route | The painted line of the track on the map; not the track itself. | (narrowed: never the recorded path, never the trace) | none beyond the track and trace rows |
| map | The picture of one track: the paper, washes, pen and lettering laid on its card, as `compose` returns it and `pyntpot map` writes it. The maps side's word, which `ink` and `letters` never use. | card and raster card, for the picture | `maps/compose.py:1` "The raster card's drawing steps: the painted map, the route and the label plate." to "The map's drawing steps: the painting, the route and the nib plate."; `maps/compose.py:5` "into a single raster card" to "into a single map"; `maps/pipeline.py:7` "into one raster card" to "into one map"; `maps/pipeline.py:143` "into one raster card." to "into one map." |
| card | The coordinate frame of one map: a box in card metres and the display and render pixel grids it maps to; converts between them. A canvas is the raster a plate is painted on; a card is the frame that says where things go on it. Not the picture: that is the map. | (narrowed) | ink never says card: `ink/sheet.py:4` "a box in the card's metres" to "a box in world units"; `ink/sheet.py:6` and `:23` "the card's own cream" to "the paper's own cream"; `ink/sheet.py:47` "The card's metre box and the pixel grid it is painted on." to "A world-unit box and the pixel grid it is painted on."; `ink/sheet.py:65` "Points in the card's metres" to "Points in world units"; `ink/cut.py:4-5` "runs off a card is drawn up to the card's edge" to "runs off a canvas is drawn up to the canvas's edge"; `ink/io.py:131` "on the card" to "on the painting"; `ink/style.py:182` "the dry share of the card" to "the dry share of the painting". 9 lines in 4 files. |
| trace | How a glyph becomes strokes: `centreline` thins it to its skeleton and writes that, `outline` draws round its edge. The face style's `label_route` chooses it. | route, for centreline or outline | prose "route" meaning the trace to "trace": `letters/trace.py:1` ("the centreline trace and the outline trace"), `:15` ("does not choose a trace"); `letters/font.py:6` ("chooses the trace"), `:311` ("a path and trace"); `letters/nib.py:116` ("an outline trace"); `letters/style.py:74` ("The outline trace"); `letters/skeleton.py:58` ("the outline trace draws"); and the `route:` argument lines start "The trace," at `letters/hand.py:54`, `letters/font.py:200`, `letters/font.py:315`, `maps/lettering_marks.py:96`, `maps/lettering/pipeline.py:223`. 12 lines in 8 files. |
| landmark | A named thing a map letters beside the route, such as a fell, a bridge or a bakery: one the caller names, at its own coordinates or looked up among the basemap's candidates, or one the lettering ranks and picks itself. | callout | `maps/lettering_furniture.py:87` "a callout drawn in one go" to "one mark drawn in one go". |
| treatment | One row of the brush sheet, `1` to `8`: how a brush behaves, how dark, how many bristles, how dry, whatever its width and ink. | treatment, for the route ink's `style` | "treatment" for the route ink's `style` to "style": `maps/strands.py:56` (`the "pen" style`); `maps/style.py:166,168`; `maps/style_groups.py:15,261`. 5 lines in 3 files. |
| route ink | How the route is drawn on the map: its `style` (`pen`, or any other value for a solid line), its width in display pixels, its colour, its blend and its opacity; the width also sets how near two passes of a retraced route have to come to be drawn as one stroke. The style field `Style.route_ink`, a theme's `[route_ink]` table; a caller feeds its colour and width through `Style.with_route_ink`. | (treatment, see above) | covered by the treatment row |
| annotations | Caller-supplied landmarks, roads, places, span requests and journal notes. | | none |
| tooth | The paper's height, high where the paper stands up: a wash lightens where the tooth is high, and granulation settles where it is low. The sheet's `paper` field. | | none |
| granulation | Pigment settling into the paper's low places as a wash dries, so the wash reads grainy; the sheet's `gran_px` sets the size of its grain. | | none |
| foxing | The small rust specks of an old sheet of paper, laid by the paper plate; `PaperStyle.paper_foxing` sets how strong. | | none |
| coverage mask | The array in 0 to 1 that says where a wash goes, 1 inside the shape and 0 outside: the first argument of `wash`. | | none |
| body | The flat, even part of a wash inside its edge; `wash`'s `base` is the body's density. | | none |
| pool | The extra density a wash carries in a band just inside its edge, where the pigment gathers as the water dries: a real wash's edge darkening. `wash`'s `pool`. | | none |
| glaze | Laying one pigment layer over another so the light passes through both and the colours mix as transparent films, by the Kubelka-Munk model, rather than multiplying; `PaperStyle.km_glazing` turns it on. | | none |
| backrun | A second front of water pushing deposited pigment ahead of it, leaving a pale centre and a dark, crenellated ridge where it dries. | | none |
| accumulator | The float array a stroke's bristles deposit ink into, before `ink_density` turns it into a density. | | none |
| tip | The brush's bristles, sampled across and along a stroke as it is stamped. | | none |
| dab | One small mark of a brush pressed and lifted rather than pulled: the wood's texture is laid in dabs. | | none |
| face | The typeface the hand writes from: a font whose glyph outlines become pen paths. | | none |
| glyph | One character's shape in the face, read as an outline and traced into strokes. | | none |
| skeleton | The one-pixel centre line a glyph's filled shape is thinned to, which the centreline trace walks into pen strokes. | | none |
| backing wash | A pale patch of the paper's own colour lifted under a name so it reads over paint; a setting's `wash` flag asks for it. | wash, for the flag | none (renaming `Setting.wash` is out of scope) |
| leader | The thin line from a name set beside its anchor to that anchor, ending at its pin. | | none |
| label | One name on the map as the lettering places it: its text, its anchor, its kind and the box it takes. | | none |
| place | A settlement the caller names for the lettering always to letter. | | none |
| ribbon | The trimmed extent of the painted ground round the track: the washes stop at its edge and the paper shows beyond it; its radius grows with the root of the track's box. | | none |
| line class | The kind of a line on the map, such as a major road, a lane or a river, by which the style picks its brush and width. | | none |
| cover class | The kind of a land cover area, such as wood, meadow or water, by which the style picks its pigment and wash. | | none |
| digest | A hash of some of the style's groups: `base_digest` keys the base plates, `lettering_digest` the lettering and `digest` the whole style, so a change repaints only what its digest covers. | | none |
| rung | One step of the watercolour tutorial: a script in `examples/` and the section that teaches it. There are seven, from stretching the paper to composing the painting. | step, for a rung | none (the lettering's offset-ladder "rung" is filed separately) |
| ink pad | One line class's accumulator on a plate's grid, which strokes are laid into and density is read back from. (contributor) | | none |

Retired words, the glossary's "Retired words" table: label plate (say nib plate), callout
(landmark), raster card (map), recorded route (track), centreline route (centreline
trace), outline route (outline trace).

## Decisions

- **Generated and checked, not generated at build time.** A stdlib-only generator,
  `tests/support/glossary.py`, writes the glossary page and the abbreviations file from
  `GLOSSARY.md`; both are committed, and pytest fails on drift with the command to
  regenerate. The page reads on GitHub, the check runs without the docs group, and no
  build-time code goes untested. ADR 0034's rule holds: the source pages carry no
  site-only syntax; the only site-only file is the excluded abbreviations file.
- **Tooltips only for distinctive terms**, by explicit forms per row, so common words are
  never underlined and plurals and capitals are listed rather than guessed.
- **No "Terms on this page" box.** `abbr` marks every use in place and the glossary page
  has an anchor per term, which together do the box's job; the box would need a build
  hook. #65 closes on this.
- **B-neutral wording.** Every page this feature writes is true whether or not feature
  006 exports the style groups, `WashOptions` or the provider protocols, and whatever it
  renames the four shadowing modules to: a group line names a package only when it
  exports the group, the wash essay makes no export claim, and the glossary's "In the
  code" cells name exported names or private modules outside the four 006 renames.
- **The docs-truth suite is generic and data-driven**: pages come from `mkdocs.yml`
  (`docs_dir` minus `exclude_docs`), order from its nav, images from the registry, facts
  from the code. A new page, nav entry, image or style field is covered with no test
  edit.

## Interaction with feature 006 (one public surface)

006 owns `src/`, the `__init__` files, docstrings and `tests/architecture/`; this feature
owns prose under `docs/`, `GLOSSARY.md`, and the new `tests/docs/` suite. 006 executes the
"src changes" column above in its docstring sweep. If 006 moves names this suite imports
(`BRUSH_TREATMENTS`, `BRUSH_COLOURS`, `PEN_ROWS`, `CONSUMER_ONLY`), it repoints the import
lines in `tests/docs/`. After 006 lands, plan slice S8 adds the exporting package to group
lines and glossary cells for whatever 006 exported, and extends the retired-word scan to
`src/`.

## Changelog

PR title: `docs(docs): one glossary shown in place, and docs tests that check what pages say`

- `docs(docs): the glossary renders on the site, and its distinctive terms show their meaning when you point at them`
- `docs(docs): about 30 new glossary terms, one name per concept, and a retired-words table`
- `docs(docs): correct the nib-angles caption, two theme captions and the style-fields import lines`
- `docs(docs): the command-line synopsis shows --margin-m, as the parser does`
- `docs(docs): the wash essay states what wash takes, WashOptions included`
- `docs(docs): one Painting with Python order, a Next line on every tutorial, and links on to guides, reference and explanation`
- `docs(docs): the first map ends in the Ambleside theme, and the gallery shows every registered picture`
- `docs(docs): the performance log moves out of Explanation to the maintainers' runbooks`
- `test(tests): docs tests compare tables, synopsis, captions, imports and quoted code with the code, over every page`

## Out of scope, filed separately

Each gets a note and a GitHub issue in plan slice S7 unless it names an existing note.

- Short complete programs opening each Painting with Python page, shorter once blank
  paper and lettering take one call (#165, #166): `docs/features/docs-tutorial-opening-programs.md`.
- Example code names: `route = Track.from_gpx(track)`, `card = compose(...)`, `crest` and
  `WASH_BODY` for a wash body, and example docstrings that call the picture a card: fold
  into `docs/features/docs-examples-housekeeping.md` (#174), whose scripts the docs quote
  verbatim.
- "card" meaning the picture in `src/` docstrings beyond the lines above:
  `docs/issues/maps-card-means-the-frame.md`.
- The lettering's offset ladder calls its steps "rungs", a homonym of the tutorial rung:
  `docs/issues/maps-lettering-rung-homonym.md`.
- `fetch(places=)` (points of interest) against `Annotations.places` (settlement names),
  unless 006's ADR renames it: `docs/issues/maps-fetch-places-name-collision.md`.
- Identifiers that say route for the trace (`FaceStyle.label_route`, `route=` arguments,
  the nib plate sidecar key `route`): `docs/issues/letters-route-means-trace.md`.
- The route ink's key `style` overloading `Style`: `docs/issues/maps-route-ink-style-key.md`.
- `Setting.wash` named for the backing wash: `docs/issues/letters-setting-wash-names-the-backing-wash.md`.
- A user-facing page on how long a map takes and how much memory, from measurements:
  `docs/features/docs-performance-guide.md`.
- Splitting the 710-line watercolour tutorial and moving its explanation out:
  `docs/features/docs-watercolour-tutorial-split.md`.
- The keys of the eight style fields shown as `table`: `docs/features/docs-style-field-table-keys.md`.
- Dataclass defaults that differ from the resolved default style: existing #158, not
  refiled.
