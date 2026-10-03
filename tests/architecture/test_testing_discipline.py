"""No-mock gate for tests/.

Per CLAUDE.md: unittest.mock and pytest_mock are banned. Real objects keep
tests honest. A genuine third-party boundary (network, filesystem, external
process) earns an explicit allowlist entry via review — nothing else does.

Matching scope
--------------
Flagged import forms:
  - ``import unittest.mock`` / ``import pytest_mock``
  - ``from unittest import mock``
  - ``from unittest.mock import ...``
  - ``from pytest_mock import ...``
String literals mentioning these names are not scanned — only import AST nodes.
"""

import ast

from ._ast_checks import REPO_ROOT, _source_files

_TESTS_ROOT = REPO_ROOT / "tests"

# Policy: a genuine third-party boundary earns an entry via review, nothing
# else does. Paths are relative to REPO_ROOT (e.g. "tests/foo/bar.py").
ALLOWED_MOCK_USERS: frozenset[str] = frozenset[str]()

_MOCK_TOP_MODULES = {"unittest.mock", "pytest_mock"}


def _is_banned_direct(names: list[ast.alias]) -> bool:
    """Return True if any bare import name is a banned mock module."""
    return any(a.name in _MOCK_TOP_MODULES or a.name.startswith("unittest.mock.") for a in names)


def _is_banned_from(module: str | None, names: list[ast.alias]) -> bool:
    """Return True if a from-import pulls in a banned mock name."""
    if module is None:
        return False
    if module in _MOCK_TOP_MODULES or module.startswith("unittest.mock."):
        return True
    return module == "unittest" and any(a.name == "mock" for a in names)


def test_no_mock_imports() -> None:
    """No test module imports unittest.mock or pytest_mock — real objects only."""

    def is_mock_import(node: ast.AST) -> bool:
        match node:
            case ast.Import(names=aliases):
                return _is_banned_direct(aliases)
            case ast.ImportFrom(module=module, names=aliases):
                return _is_banned_from(module, aliases)
            case _:
                return False

    violations: list[str] = []
    for path in _source_files(_TESTS_ROOT):
        rel = str(path.relative_to(REPO_ROOT))
        if rel in ALLOWED_MOCK_USERS:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if is_mock_import(node):
                lineno = getattr(node, "lineno", "?")
                violations.append(f"{rel}:{lineno}")

    assert not violations, (
        "unittest.mock / pytest_mock imports found — use real objects "
        "instead; add to ALLOWED_MOCK_USERS only for genuine "
        "third-party boundaries, approved via review"
    )
