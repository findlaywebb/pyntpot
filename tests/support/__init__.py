"""Shared test support: repo paths."""

from pathlib import Path

# The one canonical repo-root anchor for repo-relative test paths. Test modules import this
# rather than recomputing Path(__file__).parents[N], which is fragile to file moves and
# obscure. Kept dependency-free (no pyntpot imports) so the AST architecture checks can use
# it too.
REPO_ROOT = Path(__file__).resolve().parents[2]
