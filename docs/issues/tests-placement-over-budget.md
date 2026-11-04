# test_placement.py is over the 400-line budget

GitHub issue: [#198](https://github.com/findlaywebb/pyntpot/issues/198)

Area: tests (maps lettering).

`tests/unit/maps/lettering/test_placement.py` is 404 lines (`wc -l`), over the 400-line
soft budget in `CLAUDE.md`. Nothing fails, because the budget test reads only `src/`.
It predates feature 006.

Fix by splitting along responsibility lines into separate test files, as verbatim moves,
never by trimming tests or docstrings to fit.

Source: `specs/006-one-public-surface/review/diff-review.md`, nice-to-have 2.
