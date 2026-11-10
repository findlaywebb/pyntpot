# Mutation testing: spec 009a (G)

Scope: `uv run python tests/mutation/scope.py --base origin/claude/quirky-hypatia-z2pii3 --out "$patterns"`,
run with `mutmut run` under `prlimit --as=3500000000`. One changed `ink` function:
`pyntpot.ink.pigment_table.role_transparencies` (its docstring and the module's no longer name
`PaperStyle.pigment_transparency`). One mutant. As the plan expected, `maps` is outside
`only_mutate`, so the maps changes are not in scope; they are covered by exact-value tests.

- **Harness.** The pytest-9 workaround of `specs/009-line-effects-and-registry/mutation.md`
  (issue #207): a `sitecustomize.py` outside the repo aliasing `Node._nodeid`; nothing in the repo
  changed. A stale `mutants/` cache from an earlier run was removed first.

## Result

| | mutants |
| --- | --- |
| Total | 1 |
| Killed by the existing suite | 0 |
| Survived the existing suite | 1 |
| Killed by a new test | 1 |
| Equivalent | 0 |

The survivor, `role_transparencies` 1 (`_transparencies(None)` for `_transparencies(ROLE_PIGMENTS)`),
survived because `TRANSPARENCY` is built at import, before any mutant is active, so only a direct
call reaches it (as `_entry` did in 009). Killed by
`tests/unit/ink/test_pigment_entry.py::test_role_transparencies_is_a_fresh_copy_of_the_role_table`.
No survivor revealed a bug in `src`.
