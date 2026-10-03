"""AST-level fitness checks import-linter can't express.

These encode the conventions from BOUNDARIES.md and the root CLAUDE.md as
unskippable, fast tests. They parse source directly, so they run before any
package is even importable.
"""

import ast

from ._ast_checks import CORE_SRC, PACKAGES, REPO_ROOT, _source_files, _violations
from support.exemptions import read_exemption_lines


def test_package_has_no_env_access() -> None:
    """The package must not read the environment — config is injected, not read."""

    def is_env_access(node: ast.AST) -> bool:
        match node:
            case ast.Attribute(value=ast.Name(id="os"), attr="environ" | "getenv"):
                return True
            case _:
                return False

    assert not _violations(CORE_SRC, is_env_access), (
        "os.environ/os.getenv access in the package — inject configuration instead"
    )


def test_no_print_statements() -> None:
    """Production code logs; it never prints."""

    def is_print(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Name(id="print")):
                return True
            case _:
                return False

    assert not _violations(PACKAGES, is_print), "print() in production code — use logging"


def test_no_oversized_files() -> None:
    """Soft budget ~400 lines/file — over budget, SPLIT into multiple files.

    The remedy is never to trim or squeeze docstrings to fit: a file over 400 is
    decomposed along responsibility lines into multiple files optimised for
    agentic discovery (one concept per file). Files listed in
    exemptions/line_budget.txt are skipped.
    """
    max_lines = 400
    exempt = set(read_exemption_lines("line_budget.txt"))
    offenders = [
        f"{path.relative_to(REPO_ROOT)} ({n} lines)"
        for path in _source_files(PACKAGES)
        if str(path.relative_to(REPO_ROOT)) not in exempt
        and (n := len(path.read_text().splitlines())) > max_lines
    ]
    assert not offenders, f"files over the {max_lines}-line budget: {offenders}"
