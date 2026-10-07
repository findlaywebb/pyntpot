# `uv run prek` fails because prek is not a project dependency

G-here and the CLAUDE.md toolchain run the hooks as
`uv run prek run --all-files`. At `5299ab1` that fails in this container
with `error: Failed to spawn: prek` (`No such file or directory`): prek is
not in `pyproject.toml` or `uv.lock`, so `uv sync` does not put it in the
venv, and it is not on the `PATH` either. P6.1 ran the same hooks as
`uvx prek run --all-files` (prek 0.5.5, fetched through the proxy into uv's
tool cache) and logged the substitution; nothing in the repository changed.

P6.1 does not fix it: adding a dependency is a change to `pyproject.toml`
and `uv.lock`, outside a docs slice's owner files.

Possible fix: add `prek` to the dev dependency group so `uv sync` installs
it and `uv run prek` resolves everywhere, or change the gate text to
`uvx prek` in the plan, CLAUDE.md and CONTRIBUTING.md together.
