# `_radii` in the trace has no caller

`pyntpot.letters.trace._radii` returns the inscribed radius under each point
of a run. Nothing in `src/` or `tests/` calls it: `_centrelines`, `_flanks`,
`_extend` and `_dots` all read the distance field directly.

P6 does not fix it because deleting a function is a code change.

Possible fix: delete `_radii`, after `uv run vulture` confirms it is unused;
the AST of every other function is unchanged.
