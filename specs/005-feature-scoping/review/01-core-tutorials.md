# Review 01: core tutorials (watercolour, first map) and their entry points

Slice: docs/tutorials/index.md, docs/tutorials/paint-a-watercolour.md, docs/tutorials/first-map.md,
examples/{paper,wash,brush_stroke,pigments,nib_line,lettering,composition,tutorial_grids,route_map}.py,
README.md, docs/index.md.

Run check (this machine, no network):
- paper, wash, brush_stroke, pigments, nib_line: run, under 1 s each. lettering, composition: run, about 2 s each.
  `save_image` creates the out dir, so the claim at paint-a-watercolour.md:39-41 holds.
- route_map.py from a copy of tests/fixtures/ambleside: runs, 28 s, no fetch, writes 1800x1281 `map.png`.
  It prints nothing until the final "wrote" line.
- `pyntpot map` from the same cache: says "plates ... are current, nothing repainted" and writes the card.
  The second run took 5 s. The first run took 3 min 17 s of wall time but only 5 s of CPU; I could not reproduce
  it. It was probably uv's first start of the console script, but this is unconfirmed.
- The code blocks match the scripts. tests/architecture/test_tutorials.py and test_readme.py enforce that through the `<!-- from examples/X.py -->` marker
  (these pages do not use `--8<--` includes).

Findings are in order of impact.

---

## 1. The first map does not look like the map that drew the reader in, and the tutorial never says how to get there
- **Where:** README.md:7-9, README.md:45 (gallery cell 8), docs/index.md:3-5, docs/tutorials/first-map.md:3-5, 63, 171-175; examples/place_card.py:1-20.
- **What's wrong:** The README hero, the docs landing image and the README gallery's "route map" thumbnail are all painted by
  `place_card.py`. That script uses the hand-tuned `examples/themes/ambleside-hero.toml` / `ambleside.toml` theme and the curated callouts
  in `examples/places.toml`. The README gallery cell links that thumbnail to first-map.md, but labels it `examples/place_card.py`. The
  tutorial then runs `route_map.py` with `Style.default()` and no annotations. The newcomer gets a visibly weaker card: pink route instead
  of maroon, washes on only part of the card, Rydal Water and Grasmere not named, "Loughrigg Terrace" missing. Nothing in the tutorial
  mentions `examples/themes/`, `place_card.py`, annotations or callouts, so the reader cannot reach the picture that sold them. The
  docs/index caption says "the Ambleside theme", but the hero is actually `ambleside-hero.toml`.
- **Cause:** prose and docs structure (the entry images and the tutorial output come from different scripts and styles). A missing
  library feature makes it worse: themes are repo files, not named package themes.
- **Fix:** Pick one of two options. (a) Make the README gallery cell and the first-map hero both use the `route_map.py` image, captioned as
  such. (b) Add a final first-map section, "Paint it in the Ambleside theme": `--style examples/themes/ambleside.toml`, then
  `place_card.py` with `places.toml`, with the result image. Fix the docs/index caption to name `ambleside-hero.toml`.
- **Size:** M · **Area:** docs (maps) · **Related:** maps-named-themes. New evidence: the first tutorial's output is visibly worse than the
  README hero because the good look lives only in `examples/themes/`.

## 2. Laying lettering over a picture takes about 20 lines of disk round-trip and image maths, copied verbatim into two rungs
- **Where:** examples/lettering.py:78-94, examples/composition.py:119-135 (quoted at paint-a-watercolour.md:541-557 and 652-668);
  examples/tutorial_grids.py:118-154 (`_letter`).
