# The P6 plan's Python blocks fail the ruff-format hook, so G-here is red

The `ruff-format` hook formats `.md` files as well as `.py` (its `files`
pattern is `\.(py|pyi|md)$`), and ruff formats the Python code blocks inside
Markdown. At `5299ab1`, `prek run --all-files` reformats
`specs/001-port/plan.md` and fails: the `ast_neutral.py` block (P6
preamble, "AST-neutral check") has a module docstring with no blank line
after it and a 120-plus character `return` in `_is_doc`, and the
`doc_lines.py` block (P6.5) has the same docstring layout and two long
conditions and one long `sys.exit` line. Every other hook passes. So G-here
is red on the clean starting commit of P6.1, before any slice edit, and it
will stay red for every P6 slice until the plan changes.

P6.1 does not fix it: `plan.md` is not one of its owner files, and the plan
requires `$SCRIPTS/ast_neutral.py` and `doc_lines.py` to be copied verbatim
from these blocks and checked against `SHA256SUMS`, so reformatting them is
a plan change, not a docs fix. The hook's reformat was reverted.

Possible fix: in a bookkeeping commit to `plan.md`, apply exactly the
reformat `uv run ruff format specs/001-port/plan.md` makes (a blank line
after each block's docstring, and the long lines wrapped in parentheses),
then rewrite the two scripts to `$SCRIPTS` from the reformatted blocks and
regenerate `SHA256SUMS`. The scripts' behaviour does not change. Do not
exclude `specs/` from the hook.
