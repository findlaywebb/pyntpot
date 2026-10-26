# P7 research 6: identity and voice

Scope: the project's core point, how comparable projects carry identity in their docs,
principles for carrying it without hurting clarity, and concrete proposals for pyntpot.
Not covered here (other agents): README contents, docs tree structure, galleries,
tutorial prose, release surface. Fetched pages were read on 2026-10-23 and treated as
data.

## 1. The core point, distilled from the repo

What the repo says about itself, in its own words:

- Purpose: "paints hand-drawn watercolour and pen-and-ink raster images: paper, washes,
  brushes, nibs, pigment compositing and hand lettering, with route maps from vector
  OpenStreetMap data and elevation as its first application" (`specs/001-port/spec.md`,
  `CLAUDE.md`, `docs/architecture.md`).
- It simulates the medium, not a look. `docs/explanation/references.md` cites
  Kubelka-Munk glazing, Curtis et al.'s *Computer-Generated Watercolor*, edge darkening as
  outward flow, backruns, granulation following the paper, a shallow-water pass, a
  per-bristle ink reservoir with reload, pigment separation into the paper's pits, a pen
  nib stroke. `examples/paper.py` paints "the cream rag, its worn border, vignette and
  foxing". `examples/pigments.py` shows multiply beside Kubelka-Munk glazing. This is a
  painter's process in code, not a post-filter over a vector render.
- It is deterministic. Every example says "Every seed is fixed, so one run writes the same
  files"; goldens are pinned literals; the 001 spec demands a pixel-identical reference
  render. A painting that looks accidental but reproduces byte for byte is the project's
  most distinctive claim.
- It is scholarly. Every technique names a source key, verified live (D24), with a status
  line. Few generative-art libraries credit their lineage this carefully.
- It is layered like a studio: `ink` (paper, pigment, brushes), `letters` (the hand and
  the nib), `maps` (an application). The maps are the first application, not the
  product's edge; `ink` and `letters` never say "map" (GLOSSARY: map is "the maps side's
  word, which `ink` and `letters` never use").
- It is polite to the commons: contact strings required, published provider limits
  enforced by default, attribution drawn unless switched off (D8).
- Audience: Python programmers who want images that look made by hand: people making
  route cards and keepsake maps from GPX tracks, generative artists who want a physically
  grounded watercolour and ink engine, and anyone who wants a hand-lettered label on a
  painted ground without a vector toolchain.

### Candidate one-line pitches

1. "Watercolour and pen-and-ink painting for Python, with route maps." (closest to the
   current README and package docstring; safe, plain)
2. "Paint with paper, pigment and a nib, in Python: watercolour and ink images that come
   out the same every time."
3. "A watercolour and pen-and-ink engine for Python, from the paper up, with hand-lettered
   route maps as its first application."
4. "Lay a wash, pull a brush, letter a name: hand-drawn raster images from seeded Python."
5. "Hand-drawn maps and pictures, painted the way a painter works: paper, wash, pen,
   then the names." (best for the tutorial and README lede, weaker as a PyPI summary)

Recommendation: 1 or 3 as the PyPI summary and package docstring (they must stay plain
and greppable); 4 or 5 as the README's first painted line.

### Paragraph version

pyntpot paints raster images the way a watercolourist and a pen-and-ink illustrator
work: it lays down a sheet of cream paper with its tooth and foxing, floods washes that
pool at their edges and granulate into the paper, drags bristle brushes that run out of
ink and reload, glazes pigments over one another by Kubelka-Munk, and writes names by
hand with a nib in the vendored Patrick Hand face. Every mark is seeded, so a painting
that looks accidental comes out byte for byte the same on every run, and every technique
cites the paper or essay it comes from. Route maps, built from OpenStreetMap features and
elevation, are its first application; the engine underneath (`pyntpot.ink` and
`pyntpot.letters`) paints anything.

### Vocabulary to lean on (GLOSSARY canonical terms)

