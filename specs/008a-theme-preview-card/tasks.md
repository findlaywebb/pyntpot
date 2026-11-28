# 008a — tasks

Plan: `plan.md` revision 3 (decisions 1 to 19). Review: `review-plan.md`.

## P1: ADR and fixture

- [x] Branch named on #79.
- [x] ADR 0072 "A preview fixture in the Lynmouth box" (decision 12) and its index row.
- [x] Red: `tests/fixtures/test_make_preview.py` — byte equality with the committed fixture,
      `PREVIEW_KEY`, every coordinate in `BOXES["preview"]`, names from the spec's list,
      presence on `Style()` and the y-fenni style (finding 3, decision 16), small patches at
      900 px (decision 4), doubling back (decision 6), per-theme card inside the fetch box and
      lanes painted (decision 17).
- [x] Green: `tests/fixtures/make_preview.py` and `tests/fixtures/preview_payloads.py`
      (decisions 1 to 9, 16, 19); fixture written and committed with its `README.md`.
- [x] `tests/support/paths.py` `PREVIEW_KEY`; `tests/architecture/test_coordinates.py`
      `BOXES`, `KEYS`, `BUDGETS` entries; gates green.

## P2: Example and goldens

- [x] Red: `tests/golden/test_theme_preview.py` (golden paint test; unmarked theme-set test).
- [x] Green: `examples/theme_preview.py` (decisions 10, 15); `NOTE_POINT` check in
      `test_make_preview.py` (decision 18).
- [x] `CARD_SIZE`, `MEAN_RGB` and the label sets measured once and pinned as literals.
- [x] Timed CLI run `uv run python examples/theme_preview.py --theme default out/`; time
      recorded for the PR body.

## P3: Docs

- [x] `tests/support/docs_images_008a.py` and the three `docs_images.py` edits (decision 13).
- [x] Images painted by `make_docs_images.py`; masters committed; docs image tests green.
- [x] `docs/how-to/write-a-theme.md` and `docs/gallery.md` placements and captions.
- [x] `docs/features/maps-theme-preview-card.md` deleted.

## P4: Review and PR

- [x] Full gates, golden suite included.
- [x] Fresh-context diff review against the plan; findings triaged and applied.
- [x] Spec acceptance criteria ticked against evidence.
- [ ] PR `feat(maps): a theme preview card that holds every feature and the awkward meetings between them`, `Closes #79`; merged when CI is green.
