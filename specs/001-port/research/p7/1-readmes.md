# P7 research 1: what makes a great README

Scope: case studies of widely praised READMEs (13 Python tools and libraries, 5 visual or
creative ones), the guidance literature, then implications for pyntpot's README at
0.1.0. All READMEs were fetched raw from `https://raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md`
on 2026-10-23 and are cited by repo. Line counts are of the raw Markdown.

## Case studies

"Above the fold" means the first screen of the rendered GitHub page, roughly the first
25 to 40 raw lines once badges are collapsed.

### Developer tools and libraries

**rich** (Textualize/rich, 445 lines, 29 images). Opens with six badges, a logo, then
eighteen translation links before a word of prose. Pitch: "Rich is a Python library for
_rich_ text and beautiful formatting in the terminal." Directly under it, `features.png`:
one screenshot of everything Rich renders. Quick start is two shell lines (`pip install
rich`, `python -m rich`) then a one-line `print` with its rendered output as an image.
Every renderable gets a `<details>` fold with code and a screenshot. Leaves out: API
reference, configuration. The lesson: the product *is* the visual, so the README is a
gallery of its own output. The anti-lesson: the translation wall pushes the pitch below
the fold.

**textual** (Textualize/textual, 211 lines, 7 GIFs). Splash image, then a clock widget
image floated right beside a two-sentence pitch ("Build cross-platform user interfaces
with a simple Python API. Run your apps in the terminal *or* a web browser."), then a
complete 30-line app. Sections: Widgets (GIF gallery), Installing, Demo (`python -m
textual`, or `uvx textual-demo` without installing), Dev Console, Command Palette. Every
claim sits next to a moving picture. Leaves out tutorials entirely: one link to
"getting started".

**httpx** (encode/httpx, 147 lines). Centred butterfly logo, italic tagline "A
next-generation HTTP client for Python", two badges, then one sentence of three bolded
differentiators. Install is one line; the first example is a `>>>` REPL session showing
real return values. Then a terse Features bullet list, Installation extras,
Documentation (links out), Contribute, Dependencies (each dependency named and
justified). Leaves out every advanced topic. A model of restraint.

**uv** (astral-sh/uv, 326 lines). Title, three badges, pitch "An extremely fast Python
package and project manager, written in Rust." Hero is a benchmark bar chart in a
`<picture>` element with light and dark sources and an italic caption naming exactly what
was measured ("Installing Trio's dependencies with a warm cache"). Highlights is a
bulleted list where nearly every bullet links into the docs. Sections then follow the
user's tasks (Projects, Scripts, Tools, Python versions, The pip interface), each a short
console transcript and a docs link. FAQ, Acknowledgements, License close it.

**ruff** (astral-sh/ruff, 454 lines). Same house pattern as uv: badges, a `Docs |
Playground` link bar, one-sentence pitch, benchmark chart with a caption, emoji-bulleted
features. Then Testimonials (named quotes), a table of contents, Getting Started, Rules,
Contributing, Support, Acknowledgements, "Show your support" (a badge to copy). The
README is wrapped in `<!-- Begin section -->` markers so the docs site reuses it: one
source, two surfaces.

**FastAPI** (fastapi/fastapi, 533 lines). Logo, italic tagline "FastAPI framework, high
performance, easy to learn, fast to code, ready for production", four badges, then a
bold **Documentation** and **Source Code** link pair. Key features in bold-lead
bullets, some with quantified claims flagged with an asterisk. Then Sponsors, Opinions
(quotes), a mini documentary, Requirements, Installation, and the famous Example: create
it, run it, check it, see the interactive docs (screenshots), then "Example upgrade"
and a Recap. Long, but it is a tutorial in miniature with screenshots at every step.

**Typer** (fastapi/typer, 380 lines). Same template as FastAPI. Notable section name:
"The absolute minimum", a two-line program, then "Run it" with the terminal output.

**Pydantic** (pydantic/pydantic, 70 lines). Nine badges, pitch "Data validation using
Python type hints." Then, unusually, a product advert (Logfire) and a version note
(V1 vs V2) above Installation. One "Simple Example" with output. Short, but the advert
and migration notice occupy the slot where a newcomer wants the example.

**polars** (pola-rs/polars, 161 lines). Banner logo, five registry badges, a
documentation link bar per language binding. Pitch heading "Extremely fast Query Engine
for DataFrames", bold-lead features, then "Polars in action": one realistic 12-line lazy
query. Performance links out to benchmarks. Install covers optional extras.

**attrs** (python-attrs/attrs, 161 lines). Logo with a dark-mode variant, five badges
(including a "no slop" AI-policy badge). The pitch has a voice: "the Python package that
will bring back the **joy** of **writing classes** by relieving you from the drudgery
of implementing object protocols". Sponsors block (generated by `cog`), one Example with
REPL output, a subsection "Hate Type Annotations!?", a short "Data Classes" comparison,
then Project Information as a link list. The `<!-- teaser-begin -->` markers let the
docs and PyPI reuse the opening.

**requests** (psf/requests, 76 lines) and **Flask** (pallets/flask, 53 lines). The
minimalist pole. requests: title, five badges, "a simple, yet elegant, HTTP library",
then a REPL session as the very first content. Flask: a logo, two paragraphs that say
what it is and what it deliberately does *not* do ("doesn't enforce any dependencies or
project layout"), one example with its `flask run` output, Donate, Contributing. No
feature list at all.

### Visual and creative

**prettymaps** (marceloprates/prettymaps, 112 lines). The closest neighbour to
pyntpot: maps from OpenStreetMap, rendered as art. Pitch on line 3 ("A minimal Python
library to draw customized maps from OpenStreetMap..."), then immediately one full-width
map. Badges come *after* the picture. Then licence, a strongly worded note on crediting
("keep the printed message on the figures crediting my repository and OpenStreetMap
([mandatory by their license])") and NFTs, a Hacker News screenshot, install, a
three-line quick start (`prettymaps.plot('Stad van de Zon, Heerhugowaard,
Netherlands')`), a resource table (tutorial, notebook, Colab, Streamlit app), one
customised example *with its output image directly beneath*. Weakness: the heading
hierarchy is chaotic (a badge row as an `h1`), and the politics sit above install.

**vsketch** (abey79/vsketch, 184 lines). No hero at all; badges then "What is
_vsketch_?" with four bold-lead focus bullets, including one that says what it does not
do: "Plotter-centric ... doesn't aim to solve other problems." An honest early-stage
note asking for contributions. Getting Started is a narrated walkthrough (`vsk init`,
edit the sketch, `vsk run`) with screenshots of the live viewer interleaved.

**Pillow** (python-pillow/Pillow, 112 lines). Logo, a badge *table* (docs, tests,
package, social), a three-sentence Overview, links out. No example, no output image.
It works because everyone already knows what Pillow is; it would fail for a new project.

**matplotlib** (matplotlib/matplotlib, 73 lines). Fourteen badges in three rows, then
the logotype, one sentence ("a comprehensive library for creating static, animated, and
interactive visualizations in Python"), and `readme_preview.png`: a grid of figure types.
Install, Contribute, Contact and Citing all link out. The image does the work the prose
does not.

**manim** (ManimCommunity/manim, 140 lines; 3b1b/manim, 188 lines). A surprising gap:
an animation engine whose READMEs show *no* rendered output, only a logo and code. The
community README describes what you "should see" in prose ("a simple scene in which a
square is transformed into a circle") and links to the gallery. Both lead with a
warning box disambiguating the two forks. This is the cautionary tale for a visual
library: telling instead of showing.

## Guidance sources

- GitHub, "About READMEs" (github/docs, `about-readmes.md`): a README says what the
  project does, why it is useful, how to get started, where to get help, who maintains
  it; "should only contain information necessary for developers to get started using
  and contributing", longer material belongs elsewhere. GitHub renders an Outline menu
  from headings, so a hand-written table of contents is optional; content beyond 500 KiB
  is truncated; relative links and image paths work on GitHub.
- makeareadme.com: name, description, badges, visuals ("screenshots or even a video"),
  installation, usage ("the smallest example of usage that you can demonstrate", "show
  the expected output if you can"), support, roadmap, contributing, licence, project
  status. It argues "too long is better than too short", the main dissent from the
  minimalist school.
- Write the Docs, "A beginner's guide to writing documentation": first say "what your
  project does and why it exists"; install "should be a couple lines for the basic
  case", with caveats linked out; cites Tom Preston-Werner's "Readme Driven
  Development" (2010).
- awesome-readme (matiassingers/awesome-readme): the curators' recurring praise is
  "clear description", "GIF demo" or screenshot, "TOC", "badges", "simple install".
  It rewards decoration more than the other sources do; read with that bias in mind.
- Hackergrrl's "Art of README" could not be re-fetched in this session (404 on raw
  paths), so it is not quoted here.

## Synthesis

**Recurring patterns.**

1. *One sentence that names the category and the differentiator.* "An extremely fast
   Python package and project manager, written in Rust." "Data validation using Python
   type hints." The best are under fifteen words, start with the noun phrase, and contain
   no adjective that could describe any project ("modern", "powerful").
2. *The hero shows the core claim.* uv and ruff sell speed, so the hero is a benchmark
   chart. rich, textual, prettymaps and matplotlib sell output, so the hero is output.
   The picture is chosen by asking "what is the one thing we want believed?"
3. *Captions.* uv and ruff put an italic line under the hero saying exactly what it
   shows. This turns a pretty picture into evidence.
4. *Shortest runnable thing, with its output.* requests, httpx and Flask show results
   inline; rich and prettymaps put the rendered image straight after the code. A visual
   library's example is incomplete without the picture it produces.
5. *Link out early and often.* uv's Highlights bullets each link into the docs; Pillow
   and matplotlib are almost entirely links. The README is a lobby, not the building.
6. *Saying what it is not.* Flask ("doesn't enforce any dependencies or project
   layout"), vsketch ("doesn't aim to solve other problems"). Scope statements build
   trust faster than feature lists.
7. *Reuse markers.* ruff's section comments and attrs' `teaser-begin` keep README, docs
   and PyPI in step from one source.

**Disagreements between good READMEs.**

- Length: Flask (53 lines) and FastAPI (533) are both admired. The split follows whether
  a docs site exists: FastAPI's README *is* a tutorial; Flask hands off to one. pyntpot
  has no docs site at 0.1 (D13), which argues for a middle length that links into
  `docs/` on GitHub.
- Badges: matplotlib has fourteen; prettymaps puts them below the hero; requests keeps
  five. Nobody's praise rests on badges.
- Feature lists: uv, FastAPI and polars lead with them; Flask and requests have none.
  Feature lists help when the category is crowded and the differentiators are several.
- Social proof: ruff (testimonials), FastAPI (opinions, sponsors), prettymaps (Hacker
  News). Earned only with an audience; premature at 0.1.

**Anti-patterns observed.**

- Pushing the pitch below the fold with translation links (rich), adverts and migration
  notices (Pydantic), or badge walls (matplotlib).
- A visual library that shows no output (manim).
- Politics or grievances above install (prettymaps' NFT section), however justified.
- Messy heading levels (prettymaps uses `#` for badges and links), which breaks GitHub's
  Outline menu.
- Emoji-bullet feature lists (ruff) read as generic; they suit a speed tool, not an
  aesthetic one.

## How READMEs carry identity and aesthetic

GitHub fixes the typeface and colours, so a README's identity is carried by four things:
the pitch's wording, the voice of the prose, the images, and what is withheld.

- *Pitch reflects the product.* uv and ruff both say "extremely fast", and the hero is a
  chart: the product is speed, the README is spare and numeric. attrs' "bring back the
  **joy**" is warm because the library is about taste.
- *Voice.* attrs is witty ("Hate Type Annotations!?"); Flask is dry and confident; rich
  is enthusiastic. Voice is consistent from tagline to closing link.
- *Imagery is the only typography available.* Textual's splash and rich's logo are
  rendered by the libraries themselves, so even the branding is a demo. rich's
  `features.png` is a terminal screenshot of Rich output: the medium is the message.
- *Restraint.* httpx and Flask feel crafted because nothing is extraneous. An
  aesthetic product undermines itself with a cluttered page.
- *Dark mode.* uv, ruff and attrs ship `<picture>` light and dark variants. A painting
  on paper carries its own background and needs neither.

## Implications for pyntpot

**Opening sentence candidates.** Keep it in the noun-phrase-first form and let the
picture carry the adjectives:

1. "pyntpot paints watercolour and pen-and-ink pictures in Python: paper, washes, brush
   and nib strokes, and hand lettering, with route maps as its first application."
2. "Hand-drawn watercolour and pen-and-ink painting for Python, with route maps." (the
   current line and `pyproject.toml` description; good, and identical on PyPI)
3. "Turn a GPX track into a hand-painted watercolour map, or paint your own pictures
   with the same brushes." (user-outcome led; strongest hook, but buries the engine)

Recommend (2) as the tagline under the title and a two-sentence paragraph after the
hero that expands it as (1) and names the layering in plain words: a painting engine,
hand lettering on top of it, maps on top of both.

**Hero image.** A route map, full width, immediately under the tagline and *before*
badges (prettymaps' order), with a uv-style italic caption: what it is, where, and the
one command that made it. The Lynmouth golden (`tests/golden/lynmouth/map.png`,
1800x1457, 2.7 MB) shows the style well (sea wash, pen coastline, lettering), but:
(a) it shows a lettering artefact, "East Lp" beside "East Lyn", which a hero must not;
(b) it is a test fixture that changes on golden regeneration and is 2.7 MB. Commit a
separate, downscaled README image (about 1200 px wide, under 500 KB) under `docs/img/`,
regenerated deliberately. Reference it by an absolute
`raw.githubusercontent.com/.../v0.1.0/...` URL, because the README is the PyPI long
description (`readme = "README.md"`) and relative image paths do not render on PyPI.

**Second image and gallery.** The plan's non-map image (a lettered word on a washed
circle from `examples/word.py`) is right: it proves the engine stands without maps.
Better still, make that word "pyntpot" and use it as the README's logo or the start of
the gallery, so the branding is painted by the product, as rich and textual do. D13 asks
for a gallery: a two-column table of the eight rung outputs (paper, wash, brush stroke,
nib line, pigments, lettering, composition, route map), each thumbnail linking to its
`examples/` script, gives a visual table of contents and doubles as the tutorial's map.

**Quick start shape.** The P7 outline says "three-line quick start". The Python map
pipeline is seven calls plus two providers with a contact (`examples/route_map.py`), so
three lines of Python would be a fiction. Two honest options:

- Map, by CLI: `pip install pyntpot` then
  `pyntpot map route.gpx -o map.png --cache cache/ --contact you@example.org`, followed
  by the image it produces. Genuinely three lines, network required.
- Engine, by Python: the `examples/wash.py` disc in about eight lines, offline, with its
  output image. Shows that pyntpot is a painting library, not only a map tool.

Recommend both, CLI first, each followed by its picture, as makeareadme and prettymaps
urge. Show `uv add pyntpot` alongside pip.

**Section order.** Title and tagline; hero with caption; badges (few: PyPI version,
Python versions, CI, CodSpeed as the plan fixes it); what it is (two short paragraphs,
including what it does not do, stated from the module docstrings at P7 rather than
from this note: for example, it paints raster images, it is not a tile server, and its data
providers are pluggable); gallery; install; quick start (map, then engine); data and
attribution (OpenStreetMap and OpenTopoData terms, the required contact string, the
cache, why `compose` draws attribution by default); documentation (links into
`docs/tutorials`, `how-to`, `reference`, `explanation`, and `references.md` for the
technique bibliography); status (0.1, API may change, keep-a-changelog); contributing
(one line to `CONTRIBUTING.md`); licence (MIT, OFL for the vendored Patrick Hand face).

**What to keep out.** The gate stack, ADR numbers, the agentic workflow, `prek`
commands and `CLAUDE.md` (move the current "Develop" section to `CONTRIBUTING.md`; a
user's README is not a contributor's). Internal names (`_port`, plate manifest
internals). Phase and spec numbers. Testimonials and sponsors. A hand-written table of
contents (GitHub's Outline covers it). Emoji bullets.

**Challenges to the current P7 outline.**

1. "Three-line quick start" should be scoped to the CLI, or relaxed; a Python map in
   three lines does not exist in the API.
2. The outline omits a caption, badge placement, and the image hosting question
   (absolute URLs for PyPI); add them.
3. The outline lists "data policy" and "attribution requirement" separately; prettymaps
   shows one clear "crediting" paragraph reads better, linking to
   `docs/explanation/data-policy.md`.
4. Consider a scope sentence ("what it does not do") as a named outline item.
5. Choose and fix the hero render before writing prose round it; the "East Lp" label is
   a defect worth a `docs/issues/` note independent of the README.

### Weaving the core point and style through the README

The core point is that the output looks drawn by hand. The README should prove that
before it claims it, and then keep the reader looking at paint.

- **Image before adjective.** The first thing seen after the name is a painting, not a
  badge or a feature list. Every later section that produces output ends with that
  output, so the page reads as a sketchbook interleaved with recipes.
- **Paint the furniture.** A wordmark lettered by `pyntpot.letters` on a wash, and
  optionally small section dividers or gallery thumbnails on the same paper, so the
  brand is a demo (rich, textual). Keep them light: one wordmark, one gallery.
- **Vocabulary from the studio, terms from the glossary.** Use the words a painter uses
  and that `GLOSSARY.md` already fixes: paper, wash, pigment, brush, nib, plate, hand.
  Prefer "paints", "lays a wash", "letters" over "renders" and "generates", and never
  introduce a synonym the glossary does not hold.
- **A calm, plain voice.** British spelling throughout (watercolour, colour), short
  declarative sentences, no hype words, no emoji. Restraint (httpx, Flask) matches a
  craft product better than enthusiasm (FastAPI).
- **Captions as provenance.** Each image says what painted it and from what data
  ("Lynmouth, Devon, from a GPX track, OpenStreetMap and OpenTopoData, painted by
  `pyntpot map` with the default style"). This keeps the hand-drawn claim honest and
  carries the attribution ethos into the imagery.
- **Real places, consistent palette.** Gallery maps use the CONTRIBUTING place names and
  the default style, so the page has one palette and one paper, like a single artist's
  portfolio, rather than a theme showcase.
- **Thread into docs.** End the README with the same image vocabulary the tutorials use:
  the gallery thumbnails are the tutorial rungs, so a reader who likes a picture lands
  on the page that teaches it.