- **What's wrong:** To put a name on the paper, the reader has to do all of the following:
  - build a `Hand`;
  - build a second `Canvas` at `NIB_SCALE`, and a zero `dark2` array (never explained on the page);
  - build a `NibSurface` with `GRAN_PX * NIB_SCALE`;
  - build `NibGroups(NibStyle(), face, hand_style, BrushStyle(), PaperStyle())`. That is five style groups, two of them from `ink`, and
    `face`/`hand_style` are passed a second time;
  - call `nib_plate` with a **file path**, check for `None`;
  - reopen the file with PIL, Lanczos-resize it, and alpha-blend by hand.

  `nib_plate` can only write to disk, so an in-memory picture still needs a temp file (the grids use `tempfile`). The prose
  (paint-a-watercolour.md:507-513) names `NibSurface` but never explains `NIB_SCALE`, `canvas2` or `dark2`. "Compose the painting" says
  it "adds nothing new", yet repeats the whole block. There is also a correctness inconsistency: the rung scripts resize in straight
  `RGBA`, but `_letter` resizes premultiplied (`convert("RGBa")`, tutorial_grids.py:151). So the scripts a reader copies use the variant
  that can leave dark fringes on Lanczos edges.
- **Cause:** a missing library feature, plus code.
- **Fix:** Add a public `letters` helper that returns the plate as an array and lays it over an image by alpha. One shape:
  `nib_array(marks, surface, groups) -> np.ndarray` plus `lay_over(image, rgba)`. Better still, `letter_onto(image, settings, nib=NibStyle(), seed=..., supersample=2, ground=None)`, which hides the NibSurface, the scale and the dark grid. Shrink both rungs to about 3 lines.
  Until then, put the block in one shared helper and explain `NIB_SCALE` and `dark` in the prose. Use premultiplied resizing everywhere.
- **Size:** L (API) / S (interim docs) · **Area:** letters · **Related:** none directly (letters-nib-follows-writing-line touches
  nib_plate but not this).

## 3. Every ink rung opens with `Canvas(0, 0, W, H, W, H)` and `paper_plate(..., W)`, which do nothing the reader can see
- **Where:** paint-a-watercolour.md:59-62, 75-77, 145-147, 238-240, 338-340, 434-436, 537-539, 641-643; README.md:110-112;
  src/pyntpot/ink/paper.py:41-52; src/pyntpot/ink/sheet.py:46-55.
- **What's wrong:**
  - `paper_plate` reads only the canvas's `w`/`h`, and reads `display_px` only when the style asks for a grid (its own docstring says
    so). Every rung still builds a 6-argument `Canvas` and passes `W` a second time. Neither is explained.
  - The prose calls `Canvas` "the pixel grid you paint on". GLOSSARY.md:9 says it is "a world-unit box and the pixel grid". The first
    four arguments are a metre box, and here it is set equal to the pixels, silently.
  - `Sheet(H, W, ...)` takes height first, while `Canvas(..., W, H)` takes width first. That is a trap when a reader edits sizes.
  - The README Quick start shows the same three lines to every first-time visitor.
- **Cause:** a missing library feature (the paper API is shaped for the map painter). Also a terminology mismatch between the prose and
  the glossary.
- **Fix:** Add `paper_plate(sheet, style=PaperStyle())`, with the canvas and `display_px` optional and taken from the sheet, or a
  `Sheet.paper(style)` method. Meanwhile, use keywords in the examples (`Canvas(x0=0, y0=0, x1=W, y1=H, w=W, h=H)`) and say once on
  the page why the box equals the pixels. Make the prose say what the glossary says.
- **Size:** M · **Area:** ink · **Related:** docs-examples-review (#63). New evidence: this is the boilerplate in all 7 rungs and the
  README.

## 4. The tutorials are dead ends: no links to the how-to, reference or explanation pages they lean on
- **Where:** paint-a-watercolour.md:716-720, first-map.md:171-175, tutorials/index.md:3-10.
- **What's wrong:** The two pages link only to each other, to uv and to the fixture. Things a newcomer needs next, with no link to them:
  - the brush ids used (`RIV1-a`, `MAJ6-e`) → docs/reference/brushes.md;
  - the pigment keys → docs/reference/pigments.md;
  - "edge darkening / pooled edge" → docs/explanation/how-the-wash-works.md;
  - hand and nib → docs/explanation/the-hand-and-the-nib.md.

  first-map's "Where next" says to open two scripts side by side. It does not point to Painting with Python (which the tutorial index
  lists as the third tutorial), nor to the obvious next tasks: write-a-theme, letter-your-own-landmarks, change-the-route-ink,
  work-offline-and-reuse-the-cache. first-map also says `--style takes a TOML theme` (first-map.md:157) without naming
  `examples/themes/` or write-a-theme.md.
