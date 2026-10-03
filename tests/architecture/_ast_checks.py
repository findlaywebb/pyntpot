"""Shared helpers and path constants for AST-level architecture checks.

All architecture test modules import from here rather than duplicating the
helpers. They parse source directly, so they run before any package is even
importable.
"""

import ast
from pathlib import Path

from support import REPO_ROOT

PACKAGES = REPO_ROOT / "src"
CORE_SRC = PACKAGES / "pyntpot"


def _source_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _violations(root: Path, predicate, exempt: frozenset[str] = frozenset()) -> list[str]:
    found: list[str] = []
    for path in _source_files(root):
        if str(path.relative_to(REPO_ROOT)) in exempt:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if predicate(node):
                lineno = getattr(node, "lineno", "?")
                found.append(f"{path.relative_to(REPO_ROOT)}:{lineno}")
    return found
