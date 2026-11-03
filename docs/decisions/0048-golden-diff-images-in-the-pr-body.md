# 0048 — Golden diff images in the PR body (amends 0006 and 0036)

Status: accepted

## Context

A golden regeneration (ADRs 0006, 0025, 0031, 0036, 0041, 0045) records what moved as
numbers: `make_golden.py --compare` and `make_docs_images.py --compare` log, per image,
whether it is byte-identical and the fraction of pixels past the channel bound, and the ADR
tables those fractions. Nothing showed the change itself. A reviewer opened the old and new
images by hand and looked for the difference, and a 0.0006 move in the wash, or a label
shifted in one corner of a 1800 by 1457 card, is easy to miss that way. When the golden
workflow failed on CI, it kept the fresh paints but not the image each one was compared
with, so a reviewer had to pair them by hand as well.

## Decision

### The tool

Test tooling beside `make_golden.py`, in `tests/golden/`, outside the package: nothing in
`src/pyntpot` imports it, and only `repaint.py` paints (through the two make scripts).

- `diff_images.py OUT` compares two sides: two directories of one layout (`--before DIR
  --after DIR`), or the repository at a git ref against the working tree or a second ref
  (`--ref REF [--after-ref REF]`), over `docs/images` and `tests/golden`. For each PNG,
  WebP or JPEG whose decoded pixels differ it writes a diff image (before, after, a heat
  map of the delta and a key, two by two, each cell shrunk by a whole factor to fit 480
  pixels) and a 1:1 crop image of the most-changed region (the changed pixels' box padded by
  16 pixels, or its densest 360-pixel window, with a locator), then `summary.json` and
  `summary.md`. An image whose bytes differ but whose pixels do not is skipped.
- `publish_diffs.py OUT [--push]` commits `OUT` to `<pr-branch>/` on the orphan branch
  `pr-assets`, through a temporary `git worktree`, and writes the Markdown block for the PR
  body (`OUT/pr-body.md`).
- `repaint.py OUT [NAME ...]` repaints the Lynmouth goldens and the docs images into a
  scratch tree laid out as the repository is, logs `make_golden.py`'s compare, and runs
  `diff_images.py` against the working tree.
- `diff_measure.py`, `diff_render.py` and `diff_report.py` are the measuring, drawing and
  summary modules the commands share, tested with real tiny images
  (`tests/golden/test_diff_*.py`, not golden-marked, so they run in every gate).

The numbers are the parity gate's. A pixel's delta is its largest channel difference over
RGB, or RGBA where the image has alpha; the changed fraction counts the pixels past
`MAX_CHANNEL_DELTA` (2), the number ADR 0030's bound (`MAX_DIFFERING_FRACTION`, 0.005)
holds. The summary flags a fraction past that bound, and marks an image `local` when the
changed pixels' box covers at most a quarter of it, else `widespread`. The box follows the
pixels past the channel bound, or every changed pixel when none is past it.

### Links that render

The repository is public, so the block links `raw.githubusercontent.com` files, which
GitHub renders inline for any reader; `--url-form blob` writes
`github.com/<owner>/<repo>/blob/<commit>/<path>?raw=true` links for a private repository.
Each link names the `pr-assets` commit, not the branch: a PR body keeps showing the review images
it was written with after a later publish replaces them, and no cache serves an old review image
at a moved branch's URL. `pr-assets` is an orphan branch that holds review images only, so it
never merges and adds no history to `main`; each PR's review images sit under its branch name.
The publish never touches the working tree, the index or the checked-out branch, and it
pushes only when given `--push`.

### The rule

Every PR that moves a golden (`tests/golden/lynmouth/`) or a docs image or master
(`docs/images/`, `tests/golden/docs/`) runs `diff_images.py --ref origin/main` on its branch,
publishes with `publish_diffs.py --push`, and pastes the block into the PR body under
"Golden and docs images" (the PR template's section). The regeneration ADR keeps its
numbers and its reading of the images, as ADR 0036 sets out; the review images are the evidence a
reviewer looks at, and the ADR may link them. ADR 0036's process gains one step: after the
first compare, `repaint.py` (or `diff_images.py` on the compare's output) draws what moved.

### CI

On a failure the golden workflow also runs `diff_images.py` over the fresh paints against
the checkout, leaving out changes within the parity bound (`--min-fraction 0.005`), and
uploads the review images as `golden-diffs-<os>` beside the fresh paints. The parity and docs pin
tests copy their paints into `fresh` trees at the repository paths so the step can pair
each paint with its committed image; nothing else in the tests changes, and a passing run
draws nothing.

## Consequences

- A golden-moving PR shows its changes as pictures, with the region that moved at full
  size, and the table carries ADR 0030's bound beside each fraction.
- The tolerance gate, the channel bound and the exact local gate are unchanged. The tool
  reports and never gates: it exits 0 whatever moved.
- `pr-assets` grows with every published PR. Its review images are a few hundred kilobytes per
  image; a branch that has merged may have its directory deleted from `pr-assets` in a
  later commit, which leaves its old links working, since they name earlier commits.
