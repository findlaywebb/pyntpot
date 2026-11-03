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
[#176](https://github.com/findlaywebb/pyntpot/issues/176) (the wash essay says `wash`
takes nothing but a body and a pool; note `docs/issues/docs-wash-takes-options.md`).

Branch: `feat/007-docs-truth-and-glossary` (worktree branch
`docs/007-docs-truth-and-glossary`). Scope source:
`specs/005-feature-scoping/sessions.md` section A. Lands after feature 006 (one public
surface, ADR 0068): slices S0 to S7 are written before 006 merges, S8 after it, and the PR
merges only once S8 is done.

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
  "nothing else" when it takes an optional `WashOptions` (#176).
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
- [ ] After 006 (S8): ADR 0068 exports every style group, so every group line names its
      package (`WashStyle` from `pyntpot.ink`, the seven map groups from `pyntpot.maps`,
      the five already exported as before), and the two renamed groups read
      `LetteringStyle` and `RouteInkStyle`; the test requires the `, from` part.
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

### The wash essay (#176)

- [ ] `how-the-wash-works.md` says `wash` takes a coverage mask, a sheet, a body, a pool
      and an optional `WashOptions`; backruns and bleed are among its fields, while pigment
      separation and the shallow-water pass are not: they act on what washes produce, and
      the map painter runs them after its washes. It no longer links the feature note.
- [ ] After 006 (S8): the essay names `WashOptions`, `separated` and `fluid_modulate` as
      from `pyntpot.ink` (the from-claim test checks each), and says the last two read
      their settings from `WashStyle`.
- [ ] A backticked signature `name(a, b, ...)` of a public function, whose arguments are
      all parameter names of it, lists every parameter in order (test).

### Whole feature

- [ ] No pinned or golden image moves; no image is added to the registry; no example
      script's output changes (full suite with golden-marked tests green).
- [ ] The notes for #162 and #163 and the feature notes for #65 and #172 are deleted, as
      is `docs/issues/docs-wash-takes-options.md` (#176); the PR body says `Closes #65`,
      `Closes #162`, `Closes #163`, `Closes #172` and `Closes #176`.
- [ ] After 006 (S8): the prose 006's plan hands to this feature ("Handed to session A")
      is true: `self-host-providers.md` says the provider protocols are public and links
      no deleted note; `letter-your-own-landmarks.md` names `Landmark` from
      `pyntpot.maps`; `docs/architecture.md` states ADR 0068's rule; every GitHub link on a
      site page names a file that exists on the branch (test).
- [ ] No 007 slice edits a file under `src/`. 006's S9 makes the docstring changes listed
      under "Docstring changes for 006's S9" below; S8 proves them with the retired-word
      scan over `src/`.
- [ ] Each item under "Out of scope, filed separately" has its note and GitHub issue, or
      is folded into the existing note named there.

## Canonical terms

The glossary's new and changed rows. The Meaning column is the exact text for
`GLOSSARY.md`. "Replaces" lists the words this retires or narrows. "src changes (006 S9)"
counts what feature 006's slice S9 ("docstring terminology sweep") changes in `src/`; the
exact old and new strings, file by file, are under "Docstring changes for 006's S9" below
the table. No 007 slice edits `src/`. Identifiers, parameters, file names and manifest
keys never change here. Where the column says "none", `src/` already agrees.

| Term | Meaning | Replaces | src changes (006 S9) |
| --- | --- | --- | --- |
| nib plate | The lettering's own RGBA plate: marks stroked through the ink engine on the paper's colour, composited normally rather than multiplied. The lettering stage keeps it in the fetch cache as `labels-centreline.webp` or `labels-outline.webp`. | label plate | 25 uses in 26 lines (two wrap) of 8 files: N1 to N24 below. |
| track | The recorded GPS path being mapped: its points, and optionally their heights and times. | route, for the recorded path | 3 lines in 2 files: T1 to T3. |
| route | The painted line of the track on the map; not the track itself. | (narrowed: never the recorded path, never the trace) | none beyond the track and trace rows |
| map | The picture of one track: the paper, washes, pen and lettering laid on its card, as `compose` returns it and `pyntpot map` writes it. The maps side's word, which `ink` and `letters` never use. | card and raster card, for the picture | 4 lines in 2 files: M1 to M4 (M1 and M3 are also N11 and N20). |
| card | The coordinate frame of one map: a box in card metres and the display and render pixel grids it maps to; converts between them. A canvas is the raster a plate is painted on; a card is the frame that says where things go on it. Not the picture: that is the map. | (narrowed) | 9 lines in 4 files, all in `ink`: C1 to C8. |
| trace | How a glyph becomes strokes: `centreline` thins it to its skeleton and writes that, `outline` draws round its edge. The face style's `label_route` chooses it. | route, for centreline or outline | 12 lines in 8 files: R1 to R12. |
| landmark | A named thing a map letters beside the route, such as a fell, a bridge or a bakery: one the caller names, at its own coordinates or looked up among the basemap's candidates, or one the lettering ranks and picks itself. | callout | 1 line in 1 file: L1. |
| treatment | One row of the brush sheet, `1` to `8`: how a brush behaves, how dark, how many bristles, how dry, whatever its width and ink. | treatment, for the route ink's `style` | 5 lines in 3 files: S1 to S5. |
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

### Docstring changes for 006's S9

The exact strings 006's slice S9 changes, for 006 to execute; 007 changes none of them.
Line numbers are at `cb75c7b` (`src/` is unchanged through `03cf136`, this plan's base).
006's earlier slices move lines (the S0 splits, the S4 to S6 field docs) and rename
`maps/compose.py` to `maps/compose_steps.py`, so S9 finds each change by its old string,
which is unique in its file. Where a lane has already moved a `#:` comment into an
`Attributes:` entry or an attribute docstring, the change applies to the text where it now
sits, with the same new wording. A line the new text pushes past 100 characters is
rewrapped within its docstring. Every change is inside a docstring or a comment except N24,
a log message (no test reads it), which S9 changes as its one string literal.

Totals: 58 lines in 21 files (N 26, T 3, M 4 of which 2 are N lines, C 9, R 12, L 1, S 5).
After S9, `grep -rniE 'label plate|label$|raster card|recorded route|centreline route|outline route|callout' src/pyntpot`
finds nothing but unrelated lines that end in "label" (`span_ends.py:127`,
`picks_lines.py:91`, `label.py:145` at `cb75c7b`).

nib plate, replacing "label plate": 25 uses in 26 lines of 8 files.

```text
N1  ink/io.py:123                  The label plate is composited normally rather than multiplied, so it needs
                                -> A plate with its own alpha, such as the nib plate, is composited normally rather than multiplied, so it needs   (rewrap the paragraph)
N2  maps/lettering_marks.py:83     #: the map's own ink on the label plate, so the card and the page get the same
                                -> #: the map's own ink on the nib plate, so the card and the page get the same
N3  maps/lettering/pipeline.py:5   measured by the hand, and strokes them into a label plate beside the plates;
                                -> measured by the hand, and strokes them into a nib plate beside the plates;
N4  maps/lettering/pipeline.py:7   label plate's path.
                                -> nib plate's path.
N5  maps/lettering/pipeline.py:73  plate_path: The label plate, or `None` when nothing was stroked.
                                -> plate_path: The nib plate, or `None` when nothing was stroked.
N6  maps/lettering/pipeline.py:84  """Place a map's names and spans and stroke them into a label plate.
                                -> """Place a map's names and spans and stroke them into a nib plate.
N7  maps/lettering/pipeline.py:88-89  against, their darkness keeps names on light ground, and the label / plate is written beside them.
                                -> against, their darkness keeps names on light ground, and the nib / plate is written beside them.
N8  maps/lettering/pipeline.py:98  The placed labels and spans and the label plate; empty, with no plate,
                                -> The placed labels and spans and the nib plate; empty, with no plate,
N9  maps/lettering/pipeline.py:217 plates: The painted plates, beside which the label plate is written.
                                -> plates: The painted plates, beside which the nib plate is written.
N10 maps/lettering/__init__.py:7-8 ... and `pipeline` (the `letter` stage and the label / plate it strokes).
                                -> ... and `pipeline` (the `letter` stage and the nib / plate it strokes).
N11 maps/compose.py:1 (compose_steps.py)  """The raster card's drawing steps: the painted map, the route and the label plate.
                                -> """The map's drawing steps: the painting, the route and the nib plate.   (also M1)
N12 maps/compose.py:7              the route ink, and `paste_labels` pastes the label plate over both. The
                                -> the route ink, and `paste_labels` pastes the nib plate over both. The
N13 maps/compose.py:11             painter made, a route already in display pixels and a label plate already
                                -> painter made, a route already in display pixels and a nib plate already
N14 maps/compose.py:125            """The label plate, over the painting, at the card's own size.
                                -> """The nib plate, over the painting, at the card's own size.
N15 maps/cache.py:7                digest), and `Cache.lettering_key`, the key of the label plate (the marks the nib
                                -> digest), and `Cache.lettering_key`, the key of the nib plate (the marks the nib
N16 maps/cache.py:25               The label plate's key is derived from the marks themselves, every float rounded to
                                -> The nib plate's key is derived from the marks themselves, every float rounded to
N17 maps/cache.py:228              """Return the key a label plate is cached under.
                                -> """Return the key a nib plate is cached under.
N18 maps/cache.py:232              base_hash: The hash of the base plates the label plate is drawn against.
                                -> base_hash: The hash of the base plates the nib plate is drawn against.
N19 maps/style_groups.py:245       #: no labels or spans and draws no label plate. The attribution follows
                                -> #: no labels or spans and draws no nib plate. The attribution follows
N20 maps/pipeline.py:7             lays the painted plates, the route and the label plate into one raster card;
                                -> lays the painted plates, the route and the nib plate into one map;   (also M3)
N21 maps/pipeline.py:21            pastes the label plate over it when the lettering has one; with no label plate
                                -> pastes the nib plate over it when the lettering has one; with no nib plate
N22 maps/pipeline.py:147           ink is a pen), the label plate is pasted over both when there is one, and
                                -> ink is a pen), the nib plate is pasted over both when there is one, and
N23 maps/pipeline.py:152           lettering: The lettering; its label plate, when set, is pasted over the
                                -> lettering: The lettering; its nib plate, when set, is pasted over the
N24 maps/pipeline.py:167           log.info("no label plate for %s, the card has no lettering", plates.directory)
                                -> log.info("no nib plate for %s, the map has no lettering", plates.directory)   (log message)
```

track, replacing "route" for the recorded path: 3 lines in 2 files.

```text
T1  maps/track.py:1                """A recorded route as plain data: where it went, and optionally how high and when.
                                -> """A recorded GPS track as plain data: where it went, and optionally how high and when.
T2  maps/track.py:40               """A recorded route.
                                -> """A recorded GPS track.
T3  maps/pipeline.py:73            track: The route to map.
                                -> track: The track to map.
```

map, replacing "raster card": 4 lines in 2 files.

```text
M1  maps/compose.py:1              (N11)
M2  maps/compose.py:5              plates into a single raster card instead, so the picture can be handed over
                                -> plates into a single map instead, so the picture can be handed over
M3  maps/pipeline.py:7             (N20)
M4  maps/pipeline.py:143           """Compose painted, lettered plates into one raster card.
                                -> """Compose painted, lettered plates into one map.
```

card, which `ink` never says: 9 lines in 4 files.

```text
C1  ink/sheet.py:4                 mark; `Canvas`, a box in the card's metres and the pixel grid it is painted on, which
                                -> mark; `Canvas`, a box in world units and the pixel grid it is painted on, which
C2  ink/sheet.py:6                 is the card's own cream.
                                -> is the paper's own cream.
C3  ink/sheet.py:23                #: The card's own cream, before anything is laid on it.
                                -> The paper's own cream, before anything is laid on it.   (an attribute docstring after 006 S4)
C4  ink/sheet.py:47                """The card's metre box and the pixel grid it is painted on."""
                                -> """A world-unit box and the pixel grid it is painted on."""   (the summary line, once S4 adds Attributes:)
C5  ink/sheet.py:65                pts: Points in the card's metres, `(n, 2)`.
                                -> pts: Points in world units, `(n, 2)`.
C6  ink/cut.py:4-5                 ... so a line that runs off a card / is drawn up to the card's edge.
                                -> ... so a line that runs off a canvas / is drawn up to the canvas's edge.   (2 lines)
C7  ink/io.py:131                  the card a reader looks at closest.
                                -> the painting a reader looks at closest.
C8  ink/style.py:182               #: the dry share of the card moves 0.148 to 0.140, so the land's outer
                                -> #: the dry share of the painting moves 0.148 to 0.140, so the land's outer
```

trace, replacing "route" for centreline or outline: 12 lines in 8 files.

```text
R1  letters/trace.py:1             """Strokes from a glyph: the centreline route and the outline route.
                                -> """Strokes from a glyph: the centreline trace and the outline trace.
R2  letters/trace.py:15            and does not choose a route; `letters.font` does.
                                -> and does not choose a trace; `letters.font` does.
R3  letters/font.py:6              How a glyph becomes strokes is `letters.trace`; this module chooses the route
                                -> How a glyph becomes strokes is `letters.trace`; this module chooses the trace
R4  letters/font.py:311            """A face, the vendored one by default, opened once a path and route and kept.
                                -> """A face, the vendored one by default, opened once a path and trace and kept.
R5  letters/nib.py:116             outline: True when the glyph pen is narrowed for an outline route; it
                                -> outline: True when the glyph pen is narrowed for an outline trace; it
R6  letters/style.py:74            #: The outline route draws two strokes where the centreline draws one, a
                                -> #: The outline trace draws two strokes where the centreline draws one, a
R7  letters/skeleton.py:58         contours the outline route draws.
                                -> contours the outline trace draws.
R8  letters/hand.py:54             route: `centreline` or `outline`; the face style's when not given.
                                -> route: The trace, `centreline` or `outline`; the face style's when not given.
R9  letters/font.py:200            route: `CENTRELINE` to thin the glyph to a written skeleton, `OUTLINE`
                                -> route: The trace, `CENTRELINE` to thin the glyph to a written skeleton, `OUTLINE`   (rewrap the entry)
R10 letters/font.py:315            route: `CENTRELINE` or `OUTLINE`.
                                -> route: The trace, `CENTRELINE` or `OUTLINE`.
R11 maps/lettering_marks.py:96     route: `centreline` or `outline`; the style's when not given.
                                -> route: The trace, `centreline` or `outline`; the style's when not given.
R12 maps/lettering/pipeline.py:223 route: `centreline` or `outline`; the style's when not given.
                                -> route: The trace, `centreline` or `outline`; the style's when not given.
```

`letters/nib.py:135` ("the route's own set-down") and `letters/style.py:95` ("the route's
own colour") mean the painted route and stay.

landmark, replacing "callout": 1 line in 1 file.

```text
L1  maps/lettering_furniture.py:87 the leader and the ring read as one mark, a callout drawn in one go. A gap
                                -> the leader and the ring read as one mark, drawn in one go. A gap
```

style, replacing "treatment" for the route ink's `style`: 5 lines in 3 files. S4 and S5
read the class name after 006's S6 rename.

```text
S1  maps/strands.py:56             When the style paints the route pen and its route ink is the `"pen"` treatment,
                                -> When the style paints the route pen and its route ink is the `"pen"` style,
S2  maps/style.py:166              Only the colour and the width are fed: the route's treatment, blend and
                                -> Only the colour and the width are fed: the route's style, blend and
S3  maps/style.py:168              width, except when the treatment is `"pen"` and a pen plate was painted: then
                                -> width, except when the style is `"pen"` and a pen plate was painted: then
S4  maps/style_groups.py:15        basemap options and the resolved ink are theme values. `RouteInkStyle`'s treatment,
                                -> basemap options and the resolved ink are theme values. `RouteInkStyle`'s style,
S5  maps/style_groups.py:261       """How the route is drawn on the card: its treatment, width, colour, blend and opacity.
                                -> """How the route is drawn on the map: its style, width, colour, blend and opacity.
```

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
- **True on both sides of 006.** ADR 0068 settles what 006 changes: every style group is
  exported (`WashStyle` from `pyntpot.ink`, `CardStyle`, `RibbonStyle`, `CoverStyle`,
  `RouteStyle`, `BasemapStyle`, `LetteringStyle` and `RouteInkStyle` from
  `pyntpot.maps`), `LetteringPolicy` becomes `LetteringStyle` and `RouteInk` becomes
  `RouteInkStyle`; `WashOptions`, `Flow`, `Blooms`, `separated` and `fluid_modulate` are
  exported from `pyntpot.ink`; `Features`, `Elevation`, `Card`, `Credit`, `Manifest`,
  `Label`, `Landmark`, `SpanRequest` and the rest of its table from `pyntpot.maps`; `Pt`
  becomes `Point` and `Anchor` gives way to `Align`; `ink/stamp.py`, `ink/wash.py`,
  `maps/compose.py` and `maps/vector_layers.py` become `ink/stamping.py`,
  `ink/washing.py`, `maps/compose_steps.py` and `maps/vector_layer_build.py`; the brush
  sheet tables move to `ink/brush_sheet.py`. Every sentence S0 to S7 write is true at
  this branch's base and stays true once 006 lands: a group line names a package only
  when it exports the group today, the wash essay makes no export claim, and the
  glossary's "In the code" cells name exported names or private paths that resolve on
  both sides. A sentence that can only be true on one side (a renamed class, a newly
  exported name, a module that exists only after 006) is written in S8, after the rebase.
- **The docs-truth suite is generic and data-driven**: pages come from `mkdocs.yml`
  (`docs_dir` minus `exclude_docs`), order from its nav, images from the registry, facts
  from the code. A new page, nav entry, image or style field is covered with no test
  edit.

## Interaction with feature 006 (one public surface)

006 (`specs/006-one-public-surface/`, ADR 0068) merges first. It owns, and this feature
leaves alone until it has merged:

- `src/**`, docstrings included. Its slice S9 makes the changes under "Docstring changes
  for 006's S9" above; no 007 slice edits `src/`.
- `tests/architecture/**`, in particular `test_reference_pages.py` (its brush-table import
  line moves to `pyntpot.ink.brush_sheet`), `test_site.py` and `test_reference_keys.py`.
  007 writes its new docs-truth tests in a new `tests/docs/` package from the start;
  moving `test_tutorials.py` and `test_reference_pages.py` into `tests/docs/` happens in
  plan slice S8, after the rebase onto 006.
- The directives and dotted paths in `docs/reference/{ink,letters,maps}.md` and the
  "Implemented in" lines of `docs/explanation/references.md`.
- Three `GLOSSARY.md` rows: "brush sheet" (cites `ink.brush_sheet` for the tables),
  "style group" (adds that each is a frozen, keyword-only dataclass named
  `<Group>Style`) and "vector layers" (cites `maps.vector_layer_build.VectorLayers`).
  S1 restructures the whole file and keeps those rows' meaning as it is on `main`; S8
  resolves the rebase conflict by writing 006's three facts into the new format.
- The note edits of 006's S8, among them `docs/features/docs-missing-how-tos.md` and
  `docs/features/docs-examples-housekeeping.md`; this feature's edits to those two notes
  wait for S8.
- `tests/unit/maps/**` by glob (006's S6). 007's S5 edits one file under it,
  `tests/unit/maps/test_example_themes.py` (the `callouts` key); 006 names nothing in that
  file (no renamed class, alias, module or positional style group), so the two diffs do
  not meet.

After 006 lands, plan slice S8 rebases, makes the sentences that are only true after 006
(the "Handed to session A" list of 006's plan), repoints this suite's imports to 006's
modules, moves the two test files, and extends the retired-word scan to `src/`.

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
- `fetch(places=)` (points of interest) against `Annotations.places` (settlement names);
  ADR 0068 does not rename it: `docs/issues/maps-fetch-places-name-collision.md`.
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
