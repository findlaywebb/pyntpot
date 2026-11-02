# P7 research: what makes great READMEs, docs and guides, and what it means for pyntpot

Researched 2026-10-23, before P7 is cut into slices. Six research notes sit under
`research/p7/`, each with its case studies and sources:

1. `1-readmes.md`: 18 READMEs fetched raw (rich, textual, httpx, uv, ruff, FastAPI, Typer,
   Pydantic, polars, attrs, requests, Flask, prettymaps, vsketch, Pillow, matplotlib,
   manim) plus GitHub, makeareadme and Write the Docs guidance.
2. `2-docs-structure.md`: Diátaxis in practice (Django, NumPy, Canonical, Python core),
   its critics, Stripe, FastAPI, Pydantic, polars, SQLAlchemy, Rust; reference tooling;
   the docs-site question.
3. `3-visual-libraries.md`: matplotlib, sphinx-gallery, scikit-image, three.js, p5.js,
   Processing, manim, vsketch, prettymaps, cartopy, datashader, Hobbs, Stamen.
4. `4-tutorials.md`: Django polls, the Rust Book, FastAPI, Flask, Elm, Svelte, polars,
   Stripe quickstarts, Julia Evans, learning research (worked examples, fading,
   expertise reversal).
5. `5-release-surface.md`: PyPI rendering, metadata, badges, changelogs, the ODbL and
   OSMF attribution rules, 0.x policy, docs gates.
6. `6-identity-and-voice.md`: the core point distilled from the repo; Rough.js,
   Excalidraw, tldraw, xkcd mode, p5.js, Processing, Charm, Rich, Nature of Code,
   Ciechanowski, Stamen.

This note is the synthesis. It proposes; nothing here is decided until the maintainer
says so. The decisions are in section 4.

## 1. The core point

pyntpot paints the way a painter works. It does not lay a filter over a render: it lays
cream paper with tooth and foxing, floods washes that pool at their edges and granulate
into the paper, drags brushes that run dry and reload, glazes pigments by Kubelka-Munk,
and letters names with a nib. Three things set it apart:

- **It simulates the craft**, and every technique cites its source (`references.md`).
- **It is deterministic**: a painting that looks accidental comes out the same, byte for
  byte, from the same seed.
- **Maps are its first application, not the whole of it.** `ink` and `letters` paint
  anything; `maps` sits on top.

It is also polite to the commons: a contact string is required, provider limits are
kept, and the credit is lettered on the card.

Candidate lines (from notes 1, 5 and 6):

| Use | Candidate |
| --- | --- |
| Tagline, PyPI summary, GitHub description (plain, greppable) | "Hand-drawn watercolour and pen-and-ink painting for Python, with route maps." (current) |
| Same slot, verb-led alternative | "Paint hand-drawn watercolour and pen-and-ink images in Python, with route maps from OpenStreetMap." |
| README lede after the hero | "Lay a wash, pull a brush, letter a name." |
| README lede, alternative | "Pictures and maps painted the way a painter works: paper, wash, pen, then the names." |

## 2. The through-line: how the core point and style run through everything

Every source agreed on one rule, and it answers "weave the core point and styling
through it all":

