# A feature note still cites the tip's path smoother by its underscore name

GitHub issue: [#38](https://github.com/findlaywebb/pyntpot/issues/38)

Area: docs.

`pyntpot.ink.tip._smooth_path` is now `pyntpot.ink.tip.smooth_path`: `ink.stamp`
imports it, and a name another module imports carries no underscore
(`tests/unit/maps/test_import_order.py::test_no_module_imports_another_modules_private_name`).
`docs/features/ink-tip-hold-stroke-ends.md` still names it `_smooth_path`, at
its "What exists today" line and again where it names the docstrings to update.
No test reads that file, so nothing fails.

To show it: `grep -n "_smooth_path" docs/features/ink-tip-hold-stroke-ends.md`
prints two lines; it should print none.

Possible fix: write `smooth_path` (and `pyntpot.ink.tip.smooth_path`) in both
places. Prose only; no code or output changes.
