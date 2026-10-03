# Summary

<!-- What changed and why. Link the spec dir (specs/NNN-name/). -->

## Spec

- [ ] Matches `specs/NNN-name/spec.md` acceptance criteria
- [ ] Plan-reviewer pass recorded (no human approval gate — the review agent blocks)

## Gates (green or explained)

- [ ] `uv run ruff format --check . && uv run ruff check .`
- [ ] `uv run ty check`
- [ ] `uv run lint-imports`
- [ ] `uv run pytest --cov`
