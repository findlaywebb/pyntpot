# How visual and creative-coding libraries document themselves

Research note for P7 (docs and 0.1.0). Angle: pyntpot's output is a picture, so its docs
should be image-first; how do libraries whose output is a picture keep their pictures
honest, small and in step with the code? Sources were checked live on 2026-10-23 unless
marked "from knowledge".

## What pyntpot already has

- Eight rung scripts in `examples/` (paper, wash, brush_stroke, nib_line, pigments,
  lettering, composition, route_map), each with a module docstring that is already
  tutorial prose: what the rung does, the public names it introduces, how to run it. Each
  has `main(out_dir) -> Path`.
- `tests/support/examples.py::run_example` loads a script without its `__main__` block and
  calls `main`. `tests/examples/` checks size, mode and "not one flat colour"; the route
  map runs offline from the Lynmouth fixture cache with providers pointed at a dead port.
- `tests/architecture/test_examples.py` checks that scripts import public names only.
- Golden parity for the Lynmouth render (`tests/golden/lynmouth/`: `map.png` 2.6 MB,
  `paper.webp` 1.4 MB, `wash.webp` 1.1 MB), exact locally, `--golden-tolerance` on CI
  (`.github/workflows/golden.yml`), regeneration governed by ADRs 0006 and 0025.
- D13: README with a gallery, `docs/` in Diátaxis layout, no docs site at v0.1.

That is most of a sphinx-gallery already, minus the rendering step. The ink rungs are not
golden-pinned: a script could drift visually and its test would stay green.

## Case studies

### sphinx-gallery and matplotlib: scripts are the gallery

