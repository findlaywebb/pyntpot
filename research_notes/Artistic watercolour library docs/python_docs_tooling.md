# Python documentation tooling for a visual, self-illustrating docs site (state as of 7 October 2026)

Context: pyntpot is a uv-managed Python 3.13+ library (single `src/pyntpot`, ruff, ty, prek, strict pytest with warnings-as-errors) that paints watercolour and pen-and-ink rasters. The docs use Diátaxis paths (`docs/tutorials`, `docs/how-to`, `docs/reference`, `docs/explanation`), need a custom watercolour identity, and should render their own images with the library at build time.

Version and date data below comes from the PyPI JSON API (`https://pypi.org/pypi/<name>/json`), queried on 7 October 2026. The "PyPI snapshot" table at the end lists every package.

## MkDocs and Material for MkDocs: status in 2026

### Takeaway
Material for MkDocs went into maintenance mode with 9.7.0 on 11 November 2025. It reaches end of life on **5 November 2026**, four weeks after this note. MkDocs core has had no release since 1.6.1 (30 August 2024), and its governance broke down in early 2026. Starting a new project on MkDocs + Material in October 2026 means adopting software that is about to stop receiving fixes.

### Cited Findings
- 9.7.0 (11 Nov) was titled "Material for MkDocs is now in maintenance mode" and stated "This is the last release of Material for MkDocs that will receive new features." — [mkdocs-material releases](https://github.com/squidfunk/mkdocs-material/releases)
- The latest release, 9.7.7 (17 July 2026), states: "Material for MkDocs is scheduled to reach end of life on November 5, 2026", and says maintenance until then "is limited to critical bug fixes and security updates." — [mkdocs-material releases](https://github.com/squidfunk/mkdocs-material/releases); PyPI confirms 9.7.7 uploaded 2026-07-17, MIT licence — [PyPI](https://pypi.org/pypi/mkdocs-material/json)
- 9.7.0 also made every former sponsor-only "Insiders" feature free for everyone — [Material blog, 11 Nov 2025](https://squidfunk.github.io/mkdocs-material/blog/2025/11/11/insiders-now-free-for-everyone/)
- Secondary sources agree: the team "shift[s] their efforts to Zensical", with critical and security fixes for at least 12 months — [Renovate discussion #39232](https://github.com/renovatebot/renovate/discussions/39232); [duerrenberger.dev, 6 Nov 2025](https://duerrenberger.dev/blog/2025/11/06/material-for-mkdocs-is-no-more-long-live-zensical/). One secondary source (pydevtools) dates the start of maintenance mode to "early 2026". That conflicts with the primary release notes, which say November 2025 — [pydevtools](https://pydevtools.com/handbook/reference/mkdocs-material/).
- **MkDocs core:** the last release is 1.6.1, uploaded 2024-08-30 — [PyPI](https://pypi.org/pypi/mkdocs/json).
- Timeline from "The Slow Collapse of MkDocs" (Florian Maas, 22 March 2026):
  - MkDocs 2.0 was announced on 21 January 2026 without plugin support, from a private repository under `encode`.
  - A backward-compatibility notice was removed on 13 February 2026.
  - On 18 February 2026 the Material team published an analysis of v2's incompatibility, and Material now prints a build warning about it.
  - On 9 March 2026 there was a brief dispute over control of the `mkdocs` name on PyPI.
  - The v2 repository has been inactive since 19 February 2026.
  - Source: [fpgmaas.com](https://fpgmaas.com/blog/collapse-of-mkdocs/)
- **Forks:**
  - ProperDocs is a drop-in MkDocs 1.x continuation by oprypin, launched 15 March 2026. The latest release is 1.6.7 (2026-03-20), BSD-2 licence — [fpgmaas.com](https://fpgmaas.com/blog/collapse-of-mkdocs/); [PyPI](https://pypi.org/pypi/properdocs/json).
  - MaterialX (`mkdocs-materialx`) is a community continuation of Material. The latest release is 10.2.0 (2026-07-23), MIT licence — [PyPI](https://pypi.org/pypi/mkdocs-materialx/json).
- **Customisation depth:** Zensical's roadmap describes Material's model of `extra_css`, `extra_javascript` and `custom_dir` template overrides as something it keeps ("Additional CSS, JavaScript, and most template overrides are kept"). This confirms that the Material customisation model carries forward — [Zensical roadmap](https://zensical.org/roadmap/)

### Inferences
- Material's customisation depth (CSS custom properties for the palette, `extra_css`, Jinja block overrides through `custom_dir`, `main.html` and partials) is still excellent. It can carry a full watercolour identity: painted header backgrounds, heading flourishes, custom fonts. But a greenfield project should not target MkDocs + Material as the engine. Target Zensical, which keeps the same configuration and override model.
- MaterialX and ProperDocs are hedges if Zensical disappoints. Both are small, single-maintainer forks, so they carry bus-factor risk.

### Gaps
- I did not verify from primary sources whether ProperDocs is still actively developed after March 2026. PyPI shows no release after 1.6.7 (2026-03-20).
- I did not check MaterialX's maintainer count or its issue activity.

## Zensical: maturity, plugin support, theming, migration

### Takeaway
Zensical is the Material team's MIT-licensed, Rust-based successor. It is still on 0.0.x (0.0.68, released 5 October 2026), but releases come often. It reads `mkdocs.yml` and supports Material's theme, `extra_css`/JS and most template overrides. It natively reimplements **mkdocstrings (preliminary, since 0.0.11), markdown-exec (since 0.0.47), mike (since 0.0.30)** and about 30 other plugins. It does **not** run arbitrary MkDocs plugins: `gen-files` is unsupported, and mkdocs-gallery and mkdocs-jupyter are not covered.

### Cited Findings
- Latest release 0.0.68, uploaded 2026-10-05; requires Python >=3.11 — [PyPI](https://pypi.org/pypi/zensical/json)
- Zensical was announced on 5 November 2025 ("Zensical 0.1.0, Studio, and Spark Community launch" banner), alongside Material 9.7.0 — [Zensical roadmap](https://zensical.org/roadmap/); [fpgmaas.com](https://fpgmaas.com/blog/collapse-of-mkdocs/). PyPI version numbers are still 0.0.x, which conflicts with the "0.1.0" in the banner. I could not resolve this from the sources.
- Licence: MIT, per secondary summaries — [Renovate discussion](https://github.com/renovatebot/renovate/discussions/39232). The roadmap says the planned Markdown parser will also be MIT — [Zensical roadmap](https://zensical.org/roadmap/)
- Compatibility: Zensical supports existing `mkdocs.yml`, the standard project structure and Python Markdown, and "many MkDocs projects build with few or no changes". It supports Material settings and the `classic` theme. "Additional CSS, JavaScript, and most template overrides are kept." Installable themes and reusable components are planned — [Zensical roadmap](https://zensical.org/roadmap/)
- Plugin model: "Zensical provides native implementations of the MkDocs plugins listed below." Unlisted plugins: "Zensical does not import or run them." — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- Supported plugins, with the version that added each:
  - mkdocstrings 0.0.11, autorefs 0.0.22, mike 0.0.30, glightbox 0.0.35, macros 0.0.40, markdown-exec 0.0.47
  - literate-nav, awesome-nav, redirects, minify, tags and meta 0.0.58
  - blog 0.0.64, rss 0.0.65, autoapi and api-autonav 0.0.66
  - social, exclude, llmstxt and gh-admonitions 0.0.67
  - video and audio 0.0.68
  - gen-files: **unsupported**. Use autoapi or api-autonav instead, or run generation scripts outside the build.
  - optimize: in progress. privacy and the git-* plugins: planned.
  - Source: [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- mkdocstrings support is "preliminary": backlinks are not supported yet. You install `mkdocstrings-python` separately and configure it under `[project.plugins.mkdocstrings.handlers.python]` — [Zensical mkdocstrings page (redirects to compatibility)](https://zensical.org/docs/setup/extensions/mkdocstrings/), as summarised by search
- mike requires "a compatible fork", per Zensical's versioning guide — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- macros is native but behaves differently: environments are per page and there is no `on_post_build` hook — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- Roadmap items:
  - **In development:** a Rust reimplementation of Python Markdown that the project says runs "over 50x faster", and an `optimize` replacement.
  - **Up next:** a "Module API for Python" for custom publishing steps (Spark members get early access first). No dates are promised.
  - Source: [Zensical roadmap](https://zensical.org/roadmap/)
- Recent fixes include a reload loop caused by the auto-watched `custom_dir` (0.0.42), which confirms that `custom_dir` overrides are a live feature. 0.0.34 added TOML v1.1 support in `zensical.toml` — [newreleases 0.0.42](https://newreleases.io/project/pypi/zensical/release/0.0.42); [newreleases 0.0.34](https://newreleases.io/project/pypi/zensical/release/0.0.34)

### Inferences
- For pyntpot, Zensical covers the three things that matter: mkdocstrings-python API reference, markdown-exec for build-time image generation, and Material-grade theming with `custom_dir` and `extra_css`.
- There is no public plugin API until the "Module API for Python" ships. Any custom build step, such as "render all site artwork with pyntpot", has to run as a separate script before `zensical build`, for example `uv run python docs/_build/render_art.py && uv run zensical build`. That pattern is cleaner and easier to test anyway.
- Pin an exact Zensical version. 0.0.x releases can change behaviour.

### Gaps
- I did not find a primary source for Zensical's licence file. "MIT" comes from secondary sources.
- I could not establish whether markdown-exec under Zensical honours `session`, `html`, `workdir` and the other options exactly as under MkDocs.
- I could not confirm whether Zensical has an equivalent of `mkdocs build --strict` that fails on warnings.

## Sphinx with Furo, PyData Sphinx theme, Shibuya, and MyST

### Takeaway
Sphinx is healthy and stable: 9.1.0, released 31 December 2025, requires Python >=3.12. Its execution story is the most mature: sphinx-gallery and MyST-NB both cache results and fail the build on errors. Its themes are actively maintained. The costs: theme overrides are more constrained (Furo deliberately exposes only CSS variables), and authors write MyST or reST rather than plain Markdown.

### Cited Findings
- Sphinx 9.1.0 (2025-12-31), BSD-2, Python >=3.12 — [PyPI](https://pypi.org/pypi/sphinx/json)
- Furo 2025.12.19 (2025-12-19) — [PyPI](https://pypi.org/pypi/furo/json). Furo's recommended customisation is `light_css_variables` and `dark_css_variables` in `html_theme_options` (typos in these keys are silently ignored). Its other options are `announcement`, `sidebar_hide_name`, `footer_icons` and `top_of_page_buttons`, plus custom CSS through "injecting code". Of the options inherited from Sphinx's basic theme, "only the ones documented here are supported." — [Furo customisation](https://pradyunsg.me/furo/customisation/)
- PyData Sphinx theme 0.22.0 (2026-09-25), Python >=3.11 — [PyPI](https://pypi.org/pypi/pydata-sphinx-theme/json)
- Shibuya 2026.7.12 (2026-07-11), BSD-3 — [PyPI](https://pypi.org/pypi/shibuya/json)
- sphinx-book-theme 1.4.0 (2026-07-19) — [PyPI](https://pypi.org/pypi/sphinx-book-theme/json)
- myst-parser 5.1.0 (2026-05-13); myst-nb 1.4.0 (2026-03-02); sphinx-autoapi 3.8.1 (2026-08-23) — [PyPI myst-parser](https://pypi.org/pypi/myst-parser/json); [PyPI myst-nb](https://pypi.org/pypi/myst-nb/json); [PyPI sphinx-autoapi](https://pypi.org/pypi/sphinx-autoapi/json)
- jupyter-cache (MyST-NB's execution cache) 1.0.1, last released 2024-11-15 — [PyPI](https://pypi.org/pypi/jupyter-cache/json)

### Inferences
- PyData and Shibuya both allow template overrides through Sphinx `templates_path` and custom CSS. Furo is the most opinionated of the three. A heavily art-directed watercolour look is easier in Shibuya or PyData than in Furo. Overall it is easier still with Material/Zensical, where you override Jinja blocks directly.
- The Sphinx toolchain itself does not have the MkDocs governance risk.

### Gaps
- I did not fetch the PyData or Shibuya theming docs, so the inference about how far their templates can be overridden rests on general Sphinx `templates_path` behaviour, not on pages I checked.
- I did not check Sphinx 9's own maintenance announcements.

## API reference generation

### Takeaway
mkdocstrings-python with griffe is very actively maintained, and griffe had a release the day before this note. It renders Google-style docstrings well and works under both MkDocs and Zensical, though Zensical's support is still preliminary. On Sphinx, autodoc with napoleon, or sphinx-autoapi, does the same job.

### Cited Findings
- mkdocstrings 1.0.6 (2026-07-11), ISC; mkdocstrings-python 2.0.9 (2026-09-22), ISC; griffe 2.3.2 (2026-10-06), ISC, Python >=3.11 — [PyPI mkdocstrings](https://pypi.org/pypi/mkdocstrings/json); [PyPI mkdocstrings-python](https://pypi.org/pypi/mkdocstrings-python/json); [PyPI griffe](https://pypi.org/pypi/griffe/json)
- Zensical supports mkdocstrings since 0.0.11 (preliminary, no backlinks), and autoapi and api-autonav (for generating reference pages without gen-files) since 0.0.66 — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- sphinx-autoapi 3.8.1 (2026-08-23) — [PyPI](https://pypi.org/pypi/sphinx-autoapi/json)

### Inferences
- The project's docstring contract is "module and public-API docstrings are the agent contract". mkdocstrings `::: pyntpot.ink` directives in `docs/reference/*.md` make those docstrings the reference pages directly, which fits the Diátaxis reference quadrant.
- griffe can also be used offline as a check, for example `griffe check` for API breakage against the last tag. That would sit well alongside the boundary gates.

### Gaps
- I did not verify whether griffe's API-breakage check suits pyntpot's CI.

## Executing code at build time to produce images, caching and testing

### Takeaway
On the MkDocs/Zensical side, **markdown-exec** is the maintained, Zensical-supported option. It runs fenced Python and injects Markdown or HTML output, but it has **no caching**. mkdocs-gallery is effectively dormant: last release September 2024. sphinx-gallery is the gold standard for cached, scraper-based example galleries. For pyntpot, the robust pattern is to keep slow renders out of the doc build:
1. Write example scripts as plain Python files.
2. Render them with a cached script, keyed on a hash of the source plus the pyntpot version.
3. Test those same scripts under pytest, with golden-image comparison.
4. Use markdown-exec or snippets only for light, fast inline output.

### Cited Findings
- markdown-exec 1.12.4 (2026-10-06), ISC, Python >=3.11 — [PyPI](https://pypi.org/pypi/markdown-exec/json)
- markdown-exec runs a fenced block when it has the `exec` option.
  - `html="true"` injects raw HTML; otherwise output is rendered as Markdown.
  - The `session` option persists state between blocks ("Sessions only work with Python and Pycon syntax for now").
  - `workdir` sets the execution directory, and `source` controls how code is shown next to its output.
  - On failure, the traceback replaces the output and a warning is logged.
  - The usage page does not mention caching.
  - Source: [markdown-exec usage](https://pawamoy.github.io/markdown-exec/usage/)
- Zensical supports markdown-exec since 0.0.47 and recommends enabling it as a plugin rather than through manual superfences configuration — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- mkdocs-gallery 0.10.4, last release 2024-09-30, with no `requires_python` declared — [PyPI](https://pypi.org/pypi/mkdocs-gallery/json). Zensical does not list it — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- mkdocs-jupyter 0.26.3 (2026-04-17), Apache-2.0. Zensical does not list it — [PyPI](https://pypi.org/pypi/mkdocs-jupyter/json); [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)
- sphinx-gallery 0.22.1 (2026-09-18), BSD-3 — [PyPI](https://pypi.org/pypi/sphinx-gallery/json)
  - "By default, Sphinx-Gallery only rebuilds examples that have changed", using an MD5 hash per example; `run_stale_examples` forces a rebuild.
  - `filename_pattern` (default `plot_` prefix) selects which examples execute.
  - Image capture uses `image_scrapers` (default `('matplotlib',)`), and custom scrapers can be written for other libraries.
  - The option index lists `abort_on_example_error`, `only_warn_on_example_error`, `reset_modules` and `parallel`.
  - Source: [sphinx-gallery configuration](https://sphinx-gallery.github.io/stable/configuration.html)
- Testing Markdown snippets:
  - pytest-markdown-docs 0.9.2 (2026-03-23), MIT
  - pytest-codeblocks 0.18.0 (2026-06-15), MIT
  - Sybil 10.1.0 (2026-06-13), MIT, Python >=3.11
  - phmdoctest 1.4.0: last release 2022-03-19, which makes it stale
  - Sources: [PyPI pytest-markdown-docs](https://pypi.org/pypi/pytest-markdown-docs/json); [PyPI pytest-codeblocks](https://pypi.org/pypi/pytest-codeblocks/json); [PyPI sybil](https://pypi.org/pypi/sybil/json); [PyPI phmdoctest](https://pypi.org/pypi/phmdoctest/json)

### Inferences
- **Determinism:** sphinx-gallery and markdown-exec only execute code. Whether the output is deterministic is up to pyntpot: seeded RNG, pinned fonts, no wall-clock input, and a fixed paper texture seed. The project's golden-image discipline (pinned literals, `--golden-tolerance` in CI) should cover the tutorial images. Docs images and golden test images can share one deterministic render path.
- **Recommended layout:**
  - `docs/examples/*.py` holds runnable scripts, one per tutorial or how-to output.
  - A cached render step (for example `uv run python -m docs_build.render`) writes PNG and WebP files into `docs/assets/generated/`. The cache key is a hash of the script source plus the `pyntpot` version plus the paths of any fixture data.
  - Pages include the scripts with pymdownx.snippets (`--8<--`) and show the images.
  - A pytest module parametrised over `docs/examples/*.py`, with `ids=`, runs each script and compares the output to pinned golden hashes, within tolerance.
  - With this layout the build-time render is a cache hit, the image correctness gate is in pytest where it belongs, and the build does not depend on markdown-exec caching, which does not exist.
- **Choosing a snippet tester:** Sybil is the most flexible (its parsers cover Markdown and MyST) and is actively maintained. pytest-markdown-docs is the lightest. Avoid phmdoctest: its last release was in 2022. Under `filterwarnings = ["error"]` and pytest-randomly, prefer explicit example scripts over doctest-style snippet chains. Snippet chains share state between blocks, which conflicts with randomised ordering.
- **Site artwork** (painted backgrounds, heading flourishes, banner): render it with pyntpot in the same pre-build step. Commit the README banner, because GitHub and PyPI need a stable URL. CI can regenerate the rest.
- If heavy galleries become central, Sphinx with sphinx-gallery and a custom pyntpot image scraper is the only mature cached-gallery option. That would mean choosing Sphinx over Zensical.

### Gaps
- I found no maintained MkDocs or Zensical gallery plugin with hash-based caching.
- I did not verify Quarto's 2026 status or its fit for this setup. Quarto would add a non-Python toolchain (a Pandoc-based CLI), which conflicts with the single-venv uv approach. This is my own judgement, not from a source.
- I did not confirm MyST-NB's execution and caching behaviour in its 1.4.0 docs.
- I did not confirm whether markdown-exec's failure warning aborts a `--strict` build under Zensical.

## Hosting and versioning

### Takeaway
GitHub Pages deployed from GitHub Actions is the simplest option for a Zensical or MkDocs static build. Use mike for versioned docs: Zensical supports it, though only through a compatible fork. Read the Docs suits Sphinx best and also builds MkDocs-style projects.

### Cited Findings
- mike 2.2.0 (2026-04-14), BSD-3 — [PyPI](https://pypi.org/pypi/mike/json)
- Zensical supports mike since 0.0.30, through "a compatible fork" described in its versioning guide — [Zensical compatibility: plugins](https://zensical.org/compatibility/plugins)

### Inferences
- With GitHub Pages and Actions, the workflow would be: `uv sync`, then the pyntpot render step (with `actions/cache` keyed on the example hashes), then `zensical build`, then `actions/upload-pages-artifact` and `actions/deploy-pages`.
- Versioned docs are probably premature for a pre-1.0 library. Add mike when the first stable API is tagged.

### Gaps
- I did not fetch current GitHub Pages Actions docs or Read the Docs docs in this session. I did not confirm Read the Docs' 2026 support for Zensical.

## GitHub README and PyPI long_description constraints

### Takeaway
GitHub READMEs support the `<picture>` element, and the documented pattern is `<picture>` with `<source media="(prefers-color-scheme: dark)">`. GitHub resolves relative image paths per branch. PyPI's renderer (readme_renderer with nh3) **allows `<picture>` but strips `<source>`**, so only the fallback `<img>` shows on PyPI. PyPI also allows only `http`, `https` and `mailto` URL schemes, so `data:` URIs are removed. Relative image paths do not resolve on PyPI: use absolute URLs, ideally `raw.githubusercontent.com` pinned to a tag.

### Cited Findings
- GitHub: "The `<picture>` HTML element is supported." GitHub "will automatically transform your relative link or image path based on whatever branch you're currently on"; links starting with `/` are relative to the repository root — [GitHub basic writing and formatting syntax](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
- GitHub: "By using the HTML `<picture>` element with the `prefers-color-scheme` media feature, you can add an image that changes" with the theme. The pattern uses two `<source media="(prefers-color-scheme: dark|light)" srcset=...>` elements plus a fallback `<img alt src>`. The fallback shows when no source matches — [GitHub quickstart for writing on GitHub](https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/quickstart-for-writing-on-github)
- PyPI renders plain text, reStructuredText (without Sphinx extensions) and Markdown, selected by `long_description_content_type`. Invalid reST falls back to raw source. `twine check dist/*` reports rendering problems — [packaging.python.org: Making a PyPI-friendly README](https://packaging.python.org/en/latest/guides/making-a-pypi-friendly-readme/)
- readme_renderer `clean.py`:
  - `ALLOWED_TAGS` includes `picture`, `img`, `div`, `p`, `h1`–`h6`, `details`, `summary`, `figure`, `figcaption` and others, but **not `source`**.
  - `img` may carry the attributes `src`, `width`, `height`, `alt`, `align` and `class`.
  - `url_schemes={"http","https","mailto"}`.
  - Source: [pypa/readme_renderer clean.py](https://github.com/pypa/readme_renderer/blob/main/readme_renderer/clean.py). readme-renderer 46.0 was released 2026-08-28 — [PyPI](https://pypi.org/pypi/readme-renderer/json)
- Relative README image paths break on PyPI. The common fixes:
  - Absolute `raw.githubusercontent.com/<owner>/<repo>/<ref>/...` URLs — [codeanalyzer-python PR #5](https://github.com/codellm-devkit/codeanalyzer-python/pull/5)
  - Rewriting relative links at build time with `hatch-fancy-pypi-readme` regex substitutions — [agent-mcp-gateway doc](https://glama.ai/mcp/servers/@roddutra/agent-mcp-gateway/blob/a1d664a4129bb6358b3cc9045f0095f2f32f127e/docs/pypi-readme-transformation.md)
  - Pinning rewritten links to the release tag and failing the build if relative links remain — [replicate/cog commit](https://app.semanticdiff.com/gh/replicate/cog/commit/5e3a8c97cfbecdd04b2bf2153909aa9c03c440ca)
  - These are project reports, not an official PyPI statement.

### Inferences
- Banner strategy:
  - Use a painted pyntpot banner as `<picture>` with dark and light `<source>` elements on GitHub.
  - Make the fallback `<img>` use an absolute, tag-pinned `raw.githubusercontent.com` URL to a banner that reads on both light and dark backgrounds. PyPI shows only that fallback, so it must stand on its own.
  - Raster banners for READMEs should be compressed WebP or PNG. GitHub, PyPI and the CDNs cache aggressively.
- No CSS or JS works on either surface. Any "watercolour" look in the README has to be baked into images: banner, section-heading images, sample outputs. Each needs alt text.
- One option is a prek or CI check that runs `twine check` and greps the built METADATA for relative image paths. This fits the project's "gates are the source of truth" stance.

### Gaps
- I did not verify GitHub's current per-file size limits for images rendered in READMEs, or PyPI's maximum `long_description` size, from primary docs in this session.
- I did not confirm whether GitHub keeps `width`/`align` on `<img>` inside `<picture>`.

## Licensing and maintenance health (summary)

### Takeaway
Every candidate uses a permissive licence (MIT, ISC, BSD or Apache-2.0). The maintenance risks are MkDocs core (dormant since August 2024, with governance turmoil), Material (end of life on 5 November 2026), mkdocs-gallery (no release since September 2024), phmdoctest (no release since 2022) and jupyter-cache (last release November 2024). Zensical is young (0.0.x) but releases often and is backed by the former Material team.

### Cited Findings
PyPI snapshot, 7 October 2026 ([PyPI JSON API](https://pypi.org/pypi/zensical/json), and the same endpoint per package):

| Package | Latest | Uploaded | Licence | Python |
|---|---|---|---|---|
| zensical | 0.0.68 | 2026-10-05 | MIT (secondary sources; not in PyPI metadata) | >=3.11 |
| mkdocs | 1.6.1 | 2024-08-30 | BSD-2 (not in PyPI metadata) | >=3.8 |
| mkdocs-material | 9.7.7 | 2026-07-17 | MIT | >=3.8 |
| mkdocs-materialx | 10.2.0 | 2026-07-23 | MIT | >=3.8 |
| properdocs | 1.6.7 | 2026-03-20 | BSD-2 | >=3.9 |
| mkdocstrings | 1.0.6 | 2026-07-11 | ISC | >=3.10 |
| mkdocstrings-python | 2.0.9 | 2026-09-22 | ISC | >=3.10 |
| griffe | 2.3.2 | 2026-10-06 | ISC | >=3.11 |
| markdown-exec | 1.12.4 | 2026-10-06 | ISC | >=3.11 |
| mkdocs-gallery | 0.10.4 | 2024-09-30 | BSD-3 | n/a |
| mkdocs-jupyter | 0.26.3 | 2026-04-17 | Apache-2.0 | >=3.9 |
| mike | 2.2.0 | 2026-04-14 | BSD-3 | n/a |
| sphinx | 9.1.0 | 2025-12-31 | BSD-2 | >=3.12 |
| furo | 2025.12.19 | 2025-12-19 | (MIT; not in PyPI metadata) | >=3.8 |
| pydata-sphinx-theme | 0.22.0 | 2026-09-25 | (BSD; not in PyPI metadata) | >=3.11 |
| shibuya | 2026.7.12 | 2026-07-11 | BSD-3 | >=3.10 |
| sphinx-book-theme | 1.4.0 | 2026-07-19 | n/a | >=3.11 |
| myst-parser | 5.1.0 | 2026-05-13 | n/a | >=3.11 |
| myst-nb | 1.4.0 | 2026-03-02 | n/a | >=3.10 |
| jupyter-cache | 1.0.1 | 2024-11-15 | n/a | >=3.9 |
| sphinx-autoapi | 3.8.1 | 2026-08-23 | n/a | >=3.10 |
| sphinx-gallery | 0.22.1 | 2026-09-18 | BSD-3 | >=3.10 |
| sybil | 10.1.0 | 2026-06-13 | MIT | >=3.11 |
| pytest-markdown-docs | 0.9.2 | 2026-03-23 | MIT | >=3.9 |
| pytest-codeblocks | 0.18.0 | 2026-06-15 | MIT | >=3.10 |
| phmdoctest | 1.4.0 | 2022-03-19 | MIT | >=3.6 |
| readme-renderer | 46.0 | 2026-08-28 | Apache-2.0 | >=3.10 |

Licences in parentheses or marked "not in PyPI metadata" were missing from the PyPI `license`/`license_expression` field. They come from general knowledge, not from a source checked here.

### Inferences
- **Recommendation for pyntpot: Zensical** (pin the exact 0.0.x version), with:
  - Material theme customisation: a custom palette through CSS custom properties in `extra_css`, plus `custom_dir` overrides for a painted header and hero, and heading backgrounds.
  - mkdocstrings-python for `docs/reference`.
  - A separate, cached, pytest-tested pyntpot render step for tutorial images and site artwork, plus pymdownx.snippets to include example source.
  - markdown-exec only for small inline outputs.
  - GitHub Pages through Actions; mike later.
- **Fallback:** Sphinx 9 with Shibuya or PyData, MyST-parser, autodoc or autoapi, and sphinx-gallery with a custom pyntpot image scraper. Choose this if Zensical's preliminary mkdocstrings support or its lack of a plugin API blocks work, or if a cached example gallery becomes the centrepiece.
- **Avoid for new work:**
  - MkDocs 1.6 + Material: end of life on 5 November 2026.
  - mkdocs-gallery: dormant, and not supported by Zensical.
  - phmdoctest: stale since 2022.
  - Quarto: adds a non-uv toolchain. This is my judgement only.
- Adopting a docs toolchain is a boundary-level decision for this repo. Per CLAUDE.md it warrants an ADR in `docs/decisions/`.

### Gaps
- The licences of furo, pydata-sphinx-theme, myst-* and zensical were not in the PyPI metadata fields I queried. Confirm them from each repository's LICENSE file.
- GitHub stars and contributor counts were not collected, apart from Zensical (">3,700 stars" as of March 2026, per [fpgmaas.com](https://fpgmaas.com/blog/collapse-of-mkdocs/)).