Lean on: **sheet**, **plate**, **plates**, **wash**, **brush**, **brush sheet**,
**mark**, **hand**, **setting**, **trace**, **nib plate**, **pigment**, **pigment
layer**, **density**, **card**, **route**, **route ink**, **style**, **theme**,
**credit**. Also the craft verbs the code already uses: lay (a wash), stamp (a brush),
glaze, composite, letter, compose.

Traps to police in a docs style guide:

- **sheet** is "the paper's noise fields, seeded; never the map". Prose that says "a
  sheet of cream paper" (as `examples/composition.py` does) is evocative and close, but
  the reference must keep the glossary meaning. Reserve "paper" for what is painted by
  `paper_plate`.
- **canvas** is a pixel grid and world box, not a stretched painter's canvas. Never use
  it in the artistic sense.
- **map** never appears in `ink` or `letters` docs; use "image" or "picture".
- **layers** (the basemap's) is not **pigment layer**; do not say "layer" loosely.
- **mark**, not "stroke" or "glyph stroke", for what the nib runs along; **hand**, not
  "writer" or "renderer".
- Do not coin "watercolour filter", "effect", "shader", "style transfer". The pitch rests
  on simulation, and those words undo it.

## 2. Case studies

**Rough.js** (https://roughjs.com/). Tagline "Create graphics with a hand-drawn, sketchy,
appearance". The page is illustrated almost entirely by the library's own output
(sketched shapes, fill styles, a map), with plain sans body and code. Identity comes from
the pictures, not from styled prose; the copy stays direct. Lesson: the output is the
brand. Weakness: the hand-drawn look stops at the images, so the page feels generic
between them.

**Excalidraw** (https://plus.excalidraw.com/blog). The product's hand-drawn font carries
into marketing (there is a post about adding hand-drawn CJK fonts), which is consistent
but shows the risk: a handwriting face as body or UI text tires the eye and fails in
scripts it does not cover. Lesson: use the hand face for display only.

**tldraw** (https://tldraw.dev/). Tagline "Build infinite canvas apps in React with the
tldraw SDK". The developer site drops the sketchy aesthetic for polished, enterprise copy
("production-ready"). Lesson: the opposite pole; it proves a hand-drawn product can have
plain docs, but loses the warmth the product has. pyntpot should sit between Rough.js and
tldraw: hand-made pictures, plain words.

**matplotlib xkcd mode**
(https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.xkcd.html). Reference stays
austere ("Turn on xkcd sketch-style drawing mode"), parameters described flatly (scale,
length, randomness), and it states the font gap as a fact: "xkcd fonts are not packaged
with Matplotlib". Lesson: the whimsical feature gets a dry reference page, and that is
correct. pyntpot vendors its face, which is worth saying as plainly.

**p5.js** (https://p5js.org/). "a friendly tool for learning to code and make art",
"built by an inclusive, nurturing community", and "p5.js will not add any new features
except those that increase access". Imagery is people. Lesson: a stated value (access)
that constrains the docs. pyntpot's equivalent stated values could be determinism,
citation and good manners to data providers. Tip into twee: none on the page, but the
friendliness depends on a community pyntpot does not yet have; do not borrow its warmth
without the substance.

**Processing** (https://processing.org/). "a flexible software sketchbook"; "Sketch with
code"; "everything is code, even the logo". Lesson: one metaphor (sketchbook) carried into
names (programs are "sketches"), and a logo generated by the tool. pyntpot's metaphor is
the painter's studio, already in its API names (plate, wash, nib, hand), so the docs need
only to stop translating them away.

**Charm** (https://charm.land/). "We make the command line glamorous." Mascots, jokes,
"haters > /dev/null". Strong identity; the product's own output (terminal screenshots) is
the hero image. Lesson: output as brand, again. Where it tips: the jokes date fast and
would jar against pyntpot's quiet, careful voice. Borrow the confidence, not the wink.

**Rich and Textual** (https://rich.readthedocs.io/en/stable/introduction.html). "Rich is
a Python library for writing rich text (with color and style) to the terminal". The
README famously shows terminal renders made with Rich; the narrative docs use plain code
blocks. Lesson: the gallery is generated by the library; the API docs stay plain.

**Svelte** (https://svelte.dev/). "web development for the rest of us"; calls itself "a
love letter to web development". Lesson: a short, opinionated, human tagline works if
everything below it is restrained.

**Tailwind and Stripe** (not fetched; from general knowledge, so weight lightly). Both are
cited for typographic craft and live, runnable examples beside prose. The transferable
part is discipline: one type scale, consistent code samples, every example actually
runs. pyntpot's tested `examples/` already meet the last.

**Tyler Hobbs**
(https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art,
a design input in `references.md`). First person, candid ("doesn't really replicate what
happens with real watercolor paint, but it looks cool anyway"), anchored in his own
sketchbook. Each step has an image of the intermediate state. Weakness: many images lack
alt text. Lesson: show intermediate states; be honest about where simulation stops.

**Stamen, Watercolor Process** (https://stamen.com/watercolor-process-3dd5135861fe/, a
design input for `multiply-compositing`). One London tile carried through every stage
(mask, blur, noise, threshold, edge darkening, composite), one image per operation.
Lesson: a single recurring sample place makes process legible. pyntpot has Lynmouth.

**Inconvergent** (https://inconvergent.net/, 403 to the fetcher). Known for terse essays
where each algorithm is shown by its own output, monochrome, generous whitespace. Lesson:
restraint as style.

**The Nature of Code** (https://natureofcode.com/introduction/). Conversational, warm,
"phenomena that naturally occur in the physical world"; visuals are "drawn only with
basic shapes and grayscale color". Lesson: the physical world as the organising idea; the
book is structured by phenomena, which maps onto pyntpot explanations organised by
phenomena (pooling, granulation, backruns, the reservoir).

**Bartosz Ciechanowski** (https://ciechanow.ski/mechanical-watch/). Builds the mechanism
one part at a time, each part introduced by the problem it solves, often showing a broken
version first. Lesson for pyntpot: an explanation can show the wash without edge
darkening, then with it, from the same seed. Static images suffice; interactivity is
beyond a no-site v0.1 (D13).

**Observable** (not fetched). The notebook pattern, prose beside the live output that
code made, is the model for how each pyntpot figure should be anchored to the script that
painted it.

## 3. Principles

1. **The pictures carry the style; the words stay plain.** Every case that works (Rough.js,
   Rich, Charm, Stamen) puts identity in the product's own output. Prose should be quiet,
   British, concrete, in the craft vocabulary. No jokes that need a community to land.
2. **Style by document type** (Diátaxis: reference "should be austere"; "Neutral
   description is the key imperative"; "consistent", and should "mirror the product",
   https://diataxis.fr/reference/):
   - More style: README (painted wordmark, gallery, one lettered pitch line), tutorial
     (painter's order of work, one image per rung), explanation (essays on the craft with
     before-and-after figures and citations).
   - Less: how-to (task, steps, result image at most), reference (no imagery beyond a
     swatch where a value is a colour or a brush; same template for every entry; glossary
     terms only).
3. **Alt text is content.** A painted image needs a two-part text alternative for complex
   images, a short identification plus "a textual representation of the essential
   information" (https://www.w3.org/WAI/tutorials/images/complex/). For a process figure
   the alt says what changed between states ("the same disc wash, now with pigment pooled
   at its edge"). Never alt "watercolour image".
4. **Text never lives only in pixels.** Any lettered word in an image (wordmark, labels on
   a card) is repeated as real text nearby. The Patrick Hand face is for display images,
   never for body or code.
5. **Contrast and dark mode.** Cream paper on a dark page reads as a glaring rectangle;
   that is acceptable for a painting (it is a physical object), but give images a small
   margin or border and do not rely on transparent PNGs with dark ink. Where a transparent
   plate is shown (the nib plate), composite it on paper for the docs. GitHub supports the
   `<picture>` element in Markdown, so a dark-page variant is possible later; at v0.1 one
   opaque image is simpler. Captions and labels in figures should meet WCAG AA as text.
6. **Determinism is part of the look.** Every image cites its script and seed. A reader
   can reproduce the figure exactly; say so once, prominently, and let captions point to it.
7. **Honest about the limits** (Hobbs, matplotlib). State designed gaps as capability
   facts, as CLAUDE.md requires: "It does not letter, read geographic data or touch the
   network."
8. **No style in identifiers.** Never rename a public thing for charm; the glossary wins.

## 4. Concrete proposals for pyntpot

1. **Docs illustrated only by pyntpot.** Every image in README and `docs/` is painted by a
   tested script under `examples/` (the P11 `main(out_dir)` convention), run offline under
   `tests/examples/`. A short architecture test can check that each image path in `docs/`
   names a script that writes it. No stock photos, no hand-made diagrams. Caption pattern:
   "Painted by `examples/wash.py` (seed 11)."
2. **A painted, lettered wordmark.** `examples/word.py` (already planned for the README)
   doubles as the wordmark: "pyntpot" written by the hand on a washed disc, the paint pot
   of D2's name ("reads paint pot"). Keep it a PNG with real-text title beside it.
3. **Tutorial in the painter's order of work.** The rungs already follow it: paper, wash,
   brush stroke, nib line, pigments, lettering, composition, route map. Name the sections
   as a painter would ("Stretch the paper", "Lay a wash", "Pull a brush", "Ink a line",
   "Glaze two colours", "Letter a name", "Bring it together", "Paint a route"), with the
   API names in the body. That ordering is also the dependency order of `ink -> letters ->
   maps`, so the craft story and the architecture agree; say so in one line.
4. **Explanation pages as short essays on the craft.** `how-the-wash-works.md` (P7 list)
   organised by phenomenon (Nature of Code) and built part by part (Ciechanowski): flat
   body, edge darkening, backruns, granulation, wet-area bleed, each a same-seed figure,
   each ending in its `references.md` key. A companion essay on the nib and the reservoir
   later. The essays may use first person plural sparingly; reference never does.
5. **One recurring setting.** Stamen used one London tile; pyntpot uses the Lynmouth
   fixture box for every map figure (D10), and its fixture names (Lyn, Heddon, Brendon,
   Watersmeet) recur. Non-map figures letter real names from the CONTRIBUTING list
   (Grasmere, Keswick already appear), spread across regions. Never invent a name; never
   step outside the box for coordinates.
6. **A one-page docs voice guide** (in CONTRIBUTING or `docs/`): British English
   (watercolour, colour, licence as noun); no em-dashes or en-dashes in human-facing prose
   (the P6 gate greps README, GLOSSARY, CHANGELOG, CONTRIBUTING and `docs/`); glossary
   terms only, with the trap list above; craft verbs over software verbs; no hype words
   ("stunning", "beautiful", "magic"); captions name script and seed; alt text describes
   the change; designed gaps stated as capability facts, never roadmap numbers.
7. **Stated values, p5-style, but ours**: three short lines in README: every image is
   reproducible from its seed; every technique cites its source; the data providers are
   asked politely and credited on the card.
8. **Reference stays plain.** Autogenerated or hand-written, each entry: signature, one
   line, invariants, what it does not do. A brush id or pigment key may carry a small
   swatch painted by a script; nothing else.

### Where it would tip into twee

Handwriting fonts for headings, faux paper backgrounds behind text, puns on "pot", tea and
brush emoji, mascot characters, first-person anecdotes in reference, renaming errors
("the brush ran dry"). Each costs clarity or accessibility and none adds information.

### Constraints checklist

- British English; no em-dashes or en-dashes in human-facing prose.
- Canonical GLOSSARY terms; add any new term there.
- Real UK place names from CONTRIBUTING; coordinates inside 51.19 to 51.26 N, 3.80 to
  3.88 W.
- Docstrings state gaps as capability facts, never spec or roadmap numbers.
- Images from tested, public-name-only scripts.
- No docs site at v0.1 (D13), so everything must read well on GitHub and PyPI.
