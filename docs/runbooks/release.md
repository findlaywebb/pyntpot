# Runbook: releasing pyntpot

A release is a merged release PR and a tag pushed straight after it. The `Publish`
workflow (`.github/workflows/publish.yml`) does the rest: it fails unless the tag is `v`
plus the project version, runs the checks, builds, uploads to PyPI by trusted publishing,
then creates the GitHub release with the changelog section as notes and the dists attached.

## Once, before the first release

1. **Pending trusted publisher on PyPI.** The project is not on PyPI yet, so create a
   pending publisher at https://pypi.org/manage/account/publishing/ with owner
   `findlaywebb`, repository `pyntpot`, workflow `publish.yml` and environment `pypi`. A
   pending publisher does not reserve the name, so create it close to the tag.
2. **The `pypi` environment** exists under Settings, Environments on GitHub (the workflow
   names it).
3. **GitHub settings** (Settings, General, and the repository page):
   - Description: the same text as the PyPI summary (`description` in `pyproject.toml`).
   - Topics, craft first: `watercolour`, `watercolor`, `pen-and-ink`, `hand-drawn`,
     `hand-lettering`, `generative-art`, then `maps`, `gpx`, `openstreetmap`.
   - Homepage: the PyPI page once it exists.
   - Social preview: upload `docs/images/social-preview.jpg` (there is no REST endpoint).
4. **Pages.** Under Settings, Pages, set the source to GitHub Actions so the docs site is
   published at https://findlaywebb.github.io/pyntpot/.

## Each release

1. Branch `release-X.Y.Z` from `main`.
2. Set `version` in `pyproject.toml`; run `uv lock`.
3. In `CHANGELOG.md`, give the section `## [X.Y.Z] - DATE`, put breaking changes first, and
   add the compare link at the foot.
4. Repoint the README's image URLs from the previous tag (or `main`) to `vX.Y.Z`. That is
   the only README edit; PyPI shows the images at the tag, so the page keeps its pictures.
5. Gate: `uv run prek run --all-files`, `uv run pytest -m "not golden"`,
   `uv build && uv run twine check --strict dist/*` (do not commit `dist/`), and the dash
   gate in `CONTRIBUTING.md`.
6. Merge the release PR, then **push the tag immediately**, because the README names images
   at the tag: `git tag vX.Y.Z <merge commit> && git push origin vX.Y.Z`.
7. Watch the `Publish` run. Check the PyPI page shows the images and the GitHub release
   exists with its notes and two dists.

## If a publish run fails

Fix the cause and move on with a new version. Never re-run the failed `v0.0.1` and
`v0.0.2` publish jobs: once the publisher exists a re-run would upload those two
candidates, which are not for general use, and 0.1.0 is the first upload. A failure
before the upload step leaves nothing on PyPI; delete the tag, fix on a new commit and tag
again. A file uploaded to PyPI can never be replaced, so a failure after the upload
needs a new version.
