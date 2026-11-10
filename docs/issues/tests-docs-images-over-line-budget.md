# tests/support/docs_images.py is over the 400-line file budget

GitHub issue: [#212](https://github.com/findlaywebb/pyntpot/issues/212)

Area: tests.

`tests/support/docs_images.py` is 511 lines (565 before `docs_image.py` was split out), over the soft budget of 400 lines per file
stated in `CLAUDE.md` ("Over budget: split into multiple files along responsibility
lines; never trim, squeeze, or thin docstrings to fit").

## Why no gate catches it

`test_no_oversized_files` (`tests/architecture/test_boundaries.py:40`, limit at `:48`)
walks `PACKAGES` only, and `PACKAGES` is `REPO_ROOT / "src"`
(`tests/architecture/_ast_checks.py:13`). `tests/` is neither exempted nor allowlisted
in the test; it is simply outside its scan, so the budget is unenforced for test support
code and the file grew past it unnoticed.

## What the file holds today

One module mixes several responsibilities:

- the `DocsImage` type and `master_path` (`:63`, `:89`)
- the byte budgets: `KIND_BUDGET_BYTES`, `SLICE_SHARE_BYTES`, `TOTAL_BUDGET_BYTES`
  (`:95`, `:103`, `:125`)
- the builders `_gallery`, `_stages`, `_rung`, `_place_card` and the `IMAGES` registry
  with each slice's entries (`:128` onwards)

## Relation to spec 009a (PR 2)

Spec 009a moves `DocsImage` into its own module and puts the new slices' entries in a
new module. That shrinks the file and stops it growing, but does not finish the split:
the budgets and the existing slices' entries stay behind, so the remainder should be
checked against the budget once 009a lands.

## Proposed fix

Split the registry by responsibility, one concept per file:

1. types (`DocsImage`, `master_path`)
2. budgets (the three byte-budget constants)
3. per-slice entry blocks, one module per slice, with a thin `IMAGES` assembly

Optionally extend `test_no_oversized_files` to scan `tests/` too, once every test file is
under budget (other test files may be over; see #198 for `test_placement.py`).
