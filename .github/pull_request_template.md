# Summary

<!-- What changed and why. Link the spec dir (specs/NNN-name/). -->

## Changelog

<!-- The PR title is the main entry, as type(scope): description (ADR 0042). List here,
one per line, any other change a user would notice, in the same form; leave it empty
otherwise. These lines go into the squash commit and git-cliff reads them.
fix(maps): a note no longer hides the home glyph -->

## Golden and docs images

<!-- Delete this section unless the PR moves a golden or a docs image (ADR 0052). Paste the
block `tests/golden/publish_diffs.py --push` prints, after `diff_images.py --ref origin/main`
(CONTRIBUTING.md, "Golden and docs images"). -->

## Spec

- [ ] Matches `specs/NNN-name/spec.md` acceptance criteria
- [ ] Plan-reviewer pass recorded (no human approval gate — the review agent blocks)

## Gates (green or explained)

- [ ] `uv run ruff format --check . && uv run ruff check .`
- [ ] `uv run ty check`
- [ ] `uv run lint-imports`
- [ ] `uv run pytest --cov`
- [ ] Mutation run on the changed `ink`/`letters` functions (CONTRIBUTING.md): score, and each
      surviving mutant either killed by a new test or listed here as equivalent