- **Cause:** prose.
- **Fix:** End each tutorial with "Where next" links to the next tutorial plus two or three how-tos. On first use of each term or id,
  link the reference or explanation page.
- **Size:** S · **Area:** docs · **Related:** docs-glossary-in-place (for terms only).

## 5. The grid script is never given as a command, and its snippets depend on helpers the reader cannot see
- **Where:** paint-a-watercolour.md:43-48, 96, 175, 266, 371, 467, 578, 691; examples/tutorial_grids.py:92-189.
- **What's wrong:**
  - Every rung has a `console` block, but the grids do not. A reader has to work out
    `uv run python examples/tutorial_grids.py out/ --figure paper` from a sentence (the default figure is `nib`).
  - The quoted loops call `_layout`, `_desk`, `_paper`, `_disc`, `_letter`, `_labels` and `_composition_cell`. Only three of these are
    described (lines 46-48), and `_desk`, `_disc`, `_paper` and `_composition_cell` are never mentioned.
  - Each "Try changing ..." asks the reader to edit `examples/tutorial_grids.py` in the clone. That dirties the working tree, and the
    script paints pinned images.
  - The helpers are explained before the first picture, which is reference detail in the opening of a tutorial.
  - The loops index `boxes[r][c]` and slice `out[y : y + ch, x : x + w]` two levels deep. That is a layout API the library lacks.
- **Cause:** prose and code. The missing feature is a public small-multiples/grid helper.
- **Fix:** Add a console block under each "Vary it" (`... --figure wash`). Move the helper note to just before the first grid, covering
  every helper. Suggest copying the script before editing it (`cp examples/tutorial_grids.py my_grids.py`). Consider a public
  `ink.grid(cells, labels)` helper.
- **Size:** S (docs) / M (helper) · **Area:** docs · **Related:** docs-variable-effect-grids. New evidence: the existing grids are hard to
  re-run and to modify.

## 6. The composition grid is not the composition rung, and its two variables barely show
- **Where:** paint-a-watercolour.md:604-606 vs 689-698; examples/composition.py:84-92 vs examples/tutorial_grids.py:313-330.
- **What's wrong:** The rung strokes in `PAINTERS_PIGMENTS["burnt_sienna"]` with wash body 0.6. The grid uses the brush's own blue ink
  (`stroke_hex` from `RIV1-a`) with body 0.9, so the grid shows a different picture. The alt text even calls the stroke "dark blue". In
  the rendered grid-composition.webp, the three seeds are hard to tell apart and the "on" row's backing wash is barely visible. The
  prose also says the script "gives it none" (`ground`), but the script passes a zero `dark2` array to a field called `dark`, not
  `ground`.
- **Cause:** code and prose.
- **Fix:** Paint the grid with the rung's own stroke pigment and body. Use a darker wash, or a name crossing the stroke, so the backing
  wash visibly matters. Pick seeds that differ visibly. Use one word, `dark` or `ground`, on both sides.
- **Size:** S · **Area:** docs · **Related:** docs-variable-effect-grids.

## 7. The map stages leak cache internals and an unexplained positional `None`; the chain is copied in the CLI
- **Where:** first-map.md:88-94, 102-111; examples/route_map.py:65-71; src/pyntpot/maps/cli.py:82-86.
- **What's wrong:** `paint(basemap, style, cache.plates_dir(cache.key(route, features, elevation)))` makes the reader compute a cache key
  by hand and pass the providers a second time. `letter(plates, basemap, None, style)` has a positional `None` (the annotations), and
  the four-stage prose list never mentions it. The CLI repeats exactly these five lines, which suggests the library is missing a
  one-call path.
