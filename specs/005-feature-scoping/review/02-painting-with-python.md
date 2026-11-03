# Review 02: Painting with Python series

Slice: `docs/tutorials/painting-with-python/{index,curves,symmetry,fractals,pictures,vector-drawing}.md`,
`examples/{curves,kaleidoscope,fern,fern_family,trees,derwentwater,svg_drawing}.py`,
`examples/drawings/fell.svg`.

**Run check (no network).** All seven run from the repo root into a fresh, missing directory
and write the file the page names: fern 2.5 s, curves rose 1.7 s, kaleidoscope 1.8 s,
svg_drawing washes 1.6 s, derwentwater 3.2 s, fern_family 3.5 s, trees tree 6.8 s. All the
docs images the pages reference exist. No step is broken. The problems are in how well the
pages teach and in API friction.

Findings are ordered by impact.

---

## 1. The "tutorials" give the reader nothing to write: the snippets are fragments that cannot run

- **Where:** every page. Examples: `symmetry.md:90-95` (starts indented and uses `acc`, `brush`, `rng`, `_dense`, which are never shown), `curves.md:208-215` (uses `nib_px`, `paper`, `style`), `fractals.md:187-197` (uses `pad`, `ch`, `cw`, `densities`, `paint_fern`), `fractals.md:408-418`, `curves.md:133-159` (calls `_stack`, which is not shown).
- **What's wrong:** each page runs a finished script and then quotes pieces of it with the imports, constants and helpers left out. The reader never builds the picture: there is no "write this, run it, see this" loop, and no complete minimal program anywhere in the series. Someone who copies a block gets a `NameError`. The pages link the full script only on `vector-drawing.md` (the SVG), so a reader on the docs site cannot see the rest of the code. Read as a whole, the series is a guided code walkthrough (explanation), not a tutorial.
- **Cause:** prose (the structure).
- **Fix:** give each page one complete, short program near the top (imports, paper, one wash, one stroke, save) that the reader types and runs, then build on it step by step. Put a "full script on GitHub" link beside every "Painted by" caption. Alternatively, rename the series a walkthrough and move it out of `tutorials/`.
- **Size:** L. **Area:** docs. **Related:** docs-examples-review (#63). New evidence: no block in the series runs on its own, and only one page links its source.

## 2. Lettering a painting takes about 20 lines of setup, including a round trip through a file on disk

- **Where:** `examples/derwentwater.py:237-257` and `:294-296`. The page `pictures.md:66-71` covers it in four sentences and shows no code.
- **What's wrong:** to write one word on a picture, the script:
  1. builds a second `Canvas` at `NIB_SCALE`;
  2. makes a zeros array `dark2` for `NibSurface` (the page never says what it is);
  3. builds `NibGroups` from five style objects (`NibStyle(), face, hand_style, BrushStyle(), PaperStyle()`);
  4. calls `nib_plate`, which writes a `.webp` to disk and returns a path or `None`;
  5. re-opens the file with Pillow and downsizes it with LANCZOS;
  6. alpha-composites it by hand (`painted * (1 - alpha) + rgba[..., :3] * alpha`).

  A newcomer who wants their picture "with a name under it" cannot get there from the page, and the page's one sentence, "laid over the painting by its alpha", hides all of this.
- **Cause:** a missing library feature, plus prose that skips the step.
- **Fix:** add a public `letters` call that returns the nib plate as an RGBA array (with no file write needed) and optionally lays it over an RGB painting, with the supersampling built in. Until then, quote `_name` on `pictures.md` and explain `NibSurface`'s arguments.
- **Size:** M (library) / S (docs). **Area:** letters. **Related:** none. This is a new candidate feature.

## 3. Map vocabulary leaks into every non-map picture, so the paper setup is opaque boilerplate

- **Where:**
  - `Canvas(0, 0, w, h, w, h)` appears in all seven scripts (for example `curves.py:240` and `derwentwater.py:248`). Its docstring calls it "The card's metre box" (`src/pyntpot/ink/sheet.py:47`), and `paper_plate` reads only its `w` and `h` (`paper.py:47`).
  - `Sheet(h, w, ...)` is rows first, while `Canvas(..., w, h)` is width first.
  - `paper_plate(sheet, canvas, style, w)` takes a `display_px` that is always the width.
  - `brush_from_id(id, width_display_px, 1.0, BrushStyle())`: the docstring says "One class's brush", `scale` is "render pixels per display pixel" and is always `1.0`, and the returned ink hex is mostly thrown away as `_`.
  - Pigments named by map role (`wetland`, `relief`, `rock`, `heath`) paint a lake view (`pictures.md:37-41`), and the curves FIGURES table washes a Lissajous figure in `water`.
- **What's wrong:** a newcomer making a non-map picture has to pass six numbers whose meaning (a metre box, display pixels against render pixels, a feature class) belongs to the maps side. The four-line paper setup (Sheet, Canvas, PaperStyle, paper_plate) is copied into every script. "Display pixels", "render pixels" and "card" are glossary terms for maps, and these pages never explain them.
- **Cause:** a missing library feature (no blank-paper entry point) and terminology.
- **Fix:** add a `paper(w, h, seed, style=...)` (or `Sheet.blank`) that returns the sheet and the paper plate. Give `brush_from_id`'s `scale` a default of 1.0 and make it keyword-only. Choose one axis order for `Sheet` and `Canvas`. Have the pages use painter's pigments for pictures.
- **Size:** M. **Area:** ink. **Related:** ink-one-pigment-registry, for the pigment half. The Canvas, Sheet and brush_from_id points are new evidence.

## 4. Pigment handling forces hand-rolled lookups, merges and blends

- **Where:**
  - `curves.py:148-153` (`_stack`) and `trees.py:339-344` (`_stack` again);
  - `curves.py:186-193` (`_mixed` interpolates RGB and transparency by hand between three painter's pigments);
  - `svg_drawing.py:100-101` (merges `{**PIGMENTS, **PAINTERS_PIGMENTS}` and the two transparency tables) and `:187-190` (`_nearest` picks a pigment by hex);
  - `fern.py:141-158` (`rgb(PIGMENTS["wood"]), TRANSPARENCY["wood"]` written four times);
  - `curves.py:201` (a literal transparency `0.22` in place of the table's value).
- **What's wrong:** every script carries its own adapter from a pigment name to a `PigmentLayer`, and that adapter looks different in each one. Blending two pigments and finding the nearest pigment to a colour are reinvented as one-off helpers.
- **Cause:** a missing library feature.
- **Fix:** covered by the registry note. Add to it: a `Pigment.mix(other, t)` (or a blend along a stroke) and a `nearest_pigment(hex)`, both of which these examples need.
- **Size:** M. **Area:** ink. **Related:** ink-one-pigment-registry. New evidence: blending and nearest-by-hex both appear in this series as ad-hoc code. Also ink-data-driven-brushes-and-pigments.

## 5. The series' order disagrees with itself, and the first page is the hardest

- **Where:**
  - `index.md:5-9` lists Curves, Symmetry, Fractals, **Pictures, Vector drawing**;
  - `mkdocs.yml:80-84` orders them Curves, Symmetry, Fractals, **Vector drawing, Pictures**;
  - `pictures.md:80` says "The next page, Vector drawing". No other page has a "next" link.
- **What's wrong:** a reader following the nav goes Vector drawing → Pictures and is then sent back to Vector drawing. The progression is also inverted:
  - Curves comes first but brings in the most at once: brush ids, `stamp`, `wprof`, painter's pigments, Kubelka-Munk, `ink_density`, mgrid "deepen" maths, and per-petal drift.
  - Within Curves the rose is the most complex figure and is shown first, while the simplest (Lissajous: one wash and one pen line) comes last.
  - Symmetry, which is one wash per pigment plus a pen, would be the gentler first page.
- **Cause:** prose.
- **Fix:** pick one order in the index and the nav, add a "Next:" line to every page, and order from simplest to richest: Symmetry or Lissajous first, the rose and spirograph later, lettering (Pictures) last.
- **Size:** S. **Area:** docs. **Related:** none.

## 6. Pages point at earlier lessons by names that don't exist, and link nothing

- **Where:**
  - `curves.md:203` "as in the nib line rung";
  - `pictures.md:68` "the lettering rung again";
  - `vector-drawing.md:76` "as the rungs handed it a disc";
  - `fractals.md:323` "a wet brush of the brush sheet (`RIV2-a`)";
  - the `trees.py:13-19` docstring: "the brush sheet's row 2", "row 6", "row 1".
- **What's wrong:** the rungs of `paint-a-watercolour.md` are titled "Take up the pen" and "Letter a name", so "nib line rung" and "lettering rung" match nothing. No page in the series links back to a rung, to `docs/reference/brushes.md`, to `docs/reference/pigments.md` or to `GLOSSARY.md`. `index.md:3` says you need only the first tutorial, but the reader has to recall its details unaided.
- **Cause:** prose.
- **Fix:** use the rungs' real titles as links (`../paint-a-watercolour.md#take-up-the-pen`). Link each brush id to the brushes reference and each pigment to the pigments reference on first use.
- **Size:** S. **Area:** docs. **Related:** docs-glossary-in-place.

## 7. Core painting terms are missing from GLOSSARY.md, and one wash parameter has three names

- **Where:**
  - Terms used across the series with no glossary entry: *coverage mask* (every page), *accumulator* (`curves.md:204`), *granulation* (`pictures.md:50`), *pool* (`pictures.md:34`), *tooth* (`curves.md:205`), *glaze* / Kubelka-Munk (`curves.md:131`, `fractals.md:108`), *dab* (`fractals.md:111`), *rung*. `GLOSSARY.md` has none of these strings.
  - The first positional float of `wash` is `base` in the API (`ink/wash.py:122`, "density of the flat body"), `crest` in `derwentwater.py:186-190` and `pictures.md:34`, and `WASH_BODY` in `svg_drawing.py:88`.
  - `_cover` means a polygon mask in `curves.py:130` and `kaleidoscope.py:127` but a saturating count in `fern.py:102`.
- **What's wrong:** CLAUDE.md requires one canonical name per concept, and these are the concepts the engine is built on. A reader meets "crest" and cannot connect it to `wash(base=...)`.
- **Cause:** terminology.
- **Fix:** add glossary rows for coverage (mask), accumulator, granulation, pool, tooth, glaze, dab and rung. Rename `crest` to `base` (or rename the parameter `body` everywhere). Pass `wash`'s floats by keyword in the examples (`wash(cover, sheet, base=0.55, pool=0.35)`). Rename the fern's `_cover` to `_saturate`.
- **Size:** S/M. **Area:** docs, ink. **Related:** docs-glossary-in-place. New evidence: the terms are absent from the glossary, not just unlinked.

## 8. pictures.md has two unmarked snippets, and one has already drifted from the code

- **Where:** `pictures.md:28-31` against `derwentwater.py:189`; `pictures.md:46-48`.
- **What's wrong:** the page shows `& inside)`, but the code says `& scene.inside)`, and the prose then explains `inside` as if it were a local. Neither block has a `<!-- from examples/derwentwater.py -->` marker, so `tests/architecture/test_tutorials.py` does not check them. These are the only two unmarked Python blocks in the series.
- **Cause:** prose and a gap in the test.
- **Fix:** add markers, make the first block verbatim, and consider having the test reject unmarked `python` blocks on tutorial pages.
- **Size:** S. **Area:** docs, tests.

## 9. vector-drawing.md shows no code at all

- **Where:** `vector-drawing.md` (the whole page). It names `CURVE_SEGMENTS`, `PENS` (in "Try it", line 119), `wash`, `stamp`, the nearest-pigment rule and the "washed around the shapes in front" occlusion, but quotes none of them. The same painting image appears twice (lines 12 and 106).
- **What's wrong:** this is the page most useful to a newcomer with their own art, and it is the only one with no code to copy. The occlusion trick (`svg_drawing.py:226-246`: subtract the eroded masks of nearer shapes, with `TUCK`) is the interesting idea, and the reader never sees it. "Give a stroke a new class and add a pen to PENS" asks the reader to edit a table they have not been shown.
- **Cause:** prose.
- **Fix:** quote `parse_path`'s dispatch, `_washes` and `PENS` under markers, and drop the duplicate image.
- **Size:** S/M. **Area:** docs. **Related:** ink-read-svg-drawings.

## 10. The brush width argument does not predict the width of the mark, so the examples carry fudge factors

- **Where:**
  - `svg_drawing.py:83-84`: `PEN_SHARE = 0.5`, "a brush's marks spread past its nominal width";
  - `curves.py:248` and `kaleidoscope.py:167`: `nib_px * size / SIZE + 1.0`;
  - `trees.py:246-250`: a width floor and per-stroke brushes.
- **What's wrong:** a newcomer who asks for a 3 px line gets one about twice as wide, and the only place this is written down is a constant's comment in one example. The `+ 1.0` on the nib width is never explained.
- **Cause:** a missing library feature and missing documentation.
- **Fix:** state in `brush_from_id`'s docstring and the brushes reference how the drawn width relates to `width_display_px` for wet, dry and nib rows. Alternatively, offer a "visible width" option. Then remove `PEN_SHARE` and `+1.0` from the examples, or explain them.
- **Size:** M. **Area:** ink. **Related:** docs-brush-id-gallery (a gallery at stated widths would show this).

## 11. Brush ids are chosen without a word on why

- **Where:** `RIV2-a`, `TRK3-a` (`curves.py:160, 204`), `MAJ6-e` (`curves.py:248`, `kaleidoscope.py:167`, `trees.py:319`), `RIV1-a` (`fern.py:116`), `TRK4-d` (`trees.py:308`, `svg_drawing.py:82`).
- **What's wrong:** `curves.md:232` suggests swapping `TRK3-a` for `RIV2-a` "for a line that does not run so dry", which is the only hint in the series that the row sets the treatment. The reader cannot pick a different brush.
- **Cause:** terminology and a missing gallery.
- **Fix:** on first use, gloss each id ("RIV2-a: row 2, a wet round; MAJ6-e: row 6, a narrow nib") and link to the brushes reference.
- **Size:** S. **Area:** docs. **Related:** docs-brush-id-gallery. New evidence: five ids are used across the series with no explanation.

## 12. kaleidoscope's `_dense` does nothing, yet the page quotes it

- **Where:** `kaleidoscope.py:137-143` and `:172`; `symmetry.md:94`.
- **What's wrong:** `stamp` already resamples every path evenly by arc length (`ink/stamp.py:44-57`, `_trace`). I stamped five of the motif's lines with and without `_dense(points, 1.0)` using the same generator, and the accumulators were identical (max difference 0.0). A newcomer learns a ritual that isn't needed and may think `svg_drawing.py` is wrong for leaving it out.
- **Cause:** code, and `stamp`'s docstring, which does not say that it resamples.
- **Fix:** delete `_dense` (the output is unchanged). Add "the path is resampled evenly; any spacing of points is fine" to `stamp`'s `pts` doc.
- **Size:** S. **Area:** docs, ink.

## 13. Drawing a stroke whose colour changes means cutting it into sixteen overlapping strokes

- **Where:** `curves.py:204-214` (`np.array_split(..., 16)`, the overlap `min(idx[-1] + 3, ...)`, one accumulator and one `ink_density` per piece); `curves.md:161-169`.
- **What's wrong:** `wprof` profiles width along a stroke, but nothing profiles colour or density. The workaround is the hardest code in the series, with its own magic numbers (16, +3, 0.55, 0.45), and the page presents it as technique when it is really a gap in the API.
- **Cause:** a missing library feature.
- **Fix:** add a density profile along a stroke (`dprof`, beside `wprof`) and/or a pigment blend along a stroke. At minimum, say on the page that this is a workaround.
- **Size:** M. **Area:** ink. **Related:** ink-one-pigment-registry (the blending half).

## 14. Copied code between examples, and helpers the library could own

- **Where:**
  - `fern_family.py:57-134` repeats `MAPS`, `PROBABILITIES`, `LEFT_LEAFLET`, `fern_points`, `_cover`, `_thicken` and `_count` from `fern.py`, rather than importing them.
  - The grid-of-cells loop (a window, a `Sheet` per cell, then pasting the densities) is written twice (`fern_family.py:174-185`, `trees.py:372-382`).
  - Polygon to coverage mask through Pillow is written three times (`curves.py:130`, `kaleidoscope.py:127`, `svg_drawing.py:217`), and `_disc` five times across `examples/`.
- **What's wrong:** the series cannot build progressively when each script starts from scratch, and every newcomer has to rediscover Pillow's polygon fill (and its odd-winding rule, which `curves.md:82-86` spends a paragraph on).
- **Cause:** code and a missing library feature.
- **Fix:** have `fern_family.py` import from `fern.py`. Consider public `ink` helpers for a polygon or disc coverage mask and for laying a grid of cells.
- **Size:** M. **Area:** ink, docs. **Related:** docs-examples-review (#63).

## 15. Settings held in positional tuples, with dead fields and unexplained numbers the prose glosses over

- **Where:**
  - `curves.py:111-119`: `FIGURES` 4-tuples, where the pigment and nib width are unused for two of the three figures (the comment admits this), and `_points` unpacks `_pigment, _width` only to drop them.
  - `derwentwater.py:79-89`: `HILLS` 5-tuples and `BANKS` 4-tuples.
  - `derwentwater.py:131`: the `_blobs` "spec" tuple.
  - `curves.py:202`: `_loops(points, 9, 222)` (222 is unexplained).
  - `trees.py:181-197`: 0.62, 0.78, 0.45, 0.8, 1.3, 0.1, 1.2, 0.88, 0.75–1.15.
- **What's wrong:** `fractals.md:230-233` describes the tree rule as "shorter by `ratio`, turned by `spread`", but the quoted `grow` scales the turn by 0.45 or 0.8 at the first two depths, jitters the length by 0.75–1.15 and narrows side children by 0.88. A reader who checks the prose against the code finds it doesn't match. The "Try it" edits ("add a sixth hill") require knowing what each tuple position means.
- **Cause:** code.
- **Fix:** use small frozen dataclasses (`Hill(pigment, ridge, swing, base, granulation)`), name the tree's factors, drop the unused `FIGURES` fields, and name the 222.
- **Size:** M. **Area:** docs. **Related:** docs-examples-review (#63). This gives it concrete instances.

## 16. ink_density needs a Brush, so scripts build brushes only to convert accumulators

- **Where:** `trees.py:318-324` (`wet` and `nib` are made only for `ink_density`, while `_lay` stamps with brushes sized per stroke) and `trees.py:332`.
- **What's wrong:** the reader cannot tell which brush properties `ink_density` reads, or whether passing a brush of a different width from the one that stamped matters.
- **Cause:** a missing library feature and missing documentation.
- **Fix:** document which `Brush` fields `ink_density` reads. If it needs only the treatment, let it take that, or have `stamp` return or carry it.
- **Size:** S/M. **Area:** ink.

## 17. The command-line options differ from script to script

- **Where:**
  - `--seed` exists on `fern.py`, `fern_family.py` and `trees.py`, but not on `curves.py`, `kaleidoscope.py`, `derwentwater.py` or `svg_drawing.py`;
  - `pictures.md:77` says "Change `SEED`", which means editing the source;
  - the default size is a named `SIZE` in some scripts and a literal `720` in `derwentwater.py:260,307` and `svg_drawing.py:271,313`;
  - trees uses a `SIZES` dict.
- **What's wrong:** a newcomer who has learned `--seed` on the fractals page finds it missing on the next one.
- **Cause:** code.
- **Fix:** give every script `--seed` and `--size`, each with a named default.
- **Size:** S. **Area:** docs (examples). **Related:** cli-wider-commands (loosely).

## 18. The Diátaxis modes are mixed inside the tutorials

- **Where:**
  - "What a painter does" and "How the engine models it" sections in `fractals.md` (lines 23, 134, 140, 220, 228, 376, 382);
  - `vector-drawing.md:8-10`, which discusses what pyntpot does not do and links a feature note (roadmap material in a tutorial);
  - `curves.md:47-58`, a maths explanation.
- **What's wrong:** explanation and roadmap material push out the doing. Combined with finding 1, the pages read as essays.
- **Cause:** prose.
- **Fix:** keep one or two lines of "why" in each step. Move the maths and the background on painters to an explanation page (say `explanation/curves-and-fractals.md`), and drop the feature-note link from the tutorial.
- **Size:** M. **Area:** docs.

## 19. An image sits under the wrong heading

- **Where:** `curves.md:100-104`.
- **What's wrong:** the spirograph image and its caption sit directly under "## Paint the rose with a brush". The rose image is at the top of the page, so a reader looking at the rose section sees the spirograph.
- **Cause:** prose.
- **Fix:** move it under "## Paint the spirograph with one long stroke" (line 161).
- **Size:** S. **Area:** docs.

## 20. Docstrings in the examples disagree with their code

- **Where:**
  - `fern_family.py:9-10` says the leaflet entries move "by up to 5 per cent". The code uses `uniform(0.94, 1.06)`, which is 6 per cent, and `fractals.md:145` says 6.
  - `derwentwater.py:8` says the colour "warms from `wetland` through `rock` and `relief` to `wood`". The hills are wetland, rock and relief, the banks are scrub and heath, and wood is only the trees.
  - `fern.py:11` says "The frond, the points that last took the 85 per cent map", but `frond` includes the stem map (`< LEFT_LEAFLET`), as `fractals.md:106` correctly says.
- **Cause:** code (the docstrings).
- **Fix:** correct the three docstrings.
- **Size:** S. **Area:** docs.

## 21. The ink-read-svg-drawings note is stale about the example

- **Where:** `docs/features/ink-read-svg-drawings.md` ("Why it is not a defect").
- **What's wrong:** the note says the tutorial "uses a third-party reader in the example script only". `svg_drawing.py` uses the standard library's `xml.etree` and its own `M/L/C/Z` parser, as `vector-drawing.md:8` says. The note also leaves out that the script hand-rolls nearest-pigment matching and the occlusion of nearer shapes, both of which a public reader would want to own.
- **Cause:** prose (the note).
- **Fix:** update the note's "What exists today" and "Why it is not a defect" sections.
- **Size:** S. **Area:** docs. **Related:** ink-read-svg-drawings.
