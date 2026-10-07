# Exemplary visually distinctive and artistic documentation sites (for pyntpot docs)

Research date: 2026-10-07. Tool budget limited this to about 18 searches and fetches. Sites I fetched directly are cited. Points from background knowledge that I did not re-verify this session are marked **[unverified]** and kept out of "Cited Findings".

## Per-site catalogue: visual identity, navigation, example presentation, readability

### Takeaway
The creative-coding docs that work best are not the ones with painterly chrome. They put **the library's own output next to the code that made it**, every time: Rough.js puts a sample image beside each snippet, Manim pairs each rendered video with its source and API links, sphinx-gallery builds thumbnails by running the scripts, and Prettymaps leads with one map hero. The chrome stays plain, usually Furo or a near-default theme. Where a hand-drawn identity is applied to the UI itself, as in Excalidraw, it is held to headings, borders and accents, while body text, code and focus rings stay precise.

### Cited Findings

**Rough.js** (sketchy rendering library, the basis of Excalidraw-style art)
- The tagline is the identity: "Create graphics with a hand-drawn, sketchy, appearance". The hero is a title, the tagline and links (GitHub, API wiki, sponsor), followed by a "Rough.js sample" image. — [roughjs.com](https://roughjs.com/)
- The page is a single long scroll: Install, Usage (Canvas, SVG), Lines and Ellipses, Filling, Sketching Style, SVG Paths, Examples, API. Each feature section pairs a short heading and description with a code snippet and the rendered sample image, which has alt text such as "Rough.js rectangle". The full API reference lives on the GitHub wiki, not the site. — [roughjs.com](https://roughjs.com/)
- Worth copying for pyntpot: one section per primitive (paper, wash, brush, nib), each with a snippet and its rendered PNG beside it.

**Rough Notation** (hand-drawn underline, box, circle and highlight annotations)
- The demo page has one section per annotation type (underline, box, circle, highlight, brackets, multiple lines). Each has a heading, a description and an "annotate" button that plays the animation on the page's own text. — [roughnotation.com](https://roughnotation.com/)
- The library is about 3.8 KB gzipped. Animation is configurable and can be turned off. The page does not mention keyboard access, reduced motion or alt text. — [roughnotation.com](https://roughnotation.com/)
- Takeaway: hand-drawn highlights are cheap in page weight, but accessibility is left to the integrator.

**Excalidraw** (hand-drawn whiteboard; its design system is described by a third-party "design.md" teardown, not an official Excalidraw source)
- The philosophy is "draw it badly on purpose". Excalifont (successor to Virgil) is a handwriting display face for headings only. Body text is **Assistant**, a rounded sans, at 16px with 1.55 line height. Code is Cascadia Code. — [webdesignhot design.md: Excalidraw](https://www.webdesignhot.com/design.md/excalidraw/)
- Colour: paper-white canvas `#fffefd` with a faint cream undertone, near-black text `#1b1b1f`, and one muted purple `#6965db` for actions and links. Marker pastels appear **only as shape fills, never as UI surfaces or calls to action**. — [same](https://www.webdesignhot.com/design.md/excalidraw/)
- Cards use a 2px hand-drawn near-black border instead of shadows for elevation. Focus rings stay precise even though borders are rough. Reduced-motion settings turn hover lifts and rotations into opacity changes. Touch targets are at least 44px. The teardown claims contrast of about 16.8:1 for text and 4.7:1 for white on purple; I did not verify these figures. — [same](https://www.webdesignhot.com/design.md/excalidraw/)
- Dark mode follows `prefers-color-scheme` with a manual toggle. The background is warm near-black `#121212`, not pure black. Purple lifts to `#8b87e6`, the hand-drawn borders invert to light grey and the pastels are muted. — [same](https://www.webdesignhot.com/design.md/excalidraw/)
- Excalidraw's look is built on rough.js. tldraw and Whimsical are described as its descendants. — [same](https://www.webdesignhot.com/design.md/excalidraw/)

**tldraw**
- The SDK bundles IBM Plex (Sans, Serif, Mono) plus **Shantell Sans** for "draw"-style text on the canvas. The UI inherits the host font; the docs' example sets it to Inter. — [tldraw DOCS.md (npm 5.4.2)](https://cdn.jsdelivr.net/npm/tldraw@5.4.2/DOCS.md)
- A third-party guide describes tldraw's UI as light mode, Inter, on a 4px grid: the hand-drawn feel is confined to the canvas, not the chrome. — [tessl tldraw-ui-skills](https://tessl.io/registry/skills/github/ihlamury/design-skills/tldraw-ui-skills)

**Manim Community** (maths animation, Python, closest structural analogue to pyntpot)
- Built with Sphinx and the **Furo** theme, with a left sidebar, "Edit this page" and "View this page" links, a version label and light and dark logo variants. — [docs.manim.community examples](https://docs.manim.community/en/stable/examples.html)
- The Examples page is grouped into Basic Concepts, Animations, Plotting, and Special Camera Settings. Each "Example: Name" shows the rendered image or video, then the source, then a "References" list linking the API objects used. It also links an online Jupyter environment for running examples without installing anything. — [same](https://docs.manim.community/en/stable/examples.html)
- The ManimCE logo example uses a warm off-white `#ece6e2` background. — [same](https://docs.manim.community/en/stable/examples.html)
- Worth copying: the output → code → "References" (API cross-links) triad.

**matplotlib + sphinx-gallery**
- sphinx-gallery runs each example script during the docs build, captures the figures and builds gallery pages with thumbnails. It can also offer each example as a downloadable .py file and a Jupyter notebook. — [tessl summary of sphinx-gallery (third party)](https://tessl.io/registry/tessl/pypi-sphinx-gallery); [HoloViz nbsite gallery guide](https://nbsite.holoviz.org/user_guide/gallery.html)
- Default thumbnails are 400×280 px, scaled by CSS to about 160×112. The default image scraper is matplotlib, configurable through `image_scrapers` and `thumbnail_size`. — [matplotlib gen_gallery.py source](https://dods.mbari.org/data/lrauv/oavenv/build/matplotlib/doc/sphinxext/gen_gallery.py); [tessl config ref](https://tessl.io/registry/tessl/pypi-sphinx-gallery/files/docs/extension-setup.md)
- Relevance: a custom scraper can collect pyntpot's raster outputs (PIL or numpy images) the same way, so the docs build doubles as a smoke test of every example.

**Prettymaps** (Python map-art library, closest domain analogue)
- The README leads with one large hero map (Heerhugowaard), then badges. A second inline image shows "Macau, custom parameters". The wider gallery (Macau, Barcelona plotter, Tijuca, mosaic, multiplot, hillshade and others) lives in `docs/tutorial.md`. — [github.com/marceloprates/prettymaps](https://github.com/marceloprates/prettymaps)
- Docs use **MkDocs** (`mkdocs.yml`) on GitHub Pages. The tutorial exists three ways: as markdown, as a runnable marimo notebook, and on Colab. Named JSON **presets** (`default`, `minimal`, `macao`, `tijuca`) act as the style vocabulary. There is a hosted **Streamlit** demo at prettymaps.streamlit.app. — [same](https://github.com/marceloprates/prettymaps)
- Worth copying: named presets as gallery entries, each preset shown as one rendered thumbnail.

**vsketch / vpype** (plotter generative art)
- vsketch docs use Sphinx with Furo and autoapi, and a plain sidebar (Installation, Overview, Contributing, API Reference). The landing page shows no gallery images. — [vsketch.readthedocs.io](https://vsketch.readthedocs.io/en/latest/)
- This is a counter-example: an art library whose docs show none of its art.

**p5.js**
- Reference entries have a title and description, then Examples, Syntax, a Parameters list, an invitation to report errors, and "Related References" cards. The site has skip-to-content and a header "Accessibility" link, with top navigation to Reference, Tutorials, Examples, Contribute, Community and About plus a "Start Coding" call to action. — [p5js.org/reference/p5/ellipse](https://p5js.org/reference/p5/ellipse/)
- Accessibility is long-running work: a fellowship redesign of the learning resources and editor with input from people with low vision and blindness, from 2016 on. — [Processing Foundation: P5 Accessibility](https://processingfoundation.org/blog/p5-accessibility/); [Making p5.js Accessible](https://processingfoundation.org/blog/making-p5js-accessible/)
- Sovereign Tech Fund-backed work describes publishing documentation "on a new site designed and developed with accessibility-first approach", with 100+ documents reworked by 70+ contributors. — [sovereign.tech/tech/p5js](https://www.sovereign.tech/tech/p5js)
- A 2026 microgrant targets clearer link styling, better colour contrast and cues that do not rely on colour alone in Web Editor themes. — [Processing Foundation microgrant 2026](https://processingfoundation.org/programs/grants/oss-microgrants/2026/izzy-snyder/)

**Svelte tutorial** (live-editor pattern)
- A sidebar of lessons is grouped into Basic and Advanced Svelte, and Basic and Advanced SvelteKit. Each lesson shows prose with a file tree and a line-numbered editor, a **"solve"** button that reveals the answer (disabled on lessons without an exercise), previous and next links, and a Vim-mode toggle. — [svelte.dev/tutorial](https://svelte.dev/tutorial)

**Julia Evans / Wizard Zines** (hand-drawn teaching)
- The first zine was drawn with Sharpie and pen on half-letter paper. Later ones were drawn on a Samsung tablet with S Pen in Autodesk Sketchbook, then assembled with ImageMagick, pdftk, pdfcrop and pdfjam. — [jvns.ca: How I made a zine](https://jvns.ca/blog/2016/08/29/how-i-made-a-zine/)
- Her reasoning is that a fun, small format makes intimidating tools (strace, tcpdump) approachable. — [same](https://jvns.ca/blog/2016/08/29/how-i-made-a-zine/)
- She says she "only draws stick figures": the hand-made quality is deliberately simple, not virtuosic. Each zine is kept to one narrow topic. — [egghead podcast](https://egghead.io/podcasts/exploring-concepts-and-teaching-using-focused-zines-with-julia-evans); [Humans+Tech episode](https://humansplustech.buzzsprout.com/800381/episodes/5206942-julia-evans)

**Interactive or explorable articles** (Ciechanowski-style)
- Hohman et al. (Distill 2020) name five affordances of interactive articles: connecting people and data, making systems playful, prompting self-reflection, personalising reading and reducing cognitive load. — [Communicating with Interactive Articles](https://mlanthology.org/distill/2020/hohman2020distill-communicating)
- Their effectiveness with real audiences is under-studied. — [UW IDL: Idyll analytics](https://idl.uw.edu/papers/idyll-analytics)

### Inferences
- **Recurring pattern:** a plain, high-contrast reading shell (Furo, Starlight or MkDocs Material), with **the art carried by generated example output**, not decorative chrome. Manim, matplotlib and Rough.js all follow it, and it suits a raster-painting library: every docs page can show a real painted PNG.
- **For pyntpot specifically:** sphinx-gallery with a custom image scraper, or an MkDocs and mkdocs-gallery equivalent, gives (a) a thumbnail grid, (b) the output → code → API cross-link triad from Manim, and (c) build-time execution, which fits the project's "the gates are the truth" ethos. The pinned golden images could double as gallery art.
- **Before/after pairs** (vector input → painted output, such as a raw OSM layer beside its wash) are an obvious pyntpot-specific pattern. Prettymaps' preset gallery comes close but does not show inputs.
- **[unverified]** three.js: a dark full-bleed grid of live WebGL example thumbnails with a filter box, and docs in a separate plain reference. Observable and D3: notebook cells that render live output above the code. Stripe: a three-column layout with prose, code panel and language switcher, a reference point for clarity not art. Tailwind: an in-page live preview above each snippet. Astro Starlight: an accessible default docs theme with light and dark modes, aimed at WCAG. OPENRNDR and Nannou: guide books, OPENRNDR with inline rendered sketch images. Processing.org: reference pages with a static output image beside each code example. _Why's (Poignant) Guide to Ruby: cartoon foxes and digressions, beloved but criticised as hard to use as reference. None of these was fetched this session, so the report writer should treat them as leads.

### Gaps
- I did not fetch three.js, Processing, drawsvg, Observable and D3, Stripe, Tailwind, Astro Starlight, Shapely and GeoPandas galleries, Nannou, OPENRNDR, Kenney, Wattenberg or the Poignant Guide this session, so I have no cited specifics for them.
- I could not confirm the p5.js site's current framework (Astro was suspected) or the launch date of its redesign.
- Screenshots were not captured. The fetch tool returns text only, so visual details (exact fonts and colours) are unconfirmed except for the Excalidraw teardown and the Manim colour value.

## Which sites use painted or hand-made art as UI elements, and how well does it work?

### Takeaway
I found real hand-made UI chrome only in the whiteboard tools (Excalidraw, tldraw) and in Rough Notation used as an accent. In each case it is limited to display type, borders, highlights and illustrations; body text, code, focus states and navigation stay crisp. I found no well-known creative-coding docs site that uses painted textures as page backgrounds.

### Cited Findings
- Excalidraw puts its handwriting face (Excalifont/Virgil) on headings and on-canvas notes only, and pairs it with a rounded sans for body text. Its rough.js hand-drawn borders replace shadows as the elevation device. Pastel colours are kept off UI surfaces and calls to action. Focus rings stay precise. Negative letter-spacing on display sizes stops the handwriting looking too casual. — [webdesignhot design.md: Excalidraw](https://www.webdesignhot.com/design.md/excalidraw/)
- tldraw keeps Shantell Sans for "draw"-style canvas text, and the UI uses whatever the host sets (Inter in the example). — [tldraw DOCS.md](https://cdn.jsdelivr.net/npm/tldraw@5.4.2/DOCS.md); [tessl tldraw-ui-skills](https://tessl.io/registry/skills/github/ihlamury/design-skills/tldraw-ui-skills)
- Rough Notation provides hand-drawn underline, box, circle, highlight and bracket marks at about 3.8 KB gzipped, with animations that can be disabled. — [roughnotation.com](https://roughnotation.com/)
- Julia Evans' hand-drawn art is the content itself (comic pages), not decoration around text. — [jvns.ca](https://jvns.ca/blog/2016/08/29/how-i-made-a-zine/)

### Inferences
- For pyntpot, the natural move is **eating its own cooking**: use pyntpot-painted assets as limited UI elements, such as a wash swatch behind the logo or hero, painted section dividers, a hand-lettered wordmark, or a nib-stroke underline on H1s. Keep body text on a flat paper-tone background. This follows Excalidraw's split (expressive display, sober body).
- Painted elements should be raster images with explicit width and height, light and dark variants, and `alt=""` when purely decorative, so they do not hurt layout stability or screen readers.
- A watercolour wash under a heading should sit behind the type with enough lightness margin to keep 4.5:1 contrast on its darkest pigment pooling (edge darkening), not just on its average colour.

### Gaps
- I found no published case study or measurement of how painted UI chrome affects reader comprehension or task time in docs.
- I did not verify any docs site using watercolour textures as backgrounds. Absence in this sample is not proof that none exist.

## Common pitfalls of artistic docs (legibility, contrast, distraction, page weight, dark mode)

### Takeaway
The documented failures are mundane. Low-contrast grey or textured backgrounds behind thin type, a palette tuned only for light mode, and decorative motion with no reduced-motion fallback. Handwriting fonts in body text and heavy decorative images are the main risks specific to an artistic identity.

### Cited Findings
- On Pulp's docs, a user reported that the grey background "made the thin black font difficult/uncomfortable to read". It was fixed by switching to a higher-contrast theme. — [Playdate devforum: Pulp docs background](https://devforum.play.date/t/background-for-pulp-documentation-makes-it-difficult-to-read/1964)
- A user complained that Hugo's `#555` body text was too faint and caused eyestrain, and asked for something closer to black. — [Hugo discourse](https://discourse.gohugo.io/t/hugo-documentation-webpage-contrast-too-low-getting-eyestrain/13255)
- The Python docs theme had colour-coded type that became nearly invisible in dark mode with a night-shift filter. — [python-docs-theme #145](https://github.com/python/python-docs-theme/issues/145)
- Colours that work in light mode may lack contrast in dark mode, so review both themes. — [Document360 colours and typography](https://docs.document360.com/docs/colors-and-typography)
- VGS rebuilt its palette to meet WCAG 4.5:1 on light and dark backgrounds. It kept a display face for headings and moved body text to Inter for readability. — [VGS new look](https://www.verygoodsecurity.com/blog/posts/vgs-new-look)
- A reviewer flagged thin font weights on a docs page as hard to read. — [freeCodeCamp forum](https://forum.freecodecamp.org/t/technical-documentation-page-in-dark-mode-hurrah/399522)
- Excalidraw's dark mode avoids pure black (`#121212`), brightens its accent colour and mutes its pastels. Reduced-motion settings turn decorative motion into opacity changes. — [webdesignhot design.md: Excalidraw](https://www.webdesignhot.com/design.md/excalidraw/)
- Rough Notation's demo page does not address keyboard or reduced-motion behaviour. — [roughnotation.com](https://roughnotation.com/)
- vsketch, a generative-art tool, shows no output art on its docs landing page: the reverse failure, an artistic library with visually empty docs. — [vsketch docs](https://vsketch.readthedocs.io/en/latest/)

### Inferences
- **Paper texture behind body text** is the biggest risk for pyntpot. Grain and noise lower effective contrast even when the colour values pass (the Pulp grey-background case is the mild version). Keep the reading column flat, and put texture in margins, the hero and dividers.
- **Dark mode is hard for watercolour:** painted art on white paper does not invert. Options are to show artwork in a "paper card" framed on a dark page (as Manim's examples sit on their own off-white `#ece6e2` background), or to paint dark-paper variants. Do not CSS-invert raster art.
- **Page weight:** a gallery of full-resolution raster paintings is heavy. Ship thumbnails at the sphinx-gallery default scale (400×280) in WebP or AVIF, lazy-load them, and link to full size, as Prettymaps links its hero to the full-size image.
- **Handwritten lettering** (pyntpot's own hand lettering) belongs in display sizes and in the art only. Use a highly legible sans or serif for body text and a clear monospace for code.
- **Golden-image gallery drift:** if the gallery is regenerated at build time, changes to the art become visible in docs diffs, which is useful. Pin seeds so thumbnails are deterministic.

### Gaps
- I found no authoritative source (WCAG technique, Smashing or Awwwards article) specifically on textured backgrounds or handwriting fonts in docs. Searches returned generic or low-quality results, so the related guidance above is inference.
- I found no measured page-weight figures for creative-coding gallery sites.
- Hacker News threads on "beautiful docs" were not reached within the tool budget.
