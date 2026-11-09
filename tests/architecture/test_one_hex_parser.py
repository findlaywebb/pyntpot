"""Hex is parsed in one module: `ink/colour.py` alone reads digits from a string.

The check walks the AST of every module under `src/pyntpot` and refuses a call of `int` with
base 16 or of `fromhex` anywhere but `ink/colour.py`.
"""

import ast

from support import REPO_ROOT

SRC = REPO_ROOT / "src" / "pyntpot"
PARSER = "ink/colour.py"


def _parses_hex(node: ast.AST) -> bool:
    """Whether `node` is `int(..., 16)` or a `.fromhex(...)` call."""
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "fromhex":
        return True
    return (
        isinstance(func, ast.Name)
        and func.id == "int"
        and len(node.args) == 2
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == 16
    )


def test_only_the_colour_module_parses_hex():
    """No module under `src/` but `ink/colour.py` calls `int(..., 16)` or `fromhex`."""
    offenders = [
        path.relative_to(SRC).as_posix()
        for path in sorted(SRC.rglob("*.py"))
        if any(_parses_hex(node) for node in ast.walk(ast.parse(path.read_text())))
    ]
    assert [o for o in offenders if o != PARSER] == []


def test_the_colour_module_does_parse_hex():
    """The check sees the one parser, so it is not passing by finding nothing."""
    tree = ast.parse((SRC / PARSER).read_text())
    assert any(_parses_hex(node) for node in ast.walk(tree))
