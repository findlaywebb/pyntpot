# Mutation testing fails under pytest 9.2

GitHub issue: [#207](https://github.com/findlaywebb/pyntpot/issues/207)

Area: tests (mutation testing).

mutmut 3.8.0 fails its stats pass under pytest 9.2. The pass reads `item._nodeid` at
`mutmut/runners/harness.py:157`, and pytest 9.2 removed that attribute (the public
`item.nodeid` remains). Mutation runs on `main` have therefore failed since commit
f34de97 (#205), which bumped pytest.

Workaround used on spec 008: run mutmut in a throwaway worktree, install an older pytest
with `uv pip install "pytest<9.2"`, and invoke everything with `uv run --no-sync` so uv
does not restore pytest 9.2.

Fix options:

- Pin pytest below 9.2 for the mutation run only.
- Upgrade mutmut once a release supports pytest 9.2.
