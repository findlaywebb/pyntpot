# P7 research 2: docs set structure and the docs-site question

Researched 2026-10-23 against the repo at `main` (README, CLAUDE.md, `docs/README.md`,
spec D13 and "Out of scope", plan P7 at `specs/001-port/plan.md:5809`, ADR 0026,
`examples/*.py`, `docs/explanation/`). Tool status facts were checked live; dates matter
because the Python docs tooling changed under our feet in the last year.

## 1. Diátaxis: what it actually asks for

Diátaxis (https://diataxis.fr/) sorts documentation by the reader's need on two axes,
action or cognition and study or work, giving tutorials, how-to guides, reference and
explanation. It grew out of Daniele Procida's Divio "documentation system"
(https://docs.divio.com/documentation-system/), which is the same four-way split under an
older name.

Two things in the framework itself are often missed by adopters, and both bear on P7:

- **It is not a template.** "How to use Diátaxis" (https://diataxis.fr/how-to-use-diataxis/)
  says the structure "is not intended to be a plan", warns explicitly against creating
  "empty structures for tutorials/howto guides/reference/explanation", and says the
  structure should emerge "from the inside" as pages improve. A `docs/how-to/` folder
  created to hold one page so the quadrant exists is the anti-pattern it names.
- **Generated reference is necessary, not sufficient.** The reference page
  (https://diataxis.fr/reference/) welcomes auto-generated API reference because it stays
  faithful to the code, but calls the belief that "auto-generated reference material is
  all the documentation required" a mistake, and says reference structure "should mirror
  the structure of the product". For pyntpot that means reference organised as
  `ink`, `letters`, `maps`, matching the layering.

### In practice at adopters

- **Django** (https://docs.djangoproject.com/en/stable/) is the canonical case (Procida is
  a Django core developer). Its index names tutorials, topic guides, reference guides and
  how-to guides, each with a one-sentence purpose and audience. Its reference is largely
  **hand-written** in Sphinx directives, not autodoc.
- **NumPy** adopted the split in NEP 44
  (https://numpy.org/neps/nep-0044-restructuring-numpy-docs.html), citing the Divio
  system, adding tutorials, how-tos and explanations around an existing generated
  reference. NEP 44 also created a docs team: the restructure was staffed work.
- **Canonical** (https://ubuntu.com/blog/diataxis-a-new-foundation-for-canonical-documentation)
  rolled it out across products and is candid: "the first thing Diátaxis does is make
  existing documentation look worse, not better", and "it's going to take time". They
  call it "unforgiving" as a lens, meaning it exposes conflation.
- The Python core docs discussion
  (https://discuss.python.org/t/adopting-the-diataxis-framework-for-python-documentation/15072)
  converged on "avoid mixing types" as the goal, not "have exactly four top-level
  sections"; splitting reference into two trees was judged fine.

### Critiques and limits

- Peter Newton (https://newton.cx/~peter/2023/divio-documentation-system/) suspects the
  quadrant is partly "we have four things, so let's put them into quadrants", doubts a
  firm line between tutorials and how-tos, and notes the framework says nothing about
  **finding aids**: landing pages and indexes.
- Emmanuel Bernard (https://emmanuelbernard.com/blog/2024/12/19/diataxis/) finds
  knowledge that fits no quadrant and observes the Diátaxis site does not itself follow
  the layout.
- Vendor guides (e.g. https://ekline.io/blog/a-technical-guide-to-the-diataxis-framework-for-modern-documentation)
  name "content drift": how-tos fill with explanation, reference fills with instructions.

The disagreement is mostly about layout, not about the core claim. Everyone, critics
included, accepts "one page, one mode"; the dispute is whether the four modes must be the
top-level navigation. Diátaxis itself sides with the critics on that.

## 2. What the best-regarded docs sets do

| Project | Engine | Reference | Note |
| --- | --- | --- | --- |
| Stripe (https://docs.stripe.com/) | custom, Markdoc | generated from OpenAPI | identity carried by consistent layout, live examples |
| Django | Sphinx | hand-written | four-mode index, long tutorial |
| FastAPI (https://fastapi.tiangolo.com/) | MkDocs Material | mkdocstrings, added late | tutorial-led "User Guide"; every example is a tested file in `docs_src/` |
| Pydantic (https://docs.pydantic.dev/) | MkDocs Material | mkdocstrings | code blocks tested by `pytest-examples` |
| polars (https://docs.pola.rs/) | MkDocs user guide, Sphinx API | generated | two engines, one site |
| httpx (https://www.python-httpx.org/) | MkDocs | mostly hand-written | small, flat, quick start first |
| attrs (https://www.attrs.org/) | Sphinx + Furo | autodoc | strong "why" explanation pages |
| SQLAlchemy 2.0 (https://docs.sqlalchemy.org/en/20/) | Sphinx | autodoc plus prose | rewrote as one "Unified Tutorial" |
| Rust (https://doc.rust-lang.org/book/) | mdBook, rustdoc | generated | doctests run by `cargo test` |
| Tailwind (https://tailwindcss.com/docs) | custom | hand-written | docs are the product demo |

Patterns that recur: examples are **files that are executed** (FastAPI, Pydantic, Rust),
not snippets that rot; the tutorial is one continuous story (SQLAlchemy, Django, Rust
Book); the landing page is a finding aid, not a table of contents; and the projects with
the strongest identity (Stripe, Tailwind, FastAPI) carry it through a consistent voice
**and** consistent visual treatment, which is a site-level property.

## 3. Style guides

- **Google developer documentation style guide** (https://developers.google.com/style/highlights):
  second person, active voice, conditions before instructions, sentence-case headings,
  code font for code, descriptive link text, alt text on every image, consistent
  terminology. It prescribes **American** spelling; pyntpot writes British English, so
  adopt the guide minus spelling and say so in `CONTRIBUTING.md`.
- **Write the Docs** "docs as code" (https://www.writethedocs.org/guide/docs-as-code/):
  docs in the repo, reviewed in PRs, built and checked in CI. pyntpot already lives this
  for code; P7 should extend it to prose.
- The repo's own GLOSSARY rule ("one canonical name, no synonyms") is stricter than
  either guide and is the most useful voice rule pyntpot has.

## 4. API reference: hand-written versus generated

- **mkdocstrings + Griffe** (https://mkdocstrings.github.io/): reads Google-style
  docstrings statically, renders their bodies **as Markdown**. pyntpot's docstrings use
  single backticks for names (`` `Sheet` ``, `` `brush_from_id` ``) and Markdown paths; under
  mkdocstrings those render as code, and with autorefs can become links.
- **Sphinx autodoc / sphinx-autoapi** with Napoleon: handles the Google sections, but the
  docstring body is reStructuredText, where single backticks are the "default role"
  (italic title reference), not code. Every pyntpot docstring would render subtly wrong
  unless `default_role` is set, and Markdown idioms in docstrings would not render. MyST
  fixes the narrative pages, not the docstrings.
- **pdoc** (https://pdoc.dev/): zero config, Markdown docstrings, Google style, one page per
  module. Excellent for reference alone, weak for narrative pages and theming.
- **Hand-written** (Django, httpx): best prose, but duplicates the docstrings, which in
  this repo are already "the agent contract", enforced by architecture tests and
  audited in D25. Hand-writing a second copy creates the drift those tests exist to stop.

Griffe also offers `griffe check` (https://mkdocstrings.github.io/griffe/guide/users/checking/),
which diffs the public API against the last tag and fails CI on breaking changes
(removed objects, changed parameters). That is a natural gate for a library whose public
surface is an ADR-governed `__all__` (ADR 0007, 0026), though it belongs to the release
phase rather than docs.

The consensus is a hybrid: generated reference for the API, hand-written reference for
things that are not Python objects (file formats, cache layout, CLI semantics), and
explanation pages carrying what docstrings cannot.

## 5. The docs-site question: challenging D13

D13 says README plus Diátaxis `docs/`, no site at 0.1; the spec's "Out of scope" repeats
it. The case for D13 is real: zero tooling, GitHub renders Markdown, relative links work,
nothing to host, nothing to break.

### What GitHub-rendered Markdown cannot do

- **No styling.** GitHub sanitises rendered HTML, removing "`script` tags, inline-styles,
  and `class` or `id` attributes" (https://github.com/github/markup). No fonts, colours,
  backgrounds or layout. `<picture>` is supported
  (https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax),
  so light and dark images are possible; that is the ceiling.
- **No generated reference.** Either the reference is hand-written (drift) or it is a
  pointer to the source.
- **No search across docs, no cross-reference resolution, no build to fail.** A broken
  link or a renamed public name surfaces only when a reader hits it, unless separate
  tools check.
- **PyPI breaks relative images.** The README is the PyPI page; its gallery images need
  absolute URLs (raw GitHub or the site) or they vanish on PyPI. True with or without a
  site, but often missed.

### Gating: both options can be gated, the site adds one gate

Without a site: `lychee` (https://lychee.cli.rs/) checks links in Markdown;
`pytest-examples` (https://github.com/pydantic/pytest-examples) runs and ruff-lints
fenced code in Markdown and docstrings; `tests/examples/` already executes the eight rung
scripts. With a site, add a **strict build** that fails on unresolved cross-references and
on any public name missing from the reference, and the gallery images are produced by
running the examples during the build, so a stale image is impossible. That fits
ADR 0001: the build becomes one more deterministic gate.

### What readers expect of a 0.1

For a 0.1 Python library a hosted site is expected rather than exceptional; most of the
table above had one early, and an API reference link on PyPI is the norm. But the bar a
0.1 reader applies is "can I get a picture out in five minutes", which the README answers.
The site is about the second visit, and about identity.

### Identity: the deciding factor for this project

pyntpot's core point is a look: hand-drawn watercolour and pen-and-ink. Docs sets carry
identity on three levels: voice (consistent person, tense, terminology), imagery (every
page shows the thing), and visual theme (type, colour, texture). GitHub Markdown carries
the first two only. A site carries all three, and here uniquely the theme can be **made
by the library**: a paper texture from `paper_plate`, heading rules and dividers from
`stamp` along a path, the palette as CSS custom properties generated from `PIGMENTS`, the
vendored Patrick Hand face (OFL 1.1 permits embedding as a web font) for headings, page
banners lettered by `pyntpot.letters`. Docs styled by the engine they document are both
proof and demo, and every such asset is a build-time execution of public API. No other
docs-as-identity example (Tailwind, Stripe) can paint its own chrome; pyntpot can.
Caution: hand-lettered display type for headings only, a plain readable face for body
and code, and contrast checked on cream paper and in dark mode.

### Engine choice in October 2026

- **MkDocs 1.x** has had no release for well over a year; a 2.0 rewrite reportedly drops
  the plugin system (secondary accounts, e.g. https://codeberg.org/Safeguarding/sciop/issues/493;
  not confirmed from MkDocs itself). **Material for MkDocs** went into maintenance mode on
  5 November 2025; critical maintenance now ends **5 May 2027**
  (https://zensical.org/upcoming-changes/). Starting a new site on it is starting on a
  frozen stack.
- **Zensical** (https://zensical.org/), from the Material team, reads `mkdocs.yml`, has
  supported mkdocstrings since 0.0.11 and cross-references and `objects.inv` since
  0.0.17 to 0.0.19 (https://mail.zensical.org/monthly/2026/01/). Latest is 0.0.71
  (16 October 2026, https://pypi.org/project/zensical/); **0.1.0, "a dependable release
  line", is due 5 November 2026**. Young, and the team's commercial tiers launch the same
  day, so budget for churn.
- **Sphinx + Furo** (https://pradyunsg.me/furo/): the most stable option, mature
  extensions (`linkcheck`, doctest, intersphinx), but the RST docstring mismatch in
  section 4 is a real tax on this repo's docstrings.
- **Hosting**: GitHub Pages via an Actions workflow is free, ad-free and enough for one
  version. Read the Docs adds per-version builds (and ads on the community plan); not
  needed until there are versions worth keeping apart.

## 6. Docs for agents

llms.txt (https://llmstxt.org/, Jeremy Howard, 2024, revised August 2026) is a Markdown
index at the site root plus `.md` twins of pages. Adoption is rising but readership is
near nil: an Ahrefs log study reported 97% of files received no requests
(https://ppc.land/llms-txt-adoption-rises-8-8x-but-97-of-files-get-zero-ai-requests/;
vendor sources, treat as indicative), and Google says it does not use it. The useful
part is the principle, not the file: Markdown-first source that an agent can fetch raw.
pyntpot's agents read the repo, where docstrings are already the contract. So: keep the
docs source plain Markdown readable on GitHub, emit `llms.txt` only if the engine does it
for free (`mkdocs-llmstxt`, https://github.com/pawamoy/mkdocs-llmstxt, is itself now in
maintenance mode), and do not write anything by hand for it.

## Implications for pyntpot

### Recommended docs tree

```
README.md                      what, gallery (absolute image URLs), install, quick start,
                               data policy and attribution, licence, link to the site
docs/
  index.md                     landing page as a finding aid: one painted image, four
                               signposted routes, one sentence each (Django's pattern)
  gallery.md                   every image generated by examples/ at build time
  tutorial/                    ONE tutorial, the eight P11 rungs as eight pages:
    index.md                   paper, wash, brush-stroke, nib-line, pigments,
    01-paper.md ... 08-route-map.md   lettering, composition, route-map
  how-to/                      only pages with a real task behind them, e.g.
                               supply-your-own-provider, run-offline-from-the-cache,
                               change-the-route-ink, credit-the-map-data, use-the-cli
  reference/
    ink.md letters.md maps.md  generated (`::: pyntpot.ink` and friends)
    style-fields.md            generated from the style groups and `Style`
    cli.md                     generated from argparse, or pinned by a test against --help
    cache-layout.md manifest.md   hand-written, with a test that the documented keys exist
    glossary.md                GLOSSARY.md included, not copied
  explanation/
    how-the-wash-works.md, the-hand-and-the-nib.md, data-policy.md,
    performance.md, references.md
  project/                     out of the site nav: decisions/, issues/, features/,
                               runbooks/, architecture.md (contributor material)
```

The current `docs/` mixes user documentation with maintainer records (ADRs, issues,
feature notes, runbooks). Diátaxis is for users; those are project records. Keep them in
the repo, exclude them from the nav (`not_in_nav`, now supported by Zensical 0.0.70), or
move them under `docs/project/`. Moving touches `CLAUDE.md`, `docs/README.md` and the
architecture tests that name these paths, so it may be better to leave paths and only
exclude from the nav.

### Docs-site recommendation

Amend D13 by ADR: **ship a small site at 0.1**, Zensical (or Material for MkDocs pinned,
if Zensical 0.1.0 slips past 5 November 2026) with mkdocstrings, deployed to GitHub
Pages. Reasons: the core point is visual and only a site can carry the look; the
docstrings are Markdown-flavoured Google style that mkdocstrings renders correctly and
Sphinx does not; generated reference keeps one source of truth with the agent contract;
the strict build is another deterministic gate in the ADR 0001 sense. The source stays
plain Markdown, so GitHub rendering remains a usable fallback and the agent-readable
form. This also edits the spec's "Out of scope" line; it is the maintainer's call. If
the maintainer holds D13, the minimum is pdoc on Pages for reference plus the gates
below on plain Markdown.

### How reference should be produced

Generated from the docstrings for every name in the four `__all__` lists, grouped by
layer; a test that every public name appears exactly once in `reference/`; style fields
generated rather than listed by hand; non-Python formats hand-written and pinned by
tests. No docstring rewritten for the site: if it reads badly rendered, that is a D25
docstring finding.

### Gates to add

Strict site build (unresolved reference fails); `lychee` link check (offline for internal
links in CI, external links weekly and advisory); `pytest-examples` over `docs/**/*.md`
and README; gallery images generated by running `examples/` from the Lynmouth fixtures so
the build never touches the network; README image URLs absolute (a test can check).

### Changes to the current P7 outline

1. `docs/tutorials/first-map.md` becomes the eight-rung tutorial; the route map is rung 8,
   not the whole tutorial.
2. `how-to/use-the-engine-without-maps` conflates with the tutorial rungs 1 to 7; drop it
   or replace it with a concrete task. `write-a-theme` needs checking against what
   `Style` from TOML really supports, so it documents a capability, not a hope.
3. `reference/` splits into generated (API, style fields, CLI) and hand-written (cache,
   manifest), each with its pinning test.
4. Add `index.md`, `gallery.md`, `glossary.md` (included), and the site config, theme
   assets and Pages workflow.
5. Separate project records from user docs in the nav.
6. Add a short style section to `CONTRIBUTING.md`: Google guide, British spelling,
   GLOSSARY terms, sentence-case headings, alt text on every painted image.

### Weaving the core point and style through the docs set

- **Every page opens with a painted image** made by the code the page teaches, generated
  at build time; tutorial rung N shows rung N's output. The image is the claim.
- **One voice**: second person, present tense, British English, glossary terms only;
  painter's vocabulary (paper, wash, nib, plate) used exactly as GLOSSARY defines it, so
  the craft metaphor is consistent rather than decorative.
- **The theme is painted by pyntpot**: paper texture, brush-stroke rules, pigment palette
  as CSS variables, Patrick Hand for headings and banners, all produced by a docs build
  script using public API only. Body text stays a plain readable face.
- **The README carries the same identity in miniature**: the hero route map, the lettered
  word on a washed circle, and the same one-sentence statement of the core point that the
  site's landing page uses, so PyPI, GitHub and the site say one thing.
- **Explanation pages tie technique to source**: how-the-wash-works cites
  `references.md` keys (D24), so the hand-drawn look is presented as modelled craft, which
  is the project's real distinction.