**The pictures carry the style; the words stay plain.** Rough.js, Rich, Charm and Stamen
all put their identity into the product's own output, not into decorated prose. Where
projects style the words (Charm's jokes, handwriting fonts as body text) it dates fast
or hurts reading.

From that rule:

1. **Every image is painted by pyntpot, from a tested script.** The wordmark, the README
   hero, the gallery, the reference swatches, the explanation figures, the social preview.
   No stock images, no hand-made diagrams. Each caption names its script and seed
   ("Painted by `examples/wash.py`, seed 11"), which turns determinism into something a
   reader can check. A test fails when a docs image has no script that writes it.
2. **The wordmark is painted.** `examples/word.py` letters "pyntpot" on a washed disc
   (the paint pot in the name). It opens the README, and forms half of the social preview.
3. **The tutorial follows the painter's order of work**: stretch the paper, lay a wash,
   pull a brush, mix the pigments, take up the pen, letter a name, compose the sheet,
   paint a route. That is also the `ink -> letters -> maps` order, so the craft story
   and the architecture agree; the tutorial says so in one line.
4. **Explanation pages are short essays on the craft**, built one effect at a time from a
   single seed, as Ciechanowski and Stamen do: a flat wash, then edge darkening, then
   granulation, each step a figure, each ending on its `references.md` key.
5. **One recurring setting.** Lynmouth (Lyn, Heddon, Brendon, Watersmeet) for every map
   figure, as Stamen carried one London tile through every stage. Real UK names from
   `CONTRIBUTING.md` elsewhere.
6. **Style by page type.** More in the README, the tutorial and the explanation essays;
   little in how-to guides; none in reference beyond a swatch where a value is a colour
   or a brush (matplotlib's xkcd mode has a dry reference page, which is right).
7. **A one-page voice guide.** British English; no em or en dashes; glossary terms only;
   studio verbs ("paints", "lays a wash", "letters") over software verbs ("renders",
   "generates"); no hype words; designed gaps stated as capability facts. The trap
   list: "sheet" means the paper's noise fields, not paper; "canvas" is a pixel grid;
   "map" never appears in `ink` or `letters` docs; never "filter", "effect" or "shader",
   because the pitch rests on simulation and those words undo it.
8. **Stated values**, three short lines in the README: every image reproduces from its
   seed; every technique cites its source; data providers are asked politely and
   credited on the card.
9. **Accessibility.** Lettered text is always repeated as real text. Patrick Hand is for
   images, never body text. Alt text says what the picture shows or what changed
   ("the same disc wash, now with pigment pooled at its edge"). Images sit on opaque
   cream paper with a margin, which reads in light and dark mode alike.

## 3. Proposed shape of P7

### README

Order: wordmark and tagline; the hero route map with a provenance caption; the non-map
image beside it; few badges (PyPI version, Python versions, CI, licence, CodSpeed); what
it is in two short paragraphs, including what it does not do; stated values; a gallery
strip of the eight tutorial outputs, each linking to its page; install (`pip` and
`uv add`); quick start; crediting the data; documentation links; status (0.x policy);
licence. The "Develop" section moves to `CONTRIBUTING.md`; gates, ADRs, phases and
`CLAUDE.md` stay out.

**Quick start.** The outline's "three-line quick start" does not exist in Python: a map
takes seven calls and two providers. Two honest versions, each followed by its picture:

- A map, by the command line, in three lines:
  `pyntpot map route.gpx -o map.png --cache cache/ --contact you@example.org`.
- The engine, in Python: the `wash.py` disc in about eight lines, offline.

**Images on PyPI.** The README is the PyPI page. PyPI hosts no images and does not
resolve relative paths, and strips `<picture>`, so every image is an absolute raw URL
pinned to the `v0.1.0` tag, small (under 500 KB for the hero, under 60 KB per
thumbnail), with alt text. The 2.7 MB golden `map.png` is not the hero; a downscaled copy
from a tested script is.

### Docs tree

```
docs/
  index.md                 landing page: one painting, four signposted routes
  gallery.md               every image from examples/, captioned
  tutorials/
    index.md
    paint-a-watercolour.md rungs 1 to 7, one section per rung
    first-map.md           rung 8, the application
  how-to/                  only guides with a real task behind them (section 4, F)
  reference/
    ink.md letters.md maps.md   generated from the docstrings
    style-fields.md cli.md      generated, or pinned by a test
    cache-layout.md manifest.md hand-written, each pinned by a test
    pigments.md brushes.md      painted swatch sheets
    glossary.md
  explanation/
    how-the-wash-works.md the-hand-and-the-nib.md data-policy.md
    performance.md references.md
```

The maintainer records (`decisions/`, `issues/`, `features/`, `runbooks/`,
`architecture.md`) stay where they are but out of the reader's path.

**Each tutorial section has the same shape** (Flask, Elm, Rust Book): the finished
picture first; the command and the log line it prints; the script's `main` quoted
verbatim; "what to notice" (the pigment pooled inside the edge, the dry stroke breaking
on the tooth); one "try changing" line. First success is rung 1, offline, inside five
minutes.

**Keeping prose and code in step.** Tutorial code blocks are verbatim copies of script
regions under a marker comment; a test checks each block against its script, and that
every rung is quoted. Images are compared with a fresh run under `--golden-tolerance`.

**Reference is generated from the docstrings**, which are already the agent contract;
hand-writing a second copy would drift. A test checks that every public name appears
once. A docstring that reads badly when rendered is a docstring finding, not a reason to
rewrite it in the docs.

### Release surface

- PyPI trusted publisher created before the tag (a pending publisher; Q14 chose tag only
  for 0.0.x, so the two upload jobs on `v0.0.1` and `v0.0.2` failed as expected and must
  never be re-run).
- `publish.yml`: check the tag matches the version, run the gates before upload, pin the
  publish action, create the GitHub release from the changelog section.
- Metadata: classifiers (3.13, GIS, Artistic Software; no `License ::` classifier, which
  conflicts with the PEP 639 expression), `Documentation` and `Changelog` URLs.
- GitHub: description identical to the PyPI summary; topics craft-first (watercolour,
  pen-and-ink, hand-drawn, hand-lettering, generative-art) then maps; a painted
  1280 by 640 social preview.
- CHANGELOG 0.1.0 with a short summary for newcomers and compare links; `CITATION.cff`;
  a bug-report form.
- `docs/explanation/data-policy.md`: a map is an ODbL Produced Work; turning attribution
  off moves the duty to the caller; the cache and the exports are Derivative Databases
  if republished; the providers' usage limits.
- Status statement: on 0.x a minor release may break the API and a patch never does;
  painted pixels may change between minors.
- Docs gates: lychee for links (offline per PR, online weekly), `twine check --strict`,
  a test that README links are absolute, the README quick start copied from a tested
  example.
- The publisher setup goes in `docs/runbooks/release.md`, not `CONTRIBUTING.md`.

## 4. Decisions for the maintainer

Each has a recommendation. The big ones shape the slicing; the smaller ones have
defaults that the plan will use unless changed.

### The big ones

**A. A docs site, or plain Markdown on GitHub? (amends D13 if a site)**
GitHub strips all styling, so plain Markdown carries the voice and the pictures but not
the look. A site can carry the look, and here uniquely the theme can be painted by
pyntpot itself (paper texture, a pigment palette, brush-stroke rules, Patrick Hand for
display headings), at build time, from public API. A site also gives generated reference
and a strict build that fails on a broken link or a missing public name. Engines in
October 2026: Material for MkDocs is in maintenance mode (critical fixes end
5 May 2027); Zensical, from the same team, is at 0.0.71 with 0.1.0 due 5 November 2026
and supports mkdocstrings, which renders this repo's Markdown-style docstrings
correctly (Sphinx does not). Options:
1. A small Zensical site on GitHub Pages at 0.1, source kept as plain Markdown so it
   still reads on GitHub. **Recommended**, with the site setup as its own late slice so
   it can slip to 0.1.x without holding the release.
2. Keep D13: plain Markdown, reference generated by pdoc.
3. Plain Markdown at 0.1, site at 0.2.

**B. Tutorial shape.**
1. Two pages: `paint-a-watercolour.md` (rungs 1 to 7, one section each) and
   `first-map.md` (rung 8). **Recommended**: the rungs are short, and the outline's
   map-only tutorial would leave seven tested scripts unexplained.
2. Eight pages, one per rung (suits a site).

**C. Rung order.** Pigments (rung 5) come after the pen, which breaks the painter's
order. Move it to rung 4, before the nib (a docstring renumbering and the test list).
**Recommended.**

**D. Pin every docs image as a golden.** The ink rung tests check only size, mode and
"not one flat colour", so a rung can change visually and stay green. Making each
gallery image its own comparison baseline (three.js does this) closes the gap and keeps
the docs truthful. It widens what is pinned, so it needs an ADR alongside 0006 and 0025.
**Recommended.**

**E. How far the painted identity goes.**
1. Images only: wordmark, hero, gallery, swatch sheets, explanation figures, social
   preview.
2. Option 1 plus a painted site theme (paper texture, palette, brush rules, Patrick Hand
   display headings). **Recommended if A is a site.**
3. Option 2 plus lettered page-title images and section vignettes on every page. Not
   recommended: it starts to tip into decoration, and costs accessibility.

**F. The "East Lp" label.** The golden Lynmouth map letters the East Lyn twice, once
as "East Lyn" and once as "East Lp". (Corrected after the root cause: the route is not involved; see `docs/issues/maps-lettering-curved-name-window-and-flat-repeat.md`.) It is the
obvious hero image. Options: fix it before 0.1.0 (a code fix plus a golden
regeneration window), or file it and use a hero render that does not show it.
**Recommended: file it now under `docs/issues/` and fix it before 0.1.0**, as the hero is
the first thing anyone sees.

### The smaller calls

| | Question | Default |
| --- | --- | --- |
| G | Tagline and README lede | Keep the current tagline; lede "Lay a wash, pull a brush, letter a name." |
| H | Quick start | Command line (three lines) then the Python wash (about eight), each with its picture |
| I | How-to guides | Paint a map from your GPX with the command line; change the route's colour and width; work offline and reuse the cache; credit the map data; write a theme (starting from a copy of `default.toml`); self-host the providers; paint your own shapes with the engine |
| J | Provider protocols `Features` and `Elevation` are not public, so no guide can show writing a new provider | Keep them private at 0.1; the self-host guide covers the shipped providers only |
| K | Offline first map | Link the Lynmouth fixture files at the tag, so the first map paints from cache with no request |
| L | Reference swatch sheets for `PIGMENTS` and the brush ids | Yes: brush ids like `RIV1-a` mean nothing without a picture |
| M | Social preview and wordmark | Both painted by tested scripts (`word.py`, a new preview script) |
| N | `CITATION.cff`, bug-report form | Yes; a code of conduct only with a public contact address |
| O | Changelog tooling | Hand-written Keep a Changelog, no towncrier |

## 5. Corrections to the P7 outline in `plan.md`

- "Three-line quick start": true only for the command line (H).
- `first-map.md` alone is not the tutorial (B).
- `use-the-engine-without-maps` repeats rungs 1 to 7; reframe it as painting the
  reader's own shapes.
- `write-a-theme` must start from the packaged `default.toml`: `Style.from_toml` needs
  every group.
- "Set back from P10.R's 0.0.1 to 0.1.0": the tree is at 0.0.2.
- "Configure the PyPI trusted publisher (documented in CONTRIBUTING)": document it in
  `docs/runbooks/release.md`; it is not configured yet.
- Missing from the outline: the gallery and its pin test, the tutorial sync test, image
  hosting by absolute URL, a caption per image, the docs gates, the voice guide, the
  data-policy page's four duties, the status statement, the release surface outside the
  repo, and the `publish.yml` fixes.

## 6. Found along the way

- The "East Lp" double label on the golden map (F).
- The ink rung tests cannot see a visual change (D).
- The sdist and wheel carry no `tests/`, so the ODbL Overpass fixtures never reach PyPI;
  keep it so, and keep `docs/` out of the distributions too.
- The current packages pass `twine check --strict`.
- The GitHub repo has no topics, homepage or social preview.

## 7. Maintainer's answers, 2026-10-23

- A to F and the defaults G to O: accepted as recommended. F is fixed before 0.1.0.
- **New directive, places.** The docs, examples and tests focus on these places.
  Nature: the Lake District, the Highlands and Skye, Eryri (Welsh names are used:
  Eryri, not Snowdonia). Urban: Ambleside, Keswick, Oxford, St Ives.
- **New directive, non-map tutorials.** Beyond the eight rungs: more abstract pieces;
  Python making mathematical shapes, fractals and symmetries; drawing pictures; taking a
  vector drawing and painting it.
- **New directive, map styles.** Examples that restyle the map, so the docs are not
  limited to the default theme, which reflects the upstream project's taste.
- **Process.** Every decision for the maintainer is set out in the chat, not only in a
  file.

## 8. Open questions raised by the new directives

Facts behind them, checked 2026-10-23:

- The coordinate gate (`tests/architecture/test_coordinates.py`, D10) allows one box,
  Lynmouth, and every golden and map test reads the Lynmouth fixtures (about 3.5 MB of
  recorded provider payloads plus a track).
- `pyntpot.maps.svg_path.parse_path` reads back only the `M`/`L` paths pyntpot writes;
  there is no general SVG reader, public or private.
- The public `ink` names (`wash`, `stamp`, `Brush`, `brush_from_id`, `paper_plate`,
  `composite`, `PigmentLayer`) take numpy masks and point lists, which is enough to paint
  curves, fractals and symmetric figures from Python with no new API.
- The default theme's route inks are named `run`, `ride`, `swim` and `other`; `Style`
  covers paper, wash, brush, face, nib, hand, card, ribbon, cover, route, lettering and
  basemap groups.

Questions (Q-P1 to Q-P8) and recommendations are set out in the chat of 2026-10-23 and
recorded here with their answers once given.

**Parking rule** (maintainer, 2026-10-23): an idea that cannot be done in P7 is parked and
the feature it needs goes to `docs/features/`. Parked so far:
`ink-read-svg-drawings.md` (Q-P6 b), `maps-named-themes.md` (Q-P7 b),
`maps-public-provider-protocols.md` (default J).

**Blocker for Q-P1:** this session's network policy denies `overpass-api.de` and its
mirrors (OpenTopoData answers), so new place fixtures cannot be recorded here until the
host is allowed or the maintainer records them locally.

## 9. Maintainer's answers to Q-P1 to Q-P8, 2026-10-23

- **Q-P1** Maps for: Keswick and Derwentwater (the Lake District), Skye, Eryri around Yr
  Wyddfa, Oxford, and **Y Fenni** in place of St Ives. Ambleside
  appears in the lettering and non-map pieces. Each map's track follows public
  paths.
- **Q-P2** Lynmouth stays the test place for now, slated for retirement at a later point
  of stability (`docs/features/tests-retire-lynmouth.md`, post-port roadmap).
- **Q-P3** Widen the coordinate gate to one box per place, by ADR.
- **Q-P4** Welsh names for Welsh places (Eryri, Yr Wyddfa, Y Fenni) everywhere, including
  the CONTRIBUTING name list.
- **Q-P5** The "Painting with Python" set as recommended, except the fractal: the Koch
  snowflake is too stereotyped; a more beautiful fractal is open (Q-P9).
- **Q-P6** (a) at 0.1, a third-party SVG reader in the example only; (b) on the
  post-port roadmap.
- **Q-P7** (a) at 0.1, example theme files; (b) on the post-port roadmap.
- **Q-P8** All of it in 0.1.0; only the docs site may slip to 0.1.x.

**Welsh names on the cards** (maintainer, 2026-10-23): the Y Fenni card reads "Y Fenni",
not "Abergavenny"; the card's other names may be English or Welsh for now. Taken into
P7 as P7.3b (a style setting naming the tags lettering reads), so the parked note
`docs/features/maps-prefer-welsh-names.md` is deleted when P7.3b lands.

## 10. Maintainer feedback, round 1 (2026-10-24, after the overnight run)

Recorded as given; to be planned as a P7 revision round.

- **Route colour** looks too digital; go for a more maroon style.
- **Maps as hero images.** Many maps do not come across well: the routes are not iconic,
  and the styling is tuned to the maintainer's sports maps. As the docs' hero images they
  need to be more striking.
- **The main hero should be Ambleside**, showing more landscape.
- **Oxford** does not show the city well: more roads need drawing. The route should go
  along Queen's Lane and by the Radcliffe Camera, and through Christ Church on the return;
  out and back over Magdalen Bridge is good. Something odd happens with the Isis,
  perhaps the flood plain.
- **Image review.** Agents should review and critique every image.
- **The main tutorial** alternates between explaining concepts and the underlying
  engine; both are wanted, but together they read as incoherent.
- **The Python is a bit hard to follow**, partly from limits of the current code base,
  to address in future.
- **Show, not just tell.** Where the docs say ink or colour can change, show a grid of
  options made with a Python `for` loop.
- **The circle fractal** (the Apollonian gasket) does not work; reconsider which fractal.
- **The fern is the favourite image: keep it unchanged.**
- **Nature pieces** should lean into procedural generation: small random perturbations
  giving a varied family of outputs.
- **Some Python curve drawings** could swap the pen for the brush.
- **Some lettering** shows odd pixelation; perhaps double the grid density.
- **"Keswick"** lettering has an unexplained kink.
- **Landmarks worth calling out.** "The Retro Zone" (a shop) must not be a highlight.
  Agents should decide what is genuinely worth lettering at each place, for example the
  Angel Bakery and the Tŷ Melin bakery in Y Fenni; bridges and colleges in Oxford; the
  Moot Hall (the town hall) in Keswick.
- **Skye is missing its key feature: it is an island.** The map should show a large
  stretch of coastline, if not the whole island.

### 10.1 Decisions after round 1

The maintainer said the recommendations offered so far are good. Those were:

1. A showcase theme for the hero maps; the default theme stays as it is.
2. Ambleside hero route: the Loughrigg circuit, via Loughrigg Terrace and Rydal Water.
3. Maps: drop Keswick as a map, keep Skye, Yr Wyddfa and Y Fenni, rework Oxford.
4. Replace the gasket with a family of procedural trees. The fern image stays unchanged.
5. Tutorial rhythm: picture, what a painter does, how the engine models it, code, what
   to notice, then a `for`-loop variation grid.
6. Fixture size: the recorder stores fixtures minified, keeping only the fields and tags
   the code reads, without rounding coordinates. Existing fixtures are re-recorded, and
   goldens must come out byte-identical. This is folded into the revision round.
7. Any fern family is a separate new image; the existing fern is untouched.

### 10.2 Further feedback

- **Out of scope:** a command line for much more of the library, including theme
  cloning. Parked on the post-port roadmap (`docs/features/cli-wider-commands.md`).
- **In scope:** the SVG example shows the raw SVG and each step to the painting, so the
  reader sees what is gained and what changes.
- **Skye** at whole-island scale should be simplified further than 10 cm coordinates;
  proposed as a road trip with short journal notes ("Tuesday: Dunvegan Castle and the
  Coral Beaches"). **Each showcased map is a different theme or idea.**
- **Y Fenni food tour.** The maintainer added Bean & Bread, Rate of Rise and Shepherd's
  Ice Cream to the Angel Bakery and Tŷ Melin. The first four are in OpenStreetMap
  (checked 2026-10-24); Tŷ Melin is not.

### 10.3 Decisions, 2026-10-24 (later)

- Tŷ Melin: added by hand as a custom label, the docs' example of a curated entry.
- No town hall on the Y Fenni map: it is a food tour.
- Landmark fixes: both the curated callouts and the general ranking fix.
- Route style: candidate B, the wet pen in maroon.
- Skye: the whole island, through a wider fetch option; Yr Wyddfa may go a bit wider
  too.
- Journal notes, and one idea per showcased map: yes.
- (The two earlier "yes" answers were to the previous block: Skye simplified to its
  card's scale, and the journal notes and one-idea table as first proposed.)
- Paper: foxing off in the reference and explanation figures, and the paper's edge and
  foxing restyled in the library (warm, narrow, uneven edge; rust specks) in this round.

### 10.4 Orchestrator decisions after plan review 1, 2026-10-25

Settled on `reviews/p7v-plan-review-1.md` and written into the plan's P7.V section as
prescribed, not options:

- **The fern and the new paper (B1, S6).** The new paper is the default look:
  `PaperStyle.paper_edge: Literal["classic", "warm"] = "warm"`, not omitted from the
  digest (the default look changes, so the default digests move and are re-pinned).
  `"classic"` is today's code path exactly, with the same generator draws, and
  `examples/fern.py` passes it, so the fern stays byte-identical. Decision 1 now reads
  "`default.toml`'s settings are unchanged; its paper looks as decision 13 says". The
  maintainer is asked whether the fern should take the new paper instead; if yes,
  P7.V7b drops the fern's opt-out.
- **The paper's draws (S5).** The two existing `sheet.noise` draws stay, in order and at
  the same scales; the specks come from `sheet.gran`, and the edge is modulated by the
  existing `noise(26, 2)` field.
- **Skye (B2, S8).** The route is a one-way island tour on public roads, Kyleakin to
  Portree by Broadford, Armadale, Sligachan, the Fairy Pools, Carbost, Dunvegan, Neist
  Point, Uig, Staffin and the Storr (240 to 320 km). Margins are explicit (C1 not
  taken), sized so the card box lies inside the fetched box; `test_places.py` asserts
  it for Skye and Yr Wyddfa. `make_track.py` gains `--step-m`. The size estimate is
  about 10 MB after trimming, at the budget, with a 25 m simplification as the one
  fallback.
- **The cache key (B3).** The land-cover margin joins the key only when non-default;
  the default key stays byte-identical and pinned. The CLI, `place_card.py` and
  `test_places.py` pass the margins through.
- **Tags (B4, C2).** `KEPT_TAG_KEYS` is the grep's result (`--include='*.py'`) plus
  `wikidata`, `wikipedia`, `heritage`, `listed_status`, `shop`, `brand` and
  `brand:wikidata`; P7.V5 re-records nothing. P7.V1 trims Lynmouth and Yr Wyddfa only;
  the recorder trims every later recording.
- **Painter's pigments (B7).** A separate `PAINTERS_PIGMENTS` and
  `PAINTERS_TRANSPARENCY` table; `PIGMENTS` and everything drawn from it stay
  byte-identical.
- **Route effects (B8).** `blend` is read from the existing effect key, `opacity` with a
  `.get` default of 1.0 and never written into `default.toml`; only
  `minor_road_classes` and `relief_strength` join `DIGEST_OMITS_AT_DEFAULT`.
- **Lettering scale (B9).** P7.V11 is cut to the nib plate painted at scale 2 and
  downsized with Lanczos in every lettered example, lossless for lettering figures,
  published widths unchanged. Doubling the published widths was dropped: it breaks the
  size budgets of ADR 0033 and repaints the maps at 1440 and 2400 px.
- **The docs group (B10).** Fixture references are found by a fixture-reference grep,
  each Keswick consumer has a named replacement (Ambleside for the hero, gallery, map
  styles, social preview, first-map rung and route-ink how-to; Lynmouth for the
  command-line how-to), `gallery.md` is owned section by section, and the README's
  quick start is left alone.
- **Journal notes (B11).** No margin band: notes are seated first through `_place_flat`
  as flat blocks with leaders, their boxes taken before any other name, never dropped.
- **CI time (S9).** One budget for the round, 4 minutes over the baseline P7.V1 records,
  with runs recorded after P7.V9a, P7.V7b, P7.V10, P7.V11 and the P7.V12 group.
- **The tutorial grids (S10).** Every rung of `paint-a-watercolour.md` has a named grid.
- The other findings (B5, B6, S1 to S4, S7, S11) are applied as the review proposed.

After plan review 2 (`reviews/p7v-plan-review-2.md`), also settled:

- **Keswick's fixture budget (B1).** P7.V9a sets `BUDGETS["keswick"] = 7_000_000` for
  the untrimmed directory; P7.V12a removes it with the fixture.
- **CI time (B2).** The budget binds only at the P7.V12-group checkpoint; the earlier
  runs are recorded with an allowance for the Keswick and Trotternish cost P7.V12a
  removes, never a stop. Grids paint at their published size; the route-ink grid paints
  once per pen brush (the brush is in the base digest) and composes every cell.
- **Yr Wyddfa's size (S1).** Skye's rule: re-trim at 25 m if over 10 MB, accept up to
  12 MB with the budget set to the measured size rounded up to 0.5 MB.
- **One strand gap (S2).** When the pen draws the route, the lettering's strands use
  `route_pen_width_px` too, through one helper in `strands.py`.
- **The route-ink grid (S4).** Solid, wet pen `MAJ1-e` and dry pen `MAJ3-e`, by the
  maroon, the default pink, indigo and burnt sienna; dotted left out until it renders.
- **Places data (S6).** Callouts and notes live in `examples/places.toml`, read by
  `place_card.py` through a new `place` option; notes are seated against the taken
  boxes too.
- **Encodings (S7).** `word.webp` stays lossy (a mixed figure); a lettered thumbnail or
  any regenerated image that would pass its budget falls back to lossy WebP at quality
  95, recorded.
- **Skye's painted area (S10).** At least 45% is accepted when 60% is out of reach
  inside the card-box rule.
- **Skye's track (S11).** `make_track.py --ref REF` chains a road ref's ways
  automatically, failing on a gap over 5 m.
- **Specks (S12).** The threshold is a quantile of `sheet.gran`; foxing goes off in the
  reference and explanation figures in P7.V7b. The "Compose the painting" grid is hand
  seed by backing wash.

After plan review 3 (`reviews/p7v-plan-review-3.md`), also settled:

- **The pen plate's gap (B1).** Always `route_pen_width_px * STRAND_GAP_WIDTHS *
  job.scale`, base-group fields only, so a fed or changed route ink never changes a
  cached plate (ADRs 0005 and 0027); `strand_gap_px` is used by `pipeline.paint` only.
- **The paper's golden check (B2).** A unit test (vignette and foxing 0: warm equals
  classic more than a tenth of the width in) proves the draws unchanged; the goldens'
  interior change is recorded as the vignette's narrowing, smudges removed and specks
  added.
- **Yr Wyddfa (B3).** Never simplified; accepted up to 12 MB; over that stops.
- **Confirmed assumptions.** The Lynmouth job sheet is built by `PaintJob.begin`;
  `MAJ3-e` is the dry pen, swapped for `MAJ4-e` if P7.V13 finds it does not read dry.
- **Pushes (maintainer, 2026-10-25).** Commit locally; push only when a slice lands.

### 10.5 Decisions, 2026-10-25

- The fern takes the new paper; its drawing is unchanged.
- Skye is not stopped for a slight overrun of its size budget: after the 25 m re-trim,
  up to 12 MB is accepted and the budget set to the measured size.
