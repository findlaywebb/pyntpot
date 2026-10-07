# Documentation quality principles for a creative/graphics Python library (pyntpot)

Scope: principles and concrete patterns for tutorials, how-tos, reference, explanation, galleries, executable examples, READMEs and writing voice, applied to a watercolour and pen-and-ink painting library whose tutorials should build from primitives (paper, wash, brush, nib, pigment, lettering) to composition, with route maps as one application among many. Research done October 2026. Every claim carries a URL. Inferences are labelled as such.

## 1. What Diátaxis prescribes, how it fails, and how known projects apply it

### Takeaway
Diátaxis splits docs into four modes on two axes: action versus cognition, and acquisition versus application of skill. Tutorials are lessons for someone *at study*: one reliable path, visible results early and often, very little explanation. Mixing modes is the main failure. Django, NumPy (NEP 44), Canonical and Cloudflare use the model, but I found no evidence that Gradio does.

### Cited Findings
**The model**
- Diátaxis names four forms (tutorials, how-to guides, technical reference, explanation), each serving a distinct user need, and says documentation should be organised around those needs. — [diataxis.fr](https://diataxis.fr/)
- The "compass" asks two questions: "action or cognition?" and "acquisition or application?" Informs action plus acquisition = tutorial; action plus application = how-to; cognition plus application = reference; cognition plus acquisition = explanation. — [Diátaxis compass](https://diataxis.fr/compass/)
- The tutorial/how-to split is "study versus work". A tutorial runs in a controlled environment with a single line and no choices. It must be safe, the teacher is responsible for the learner's problems, and it spells out embodied details. A how-to addresses the messy real world, branches into alternatives, and assumes competence. — [Diátaxis: tutorials vs how-to](https://diataxis.fr/tutorials-how-to/)
- The "basic vs advanced" split is explicitly rejected as a misconception. Tutorials can be advanced, as with an anaesthetist's course on difficult neonatal intubations, and how-tos can be basic. — [Diátaxis: tutorials vs how-to](https://diataxis.fr/tutorials-how-to/)

**Tutorial prescriptions (exact principle names from diataxis.fr)**
- "Show the learner where they'll be going". Avoid presumptuous framing such as "In this tutorial you will learn…". — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Deliver visible results early and often". Every step yields a comprehensible result, however small. — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Maintain a narrative of the expected". Show sample or exact expected output and warn about likely errors. — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Point out what the learner should notice", with cues such as "Notice that…" and "Let's check…". — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Target the feeling of doing"; "Encourage and permit repetition". — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Ruthlessly minimise explanation" (link to it elsewhere instead); "… and focus on the concrete"; "Ignore options and alternatives". — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Aspire to perfect reliability": the tutorial must work for every user, every time, because the author cannot intervene. — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- "Don't try to teach": the learner learns by doing. Tutorials use "we" to signal shared effort and acknowledge what the learner has achieved. — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- Named failure modes: giving in to the urge to explain, abstract, generalise or offer choices; conflating tutorials with how-to guides; leaving the learner without feedback; not testing with real users; underestimating maintenance, because product changes cascade through a tutorial. — [Diátaxis tutorials](https://diataxis.fr/tutorials/)

**How-to prescriptions**
- How-tos are goal-oriented, "action and only action", with no digression or teaching. "Practical usability is more helpful than completeness." They may start and end at sensible points, fork, and have several entry and exit points. Titles say exactly what the guide shows. — [Diátaxis how-to guides](https://diataxis.fr/how-to-guides/)
- The model for a how-to is a recipe. It defines what it will achieve, assumes basic competence, and is "not a substitute for a cooking lesson". — [Diátaxis how-to guides](https://diataxis.fr/how-to-guides/)

**Adopters**
- Diátaxis's home page quotes Vonage, Gatsby and Cloudflare. Cloudflare used it as the information-architecture guide for its developer docs. — [diataxis.fr](https://diataxis.fr/)
- Django's docs index lists Tutorials ("take you by the hand… Start here if you're new"), Topic guides (explanation), Reference guides, and How-to guides ("recipes… more advanced than tutorials and assume some knowledge"). — [Django docs](https://docs.djangoproject.com/en/5.2/)
  - Note: Django describes how-tos as "more advanced than tutorials", which is the basic/advanced framing that Diátaxis rejects. Django's structure predates the formal framework. Procida is a Django core developer. — [DjangoCon EU 2022 speaker page](https://2022.djangocon.eu/pretalx.evolutio.pt/djangocon-europe-2022/speaker/FDRCZ3/index.html)
- NumPy NEP 44 adopts the four categories "for writing and reviewing whenever we add a new documentation section". Its rationale: "if explanations are mixed with basic tutorials, beginners might be overwhelmed… if the reference guide contains basic how-tos, it might be difficult for experienced users to find the information". It audits NumPy's state as a strong reference, few how-tos, explanations that leak into the reference, and tutorials that "need work". It proposes engaging, data-driven tutorials, such as the Keeling curve for curve fitting. — [NEP 44](https://numpy.org/neps/nep-0044-restructuring-numpy-docs.html)
- Canonical: the MAAS team blogged about adopting Diátaxis, and Procida, as Canonical's Director of Engineering, drove documentation practice across many teams. — [Ubuntu Discourse](https://discourse.ubuntu.com/t/ways-to-improve-documentation/23478/5); the scale claim ("40-plus teams") comes only from a secondary article: [pasqualepillitteri.it](https://pasqualepillitteri.it/es/news/5530/diataxis-framework-documentacion-ia)
- Python's docs community discussed adopting Diátaxis as a guide. This was a proposal, not a confirmed outcome. — [discuss.python.org](https://discuss.python.org/t/adopting-the-diataxis-framework-for-python-documentation/15072)
- Other adopters: HoloViz (Panel, hvPlot) presented its mapping of existing content to Diátaxis at PyData Berlin 2025 ([PyData Berlin 2025](https://berlin.pydata.org/conferences/2025/PPAYDV.html)). CloudCannon redesigned its docs on a modified Diátaxis in Feb 2026 ([CloudCannon blog](https://cloudcannon.com/blog/redesigning-cloudcannons-docs-with-diataxis-lume-and-pagefind/)). Noir added a quick-reference section because the four-part split alone did not address readers' initial motivation ([noir PR #3711](https://github.com/noir-lang/noir/pull/3711)).

### Inferences
- For pyntpot, the HoloViz case (a visualisation library) is the closest comparable adoption. Noir's addition of a "quick reference" supports the idea that a visual library also needs a front door, a gallery or README hero, that sits outside the four modes.
- A pyntpot tutorial series should be *one* path with no options ("paint a wash on paper", then "add a pen line", then "letter a title"). Variations such as granulation strength or nib choice belong in how-tos ("How to get granulating washes") or in the reference. Why a wash pools at its edges (the physical model) belongs in explanation.
- "Perfect reliability" means tutorial output must be deterministic: fixed seeds, pinned fonts and fixture data. This matches pyntpot's golden-value testing culture (CLAUDE.md).

### Gaps
- I found no source showing that Gradio adopted Diátaxis. Treat the brief's mention of Gradio as unverified.
- I did not find a primary Procida talk transcript. The diataxis.fr pages served as his primary written source.

## 2. Tutorials that build from primitives to composition

### Takeaway
The best creative-coding curricula climb a ladder: setup and "hello world", then single primitives, then combination, generation and simulation, then a cumulative project. Every rung produces an image, and the code sits beside its output, ideally live-editable. Interactive explainers (Red Blob Games, Bret Victor's explorables) add a second rule: let the reader change inputs and see outputs.

### Cited Findings
- The Book of Shaders's chapter order: Getting started (What is a shader?, "Hello world!", Uniforms, Running your shader), then Algorithmic drawing (shaping functions, colours, shapes, matrices, patterns), then Generative designs (random, noise, cellular noise, fBm, fractals), then Image processing, then Simulation (including "Water color" and reaction diffusion), then 3D. It ends with an Examples Gallery and a Glossary. It calls itself "a gentle step-by-step guide". — [The Book of Shaders](https://thebookofshaders.com/)
- Nature of Code climbs from randomness (Ch. 0) to vectors, forces, oscillation and particles (Part 1), then agents, cellular automata and fractals (Part 2), then genetic algorithms and neural nets (Part 3). Chapter 1 shows that existing `xspeed`/`yspeed` variables *are* a vector, introducing the abstraction only after the learner already has the concrete thing. — [Nature of Code introduction](https://natureofcode.com/introduction/)
- Nature of Code's structure: numbered examples with code comments beside it; a "snipped" scissors icon for partial listings; exercises ranging from technical to open-ended to fill-in-the-blank, with answers revealed on demand; and a cumulative "Ecosystem Project" at the end of every chapter. Every full example has "Open in Web Editor" so readers can "interact with, modify, and experiment with the code", with "no installation required". — [Nature of Code introduction](https://natureofcode.com/introduction/)
- p5.js's tutorial hub orders its lessons: Setting Up, Get Started (an interactive landscape), Variables and Change, Conditionals, Functions, Loops, Data Structure Garden, Animating with Media. Then come Drawing (Color Gradients; Custom Shapes and Smooth Curves), WebGL, and so on. Every tutorial card shows a preview image of the intended result. — [p5.js tutorials](https://p5js.org/tutorials/)
- Red Blob Games (Amit Patel) builds the visual working before the prose. He makes it interactive by letting "the reader change the *inputs* to the algorithm and then I show the *outputs*", and splits concepts into separate diagrams that build up. For line drawing, the sequence runs from interpolating numbers to interpolating points, counting steps and snapping to the grid. — [Red Blob Games: making of line drawing](https://www.redblobgames.com/making-of/line-drawing/)
- Patel structures by "the steps of the execution and sometimes… the steps of the code". He builds a small tutorial-specific layer system rather than a general library, and polishes visual hierarchy last ("drag handles should have a bolder look than minor elements"). — [Red Blob Games: making of line drawing](https://www.redblobgames.com/making-of/line-drawing/)
- Bret Victor: an "explorable example makes the abstract concrete, and allows the reader to develop an intuition for how a system works"; a "reactive document allows the reader to play with the author's assumptions". In a 2024 postscript he says the term has diluted to "any article with interactive graphics", whereas he meant "a written *argument* whose assertions are backed by explorable computational models". — [Explorable Explanations](https://worrydream.com/ExplorableExplanations/)
- Write the Docs principle "Cumulative": "Content should be ordered to cover prerequisite concepts first." — [Write the Docs principles](https://www.writethedocs.org/guide/writing/docs-principles/)

### Inferences
- Proposed pyntpot ladder, mirroring Book of Shaders and Nature of Code. Each rung is one tutorial page ending in a saved PNG:
  1. A blank sheet of paper (texture and tooth), the "hello world".
  2. One flat wash, then a graded wash, then wet-in-wet (one primitive, varied).
  3. A brush stroke and a nib line: the same path, two media.
  4. Pigment compositing: two overlapping washes, showing glazing versus mixing.
  5. Hand lettering: a word, then a title block.
  6. Composition: a small still life or botanical study combining all of the above.
  7. Data-driven application: a route map (OSM + elevation) as *one* capstone, alongside other capstones such as a botanical plate, a sketchbook page, a greeting card or a chart painted in watercolour.
- Borrow Nature of Code's running project: the same small scene could grow chapter by chapter, so each primitive lands in a composition the learner already cares about.
- Borrow Nature of Code's discovery move: let learners use a primitive concretely (paint a wash with explicit parameters) before naming the abstraction (a `Wash` type, a pigment model).
- Since pyntpot is Python, not browser JS, the closest analogue to "Open in Web Editor" is a downloadable `.py`/`.ipynb` per example (sphinx-gallery or mkdocs-gallery produce these) and possibly JupyterLite/Binder. That is an inference. I did not verify pyntpot's runtime compatibility with Pyodide.
- Red Blob's "inputs change, outputs shown" pattern can be approximated statically with *parameter strips*: one image per parameter value (wetness 0.2/0.5/0.8) in a row. This gives explorable-like intuition without an interactive runtime.

### Gaps
- I could not fetch a Ciechanowski article (ciechanow.ski/watch returned 404). I found no primary source describing his method, so treat any claims about his process as unsourced.
- I did not research The Coding Train, Processing.org's learn pages, Shadertoy or Inigo Quilez's articles in this pass.
- I could not confirm from the hub page whether p5.js tutorials embed live editable sketches inline.

## 3. Galleries, cookbooks and recipe pages

### Takeaway
Gallery-first docs work because each item is a short, runnable script with its rendered output, a 1 to 3 sentence description, and back-links to the API it demonstrates, so reference pages show "examples using this function". Gallery items "teach by demonstration", which is a different job from tutorials.

### Cited Findings
- Matplotlib: "Sphinx Gallery finds `*.py` files in source directories and runs the files to create images and narrative that are embedded in `*.rst` files". It keeps four galleries: plot_types, examples, tutorials, and users_explain. — [Matplotlib: writing documentation](https://matplotlib.org/devdocs/devel/document.html)
- Matplotlib: "Gallery examples should contain a very brief description of *what* is being demonstrated and, when relevant, *how*… Unlike tutorials or user guides, gallery examples teach by demonstration, rather than by explanation or instruction." — [Matplotlib: writing documentation](https://matplotlib.org/devdocs/devel/document.html)
- Matplotlib's code rule: "Write the minimum necessary to showcase the feature that is the focus of the example. Avoid custom styling and annotation… when it will not improve the clarity". Titles run about 1 to 6 words, with no "demo" and simple present tense ("Fill the area between two curves"). Descriptions run "approx 1-3 sentences". Plots should be "uncluttered". Figure width is capped at 720px. — [Matplotlib: writing documentation](https://matplotlib.org/devdocs/devel/document.html)
- Matplotlib's back-references: a trailing "References" admonition lists the API objects an example uses, so "sphinx-gallery [can] place an entry to the example in the mini-gallery of the mentioned functions". Only list functions the example actually illustrates. Ordering is controlled by `gallery_order.txt`. — [Matplotlib: writing documentation](https://matplotlib.org/devdocs/devel/document.html)
- Matplotlib's tutorials use `# %%` cell separators so text, code and figures render "notebook" style and IDEs can re-run cells. The `.. plot::` directive embeds figures in docstrings. — [Matplotlib: writing documentation](https://matplotlib.org/devdocs/devel/document.html)
- Sphinx-Gallery: "running pure Python example scripts while capturing outputs + figures"; generates a Jupyter notebook per example; builds mini-galleries of every example using a given function; links names in example code to API docs via intersphinx; supports image scrapers for other libraries (seaborn named). — [Sphinx-Gallery](https://sphinx-gallery.github.io/stable/index.html)
- Manim's example gallery groups items under Basic Concepts, Animations, Plotting, and Special Camera Settings. Each item has an anchored heading, rendered output, full copy-pasteable code (MIT-licensed, "feel free to copy & paste"), and a "References:" line linking to the classes used. Docs build utilities include a `manim_directive` module. — [Manim examples](https://docs.manim.community/en/stable/examples.html)
- Diátaxis treats recipes as how-tos: a recipe defines what it achieves and assumes competence. — [Diátaxis how-to guides](https://diataxis.fr/how-to-guides/)

### Inferences
- A pyntpot gallery should be the docs landing page's visual front door: a thumbnail grid of finished images, each linking to a short script. Every primitive's reference page should then show a mini-gallery ("Examples using `Wash`"). This turns the reference into a discovery tool and satisfies Write the Docs' "Discoverable" principle.
- Gallery categories should be organised by *medium/primitive* (Paper, Washes, Brushes, Nibs, Pigments, Lettering, Composition) plus *Applications* (Maps, Botanical, Cards…). Maps then reads as one shelf among many, not the identity of the library.
- Write gallery titles as artefacts ("Graded sky wash", "Granulating ultramarine"), not as "demo of X".
- Keep a cookbook (how-tos) separate from the gallery. Gallery items are one-image demonstrations; recipes are goal statements with steps and branches ("How to match a printed paper size and DPI").

### Gaps
- I did not fetch seaborn's or D3/Observable's gallery documentation. Nothing in my findings explains *why* they succeed beyond the sphinx-gallery mechanics.
- I did not verify mkdocs-gallery (the MkDocs equivalent) in this pass, which matters if pyntpot uses MkDocs rather than Sphinx.

## 4. Executable and tested examples

### Takeaway
Docs examples should run in the docs build and/or the test suite, so images and outputs cannot drift. Sphinx-Gallery executes scripts at build time. Sybil runs code in rST, Markdown and MyST docs within pytest. Write the Docs ranks incorrect docs as worse than missing ones.

### Cited Findings
- Write the Docs "Current": "Consider incorrect documentation to be worse than missing documentation." "Nearby": "Store sources as close as possible to the code which they document." — [Write the Docs principles](https://www.writethedocs.org/guide/writing/docs-principles/)
- Matplotlib's example scripts run during the docs build, so figures reflect current code. It has escape hatches: `make html-noplot`, `html-skip-subdirs`, and an `sgskip` filename marker. — [Matplotlib: writing documentation](https://matplotlib.org/devdocs/devel/document.html)
- Sybil "provides a way to check examples in your code and documentation by parsing them from their source and evaluating the parsed examples as part of your normal test run". It integrates with pytest and unittest, has parsers for ReST, Markdown and MyST, handles doctest and code-block examples, and documents migration from `sphinx.ext.doctest`. — [Sybil](https://sybil.readthedocs.io/en/latest/)
- Diátaxis warns that product changes cascade through tutorials ("underestimating maintenance") and demands "perfect reliability". — [Diátaxis tutorials](https://diataxis.fr/tutorials/)

### Inferences
- For pyntpot: (a) tutorial and gallery scripts should be ordinary `.py` files executed by the docs build, with output PNGs never committed by hand. (b) The same scripts should be imported or run by a pytest test that compares outputs against pinned golden images or hashes, reusing pyntpot's existing golden-tolerance machinery (CLAUDE.md: golden values are pinned literals, CI uses `--golden-tolerance`). (c) Markdown/MyST prose snippets should be checked with Sybil, which uses pytest and no mocking, consistent with pyntpot's testing rules.
- README code should also be tested, for example through Sybil over README.md, so the quick start cannot rot.
- Determinism (fixed RNG seeds, bundled fonts, a fixture OSM/elevation box such as the Lynmouth fixture) is a precondition for both reliable tutorials and stable doc images.

### Gaps
- I did not fetch the stdlib `doctest` or pytest `--doctest-modules` docs, or projects' CI configurations showing docs-build-as-test. These mechanisms are well known but uncited here.
- I found no source quantifying how often untested docs examples break.

## 5. What makes an excellent README for a visual library

### Takeaway
For a visual library, show output before prose: a hero image or grid, then a one-line description, then the single shortest install-and-run snippet that produces a picture, then links out. Keep the README short and let the docs site carry depth.

### Cited Findings
- awesome-readme highlights examples that pair a logo and clear description with a demo screenshot. It lists images, screenshots and GIFs as elements of good READMEs. — [awesome-readme mirror](https://git.hackliberty.org/Awesome-Mirrors/awesome-readme/src/branch/revert-150-master) (mirror; I did not verify the current upstream repo)
- In a README-examples write-up, Prettier's README is praised for opening with a punchy description and an animated GIF of the tool in action, "the visual does more work than three paragraphs". Create React App leads with one command to get started; the advice is to keep the one command that proves the project works above everything optional. Poetry keeps the README short and links out. — [docsio blog: README examples](https://docsio.co/blog/readme-examples) (secondary blog; moderate reliability)
- Diátaxis's "Show the learner where they'll be going" and "Deliver visible results early" apply to the README's quick start as a micro-tutorial. — [Diátaxis tutorials](https://diataxis.fr/tutorials/)
- Every p5.js tutorial card leads with a preview image of the result. — [p5.js tutorials](https://p5js.org/tutorials/)

### Inferences
- A suggested pyntpot README order:
  1. Hero image, ideally a 2×3 grid of *different* subjects (botanical wash, ink sketch, lettered card, route map) to signal breadth.
  2. One sentence on what it is.
  3. `uv add pyntpot` (or pip).
  4. A runnable snippet of about 10 lines that saves a PNG, with that exact PNG shown beneath it.
  5. Links: Tutorials, Gallery, How-to, Reference, Explanation.
  6. Licence.
- Show the quick start's output image *under* the code ("narrative of the expected").
- Use real committed images regenerated by CI from the same script, so the hero image never drifts from the code.

### Gaps
- Art of README (hackergrrl) returned 404 on GitHub and raw, so I could not cite it. Its "cognitive funnelling" idea is therefore unsourced here.
- Most README guidance found is secondary (blogs and skill pages). I found no authoritative primary study.

## 6. Writing quality: voice, brevity, second person, outputs, no marketing

### Takeaway
Write like a knowledgeable friend: conversational and direct, second person and imperative, no hype, no "simply/easy", no exclamation marks. Show the expected output at each step. Diátaxis endorses tutorial "we" while Google discourages "let's", so choose a convention and apply it consistently.

### Cited Findings
- Google style: "conversational, friendly, and respectful"; "Try to sound like a knowledgeable friend who understands what the developer wants to do"; the reader "may be in a hurry". — [Google style: voice and tone](https://developers.google.com/style/tone)
- Google says to avoid buzzwords, being too cutesy, "please note"/"at this time", exclamation marks, "simply, It's that simple, It's easy, or quickly in a procedure", "let's do something" phrasing, and starting every sentence the same way. Its too-informal example: "Dude! This API is totally awesome!" Its just-right example: "This API lets you collect data about what your users like." It also advises reading sections aloud. — [Google style: voice and tone](https://developers.google.com/style/tone)
- Google style: "address the reader… using the second person instead of the first person". Use the imperative for instructions ("Click **Submit**"). "We" is acceptable only for the authoring organisation, with a clear antecedent. Identify who "you" is and stay consistent. — [Google style: person](https://developers.google.com/style/person)
- Conflict: Diátaxis recommends "we" in tutorials to signal shared effort and uses "Let's check…" as a cue ([Diátaxis tutorials](https://diataxis.fr/tutorials/)). Google discourages "let's" ([Google style: voice and tone](https://developers.google.com/style/tone)).
- Write the Docs: "ARID" (accept some repetition), "Skimmable", "Exemplary" (include examples), "Consistent", "Complete" ("cover concepts in full, or not at all"), "Beautiful" ("Visual style should be intentional and aesthetically pleasing"). — [Write the Docs principles](https://www.writethedocs.org/guide/writing/docs-principles/)

### Inferences
- A reasonable pyntpot house rule: second person and imperative everywhere. "We" is allowed sparingly inside tutorials only, per Diátaxis. "Let's", "simply", "just", "easy" and "beautiful results" are banned. These could be enforced by a docs lint (Vale or a test), in keeping with the project's gate culture.
- "Beautiful" matters more than usual for an art library. The docs site's own typography and image presentation is part of the pitch, which aligns with Red Blob's dedicated polish pass.
- ARID tension: pyntpot's CLAUDE.md demands one canonical name per concept (GLOSSARY.md). Repetition of *content* is acceptable; repetition of *synonyms* is not.

### Gaps
- I did not find a source specifically on writing for artists or creative audiences, for example explaining a painting term such as "glazing" versus a code concept.
