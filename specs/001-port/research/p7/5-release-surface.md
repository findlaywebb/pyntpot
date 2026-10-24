# P7 research 5: the release surface beyond the README body

Scope: what a stranger sees of pyntpot 0.1.0 on PyPI and GitHub before reading a line of
code, and the CI gates that keep that surface honest. Measured at the working tree on
2026-10-23 (`pyproject.toml` version `0.0.2`, tags `v0.0.1` and `v0.0.2`, no GitHub
releases, project absent from PyPI).

## 0. Two findings from probing the repo

1. **Trusted publishing is not configured, and both tag pushes already failed.** The
   `Publish` workflow ran for `v0.0.1` and `v0.0.2`; both failed at
   `pypa/gh-action-pypi-publish` with `invalid-publisher: valid token, but no
   corresponding publisher`. `curl https://pypi.org/pypi/pyntpot/json` returns 404, so
   the name is unclaimed. The P7 outline's "already done if Q14 chose PyPI for 0.0.1" is
   false in fact. Because the project does not exist yet, the fix is a **pending
   publisher** (https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
   with owner `findlaywebb`, repo `pyntpot`, workflow `publish.yml`, environment `pypi`.
   Gotcha: once it exists, "Re-run failed jobs" on the old runs would publish 0.0.1 and
   0.0.2, which the changelog calls "not for general use". Do not re-run them; let
   0.1.0 be the first upload. A pending publisher does not reserve the name, so create it
   close to the tag.
2. **`twine check --strict` passes today** on both the sdist and wheel built by
   `uv build` (`check-wheel-contents` is also clean; `py.typed` and the Patrick Hand TTF
   are in the wheel). The sdist holds only `src/`, `pyproject.toml`, `README.md` and the
   two licence files: no tests, so the ODbL Overpass payloads in
   `tests/fixtures/lynmouth/` are never redistributed through PyPI. That is a good
   property; keep it, and note it in the data-policy page. (Trade-off: conda-forge
   recipes like to run tests from the sdist; they can use the GitHub tarball.)

## 1. README on PyPI versus GitHub

PyPI renders the long description with `readme_renderer` (CommonMark plus a GFM subset,
sanitised; https://github.com/pypa/readme_renderer). Concrete differences:

- **Relative links and images break on PyPI.** `![map](docs/images/route-map.png)`
  resolves against `pypi.org/project/pyntpot/`, so the image is a 404. Use absolute URLs
  pinned to the tag:
  `https://raw.githubusercontent.com/findlaywebb/pyntpot/v0.1.0/docs/images/route-map.png`.
  Pinning to the tag (not `main`) keeps the 0.1.0 page showing 0.1.0's pictures forever
  even after the images change. The tag exists by the time the publish job runs, because
  the job is triggered by it. The same applies to links: today's README names
  `CONTRIBUTING.md`, `BOUNDARIES.md`, `LICENSE-FONT` in backticks, which is harmless, but
  any `[text](CONTRIBUTING.md)` link must become an absolute `github.com/.../blob/v0.1.0/`
  link.
- **No README rewriting plugin with `uv_build`.** Projects on hatchling use
  `hatch-fancy-pypi-readme` to rewrite relative links at build time (attrs does this,
  and it also splices the latest changelog section into the PyPI page). `uv_build` has
  no such hook, so absolute links written by hand are the way. A test can enforce it (see
  section 8).
- **GitHub-only features silently degrade on PyPI**: alert blocks (`> [!NOTE]`),
  Mermaid, `<picture>` with `prefers-color-scheme` sources, `#gh-dark-mode-only`
  fragments, and `<details>` styling. A painted image on cream paper suits both themes
  anyway; avoid transparent PNGs, which look wrong on GitHub's dark background.
- **Image weight.** Watercolour PNGs compress badly; a 1600 px card can be several MB.
  Ship README images at display size (about 800 to 1000 px wide), run them through
  `oxipng` or similar, and keep each under about 500 KB. Store them under `docs/images/`;
  `uv_build` will not put them in the sdist.
- **Alt text** that describes the painting ("a watercolour route map of the Lyn valley
  with a red ink track and hand-lettered labels") matters for screen readers and is what
  PyPI shows when an image fails.
- `readme = "README.md"` already sets `Description-Content-Type: text/markdown`
  (confirmed in the built METADATA). Nothing to change.

## 2. `pyproject.toml` metadata

Current: three classifiers and three URLs. Recommended for 0.1.0:

```toml
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3 :: Only",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",   # only if CI runs it
    "Operating System :: OS Independent",
    "Topic :: Artistic Software",
    "Topic :: Multimedia :: Graphics",
    "Topic :: Scientific/Engineering :: GIS",
    "Typing :: Typed",
]

[project.urls]
Homepage = "https://github.com/findlaywebb/pyntpot"
Documentation = "https://github.com/findlaywebb/pyntpot/tree/main/docs"
Changelog = "https://github.com/findlaywebb/pyntpot/blob/main/CHANGELOG.md"
Source = "https://github.com/findlaywebb/pyntpot"
Issues = "https://github.com/findlaywebb/pyntpot/issues"
```

Gotchas:
- **Do not add a `License ::` classifier.** The project uses a PEP 639 `license = "MIT"`
  expression; PyPI rejects uploads that combine a licence expression with licence
  classifiers (https://peps.python.org/pep-0639/#deprecate-license-classifiers).
- PyPI gives icons only to recognised labels (Homepage, Documentation, Changelog, Source
  or Repository, Issues, Funding, Security; https://docs.pypi.org/project_metadata/).
  "Changelog" earns a dedicated sidebar link, which matters more than any badge.
- **Verified URLs**: with trusted publishing from GitHub Actions, PyPI marks
  `github.com/findlaywebb/pyntpot` and its subpaths as verified and shows the live
  repository statistics panel. This only works if the URLs point at exactly that repo.
- Classifier strings are validated on upload; check against
  https://pypi.org/classifiers/ (`trove-classifiers` package) before tagging.
- Keywords: add `openstreetmap`, `hand-drawn`, `generative-art`, `non-photorealistic`;
  drop nothing. PyPI search weights keywords and summary.
- Development Status: 3 - Alpha is the honest value for a 0.1.0 "release candidate"
  with a declared breaking-change policy. 4 - Beta signals API settledness the project
  has not yet claimed.

## 3. GitHub repository page

`gh api repos/findlaywebb/pyntpot` reports the description set (same as the summary),
**no topics, no homepage, no custom social preview**, Discussions off.

- **Topics** (max 20, lowercase, hyphenated; set with
  `gh api -X PUT repos/findlaywebb/pyntpot/topics -f names[]=...`): `watercolour`,
  `watercolor` (the US spelling is what people search), `pen-and-ink`, `hand-drawn`,
  `generative-art`, `non-photorealistic-rendering`, `procedural-art`, `openstreetmap`,
  `cartography`, `route-map`, `gpx`, `elevation`, `hand-lettering`, `raster-graphics`,
  `python`, `numpy`.
- **Homepage field**: the PyPI page once it exists.
- **Social preview**: 1280 x 640 px recommended, under 1 MB, PNG or JPG; set by hand
  under Settings, General, Social preview (no REST endpoint). Without it, every link to
  the repo on Slack, Mastodon or Bluesky shows GitHub's generated card with the avatar
  and stats. This is the single highest-leverage image on the release surface; see
  the identity subsection below.
- **"Releases" and "Packages" sidebar**: empty until a GitHub release is created; a tag
  alone does not populate "Releases" with notes.
- **Community profile** (`/community`): GitHub ticks README, licence, CONTRIBUTING,
  SECURITY, code of conduct, issue templates, PR template. pyntpot has all but the code
  of conduct and issue templates.

## 4. Badges

Keep to the ones a reader acts on, below the hero image (prettymaps and rich both lead
with the picture, badges after or none):

- PyPI version (`img.shields.io/pypi/v/pyntpot`) and supported Pythons
  (`img.shields.io/pypi/pyversions/pyntpot`, read from the classifiers above, which is
  another reason to add them). Both show "not found" until the first upload, so add them
  in the 0.1.0 commit knowing they go live minutes after the tag.
- CI status (`github.com/findlaywebb/pyntpot/actions/workflows/ci.yml/badge.svg`).
- Licence (shields reads it from PyPI).
- CodSpeed, already mandated verbatim by P10.2 Q13.

Skip: coverage (no hosted service, and the gate already lives in CI), downloads (zero
and misleading for months), "code style: ruff", "checked with ty", "uv", Discord or
sponsor badges. Badges that state tooling read as noise to users and decay as tooling
changes.

## 5. CHANGELOG and release notes

Practice in the comparison set:
- **httpx** and **rich**: a hand-written `CHANGELOG.md` in Keep a Changelog shape,
  version headings with dates, Added / Changed / Fixed.
- **attrs**: towncrier fragments in `changelog.d/`, one file per PR, compiled at release,
  with a "Backwards-incompatible changes" section first and links to the PR.
  https://www.attrs.org/en/stable/changelog.html
- **Pydantic**: `HISTORY.md` plus long GitHub release notes, partly generated, with a
  "What's Changed" PR list and contributor credits.
- **uv**: `CHANGELOG.md` generated from PR labels by Astral's `rooster`; GitHub releases
  carry the same text plus binaries.
- **shapely** (`CHANGES.txt`) and **osmnx** (`CHANGELOG.md`) are hand-written, short,
  and lead each version with breaking changes.

For one maintainer with agent sessions that already write changelog lines per PR, towncrier
adds a directory and a build step for no gain; keep hand-written Keep a Changelog
(https://keepachangelog.com/en/1.1.0/). Fix the details:
- Add the **compare links** at the foot that Keep a Changelog specifies
  (`[0.1.0]: https://github.com/findlaywebb/pyntpot/compare/v0.0.2...v0.1.0`); they are
  missing today, so `[0.0.1]` headings link nowhere.
- Add a **"Removed"** and, when needed, **"Deprecated"** and **"Security"** section;
  put breaking changes first in each 0.x minor.
- Write 0.1.0 as a **summary for a newcomer**, not only the delta from 0.0.2: one
  paragraph saying what the library does, then the changes since 0.0.2. The 0.0.x
  entries stay as history.
- ADR numbers in entries ("ADR 0029") are fine on GitHub but are bare text on PyPI and
  in release notes; link them absolutely or drop them from the user-facing line.
- Use GLOSSARY terms (wash, plate, nib, credit) consistently; the changelog is read
  more than any other doc after the README.

**GitHub releases**: add a step to `publish.yml` after the upload, with
`permissions: contents: write`, that extracts the version's section from `CHANGELOG.md`
and runs `gh release create "$GITHUB_REF_NAME" dist/* --verify-tag --notes-file notes.md`.
Attaching the dists gives a second download origin. `--generate-notes` and
`.github/release.yml` categories are useful for multi-contributor projects; for pyntpot
the changelog section is better text. The `gh-action-pypi-publish` action already uploads
PEP 740 attestations under trusted publishing; nothing to add.

**Publish workflow gaps** worth fixing in the same slice: it does not run the gate
before uploading, does not check the tag equals `project.version` (a `v0.1.0` tag on a
`0.0.2` tree would upload 0.0.2), and pins `gh-action-pypi-publish@release/v1` while
every other action is pinned to a version. Add `needs:` on a CI job or a check step
(`test "v$(uv version --short)" = "$GITHUB_REF_NAME"`), and pin the action to a release
SHA. Consider a TestPyPI dry run (separate pending publisher, environment `testpypi`).

## 6. CONTRIBUTING, code of conduct, issue templates, citation

- **CONTRIBUTING** is written for agent sessions (spec flow, trailers, mutation shards).
  Add a short top section for an outside contributor: open an issue first, how to run
  the gate, that golden pixels are exact locally so a PR that moves pixels needs a
  stated reason, and the place-name rule. The `personal_terms_file` test skips cleanly
  when `~/personal/...` is absent (checked), so an outside clone stays green; say so.
- **Code of conduct**: for a one-person project it is optional. Contributor Covenant 2.1
  (https://www.contributor-covenant.org/version/2/1/code_of_conduct/) is the norm (httpx,
  rich, attrs, Pydantic use it or a variant) but it requires a named enforcement contact.
  Adopt it only with a contact address the maintainer is happy to publish (the private
  vulnerability form is not a CoC channel); otherwise skip for 0.1.0.
- **Issue templates**: one `bug.yml` form asking for pyntpot version, Python, OS, the
  smallest script, and the output image attached; a `config.yml` pointing questions
  away. Image libraries live on attached images.
- **CITATION.cff** (https://citation-file-format.github.io/, `cff-version: 1.2.0`) gives
  GitHub's "Cite this repository" button. Cheap, a dozen lines; validate with
  `cffconvert --validate`. Its `version` and `date-released` fields go stale unless the
  release slice bumps them, so either add a test that compares `version` to
  `pyproject.toml` or omit those two fields. Zenodo DOIs (via the GitHub integration) are
  optional; skip for 0.1.0.

## 7. Data licensing and attribution docs

The library code is MIT; the **data it paints is not**. The docs must say who owes what.

- A pyntpot map is an ODbL **Produced Work**
  (https://osmfoundation.org/wiki/Licence/Community_Guidelines/Produced_Work_-_Guideline).
  The Produced Work may be under any licence, but when used publicly it must carry
  attribution "to OpenStreetMap" making clear the data is under the ODbL; "© OpenStreetMap
  contributors" remains acceptable and the URL `openstreetmap.org/copyright` must be
  printed on static or printed output
  (https://osmfoundation.org/wiki/Licence/Attribution_Guidelines). The shipped
  `Credit.short` for Overpass, "© OpenStreetMap contributors
  (openstreetmap.org/copyright)", meets that. The guidelines also want the text "easily
  readable" with WCAG-level contrast: a hand-lettered line in pale ink on a wash can
  fail this, so the data-policy page should state the contrast the default theme gives
  and a test could pin it.
- **The guideline encourages qualified credit when the data is restyled**, for example
  "Map data from OpenStreetMap", which fits a watercolour rendering better than a bare
  ©. A wording change is a maintainer call; note it.
- **`attribution=False` and `--no-attribution` move the duty to the caller.** Say this
  in the docstring, the CLI help and the data-policy page: the caller must then credit
  beside the image, in a footnote or in acknowledgements, in that order of preference.
  prettymaps states the equivalent plainly ("keep the printed message on the figures");
  osmnx's getting-started page only points at the Overpass and Nominatim usage policies
  and never says how to credit, which is the gap to avoid.
- **Derivative Database exports.** The fetch cache, `vector_layers` and
  `candidate_export` hand callers OSM data in other forms. A substantial extract that is
  republished is a Derivative Database and is share-alike under the ODbL. State it once
  in the data-policy page and in those functions' docstrings.
- **Elevation**: SRTM is NASA data with no use restrictions; credit it anyway
  (`Credit` already does, "elevation: NASA SRTM"). OpenTopoData's public API has its own
  limits (100 locations per request, 1 call per second, 1000 per day;
  https://www.opentopodata.org/#public-api); the Overpass instance asks for well under
  10,000 queries and 1 GB a day (https://dev.overpass-api.de/overpass-doc/en/preface/commons.html).
  Both belong in the data-policy page with the self-host how-to as the answer for heavy
  use.
- **Docs images are Produced Works too.** The README's route map must carry its drawn
  attribution, and its caption should repeat it. Render it from the Lynmouth fixture
  (already ODbL-noted) so no personal route appears.
- The font's OFL obligations are met by `LICENSE-FONT` in both dists; mention it in the
  README licence section (it is there).

## 8. Versioning, deprecation and status statements

SemVer says anything may change in 0.x (https://semver.org/#spec-item-4), which is why
users need the project's own rule. Good small examples: attrs's "Backwards Compatibility"
policy page, Pydantic's "Version policy"
(https://docs.pydantic.dev/latest/version-policy/), httpx's long 0.x with breaking
changes called out per minor. A pyntpot statement, in the README "Status" section and
`docs/reference/`:

- 0.x: a **minor** (0.2.0) may break the public API; a **patch** (0.1.1) never does.
- Public API is what `pyntpot.ink`, `pyntpot.letters` and `pyntpot.maps` export
  (ADR 0007/0026); underscored and unexported modules are private.
- Deprecations: a `DeprecationWarning` for at least one minor before removal where
  practical, listed under "Deprecated" in the changelog. (Users running with
  `-W error`, as pyntpot's own tests do, see it at once.)
- **Pixel stability**, which no comparison project has to state: rendered output is
  byte-identical only for the same pyntpot version and the same numpy and Pillow; a
  minor may change how a picture looks, and the changelog says when. Callers that pin
  image hashes (the upstream consumer does) must pin pyntpot exactly.
- The cache layout and manifest format: say whether a minor may invalidate caches.
- Supported Pythons: 3.13 and later, dropping a version only in a minor.

## 9. Docs CI gates

- **Link checking: lychee** (https://github.com/lycheeverse/lychee,
  `lycheeverse/lychee-action`). Run `--offline` on every PR (relative links, anchors
  with `--include-fragments`, and local image paths, which also covers "images exist"),
  and the full online check on a weekly schedule only: external links flake, and
  `openstreetmap.org` and `opentopodata.org` rate-limit. Exclude `pypi.org/project/pyntpot`
  and `raw.githubusercontent.com/.../v0.1.0/...` before the tag exists, or they fail the
  release PR itself.
- **Markdown lint**: `markdownlint-cli2` (Node) or `rumdl` (Rust, ruff-like config, runs
  as a prek hook without Node). Keep the rule set small: heading levels, no bare URLs,
  fenced-code languages. Line length off, as with ruff's E501.
- **Executing code blocks**: the examples are already tested scripts. Rather than
  doctest the README (Sybil, `pytest-markdown-docs`, `phmdoctest`), make the README quick
  start a verbatim excerpt of an example and add an architecture test that the README's
  `python` block appears in `examples/` byte for byte. One source, already under test,
  and no network (the fixture cache) in CI.
- **README for PyPI**: `uvx twine check --strict dist/*` in CI after `uv build`, plus a
  test that every Markdown image and link in `README.md` is absolute (`https://`), since
  PyPI cannot resolve relative ones.
- **Image budget**: a test that images under `docs/images/` stay under a size cap.

## Implications for pyntpot

### Checklist for the 0.1.0 release surface

- [ ] Create the PyPI **pending trusted publisher** (owner `findlaywebb`, `publish.yml`,
      env `pypi`); never re-run the failed 0.0.1 and 0.0.2 publish jobs.
- [ ] `publish.yml`: tag equals version check, gate before upload, pin the action, GitHub
      release from the changelog section with dists attached.
- [ ] Optional TestPyPI dry run from a pre-release tag.
- [ ] Classifiers (Python versions, GIS, Artistic Software, OS Independent), no licence
      classifier; `Documentation` and `Changelog` URLs; keywords.
- [ ] README images under `docs/images/`, optimised, absolute raw URLs pinned to
      `v0.1.0`, alt text; links absolute.
- [ ] Badges: PyPI version, Pythons, CI, licence, CodSpeed. Nothing else.
- [ ] README "Status" section: 0.x policy, pixel stability, supported Pythons.
- [ ] `docs/explanation/data-policy.md`: Produced Work, attribution placement when
      turned off, Derivative Database exports, provider usage limits, contrast.
- [ ] CHANGELOG 0.1.0 with newcomer summary, compare links, breaking-first.
- [ ] GitHub topics, homepage field, social preview set by hand.
- [ ] CITATION.cff (with a version-sync test or without `version`).
- [ ] Bug-report issue form. Code of conduct only with a public contact.
- [ ] Docs gates: lychee offline in CI and online weekly, a markdown lint hook,
      `twine check --strict`, the absolute-links and README-excerpt tests.

### Changes to the P7 outline

- Strike "already done if Q14 chose PyPI for 0.0.1": it was not done; both runs failed.
- "set back from P10.R's 0.0.1 to 0.1.0" is stale: the tree is at 0.0.2.
- "Configure the trusted publisher (manual, documented in CONTRIBUTING)" belongs in a
  `docs/runbooks/release.md` next to `update-dependencies.md`, not CONTRIBUTING, which
  outsiders read.
- Add a slice for the release surface outside the repo (topics, social preview,
  GitHub release, CITATION) and one for docs gates; neither is in the outline.
- Add the versioning and pixel-stability statement and the "attribution off moves the
  duty" text explicitly; the outline says only "attribution requirement".
- The README hero images must be generated by tested example scripts from the Lynmouth
  fixture (as `examples/word.py` is planned), so they can be regenerated each release.

### Weaving the core point and style through the release surface

pyntpot's point is that it *paints*: every surface where it can show a painting instead
of describing one should, and the painting should be made by pyntpot.

- **Social preview (1280 x 640)**: the strongest identity slot. A painted Lynmouth card
  on the left, and the word "pyntpot" lettered by `pyntpot.letters` with the nib on a
  washed circle on the right, on the paper texture. Generate it with an
  `examples/social_preview.py` under the examples convention so it is reproducible and
  tested; it carries its OSM credit legibly.
- **Wordmark or logo**: the same lettered word on a wash (the `examples/word.py` image
  is nearly this). Use it as the README's first image on GitHub and PyPI, and as the
  GitHub avatar for any org later. No vector logo needed: a painted raster is the brand.
- **PyPI summary** (one line, shown in search results and `pip search` mirrors): lead
  with the verb and the craft, for example "Paint hand-drawn watercolour and
  pen-and-ink images in Python, with route maps from OpenStreetMap". Keep the GitHub
  description identical so the two never drift.
- **Topics and keywords**: craft words first (watercolour, watercolor, pen-and-ink,
  hand-drawn, hand-lettering), maps second; the maps are the first application, not the
  identity.
- **README order**: wordmark, one sentence, the route map and the non-map image side by
  side, then badges. The non-map image matters: it tells a visitor this is a painting
  library that happens to draw maps.
- **Release notes voice**: plain and specific, in GLOSSARY terms, with one painted
  image per release where a change is visible (for example, a stroke at the card edge
  before and after the deposit fix). A painting library's changelog should show its
  work. No hype adjectives.
- **Attribution as part of the style**: the OSM credit is hand-lettered on the card;
  present that as a feature in the data-policy page, while keeping it legible.
- **Avoid** stock fonts or a flat vector logo on any surface: they contradict the
  point. Keep image backgrounds on the paper colour so GitHub dark mode and PyPI both
  show a sheet of paper, not a cut-out.
