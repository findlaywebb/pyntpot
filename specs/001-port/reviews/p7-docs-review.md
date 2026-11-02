# P7 docs review: `origin/main...p7-docs-release` (head c1d8597)

Reviewer: fresh-context, sceptical. Scope: README.md, docs/index.md, docs/gallery.md,
docs/tutorials/**, docs/how-to/**, docs/reference/**, docs/explanation/** (the three new
essays) and the examples they quote.

## Verdict

**No blockers. Fix the six majors before PR 2 merges.** The docs are accurate where it
counts most. I ran every tutorial and Painting with Python command, the first-map
script and `pyntpot map` offline on a copy of the Keswick fixture (proxy pointed at
127.0.0.1:9), and the how-to scripts. All of them work and print the log lines the pages
show. The links and anchors resolve. `tests/architecture` is green and the dash gate is
clean.

Four kinds of problem remain:

- **Two false claims about behaviour:** the route "casing", and a "Try changing" step
  that draws a broken figure.
- **A README Python quick start that a pip reader cannot run.**
- **Repeated misuse of "sheet" as paper.** This is the first trap the voice guide names.
- **A confusing download step in the first-map tutorial.**

## How I checked

- Ran `examples/{paper,wash,brush_stroke,pigments,nib_line,lettering,composition}.py out/`
  (5 s in total), plus `curves.py` (each figure), `kaleidoscope`, `fern`, `gasket`,
  `derwentwater`, `svg_drawing` and `how_to_own_shapes`. All wrote the files the pages
  name.
- Ran `route_map.py keswick/track.gpx keswick/ out/ you@example.org` on a copy of
  `tests/fixtures/keswick` with the network blocked. It took 60 s and sent no request.
  `pyntpot map ... --cache keswick/` then printed `plates in ... are current, nothing
  repainted` and finished in 4 s. `how_to_route_ink.py` behaved the same way.
- Grepped every error message the "When it goes wrong" lists quote. All exist in `src/`
  except the third-party ones. I reproduced the five theme errors in
  `write-a-theme.md:101-115` exactly.
- Wrote a link and anchor checker over the README and the user docs, which resolves
  absolute repo URLs to local paths. It found 0 missing.

---

## Blocker

None.

## Major

### M1. The route "casing" is documented but nothing paints it
- **Where:** `docs/how-to/write-a-theme.md:65-68` ("lays the route in black with a cream
  casing so that it still stands out") and `:86-88` ("a wide magenta route with a cream
  casing"). Also `docs/reference/style-fields.md:278` (`effect`: "casing, glow, shadow,
  blend and adaptive percentage").
- **Evidence:** `RouteInk.effect` (`src/pyntpot/maps/style_groups.py:256`) is never
  read. `grep -rn "casing\|\.effect" src/pyntpot` finds only the field itself. The
  route drawer (`maps/compose.py:68-85`) reads `ink.style`, `ink.colour` and `ink.px`
  only. The pen-and-ink theme's `casing_px = 1.6` therefore changes nothing on the card.
- **Fix:**
  - Delete the casing claims from both theme descriptions.
  - In `style-fields.md`, mark `effect` as a field with no reader and add it to "Fields
    with no reader" (`:336-338`), next to `hillshade_opacity` and `pick_places`.
  - Optionally, file `docs/features/maps-route-casing.md`.
  - If the casing was meant to come from the example themes, drop the `effect` edits from
    `examples/themes/{pen-and-ink,bold}.toml`, so a reader does not copy settings that do
    nothing.

### M2. The rose's "Try changing" step draws a broken rose
- **Where:** `docs/tutorials/painting-with-python/curves.md` "Try changing": "Change the
  factor 5 in `rose` to 4 for eight petals: an even factor doubles the petals."
- **Evidence:** `examples/curves.py:97` stops the rose at `t_end = np.pi`. With
  `cos(4 t)` over [0, π], the tips fall at 0°, 90°, 180°, 225° and 315° only (checked
  numerically). That is three petals missing and two halves, not eight. The page's own
  sentence that "the second half of a turn would only draw the same petals again" holds
  only for odd factors.
- **Fix:** add "and change the rose's `np.pi` in `FIGURES` to `2 * np.pi`", or choose an
  odd factor (7 gives seven petals).

### M3. The README's Python quick start does not run as shown
- **Where:** `README.md:79-108`.
- **Evidence:** the block is `wash.py` "after its imports". It uses `np`, `Path`,
  `Sheet`, `Canvas`, `paper_plate`, `PaperStyle`, `wash`, `composite`, `rgb`, `PIGMENTS`,
  `save_image` and `logger`, none of which it imports. It also defines `main` but never
  calls it. A reader who has just run `pip install pyntpot` has no `examples/` directory
  to fall back on, because the examples are not in the wheel. The plan wanted a quick
  start, and this is a fragment.
- **Fix:** quote `wash.py` verbatim from `import numpy as np` / `from pyntpot.ink import
  (...)` through `main`. That is still one verbatim substring, so `test_readme.py`'s pin
  holds as long as the lines are contiguous. Then add one line in a second block:
  `main(Path("out"))` (or `python -c`). Alternatively, say plainly that it needs a
  checkout: "from a clone: `uv run python examples/wash.py out/`".

### M4. "sheet" is used for the paper on reader pages
The voice guide's first trap (`CONTRIBUTING.md` "Writing docs"; `GLOSSARY.md`: sheet is
"the paper's noise fields") is broken in these places:
- `README.md:26` "stretches a sheet of paper".
- `docs/index.md:13` "from a sheet of paper".
- `docs/tutorials/paint-a-watercolour.md:4` "stretched a sheet of paper"; `:63` "as if
  the sheet had been handled"; `:71` "another sheet of the same stock". Line 71 is worst,
  because it comes straight after `:36` has defined `Sheet` as the noise fields.
- `docs/tutorials/paint-a-watercolour.md:369` heading "Compose the sheet". The same title
  appears in `docs/tutorials/index.md:7` and in the README anchor `#compose-the-sheet`
  (`README.md:48`). The plan's P7.5 prescribed this title, and
  `tests/architecture/test_tutorials.py:28` pins it.
- `docs/tutorials/painting-with-python/fractals.md:4` "fill a whole sheet".
- `docs/tutorials/painting-with-python/pictures.md:32` "`inside` is the sheet less its
  margin".
- `docs/tutorials/painting-with-python/vector-drawing.md:61` heading "Fit it to the
  sheet"; `:64` "88 per cent of the sheet's width".
- Alt text: "A sheet of cream paper..." at `README.md:47`, `docs/tutorials/paint-a-watercolour.md:32`,
  `docs/gallery.md:9` and `:255`; "on one sheet of cream paper" at `docs/gallery.md:247`.
  Fixing these needs the matching `docs_images` registry alt, if it is pinned.

**Fix:** use "paper", "picture" or "image" ("a piece of cream paper", "Compose the
picture", "Fit it to the paper"). Update the README anchor, the tutorials index and
`test_tutorials.py:28` together. Record in the run log that this departs from the plan's
title, because the plan contradicted its own voice guide.

### M5. The first-map tutorial downloads files the reader already has
- **Where:** `docs/tutorials/first-map.md:20-49`.
- **Evidence:** the tutorial's prerequisite (`paint-a-watercolour.md:16-23`) is
  `git clone` plus `uv sync`, and every command runs from the checkout. The four
  Keswick files are therefore already in `tests/fixtures/keswick/`, yet the page has
  the reader `curl` them from `raw.githubusercontent.com/.../main/`. That adds a network
  step to a page that claims none. It also pins `main` rather than the release tag; the
  plan said "the tag's tree". After a release, a change to the cache key on `main` would
  leave a reader on the released package with misnamed payloads.
- **Fix:** replace the step with `cp -r tests/fixtures/keswick keswick`, and say why the
  copy matters: the run writes `plates/` into the cache, which must not dirty the fixture.
  Keep the curl loop only as a note for readers without a clone, pointed at
  `v0.1.0`, and add the tutorial to P7.R's list of URLs to repoint at the tag.

### M6. The voice guide's "lettered text repeated as real text" rule is half-applied on the place cards, and the hero letters a shop
- **Where:**
  - `docs/gallery.md:209`: the Keswick card "letters Keswick, Portinscale, Crosthwaite,
    Derwent, Greta". It also letters Derwent Bridge, The Retro Zone, Lake Road Chapel,
    A5271 and "start" (visible in `docs/images/hero.webp`).
  - `docs/gallery.md:233`: the Y Fenni caption omits United Reformed Church, Borough
    Theatre, Methodist Church, Gavenny River, A40 and B4246.
  - `docs/tutorials/first-map.md:127-129` names "The Retro Zone", a shop, as a lettered
    landmark in the project's hero picture.
- **Fix:**
  - List every lettered name in each place caption, or write "among them" and say the
    list is partial.
  - Ask the maintainer whether a commercial premises should letter in the README hero. If
    not, add the shop to `pick_landmarks` or set `label_max` in a hero-only option of
    `place_card.py`. That is a separate decision from the docs.

## Minor

1. **Exit status is incomplete.** `docs/reference/cli.md:82-87` lists only 0 and 2.
   Every error in `map-from-the-command-line.md:69-76` (FileNotFoundError, FetchError,
   ValueError, ValidationError) leaves as a traceback with status 1; I verified
   `pyntpot map nothere.gpx ...` exits 1. Add the row "1: any other error; the traceback
   names it".
2. **"Nothing is resolved against the working directory."** At `docs/reference/cli.md:52`
   this is misleading: a relative `--cache` is relative to the working directory. Fix:
   "Relative paths are taken as given, relative to where you run the command."
3. **"Only compose reads it" is not quite true.** `docs/how-to/change-the-route-ink.md:45-46`
   says so of the route ink, but `paint` reads `style.route_ink().px` for the strand gap
   (`maps/pipeline.py:126`). The plates do not depend on it, which is the point being
   made. Fix: "No plate is painted from it: `paint` reads its width only to space the
   strands, and `compose` draws it."
4. **The log lines lack their prefix.** `change-the-route-ink.md:40-43` shows bare log
   lines, but the script prints `INFO:pyntpot.maps.pipeline:plates in ...` and
   `INFO:__main__:wrote ...` because it uses `basicConfig` without a format. Show the real
   lines, as the tutorial does.
5. **The tutorial's script length is understated.** `docs/tutorials/paint-a-watercolour.md:3-4`
   says "a script of about forty lines", but the scripts are 46 to 138 lines (`wc -l`).
   Fix: "a short script".
6. **The "strip of eight" shows seven.** `docs/gallery.md:251-281` has no
   `gallery/route-map.webp` in it, though the image appears under the command-line
   how-to at `:119-123`. Add it, or retitle the section.
7. **Gallery captions drop seeds.** Captions at `docs/gallery.md` (for example `:11`,
   `:49` and `:69`) omit the seed that the source pages give. The voice guide asks for
   "with the seed where the script takes one". Copy the seeds across.
8. **Caption style is inconsistent.** Captions are italic in the tutorials, the
   explanation and the README, but plain in `docs/how-to/*.md`, `curves.md`,
   `symmetry.md`, `fractals.md`, `pictures.md`, `vector-drawing.md` and
   `reference/{pigments,brushes}.md`. Pick one.
9. **The data-policy essay has no image.** `docs/explanation/data-policy.md` has none,
   but the voice guide says explanation pages show an image on every page. The credit
   corner of the Keswick card, cropped, would serve; it is also the subject of
   "The credit has to be readable".
10. **"effect" appears in the explanation index.** `docs/explanation/index.md:5` has
    "one figure for each effect", and "effect" is a trap word for what the engine does.
    Fix: "one figure for each behaviour", which is the essay's own word at
    `how-the-wash-works.md:6`.
11. **"sheet" is used bare for the brush sheet.** At `docs/explanation/the-hand-and-the-nib.md:103-104`,
    "the pen as the sheet makes it" means the brush sheet. Write "brush sheet".
12. **"toward" is an American form.** It appears at `pictures.md:43`, `style-fields.md:138`
    and in the svg-drawing alt text. Write "towards".
13. **Two pages contradict each other on granulation.**
    `docs/explanation/how-the-wash-works.md:82-85` says the public wash's grain "is its
    own noise field" and does not follow the paper. `docs/tutorials/painting-with-python/pictures.md:49-51`
    says scaling by `sheet.gran` makes "the pigment settle in the same hollows wherever it
    is laid", which is true only in the sense of one field reused. Fix: in `pictures.md`
    say "the same grain field everywhere", without "hollows".
14. **The route's colour has two names.** The hero alt (`README.md:7`) and
    `first-map.md:3` call it pink, while `map-from-the-command-line.md:41` and
    `change-the-route-ink.md:22` call it crimson. Use one; `#c22050` is crimson.
15. **Two links are relative to the source tree.** `write-a-theme.md:49`, `:54-55` and
    `vector-drawing.md:18` link `../../examples/...`. That works on GitHub but breaks
    once P7.14 builds a site with `examples/` outside `docs/`. Either use absolute GitHub
    URLs, or record the case for the P7.14 brief.
16. **Two snippets would fail as written.** `work-offline-and-reuse-the-cache.md:54-56`
    passes `track` to `fetch`, which needs a `Track` (`Track.from_gpx(...)`), not the GPX
    path the step mentions. `self-host-providers.md:58` calls `card.save("out/self-hosted.png")`,
    which fails if `out/` is missing. Add `Track.from_gpx` and `Path("out").mkdir(exist_ok=True)`.
17. **Place-card defects that are not parked.** In `docs/images/places/yr-wyddfa.webp`,
    "Afon Arddu" is clipped at the left edge and reads "fon Arddu". In the Oxford card the
    Cherwell is a large dark-blue blob. Neither has an issue file (the plan's parking
    rule). The run log already flags the Keswick hero's empty left paper and stray river
    strokes. File `docs/issues/maps-lettering-label-clipped-at-card-edge.md` and consider
    a tighter card or another hero.

## Plan conformance

- **Every brief's owner files landed** (P7.2 to P7.13), and every tasks line is ticked
  (`tasks.md:149-165`). P7.14 and P7.R are open, as planned.
- **Departures that the run log records, all of which need the maintainer's sign-off:**
  - P7.4's done line, a green two-OS golden run before the fan-out, was not met.
  - The docs-image pins were redesigned to PNG masters under `tests/golden/docs/`
    (ADR 0033 "provisional").
  - The gasket's cap was raised from 150 to 300 circles. `fractals.md` matches the code.
  - `svgelements` was dropped after the `ty` spike, so the vector page reads with the
    standard library. That is consistent.
- **Not delivered: the plan's focus-places line** (plan P7, "Focus places"): "Ambleside
  appears in lettering and non-map pieces". No example or doc letters Ambleside
  (`grep -rn Ambleside examples docs` finds nothing). The non-map pieces use Grasmere,
  Keswick, Skiddaw and Derwentwater, all in the Lake District. Skye, the Highlands and
  Eryri appear only on the cards. Fix: letter "Ambleside" in `lettering.py` or
  `composition.py` (this moves their pins), or record the decision.
- **P7.5 asked for the fixtures "from the tag's tree".** The page uses `main` (see M5).
- **P7.13's README order is exactly as prescribed.** The badges match the plan
  character for character.

## Place names

- Real UK names throughout. Welsh names hold on every Welsh card and page: Y Fenni,
  Afon Wysg, Llan-ffwyst, Yr Wyddfa, Garnedd Ugain, Crib Goch, Eryri.
- No English forms for Welsh places in reader docs or examples (I grepped for Snowdon,
  Abergavenny, Brecon, Crickhowell, Monmouth, Usk and Llanfoist).
- Lynmouth names appear nowhere in the reader docs.
- The only items to raise with the maintainer are the lettered shop "The Retro Zone"
  (M6) and the English "Gavenny River", which the maintainer has accepted.

## What is good

- **Accurate where readers will test it.** Every quoted error message exists verbatim.
  The CLI options, help text, defaults (`#c22050`, 5.4 px, the budgets of 100 and 1000,
  1.1 s pauses, 64 calls, 80 × 80 grid, 11 px credit) and the log lines are faithful.
  The theme errors reproduce exactly.
- **The tutorial works.** The seven rungs run in about 5 s from a fresh `out/`, and each
  quoted `main` is pinned verbatim by `test_tutorials.py`. The first map really paints
  offline from the cache in about a minute, and the rerun takes seconds, as the page
  says.
- **The explanation essays are honest about the simulation.**
  - `how-the-wash-works.md` says outright that edge darkening is "the mask minus a blur
    of itself", one width everywhere.
  - It says the granulation is its own noise field, not the paper's pits.
  - It says backruns, bleed, pigment separation and the shallow-water pass have no
    figure because the public `wash` cannot isolate them, and it links the feature note.
  - `the-hand-and-the-nib.md` is equally candid that the nib's angle is fixed to the
    page.
- **Designed gaps are stated as capability facts with feature-note links:** named themes,
  public provider protocols, SVG reading and wash options. No roadmap numbers appear.
- **The data policy and credit pages are careful and practical:**
  - They cover the Produced Work versus Derivative Database distinction.
  - They say who owes the credit when attribution is off.
  - They note that the budgets are per instance and are not a daily limit.
  - They give an actual WCAG contrast for the credit.
- **Each how-to opens by assuming the tutorial**, and its "When it goes wrong" list is
  keyed on what the reader actually sees.
- **No dashes, no hype, no "renders" or "generates"**, and alt text is present and
  descriptive on every image.
