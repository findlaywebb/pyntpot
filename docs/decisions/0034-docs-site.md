# 0034 — A docs site on GitHub Pages

Status: accepted

Amends D13 of the port spec (README and Diátaxis `docs/`, no docs site at 0.1).

## Context

The P7 research found three things a Markdown tree on GitHub cannot do: carry the look
(GitHub strips styles, fonts and class names), generate the API reference from the
docstrings, and fail a build on a broken link or a renamed public name. pyntpot's point is a
look, and the library can paint its own chrome. The cost is one more gate and one more thing
to host.

## Decision

- **A site on GitHub Pages, from Markdown that stays plain.** `docs/` is still the source and
  still reads on GitHub: relative links stay relative, and a link that leaves `docs/` (to
  `examples/`, `GLOSSARY.md` or a feature note) is an absolute `github.com` URL, because the
  site does not contain those files. `mkdocs.yml` chooses the pages. `decisions/`, `issues/`,
  `features/`, `runbooks/`, `architecture.md` and `docs/README.md` are maintainer records and
  stay out of the nav and the build (`exclude_docs`).
- **The engine.** The plan picks Zensical when a 0.1.x release is on PyPI. The latest is
  0.0.72, so the site uses Material for MkDocs 9.7.7 (its last release) with
  mkdocstrings-python 2.0.10, both pinned exactly in the `docs` dependency group. MkDocs 1.6.1
  comes with them and is not pinned by us. The configuration is a plain `mkdocs.yml`, which
  Zensical reads, so a move later is a change of command, not of files. Material is in
  maintenance and MkDocs 2.0 drops plugins, so the pin is the plan: the strict build is the
  alarm.
- **mkdocstrings for the API reference.** The docstrings are Google-style Markdown, which
  mkdocstrings renders as written. `docs/reference/{pyntpot,ink,letters,maps}.md` each hold a
  directive for the module with `members: false`, then one directive per public name. A
  module directive alone does not render a name that is also a submodule (`stamp`, `wash`,
  `compose`, `vector_layers`) or a module-level table, so each name has its own, and
  `tests/architecture/test_site.py` requires every name in the four `__all__` lists to have
  exactly one.
- **Identity, kept restrained.** The pictures carry the style. `examples/site_theme.py` paints
  the paper the light scheme sits on and a brush-stroke rule, registered in
  `tests/support/docs_images.py` under slice P7.14, and writes `docs/stylesheets/pyntpot.css`
  (`figure="palette"`), whose colours are the `PIGMENTS` as CSS custom properties. A test pins
  the stylesheet and checks that every text colour reads on its ground in both schemes at
  contrast 4.5 or more. Patrick Hand, the vendored OFL font, is copied to `docs/assets/` with
  its licence and used for display headings only; body and code keep the theme's faces.
- **The workflow.** `.github/workflows/docs-site.yml` builds strictly on every pull request. On
  a push to `main` it builds and deploys with `actions/upload-pages-artifact` and
  `actions/deploy-pages`.

## Consequences

- **Maintainer action:** enable Pages in the repository settings, with "GitHub Actions" as the
  source. Until then the deploy job fails and the build job still gates pull requests.
- A docstring that mkdocstrings renders badly is a finding about the docstring, not a reason
  to loosen the build.
- The README's absolute image URLs are unchanged; the site's own pictures are under
  `docs/images/`.