- **Cause:** a missing library feature, plus prose.
- **Fix:** Short term: write `letter(plates, basemap, annotations=None, style=style)` if the signature allows it, and say "no
  annotations; see letter-your-own-landmarks". Library: `cache.plates_dir_for(route, features, elevation)` or `paint(basemap, style,
  cache)`, and a `render_map(track, cache, features, elevation, style, annotations=None) -> Image` that both the CLI and the example use.
- **Size:** M · **Area:** maps · **Related:** maps-public-provider-protocols (adjacent), cli-wider-commands (the CLI would share it).

## 8. Names and numbering disagree between pages
- **Where:** paint-a-watercolour.md:719-720 says First map paints "a route round Keswick", but first-map.md and tutorials/index.md:9 say
  Ambleside. examples/route_map.py:1 calls itself "Rung 8 of the tutorial", but the watercolour tutorial has seven rungs and first-map is
  a separate tutorial. tutorials/index.md:8 says "in seven steps", while the page calls them "rungs". README.md:40 says "Each picture
  is one rung of the tutorial", but the 8th thumbnail (place_card) is not a rung.
- **Cause:** prose.
- **Fix:** Change "Keswick" to "Ambleside" in Where next. Drop "Rung 8" from the route_map docstring. Use one word for the units
  (step or rung) and define it once.
- **Size:** S · **Area:** docs.

## 9. Following the tutorial leaves untracked output in the clone
- **Where:** paint-a-watercolour.md:39 ("run every command from the top directory"), first-map.md:33-40, 152; .gitignore (no `out/`,
  `ambleside/`, `cache/`).
- **What's wrong:** Every command writes `out/`, and first-map adds `ambleside/` (with painted plates) and `cache/` at the repo root.
  None of these is ignored, so `git status` fills up, and a contributor who learned this way may commit them. first-map.md:39-40 even
  says the copy is there to "keep them out of the repository", but it is in the repository's directory.
- **Cause:** prose and build config.
- **Fix:** Ignore `/out/`, `/cache/` and `/ambleside/` in .gitignore, or have the tutorial write under a directory that is already
  ignored. State this once in "Before you begin".
- **Size:** S · **Area:** docs.

## 10. Positional magic numbers, and a granulation value that changes silently between rungs
- **Where:** wash.py:52 `wash(disc, sheet, 0.6, 0.3)` (explained only after the code, at md:160); brush_stroke.py:52 and nib_line.py:58
  `brush_from_id(id, w, 1.0, BrushStyle())`, where the `1.0` (`scale`, render px per display px) is never explained; lettering.py:46
  and composition.py:62 `GRAN_PX = 3.0` against 8.0 in rungs 1-5 and 6.0 in the grids, with no word on why; `0.3 * min(W, H)` disc
  maths repeated in three scripts.
- **What's wrong:** A copier cannot tell which numbers are artistic choices and which are plumbing.
- **Cause:** code.
- **Fix:** Use the keyword names the signatures already have (`wash(disc, sheet, base=0.6, pool=0.3)`,
  `brush_from_id("RIV1-a", width_display_px=6.0, scale=1.0, style=BrushStyle())`). Give `scale` a default of 1.0 in the library.
  Comment `GRAN_PX` where it changes. Add a public `disc_mask(h, w, cx, cy, r)` or keep one helper.
- **Size:** S · **Area:** ink · **Related:** ink-public-wash-options, docs-examples-review (#63).

## 11. Rung 2 teaches the map-role pigment `"water"` for a plain picture; rung 4 then brings in a second registry
- **Where:** wash.py:54, composition.py:114, README.md:118, paint-a-watercolour.md:133-134 vs 312-316 and 373-377.
- **What's wrong:** The first wash of the "no maps yet" tutorial is coloured `PIGMENTS["water"]`, a map-role key. Two rungs later the
  reader learns that painters' colours live in `PAINTERS_PIGMENTS` plus `PAINTERS_TRANSPARENCY`, and the page has to explain why there
  are two tables (md:373-377). Each layer is a three-step lookup (`rgb(TABLE[key]), TRANSPARENCY_TABLE[key]`).
- **Cause:** a missing library feature, plus code.
- **Fix:** Library: see the note. Docs, now: use `PAINTERS_PIGMENTS["cerulean"]` from rung 2 on, and in the README, so map-role
  pigments first appear in First map.
- **Size:** S (docs) / M (lib) · **Area:** ink · **Related:** ink-one-pigment-registry. New evidence: the very first wash in the README
  and in the tutorial uses a map-role key, and the tutorial spends a paragraph on the two-table split.

## 12. Brush ids are opaque codes, and the script docstring contradicts the glossary
- **Where:** brush_stroke.py:3-5 ("`RIV1-a` (a wet river brush) or `TRK4-d` (a dry track brush)"), paint-a-watercolour.md:213-215,
  419-420 ("Row 6 of the brush sheet is a pen, so `MAJ6-e`"); GLOSSARY.md:13 ("opaque cell name; `ink` never reads the prefix as a
  feature class").
- **What's wrong:** The reader has to memorise `MAJ6-e` to get a pen. The docstring gives the prefixes a map meaning ("river", "track")
  that the glossary forbids. The page does not link to reference/brushes.md.
- **Cause:** terminology, plus a missing library feature (no named brushes).
- **Fix:** Remove "river/track" from the docstring and describe the cells by treatment (wet round, dry). Link brushes.md on first use.
  Consider readable aliases such as `PEN = "MAJ6-e"`.
- **Size:** S · **Area:** ink/docs · **Related:** docs-brush-id-gallery, ink-data-driven-brushes-and-pigments.

## 13. The pen rung uses one nib in its script and a different one in its grid
- **Where:** paint-a-watercolour.md:409-495; examples/nib_line.py vs tutorial_grids.py:252-264.
- **What's wrong:** The rung script draws with an `ink` brush-sheet pen (`MAJ6-e`) through `stamp`. The grid varies `NibStyle`
  `label_pen_angle_deg` and `label_pen_thin` through `letters`' `nib_plate` and the hand, which belong to the next rung, as the page
  admits ("It uses the next rung's hand early"). The angle the prose explains is not a parameter of the script. The spiral result is
  also described as showing "no visible difference", so the rung's own picture shows nothing about the nib.
- **Cause:** code and docs structure.
- **Fix:** Either make the rung script draw a straight stroke at several directions with a nib whose angle can be set, or move the nib
  grid to the lettering rung and give rung 5 a grid over `MAJ6-*` widths. Say plainly that there are two pens: the ink pen brush and
  the letters nib.
- **Size:** M · **Area:** docs (letters/ink) · **Related:** letters-nib-follows-writing-line (adjacent).

## 14. Painter's terms are used but not in the glossary, and "wash" means two things on one page
- **Where:** GLOSSARY.md (no rung, accumulator, tooth, foxing, granulation, body, pool, glaze/glazing, Kubelka-Munk, backing wash);
  docs/reference/glossary.md (a 3-line pointer to GitHub); docs/index.md:23 ("gives the name of each thing in the studio");
  paint-a-watercolour.md:489, 591, 693-698 (`Setting(..., wash=False)` vs the `wash()` function); `ground` (prose) vs `NibSurface.dark`.
- **What's wrong:** The tutorial's core vocabulary is not in the one canonical list. The site's glossary page sends the reader
  off-site. `Setting.wash` (the backing wash) shares a name with the rung-2 function `wash`, so `wash=False` reads as "no wash was
  laid".
- **Cause:** terminology.
- **Fix:** Add the painter's terms to GLOSSARY.md. Render the glossary on the site. Rename `Setting.wash` to `backing_wash` (an ADR,
  because it is a public API). Use `dark` or `ground`, not both.
- **Size:** S (glossary) / M (rename) · **Area:** docs/letters · **Related:** docs-glossary-in-place. New evidence: the site glossary
  page has no content at all, and `Setting.wash` collides with `wash`.

## 15. One 720-line page, with explanation woven into every rung
- **Where:** paint-a-watercolour.md overall; 18-26, 43-48, 312-321, 693-698.
- **What's wrong:** There are seven rungs and seven grids in one page. Each rung has "how the engine models it" explanation (the
  transparency definition, Kubelka-Munk, the backing-wash mechanism) and helper-function reference before any action. A newcomer's
  "do this, see that" path is about 30% of the text. A short first win is far down the page.
- **Cause:** prose (Diátaxis mode mixing).
- **Fix:** Keep one or two sentences of "why" per rung and link the explanation pages for the rest. Consider one page per rung (or
  paper+wash, brush+pen, pigments, lettering+composition), with "Vary it" marked optional.
- **Size:** M · **Area:** docs.

## 16. README → tutorial has a hidden fork for pip users
- **Where:** README.md:49-61, 65-71, 76-77; paint-a-watercolour.md:28-37; first-map.md:21-24.
- **What's wrong:** The README says `pip install pyntpot`, then sends readers to a tutorial that needs `git clone` and `uv sync`, because
  `examples/` and `tests/fixtures/ambleside` are not in the wheel. The README CLI quick start uses `route.gpx`, which a new user does
  not have, and does not mention the bundled Ambleside track.
- **Cause:** prose (and packaging).
- **Fix:** Say "to follow the tutorials, clone the repo" next to the install block. Point the CLI quick start at the first-map tutorial
  for a ready-made track. Optionally ship the Ambleside sample as package data, or add a `pyntpot sample` command (cli-wider-commands).
- **Size:** S · **Area:** docs · **Related:** cli-wider-commands.

## 17. The first map paints for 30-60 s in silence
- **Where:** examples/route_map.py:65-75; first-map.md:59.
- **What's wrong:** At INFO level nothing is logged until "wrote". On my run that was 28 s of silence; the docs say about a minute. A
  newcomer may think it has hung. With a real track the first run also fetches from rate-limited servers, and still logs nothing.
- **Cause:** code (library logging).
- **Fix:** Log one INFO line per stage in `fetch`, `paint`, `letter` and `compose` (cache hit or miss, plate n of m).
- **Size:** S · **Area:** maps.

## 18. "Same pixels as the pictures on this page" over-promises
- **Where:** paint-a-watercolour.md:40-41; first-map.md:63.
- **What's wrong:** The page images are downscaled webp: route-map.webp is 900x640, but the script writes 1800x1281. CLAUDE.md says pixel
  parity is exact only on the pinning machine. "It is the picture at the top of this page" invites a pixel comparison that fails.
- **Cause:** prose.
- **Fix:** Say "the same picture (the page shows it smaller)", and drop the "same pixels" claim.
- **Size:** S · **Area:** docs.

## 19. The default map has washes on only part of the card, with lines running out over bare paper, and the prose does not prepare the reader
- **Where:** docs/images/tutorials/route-map.webp; first-map.md:115-125.
- **What's wrong:** The land cover covers a ragged blob round the route, while rivers and roads run on to the card edge over bare
  paper. Rydal Water is unnamed. "Rothay" is lettered twice, once at low contrast on the river. The prose says only "The land is
  washed, not filled", so a reader may think their run is broken.
- **Cause:** prose (and possibly the default land-cover margin or theme).
- **Fix:** Add a "What to notice" line explaining the washed extent (the land-cover fetch margin), or widen the default. Check the
  double "Rothay".
- **Size:** S (prose) / M (default) · **Area:** maps/docs · **Related:** maps-cover-layering-order; docs/issues/maps-lettering-names-under-strokes-and-lakes.md.

---
Count: 19 findings.