sphinx-gallery (https://sphinx-gallery.github.io/stable/configuration.html) turns a
directory of `.py` files into a gallery: the module docstring becomes the page's
introduction, `# %%` comment blocks become prose between code cells, each figure the
script makes is captured by an image scraper (`image_scrapers`) and becomes the thumbnail
(`sphinx_gallery_thumbnail_number` picks which). `filename_pattern` selects which scripts
run; `plot_gallery = False` builds without executing. The feature most worth stealing is
backreferences: with `doc_module` and `backreferences_dir` set, every API entry gets an
"Examples using X" strip of thumbnails, and a `minigallery` directive drops the same strip
anywhere. scikit-image's API page shows it at work: `skimage.filters.gaussian` carries five
example cards (https://scikit-image.org/docs/stable/api/skimage.filters.html). Each example
page also offers a download of the script and notebook, so the reader leaves with code
that produced exactly the image they saw.

Matplotlib's gallery (https://matplotlib.org/stable/gallery/) has two kinds of page worth
copying. The first is the **reference sheet**: one image enumerating every value of a
categorical option, such as the colormap reference
(https://matplotlib.org/stable/gallery/color/colormap_reference.html), the line-style
sheet (https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html) and
the marker reference. The second is the **parameter sweep**: the same input rendered under
each setting in a grid, as in "Interpolations for imshow"
(https://matplotlib.org/stable/gallery/images_contours_and_fields/interpolation_methods.html).
Its explanation page "Choosing colormaps"
(https://matplotlib.org/stable/users/explain/colors/colormaps.html) mixes generated
figures with perceptual argument, every figure from code on the page. Matplotlib also has
a `.. plot::` directive so docstrings can carry rendered images on reference pages (from
knowledge).

### Keeping images truthful: baselines, hashes, screenshots

Matplotlib's test suite (https://matplotlib.org/devdocs/devel/testing.html) uses
`@image_comparison(baseline_images=[...], tol=...)`, failing when the mean per-pixel
difference exceeds `tol`, with baselines committed under
`lib/matplotlib/tests/baseline_images/`. The page warns that baselines "take a lot of
space in the Matplotlib repository" and steers new tests to `check_figures_equal` (two
drawings that should agree) or to asserting values when feasible. Regeneration is a
deliberate human act: copy from `result_images/`, or accept in `tools/triage_tests.py`;
`tools/visualize_tests.py` compiles failures into one HTML page of expected, actual and
diff.

pytest-mpl (https://pytest-mpl.readthedocs.io/en/latest/configuration.html) separates the
two concerns repo size forces apart: `--mpl-hash-library` pins a JSON of image hashes in
the repo, while `--mpl-baseline-path` may be a **URL**, so the baseline images live
elsewhere; `--mpl-generate-summary=html` writes a visual diff report, and
`--mpl-default-tolerance` sets the RMS bound.

three.js (https://threejs.org/examples/) is the cleanest case of "the gallery thumbnail
*is* the regression baseline". `test/e2e/puppeteer.js`
(https://github.com/mrdoob/three.js/blob/dev/test/e2e/puppeteer.js) renders every example
in headless Chrome, screenshots it at 800 by 500, scales it to 400 by 250 JPEG at quality
95, and compares with `examples/screenshots/<name>.jpg` (pixel threshold 0.1, fewer than
0.1% of pixels may differ); on failure it writes `-actual`, `-expected` and `-diff`
images. The same JPEGs are the thumbnails on the examples page, regenerated with
`--make`. Small, lossy, and still honest, because the check is against the same file the
reader sees.

manim (https://docs.manim.community/en/stable/contributing/docs/examples.html) renders
every `.. manim::` block in the docs with the current version at build time, preferring
`save_last_frame` stills because they are cheap; so its gallery cannot show a scene the
library no longer produces. Its graphical unit tests compare frames against stored control
data (from knowledge).

### Reference pages that carry pictures

Processing's reference (https://processing.org/reference/ellipse_.html) puts a short code
sample and its output image at the top of every entry, before syntax and parameters. p5.js
(https://p5js.org/reference/) goes further with live, editable sketches on each entry, plus
a separate Learn section of tutorials: the split between reference and tutorial is the
Diátaxis split, done by a creative-coding project. Cartopy's projection list
(https://scitools.org.uk/cartopy/docs/v0.21/reference/projections.html) gives every
projection class one rendered world map; it is the model for "one image per enumerated
member", which in pyntpot means one swatch per `PIGMENTS` entry and one cell per brush id.
Shapely's manual (https://shapely.readthedocs.io/en/stable/manual.html) numbers its figures
and links each to the standalone script and PNG, hi-res PNG and PDF it came from.

### Explaining the algorithm

Datashader's pipeline page (https://datashader.org/getting_started/Pipeline.html) opens
with a stage diagram (steps across the top, data structures along the bottom), then walks
each stage with its intermediate output, and compares four reductions side by side in one
`tf.Images` call. Tyler Hobbs' "A Guide to Simulating Watercolor Paint with Generative
Art" (https://www.tylerxhobbs.com/words/a-guide-to-simulating-watercolor-paint-with-generative-art)
explains recursive polygon deformation, layering, variance and texture masking with about
20 process images, one per stage, ending in finished work; it states parameters in prose
but has no systematic sweeps, which is the gap a library's explanation page can fill.
Inconvergent's essays (https://inconvergent.net/generative/, from knowledge; the site
refused the fetch) take the same "one picture per idea" line. The canonical academic
source, Curtis et al., "Computer-Generated Watercolor" (SIGGRAPH 1997), is built on
figures that isolate one effect each: edge darkening, backruns, granulation, glazing. Those
are pyntpot's techniques too (the wash's pooled edge, paper tooth, Kubelka-Munk glazing in
`pigments.py`), so `how-the-wash-works.md` can follow that figure grammar exactly.

### Pen plotting and map renderers

vsketch and vpype (https://vsketch.readthedocs.io/, https://vpype.readthedocs.io/) document
with example sketches in the repo and photographs or renders beside them; vpype's cookbook
is task-shaped how-to. prettymaps (https://github.com/marceloprates/prettymaps) leads its
README with one striking map from `pictures/`, keeps tutorial images in `docs/img/`, and
names its presets in text without showing them: a missed chance, since a preset is exactly
the thing a picture explains. MapLibre's style specification pairs each property with live
examples (from knowledge). The lesson for a map renderer: show each style choice, not
only the hero map.

### Hosting, size and PyPI

PyPI renders the README through `readme_renderer`, whose sanitiser
(https://github.com/pypa/readme_renderer/blob/main/readme_renderer/clean.py) allows `img`
with `src`, `width`, `height`, `alt`, `align` and `class`, and allows `picture` but **not
`source`**, so GitHub's dark-mode `<picture><source media=...>` trick degrades to the
fallback `<img>` on PyPI, and there is no `srcset`. PyPI hosts no images, and relative
paths do not resolve there (from knowledge); README images need absolute URLs, best pinned
to the release tag (`https://raw.githubusercontent.com/findlaywebb/pyntpot/v0.1.0/...`) so
the PyPI page for 0.1.0 shows 0.1.0's output forever. Git LFS objects are not served from
`raw.githubusercontent.com` in the usual way, so LFS is a poor fit for README images.

## Implications for pyntpot

### Gallery strategy that fits the harness

1. **The rung scripts are the gallery; keep them that way.** Do not add sphinx-gallery
   (D13 rules out a site). Instead add one generator, `docs/gallery/make_gallery.py` or a
   `tests/support` entry point, that calls `run_example` for every stem in
   `tests/architecture/test_examples.py::EXAMPLES`, downsizes each finished image and
   writes it to `docs/images/gallery/<stem>.webp`. The route map runs from the Lynmouth
   fixture exactly as its test does, so the gallery needs no network.
2. **Pin the gallery the three.js way.** A test regenerates each thumbnail and compares it
   with the committed one: exact locally, `--golden-tolerance` on CI, same switch as the
   parity test, marked `golden`. Then the README image is the baseline, and an ink rung can
   no longer drift visually while its test stays green. Regenerating the gallery is the
   same deliberate act ADR 0006 describes for plates; extend that ADR (or add one, since it
   widens what is pinned) rather than inventing a second process. A test also asserts every
   `EXAMPLES` stem has a thumbnail and every thumbnail a stem.
3. **Backreferences by convention, not by tool.** Each rung docstring already lists the
   public names it introduces. A small architecture test can parse "Public names it
   introduces" and check that every name in `pyntpot.ink.__all__` and
   `pyntpot.letters.__all__` is introduced by some rung, which is sphinx-gallery's
   "Examples using X" turned into a gate. `docs/reference/` then links each name to its
   rung and thumbnail.

### Which images to make

- **README** (D13 gallery): the route map (hero), the `word.py` lettered washed circle,
  then a strip of eight rung thumbnails, each linking to its script. At most about 600 px
  wide, WebP or high-quality JPEG; 2.6 MB `map.png` must not be the README image.
- **Reference sheets** (matplotlib colormap reference, cartopy projection list): one
  swatch sheet of every `PIGMENTS` entry with its name and hex, ideally each as a small
  wash disc so it shows granulation and edge pooling, not a flat box; one brush sheet of
  every brush id (`RIV1-a`, `TRK4-d`, `MAJ6-e` and the rest) as a short stroke, labelled.
  These are the single most useful images for anyone choosing a brush id, which is
  otherwise an opaque string.
- **Parameter sweeps** (matplotlib interpolation grid, datashader's side-by-side): the
  wash's two numbers in `wash(disc, sheet, 0.6, 0.3)` as a 3 by 3 grid; `GRAN_PX` across a
  row; seeds 1 to 4 to show that variation is seeded, not random; `km_glazing` off and on
  (already `pigments.py`'s two panels). Each sweep is itself a script under `examples/`
  (or `docs/figures/`) with `main(out_dir)`, so the same harness runs and pins it.
- **Explanation figures** (Curtis, Hobbs, datashader): `how-the-wash-works.md` walks
  mask, density, edge pooling, paper tooth, composite, one image per stage from one seed,
  plus a stage diagram for the map pipeline `fetch -> paint -> letter -> compose` with the
  plate each stage writes (paper, wash, pen, labels; the Lynmouth plates are already on
  disk).
- **Style how-to**: `write-a-theme.md` shows the default style beside one changed field,
  the before and after prettymaps never shows.

### Keeping them truthful

Every image in `docs/` and the README comes from a script under test; none is hand-made
or retouched. Captions name the script and seed. A test fails when an image file in
`docs/images/` has no generator, the docs analogue of the example pin. Golden values stay
pinned literals per CLAUDE.md: thumbnails are the committed bytes, never recomputed on both
sides. Image tests are `golden`-marked so the default CI job stays fast.

### Where images live

In the repo, under `docs/images/`, small: aim for each thumbnail under 60 KB and the whole
docs image set under about 2 MB (the `.git` is 12 MB today, mostly goldens). WebP at a
fixed quality is deterministic for a given Pillow pin, but lossy encoders can vary across
libwebp builds, so compare decoded pixels under the tolerance switch rather than bytes on
CI, as the parity test does. Exclude `docs/` from the sdist and wheel (check `uv_build`'s
include rules) so images do not bloat the distribution. README image URLs are absolute and
tag-pinned; the release checklist rewrites `main` to the tag before publishing, or the
README always uses the tag. No `<picture>`/`<source>` dark-mode variants, since PyPI strips
`source`; paint images on cream paper, which reads on both themes anyway.

### Changes to the P7 outline

- Add `docs/reference/brushes.md` and `docs/reference/pigments.md` with the two reference
  sheets; they are reference, not tutorial.
- Add a `docs/tutorials/` index for the eight rungs (P7.2 writes prose "around" the
  scripts: make each rung page image, then docstring prose, then the script, then "what
  changed from the last rung" with both images).
- Rename or extend `use-the-engine-without-maps.md` to point at rungs 1 to 7 rather than
  repeating them.
- Add the gallery generator, its pin test and the backreference test as P7 tasks, with an
  ADR for the widened golden set.
- Give `how-the-wash-works.md` an explicit figure list (above) and cite `references.md`
  keys per figure (D24).

### Weaving the core point and style through the imagery

pyntpot's claim is that code can paint by hand. The docs should make that claim on every
page by being painted by pyntpot, the way manim's docs are animated by manim.

- **Lettered titles.** Each docs page and the README opens with its title written by
  `Hand` on a strip of paper (`lettering.py`'s path, with the page title as the text),
  generated by one script from a list of titles. Alt text carries the plain title, and the
  Markdown `#` heading stays for accessibility, search and PyPI.
- **Section art.** Tutorials, how-to, reference and explanation each get a small header
  vignette in one consistent palette: a wash disc, a brush stroke, a nib spiral, a
  fragment of the Lynmouth map. The Diátaxis quadrants become recognisable at a glance.
- **Painted diagrams.** The pipeline diagram is itself painted: four plates drawn as
  overlapping washed rectangles with nib arrows and lettered stage names, made from the
  public API. This doubles as a composition example and proves the engine does more than
  maps, which is the README's second image's job too.
- **Painted explanatory figures.** Sweeps and stage figures are on pyntpot paper, not
  matplotlib axes; labels are lettered by `Hand` where legibility allows, plain text in
  captions where it does not.
- **Discipline.** All of it lives in one `docs/figures/` script set with `main(out_dir)`,
  run by `run_example`, pinned under the gallery test, regenerated only through the golden
  ADR. One shared style module for the docs art keeps palette and paper seed consistent.
  Keep the decoration small (headers under 30 KB), never put essential information only in
  an image, and keep the plain-text docs complete without the art: the style is the
  library's argument, not a substitute for the words.
